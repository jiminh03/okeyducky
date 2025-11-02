# duck_train_env.py
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations
import math
from typing import Sequence

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane
from isaaclab.utils.math import quat_apply
# NOTE: InteractiveScene는 DirectRLEnv(super().__init__)에서 cfg.scene로 생성된다.

class DuckTrainEnv(DirectRLEnv):
    """Minimal env: 제어 DOF (q, qd, +센서) 관측 / Δq 위치제어 / 퍼텐셜+게이팅 보상 / 기울기+낮은 높이 종료"""

    cfg: "DuckTrainEnvCfg"

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    def __init__(self, cfg: "DuckTrainEnvCfg", render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        # --- 제어 인덱스/스케일 ---
        self._ctrl_idx, _ = self.robot.find_joints(self.cfg.control_dof_names)
        if not self._ctrl_idx:
            raise RuntimeError(f"[duck] control_dof_names not found on stage: {self.cfg.control_dof_names}")

        # Δq 스케일 (라디안 등) — 기본 0.05
        self.action_scale = float(getattr(self.cfg, "action_scale", 0.05))
        self.num_actions = len(self._ctrl_idx)

        # 종료 기준(라디안): 기본 45°
        self._max_tilt = float(getattr(self.cfg, "max_tilt_rad", math.pi / 4))

        # 높이 Dead-Band 파라미터 (관측용)
        self._height_band = float(getattr(self.cfg, "height_band", 0.05))      # ±5cm 허용대역
        self._height_k    = float(getattr(self.cfg, "height_k", 20.0))         # 대역 밖 패널티 기울기
        self._h_fail_margin = float(getattr(self.cfg, "height_fail_margin", 0.08))  # 기준-8cm 이하면 종료

        # env별 기준 높이 버퍼
        self._h_ref = torch.zeros(self.num_envs, device=self.device)

        # 센서 핸들
        self._imu = self.scene["imu"]                   # scene cfg에 등록돼 있어야 함
        self._feet_contact = self.scene["contact_forces"]

        # ------------- 보상 파라미터 (튜닝 포인트) -------------
        self.gamma_shape = 0.99  # PPO의 γ와 비슷하게 맞출 것을 권장

        # 양(+) 보상 가중치
        self.w_upright = 2.0
        self.w_height  = 1.0
        self.w_shape   = 1.5
        self.alive_per_step = 0.01

        # 규제(−) 가중치
        self.c_action = 1e-3
        self.c_rate   = 5e-4
        self.c_lin    = 0.5
        self.c_yaw    = 0.02

        # 실패 시 큰 패널티
        self.fall_penalty = 5.0

        # 캐시
        self._phi_prev = torch.zeros(self.num_envs, device=self.device)
        self._last_actions = None
        self._foot_bin_prev = None

    # ------------------------------------------------------------------
    # Scene
    # ------------------------------------------------------------------
    def _setup_scene(self):
        # 로봇
        self.robot = Articulation(self.cfg.robot_cfg)

        # 바닥
        spawn_ground_plane(prim_path="/World/ground", cfg=GroundPlaneCfg())

        # 씬 복제
        self.scene.clone_environments(copy_from_source=False)

        # CPU일 땐 충돌 필터
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[])

        # 등록
        self.scene.articulations["robot"] = self.robot

        # 라이트(선택)
        light = sim_utils.DomeLightCfg(intensity=1500.0)
        light.func("/World/Light", light)
        
    # ------------------------------------------------------------------
    # RL hooks
    # ------------------------------------------------------------------
    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        # 정책 출력 [-1,1] → tanh 포화 → Δq 스케일
        self.actions = self.action_scale * torch.clamp(actions, -1.0, 1.0)

    def _apply_action(self) -> None:
        # Δq 위치제어: q_target = q_now + Δq
        q_now = self.robot.data.joint_pos[:, self._ctrl_idx]
        q_t = q_now + self.actions
        # (선택) 조인트 한계가 필요하면 여기서 clamp
        # limits = getattr(self.robot.data, "joint_pos_limits", None)
        # if limits is not None:
        #     lo, hi = limits[0, self._ctrl_idx], limits[1, self._ctrl_idx]
        #     q_t = torch.clamp(q_t, lo, hi)
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
            net_forces_w = net_forces_w[..., -1, :]  # 마지막 시점 (N,F,3)
        f_n = torch.clamp(net_forces_w[..., 2], min=0.0)  # (N,F)

        # 히스테리시스 이진화
        th_on, th_off = 3.0, 1.5
        if self._foot_bin_prev is None:
            self._foot_bin_prev = torch.zeros_like(f_n)
        foot_bin = torch.where(self._foot_bin_prev > 0.5,
                               (f_n > th_off).float(),
                               (f_n > th_on).float())
        self._foot_bin_prev = foot_bin

        # 연속 힘 정규화
        Fmax = 50.0
        foot_force_norm = torch.clamp(f_n / Fmax, 0.0, 1.0)

        # --- obs 조립 ---
        obs = torch.cat(
            [q, qd, foot_bin, foot_force_norm, ang_vel_b, lin_acc_b, quat_w],
            dim=-1
        )
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6).clamp_(-20.0, 20.0)
        return {"policy": obs}

    def _get_rewards(self):
        # --- 루트 상태 ---
        pos, quat_root, lin, ang = self._get_root_state()
        h   = pos[:, 2]
        vz  = lin[:, 2]

        # --- 관절/센서 ---
        q   = self.robot.data.joint_pos[:, self._ctrl_idx]
        qd  = self.robot.data.joint_vel[:, self._ctrl_idx]
        imu = self._imu.data
        
        # --- 살아남은 시간 ---
        t = self.episode_length_buf.float()
        T = float(self.max_episode_length)

        # 접촉(마지막 시점)
        netF = self._feet_contact.data.net_forces_w
        if netF.dim() == 4:
            netF = netF[..., -1, :]
        f_n = torch.clamp(netF[..., 2], min=0.0)              # (N,F)
        th_on = getattr(self, "contact_on", 3.0)
        contact_bin = (f_n > th_on).float()
        r_stance = contact_bin.max(dim=1).values              # (N,)  # 보조 + 항

        # --- 직립 보상 -> '중심 0' 패널티로 변환 ---
        quat = imu.quat_w
        quat = quat / (quat.norm(dim=1, keepdim=True) + 1e-8)
        w, x, y, z = quat[:, 0], quat[:, 1], quat[:, 2], quat[:, 3]
        s = (x * x + y * y).clamp(0, 1 - 1e-8)
        tilt = 2.0 * torch.asin(torch.sqrt(s))
        r_upright = torch.exp(-4.0 * tilt * tilt)            # 0~1 (좋을수록 1)

        # --- 높이 Dead-Band: '중심 0' 패널티로 변환 ---
        dh = h - self._h_ref                                  # 기준 대비 편차
        band = self._height_band
        # 가우시안 근접도(좋으면 1) -> (1 - r)로 바꿔 패널티
        r_height = torch.exp(- (torch.abs(dh) / band) ** 2)   # 0~1
        p_height = (1.0 - r_height)                           # 0(좋음) ~ 1(나쁨)

        # --- 추가 패널티(포화/비선형 제거: 제곱형/Huber 권장) ---
        p_vz  = vz * vz                                       # 수직 튐/낙하 억제
        p_yaw = imu.ang_vel_b[:, 2].abs()                     # 요 흔들림 억제 (L1)
        # 액션/레이트: 평균 제곱
        p_action = (self.actions ** 2).mean(dim=1)
        if self._last_actions is not None:
            p_action_rate = ((self.actions - self._last_actions) ** 2).mean(dim=1)
        else:
            p_action_rate = torch.zeros_like(p_action)
        # 관절 속도: 평균 제곱
        p_qd = (qd ** 2).mean(dim=1)
        
        # 직립/높이 게이트 (넘어지지 않고 서 있을 때만 생존 보상 지급)
        alive_gate = (r_upright > 0.6) & (h > self._h_ref - 0.03)

        # --- 가중치 (초기 안정화용 예시값) ---
        w_height    = 2.0     # 높이 이탈 패널티
        w_upright   = 1.5     # 기울기 패널티
        w_vz        = 0.2
        w_yaw       = 0.05
        w_action    = 0.002
        w_action_rt = 0.001
        w_qd        = 0.01
        w_stance    = 0.2     # 접촉 +보상 (너무 크지 않게)

        # 작은 생존 보상(상수)은 0 또는 아주 작게
        alive_base = 0.01
        alive_scale = 0.20
        alive_power = 2.0
        r_alive = alive_gate.float() * (alive_base + alive_scale * (t / T) **alive_power)

        # --- 최종 리워드 (0을 중심으로, 대부분은 음수 패널티) ---
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
        
        # _get_rewards 말미(또는 _get_dones 로직 복제)에서 같이 계산
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        # 넘어짐 판정 재계산(보상에서 쓰기 위해)
        _, base_quat, _, _ = self._get_root_state()
        z_body = self._body_z(base_quat)
        pitch = torch.atan2(-z_body[:, 0], z_body[:, 2])
        roll  = torch.atan2( z_body[:, 1], z_body[:, 2])
        too_tilt = (torch.abs(pitch) > self._max_tilt) | (torch.abs(roll) > self._max_tilt)
        too_low  = h < (self._h_ref - self._h_fail_margin)
        terminated = too_tilt | too_low

        success = time_out & (~terminated)
        fail    = (~time_out) & terminated

        reward = reward + success.float() * 5.0      # timeout 성공 보너스
        reward = reward - fail.float()    * 100.0      # 조기 종료 패널티(과하지 않게)


        reward = torch.nan_to_num(reward, nan=-10.0, posinf=-10.0, neginf=-10.0)

        # --- 로깅 ---
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
        # 타임아웃
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        # 루트 자세/높이
        pos, base_quat, _, _ = self._get_root_state()
        z_b = self._body_z(base_quat)
        pitch = torch.atan2(-z_b[:, 0], z_b[:, 2])
        roll  = torch.atan2( z_b[:, 1], z_b[:, 2])

        # h_ref: 리셋 스텝 보정
        self._h_ref = torch.where((self.episode_length_buf == 0), pos[:, 2].detach(), self._h_ref)
        h_fail = 0.1 * self._h_ref

        out_of_bounds = (torch.abs(pitch) > self._max_tilt) | (torch.abs(roll) > self._max_tilt) | (pos[:, 2] < h_fail)
        return out_of_bounds, time_out

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    def _reset_idx(self, env_ids: Sequence[int] | None):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        super()._reset_idx(env_ids)

        # 기본 상태로 리셋
        q0    = self.robot.data.default_joint_pos[env_ids]
        qd0   = self.robot.data.default_joint_vel[env_ids]
        root0 = self.robot.data.default_root_state[env_ids]
        root0[:, :3] += self.scene.env_origins[env_ids]  # 각 env 원점으로 이동
        root0[:, 2]  += 0.20                             # 초기 떠주기(20cm)

        # 적용
        self.robot.write_root_pose_to_sim(root0[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(root0[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(q0, qd0, None, env_ids)

        # 기준 높이 갱신 + 퍼텐셜 초기화
        self._h_ref[env_ids] = root0[:, 2]
        if self._phi_prev is not None:
            self._phi_prev[env_ids] = 0.0  # 첫 스텝 shaping=0 보장(보상에서 mask 처리도 함)

        # 상태 버퍼 초기화
        if self._foot_bin_prev is not None:
            self._foot_bin_prev[env_ids] = 0.0
        self._last_actions = None  # 첫 스텝은 action_rate 패널티 0

    # ----------------------------- 유틸 -----------------------------
    def _body_z(self, base_quat: torch.Tensor) -> torch.Tensor:
        """(N,4[wxyz]) 쿼터니언 기준 body z-axis (N,3)"""
        n = base_quat.shape[0]
        unit_z = torch.zeros((n, 3), device=self.device, dtype=base_quat.dtype)
        unit_z[:, 2] = 1.0
        return quat_apply(base_quat, unit_z)

    def _get_root_state(self):
        """ArticulationData에서 루트 pos/quat/lin/ang을 안전하게 꺼낸다."""
        d = self.robot.data
        if hasattr(d, "root_state_w"):
            rs = d.root_state_w  # (N,13): pos[0:3], quat[3:7], lin[7:10], ang[10:13]
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
            bs = d.body_state_w  # (N, num_bodies, 13)
            rs = bs[:, 0, :]
            return rs[:, 0:3], rs[:, 3:7], rs[:, 7:10], rs[:, 10:13]
        raise RuntimeError("No root state tensors found on ArticulationData.")
