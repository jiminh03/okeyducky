import os
from dotenv import load_dotenv
# .env 파일 로드
load_dotenv()

import asyncio
from datetime import datetime
import json
import logging
import os
import cv2
import numpy as np
import pyaudio
import requests
import socketio # ⬅️ aiohttp 대신 socketio 클라이언트 사용
from typing import Dict, Any # ⬅️ [변경] Pydantic 모델 대신 Dict 사용
from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack
from aiortc import AudioStreamTrack, VideoStreamTrack
from av import AudioFrame, VideoFrame
from fractions import Fraction as Rational
from aiortc.sdp import candidate_from_sdp  # ⬅️ [추가] candidate_from_sdp 임포트


# ⬇️ [변경] webrtc_event.py와 스키마 임포트
from common.schemas.socket_event_schema import WebRTCEvents
from common.schemas.session_schema import SessionType

# --- HTTP 클라이언트 (로그인/등록용) ---
http_client = requests.Session()

# --- 로그 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("broadcaster")

# --- 웹 서버 연결 설정 ---
BASE_URL = os.getenv("TEST_SERV")
DEBUG_PREFIX = "/_manual_test" 

TEST_EMAIL = f"webrtc@example.com"
TEST_PASSWORD = "pw123"
TEST_ROBOT_SN = f"SN-WEBRTC-WEBRTC"

# [변경] 단일 PeerConnection
sio = socketio.AsyncClient(logger=True, engineio_logger=False)

ice_servers = [
    RTCIceServer(urls=["stun:stun.l.google.com:19302"])
]
config = RTCConfiguration(iceServers=ice_servers)

pc = RTCPeerConnection()
ice_candidates_buffer = []


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

# --- WebRTC 관련 함수 ---

async def start_webrtc_broadcast():
    """
    WebRTC PeerConnection을 초기화하고, Offer를 생성하여 서버에 전송하는
    전체적인 방송 시작 과정을 담당합니다.
    """
    global pc
    if pc.connectionState != "closed":
        await pc.close()

    config = RTCConfiguration(
        iceServers=[
            RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
            RTCIceServer(
                urls=[
                    "turn:3.38.103.192",
                ],
                username="okeyducky",
                credential="a4081234",
            ),
        ], 
    )
    pc = RTCPeerConnection(configuration=config)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Connection state is -> {pc.connectionState}")

        if pc.connectionState == "connected":
            try:
                stats = await pc.getStats()
                active_pair = next(
                    (
                        s
                        for s in stats.values()
                        if s.type == "candidate-pair" and s.selected
                    ),
                    None,
                )

                if active_pair:
                    local = stats.get(active_pair.localCandidateId)
                    remote = stats.get(active_pair.remoteCandidateId)
                    if local and remote:
                        logger.info(
                            f"✅ 연결 성공! 타입: {local.candidateType} <-> {remote.candidateType}"
                        )
            except Exception as e:
                logger.warning(f"연결 정보 확인 중 오류: {e}")

    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        """
        8. 로컬 PeerConnection에서 ICE Candidate가 생성될 때마다 호출됩니다.
        생성된 Candidate를 서버로 전송하여 Viewer에게 전달합니다.
        """
        if candidate:
            logger.info(f"[ICE 생성] ICE Candidate 생성 완료")
            ice_data = {
                "candidate": candidate.candidate,
                "sdpMid": candidate.sdpMid,
                "sdpMLineIndex": candidate.sdpMLineIndex,
            }
            # 프론트엔드는 이 이벤트를 수신하여 addIceCandidate를 호출해야 합니다.
            await sio.emit(
                WebRTCEvents.SEND_ICE_CANDIDATE, 
                (SessionType.PARENT.value, parent_id, ice_data) 
                # (opp_clnt_type, opp_clnt_id, data)
            )

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Connection state is -> {pc.connectionState}")

        if pc.connectionState == "connected":
            try:
                # 1. 표준 통계(Stats) 가져오기
                stats = await pc.getStats()
                active_pair = None

                # 2. 활성화된(selected) candidate-pair 찾기
                for stat in stats.values():
                    if stat.type == "candidate-pair" and stat.selected:
                        active_pair = stat
                        break

                # 3. 선택된 쌍의 상세 정보(로컬/리모트 후보자) 확인
                if active_pair:
                    local_cand = stats.get(active_pair.localCandidateId)
                    remote_cand = stats.get(active_pair.remoteCandidateId)

                    if local_cand and remote_cand:
                        local_type = local_cand.candidateType
                        remote_type = remote_cand.candidateType
                        logger.info(f"✅ 연결 성공! 타입: Local({local_type}) <-> Remote({remote_type})")

                        if local_type == "relay" or remote_type == "relay":
                            logger.info("🌐 TURN 서버를 경유한 릴레이 연결입니다.")
                        else:
                            logger.info("💻 P2P 직접 연결입니다 (host/srflx/prflx).")
            except Exception as e:
                logger.warning(f"연결 정보 확인 중 오류 발생: {e}")

        elif pc.connectionState in ["failed", "closed"]:
            logger.warning(f"Connection {pc.connectionState}. 리소스 정리 필요.")

    try:
        # 로컬 카메라 트랙을 PeerConnection에 추가합니다.
        # 이 트랙이 Viewer에게 스트리밍될 미디어 소스입니다.
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            logger.error("웹캠을 열 수 없습니다.")
            return

        video_track = OpenCVVideoStreamTrack(cap)
        audio_track = PyAudioStreamTrack()
        pc.addTrack(video_track)
        pc.addTrack(audio_track)
        logger.info("✅ 카메라 트랙 추가 완료")
    except Exception as e:
        logger.error(f"카메라 트랙 추가 중 오류 발생: {e}")
        return

async def send_offer():
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    offer_packet = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    
    logger.info(f"'SEND_OFFER' 전송 (to parent_id: {PARENT_ID})...")
    await sio.emit(
        WebRTCEvents.SEND_OFFER,
        (SessionType.PARENT.value, PARENT_ID, offer_packet)
        # (offer_clnt_type, offer_clnt_id, offer_data)
    )


@sio.on(WebRTCEvents.CAST_REQUESTED)
async def on_cast_requested(data: Dict[str, Any]):
    """
    (Point 1) 뷰어(Parent)가 'REQUEST_CAST'를 보내 서버가 중계한 이벤트
    data 에는 {'opp_type': 'parent', 'opp_id': 123}가 들어옵니다.
    """
    logger.info(f"'CAST_REQUESTED' 수신 (from {data.get('opp_type')}:{data.get('opp_id')})")
    await sio.emit(
        WebRTCEvents.ACCPET_REQUEST,
        (SessionType.PARENT.value, PARENT_ID)
    )
    logger.info(f"'ACCPET_REQUEST' 전송 (to parent_id: {PARENT_ID})...")
    await start_webrtc_broadcast()

@sio.on(WebRTCEvents.PEER_IS_READY)
async def on_peer_is_ready(data: Dict[str, Any]):
    logger.info(f"'PEER_IS_READY' 수신 (from {data.get('opp_type')}:{data.get('opp_id')})")
    await send_offer()


# --- [변경] Socket.IO 이벤트 핸들러 ---
@sio.event
async def connect():
    """서버 연결 성공 시 (1단계)"""
    logger.info(f"Socket.IO 연결 성공 (SID: {sio.sid}).")

@sio.event
async def auth_success():
    """서버 인증 성공 시 (2단계) - WebRTC Offer 등록"""
    logger.info("🔑 Socket.IO 인증 성공! WebRTC Offer 등록을 시작합니다.")

@sio.on(WebRTCEvents.NEW_ANSWER)
async def on_new_answer(answer_data: Dict[str, Any]):
    global pc, ice_candidates_buffer # 버퍼 전역변수 사용
    logger.info("⬇️ 'NEW_ANSWER' 수신!")
    try:
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        await pc.setRemoteDescription(answer)
        logger.info("✅ RemoteDescription (Answer) 설정 완료.")

        # 버퍼에 저장된 ICE Candidate들이 있다면 일괄 추가
        if ice_candidates_buffer:
            logger.info(f"📦 버퍼링된 {len(ice_candidates_buffer)}개의 ICE Candidate 추가 시작")
            for candidate in ice_candidates_buffer:
                await pc.addIceCandidate(candidate)
            ice_candidates_buffer = [] # 버퍼 초기화
            logger.info("✅ 버퍼링된 ICE Candidate 추가 완료")

    except Exception as e:
        logger.error(f"Answer 처리 실패: {e}", exc_info=True)

@sio.on(WebRTCEvents.NEW_ICE_CANDIDATE)
async def on_new_ice_candidate(data: Dict[str, Any]): # ⬅️ Dict 타입 명시
    """Parent가 보낸 ICE Candidate 수신 (5단계)"""
    global pc, video_track, audio_track
    logger.info(f"⬇️ 'NEW_ICE_CANDIDATE' (from Parent) 수신")
    logger.info(f"ICE Candidate 데이터: {data}")
    try:
        candidate = data["candidate"]
        
        # 💡 [핵심 수정] 빈 candidate (end-of-candidates 신호) 무시
        if not candidate:
            logger.info("End-of-candidates 신호 (빈 문자열) 수신. 무시합니다.")
            return  # 함수 종료
        
        parsed_sdp=candidate_from_sdp(candidate)
        parsed_sdp.sdpMid = data["sdpMid"]
        parsed_sdp.sdpMLineIndex = data["sdpMLineIndex"]

        if pc.remoteDescription is None:
            # Remote SDP가 아직 없으면 버퍼에 저장
            logger.info("⏳ RemoteDescription이 아직 없습니다. ICE Candidate를 버퍼에 저장합니다.")
            ice_candidates_buffer.append(parsed_sdp)
        else:
            # Remote SDP가 있으면 즉시 추가
            await pc.addIceCandidate(parsed_sdp)
            logger.info("✅ ICE Candidate 즉시 추가 완료")

    except KeyError:
        logger.error(f"ICE Candidate 처리 실패: 'candidate' 키가 없습니다. {data}")
    except Exception as e:
        logger.error(f"ICE Candidate 추가 실패: {e}", exc_info=True)

@sio.event
async def disconnect():
    global pc, video_track, audio_track
    logger.warning("Socket.IO 연결 종료.")
    await pc.close()


async def main():
    try:
        await sio.connect(BASE_URL, transports=['websocket'], auth={"token": ACCESS_TOKEN, "session_type": SESSION_TYPE})
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        logger.error(f"시그널링 서버 연결 실패: {e}")
    except KeyboardInterrupt:
        logger.info("Broadcaster shutting down...")
    finally:
        if sio.connected:
            await sio.disconnect()


if __name__ == "__main__":
    parent_id, child_id, robot_id, access_token = None, None, None, None

    # 부모, 자녀, 로봇 모두 등록된 것 사용하기

    print("--- [HTTP 2] 로그인 (토큰 획득) ---")
    log_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/login", json=log_data)
    assert resp.status_code == 200, f"로그인 실패: {resp.text} (auth_service.py 수정 필요)"
    access_token = resp.json()["access_token"]
    print(f"✅ 로그인 성공 (Token: {access_token})")

    print("--- [HTTP 5] 로봇 로그인 (토큰 획득) ---")
    robot_id=ROBOT_ID
    log_data = {"robot_id": robot_id, "serial_number": TEST_ROBOT_SN}
    resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/login/robot", json=log_data)
    assert resp.status_code == 200, f"로그인 실패: {resp.text} (auth_service.py 수정 필요)"
    robot_access_token = resp.json()["access_token"]
    print(f"✅ 로그인 성공 (Token: {robot_access_token[:10]}...)")
    ROBOT_ID = robot_id
    ACCESS_TOKEN = robot_access_token

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n프로그램을 종료합니다.")
