from ai.providers.dialogue_providers import *
from fastapi import Depends  # Depends를 임포트해야 합니다.
from typing import List
from datetime import date

from ai.modules.dialogue_func import _get_daily_report_id


async def update_daily_report(
    child_id: int,
    report: DailyReportUpdateRequest,
    update_daily_report_service=Depends(get_update_daily_report_service),
    # 1. _get_daily_report_id를 호출하는 대신, 매개변수로 주입받습니다.
    daily_report_id: int = Depends(_get_daily_report_id),
) -> DailyReportResponse:
    """
    일일 리포트를 수정합니다.
    (이하 Docstring 생략)
    """
    # 2. 이 줄을 삭제합니다. (daily_report_id는 이미 위에서 주입받음)
    # daily_report_id = await _get_daily_report_id(child_id)
    return await update_daily_report_service(daily_report_id, report)


async def register_dialogue_log(
    log: DialogueLogBase,
    child_id: int,
    create_dialogue_log_service=Depends(get_create_dialogue_log_service),
    # 1. _get_daily_report_id를 호출하는 대신, 매개변수로 주입받습니다.
    daily_report_id: int = Depends(_get_daily_report_id),
) -> DialogueLogResponse:

    # 2. 이 줄을 삭제합니다.
    # daily_report_id = await _get_daily_report_id(child_id)
    log_with_report_id = DialogueLogCreate(
        speaker=log.speaker, message=log.message, report_id=daily_report_id
    )

    return await create_dialogue_log_service(log_with_report_id)


async def register_parent_dialogue(
    request_data: ChatRequest,
    child_id: int,
    create_dialogue_log_service=Depends(get_create_dialogue_log_service),
    # 1. _get_daily_report_id를 호출하는 대신, 매개변수로 주입받습니다.
    daily_report_id: int = Depends(_get_daily_report_id),
) -> DialogueLogResponse:

    # 2. 이 줄을 삭제합니다. (오류가 발생했던 원인)
    # daily_report_id = await _get_daily_report_id(child_id)
    log_with_report_id = DialogueLogCreate(
        speaker=Speaker.PARENT, message=request_data.text, report_id=daily_report_id
    )

    return await create_dialogue_log_service(log_with_report_id)


async def register_child_dialogue(
    request_data: ChatRequest,
    child_id: int,
    create_dialogue_log_service=Depends(get_create_dialogue_log_service),
    # 1. _get_daily_report_id를 호출하는 대신, 매개변수로 주입받습니다.
    daily_report_id: int = Depends(_get_daily_report_id),
) -> DialogueLogResponse:

    # 2. 이 줄을 삭제합니다.
    # daily_report_id = await _get_daily_report_id(child_id)
    log_with_report_id = DialogueLogCreate(
        speaker=Speaker.CHILD, message=request_data.text, report_id=daily_report_id
    )

    return await create_dialogue_log_service(log_with_report_id)
