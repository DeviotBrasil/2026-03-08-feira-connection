# backend — WebRTC

Consome frames anotados do **service** via **ZMQ PULL** e os distribui em tempo real para browsers via **WebRTC** (aiortc). Também serve o build estático do frontend React.

Pipeline: `ZMQ PULL → FrameDistributor → QueuedVideoTrack → RTCPeerConnection → Browser`

---

## Pré-requisitos

- Python 3.11+
- `app/service` em execução e publicando em `tcp://127.0.0.1:5555`
- Porta `8080` disponível

---

## Instalação

```bash
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuração

Crie `.env` em `app/backend/` se precisar customizar (todos os valores têm defaults funcionais):

```env
ZMQ_ENDPOINT=tcp://127.0.0.1:5555
HTTP_PORT=8080
HTTP_HOST=0.0.0.0
ICE_TIMEOUT=3.0
LOG_LEVEL=INFO
```

---

## Execução

```bash
# Modo direto
source .venv/bin/activate
python main.py

# Via supervisord (adicionar stanza em app/service/supervisord.conf)
supervisorctl -c ../service/supervisord.conf update
```

Saída esperada:
```
INFO:     ZMQ PULL conectado em tcp://127.0.0.1:5555
INFO:     Iniciando servidor em http://0.0.0.0:8080
INFO:     Application startup complete.
```

---

## Verificação

```bash
# Health check
curl -s http://localhost:8080/health | python3 -m json.tool
```

Resposta esperada:
```json
{
  "status": "ok",
  "zmq_connected": true,
  "peers_active": 0,
  "fps_recent": 27.4,
  "frames_received": 1240,
  "uptime_seconds": 42.1
}
```

Teste WebRTC rápido sem o frontend React:

```bash
python3 -m http.server 9000 --directory .
# Abrir http://localhost:9000/test.html → clicar "Conectar WebRTC"
```

---

## Endpoints HTTP

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/offer` | Sinalização WebRTC offer/answer (SDP) |
| `GET` | `/health` | Status ZMQ, peers ativos, FPS medido |
| `GET` | `/` | Serve o frontend React (`app/frontend/dist/`) |

---