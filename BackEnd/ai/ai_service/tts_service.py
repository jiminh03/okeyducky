# tts_service.py
from loguru import logger

import asyncio
from typing import Dict, Callable, Awaitable

from ai.ai_service.ai_core.model import request_tts
from ai.request import send_stream_start, send_audio_chunk, send_stream_end

CHUNK_SIZE = 1024

# (가상) 실제 TTS 변환 및 웹소켓 전송 로직
async def _actual_tts_and_send(child_id: str, sentence: str):
    """
    [수정됨] 이 함수가 TTS 작업의 시작과 끝을 모두 알립니다.
    """
    try:
        logger.info(f"   [TTS WORKER {child_id}] 🔊 START: '{sentence}'")
        # [수정] 작업 시작 시 STREAM_START 전송
        await send_stream_start(child_id) 

        response = await request_tts(sentence)

        for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
            if chunk:
                await send_audio_chunk(child_id, chunk)
        
    except Exception as e:
        logger.error(f"   [TTS WORKER {child_id}] _actual_tts_and_send 오류: {e}")
    finally:
        # [수정] 작업 완료 시(성공/실패 무관) STREAM_END 전송
        logger.info(f"   [TTS WORKER {child_id}] 🏁 END: '{sentence}'")
        await send_stream_end(child_id)


class TTSService:
    def __init__(self):
        # {child_id: asyncio.Queue[str]}
        self.queues: Dict[str, asyncio.Queue] = {}
        # {child_id: asyncio.Task} (워커 태스크)
        self.workers: Dict[str, asyncio.Task] = {}

    async def _tts_worker(self, child_id: str):
        """
        child_id 전용 큐를 순차적으로 처리하는 워커
        """
        queue = self.queues[child_id]
        logger.info(f"   [TTS SERVICE] ✨ 워커 시작 (Child: {child_id})")
        # [삭제] await send_stream_start(child_id)
        try:
            while True:
                sentence = await queue.get()
                if sentence is None:  # 종료 신호
                    break

                try:
                    await _actual_tts_and_send(child_id, sentence)
                except Exception as e:
                    logger.error(
                        f"   [TTS WORKER {child_id}] 작업 처리 중 오류 발생: {e}"
                    )
                finally:
                    queue.task_done()

        except asyncio.CancelledError:
            logger.info(f"   [TTS WORKER {child_id}] 중단됨.")
        finally:
            logger.info(f"   [TTS WORKER {child_id}] 종료됨.")
            # [삭제] await send_stream_end(child_id)

    async def submit_task(self, child_id: str, sentence: str):
        """
        run_chat_with_parsing에서 호출할 함수 (빠르게 반환됨)
        """
        if child_id not in self.queues:
            # 이 child_id를 처음 본 경우, 큐와 워커를 생성
            self.queues[child_id] = asyncio.Queue()
            self.workers[child_id] = asyncio.create_task(
                self._tts_worker(child_id)
            )
        
        # 큐에 문장을 넣고 즉시 반환 (논블로킹)
        await self.queues[child_id].put(sentence)

# (선택) 싱글턴 인스턴스로 관리
tts_service = TTSService()