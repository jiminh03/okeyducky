from app.providers.dialogue_providers import *

async def register_daily_report(
    report: DailyReportCreate,
    create_daily_report_service=Depends(get_create_daily_report_service),
):
    return await create_daily_report_service(report)

async def update_daily_report(
    report_id: int,
    report: DailyReportUpdateRequest,
    update_daily_report_service=Depends(get_update_daily_report_service),
):
    return await update_daily_report_service(report_id, report)

async def get_daily_report_by_id(
    report_id: int,
    get_daily_report_by_id_service=Depends(get_daily_report_by_id_service),
):
    return await get_daily_report_by_id_service(report_id)

async def get_daily_report_by_child_id(
    child_id: int,
    start_date: date,
    end_date: date,
    get_daily_report_by_child_id_service=Depends(get_daily_report_by_child_id_service),
):
    return await get_daily_report_by_child_id_service(child_id, start_date, end_date)

async def register_dialogue_log(
    log: DialogueLogCreate,
    create_dialogue_log_service=Depends(get_create_dialogue_log_service),
):
    return await create_dialogue_log_service(log)