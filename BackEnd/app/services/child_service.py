from app.providers.parent_providers import *
from app.providers.child_providers import *
from app.services.auth_service import get_current_parent

from app.exceptions import *


async def register_child(
    child: ChildRegisterRequest,
    parent: Parent = Depends(get_current_parent),
    create_child_service=Depends(get_create_child_service),
) -> ChildInfoResponse:
    """
    자녀를 등록합니다.

    Args:
        child (ChildRegisterRequest): 자녀 등록 요청 데이터
        parent (Parent, optional): 현재 로그인한 부모님 정보. Defaults to Depends(get_current_parent).
        create_child_service (Depends, optional): 자녀 생성 서비스. Defaults to Depends(get_create_child_service).

    Raises:
        NotOwnerError: 자녀를 등록할 권한이 없을 경우 발생

    Returns:
        ChildInfoResponse: 등록된 자녀 정보
    """
    if child.parent_id != parent.parent_id:
        raise NotOwnerError(detail="자녀를 등록할 권한이 없습니다.")
    return await create_child_service(child)


async def get_child_list(
    parent: Parent = Depends(get_current_parent),
    get_child_list_service=Depends(get_children_by_parent_id_service),
) -> List[ChildInfoResponse]:
    """
    현재 로그인한 부모님의 자녀 목록을 가져옵니다.

    Args:
        parent (Parent, optional): 현재 로그인한 부모님 정보. Defaults to Depends(get_current_parent).
        get_child_list_service (Depends, optional): 부모 ID로 자녀 목록을 가져오는 서비스. Defaults to Depends(get_children_by_parent_id_service).

    Returns:
        List[ChildInfoResponse]: 자녀 정보 목록
    """
    return await get_child_list_service(parent.parent_id)


async def get_child_info(
    child_id: int,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_info_service=Depends(get_child_by_id_service),
    
) -> ChildInfoResponse :
    """
    특정 자녀의 정보를 가져옵니다.

    Args:
        child_id (int): 자녀 ID
        child_list (List[ChildInfoResponse], optional): 현재 로그인한 부모님의 자녀 목록. Defaults to Depends(get_child_list).
        get_child_info_service (Depends, optional): ID로 자녀 정보를 가져오는 서비스. Defaults to Depends(get_child_by_id_service).

    Raises:
        ChildNotFound: 해당 ID의 자녀를 찾을 수 없을 경우 발생
        NotOwnerError: 해당 자녀 정보에 접근할 권한이 없을 경우 발생

    Returns:
        ChildInfoResponse: 자녀 정보
    """
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
    """
    자녀 정보를 수정합니다.

    Args:
        child_id (int): 수정할 자녀 ID
        child (ChildUpdateRequest): 자녀 수정 요청 데이터
        child_list (List[ChildInfoResponse], optional): 현재 로그인한 부모님의 자녀 목록. Defaults to Depends(get_child_list).
        update_child_service (Depends, optional): 자녀 정보 수정 서비스. Defaults to Depends(get_update_child_service).
        get_child_info_service (Depends, optional): ID로 자녀 정보를 가져오는 서비스. Defaults to Depends(get_child_by_id_service).

    Raises:
        ChildNotFound: 해당 ID의 자녀를 찾을 수 없을 경우 발생
        NotOwnerError: 해당 자녀 정보에 접근할 권한이 없을 경우 발생

    Returns:
        ChildInfoResponse: 수정된 자녀 정보
    """
    child_db = await get_child_info_service(child_id)
    if child_db is None:
        raise ChildNotFound
    
    child_ids = [c.child_id for c in child_list]
    if child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")
    
    return await update_child_service(child_id, child)