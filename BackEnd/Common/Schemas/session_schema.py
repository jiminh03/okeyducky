import json
from typing import Optional, Dict, Any
from enum import Enum


# SessionType을 Enum으로 정의합니다.
class SessionType(Enum):
    """세션 타입을 나타내는 열거형"""

    FE = "fe"  # 프론트엔드 (Frontend) 세션
    ROBOT = "robot"  # 로봇 (Robot) 세션


class ConnectionInfo:
    """
    세션 연결 정보를 캡슐화하는 클래스입니다.
    Socket.IO 세션(sid)을 기준으로 어떤 사용자/로봇이 연결되었는지 관리합니다.
    """

    def __init__(
        self,
        sid: str,
        session_type: SessionType,
        parent_id: Optional[int] = None,
        robot_id: Optional[int] = None,
    ):
        """
        ConnectionInfo 객체를 초기화합니다.

        Args:
            sid (str): 고유 세션 ID (예: Socket.IO의 `request.sid`).
            session_type (SessionType): 세션의 타입 (FE 또는 ROBOT).
            parent_id (Optional[int]): 세션에 연결된 부모(사용자/관리자) 계정의 ID.
            robot_id (Optional[int]): 세션에 연결된 로봇의 ID.
        """
        # 타입 힌트(SessionType)가 enum 값의 유효성을 검사합니다.
        self.sid = sid
        self.session_type = session_type
        self.parent_id = parent_id
        self.robot_id = robot_id

    def to_dict(self) -> Dict[str, Any]:
        """
        ConnectionInfo 객체를 직렬화 가능한 딕셔너리로 변환합니다.

        Returns:
            Dict[str, Any]: 객체의 속성을 담은 딕셔너리.
        """
        data: Dict[str, Any] = {
            "sid": self.sid,
            # JSON/Redis 등에 저장하기 위해 enum 멤버의 실제 값(예: "fe", "robot")을 사용합니다.
            "session_type": self.session_type.value,
        }
        # 값이 None이 아닌 선택적 필드(parent_id, robot_id)만 딕셔너리에 추가합니다.
        if self.parent_id is not None:
            data["parent_id"] = self.parent_id
        if self.robot_id is not None:
            data["robot_id"] = self.robot_id
        return data

    def to_json(self) -> str:
        """
        ConnectionInfo 객체를 JSON 문자열로 변환합니다.

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
            # 문자열 값(예: "fe", "robot")을 다시 SessionType enum 멤버로 변환합니다.
            session_type=SessionType(data["session_type"]),
            parent_id=data.get("parent_id"),  # 키가 존재하지 않으면 None을 반환
            robot_id=data.get("robot_id"),  # 키가 존재하지 않으면 None을 반환
        )
