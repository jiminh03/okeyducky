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
        print(f"{client_type} client type not exist")

    return session_info


@sio.on(TTSEvents.AI_TO_BE_STREAM_START)
async def on_stream_start(sid, data: dict):
    """AI 서버로부터 스트림 시작 신호를 받아 로봇에게 중계"""
    child_id = data.get("child_id")
    if not child_id:
        return

    print(f"tts log: stream start , AI_SID: {sid}, Child: {child_id}")
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
async def on_stream_end(sid, data: dict): # [수정] 함수 이름 및 인자
    """AI 서버로부터 스트림 종료 신호를 받아 로봇에게 중계"""
    child_id = data.get("child_id")
    if not child_id:
        return

    print(f"tts log: stream end , AI_SID: {sid}, Child: {child_id}") # [수정] 로그
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    requested_session_info = await _get_session_info(
        sess_man, SessionType.ROBOT, child_id
    )
    
    if requested_session_info:
        await sio.emit(RobotTTSEvents.STREAM_END, to=requested_session_info.sid)

@sio.on(TTSEvents.AI_TO_BE_AUDIO_CHUNK)
async def on_audio_chunk(sid, data: dict): # [수정] 인자를 data: dict로 받음
    """AI 서버로부터 오디오 청크를 받아 로봇에게 바이너리로 중계"""
    child_id = data.get("child_id")
    chunk = data.get("chunk") # 딕셔너리에서 chunk(bytes) 추출
    
    if not child_id or not chunk:
        return

    # print(f"tts log: audio chunk , AI_SID: {sid}, Child: {child_id}, Size: {len(chunk)}") # (디버깅용)
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    requested_session_info = await _get_session_info(
        sess_man, SessionType.ROBOT, child_id
    )
    
    if requested_session_info:
        # `data=` 인자에 raw bytes(chunk)를 직접 전달하면
        # Socket.IO가 알아서 바이너리 프레임으로 전송합니다.
        await sio.emit(
            RobotTTSEvents.AUDIO_CHUNK,
            to=requested_session_info.sid,
            data=chunk
        )