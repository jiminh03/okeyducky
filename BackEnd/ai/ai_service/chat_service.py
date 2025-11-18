from loguru import logger

import asyncio
import re
from typing import Callable, Awaitable
from langchain_core.messages import HumanMessage

from ai.ai_service.ai_core.chain import chat_chain_with_history
from ai.ai_service.ai_core.memory import get_chat_history
from ai.ai_service.tts_service import tts_service
from ai.request import send_face_request
from common.schemas.dialogue_schema import DialogueLogBase
from typing import Callable, Awaitable, AsyncGenerator, List, Any

import asyncio
import logging
from typing import Callable, Awaitable, AsyncGenerator, List, Any, Optional


async def _stream_and_parse_response(
    chat_chain: Any,
    user_text: str,
    config: dict,
    tag_close_char: str = ")",
    sentence_delimiter: str = "\\",
) -> AsyncGenerator[str | None, None]:
    """
    AI 체인을 스트리밍하고, (감정 태그)와 문장을 분리하여 yield하는 비동기 제너레이터입니다.

    - 첫 번째 Yield: 감정 태그 (예: "(기쁨)") 또는 None (태그가 없을 경우)
    - 이후 Yields: 구분자(\\)로 분리된 순수 문장들
    """
    sentence_buffer = ""
    tag_yielded = False
    
    try:
        async for token in chat_chain.astream({"input": user_text}, config=config):
            sentence_buffer += token

            if not tag_yielded:
                if tag_close_char in sentence_buffer:
                    tag_part, rest = sentence_buffer.split(tag_close_char, 1)
                    potential_tag = (tag_part + tag_close_char).strip()

                    if potential_tag.startswith("("):
                        yield potential_tag
                        tag_yielded = True
                        sentence_buffer = rest.lstrip()
                    else:
                        yield None
                        tag_yielded = True
                
                elif sentence_delimiter in sentence_buffer:
                    yield None
                    tag_yielded = True

            if tag_yielded:
                while sentence_delimiter in sentence_buffer:
                    sentence, rest = sentence_buffer.split(sentence_delimiter, 1)
                    clean_sentence = sentence.strip()
                    
                    if clean_sentence:
                        yield clean_sentence
                    
                    sentence_buffer = rest.lstrip()

        if not tag_yielded:
            yield None
        
        final_part = sentence_buffer.strip()
        if final_part:
            yield final_part
            
    except Exception as e:
        logger.error(f"[AI Stream Error] _stream_and_parse_response 실패: {e}")
        raise


async def process_child_interaction(
    child_id: int,
    user_text: str,
    save_log_service: Callable[[DialogueLogBase, int], Awaitable],
):
    """
    Background Task: AI 체인을 실행하고, 감정 태그를 분리하며,
    TTS 큐에 작업을 제출하고, 완성된 AI 응답을 DB에 저장합니다. (리팩토링 V2)
    """
    full_response_parts: List[str] = []
    emotion_tag: Optional[str] = None
    child_id_str = str(child_id)
    config = {"configurable": {"session_id": child_id_str}}

    try:
        response_generator = _stream_and_parse_response(
            chat_chain_with_history, user_text, config
        )

        try:
            emotion_tag = await anext(response_generator)
            if emotion_tag:
                logger.info(f"[AI 감정 태그] {emotion_tag}")
                await send_face_request(child_id, emotion_tag)
            else:
                logger.info("[AI 감정 태그] 감정 태그가 없습니다.")
            
        except StopAsyncIteration:
            logger.info("[AI 응답] 스트림이 비어있습니다.")
            return

        async for sentence in response_generator:
            if sentence:
                full_response_parts.append(sentence)

                asyncio.create_task(
                    tts_service.submit_task(child_id_str, sentence)
                )

        full_response_buffer = " ".join(full_response_parts)

        if full_response_buffer:
            logger.info(f"[DB 저장] AI 응답: {full_response_buffer}")
            
            await save_log_service(
                log=DialogueLogBase(message=full_response_buffer, speaker="robot"),
                child_id=child_id,
            )
        else:
            logger.info("[DB 저장] AI가 생성한 문장이 없습니다.")

    except Exception as e:
        logger.error(f"[AI Error] process_child_interaction 실패: {e}")


async def process_parent_interaction(child_id: int, parent_text: str):
    """
    Background Task: 부모의 말을 AI 메모리에 주입하고 TTS 큐에 제출합니다.
    (AI 응답을 생성하거나 DB에 저장하지 않습니다)
    """
    child_id_str = str(child_id)
    try:
        history = get_chat_history(child_id_str)
        history.add_message(HumanMessage(content=f"[부모님의 메시지]: {parent_text}"))

        logger.info(f"[TTS 제출] 부모 발화: {parent_text}")
        asyncio.create_task(tts_service.submit_task(child_id_str, parent_text))
    except Exception as e:
        logger.info(f"[TTS Error] process_parent_interaction 실패: {e}")