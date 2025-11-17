import asyncio
import re
from typing import Callable, Awaitable
from langchain_core.messages import HumanMessage

# AI 체인, 메모리, TTS 서비스 임포트
from ai.ai_service.ai_core.chain import chat_chain_with_history
from ai.ai_service.ai_core.memory import get_chat_history
from ai.ai_service.tts_service import tts_service
from common.schemas.dialogue_schema import DialogueLogBase


# --- 1. 아이 발화 처리 (AI 응답 생성 -> TTS -> DB 저장) ---
async def process_child_interaction(
    child_id: int,
    user_text: str,
    save_log_service: Callable[[DialogueLogBase, int], Awaitable],
):
    """
    Background Task: AI 체인을 실행하고, TTS 큐에 작업을 제출하며,
    완성된 AI 응답을 DB에 저장합니다.
    """
    sentence_buffer = ""
    full_response_buffer = ""  # DB 저장용 전체 응답
    child_id_str = str(child_id)  # 서비스 내부에서는 str 사용

    try:
        # 1. AI 체인 스트리밍 및 TTS 작업 제출
        async for token in chat_chain_with_history.astream(
            {"input": user_text},
            config={"configurable": {"session_id": child_id_str}},  # session_id 키 사용
        ):
            sentence_buffer += token
            if "\\" in sentence_buffer:
                parts = sentence_buffer.split("\\")

                for part in parts[:-1]:
                    clean_sentence = part.strip()
                    if clean_sentence:
                        # DB 버퍼에 누적
                        if full_response_buffer:
                            full_response_buffer += " "
                        full_response_buffer += clean_sentence

                        # [Task 1] TTS 스트리밍 시작 (큐에 제출)
                        asyncio.create_task(
                            tts_service.submit_task(child_id_str, clean_sentence)
                        )

                sentence_buffer = parts[-1].lstrip()

        # 남은 버퍼 처리
        final_part = sentence_buffer.strip()
        if final_part:
            if full_response_buffer:
                full_response_buffer += " "
            full_response_buffer += final_part

            # [Task 1] TTS 스트리밍 시작 (큐에 제출)
            asyncio.create_task(tts_service.submit_task(child_id_str, final_part))

        # 2. [Task 2] AI 답변 DB에 저장
        if full_response_buffer:
            print(f"[DB 저장] AI 응답: {full_response_buffer}")
            await save_log_service(
                log=DialogueLogBase(message=full_response_buffer, speaker="robot"),
                child_id=child_id,
            )

    except Exception as e:
        print(f"[AI Error] process_child_interaction 실패: {e}")
        # (선택) 에러 발생 시 DB에 에러 로그 저장
        await save_log_service(
            log=DialogueLogBase(message=f"AI 응답 생성 실패: {e}", speaker="error"),
            child_id=child_id,
        )


# --- 2. 부모 발화 처리 (메모리 주입 -> TTS) ---
async def process_parent_interaction(child_id: int, parent_text: str):
    """
    Background Task: 부모의 말을 AI 메모리에 주입하고 TTS 큐에 제출합니다.
    (AI 응답을 생성하거나 DB에 저장하지 않습니다)
    """
    child_id_str = str(child_id)
    try:
        # 1. AI 메모리에 부모 발화 주입 (다음 대화를 위해)
        history = get_chat_history(child_id_str)
        history.add_message(HumanMessage(content=f"[부모님의 메시지]: {parent_text}"))

        # 2. [Task 1] TTS 스트리밍 시작 (큐에 제출)
        print(f"[TTS 제출] 부모 발화: {parent_text}")
        asyncio.create_task(tts_service.submit_task(child_id_str, parent_text))
    except Exception as e:
        print(f"[TTS Error] process_parent_interaction 실패: {e}")
