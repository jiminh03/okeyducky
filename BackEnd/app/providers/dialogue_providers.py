from typing import Callable, Awaitable, Optional
from fastapi import Depends

from common.schemas.dialogue_schema import *
from common.models.dialogue_model import *
from common.repo.dialogue_repo import DialogueRepo

async def get_create_daily_report_service(
    repo: DialogueRepo = Depends(DialogueRepo),
) -> Callable[[DailyReportCreate], Awaitable[DailyReport]]:
    """
    DialogueRepo.create_daily_report 메서드를 주입합니다.
    """
    return repo.create_daily_report

async def get_update_daily_report_service(
    repo: DialogueRepo = Depends(DialogueRepo),
) -> Callable[[int, DailyReportUpdateRequest], Awaitable[Optional[DailyReport]]]:
    """
    DialogueRepo.update_daily_report 메서드를 주입합니다.
    """
    return repo.update_daily_report

async def get_daily_report_by_id_service(
    repo: DialogueRepo = Depends(DialogueRepo),
)-> Callable[[int], Awaitable[Optional[DailyReport]]]:
    """
    DialogueRepo.get_daily_report_by_id 메서드를 주입합니다.
    """
    return repo.get_daily_report_by_id

async def get_daily_report_by_child_id_service(
        repo: DialogueRepo = Depends(DialogueRepo),
)-> Callable[[int, date, date], Awaitable[List[DailyReport]]]:
    """
    DialogueRepo.get_daily_reports_by_child_id_and_date_range 메서드를 주입합니다.
    """
    return repo.get_daily_reports_by_child_id_and_date_range

async def get_create_dialogue_log_service(
    repo: DialogueRepo = Depends(DialogueRepo),
) -> Callable[[DialogueLogCreate], Awaitable[DialogueLog]]:
    """
    DialogueRepo.create_dialogue_log 메서드를 주입합니다.
    """
    return repo.create_dialogue_log
