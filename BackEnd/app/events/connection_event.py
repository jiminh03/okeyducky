from typing import Dict, Union

from fastapi import Depends

from app.modules.websocket_module import sio
from app.modules.crypt_module import InvalidCredentialsError, crypt_module


from common.modules.session_manager import SessionManager
from common.schemas.socket_event_schema import ConnectEvents
from common.schemas.session_schema import ConnectionInfo, SessionRequest




@sio.on(ConnectEvents.CONNECT)
async def connect(sid, environ, auth: Dict[str, str], session_manager: SessionManager = Depends(SessionManager)):
    print(f"✅ [연결 시도] 클라이언트 접속. sid: {sid}")

    if not auth:
        print(f"[인증 실패] 인증 정보가 없습니다. sid: {sid}")
        await sio.disconnect(sid)
        return

    session_request = SessionRequest.model_validate(auth)
    
    try:
        token_payload = crypt_module.decode_jwt_payload(session_request.token)
    except InvalidCredentialsError:
        print(f"[인증 실패] 토큰 디코딩 실패. sid: {sid}, token: {session_request.token}")
        await sio.disconnect(sid)
        return
    
    con_info = ConnectionInfo(
                sid=sid,
                session_type=session_request.session_type,
                parent_id=token_payload.parent_id,
            )
    await session_manager.create_session(con_info)
    await sio.emit(ConnectEvents.AUTH_SUCCESS, to=sid)
    print(f"🔑 [인증 성공] 클라이언트 인증 완료. sid: {sid}, session_type: {session_request.session_type}, parent_id: {token_payload.parent_id}")
    
    #TODO: 추후 일정 시간 인증이 안되면 연결을 끊는 기능이 필요

@sio.on(ConnectEvents.DISCONNECT)
async def disconnect(sid, session_manager: SessionManager = Depends(SessionManager)):
    """연결 종료 시 Redis에서 매핑 정보를 삭제합니다."""
    await session_manager.delete_session(sid)
    print(f"👋 [연결 종료] 클라이언트 연결 끊김. sid: {sid}")

