# Data Model: Serviço Python de Visão Computacional

**Feature**: 001-python-service  
**Date**: 2026-03-08  
**Source**: spec.md § Key Entities + research.md decisões 5, 6, 7

---

## Entidade 1: Detection

Representa um objeto identificado pelo YOLO em um único frame.

| Campo | Tipo | Validação | Descrição |
|---|---|---|---|
| `class_name` | `str` | não vazio | Nome da classe COCO (ex: `"person"`, `"chair"`) |
| `class_id` | `int` | 0–79 | Índice numérico da classe COCO |
| `confidence` | `float` | 0.0–1.0 | Score de confiança retornado pelo YOLO |
| `bbox` | `BoundingBox` | ver abaixo | Coordenadas do bounding box no frame de captura |

### Entidade 1a: BoundingBox

| Campo | Tipo | Validação | Descrição |
|---|---|---|---|
| `x` | `int` | ≥ 0 | Coordenada X do canto superior esquerdo (pixels, frame original) |
| `y` | `int` | ≥ 0 | Coordenada Y do canto superior esquerdo (pixels, frame original) |
| `width` | `int` | > 0 | Largura do box em pixels |
| `height` | `int` | > 0 | Altura do box em pixels |

**Observação**: As coordenadas são sempre relativas à resolução do frame **publicado** (1280×720),
não à resolução de inferência (640×480). O serviço converte após inferência.

---

## Entidade 2: FrameMetadata

Payload JSON enviado como segundo frame da mensagem ZMQ multipart junto ao JPEG anotado.

| Campo | Tipo | Validação | Descrição |
|---|---|---|---|
| `frame_id` | `int` | > 0, sequencial | Contador monotônico desde o início do processo |
| `timestamp_iso` | `str` | ISO 8601 UTC | Momento da captura do frame pela câmera |
| `timestamp_ms` | `int` | ≥ 0 | Unix timestamp em milissegundos (para cálculo de latência) |
| `fps_measured` | `float` | ≥ 0.0 | FPS médio dos últimos 30 frames (janela deslizante) |
| `width` | `int` | > 0 | Largura do frame JPEG publicado em pixels |
| `height` | `int` | > 0 | Altura do frame JPEG publicado em pixels |
| `detections` | `list[Detection]` | pode ser vazio | Lista de todas as detecções do frame; vazia se nenhum objeto detectado |
| `inference_error` | `bool` | — | `true` se inferência falhou neste frame; `detections` será vazio |
| `person_count` | `int` | ≥ 0 | Atalho: número de detecções com `class_name == "person"` |

---

## Entidade 3: ServiceConfig

Estado de configuração mutável do serviço. Persistido em `config.json` a cada alteração via
`POST /config`. Carregado na inicialização do processo.

| Campo | Tipo | Default | Env Var Override | Descrição |
|---|---|---|---|---|
| `camera_device_index` | `int` | `0` | `CAMERA_DEVICE_INDEX` | Índice OpenCV da câmera (macOS: 0=interna, 1=USB) |
| `zmq_endpoint` | `str` | `"tcp://0.0.0.0:5555"` | `ZMQ_ENDPOINT` | Endereço de bind do socket ZMQ PUSH |
| `yolo_model_path` | `str` | `"yolov8n.pt"` | `YOLO_MODEL_PATH` | Path local do arquivo do modelo |
| `confidence_threshold` | `float` | `0.5` | `CONFIDENCE_THRESHOLD` | Score mínimo para incluir detecção no payload |
| `inference_width` | `int` | `640` | `INFERENCE_WIDTH` | Largura do frame redimensionado para inferência YOLO |
| `inference_height` | `int` | `480` | `INFERENCE_HEIGHT` | Altura do frame redimensionado para inferência YOLO |
| `capture_width` | `int` | `1280` | `CAPTURE_WIDTH` | Largura alvo de captura da câmera |
| `capture_height` | `int` | `720` | `CAPTURE_HEIGHT` | Altura alvo de captura da câmera |
| `jpeg_quality` | `int` | `85` | `JPEG_QUALITY` | Qualidade de codificação JPEG do frame publicado (1–100) |
| `brightness` | `int` | `128` | — | Valor de brilho da câmera via `cv2.CAP_PROP_BRIGHTNESS` (0–255) |
| `exposure` | `int` | `-5` | — | Valor de exposição da câmera via `cv2.CAP_PROP_EXPOSURE` (-13 a -1 em macOS) |
| `autofocus` | `bool` | `true` | — | Liga/desliga autofoco via `cv2.CAP_PROP_AUTOFOCUS` |

**Validações**:
- `confidence_threshold`: 0.01 ≤ valor ≤ 0.99
- `jpeg_quality`: 1 ≤ valor ≤ 100
- `exposure`: -13 ≤ valor ≤ -1 (escala macOS/AVFoundation)
- `brightness`: 0 ≤ valor ≤ 255

---

## Entidade 4: HealthStatus

Snapshot do estado operacional retornado por `GET /health`.

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | `enum` | `"ok"` \| `"reconnecting"` \| `"degraded"` |
| `uptime_seconds` | `float` | Segundos desde o início do processo |
| `fps_measured` | `float` | FPS médio dos últimos 30 frames |
| `fps_below_threshold` | `bool` | `true` se `fps_measured` < 24.0 |
| `camera_connected` | `bool` | `true` se a câmera está acessível |
| `inference_ok` | `bool` | `true` se a última inferência foi bem sucedida |
| `frames_published` | `int` | Total de frames publicados via ZMQ desde o start |
| `config` | `ServiceConfig` | Configuração ativa no momento |

### Transições de Estado

```
ok  ──[câmera desconectada]──►  reconnecting  ──[câmera reconectada]──►  ok
ok  ──[FPS < 24 por > 10s]───►  degraded      ──[FPS ≥ 24 por > 5s]───►  ok
```

---

## Diagrama de Relacionamento

```
ServiceConfig  ←──(carregada por)──  main.py
     │
     └──configura──► CameraCapture  ──cap→frame──► YOLOInference
                                                        │
                                                   detections[]
                                                        │
                                     FrameAnnotator ◄──┘
                                          │
                                     frame_annotated
                                          │
                                    ZMQPublisher
                                          │
                               [frame_jpeg | FrameMetadata JSON]
                                          │
                                    ──ZMQ PUSH──►  Backend (consumidor)
```
