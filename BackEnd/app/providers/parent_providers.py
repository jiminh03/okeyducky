from typing import Callable, Awaitable, Optional
from fastapi import Depends

from common.schemas.user_schema import *
from common.models.user_models import *
from common.repo.user_repo import ParentRepo # (파일 위치에 따라 수정)


async def get_create_parent_service(
    repo: ParentRepo = Depends(ParentRepo),
) -> Callable[[ParentRegisterRequest], Awaitable[Parent]]:
    """
    ParentRepo.create_parent 메서드를 주입합니다.
    """
    return repo.create_parent


async def get_parent_by_email_service(
    repo: ParentRepo = Depends(ParentRepo),
) -> Callable[[str], Awaitable[Optional[Parent]]]:
    """
    ParentRepo.get_parent_by_email 메서드를 주입합니다.
    """
    return repo.get_parent_by_email


async def get_parent_by_id_service(
    repo: ParentRepo = Depends(ParentRepo),
) -> Callable[[int], Awaitable[Optional[Parent]]]:
    """
    ParentRepo.get_parent_by_id 메서드를 주입합니다.
    """
    return repo.get_parent_by_id


async def get_update_parent_service(
    repo: ParentRepo = Depends(ParentRepo),
) -> Callable[[int, ParentUpdateRequest], Awaitable[Optional[Parent]]]:
    """
    ParentRepo.update_parent 메서드를 주입합니다.
    """
    return repo.update_parent


async def get_delete_parent_service(
    repo: ParentRepo = Depends(ParentRepo),
) -> Callable[[int], Awaitable[bool]]:
    """
    ParentRepo.delete_parent 메서드를 주입합니다.
    """
    return repo.delete_parent


