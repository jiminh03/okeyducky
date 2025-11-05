# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import math

# (신규) mdp 모듈 임포트 (표준 + 커스텀 함수 모두 포함)
from . import mdp

# (신규) 표준 Action 및 Command 클래스 임포트
import isaaclab.envs.mdp.actions as mdp_actions
from isaaclab.envs.mdp.commands.commands_cfg import UniformVelocityCommandCfg

# (기존)
from isaaclab_assets.robots.duck import DUCK_CFG
from isaaclab.assets import ArticulationCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import SimulationCfg
from isaaclab.utils import configclass
from isaaclab.sensors import ImuCfg, ContactSensorCfg
from isaaclab.terrains import TerrainImporterCfg

# (신규) 텀(Term) 설정을 위한 클래스 임포트
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm

##
# 씬(Scene) 정의
##

@configclass
class DuckSceneCfg(InteractiveSceneCfg):
    """오리 로봇을 포함하는 씬 설정."""
    
    terrain: TerrainImporterCfg = TerrainImporterCfg(
        prim_path="/World/Terrain",
        terrain_type="plane",
    )
    
    robot: ArticulationCfg = DUCK_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

    # (수정) 센서를 씬 내부에 정의
    imu = ImuCfg(
        prim_path="{ENV_REGEX_NS}/Robot/Open_Duck_Mini_v2/body_assembly",
        update_period=0.0
    )
    contact_forces = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/Open_Duck_Mini_v2/foot.*$",
        update_period=0.0,
        history_length=6
    )

##
# MDP 설정
##

@configclass
class ObservationsCfg:
    """관측(Observation) 설정."""
    @configclass
    class PolicyCfg(ObsGroup):
        joint_pos: ObsTerm = ObsTerm(
            func=mdp.joint_pos,
            params={"asset_cfg": SceneEntityCfg("robot", joint_names=r"dof_.*(hip|knee|ankle|neck)")}
        )
        joint_vel: ObsTerm = ObsTerm(
            func=mdp.joint_vel,
            params={"asset_cfg": SceneEntityCfg("robot", joint_names=r"dof_.*(hip|knee|ankle|neck)")}
        )
        ang_vel: ObsTerm = ObsTerm(
            func=mdp.imu_ang_vel, 
            params={"asset_cfg": SceneEntityCfg("imu")} # sensor_cfg -> asset_cfg
        )
        lin_acc: ObsTerm = ObsTerm(
            func=mdp.imu_lin_acc, 
            params={"asset_cfg": SceneEntityCfg("imu")} # sensor_cfg -> asset_cfg
        )
        orientation: ObsTerm = ObsTerm(
            func=mdp.imu_orientation, 
            params={"asset_cfg": SceneEntityCfg("imu")} # sensor_cfg -> asset_cfg
        )
        foot_contact: ObsTerm = ObsTerm(
            func=mdp.duck_foot_contact, # 커스텀 함수
            params={"sensor_cfg": SceneEntityCfg("contact_forces")}
        )
        commands: ObsTerm = ObsTerm(
            func=mdp.generated_commands,
            params={"command_name": "velocity"}
        )

        def __post_init__(self):
            self.concatenate_terms = True
    
    policy: PolicyCfg = PolicyCfg()

@configclass
class ActionsCfg:
    """액션(Action) 설정."""
    joint_pos: mdp_actions.RelativeJointPositionActionCfg = mdp_actions.RelativeJointPositionActionCfg(
        asset_name="robot",
        joint_names=r"dof_.*(hip|knee|ankle|neck)",
        scale=1.0,
        use_zero_offset=True 
    )

@configclass
class CommandsCfg:
    """커맨드(Command) 설정."""
    velocity: UniformVelocityCommandCfg = UniformVelocityCommandCfg(
        asset_name="robot",
        ranges=UniformVelocityCommandCfg.Ranges(
            lin_vel_x=(-0.3, 0.6),
            lin_vel_y=(-0.2, 0.2),
            ang_vel_z=(-0.5, 0.5),
        ),
        resampling_time_range=(5.0, 5.0),
        debug_vis=True
    )

@configclass
class RewardsCfg:
    """보상(Reward) 설정."""
    lin_vel_tracking: RewTerm = RewTerm(func=mdp.track_lin_vel_xy_exp, weight=2.0,
        params={"std": 0.5, "command_name": "velocity", "asset_cfg": SceneEntityCfg("robot")})
    ang_vel_tracking: RewTerm = RewTerm(func=mdp.track_ang_vel_z_exp, weight=1.0,
        params={"std": 0.5, "command_name": "velocity", "asset_cfg": SceneEntityCfg("robot")})
    upright: RewTerm = RewTerm(func=mdp.flat_orientation_l2, weight=1.5, 
        params={"asset_cfg": SceneEntityCfg("robot")})
    action_rate: RewTerm = RewTerm(func=mdp.action_rate_l2, weight=-0.001)
    joint_vel: RewTerm = RewTerm(func=mdp.joint_vel_l2, weight=-0.005,
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=r"dof_.*")})

@configclass
class TerminationsCfg:
    """종료(Termination) 설정."""
    time_out: DoneTerm = DoneTerm(func=mdp.time_out, time_out=True)
    base_tilt: DoneTerm = DoneTerm(func=mdp.bad_orientation,
        params={"limit_angle": math.radians(45.0), "asset_cfg": SceneEntityCfg("robot")})
    robot_stuck: DoneTerm = DoneTerm(
        func=mdp.terminate_if_stuck_while_commanded, # 커스텀 함수
        params={
            "command_name": "velocity",
            "asset_cfg": SceneEntityCfg("robot"),
            "min_command_abs_speed_threshold": 0.1,
            "actual_velocity_threshold": 0.02,
            "duration_steps_threshold": 120,
        }
    )

@configclass
class EventCfg:
    """이벤트(Event) 및 리셋 설정."""
    
    reset_robot_joints: EventTerm = EventTerm(
        func=mdp.reset_joints_by_offset, 
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot", joint_names=r"dof_.*"),
            "position_range": (0.0, 0.0), 
            "velocity_range": (0.0, 0.0),
        },
    )
    
    reset_root_state: EventTerm = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "pose_range": {"z": (0.2, 0.2)}, 
            "velocity_range": {}
        }
    )

    # (삭제) 마찰 랜덤화 텀 제거
    
    reset_contact_buffer: EventTerm = EventTerm(
        func=mdp.reset_duck_foot_contact_hysteresis, # 커스텀 함수
        mode="reset",
        params={}
    )

##
# 환경(Environment) 설정
##

@configclass
class DuckEnvCfg(ManagerBasedRLEnvCfg):
    """오리 로봇 훈련 환경 설정."""
    
    scene: DuckSceneCfg = DuckSceneCfg(num_envs=512, env_spacing=4.0)
    
    # MDP
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    commands: CommandsCfg = CommandsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventCfg = EventCfg()

    def __post_init__(self) -> None:
        """Post initialization."""
        self.decimation = 2
        self.episode_length_s = 5.0
        self.viewer.eye = (4.0, 4.0, 4.0)
        self.viewer.lookat = (0.0, 0.0, 0.5)
        self.sim.dt = 1 / 120.0
        self.sim.render_interval = self.decimation
        
    # (삭제) 마찰 랜덤화 속성 제거