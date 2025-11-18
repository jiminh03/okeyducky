from loguru import logger
import pyaudio  # sounddevice 대신 pyaudio 사용
import requests
import time
import sys
import socketio
# import sounddevice as sd  <- [삭제]
import threading
import queue
from datetime import datetime

# common.schemas.socket_event_schema가 없어서 임시 클래스로 대체합니다.
# 실제 환경에서는 이 부분을 지우고 원래 import를 사용하세요.
class RobotTTSEvents:
    STREAM_START = "server:stream_start"
    AUDIO_CHUNK = "server:audio_chunk"
    STREAM_END = "server:stream_end"

# --- 설정 ---
BASE_URL = "http://k13a408.p.ssafy.io:8000"
DEBUG_PREFIX = "/_manual_test"
ROBOT_ID = 1
TEST_ROBOT_SN = "SN-WEBRTC-WEBRTC"

# --- HTTP 클라이언트 ---
http_client = requests.Session()

# --- Socket.IO 클라이언트 ---
sio_robot = socketio.Client(http_session=http_client, logger=True, engineio_logger=True)

# --- PyAudio 설정 (OpenAI PCM 기본값) ---
FORMAT = pyaudio.paInt16  # 16-bit
CHANNELS = 1             # 1-channel (모노)
RATE = 24000             # 24kHz

# [수정] PyAudio 리소스를 전역으로 관리 (main의 finally에서 정리)
p = None
stream = None

# --- 스레딩 및 큐 ---
auth_done = threading.Event()
audio_queue = queue.Queue()
# [삭제] audio_thread = None (더 이상 별도 워커 스레드를 사용하지 않음)
# [삭제] audio_playback_worker 함수 (로직이 on_stream_end로 이동)

# ===================================================================
# 1. 로봇 클라이언트 이벤트 핸들러
# ===================================================================
@sio_robot.event
def connect():
    logger.info("🤖 [Robot] WebSocket 연결 성공.")

@sio_robot.event
def auth_success():
    logger.info("🔑 [Robot] 'AUTH_SUCCESS' 이벤트 수신!")
    auth_done.set()

@sio_robot.on(RobotTTSEvents.STREAM_START)
def on_stream_start(data=None):
    """
    [수정] 스트림 시작 시, 버퍼(큐)를 비우고 대기합니다.
    """
    logger.info(f"🔊 [Robot] 'STREAM_START' 수신. 버퍼(큐)를 비웁니다...")
    # 큐 비우기
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break
    logger.info("✅ [Robot] 버퍼 준비 완료. 청크 수신 대기 중...")

@sio_robot.on(RobotTTSEvents.AUDIO_CHUNK)
def on_audio_chunk(data: bytes):
    """
    [수정] 청크를 큐에 쌓기만 합니다. (재생 X)
    """
    # logger.debug("🎧 [Robot] 'AUDIO_CHUNK' 수신. 큐에 저장.") # 너무 많으므로 주석 처리
    audio_queue.put(data)

@sio_robot.on(RobotTTSEvents.STREAM_END)
def on_stream_end():
    """
    [수정] 스트림 종료 시, 큐에 쌓인 모든 청크를 한 번에 재생합니다.
    """
    logger.info("🏁 [Robot] 'STREAM_END' 수신. 버퍼 재생 시작.")
    
    all_chunks = []
    try:
        # 큐에 쌓인 모든 데이터를 리스트로 가져오기
        while not audio_queue.empty():
            try:
                all_chunks.append(audio_queue.get_nowait())
                audio_queue.task_done()
            except queue.Empty:
                break
        
        if not all_chunks:
            logger.warning("⚠️ [Robot] 큐에 재생할 오디오 데이터가 없습니다.")
            return

        # 모든 청크를 하나의 바이트 스트림으로 결합
        full_audio_data = b''.join(all_chunks)
        
        logger.info(f"🎧 [Robot] 총 {len(all_chunks)}개 청크, {len(full_audio_data)} 바이트 재생 시작...")
        
        if stream:
            # PyAudio 스트림에 전체 데이터 쓰기
            stream.write(full_audio_data)
            logger.info("✅ [Robot] 전체 오디오 재생 완료.")
        else:
            logger.error("🚨 [Robot] PyAudio 스트림이 초기화되지 않았습니다.")

    except Exception as e:
        logger.error(f"🚨 [Robot] 오디오 재생 중 오류: {e}")
    finally:
        # [수정] 테스트를 위해 재생이 끝나면 연결 해제
        if sio_robot.connected:
            logger.info("🔌 [Robot] 테스트 완료. 연결 해제 요청...")
            sio_robot.disconnect()


@sio_robot.event
def disconnect():
    logger.info("🔌 [Robot] WebSocket 연결 종료됨.")
    # [삭제] audio_queue.put(None) (더 이상 필요 없음)

# ===================================================================
# 2. 메인 실행 함수
# ===================================================================
def main():
    """메인 실행 로직"""
    global p, stream  # [수정] 전역 변수 p, stream 사용
    
    try:
        # --- [수정] 1단계: PyAudio 초기화 ---
        logger.info("🔊 PyAudio 초기화 중...")
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True)
        logger.info("🔊 PyAudio 스트림 열기 성공.")

        # --- 2단계: 로봇으로 로그인 (진짜 토큰 획득) ---
        logger.info("--- [HTTP] 로봇 로그인 (토큰 획득) ---")
        robot_log_data = {"robot_id": ROBOT_ID, "serial_number": TEST_ROBOT_SN}
        resp = http_client.post(
            f"{BASE_URL}{DEBUG_PREFIX}/auth/login/robot", json=robot_log_data
        )
        resp.raise_for_status()
        robot_access_token = resp.json()["access_token"]
        logger.info(f"✅ 로봇 로그인 성공 (Token: {robot_access_token[:10]}...)")

        # --- 3단계: WebSocket 연결 및 인증 ---
        auth_payload = {
            "token": robot_access_token,
            "session_type": "robot",
            "robot_id": ROBOT_ID,
        }
        sio_robot.connect(BASE_URL, auth=auth_payload, transports=["websocket"])

        if not auth_done.wait(timeout=10):
            raise RuntimeError("🤖 [Robot] 'AUTH_SUCCESS' 타임아웃")

        logger.info("✅ 로봇 인증 성공! AI 서버의 오디오 스트림 대기 중...")

        while sio_robot.connected:
            time.sleep(1)
        logger.info("--- 테스트 종료 (연결 해제됨) ---")

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
            logger.info("🔌 [Main] 메인 스레드: 연결 정리를 시도합니다...")
            sio_robot.disconnect()
        
        # [수정] PyAudio 리소스 정리
        logger.info("🔊 PyAudio 리소스 정리 중...")
        if stream:
            stream.stop_stream()
            stream.close()
            logger.info("   - PyAudio 스트림 닫힘.")
        if p:
            p.terminate()
            logger.info("   - PyAudio 인스턴스 종료됨.")
        logger.info("🔊 PyAudio 종료.")

if __name__ == "__main__":
    main()