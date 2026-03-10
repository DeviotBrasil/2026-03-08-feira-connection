import asyncio
import json
import logging
import time
from uuid import uuid4

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from aiortc import RTCPeerConnection, RTCSessionDescription

from config import settings
from distributor import FrameDistributor
from models import AnswerResponse, ChatRequest, HealthStatus, OfferRequest
from rag import build_system_prompt
from webrtc_track import QueuedVideoTrack
from zmq_subscriber import ZMQSubscriber

logger = logging.getLogger(__name__)

app = FastAPI(title="WebRTC Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons injetados pelo main.py via lifespan
distributor: FrameDistributor | None = None
subscriber: ZMQSubscriber | None = None
_start_time: float = time.monotonic()

# dict[peer_id, (RTCPeerConnection, created_at)] — obrigatório para TTL (T012)
peer_connections: dict[str, tuple[RTCPeerConnection, float]] = {}


@app.post("/offer", response_model=AnswerResponse)
async def offer(request: OfferRequest) -> AnswerResponse:
    peer_id = str(uuid4())
    queue: asyncio.Queue = asyncio.Queue(maxsize=1)

    pc = RTCPeerConnection()
    peer_connections[peer_id] = (pc, time.monotonic())

    await distributor.add_session(peer_id, queue)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        state = pc.connectionState
        logger.info("Peer %s connectionState → %s", peer_id, state)
        if state in ("failed", "closed", "disconnected"):
            logger.info("Liberando peer desconectado: %s (state=%s)", peer_id, state)
            await distributor.remove_session(peer_id)
            peer_connections.pop(peer_id, None)
            try:
                await pc.close()
            except Exception as exc:
                logger.warning("Erro ao fechar RTCPeerConnection %s: %s", peer_id, exc)

    # Ordem correta para answerer: setRemoteDescription → addTrack → createAnswer
    remote_desc = RTCSessionDescription(sdp=request.sdp, type=request.type)
    await pc.setRemoteDescription(remote_desc)

    track = QueuedVideoTrack(queue)
    pc.addTrack(track)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Aguardar ICE gathering completo (ICE bundled — sem trickle ICE)
    if pc.iceGatheringState != "complete":
        ice_complete = asyncio.Event()

        @pc.on("icegatheringstatechange")
        def on_ice_gathering() -> None:
            if pc.iceGatheringState == "complete":
                ice_complete.set()

        try:
            await asyncio.wait_for(ice_complete.wait(), timeout=settings.ICE_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("ICE gathering timeout para peer %s — retornando SDP parcial", peer_id)

    return AnswerResponse(sdp=pc.localDescription.sdp, type=pc.localDescription.type)


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Encaminha mensagens ao Ollama com system prompt RAG e transmite resposta via SSE."""
    system_prompt = build_system_prompt()
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [{"role": "system", "content": system_prompt}]
        + [m.model_dump() for m in request.messages],
        "stream": True,
    }

    async def event_stream():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{settings.OLLAMA_URL}/api/chat",
                    json=payload,
                    timeout=settings.OLLAMA_TIMEOUT,
                ) as resp:
                    if resp.status_code != 200:
                        yield f'data: {{"error": "Ollama returned {resp.status_code}", "done": true}}\n\n'
                        return
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        done = chunk.get("done", False)
                        yield f'data: {json.dumps({"content": content, "done": done})}\n\n'
                        if done:
                            break
        except httpx.ConnectError:
            yield 'data: {"error": "Ollama service unavailable", "done": true}\n\n'
        except httpx.TimeoutException:
            yield 'data: {"error": "Model response timeout", "done": true}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    # Leituras O(1) — sem adquirir nenhum lock blocante (SC-005 < 200ms)
    connected = subscriber.is_connected if subscriber else False
    fps = subscriber.last_fps_measured if subscriber else 0.0
    frames_rx = subscriber.frames_received if subscriber else 0
    sessions = distributor.session_count if distributor else 0
    frames_dist = distributor.frames_distributed if distributor else 0
    uptime = time.monotonic() - _start_time

    return HealthStatus(
        status="ok" if connected else "degraded",
        zmq_connected=connected,
        peers_active=sessions,
        fps_recent=fps,
        fps_below_threshold=fps < 24.0,
        frames_received=frames_rx,
        frames_distributed=frames_dist,
        uptime_seconds=uptime,
    )


# ---------------------------------------------------------------------------
# Servir frontend estático (React SPA)
# ---------------------------------------------------------------------------
from pathlib import Path  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402

_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=_FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(_FRONTEND_DIST / "index.html")
