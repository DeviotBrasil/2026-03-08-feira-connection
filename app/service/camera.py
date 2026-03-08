"""
Captura de frames via OpenCV.
Suporte macOS (AVFoundation) e Linux (V4L2) via índice numérico.
"""
from __future__ import annotations

import logging
import time

import cv2
import numpy as np

from models import ServiceConfig

logger = logging.getLogger(__name__)

_CONSECUTIVE_NONE_THRESHOLD = 5
_RETRY_INTERVAL_S = 2.0


class CameraCapture:
    """
    Abstração sobre cv2.VideoCapture.

    Retry de 2s no construtor se a câmera não abrir (sem lançar exceção).
    Durante operação, após 5 frames consecutivos None, tenta reconectar.
    """

    def __init__(self, config: ServiceConfig) -> None:
        self._config = config
        self._cap: cv2.VideoCapture | None = None
        self._consecutive_none = 0
        self._connected = False
        self._open_camera()

    # ------------------------------------------------------------------
    # Propriedades públicas
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def read(self) -> np.ndarray | None:
        """
        Retorna o próximo frame BGR ou None se a leitura falhar.
        Após _CONSECUTIVE_NONE_THRESHOLD falhas consecutivas reconecta.
        """
        if self._cap is None or not self._cap.isOpened():
            self._connected = False
            self._try_reconnect()
            return None

        ret, frame = self._cap.read()
        if not ret or frame is None:
            self._consecutive_none += 1
            if self._consecutive_none >= _CONSECUTIVE_NONE_THRESHOLD:
                logger.warning(
                    "Câmera: %d frames None consecutivos — tentando reconectar",
                    self._consecutive_none,
                )
                self._connected = False
                self._try_reconnect()
            return None

        self._consecutive_none = 0
        self._connected = True
        return frame

    def apply_camera_props(self, config: ServiceConfig) -> None:
        """Aplica propriedades de câmera a partir de uma configuração."""
        if self._cap is None or not self._cap.isOpened():
            return
        self._cap.set(cv2.CAP_PROP_BRIGHTNESS, config.brightness)
        self._cap.set(cv2.CAP_PROP_EXPOSURE, config.exposure)
        autofocus_val = 1.0 if config.autofocus else 0.0
        self._cap.set(cv2.CAP_PROP_AUTOFOCUS, autofocus_val)

    def release(self) -> None:
        """Libera o recurso de câmera."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._connected = False

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _open_camera(self) -> None:
        """
        Abre a câmera com retry de 2s.
        Não lança exceção — registra aviso e continua tentando.
        """
        index = self._config.camera_device_index
        while True:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.capture_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.capture_height)
                self.apply_camera_props(self._config)
                self._cap = cap
                self._connected = True
                logger.info(
                    "Câmera aberta: índice=%d, resolução=%dx%d",
                    index,
                    self._config.capture_width,
                    self._config.capture_height,
                )
                return
            else:
                cap.release()
                logger.warning(
                    "Câmera índice %d não disponível — nova tentativa em %.0fs",
                    index,
                    _RETRY_INTERVAL_S,
                )
                time.sleep(_RETRY_INTERVAL_S)

    def _try_reconnect(self) -> None:
        """Tenta reconectar uma vez; se falhar, agenda próxima tentativa no ciclo."""
        logger.info("Reconectando câmera…")
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._consecutive_none = 0

        index = self._config.camera_device_index
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.capture_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.capture_height)
            self.apply_camera_props(self._config)
            self._cap = cap
            self._connected = True
            logger.info("Câmera reconectada com sucesso.")
        else:
            cap.release()
            logger.warning(
                "Reconexão falhou — nova tentativa em %.0fs", _RETRY_INTERVAL_S
            )
            time.sleep(_RETRY_INTERVAL_S)
