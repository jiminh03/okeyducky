from fastapi import APIRouter, Depends, File, Form, UploadFile, status
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

@router.post("", status_code=status.HTTP_201_CREATED, summary="아이 등록 (및 로봇 연동) (R2 신규)", response_model=ChildInfoResponse)
async def register_child_endpoint(
    # 1. [입력] Multipart 폼 데이터 수신
    name: str = Form(...),
    gender: Gender = Form(...), # 문자열로 오지만 Pydantic이 Enum으로 변환 시도
    birth_date: date = Form(...),
    serial_number: str = Form(...),
    school: Optional[str] = Form(None),
    
    # 2. [입력] 파일 데이터 수신 (FastAPI 전용 타입)
    profile_img: Optional[UploadFile] = File(None),
    
    # 3. [의존성] 현재 사용자 및 서비스 주입
    current_parent: Parent = Depends(get_current_parent),
):
    """
    부모 계정에 아이 정보를 등록하고, 로봇 시리얼 번호를 입력하여 아이와 로봇을 1:1로 연동합니다.
    프로필 이미지를 업로드할 수 있습니다.
    """
    
    # 4. [변환] UploadFile -> bytes (비동기 읽기)
    img_bytes = None
    if profile_img:
        img_bytes = await profile_img.read()
        # (선택 사항) 여기서 파일 크기나 타입 검증 로직을 추가할 수 있습니다.
        # if len(img_bytes) > 5 * 1024 * 1024: ...

    # 5. [조립] 서비스 계층용 순수 DTO 생성
    register_request = ChildRegisterRequest(
        name=name,
        gender=gender,
        birth_date=birth_date,
        school=school,
        profile_img=img_bytes,  # 변환된 bytes 주입
        parent_id=current_parent.parent_id,
    )

    # 6. [호출] 서비스 실행 및 결과 반환
    # (서비스는 DTO와 부모 객체만 받으면 됩니다)
    result = await register_child(register_request, current_parent)
    
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
    # 1. [입력] 수정할 데이터 (모두 Optional + Form)
    name: Optional[str] = Form(None),
    gender: Optional[Gender] = Form(None),
    birth_date: Optional[date] = Form(None),
    school: Optional[str] = Form(None),
    
    # 2. [입력] 수정할 프로필 이미지 파일
    profile_img: Optional[UploadFile] = File(None),

    # 3. [의존성]
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    update_child_service=Depends(get_update_child_service),
):
    """
    내 계정에 등록된 아이의 상세 정보와 연동된 로봇 정보를 조회합니다.
    
    서비스: `get_child_list` (첫 번째 아이 반환)
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 404 Not Found (등록된 아이가 없음)
    """
    if not child_list:
        raise ChildNotFound
    
    # 계정당 1명만 등록 가능하므로 첫 번째 아이 ID 사용
    child_id = child_list[0].child_id

    img_bytes = None
    if profile_img:
        img_bytes = await profile_img.read()

    update_request = ChildUpdateRequest(
        name=name,
        gender=gender,
        birth_date=birth_date,
        school=school,
        profile_img=img_bytes # 변환된 bytes 주입
    )

    updated_child = await update_child_service(child_id, update_request)
    
    if updated_child is None:
        raise ChildNotFound
        
    return updated_child