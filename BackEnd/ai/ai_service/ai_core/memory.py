# memory.py
import os
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# URL 생성 로직
if REDIS_PASSWORD:
    redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

def get_chat_history(session_id: str):
    # 커스텀 클래스 대신 기본 클래스 사용 (DB 저장은 라우터에서 함)
    return RedisChatMessageHistory(
        session_id=session_id,
        url=redis_url
    )

def get_memory(session_id: str):
    # 최근 10턴만 기억 (LLM 컨텍스트용)
    return ConversationBufferWindowMemory(
        chat_memory=get_chat_history(session_id),
        k=10,
        return_messages=True,
        memory_key="history"
    )