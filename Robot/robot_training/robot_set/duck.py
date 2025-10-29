# source/duck_train_lab/robots/duck.py
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg

DUCK_CFG = ArticulationCfg(
    # 로봇 스폰 설정
    spawn=sim_utils.UsdFileCfg(
        usd_path="C:/Users/SSAFY/S13P31A408/Robot/robot_training/usd/duck_robot.usd", # 로봇 usd 파일 링크
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            rigid_body_enabled=True,            # 로봇에 링크를 시뮬에 넣음
            max_linear_velocity=10.0,         # 링크 선속도 상한
            max_angular_velocity=10.0,        # 링크 각속도 상한
            max_depenetration_velocity=10.0,   # 관통 보정(밀어내기)속도 상한
            enable_gyroscopic_forces=False,     # 자이로 값 사용(속도가 느리면 사용하지 않아도 문제 없음)
            disable_gravity=False,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,       # 링크끼리 충돌 처리
            solver_position_iteration_count=8,  # 포지션값을 solver로 계산하는 횟수
            solver_velocity_iteration_count=2,  # 속도값을 solver로 계산하는 횟수
            sleep_threshold=0.005,              # 링크가 sleep(계산에서 제외)되는 임계값
            stabilization_threshold=0.001,      # 작은 노이즈 감쇠 임계값(미세한 떨림 억제)
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg( # 조인트 초기값
        joint_pos={
            "dof_left_hip_yaw":   0.0,
            "dof_left_hip_roll":  0.0,
            "dof_left_hip_pitch": 0.0,
            "dof_left_knee":       0.0,
            "dof_left_ankle":     0.0,
            "dof_right_hip_yaw":  0.0,
            "dof_right_hip_roll": 0.0,
            "dof_right_hip_pitch": 0.0,
            "dof_right_knee":      0.0,
            "dof_right_ankle":    0.0,
            "dof_neck_pitch": 0.0,
            "dof_head_pitch": 0.0,
            "dof_head_yaw":   0.0,
            "dof_head_roll":  0.0,
            "fix_left_antenna":  0.0,
            "fix_right_antenna": 0.0,
        },
        pos=(0,0,0), # 로봇 초기 위치
    ),
    actuators={ # actuator의 특성
        # 기본값(다리 전반)
        "legs_default": ImplicitActuatorCfg(
            joint_names_expr="dof_.*(hip_yaw|hip_roll|ankle)",
            stiffness=8.0,
            damping=1.5,
            effort_limit=2.9,          # N·m (STS3215 기준)
            velocity_limit=100.0,
        ),
        # 세부 튜닝은 패턴별로 별도 항목을 만들어 줍니다.
        "hip_pitch": ImplicitActuatorCfg(
            joint_names_expr="dof_.*hip_pitch",
            stiffness=10.0,
            damping=2.0,
            effort_limit=2.9,
            velocity_limit=100.0,
        ),
        "knee": ImplicitActuatorCfg(
            joint_names_expr="dof_.*knee",
            stiffness=11.0,
            damping=2.2,
            effort_limit=2.9,
            velocity_limit=100.0,
        ),
        # 머리/목은 약한 홀드
        "head_hold": ImplicitActuatorCfg(
            joint_names_expr="dof_(head|neck)_.*",
            stiffness=2.0,
            damping=0.4,
            effort_limit=1.0,
            velocity_limit=50.0,
        ),
        # 안테나는 비활성(토크 0)
        "antenna_off": ImplicitActuatorCfg(
            joint_names_expr="fix_.*antenna",
            stiffness=0.0,
            damping=0.0,
            effort_limit=0.0,
            velocity_limit=0.0,
        ),
    },
)



