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

from isaaclab.sensors import ImuCfg, ContactSensorCfg
from isaaclab.terrains import TerrainImporterCfg, TerrainGeneratorCfg
from isaaclab.terrains.height_field import hf_terrains_cfg as HF

import math

@configclass
class DuckTrainEnvCfg(DirectRLEnvCfg):
    # 시뮬레이션 환경 관련 설정
    # env
    decimation = 2
    episode_length_s = 5.0
    # - spaces definition
    action_scale = 1 # [N]
    action_space = 14
    observation_space = 42
    state_space = 0
    max_tilt_rad = math.pi

    # simulation
    sim: SimulationCfg = SimulationCfg(dt=1 / 120, render_interval=decimation)

    # robot(s)
    ENV_REGEX_NS = "/World/envs/env_.*"
    robot_cfg: ArticulationCfg = DUCK_CFG.replace(
            prim_path=f"{ENV_REGEX_NS}/Robot",
    )

    # scene
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=512, 
        env_spacing=4.0, 
        replicate_physics=True,
    )
    
    scene.imu = ImuCfg(
        prim_path=f"{ENV_REGEX_NS}/Robot/Open_Duck_Mini_v2/Open_Duck_Mini_v2/body_assembly",
        update_period=sim.dt,
    )

    
    scene.contact_forces = ContactSensorCfg(
        prim_path=f"{ENV_REGEX_NS}/Robot/Open_Duck_Mini_v2/Open_Duck_Mini_v2/foot.*$",
        update_period=0.0,
        history_length=6,
        #filter_prim_paths_expr=["/World/ground/GroundPlane"],
    )
    
    observe_extra_dof_names: list[str] = []
    # 학습에서 제어할 DOF (RL 정책 정하기 쉽게 그룹화 하기)
    # --- semantic DOF groups ---
    left_leg_names  = ["dof_left_hip_yaw","dof_left_hip_roll","dof_left_hip_pitch",
                       "dof_left_knee","dof_left_ankle"]
    right_leg_names = ["dof_right_hip_yaw","dof_right_hip_roll","dof_right_hip_pitch",
                       "dof_right_knee","dof_right_ankle"]
    neck_names      = ["dof_neck_pitch"]
    head_names      = ["dof_head_pitch","dof_head_yaw","dof_head_roll"]

    passive_dof_names = ["fix_left_antenna","fix_right_antenna"]  # 예시: 장식

    # 태스크 따라 선택
    control_dof_names = left_leg_names + right_leg_names + neck_names + head_names          # 보행/서기
    observe_dof_names = control_dof_names + neck_names + head_names

    # 좌우 대칭 정보(보상/정규화에 유용)
    symmetry_pairs = [
        ("dof_left_hip_yaw","dof_right_hip_yaw"),
        ("dof_left_hip_roll","dof_right_hip_roll"),
        ("dof_left_hip_pitch","dof_right_hip_pitch"),
        ("dof_left_knee","dof_right_knee"),
        ("dof_left_ankle","dof_right_ankle"),
    ]

    # 안전/리셋
    default_pose = {
        "dof_left_hip_pitch": 0.0, "dof_right_hip_pitch": 0.0,
        "dof_left_knee": 0.0, "dof_right_knee": 0.0,
        "dof_left_ankle": 0.0, "dof_right_ankle": 0.0,
        # 나머지는 0
    }

    # 보상/종료 조건 스케일(예시)
    rew_alive = 0.2
    rew_w_upright = 1.0     # 직립(roll/pitch) 보상 가중치
    # rew_w_pose    = 1.0     # 목표 포즈 근접 보상
    rew_w_vel     = 0.02    # 관절 속도 패널티
    # rew_w_tau     = 0.002   # 토크 L2 패널티
    rew_w_action_rate = 0.01
    term_max_tilt = 0.7     # [rad] |roll| or |pitch| > 0.7 rad이면 종료
    term_min_base_z = 0.15  # [m] 베이스가 너무 낮아지면 종료

