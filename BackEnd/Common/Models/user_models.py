from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Column, Enum as SAEnum, LargeBinary
from sqlmodel import Field, Relationship, SQLModel

from common.models.enums import Gender


class Parent(SQLModel, table=True):
    parent_id: Optional[int] = Field(default=None, primary_key=True)
    parent_name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    children: List["Child"] = Relationship(back_populates="parent")


class Child(SQLModel, table=True):
    child_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    birth_date: date
    gender: Gender = Field(sa_column=Column(SAEnum(Gender), nullable=False))
    school: Optional[str] = None
    profile_img: Optional[bytes] = Field(
        default=None, sa_column=Column(LargeBinary), description="아이 프로필 이미지"
    )

    parent_id: Optional[int] = Field(default=None, foreign_key="parent.parent_id")
    parent: Optional[Parent] = Relationship(back_populates="children")

    daily_reports: List["DailyReport"] = Relationship(back_populates="child")

    robot: Optional["Robot"] = Relationship(back_populates="child")