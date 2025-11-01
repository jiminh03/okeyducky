# duck_train_env.py
# SPDX-License-Identifier: BSD-3-Clause

# duck_train_env.py  (최소 동작 버전)

from __future__ import annotations
import math
from typing import Sequence

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane
from isaaclab.utils.math import sample_uniform, quat_apply

class DuckTrainEnv(DirectRLEnv):
    """Minimal env: 제어 DOF (q, qd)만 관측 / 위치제어 / 서있기 보상 / 기울기 종료"""

    cfg: "DuckTrainEnvCfg"

    def __init__(self, cfg: "DuckTrainEnvCfg", render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        # --- 인덱스/스케일/차원 초기화 ---
        # 제어할 조인트들
        self._ctrl_idx, _ = self.robot.find_joints(self.cfg.control_dof_names)
        if not self._ctrl_idx:
            raise RuntimeError(f"[duck] control_dof_names not found on stage: {self.cfg.control_dof_names}")

        # 액션 스케일 (없으면 작은 값)
        self.action_scale = float(getattr(self.cfg, "action_scale", 0.05))

        # 관측 차원: (q, qd)만 — 2 * (#ctrl)
        self.num_actions = len(self._ctrl_idx)
        self.num_obs = 2 * len(self._ctrl_idx)

        # 종료 기준(라디안): 없으면 45도
        self._max_tilt = float(getattr(self.cfg, "max_tilt_rad", math.pi / 4))

        # 캐시
        self._zeros_action = torch.zeros((self.num_envs, self.num_actions), device=self.device)
        
        # -- 센서 값 가져오기 --
        self._imu = self.scene["imu"]
        self._feet_contact = self.scene["contact_forces"]


        

    def _setup_scene(self):
        # 로봇
        self.robot = Articulation(self.cfg.robot_cfg)

        # 바닥
        spawn_ground_plane(prim_path="/World/GroundPlane", cfg=GroundPlaneCfg())

        # 씬 복제
        self.scene.clone_environments(copy_from_source=False)

        # CPU일 땐 충돌 필터
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[])

        # 등록
        self.scene.articulations["robot"] = self.robot

        # 기본 라이트(선택)
        light = sim_utils.DomeLightCfg(intensity=1500.0)
        light.func("/World/Light", light)
        
        
    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        self.actions = self.action_scale * actions.clone()

        # # _apply_action 교체
    def _apply_action(self) -> None:
        self.robot.set_joint_position_target(self.actions, joint_ids=self._ctrl_idx)

    def _get_observations(self) -> dict:
        q = self.robot.data.joint_pos[:, self._ctrl_idx]
        qd = self.robot.data.joint_vel[:, self._ctrl_idx]
        
        # ------------------ IMU ------------------
        imu_data = self._imu.data
        ang_vel_b = getattr(imu_data, "ang_vel_b")
        if ang_vel_b is None: 
            raise RuntimeError("IMU: cannot find ang_vel_b")
        lin_acc_b = getattr(imu_data, "lin_acc_b")
        if lin_acc_b is None: 
            raise RuntimeError("IMU: cannot find lin_acc_b")
        upright = getattr(imu_data, "quat_w")
        if upright is None: 
               raise RuntimeError("IMU: cannot find upright")
        
        imu_obs = []
        imu_obs.append(ang_vel_b)
        imu_obs.append(lin_acc_b) 
        imu_obs.append(upright) 
        # # ------------------ contact sensor ------------------
        contact_data = self._feet_contact.data
        net_forces_w = getattr(contact_data, "net_forces_w")
        if net_forces_w is None: 
            raise RuntimeError("ContactSensor: cannot find net_forces_w")
        if net_forces_w.dim() == 4:
            net_forces_w = net_forces_w[..., -1, :] 
        
        f_n = torch.clamp(net_forces_w[...,2], min=0.0) # 평탄화
        
        # 히스테리시스 이진화
        th_on, th_off = 3.0, 1.5 # 튜닝 포인트
        prev = getattr(self, "_foot_bin_prev", torch.zeros_like(f_n))
        foot_bin = torch.where(prev > 0.5, (f_n > th_off).float(), (f_n > th_on).float())
        self._foot_bin_prev = foot_bin
        
        # 연속 힘(정규화)
        Fmax = 50.0
        foot_force_norm = torch.clamp(f_n / Fmax, 0.0, 1.0)
        
        
        obs = torch.cat(
            [q, qd, foot_bin, foot_force_norm] + imu_obs,
            dim=-1
        )
        
       # obs = torch.cat([q, qd], dim=-1)
        
        # 수치 안정화(초기 폭주 방지)
        obs = torch.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6).clamp_(-20.0, 20.0)
        return {"policy": obs}


    def _get_rewards(self):

        # ---------- 관측에서 쓰는 센서만 ----------
        q   = self.robot.data.joint_pos[:, self._ctrl_idx]
        alive = torch.full((self.num_envs,), 0.05, device=self.device)

        qd  = self.robot.data.joint_vel[:, self._ctrl_idx]
        
        imu  = self._imu.data
        ang_b = imu.ang_vel_b

        quat = imu.quat_w
        # 쿼터니언 폭주 방지
        if torch.isnan(quat).any():
            # NaN이 하나라도 있으면, 해당 env의 쿼터니언을 기본값(0,0,0,1)으로 대체
            nan_mask = torch.isnan(quat).any(dim=1)
            default_quat = torch.tensor([0.0, 0.0, 0.0, 1.0], device=quat.device, dtype=quat.dtype)
            quat[nan_mask] = default_quat.expand_as(quat[nan_mask])

        # 접촉 (마지막 시점)
        contact_data = self._feet_contact.data
        netF = contact_data.net_forces_w
        if netF.dim() == 4:
            netF = netF[..., -1, :]
        f_n = torch.clamp(netF[..., 2], min=0.0)   # (N,F)
        # 이진 접지 (히스테리시스는 관측에서 쓰던 것 재활용 가능)
        th_on = getattr(self, "contact_on", 3.0)
        contact_bin = (f_n > th_on).float()                         # (N,F)
        # 최소 한 발 접지 보상
        r_stance = (contact_bin.max(dim=1).values)                  # (N,)

        # ---------- 리워드 항목 ----------
        # 자세 안정(roll/pitch만): IMU quaternion 기반
        quat = quat / (quat.norm(dim=1, keepdim=True) + 1e-8)
        w, x, y, z = quat[:,0], quat[:,1], quat[:,2], quat[:,3]
        # R_zz = 1 - 2*(x^2 + y^2)  → tilt_xy ~ sqrt(1 - R_zz^2) ≈ 2*sqrt(x^2+y^2)*sqrt(1 - (x^2+y^2))
        s = (x*x + y*y).clamp(0, 1)              # roll/pitch 에너지
        # 간단 근사: tilt = 2*asin(sqrt(s))  (소각 근사에서 ≈ 2*sqrt(s))
        tilt = 2.0 * torch.asin(torch.sqrt(s.clamp(max=1-1e-8)))

        r_upright = torch.exp(-4.0 * tilt*tilt)    # 0~1

        # 요 흔들림 억제: |ωz|
        p_yaw = ang_b[:, 2].abs()
        p_yaw = torch.tanh(p_yaw)                  # 포화

        # 액션 크기/변화량 패널티
        p_action = torch.tanh((self.actions ** 2).mean(dim=1))
        if hasattr(self, "_last_actions") and self._last_actions is not None:
            p_action_rate = torch.tanh(((self.actions - self._last_actions) ** 2).mean(dim=1))
        else:
            p_action_rate = torch.zeros_like(p_action)

        # (선택) 관절 속도 과다 억제
        p_qd = torch.tanh((qd.abs()).mean(dim=1) / 10.0)

        # ---------- 가중합 ----------
        w_upright   = 15.0
        w_stance    = 2.5
        w_yaw       = 0.3
        w_action    = 0.01
        w_action_rt = 0.004
        w_qd        = 0.1
        w_posture = 5.0

        reward = (
            w_upright * r_upright
            + w_stance  * r_stance
            - w_yaw     * p_yaw
            - w_action  * p_action
            - w_action_rt * p_action_rate
            - w_qd      * p_qd
            + alive
        )

        reward = torch.nan_to_num(reward, nan=-10.0, posinf=-10.0, neginf=-10.0)

        # ---------- 로깅 & 북키핑 ----------
        self.extras["r/upright_imu"] = r_upright.mean()
        self.extras["r/stance"]      = r_stance.mean()
        self.extras["p/yaw_imu"]     = p_yaw.mean()
        self.extras["p/action"]      = p_action.mean()
        self.extras["p/action_rate"] = p_action_rate.mean()
        self.extras["p/qd"]          = p_qd.mean()
        #self.extras["r/posture"]     = r_posture.mean()
        self.extras["r/alive"]       = alive.mean()

        self._last_actions = self.actions.clone()
        return reward



    # def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
    #     # 에피소드 타임아웃
    #     time_out = self.episode_length_buf >= self.max_episode_length - 1

    #     # 큰 기울기면 종료
    #     _, base_quat, _, _ = self._get_root_state()
    #     z_body = self._body_z(base_quat)
    #     # pitch/roll 근사
    #     pitch = torch.atan2(-z_body[:, 0], z_body[:, 2])
    #     roll = torch.atan2( z_body[:, 1], z_body[:, 2])
    #     out_of_bounds = (torch.abs(pitch) > self._max_tilt) | (torch.abs(roll) > self._max_tilt)

    #     return out_of_bounds, time_out

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
    # 1) 타임아웃
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        # 2) IMU 기반 기울기(roll/pitch)로 '넘어짐' 판단
        imu = self._imu.data
        quat = imu.quat_w                         # (N,4)
        # 수치 안전화 + 정규화
        quat = torch.nan_to_num(quat, nan=0.0, posinf=0.0, neginf=0.0)
        quat = quat / (quat.norm(dim=1, keepdim=True) + 1e-8)

        # tilt ≈ 2*asin(sqrt(x^2 + y^2)) : yaw 불변, roll/pitch만 캡처
        # (여기선 quat[:,1], quat[:,2]를 roll/pitch 성분으로 사용)
        x, y = quat[:, 1], quat[:, 2]
        s = (x*x + y*y).clamp(0, 1 - 1e-8)
        tilt = 2.0 * torch.asin(torch.sqrt(s))    # [rad], 0이 직립
        fall_tilt = tilt > self._max_tilt         # self._max_tilt는 기존 값(예: 20~30°)

        # 3) 접촉 기반 보조 종료: 양발 모두 장시간 떠 있으면 종료 (히스테리시스)
        contact_data = self._feet_contact.data
        netF = contact_data.net_forces_w          # (N,F,3) 또는 (N,F,T,3)
        if netF.dim() == 4:
            netF = netF[..., -1, :]
        f_n = torch.clamp(netF[..., 2], min=0.0)  # (N,F)
        th_on = getattr(self, "contact_on", 3.0)  # N
        any_contact = (f_n > th_on).any(dim=1)    # (N,)
        # 누적 미접촉 스텝 카운터
        if not hasattr(self, "_no_contact_steps"):
            self._no_contact_steps = torch.zeros_like(self.episode_length_buf)
        self._no_contact_steps = torch.where(any_contact, 
                                            torch.zeros_like(self._no_contact_steps),
                                            self._no_contact_steps + 1)
        fall_contact = self._no_contact_steps > getattr(self, "no_contact_steps_thresh", 15)

        terminated = fall_tilt | fall_contact
        return terminated, time_out

    def _reset_idx(self, env_ids: Sequence[int] | None):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        super()._reset_idx(env_ids)

        # 기본 상태로 리셋
        q0 = self.robot.data.default_joint_pos[env_ids]
        qd0 = self.robot.data.default_joint_vel[env_ids]
        root0 = self.robot.data.default_root_state[env_ids]
        root0[:, :3] += self.scene.env_origins[env_ids]  # 각 env 위치로 평행이동
        root0[:, 2] += 0.20

        # 썩소량 초기 랜덤 약간(너무 크지 않게)
        # q0[:, self._ctrl_idx] += 0.0

        self.robot.write_root_pose_to_sim(root0[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(root0[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(q0, qd0, None, env_ids)

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
        if hasattr(d, "root_state_w"):      # (N,13): pos[0:3], quat[3:7], lin[7:10], ang[10:13]
            rs = d.root_state_w
            pos = rs[:, 0:3]
            quat = rs[:, 3:7]
            lin  = rs[:, 7:10]
            ang  = rs[:, 10:13]
            return pos, quat, lin, ang
        if hasattr(d, "root_state"):
            rs = d.root_state
            pos = rs[:, 0:3]
            quat = rs[:, 3:7]
            lin  = rs[:, 7:10]
            ang  = rs[:, 10:13]
            return pos, quat, lin, ang
        if hasattr(d, "root_pose_w") and hasattr(d, "root_vel_w"):
            pos  = d.root_pose_w[:, 0:3]
            quat = d.root_pose_w[:, 3:7]
            lin  = d.root_vel_w[:, 0:3]
            ang  = d.root_vel_w[:, 3:6]
            return pos, quat, lin, ang
        if hasattr(d, "body_state_w"):
            bs = d.body_state_w  # (N, num_bodies, 13) → 루트링크를 0번으로 가정
            rs = bs[:, 0, :]
            pos = rs[:, 0:3]
            quat = rs[:, 3:7]
            lin  = rs[:, 7:10]
            ang  = rs[:, 10:13]
            return pos, quat, lin, ang
        raise RuntimeError("No root state tensors found on ArticulationData.")
