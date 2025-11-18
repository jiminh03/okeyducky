from loguru import logger

import socketio

from common.schemas.socket_event_schema import ConnectEvents

# 1. 단 하나의 'sio_ai' 인스턴스를 생성합니다.
sio_ai = socketio.AsyncClient(logger=False, engineio_logger=False)


@sio_ai.event
async def connect():
    """
    BE 서버에 연결 성공 시 호출됩니다.
    """
    logger.info(f"✅ [AI_SVC] BE 서버에 성공적으로 연결되었습니다. (SID: {sio_ai.sid})")


@sio_ai.on(ConnectEvents.AUTH_SUCCESS)
async def auth_success():
    """
    BE 서버로부터 인증 성공 이벤트를 수신했을 때 호출됩니다.
    """
    logger.info(f"🔑 [AI_SVC] BE 서버로부터 인증에 성공했습니다.")


@sio_ai.event
async def disconnect():
    """
    BE 서버와 연결이 끊어졌을 때 호출됩니다.
    """
    logger.info(f"🔌 [AI_SVC] BE 서버와 연결이 끊어졌습니다.")
