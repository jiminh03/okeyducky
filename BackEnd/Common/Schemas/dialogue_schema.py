from datetime import date, datetime
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

class DialogueLogBase(BaseModel):
    speaker: str
    message: str

class DialogueLogResponse(DialogueLogBase):
    log_id: int
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class DailyReportBase(BaseModel):
    date: date
    daily_summary: str
    analysis_summary: str
    positive_keywords: str
    special_notes: str

class DailyReportResponse(DailyReportBase):
    report_id: int
    dialogue_logs: List[DialogueLogResponse] = []

    model_config = ConfigDict(
        from_attributes=True
    )

class DailyReportCreate(DailyReportBase):
    child_id: int
    dialogue_logs: List[DialogueLogBase] = []

class DialogueLogCreate(DialogueLogBase):
    report_id: int
