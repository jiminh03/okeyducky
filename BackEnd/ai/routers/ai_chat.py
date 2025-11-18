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
from ai.modules.dialogue_func import _get_daily_report_id
from ai.schemas.ai_chat import ChildStartRequest, ParentStartRequest
from ai.services.dialogue_service import register_child_dialogue, register_dialogue_log, register_parent_dialogue
from common.schemas.dialogue_schema import (
    ChatRequest,
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
    get_create_dialogue_log_service,
    get_daily_report_by_child_id_service,
    get_create_daily_report_service,
    get_update_daily_report_service,
)

from pydantic import BaseModel



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
    parent_log=Depends(register_parent_dialogue),
):

    # C. [작업 위임] 백그라운드 작업 추가 (부모 로직)
    background_tasks.add_task(process_parent_interaction, child_id, request_data.text,)

    # D. 즉시 응답
    return {"status": "queued", "message": f"{parent_log} is being sent to the robot."}


# --- 2. 아이 발화 라우터 ---
@router.post("/child_start/{child_id}")
async def child_chat(
    child_id: int,
    request_data: ChatRequest,
    background_tasks: BackgroundTasks,
    child_log=Depends(register_child_dialogue),
    
    # --- 1. 백그라운드 작업에 필요한 의존성을 *여기서* 미리 주입받습니다. ---
    
    # register_dialogue_log가 필요로 하는 첫 번째 의존성
    create_log_service=Depends(get_create_dialogue_log_service),
    
    # register_dialogue_log가 필요로 하는 두 번째 의존성
    # (_get_daily_report_id는 child_id가 필요할 텐데, 
    # FastAPI가 이 함수의 child_id를 보고 알아서 주입해줍니다.)
    daily_report_id: int = Depends(_get_daily_report_id),
):
    
    # --- 2. 'register_dialogue_log'의 로직을 수행할 헬퍼 함수를 정의합니다. ---
    
    # 이 함수는 process_child_interaction 내부에서 호출될 것입니다.
    # (log: DialogueLogBase, child_id: int) 시그니처를 따릅니다.
    async def _save_log_helper(log: DialogueLogBase, child_id: int):
        """
        백그라운드 작업에서 호출될 실제 로그 저장 함수.
        바깥 스코프(child_chat)에서 주입받은 report_id와 service를 사용합니다.
        """
        # register_dialogue_log의 핵심 로직을 그대로 가져옵니다.
        log_with_report_id = DialogueLogCreate(
            speaker=log.speaker, 
            message=log.message, 
            report_id=daily_report_id  # <-- child_chat에서 주입된 값
        )
        
        # <-- child_chat에서 주입된 값
        await create_log_service(log_with_report_id)
        
        # (참고: child_id_from_task는 이 로직에선 필요 없지만, 
        # process_child_interaction가 호출하는 시그니처를 맞추기 위해 받습니다.)


    # --- 3. 백그라운드 작업에 'Depends'가 아닌, 위에서 만든 '헬퍼 함수'를 전달합니다. ---
    background_tasks.add_task(
        process_child_interaction,
        child_id,
        request_data.text,
        _save_log_helper  # <-- 'Depends(...)' 대신 실제 함수 객체를 전달
    )

    # D. 즉시 응답
    return {"status": "processing", "message": f"AI is thinking about {child_log}..."}