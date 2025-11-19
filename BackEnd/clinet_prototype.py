import os
from dotenv import load_dotenv

# .env 파일 로드 (KEY, ENDPOINT 포함)
load_dotenv()

import asyncio
from datetime import datetime
import json
import logging
import base64
import queue

import cv2
import numpy as np
import pyaudio
import requests
import socketio  # aiohttp 대신 socketio 클라이언트 사용

from typing import Dict, Any

from aiortc import (
    RTCConfiguration,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc import AudioStreamTrack, VideoStreamTrack
from aiortc.sdp import candidate_from_sdp
from av import AudioFrame, VideoFrame
from fractions import Fraction as Rational

import azure.cognitiveservices.speech as speechsdk

from enum import Enum


# --- 설정 ---
BASE_URL = "http://k13a408.p.ssafy.io:8000"
DEBUG_PREFIX = "/_manual_test"

# WebRTC/STT 설정
TEST_EMAIL = "webrtc@example.com"
TEST_PASSWORD = "pw123"
RATE_STT_WEBRTC = 16000  # Azure STT에서 잘 쓰는 16kHz
FORMAT_STT_WEBRTC = pyaudio.paInt16
CHANNELS_STT_WEBRTC = 1
FRAMES_PER_BUFFER = 2048
AUDIO_PTIME = 0.020
DEVICE_INDEX = 0

# TTS 재생 설정 (OpenAI PCM 기본값)
RATE_TTS_PLAYBACK = 24000              # 24kHz
FORMAT_TTS_PLAYBACK = pyaudio.paInt16  # 16-bit
CHANNELS_TTS_PLAYBACK = 1             # 1-channel (모노)

CHILD_ID = 1

# --- Socket.IO / WebRTC 공통 ---
http_client = requests.Session()
sio = socketio.AsyncClient(logger=False, engineio_logger=False)

ice_servers = [RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
config = RTCConfiguration(iceServers=ice_servers)

pc = RTCPeerConnection()
ice_candidates_buffer = []

# ⬇️ broadcaster(로봇)가 알아야 하는 값들
ACCESS_TOKEN = "YOUR_VALID_JWT_TOKEN_HERE"  # (필수) 로봇 로그인 토큰
PARENT_ID = 1  # (필수) 이 브로드캐스터(로봇)가 통화할 부모의 ID
ROBOT_ID = 1  # (필수) 이 브로드캐스터(로봇) 자신의 ID
TEST_ROBOT_SN = "SN-WEBRTC-WEBRTC"
SESSION_TYPE = "robot"  # (필수)

# STT / 마이크 공유 객체 (전역)
azure_stt: 'AzureSTT' = None
mic_source: 'MicSource' = None

# TTS 재생 관련 전역 관리 객체
p_audio: pyaudio.PyAudio | None = None # PyAudio 인스턴스 (STT/WebRTC와 공유)
stream_tts: pyaudio.Stream | None = None # TTS 재생용 스트림 (24kHz)
playback_queue: asyncio.Queue[bytes | None] = asyncio.Queue() # TTS 재생 큐

# TTS 스트리밍 상태 관리
chunk_buffer: list[bytes] = []
streaming_lock = asyncio.Lock()
is_streaming = False # 스트리밍 상태 플래그
is_tts_playing = False
# --- 로그 설정 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unified_broadcaster")


class FaceRequestEvent(str, Enum):
    """
    클라이언트(로봇)가 서버에게 얼굴 표정 변경을 요청하는 이벤트
    """
    # [C->S] 평소 얼굴 요청
    REQUEST_FACE_NORMAL = "client:request_face_normal"
    # [C->S] 하트눈 얼굴 요청
    REQUEST_FACE_HEART = "client:request_face_heart"
    # [C->S] 슬픈 얼굴 요청
    REQUEST_FACE_SAD = "client:request_face_sad"
    # [C->S] 말하는 얼굴 요청
    REQUEST_FACE_SPEAKING = "server:face_speaking"
    # [C->S] 말하지 않는 얼굴 요청
    REQUEST_FACE_NOT_SPEAKING = "server:face_not_speaking"

class ConnectEvents(str, Enum):
    """소켓 통신에서 사용되는 이벤트 이름 목록"""
    AUTH_SUCCESS = "auth_success"
    AuTH_FAILURE = "auth_failure"
    CONNECT = "connect"
    DISCONNECT = "disconnect"

class WebRTCEvents(str, Enum):
    """WebRTC 시그널링 이벤트 목록"""
    REQUEST_CAST = "client:request_cast"
    ACCPET_REQUEST = "client:accept_request"
    REJECT_REQUEST = "client:reject_request"
    CAST_REQUESTED = "server:cast_requested"
    CAST_ACCEPTED = "server:cast_accepted"
    CAST_REJECTED = "server:cast_rejected"
    READY_FOR_OFFER = "client:ready_for_offer"
    PEER_IS_READY = "server:peer_is_ready"
    SEND_OFFER = "client:send_offer"
    SEND_ANSWER = "client:send_answer"
    NEW_OFFER = "server:new_offer"
    NEW_ANSWER = "server:new_answer"
    SEND_ICE_CANDIDATE = "client:send_ice_candidate"
    NEW_ICE_CANDIDATE = "server:new_ice_candidate"

class RobotTTSEvents(str, Enum):
    """TTS 스트리밍 이벤트 목록"""
    STREAM_START = "server:stream_start"
    AUDIO_CHUNK = "server:audio_chunk"
    STREAM_END = "server:stream_end"

class SessionType(Enum):
    """세션 타입을 나타내는 열거형"""
    PARENT = "parent"
    ROBOT = "robot"


# ===================================================================
# STT / 마이크 관리 (MicSource)
# ===================================================================

class AzureSTT:
    # ... (broadcaster_for_js.py 의 AzureSTT 클래스 내용 그대로) ...
    """Azure Speech SDK를 이용한 실시간 STT 래퍼 (PushAudioInputStream)."""

    def __init__(self, on_text_callback, language: str = "ko-KR"):
        key = os.environ.get("KEY")
        endpoint = os.environ.get("ENDPOINT")
        if not key or not endpoint:
            raise RuntimeError("환경변수 KEY, ENDPOINT 가 설정되지 않았습니다.")

        self._on_text = on_text_callback

        speech_config = speechsdk.SpeechConfig(subscription=key, endpoint=endpoint)
        speech_config.speech_recognition_language = language

        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=RATE_STT_WEBRTC,
            bits_per_sample=16,
            channels=1,
        )
        self._push_stream = speechsdk.audio.PushAudioInputStream(
            stream_format=audio_format
        )
        audio_config = speechsdk.audio.AudioConfig(stream=self._push_stream)

        self._recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        self._recognizer.recognized.connect(self._on_recognized)
        self._recognizer.canceled.connect(self._on_canceled)

    def _on_recognized(self, evt):
        result = evt.result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech and result.text:
            try:
                self._on_text(result.text)
            except Exception as e:
                logger.error(f"STT 콜백 처리 중 오류: {e}", exc_info=True)

    def _on_canceled(self, evt):
        logger.warning(f"Azure STT canceled: {evt}")

    def start(self):
        self._recognizer.start_continuous_recognition()

    def stop(self):
        self._recognizer.stop_continuous_recognition()

    def push_audio(self, data: bytes):
        # pyaudio에서 읽은 16bit PCM 데이터를 그대로 푸시
        self._push_stream.write(data)


class MicSource:
    """
    하나의 PyAudio 입력을 계속 읽으면서
    1) Azure STT로 푸시하고
    2) WebRTC용 최신 프레임을 보관하는 클래스
    """
    global p_audio # PyAudio 인스턴스를 전역으로 공유

    def __init__(self, stt: AzureSTT | None = None, device_index: int | None = None):
        if p_audio is None:
            raise RuntimeError("PyAudio 인스턴스가 초기화되지 않았습니다.")
            
        self.p = p_audio # 전역 인스턴스 사용
        self.stream_input = self.p.open(
            format=FORMAT_STT_WEBRTC,
            channels=CHANNELS_STT_WEBRTC,
            rate=RATE_STT_WEBRTC,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER,
            # input_device_index=device_index,
        )
        self.stt = stt
        self.webrtc_enabled: bool = False

        self._input_channels = CHANNELS_STT_WEBRTC

        # 🔹 20ms 프레임 몇 개만 쌓는 지터 버퍼 (최대 5개 = 100ms)
        self._buffer: asyncio.Queue[bytes] = asyncio.Queue(maxsize=5)

        self._latest_frame: bytes | None = None
        self._frame_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    def start(self, loop: asyncio.AbstractEventLoop):
        if self._task is None or self._task.done():
            self._task = loop.create_task(self._run())

    async def _run(self):
        logger.info("MicSource: 마이크 캡쳐 루프 시작")
        try:
            while True:
                # 20ms 만큼씩 읽기
                try:
                    data = await asyncio.to_thread(
                        self.stream_input.read,
                        FRAMES_PER_BUFFER,
                        exception_on_overflow=False,
                    )
                except Exception as e:
                    logger.warning(f"MicSource: PyAudio read 오류, 무음 전송: {e}")
                    data = b"\0" * FRAMES_PER_BUFFER * CHANNELS_STT_WEBRTC * 2

                # 🔹 (옵션) 다운믹스 – 지금은 CHANNELS=1 이라 거의 그대로
                try:
                    pcm = np.frombuffer(data, dtype=np.int16)
                    if self._input_channels > 1:
                        pcm = pcm.reshape(-1, self._input_channels)
                        mono = pcm[:, 0]
                    else:
                        mono = pcm
                    mono_bytes = mono.astype(np.int16).tobytes()
                except Exception as e:
                    logger.warning(f"MicSource: 다운믹스 실패, 원본 사용: {e}")
                    mono_bytes = data

                # 1) STT 로 전송 (통화 여부와 상관없이 항상)
                if self.stt is not None:
                    try:
                        self.stt.push_audio(mono_bytes)
                    except Exception as e:
                        logger.warning(f"MicSource: STT push 실패: {e}")

                # 2) WebRTC용 지터 버퍼에 넣기 (통화 중일 때만)
                if self.webrtc_enabled:
                    try:
                        self._buffer.put_nowait(mono_bytes)
                    except asyncio.QueueFull:
                        # 가득 차면 가장 오래된 것 하나 버리고 새로 넣기
                        try:
                            _ = self._buffer.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                        try:
                            self._buffer.put_nowait(mono_bytes)
                        except asyncio.QueueFull:
                            pass

                    # 최신 프레임 캐시도 업데이트
                    self._latest_frame = mono_bytes

                    # 대기 중인 WebRTC 쪽 깨우기
                    if not self._frame_event.is_set():
                        self._frame_event.set()

        except asyncio.CancelledError:
            logger.info("MicSource: 캡쳐 루프 취소")
        except Exception as e:
            logger.error(f"MicSource: 예외 발생: {e}", exc_info=True)
        finally:
            self.close()

    async def get_latest_frame(self) -> bytes:
        """
        WebRTC 오디오 트랙에서 호출.
        지터 버퍼에서 가장 최신 프레임을 하나 꺼내서 반환.
        """
        # 새 데이터가 들어올 때까지 대기
        await self._frame_event.wait()
        self._frame_event.clear()

        chunk: bytes | None = None

        # 큐에 여러 개 쌓여 있으면 가장 마지막 것만 사용 (중간 건 버림)
        try:
            while True:
                chunk = self._buffer.get_nowait()
        except asyncio.QueueEmpty:
            pass

        if chunk is None:
            # 버퍼에 아무 것도 없으면 캐시나 무음 사용
            if self._latest_frame is not None:
                chunk = self._latest_frame
            else:
                chunk = b"\0" * FRAMES_PER_BUFFER * CHANNELS_STT_WEBRTC * 2

        self._latest_frame = chunk
        return chunk

    def close(self):
        if self.stream_input is not None:
            try:
                self.stream_input.stop_stream()
                self.stream_input.close()
            except Exception:
                pass
            self.stream_input = None
        # self.p (p_audio)는 전역에서 정리


# ===================================================================
# TTS 재생 작업자 (비동기)
# ===================================================================

async def playback_worker_async():
    """
    [통합/수정] 별도 Task에서 실행되며,
    'playback_queue'에 완성된 오디오 묶음이 들어오면
    순차적으로 하나씩 재생합니다.
    """
    logger.info("🎧 [Playback Worker] 준비 완료. 재생 큐 대기 중...")
    
    while True:
        try:
            global is_tts_playing
            # 큐에서 완성된 오디오 묶음을 가져옴 (없으면 대기)
            full_audio_data = await playback_queue.get()

            if full_audio_data is None:
                logger.info("🎧 [Playback Worker] 종료 신호(None) 수신. Task를 종료합니다.")
                playback_queue.task_done()
                break

            if not stream_tts:
                logger.error("🚨 [Playback Worker] PyAudio TTS 스트림이 없습니다. (재생 불가)")
                playback_queue.task_done()
                continue

            if len(full_audio_data) == 0:
                logger.warning("⚠️ [Playback Worker] 빈 오디오 데이터 수신. (무시)")
                playback_queue.task_done()
                continue
                
            logger.info(f"🎧 [Playback Worker] 큐에서 {len(full_audio_data)} 바이트 묶음 재생 시작...")
           
            is_tts_playing = True
            await sio.emit(FaceRequestEvent.REQUEST_FACE_SPEAKING, {"child_id": CHILD_ID})
            # PyAudio 스트림에 전체 데이터 쓰기 (await asyncio.to_thread 사용)
            # 이 작업이 끝날 때까지 블로킹됨
            await asyncio.to_thread(stream_tts.write, full_audio_data)
            
            await asyncio.sleep(0.5)
            playback_queue.task_done()

            is_tts_playing = False
            await sio.emit(FaceRequestEvent.REQUEST_FACE_NOT_SPEAKING,{"child_id": CHILD_ID})
            logger.info("✅ [Playback Worker] 재생 완료.")

        except Exception as e:
            logger.error(f"🚨 [Playback Worker] 오류: {e}")
            # 루프가 계속 돌도록 수정
            if not sio.connected:
                break # 소켓 연결이 끊기면 Task 종료
    
    logger.info("🎧 [Playback Worker] Task 종료됨.")


# ===================================================================
# WebRTC / Video / Audio Track (PyAudioStreamTrack, OpenCVVideoStreamTrack)
# ===================================================================

class PyAudioStreamTrack(AudioStreamTrack):
    # ... (broadcaster_for_js.py 의 PyAudioStreamTrack 클래스 내용 그대로) ...
    """
    WebRTC AudioStreamTrack: MicSource에서 프레임을 받아서 송출.
    """

    def __init__(self):
        super().__init__()
        if mic_source is None:
            raise RuntimeError("MicSource가 초기화되지 않았습니다.")
        self.samples_per_frame = int(RATE_STT_WEBRTC * AUDIO_PTIME)  # 320
        self._timestamp = 0
        logger.info("PyAudioStreamTrack initialized (MicSource 기반)")

    async def recv(self):
        # MicSource에서 최신 프레임을 가져와 AudioFrame으로 변환
        data = await mic_source.get_latest_frame()  # type: ignore[arg-type]

        samples = np.frombuffer(data, dtype=np.int16).reshape(CHANNELS_STT_WEBRTC, -1)

        frame = AudioFrame.from_ndarray(samples, format="s16", layout="mono")
        frame.sample_rate = RATE_STT_WEBRTC
        frame.time_base = Rational(1, RATE_STT_WEBRTC)
        frame.pts = self._timestamp
        # 받은 샘플 개수만큼 타임스탬프 증가 (보통 320)
        self._timestamp += samples.shape[1]

        return frame

    def stop(self):
        super().stop()
        logger.info("PyAudioStreamTrack stopped")


class OpenCVVideoStreamTrack(VideoStreamTrack):
    # ... (broadcaster_for_js.py 의 OpenCVVideoStreamTrack 클래스 내용 그대로) ...
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
        if self.capture:
            self.capture.release()
        logger.info("OpenCVVideoStreamTrack stopped")


# ===================================================================
# WebRTC 시그널링 함수
# ===================================================================


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
            # ... (로그인 상세 정보 출력 생략, 원본과 동일) ...
            logger.info("✅ WebRTC PeerConnection 연결 완료!")
            try:
                stats = await pc.getStats()
                for report in stats.values():
                    if report.type == "candidate-pair" and getattr(
                        report, "state", None
                    ) == "succeeded":
                        active_pair = report
                        local_cand = stats.get(active_pair.localCandidateId)
                        remote_cand = stats.get(active_pair.remoteCandidateId)

                        if local_cand and remote_cand:
                            local_type = local_cand.candidateType
                            remote_type = remote_cand.candidateType
                            logger.info(
                                f"✅ 연결 성공! 타입: Local({local_type}) <-> Remote({remote_type})"
                            )

                            if local_type == "relay" or remote_type == "relay":
                                logger.info(
                                    "🌐 TURN 서버를 경유한 릴레이 연결입니다."
                                )
                            else:
                                logger.info(
                                    "💻 P2P 직접 연결입니다 (host/srflx/prflx)."
                                )
            except Exception as e:
                logger.warning(f"연결 정보 확인 중 오류 발생: {e}")

        elif pc.connectionState in ["failed", "closed"]:
            logger.warning(f"Connection {pc.connectionState}. 리소스 정리 필요.")

    try:
        # 로컬 카메라 트랙을 PeerConnection에 추가합니다.
        cap = cv2.VideoCapture(0)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not cap.isOpened():
            print("Failed to open capture")
            # exit(-1) # main()에서 처리
            return

        video_track = OpenCVVideoStreamTrack(cap)
        audio_track = PyAudioStreamTrack()

        # ⬇️ WebRTC 시작 시점부터만 마이크 프레임을 WebRTC에 복사
        if mic_source is not None:
            mic_source.webrtc_enabled = True

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
        WebRTCEvents.SEND_OFFER.value,
        (SessionType.PARENT.value, PARENT_ID, offer_packet),
        # (offer_clnt_type, offer_clnt_id, offer_data)
    )


# ===================================================================
# Socket.IO 이벤트 핸들러 (WebRTC & TTS)
# ===================================================================


@sio.event
async def connect():
    """서버 연결 성공 시 (1단계)"""
    logger.info(f"Socket.IO 연결 성공 (SID: {sio.sid}).")


@sio.event
async def auth_success():
    """서버 인증 성공 시 (2단계)"""
    logger.info("🔑 Socket.IO 인증 성공! WebRTC Offer 등록/TTS 수신 준비 완료.")


@sio.on(WebRTCEvents.CAST_REQUESTED.value)
async def on_cast_requested(data: Dict[str, Any]):
    # ... (broadcaster_for_js.py 의 on_cast_requested 내용 그대로) ...
    """
    (Point 1) 뷰어(Parent)가 'REQUEST_CAST'를 보내 서버가 중계한 이벤트
    data 에는 {'opp_type': 'parent', 'opp_id': 123}가 들어옵니다.
    """
    logger.info(
        f"'CAST_REQUESTED' 수신 (from {data.get('opp_type')}:{data.get('opp_id')})"
    )
    await sio.emit(WebRTCEvents.ACCPET_REQUEST.value, (SessionType.PARENT.value, PARENT_ID))
    logger.info(f"'ACCPET_REQUEST' 전송 (to parent_id: {PARENT_ID})...")
    await start_webrtc_broadcast()


@sio.on(WebRTCEvents.PEER_IS_READY.value)
async def on_peer_is_ready(data: Dict[str, Any]):
    # ... (broadcaster_for_js.py 의 on_peer_is_ready 내용 그대로) ...
    logger.info(
        f"'PEER_IS_READY' 수신 (from {data.get('opp_type')}:{data.get('opp_id')})"
    )
    await send_offer()


@sio.on(WebRTCEvents.NEW_ANSWER.value)
async def on_new_answer(answer_data: Dict[str, Any]):
    # ... (broadcaster_for_js.py 의 on_new_answer 내용 그대로) ...
    global pc, ice_candidates_buffer  # 버퍼 전역변수 사용
    logger.info("⬇️ 'NEW_ANSWER' 수신!")
    try:
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        await pc.setRemoteDescription(answer)
        logger.info("✅ RemoteDescription (Answer) 설정 완료.")

        # 버퍼에 저장된 ICE Candidate들이 있다면 일괄 추가
        if ice_candidates_buffer:
            logger.info(
                f"📦 버퍼링된 {len(ice_candidates_buffer)}개의 ICE Candidate 추가 시작"
            )
            for candidate in ice_candidates_buffer:
                await pc.addIceCandidate(candidate)
            ice_candidates_buffer = []  # 버퍼 초기화
            logger.info("✅ 버퍼링된 ICE Candidate 추가 완료")

    except Exception as e:
        logger.error(f"Answer 처리 실패: {e}", exc_info=True)


@sio.on(WebRTCEvents.NEW_ICE_CANDIDATE.value)
async def on_new_ice_candidate(data: Dict[str, Any]):
    # ... (broadcaster_for_js.py 의 on_new_ice_candidate 내용 그대로) ...
    """Parent가 보낸 ICE Candidate 수신 (5단계)"""
    global pc, ice_candidates_buffer
    logger.info(f"⬇️ 'NEW_ICE_CANDIDATE' (from Parent) 수신")
    logger.info(f"ICE Candidate 데이터: {data}")

    try:
        candidate_str = data.get("candidate", "")

        # ✅ 1) 빈 candidate 는 end-of-candidates 로 보고 무시
        if not candidate_str:
            logger.info("비어 있는 ICE candidate 수신 → 무시 (end-of-candidates 로 간주)")
            return

        try:
            parsed_sdp = candidate_from_sdp(candidate_str)
        except AssertionError:
            # ✅ 2) 형식이 이상한 candidate 도 그냥 버린다
            logger.warning(f"형식이 잘못된 ICE candidate, 무시: {candidate_str!r}")
            return

        parsed_sdp.sdpMid = data.get("sdpMid")
        parsed_sdp.sdpMLineIndex = data.get("sdpMLineIndex")

        if pc.remoteDescription is None:
            # Remote SDP가 아직 없으면 버퍼에 저장
            logger.info(
                "⏳ RemoteDescription이 아직 없습니다. ICE Candidate를 버퍼에 저장합니다."
            )
            ice_candidates_buffer.append(parsed_sdp)
        else:
            # Remote SDP가 있으면 즉시 추가
            await pc.addIceCandidate(parsed_sdp)
            logger.info("✅ ICE Candidate 즉시 추가 완료")

    except KeyError:
        logger.error(f"ICE Candidate 처리 실패: 'candidate' 키가 없습니다. {data}")
    except Exception as e:
        logger.error(f"ICE Candidate 추가 실패: {e}", exc_info=True)


@sio.on(RobotTTSEvents.STREAM_START.value)
async def on_stream_start(data=None):
    """
    [통합/수정] 스트림 시작 시, 임시 청크 버퍼(리스트)를 초기화합니다.
    (비동기 락 사용)
    """
    global is_streaming, chunk_buffer, is_tts_streaming
    
    async with streaming_lock: # 비동기 락 사용
        logger.info(f"🔊 [TTS] 'STREAM_START' 수신. 임시 청크 버퍼를 초기화합니다.")
        is_streaming = True
        chunk_buffer.clear() # 새 오디오를 받기 위해 리스트를 비움
    
    logger.debug("  - 임시 청크 버퍼 비우기 완료.")

@sio.on(RobotTTSEvents.AUDIO_CHUNK.value)
async def on_audio_chunk(data: dict):
    """
    [통합/수정] is_streaming 상태일 때만 임시 청크 버퍼(리스트)에 쌓습니다.
    (비동기 락 사용)
    """
    global is_streaming, chunk_buffer
    
    frame_b64 = data.get("chunk")
    frame = base64.b64decode(frame_b64)

    async with streaming_lock: # 비동기 락 사용
        if not is_streaming:
            logger.warning("⚠️ [TTS] 'STREAM_START' 없이 'AUDIO_CHUNK' 수신. (무시)")
            return
        
        # logger.debug("🎧 [TTS] 'AUDIO_CHUNK' 수신. 임시 버퍼에 저장.") # 로그가 너무 많음
        chunk_buffer.append(frame)

@sio.on(RobotTTSEvents.STREAM_END.value)
async def on_stream_end():
    """
    [통합/수정] 스트림 종료 시, 임시 버퍼의 모든 청크를 '하나의 묶음'으로 합쳐
    'playback_queue'에 넣습니다. (비동기 락 사용)
    """
    global is_streaming, chunk_buffer, playback_queue
    
    full_audio_data = None

    async with streaming_lock: # 비동기 락 사용
        if not is_streaming:
            logger.warning("⚠️ [TTS] 'STREAM_START' 없이 'STREAM_END' 수신. (무시)")
            return
        
        logger.info("🏁 [TTS] 'STREAM_END' 수신. 재생 큐에 묶음을 추가합니다.")
        is_streaming = False # 스트리밍 상태 종료

        if not chunk_buffer:
            logger.warning("⚠️ [TTS] 'STREAM_END' 수신했으나 임시 버퍼가 비어있습니다.")
            return

        # 모든 청크를 하나의 바이트 스트림으로 결합
        full_audio_data = b''.join(chunk_buffer)
        chunk_buffer.clear() # 버퍼 비우기
    
    # 락(lock) 바깥에서 큐에 넣습니다.
    if full_audio_data:
        logger.info(f"  -> {len(full_audio_data)} 바이트 묶음을 재생 큐에 추가.")
        await playback_queue.put(full_audio_data)


@sio.event
async def disconnect():
    global pc, mic_source, stream_tts
    logger.warning("Socket.IO 연결 종료.")

    # WebRTC 오디오 스트리밍 비활성화
    if mic_source is not None:
        mic_source.webrtc_enabled = False

    # WebRTC PeerConnection 정리
    await pc.close()
    
    # TTS 재생 스트림 정리
    if stream_tts:
        try:
            stream_tts.stop_stream()
            stream_tts.close()
            stream_tts = None
            logger.info("🔊 PyAudio TTS 스트림 닫힘.")
        except Exception as e:
            logger.warning(f"TTS 스트림 정리 중 오류: {e}")
            pass


# ===================================================================
# 메인 실행 함수
# ===================================================================

async def main():
    global azure_stt, mic_source, p_audio, stream_tts, is_tts_playing

    loop = asyncio.get_running_loop()
    playback_task = None # [신규] 재생 작업자 Task 핸들

    # STT 결과를 서버 대신 일단 print로만 출력
    def on_stt_result(text: str):
        if is_tts_playing: # Stop send text when playing tts
            return
        print(f"[STT] {text}")
        resp = http_client.post(f"{BASE_URL}/chat/child_start/1", json={"text":text})
        
    try:
        # --- 1단계: PyAudio 초기화 ---
        logger.info("🔊 PyAudio 초기화 중...")
        p_audio = pyaudio.PyAudio()
        
        # TTS 재생 스트림 열기 (24kHz)
        stream_tts = p_audio.open(format=FORMAT_TTS_PLAYBACK,
                                  channels=CHANNELS_TTS_PLAYBACK,
                                  rate=RATE_TTS_PLAYBACK,
                                  output=True,
                                  frames_per_buffer=4096)
        logger.info(f"🔊 PyAudio TTS 스트림 ({RATE_TTS_PLAYBACK}Hz) 열기 성공.")
        
        # --- [신규] TTS 재생 작업자 Task 시작 ---
        playback_task = loop.create_task(playback_worker_async())


        # --- 2단계: Azure STT 초기화 & 시작 ---
        try:
            azure_stt = AzureSTT(on_stt_result)
            azure_stt.start()
            logger.info("Azure STT continuous recognition started")
        except Exception as e:
            logger.error(f"Azure STT 초기화 실패: {e}")
            azure_stt = None

        # --- 3단계: MicSource 시작 (항상 마이크를 읽어서 STT로 보냄) ---
        mic_source = MicSource(stt=azure_stt, device_index=DEVICE_INDEX)
        mic_source.start(loop)

        # --- 4단계: Socket.IO 연결 (WebRTC 시그널링 & TTS 수신) ---
        await sio.connect(
            BASE_URL,
            transports=["websocket"],
            auth={"token": ACCESS_TOKEN, 
                "session_type": SESSION_TYPE,
                "robot_id": ROBOT_ID
            },
        )
        await sio.wait()
        
    except socketio.exceptions.ConnectionError as e:
        logger.error(f"시그널링 서버 연결 실패: {e}")
    except KeyboardInterrupt:
        logger.info("\n프로그램을 종료합니다.")
    except Exception as e:
        logger.error(f"\n--- 🚨 테스트 중단: {e} ---", exc_info=True)
    finally:
        logger.info("--- 통합 클라이언트 종료 및 정리 시작 ---")
        
        # Socket.IO 연결 해제 및 WebRTC 정리
        if sio.connected:
            await sio.disconnect()

        # MicSource 정리
        if mic_source is not None:
            mic_source.webrtc_enabled = False
            mic_source.close()
            
        # TTS 재생 Task에 종료 신호(None) 전송 및 대기
        if playback_task and not playback_task.done():
            logger.info("🎧 [Main] TTS 재생 작업자 Task에 종료 신호 전송...")
            await playback_queue.put(None)
            try:
                await asyncio.wait_for(playback_task, timeout=2)
            except asyncio.TimeoutError:
                logger.warning("⚠️ [Main] 재생 작업자 Task가 시간 내에 종료되지 않았습니다.")
            
        # Azure STT 정리
        if azure_stt is not None:
            try:
                azure_stt.stop()
            except Exception:
                pass

        # PyAudio 인스턴스 최종 정리
        logger.info("🔊 PyAudio 리소스 정리 중...")
        if p_audio:
            try:
                p_audio.terminate()
                logger.info("   - PyAudio 인스턴스 종료됨.")
            except Exception:
                pass
        
        logger.info("--- 통합 클라이언트 종료 완료 ---")


if __name__ == "__main__":
    
    # --- [HTTP 5] 로봇 로그인 (토큰 획득) ---
    print("--- [HTTP] 로봇 로그인 (토큰 획득) ---")
    log_data = {"robot_id": ROBOT_ID, "serial_number": TEST_ROBOT_SN}
    try:
        resp = http_client.post(f"{BASE_URL}{DEBUG_PREFIX}/auth/login/robot", json=log_data)
        resp.raise_for_status()
        robot_access_token = resp.json()["access_token"]
        print(f"✅ 로그인 성공 (Token: {robot_access_token[:10]}...)")
        ACCESS_TOKEN = robot_access_token
    except Exception as e:
        logger.error(f"🚨 로봇 로그인 실패: {e}")
        # exit(-1) # 실패 시 종료하는 것이 안전
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n프로그램을 종료합니다.")
