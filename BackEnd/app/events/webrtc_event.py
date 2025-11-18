from typing import Dict, Optional

from common.schemas.session_schema import ConnectionInfo, SessionType 
from common.modules.session_manager import SessionManager
from common.modules.webrtc_manager import WebRTCManager
from common.schemas.socket_event_schema import WebRTCEvents

from common.modules.db_instance import red

from app.modules.websocket_module import sio


# --- 헬퍼 함수 ---
async def _get_session_info(
    sess_man: SessionManager, 
    client_type: SessionType, 
    client_id: int
) -> Optional[ConnectionInfo]: # 실제 세션 정보 객체 타입(SessionInfo)으로 가정
    """클라이언트 타입과 ID를 기반으로 세션 정보를 가져오는 헬퍼 함수"""
    session_info = None
    if client_type == SessionType.PARENT.value:
        session_info = await sess_man.get_session_by_parent_id(client_id)
    elif client_type == SessionType.ROBOT.value:
        session_info = await sess_man.get_session_by_robot_id(client_id)
    else:
        logger.info(f"{client_type} client type not exist")

    return session_info


# WebRTC 요청 및 요청 알림 이벤트
@sio.on(WebRTCEvents.REQUEST_CAST)
async def on_request_cast(sid, opp_clnt_type: SessionType, opp_clnt_id: int):
    logger.info(f"WebRTC log: Requesting Cast ,sid: {sid}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    requested_session_info = await _get_session_info(
        sess_man, opp_clnt_type, opp_clnt_id
    )
    await sio.emit(
        WebRTCEvents.CAST_REQUESTED,
        to=requested_session_info.sid,
        data={"opp_type": opp_clnt_type, "opp_id": opp_clnt_id},
    )


@sio.on(WebRTCEvents.ACCPET_REQUEST)
async def on_request_cast(sid, opp_clnt_type: SessionType, opp_clnt_id: int):
    logger.info(f"WebRTC log: Cast Accepted ,sid: {sid}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client) 
    requested_session_info = await _get_session_info(sess_man, opp_clnt_type, opp_clnt_id)
    await sio.emit(
        WebRTCEvents.CAST_ACCEPTED,
        to=requested_session_info.sid,
        data={"opp_type": opp_clnt_type, "opp_id": opp_clnt_id},
    )

# TODO: 캐스트 거절 이벤트는 mvp 제외

@sio.on(WebRTCEvents.READY_FOR_OFFER)
async def on_ready_for_offer(sid, opp_clnt_type: SessionType, opp_clnt_id: int):
    logger.info(f"WebRTC log: Ready for Offer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client) 
    requested_session_info = await _get_session_info(sess_man, opp_clnt_type, opp_clnt_id)
    await sio.emit(
        WebRTCEvents.PEER_IS_READY,
        to=requested_session_info.sid,
        data={"opp_type": opp_clnt_type, "opp_id": opp_clnt_id},
    )


# WebRTC 시그널링 이벤트 핸들러 ---
# 사용 규칙
# 1. 반드시 상대방의 세션 타입과 id를 알고 있어야함

@sio.on(WebRTCEvents.SEND_OFFER)
async def on_send_offer(sid, offer_clnt_type: SessionType, offer_clnt_id: int, offer_data: Dict[str, str]):
    """(로봇 -> 서버) 로봇이 Offer를 등록하는 이벤트"""
    logger.info(f"WebRTC log: Sending Offer ,sid: {sid}")
    redis_client = await red.get_redis_client()

    sess_man = SessionManager(redis_client) 
    session_info= await _get_session_info(sess_man, offer_clnt_type, offer_clnt_id)

    await sio.emit(WebRTCEvents.NEW_OFFER, offer_data, to=session_info.sid)



@sio.on(WebRTCEvents.SEND_ANSWER)
async def on_send_answer(sid, offer_clnt_type: SessionType, offer_clnt_id: int, answer_data: Dict[str, str]):
    """(FE -> 서버) FE가 Answer를 제출하는 이벤트"""
    logger.info(f"WebRTC log: Sending Answer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client) 
    session_info= await _get_session_info(sess_man, offer_clnt_type, offer_clnt_id)

    
    await sio.emit(WebRTCEvents.NEW_ANSWER, answer_data, to=session_info.sid)

@sio.on(WebRTCEvents.SEND_ICE_CANDIDATE)
async def on_send_ice_candidate(sid, opp_clnt_type: SessionType, opp_clnt_id: int ,data):
    """(로봇/FE -> 서버) ICE Candidate를 중계하는 이벤트"""
    logger.info(f"WebRTC log: ice exchange ,sid: {sid}")
    redis_client = await red.get_redis_client()
    sess_man = SessionManager(redis_client)
    
    if data:
        # 헬퍼 함수 사용
        session_info = await _get_session_info(sess_man, opp_clnt_type, opp_clnt_id)

        # session_info가 None인지 확인하여 오류 방지
        if session_info:
            recv_sid = session_info.sid
            # 상대방에게 'server:new_ice_candidate' 이벤트를 보냅니다.
            logger.info(f"[ICE 전송] ,sid: {sid} -> {recv_sid} ICE Candidate 수신")
            await sio.emit(WebRTCEvents.NEW_ICE_CANDIDATE, data, to=recv_sid)
        else:
            logger.info(f"{opp_clnt_type} {opp_clnt_id} session_info not exist")
    else:
        logger.info("data not exist")
