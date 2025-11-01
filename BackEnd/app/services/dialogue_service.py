from app.providers.dialogue_providers import *

from app.exceptions import *
from app.services.child_service import *

#TODO:register_daily_report, update_daily_report, register_dialogue_log는 mvp에서 별도의 인증 절차 없음

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

async def register_dialogue_log(
    log: DialogueLogCreate,
    create_dialogue_log_service=Depends(get_create_dialogue_log_service),
):
    return await create_dialogue_log_service(log)

async def get_daily_report_by_id(
    report_id: int,
    get_daily_report_by_id_service=Depends(get_daily_report_by_id_service),
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_info_service=Depends(get_child_by_id_service),
):
    daily_report = await get_daily_report_by_id_service(report_id)
    if daily_report is None:
        raise ReportNotFound
    child = await get_child_info_service(daily_report.child_id)
    if child is None:
        raise ChildNotFound
    
    child_ids = [child.child_id for child in child_list]
    if daily_report.child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")
    
    return await get_daily_report_by_id_service(report_id)

async def get_daily_report_by_child_id(
    child_id: int,
    start_date: date,
    end_date: date,
    get_daily_report_by_child_id_service=Depends(get_daily_report_by_child_id_service),
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_info_service=Depends(get_child_by_id_service),
):
    child = await get_child_info_service(child_id)
    if child is None:
        raise ChildNotFound
    
    child_ids = [child.child_id for child in child_list]
    if child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")
    
    return await get_daily_report_by_child_id_service(child_id, start_date, end_date)

