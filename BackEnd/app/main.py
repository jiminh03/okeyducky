from loguru import logger

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
from fastapi import FastAPI, HTTPException, Request, status

from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ⬇️ 새로 만든 디버그 라우터 임포트
from app.router.debug_repo import router as debug_repo
from app.router.manual_debug_router import router as manual_debug_router

from app.router import auth
from app.router import child
from app.router import dialogue
from app.router import parent
from app.router import robot
from app.router import chat

from app.modules.websocket_module import sio

from app.events.connection_event import *
from app.events.webrtc_event import *
from app.events.tts_event import *
from app.events.robot_face_event import *

from common.modules.db_instance import db, red
import socketio

# 1. (가정) app/exceptions.py 파일에서 모든 예외를 임포트합니다.
#    (경로는 실제 파일 위치에 맞게 수정하세요)
from app.exceptions import * # ⬆️ (ParentNotFound, ChildNotFound, InvalidTokenError 등)

# ⬇️ (추가) Repo 계층의 예외도 임포트합니다.
from common.exceptions import CustomException, DatabaseError, IntegrityViolationError


# Lifespan 컨텍스트 매니저 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작과 종료 시 처리할 로직"""
    logger.info("--- FastAPI app startup: creating DB tables... ---")
    await db.create_db_and_tables()
    logger.info("--- DB tables created successfully. ---")

    # 연결 확인
    try:
        await red.ping()
        logger.info("Redis connect successfully")
    except redis.exceptions.ConnectionError as e:
        logger.info(f"Redis connect fail: {e}")
        exit()
    yield
    logger.info("--- FastAPI app shutdown. ---")

# FastAPI 앱 인스턴스 생성
app = FastAPI(lifespan=lifespan)

# -----------------------------------------------------------------
# 🌟 2. 커스텀 비즈니스 예외 핸들러
# -----------------------------------------------------------------
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """
    'exceptions.py'에 정의된 모든 커스텀 예외를 잡아
    적절한 HTTP 상태 코드로 변환합니다.
    """
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # 404 계열 예외 매핑 (Service)
    if isinstance(exc, (ParentNotFound, ChildNotFound, RobotNotFound, ReportNotFound)):
        status_code = status.HTTP_404_NOT_FOUND
    
    # 401 계열 예외 매핑 (Service)
    elif isinstance(exc, (InvalidCredentialsError, InvalidTokenError)):
        status_code = status.HTTP_401_UNAUTHORIZED
    
    # 403 계열 예외 매핑 (Service)
    elif isinstance(exc, NotOwnerError):
        status_code = status.HTTP_403_FORBIDDEN
    
    # 409 계열 예외 매핑 (Service)
    elif isinstance(exc, ReportAlreadyExistsError):
        status_code = status.HTTP_409_CONFLICT
        
    # 400 계열 예외 매핑 (Service)
    elif isinstance(exc, InvalidRequestError):
        status_code = status.HTTP_400_BAD_REQUEST
    
    # --- ⬇️ [반영된 코드] Repo 계층 예외 매핑 ---
    
    # 409 계열 예외 매핑 (Repo)
    elif isinstance(exc, IntegrityViolationError):
        status_code = status.HTTP_409_CONFLICT
        
    # 500 계열 예외 매핑 (Repo)
    elif isinstance(exc, DatabaseError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
    # --- ⬆️ [반영된 코드] ---

    # 3. (요청 사항) 간단한 에러 로그 출력
    logger.info(f"--- ⚠️  Handled Exception ({status_code}) ---")
    logger.info(f"Path: {request.url.path}")
    logger.info(f"Error: {exc.__class__.__name__} | Detail: {exc.detail}")
    
    # 4. 클라이언트에 HTTP 에러 응답 전송
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.detail}
    )


# -----------------------------------------------------------------
# 🌟 (권장) 3. 예상치 못한 모든 오류 핸들러 (Fallback)
# -----------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    'CustomException'이 아닌, 예상치 못한 모든 오류를 처리합니다.
    """
    
    logger.info(f"--- 🚨 UNHANDLED Exception (500) ---")
    logger.info(f"Path: {request.url.path}")
    logger.info(f"Error: {exc.__class__.__name__} | Detail: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "서버 내부에서 예상치 못한 오류가 발생했습니다."}
    )

# -----------------------------------------------------------------

# --- 라우터 등록 ---

#app.include_router(auth.router)

# ⬇️ (추가) 디버그 라우터를 앱에 포함시킵니다.
# (선택 사항) 운영 환경에서는 이 라우터를 포함하지 않도록
# 환경 변수로 분기 처리를 할 수 있습니다.
app.include_router(parent.router)
app.include_router(child.router)
app.include_router(robot.router)
app.include_router(dialogue.router)
app.include_router(auth.router)
app.include_router(chat.router)

IS_DEBUG = os.getenv("DEBUG", "false").lower() == "true"
if IS_DEBUG:
    logger.info("--- ⚠️  디버그/검증용 라우터를 포함합니다. ---")
    app.include_router(debug_repo)
    app.include_router(manual_debug_router)
else:
    logger.info("--- 릴리즈 모드로 실행합니다. (디버그 라우터 제외) ---")

# Socket.IO 앱을 FastAPI 앱에 마운트
# 이 한 줄이 '/socket.io' 경로로 들어오는
# HTTP 핸드셰이크와 WebSocket 연결을 모두 처리합니다.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 origins 변수 사용 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_app = socketio.ASGIApp(sio, app) # 실행시 진입점


# CORS 미들웨어 설정
# origins = [
#     "http://localhost",
#     "http://localhost:8080",
#     "http://i13a106.p.ssafy.io:8080",
# ]



# 이 파일을 직접 실행할 때를 위한 코드
if __name__ == "__main__":
    uvicorn.run("web.main:socket_app", host="0.0.0.0", port=int(os.getenv("MAIN_SERV_PORT")), reload=True)
