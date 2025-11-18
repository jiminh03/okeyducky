from loguru import logger

import os
import redis.asyncio as redis
import json
from typing import Any, Dict, Optional, Type, Union
from common.modules.db_manager import RedisSessionManager

SDP_EXPIRATION_SECONDS = os.environ.get("SDP_EXPIRATION_SECONDS", 300)


class WebRTCManager:
    """Redis에 WebRTC 패킷을 등록하고 조회하는 작업을 관리합니다."""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def _get_offer_key(self, sid: int) -> str:
        return f"webrtc:offer:{sid}"

    def _get_answer_key(self, sid: int) -> str:
        return f"webrtc:answer:{sid}"

    async def _register_sdp(self, key: str, packet: Dict[str, Any], sdp_type: str):
        await self.redis_client.set(key, json.dumps(packet), ex=SDP_EXPIRATION_SECONDS)
        logger.info(
            f"WebRTC log: Registered {sdp_type} with key '{key}' (expires in {SDP_EXPIRATION_SECONDS}s)"
        )

    async def register_offer(self, sid: int, offer_packet: Dict[str, Any]):
        key = self._get_offer_key(sid)
        await self._register_sdp(key, offer_packet, "Offer")

    async def register_answer(self, sid: int, answer_packet: Dict[str, Any]):
        key = self._get_answer_key(sid)
        await self._register_sdp(key, answer_packet, "Answer")

    async def consume_sdp(self, key: str, sdp_type: str) -> Optional[Dict[str, Any]]:
        """
        SDP(Offer/Answer) 패킷을 조회하고 즉시 삭제한 뒤,
        파싱된 파이썬 딕셔너리로 반환합니다.
        """
        data_str = await self.redis_client.getdel(key)

        if data_str:
            logger.info(f"WebRTC log: Consumed {sdp_type} from key '{key}'")
            # ❗ Redis에서 가져온 JSON 문자열을 파이썬 딕셔너리로 파싱합니다.
            return json.loads(data_str)

        logger.info(f"No {sdp_type} found for key '{key}'")
        return None

    async def consume_offer(self, sid: int) -> Optional[Dict[str, Any]]:
        key = self._get_offer_key(sid)
        return await self.consume_sdp(key, "Offer")

    async def consume_answer(self, sid: int) -> Optional[Dict[str, Any]]:
        key = self._get_answer_key(sid)
        return await self.consume_sdp(key, "Answer")
