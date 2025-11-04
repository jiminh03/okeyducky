from fastapi import Depends
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select  # SQLAlchemy 1.4+

from common.modules.db_instance import db

from common.models.dialogue_model import *
from common.schemas.dialogue_schema import *

from common.exceptions import *


class DialogueRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_daily_report(
        self, report: DailyReportCreate
    ) -> DailyReport:
        try:
            new_report = DailyReport(
                date=report.date,
                daily_summary=report.daily_summary,
                analysis_summary=report.analysis_summary,
                child_id=report.child_id,
            )

            logs_to_add = []
            for log_data in report.dialogue_logs:
                logs_to_add.append(
                    DialogueLog(
                        speaker=log_data.speaker,
                        message=log_data.message,
                        # 중요: new_report.report_id가 아닌,'daily_report' 관계(relationship)에 객체를 직접 연결
                        daily_report=new_report 
                    )
                )

            self.session.add(new_report)
            if logs_to_add:
                self.session.add_all(logs_to_add)

            await self.session.commit()
            
            await self.session.refresh(new_report)
            
            stmt = (
                select(DailyReport)
                .where(DailyReport.report_id == new_report.report_id)
                .options(selectinload(DailyReport.dialogue_logs))
            )
            result = await self.session.execute(stmt)
            final_loaded_report = result.scalar_one()

            return final_loaded_report
        
        except IntegrityError as e:
            await self.session.rollback()
            # (child_id 외래 키 오류 등)
            detail = f"리포트 생성 실패: Child ID {report.child_id}가 존재하지 않거나, 날짜({report.date})가 중복될 수 있습니다."
            # log.warning(f"create_daily_report IntegrityError: {detail} | Error: {e}")
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"create_daily_report DB 오류: {e}", exc_info=True)
            raise DatabaseError() from e
        
    async def update_daily_report(
        self, report_id: int, report_update: DailyReportUpdateRequest
    ) -> Optional[DailyReport]:
        try:
            report = await self.get_daily_report_by_id(report_id)
            if not report:
                return None

            update_data = report_update.model_dump(exclude_none=True)
            for key, value in update_data.items():
                setattr(report, key, value)

            await self.session.commit()
            await self.session.refresh(report)
            return report
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"update_daily_report DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_daily_report_by_id(
        self, report_id: int
    ) -> Optional[DailyReport]:
        try:
            statement = (
                select(DailyReport)
                .where(DailyReport.report_id == report_id)
                .options(selectinload(DailyReport.dialogue_logs))
            )
            result = await self.session.execute(statement)
            report = result.scalar_one_or_none()
            return report
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_daily_report_by_id DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e

    async def get_daily_reports_by_child_id_and_date_range(  # 함수 이름 변경 및 파라미터 추가
        self, child_id: int, start_date: date, end_date: date
    ) -> List[DailyReport]:
        """
        특정 아이의 지정된 기간 동안의 일일 리포트 목록을 조회합니다.
        """
        try:
            statement = (
                select(DailyReport)
                .where(DailyReport.child_id == child_id)
                .where(DailyReport.date >= start_date)
                .where(DailyReport.date <= end_date)
                .options(selectinload(DailyReport.dialogue_logs)) # <-- 관계 로드
                .order_by(DailyReport.date.asc())
            )

            result = await self.session.execute(statement)

            db_reports = result.scalars().all()

            return db_reports
        
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"get_daily_reports DB 오류: {e}", exc_info=True)
            raise DatabaseError() from e
        
    async def create_dialogue_log(self, log: DialogueLogCreate) -> DialogueLog:
        try:
            new_log = DialogueLog(
                speaker=log.speaker,
                message=log.message,
                report_id=log.report_id,
            )
            self.session.add(new_log)
            await self.session.commit()
            await self.session.refresh(new_log)
            return new_log
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(
                detail="대화 로그 생성 중 무결성 오류가 발생했습니다."
            ) from e
        except DBAPIError as e:
            await self.session.rollback()
            # log.error(f"create_dialogue_log DB 오류: {e}", exc_info=True) # (희망사항) 간단한 로그
            raise DatabaseError() from e
