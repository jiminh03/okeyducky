from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import Response
from typing import List

# --- 모든 서비스, 스키마, 예외 임포트 ---
from app.services._img_parse_service import get_image_mimetype
from app.services.child_service import *
from app.services.robot_service import *
from common.schemas.user_schema import *
from app.exceptions import *

# --- 라우터 생성 ---
router = APIRouter(
    prefix="/users/child",
    tags=["사용자 (Parent & Child)"],
    include_in_schema=True,
)

# ===================================================================
# ChildService (자녀)
# ===================================================================

@router.post("", status_code=status.HTTP_201_CREATED, summary="아이 등록 (및 로봇 연동) (R2 신규)", response_model=ChildInfoResponse)
async def register_child_endpoint(
    result: ChildInfoResponse = Depends(register_child),
):
    """
    부모 계정에 아이 정보를 등록하고, 로봇 시리얼 번호를 입력하여 아이와 로봇을 1:1로 연동합니다.
    프로필 이미지를 업로드할 수 있습니다.
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


@router.put("", summary="내 아이 정보 수정 (R2 신규)", response_model=ChildInfoResponse)
async def update_child_info_endpoint(
    updated_child: ChildInfoResponse = Depends(update_child_info),
):
    """
    내 계정에 등록된 아이의 상세 정보와 연동된 로봇 정보를 조회합니다.

    서비스: `get_child_list` (첫 번째 아이 반환)
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 404 Not Found (등록된 아이가 없음)
    """

    return updated_child


@router.get("/profile-image", summary="어린이 프로필 이미지 조회")
async def get_child_profile_image_endpoint(
    profile_img: bytes = Depends(get_child_profile_img),
):
    """
    현재 로그인한 부모가 접근 가능한 어린이의 프로필 이미지를 조회합니다.

    서비스: `profile_img`
    - (성공) 200 OK (이미지 바이너리 반환)
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 403 Forbidden (NotOwnerError)
    - (실패) 404 Not Found (이미지 없음)
    """

    if profile_img is None:
        raise ChildNotFound(detail="해당 어린이의 프로필 이미지를 찾을 수 없습니다.")

    detected_mimetype = get_image_mimetype(profile_img[:16])

    media_type = detected_mimetype or "application/octet-stream"
    
    return Response(
        content=profile_img,
        media_type=media_type
    )