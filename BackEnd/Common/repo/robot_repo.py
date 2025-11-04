from fastapi import Depends
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from common.modules.db_instance import db

from common.models.robot_models import *
from common.schemas.robot_schema import *

from common.exceptions import *


class RobotRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_robot(self, robot: RobotRegisterRequest) -> Robot:
        try:
            new_robot = Robot(
                serial_number=robot.serial_number,
                child_id=robot.child_id,
            )
            self.session.add(new_robot)
            await self.session.commit()
            await self.session.refresh(new_robot)
            return new_robot
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(detail=f"시리얼 넘버 {robot.serial_number}은(는) 이미 사용 중입니다.") from e
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"create_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_robot_by_serial_number(
        self, serial_number: str
    ) -> Optional[Robot]:
        try:
            statement = select(Robot).where(Robot.serial_number == serial_number)
            result = await self.session.execute(statement)
            robot = result.scalar_one_or_none()
            return robot
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"create_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_robot_by_id(self, robot_id: int) -> Optional[Robot]:
        try:
            robot = await self.session.get(Robot, robot_id)
            return robot
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"create_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_robot_by_child_id(self, child_id: int) -> Optional[Robot]:
        try:
            statement = select(Robot).where(Robot.child_id == child_id)
            result = await self.session.execute(statement)
            robot = result.scalar_one_or_none()
            return robot
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"create_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def update_robot_child_id(
        self, robot_id: int, child_id: int
    ) -> Optional[Robot]:
        try:
            robot = await self.session.get(Robot, robot_id)
            
            if not robot:
                return None

            robot.child_id = child_id
            await self.session.commit()
            await self.session.refresh(robot)
            return robot
        except IntegrityError as e:
            await self.session.rollback()
            detail = f"Robot {robot_id} 업데이트 실패: 존재하지 않는 Child ID {child_id}일 수 있습니다."
            #log.warning(f"IntegrityError in update_robot_child_id: {detail} | Error: {e}")
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"create_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e