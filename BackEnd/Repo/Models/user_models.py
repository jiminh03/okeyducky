from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

from Repo.Models.enums import Gender


class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    children: List["Child"] = Relationship(back_populates="user")


class Child(SQLModel, table=True):
    child_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    birth_date: date
    gender: Gender = Field(sa_column=Column(SAEnum(Gender), nullable=False))
    school: Optional[str] = None

    user_id: Optional[int] = Field(default=None, foreign_key="user.user_id")
    user: Optional[User] = Relationship(back_populates="children")
