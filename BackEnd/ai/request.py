import base64
from loguru import logger

from ai.websocket import sio_ai

from common.schemas.socket_event_schema import TTSEvents, FaceRequestEvent


async def send_stream_start(child_id: int):
    # [로그 추가]
    logger.info(f"<- [Socket Emit] 'AI_TO_BE_STREAM_START' 전송 (Child: {child_id})")
    await sio_ai.emit(TTSEvents.AI_TO_BE_STREAM_START, {"child_id": child_id}, )

async def send_audio_chunk(child_id: int, frames: bytes):
    # [로그 추가] (청크 크기도 함께 로깅)
    #logger.info(f"<- [Socket Emit] 'AI_TO_BE_AUDIO_CHUNK' 전송 (Child: {child_id}, Size: {len(frames)})")
    frames_b64 = base64.b64encode(frames).decode('utf-8')
    payload = {
        "child_id": child_id, 
        "chunk": frames_b64 # "U3RyaW5n..." 같은 문자열
    }
    await sio_ai.emit(TTSEvents.AI_TO_BE_AUDIO_CHUNK, payload, )

async def send_stream_end(child_id: int):
    # [로그 추가]
    logger.info(f"<- [Socket Emit] 'AI_TO_BE_STREAM_END' 전송 (Child: {child_id})")
    await sio_ai.emit(TTSEvents.AI_TO_BE_STREAM_END, {"child_id": child_id}, )

async def send_face_request(child_id: int, emotion_tag: str):
    # [로그 추가]
    logger.info(f"<- [Socket Emit] 'FACE_REQUEST' 전송 (Child: {child_id}, Face: {emotion_tag})")

    if emotion_tag == "(기본 표정)":
        await sio_ai.emit(FaceRequestEvent.REQUEST_FACE_NORMAL, {"child_id": child_id}, )
    elif emotion_tag == "(하트눈 표정)":
        await sio_ai.emit(FaceRequestEvent.REQUEST_FACE_HEART, {"child_id": child_id}, )
    elif emotion_tag == "(슬픈 표정)":
        await sio_ai.emit(FaceRequestEvent.REQUEST_FACE_SAD, {"child_id": child_id}, )
    else:
        print(f"알 수 없는 표정입니다: {emotion_tag}")

    