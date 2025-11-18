from loguru import logger

from typing import Dict

from app.modules.websocket_module import sio
from app.modules.crypt_module import InvalidCredentialsError, crypt_module


from common.modules.session_manager import SessionManager
from common.modules.db_instance import red
from common.schemas.socket_event_schema import ConnectEvents
from common.schemas.session_schema import ConnectionInfo, SessionRequest, SessionType
from common.schemas.user_schema import RobotTokenPayload, TokenPayload


@sio.on(ConnectEvents.CONNECT)
async def connect(sid, environ, auth: Dict[str, str]):
    logger.info(f"✅ [연결 시도] 클라이언트 접속. sid: {sid}")
    logger.info(f"--- auth data: {auth} ---")

    if auth.get("session_type") == SessionType.AI_SERV.value:
        logger.info(f"🤖 [AI 서버] 연결 확인됨. 인증을 생략합니다. sid: {sid}")
        await sio.emit(ConnectEvents.AUTH_SUCCESS, to=sid)
        return  # <-- 이제 이 return이 정상적으로 실행됩니다.

    redis_client = await red.get_redis_client()
    session_manager = SessionManager(redis_client=redis_client)

    if not auth:
        logger.info(f"[인증 실패] 인증 정보가 없습니다. sid: {sid}")
        await sio.disconnect(sid)
        return

    session_request = SessionRequest.model_validate(auth)

    clnt_id = None
    try:
        token_payload = crypt_module.decode_jwt_payload(session_request.token)
        if session_request.session_type == SessionType.PARENT or session_request.session_type == SessionType.ROBOT_HEAD:
            clnt_id = TokenPayload.model_validate(token_payload).parent_id
        elif session_request.session_type == SessionType.ROBOT:
            clnt_id = RobotTokenPayload.model_validate(token_payload).robot_id
    except InvalidCredentialsError:
        logger.info(
            f"[인증 실패] 토큰 디코딩 실패. sid: {sid}, token: {session_request.token}"
        )
        await sio.disconnect(sid)
        return

    con_info = ConnectionInfo(
        sid=sid,
        session_type=session_request.session_type,
        id=clnt_id,
    )

    if not con_info:
        logger.info(f"[세션 생성 실패] 요청 정보: {session_request}")

    await session_manager.create_session(con_info)
    await sio.emit(ConnectEvents.AUTH_SUCCESS, to=sid)
    logger.info(
        f"🔑 [인증 성공] 클라이언트 인증 완료. sid: {sid}, session_type: {session_request.session_type}, id: {clnt_id}"
    )

    # TODO: 추후 일정 시간 인증이 안되면 연결을 끊는 기능이 필요


@sio.on(ConnectEvents.DISCONNECT)
async def disconnect(sid):
    """연결 종료 시 Redis에서 매핑 정보를 삭제합니다."""
    redis_client = await red.get_redis_client()
    session_manager = SessionManager(redis_client=redis_client)
    session_info = await session_manager.get_session_by_sid(sid)
    if session_info:
        logger.info(
            f"👋 [연결 종료] 클라이언트 연결 끊김. sid: {sid}, session_type: {session_info.session_type}, id: {session_info.id}"
        )
        await session_manager.delete_session(session_info)
    logger.info(f"👋 [연결 종료] 클라이언트 연결 끊김. sid: {sid}")
