import base64
import os
from loguru import logger
import pyaudio
import requests
import time
import sys
import socketio
import threading
import queue
from datetime import datetime

# common.schemas.socket_event_schema가 없어서 임시 클래스로 대체합니다.
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
sio_robot = socketio.Client(http_session=http_client, logger=True, engineio_logger=False)

# --- PyAudio 설정 (OpenAI PCM 기본값) ---
FORMAT = pyaudio.paInt16  # 16-bit
CHANNELS = 1              # 1-channel (모노)
RATE = 24000              # 24kHz

# PyAudio 리소스를 전역으로 관리 (main의 finally에서 정리)
p = None
stream = None

# --- 스레딩 및 큐 ---
auth_done = threading.Event()

# [수정] 큐의 역할을 명확히 합니다.
# audio_queue는 이제 '완성된 오디오 묶음'을 저장하는 '재생 큐'입니다.
playback_queue = queue.Queue()  

# [신규] 스트리밍 도중 청크를 임시 저장할 버퍼 (리스트)
# Socket.IO 스레드 간 동시 접근을 막기 위해 락(Lock)도 추가합니다.
chunk_buffer = []
streaming_lock = threading.Lock()
is_streaming = False # 스트리밍 상태 플래그


# [신규] '재생 작업자' 스레드 함수 (순차 재생 보장)
def playback_worker():
    """
    [신규] 별도 스레드에서 실행되며,
    'playback_queue'에 완성된 오디오 묶음이 들어오면
    순차적으로 하나씩 재생합니다.
    """
    logger.info("🎧 [Playback Worker] 준비 완료. 재생 큐 대기 중...")
    
    while True:
        try:
            # 큐에서 완성된 오디오 묶음을 가져옴 (없으면 대기)
            # [수정] 프로그램 종료 시 None을 받아 스레드를 종료합니다.
            full_audio_data = playback_queue.get()

            if full_audio_data is None:
                logger.info("🎧 [Playback Worker] 종료 신호(None) 수신. 스레드를 종료합니다.")
                playback_queue.task_done()
                break

            if not stream:
                logger.error("🚨 [Playback Worker] PyAudio 스트림이 없습니다. (재생 불가)")
                playback_queue.task_done()
                continue

            if len(full_audio_data) == 0:
                logger.warning("⚠️ [Playback Worker] 빈 오디오 데이터 수신. (무시)")
                playback_queue.task_done()
                continue
                
            logger.info(f"🎧 [Playback Worker] 큐에서 {len(full_audio_data)} 바이트 묶음 재생 시작...")
            
            # PyAudio 스트림에 전체 데이터 쓰기 (이 작업이 끝날 때까지 블로킹됨)
            stream.write(full_audio_data)
            
            logger.info("✅ [Playback Worker] 재생 완료.")
            time.sleep(0.3)
            playback_queue.task_done()

        except Exception as e:
            logger.error(f"🚨 [Playback Worker] 오류: {e}")
            # [수정] 루프가 계속 돌도록 수정
            if not sio_robot.connected:
                break # 소켓 연결이 끊기면 스레드 종료
    
    logger.info("🎧 [Playback Worker] 스레드 종료됨.")


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
    [수정] 스트림 시작 시, 임시 청크 버퍼(리스트)를 초기화합니다.
    """
    global is_streaming
    
    with streaming_lock: # 스레드 안전하게 플래그 및 버퍼 접근
        logger.info(f"🔊 [Robot] 'STREAM_START' 수신. 임시 청크 버퍼를 초기화합니다.")
        is_streaming = True
        chunk_buffer.clear() # 새 오디오를 받기 위해 리스트를 비움
    
    logger.debug("  - 임시 청크 버퍼 비우기 완료.")

@sio_robot.on(RobotTTSEvents.AUDIO_CHUNK)
def on_audio_chunk(data: dict):
    """
    [수정] is_streaming 상태일 때만 임시 청크 버퍼(리스트)에 쌓습니다.
    """
    global is_streaming, chunk_buffer
    
    frame_b64 = data.get("chunk")
    frame = base64.b64decode(frame_b64)

    with streaming_lock: # 스레드 안전하게 플래그 및 버퍼 접근
        if not is_streaming:
            logger.warning("⚠️ [Robot] 'STREAM_START' 없이 'AUDIO_CHUNK' 수신. (무시)")
            return
        
        # logger.debug("🎧 [Robot] 'AUDIO_CHUNK' 수신. 임시 버퍼에 저장.") # 로그가 너무 많음
        chunk_buffer.append(frame)

@sio_robot.on(RobotTTSEvents.STREAM_END)
def on_stream_end():
    """
    [수정] 스트림 종료 시, 임시 버퍼의 모든 청크를 '하나의 묶음'으로 합쳐
    'playback_queue'에 넣습니다. (재생 X)
    """
    global is_streaming, chunk_buffer, playback_queue
    
    full_audio_data = None

    with streaming_lock: # 스레드 안전하게 플래그 및 버퍼 접근
        if not is_streaming:
            logger.warning("⚠️ [Robot] 'STREAM_START' 없이 'STREAM_END' 수신. (무시)")
            return
        
        logger.info("🏁 [Robot] 'STREAM_END' 수신. 재생 큐에 묶음을 추가합니다.")
        is_streaming = False # 스트리밍 상태 종료

        if not chunk_buffer:
            logger.warning("⚠️ [Robot] 'STREAM_END' 수신했으나 임시 버퍼가 비어있습니다.")
            return

        # 모든 청크를 하나의 바이트 스트림으로 결합
        full_audio_data = b''.join(chunk_buffer)
        chunk_buffer.clear() # 버퍼 비우기
    
    # [수정] 락(lock) 바깥에서 큐에 넣습니다.
    if full_audio_data:
        logger.info(f"  -> {len(full_audio_data)} 바이트 묶음을 재생 큐에 추가.")
        playback_queue.put(full_audio_data)
    

@sio_robot.event
def disconnect():
    logger.info("🔌 [Robot] WebSocket 연결 종료됨.")

# ===================================================================
# 2. 메인 실행 함수
# ===================================================================
def main():
    """메인 실행 로직"""
    global p, stream
    playback_thread = None # [신규] 재생 작업자 스레드 핸들
    
    try:
        # --- 1단계: PyAudio 초기화 ---
        logger.info("🔊 PyAudio 초기화 중...")
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True)
        logger.info("🔊 PyAudio 스트림 열기 성공.")

        # --- [신규] 재생 작업자 스레드 시작 ---
        # daemon=True: 메인 스레드 종료 시 함께 종료됨
        playback_thread = threading.Thread(target=playback_worker, daemon=True)
        playback_thread.start()

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

        logger.info("✅ 로봇 인증 성공! AI 서버의 오디오 스트림 수신 대기 중...")

        # --- 4단계: [수정] 메인 스레드는 연결이 끊길 때까지 대기
        while sio_robot.connected and playback_thread.is_alive():
            time.sleep(1)
            
        logger.info("--- 테스트 종료 (메인 루프 탈출) ---")

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
        
        # [신규] 재생 작업자 스레드에 종료 신호(None) 전송
        if playback_thread and playback_thread.is_alive():
            logger.info("🎧 [Main] 재생 작업자 스레드에 종료 신호 전송...")
            playback_queue.put(None)
            playback_thread.join(timeout=2) # 스레드가 종료될 때까지 최대 2초 대기
            if playback_thread.is_alive():
                logger.warning("⚠️ [Main] 재생 작업자 스레드가 시간 내에 종료되지 않았습니다.")

        logger.info("🔊 PyAudio 리소스 정리 중...")
        if stream:
            stream.stop_stream()
            stream.close()
            logger.info("    - PyAudio 스트림 닫힘.")
        if p:
            p.terminate()
            logger.info("   - PyAudio 인스턴스 종료됨.")
        logger.info("🔊 PyAudio 종료.")

if __name__ == "__main__":
    main()