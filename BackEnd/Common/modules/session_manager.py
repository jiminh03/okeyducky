import os

import json
from typing import Union, Optional, List
from enum import Enum
from fastapi import Depends
import redis.asyncio as redis  # 'redis.asyncio'를 직접 사용

# (가정) ConnectionInfo 모델이 있고, from_dict / to_json 메서드가 있다고 가정합니다.
# (가정) Redis 클라이언트를 주입하는 'get_redis_client' 의존성이 있다고 가정합니다.
from common.modules.db_instance import red  # (가정)
from common.schemas.session_schema import ConnectionInfo, SessionType  # (가정)


# 키 타입용 Enum (오타 방지)
class SessionKeyType(str, Enum):
    SID = "sid"
    ROBOT_ID = "robot_id"
    PARENT_ID = "parent_id"


class SessionManager:
    # 세션 만료 시간 (예: 24시간)
    SESSION_EXPIRE_SECONDS = os.getenv("SESSION_EXPIRE_SECONDS", 86400)

    def __init__(
        self,
        # Redis 클라이언트를 FastAPI를 통해 직접 주입받습니다.
        redis_client: redis.Redis,
    ):
        # 모든 메서드가 'self.redis_client'를 공유합니다.
        self.redis_client = redis_client

    def _get_key(self, key_type: SessionKeyType, value: Union[str, int]) -> str:
        return f"session:{key_type.value}:{value}"

    async def create_session(self, session_info: ConnectionInfo) -> None:
        """
        세션과 모든 인덱스를 Redis 파이프라인으로 생성하고 만료 시간을 설정합니다.
        """
        try:
            async with self.redis_client.pipeline() as pipe:
                sid_key = self._get_key(SessionKeyType.SID, session_info.sid)

                # 원본의 .to_json() 메서드 사용
                session_data_json = session_info.to_json()

                # 'set' 대신 'setex' (Set with Expiry) 사용
                pipe.setex(sid_key, self.SESSION_EXPIRE_SECONDS, session_data_json)
                print(f"[SETEX] {sid_key} (Expires: {self.SESSION_EXPIRE_SECONDS}s)")

                if session_info.session_type == SessionType.ROBOT:
                    robot_id_key = self._get_key(
                        SessionKeyType.ROBOT_ID, session_info.id
                    )
                    pipe.setex(
                        robot_id_key, self.SESSION_EXPIRE_SECONDS, session_info.sid
                    )
                    print(f"[SETEX-INDEX] {robot_id_key} -> {session_info.sid}")
                elif session_info.session_type == SessionType.PARENT:
                    parent_id_key = self._get_key(
                        SessionKeyType.PARENT_ID, session_info.id
                    )
                    pipe.setex(
                        parent_id_key, self.SESSION_EXPIRE_SECONDS, session_info.sid
                    )
                    print(f"[SETEX-INDEX] {parent_id_key} -> {session_info.sid}")                    

                await pipe.execute()
            print(f"--- 세션 생성이 완료되었습니다 (SID: {session_info.sid}) ---")
        except redis.RedisError as e:
            print(f"🚨 Redis 세션 생성 실패 (SID: {session_info.sid}): {e}")
            # (선택) 여기서 'DatabaseError' 같은 커스텀 예외를 raise 할 수 있습니다.

    async def get_session_by_sid(self, sid: str) -> Optional[ConnectionInfo]:
        """SID로 세션 정보(JSON)를 직접 조회합니다."""
        sid_key = self._get_key(SessionKeyType.SID, sid)
        try:
            session_data_json = await self.redis_client.get(sid_key)

            if session_data_json:
                print(f"(sid: {sid}) -> 세션을 찾았습니다.")
                # 원본의 .from_dict() 메서드 사용
                return ConnectionInfo.from_dict(json.loads(session_data_json))

            print(f"(sid: {sid}) -> 세션을 찾을 수 없습니다.")
            return None
        except redis.RedisError as e:
            print(f"🚨 Redis get_session_by_sid 실패 (SID: {sid}): {e}")
            return None

    async def get_session_by_robot_id(self, robot_id: int) -> Optional[ConnectionInfo]:
        """Robot ID 인덱스를 조회한 후, SID로 세션 정보를 조회합니다."""
        robot_id_key = self._get_key(SessionKeyType.ROBOT_ID, robot_id)
        try:
            sid = await self.redis_client.get(robot_id_key)

            if not sid:
                print(f"(robot_id: {robot_id}) -> 해당 인덱스를 찾을 수 없습니다.")
                return None

            print(
                f"(robot_id: {robot_id}) -> sid({sid})를 찾았습니다. 세부 정보를 조회합니다."
            )
            # 중복 로직을 피하기 위해 SID 키로 직접 조회합니다.
            sid_key = self._get_key(SessionKeyType.SID, sid)
            session_data_json = await self.redis_client.get(sid_key)

            if not session_data_json:
                print(
                    f"⚠️ 데이터 불일치! (robot_id: {robot_id}) -> (sid: {sid})를 찾았으나, 실제 세션 데이터가 없습니다."
                )
                return None

            return ConnectionInfo.from_dict(json.loads(session_data_json))

        except redis.RedisError as e:
            print(f"🚨 Redis get_session_by_robot_id 실패 (RobotID: {robot_id}): {e}")
            return None

    async def get_session_by_parent_id(
        self, parent_id: int
    ) -> Optional[ConnectionInfo]:
        """Parent ID 인덱스를 조회한 후, SID로 세션 정보를 조회합니다."""
        parent_id_key = self._get_key(SessionKeyType.PARENT_ID, parent_id)
        try:
            sid = await self.redis_client.get(parent_id_key)

            if not sid:
                print(f"(parent_id: {parent_id}) -> 해당 인덱스를 찾을 수 없습니다.")
                return None

            print(
                f"(parent_id: {parent_id}) -> sid({sid})를 찾았습니다. 세부 정보를 조회합니다."
            )
            sid_key = self._get_key(SessionKeyType.SID, sid)
            session_data_json = await self.redis_client.get(sid_key)

            if not session_data_json:
                print(
                    f"⚠️ 데이터 불일치! (parent_id: {parent_id}) -> (sid: {sid})를 찾았으나, 실제 세션 데이터가 없습니다."
                )
                return None

            return ConnectionInfo.from_dict(json.loads(session_data_json))

        except redis.RedisError as e:
            print(
                f"🚨 Redis get_session_by_parent_id 실패 (ParentID: {parent_id}): {e}"
            )
            return None

    async def delete_session(self, session_info: ConnectionInfo) -> bool:
        """
        'ConnectionInfo' 객체를 직접 받아 불필요한 GET 요청을 제거합니다.
        """
        #TODO: 세션 확인용 코드
        return True
    
        if not session_info:
            print("⚠️ 삭제할 세션 정보가 없습니다.")
            return False

        try:
            async with self.redis_client.pipeline() as pipe:

                keys_to_delete: List[str] = []

                sid_key = self._get_key(SessionKeyType.SID, session_info.sid)
                keys_to_delete.append(sid_key)

                if session_info.id is not None:
                    keys_to_delete.append(
                        self._get_key(SessionKeyType.ROBOT_ID, session_info.id)
                    )

                if session_info.id is not None:
                    keys_to_delete.append(
                        self._get_key(SessionKeyType.PARENT_ID, session_info.id)
                    )

                # 'pipe.delete'에 리스트를 한 번에 전달
                if keys_to_delete:
                    pipe.delete(*keys_to_delete)
                    print(f"[DELETE] {keys_to_delete}")

                results = await pipe.execute()

            deleted_count = results[0] if results else 0
            print(
                f"--- 세션 삭제 완료 (SID: {session_info.sid}), 총 {deleted_count}개 키 삭제됨. ---"
            )
            return deleted_count > 0

        except redis.RedisError as e:
            print(f"🚨 Redis 세션 삭제 실패 (SID: {session_info.sid}): {e}")
            return False
