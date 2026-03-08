import asyncio
import logging
import time
from contextlib import asynccontextmanager

import uvicorn

import api
from config import settings
from distributor import FrameDistributor
from zmq_subscriber import ZMQSubscriber

logger = logging.getLogger(__name__)


async def cleanup_stale_peers() -> None:
    """Background task: remove peers stale (> 300s sem estar conectado)."""
    while True:
        await asyncio.sleep(30)
        now = time.monotonic()
        stale = [
            peer_id
            for peer_id, (pc, created_at) in list(api.peer_connections.items())
            if (now - created_at > 300) and pc.connectionState != "connected"
        ]
        for peer_id in stale:
            pc, _ = api.peer_connections.pop(peer_id, (None, None))
            if pc is not None:
                await api.distributor.remove_session(peer_id)
                try:
                    await pc.close()
                except Exception as exc:
                    logger.warning("Erro ao fechar peer stale %s: %s", peer_id, exc)
                logger.info("Peer stale removido: %s", peer_id)


@asynccontextmanager
async def lifespan(app):
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    dist = FrameDistributor()
    sub = ZMQSubscriber(
        endpoint=settings.ZMQ_ENDPOINT,
        distributor=dist,
        threshold_s=settings.ZMQ_CONNECTED_THRESHOLD_S,
    )

    # Injetar singletons no módulo api
    api.distributor = dist
    api.subscriber = sub
    api._start_time = time.monotonic()

    asyncio.create_task(sub.start())
    asyncio.create_task(cleanup_stale_peers())

    logger.info(
        "webrtc-backend iniciado — ZMQ: %s | HTTP: %s:%d",
        settings.ZMQ_ENDPOINT,
        settings.HTTP_HOST,
        settings.HTTP_PORT,
    )

    yield

    logger.info("webrtc-backend encerrando...")


api.app.router.lifespan_context = lifespan


if __name__ == "__main__":
    uvicorn.run(
        api.app,
        host=settings.HTTP_HOST,
        port=settings.HTTP_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
