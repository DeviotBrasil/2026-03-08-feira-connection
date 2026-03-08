# Implementation Plan: Serviço Python de Visão Computacional

**Branch**: `001-python-service` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-python-app/service/spec.md`

## Summary

Serviço Python standalone que captura frames de uma Logitech C925e via USB em macOS, executa
inferência YOLO (YOLOv8n) para detecção de pessoas (e demais classes COCO) em tempo real,
anota o frame com bounding boxes e scores de confiança, e publica cada frame processado via
ZMQ PUSH como mensagem multipart `[frame_jpeg, metadata_json]`. Expõe endpoints HTTP leves
(FastAPI) para health-check e reconfiguração em runtime sem restart do processo. Projetado
para operar 8h contínuas em macOS com auto-restart via launchd/supervisord.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: ultralytics (YOLOv8n), opencv-python-headless, pyzmq ≥ 25, fastapi ≥ 0.100, uvicorn, pydantic ≥ 2, numpy
**Storage**: Arquivo JSON local `config.json` (persistência de ServiceConfig); modelo `yolov8n.pt` armazenado localmente
**Testing**: N/A — Demo-Mode (Princípio VII da constituição)
**Target Platform**: macOS 13+ (Ventura) com Python 3.11 via pyenv/homebrew; câmera Logitech C925e via USB
**Project Type**: Background service (processo standalone gerenciado por supervisor)
**Performance Goals**: ≥ 24 FPS publicados no ZMQ com inferência YOLO inclusa; latência câmera → ZMQ < 100ms por frame
**Constraints**: Sem GPU obrigatória (YOLOv8n roda em CPU Apple Silicon/Intel); sem acesso à internet em runtime; câmera acessada por device index OpenCV (não por path `/dev/videoX` — macOS não usa V4L2)
**Scale/Scope**: 1 câmera, 1 processo, 1 consumidor ZMQ (backend FastAPI); demo para visitantes de feira industrial

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Gate | Status | Observação |
|---|---|---|---|
| I. Demo-First | Serviço produz output visual direto (frames anotados com bounding boxes)? | ✅ PASS | Frames JPEG com overlay YOLO publicados a cada ciclo |
| II. Latência Zero-Compromisso | Transporte usa ZMQ (não HLS/MJPEG/RTSP)? | ✅ PASS | ZMQ PUSH socket; nenhum protocolo com buffer no caminho crítico |
| III. Estabilidade 8h | Serviço tem health-check, retry de câmera e graceful degradation? | ✅ PASS | Health endpoint + retry loop + frame publicado mesmo sem detecções |
| IV. 24 FPS Mínimo | Design suporta ≥ 24 FPS com YOLOv8n em CPU? | ✅ PASS | YOLOv8n em Apple M-series atinge 30–60 FPS; ajuste de resolução disponível |
| V. Rede Cabeada | Serviço tem dependência de rede externa em runtime? | ✅ PASS | Zero dependências externas; modelo local; ZMQ em loopback |
| VI. Degradação Graciosa | Parâmetros ajustáveis em runtime via endpoint? | ✅ PASS | `POST /config` sem restart; persiste config em JSON local |
| VII. Demo-Mode: Sem Testes | Nenhuma tarefa de teste no tasks.md? | ✅ PASS | Testes automatizados proibidos; validação manual + soak test de 8h |
| Stack Mandatório | Usa Python + YOLO + ZMQ conforme tabela da constituição? | ✅ PASS | Stack 100% alinhado |

**Resultado: APROVADO — pode prosseguir para Phase 0.**

**⚠️ Atenção macOS**: A spec original menciona `/dev/video0` (V4L2 — Linux only). macOS não usa V4L2.
A câmera Logitech C925e no macOS é acessada por **device index** via OpenCV (`cv2.VideoCapture(0)`),
e o controle de exposição/brilho é via `cv2.VideoCapture.set()` com propriedades AVFoundation.
Controle UVC granular (V4L2-ctl) não está disponível nativamente no macOS — isso é RESOLVIDO
na research.md com a abordagem `opencv-python` + propriedades CAP_PROP_*.

**Re-check pós-Phase 1**: ✅ PASS — Estrutura de projeto e contratos confirmam stack mandatório.

## Project Structure

### Documentation (this feature)

```text
specs/001-python-app/service/
├── plan.md              # Este arquivo
├── research.md          # Phase 0: decisões de plataforma macOS + C925e
├── data-model.md        # Phase 1: entidades Frame, Detection, ServiceConfig, HealthStatus
├── quickstart.md        # Phase 1: como rodar localmente e testar
├── contracts/
│   └── zmq-frame-contract.md  # Contrato ZMQ multipart (formato de mensagem)
└── tasks.md             # Phase 2 (gerado por /speckit.tasks)
```

### Source Code (repository root)

```text
app/service/
├── main.py                    # Entrypoint: inicializa câmera, YOLO, ZMQ, FastAPI
├── config.py                  # ServiceConfig (Pydantic model + load/save JSON)
├── camera.py                  # CameraCapture: OpenCV + retry loop + UVC props macOS
├── inference.py               # YOLOInference: carrega modelo, executa, retorna detections
├── publisher.py               # ZMQPublisher: socket PUSH, serializa frame + metadata
├── annotator.py               # FrameAnnotator: desenha bounding boxes + labels no frame
├── api.py                     # FastAPI: GET /health, POST /config
├── models.py                  # Pydantic models: Detection, FrameMetadata, HealthStatus, ConfigRequest
├── config.json                # Config persistida em runtime (gitignored)
├── requirements.txt           # Dependências fixadas
└── supervisord.conf           # Processo supervisor para auto-restart
```

**Structure Decision**: Single-project Python service em `app/service/`. Não há frontend
nem backend nesta feature — este serviço é apenas a Engine de IA que publica para o backend
(feature separada). Estrutura plana favorece legibilidade e manutenção durante a feira.

## Complexity Tracking

> Nenhuma violação da constituição identificada. Tabela não aplicável.
