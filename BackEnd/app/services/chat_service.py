# ai/ai_service/chat_service.py
from loguru import logger
import httpx
import os
from common.models.enums import Speaker
from common.schemas.dialogue_schema import DialogueLogBase
from common.modules.db_instance import db # ⬅️ DB 인스턴스 직접 임포트

async def trigger_ai_server_task(
    child_id: int, 
    user_text: str, 
    user_speaker: Speaker
):
    """
    (백그라운드 작업) 실제 AI 서버 API를 호출하고, 응답을 DB에 저장합니다.
    """
    AI_SERVER_URL = os.getenv("AI_SERVER_URL") # (예: "http://ai.server.com/chat")
    if not AI_SERVER_URL:
        logger.info("🚨 AI_SERVER_URL이 .env 파일에 설정되지 않았습니다.")
        return
    
    if user_speaker is Speaker.PARENT:
        api_url = f"{AI_SERVER_URL}/ai_chat/parent_start/{child_id}"
    elif user_speaker is Speaker.CHILD:
        api_url = f"{AI_SERVER_URL}/ai_chat/child_start/{child_id}"

    ai_payload = {
        "text": user_text,
    }
    
    try:
        # 1. AI 서버 호출 (응답 대기)
        async with httpx.AsyncClient() as client:
            logger.info(f"--- 🤖 AI 서버 호출 시작 (Child: {child_id}) ---")
            response = await client.post(api_url, json=ai_payload, timeout=60.0)
            response.raise_for_status() 
            
            ai_response_data = response.json()
            ai_status = ai_response_data.get("status", "no status")
            ai_message = ai_response_data.get("message", "AI 응답 파싱 실패")
            logger.info(f"--- 🤖 AI 서버 상태: {ai_status}... ---")
            logger.info(f"--- 🤖 AI 서버 응답 수신: {ai_message}... ---")

    except httpx.HTTPStatusError as e:
        logger.info(f"🚨 AI 서버 HTTP 오류 (Child: {child_id}): {e}")
    except Exception as e:
        logger.info(f"🚨 AI 서버 작업 중 오류 (Child: {child_id}): {e}")