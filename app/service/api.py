"""
API HTTP FastAPI do Vision Service.
Endpoints: GET /health, POST /config
"""
from __future__ import annotations

import threading
import time
from queue import Queue
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from models import ConfigRequest, HealthStatus, ServiceConfig, ServiceStatus

app = FastAPI(title="Vision Service API", version="1.0.0")

# ---------------------------------------------------------------------------
# Estado compartilhado (acesso thread-safe via lock)
# ---------------------------------------------------------------------------

_lock = threading.Lock()

_state: dict[str, Any] = {
    "status": ServiceStatus.ok,
    "uptime_seconds": 0.0,
    "fps_measured": 0.0,
    "fps_below_threshold": False,
    "camera_connected": False,
    "inference_ok": False,
    "frames_published": 0,
    "config": None,          # ServiceConfig atual
    "start_time": time.monotonic(),
}

# Fila de atualizações de config (main loop consome)
config_update_queue: Queue[ServiceConfig] = Queue(maxsize=1)


# ---------------------------------------------------------------------------
# Funções para atualização de estado (chamadas pelo main loop)
# ---------------------------------------------------------------------------

def update_health_state(**kwargs: Any) -> None:
    """Atualiza campos do estado de saúde do serviço."""
    with _lock:
        _state.update(kwargs)


def get_current_config() -> ServiceConfig | None:
    with _lock:
        return _state.get("config")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    """Retorna snapshot do estado operacional do serviço."""
    with _lock:
        snapshot = dict(_state)

    uptime = time.monotonic() - snapshot["start_time"]
    return HealthStatus(
        status=snapshot["status"],
        uptime_seconds=round(uptime, 1),
        fps_measured=snapshot["fps_measured"],
        fps_below_threshold=snapshot["fps_below_threshold"],
        camera_connected=snapshot["camera_connected"],
        inference_ok=snapshot["inference_ok"],
        frames_published=snapshot["frames_published"],
        config=snapshot.get("config"),
    )


@app.post("/config", response_model=HealthStatus)
async def update_config(request: ConfigRequest) -> HealthStatus:
    """
    Aplica atualização parcial de configuração em runtime.
    Apenas campos não-None de ConfigRequest são aplicados.
    Responde HTTP 422 se a validação Pydantic falhar (automático).
    """
    current = get_current_config()
    if current is None:
        raise HTTPException(status_code=503, detail="Serviço ainda inicializando")

    # Aplica campos fornecidos sobre a config atual
    patch = request.model_dump(exclude_none=True)
    new_config = current.model_copy(update=patch)

    # Envia para o main loop; descarta se a fila estiver cheia (demanda anterior pendente)
    try:
        config_update_queue.put_nowait(new_config)
    except Exception:
        pass  # já existe atualização pendente na fila — ok

    return await health()
