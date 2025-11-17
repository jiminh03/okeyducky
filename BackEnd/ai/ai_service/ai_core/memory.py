# memory.py
import os
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# URL 생성 로직
if REDIS_PASSWORD:
    redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

def get_chat_history(child_id: str) -> BaseChatMessageHistory:
    """
    RunnableWithMessageHistory가 이 함수를 호출합니다.
    인자 이름('child_id')이 config의 키와 일치해야 합니다.
    """
    return RedisChatMessageHistory(
        session_id=child_id,
        url=redis_url
    )
