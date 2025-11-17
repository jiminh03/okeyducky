import asyncio
from typing import Callable, Awaitable
from dotenv import load_dotenv
from ai.ai_service.ai_core.chain import (
    chat_chain_with_history,
)
# 위에서 만든 tts_service 인스턴스를 임포트
from .tts_service import tts_service 

load_dotenv()

async def run_chat_with_parsing(
    child_id: str, 
    user_input: str,
    # [자료형 정의] 
    # str 2개(child_id, sentence)를 받고, 
    # Awaitable(비동기)을 반환하며, 리턴값은 없는(None) 함수
    tts_func: Callable[[str, str], Awaitable[None]]
):
    sentence_buffer = ""
    full_response_buffer = ""

    async for token in chat_chain_with_history.astream(
        {"input": user_input},
        config={"configurable": {"session_id": child_id}} # session_id 키 사용
    ):
        sentence_buffer += token
        if "\\" in sentence_buffer:
            parts = sentence_buffer.split("\\")
            
            for part in parts[:-1]:
                clean_sentence = part.strip()
                
                if clean_sentence:
                    if full_response_buffer:
                        full_response_buffer += " "
                    full_response_buffer += clean_sentence

                    print(f"\n   [AI 파서] ➡️  TTS 큐에 제출: '{clean_sentence}'")
                    
                    # [호출 방식]
                    # await tts_func(...) : 큐에 put()하는 것을 기다림 (잠깐 블로킹)
                    # asyncio.create_task(...) : 큐에 넣는 것조차 기다리지 않음 (완전 논블로킹)
                    # -> 1번(논블로킹) 요구사항을 극대화하려면 create_task가 가장 좋습니다.
                    asyncio.create_task(
                        tts_func(child_id, clean_sentence)
                    )
                    
                    print("🐥 오리(Raw): ", end="", flush=True)

            sentence_buffer = parts[-1].lstrip()

    # ... (이하 동일) ...
    final_part = sentence_buffer.strip()
    if final_part:
        if full_response_buffer:
            full_response_buffer += " "
        full_response_buffer += final_part
        
        print(f"\n   [AI 파서] ➡️  TTS 큐에 제출(나머지): '{final_part}'")
        # 마지막 문장도 큐에 제출
        asyncio.create_task(
            tts_func(child_id, final_part)
        )

    print("\n" + "-" * 50)
    print(f"💾 [DB 저장용 전체 텍스트]: {full_response_buffer}")