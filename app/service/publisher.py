"""
Publisher ZMQ PUSH para envio de frames anotados + metadados ao backend.
"""
from __future__ import annotations

import json
import logging

import cv2
import numpy as np
import zmq

from models import FrameMetadata

logger = logging.getLogger(__name__)

_SNDHWM = 2
_LINGER = 0
_SNDTIMEO = 100  # ms


class ZMQPublisher:
    """
    Vincula um socket ZMQ PUSH e publica frames multipart:
        [frame_jpeg: bytes, metadata_json: bytes]
    """

    def __init__(self, endpoint: str) -> None:
        self._ctx = zmq.Context.instance()
        self._sock = self._ctx.socket(zmq.PUSH)
        self._sock.setsockopt(zmq.SNDHWM, _SNDHWM)
        self._sock.setsockopt(zmq.LINGER, _LINGER)
        self._sock.setsockopt(zmq.SNDTIMEO, _SNDTIMEO)
        self._sock.bind(endpoint)
        logger.info("ZMQ PUSH vinculado em %s", endpoint)

    def publish(
        self,
        frame: np.ndarray,
        metadata: FrameMetadata,
        jpeg_quality: int,
    ) -> None:
        """
        Codifica o frame como JPEG e envia multipart junto com metadados JSON.
        ZMQError é capturado silenciosamente para não interromper o loop principal.
        """
        try:
            ret, buf = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
            )
            if not ret:
                logger.warning("Falha na codificação JPEG — frame ignorado")
                return

            frame_bytes = buf.tobytes()
            meta_bytes = metadata.model_dump_json().encode("utf-8")
            self._sock.send_multipart([frame_bytes, meta_bytes])
        except zmq.ZMQError as exc:
            logger.debug("ZMQError ao publicar frame: %s", exc)
        except Exception as exc:
            logger.warning("Erro inesperado no publisher: %s", exc)

    def close(self) -> None:
        """Fecha o socket e encerra o contexto."""
        try:
            self._sock.close()
        except Exception:
            pass
        logger.info("ZMQPublisher fechado.")
