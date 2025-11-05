import asyncio
import json
import logging
import cv2
import numpy as np
import requests
import socketio # ⬅️ aiohttp 대신 socketio 클라이언트 사용
import sounddevice as sd
from typing import Dict, Any

from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
from av import VideoFrame

# ⬇️ [변경] webrtc_event.py의 이벤트 스키마 임포트
from common.schemas.socket_event_schema import ConnectEvents, WebRTCEvents
from common.schemas.session_schema import SessionType

# --- HTTP 클라이언트 (로그인/등록용) ---
http_client = requests.Session()

# --- 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("viewer")

BASE_URL = "http://127.0.0.1:8000" 
DEBUG_PREFIX = "/_manual_test" 

# [변경] 단일 PeerConnection (요청 수락 시 생성)
pc: RTCPeerConnection = None
sio = socketio.AsyncClient(logger=True, engineio_logger=False)

# ⬇️ [추가] 플레이스홀더: 이 값들은 viewer(Parent)가 알아야 함
ACCESS_TOKEN = "YOUR_VALID_PARENT_JWT_TOKEN_HERE" 
PARENT_ID = 1 # ⬅️ (필수) 이 뷰어(부모) 자신의 ID
ROBOT_ID = 1 # ⬅️ (필수) 연결할 로봇(Broadcaster)의 ID
SESSION_TYPE = "parent" # ⬅️ (필수)

# --- 테스트용 데이터 ---
# (HTTP 요청 로직이 main 함수로 이동)
TEST_EMAIL = f"webrtc@example.com"
TEST_PASSWORD = "pw123"

# --- 미디어 트랙 수신 (원본 코드와 동일) ---
video_track_task = None
audio_track_task = None

ice_servers = [
    RTCIceServer(urls=["stun:stun.l.google.com:19302"])
]
config = RTCConfiguration(iceServers=ice_servers)

async def video_track_receiver(track):
    # (원본 코드와 동일)
    logger.info(f"Video track received: {track.kind}")
    window_name = "Viewer"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    try:
        while True:
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")
            cv2.imshow(window_name, img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e: logger.error(f"Error in video track receiver: {e}")
    finally:
        cv2.destroyWindow(window_name)
        logger.info("Video display stopped.")

async def audio_track_receiver(track):
    # (원본 코드와 동일)
    logger.info("Audio track receiver started")
    stream = None
    try:
        while True:
            frame = await track.recv()
            if stream is None:
                samplerate = frame.sample_rate
                channels = frame.layout.nb_channels
                dtype = 'int16'
                logger.info(f"Initializing sounddevice stream SR={samplerate}, Channels={channels}")
                stream = sd.RawOutputStream(samplerate=samplerate, channels=channels, dtype=dtype)
                stream.start()
            data = frame.to_ndarray().tobytes()
            await asyncio.to_thread(stream.write, data)
    except Exception as e: logger.error(f"Error in audio track receiver: {e}")
    finally:
        if stream: stream.stop(); stream.close()
        logger.info("Audio stream stopped.")
# --- 미디어 트랙 수신 끝 ---


# --- [변경] WebRTC 이벤트 핸들러 ---
async def cleanup_pc():
    """PeerConnection을 닫고 태스크를 정리합니다."""
    global pc, video_track_task, audio_track_task
    if video_track_task: video_track_task.cancel()
    if audio_track_task: audio_track_task.cancel()
    video_track_task, audio_track_task = None, None
    
    if pc and (pc.connectionState != "failed" or pc.connectionState != "closed"):
        await pc.close()
        logger.info("PeerConnection closed.")
    pc = None

# ⬇️ [변경] on_icecandidate 핸들러는 PC가 생성될 때 동적으로 추가됩니다.

# --- [변경] Socket.IO 이벤트 핸들러 ---
@sio.event
async def connect():
    """서버 연결 성공 시 (1단계) - 인증 시도"""
    logger.info(f"Socket.IO 연결 성공 (SID: {sio.sid}).")

@sio.on(ConnectEvents.AUTH_SUCCESS)
async def auth_success():
    """서버 인증 성공 시 (2단계) - 캐스트(송출) 요청"""
    logger.info("🔑 Socket.IO 인증 성공!")
    # ⬇️ [2] (해결책) emit을 호출하기 전, 이벤트 루프에 제어권을 넘깁니다.
    await asyncio.sleep(3)
    
    # 1. (Point 1) 로봇에게 'REQUEST_CAST'를 보냅니다.
    logger.info(f"⬆️ 'REQUEST_CAST' 전송 (to Robot ID: {ROBOT_ID})...")
    await sio.emit(
        WebRTCEvents.REQUEST_CAST,
        (SessionType.ROBOT.value, ROBOT_ID)
        # (opp_clnt_type, opp_clnt_id)
    )

@sio.on(WebRTCEvents.CAST_ACCEPTED)
async def on_cast_accepted(data: Dict[str, Any]):
    """
    (Point 1) 로봇이 요청을 수락했음을 알림.
    """
    logger.info(f"'CAST_ACCEPTED' 수신 (from {data.get('opp_type')}:{data.get('opp_id')}). PC 설정 시작...")
    
    global pc
    if pc is not None:
        # 이미 연결 중이면 기존 연결 정리
        await cleanup_pc()
        
    # 2. (Point 2) 요청이 수락되었으므로 PC 객체 생성
    pc = RTCPeerConnection(configuration=config)
    await asyncio.sleep(0)  # 이벤트 루프 순서 보정 (yield)
    logger.info("PC 준비 완료. Offer 대기 중...")
        
    # 3. (Point 2) ⬇️ [수정] PC 핸들러를 'pc' 객체 생성 *이후*에 동적으로 설정
    
    @pc.on("track")
    def on_track(track):
        global video_track_task, audio_track_task
        if track.kind == "audio":
            logger.info("Audio track received")
            if audio_track_task is None:
                audio_track_task = asyncio.create_task(audio_track_receiver(track))
        elif track.kind == "video":
            logger.info("Video track received, starting display task...")
            if video_track_task is None:
                video_track_task = asyncio.create_task(video_track_receiver(track))

    @pc.on("icecandidate")
    def on_icecandidate(candidate):
        if candidate:
            asyncio.create_task(
                sio.emit(
                    WebRTCEvents.SEND_ICE_CANDIDATE,
                    (SessionType.ROBOT.value, ROBOT_ID, candidate.to_dict())
                )
            )

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        # 현재 연결 상태를 로그로 남깁니다.
        print(f"Connection state is {pc.connectionState}")

        # 연결이 끊기거나 실패한 상태에서는 transport에 접근하지 않고 함수를 종료합니다.
        if pc.connectionState in ["failed", "disconnected", "closed"]:
            print("Connection closed or failed.")
            return

        # "connected" 또는 "connecting" 상태일 때
        # transport 객체가 None이 아닌지 순차적으로 확인하고 접근합니다.
        if pc.sctp and pc.sctp.transport and pc.sctp.transport.transport:
            try:
                selected_pair = pc.sctp.transport.transport.getSelectedCandidatePair()
                if selected_pair:
                    print(f"Selected pair: {selected_pair.local.ip} <-> {selected_pair.remote.ip}")
            except Exception as e:
                # getSelectedCandidatePair()가 실패할 경우를 대비
                print(f"Error getting selected pair: {e}")
        else:
            # "connecting" 상태와 같이 아직 transport가 설정되지 않은 경우일 수 있습니다.
            print("SCTP transport not yet available.")
    
    @pc.on("iceconnectionstatechange")
    def on_iceconnectionstatechange():
        logger.info(f"ICE Connection State: {pc.iceConnectionState}")
    
    await sio.emit(WebRTCEvents.READY_FOR_OFFER,(SessionType.ROBOT.value, ROBOT_ID))
    logger.info("PC 및 이벤트 핸들러 설정 완료. Offer 대기 중...")


@sio.on(WebRTCEvents.NEW_OFFER)
async def on_new_offer(offer_data: Dict[str, Any]):
    """(Point 3) 로봇이 보낸 Offer 수신"""
    logger.info("⬇️ 'NEW_OFFER' 수신! Answer 생성 및 전송 시작...")
    
    global pc
    if pc is None:
        logger.error("Offer를 수신했으나 PC가 초기화되지 않았습니다. ('CAST_ACCEPTED' 누락)")
        return
        
    try:
        offer = RTCSessionDescription(sdp=offer_data["sdp"], type=offer_data["type"])
        await pc.setRemoteDescription(offer)
        
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        answer_packet = {"type": answer.type, "sdp": answer.sdp}
        
        await sio.emit(
            WebRTCEvents.SEND_ANSWER,
            (SessionType.ROBOT.value, ROBOT_ID, answer_packet)
        )
        logger.info("✅ Answer 전송 완료.")
        
    except Exception as e:
        logger.error(f"Offer 처리 또는 Answer 생성 실패: {e}", exc_info=True)

@sio.on(WebRTCEvents.NEW_ICE_CANDIDATE)
async def on_new_ice_candidate(data):
    if pc is None:
        return
    candidate_data = data["candidate"]
    async def safe_add():
        try:
            await pc.addIceCandidate(candidate_data)
        except Exception as e:
            logger.error(f"addIceCandidate 실패: {e}")
    asyncio.create_task(safe_add())

@sio.event
async def disconnect():
    logger.warning("Socket.IO 연결 종료.")
    await cleanup_pc()


async def main():
    global ACCESS_TOKEN, PARENT_ID, ROBOT_ID
    
    # 1. (요청대로) HTTP로 먼저 로그인하여 토큰/ID 획득
    try:
        print("--- [HTTP 1] 부모 로그인 (토큰 획득) ---")
        log_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/login", json=log_data)
        assert resp.status_code == 200, f"로그인 실패: {resp.text}"
        ACCESS_TOKEN = resp.json()["access_token"]
        print(f"✅ 부모 로그인 성공 (Token: {ACCESS_TOKEN[:10]}...)")
        
        # (가정) 자녀 목록을 조회하여 연결할 로봇 ID 획득
        print("--- [HTTP 2] 자녀/로봇 ID 획득 ---")
        resp = http_client.get(f"{BASE_URL}{DEBUG_PREFIX}/child/list", headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
        assert resp.status_code == 200, f"자녀 목록 조회 실패: {resp.text}"
        children = resp.json()
        resp = http_client.get(f"{BASE_URL}{DEBUG_PREFIX}/robot?serial_number={children[0]["serial_number"]}", headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
        robot = resp.json()
        
        if not robot or not robot.get("robot_id"):
             print(f"🚨 오류: {TEST_EMAIL} 계정에 로봇이 연결된 자녀가 없습니다.")
             return
        
        ROBOT_ID = robot.get("robot_id")
        print(f"✅ 통화 대상 로봇 ID 획득: {ROBOT_ID}")

    except requests.exceptions.ConnectionError:
        logger.error(f"HTTP 연결 실패. '{BASE_URL}' 서버가 실행 중인지 확인하세요.")
        return
    except Exception as e:
        logger.error(f"HTTP 사전 설정 실패: {e}")
        return

    # [변경] Socket.IO 서버 연결 및 대기
    try:
        await sio.connect(
            BASE_URL, 
            auth={"token": ACCESS_TOKEN, "session_type": SESSION_TYPE},
            transports=['websocket']
        )
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        logger.error(f"시그널링 서버 연결 실패: {e}")
    except KeyboardInterrupt:
        logger.info("Viewer shutting down...")
    finally:
        if sio.connected:
            await sio.disconnect()
        
        await cleanup_pc()
        cv2.destroyAllWindows()
        logger.info("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())