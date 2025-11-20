from fastapi import APIRouter, Depends, status, BackgroundTasks
from typing import List

# (가정) 수정된 ChatRequest 스키마 임포트 (text 필드만 있음)
from common.schemas.dialogue_schema import ChatRequest
# (가정) Speaker Enum 임포트 (라우터가 사용해야 함)
from common.models.enums import Speaker 

from app.services.chat_service import trigger_ai_server_task



# --- 라우터 생성 ---
router = APIRouter(
    prefix="/chat",
    tags=["ai와의 채팅 요청"],
    include_in_schema=True,
)

@router.post(
    "/parent_start/{child_id}", 
    status_code=status.HTTP_202_ACCEPTED,
    summary="[부모 발화] AI 대화 요청 (백그라운드 트리거)"
)
async def parent_chat_endpoint(
    child_id: int,
    request_data: ChatRequest, # ⬅️ 'text' 필드만 있는 Pydantic 모델
    background_tasks: BackgroundTasks,
):
    """
    '부모'의 발화를 접수하고, AI 처리를 백그라운드 작업으로 위임합니다.
    """
    
    background_tasks.add_task(
        trigger_ai_server_task, 
        child_id=child_id, 
        user_text=request_data.text,
        user_speaker=Speaker.PARENT # ⬅️ [핵심] 'parent'로 스피커 고정
    )

    return {"status": "processing", "message": "AI가 요청을 처리 중입니다..."}


@router.post(
    "/child_start/{child_id}", 
    status_code=status.HTTP_202_ACCEPTED,
    summary="[아이 발화] AI 대화 요청 (백그라운드 트리거)"
)
async def child_chat_endpoint(
    child_id: int,
    request_data: ChatRequest, # ⬅️ 'text' 필드만 있는 Pydantic 모델
    background_tasks: BackgroundTasks,
):
    """
    '아이'의 발화를 접수하고, AI 처리를 백그라운드 작업으로 위임합니다.
    """
    
    background_tasks.add_task(
        trigger_ai_server_task, 
        child_id=child_id, 
        user_text=request_data.text,
        user_speaker=Speaker.CHILD # ⬅️ [핵심] 'child'로 스피커 고정
    )

    return {"status": "processing", "message": "AI가 요청을 처리 중입니다..."}