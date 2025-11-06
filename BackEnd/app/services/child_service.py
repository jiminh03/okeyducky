
from app.providers.parent_providers import *
from app.providers.child_providers import *
from app.services.auth_service import get_current_parent

from app.exceptions import *


async def register_child(
    child: ChildRegisterRequest,
    parent: Parent = Depends(get_current_parent),
    create_child_service=Depends(get_create_child_service),
) -> ChildInfoResponse:
    if child.parent_id != parent.parent_id:
        raise NotOwnerError(detail="자녀를 등록할 권한이 없습니다.")
    return await create_child_service(child)


async def get_child_list(
    parent: Parent = Depends(get_current_parent),
    get_child_list_service=Depends(get_children_by_parent_id_service),
) -> List[ChildInfoResponse]:
    return await get_child_list_service(parent.parent_id)


async def get_child_info(
    child_id: int,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_info_service=Depends(get_child_by_id_service),
    
) -> ChildInfoResponse :
    child = await get_child_info_service(child_id)
    if child is None:
        raise ChildNotFound
    
    child_ids = [child.child_id for child in child_list]
    if child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")
    
    return child


async def update_child_info(
    child_id: int,
    child: ChildUpdateRequest,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    update_child_service=Depends(get_update_child_service),
    get_child_info_service=Depends(get_child_by_id_service),
) -> ChildInfoResponse:
    child = await get_child_info_service(child_id)
    if child is None:
        raise ChildNotFound
    
    child_ids = [child.child_id for child in child_list]
    if child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")
    
    return await update_child_service(child_id, child)

