from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Enum as SAEnum, Text
from sqlmodel import Field, Relationship, SQLModel

from common.models.enums import Speaker

if TYPE_CHECKING:
    from .user_models import Child


class DailyReport(SQLModel, table=True):
    report_id: Optional[int] = Field(default=None, primary_key=True)
    date: date
    daily_summary: Optional[str] = Field(default=None, sa_column=Column(Text))
    analysis_summary: Optional[str] = Field(default=None, sa_column=Column(Text))

    child_id: Optional[int] = Field(default=None, foreign_key="child.child_id")
    child: Optional["Child"] = Relationship(back_populates="daily_reports")

    dialogue_logs: List["DialogueLog"] = Relationship(back_populates="daily_report")


class DialogueLog(SQLModel, table=True):
    log_id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker: Speaker = Field(sa_column=Column(SAEnum(Speaker), nullable=False)) 
    message: str

    report_id: Optional[int] = Field(default=None, foreign_key="dailyreport.report_id")
    daily_report: Optional["DailyReport"] = Relationship(back_populates="dialogue_logs")
