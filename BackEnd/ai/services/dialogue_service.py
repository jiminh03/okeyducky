from ai.providers.dialogue_providers import *
from fastapi import Depends  # Depends를 임포트해야 합니다.
from typing import List
from datetime import date
# ... (다른 import 구문들)


# 이 함수는 수정할 필요가 없습니다. 이미 잘 정의된 의존성입니다.
async def _get_daily_report_id(
    child_id: int,
    get_daily_report_by_child_id_service=Depends(get_daily_report_by_child_id_service),
    create_daily_report=Depends(get_create_daily_report_service),
) -> int:
    """
    특정 아동의 오늘 날짜 일일 리포트 ID를 반환합니다.
    오늘 날짜의 리포트가 없으면 새로 생성합니다.
    (이하 Docstring 생략)
    """
    today = date.today()

    daily_reports: List[DailyReportResponse] = (
        await get_daily_report_by_child_id_service(child_id, today, today)
    )
    if daily_reports:
        return daily_reports[0].report_id
    else:
        # 오늘 날짜의 일일 리포트가 없으면 새로 생성
        new_report_data = DailyReportCreate(
            date=today,
            daily_summary="",
            analysis_summary="",
            child_id=child_id,
            dialogue_logs=[],
        )
        daily_report = await create_daily_report(new_report_data)
        return daily_report.report_id


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