from pydantic import BaseModel
from typing import Literal


class OfferRequest(BaseModel):
    sdp: str
    type: Literal["offer"]


class AnswerResponse(BaseModel):
    sdp: str
    type: Literal["answer"]


class HealthStatus(BaseModel):
    status: Literal["ok", "degraded"]
    zmq_connected: bool
    peers_active: int
    fps_recent: float
    fps_below_threshold: bool  # True se fps_recent < 24.0 — Princípio IV
    frames_received: int
    frames_distributed: int
    uptime_seconds: float
