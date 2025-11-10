from enum import Enum


class ConnectEvents(str, Enum):
    """소켓 통신에서 사용되는 이벤트 이름 목록"""

    # 서버 -> 클라이언트
    AUTH_SUCCESS = "auth_success"
    AuTH_FAILURE = "auth_failure"

    # 클라이언트 -> 서버
    CONNECT = "connect"
    DISCONNECT = "disconnect"


from enum import Enum


class WebRTCEvents(str, Enum):
    """
    WebRTC 시그널링 (대칭적 방 입장) 이벤트 목록
    """

    # --- 1. 송출 요청 및 요청 알림 ---
    #이미 송출자, 수신자 모두 접속되어있다고 가정

    REQUEST_CAST = "client:request_cast"
    ACCPET_REQUEST = "client:accept_request"
    REJECT_REQUEST = "client:reject_request"

    CAST_REQUESTED = "server:cast_requested"
    CAST_ACCEPTED = "server:cast_accepted"
    CAST_REJECTED = "server:cast_rejected"

    READY_FOR_OFFER = "client:ready_for_offer"
    PEER_IS_READY = "server:peer_is_ready"

    # --- 2. SDP 교환 (Offer/Answer) ---
    SEND_OFFER = "client:send_offer"
    SEND_ANSWER = "client:send_answer"

    NEW_OFFER = "server:new_offer"
    NEW_ANSWER = "server:new_answer"

    # --- 3. ICE Candidate 교환 ---
    SEND_ICE_CANDIDATE = "client:send_ice_candidate"
    NEW_ICE_CANDIDATE = "server:new_ice_candidate"
