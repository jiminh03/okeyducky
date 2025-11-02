from enum import Enum

class ConnectEvents(str, Enum):
    """소켓 통신에서 사용되는 이벤트 이름 목록"""
    
    # 서버 -> 클라이언트
    AUTH_SUCCESS = 'auth_success'
    AuTH_FAILURE = 'auth_failure'
    
    # 클라이언트 -> 서버
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'