# ai/routers/ai_router.py

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from ai.schemas.ai_chat import ChildStartRequest, ParentStartRequest
from common.deps import get_create_dialogue_log_service
from common.schemas.dialogue_schema import DialogueLogCreate
from .socket_manager import manager

# 위에서 작성한 로직 임포트
from ai.ai_service.ai_processing import process_child_interaction, process_parent_interaction

router = APIRouter()

# --- 1. 부모 발화 라우터 ---
@router.post("/ai_chat/parent_start")
async def parent_chat(
    req: ParentStartRequest,
    background_tasks: BackgroundTasks,
    save_log_service = Depends(get_create_dialogue_log_service)
):
    child_id = str(req.child_id)

    # A. 연결 확인
    if not await manager.get_connection(child_id):
        raise HTTPException(status_code=404, detail="Robot not connected via WebSocket")

    # B. [DB] 부모 발화 저장 (비동기 실행)
    await save_log_service(DialogueLogCreate(
        child_id=int(req.child_id),
        content=req.text,
        speaker="parent" 
    ))

    # C. [작업 위임] 백그라운드 작업 추가 (부모 로직)
    background_tasks.add_task(
        process_parent_interaction, 
        child_id, 
        req.text
    )

    # D. 즉시 응답
    return {"status": "queued", "message": "Parent message is being sent to the robot."}


# --- 2. 아이 발화 라우터 ---
@router.post("/ai_chat/child_start")
async def child_chat(
    req: ChildStartRequest,
    background_tasks: BackgroundTasks,
    save_log_service = Depends(get_create_dialogue_log_service)
):
    child_id = str(req.child_id)

    # A. 연결 확인
    if not await manager.get_connection(child_id):
        raise HTTPException(status_code=404, detail="Robot not connected via WebSocket")

    # B. [DB] 아이 발화 저장
    await save_log_service(DialogueLogCreate(
        child_id=int(req.child_id),
        content=req.text,
        speaker="child"
    ))

    # C. [작업 위임] 백그라운드 작업 추가 (아이 로직 + 서비스 의존성 전달)
    background_tasks.add_task(
        process_child_interaction, 
        child_id, 
        req.text,
        save_log_service # 나중에 로봇 응답 저장용으로 전달
    )

    # D. 즉시 응답
    return {"status": "processing", "message": "AI is thinking..."}