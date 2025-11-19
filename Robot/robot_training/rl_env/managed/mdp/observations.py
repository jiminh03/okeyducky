from __future__ import annotations
import torch
from typing import TYPE_CHECKING

from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv

def duck_foot_contact(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg,
    th_on: float = 3.0,
    th_off: float = 1.5,
    fmax: float = 50.0,
) -> torch.Tensor:
    """
    발바닥 접촉 여부(이력 포함)와 접촉력을 계산합니다.
    (이전 duck_train_env_cfg.py에서 이동됨)
    """
    contact_sensor = env.scene.sensors[sensor_cfg.name]
    net_forces_w = contact_sensor.data.net_forces_w
    if net_forces_w.dim() == 4:
        net_forces_w = net_forces_w[..., -1, :]
    f_n = torch.clamp(net_forces_w[..., 2], min=0.0)  # (N,F)

    # env 객체에 상태(_foot_bin_prev) 저장
    if not hasattr(env, "_foot_bin_prev"):
        env._foot_bin_prev = torch.zeros_like(f_n)

    foot_bin = torch.where(
        env._foot_bin_prev > 0.5, (f_n > th_off).float(), (f_n > th_on).float()
    )
    env._foot_bin_prev = foot_bin
    foot_force_norm = torch.clamp(f_n / fmax, 0.0, 1.0)
    
    # (N, num_feet * 2) 형태로 flatten
    return torch.cat([foot_bin, foot_force_norm], dim=-1)

def reset_duck_foot_contact_hysteresis(env: ManagerBasedRLEnv, env_ids: torch.Tensor):
    """
    duck_foot_contact 함수가 사용하는 이력(hysteresis) 버퍼를 리셋합니다.
    """
    if hasattr(env, "_foot_bin_prev"):
        env._foot_bin_prev[env_ids] = 0.0