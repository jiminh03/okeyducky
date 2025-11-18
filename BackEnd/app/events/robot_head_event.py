from enum import Enum
from typing import Optional

from loguru import logger

from common.schemas.session_schema import ConnectionInfo, SessionType
from common.schemas.socket_event_schema import FaceEvent, FaceRequestEvent
from common.modules.session_manager import SessionManager
from common.modules.db_instance import red



from app.modules.websocket_module import sio


# --- 헬퍼 함수 ---
# (사용자 예제에서 가져온 헬퍼)
async def _get_head_session_info(
    sess_man: SessionManager, child_id: int
) -> Optional[ConnectionInfo]:
    """클라이언트 타입과 ID를 기반으로 세션 정보를 가져오는 헬퍼 함수"""
    #TODO:어린이 아이디로 머리 아이디(부모 아이디로 사용중)조회하는 기능 필요
    session_info = sess_man.get_session_by_robot_head_id(1)

    return session_info


# --- 로봇 얼굴 표정 이벤트 핸들러 ---
# 클라이언트(FE) -> 서버 -> 로봇
# 클라이언트가 [C->S] FaceRequestEvent를 보내면,
# 서버가 [S->C] FaceEvent를 로봇에게 전송합니다.

@sio.on(FaceRequestEvent.REQUEST_FACE_NORMAL)
async def on_request_face_normal(sid, robot_clnt_type: SessionType, robot_clnt_id: int):
    """
    [C->S] 클라이언트(FE)가 서버에 '평소 얼굴'을 요청
    서버는 이 요청을 받아 [S->C] 'FACE_NORMAL' 이벤트를 로봇에게 전송
    """
    logger.info(f"FaceEvent log: Request for FACE_NORMAL from {sid} for robot {robot_clnt_id}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    
    # 헬퍼 함수를 사용해 로봇의 세션 정보 조회
    robot_session_info = await _get_head_session_info(
        sess_man, robot_clnt_type, robot_clnt_id
    )

    if robot_session_info:
        logger.info(f"Emitting FACE_NORMAL to robot {robot_clnt_id} at sid {robot_session_info.sid}")
        await sio.emit(
            FaceEvent.FACE_NORMAL,
            to=robot_session_info.sid,
            # data=... (데이터가 필요하면 여기에 추가)
        )
    else:
        logger.warning(f"FaceEvent log: Robot {robot_clnt_id} session not found.")


@sio.on(FaceRequestEvent.REQUEST_FACE_TALKING)
async def on_request_face_talking(sid, robot_clnt_type: SessionType, robot_clnt_id: int):
    """
    [C->S] 클라이언트(FE)가 서버에 '말하는 얼굴'을 요청
    서버는 이 요청을 받아 [S->C] 'FACE_TALKING' 이벤트를 로봇에게 전송
    """
    logger.info(f"FaceEvent log: Request for FACE_TALKING from {sid} for robot {robot_clnt_id}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    
    robot_session_info = await _get_head_session_info(
        sess_man, robot_clnt_type, robot_clnt_id
    )

    if robot_session_info:
        logger.info(f"Emitting FACE_TALKING to robot {robot_clnt_id} at sid {robot_session_info.sid}")
        await sio.emit(
            FaceEvent.FACE_TALKING,
            to=robot_session_info.sid,
        )
    else:
        logger.warning(f"FaceEvent log: Robot {robot_clnt_id} session not found.")


@sio.on(FaceRequestEvent.REQUEST_FACE_HEART)
async def on_request_face_heart(sid, robot_clnt_type: SessionType, robot_clnt_id: int):
    """
    [C->S] 클라이언트(FE)가 서버에 '하트눈 얼굴'을 요청
    서버는 이 요청을 받아 [S->C] 'FACE_HEART' 이벤트를 로봇에게 전송
    """
    logger.info(f"FaceEvent log: Request for FACE_HEART from {sid} for robot {robot_clnt_id}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    
    robot_session_info = await _get_head_session_info(
        sess_man, robot_clnt_type, robot_clnt_id
    )

    if robot_session_info:
        logger.info(f"Emitting FACE_HEART to robot {robot_clnt_id} at sid {robot_session_info.sid}")
        await sio.emit(
            FaceEvent.FACE_HEART,
            to=robot_session_info.sid,
        )
    else:
        logger.warning(f"FaceEvent log: Robot {robot_clnt_id} session not found.")


@sio.on(FaceRequestEvent.REQUEST_FACE_SAD)
async def on_request_face_sad(sid, robot_clnt_type: SessionType, robot_clnt_id: int):
    """
    [C->S] 클라이언트(FE)가 서버에 '슬픈 얼굴'을 요청
    서버는 이 요청을 받아 [S->C] 'FACE_SAD' 이벤트를 로봇에게 전송
    """
    logger.info(f"FaceEvent log: Request for FACE_SAD from {sid} for robot {robot_clnt_id}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    
    robot_session_info = await _get_head_session_info(
        sess_man, robot_clnt_type, robot_clnt_id
    )

    if robot_session_info:
        logger.info(f"Emitting FACE_SAD to robot {robot_clnt_id} at sid {robot_session_info.sid}")
        await sio.emit(
            FaceEvent.FACE_SAD,
            to=robot_session_info.sid,
        )
    else:
        logger.warning(f"FaceEvent log: Robot {robot_clnt_id} session not found.")