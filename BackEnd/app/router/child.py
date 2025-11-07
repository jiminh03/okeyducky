from fastapi import APIRouter, Depends, status
from typing import List

# --- 모든 서비스, 스키마, 예외 임포트 ---
from app.services.child_service import *
from common.schemas.user_schema import *
from app.exceptions import *
from app.providers.child_providers import *

# --- 라우터 생성 ---
router = APIRouter(
    prefix="/users/child",
    tags=["사용자 (Parent & Child)"],
    include_in_schema=True,
)

# ===================================================================
# ChildService (자녀)
# ===================================================================

@router.post("", status_code=status.HTTP_201_CREATED, summary="아이 등록 (및 로봇 연동) (R2 신규)")
async def register_child_endpoint(
    result: ChildInfoResponse = Depends(register_child),
):
    """
    부모 계정에 아이 정보를 등록하고, 로봇 시리얼 번호를 입력하여 아이와 로봇을 1:1로 연동합니다. (계정당 1명/1대)
    
    서비스: `register_child`
    - (성공) 201 Created
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 403 Forbidden (NotOwnerError)
    - (실패) 409 Conflict (이미 아이가 등록되어 있거나, 사용 중인 시리얼 번호)
    """
    return result


@router.get("", summary="내 아이 정보 조회 (R2 신규)")
async def get_child_info_endpoint(
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
):
    """
    내 계정에 등록된 아이의 상세 정보와 연동된 로봇 정보를 조회합니다.
    
    서비스: `get_child_list` (첫 번째 아이 반환)
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 404 Not Found (등록된 아이가 없음)
    """
    # 계정당 1명만 등록 가능하므로 리스트의 첫 번째 아이 반환
    if not child_list or len(child_list) == 0:
        raise ChildNotFound
    return child_list[0]


@router.put("", summary="내 아이 정보 수정 (R2 신규)")
async def update_child_info_endpoint(
    child: ChildUpdateRequest,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    update_child_service=Depends(get_update_child_service),
):
    """
    내 계정에 등록된 아이의 정보(이름, 성별, 생일, 학교)를 수정합니다.
    
    서비스: `update_child_info` (현재 로그인한 부모의 아이만 수정)
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 404 Not Found (등록된 아이가 없음)
    """
    # 계정당 1명만 등록 가능하므로 리스트의 첫 번째 아이의 ID 사용
    if not child_list or len(child_list) == 0:
        raise ChildNotFound
    child_id = child_list[0].child_id
    updated_child = await update_child_service(child_id, child)
    if updated_child is None:
        raise ChildNotFound
    return updated_child

