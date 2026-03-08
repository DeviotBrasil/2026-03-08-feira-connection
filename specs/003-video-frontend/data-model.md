# Data Model: Frontend React — Visualização de Vídeo WebRTC

**Feature**: 003-video-frontend  
**Date**: 2026-03-08

> O frontend é estateless em relação ao servidor — não persiste dados em localStorage, IndexedDB nem cookies. Todo o estado vive em memória React durante a sessão.

---

## Entidades de Estado

### ConnectionState

Estado atual da conexão WebRTC entre o frontend e o backend.

| Valor | Descrição | Transições Permitidas |
|---|---|---|
| `idle` | Componente montado, conexão ainda não iniciada | → `connecting` |
| `connecting` | Handshake WebRTC em andamento (offer/answer) | → `connected`, `failed` |
| `connected` | Stream ativo e recebendo frames | → `disconnected`, `failed` |
| `disconnected` | ICE transitoriamente perdido (pode se auto-recuperar) | → `connected`, `failed` |
| `reconnecting` | Backend desconectado — aguardando backoff para nova tentativa | → `connecting` |
| `failed` | Conexão falhou definitivamente — nova tentativa agendada | → `reconnecting` → `connecting` |

**Diagrama de transições**:

```
idle → connecting → connected
                 ↘         ↓ (failed/disconnected)
                   failed → reconnecting → connecting
                         ↗
                 disconnected (transitório LAN — pode resolver sozinho)
```

---

### HealthData

Dados retornados pelo endpoint `GET /health` do backend. Reflete a estrutura do modelo `HealthStatus` de [models.py](../../app/backend/models.py).

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | `"ok" \| "degraded"` | Estado geral do backend |
| `zmq_connected` | `boolean` | Se o ZMQ subscriber está conectado ao service |
| `peers_active` | `number` | Número de peers WebRTC ativos no backend |
| `fps_recent` | `number` | FPS medido pelo backend no stream ZMQ recebido |
| `fps_below_threshold` | `boolean` | `true` se `fps_recent < 24.0` |
| `frames_received` | `number` | Total de frames recebidos pelo backend desde startup |
| `frames_distributed` | `number` | Total de frames distribuídos a peers desde startup |
| `uptime_seconds` | `number` | Tempo de uptime do backend em segundos |

**Estado inicial**: `null` (antes da primeira consulta ao `/health`).  
**Atualização**: polling a cada 5 segundos via `useHealthPolling`.

---

### StreamStats

Estatísticas de vídeo medidas diretamente no elemento `<video>` do browser.

| Campo | Tipo | Descrição |
|---|---|---|
| `fps` | `number` | FPS calculado via `requestVideoFrameCallback` (frames/segundo) |
| `lastFrameAt` | `number \| null` | Timestamp (ms) do último frame recebido; `null` se nenhum frame ainda |

**Atualização**: em tempo real via `requestVideoFrameCallback`, calculado a cada segundo.

---

### BackendConfig

Configuração de runtime resolvida uma única vez na inicialização do app.

| Campo | Tipo | Valor Padrão | Descrição |
|---|---|---|---|
| `url` | `string` | `window.location.origin` | URL base do backend (ex: `http://192.168.1.10:8080`) |

**Resolução**: lida do parâmetro de URL `?backend=<url>`. Se ausente, usa `window.location.origin` (funciona quando frontend é servido pelo próprio FastAPI).

---

## Relacionamentos

```text
App
├── BackendConfig (1) ────────────── lida uma vez no mount
│
├── useWebRTC (1)
│   ├── ConnectionState (1) ──────── derivado de pc.connectionState
│   └── StreamStats (1) ──────────── medido via rVFC no <video>
│
└── useHealthPolling (1)
    └── HealthData (1 | null) ────── atualizado a cada 5s
```

---

## Validações e Regras de Negócio

- `HealthData.status === "degraded"` → exibir alerta ZMQ visível (borda vermelha + mensagem).
- `HealthData.fps_below_threshold === true` → exibir aviso de FPS baixo no painel de saúde.
- `StreamStats.fps < 24` quando `ConnectionState === "connected"` → exibir aviso de FPS baixo localmente (independente do valor do backend — AC-002).
- `ConnectionState === "reconnecting"` → exibir indicador de "Reconectando..." com animação (skeleton ou spinner).
- `lastFrameAt !== null && (Date.now() - lastFrameAt) > 5000` → stream congelado; tratar como `reconnecting`.
