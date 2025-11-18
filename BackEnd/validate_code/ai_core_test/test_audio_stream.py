from loguru import logger

import requests
import time
import sys
import socketio
import sounddevice as sd
import threading
from datetime import datetime

from common.schemas.socket_event_schema import RobotTTSEvents

# --- 설정 ---
BASE_URL = "http://k13a408.p.ssafy.io:8000"
DEBUG_PREFIX = "/_manual_test"

# (참고) 이 테스트는 'validate_scenario.py'를 먼저 실행하여
# 'test_..._@example.com' 사용자가 'SN-TEST-...' 로봇을
# 이미 등록했다고 가정합니다. (또는 아래 값을 실제 DB 값으로 수정)

ROBOT_ID = 1
TEST_ROBOT_SN = "SN-WEBRTC-WEBRTC"

# --- HTTP 클라이언트 (로그인/등록용) ---
http_client = requests.Session()

# --- Socket.IO 클라이언트 ---
sio_robot = socketio.Client(http_session=http_client, logger=True, engineio_logger=True)

# --- 오디오 스트림 설정 ---
SAMPLE_RATE = 24000  # ⬅️ (중요) AI 서버가 생성하는 오디오의 Sample Rate
CHANNELS = 1
DTYPE = "int16"  # ⬅️ (중요) AI 서버가 보내는 오디오 형식 (float32 또는 int16)
audio_stream = None

# 3. PyAudio 설정 (OpenAI PCM 기본값)
# FORMAT = pyaudio.paInt16  # 16-bit
# CHANNELS = 1               # 1-channel (모노)
# RATE = 24000               # 24kHz
# CHUNK_SIZE = 1024

auth_done = threading.Event()
stream_started = threading.Event()


# ===================================================================
# 1. 로봇 클라이언트 이벤트 핸들러
# ===================================================================
@sio_robot.event
def connect():
    global audio_stream
    logger.info("🤖 [Robot] WebSocket 연결 성공.")
    try:
        audio_stream = sd.RawOutputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE
        )
        audio_stream.start()
        stream_started.set()  # ⬅️ 인자 없이 호출해야 합니다.
    except Exception as e:
        logger.info(f"🚨 오디오 스트림 시작 실패: {e}")


@sio_robot.event
def auth_success():
    logger.info("🔑 [Robot] 'AUTH_SUCCESS' 이벤트 수신!")
    auth_done.set()  # 메인 스레드에 "인증 완료" 신호


# ⬇️ --- (수정 1) 'on_stream_start'가 데이터를 받아도 오류가 나지 않도록 수정 --- ⬇️
@sio_robot.on(RobotTTSEvents.STREAM_START)
def on_stream_start(data=None):
    """서버(AI)가 스트림 시작을 알림"""

    logger.info(f"🔊 [Robot] 'STREAM_START' 수신.")
    
# ⬆️ --- (수정 1) 여기까지 --- ⬆️


@sio_robot.on(RobotTTSEvents.AUDIO_CHUNK)  # ⬅️ [수신 2] tts_event.py 참조
def on_audio_chunk(data: bytes):
    """서버(AI)가 보낸 오디오 청크(bytes)를 수신"""
    if audio_stream:
        # logger.info(f"🎧 [Robot] 'AUDIO_CHUNK' 수신 (Size: {len(data)})") # (디버깅용)
        audio_stream.write(data)
    else:
        logger.info("⚠️ [Robot] 오디오 청크를 받았으나, 스트림이 준비되지 않았습니다.")


@sio_robot.on(RobotTTSEvents.STREAM_END)  # ⬅️ [수신 3] tts_event.py 참조
def on_stream_end():
    """서버(AI)가 스트림 종료를 알림"""
    global audio_stream
    logger.info("🏁 [Robot] 'STREAM_END' 수신. 오디오 스트림 종료.")


@sio_robot.event
def disconnect():
    logger.info("🔌 [Robot] WebSocket 연결 종료.")
    if audio_stream:
        audio_stream.stop()
        audio_stream.close()


# ===================================================================
# 2. 메인 실행 함수
# ===================================================================
def main():
    """메인 실행 로직"""
    try:

        # --- 3단계: 로봇으로 로그인 (진짜 토큰 획득) ---
        logger.info("--- [HTTP 3] 로봇 로그인 (토큰 획득) ---")
        robot_log_data = {"robot_id": ROBOT_ID, "serial_number": TEST_ROBOT_SN}
        resp = http_client.post(
            f"{BASE_URL}{DEBUG_PREFIX}/auth/login/robot", json=robot_log_data
        )
        resp.raise_for_status()
        robot_access_token = resp.json()["access_token"]
        logger.info(f"✅ 로봇 로그인 성공 (Token: {robot_access_token[:10]}...)")

        # --- 4단계: WebSocket 연결 및 인증 ---
        auth_payload = {
            "token": robot_access_token,
            "session_type": "robot",
            "robot_id": ROBOT_ID,
        }

        sio_robot.connect(BASE_URL, auth=auth_payload, transports=["websocket"])

        if not auth_done.wait(timeout=10):
            raise RuntimeError("🤖 [Robot] 'AUTH_SUCCESS' 타임아웃")

        logger.info("✅ 로봇 인증 성공! AI 서버의 오디오 스트림 대기 중...")

        # ⬇️ --- (수정 2) Ctrl+C에 반응하도록 'wait()' 대신 루프 사용 --- ⬇️
        while sio_robot.connected:
            time.sleep(1)
        logger.info("--- 테스트 종료 ---")
        # ⬆️ --- (수정 2) 여기까지 --- ⬆️

    except KeyboardInterrupt:
        logger.info("\n--- 🛑 (Ctrl+C) 사용자 요청으로 테스트를 중단합니다. ---")
    except requests.exceptions.ConnectionError as e:
        logger.info(f"--- 🚨 연결 실패: '{e.request.url}'에 서버가 실행되고 있는지 확인하세요. ---")
    except requests.exceptions.HTTPError as e:
        logger.info(f"--- 🚨 HTTP 오류: {e.response.status_code} - {e.response.text} ---")
    except Exception as e:
        logger.info(f"\n--- 🚨 테스트 중단: {e} ---")
        import traceback
        traceback.print_exc()
    finally:
        if sio_robot.connected:
            logger.info("🔌 [Robot] 연결을 정리하고 종료합니다...")
            sio_robot.disconnect()


if __name__ == "__main__":
    main()