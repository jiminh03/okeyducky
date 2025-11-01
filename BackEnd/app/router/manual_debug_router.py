import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import date, datetime
from typing import Dict, Any, List

# --- 모든 서비스, 스키마, 예외 임포트 ---
from app.services.auth_service import *
from app.services.parent_service import *
from app.services.child_service import *
from app.services.robot_service import *
from app.services.dialogue_service import *

from common.schemas.user_schema import *
from common.schemas.robot_schema import *
from common.schemas.dialogue_schema import *
from common.models.user_models import Parent # 'Depends' 타입 힌트용

# --- 라우터 생성 ---
router = APIRouter(
    prefix="/_manual_test",
    tags=["[Debug]  MANUAL Service Test"],
    include_in_schema=True, 
)

# ===================================================================
# 1. AuthService (인증)
# ===================================================================

@router.post("/auth/register", summary="[1] (Auth) register_parent 테스트")
async def test_register_parent(
    result: ParentInfoResponse = Depends(register_parent)
):
    """
    서비스: `register_parent`
    - (성공) 200 OK
    - (실패) 409 Conflict (Repo가 IntegrityViolationError 발생 시)
    """
    return result

@router.post("/auth/login", summary="[2] (Auth) login_parent 테스트")
async def test_login_parent(
    result: ParentInfoResponse = Depends(login_parent)
):
    """
    서비스: `login_parent`
    - (성공) 200 OK
    - (실패) 401 Unauthorized (InvalidCredentialsError)
    """
    return result

@router.get("/auth/get_current", summary="[3] (Auth) get_current_parent 테스트 (토큰 필요)")
async def test_get_current_parent(
    result: Parent = Depends(get_current_parent)
):
    """
    서비스: `get_current_parent`
    - (성공) 200 OK
    - (실패) 401 Unauthorized (InvalidTokenError 또는 토큰의 유저 없음)
    """
    return result

# ===================================================================
# 2. ParentService (부모 정보)
# ===================================================================

@router.get("/parent/{parent_id}", summary="(Parent) get_parent_info 테스트")
async def test_get_parent_info(
    result: ParentInfoResponse = Depends(get_parent_info)
):
    """
    서비스: `get_parent_info`
    - (성공) 200 OK
    - (실패) 404 Not Found (ParentNotFound)
    """
    return result

@router.patch("/parent/{parent_id}", summary="(Parent) update_parent_info 테스트")
async def test_update_parent_info(
    result: ParentInfoResponse = Depends(update_parent_info)
):
    """
    서비스: `update_parent_info`
    - (성공) 200 OK
    - (실패) 404 Not Found (ParentNotFound)
    - (주의) 이 서비스는 아직 '인가(NotOwnerError)' 로직이 빠져있습니다.
    """
    return result

# ===================================================================
# 3. ChildService (자녀)
# ===================================================================

@router.post("/child", summary="[4] (Child) register_child 테스트 (토큰 필요)")
async def test_register_child(
    result: ChildInfoResponse = Depends(register_child)
):
    """
    서비스: `register_child`
    - (성공) 200 OK
    - (실패) 403 Forbidden (NotOwnerError)
    """
    return result

@router.get("/child/list", summary="[5] (Child) get_child_list 테스트 (토큰 필요)")
async def test_get_child_list(
    result: List[ChildInfoResponse] = Depends(get_child_list)
):
    """
    서비스: `get_child_list`
    - (성공) 200 OK (빈 리스트 `[]` 포함)
    """
    return result

@router.get("/child/{child_id}", summary="[6] (Child) get_child_info 테스트 (토큰 필요)")
async def test_get_child_info(
    result: ChildInfoResponse = Depends(get_child_info)
):
    """
    서비스: `get_child_info`
    - (성공) 200 OK
    - (실패) 404 Not Found (ChildNotFound)
    - (실패) 403 Forbidden (NotOwnerError)
    """
    return result

# ===================================================================
# 4. RobotService (로봇)
# ===================================================================

@router.post("/robot", summary="[7] (Robot) register_robot 테스트 (토큰 필요)")
async def test_register_robot(
    result: RobotInfoResponse = Depends(register_robot)
):
    """
    서비스: `register_robot`
    - (성공) 200 OK
    - (실패) 404 Not Found (ChildNotFound)
    - (실패) 403 Forbidden (NotOwnerError)
    - (실패) 409 Conflict (Repo가 IntegrityViolationError 발생 시 - 시리얼 중복)
    """
    return result

@router.get("/robot", summary="[8] (Robot) get_robot_info 테스트 (토큰 필요)")
async def test_get_robot_info(
    result: RobotInfoResponse = Depends(get_robot_info)
):
    """
    서비스: `get_robot_info`
    - (성공) 200 OK
    - (실패) 404 Not Found (RobotNotFound)
    - (실패) 403 Forbidden (NotOwnerError)
    - (실패) 400 Bad Request (InvalidRequestError - ID 미제공 시)
    """
    return result

# ===================================================================
# 5. DialogueService (리포트)
# ===================================================================
# (TODO 주석에 따라 인증이 없는 엔드포인트)
@router.post("/dialogue/report", summary="(Dialogue) register_daily_report 테스트 (인증 불필요)", response_model=DailyReportResponse)
async def test_register_daily_report(
    result: DailyReportResponse = Depends(register_daily_report)
):
    return result

@router.patch("/dialogue/report/{report_id}", summary="(Dialogue) update_daily_report 테스트 (인증 불필요)")
async def test_update_daily_report(
    result: DailyReportResponse = Depends(update_daily_report)
):
    return result
    
# (인증이 필요한 엔드포인트)
@router.get("/dialogue/report/{report_id}", summary="[9] (Dialogue) get_daily_report_by_id 테스트 (토큰 필요)")
async def test_get_daily_report_by_id(
    result: DailyReportResponse = Depends(get_daily_report_by_id)
):
    """
    서비스: `get_daily_report_by_id`
    - (성공) 200 OK
    - (실패) 404 Not Found (ReportNotFound / ChildNotFound)
    - (실패) 403 Forbidden (NotOwnerError)
    """
    return result

@router.get("/dialogue/report/by-child/{child_id}", summary="[10] (Dialogue) get_daily_report_by_child_id 테스트 (토큰 필요)")
async def test_get_daily_report_by_child_id(
    start_date: date, # 쿼리 파라미터로 받음
    end_date: date,   # 쿼리 파라미터로 받음
    # 'child_id'는 경로에서 오고, start/end_date는 쿼리에서 와서
    # 서비스 함수로 '자동 주입'됩니다.
    result: List[DailyReportResponse] = Depends(get_daily_report_by_child_id)
):
    """
    서비스: `get_daily_report_by_child_id`
    - (성공) 200 OK
    - (실패) 404 Not Found (ChildNotFound)
    - (실패) 403 Forbidden (NotOwnerError)
    """
    return result