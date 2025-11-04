# duck_train_env.py
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations
import math
from typing import Sequence, List

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.utils.math import quat_apply

# NEW: USD access for physics-material binding
from pxr import Usd, UsdPhysics, PhysxSchema, UsdGeom
import omni.usd
import re

class DuckTrainEnv(DirectRLEnv):
    """Minimal env: 제어 DOF (q, qd, +센서) 관측 / Δq 위치제어 / 보상 / 종료
       TerrainImporter를 사용하고, per-env 발바닥 마찰을 랜덤화한다.
    """

    cfg: "DuckTrainEnvCfg"

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    def __init__(self, cfg: "DuckTrainEnvCfg", render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        # 제어 인덱스/스케일
        self._ctrl_idx, _ = self.robot.find_joints(self.cfg.control_dof_names)
        if not self._ctrl_idx:
            raise RuntimeError(f"[duck] control_dof_names not found on stage: {self.cfg.control_dof_names}")

        self.action_scale = float(getattr(self.cfg, "action_scale", 0.05))
        self.num_actions = len(self._ctrl_idx)
        self._max_tilt = float(getattr(self.cfg, "max_tilt_rad", math.pi / 4))

        # 관측/보상용 파라미터
        self._height_band      = float(getattr(self.cfg, "height_band", 0.05))
        self._height_k         = float(getattr(self.cfg, "height_k", 20.0))
        self._h_fail_margin    = float(getattr(self.cfg, "height_fail_margin", 0.08))
        self._h_ref            = torch.zeros(self.num_envs, device=self.device)
        self.gamma_shape = 0.99
        self.w_upright = 2.0
        self.w_height  = 1.0
        self.w_shape   = 1.5
        self.alive_per_step = 0.01
        self.c_action = 1e-3
        self.c_rate   = 5e-4
        self.c_lin    = 0.5
        self.c_yaw    = 0.02
        self.fall_penalty = 5.0
        self._phi_prev = torch.zeros(self.num_envs, device=self.device)
        self._last_actions = None
        self._foot_bin_prev = None

        # 센서 핸들
        self._imu = self.scene["imu"]
        self._feet_contact = self.scene["contact_forces"]

        # NEW: friction randomization config (from cfg)
        self._mu_s_rng = getattr(self.cfg, "friction_static_range", (0.6, 1.3))
        self._mu_d_rng = getattr(self.cfg, "friction_dynamic_range", (0.5, 1.1))
        self._mu_mode  = getattr(self.cfg, "friction_combine_mode", "average")

        # cache stage
        self._stage = omni.usd.get_context().get_stage()

    # ------------------------------------------------------------------
    # Scene
    # ------------------------------------------------------------------
    def _setup_scene(self):
        # 로봇
        self.robot = Articulation(self.cfg.robot_cfg)

        # NOTE: GroundPlane 제거 — TerrainImporter가 scene cfg에서 생성됨.
        # spawn_ground_plane(...) was removed.

        # 씬 복제
        self.scene.clone_environments(copy_from_source=False)

        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[])

        self.scene.articulations["robot"] = self.robot

        # 라이트(선택)
        light = sim_utils.DomeLightCfg(intensity=1500.0)
        light.func("/World/Light", light)

    # ------------------------------------------------------------------
    # RL hooks
    # ------------------------------------------------------------------
    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        self.actions = self.action_scale * torch.clamp(actions, -1.0, 1.0)

    def _apply_action(self) -> None:
        q_now = self.robot.data.joint_pos[:, self._ctrl_idx]
        q_t = q_now + self.actions
        self.robot.set_joint_position_target(q_t, joint_ids=self._ctrl_idx)

    def _get_observations(self) -> dict:
        # --- 관절 ---
        q  = self.robot.data.joint_pos[:, self._ctrl_idx]
        qd = self.robot.data.joint_vel[:, self._ctrl_idx]

        # --- IMU ---
        imu_data = self._imu.data
        ang_vel_b = imu_data.ang_vel_b            # (N,3)
        lin_acc_b = imu_data.lin_acc_b            # (N,3)
        quat_w    = imu_data.quat_w               # (N,4)  (wxyz)

        # --- 발 접촉 ---
        contact_data = self._feet_contact.data
        net_forces_w = contact_data.net_forces_w  # (N,F,3) or (N,F,T,3)
        if net_forces_w.dim() == 4:
            net_forces_w = net_forces_w[..., -1, :]
        f_n = torch.clamp(net_forces_w[..., 2], min=0.0)  # (N,F)

        th_on, th_off = 3.0, 1.5
        if self._foot_bin_prev is None:
            self._foot_bin_prev = torch.zeros_like(f_n)
        foot_bin = torch.where(self._foot_bin_prev > 0.5,
                               (f_n > th_off).float(),
                               (f_n > th_on).float())
        self._foot_bin_prev = foot_bin

        Fmax = 50.0
        foot_force_norm = torch.clamp(f_n / Fmax, 0.0, 1.0)

        obs = torch.cat(
            [q, qd, foot_bin, foot_force_norm, ang_vel_b, lin_acc_b, quat_w],
            dim=-1
        )
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6).clamp_(-20.0, 20.0)
        return {"policy": obs}

    def _get_rewards(self):
        pos, quat_root, lin, ang = self._get_root_state()
        h   = pos[:, 2]
        vz  = lin[:, 2]

        q   = self.robot.data.joint_pos[:, self._ctrl_idx]
        qd  = self.robot.data.joint_vel[:, self._ctrl_idx]
        imu = self._imu.data

        t = self.episode_length_buf.float()
        T = float(self.max_episode_length)

        netF = self._feet_contact.data.net_forces_w
        if netF.dim() == 4:
            netF = netF[..., -1, :]
        f_n = torch.clamp(netF[..., 2], min=0.0)
        th_on = getattr(self, "contact_on", 3.0)
        contact_bin = (f_n > th_on).float()
        r_stance = contact_bin.max(dim=1).values

        quat = imu.quat_w
        quat = quat / (quat.norm(dim=1, keepdim=True) + 1e-8)
        w, x, y, z = quat[:, 0], quat[:, 1], quat[:, 2], quat[:, 3]
        s = (x * x + y * y).clamp(0, 1 - 1e-8)
        tilt = 2.0 * torch.asin(torch.sqrt(s))
        r_upright = torch.exp(-4.0 * tilt * tilt)

        dh = h - self._h_ref
        band = self._height_band
        r_height = torch.exp(- (torch.abs(dh) / band) ** 2)
        p_height = (1.0 - r_height)

        p_vz  = vz * vz
        p_yaw = imu.ang_vel_b[:, 2].abs()
        p_action = (self.actions ** 2).mean(dim=1)
        if self._last_actions is not None:
            p_action_rate = ((self.actions - self._last_actions) ** 2).mean(dim=1)
        else:
            p_action_rate = torch.zeros_like(p_action)
        p_qd = (qd ** 2).mean(dim=1)

        alive_gate = (r_upright > 0.6) & (h > self._h_ref - 0.03)

        w_height    = 2.0
        w_upright   = 1.5
        w_vz        = 0.2
        w_yaw       = 0.05
        w_action    = 0.002
        w_action_rt = 0.001
        w_qd        = 0.01
        w_stance    = 0.2

        alive_base = 0.01
        alive_scale = 0.20
        alive_power = 2.0
        r_alive = alive_gate.float() * (alive_base + alive_scale * (t / T) ** alive_power)

        reward = (
            - w_height    * p_height
            - w_upright   * (1.0 - r_upright)
            - w_vz        * p_vz
            - w_yaw       * p_yaw
            - w_action    * p_action
            - w_action_rt * p_action_rate
            - w_qd        * p_qd
            + w_stance    * r_stance
            + r_alive
        )

        time_out = self.episode_length_buf >= self.max_episode_length - 1

        _, base_quat, _, _ = self._get_root_state()
        z_body = self._body_z(base_quat)
        pitch = torch.atan2(-z_body[:, 0], z_body[:, 2])
        roll  = torch.atan2( z_body[:, 1], z_body[:, 2])
        too_tilt = (torch.abs(pitch) > self._max_tilt) | (torch.abs(roll) > self._max_tilt)
        too_low  = h < (self._h_ref - self._h_fail_margin)
        terminated = too_tilt | too_low

        success = time_out & (~terminated)
        fail    = (~time_out) & terminated

        reward = reward + success.float() * 5.0
        reward = reward - fail.float()    * 100.0

        reward = torch.nan_to_num(reward, nan=-10.0, posinf=-10.0, neginf=-10.0)

        self.extras["r/upright_imu"] = r_upright.mean()
        self.extras["p/height"]      = p_height.mean()
        self.extras["p/vz"]          = p_vz.mean()
        self.extras["p/yaw_imu"]     = p_yaw.mean()
        self.extras["p/action"]      = p_action.mean()
        self.extras["p/action_rate"] = p_action_rate.mean()
        self.extras["p/qd"]          = p_qd.mean()
        self.extras["r/stance"]      = r_stance.mean()

        self._last_actions = self.actions.clone()
        return reward

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        pos, base_quat, _, _ = self._get_root_state()
        z_b = self._body_z(base_quat)
        pitch = torch.atan2(-z_b[:, 0], z_b[:, 2])
        roll  = torch.atan2( z_b[:, 1], z_b[:, 2])

        self._h_ref = torch.where((self.episode_length_buf == 0), pos[:, 2].detach(), self._h_ref)
        h_fail = 0.3 * self._h_ref

        out_of_bounds = (torch.abs(pitch) > self._max_tilt) | (torch.abs(roll) > self._max_tilt) | (pos[:, 2] < h_fail)
        return out_of_bounds, time_out

    # ------------------------------------------------------------------
    # Reset + (NEW) friction randomization
    # ------------------------------------------------------------------
    def _reset_idx(self, env_ids: Sequence[int] | None):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        super()._reset_idx(env_ids)

        # 기본 상태 리셋
        q0    = self.robot.data.default_joint_pos[env_ids]
        qd0   = self.robot.data.default_joint_vel[env_ids]
        root0 = self.robot.data.default_root_state[env_ids]
        root0[:, :3] += self.scene.env_origins[env_ids]
        root0[:, 2]  += 0.20

        self.robot.write_root_pose_to_sim(root0[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(root0[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(q0, qd0, None, env_ids)

        self._h_ref[env_ids] = root0[:, 2]
        if self._phi_prev is not None:
            self._phi_prev[env_ids] = 0.0
        if self._foot_bin_prev is not None:
            self._foot_bin_prev[env_ids] = 0.0
        self._last_actions = None

        # NEW: per-env effective ground friction via foot sole material randomization
        #if self.training:
        self._randomize_foot_friction(env_ids)

    # ----------------------------- NEW: helpers -----------------------------
    def _randomize_foot_friction(self, env_ids: Sequence[int]):
        """Randomize physics material on *foot colliders* for each env.
        With frictionCombineMode="average" on ground (or default), this
        mimics per-env ground µ while keeping a single Terrain mesh.
        """
        mu_s_min, mu_s_max = self._mu_s_rng
        mu_d_min, mu_d_max = self._mu_d_rng

        for env_id in env_ids:
            # sample µ for this env
            mu_s = float(torch.rand(1).item() * (mu_s_max - mu_s_min) + mu_s_min)
            mu_d = float(torch.rand(1).item() * (mu_d_max - mu_d_min) + mu_d_min)
            # collect foot collider prims for this env and bind material
            for p in self._find_env_foot_colliders(int(env_id)):
                self._bind_physics_material(p, mu_s, mu_d, self._mu_mode)


    def _find_env_foot_colliders(self, env_id: int):
        import re

        stage = self._stage  # << 기존 self._scene.stage 대신
        base = f"/World/envs/env_{env_id}/Robot"
        pat = re.compile(rf"^{re.escape(base)}/.*foot", re.IGNORECASE)

        base_prim = stage.GetPrimAtPath(base)
        if not base_prim.IsValid():
            return []

        colliders = []
        # 로봇 하위 모든 프림 순회
        for prim in Usd.PrimRange(base_prim):
            p = prim.GetPath().pathString
            # 충돌체(API) 또는 메시인 경우만 채택
            if pat.match(p) and prim.IsValid() and (
                prim.HasAPI(UsdPhysics.CollisionAPI) or prim.IsA(UsdGeom.Mesh)
            ):
                colliders.append(prim)   # ← 경로 문자열이 아니라 Usd.Prim을 반환
        return colliders


    def _bind_physics_material(self, prim, mu_s: float, mu_d: float, combine: str):
        # prim이 경로 문자열로 오더라도 Prim으로 변환
        if isinstance(prim, str):
            prim = self._stage.GetPrimAtPath(prim)
        if not prim.IsValid():
            return

        mat_path = f"/World/Materials/{prim.GetName()}_mat"
        mat = UsdPhysics.Material.Define(self._stage, mat_path)
        mat.GetStaticFrictionAttr().Set(mu_s)
        mat.GetDynamicFrictionAttr().Set(mu_d)
        mat.GetRestitutionAttr().Set(0.0)

        px = PhysxSchema.PhysxMaterialAPI.Apply(self._stage.GetPrimAtPath(mat_path))
        px.GetFrictionCombineModeAttr().Set(combine)  # "average"/"max"/"min"/"multiply"

        mb = UsdPhysics.MaterialBindingAPI(prim)
        mb.GetDirectBindingRel().SetTargets([mat.GetPath()])

    # ----------------------------- utils -----------------------------
    def _body_z(self, base_quat: torch.Tensor) -> torch.Tensor:
        n = base_quat.shape[0]
        unit_z = torch.zeros((n, 3), device=self.device, dtype=base_quat.dtype)
        unit_z[:, 2] = 1.0
        return quat_apply(base_quat, unit_z)

    def _get_root_state(self):
        d = self.robot.data
        if hasattr(d, "root_state_w"):
            rs = d.root_state_w
            return rs[:, 0:3], rs[:, 3:7], rs[:, 7:10], rs[:, 10:13]
        if hasattr(d, "root_state"):
            rs = d.root_state
            return rs[:, 0:3], rs[:, 3:7], rs[:, 7:10], rs[:, 10:13]
        if hasattr(d, "root_pose_w") and hasattr(d, "root_vel_w"):
            pos  = d.root_pose_w[:, 0:3]
            quat = d.root_pose_w[:, 3:7]
            lin  = d.root_vel_w[:, 0:3]
            ang  = d.root_vel_w[:, 3:6]
            return pos, quat, lin, ang
        if hasattr(d, "body_state_w"):
            bs = d.body_state_w
            rs = bs[:, 0, :]
            return rs[:, 0:3], rs[:, 3:7], rs[:, 7:10], rs[:, 10:13]
        raise RuntimeError("No root state tensors found on ArticulationData.")