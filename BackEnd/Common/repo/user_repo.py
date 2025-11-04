from fastapi import Depends
from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from common.models.robot_models import Robot
from common.modules.db_instance import db

from common.models.user_models import *
from common.schemas.user_schema import *

from common.exceptions import *


class ParentRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_parent(self, parent: ParentRegisterRequest) -> Parent:
        try:
            new_parent = Parent(
                parent_name=parent.parent_name,
                email=parent.email,
                password_hash=parent.password,
            )
            self.session.add(new_parent)
            await self.session.commit()
            await self.session.refresh(new_parent)
            return new_parent
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(
                detail=f"이메일 {parent.email}은(는) 이미 사용 중입니다."
            ) from e
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"create_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_parent_by_email(self, email: str) -> Optional[ParentInfoResponse]:
        """
        email을 기준으로 Parent 객체 하나를 조회합니다.
        (text() 대신 select() 사용)
        """
        try:
            statement = select(
                Parent.parent_id, Parent.parent_name, Parent.email
            ).where(Parent.email == email)

            result = await self.session.execute(statement)
            row = result.mappings().one_or_none()  # dict로 데이터 획득

            if row:
                return ParentInfoResponse.model_validate(row)
            return None
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_parent_by_email DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_parent_by_id(self, parent_id: int) -> Optional[ParentInfoResponse]:
        try:
            statement = select(
                Parent.parent_id, Parent.parent_name, Parent.email
            ).where(Parent.parent_id == parent_id)
            result = await self.session.execute(statement)
            row = result.mappings().one_or_none()  # dict로 데이터 획득

            if row:
                return ParentInfoResponse.model_validate(row)
            return None
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_parent_by_id DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def update_parent(
        self, parent_id: int, parent_update: ParentUpdateRequest
    ) -> Optional[Parent]:
        try:
            parent = await self.session.get(Parent, parent_id)
            if not parent:
                return None

            # 'ChildRepo.update_child'와 동일한 방식으로 변경
            update_data = parent_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(parent, key, value)

            # (참고) email 필드도 업데이트하는 경우, IntegrityError 처리가 필요할 수 있습니다.
            # 현재 스키마(ParentUpdateRequest)에는 email이 없으므로 문제는 없습니다.

            await self.session.commit()
            await self.session.refresh(parent)
            return parent
        except IntegrityError as e:
            await self.session.rollback()
            detail = f"Parent {parent_id} 업데이트 실패: 변경하려는 값이 제약 조건을 위반합니다 (예: 이메일 중복)."
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"update_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def delete_parent(self, parent_id: int) -> bool:
        try:
            parent = await self.session.get(Parent, parent_id)
            if not parent:
                return False

            await self.session.delete(parent)
            await self.session.commit()
            return True
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"delete_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e


class ChildRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_child(self, child: ChildRegisterRequest) -> int:
        try:
            new_child = Child(
                name=child.name,
                gender=child.gender,
                birth_date=child.birth_date,
                school=child.school,
                parent_id=child.parent_id,
            )
            self.session.add(new_child)
            await self.session.commit()
            await self.session.refresh(new_child)
            return new_child.child_id

        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(
                detail=f"부모 ID {child.parent_id}은(는) 존재하지 않습니다."
            ) from e
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"create_child DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_child_by_id(self, child_id: int) -> Optional[ChildInfoResponse]:
        try:
            statement = (
                select(Child.child_id, Child.name, Child.gender, Child.birth_date, Child.school, Robot.serial_number)
                .join(Robot, Robot.child_id == Child.child_id)
                .where(Robot.child_id == child_id)
            )
            result = await self.session.execute(statement)
            row = result.mappings().one_or_none()  # dict로 데이터 획득

            if row:
                return ChildInfoResponse.model_validate(row)
            return None
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_child_by_id DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_children_by_parent_id(self, parent_id: int) -> List[ChildInfoResponse]:
        try:
            statement = (
                select(
                    Child.child_id,
                    Child.name,
                    Child.gender,
                    Child.birth_date,
                    Child.school,
                    Robot.serial_number
                )
                # 4. isouter=True (LEFT JOIN)를 사용해 로봇이 없는 자녀도 포함합니다.
                .join(Robot, Child.child_id == Robot.child_id, isouter=True)
                .where(Child.parent_id == parent_id)
            )
            result = await self.session.execute(statement)
            rows = result.mappings().all()  # dict로 데이터 획득

            children_list = [ChildInfoResponse.model_validate(row) for row in rows]
            
            return children_list
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_children_by_parent_id DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def update_child(
        self, child_id: int, child_update: ChildUpdateRequest
    ) -> Optional[Child]:
        try:
            child = await self.session.get(Child, child_id)
            if not child:
                return None

            # Pydantic 모델을 사용하여 None이 아닌 필드만 업데이트
            update_data = child_update.model_dump(
                exclude_unset=True
            )  # exclude_unset=True가 더 안전합니다
            for key, value in update_data.items():
                setattr(child, key, value)

            await self.session.commit()
            await self.session.refresh(child)
            return child
        except IntegrityError as e:
            await self.session.rollback()
            detail = (
                f"Child {child_id} 업데이트 실패: 존재하지 않는 Child ID일 수 있습니다."
            )
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"update_child DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e
