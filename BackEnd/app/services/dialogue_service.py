from app.providers.dialogue_providers import *

from app.exceptions import *
from app.services.child_service import *

#TODO:register_daily_report, update_daily_report, register_dialogue_log는 mvp에서 별도의 인증 절차 없음

async def register_daily_report(
    report: DailyReportCreate,
    create_daily_report_service=Depends(get_create_daily_report_service),
)->DailyReportResponse:
    """
    일일 리포트를 등록합니다.

    Args:
        report (DailyReportCreate): 일일 리포트 생성 요청 데이터
        create_daily_report_service (Depends, optional): 일일 리포트 생성 서비스. Defaults to Depends(get_create_daily_report_service).

    Returns:
        DailyReportResponse: 생성된 일일 리포트 정보
    """
    return await create_daily_report_service(report)

async def update_daily_report(
    report_id: int,
    report: DailyReportUpdateRequest,
    update_daily_report_service=Depends(get_update_daily_report_service),
)->DailyReportResponse:
    """
    일일 리포트를 수정합니다.

    Args:
        report_id (int): 수정할 일일 리포트 ID
        report (DailyReportUpdateRequest): 일일 리포트 수정 요청 데이터
        update_daily_report_service (Depends, optional): 일일 리포트 수정 서비스. Defaults to Depends(get_update_daily_report_service).

    Returns:
        DailyReportResponse: 수정된 일일 리포트 정보
    """
    return await update_daily_report_service(report_id, report)

async def register_dialogue_log(
    log: DialogueLogCreate,
    create_dialogue_log_service=Depends(get_create_dialogue_log_service),
)->DialogueLogResponse:
    """
    대화 로그를 등록합니다.

    Args:
        log (DialogueLogCreate): 대화 로그 생성 요청 데이터
        create_dialogue_log_service (Depends, optional): 대화 로그 생성 서비스. Defaults to Depends(get_create_dialogue_log_service).

    Returns:
        DialogueLogResponse: 생성된 대화 로그 정보
    """
    return await create_dialogue_log_service(log)

async def get_daily_report_by_id(
    report_id: int,
    get_daily_report_by_id_service=Depends(get_daily_report_by_id_service),
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_child_info_service=Depends(get_child_by_id_service),
)->DailyReportResponse:
    """
    ID로 일일 리포트를 가져옵니다.

    Args:
        report_id (int): 가져올 일일 리포트 ID
        get_daily_report_by_id_service (Depends, optional): ID로 일일 리포트를 가져오는 서비스. Defaults to Depends(get_daily_report_by_id_service).
        child_list (List[ChildInfoResponse], optional): 현재 로그인한 부모님의 자녀 목록. Defaults to Depends(get_child_list).
        get_child_info_service (Depends, optional): ID로 자녀 정보를 가져오는 서비스. Defaults to Depends(get_child_by_id_service).

    Raises:
        ReportNotFound: 해당 ID의 리포트를 찾을 수 없을 경우 발생
        ChildNotFound: 해당 리포트의 자녀를 찾을 수 없을 경우 발생
        NotOwnerError: 해당 자녀 정보에 접근할 권한이 없을 경우 발생

    Returns:
        DailyReportResponse: 일일 리포트 정보
    """
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
) -> List[DailyReportResponse]:
    """
    자녀 ID와 기간으로 일일 리포트 목록을 가져옵니다.

    Args:
        child_id (int): 자녀 ID
        start_date (date): 시작일
        end_date (date): 종료일
        get_daily_report_by_child_id_service (Depends, optional): 자녀 ID와 기간으로 일일 리포트 목록을 가져오는 서비스. Defaults to Depends(get_daily_report_by_child_id_service).
        child_list (List[ChildInfoResponse], optional): 현재 로그인한 부모님의 자녀 목록. Defaults to Depends(get_child_list).
        get_child_info_service (Depends, optional): ID로 자녀 정보를 가져오는 서비스. Defaults to Depends(get_child_by_id_service).

    Raises:
        ChildNotFound: 해당 ID의 자녀를 찾을 수 없을 경우 발생
        NotOwnerError: 해당 자녀 정보에 접근할 권한이 없을 경우 발생

    Returns:
        List[DailyReportResponse]: 일일 리포트 정보 목록
    """
    child = await get_child_info_service(child_id)
    if child is None:
        raise ChildNotFound
    
    child_ids = [child.child_id for child in child_list]
    if child_id not in child_ids:
        raise NotOwnerError(detail="해당 자녀 정보에 접근할 권한이 없습니다.")
    
    return await get_daily_report_by_child_id_service(child_id, start_date, end_date)