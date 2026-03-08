# service — Visão Computacional

Captura frames da webcam USB, executa inferência **YOLOv8n** para detecção de pessoas e publica cada frame anotado via **ZMQ PUSH** para o backend.

Pipeline: `Câmera USB → OpenCV → YOLOv8n → FrameAnnotator → ZMQ PUSH`

---

## Pré-requisitos

- Python 3.11+
- Logitech C925e (ou outra webcam USB) conectada
- macOS com permissão de câmera concedida ao Terminal

---

## Instalação

```bash
cd app/service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuração

```bash
cp .env.example .env
# Editar .env para ajustar CAMERA_DEVICE_INDEX se necessário
```

Descobrir o índice correto da câmera:

```bash
python3 discover_camera.py
# Exemplo: Índice 0 = webcam interna, Índice 1 = Logitech C925e
```

Variáveis principais (`.env`):

| Variável | Padrão | Descrição |
|---|---|---|
| `CAMERA_DEVICE_INDEX` | `1` | Índice OpenCV da câmera USB |
| `ZMQ_ENDPOINT` | `tcp://0.0.0.0:5555` | Endereço de publicação ZMQ |
| `YOLO_MODEL_PATH` | `yolov8n.pt` | Modelo YOLO local |
| `CONFIDENCE_THRESHOLD` | `0.5` | Score mínimo de detecção |
| `HTTP_PORT` | `8000` | Porta da API de health/config |

---

## Execução

```bash
# Modo direto
source .venv/bin/activate
python3 main.py

# Via supervisord (auto-restart)
supervisord -c supervisord.conf
```

Saída esperada:
```
[INFO] Camera opened: index=1 (1280x720)
[INFO] YOLO model loaded: yolov8n.pt (device=mps)
[INFO] ZMQ PUSH bound to tcp://0.0.0.0:5555
[INFO] HTTP API started at http://127.0.0.1:8000
[INFO] Stream started — 27.3 FPS
```

---

## Verificação

```bash
# Health check
curl -s http://localhost:8000/health | python3 -m json.tool

# Consumer ZMQ de teste (outro terminal)
python3 zmq_consumer.py
```

---

## Endpoints HTTP

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Status do serviço, FPS e estado da câmera |
| `POST` | `/config` | Atualizar configurações em runtime sem restart |

