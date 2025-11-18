from loguru import logger

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
import asyncio
from datetime import date
from fastapi import Depends
from typing import List

# --- 스키마 임포트 (경로는 실제 프로젝트에 맞게 조정) ---
from common.schemas.dialogue_schema import (
    DailyReportCreate,
    DailyReportUpdateRequest,
    DailyReportResponse,
)

# --- AI 서비스 임포트 ---
from ai.ai_service.report_service import create_daily_report

# --- DB 서비스 프로바이더 임포트 (dialogue_service.py에서 사용) ---
from ai.providers.dialogue_providers import (
    get_daily_report_by_child_id_service,
    get_create_daily_report_service,
    get_update_daily_report_service,
)

router = APIRouter(
    prefix="/ai_report",
    tags=["대화 요약 및 분석"],
    include_in_schema=True,
)

# --- 3. 리포트 생성 ---
@router.post("/{child_id}")
async def update_daily_report(
    child_id: int,
    get_daily_report_svc=Depends(get_daily_report_by_child_id_service),
    create_daily_report_svc=Depends(get_create_daily_report_service),
    update_daily_report_svc=Depends(get_update_daily_report_service),
) -> DailyReportResponse:
    """
    AI로부터 리포트를 생성하고, 오늘 날짜의 DB 레코드에 업데이트합니다.
    """

    logger.info(f"AI 리포트 생성 중... (Child ID: {child_id})")
    ai_content = await create_daily_report(str(child_id))

    # --- 3. DB 저장을 위해 데이터 가공 ---
    # summary_list (JSON 리스트)를 DB 저장을 위해 하나의 문자열로 합칩니다.
    summary_text = "\n".join(ai_content["summary"])

    update_payload = DailyReportUpdateRequest(
        daily_summary=summary_text, analysis_summary=ai_content["analysis"]
    )

    today = date.today()
    daily_reports: List[DailyReportResponse] = await get_daily_report_svc(
        child_id, today, today
    )

    if daily_reports:
        report_id = daily_reports[0].report_id
    else:
        # 오늘 날짜 리포트가 없으면 새로 생성
        new_report_data = DailyReportCreate(
            date=today,
            daily_summary="",  # 먼저 빈 값으로 생성
            analysis_summary="",
            child_id=child_id,
            dialogue_logs=[],
        )
        new_report = await create_daily_report_svc(new_report_data)
        report_id = new_report.report_id

    # B. AI가 생성한 내용으로 리포트 업데이트 (dialogue_service.update_daily_report 로직)
    logger.info(f"DB에 리포트 저장 중... (Report ID: {report_id})")
    updated_report = await update_daily_report_svc(report_id, update_payload)

    logger.info("리포트 생성 및 저장 완료.")
    return updated_report
