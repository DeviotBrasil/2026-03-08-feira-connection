"""
Modelos Pydantic do Vision Service.
Entidades: BoundingBox, Detection, FrameMetadata, ServiceConfig, HealthStatus, ConfigRequest
"""
from __future__ import annotations

import json
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Entidades de detecção YOLO
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    """Coordenadas do bounding box no frame publicado (resolução de captura)."""
    x: int = Field(..., ge=0, description="X canto superior esquerdo (pixels)")
    y: int = Field(..., ge=0, description="Y canto superior esquerdo (pixels)")
    width: int = Field(..., gt=0, description="Largura em pixels")
    height: int = Field(..., gt=0, description="Altura em pixels")


class Detection(BaseModel):
    """Objeto detectado pelo YOLO em um frame."""
    class_name: str = Field(..., min_length=1, description="Nome da classe COCO")
    class_id: int = Field(..., ge=0, le=79, description="Índice numérico COCO (0–79)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Score de confiança")
    bbox: BoundingBox


class FrameMetadata(BaseModel):
    """Payload JSON publicado como segundo frame ZMQ multipart."""
    frame_id: int = Field(..., gt=0, description="Contador sequencial desde o start")
    timestamp_iso: str = Field(..., description="Momento de captura — ISO 8601 UTC")
    timestamp_ms: int = Field(..., ge=0, description="Unix timestamp em ms")
    fps_measured: float = Field(..., ge=0.0, description="FPS médio últimos 30 frames")
    width: int = Field(..., gt=0, description="Largura do frame JPEG publicado")
    height: int = Field(..., gt=0, description="Altura do frame JPEG publicado")
    detections: list[Detection] = Field(default_factory=list)
    inference_error: bool = Field(False, description="True se inferência falhou neste frame")
    person_count: int = Field(0, ge=0, description="Atalho: qtd de detecções com class_name=='person'")


# ---------------------------------------------------------------------------
# Configuração do serviço
# ---------------------------------------------------------------------------

class ServiceConfig(BaseModel):
    """Estado de configuração mutável em runtime. Persistido em config.json."""
    camera_device_index: int = Field(0, ge=0, description="Índice OpenCV da câmera")
    zmq_endpoint: str = Field("tcp://0.0.0.0:5555", description="Bind do socket ZMQ PUSH")
    yolo_model_path: str = Field("yolov8n.pt", description="Path local do modelo YOLO")
    confidence_threshold: float = Field(0.5, ge=0.01, le=0.99, description="Limiar mínimo de confiança")
    inference_width: int = Field(640, gt=0, description="Largura de inferência YOLO")
    inference_height: int = Field(480, gt=0, description="Altura de inferência YOLO")
    capture_width: int = Field(1280, gt=0, description="Largura alvo de captura")
    capture_height: int = Field(720, gt=0, description="Altura alvo de captura")
    jpeg_quality: int = Field(85, ge=1, le=100, description="Qualidade JPEG do frame publicado")
    brightness: int = Field(128, ge=0, le=255, description="Brilho da câmera (CAP_PROP_BRIGHTNESS)")
    exposure: int = Field(-5, ge=-13, le=-1, description="Exposição da câmera macOS (CAP_PROP_EXPOSURE)")
    autofocus: bool = Field(True, description="Liga/desliga autofoco da câmera")
    http_port: int = Field(8000, ge=1024, le=65535, description="Porta HTTP da API")
    log_level: str = Field("INFO", description="Nível de log")


class ConfigRequest(BaseModel):
    """Campos opcionais para PATCH parcial via POST /config."""
    confidence_threshold: Optional[float] = Field(None, ge=0.01, le=0.99)
    inference_width: Optional[int] = Field(None, gt=0)
    inference_height: Optional[int] = Field(None, gt=0)
    jpeg_quality: Optional[int] = Field(None, ge=1, le=100)
    brightness: Optional[int] = Field(None, ge=0, le=255)
    exposure: Optional[int] = Field(None, ge=-13, le=-1)
    autofocus: Optional[bool] = None
    camera_device_index: Optional[int] = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class ServiceStatus(str, Enum):
    ok = "ok"
    reconnecting = "reconnecting"
    degraded = "degraded"


class HealthStatus(BaseModel):
    """Snapshot do estado operacional retornado por GET /health."""
    status: ServiceStatus = ServiceStatus.ok
    uptime_seconds: float = Field(0.0, ge=0.0)
    fps_measured: float = Field(0.0, ge=0.0)
    fps_below_threshold: bool = False
    camera_connected: bool = False
    inference_ok: bool = False
    frames_published: int = Field(0, ge=0)
    config: Optional[ServiceConfig] = None
