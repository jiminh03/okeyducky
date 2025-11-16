# main.py (또는 router.py)
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser



# 위에서 정의한 모듈들 임포트 가정
from .ai_core.memory import get_memory, get_chat_history
from .ai_core.prompts import child_chat_prompt

# LLM 설정




