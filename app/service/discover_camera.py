#!/usr/bin/env python3
"""
Script de diagnóstico — descobre câmeras disponíveis via OpenCV.
Itera índices 0-9 e imprime as câmeras abertas com resolução detectada.

Uso:
    python discover_camera.py
"""
import cv2


def discover_cameras(max_index: int = 9) -> None:
    print("Procurando câmeras (índices 0–%d)…\n" % max_index)
    found = []

    for idx in range(max_index + 1):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            found.append((idx, width, height, fps))
            cap.release()

    if not found:
        print("Nenhuma câmera encontrada.")
        return

    print(f"{'Índice':<8} {'Resolução':<16} {'FPS':<8}")
    print("-" * 36)
    for idx, w, h, fps in found:
        print(f"{idx:<8} {w}x{h:<12}  {fps:.1f}")

    print()
    print("Dica: defina CAMERA_DEVICE_INDEX=<índice> no .env")
    print("      Índice 0 geralmente é a webcam integrada do Mac.")
    print("      A Logitech C925e costuma aparecer como índice 1.")


if __name__ == "__main__":
    discover_cameras()
