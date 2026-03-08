import asyncio
import time
from typing import Optional


class FrameDistributor:
    """Distribui frames JPEG para filas de peers via fan-out assíncrono."""

    def __init__(self) -> None:
        self._sessions: dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()
        self._frames_distributed: int = 0
        self._last_frame_ts: float = 0.0

    async def add_session(self, peer_id: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            self._sessions[peer_id] = queue

    async def remove_session(self, peer_id: str) -> None:
        async with self._lock:
            self._sessions.pop(peer_id, None)

    async def distribute(self, jpeg_bytes: bytes) -> None:
        self._last_frame_ts = time.monotonic()
        async with self._lock:
            queues = list(self._sessions.values())

        if not queues:
            return

        async def _put(q: asyncio.Queue) -> None:
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(jpeg_bytes)
            except asyncio.QueueFull:
                pass

        await asyncio.gather(*[_put(q) for q in queues], return_exceptions=True)
        self._frames_distributed += 1

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    @property
    def frames_distributed(self) -> int:
        return self._frames_distributed

    @property
    def last_frame_ts(self) -> float:
        return self._last_frame_ts
