from dotenv import load_dotenv
# .env 파일 로드
load_dotenv()

import asyncio
from datetime import datetime, timezone
import os
from typing import Any, Dict

import httpx
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, HTTPException

from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# ⬇️ 새로 만든 디버그 라우터 임포트
from app.router.debug_router import router as debug_router



from common.modules.db_instance import db, red
import socketio
# Lifespan 컨텍스트 매니저 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작과 종료 시 처리할 로직"""
    print("--- FastAPI app startup: creating DB tables... ---")
    await db.create_db_and_tables()
    print("--- DB tables created successfully. ---")

    # 연결 확인
    try:
        await red.ping()
        print("Redis connect successfully")
    except redis.exceptions.ConnectionError as e:
        print(f"Redis connect fail: {e}")
        exit()
    yield
    print("--- FastAPI app shutdown. ---")

# FastAPI 앱 인스턴스 생성
app = FastAPI(lifespan=lifespan)

# --- 라우터 등록 ---

#app.include_router(auth.router)

# ⬇️ (추가) 디버그 라우터를 앱에 포함시킵니다.
# (선택 사항) 운영 환경에서는 이 라우터를 포함하지 않도록
# 환경 변수로 분기 처리를 할 수 있습니다.
IS_DEBUG = os.getenv("DEBUG", "false").lower() == "true"
if IS_DEBUG:
    print("--- ⚠️  디버그/검증용 라우터를 포함합니다. ---")
    app.include_router(debug_router)
else:
    print("--- 릴리즈 모드로 실행합니다. (디버그 라우터 제외) ---")

# Socket.IO 앱을 FastAPI 앱에 마운트
# 이 한 줄이 '/socket.io' 경로로 들어오는
# HTTP 핸드셰이크와 WebSocket 연결을 모두 처리합니다.
#socket_app = socketio.ASGIApp(sio, app) # 실행시 진입점


# CORS 미들웨어 설정
# origins = [
#     "http://localhost",
#     "http://localhost:8080",
#     "http://i13a106.p.ssafy.io:8080",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 실제 운영 환경에서는 origins 변수 사용 권장
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 이 파일을 직접 실행할 때를 위한 코드
if __name__ == "__main__":
    uvicorn.run("web.main:socket_app", host="0.0.0.0", port=int(os.getenv("MAIN_SERV_PORT")), reload=True)
