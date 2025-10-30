from fastapi import Depends
from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from common.modules.db_instance import db

from common.models.user_models import *
from common.schemas.user_schema import *


class ParentRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_parent(self, parent: ParentRegisterRequest) -> ParentInfoResponse:
        new_parent = Parent(
            parent_name=parent.parent_name,
            email=parent.email,
            password_hash=parent.password,
        )
        self.session.add(new_parent)
        await self.session.commit()
        await self.session.refresh(new_parent)
        return new_parent

    async def get_parent_by_email(self, email: str) -> Optional[ParentInfoResponse]:
        """
        email을 기준으로 Parent 객체 하나를 조회합니다.
        (text() 대신 select() 사용)
        """
        statement = select(Parent).where(Parent.email == email)
        
        result = await self.session.execute(statement)
        parent = result.scalar_one_or_none()
        
        return parent

    async def get_parent_by_id(self, parent_id: int) -> Optional[Parent]: # 반환 타입을 모델로 변경
        
        # .get()을 사용하면 (모델 클래스, ID)로 바로 객체를 가져옵니다.
        parent = await self.session.get(Parent, parent_id)
        
        return parent

    async def update_parent(
        self, parent_id: int, parent_update: ParentUpdateRequest
    ) -> Optional[ParentInfoResponse]:
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

    async def delete_parent(self, parent_id: int) -> bool:
        parent = await self.get_parent_by_id(parent_id)
        if not parent:
            return False

        await self.session.delete(parent)
        await self.session.commit()
        return True


class ChildRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_child(self, child: ChildRegisterRequest) -> ChildInfoResponse:
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

    async def get_child_by_id(self, child_id: int) -> Optional[ChildInfoResponse]:
        child = await self.session.get(Child, child_id)
        return child

    async def get_children_by_parent_id(self, parent_id: int) -> List[ChildInfoResponse]:
        statement = select(Child).where(Child.parent_id == parent_id)
        result = await self.session.execute(statement)
        children = result.scalars().all()
        return children

    async def update_child(self, child_id: int, child_update: ChildUpdateRequest) -> Optional[ChildInfoResponse]:
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
