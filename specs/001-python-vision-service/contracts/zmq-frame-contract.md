# Contrato ZMQ: Vision Service → Backend

**Feature**: 001-python-service  
**Date**: 2026-03-08  
**Socket Pattern**: PUSH (serviço) → PULL (backend)  
**Protocolo**: TCP, bind no serviço, connect no consumidor

---

## Endereço Padrão

| Parâmetro | Valor |
|---|---|
| Bind (serviço) | `tcp://0.0.0.0:5555` |
| Connect (backend) | `tcp://127.0.0.1:5555` |
| Configurável via | `ZMQ_ENDPOINT` env var |

---

## Formato da Mensagem (Multipart)

Cada mensagem é composta por exatamente **2 frames ZMQ**:

```
Frame 0:  [bytes]  — JPEG do frame de vídeo anotado
Frame 1:  [bytes]  — JSON UTF-8 com metadados de detecção
```

Ambos chegam atomicamente — o consumidor recebe os 2 frames ou nenhum.

---

## Esquema JSON (Frame 1)

```json
{
  "frame_id": 1042,
  "timestamp_iso": "2026-03-08T14:32:11.847Z",
  "timestamp_ms": 1741441931847,
  "fps_measured": 27.4,
  "width": 1280,
  "height": 720,
  "person_count": 2,
  "inference_error": false,
  "detections": [
    {
      "class_name": "person",
      "class_id": 0,
      "confidence": 0.91,
      "bbox": {
        "x": 312,
        "y": 88,
        "width": 180,
        "height": 420
      }
    },
    {
      "class_name": "person",
      "class_id": 0,
      "confidence": 0.76,
      "bbox": {
        "x": 640,
        "y": 110,
        "width": 155,
        "height": 390
      }
    }
  ]
}
```

---

## Casos Especiais

### Nenhuma detecção no frame
```json
{
  "frame_id": 1043,
  "timestamp_iso": "2026-03-08T14:32:11.889Z",
  "timestamp_ms": 1741441931889,
  "fps_measured": 27.3,
  "width": 1280,
  "height": 720,
  "person_count": 0,
  "inference_error": false,
  "detections": []
}
```
> O frame JPEG **ainda é publicado** — o stream nunca é interrompido por ausência de detecções.

### Falha de inferência num frame
```json
{
  "frame_id": 1044,
  "timestamp_iso": "2026-03-08T14:32:11.931Z",
  "timestamp_ms": 1741441931931,
  "fps_measured": 27.1,
  "width": 1280,
  "height": 720,
  "person_count": 0,
  "inference_error": true,
  "detections": []
}
```
> Frame JPEG do frame original **sem anotações** é publicado. O loop continua.

---

## Propriedades do Socket ZMQ

| Propriedade | Valor | Motivo |
|---|---|---|
| `SNDHWM` | `2` | Descarta frames antigos em vez de bloquear o produtor |
| `LINGER` | `0` | Fecha socket imediatamente no shutdown sem aguardar envios pendentes |
| `SNDTIMEO` | `100` ms | Timeout de envio; se consumidor der timeout, frame é descartado |

---

## Contrato HTTP — Endpoints do Serviço

O serviço expõe uma API HTTP mínima em `http://127.0.0.1:8000` (configurável via `HTTP_PORT`).

### GET /health

**Resposta 200 OK**:
```json
{
  "status": "ok",
  "uptime_seconds": 3600.4,
  "fps_measured": 27.4,
  "fps_below_threshold": false,
  "camera_connected": true,
  "inference_ok": true,
  "frames_published": 98412,
  "config": {
    "camera_device_index": 1,
    "zmq_endpoint": "tcp://0.0.0.0:5555",
    "confidence_threshold": 0.5,
    "capture_width": 1280,
    "capture_height": 720
  }
}
```

### POST /config

**Request body** (todos os campos são opcionais — apenas os enviados são alterados):
```json
{
  "confidence_threshold": 0.35,
  "brightness": 140,
  "exposure": -6,
  "autofocus": false
}
```

**Resposta 200 OK** — retorna o `ServiceConfig` completo após a alteração:
```json
{
  "camera_device_index": 1,
  "zmq_endpoint": "tcp://0.0.0.0:5555",
  "yolo_model_path": "yolov8n.pt",
  "confidence_threshold": 0.35,
  "inference_width": 640,
  "inference_height": 480,
  "capture_width": 1280,
  "capture_height": 720,
  "jpeg_quality": 85,
  "brightness": 140,
  "exposure": -6,
  "autofocus": false
}
```

**Resposta 422 Unprocessable Entity** — campo inválido:
```json
{
  "detail": [
    {
      "loc": ["body", "confidence_threshold"],
      "msg": "ensure this value is less than or equal to 0.99",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## Consumidor de Referência (Python Mínimo)

```python
import zmq, json, cv2, numpy as np

ctx = zmq.Context()
sock = ctx.socket(zmq.PULL)
sock.connect("tcp://127.0.0.1:5555")

while True:
    frame_bytes, meta_bytes = sock.recv_multipart()
    meta = json.loads(meta_bytes)
    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
    print(f"frame_id={meta['frame_id']} persons={meta['person_count']} fps={meta['fps_measured']:.1f}")
    cv2.imshow("Vision Service", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```
