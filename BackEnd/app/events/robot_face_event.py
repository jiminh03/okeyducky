from enum import Enum
from typing import Optional

from loguru import logger

from common.schemas.session_schema import ConnectionInfo, SessionType
from common.schemas.socket_event_schema import FaceEvent, FaceRequestEvent
from common.modules.session_manager import SessionManager
from common.modules.db_instance import red
from app.modules.websocket_module import sio


# --- 헬퍼 함수 ---
async def _get_head_session_info(
    sess_man: SessionManager, child_id: int
) -> Optional[ConnectionInfo]:
    """클라이언트 타입과 ID를 기반으로 세션 정보를 가져오는 헬퍼 함수"""
    # TODO: 어린이 아이디로 머리 아이디(부모 아이디로 사용중)조회하는 기능 필요
    session_info = await sess_man.get_session_by_robot_head_id(1)
    return session_info


# --- 로봇 얼굴 표정 이벤트 핸들러 ---


@sio.on(FaceRequestEvent.REQUEST_FACE_NORMAL)
async def on_request_face_normal(sid, data: dict):
    """
    [C->S] 클라이언트(FE)가 서버에 '평소 얼굴'을 요청
    """
    child_id = data.get("child_id")
    logger.info(
        f"FaceEvent log: Request for FACE_NORMAL from {sid}, child_id: {child_id}"
    )

    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)

    robot_session_info = await _get_head_session_info(sess_man, child_id)

    if robot_session_info:
        logger.info(
            f"Emitting FACE_NORMAL to robot {child_id} at sid {robot_session_info.sid}"
        )
        await sio.emit(
            FaceEvent.FACE_NORMAL,
            to=robot_session_info.sid,
        )
    else:
        logger.warning(f"FaceEvent log: Robot {child_id} session not found.")


@sio.on(FaceRequestEvent.REQUEST_FACE_HEART)
async def on_request_face_heart(sid, data: dict):
    """
    [C->S] 클라이언트(FE)가 서버에 '하트눈 얼굴'을 요청
    """
    child_id = data.get("child_id")
    logger.info(
        f"FaceEvent log: Request for FACE_HEART from {sid} for robot {child_id}"
    )

    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)

    robot_session_info = await _get_head_session_info(sess_man, child_id)

    if robot_session_info:
        logger.info(
            f"Emitting FACE_HEART to robot {child_id} at sid {robot_session_info.sid}"
        )
        await sio.emit(
            FaceEvent.FACE_HEART,
            to=robot_session_info.sid,
        )
    else:
        logger.warning(f"FaceEvent log: Robot {child_id} session not found.")


@sio.on(FaceRequestEvent.REQUEST_FACE_SAD)
async def on_request_face_sad(sid, data: dict):
    """
    [C->S] 클라이언트(FE)가 서버에 '슬픈 얼굴'을 요청
    """
    child_id = data.get("child_id")
    logger.info(f"FaceEvent log: Request for FACE_SAD from {sid} for robot {child_id}")

    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)

    robot_session_info = await _get_head_session_info(sess_man, child_id)

    if robot_session_info:
        logger.info(
            f"Emitting FACE_SAD to robot {child_id} at sid {robot_session_info.sid}"
        )
        await sio.emit(
            FaceEvent.FACE_SAD,
            to=robot_session_info.sid,
        )
    else:
        logger.warning(f"FaceEvent log: Robot {child_id} session not found.")


@sio.on(FaceRequestEvent.REQUEST_FACE_SPEAKING)
async def on_request_face_speaking(sid, data: dict):
    """
    [C->S] 클라이언트(FE)가 서버에 '말하는 얼굴'을 요청
    """
    child_id = data.get("child_id")
    logger.info(
        f"FaceEvent log: Request for FACE_SPEAKING from {sid} for robot {child_id}"
    )

    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)

    robot_session_info = await _get_head_session_info(sess_man, child_id)

    if robot_session_info:
        logger.info(
            f"Emitting FACE_SPEAKING to robot {child_id} at sid {robot_session_info.sid}"
        )
        await sio.emit(
            FaceEvent.FACE_SPEAKING,
            to=robot_session_info.sid,
        )
    else:
        logger.warning(f"FaceEvent log: Robot {child_id} session not found.")


@sio.on(FaceRequestEvent.REQUEST_FACE_NOT_SPEAKING)
async def on_request_face_not_speaking(sid, data: dict):
    """
    [C->S] 클라이언트(FE)가 서버에 '말하지 않는 얼굴(입 다뭄)'을 요청
    """
    child_id = data.get("child_id")
    logger.info(
        f"FaceEvent log: Request for FACE_NOT_SPEAKING from {sid} for robot {child_id}"
    )

    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)

    robot_session_info = await _get_head_session_info(sess_man, child_id)

    if robot_session_info:
        logger.info(
            f"Emitting FACE_NOT_SPEAKING to robot {child_id} at sid {robot_session_info.sid}"
        )
        await sio.emit(
            FaceEvent.FACE_NOT_SPEAKING,
            to=robot_session_info.sid,
        )
    else:
        logger.warning(f"FaceEvent log: Robot {child_id} session not found.")
