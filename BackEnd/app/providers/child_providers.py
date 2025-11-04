from typing import Callable, Awaitable, List, Optional
from fastapi import Depends

from common.schemas.user_schema import *
from common.models.user_models import *
from common.repo.user_repo import ChildRepo # (파일 위치에 따라 수정)


async def get_create_child_service(
    repo: ChildRepo = Depends(ChildRepo),
) -> Callable[[ChildRegisterRequest], Awaitable[Child]]:
    """
    ChildRepo.create_child 메서드를 주입합니다.
    """
    return repo.create_child


async def get_child_by_id_service(
    repo: ChildRepo = Depends(ChildRepo),
) -> Callable[[int], Awaitable[Optional[Child]]]:
    """
    ChildRepo.get_child_by_id 메서드를 주입합니다.
    """
    return repo.get_child_by_id


async def get_children_by_parent_id_service(
    repo: ChildRepo = Depends(ChildRepo),
) -> Callable[[int], Awaitable[List[Child]]]:
    """
    ChildRepo.get_children_by_parent_id 메서드를 주입합니다.
    """
    return repo.get_children_by_parent_id


async def get_update_child_service(
    repo: ChildRepo = Depends(ChildRepo),
) -> Callable[[int, ChildUpdateRequest], Awaitable[Optional[Child]]]:
    """
    ChildRepo.update_child 메서드를 주입합니다.
    """
    return repo.update_child


# (참고) ChildRepo에 delete_child 메서드가 있다면,
# 위 패턴과 동일하게 get_delete_child_service를 추가할 수 있습니다.