import os
import asyncio
import json
import logging
import base64
import queue
from datetime import datetime
from typing import Dict, Any
from fractions import Fraction as Rational
from enum import Enum

from dotenv import load_dotenv
import cv2
import numpy as np
import pyaudio
import requests
import socketio
import azure.cognitiveservices.speech as speechsdk
from aiortc import (
    RTCConfiguration,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
    AudioStreamTrack,
    VideoStreamTrack,
)
from aiortc.sdp import candidate_from_sdp
from av import AudioFrame, VideoFrame

# 환경 변수 로드
load_dotenv()

# -------------------------------------------------------------------
# 1. 설정 및 상수 (Configuration & Constants)
# -------------------------------------------------------------------

# 네트워크 및 서버 설정
BASE_URL = "http://k13a408.p.ssafy.io:8000"

# 인증 및 식별자 설정
ACCESS_TOKEN = "YOUR_VALID_JWT_TOKEN_HERE"  # 로봇 로그인 토큰
PARENT_ID = 1
ROBOT_ID = 1
TEST_ROBOT_SN = "SN-WEBRTC-WEBRTC"
CHILD_ID = 1
SESSION_TYPE = "robot"

# STT (Azure) 및 WebRTC 오디오 입력 설정
RATE_STT_WEBRTC = 16000
FORMAT_STT_WEBRTC = pyaudio.paInt16
CHANNELS_STT_WEBRTC = 1
FRAMES_PER_BUFFER = 2048
AUDIO_PTIME = 0.020
DEVICE_INDEX = 0

# TTS 재생 (PyAudio) 설정
RATE_TTS_PLAYBACK = 24000
FORMAT_TTS_PLAYBACK = pyaudio.paInt16
CHANNELS_TTS_PLAYBACK = 1

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unified_broadcaster")


# -------------------------------------------------------------------
# 2. 전역 변수 및 객체 초기화 (Global Objects & State)
# -------------------------------------------------------------------

# 통신 클라이언트
http_client = requests.Session()
sio = socketio.AsyncClient(logger=False, engineio_logger=False)

# WebRTC 전역 객체
ice_servers = [RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
config = RTCConfiguration(iceServers=ice_servers)
pc = RTCPeerConnection()
ice_candidates_buffer = []

# 오디오 장치 및 처리 객체
p_audio: pyaudio.PyAudio | None = None
stream_tts: pyaudio.Stream | None = None
azure_stt: "AzureSTT" = None
mic_source: "MicSource" = None

# 비동기 큐 및 락
playback_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
streaming_lock = asyncio.Lock()

# 상태 플래그
chunk_buffer: list[bytes] = []
is_streaming = False
is_tts_playing = False


# -------------------------------------------------------------------
# 3. Enum 정의 (Enums)
# -------------------------------------------------------------------


class FaceRequestEvent(str, Enum):
    """얼굴 표정 변경 요청 이벤트"""

    REQUEST_FACE_NORMAL = "client:request_face_normal"
    REQUEST_FACE_HEART = "client:request_face_heart"
    REQUEST_FACE_SAD = "client:request_face_sad"
    REQUEST_FACE_SPEAKING = "server:face_speaking"
    REQUEST_FACE_NOT_SPEAKING = "server:face_not_speaking"


class ConnectEvents(str, Enum):
    """소켓 연결 관련 이벤트"""

    AUTH_SUCCESS = "auth_success"
    AuTH_FAILURE = "auth_failure"
    CONNECT = "connect"
    DISCONNECT = "disconnect"


class WebRTCEvents(str, Enum):
    """WebRTC 시그널링 이벤트"""

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
    """TTS 스트리밍 이벤트"""

    STREAM_START = "server:stream_start"
    AUDIO_CHUNK = "server:audio_chunk"
    STREAM_END = "server:stream_end"


class SessionType(Enum):
    PARENT = "parent"
    ROBOT = "robot"


# -------------------------------------------------------------------
# 4. 클래스 정의 (Classes: STT, Mic, WebRTC Tracks)
# -------------------------------------------------------------------


class AzureSTT:
    """Azure Speech SDK STT 래퍼"""

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
            speech_config=speech_config, audio_config=audio_config
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
        self._push_stream.write(data)


class MicSource:
    """PyAudio 입력을 읽어 Azure STT 전송 및 WebRTC용 버퍼링 처리"""

    global p_audio

    def __init__(self, stt: AzureSTT | None = None, device_index: int | None = None):
        if p_audio is None:
            raise RuntimeError("PyAudio 인스턴스가 초기화되지 않았습니다.")

        self.p = p_audio
        self.stream_input = self.p.open(
            format=FORMAT_STT_WEBRTC,
            channels=CHANNELS_STT_WEBRTC,
            rate=RATE_STT_WEBRTC,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER,
        )
        self.stt = stt
        self.webrtc_enabled: bool = False
        self._input_channels = CHANNELS_STT_WEBRTC
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
                try:
                    data = await asyncio.to_thread(
                        self.stream_input.read,
                        FRAMES_PER_BUFFER,
                        exception_on_overflow=False,
                    )
                except Exception as e:
                    logger.warning(f"MicSource: PyAudio read 오류, 무음 전송: {e}")
                    data = b"\0" * FRAMES_PER_BUFFER * CHANNELS_STT_WEBRTC * 2

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

                # STT 전송
                if self.stt is not None:
                    try:
                        self.stt.push_audio(mono_bytes)
                    except Exception as e:
                        logger.warning(f"MicSource: STT push 실패: {e}")

                # WebRTC 버퍼링
                if self.webrtc_enabled:
                    try:
                        self._buffer.put_nowait(mono_bytes)
                    except asyncio.QueueFull:
                        try:
                            _ = self._buffer.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                        try:
                            self._buffer.put_nowait(mono_bytes)
                        except asyncio.QueueFull:
                            pass
                    self._latest_frame = mono_bytes
                    if not self._frame_event.is_set():
                        self._frame_event.set()

        except asyncio.CancelledError:
            logger.info("MicSource: 캡쳐 루프 취소")
        except Exception as e:
            logger.error(f"MicSource: 예외 발생: {e}", exc_info=True)
        finally:
            self.close()

    async def get_latest_frame(self) -> bytes:
        await self._frame_event.wait()
        self._frame_event.clear()
        chunk: bytes | None = None
        try:
            while True:
                chunk = self._buffer.get_nowait()
        except asyncio.QueueEmpty:
            pass

        if chunk is None:
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


class PyAudioStreamTrack(AudioStreamTrack):
    """WebRTC Audio Track (MicSource 기반)"""

    def __init__(self):
        super().__init__()
        if mic_source is None:
            raise RuntimeError("MicSource가 초기화되지 않았습니다.")
        self.samples_per_frame = int(RATE_STT_WEBRTC * AUDIO_PTIME)
        self._timestamp = 0
        logger.info("PyAudioStreamTrack initialized")

    async def recv(self):
        data = await mic_source.get_latest_frame()
        samples = np.frombuffer(data, dtype=np.int16).reshape(CHANNELS_STT_WEBRTC, -1)
        frame = AudioFrame.from_ndarray(samples, format="s16", layout="mono")
        frame.sample_rate = RATE_STT_WEBRTC
        frame.time_base = Rational(1, RATE_STT_WEBRTC)
        frame.pts = self._timestamp
        self._timestamp += samples.shape[1]
        return frame

    def stop(self):
        super().stop()
        logger.info("PyAudioStreamTrack stopped")


class OpenCVVideoStreamTrack(VideoStreamTrack):
    """WebRTC Video Track (Webcam 기반)"""

    def __init__(self, capture):
        super().__init__()
        self.capture = capture
        self.frame_count = 0
        logger.info("OpenCVVideoStreamTrack initialized")

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


# -------------------------------------------------------------------
# 5. 비동기 작업 함수 (Async Workers)
# -------------------------------------------------------------------


async def playback_worker_async():
    """TTS 오디오 재생 큐 처리 워커"""
    logger.info("[Playback Worker] 준비 완료. 재생 큐 대기 중...")

    while True:
        try:
            global is_tts_playing
            full_audio_data = await playback_queue.get()

            if full_audio_data is None:
                logger.info("[Playback Worker] 종료 신호 수신.")
                playback_queue.task_done()
                break

            if not stream_tts:
                logger.error("[Playback Worker] PyAudio TTS 스트림 없음.")
                playback_queue.task_done()
                continue

            if len(full_audio_data) == 0:
                logger.warning("[Playback Worker] 빈 오디오 데이터 무시.")
                playback_queue.task_done()
                continue

            logger.info(f"[Playback Worker] 재생 시작: {len(full_audio_data)} bytes")

            is_tts_playing = True
            await sio.emit(
                FaceRequestEvent.REQUEST_FACE_SPEAKING, {"child_id": CHILD_ID}
            )
            await asyncio.to_thread(stream_tts.write, full_audio_data)

            await asyncio.sleep(0.5)
            playback_queue.task_done()

            is_tts_playing = False
            await sio.emit(
                FaceRequestEvent.REQUEST_FACE_NOT_SPEAKING, {"child_id": CHILD_ID}
            )
            logger.info("[Playback Worker] 재생 완료.")

        except Exception as e:
            logger.error(f"[Playback Worker] 오류: {e}")
            if not sio.connected:
                break

    logger.info("[Playback Worker] Task 종료됨.")


# -------------------------------------------------------------------
# 6. WebRTC 로직 함수 (WebRTC Logic)
# -------------------------------------------------------------------


async def start_webrtc_broadcast():
    """WebRTC PeerConnection 초기화 및 Offer 전송"""
    global pc
    if pc.connectionState != "closed":
        await pc.close()

    config = RTCConfiguration(
        iceServers=[
            RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
            RTCIceServer(
                urls=["turn:3.38.103.192"],
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
            logger.info("WebRTC PeerConnection 연결 완료!")
            try:
                stats = await pc.getStats()
                for report in stats.values():
                    if (
                        report.type == "candidate-pair"
                        and getattr(report, "state", None) == "succeeded"
                    ):
                        active_pair = report
                        local_cand = stats.get(active_pair.localCandidateId)
                        remote_cand = stats.get(active_pair.remoteCandidateId)
                        if local_cand and remote_cand:
                            logger.info(
                                f"연결 타입: Local({local_cand.candidateType}) <-> Remote({remote_cand.candidateType})"
                            )
            except Exception as e:
                logger.warning(f"연결 정보 확인 중 오류: {e}")

        elif pc.connectionState in ["failed", "closed"]:
            logger.warning(f"Connection {pc.connectionState}. 리소스 정리 필요.")

    try:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not cap.isOpened():
            print("Failed to open capture")
            return

        video_track = OpenCVVideoStreamTrack(cap)
        audio_track = PyAudioStreamTrack()

        if mic_source is not None:
            mic_source.webrtc_enabled = True

        pc.addTrack(video_track)
        pc.addTrack(audio_track)
        logger.info("카메라 트랙 추가 완료")
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
    )


# -------------------------------------------------------------------
# 7. Socket.IO 이벤트 핸들러 (Socket.IO Handlers)
# -------------------------------------------------------------------


@sio.event
async def connect():
    logger.info(f"Socket.IO 연결 성공 (SID: {sio.sid}).")


@sio.event
async def auth_success():
    logger.info("Socket.IO 인증 성공! WebRTC/TTS 준비 완료.")


@sio.on(WebRTCEvents.CAST_REQUESTED.value)
async def on_cast_requested(data: Dict[str, Any]):
    logger.info(
        f"'CAST_REQUESTED' 수신 (from {data.get('opp_type')}:{data.get('opp_id')})"
    )
    await sio.emit(
        WebRTCEvents.ACCPET_REQUEST.value, (SessionType.PARENT.value, PARENT_ID)
    )
    logger.info(f"'ACCPET_REQUEST' 전송 (to parent_id: {PARENT_ID})...")
    await start_webrtc_broadcast()


@sio.on(WebRTCEvents.PEER_IS_READY.value)
async def on_peer_is_ready(data: Dict[str, Any]):
    logger.info(
        f"'PEER_IS_READY' 수신 (from {data.get('opp_type')}:{data.get('opp_id')})"
    )
    await send_offer()


@sio.on(WebRTCEvents.NEW_ANSWER.value)
async def on_new_answer(answer_data: Dict[str, Any]):
    global pc, ice_candidates_buffer
    logger.info("'NEW_ANSWER' 수신!")
    try:
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        await pc.setRemoteDescription(answer)
        logger.info("RemoteDescription (Answer) 설정 완료.")

        if ice_candidates_buffer:
            logger.info(
                f"버퍼링된 {len(ice_candidates_buffer)}개의 ICE Candidate 추가 시작"
            )
            for candidate in ice_candidates_buffer:
                await pc.addIceCandidate(candidate)
            ice_candidates_buffer = []
            logger.info("버퍼링된 ICE Candidate 추가 완료")

    except Exception as e:
        logger.error(f"Answer 처리 실패: {e}", exc_info=True)


@sio.on(WebRTCEvents.NEW_ICE_CANDIDATE.value)
async def on_new_ice_candidate(data: Dict[str, Any]):
    global pc, ice_candidates_buffer
    logger.info("'NEW_ICE_CANDIDATE' 수신")
    try:
        candidate_str = data.get("candidate", "")
        if not candidate_str:
            logger.info("빈 ICE candidate 수신 (무시)")
            return

        try:
            parsed_sdp = candidate_from_sdp(candidate_str)
        except AssertionError:
            logger.warning(f"형식이 잘못된 ICE candidate 무시: {candidate_str!r}")
            return

        parsed_sdp.sdpMid = data.get("sdpMid")
        parsed_sdp.sdpMLineIndex = data.get("sdpMLineIndex")

        if pc.remoteDescription is None:
            logger.info("RemoteDescription 없음. ICE Candidate 버퍼링.")
            ice_candidates_buffer.append(parsed_sdp)
        else:
            await pc.addIceCandidate(parsed_sdp)
            logger.info("ICE Candidate 즉시 추가 완료")

    except KeyError:
        logger.error(f"ICE Candidate 처리 실패: 키 없음 {data}")
    except Exception as e:
        logger.error(f"ICE Candidate 추가 실패: {e}", exc_info=True)


@sio.on(RobotTTSEvents.STREAM_START.value)
async def on_stream_start(data=None):
    global is_streaming, chunk_buffer
    async with streaming_lock:
        logger.info("[TTS] 'STREAM_START' 수신. 버퍼 초기화.")
        is_streaming = True
        chunk_buffer.clear()


@sio.on(RobotTTSEvents.AUDIO_CHUNK.value)
async def on_audio_chunk(data: dict):
    global is_streaming, chunk_buffer
    frame_b64 = data.get("chunk")
    frame = base64.b64decode(frame_b64)

    async with streaming_lock:
        if not is_streaming:
            logger.warning("[TTS] 스트림 시작 전 청크 수신 (무시).")
            return
        chunk_buffer.append(frame)


@sio.on(RobotTTSEvents.STREAM_END.value)
async def on_stream_end():
    global is_streaming, chunk_buffer, playback_queue
    full_audio_data = None

    async with streaming_lock:
        if not is_streaming:
            logger.warning("[TTS] 스트림 시작 전 종료 신호 수신 (무시).")
            return

        logger.info("[TTS] 'STREAM_END' 수신.")
        is_streaming = False

        if not chunk_buffer:
            logger.warning("[TTS] 버퍼가 비어있음.")
            return

        full_audio_data = b"".join(chunk_buffer)
        chunk_buffer.clear()

    if full_audio_data:
        logger.info(f"재생 큐에 {len(full_audio_data)} 바이트 추가.")
        await playback_queue.put(full_audio_data)


@sio.event
async def disconnect():
    global pc, mic_source, stream_tts
    logger.warning("Socket.IO 연결 종료.")

    if mic_source is not None:
        mic_source.webrtc_enabled = False

    await pc.close()

    if stream_tts:
        try:
            stream_tts.stop_stream()
            stream_tts.close()
            stream_tts = None
            logger.info("PyAudio TTS 스트림 닫힘.")
        except Exception as e:
            logger.warning(f"TTS 스트림 정리 중 오류: {e}")


# -------------------------------------------------------------------
# 8. 메인 함수 및 엔트리 포인트 (Main Logic)
# -------------------------------------------------------------------


async def main():
    global azure_stt, mic_source, p_audio, stream_tts, is_tts_playing

    loop = asyncio.get_running_loop()
    playback_task = None

    def on_stt_result(text: str):
        if is_tts_playing:
            return
        print(f"[STT] {text}")
        http_client.post(f"{BASE_URL}/chat/child_start/{CHILD_ID}", json={"text": text})

    try:
        # 1. PyAudio 초기화
        logger.info("PyAudio 초기화 중...")
        p_audio = pyaudio.PyAudio()
        stream_tts = p_audio.open(
            format=FORMAT_TTS_PLAYBACK,
            channels=CHANNELS_TTS_PLAYBACK,
            rate=RATE_TTS_PLAYBACK,
            output=True,
            frames_per_buffer=4096,
        )
        logger.info(f"PyAudio TTS 스트림 ({RATE_TTS_PLAYBACK}Hz) 열기 성공.")

        # TTS 워커 시작
        playback_task = loop.create_task(playback_worker_async())

        # 2. Azure STT 초기화
        try:
            azure_stt = AzureSTT(on_stt_result)
            azure_stt.start()
            logger.info("Azure STT continuous recognition started")
        except Exception as e:
            logger.error(f"Azure STT 초기화 실패: {e}")
            azure_stt = None

        # 3. MicSource 시작
        mic_source = MicSource(stt=azure_stt, device_index=DEVICE_INDEX)
        mic_source.start(loop)

        # 4. Socket.IO 연결
        await sio.connect(
            BASE_URL,
            transports=["websocket"],
            auth={
                "token": ACCESS_TOKEN,
                "session_type": SESSION_TYPE,
                "robot_id": ROBOT_ID,
            },
        )
        await sio.wait()

    except socketio.exceptions.ConnectionError as e:
        logger.error(f"시그널링 서버 연결 실패: {e}")
    except KeyboardInterrupt:
        logger.info("\n프로그램을 종료합니다.")
    except Exception as e:
        logger.error(f"\n테스트 중단: {e}", exc_info=True)
    finally:
        logger.info("통합 클라이언트 종료 및 정리 시작")

        if sio.connected:
            await sio.disconnect()

        if mic_source is not None:
            mic_source.webrtc_enabled = False
            mic_source.close()

        if playback_task and not playback_task.done():
            logger.info("[Main] TTS 재생 작업자 Task에 종료 신호 전송...")
            await playback_queue.put(None)
            try:
                await asyncio.wait_for(playback_task, timeout=2)
            except asyncio.TimeoutError:
                logger.warning(
                    "[Main] 재생 작업자 Task가 시간 내에 종료되지 않았습니다."
                )

        if azure_stt is not None:
            try:
                azure_stt.stop()
            except Exception:
                pass

        logger.info("PyAudio 리소스 정리 중...")
        if p_audio:
            try:
                p_audio.terminate()
                logger.info("PyAudio 인스턴스 종료됨.")
            except Exception:
                pass

        logger.info("통합 클라이언트 종료 완료")


if __name__ == "__main__":

    # --- [입력 단계] 초기 설정값 입력 받기 ---
    print("\n========== [설정 입력] ==========")
    print("※ 값을 입력하지 않고 엔터(Enter)를 누르면 '기본값'으로 진행됩니다.")

    input_id = input(f"1. 로봇 ID 입력 (기본값: {ROBOT_ID}): ").strip()
    if input_id:
        try:
            ROBOT_ID = int(input_id)
        except ValueError:
            print("⚠️ 잘못된 숫자 형식입니다. 기본값으로 진행합니다.")

    input_sn = input(f"2. 시리얼 넘버 입력 (기본값: {TEST_ROBOT_SN}): ").strip()
    if input_sn:
        TEST_ROBOT_SN = input_sn

    print(f"▶ 최종 설정 -> Robot ID: {ROBOT_ID}, S/N: {TEST_ROBOT_SN}")
    print("=================================\n")

    # --- [HTTP] 로봇 로그인 및 정보 획득 ---
    print("--- [HTTP] 로봇 로그인 (토큰 획득) ---")
    log_data = {"robot_id": ROBOT_ID, "serial_number": TEST_ROBOT_SN}

    try:
        # 1. 로그인 요청 (토큰 발급)
        resp = http_client.post(f"{BASE_URL}/auth/login/robot", json=log_data)
        resp.raise_for_status()

        robot_access_token = resp.json()["access_token"]
        print(f"✅ 로그인 성공 (Token: {robot_access_token[:10]}...)")
        ACCESS_TOKEN = robot_access_token  # 전역 변수 업데이트

        # [핵심 변경 사항] 세션 헤더에 인증 토큰 등록
        # 이제부터 http_client로 보내는 모든 요청에 자동으로 헤더가 포함됩니다.
        http_client.headers.update({"Authorization": f"Bearer {ACCESS_TOKEN}"})
        print("✅ HTTP 인증 헤더 설정 완료 (Authorization: Bearer ...)")

        # 2. 로봇 정보 조회 (Child ID / Parent ID)
        # 이전처럼 body에 토큰을 넣을 필요 없이 호출만 하면 됩니다.
        # (※ 서버가 헤더 인증 방식을 지원하도록 구현되어 있어야 합니다)

        # Child ID 획득
        resp = http_client.get(f"{BASE_URL}/robot/self")
        resp.raise_for_status()
        CHILD_ID = resp.json().get("child_id")
        print(f"✅ 로봇 정보 조회 성공 (Child ID: {CHILD_ID})")

        # Parent ID 획득
        # (만약 서버 응답 하나에 child_id, parent_id가 다 들어있다면 한 번만 호출해도 됩니다)
        resp = http_client.get(f"{BASE_URL}/robot/parent")
        resp.raise_for_status()
        PARENT_ID = resp.json().get("parent_id")
        print(f"✅ 로봇 정보 조회 성공 (Parent ID: {PARENT_ID})")

    except Exception as e:
        logger.error(f"🚨 로봇 로그인 또는 정보 조회 실패: {e}")
        # exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n프로그램을 종료합니다.")
