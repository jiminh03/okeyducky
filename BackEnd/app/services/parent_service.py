from app.modules.crypt_module import crypt_module
from app.providers.parent_providers import *

from app.exceptions import *


async def update_parent_info(
    parent_id: int,
    parent: ParentUpdateRequest,
    update_parent_service=Depends(get_update_parent_service),
) -> ParentInfoResponse:
    """
    부모님 정보를 수정합니다.

    Args:
        parent_id (int): 수정할 부모님 ID
        parent (ParentUpdateRequest): 부모님 수정 요청 데이터
        update_parent_service (Depends, optional): 부모님 정보 수정 서비스. Defaults to Depends(get_update_parent_service).

    Raises:
        ParentNotFound: 해당 ID의 부모님을 찾을 수 없을 경우 발생

    Returns:
        ParentInfoResponse: 수정된 부모님 정보
    """
    updated_parent = await update_parent_service(parent_id, parent)
    if updated_parent is None:
        raise ParentNotFound
    return updated_parent


async def get_parent_info(
    parent_id: int,
    get_parent_by_id_service=Depends(get_parent_by_id_service),
) -> ParentInfoResponse:
    """
    부모님 정보를 가져옵니다.

    Args:
        parent_id (int): 가져올 부모님 ID
        get_parent_by_id_service (Depends, optional): ID로 부모님 정보를 가져오는 서비스. Defaults to Depends(get_parent_by_id_service).

    Raises:
        ParentNotFound: 해당 ID의 부모님을 찾을 수 없을 경우 발생

    Returns:
        ParentInfoResponse: 부모님 정보
    """
    parent = await get_parent_by_id_service(parent_id)
    if parent is None:
        raise ParentNotFound
    return parent

async def get_parent_info_by_child_id(
    child_id: int,
    get_parent_by_child_id_service=Depends(get_parent_by_child_id_service),
) -> ParentInfoResponse:
    """
    자녀 ID로 부모님 정보를 가져옵니다.

    Args:
        child_id (int): 자녀 ID
        get_parent_by_child_id_service (Depends, optional): 자녀 ID로 부모님 정보를 가져오는 서비스. Defaults to Depends(get_parent_by_child_id_service).

    Raises:
        ParentNotFound: 해당 자녀 ID로 부모님을 찾을 수 없을 경우 발생

    Returns:
        ParentInfoResponse: 부모님 정보
    """
    parent = await get_parent_by_child_id_service(child_id)
    if parent is None:
        raise ParentNotFound
    return parent