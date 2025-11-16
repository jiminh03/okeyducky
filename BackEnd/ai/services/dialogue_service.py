from ai.providers.dialogue_providers import *


async def _get_daily_report_id(
    child_id: int,
    get_daily_report_by_child_id_service=Depends(get_daily_report_by_child_id_service),
    create_daily_report=Depends(get_create_daily_report_service),
) -> int:
    """
    특정 아동의 오늘 날짜 일일 리포트 ID를 반환합니다.
    오늘 날짜의 리포트가 없으면 새로 생성합니다.

    Args:
        child_id (int): 아동 ID
        get_daily_report_by_child_id_service (Depends, optional): 아동 ID와 날짜 범위로 일일 리포트 조회 서비스. Defaults to Depends(get_daily_report_by_child_id_service).
        create_daily_report (Depends, optional): 일일 리포트 생성 서비스. Defaults to Depends(register_daily_report).

    Returns:
        int: 오늘 날짜의 일일 리포트 ID
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
) -> DailyReportResponse:
    """
    일일 리포트를 수정합니다.

    Args:
        report_id (int): 수정할 일일 리포트 ID
        report (DailyReportUpdateRequest): 일일 리포트 수정 요청 데이터
        update_daily_report_service (Depends, optional): 일일 리포트 수정 서비스. Defaults to Depends(get_update_daily_report_service).

    Returns:
        DailyReportResponse: 수정된 일일 리포트 정보
    """
    daily_report_id = await _get_daily_report_id(child_id)
    return await update_daily_report_service(daily_report_id, report)


async def register_dialogue_log(
    log: DialogueLogBase,
    child_id: int,
    create_dialogue_log_service=Depends(get_create_dialogue_log_service),
) -> DialogueLogResponse:

    daily_report_id = await _get_daily_report_id(child_id)
    log_with_report_id = DialogueLogCreate(
        speaker=log.speaker, message=log.message, report_id=daily_report_id
    )

    return await create_dialogue_log_service(log_with_report_id)
