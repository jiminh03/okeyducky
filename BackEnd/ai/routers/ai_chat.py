from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
import asyncio
from datetime import date
from fastapi import Depends
from typing import List

# --- 스키마 임포트 (경로는 실제 프로젝트에 맞게 조정) ---
from ai.ai_service.chat_service import (
    process_child_interaction,
    process_parent_interaction,
)
from ai.schemas.ai_chat import ChildStartRequest, ParentStartRequest
from ai.services.dialogue_service import register_dialogue_log
from common.schemas.dialogue_schema import (
    DailyReportCreate,
    DailyReportUpdateRequest,
    DailyReportResponse,
    DialogueLogBase,
    DialogueLogCreate,
)

# --- AI 서비스 임포트 ---
from ai.ai_service.report_service import create_daily_report

# --- DB 서비스 프로바이더 임포트 (dialogue_service.py에서 사용) ---
from ai.providers.dialogue_providers import (
    get_daily_report_by_child_id_service,
    get_create_daily_report_service,
    get_update_daily_report_service,
)

from pydantic import BaseModel

class ChatRequest(BaseModel):
    text: str

router = APIRouter(
    prefix="/ai_chat",
    tags=["아이와의 대화"],
    include_in_schema=True,
)


# --- 1. 부모 발화 라우터 ---
@router.post("/parent_start/{child_id}")
async def parent_chat(
    child_id: int,
    request_data: ChatRequest,
    background_tasks: BackgroundTasks,
    save_log_service=Depends(register_dialogue_log),
):
    await save_log_service(
        log=DialogueLogBase(message=request_data.text, speaker="parent"),
        child_id=child_id,
    )

    # C. [작업 위임] 백그라운드 작업 추가 (부모 로직)
    background_tasks.add_task(process_parent_interaction, child_id, request_data.text,)

    # D. 즉시 응답
    return {"status": "queued", "message": "Parent message is being sent to the robot."}


# --- 2. 아이 발화 라우터 ---
@router.post("/child_start/{child_id}")
async def child_chat(
    child_id: int,
    request_data: ChatRequest,
    background_tasks: BackgroundTasks,
    save_log_service=Depends(register_dialogue_log),
):
    await save_log_service(
        log=DialogueLogBase(message=request_data.text, speaker="parent"),
        child_id=child_id,
    )

    # C. [작업 위임] 백그라운드 작업 추가 (아이 로직 + 서비스 의존성 전달)
    background_tasks.add_task(
        process_child_interaction,
        child_id,
        request_data.text,
        save_log_service,  # 나중에 로봇 응답 저장용으로 전달
    )

    # D. 즉시 응답
    return {"status": "processing", "message": "AI is thinking..."}
