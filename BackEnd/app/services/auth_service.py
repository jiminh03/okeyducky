from app.modules.crypt_module import crypt_module
from app.providers.parent_providers import *

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
):
    parent = await get_parent_by_email_service(login_request.email)
    hashed_password  = crypt_module.get_password_hash(login_request.password)
    if not parent or not crypt_module.verify_password(hashed_password, parent.password_hash):
        raise InvalidCredentialsError
    return parent

async def get_current_parent(
    token: str = Depends(crypt_module.oauth2_scheme),
    get_parent_by_id_service=Depends(get_parent_by_id_service),
):
    payload = crypt_module.decode_jwt_payload(token)
    parent = await get_parent_by_id_service(payload.parent_id)
    if not parent:
        raise InvalidCredentialsError
    return parent


