from loguru import logger
import requests
import time
import sys
import socketio
import sounddevice as sd
import threading
import queue
from datetime import datetime

from common.schemas.socket_event_schema import RobotTTSEvents

# --- 설정 ---
BASE_URL = "http://k13a408.p.ssafy.io:8000"
DEBUG_PREFIX = "/_manual_test"
ROBOT_ID = 1
TEST_ROBOT_SN = "SN-WEBRTC-WEBRTC"

# --- HTTP 클라이언트 ---
http_client = requests.Session()

# --- Socket.IO 클라이언트 ---
sio_robot = socketio.Client(http_session=http_client, logger=True, engineio_logger=True)

# --- 오디오 스트림 설정 (OpenAI PCM 표준) ---
SAMPLE_RATE = 24000
CHANNELS = 1
DTYPE = "int16"
audio_stream = None

auth_done = threading.Event()
audio_queue = queue.Queue()
audio_thread = None

def audio_playback_worker(stream_instance: sd.RawOutputStream):
    """
    [수정] 재생할 stream 객체를 인자로 직접 받습니다.
    global audio_stream 변수를 참조하지 않습니다.
    """
    logger.info("🎧 [Audio Worker] 재생 스레드 시작.")
    
    # [삭제] while audio_stream is None: ... (더 이상 필요 없음)
        
    logger.info("🎧 [Audio Worker] 스트림 감지. 재생 시작...")
    try:
        while True:
            chunk = audio_queue.get()
            
            if chunk is None:  # 종료 신호
                audio_queue.task_done()
                logger.info("🎧 [Audio Worker] 종료 신호 수신. 재생 완료.")
                break
                
            # [수정] 인자로 받은 stream_instance를 직접 사용
            if stream_instance:
                try:
                    stream_instance.write(chunk)
                except Exception as e:
                    logger.error(f"🚨 stream_instance.write() 오류: {e}")
            
            audio_queue.task_done()
            
    except Exception as e:
        logger.error(f"🚨 오디오 재생 스레드 예외: {e}")
    finally:
        # [수정] 인자로 받은 stream_instance를 정리
        logger.info("🎧 [Audio Worker] 오디오 스트림 정리 중...")
        if stream_instance:
            stream_instance.stop()
            stream_instance.close()
        
        if sio_robot.connected:
            logger.info("🔌 [Audio Worker] 재생 완료. BE 서버와 연결 해제 요청...")
            sio_robot.disconnect()

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
    [수정] 스트림을 열고, 스레드 시작 시 스트림 객체를 인자로 전달합니다.
    """
    global audio_thread # audio_thread 핸들 관리는 필요
    logger.info(f"🔊 [Robot] 'STREAM_START' 수신. 오디오 스트림 준비...")
    try:
        # 큐 비우기
        while not audio_queue.empty():
            audio_queue.get_nowait()
        
        # [수정] 'local_stream'이라는 지역 변수로 생성
        local_stream = sd.RawOutputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE
        )
        local_stream.start()
        
        # [수정] 오디오 재생 전용 스레드 시작 (기존 스레드가 있다면 종료 대기)
        if audio_thread and audio_thread.is_alive():
            audio_queue.put(None) # 이전 스레드 종료
            audio_thread.join(timeout=2)
            
        # [수정] target에 args로 local_stream을 전달
        audio_thread = threading.Thread(
            target=audio_playback_worker, 
            args=(local_stream,),  # <-- 핵심 수정
            daemon=True
        )
        audio_thread.start()

    except Exception as e:
        logger.error(f"🚨 오디오 스트림 시작 실패: {e}")
        audio_queue.put(None) # 워커 스레드 종료

@sio_robot.on(RobotTTSEvents.AUDIO_CHUNK)
def on_audio_chunk(data: bytes):
    """
    [유지] 청크를 큐에 넣습니다. (Pending)
    """
    audio_queue.put(data)

@sio_robot.on(RobotTTSEvents.STREAM_END)
def on_stream_end():
    """
    [수정] 종료 신호(None)만 큐에 넣고, 즉시 반환합니다. (블로킹 X)
    """
    logger.info("🏁 [Robot] 'STREAM_END' 수신. 큐에 종료 신호 전송.")
    audio_queue.put(None) 
    # [삭제] audio_thread.join(), stream.stop/close(), sio_robot.disconnect()

@sio_robot.event
def disconnect():
    logger.info("🔌 [Robot] WebSocket 연결 종료됨.")
    # [수정] 혹시 모를 상황 대비 큐 워커 종료
    audio_queue.put(None)

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

        while sio_robot.connected:
            time.sleep(1)
        logger.info("--- 테스트 종료 ---")

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
            logger.info("🔌 [Robot] 메인 스레드: 연결 정리를 시도합니다...")
            sio_robot.disconnect()
        
        # [수정] Sounddevice 리소스 정리
        sd.stop() # 모든 sounddevice 스트림 정지
        logger.info("🔊 Sounddevice 종료.")

if __name__ == "__main__":
    main()