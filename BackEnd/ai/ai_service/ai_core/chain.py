# chain.py
from langchain_core.runnables.history import RunnableWithMessageHistory
from .model import llm
from .prompts import child_chat_prompt
from .output_parsers import parser
from .memory import get_chat_history

# 1. 기본 체인 구성 (Prompt -> LLM -> Parser)
# 이 상태로는 메모리 기능이 없습니다.
basic_chain = child_chat_prompt | llm | parser

# 2. 메모리 기능 주입 (LCEL)
# RunnableWithMessageHistory가 'session_id'를 받아서 
# memory.py의 get_chat_history를 호출해 Redis 기록을 가져와 'history' 자리에 넣어줍니다.
chain_with_history = RunnableWithMessageHistory(
    basic_chain,
    get_chat_history,                  # Redis 기록 가져오는 함수 (Factory)
    input_messages_key="input",        # 프롬프트에서 사용자 입력 변수명
    history_messages_key="history",    # 프롬프트에서 대화 기록 변수명
)