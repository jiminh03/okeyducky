from datetime import date, datetime
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from common.models.enums import Speaker

class DialogueLogBase(BaseModel):
    speaker: Speaker
    message: str

class DialogueLogResponse(DialogueLogBase):
    log_id: int
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class DialogueLogCreate(DialogueLogBase):
    report_id: int

class DailyReportBase(BaseModel):
    date: date
    daily_summary: Optional[str] = None
    analysis_summary: Optional[str] = None

class DailyReportResponse(DailyReportBase):
    report_id: int
    dialogue_logs: List[DialogueLogResponse] = []

    model_config = ConfigDict(
        from_attributes=True
    )

class DailyReportCreate(DailyReportBase):
    child_id: int
    dialogue_logs: List[DialogueLogBase] = []

class DailyReportUpdateRequest(BaseModel):
    daily_summary: Optional[str] = None
    analysis_summary: Optional[str] = None
