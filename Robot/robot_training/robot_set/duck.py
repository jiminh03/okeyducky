# source/duck_train_lab/robots/duck.py
from isaaclab.assets.articulation import ArticulationCfg
import isaaclab.sim as sim_utils

# -------------------------------------------------------------
# DUCK_CFG : 너의 오픈덕(양발 로봇) 설정
# - spawn.usd_path 는 네 USD 경로로 바꿔라.
# - 학습에선 EnvCfg 쪽에서 prim_path 를 replace() 로 최종 확정한다.
# -------------------------------------------------------------
DUCK_CFG = ArticulationCfg(
    # (A) 스폰해서 쓰는 경우: usd_path만 올바르게 넣으면 Lab이 env별로 복제 생성
    spawn=sim_utils.UsdFileCfg(
        usd_path="/home/bmj426/S13P31A408/Robot/robot_training/usd/duck_robot.usd",
        activate_contact_sensors=True,
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            fix_root_link=False,                 # 디버그용으로 고정하고 싶으면 True
            solver_position_iteration_count=4,   # 로컬 아티큘레이션 반복
            solver_velocity_iteration_count=0,
            sleep_threshold=0.0,
        ),
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            linear_damping=0.0,
            angular_damping=0.0,
        ),
        collision_props=sim_utils.CollisionPropertiesCfg(
            contact_offset=0.005,
            rest_offset=0.001,
        ),
    ),

    # (B) 초기 자세(라디안) — 안정 서기 포즈
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.25),   # 필요시 수정
        joint_pos={
            # 왼쪽 다리
            "dof_left_hip_yaw":   0.0,
            "dof_left_hip_roll":  0.0,
            "dof_left_hip_pitch": -0.20,
            "dof_left_knee":       0.50,
            "dof_left_ankle":     -0.10,
            # 오른쪽 다리
            "dof_right_hip_yaw":   0.0,
            "dof_right_hip_roll":  0.0,
            "dof_right_hip_pitch": -0.20,
            "dof_right_knee":       0.50,
            "dof_right_ankle":     -0.10,
            # 학습 제외 관절(고정 또는 약한 홀드)
            "dof_neck_pitch": 0.0,
            "dof_head_pitch": 0.0,
            "dof_head_yaw":   0.0,
            "dof_head_roll":  0.0,
            "fix_left_antenna":  0.0,
            "fix_right_antenna": 0.0,
        },
    ),

    # (C) 액추에이터/드라이브 — FEETECH STS3215 30 kg·cm ≈ 2.9 N·m 기준
    actuators={
        # 공통: position-PD, effort_limit(=max_force) 2.9 N·m
        "legs": {
            "type": "position",
            # 관절별 튜닝: 정규식 매칭 순서대로 적용된다.
            "stiffness": {
                "dof_.*hip_pitch": 10.0,
                "dof_.*knee":      11.0,
                "dof_.*ankle":      8.0,
                "dof_.*hip_yaw":    6.0,
                "dof_.*hip_roll":   7.0,
                ".*":               8.0,   # fallback
            },
            "damping": {
                "dof_.*hip_pitch": 2.0,
                "dof_.*knee":      2.2,
                "dof_.*ankle":     1.6,
                "dof_.*hip_yaw":   1.2,
                "dof_.*hip_roll":  1.4,
                ".*":              1.5,   # fallback
            },
            "effort_limit": {
                ".*": 2.9   # N·m (STS3215 한계토크)
            },
        },
        # 머리/목은 약한 홀드(학습 제외)
        "head": {
            "type": "position",
            "stiffness": {"dof_head_.*": 2.0, "dof_neck_.*": 2.0},
            "damping":   {"dof_head_.*": 0.4, "dof_neck_.*": 0.4},
            "effort_limit": {"dof_head_.*": 1.0, "dof_neck_.*": 1.0},
        },
        # 안테나는 구동하지 않음(가능하면 USD에서 Fixed Joint)
        "antenna": {
            "type": "position",
            "stiffness": {"fix_.*antenna": 0.0},
            "damping":   {"fix_.*antenna": 0.0},
            "effort_limit": {"fix_.*antenna": 0.0},
        },
    },

    # (D) 조인트 리미트 근처에서 너무 딱딱해지지 않도록 약간 여유
    soft_joint_pos_limit_factor=0.95,
)

