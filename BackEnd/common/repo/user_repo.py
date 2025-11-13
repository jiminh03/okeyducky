from fastapi import Depends
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # ⬅️ [추가] Eager Loading

from common.models.robot_models import Robot
from common.modules.db_instance import db

from common.models.user_models import Parent, Child # ⬅️ [변경] Parent, Child 둘 다 임포트
from common.schemas.user_schema import *

from common.exceptions import *


class ParentRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_parent(self, parent: ParentRegisterRequest) -> ParentInfoResponse:
        """
        Parent를 생성하고 'ParentInfoResponse' DTO를 반환합니다.
        """
        try:
            new_parent = Parent(
                parent_name=parent.parent_name,
                email=parent.email,
                password_hash=parent.password, # (참고) Service에서 해시된 비밀번호를 전달해야 함
            )
            self.session.add(new_parent)
            await self.session.commit()
            await self.session.refresh(new_parent)

            # ⬇️ [변경] SQLModel -> Pydantic DTO로 변환
            return ParentInfoResponse.model_validate(new_parent)

        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(
                detail=f"이메일 {parent.email}은(는) 이미 사용 중입니다."
            ) from e
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def get_parent_by_email(self, email: str) -> Optional[ParentInfoResponse]:
        """
        [최적화] email로 'ParentInfoResponse' DTO에 필요한 필드만 조회합니다.
        """
        try:
            statement = select(
                Parent.parent_id, Parent.parent_name, Parent.email
            ).where(Parent.email == email)

            result = await self.session.execute(statement)
            row = result.mappings().one_or_none()

            return ParentInfoResponse.model_validate(row) if row else None

        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def get_parent_pw_by_email(self, email: str) -> Optional[str]:
        try:
            statement = select(Parent.password_hash).where(Parent.email == email)
            result = await self.session.execute(statement)
            password_hash = result.scalar_one_or_none()
            return password_hash
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def get_parent_by_id(self, parent_id: int) -> Optional[ParentInfoResponse]:
        """
        [최적화] ID로 'ParentInfoResponse' DTO에 필요한 필드만 조회합니다.
        """
        try:
            statement = select(
                Parent.parent_id, Parent.parent_name, Parent.email
            ).where(Parent.parent_id == parent_id)
            result = await self.session.execute(statement)
            row = result.mappings().one_or_none()

            return ParentInfoResponse.model_validate(row) if row else None

        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def update_parent(
        self, parent_id: int, parent_update: ParentUpdateRequest
    ) -> Optional[ParentInfoResponse]: # ⬅️ [변경] 반환 타입을 DTO로
        try:
            parent = await self.session.get(Parent, parent_id)
            if not parent:
                return None

            update_data = parent_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                # (참고) 'password' 필드명 불일치
                # 스키마의 'password'를 모델의 'password_hash'로 매핑
                if key == "password": 
                    setattr(parent, "password_hash", value)
                else:
                    setattr(parent, key, value)

            await self.session.commit()
            await self.session.refresh(parent)

            # ⬇️ [변경] SQLModel -> Pydantic DTO로 변환
            return ParentInfoResponse.model_validate(parent)

        except IntegrityError as e:
            await self.session.rollback()
            detail = f"Parent {parent_id} 업데이트 실패: 변경하려는 값이 제약 조건을 위반합니다."
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def delete_parent(self, parent_id: int) -> bool:
        # (변경 없음 - 'bool' 반환은 그대로 유지)
        try:
            parent = await self.session.get(Parent, parent_id)
            if not parent:
                return False

            await self.session.delete(parent)
            await self.session.commit()
            return True
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e


class ChildRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_child(self, child: ChildRegisterRequest) -> ChildInfoResponse: # ⬅️ [변경] 반환 타입을 DTO로
        try:
            new_child = Child(
                name=child.name,
                gender=child.gender,
                birth_date=child.birth_date,
                school=child.school,
                profile_img=child.profile_img,
                parent_id=child.parent_id,
            )
            self.session.add(new_child)
            await self.session.commit()
            await self.session.refresh(new_child)
            
            # ⬇️ [변경] 'child_id' 대신 'ChildInfoResponse' DTO를 반환
            # (참고: 'ChildInfoResponse'는 'serial_number'가 None으로 반환됨)
            return ChildInfoResponse.model_validate(new_child)

        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(
                detail=f"부모 ID {child.parent_id}은(는) 존재하지 않습니다."
            ) from e
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def get_child_by_id(self, child_id: int) -> Optional[ChildInfoResponse]:
        """
        [최적화] Child ID로 'ChildInfoResponse' DTO에 필요한 필드를 JOIN하여 조회합니다.
        """
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
                .join(Robot, Robot.child_id == Child.child_id, isouter=True) # ⬅️ LEFT JOIN
                .where(Child.child_id == child_id) # ⬅️ [버그 수정] Robot.child_id -> Child.child_id
            )
            result = await self.session.execute(statement)
            row = result.mappings().one_or_none()

            return ChildInfoResponse.model_validate(row) if row else None
        
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def get_children_by_parent_id(self, parent_id: int) -> List[ChildInfoResponse]:
        # (변경 없음 - 이 코드는 이미 DTO 리스트를 반환하도록 작성되어 있습니다)
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
                .join(Robot, Child.child_id == Robot.child_id, isouter=True)
                .where(Child.parent_id == parent_id)
            )
            result = await self.session.execute(statement)
            rows = result.mappings().all()

            children_list = [ChildInfoResponse.model_validate(row) for row in rows]
            
            return children_list
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def update_child(
        self, child_id: int, child_update: ChildUpdateRequest
    ) -> Optional[ChildInfoResponse]: # ⬅️ [변경] 반환 타입을 DTO로
        try:
            child = await self.session.get(Child, child_id)
            if not child:
                return None

            update_data = child_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(child, key, value)

            await self.session.commit()
            await self.session.refresh(child)
            
            # ⬇️ [변경] SQLModel -> Pydantic DTO로 변환
            # (참고: 'serial_number'를 로드하기 위해 다시 조회 필요)
            updated_child_dto = await self.get_child_by_id(child.child_id)
            return updated_child_dto
        
        except IntegrityError as e:
            await self.session.rollback()
            detail = (
                f"Child {child_id} 업데이트 실패: 존재하지 않는 Child ID일 수 있습니다."
            )
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e
