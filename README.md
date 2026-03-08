# feira-connection

Demo de visão computacional para feira — exibe ao vivo o feed de uma webcam USB com detecção de pessoas via YOLO em qualquer browser da rede local.

```
Câmera USB → service (YOLOv8n) → ZMQ → backend (FastAPI + aiortc) → WebRTC → frontend (React) → Browser
```

---

## Pré-requisitos

| Ferramenta | Versão | Uso |
|---|---|---|
| Python | 3.11+ | `app/service` e `app/backend` |
| Node.js | 18 LTS+ | Build do `app/frontend` (não precisa rodar em produção) |

Verificar:

```bash
python3 --version   # Python 3.11.x
node --version      # v18.x ou superior
npm --version       # 9.x ou superior
```

---

## Setup do ambiente

Execute o script de setup na raiz do projeto para criar os virtualenvs Python e instalar todas as dependências:

```bash
bash setup.sh
```

O script irá:
- Criar `.venv` e instalar `requirements.txt` em `app/service`
- Criar `.venv` e instalar `requirements.txt` em `app/backend`
- Executar `npm install` em `app/frontend`

---

## Projetos

| Diretório | Tecnologia | Função |
|---|---|---|
| [`app/service`](app/service/) | Python · OpenCV · YOLOv8n · ZMQ | Captura câmera, detecta pessoas, publica frames anotados |
| [`app/backend`](app/backend/) | Python · FastAPI · aiortc · ZMQ | Consome ZMQ, distribui via WebRTC, serve o frontend |
| [`app/frontend`](app/frontend/) | React 18 · TypeScript · Vite | Interface web com stream ao vivo, FPS e painel de saúde |

---

## Início rápido

### 1. Configurar o service

```bash
cd app/service
cp .env.example .env                  # ajustar CAMERA_DEVICE_INDEX se necessário
source .venv/bin/activate
python3 discover_camera.py            # descobrir índice da câmera USB
python3 main.py
```

### 2. Build do frontend (passo único, pré-demo)

```bash
cd app/frontend
npm run build                         # gera dist/ — Node não precisa ficar rodando
```

### 3. Iniciar service, backend e frontend

```bash
bash start.sh
```

O script inicia os 3 processos em background e encerra todos com um único **Ctrl+C**.

### 4. Abrir no browser

```bash
open http://localhost:5173   # frontend (Vite dev server)
```

```bash
open http://localhost:8080
# ou em outro dispositivo na LAN: http://<IP-do-servidor>:8080
```

---

## Verificação rápida

```bash
# Service publicando?
curl -s http://localhost:8000/health | python3 -m json.tool

# Backend recebendo ZMQ?
curl -s http://localhost:8080/health | python3 -m json.tool
```

---

## Especificações

Documentação técnica detalhada em [`specs/`](specs/):

- [`specs/001-python-vision-service/`](specs/001-python-vision-service/) — Serviço de visão
- [`specs/002-zmq-webrtc-backend/`](specs/002-zmq-webrtc-backend/) — Backend WebRTC
- [`specs/003-video-frontend/`](specs/003-video-frontend/) — Frontend React

