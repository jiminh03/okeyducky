import base64
from loguru import logger

from ai.websocket import sio_ai

from common.schemas.socket_event_schema import TTSEvents

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