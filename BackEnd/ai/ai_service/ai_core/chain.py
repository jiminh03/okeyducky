# chain.py
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage
from typing import List

from .model import chat_llm, report_llm
from .prompts import child_chat_prompt, summary_prompt, analysis_prompt
from .output_parsers import str_parser, json_parser
from .memory import get_chat_history

def trim_messages(messages: List[BaseMessage], k: int = 10):
    """
    메모리 창(k=10)을 구현합니다.
    항상 최신 k개의 메시지만 반환합니다.
    """
    return messages[-k:]

chat_chain = child_chat_prompt | chat_llm | str_parser
summary_chain = summary_prompt | report_llm | json_parser
analysis_chain = analysis_prompt | report_llm | str_parser

chain_with_trimming = (
    RunnablePassthrough.assign(
        history=lambda x: trim_messages(x["history"])
    )
    | chat_chain
)

chat_chain_with_history = RunnableWithMessageHistory(
    chain_with_trimming,  # k=10 로직이 포함된 체인을 감쌈
    get_chat_history,     # memory.py의 팩토리 함수
    input_messages_key="input",
    history_messages_key="history",
)