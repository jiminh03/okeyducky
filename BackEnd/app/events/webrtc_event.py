from typing import Dict, Optional

# SessionInfo를 세션 객체의 실제 타입으로 가정하고 추가했습니다. 
# 만약 타입이 다르다면 실제 타입으로 변경해주세요.
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
        print(f"{client_type} client type not exist")
    
    return session_info


# WebRTC 시그널링 이벤트 핸들러 ---
# 사용 규칙
# 1. 반드시 상대방의 세션 타입과 id를 알고 있어야함

@sio.on(WebRTCEvents.REGISTER_OFFER)
async def on_register_offer(sid, offer_data: Dict[str, str]):
    """(로봇 -> 서버) 로봇이 Offer를 등록하는 이벤트"""
    print(f"WebRTC log: Registering Offer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    # 원본 코드와 동일하게 유지 (sess_man이 사용되진 않음)
    sess_man = SessionManager(redis_client) 
    await rtc_man.register_offer(sid, offer_data)


@sio.on(WebRTCEvents.CHECK_OFFER)
async def on_check_offer(sid, offer_clnt_type: SessionType, offer_clnt_id: int):
    """(서버 -> FE) 이미 등록된 offer 확인하는 이벤트"""
    print(f"WebRTC log: Checking Offer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    sess_man = SessionManager(redis_client)
    
    # 헬퍼 함수 사용
    session_info = await _get_session_info(sess_man, offer_clnt_type, offer_clnt_id)
    
    if session_info is None:
        print(f"{offer_clnt_type} {offer_clnt_id} session_info not exist")
        return

    offer = await rtc_man.consume_offer(session_info.sid)
    if offer:
        await sio.emit(WebRTCEvents.NEW_OFFER, offer, to=sid)


@sio.on(WebRTCEvents.SEND_ANSWER)
async def on_send_answer(sid, offer_clnt_type: SessionType, offer_clnt_id: int, answer_data: Dict[str, str]):
    """(FE -> 서버) FE가 Answer를 제출하는 이벤트"""
    print(f"WebRTC log: Sending Answer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    sess_man = SessionManager(redis_client)

    await rtc_man.register_answer(sid, answer_data)

    # 헬퍼 함수 사용
    session_info = await _get_session_info(sess_man, offer_clnt_type, offer_clnt_id)

    # session_info가 None인지 확인하여 오류 방지
    if session_info:
        recv_sid = session_info.sid
        print(f"WebRTC log: Consume Answer ,sid: {recv_sid}")
        answer = await rtc_man.consume_answer(sid)
        await sio.emit(WebRTCEvents.NEW_ANSWER, answer, to=recv_sid)
    else:
        print(f"{offer_clnt_type} {offer_clnt_id} session_info not exist")


@sio.on(WebRTCEvents.CHECK_ANSWER)
async def on_check_answer(sid, answer_clnt_type: SessionType, answer_clnt_id: int):
    """(서버 -> FE) 이미 등록된 offer 확인하는 이벤트"""
    print(f"WebRTC log: Checking Answer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    sess_man = SessionManager(redis_client)

    # 헬퍼 함수 사용
    session_info = await _get_session_info(sess_man, answer_clnt_type, answer_clnt_id)

    # session_info가 None인지 확인하여 오류 방지
    if session_info:
        answer = await rtc_man.consume_answer(session_info.sid)
        if answer:
            await sio.emit(WebRTCEvents.NEW_ANSWER, answer, to=sid)
    else:
        print(f"{answer_clnt_type} {answer_clnt_id} session_info not exist")


@sio.on(WebRTCEvents.SEND_ICE_CANDIDATE)
async def on_send_ice_candidate(sid, opp_clnt_type: SessionType, opp_clnt_id: int ,data):
    """(로봇/FE -> 서버) ICE Candidate를 중계하는 이벤트"""
    print(f"WebRTC log: ice exchange ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    sess_man = SessionManager(redis_client)
    
    if data:
        # 헬퍼 함수 사용
        session_info = await _get_session_info(sess_man, opp_clnt_type, opp_clnt_id)

        # session_info가 None인지 확인하여 오류 방지
        if session_info:
            recv_sid = session_info.sid
            # 상대방에게 'server:new_ice_candidate' 이벤트를 보냅니다.
            print(f"[ICE 전송] ,sid: {sid} -> {recv_sid} ICE Candidate 수신")
            await sio.emit(WebRTCEvents.NEW_ICE_CANDIDATE, data, to=recv_sid)
        else:
            print(f"{opp_clnt_type} {opp_clnt_id} session_info not exist")
    else:
        print("data not exist")