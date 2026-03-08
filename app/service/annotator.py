"""
Anotação visual dos frames com bounding boxes e contadores.
"""
from __future__ import annotations

import cv2
import numpy as np

from models import Detection

# Paleta de cores por classe (BGR)
_COLOR_PERSON = (0, 200, 0)       # verde
_COLOR_DEFAULT = (200, 100, 0)    # azul-laranja


def _class_color(class_name: str) -> tuple[int, int, int]:
    if class_name.lower() == "person":
        return _COLOR_PERSON
    return _COLOR_DEFAULT


class FrameAnnotator:
    """Desenha bounding boxes e contador de pessoas sobre o frame."""

    def draw(self, frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
        """
        Parâmetros
        ----------
        frame:
            Frame BGR na resolução de publicação (ex. 1280×720).
        detections:
            Lista de detecções com bbox já no espaço do frame.

        Retorna
        -------
        Cópia anotada do frame.
        """
        canvas = frame.copy()
        person_count = sum(1 for d in detections if d.class_name.lower() == "person")

        for det in detections:
            color = _class_color(det.class_name)
            x, y, w, h = det.bbox.x, det.bbox.y, det.bbox.width, det.bbox.height
            cv2.rectangle(canvas, (x, y), (x + w, y + h), color, 2)

            label = f"{det.class_name} {det.confidence:.0%}"
            (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            label_y = max(y - 6, th + baseline)

            # Fundo escuro para legibilidade
            cv2.rectangle(
                canvas,
                (x, label_y - th - baseline),
                (x + tw + 2, label_y + baseline),
                (0, 0, 0),
                cv2.FILLED,
            )
            cv2.putText(
                canvas,
                label,
                (x + 1, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                1,
                cv2.LINE_AA,
            )

        # Contador no canto superior esquerdo
        counter_text = f"Pessoas: {person_count}"
        cv2.putText(
            canvas,
            counter_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        return canvas
