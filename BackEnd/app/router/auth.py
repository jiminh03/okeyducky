from fastapi import APIRouter, Depends, status

# --- 모든 서비스, 스키마, 예외 임포트 ---
from app.services.auth_service import *
from common.schemas.user_schema import *

# --- 라우터 생성 ---
router = APIRouter(
    prefix="/auth",
    tags=["인증 (Authentication)"],
    include_in_schema=True,
)

# ===================================================================
# AuthService (인증)
# ===================================================================

@router.post("/register", status_code=status.HTTP_201_CREATED, summary="부모(사용자) 회원 가입 (R1 수정)")
async def register_parent_endpoint(
    result: ParentInfoResponse = Depends(register_parent),
):
    """
    부모의 이름, 이메일, 비밀번호로 계정을 생성합니다. (아이 등록은 /users/child 에서 별도 수행)
    
    서비스: `register_parent`
    - (성공) 201 Created
    - (실패) 409 Conflict (이미 존재하는 이메일)
    """
    return result


@router.post("/login", summary="부모(사용자) 로그인")
async def login_parent_endpoint(
    result: LoginResponse = Depends(login_parent),
):
    """
    이메일과 비밀번호로 로그인하고 Access Token을 발급받습니다.
    
    서비스: `login_parent`
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 실패)
    """
    return result

