from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

# --- 모든 서비스, 스키마, 예외 임포트 ---
from app.services.auth_service import get_current_parent
from app.services.parent_service import *
from app.modules.crypt_module import crypt_module
from common.schemas.user_schema import *
from app.exceptions import *
from app.providers.parent_providers import *

# --- 라우터 생성 ---
router = APIRouter(
    prefix="/users/me",
    tags=["사용자 (Parent & Child)"],
    include_in_schema=True,
)

# ===================================================================
# ParentService (부모 정보)
# ===================================================================

@router.get("", summary="내 정보 (부모) 조회 (R1 수정)")
async def get_current_parent_endpoint(
    result: ParentInfoResponse = Depends(get_current_parent),
):
    """
    현재 로그인된 부모 계정의 정보를 조회합니다.
    
    서비스: `get_current_parent`
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    """
    return result


@router.put("", summary="내 정보 (부모) 수정 (R1 수정)")
async def update_current_parent_endpoint(
    parent: ParentUpdateRequest,
    current_parent: ParentInfoResponse = Depends(get_current_parent),
    update_parent_service=Depends(get_update_parent_service),
):
    """
    현재 로그인된 부모 계정의 이름 또는 비밀번호를 수정합니다.
    
    서비스: `update_parent_info` (현재 로그인한 부모의 ID 사용)
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    """
    parent_id = current_parent.parent_id
    
    # 비밀번호가 있으면 해시화
    if parent.password:
        parent.password = crypt_module.get_password_hash(parent.password)
    
    updated_parent = await update_parent_service(parent_id, parent)
    if updated_parent is None:
        raise ParentNotFound
    return updated_parent


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="회원 탈퇴")
async def delete_current_parent_endpoint(
    current_parent: ParentInfoResponse = Depends(get_current_parent),
    delete_parent_service=Depends(get_delete_parent_service),
):
    """
    현재 로그인된 부모 계정과, 연동된 아이, 로봇 정보를 모두 삭제합니다.
    
    서비스: `delete_parent` (현재 로그인한 부모의 ID 사용)
    - (성공) 204 No Content
    - (실패) 401 Unauthorized (인증 필요)
    """
    parent_id = current_parent.parent_id
    deleted = await delete_parent_service(parent_id)
    if not deleted:
        raise ParentNotFound
    return Response(status_code=status.HTTP_204_NO_CONTENT)

