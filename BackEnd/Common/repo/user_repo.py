from fastapi import Depends
from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

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
            raise IntegrityViolationError(detail=f"이메일 {parent.email}은(는) 이미 사용 중입니다.") from e
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"create_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e
        
    async def get_parent_by_email(self, email: str) -> Optional[Parent]:
        """
        email을 기준으로 Parent 객체 하나를 조회합니다.
        (text() 대신 select() 사용)
        """
        try:
            statement = select(Parent).where(Parent.email == email)
            
            result = await self.session.execute(statement)
            parent = result.scalar_one_or_none()
            
            return parent
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"get_parent_by_email DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e
        
    async def get_parent_by_id(self, parent_id: int) -> Optional[Parent]: 
        try:
            parent = await self.session.get(Parent, parent_id)
            
            return parent
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"get_parent_by_id DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e
        
    async def update_parent(
        self, parent_id: int, parent_update: ParentUpdateRequest
    ) -> Optional[Parent]:
        try:
            parent = await self.get_parent_by_id(parent_id)
            if not parent:
                return None

            if parent_update.parent_name is not None:
                parent.parent_name = parent_update.parent_name
            if parent_update.password is not None:
                parent.password_hash = parent_update.password

            await self.session.commit()
            await self.session.refresh(parent)
            return parent
        except IntegrityError as e:
            await self.session.rollback()
            detail = f"Parent {parent_id} 업데이트 실패: 변경하려는 값이 제약 조건을 위반합니다 (예: 이메일 중복)."
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"update_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e
        
    async def delete_parent(self, parent_id: int) -> bool:
        try:
            parent = await self.get_parent_by_id(parent_id)
            if not parent:
                return False

            await self.session.delete(parent)
            await self.session.commit()
            return True
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"delete_parent DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e


class ChildRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_child(self, child: ChildRegisterRequest) -> Child:
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
            return new_child
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(detail=f"부모 ID {child.parent_id}은(는) 존재하지 않습니다.") from e
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"create_child DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_child_by_id(self, child_id: int) -> Optional[Child]:
        try:
            child = await self.session.get(Child, child_id)
            return child
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"get_child_by_id DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e
        
    async def get_children_by_parent_id(self, parent_id: int) -> List[Child]:
        try:
            statement = select(Child).where(Child.parent_id == parent_id)
            result = await self.session.execute(statement)
            children = result.scalars().all()
            return children
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"get_children_by_parent_id DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def update_child(self, child_id: int, child_update: ChildUpdateRequest) -> Optional[Child]:
        try:
            child = await self.get_child_by_id(child_id) # .get()은 Child 객체를 반환합니다.
            if not child:
                return None

            # Pydantic 모델을 사용하여 None이 아닌 필드만 업데이트
            update_data = child_update.model_dump(exclude_unset=True) # exclude_unset=True가 더 안전합니다
            for key, value in update_data.items():
                setattr(child, key, value)
            
            await self.session.commit()
            await self.session.refresh(child)
            return child
        except IntegrityError as e:
            await self.session.rollback()
            detail = f"Child {child_id} 업데이트 실패: 존재하지 않는 Child ID일 수 있습니다."
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            #log.error(f"update_child DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e
