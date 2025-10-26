from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user_models import Child


class DailyReport(SQLModel, table=True):
    report_id: Optional[int] = Field(default=None, primary_key=True)
    date: date
    daily_summary: str
    analysis_summary: str
    positive_keywords: str
    special_notes: str

    child_id: Optional[int] = Field(default=None, foreign_key="child.child_id")
    child: Optional["Child"] = Relationship(back_populates="daily_reports")

    dialogue_logs: List["DialogueLog"] = Relationship(back_populates="daily_report")


class DialogueLog(SQLModel, table=True):
    log_id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker: str
    message: str

    report_id: Optional[int] = Field(default=None, foreign_key="dailyreport.report_id")
    daily_report: Optional["DailyReport"] = Relationship(back_populates="dialogue_logs")
