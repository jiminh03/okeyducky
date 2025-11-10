from fastapi import Depends
from typing import List, Optional
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select # ⬅️ [개선] SQLAlchemy 2.0+ 스타일 'select'

from common.modules.db_instance import db

from common.models.dialogue_model import DailyReport, DialogueLog # ⬅️ [변경] 모델 둘 다 임포트
from common.schemas.dialogue_schema import *

from common.exceptions import *


class DialogueRepo:
    def __init__(self, session: AsyncSession = Depends(db.get_session)):
        self.session = session

    async def create_daily_report(
        self, report: DailyReportCreate
    ) -> DailyReportResponse: # ⬅️ [변경] 반환 타입 DTO로
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
                        daily_report=new_report 
                    )
                )

            self.session.add(new_report)
            if logs_to_add:
                self.session.add_all(logs_to_add)

            await self.session.commit()
            
            # (참고: commit 후에는 new_report.dialogue_logs가 자동으로 채워지지 않으므로,
            #  refresh 대신 'selectinload'로 다시 조회하는 것이 가장 안전합니다.)
            
            stmt = (
                select(DailyReport)
                .where(DailyReport.report_id == new_report.report_id)
                .options(selectinload(DailyReport.dialogue_logs))
            )
            result = await self.session.execute(stmt)
            final_loaded_report = result.scalar_one() # 'DailyReport' (SQLModel) 객체

            # ⬇️ [변경] SQLModel 객체를 Pydantic DTO로 변환하여 반환
            return DailyReportResponse.model_validate(final_loaded_report)
        
        except IntegrityError as e:
            await self.session.rollback()
            detail = f"리포트 생성 실패: Child ID {report.child_id}가 존재하지 않거나, 날짜({report.date})가 중복될 수 있습니다."
            raise IntegrityViolationError(detail=detail) from e
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e
        
    async def update_daily_report(
        self, report_id: int, report_update: DailyReportUpdateRequest
    ) -> Optional[DailyReportResponse]: # ⬅️ [변경] 반환 타입 DTO로
        try:
            # (참고: get_daily_report_by_id가 DTO를 반환하도록 변경되었으므로,
            #  업데이트를 위해선 SQLModel 객체를 직접 가져오는 .get()이 필요합니다.)
            report = await self.session.get(DailyReport, report_id) # ⬅️ [변경] .get() 사용
            
            if not report:
                return None

            update_data = report_update.model_dump(exclude_none=True)
            for key, value in update_data.items():
                setattr(report, key, value)

            await self.session.commit()
            await self.session.refresh(report)

            # ⬇️ [변경] SQLModel 객체를 Pydantic DTO로 변환하여 반환
            # (refresh 후 dialogue_logs를 로드하기 위해 다시 조회)
            loaded_report = await self.get_daily_report_by_id(report.report_id)
            return loaded_report
        
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def get_daily_report_by_id(
        self, report_id: int
    ) -> Optional[DailyReportResponse]:
        try:
            statement = (
                select(DailyReport)
                .where(DailyReport.report_id == report_id)
                .options(selectinload(DailyReport.dialogue_logs))
            )
            result = await self.session.execute(statement)
            report = result.scalar_one_or_none() # 'DailyReport' (SQLModel) 객체
            
            # ⬇️ [변경] SQLModel 객체를 Pydantic DTO로 변환하여 반환
            return DailyReportResponse.model_validate(report) if report else None
        
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e

    async def get_daily_reports_by_child_id_and_date_range(
        self, child_id: int, start_date: date, end_date: date
    ) -> List[DailyReportResponse]:
        try:
            statement = (
                select(DailyReport)
                .where(DailyReport.child_id == child_id)
                .where(DailyReport.date >= start_date)
                .where(DailyReport.date <= end_date)
                .options(selectinload(DailyReport.dialogue_logs))
                .order_by(DailyReport.date.asc())
            )

            result = await self.session.execute(statement)

            db_reports = result.scalars().all() # 'List[DailyReport]' (SQLModel)

            # ⬇️ [변경] List[SQLModel] -> List[Pydantic DTO]로 변환
            response_list = [DailyReportResponse.model_validate(report) for report in db_reports]
            return response_list
        
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e
        
    async def create_dialogue_log(self, log: DialogueLogCreate) -> DialogueLogResponse: # ⬅️ [변경] 반환 타입 DTO로
        try:
            new_log = DialogueLog(
                speaker=log.speaker,
                message=log.message,
                report_id=log.report_id,
            )
            self.session.add(new_log)
            await self.session.commit()
            await self.session.refresh(new_log)
            
            # ⬇️ [변경] SQLModel 객체를 Pydantic DTO로 변환하여 반환
            return DialogueLogResponse.model_validate(new_log)
        
        except IntegrityError as e:
            await self.session.rollback()
            raise IntegrityViolationError(
                detail="대화 로그 생성 중 무결성 오류가 발생했습니다."
            ) from e
        except DBAPIError as e:
            await self.session.rollback()
            raise DatabaseError(detail=f"DB 오류 발생: {str(e)}") from e