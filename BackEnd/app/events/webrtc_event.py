from typing import Dict

from common.schemas.session_schema import SessionType
from common.modules.session_manager import SessionManager
from common.modules.webrtc_manager import WebRTCManager
from common.schemas.socket_event_schema import WebRTCEvents

from common.modules.db_instance import red

from app.modules.websocket_module import sio





# WebRTC 시그널링 이벤트 핸들러 ---
# 사용 규칙
# 1. 반드시 상대방의 세션 타입과 id를 알고 있어야함

@sio.on(WebRTCEvents.REGISTER_OFFER)
async def on_register_offer(sid, offer_data: Dict[str, str]):
    """(로봇 -> 서버) 로봇이 Offer를 등록하는 이벤트"""
    print(f"WebRTC log: Registering Offer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    sess_man = SessionManager(redis_client)
    await rtc_man.register_offer(sid, offer_data)


@sio.on(WebRTCEvents.CHECK_OFFER)
async def on_check_offer(sid, offer_clnt_type: SessionType, offer_clnt_id: int):
    """(서버 -> FE) 이미 등록된 offer 확인하는 이벤트"""
    print(f"WebRTC log: Checking Offer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    sess_man = SessionManager(redis_client)
    if offer_clnt_type == SessionType.PARENT:
        session_info = await sess_man.get_session_by_parent_id(offer_clnt_id)
    elif offer_clnt_type == SessionType.ROBOT:
        session_info = await sess_man.get_session_by_robot_id(offer_clnt_id)

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

    if offer_clnt_type == SessionType.PARENT:
        session_info = await sess_man.get_session_by_parent_id(offer_clnt_id)
    elif offer_clnt_type == SessionType.ROBOT:
        session_info = await sess_man.get_session_by_robot_id(offer_clnt_id)
    recv_sid = session_info.sid

    if recv_sid:
        print(f"WebRTC log: Consume Answer ,sid: {recv_sid}")
        answer = await rtc_man.consume_answer(sid)
        await sio.emit(WebRTCEvents.NEW_ANSWER, answer, to=recv_sid)
    else:
        print("recv_sid not exist")


@sio.on(WebRTCEvents.CHECK_ANSWER)
async def on_check_answer(sid, answer_clnt_type: SessionType, answer_clnt_id: int):
    """(서버 -> FE) 이미 등록된 offer 확인하는 이벤트"""
    print(f"WebRTC log: Checking Answer ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    sess_man = SessionManager(redis_client)

    if answer_clnt_type == SessionType.PARENT:
        session_info = await sess_man.get_session_by_parent_id(answer_clnt_id)
    elif answer_clnt_type == SessionType.ROBOT:
        session_info = await sess_man.get_session_by_robot_id(answer_clnt_id)

    answer = await rtc_man.consume_answer(session_info.sid)
    if answer:
        await sio.emit(WebRTCEvents.NEW_ANSWER, answer, to=sid)


@sio.on(WebRTCEvents.SEND_ICE_CANDIDATE)
async def on_send_ice_candidate(sid, opp_clnt_type: SessionType, opp_clnt_id: int ,data):
    """(로봇/FE -> 서버) ICE Candidate를 중계하는 이벤트"""
    print(f"WebRTC log: ice exchange ,sid: {sid}")
    redis_client = await red.get_redis_client()
    rtc_man = WebRTCManager(redis_client)
    sess_man = SessionManager(redis_client)
    
    if data:
        if opp_clnt_type == SessionType.PARENT:
            session_info = await sess_man.get_session_by_parent_id(opp_clnt_id)
        elif opp_clnt_type == SessionType.ROBOT:
            session_info = await sess_man.get_session_by_robot_id(opp_clnt_id)
        recv_sid = session_info.sid

        if recv_sid:
            # 상대방에게 'server:new_ice_candidate' 이벤트를 보냅니다.
            print(f"[ICE 전송] ,sid: {sid} -> {recv_sid} ICE Candidate 수신")
            await sio.emit(WebRTCEvents.NEW_ICE_CANDIDATE, data, to=recv_sid)
    else:
        print("data not exist")