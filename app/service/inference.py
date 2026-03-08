"""
Inferência YOLOv8 com Ultralytics.
Fail-fast no construtor (model missing) → graceful por frame em run().
"""
from __future__ import annotations

import logging

import cv2
import numpy as np

from models import BoundingBox, Detection

logger = logging.getLogger(__name__)


class YOLOInference:
    """
    Carrega YOLOv8 e executa inferência por frame.

    __init__: fail-fast — levanta RuntimeError se o modelo não puder ser carregado.
    run(): graceful — retorna ([], True) em caso de exceção por frame.
    """

    def __init__(self, model_path: str, published_width: int, published_height: int) -> None:
        """
        Parâmetros
        ----------
        model_path:
            Caminho para o arquivo .pt do modelo YOLOv8.
        published_width / published_height:
            Resolução do frame publicado (ex. 1280×720).
            Bounding boxes serão convertidos para este espaço.
        """
        # Importação atrasada — falha clara se ultralytics não instalado
        try:
            from ultralytics import YOLO  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "Dependência 'ultralytics' não encontrada. "
                "Execute: pip install ultralytics"
            ) from exc

        device = self._detect_device()
        logger.info("Carregando modelo YOLO '%s' no dispositivo '%s'", model_path, device)

        try:
            # Ultralytics faz download automático se o modelo não existir localmente
            self._model = YOLO(model_path)
            self._model.to(device)
        except Exception as exc:
            raise RuntimeError(f"Falha ao carregar modelo YOLO '{model_path}': {exc}") from exc

        self._device = device
        self._pub_w = published_width
        self._pub_h = published_height
        logger.info("Modelo YOLO carregado com sucesso.")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def run(
        self,
        frame: np.ndarray,
        conf: float,
        infer_width: int,
        infer_height: int,
    ) -> tuple[list[Detection], bool]:
        """
        Executa inferência em um frame.

        Retorna
        -------
        (detections, inference_error)
        Em caso de exceção retorna ([], True) sem propagar.
        """
        try:
            resized = cv2.resize(frame, (infer_width, infer_height))
            results = self._model.predict(
                resized,
                conf=conf,
                device=self._device,
                verbose=False,
            )
            detections = self._parse_results(results, frame.shape, infer_width, infer_height)
            return detections, False
        except Exception as exc:
            logger.warning("Erro de inferência por frame: %s", exc)
            return [], True

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _parse_results(
        self,
        results,
        original_shape: tuple[int, int, int],
        infer_width: int,
        infer_height: int,
    ) -> list[Detection]:
        """Converte saída YOLO para lista de Detection com coords no espaço publicado."""
        orig_h, orig_w = original_shape[:2]
        scale_x = orig_w / infer_width
        scale_y = orig_h / infer_height

        detections: list[Detection] = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                # Converte para resolução do frame publicado
                bx = max(0, int(x1 * scale_x))
                by = max(0, int(y1 * scale_y))
                bw = max(1, int((x2 - x1) * scale_x))
                bh = max(1, int((y2 - y1) * scale_y))

                class_id = int(box.cls[0].item())
                class_name = result.names.get(class_id, str(class_id))
                confidence = float(box.conf[0].item())

                detections.append(
                    Detection(
                        class_name=class_name,
                        class_id=class_id,
                        confidence=round(confidence, 4),
                        bbox=BoundingBox(x=bx, y=by, width=bw, height=bh),
                    )
                )
        return detections

    @staticmethod
    def _detect_device() -> str:
        """Detecta MPS (Apple Silicon), CUDA ou CPU."""
        try:
            import torch  # noqa: PLC0415
            if torch.backends.mps.is_available():
                return "mps"
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"
