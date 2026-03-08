# Research: Backend ZMQ → WebRTC

**Feature**: 002-zmq-backend  
**Phase**: 0 — Resolução de incógnitas técnicas  
**Date**: 2026-03-08  
**Status**: COMPLETO — sem NEEDS CLARIFICATION remanescentes

---

## D-001: Padrão de VideoStreamTrack customizado para fonte externa (aiortc)

**Contexto**: O aiortc exige que cada peer WebRTC possua um `VideoStreamTrack` cujo método `recv()` retorne um `av.VideoFrame`. A fonte dos frames é uma `asyncio.Queue` alimentada externamente pelo distribuidor ZMQ.

**Decisão**: Subclasse de `VideoStreamTrack` com `recv()` assíncrono que:
1. Chama `await self.next_timestamp()` — método da superclasse que gerencia o relógio RTP (time_base 1/90000, incremento por frame);
2. Aguarda frame da fila com `await asyncio.wait_for(queue.get(), timeout=0.05)`;
3. Em timeout (fila vazia/ZMQ lento), reutiliza o último frame válido para manter o stream contínuo;
4. Converte JPEG bytes → `av.VideoFrame` via `cv2.imdecode` + `av.VideoFrame.from_ndarray()`.

**Rationale**:
- `next_timestamp()` é o mecanismo canônico do aiortc para timing de RTP; usar `pts` manual causaria descontinuidades;
- `cv2.imdecode()` é O(n) pixels e já é dependência da feature; evita overhead de inicializar um `av.Container` por frame;
- Reutilizar último frame é exigência da spec (FR-003): stream não pode travar mesmo que ZMQ momentaneamente não entregue;
- `timeout=0.05s` (~2× intervalo a 30fps) é suficiente para detectar ZMQ lento sem gerar latência percebível.

**Alternativas rejeitadas**:
- `queue.get_nowait()` — lança exceção em fila vazia, sem mecanismo de fallback;
- `av.open(io.BytesIO(...))` por frame — inicializa container PyAV a cada frame (~10× mais lento que imdecode);
- `pts` manual com `time.time()` — causa jitter de RTP, degradando qualidade WebRTC.

---

## D-002: Sinalização WebRTC offer/answer com ICE bundled (sem trickle ICE)

**Contexto**: O browser React envia um SDP offer via HTTP POST. O servidor deve responder com um SDP answer contendo os ICE candidates já bundled, evitando a complexidade de trickle ICE (que exigiria WebSocket bidirecional).

**Decisão**: Após `setLocalDescription(answer)`, aguardar o evento `icegatheringstatechange` com timeout de 3 segundos. Retornar `pc.localDescription` somente após `iceGatheringState == "complete"`.

Fluxo:
```
POST /offer (browser SDP offer)
  → setRemoteDescription(offer)
  → addTrack(VideoStreamTrack)
  → createAnswer()
  → setLocalDescription(answer)          ← ICE gathering inicia aqui
  → aguardar event iceGatheringState == "complete" (timeout 3s)
  → retornar { sdp: pc.localDescription.sdp, type: "answer" }
```

**Rationale**:
- Em LAN cabeada (Princípio V da Constituição), ICE gathering com candidatos host completa em ~50–200ms — bem dentro do timeout de 3s;
- Resposta única simplifica drasticamente o frontend React (nenhum mecanismo de trickle necessário);
- STUN/TURN desnecessários: todos os hosts estão na mesma LAN sem NAT.

**Alternativas rejeitadas**:
- Trickle ICE — requer WebSocket ou SSE bidirecional; complexidade desproporcional para LAN;
- `asyncio.sleep(0.5)` fixo — frágil; pode retornar antes de gathering completo em CPU carregada;
- STUN/TURN — overhead desnecessário, proibido por Princípio V (sem APIs externas em runtime).

---

## D-003: Consumo ZMQ PULL assíncrono com descarte de backlog

**Contexto**: O serviço de visão usa `PUSH bind` em `tcp://0.0.0.0:5555`. O backend deve usar `PULL connect` em `tcp://127.0.0.1:5555`. O backend é mais lento que o produtor (WebRTC encoding vs. JPEG publish) — precisa sempre processar o frame mais recente.

**Decisão**: `zmq.asyncio.Context()` com socket PULL, `RCVHWM=1` e `CONFLATE=1`. Socket **connect** (não bind) para `tcp://127.0.0.1:5555` (conforme contrato ZMQ da feature 001).

Propriedades do socket PULL:
| Propriedade | Valor | Motivo |
|---|---|---|
| `RCVHWM` | `1` | Buffer de recepção de 1 mensagem |
| `CONFLATE` | `1` | Mantém apenas o frame mais recente; descarta anteriores |
| `RCVTIMEO` | `-1` | Sem timeout (recv_multipart assíncrono nunca bloqueia no asyncio) |

**Rationale**:
- `CONFLATE=1` é a solução canônica ZMQ para "always latest message": o socket mantém apenas 1 mensagem na fila de recepção, descartando silenciosamente as anteriores;
- `zmq.asyncio` integra o socket no event loop via epoll/kqueue — sem threads extras, sem bloqueio;
- ZMQ gerencia reconexão automática no nível de transporte quando o PUSH publisher reinicia; nenhuma lógica de reconexão manual necessária (FR-006 resolvido gratuitamente pelo protocolo).

**Alternativas rejeitadas**:
- Socket PULL sem `CONFLATE` — acumula frames no buffer, causando latência crescente;
- Thread bloqueante com `sock.recv_multipart()` — exige sincronização adicional com a asyncio loop;
- Polling com `poller.poll(timeout=100)` — complexidade desnecessária quando `zmq.asyncio` existe.

---

## D-004: Fan-out de frames para múltiplos peers WebRTC

**Contexto**: Até 2 browsers podem conectar simultaneamente. Cada `VideoStreamTrack` (um por peer) precisa do frame mais recente. Peers lentos não podem bloquear peers rápidos (sem head-of-line blocking).

**Decisão**: `FrameDistributor` — classe singleton com `dict[str, asyncio.Queue]` (peer_id → queue, maxsize=1). No broadcast, para cada peer: se fila cheia, `get_nowait()` descarta o frame antigo antes de `put_nowait()` novo.

Propriedades:
- Dicionário protegido por `asyncio.Lock()` nas operações de subscribe/unsubscribe;
- `asyncio.gather(*broadcast_tasks, return_exceptions=True)` para fan-out paralelo sem travar em peer lento;
- `asyncio.Queue(maxsize=1)` por peer: sempre contém no máximo 1 frame pendente.

**Rationale**:
- `asyncio.Queue(maxsize=1)` + swap atômico garante latência mínima por peer independente;
- A operação `get_nowait()` + `put_nowait()` é atomicamente segura no asyncio (single-threaded event loop);
- Lock apenas nas operações de add/remove, não no hot path de broadcast, minimizando overhead.

**Alternativas rejeitadas**:
- Fila global compartilhada — peer lento bloqueia todos os outros;
- asyncio.Event por peer — não armazena o frame, exige leitura síncrona; mais complexo;
- Redis pub/sub — overhead de rede e processo desnecessário; somos single-node.

---

## D-005: Detecção de peer desconectado e cleanup de recursos

**Contexto**: Browsers podem desconectar abrindo/fechando aba, queda de rede, ou crash. O backend deve limpar recursos (RTCPeerConnection, VideoStreamTrack, asyncio.Queue) sem vazamentos de memória durante 8h de demo.

**Decisão**: Callback no evento `connectionstatechange` do `RTCPeerConnection`. Estados que disparam cleanup: `"failed"`, `"closed"`, `"disconnected"`. Adicionalmente, task background de cleanup de peers stale com TTL de 5 minutos (guarda-costas contra crash sem evento).

**Rationale**:
- `connectionstatechange` é o mecanismo oficial aiortc para ciclo de vida de peer;
- TTL de 5min como backup trata crashes de browser que não disparam o evento;
- `pc.close()` libera RTP sockets, threads internas do aiortc e callbacks pendentes.

**Alternativas rejeitadas**:
- Polling de `pc.connectionState` — overhead constante, mesmo resultado;
- Apenas TTL sem callback — fecha peers ativos prematuramente se soak test durar > 5min.

---

## D-006: Estrutura de diretório do novo serviço

**Contexto**: O projeto já tem `app/service/` na raiz. O novo serviço é independente (processo separado, porta diferente) mas roda sob o mesmo supervisord.

**Decisão**: Novo diretório `app/backend/` na raiz do repositório, paralelo a `app/service/`. Adicionar nova stanza `[program:backend]` ao `app/service/supervisord.conf` existente, pois o supervisord já gerencia o ecosistema e reaproveitar a config minimiza operação.

Estrutura:
```text
app/backend/
├── main.py              # Ponto de entrada; inicia ZMQ consumer task + Uvicorn
├── api.py               # FastAPI app: POST /offer, GET /health
├── zmq_subscriber.py    # Async PULL consumer (zmq.asyncio) + loop de recepção
├── distributor.py       # FrameDistributor: fan-out para peers ativas
├── webrtc_track.py      # QueuedVideoTrack (VideoStreamTrack customizado)
├── models.py            # Pydantic: OfferRequest, AnswerResponse, HealthStatus
├── config.py            # Config via variáveis de ambiente
├── requirements.txt     # Dependências Python
└── logs/                # Criado em runtime pelo supervisor
```

**Rationale**: Separação de processo permite restart independente via supervisord e isola dependências (aiortc não precisa de ultralytics/cv2-headless). Reutilizar supervisord.conf existente evita criar um segundo daemon supervisor.

**Alternativas rejeitadas**:
- Incorporar ao `app/service/` — mistura responsabilidades; complicaria restart independente;
- Supervisor separado para backend — dois daemons supervisord são mais complexos de operar durante demo.

---

## Sumário de Decisões

| ID | Questão | Decisão |
|---|---|---|
| D-001 | VideoStreamTrack fonte externa | `recv()` com `next_timestamp()` + cv2 imdecode + fallback último frame |
| D-002 | ICE bundling sem trickle | Aguardar evento `icegatheringstatechange == "complete"` (timeout 3s) |
| D-003 | ZMQ PULL async | `zmq.asyncio` PULL connect + `CONFLATE=1` + `RCVHWM=1` |
| D-004 | Fan-out multi-peer | `FrameDistributor` com `asyncio.Queue(maxsize=1)` por peer |
| D-005 | Cleanup de peer | Evento `connectionstatechange` + TTL 5min background task |
| D-006 | Estrutura de diretório | `app/backend/` na raiz + stanza no supervisord.conf existente |

Todas as incógnitas técnicas resolvidas. Nenhum `NEEDS CLARIFICATION` remanescente.
