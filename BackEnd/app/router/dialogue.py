from fastapi import APIRouter, Depends
from datetime import date
from typing import List
from calendar import monthrange

# --- 모든 서비스, 스키마, 예외 임포트 ---
from app.services.dialogue_service import *
from app.services.child_service import *
from common.schemas.dialogue_schema import *
from common.schemas.user_schema import *
from app.exceptions import *
from app.providers.dialogue_providers import *

# --- 라우터 생성 ---
router = APIRouter(
    prefix="/reports",
    tags=["대화 및 리포트 (Dialogue & Reports)"],
    include_in_schema=True,
)

# ===================================================================
# DialogueService (대화 및 리포트)
# ===================================================================

@router.get("/log/{date}", summary="일일 대화 로그 조회 (R3-1)")
async def get_daily_log_endpoint(
    date: date,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_daily_report_by_child_id_service=Depends(get_daily_report_by_child_id_service),
):
    """
    특정 날짜(YYYY-MM-DD)를 지정하여, 그날의 AI 요약본(daily_summary)과 전체 대화 로그(logs)를 조회합니다.
    
    서비스: `get_daily_report_by_child_id` (날짜 범위를 같은 날짜로 설정)
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 404 Not Found (해당 날짜의 데이터가 없음)
    """
    # 계정당 1명만 등록 가능하므로 리스트의 첫 번째 아이 사용
    if not child_list or len(child_list) == 0:
        raise ChildNotFound
    
    child_id = child_list[0].child_id
    # 같은 날짜로 범위 설정
    reports = await get_daily_report_by_child_id_service(child_id, date, date)
    
    if not reports or len(reports) == 0:
        raise ReportNotFound
    
    # DailyLogResponse 형식으로 변환 (첫 번째 리포트 사용)
    report = reports[0]
    return {
        "date": report.date,
        "daily_summary": report.daily_summary,
        "logs": report.dialogue_logs
    }

@router.get("/analysis/{date}", summary="일일 AI 분석 리포트 조회 (R3-2)")
async def get_daily_analysis_endpoint(
    date: date,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_daily_report_by_child_id_service=Depends(get_daily_report_by_child_id_service),
):
    """
    특정 날짜(YYYY-MM-DD)를 지정하여, AI가 비동기 분석한 리포트(analysis_summary, keywords, notes)를 조회합니다.
    
    서비스: `get_daily_report_by_child_id` (날짜 범위를 같은 날짜로 설정)
    - (성공) 200 OK
    - (실패) 401 Unauthorized (인증 필요)
    - (실패) 404 Not Found (해당 날짜의 데이터가 없음)
    """
    # 계정당 1명만 등록 가능하므로 리스트의 첫 번째 아이 사용
    if not child_list or len(child_list) == 0:
        raise ChildNotFound
    
    child_id = child_list[0].child_id
    # 같은 날짜로 범위 설정
    reports = await get_daily_report_by_child_id_service(child_id, date, date)
    
    if not reports or len(reports) == 0:
        raise ReportNotFound
    
    # DailyReportResponse 반환 (첫 번째 리포트 사용)
    return reports[0]


@router.get("/{year}/{month}", summary="월별 일일 대화 로그 및 리포트 조회")
async def get_monthly_reports_endpoint(
    year: int,
    month: int,
    child_list: List[ChildInfoResponse] = Depends(get_child_list),
    get_daily_report_by_child_id_service=Depends(get_daily_report_by_child_id_service),
):
    """
    특정 연도와 월을 지정하여, 해당 월의 모든 일일 대화 로그와 리포트를 함께 조회합니다.
    
    각 리포트에는 다음이 포함됩니다:
    - date: 날짜
    - daily_summary: 일일 대화 요약
    - analysis_summary: AI 분석 리포트
    - dialogue_logs: 대화 로그 목록
    
    서비스: `get_daily_report_by_child_id` (월의 시작일과 종료일로 범위 설정)
    - (성공) 200 OK (빈 리스트 `[]` 포함)
    - (실패) 401 Unauthorized (인증 필요)
    """
    # 계정당 1명만 등록 가능하므로 리스트의 첫 번째 아이 사용
    if not child_list or len(child_list) == 0:
        raise ChildNotFound
    
    # 월 유효성 검사
    if month < 1 or month > 12:
        raise ValueError("월은 1부터 12 사이의 값이어야 합니다.")
    
    child_id = child_list[0].child_id
    
    # 월의 시작일과 종료일 계산
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    # 해당 월의 모든 리포트 조회 (대화 로그와 리포트 모두 포함)
    reports = await get_daily_report_by_child_id_service(child_id, start_date, end_date)
    
    # DailyReportResponse 리스트 반환 (각 리포트에 대화 로그와 리포트 정보 모두 포함)
    return reports



