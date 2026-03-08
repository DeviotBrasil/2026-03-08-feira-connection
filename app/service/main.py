"""
Ponto de entrada do Vision Service.
Loop principal: captura → inferência → anotação → publicação.
FastAPI roda em thread daemon separada.
"""
from __future__ import annotations

import collections
import logging
import signal
import sys
import threading
import time
from datetime import datetime, timezone

import uvicorn

import api as api_module
from annotator import FrameAnnotator
from camera import CameraCapture
from config import load_config, save_config
from inference import YOLOInference
from models import FrameMetadata, ServiceStatus
from publisher import ZMQPublisher

# ---------------------------------------------------------------------------
# Logging estruturado
# ---------------------------------------------------------------------------

def _setup_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Controle de encerramento
# ---------------------------------------------------------------------------

_shutdown_event = threading.Event()


def _handle_signal(signum: int, frame) -> None:  # noqa: ANN001
    logger.info("Sinal %d recebido — encerrando serviço…", signum)
    _shutdown_event.set()


# ---------------------------------------------------------------------------
# Loop principal
# ---------------------------------------------------------------------------

def main() -> None:
    config = load_config()
    _setup_logging(config.log_level)
    logger.info("Vision Service iniciando…")

    # Registra handlers de sinal
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # Fail-fast: carrega modelo YOLO (levanta RuntimeError se não existir)
    yolo = YOLOInference(
        model_path=config.yolo_model_path,
        published_width=config.capture_width,
        published_height=config.capture_height,
    )

    camera = CameraCapture(config)
    annotator = FrameAnnotator()
    publisher = ZMQPublisher(config.zmq_endpoint)

    # Compartilha config inicial com a API
    api_module.update_health_state(config=config)

    # Inicia FastAPI em thread daemon
    uv_config = uvicorn.Config(
        app=api_module.app,
        host="0.0.0.0",
        port=config.http_port,
        log_level="warning",
    )
    uv_server = uvicorn.Server(uv_config)
    api_thread = threading.Thread(target=uv_server.run, daemon=True, name="api-thread")
    api_thread.start()
    logger.info("API HTTP disponível na porta %d", config.http_port)

    # Janela deslizante para FPS (30 frames)
    fps_window: collections.deque[float] = collections.deque(maxlen=30)
    frame_id = 0
    frames_published = 0
    _FPS_LOW_THRESHOLD = 24.0

    logger.info("Loop principal iniciado.")

    try:
        while not _shutdown_event.is_set():
            # Aplica atualização de config se disponível
            try:
                new_config = api_module.config_update_queue.get_nowait()
                logger.info("Configuração atualizada via API")
                config = new_config
                save_config(config)
                camera.apply_camera_props(config)
                api_module.update_health_state(config=config)
            except Exception:
                pass  # Fila vazia — normal

            # Captura frame
            frame = camera.read()

            if frame is None:
                status = (
                    ServiceStatus.reconnecting
                    if not camera.is_connected
                    else ServiceStatus.degraded
                )
                api_module.update_health_state(
                    camera_connected=False,
                    status=status,
                )
                time.sleep(0.01)
                continue

            # Inferência
            detections, inference_error = yolo.run(
                frame,
                conf=config.confidence_threshold,
                infer_width=config.inference_width,
                infer_height=config.inference_height,
            )

            # FPS
            now_ts = time.monotonic()
            fps_window.append(now_ts)
            if len(fps_window) >= 2:
                elapsed = fps_window[-1] - fps_window[0]
                fps = (len(fps_window) - 1) / elapsed if elapsed > 0 else 0.0
            else:
                fps = 0.0

            # Anotação
            annotated = annotator.draw(frame, detections)

            # Metadados
            frame_id += 1
            now_dt = datetime.now(timezone.utc)
            metadata = FrameMetadata(
                frame_id=frame_id,
                timestamp_iso=now_dt.isoformat(),
                timestamp_ms=int(now_dt.timestamp() * 1000),
                fps_measured=round(fps, 2),
                width=annotated.shape[1],
                height=annotated.shape[0],
                detections=detections,
                inference_error=inference_error,
                person_count=sum(1 for d in detections if d.class_name.lower() == "person"),
            )

            # Publicação ZMQ
            publisher.publish(annotated, metadata, jpeg_quality=config.jpeg_quality)
            frames_published += 1

            # Atualiza estado de saúde
            api_module.update_health_state(
                status=ServiceStatus.ok,
                fps_measured=round(fps, 2),
                fps_below_threshold=fps < _FPS_LOW_THRESHOLD,
                camera_connected=True,
                inference_ok=not inference_error,
                frames_published=frames_published,
            )

    except Exception as exc:
        logger.error("Erro fatal no loop principal: %s", exc, exc_info=True)
    finally:
        logger.info("Encerrando componentes…")
        camera.release()
        publisher.close()
        uv_server.should_exit = True
        api_thread.join(timeout=3)
        logger.info("Vision Service encerrado.")


if __name__ == "__main__":
    main()
