from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from typing import List

# --- 모든 서비스, 스키마, 예외 임포트 ---
from app.services.robot_service import *
from app.services.child_service import *
from common.schemas.robot_schema import *
from common.schemas.user_schema import *
from app.exceptions import *
from app.providers.robot_providers import *

# --- 라우터 생성 ---
router = APIRouter(
    prefix="/robot/me",
    tags=["로봇 (Device)"],
    include_in_schema=True,
)

# ===================================================================
# RobotService (로봇)
# ===================================================================

@router.get("", summary="내 로봇 정보/상태 조회")
async def get_current_robot_endpoint(
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_robot_by_child_id_service=Depends(get_robot_by_child_id_service),
):
    """
    내 아이에게 등록된 로봇의 정보(시리얼, 상태 등)를 조회합니다. (/users/child GET과 동일한 로봇 정보를 반환)
    
    서비스: `get_robot_by_child_id` (현재 로그인한 부모의 아이 ID 사용)
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 404 Not Found (등록된 로봇이 없음)
    """
    # 계정당 1명만 등록 가능하므로 리스트의 첫 번째 아이 사용
    if not child_list or len(child_list) == 0:
        raise ChildNotFound
    
    child_id = child_list[0].child_id
    robot = await get_robot_by_child_id_service(child_id)
    
    if robot is None:
        raise RobotNotFound
    
    return robot


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="로봇 연동 해제")
async def delete_current_robot_endpoint(
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_robot_by_child_id_service=Depends(get_robot_by_child_id_service),
    update_robot_child_id_service=Depends(get_update_robot_child_id),
):
    """
    내 아이에게 등록된 로봇의 연동을 해제합니다. (아이 정보는 유지됩니다)
    
    서비스: `update_robot_child_id` (로봇의 child_id를 None으로 설정)
    - (성공) 204 No Content
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 404 Not Found (등록된 로봇이 없음)
    """
    # 계정당 1명만 등록 가능하므로 리스트의 첫 번째 아이 사용
    if not child_list or len(child_list) == 0:
        raise ChildNotFound
    
    child_id = child_list[0].child_id
    
    # 현재 로봇 조회
    robot = await get_robot_by_child_id_service(child_id)
    if robot is None:
        raise RobotNotFound
    
    # 로봇의 child_id를 None으로 설정하여 연동 해제
    updated_robot = await update_robot_child_id_service(robot.robot_id, None)
    if updated_robot is None:
        raise RobotNotFound
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

