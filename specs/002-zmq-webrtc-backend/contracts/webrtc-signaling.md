# Contrato HTTP — WebRTC Backend API

**Feature**: 002-zmq-backend  
**Serviço**: `backend`  
**Base URL**: `http://127.0.0.1:8080` (configurável via `HTTP_PORT`)  
**Date**: 2026-03-08

---

## Visão Geral

O backend expõe dois endpoints HTTP:

| Endpoint | Método | Propósito |
|---|---|---|
| `/offer` | POST | Sinalização WebRTC: recebe SDP offer, retorna SDP answer com ICE bundled |
| `/health` | GET | Monitor de saúde: estado ZMQ, peers ativos, FPS |

Não há autenticação — operação restrita à LAN cabeada (Princípio V da Constituição).

---

## POST /offer

### Propósito

Inicia uma sessão WebRTC entre o browser React e o backend. O browser envia o SDP offer gerado pelo seu `RTCPeerConnection`; o servidor cria a peer connection, anexa o stream de vídeo e retorna o SDP answer com todos os ICE candidates já bundled.

### Request

**Content-Type**: `application/json`

**Body**:
```json
{
  "sdp": "<SDP offer string gerado pelo browser>",
  "type": "offer"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `sdp` | string | sim | SDP offer completo gerado por `RTCPeerConnection.createOffer()` |
| `type` | `"offer"` | sim | Fixo; qualquer outro valor retorna HTTP 422 |

### Response

**Status 200 OK**  
**Content-Type**: `application/json`

```json
{
  "sdp": "<SDP answer com ICE candidates bundled>",
  "type": "answer"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `sdp` | string | SDP answer com todos os ICE host candidates incluídos |
| `type` | `"answer"` | Sempre `"answer"` |

### Fluxo completo de sinalização

```
Browser React                          backend
     │                                       │
     │  1. const pc = new RTCPeerConnection()│
     │  2. const offer = await pc.createOffer│
     │  3. await pc.setLocalDescription(offer│
     │                                       │
     │── POST /offer { sdp, type:"offer" } ─►│
     │                                       │  4. setRemoteDescription(offer)
     │                                       │  5. addTrack(QueuedVideoTrack)
     │                                       │  6. answer = createAnswer()
     │                                       │  7. setLocalDescription(answer)
     │                                       │  8. aguarda ICE gathering completo
     │                                       │     (candidatos host em LAN: ~50-200ms)
     │◄── 200 { sdp, type:"answer" } ────────│
     │                                       │
     │  9. await pc.setRemoteDescription(ans) │
     │ 10. ICE connectivity check (LAN ~100ms│
     │ 11. stream de vídeo começa fluir       │
```

### Erros

| Status | Condição |
|---|---|
| 422 Unprocessable Entity | Body inválido (campos ausentes, tipo≠"offer") |
| 504 Gateway Timeout | ICE gathering não completou em 3 segundos |
| 503 Service Unavailable | Serviço ainda inicializando |

---

## GET /health

### Propósito

Retorna snapshot do estado operacional do backend. Usado pelo operador e pelo supervisord para verificar se o serviço está saudável durante os 8h de demo.

### Request

Sem parâmetros, sem body.

### Response

**Status 200 OK** (sempre — mesmo em estado degraded)  
**Content-Type**: `application/json`

```json
{
  "status": "ok",
  "zmq_connected": true,
  "peers_active": 1,
  "fps_recent": 27.4,
  "fps_below_threshold": false,
  "frames_received": 98412,
  "frames_distributed": 98410,
  "uptime_seconds": 3600.4
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | `"ok"` \| `"degraded"` | `"ok"` se ZMQ ativo com frame recente; `"degraded"` caso contrário |
| `zmq_connected` | boolean | `true` se frame recebido do ZMQ nos últimos 2 segundos |
| `peers_active` | integer | Número de PeerSessions em estado `"connected"` |
| `fps_recent` | number | Último `fps_measured` recebido nos metadados ZMQ do service; `0.0` se nenhum frame recebido |
| `fps_below_threshold` | boolean | `true` se `fps_recent < 24.0` — indica violação do Princípio IV (alerta para operador) |
| `frames_received` | integer | Total de frames recebidos do ZMQ desde o start do processo |
| `frames_distributed` | integer | Total de frames distribuídos para peers WebRTC |
| `uptime_seconds` | number | Segundos desde o start do processo |

**Exemplo — estado degraded (ZMQ publisher ausente)**:
```json
{
  "status": "degraded",
  "zmq_connected": false,
  "peers_active": 0,
  "fps_recent": 0.0,
  "fps_below_threshold": true,
  "frames_received": 0,
  "frames_distributed": 0,
  "uptime_seconds": 12.3
}
```

**Exemplo — operação normal com 2 peers**:
```json
{
  "status": "ok",
  "zmq_connected": true,
  "peers_active": 2,
  "fps_recent": 28.1,
  "fps_below_threshold": false,
  "frames_received": 12048,
  "frames_distributed": 24096,
  "uptime_seconds": 402.0
}
```

> Nota: `frames_distributed` pode ser 2× `frames_received` quando há 2 peers ativos, porque cada frame é entregue a cada peer.

---

## Headers CORS

O backend **deve** incluir os seguintes headers CORS para permitir que o frontend React (que pode rodar em porta diferente durante desenvolvimento) acesse os endpoints:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

> Para a demo em produção (mesmo host), CORS é dispensável mas não prejudica.

---

## Variáveis de Ambiente de Configuração

| Variável | Padrão | Descrição |
|---|---|---|
| `ZMQ_ENDPOINT` | `tcp://127.0.0.1:5555` | Endereço do socket PULL para conectar ao service |
| `HTTP_PORT` | `8080` | Porta HTTP do backend (diferente de 8000 do service) |
| `HTTP_HOST` | `0.0.0.0` | Host de escuta |
| `ICE_TIMEOUT` | `3.0` | Timeout (segundos) para ICE gathering no POST /offer |
| `ZMQ_CONNECTED_THRESHOLD_S` | `2.0` | Janela em segundos para considerar ZMQ "conectado" no health |
| `LOG_LEVEL` | `INFO` | Nível de log (DEBUG, INFO, WARNING, ERROR) |
