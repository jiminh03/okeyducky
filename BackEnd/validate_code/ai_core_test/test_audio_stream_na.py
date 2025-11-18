import base64
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
sio_robot = socketio.Client(http_session=http_client, logger=True, engineio_logger=False)

# --- PyAudio 설정 (OpenAI PCM 기본값) ---
FORMAT = pyaudio.paInt16  # 16-bit
CHANNELS = 1             # 1-channel (모노)
RATE = 24000             # 24kHz

# PyAudio 리소스를 전역으로 관리 (main의 finally에서 정리)
p = None
stream = None

# --- 스레딩 및 큐 ---
auth_done = threading.Event()
audio_queue = queue.Queue()  # 오디오 청크를 쌓아둘 버퍼

def user_input_playback_worker():
    """
    [신규] 별도 스레드에서 실행되며,
    사용자가 Enter 키를 누르면 큐에 쌓인 오디오를 재생합니다.
    """
    logger.info("🎧 [Playback Worker] 준비 완료. Enter 키를 누르면 버퍼의 오디오를 재생합니다.")
    
    while sio_robot.connected:
        try:
            # Enter 키 입력을 기다림 (블로킹)
            input("\n... Enter 키를 눌러 현재까지 버퍼링된 오디오를 재생합니다 ...\n")

            if not sio_robot.connected:
                break  # input()에서 깨어났는데 연결이 끊겼을 수 있음

            all_chunks = []
            # 큐에 쌓인 모든 데이터를 리스트로 가져오기
            while not audio_queue.empty():
                try:
                    all_chunks.append(audio_queue.get_nowait())
                    audio_queue.task_done()
                except queue.Empty:
                    break
            
            if not all_chunks:
                logger.warning("⚠️ [Playback Worker] 큐에 재생할 오디오 데이터가 없습니다.")
                continue  # 다음 input() 대기로

            # 모든 청크를 하나의 바이트 스트림으로 결합
            full_audio_data = b''.join(all_chunks)
            
            logger.info(f"🎧 [Playback Worker] 총 {len(all_chunks)}개 청크, {len(full_audio_data)} 바이트 재생 시작...")
            
            if stream:
                # PyAudio 스트림에 전체 데이터 쓰기
                stream.write(full_audio_data)
                logger.info("✅ [Playback Worker] 재생 완료.")
            else:
                logger.error("🚨 [Playback Worker] PyAudio 스트림이 없습니다.")

        except (EOFError, KeyboardInterrupt):
            logger.info("🛑 [Playback Worker] 입력 스레드 종료 요청.")
            break
        except Exception as e:
            logger.error(f"🚨 [Playback Worker] 오류: {e}")
            if not sio_robot.connected:
                break
    
    logger.info("🎧 [Playback Worker] 스레드를 종료합니다.")


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
    [수정] 이벤트를 무시하고 로그만 남깁니다.
    """
    logger.info(f"🔊 [Robot] 'STREAM_START' 수신 (로직 무시).")

@sio_robot.on(RobotTTSEvents.AUDIO_CHUNK)
def on_audio_chunk(data: dict):
    """
    [수정] 청크를 큐에 쌓기만 합니다. (재생 X)
    """
    # logger.debug("🎧 [Robot] 'AUDIO_CHUNK' 수신. 큐에 저장.") # 로그가 너무 많으므로 주석 처리
    frame_b64 = data.get("chunk")
    frame = base64.b64decode(frame_b64)
    audio_queue.put(frame)

@sio_robot.on(RobotTTSEvents.STREAM_END)
def on_stream_end():
    """
    [수정] 이벤트를 무시하고 로그만 남깁니다.
    """
    logger.info("🏁 [Robot] 'STREAM_END' 수신 (로직 무시).")
    # [삭제] 재생 로직 및 disconnect 로직

@sio_robot.event
def disconnect():
    logger.info("🔌 [Robot] WebSocket 연결 종료됨.")
    logger.info("   (Enter 입력 대기 중이라면, Enter를 한 번 더 눌러야 프로그램이 종료됩니다.)")

# ===================================================================
# 2. 메인 실행 함수
# ===================================================================
def main():
    """메인 실행 로직"""
    global p, stream
    input_thread = None  # 사용자 입력 스레드 핸들
    
    try:
        # --- 1단계: PyAudio 초기화 ---
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

        logger.info("✅ 로봇 인증 성공! AI 서버의 오디오 스트림 수신 대기 중...")

        # --- 4단계: [수정] 사용자 입력 스레드 시작 ---
        # daemon=True: 메인 스레드 종료 시 함께 종료됨
        input_thread = threading.Thread(target=user_input_playback_worker, daemon=True)
        input_thread.start()

        # [수정] 메인 스레드는 연결이 끊기거나 (서버/클라이언트 요청) 
        # input_thread가 종료될 때까지 대기합니다.
        while sio_robot.connected and input_thread.is_alive():
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