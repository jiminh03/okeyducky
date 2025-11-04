import asyncio
import json
import logging
import cv2
import numpy as np
import socketio # ⬅️ [변경] aiohttp 대신 socketio 클라이언트 사용
import sounddevice as sd
from typing import Dict, Any # ⬅️ [추가]

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
from av import VideoFrame

# ⬇️ [추가] webrtc_event.py와 스키마 임포트
from common.schemas.socket_event_schema import WebRTCEvents
from common.schemas.session_schema import SessionType

# --- 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("viewer")

# [변경] Socket.IO 서버 주소 (FastAPI 서버)
SIGNALING_URL = "http://127.0.0.1:8000" 

# [변경] 단일 PeerConnection
pc = RTCPeerConnection()
sio = socketio.AsyncClient(logger=True, engineio_logger=True)

# ⬇️ [추가] 플레이스홀더: 이 값들은 viewer(Parent)가 알아야 함
# (요청대로, 이 값들을 채우는 로직은 생략합니다.
#  validate_scenario.py처럼 HTTP 요청으로 미리 받아와야 합니다.)
ACCESS_TOKEN = "YOUR_VALID_JWT_TOKEN_HERE" # ⬅️ (필수) 로그인 토큰
PARENT_ID = 1 # ⬅️ (필수) 이 뷰어(부모) 자신의 ID
ROBOT_ID = 1 # ⬅️ (필수) 연결할 로봇(Broadcaster)의 ID
SESSION_TYPE = "parent" # ⬅️ (필수)

# --- 미디어 트랙 수신 (원본 코드와 동일) ---
video_track_task = None
audio_track_task = None

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
    # (원본 코드와 동일, nb_channels 수정 포함)
    logger.info("Audio track receiver started")
    stream = None
    try:
        while True:
            frame = await track.recv()
            if stream is None:
                samplerate = frame.sample_rate
                channels = frame.layout.nb_channels # .nb_channels 사용
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
@pc.on("track")
def on_track(track):
    # (원본 코드와 동일)
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
async def on_icecandidate(candidate):
    """ICE Candidate 생성 시 서버로 전송 (Robot에게)"""
    if candidate:
        logger.info(f"ICE Candidate 생성: {candidate.candidate[:30]}...")
        # [변경] webrtc_event.py의 시그널링 방식 사용
        await sio.emit(
            WebRTCEvents.SEND_ICE_CANDIDATE, 
            (SessionType.ROBOT.value, ROBOT_ID, candidate.to_dict())
        )

@pc.on("connectionstatechange")
async def on_connectionstatechange():
    # (원본 코드와 거의 동일, 태스크 정리 로직 추가)
    logger.info(f"PC state: {pc.connectionState}")
    if pc.connectionState == "failed" or pc.connectionState == "closed":
        if video_track_task: video_track_task.cancel()
        if audio_track_task: audio_track_task.cancel()
        await pc.close()
        logger.info("PeerConnection closed.")

# --- [변경] Socket.IO 이벤트 핸들러 ---
@sio.event
async def connect():
    """서버 연결 성공 시 (1단계)"""
    logger.info(f"Socket.IO 연결 성공 (SID: {sio.sid}). 인증 시도...")
    # 'connection_event.py'의 'auth' 파라미터에 맞게 전송
    await sio.emit("auth", {"token": ACCESS_TOKEN, "session_type": SESSION_TYPE})

@sio.event
async def auth_success():
    """서버 인증 성공 시 (2단계) - 로봇의 Offer 확인"""
    logger.info("🔑 Socket.IO 인증 성공! 로봇의 Offer 확인을 시작합니다.")
    
    # 'webrtc_event.py'의 'on_check_offer' 호출
    await sio.emit(
        WebRTCEvents.CHECK_OFFER, 
        (SessionType.ROBOT.value, ROBOT_ID) 
    )
    logger.info(f"CHECK_OFFER 전송 (Robot ID: {ROBOT_ID}). Offer 대기 중...")

@sio.on(WebRTCEvents.NEW_OFFER)
async def on_new_offer(offer_data: Dict[str, Any]):
    """로봇이 등록한 Offer 수신 (3단계)"""
    logger.info("⬇️ 'NEW_OFFER' 수신! Answer 생성 및 전송 시작...")
    try:
        offer = RTCSessionDescription(sdp=offer_data["sdp"], type=offer_data["type"])
        await pc.setRemoteDescription(offer)
        
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        answer_packet = {"type": answer.type, "sdp": answer.sdp}
        
        # 'webrtc_event.py'의 'on_send_answer' 호출
        await sio.emit(
            WebRTCEvents.SEND_ANSWER,
            (SessionType.ROBOT.value, ROBOT_ID, answer_packet)
        )
        logger.info("✅ Answer 전송 완료.")
        
    except KeyError:
        logger.error(f"Offer 처리 실패: 'sdp' 또는 'type' 키가 없습니다. {offer_data}")
    except Exception as e:
        logger.error(f"Offer 처리 또는 Answer 생성 실패: {e}", exc_info=True)

@sio.on(WebRTCEvents.NEW_ICE_CANDIDATE)
async def on_new_ice_candidate(data: Dict[str, Any]):
    """로봇이 보낸 ICE Candidate 수신 (5단계)"""
    logger.info(f"⬇️ 'NEW_ICE_CANDIDATE' (from Robot) 수신")
    try:
        # [변경] validate_scenario.py의 형식을 따름
        candidate_data = data["candidate"] 
        if isinstance(candidate_data, dict):
             await pc.addIceCandidate(
                candidate_data["candidate"],
                sdpMid=candidate_data["sdpMid"],
                sdpMLineIndex=candidate_data["sdpMLineIndex"]
            )
        else:
            # (aiortc v0.9.28 이전의 간단한 형식일 경우)
            await pc.addIceCandidate(candidate_data)
    except KeyError:
        logger.error(f"ICE Candidate 처리 실패: 'candidate' 키가 없습니다. {data}")
    except Exception as e:
        logger.error(f"ICE Candidate 추가 실패: {e}", exc_info=True)

@sio.event
async def disconnect():
    logger.warning("Socket.IO 연결 종료.")
    await pc.close()


async def main():
    # [변경] Socket.IO 서버 연결 및 대기
    try:
        await sio.connect(SIGNALING_URL, transports=['websocket'])
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        logger.error(f"시그널링 서버 연결 실패: {e}")
    except KeyboardInterrupt:
        logger.info("Viewer shutting down...")
    finally:
        if sio.connected:
            await sio.disconnect()
        
        # 태스크 캔슬 (원본 코드와 동일)
        if video_track_task: video_track_task.cancel()
        if audio_track_task: audio_track_task.cancel()
        
        if pc.connectionState != "closed":
            await pc.close()
            
        cv2.destroyAllWindows()
        logger.info("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())