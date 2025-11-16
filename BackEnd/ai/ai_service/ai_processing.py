# ai/ai_service/ai_processing.py

import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from common.schemas.dialogue_schema import DialogueLogCreate

# 이전에 만든 모듈들 임포트
from .socket_manager import manager
from .ai_core.memory import get_chat_history
from app.chain import chain_with_history

# (가상) TTS 서비스 (나중에 실제 구현체로 대체)
async def mock_tts_conversion(text: str) -> bytes:
    await asyncio.sleep(0.1) # 변환 시간 시뮬레이션
    return b"mock_audio_data" 

# --- [로직 1] 아이 발화 처리 (AI 생성 -> 문장 분리 -> TTS -> WS) ---
async def process_child_interaction(
    child_id: str, 
    user_text: str, 
    save_log_service
):
    ws = await manager.get_connection(child_id)
    if not ws: return # 연결 끊김

    sentence_buffer = ""
    full_response_accumulator = ""
    
    # 1. LangChain 스트리밍
    async for token in chain_with_history.astream(
        {"input": user_text},
        config={"configurable": {"session_id": child_id}}
    ):
        full_response_accumulator += token
        sentence_buffer += token
        
        # 2. 문장 분리 (구분자 '\' 사용)
        if "\\" in sentence_buffer:
            parts = sentence_buffer.split("\\")
            for part in parts[:-1]:
                clean_text = part.strip()
                if clean_text:
                    await _send_packet_to_robot(child_id, clean_text) # 공통 전송 함수 호출
            
            sentence_buffer = parts[-1].lstrip()

    # 3. 남은 버퍼 처리
    if sentence_buffer.strip():
        await _send_packet_to_robot(child_id, sentence_buffer.strip())

    # 4. [DB] 로봇의 전체 응답 저장
    if full_response_accumulator:
        await save_log_service(DialogueLogCreate(
            child_id=int(child_id),
            content=full_response_accumulator.replace("\\", " "), # 저장할 땐 구분자 제거
            speaker="robot"
        ))
        print(f"💾 [DB] 로봇 응답 저장 완료")


# --- [로직 2] 부모 발화 처리 (메모리 주입 -> TTS -> WS) ---
async def process_parent_interaction(
    child_id: str, 
    parent_text: str
):
    ws = await manager.get_connection(child_id)
    if not ws: return

    # 1. [메모리] AI 기억에 부모 발화 강제 주입 (Context 유지용)
    history = get_chat_history(child_id)
    history.add_message(HumanMessage(content=f"[부모님의 메시지]: {parent_text}"))
    print(f"🧠 [Memory] 부모 메시지 주입 완료: {parent_text}")

    # 2. [전송] 부모의 말은 AI 생성 없이 바로 TTS로 변환하여 전송
    # 부모 말은 감정이 딱히 없으므로 기본값 사용하거나 텍스트 분석 가능
    await _send_packet_to_robot(child_id, parent_text, default_emotion="사랑")


# --- [공통] 로봇 전송 헬퍼 함수 (감정파싱 + TTS + WS) ---
async def _send_packet_to_robot(child_id: str, text: str, default_emotion="평온"):
    # A. 감정 태그 파싱
    emotion = default_emotion
    if "(기쁨)" in text: emotion = "기쁨"
    elif "(슬픔)" in text: emotion = "슬픔"
    
    tts_text = text.replace(f"({emotion})", "").strip()

    # B. 제어 신호 전송 (JSON)
    await manager.send_control_message(child_id, {
        "type": "control",
        "emotion": emotion,
        "text": tts_text
    })

    # C. TTS 변환 및 오디오 전송 (Binary)
    audio_bytes = await mock_tts_conversion(tts_text)
    await manager.send_audio_data(child_id, audio_bytes)
    
    print(f"📡 [WS전송] Type: {'Parent' if default_emotion=='사랑' else 'AI'} | 감정: {emotion} | 텍스트: {tts_text}")