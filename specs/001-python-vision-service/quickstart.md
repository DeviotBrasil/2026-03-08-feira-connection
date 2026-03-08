# Quickstart: Serviço Python de Visão Computacional

**Feature**: 001-python-service  
**Date**: 2026-03-08  
**Plataforma**: macOS 13+ | Python 3.11+ | Logitech C925e via USB

---

## Pré-requisitos

- Python 3.11+ instalado (`python3 --version`)
- Logitech C925e conectada via USB
- macOS com permissão de câmera concedida ao Terminal / IDE

> **Permissão de câmera no macOS**: Na primeira execução, o macOS pedirá acesso à câmera.
> Se o acesso foi negado, vá em *System Settings → Privacy & Security → Camera* e habilite o Terminal.

---

## Instalação

```bash
# 1. Clone e entre no diretório do serviço
cd app/service

# 2. Crie e ative o virtualenv
python3 -m venv .venv
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Baixe o modelo YOLO (primeira vez apenas — armazenado localmente)
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

---

## Descobrir o Índice da Câmera

No macOS, câmeras são acessadas por índice numérico (não por `/dev/videoX`).
A câmera interna do MacBook tipicamente é índice `0`; a C925e USB será `1` ou `2`.

```bash
# Script de descoberta incluído no projeto
python3 -c "
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f'Índice {i}: câmera disponível ({int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))})')
        cap.release()
    else:
        print(f'Índice {i}: não disponível')
"
```

Exemplo de saída esperada com MacBook + C925e:
```
Índice 0: câmera disponível (1280x720)   ← webcam interna
Índice 1: câmera disponível (1280x720)   ← Logitech C925e ✅
Índice 2: não disponível
```

---

## Configuração

Crie um arquivo `.env` (ou defina variáveis de ambiente):

```bash
# .env — copiar de .env.example
CAMERA_DEVICE_INDEX=1          # índice da C925e descoberto acima
ZMQ_ENDPOINT=tcp://0.0.0.0:5555
YOLO_MODEL_PATH=yolov8n.pt
CONFIDENCE_THRESHOLD=0.5
CAPTURE_WIDTH=1280
CAPTURE_HEIGHT=720
INFERENCE_WIDTH=640
INFERENCE_HEIGHT=480
HTTP_PORT=8000
```

---

## Rodando o Serviço

```bash
# Modo desenvolvimento (com logs no terminal)
source .venv/bin/activate
python3 main.py

# Saída esperada:
# [INFO] Camera opened: index=1 (1280x720)
# [INFO] YOLO model loaded: yolov8n.pt (device=mps)
# [INFO] ZMQ PUSH bound to tcp://0.0.0.0:5555
# [INFO] HTTP API started at http://127.0.0.1:8000
# [INFO] Stream started — 27.3 FPS
```

---

## Verificando que Funciona

### Opção 1: Consumer ZMQ de teste (outro terminal)

```bash
source .venv/bin/activate
python3 -c "
import zmq, json, cv2, numpy as np

ctx = zmq.Context()
sock = ctx.socket(zmq.PULL)
sock.connect('tcp://127.0.0.1:5555')
print('Aguardando frames...')

for _ in range(100):
    frame_bytes, meta_bytes = sock.recv_multipart()
    meta = json.loads(meta_bytes)
    print(f\"frame={meta['frame_id']:05d}  fps={meta['fps_measured']:5.1f}  pessoas={meta['person_count']}\")
"
```

Saída esperada:
```
Aguardando frames...
frame=00042  fps= 27.3  pessoas=1
frame=00043  fps= 27.4  pessoas=1
frame=00044  fps= 27.2  pessoas=0
```

### Opção 2: Health check HTTP

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

### Opção 3: Visualizar vídeo anotado localmente

```bash
source .venv/bin/activate
python3 -c "
import zmq, json, cv2, numpy as np

ctx = zmq.Context()
sock = ctx.socket(zmq.PULL)
sock.connect('tcp://127.0.0.1:5555')

while True:
    frame_bytes, _ = sock.recv_multipart()
    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
    cv2.imshow('Vision Service — Aperte Q para sair', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
"
```

---

## Ajuste de Câmera em Runtime

Sem reiniciar o serviço, ajuste os parâmetros de captura:

```bash
# Aumentar brilho (útil em pavilhão com iluminação fraca)
curl -s -X POST http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"brightness": 160}' | python3 -m json.tool

# Reduzir threshold de confiança (detectar mais objetos com menor certeza)
curl -s -X POST http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"confidence_threshold": 0.35}' | python3 -m json.tool

# Ajustar exposição manualmente (desabilita autoexposição)
curl -s -X POST http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"exposure": -7}' | python3 -m json.tool
```

---

## Modo Produção (Feira) com supervisord

```bash
# Instalar supervisord (já incluso em requirements.txt)
# Iniciar com auto-restart habilitado
supervisord -c supervisord.conf

# Verificar status
supervisorctl -c supervisord.conf status

# Parar
supervisorctl -c supervisord.conf stop service
```

O `supervisord.conf` configura `autorestart=true` com `stopwaitsecs=5` — se o processo
cair por qualquer motivo, reinicia automaticamente em < 5 segundos.

---

## Solução de Problemas

| Problema | Causa Provável | Solução |
|---|---|---|
| `cv2.VideoCapture(1)` retorna False | C925e não detectada | Verificar USB; executar script de descoberta de índice |
| Permissão negada à câmera | macOS bloqueou acesso | System Settings → Privacy & Security → Camera → habilitar Terminal |
| FPS abaixo de 24 | CPU sobrecarregado ou resolução alta | Reduzir `INFERENCE_WIDTH/HEIGHT` para 320×240; ou verificar processos pesados rodando |
| ZMQ sem mensagens no consumer | Serviço ainda não iniciou ou porta errada | Verificar `curl /health`; conferir `ZMQ_ENDPOINT` nos dois lados |
| YOLO carregando devagar (primeira vez) | Download do modelo | Modelo baixado para `~/.ultralytics/`; rodar `python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"` antecipadamente |
| `inference_error: true` nos metadados | Frame corrompido de câmera | Temporário; loop continua automaticamente |
