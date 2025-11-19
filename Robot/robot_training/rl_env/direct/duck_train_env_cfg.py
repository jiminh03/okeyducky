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
from isaaclab.terrains.height_field.hf_terrains_cfg import (
    HfRandomUniformTerrainCfg,
    HfPyramidSlopedTerrainCfg,
    HfDiscreteObstaclesTerrainCfg,
)

import math


# -----------------------------------------------------------------------------
# Terrain-enabled Scene
# -----------------------------------------------------------------------------
@configclass
class DuckSceneCfg(InteractiveSceneCfg):
    terrain: TerrainImporterCfg = TerrainImporterCfg(
            prim_path="/World/Terrain",          # 문자열! 콤마 금지
            terrain_type="plane",
            # terrain_generator=TerrainGeneratorCfg(
            #     seed=0,
            #     curriculum=False,
            #     size=(3.0, 3.0),
            #     border_width=0.0,
            #     num_rows=4,
            #     num_cols=4,
            #     color_scheme="none",
            #     horizontal_scale=0.1,
            #     vertical_scale=0.005,
            #     slope_threshold=0.75,
            #     sub_terrains={
            #         "random": HfRandomUniformTerrainCfg(
            #             proportion=0.35,
            #             size=(10.0, 10.0),
            #             horizontal_scale=0.1,
            #             vertical_scale=0.005,
            #             noise_range=(0.02, 0.15),
            #             noise_step=0.02,
            #         ),
            #         "pyramid": HfPyramidSlopedTerrainCfg(
            #             proportion=0.35,
            #             size=(10.0, 10.0),
            #             horizontal_scale=0.1,
            #             vertical_scale=0.005,
            #             slope_range=(0.0, 0.6),
            #             platform_width=1.0,
            #             inverted=False,
            #         ),
            #         "obstacle": HfDiscreteObstaclesTerrainCfg(
            #             proportion=0.30,
            #             size=(10.0, 10.0),
            #             horizontal_scale=0.1,
            #             vertical_scale=0.005,
            #             obstacle_height_mode="choice",
            #             platform_width=1.0,
            #             obstacle_width_range=(0.20, 0.60),
            #             obstacle_height_range=(0.02, 0.15),
            #             num_obstacles=40,
            #         ),
            #     },
            #     difficulty_range=(0.0, 1.0),
            #     use_cache=False,
            #     cache_dir="/tmp/isaaclab/terrains",
            # ),
        ) 


# -----------------------------------------------------------------------------
# Env Cfg
# -----------------------------------------------------------------------------
@configclass
class DuckTrainEnvCfg(DirectRLEnvCfg):
    # env
    decimation = 2
    episode_length_s = 5.0

    # spaces
    action_scale = 1
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

    # scene (now terrain-enabled)
    scene: DuckSceneCfg = DuckSceneCfg(
        num_envs=512,
        env_spacing=4.0,
        replicate_physics=True,
    )

    # sensors
    scene.imu = ImuCfg(
        prim_path=f"{ENV_REGEX_NS}/Robot/Open_Duck_Mini_v2/Open_Duck_Mini_v2/body_assembly",
        update_period=sim.dt,
    )

    scene.contact_forces = ContactSensorCfg(
        prim_path=f"{ENV_REGEX_NS}/Robot/Open_Duck_Mini_v2/Open_Duck_Mini_v2/foot.*$",
        update_period=0.0,
        history_length=6,
        # filter_prim_paths_expr=["/World/Terrain/.*"],  # optional filter
    )

    # DOF groups
    observe_extra_dof_names: list[str] = []
    left_leg_names  = [
        "dof_left_hip_yaw","dof_left_hip_roll","dof_left_hip_pitch",
        "dof_left_knee","dof_left_ankle"
    ]
    right_leg_names = [
        "dof_right_hip_yaw","dof_right_hip_roll","dof_right_hip_pitch",
        "dof_right_knee","dof_right_ankle"
    ]
    neck_names      = ["dof_neck_pitch"]
    head_names      = ["dof_head_pitch","dof_head_yaw","dof_head_roll"]
    passive_dof_names = ["fix_left_antenna","fix_right_antenna"]

    control_dof_names = left_leg_names + right_leg_names + neck_names + head_names
    observe_dof_names = control_dof_names + neck_names + head_names

    symmetry_pairs = [
        ("dof_left_hip_yaw","dof_right_hip_yaw"),
        ("dof_left_hip_roll","dof_right_hip_roll"),
        ("dof_left_hip_pitch","dof_right_hip_pitch"),
        ("dof_left_knee","dof_right_knee"),
        ("dof_left_ankle","dof_right_ankle"),
    ]

    # safety/termination
    default_pose = {
        "dof_left_hip_pitch": 0.0, "dof_right_hip_pitch": 0.0,
        "dof_left_knee": 0.0, "dof_right_knee": 0.0,
        "dof_left_ankle": 0.0, "dof_right_ankle": 0.0,
    }

    # reward weights (left as you had them)
    rew_alive = 0.2
    rew_w_upright = 1.0
    rew_w_vel     = 0.02
    rew_w_action_rate = 0.01
    term_max_tilt = 0.7
    term_min_base_z = 0.15

    # --- Friction randomization ranges (used by env.reset hook) ---
    friction_static_range = (0.6, 1.3)
    friction_dynamic_range = (0.5, 1.1)
    friction_combine_mode = "average"  # average/max/min/multiply