import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg
import math

DUCK_CFG = ArticulationCfg(
    # (unchanged) — note: no need to modify for terrain/friction randomization
    spawn=sim_utils.UsdFileCfg(
        usd_path="C:/Users/SSAFY/S13P31A408/Robot/robot_training/usd/duck_robot.usd",
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            rigid_body_enabled=True,
            max_depenetration_velocity=1.0,
            enable_gyroscopic_forces=True,
            disable_gravity=False,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=14,
            solver_velocity_iteration_count=2,
            stabilization_threshold=0.001,
        ),
        activate_contact_sensors=True,
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        joint_pos={
            "dof_left_hip_yaw":   math.radians(8.3),
            "dof_left_hip_roll":  math.radians(0.0),
            "dof_left_hip_pitch": math.radians(62.2),
            "dof_left_knee":       math.radians(-90.4),
            "dof_left_ankle":     math.radians(24.5),
            "dof_right_hip_yaw":  math.radians(0.0),
            "dof_right_hip_roll":  math.radians(0.0),
            "dof_right_hip_pitch": math.radians(-57.3),
            "dof_right_knee":      math.radians(-89.8),
            "dof_right_ankle":    math.radians(28.4),
            "dof_neck_pitch": math.radians(-33.5),
            "dof_head_pitch": math.radians(34.9),
            "dof_head_yaw":   math.radians(0.0),
            "dof_head_roll":  math.radians(0.0),
            "fix_left_antenna":  math.radians(0.0),
            "fix_right_antenna": math.radians(0.0),
        },
        pos=(0,0,-0.05),
    ),
    actuators={
        "legs_default": ImplicitActuatorCfg(
            joint_names_expr="dof_.*(hip_yaw|hip_roll|ankle)",
            stiffness=100.0,
            damping=50.0,
            effort_limit_sim=2.9,
            velocity_limit_sim=4.0,
        ),
        "hip_pitch": ImplicitActuatorCfg(
            joint_names_expr="dof_.*hip_pitch",
            stiffness=100.0,
            damping=50.0,
            effort_limit=2.9,
            velocity_limit=4.0,
        ),
        "knee": ImplicitActuatorCfg(
            joint_names_expr="dof_.*knee",
            stiffness=100.0,
            damping=50.0,
            effort_limit_sim=2.9,
            velocity_limit_sim=4.0,
        ),
        "head_hold": ImplicitActuatorCfg(
            joint_names_expr="dof_(head|neck)_.*",
            stiffness=100.0,
            damping=50.0,
            effort_limit_sim=2.9,
            velocity_limit_sim=4.0,
        ),
        "antenna_off": ImplicitActuatorCfg(
            joint_names_expr="fix_.*antenna",
            stiffness=0.0,
            damping=0.0,
            effort_limit_sim=0.0,
            velocity_limit_sim=0.0,
        ),
    },
)