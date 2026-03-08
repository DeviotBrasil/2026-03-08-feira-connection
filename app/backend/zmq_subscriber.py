import asyncio
import json
import logging
import time

import zmq
import zmq.asyncio

from distributor import FrameDistributor

logger = logging.getLogger(__name__)


class ZMQSubscriber:
    """Consome frames JPEG do vision-service via socket ZMQ PULL assíncrono."""

    def __init__(self, endpoint: str, distributor: FrameDistributor, threshold_s: float = 2.0) -> None:
        self._endpoint = endpoint
        self._distributor = distributor
        self._threshold_s = threshold_s
        self._frames_received: int = 0
        self._last_recv_ts: float = 0.0
        self._last_fps_measured: float = 0.0

    async def start(self) -> None:
        ctx = zmq.asyncio.Context()
        socket = ctx.socket(zmq.PULL)
        # RCVHWM pequeno para não acumular frames antigos na fila do socket
        # CONFLATE removido: não funciona com mensagens multipart (descarta partes individualmente)
        socket.setsockopt(zmq.RCVHWM, 5)
        socket.connect(self._endpoint)
        logger.info("ZMQSubscriber conectado em %s", self._endpoint)

        while True:
            try:
                parts = await socket.recv_multipart()
            except zmq.ZMQError as exc:
                logger.warning("ZMQError ao receber frame: %s", exc)
                await asyncio.sleep(0.1)
                continue
            except Exception as exc:
                logger.warning("Erro inesperado no recv_multipart: %s", exc)
                continue

            if len(parts) < 1 or len(parts[0]) == 0:
                logger.warning("Frame inválido recebido (partes=%d), descartando", len(parts))
                continue

            # Parsear metadados e persistir fps_measured
            if len(parts) >= 2:
                try:
                    meta = json.loads(parts[1].decode())
                    self._last_fps_measured = meta["fps_measured"]
                except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                    pass  # manter valor anterior

            self._frames_received += 1
            self._last_recv_ts = time.monotonic()
            await self._distributor.distribute(parts[0])

    @property
    def frames_received(self) -> int:
        return self._frames_received

    @property
    def last_recv_ts(self) -> float:
        return self._last_recv_ts

    @property
    def last_fps_measured(self) -> float:
        return self._last_fps_measured

    @property
    def is_connected(self) -> bool:
        if self._last_recv_ts == 0.0:
            return False
        return (time.monotonic() - self._last_recv_ts) < self._threshold_s
