from __future__ import annotations
import torch
import re
from typing import Sequence, TYPE_CHECKING

from isaaclab.managers import SceneEntityCfg

# USD API
from pxr import Usd, UsdPhysics, PhysxSchema, UsdGeom
import omni.usd

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv

def randomize_foot_friction(
    env: ManagerBasedRLEnv,
    env_ids: Sequence[int],
    asset_cfg: SceneEntityCfg, # API 호환성을 위해 asset_cfg를 받음
    static_friction_range: tuple[float, float],
    dynamic_friction_range: tuple[float, float],
    friction_combine_mode: str,
):
    """
    발바닥의 물리 재질 마찰 계수를 랜덤화합니다.
    (이전 duck_train_env.py에서 이동됨)
    """
    if not hasattr(env, "_stage_cache"):
        env._stage_cache = omni.usd.get_context().get_stage()
    
    stage = env._stage_cache
    robot_prim_paths = env.scene.articulations[asset_cfg.name].prim_path
    
    mu_s_min, mu_s_max = static_friction_range
    mu_d_min, mu_d_max = dynamic_friction_range

    for env_id in env_ids:
        mu_s = float(torch.rand(1).item() * (mu_s_max - mu_s_min) + mu_s_min)
        mu_d = float(torch.rand(1).item() * (mu_d_max - mu_d_min) + mu_d_min)
        
        base_path = robot_prim_paths[env_id]
        
        for p in _find_env_foot_colliders(stage, base_path):
            _bind_physics_material(stage, p, mu_s, mu_d, friction_combine_mode)

# --- 마찰 랜덤화 헬퍼 함수 ---

def _find_env_foot_colliders(stage, base_robot_path: str):
    # 경로는 로봇 USD 구조에 맞게 수정
    pat = re.compile(rf"^{re.escape(base_robot_path)}/.*foot", re.IGNORECASE)
    base_prim = stage.GetPrimAtPath(base_robot_path)
    if not base_prim.IsValid():
        return []
    colliders = []
    for prim in Usd.PrimRange(base_prim):
        p = prim.GetPath().pathString
        if pat.match(p) and prim.IsValid() and (
            prim.HasAPI(UsdPhysics.CollisionAPI) or prim.IsA(UsdGeom.Mesh)
        ):
            colliders.append(prim)
    return colliders

def _bind_physics_material(stage, prim, mu_s: float, mu_d: float, combine: str):
    if isinstance(prim, str):
        prim = stage.GetPrimAtPath(prim)
    if not prim.IsValid():
        return
    # 재질 경로가 겹치지 않도록 prim의 고유 ID를 사용
    mat_path = f"/World/Materials/{prim.GetName()}_mat_{prim.GetPrimId()}"
    mat = UsdPhysics.Material.Define(stage, mat_path)
    mat.GetStaticFrictionAttr().Set(mu_s)
    mat.GetDynamicFrictionAttr().Set(mu_d)
    mat.GetRestitutionAttr().Set(0.0)
    px = PhysxSchema.PhysxMaterialAPI.Apply(stage.GetPrimAtPath(mat_path))
    px.GetFrictionCombineModeAttr().Set(combine)
    mb = UsdPhysics.MaterialBindingAPI(prim)
    mb.GetDirectBindingRel().SetTargets([mat.GetPath()])