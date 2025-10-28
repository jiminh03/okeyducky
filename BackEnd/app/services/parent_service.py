from app.modules.crypt_module import crypt_module
from app.providers.parent_providers import *

async def update_parent_info(
    parent_id: int,
    parent: ParentUpdateRequest,
    update_parent_service=Depends(get_update_parent_service),
):
    return await update_parent_service(parent_id, parent)

async def get_parent_info(
        parent_id: int,
        get_parent_by_id_service=Depends(get_parent_by_id_service),
    ):
    return await get_parent_by_id_service(parent_id)