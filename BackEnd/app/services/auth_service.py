from app.modules.crypt_module import crypt_module
from app.providers.parent_providers import *
from app.providers.robot_providers import *

from app.exceptions import *


async def register_parent(
    parent: ParentRegisterRequest,
    create_parent_service=Depends(get_create_parent_service),
) -> ParentInfoResponse:
    """
    부모님 회원가입을 처리합니다.

    Args:
        parent (ParentRegisterRequest): 부모님 회원가입 요청 데이터
        create_parent_service (Depends): 부모님 생성 서비스

    Returns:
        ParentInfoResponse: 생성된 부모님 정보
    """
    hashed_password = crypt_module.get_password_hash(parent.password)
    parent.password = hashed_password
    return await create_parent_service(parent)


async def login_parent(
    login_request: LoginRequest,
    get_parent_by_email_service=Depends(get_parent_by_email_service),
    get_parent_pw_by_email_service=Depends(get_parent_pw_by_email_service),
) -> LoginResponse:
    """
    부모님 로그인을 처리합니다.

    Args:
        login_request (LoginRequest): 로그인 요청 데이터
        get_parent_by_email_service (Depends): 이메일로 부모님 정보를 가져오는 서비스
        get_parent_pw_by_email_service (Depends): 이메일로 부모님 비밀번호를 가져오는 서비스

    Raises:
        InvalidCredentialsError: 자격 증명이 유효하지 않을 경우 발생

    Returns:
        LoginResponse: 로그인 응답 (JWT 토큰)
    """
    parent_pw = await get_parent_pw_by_email_service(login_request.email)
    if not parent_pw or not crypt_module.verify_password(
        login_request.password, parent_pw
    ):
        raise InvalidCredentialsError
    parent = await get_parent_by_email_service(login_request.email)
    if not parent:
        raise InvalidCredentialsError
    token_data = TokenPayload.model_validate(parent.model_dump())
    token = crypt_module.create_access_jwt(token_data)
    return LoginResponse(access_token=token, token_type="bearer")


async def login_robot(
    login_request: RobotLoginRequest,
    get_robot_by_id_service=Depends(get_robot_by_id_service),
) -> LoginResponse:
    """
    로봇 로그인을 처리합니다.

    Args:
        login_request (RobotLoginRequest): 로봇 로그인 요청 데이터
        get_robot_by_id_service (Depends): ID로 로봇 정보를 가져오는 서비스

    Raises:
        InvalidCredentialsError: 자격 증명이 유효하지 않을 경우 발생

    Returns:
        LoginResponse: 로그인 응답 (JWT 토큰)
    """
    robot = await get_robot_by_id_service(login_request.robot_id)
    if not robot or robot.serial_number != login_request.serial_number:
        raise InvalidCredentialsError
    token_data = RobotTokenPayload.model_validate(robot.model_dump())
    token = crypt_module.create_access_jwt(token_data)
    return LoginResponse(access_token=token, token_type="bearer")


async def get_current_parent(
    token: str = Depends(crypt_module.oauth2_scheme),
    get_parent_by_id_service=Depends(get_parent_by_id_service),
) -> ParentInfoResponse:
    """
    현재 로그인한 부모님 정보를 가져옵니다.

    Args:
        token (str, optional): JWT 토큰. Defaults to Depends(crypt_module.oauth2_scheme).
        get_parent_by_id_service (Depends): ID로 부모님 정보를 가져오는 서비스

    Raises:
        InvalidCredentialsError: 자격 증명이 유효하지 않을 경우 발생

    Returns:
        ParentInfoResponse: 현재 로그인한 부모님 정보
    """
    payload = crypt_module.decode_jwt_payload(token)
    parsed_payload = TokenPayload.model_validate(payload)
    parent = await get_parent_by_id_service(parsed_payload.parent_id)
    if not parent:
        raise InvalidCredentialsError
    return parent


async def get_current_robot(
    token: str = Depends(crypt_module.oauth2_scheme),
    get_robot_by_id_service=Depends(get_robot_by_id_service),
) -> RobotInfoResponse:
    """
    현재 로그인한 로봇 정보를 가져옵니다.

    Args:
        token (str, optional): JWT 토큰. Defaults to Depends(crypt_module.oauth2_scheme).
        get_robot_by_id_service (Depends): ID로 로봇 정보를 가져오는 서비스

    Raises:
        InvalidCredentialsError: 자격 증명이 유효하지 않을 경우 발생

    Returns:
        RobotInfoResponse: 현재 로그인한 로봇 정보
    """
    payload = crypt_module.decode_jwt_payload(token)
    parsed_payload = RobotTokenPayload.model_validate(payload)
    robot = await get_robot_by_id_service(parsed_payload.parent_id)
    if not robot:
        raise InvalidCredentialsError
    return robot