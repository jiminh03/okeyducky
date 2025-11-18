from loguru import logger

from typing import Dict, Optional

from common.schemas.session_schema import ConnectionInfo, SessionType
from common.modules.session_manager import SessionManager

from common.modules.db_instance import red

from app.modules.websocket_module import sio

from common.schemas.socket_event_schema import TTSEvents, RobotTTSEvents


# --- 헬퍼 함수 (유지) ---
async def _get_session_info(
    sess_man: SessionManager, client_type: SessionType, client_id: int
) -> Optional[ConnectionInfo]: 
    """클라이언트 타입과 ID를 기반으로 세션 정보를 가져오는 헬퍼 함수"""
    session_info = None
    if client_type == SessionType.PARENT.value:
        session_info = await sess_man.get_session_by_parent_id(client_id)
    elif client_type == SessionType.ROBOT.value:
        session_info = await sess_man.get_session_by_robot_id(client_id)
    else:
        logger.info(f"{client_type} client type not exist")

    return session_info


@sio.on(TTSEvents.AI_TO_BE_STREAM_START)
async def on_stream_start(sid, data: dict):
    """AI 서버로부터 스트림 시작 신호를 받아 로봇에게 중계"""
    # [로그 추가] 이벤트 수신 즉시 로그 기록
    logger.info(f"-> [Event Received] 'AI_TO_BE_STREAM_START' from AI_SID: {sid}")

    child_id = data.get("child_id")
    if not child_id:
        logger.info("   [Event Error] child_id not in data.")
        return

    logger.info(f"   [TTS Relay] stream start, Child: {child_id}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    requested_session_info = await _get_session_info(
        sess_man, SessionType.ROBOT, child_id
    )
    
    if requested_session_info:
        await sio.emit(
            RobotTTSEvents.STREAM_START,
            to=requested_session_info.sid,
        )

@sio.on(TTSEvents.AI_TO_BE_STREAM_END)
async def on_stream_end(sid, data: dict):
    """AI 서버로부터 스트림 종료 신호를 받아 로봇에게 중계"""
    # [로그 추가] 이벤트 수신 즉시 로그 기록
    logger.info(f"-> [Event Received] 'AI_TO_BE_STREAM_END' from AI_SID: {sid}")

    child_id = data.get("child_id")
    if not child_id:
        logger.info("   [Event Error] child_id not in data.")
        return

    logger.info(f"   [TTS Relay] stream end, Child: {child_id}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    requested_session_info = await _get_session_info(
        sess_man, SessionType.ROBOT, child_id
    )
    
    if requested_session_info:
        await sio.emit(RobotTTSEvents.STREAM_END, to=requested_session_info.sid)

@sio.on(TTSEvents.AI_TO_BE_AUDIO_CHUNK)
async def on_audio_chunk(sid, data: dict):
    """AI 서버로부터 오디오 청크를 받아 로봇에게 바이너리로 중계"""
    # [로그 추가] 이벤트 수신 즉시 로그 기록
    # (chunk 데이터는 너무 크므로 로그에서 제외)
    #logger.info(f"-> [Event Received] 'AI_TO_BE_AUDIO_CHUNK' from AI_SID: {sid}")

    child_id = data.get("child_id")
    chunk = data.get("chunk")
    
    if not child_id or not chunk:
        logger.info("   [Event Error] child_id or chunk not in data.")
        return

    # logger.info(f"   [TTS Relay] audio chunk, Child: {child_id}, Size: {len(chunk)}") # (디버깅용)
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    requested_session_info = await _get_session_info(
        sess_man, SessionType.ROBOT, child_id
    )
    
    if requested_session_info:
        await sio.emit(
            RobotTTSEvents.AUDIO_CHUNK,
            to=requested_session_info.sid,
            data=data
        )