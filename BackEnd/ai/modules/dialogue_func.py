from ai.providers.dialogue_providers import *
from fastapi import Depends  # Depends를 임포트해야 합니다.
from typing import List
from datetime import date
from common.repo.dialogue_repo import DialogueRepo

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