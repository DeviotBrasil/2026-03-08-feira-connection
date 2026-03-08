"""
Carregamento e persistência de ServiceConfig.
Prioridade: config.json > variáveis de ambiente > defaults Pydantic.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from models import ServiceConfig

load_dotenv()

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent / "config.json"


def load_config() -> ServiceConfig:
    """
    Carrega ServiceConfig:
    1. Inicia com defaults Pydantic.
    2. Sobrescreve com valores de config.json (se existir).
    3. Sobrescreve com variáveis de ambiente (maior prioridade).
    """
    # 1. Defaults
    data: dict = {}

    # 2. config.json
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            logger.info("Configuração carregada de %s", CONFIG_FILE)
        except Exception as exc:
            logger.warning("Falha ao ler %s: %s — usando defaults", CONFIG_FILE, exc)

    # 3. Variáveis de ambiente sobrescrevem
    env_map = {
        "CAMERA_DEVICE_INDEX": ("camera_device_index", int),
        "ZMQ_ENDPOINT": ("zmq_endpoint", str),
        "YOLO_MODEL_PATH": ("yolo_model_path", str),
        "CONFIDENCE_THRESHOLD": ("confidence_threshold", float),
        "INFERENCE_WIDTH": ("inference_width", int),
        "INFERENCE_HEIGHT": ("inference_height", int),
        "CAPTURE_WIDTH": ("capture_width", int),
        "CAPTURE_HEIGHT": ("capture_height", int),
        "JPEG_QUALITY": ("jpeg_quality", int),
        "HTTP_PORT": ("http_port", int),
        "LOG_LEVEL": ("log_level", str),
    }
    for env_key, (field, cast) in env_map.items():
        val = os.getenv(env_key)
        if val is not None:
            try:
                data[field] = cast(val)
            except ValueError:
                logger.warning("Variável %s='%s' inválida — ignorada", env_key, val)

    return ServiceConfig(**data)


def save_config(config: ServiceConfig) -> None:
    """Persiste a configuração atual em config.json."""
    try:
        CONFIG_FILE.write_text(
            config.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("Configuração salva em %s", CONFIG_FILE)
    except Exception as exc:
        logger.error("Falha ao salvar configuração: %s", exc)
