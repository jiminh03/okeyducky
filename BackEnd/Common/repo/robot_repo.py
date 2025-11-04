from fastapi import Depends
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from common.modules.db_instance import db

# 1. (변경 없음) SQLModel과 Pydantic 스키마를 모두 임포트합니다.
from common.models.robot_models import Robot
from common.schemas.robot_schema import RobotRegisterRequest, RobotInfoResponse

from common.exceptions import *


class RobotRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_robot(self, robot: RobotRegisterRequest) -> RobotInfoResponse:
        """
        로봇을 생성하고 'RobotInfoResponse' DTO를 반환합니다.
        """
        try:
            new_robot = Robot(
                serial_number=robot.serial_number,
                child_id=robot.child_id,
            )
            self.session.add(new_robot)
            await self.session.commit()
            await self.session.refresh(new_robot)
            
            # 2. (변경) SQLModel 객체 -> Pydantic DTO로 변환하여 반환
            return RobotInfoResponse.model_validate(new_robot)
        
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(
                detail=f"시리얼 넘버 {robot.serial_number}은(는) 이미 사용 중입니다."
            ) from e
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"create_robot DB 오류: {e}", exc_info=True)
            raise DatabaseError() from e

    async def get_robot_by_serial_number(
        self, serial_number: str
    ) -> Optional[RobotInfoResponse]:
        """
        시리얼 번호로 로봇을 조회하고 'RobotInfoResponse' DTO를 반환합니다.
        """
        try:
            statement = select(Robot).where(Robot.serial_number == serial_number)
            result = await self.session.execute(statement)
            robot = result.scalar_one_or_none() # 'Robot' (SQLModel) 객체
            
            # 3. (변경) SQLModel -> Pydantic 변환 (None일 경우 None 반환)
            return RobotInfoResponse.model_validate(robot) if robot else None
        
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_robot_by_serial_number DB 오류: {e}", exc_info=True)
            raise DatabaseError() from e

    async def get_robot_by_id(self, robot_id: int) -> Optional[RobotInfoResponse]:
        """
        ID로 로봇을 조회하고 'RobotInfoResponse' DTO를 반환합니다.
        """
        try:
            robot = await self.session.get(Robot, robot_id) # 'Robot' (SQLModel) 객체
            
            # 4. (변경) SQLModel -> Pydantic 변환
            return RobotInfoResponse.model_validate(robot) if robot else None
        
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_robot_by_id DB 오류: {e}", exc_info=True)
            raise DatabaseError() from e

    async def get_robot_by_child_id(
        self, child_id: int
    ) -> Optional[RobotInfoResponse]:
        """
        Child ID로 로봇을 조회하고 'RobotInfoResponse' DTO를 반환합니다.
        """
        try:
            statement = select(Robot).where(Robot.child_id == child_id)
            result = await self.session.execute(statement)
            robot = result.scalar_one_or_none() # 'Robot' (SQLModel) 객체
            
            # 5. (변경) SQLModel -> Pydantic 변환
            return RobotInfoResponse.model_validate(robot) if robot else None
        
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_robot_by_child_id DB 오류: {e}", exc_info=True)
            raise DatabaseError() from e

    async def update_robot_child_id(
        self, robot_id: int, child_id: Optional[int] # 6. (개선) 'None'으로 연결 해제도 가능하도록
    ) -> Optional[RobotInfoResponse]:
        """
        로봇의 Child ID를 수정하고 'RobotInfoResponse' DTO를 반환합니다.
        """
        try:
            robot = await self.session.get(Robot, robot_id)

            if not robot:
                return None

            robot.child_id = child_id
            await self.session.commit()
            await self.session.refresh(robot)
            
            # 7. (변경) SQLModel -> Pydantic 변환
            return RobotInfoResponse.model_validate(robot)
        
        except IntegrityError as e:
            await self.session.rollback()
            detail = f"Robot {robot_id} 업데이트 실패: 존재하지 않는 Child ID {child_id}일 수 있습니다."
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"update_robot_child_id DB 오류: {e}", exc_info=True)
            raise DatabaseError() from e