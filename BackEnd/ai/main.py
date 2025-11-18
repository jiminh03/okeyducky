from loguru import logger

from dotenv import load_dotenv
# .env 파일 로드 (가장 먼저 실행)
load_dotenv()

# --- LLM 캐시 설정 ---
# Redis 인스턴스가 정의된 후에 LLM 캐시를 전역으로 설정합니다.
from common.modules.db_instance import red
from langchain_core.globals import set_llm_cache
from langchain_community.cache import AsyncRedisCache

# LangChain의 LLM 응답을 Redis에 캐시하도록 설정
# (참고: 대화형 체인은 history가 매번 바뀌므로 캐시가 잘 안될 수 있습니다)
set_llm_cache(AsyncRedisCache(red.redis_client))

# --- 기본 모듈 임포트 ---
import asyncio
import os
import redis.asyncio as redis
import socketio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# --- DB 및 Redis 인스턴스 ---
from common.modules.db_instance import db

# [신규] AI 서비스 라우터
from ai.routers import ai_chat, ai_report

# 웹소켓
from ai.websocket import sio_ai

from ai.request import *

from common.schemas.session_schema import SessionType

BASE_URL = os.getenv("BACKEND_URL")
SESSION_TYPE = SessionType.AI_SERV.value

# --- 애플리케이션 Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작과 종료 시 처리할 로직"""
    logger.info("--- AI Server startup: creating DB tables... ---")
    await db.create_db_and_tables()
    logger.info("--- DB tables created successfully. ---")

    # Redis 연결 확인
    try:
        await red.ping()
        logger.info("--- Redis connect successfully. ---")
    except redis.exceptions.ConnectionError as e:
        logger.info(f"--- Redis connect fail: {e} ---")
        exit() # Redis 연결 실패 시 앱 종료

    # [수정] BE 서버에 비동기(논블로킹) 연결
    async def connect_to_be():
        while True:
            try:
                await sio_ai.connect(
                    BASE_URL, 
                    transports=['websocket'], 
                    auth={"session_type": SESSION_TYPE, 'token': "ai"},
                )
                break # 연결 성공 시 루프 탈출
            except socketio.exceptions.ConnectionError as e:
                logger.info(f"--- BE 서버 연결 실패: {e}. 5초 후 재시도... ---")
                await asyncio.sleep(5)
    
    # 백그라운드에서 BE 서버 연결 및 대기 시작
    # sio_ai.wait()는 connect_to_be 안에서 실행되어야 함
    asyncio.create_task(connect_to_be())
    
    yield # 즉시 FastAPI 앱 시작
    
    # --- 종료 로직 ---
    if sio_ai.sid:
        await sio_ai.disconnect()
    logger.info("--- FastAPI app shutdown. ---")

# FastAPI 앱 인스턴스 생성
app = FastAPI(lifespan=lifespan)

# --- 미들웨어 설정 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 origins 변수 사용 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_chat.router)
app.include_router(ai_report.router)

# 이 파일을 직접 실행할 때를 위한 코드
if __name__ == "__main__":
    uvicorn.run("ai.main:app", host="0.0.0.0", port=int(os.getenv("AI_SERV_PORT")), reload=True)
