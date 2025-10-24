from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user_models import Child


class Robot(SQLModel, table=True):
    robot_id: Optional[int] = Field(default=None, primary_key=True)
    serial_number: str = Field(unique=True, index=True)
    status: str

    child_id: Optional[int] = Field(default=None, foreign_key="child.child_id")
    child: Optional["Child"] = Relationship(back_populates="robot")
