from ai.websocket import sio

from common.schemas.socket_event_schema import TTSEvents

async def send_stream_start(child_id: int):
    await sio.emit(TTSEvents.AI_TO_BE_STREAM_START, {"child_id": child_id})

async def send_audio_chunk(child_id: int, frames: bytes):
    await sio.emit(TTSEvents.AI_TO_BE_AUDIO_CHUNK, {"child_id": child_id, "chunk": frames})

async def send_stream_end(child_id: int):
    await sio.emit(TTSEvents.AI_TO_BE_STREAM_END, {"child_id": child_id})