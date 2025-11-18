from enum import Enum


class ConnectEvents(str, Enum):
    """소켓 통신에서 사용되는 이벤트 이름 목록"""

    # 서버 -> 클라이언트
    AUTH_SUCCESS = "auth_success"
    AuTH_FAILURE = "auth_failure"

    # 클라이언트 -> 서버
    CONNECT = "connect"
    DISCONNECT = "disconnect"


class WebRTCEvents(str, Enum):
    """
    WebRTC 시그널링 (대칭적 방 입장) 이벤트 목록
    """

    # --- 1. 송출 요청 및 요청 알림 ---
    # 이미 송출자, 수신자 모두 접속되어있다고 가정

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


class FaceEvent(str, Enum):
    """
    서버가 프론트엔드(로봇 얼굴)로 보내는 얼굴 표정 변경 이벤트
    """

    # [S->C] 평소 얼굴
    FACE_NORMAL = "server:face_normal"
    # [S->C] 하트눈 얼굴
    FACE_HEART = "server:face_heart"
    # [S->C] 슬픈 얼굴
    FACE_SAD = "server:face_sad"
    # [S->C] 말하는 얼굴
    FACE_SPEAKING = "server:face_speaking"
    # [S->C] 말하지 않는 얼굴
    FACE_NOT_SPEAKING = "server:face_not_speaking"

class FaceRequestEvent(str, Enum):
    """
    클라이언트(로봇)가 서버에게 얼굴 표정 변경을 요청하는 이벤트
    """

    # [C->S] 평소 얼굴 요청
    REQUEST_FACE_NORMAL = "client:request_face_normal"
    # [C->S] 하트눈 얼굴 요청
    REQUEST_FACE_HEART = "client:request_face_heart"
    # [C->S] 슬픈 얼굴 요청
    REQUEST_FACE_SAD = "client:request_face_sad"
    # [C->S] 말하는 얼굴 요청
    REQUEST_FACE_SPEAKING = "server:face_speaking"
    # [C->S] 말하지 않는 얼굴 요청
    REQUEST_FACE_NOT_SPEAKING = "server:face_not_speaking"

# --- [신규] TTS 오디오 스트리밍 이벤트 ---

class TTSEvents(str, Enum):
    """
    AI 서버와 백엔드 서버 간의 내부 통신 이벤트 (Internal)
    """
    
    # [AI_SVC -> BE]
    # AI 서버가 BE 서버로 PCM 오디오 청크를 전송합니다.
    # Data: {"child_id": str, "chunk": bytes}
    AI_TO_BE_AUDIO_CHUNK = "ai:audio_chunk"

    # [AI_SVC -> BE]
    # AI 서버가 BE 서버로 스트림 시작을 알립니다. (PCM 포맷 정보 포함)
    # Data: {"child_id": str, "format_info": {...}}
    AI_TO_BE_STREAM_START = "ai:stream_start"

    # [AI_SVC -> BE]
    # AI 서버가 BE 서버로 스트림 종료를 알립니다.
    # Data: {"child_id": str}
    AI_TO_BE_STREAM_END = "ai:stream_end"
    

class RobotTTSEvents(str, Enum):
    """
    백엔드 서버(BE)와 로봇(Client) 간의 외부 통신 이벤트 (External)
    """
    
    # [BE -> Robot]
    # BE 서버가 로봇으로 PCM 오디오 청크를 전송합니다.
    # Data: b"..." (raw bytes)
    AUDIO_CHUNK = "server:audio_chunk"

    # [BE -> Robot]
    # BE 서버가 로봇에게 스트림 시작을 알립니다.
    # Data: {"format_info": {...}}
    STREAM_START = "server:stream_start"

    # [BE -> Robot]
    # BE 서버가 로봇에게 스트림 종료를 알립니다.
    # Data: {}
    STREAM_END = "server:stream_end"