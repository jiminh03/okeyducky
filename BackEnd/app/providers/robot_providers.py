from typing import Callable, Awaitable, Optional
from fastapi import Depends

from common.schemas.user_schema import *
from common.models.user_models import *
from common.repo.robot_repo import *


async def get_create_robot_service(
    repo: RobotRepo = Depends(RobotRepo),
) -> Callable[[RobotRegisterRequest], Awaitable[Robot]]:
    """
    RobotRepo.create_robot 메서드를 주입합니다.
    """
    return repo.create_robot


async def get_robot_by_id_service(
    repo: RobotRepo = Depends(RobotRepo),
) -> Callable[[int], Awaitable[Optional[Robot]]]:
    """
    RobotRepo.get_robot_by_id 메서드를 주입합니다.
    """
    return repo.get_robot_by_id

async def get_robot_by_serial_number_service(
    repo: RobotRepo = Depends(RobotRepo),
) -> Callable[[str], Awaitable[Optional[Robot]]]:
    """
    RobotRepo.get_robot_by_serial_number 메서드를 주입합니다.
    """
    return repo.get_robot_by_serial_number


async def get_robot_by_child_id_service(
    repo: RobotRepo = Depends(RobotRepo),
) -> Callable[[int], Awaitable[Optional[Robot]]]:
    """
    RobotRepo.get_robot_by_child_id 메서드를 주입합니다.
    """
    return repo.get_robot_by_child_id


async def get_update_robot_child_id(
    repo: RobotRepo = Depends(RobotRepo),
) -> Callable[[int, int], Awaitable[Optional[Robot]]]:
    """
    RobotRepo.update_robot_child_id 메서드를 주입합니다.
    """
    return repo.update_robot_child_id
