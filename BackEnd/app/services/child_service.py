from app.modules.crypt_module import crypt_module
from app.providers.parent_providers import *
from app.providers.child_providers import *
from app.services.auth_service import get_current_parent


async def register_child(
    child: ChildRegisterRequest,
    create_child_service=Depends(get_create_child_service),
):
    return await create_child_service(child)


async def get_child_list(
    parent: Parent = Depends(get_current_parent),
    get_child_list_service=Depends(get_children_by_parent_id_service),
):
    return await get_child_list_service(parent)


async def get_child_info(
    child_id: int,
    get_child_info_service=Depends(get_child_by_id_service),
):
    return await get_child_info_service(child_id)


async def update_child_info(
    child_id: int,
    child: ChildUpdateRequest,
    update_child_service=Depends(get_update_child_service),
):
    return await update_child_service(child_id, child)

