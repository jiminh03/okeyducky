import json
from typing import Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel


# SessionType을 Enum으로 정의합니다.
class SessionType(str, Enum):
    """세션 타입을 나타내는 열거형"""

    PARENT = "parent"  # 부모 (Parent) 세션션
    ROBOT = "robot"  # 로봇 (Robot) 세션
    AI_SERV = "ai_serv"  # AI 서버
    ROBOT_HEAD = "robot_head"  # 로봇 머리


class ConnectionInfo:
    """
    세션 연결 정보를 캡슐화하는 클래스입니다.
    Socket.IO 세션(sid)을 기준으로 어떤 사용자/로봇이 연결되었는지 관리합니다.
    """

    def __init__(
        self,
        sid: str,
        session_type: SessionType,
        id: int,  # <--- 변경된 부분 (parent_id, robot_id 대신 id 사용)
    ):
        """
        ConnectionInfo 객체를 초기화합니다.

        Args:
            sid (str): 고유 세션 ID (예: Socket.IO의 `request.sid`).
            session_type (SessionType): 세션의 타입 (FE 또는 ROBOT).
            id (int): 세션에 연결된 부모(사용자) 또는 로봇의 ID. # <--- 수정된 주석
        """
        # 타입 힌트(SessionType)가 enum 값의 유효성을 검사합니다.
        self.sid = sid
        self.session_type = session_type
        self.id = id  # <--- 추가된 부분

    def to_dict(self) -> Dict[str, Any]:
        """
        ConnectionInfo 객체를 직렬화 가능한 딕셔너리로 변환합니다.

        Returns:
            Dict[str, Any]: 객체의 속성을 담은 딕셔너리.
        """
        data: Dict[str, Any] = {
            "sid": self.sid,
            # JSON/Redis 등에 저장하기 위해 enum 멤버의 실제 값(예: "parent", "robot")을 사용합니다.
            "session_type": self.session_type.value,
            "id": self.id,  # <--- 수정된 부분 (id 필드 추가)
        }
        
        # <--- 삭제된 부분 (parent_id, robot_id 관련 if 블록)
        
        return data

    def to_json(self) -> str:
        """
        ConnectionInfo 객체를 JSON 문자열로 변환합니다.
        (이 메서드는 to_dict()를 사용하므로 수정할 필요가 없습니다.)

        Returns:
            str: 객체의 JSON 문자열 표현.
        """
        # to_dict() 메서드를 재사용하여 일관된 출력을 보장합니다.
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionInfo":
        """
        딕셔너리로부터 ConnectionInfo 객체를 생성(역직렬화)합니다.

        Args:
            data (Dict[str, Any]): 객체 생성을 위한 데이터 딕셔너리.

        Returns:
            ConnectionInfo: 생성된 ConnectionInfo 객체.
        """
        return cls(
            sid=data["sid"],
            # 문자열 값(예: "parent", "robot")을 다시 SessionType enum 멤버로 변환합니다.
            session_type=SessionType(data["session_type"]),
            id=data["id"],  # <--- 수정된 부분 (data["id"] 사용)
            # parent_id=data.get("parent_id"),  <--- 삭제됨
            # robot_id=data.get("robot_id"),  <--- 삭제됨
        )

class SessionRequest(BaseModel):
    """세션 생성 요청 모델"""

    session_type: SessionType
    token: str