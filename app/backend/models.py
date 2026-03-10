from pydantic import BaseModel, field_validator
from typing import Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v: list[ChatMessage]) -> list[ChatMessage]:
        if not v:
            raise ValueError("messages must not be empty")
        if v[-1].role != "user":
            raise ValueError("last message must have role 'user'")
        return v


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
