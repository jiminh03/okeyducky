# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from isaaclab_assets.robots.duck import DUCK_CFG

from isaaclab.assets import ArticulationCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import SimulationCfg
from isaaclab.utils import configclass


@configclass
class DuckTrainLabEnvCfg(DirectRLEnvCfg):
    # env
    decimation = 2
    episode_length_s = 5.0
    # - spaces definition
    action_space = 1
    observation_space = 4
    state_space = 0

    # simulation
    sim: SimulationCfg = SimulationCfg(dt=1 / 120, render_interval=decimation)

    # robot(s)
    robot_cfg: ArticulationCfg = DUCK_CFG.replace(prim_path="/World/Open_Duck_Mini_v2/Open_Duck_Mini_v2")

    # scene
    scene: InteractiveSceneCfg = InteractiveSceneCfg(num_envs=4096, env_spacing=4.0, replicate_physics=True)

    # custom parameters/scales
     # 학습에서 제어할 DOF (액션 순서 고정)
    control_dofs = [
        "dof_left_hip_yaw", "dof_left_hip_roll", "dof_left_hip_pitch",
        "dof_left_knee", "dof_left_ankle",
        "dof_right_hip_yaw", "dof_right_hip_roll", "dof_right_hip_pitch",
        "dof_right_knee", "dof_right_ankle",
    ]
    action_scale = 0.2          # [rad] per step (PD 타깃 델타 규모)
    target_pose = {             # 안정 서기 기준 포즈(옵션)
        "dof_left_hip_pitch": -0.20, "dof_left_knee": 0.50, "dof_left_ankle": -0.10,
        "dof_right_hip_pitch": -0.20, "dof_right_knee": 0.50, "dof_right_ankle": -0.10,
    }

    # 보상/종료 조건 스케일(예시)
    rew_w_upright = 2.0     # 직립(roll/pitch) 보상 가중치
    rew_w_pose    = 1.0     # 목표 포즈 근접 보상
    rew_w_vel     = 0.02    # 관절 속도 패널티
    rew_w_tau     = 0.002   # 토크 L2 패널티
    term_max_tilt = 0.7     # [rad] |roll| or |pitch| > 0.7 rad이면 종료
    term_min_base_z = 0.15  # [m] 베이스가 너무 낮아지면 종료
