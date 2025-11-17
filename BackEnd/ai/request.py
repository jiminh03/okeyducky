from ai.websocket import sio_ai

from common.schemas.socket_event_schema import TTSEvents

async def send_stream_start(child_id: int):
    # [로그 추가]
    print(f"<- [Socket Emit] 'AI_TO_BE_STREAM_START' 전송 (Child: {child_id})")
    await sio_ai.emit(TTSEvents.AI_TO_BE_STREAM_START, {"child_id": child_id}, )

async def send_audio_chunk(child_id: int, frames: bytes):
    # [로그 추가] (청크 크기도 함께 로깅)
    print(f"<- [Socket Emit] 'AI_TO_BE_AUDIO_CHUNK' 전송 (Child: {child_id}, Size: {len(frames)})")
    await sio_ai.emit(TTSEvents.AI_TO_BE_AUDIO_CHUNK, {"child_id": child_id, "chunk": frames}, )

async def send_stream_end(child_id: int):
    # [로그 추가]
    print(f"<- [Socket Emit] 'AI_TO_BE_STREAM_END' 전송 (Child: {child_id})")
    await sio_ai.emit(TTSEvents.AI_TO_BE_STREAM_END, {"child_id": child_id}, )