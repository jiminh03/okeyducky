from fastapi import Depends
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from common.modules.database import get_session

from common.models.user_models import *
from common.schemas.user_schema import *


class ParentRepo:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def create_parent(self, parent: ParentRegisterRequest) -> ParentInfoResponse:
        new_parent = Parent(
            parent_name=parent.parent_name,
            email=parent.email,
            password=parent.password,
            children=[],
        )
        self.session.add(new_parent)
        await self.session.commit()
        await self.session.refresh(new_parent)
        return new_parent

    async def get_parent_by_email(self, email: str) -> Optional[ParentInfoResponse]:
        query = text("SELECT * FROM Parent WHERE email = :email")
        result = await self.session.execute(query, {"email": email})
        parent = result.scalar_one_or_none()
        return parent

    async def get_parent_by_id(self, parent_id: int) -> Optional[ParentInfoResponse]:
        query = text("SELECT * FROM Parent WHERE parent_id = :parent_id")
        result = await self.session.execute(query, {"parent_id": parent_id})
        parent = result.scalar_one_or_none()
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
            parent.password = parent_update.password

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
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def create_child(self, child: ChildRegisterRequest) -> ChildInfoResponse:
        new_child = Child(
            name=child.name,
            gender=child.gender,
            birth_date=child.birth_date,
            school=child.school,
            parent_id=child.parent_id,
        )
        await self.session.add(new_child)
        await self.session.commit()
        await self.session.refresh(new_child)
        return new_child

    async def get_child_by_id(self, child_id: int) -> Optional[ChildInfoResponse]:
        query = text("SELECT * FROM Child WHERE child_id = :child_id")
        result = await self.session.execute(query, {"child_id": child_id})
        child = result.scalar_one_or_none()
        return child

    async def get_children_by_parent_id(self, parent_id: int) -> List[ChildInfoResponse]:
        query = text("SELECT * FROM Child WHERE parent_id = :parent_id")
        result = await self.session.execute(query, {"parent_id": parent_id})
        children = result.scalars().all()
        return children

    async def update_child(self, child_id: int, child_update: ChildUpdateRequest) -> Optional[ChildInfoResponse]:
        child = await self.get_child_by_id(child_id)
        if not child:
            return None
