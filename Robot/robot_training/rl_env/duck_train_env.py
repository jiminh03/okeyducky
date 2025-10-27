# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import math
import torch
from collections.abc import Sequence

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane
from isaaclab.utils.math import sample_uniform

from .duck_train_env_cfg import DuckTrainEnvCfg


class DuckTrainEnv(DirectRLEnv):
    cfg: DuckTrainEnvCfg

    def __init__(self, cfg: DuckTrainEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        
        self.action_scale = self.cfg.action_scale


        # 조인트의 위치와 속도를 가져옴
        self.joint_pos = self.duck.data.joint_pos
        self.joint_vel = self.duck.data.joint_vel



    # ---- scene ----
    def _setup_scene(self):
        self.duck = Articulation(self.cfg.robot_cfg)

        # ground
        spawn_ground_plane(prim_path="/World/ground", cfg=GroundPlaneCfg())

        # 복제
        self.scene.clone_environments(copy_from_source=False)
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[])

        # 등록
        self.scene.articulations["robot"] = self.robot

        # 조명
        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
        light_cfg.func("/World/Light", light_cfg)

        # 데이터 뷰
        self.joint_pos = self.robot.data.joint_pos
        self.joint_vel = self.robot.data.joint_vel

        # DOF 인덱스 매핑
        names = self.robot.dof_names
        def idx_of(nlist):
            return torch.tensor([names.index(n) for n in nlist if n in names], device=self.device, dtype=torch.long)
 
        self._ctrl_idx = idx_of(self.cfg.control_dof_names)
        self._obs_idx_extra = idx_of(self.cfg.observe_extra_dof_names)

        # 액션/관측 차원 업데이트(선택)
        self.num_actions = int(self._ctrl_idx.numel())
        self.num_obs = 2 + 3 + self.num_actions*2 + int(self._obs_idx_extra.numel())*2
        # 2 (roll,pitch) + 3 (base ang vel xyz) + q_rel/dq for control + q_rel/dq for extra

    # ---- step hooks ----
    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        # [-1,1] → 증분 목표(rad)
        self.actions = actions.clamp(-1.0, 1.0)

    def _apply_action(self) -> None:
        # 현재 q, 기본자세 q0
        q = self.joint_pos
        q0 = self.robot.data.default_joint_pos

        # 증분 목표 생성
        target = q.clone()
        target[:, self._ctrl_idx] = (q[:, self._ctrl_idx]
                                     + self.actions * self.cfg.action_scale)

        # 조인트 리미트로 클램프
        jmin = self.robot.data.joint_pos_limits[..., 0]
        jmax = self.robot.data.joint_pos_limits[..., 1]
        target = torch.max(torch.min(target, jmax), jmin)

        # 위치 드라이브 목표로 적용 (로봇 cfg에서 position actuator 사용 가정)
        self.robot.set_joint_position_target(target)

    # ---- obs/reward/done/reset ----
    def _get_observations(self) -> dict:
        # 베이스 roll/pitch 추출(쿼터니언 → body-up 기준)
        base_quat = self.robot.data.root_quat
        up_world = torch.tensor([0, 0, 1], device=self.device, dtype=base_quat.dtype).repeat(base_quat.shape[0], 1)
        # body z축(로컬 up)을 월드로
        body_z_world = quat_apply(base_quat, torch.tensor([0,0,1], device=self.device, dtype=base_quat.dtype))
        # 롤/피치 근사
        pitch = torch.atan2(-body_z_world[:,0], body_z_world[:,2])
        roll  = torch.atan2( body_z_world[:,1], body_z_world[:,2])

        base_ang_vel = self.robot.data.root_ang_vel  # (N,3)

        q = self.joint_pos
        dq = self.joint_vel
        q0 = self.robot.data.default_joint_pos

        q_rel_ctrl = (q[:, self._ctrl_idx] - q0[:, self._ctrl_idx])
        dq_ctrl    = dq[:, self._ctrl_idx]

        if self._obs_idx_extra.numel() > 0:
            q_rel_extra = (q[:, self._obs_idx_extra] - q0[:, self._obs_idx_extra])
            dq_extra    = dq[:, self._obs_idx_extra]
            obs = torch.cat([roll.unsqueeze(1), pitch.unsqueeze(1),
                             base_ang_vel,
                             q_rel_ctrl, dq_ctrl,
                             q_rel_extra, dq_extra], dim=-1)
        else:
            obs = torch.cat([roll.unsqueeze(1), pitch.unsqueeze(1),
                             base_ang_vel,
                             q_rel_ctrl, dq_ctrl], dim=-1)

        return {"policy": obs}

    def _get_rewards(self) -> torch.Tensor:
        # 업라이트(몸체 z축과 월드 z축 코사인)
        base_quat = self.robot.data.root_quat
        body_z_world = quat_apply(base_quat, torch.tensor([0,0,1], device=self.device, dtype=base_quat.dtype))
        upright = body_z_world[:, 2].clamp(0.0, 1.0)  # 1=완전 직립

        # 토크/액션 패널티 (로봇 핸들이 최근 적용한 명령/토크를 노출한다면 사용)
        # 여기선 액션 변화율만 사용
        if not hasattr(self, "_prev_actions"):
            self._prev_actions = torch.zeros_like(self.actions)
        action_rate = (self.actions - self._prev_actions)
        self._prev_actions = self.actions.clone()

        # 합성
        rew = (
            self.cfg.rew_alive
            + self.cfg.rew_upright * upright
            + self.cfg.rew_joint_vel * torch.sum(torch.square(self.joint_vel[:, self._ctrl_idx]), dim=-1)
            + self.cfg.rew_action_rate * torch.sum(torch.square(action_rate), dim=-1)
        )
        return rew

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        # 넘어짐/타임아웃
        base_pos = self.robot.data.root_pos
        base_quat = self.robot.data.root_quat
        body_z_world = quat_apply(base_quat, torch.tensor([0,0,1], device=self.device, dtype=base_quat.dtype))
        pitch = torch.atan2(-body_z_world[:,0], body_z_world[:,2])
        roll  = torch.atan2( body_z_world[:,1],  body_z_world[:,2])

        tipped = (torch.abs(pitch) > self.cfg.max_tilt_rad) | (torch.abs(roll) > self.cfg.max_tilt_rad)
        too_low = base_pos[:, 2] < self.cfg.min_base_height

        out_of_bounds = tipped | too_low
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        return out_of_bounds, time_out

    def _reset_idx(self, env_ids: Sequence[int] | None):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        super()._reset_idx(env_ids)

        # 기본 상태
        q0 = self.robot.data.default_joint_pos[env_ids]
        dq0 = self.robot.data.default_joint_vel[env_ids]

        # 작은 노이즈
        q0[:, self._ctrl_idx] += (torch.rand_like(q0[:, self._ctrl_idx]) - 0.5) * 0.05  # ±0.025 rad
        dq0[:, self._ctrl_idx] = 0.0

        root0 = self.robot.data.default_root_state[env_ids]
        root0[:, :3] += self.scene.env_origins[env_ids]  # 배치 오프셋

        # 버퍼/시뮬에 기록
        self.joint_pos[env_ids] = q0
        self.joint_vel[env_ids] = dq0
        self.robot.write_root_pose_to_sim(root0[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(root0[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(q0, dq0, None, env_ids)
        # 액션 버퍼 리셋
        if hasattr(self, "_prev_actions"):
            self._prev_actions[env_ids] =  torch.zeros_like(self._prev_actions[env_ids])
