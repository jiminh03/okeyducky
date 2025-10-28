from fastapi import Depends
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from common.modules.database import get_session

from common.models.robot_models import *
from common.schemas.robot_schema import *


class RobotRepo:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def create_robot(self, robot: RobotRegisterRequest) -> RobotInfoResponse:
        new_robot = Robot(
            serial_number=robot.serial_number,
            child_id=robot.child_id,
        )
        self.session.add(new_robot)
        await self.session.commit()
        await self.session.refresh(new_robot)
        return new_robot

    async def get_robot_by_serial_number(
        self, serial_number: str
    ) -> Optional[RobotInfoResponse]:
        query = text("SELECT * FROM Robot WHERE serial_number = :serial_number")
        result = await self.session.execute(query, {"serial_number": serial_number})
        robot = result.scalar_one_or_none()
        return robot

    async def get_robot_by_id(self, robot_id: int) -> Optional[RobotInfoResponse]:
        query = text("SELECT * FROM Robot WHERE robot_id = :robot_id")
        result = await self.session.execute(query, {"robot_id": robot_id})
        robot = result.scalar_one_or_none()
        return robot

    async def get_robot_by_child_id(self, child_id: int) -> Optional[RobotInfoResponse]:
        query = text("SELECT * FROM Robot WHERE child_id = :child_id")
        result = await self.session.execute(query, {"child_id": child_id})
        robot = result.scalar_one_or_none()
        return robot

    async def update_robot_child_id(
        self, robot_id: int, child_id: int
    ) -> Optional[RobotInfoResponse]:
        robot = await self.get_robot_by_id(robot_id)
        if not robot:
            return None

        robot.child_id = child_id
        await self.session.commit()
        await self.session.refresh(robot)
        return robot
