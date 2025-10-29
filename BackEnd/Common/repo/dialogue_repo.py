from fastapi import Depends
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from common.modules.db_instance import db

from common.models.dialogue_model import *
from common.schemas.dialogue_schema import *


class DialogueRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_daily_report(
        self, report: DailyReportCreate
    ) -> DailyReportResponse:
        new_report = DailyReport(
            date=report.date,
            daily_summary=report.daily_summary,
            analysis_summary=report.analysis_summary,
            child_id=report.child_id,
        )
        self.session.add(new_report)
        await self.session.commit()
        await self.session.refresh(new_report)

        for log_data in report.dialogue_logs:
            dialogue_log = DialogueLog(
                speaker=log_data.speaker,
                message=log_data.message,
                report_id=new_report.report_id,
            )
            self.session.add(dialogue_log)
        await self.session.commit()
        await self.session.refresh(new_report)
        return new_report

    async def update_daily_report(
        self, report_id: int, report_update: DailyReportUpdateRequest
    ) -> Optional[DailyReportResponse]:
        report = await self.get_daily_report_by_id(report_id)
        if not report:
            return None

        update_data = report_update.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(report, key, value)

        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_daily_report_by_id(
        self, report_id: int
    ) -> Optional[DailyReportResponse]:
        query = text("SELECT * FROM DailyReport WHERE report_id = :report_id")
        result = await self.session.execute(query, {"report_id": report_id})
        report = result.scalar_one_or_none()
        return report

    async def get_daily_reports_by_child_id_and_date_range(  # 함수 이름 변경 및 파라미터 추가
        self, child_id: int, start_date: date, end_date: date
    ) -> List[DailyReportResponse]:
        """
        특정 아이의 지정된 기간 동안의 일일 리포트 목록을 조회합니다.
        """

        query = text(
            "SELECT * FROM DailyReport "
            "WHERE child_id = :child_id "
            "AND date >= :start_date AND date <= :end_date "
            "ORDER BY date ASC"  # 날짜순 정렬 추가 (선택 사항)
        )

        result = await self.session.execute(
            query,
            {"child_id": child_id, "start_date": start_date, "end_date": end_date},
        )

        db_reports = result.fetchall()
        response_reports = [
            DailyReportResponse.model_validate(report) for report in db_reports
        ]

        return response_reports

    async def create_dialogue_log(self, log: DialogueLogCreate) -> DialogueLogResponse:
        new_log = DialogueLog(
            speaker=log.speaker,
            message=log.message,
            report_id=log.report_id,
        )
        self.session.add(new_log)
        await self.session.commit()
        await self.session.refresh(new_log)
        return new_log
