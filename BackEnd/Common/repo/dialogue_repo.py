from fastapi import Depends
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select # SQLAlchemy 1.4+

from common.modules.db_instance import db

from common.models.dialogue_model import *
from common.schemas.dialogue_schema import *


class DialogueRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_daily_report(
        self, report: DailyReportCreate
    ) -> DailyReportResponse:
        
        # 1. 부모 객체 생성 (아직 커밋 안 함)
        new_report = DailyReport(
            date=report.date,
            daily_summary=report.daily_summary,
            analysis_summary=report.analysis_summary,
            child_id=report.child_id,
        )
        self.session.add(new_report)

        # 2. 부모 객체를 먼저 커밋하여 report_id를 생성합니다.
        await self.session.commit()
        await self.session.refresh(new_report) # new_report.report_id를 가져옴

        # 3. 자식 객체 리스트를 만듭니다.
        logs_to_add = []
        for log_data in report.dialogue_logs:
            logs_to_add.append(
                DialogueLog(
                    speaker=log_data.speaker,
                    message=log_data.message,
                    report_id=new_report.report_id, # 위에서 얻은 ID 사용
                )
            )

        # 4. 자식 객체들을 'add_all'로 한 번에 추가하고 'commit'도 한 번만 합니다.
        if logs_to_add:
            self.session.add_all(logs_to_add)
            await self.session.commit()

        # 5. [가장 중요]
        #    데이터를 반환하기 전, DB에서 객체를 '즉시 로딩(eager loading)' 옵션으로
        #    다시 조회합니다. 이렇게 하면 dialogue_logs가 채워진 객체를 얻습니다.
        
        stmt = (
            select(DailyReport)
            .where(DailyReport.report_id == new_report.report_id)
            .options(selectinload(DailyReport.dialogue_logs)) # <-- 핵심
        )
        result = await self.session.execute(stmt)
        final_loaded_report = result.scalar_one()

        # 6. '완전히 로드된' 객체를 반환합니다.
        #    이제 이 객체의 .dialogue_logs에 접근해도 DB I/O가 발생하지 않습니다.
        return final_loaded_report

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
        statement = (
            select(DailyReport)
            .where(DailyReport.report_id == report_id)
            .options(selectinload(DailyReport.dialogue_logs))
        )
        result = await self.session.execute(statement)
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
