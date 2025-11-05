from __future__ import annotations
import torch
from typing import TYPE_CHECKING
from isaaclab.assets import Articulation
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv

def terminate_if_stuck_while_commanded(
    env: ManagerBasedRLEnv,
    command_name: str,
    asset_cfg: SceneEntityCfg,
    min_command_abs_speed_threshold: float = 0.1,
    actual_velocity_threshold: float = 0.02,
    duration_steps_threshold: int = 120,
    check_lin_vel: bool = True,
    check_ang_vel: bool = True
) -> torch.Tensor:
    """
    Terminates if the robot is commanded to move but shows negligible actual velocity.
    """
    robot: Articulation = env.scene[asset_cfg.name]
    num_envs = env.num_envs
    device = env.device

    target_command = env.command_manager.get_command(command_name)
    target_lin_vel_magnitude = torch.linalg.norm(target_command[:, :2], dim=1)
    target_ang_vel_abs = torch.abs(target_command[:, 2])

    is_commanded_lin_move = check_lin_vel and (target_lin_vel_magnitude > min_command_abs_speed_threshold)
    is_commanded_ang_move = check_ang_vel and (target_ang_vel_abs > min_command_abs_speed_threshold)
    
    actual_lin_vel_magnitude_xy = torch.linalg.norm(robot.data.root_lin_vel_w[:, :2], dim=1)
    actual_ang_vel_abs_z = torch.abs(robot.data.root_ang_vel_w[:, 2])

    is_not_moving_lin = check_lin_vel and (actual_lin_vel_magnitude_xy < actual_velocity_threshold)
    is_not_moving_ang = check_ang_vel and (actual_ang_vel_abs_z < actual_velocity_threshold)

    is_stuck_candidate = torch.zeros(num_envs, dtype=torch.bool, device=device)
    if check_lin_vel:
        is_stuck_candidate = is_stuck_candidate | (is_commanded_lin_move & is_not_moving_lin)
    if check_ang_vel:
        is_stuck_candidate = is_stuck_candidate | (is_commanded_ang_move & is_not_moving_ang)

    if not hasattr(env, "_stuck_while_commanded_counter"):
        env._stuck_while_commanded_counter = torch.zeros(num_envs, dtype=torch.long, device=device)

    env._stuck_while_commanded_counter[is_stuck_candidate] += 1
    env._stuck_while_commanded_counter[~is_stuck_candidate] = 0

    return env._stuck_while_commanded_counter >= duration_steps_threshold