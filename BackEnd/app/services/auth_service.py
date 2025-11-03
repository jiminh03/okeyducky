from app.modules.crypt_module import crypt_module
from app.providers.parent_providers import *
from app.providers.robot_providers import *

from app.exceptions import *

async def register_parent(
    parent: ParentRegisterRequest,
    create_parent_service=Depends(get_create_parent_service),
):
    hashed_password = crypt_module.get_password_hash(parent.password)
    parent.password = hashed_password
    return await create_parent_service(parent)


async def login_parent(
    login_request: LoginRequest,
    get_parent_by_email_service=Depends(get_parent_by_email_service),
) -> LoginResponse:
    parent = await get_parent_by_email_service(login_request.email)
    if not parent or not crypt_module.verify_password(
        login_request.password, parent.password_hash
    ):
        raise InvalidCredentialsError
    token_data = TokenPayload.model_validate(parent.model_dump())
    token = crypt_module.create_access_jwt(token_data)
    return LoginResponse(access_token=token, token_type="bearer")


async def login_robot(
    login_request: RobotLoginRequest,
    get_robot_by_id_service=Depends(get_robot_by_id_service),
):
    robot = await get_robot_by_id_service(login_request.robot_id)
    if not robot or robot.serial_number != login_request.serial_number:
        raise InvalidCredentialsError
    token_data = RobotTokenPayload.model_validate(robot.model_dump())
    token = crypt_module.create_access_jwt(token_data)
    return LoginResponse(access_token=token, token_type="bearer")

async def get_current_parent(
    token: str = Depends(crypt_module.oauth2_scheme),
    get_parent_by_id_service=Depends(get_parent_by_id_service),
):
    payload = crypt_module.decode_jwt_payload(token)
    parsed_payload = TokenPayload.model_validate(payload)
    parent = await get_parent_by_id_service(parsed_payload.parent_id)
    if not parent:
        raise InvalidCredentialsError
    return parent

async def get_current_robot(
    token: str = Depends(crypt_module.oauth2_scheme),
    get_robot_by_id_service=Depends(get_robot_by_id_service),
):
    payload = crypt_module.decode_jwt_payload(token)
    parsed_payload = RobotTokenPayload.model_validate(payload)
    robot = await get_robot_by_id_service(parsed_payload.parent_id)
    if not robot:
        raise InvalidCredentialsError
    return robot
