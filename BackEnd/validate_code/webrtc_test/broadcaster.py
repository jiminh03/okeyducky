import asyncio
from datetime import datetime
import json
import logging
import cv2
import numpy as np
import pyaudio
import requests
import socketio # ⬅️ aiohttp 대신 socketio 클라이언트 사용
from typing import Dict, Any # ⬅️ [변경] Pydantic 모델 대신 Dict 사용
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack
from aiortc import AudioStreamTrack, VideoStreamTrack
from av import AudioFrame, VideoFrame
from fractions import Fraction as Rational

# ⬇️ [변경] webrtc_event.py와 스키마 임포트
from common.schemas.socket_event_schema import WebRTCEvents
from common.schemas.session_schema import SessionType

# --- HTTP 클라이언트 (로그인/등록용) ---
http_client = requests.Session()

# --- 설정 ---
BASE_URL = "http://127.0.0.1:8000" 
DEBUG_PREFIX = "/_manual_test" 

# --- 테스트용 데이터 ---
TS = int(datetime.now().timestamp())
TEST_EMAIL = f"webrtc_test_{TS}@example.com"
TEST_PASSWORD = "pw123"
TEST_ROBOT_SN = f"SN-WEBRTC-{TS}"

# --- 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("broadcaster")

# [변경] Socket.IO 서버 주소 (FastAPI 서버)
SIGNALING_URL = "http://127.0.0.1:8000" 

# [변경] 단일 PeerConnection
pc = RTCPeerConnection()
sio = socketio.AsyncClient(logger=True, engineio_logger=True)

# ⬇️ [추가] 플레이스홀더: 이 값들은 broadcaster가 알아야 함
ACCESS_TOKEN = "YOUR_VALID_JWT_TOKEN_HERE" # ⬅️ (필수) 로봇 로그인 토큰
PARENT_ID = 1 # ⬅️ (필수) 이 브로드캐스터(로봇)가 통화할 부모의 ID
ROBOT_ID = 1 # ⬅️ (필수) 이 브로드캐스터(로봇) 자신의 ID
SESSION_TYPE = "robot" # ⬅️ (필수)

# --- 미디어 트랙 (원본 코드와 동일) ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
FRAMES_PER_BUFFER = 960 
AUDIO_PTIME = 0.020  

class PyAudioStreamTrack(AudioStreamTrack):
    # (원본 코드와 동일)
    def __init__(self):
        super().__init__()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            input=True, frames_per_buffer=FRAMES_PER_BUFFER,
        )
        self.samples_per_frame = int(RATE * AUDIO_PTIME)
        logger.info("PyAudioStreamTrack initialized (mic input)")

    async def recv(self):
        data = await asyncio.to_thread(self.stream.read, FRAMES_PER_BUFFER)
        frame = AudioFrame.from_ndarray(
            np.frombuffer(data, dtype=np.int16).reshape(1, -1),
            format="s16", layout="mono",
        )
        frame.sample_rate = RATE
        frame.pts = int(self.stream.get_time() * RATE)
        frame.time_base = Rational(1, RATE)
        return frame

    def stop(self):
        super().stop()
        if self.stream: self.stream.stop_stream(); self.stream.close()
        if self.p: self.p.terminate()
        logger.info("PyAudioStreamTrack stopped")


class OpenCVVideoStreamTrack(VideoStreamTrack):
    # (원본 코드와 동일)
    def __init__(self, capture):
        super().__init__()
        self.capture = capture
        self.frame_count = 0
        logger.info("OpenCVVideoStreamTrack initialized (webcam input)")

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = await asyncio.to_thread(self.capture.read)
        if not ret:
            logger.warning("Failed to read frame from webcam")
            return VideoFrame(width=640, height=480, pts=pts, time_base=time_base)

        frame_yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV_I420)
        video_frame = VideoFrame.from_ndarray(frame_yuv, format="yuv420p")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

    def stop(self):
        super().stop()
        if self.capture: self.capture.release()
        logger.info("OpenCVVideoStreamTrack stopped")
# --- 미디어 트랙 끝 ---

pc=None
video_track=None
audio_track=None

# --- [변경] WebRTC 요청 이벤트 핸들러 ---
@sio.on(WebRTCEvents.CAST_REQUESTED)
async def on_cast_requested(data: Dict[str, Any]):
    """
    (Point 1) 뷰어(Parent)가 'REQUEST_CAST'를 보내 서버가 중계한 이벤트
    data 에는 {'opp_type': 'parent', 'opp_id': 123}가 들어옵니다.
    """
    try:
        parent_id = int(data["opp_id"])
        logger.info(f"⬇️ 'CAST_REQUESTED' 수신 (from parent_id: {parent_id}). PC 설정 시작...")
    except (KeyError, ValueError, TypeError):
        logger.error(f"잘못된 'CAST_REQUESTED' 데이터 수신: {data}")
        return

    # 1. (Point 2) 뷰어(Parent) 전용 PeerConnection 생성
    pc = RTCPeerConnection()

    # 2. (Point 2) 미디어 트랙 추가
    pc.addTrack(video_track)
    pc.addTrack(audio_track)

    # 3. (Point 2) 이벤트 핸들러 설정
    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        """ICE Candidate 생성 시 서버로 전송 (Parent에게)"""
        if candidate:
            logger.info(f"ICE Candidate 생성 (for parent_id {parent_id})...")
            await sio.emit(
                WebRTCEvents.SEND_ICE_CANDIDATE, 
                (SessionType.PARENT.value, parent_id, candidate.to_dict()) 
                # (opp_clnt_type, opp_clnt_id, data)
            )

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"PC state for {parent_id}: {pc.connectionState}")
        if pc.connectionState == "failed" or pc.connectionState == "closed":
            await pc.close()
            logger.info("PeerConnection closed.")
    
    try:
        # 4. (Point 1) 'ACCPET_REQUEST' 전송
        logger.info(f"⬆️ 'ACCPET_REQUEST' 전송 (to parent_id: {parent_id})...")
        await sio.emit(
            WebRTCEvents.ACCPET_REQUEST,
            (SessionType.PARENT.value, parent_id)
            # (opp_clnt_type, opp_clnt_id)
        )
        
        # 5. (Point 3) Offer 생성 및 전송
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        offer_packet = {"type": offer.type, "sdp": offer.sdp}
        
        logger.info(f"⬆️ 'SEND_OFFER' 전송 (to parent_id: {parent_id})...")
        await sio.emit(
            WebRTCEvents.SEND_OFFER,
            (SessionType.PARENT.value, parent_id, offer_packet)
            # (offer_clnt_type, offer_clnt_id, offer_data)
        )

    except Exception as e:
        logger.error(f"Offer 생성 또는 전송 실패 (for parent_id {parent_id}): {e}", exc_info=True)
        await pc.close()
        logger.info("PeerConnection closed.")

# --- [변경] WebRTC 이벤트 핸들러 ---
# @pc.on("icecandidate")
# async def on_icecandidate(candidate):
#     """ICE Candidate 생성 시 서버로 전송 (Parent에게)"""
#     if candidate:
#         logger.info(f"ICE Candidate 생성: {candidate.candidate[:30]}...")
#         await sio.emit(
#             WebRTCEvents.SEND_ICE_CANDIDATE, 
#             (SessionType.PARENT.value, PARENT_ID, candidate.to_dict()) 
#             # (opp_clnt_type, opp_clnt_id, data)
#         )

# @pc.on("connectionstatechange")
# async def on_connectionstatechange():
#     logger.info(f"PC Connection State: {pc.connectionState}")
#     if pc.connectionState == "failed" or pc.connectionState == "closed":
#         await pc.close()
#         logger.info("PeerConnection closed.")

# --- [변경] Socket.IO 이벤트 핸들러 ---
@sio.event
async def connect():
    """서버 연결 성공 시 (1단계)"""
    logger.info(f"Socket.IO 연결 성공 (SID: {sio.sid}). 인증 시도...")
    # 'connection_event.py'의 'auth' 파라미터에 맞게 전송
    await sio.emit("auth", {"token": ACCESS_TOKEN, "session_type": SESSION_TYPE})

@sio.event
async def auth_success():
    """서버 인증 성공 시 (2단계) - WebRTC Offer 등록"""
    logger.info("🔑 Socket.IO 인증 성공! WebRTC Offer 등록을 시작합니다.")


@sio.on(WebRTCEvents.NEW_ANSWER)
async def on_new_answer(answer_data: Dict[str, Any]): # ⬅️ Dict 타입 명시
    """Parent가 보낸 Answer 수신 (4단계)"""
    logger.info("⬇️ 'NEW_ANSWER' 수신!")
    try:
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        await pc.setRemoteDescription(answer)
        logger.info("✅ RemoteDescription (Answer) 설정 완료.")
    except KeyError:
        logger.error(f"Answer 처리 실패: 'sdp' 또는 'type' 키가 없습니다. {answer_data}")
    except Exception as e:
        logger.error(f"Answer 처리 실패: {e}", exc_info=True)

@sio.on(WebRTCEvents.NEW_ICE_CANDIDATE)
async def on_new_ice_candidate(data: Dict[str, Any]): # ⬅️ Dict 타입 명시
    """Parent가 보낸 ICE Candidate 수신 (5단계)"""
    logger.info(f"⬇️ 'NEW_ICE_CANDIDATE' (from Parent) 수신")
    try:
        candidate = data["candidate"]
        await pc.addIceCandidate(
            candidate["candidate"],
            sdpMid=candidate["sdpMid"],
            sdpMLineIndex=candidate["sdpMLineIndex"]
        )
    except KeyError:
        logger.error(f"ICE Candidate 처리 실패: 'candidate' 키가 없습니다. {data}")
    except Exception as e:
        logger.error(f"ICE Candidate 추가 실패: {e}", exc_info=True)

@sio.event
async def disconnect():
    logger.warning("Socket.IO 연결 종료.")
    await pc.close()


async def main():
    global video_track, audio_track
    
    # 미디어 소스 초기화 (원본 코드와 동일)
    try:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            logger.error("웹캠을 열 수 없습니다.")
            return
            
        video_track = OpenCVVideoStreamTrack(cap)
        audio_track = PyAudioStreamTrack()
        
    except Exception as e:
        logger.error(f"미디어 장치 초기화 실패: {e}")
        return

    # [변경] Socket.IO 서버 연결 및 대기
    try:
        await sio.connect(SIGNALING_URL, transports=['websocket'])
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        logger.error(f"시그널링 서버 연결 실패: {e}")
    except KeyboardInterrupt:
        logger.info("Broadcaster shutting down...")
    finally:
        if sio.connected:
            await sio.disconnect()
        if pc.connectionState != "closed":
            await pc.close()
        
        video_track.stop()
        audio_track.stop()
        
        logger.info("Cleanup complete.")


if __name__ == "__main__":
    parent_id, child_id, robot_id, access_token = None, None, None, None

    # === 1단계: HTTP로 사전 설정 (회원가입, 로그인, 자녀/로봇 등록) ===
    print("--- [HTTP 1] 회원가입 ---")
    reg_data = {"parent_name": "WebRTC Test", "email": TEST_EMAIL, "password": TEST_PASSWORD}
    resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/register", json=reg_data)
    parent_id = resp.json()["parent_id"]
    print(f"✅ Parent 생성 (ID: {parent_id})")

    print("--- [HTTP 2] 로그인 (토큰 획득) ---")
    log_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/login", json=log_data)
    assert resp.status_code == 200, f"로그인 실패: {resp.text} (auth_service.py 수정 필요)"
    access_token = resp.json()["access_token"]
    print(f"✅ 로그인 성공 (Token: {access_token})")

    print("--- [HTTP 3] 자녀 등록 ---")
    child_data = {"name": "WebRTC Child", "gender": "male", "birth_date": "2020-01-01", "parent_id": parent_id}
    resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/child", headers={"Authorization": f"Bearer {access_token}"}, json=child_data)
    child_id = resp.json()["child_id"]
    print(f"✅ Child 생성 (ID: {child_id})")

    print("--- [HTTP 4] 로봇 등록 ---")
    robot_data = {"serial_number": TEST_ROBOT_SN, "child_id": child_id}
    resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/robot", headers={"Authorization": f"Bearer {access_token}"}, json=robot_data)
    robot_id = resp.json()["robot_id"]
    print(f"✅ Robot 생성 (ID: {robot_id})")

    print("--- [HTTP 5] 로봇 로그인 (토큰 획득) ---")
    log_data = {"robot_id": robot_id, "serial_number": TEST_ROBOT_SN}
    resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/login/robot", json=log_data)
    assert resp.status_code == 200, f"로그인 실패: {resp.text} (auth_service.py 수정 필요)"
    robot_access_token = resp.json()["access_token"]
    print(f"✅ 로그인 성공 (Token: {robot_access_token[:10]}...)")
    ROBOT_ID = robot_id
    ACCESS_TOKEN = robot_access_token

    asyncio.run(main())
