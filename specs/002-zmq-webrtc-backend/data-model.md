# Data Model: Backend ZMQ → WebRTC

**Feature**: 002-zmq-backend  
**Phase**: 1 — Design  
**Date**: 2026-03-08  
**Baseado em**: [research.md](research.md), [spec.md](spec.md), [contrato ZMQ 001](../001-python-app/service/contracts/zmq-frame-contract.md)

---

## Entidades

### 1. `InboundFrame` *(entidade conceitual — não é uma classe Python)*

Representa a unidade de dado recebida do socket ZMQ PULL. Conceitual: no pipeline real, o ZMQSubscriber passa `jpeg_bytes: bytes` diretamente ao `FrameDistributor` sem instanciar um objeto intermediário — evita alocação desnecessária no hot path.

| Campo | Tipo | Origem | Descrição |
|---|---|---|---|
| `jpeg_bytes` | `bytes` | ZMQ Frame 0 | Imagem JPEG do frame anotado pelo YOLO |
| `fps_measured` | `float` | ZMQ Frame 1 (JSON, `fps_measured`) | FPS medido pelo service; lido pelo subscriber e armazenado em `last_fps_measured` |

**Regras**:
- Uma mensagem ZMQ é sempre composta por exatamente 2 partes (multipart atômico); se `len(parts) < 2` ou `parts[0]` vazio, o frame é descartado silenciosamente;
- Frame 1 é parseado como JSON para extrair `fps_measured`; em `JSONDecodeError`, o valor anterior de `last_fps_measured` é mantido;
- `InboundFrame` **não existe em `models.py`** — é documentação de contrato, não código.

**Referência de contrato externo (ZMQ Frame 1)**:
O campo `fps_measured` lido pelo `ZMQSubscriber` provém do JSON publicado pelo service. Schema completo em [`specs/001-python-app/service/contracts/zmq-frame-contract.md`](../001-python-app/service/contracts/zmq-frame-contract.md).

---

### 2. `PeerSession`

Representa uma conexão WebRTC ativa com um browser cliente. Criada no `POST /offer` e destruída quando o browser desconecta.

| Campo | Tipo | Descrição |
|---|---|---|
| `peer_id` | `str` (UUID4) | Identificador único desta sessão, gerado pelo servidor |
| `pc` | `RTCPeerConnection` | Objeto aiortc que gerencia o ciclo de vida WebRTC |
| `track` | `QueuedVideoTrack` | Track de vídeo customizado para esta sessão |
| `frame_queue` | `asyncio.Queue[bytes]` | Fila de frames JPEG pendentes para este peer (maxsize=1) |
| `created_at` | `float` (monotonic) | Timestamp de criação para TTL de cleanup |
| `state` | `str` | Espelha `pc.connectionState` para acesso rápido |

**Estados de ciclo de vida**:
```
new → connecting → connected → (disconnected | failed | closed)
```

**Transições**:
- `new → connecting`: browser recebe SDP answer e inicia ICE;
- `connecting → connected`: handshake ICE completo; frames começam a fluir;
- `connected → disconnected`: browser perdeu conectividade (rede instável);
- `* → failed`: ICE falhou definitivamente;
- `* → closed`: `pc.close()` chamado (cleanup explícito ou TTL).

**Regras**:
- Ao entrar em `disconnected`, `failed` ou `closed` — cleanup **imediato**: remover do `FrameDistributor`, chamar `pc.close()`;
- TTL: sessão destroyed se `state != "connected"` por mais de 5 minutos;
- `frame_queue` tem `maxsize=1`; frame antigo é descartado se peer estiver lento.

---

### 3. `FrameDistributor`

Singleton que recebe `jpeg_bytes: bytes` do `ZMQSubscriber` e os distribui para todas as peer queues ativas.

| Campo | Tipo | Descrição |
|---|---|---|
| `_sessions` | `dict[str, asyncio.Queue]` | Mapa de peer_id → `Queue(maxsize=1)` de frames JPEG pendentes para cada peer ativo |
| `_lock` | `asyncio.Lock` | Protege operações de add/remove de sessões |
| `_frames_distributed` | `int` | Contador de frames distribuídos desde o start |
| `_last_frame_ts` | `float` | Timestamp do último frame distribuído (para health check) |

**Operações**:

| Método | Assinatura | Descrição |
|---|---|---|
| `add_session` | `async (peer_id: str, queue: asyncio.Queue) → None` | Registra fila de novo peer para receber frames |
| `remove_session` | `async (peer_id: str) → None` | Desregistra peer e libera sua fila |
| `distribute` | `async (jpeg_bytes: bytes) → None` | Fan-out: entrega JPEG para todos os peers ativos |
| `session_count` | `int` (property) | Número de peers ativos no momento |

**Regras de distribute**:
- Se a `frame_queue` do peer está cheia (frame anterior não consumido): `get_nowait()` descarta o frame antigo, depois `put_nowait()` insere o novo;
- Todas as entregas paralelas via `asyncio.gather(..., return_exceptions=True)` — uma falha não bloqueia as demais;
- Sem frames distribuídos não significa parada — o distribuidor continua aguardando novos frames.

---

### 4. `ZMQSubscriber`

Gerencia o socket ZMQ PULL e executa o loop de recepção assíncrono. Singleton; roda como asyncio Task durante toda a vida do processo.

| Campo | Tipo | Descrição |
|---|---|---|
| `_endpoint` | `str` | Endereço de conexão (ex: `tcp://127.0.0.1:5555`) |
| `_distributor` | `FrameDistributor` | Referência ao distribuidor para entrega dos frames |
| `_socket` | `zmq.asyncio.Socket` | Socket PULL assíncrono |
| `_connected` | `bool` | Indica se houve recepção recente: `True` se `time.monotonic() - _last_recv_ts < threshold` |
| `_frames_received` | `int` | Contador total de frames recebidos |
| `_last_recv_ts` | `float` | Timestamp do último frame recebido (monotonic) |
| `_last_fps_measured` | `float` | Último `fps_measured` extraído do Frame 1 JSON; inicializado em `0.0` |

**Parâmetros do socket**:
| Opção ZMQ | Valor | Motivo |
|---|---|---|
| `RCVHWM` | `1` | 1 mensagem no buffer de recepção |
| `CONFLATE` | `1` | Descarta frames antigos; mantém apenas o mais recente |
| Padrão | `PULL` | Consumidor no padrão PUSH/PULL conforme contrato 001 |
| Topologia | `connect` | Conecta ao publisher; nunca bind |

**Regras**:
- O socket **conecta** (não faz bind) ao endereço do publisher — exatamente o oposto do PUSH que usa bind;
- ZMQ gerencia reconexão de transporte automaticamente se o publisher reiniciar; nenhum código de reconexão manual necessário;
- `_connected` é considerado `True` se `_last_recv_ts` foi atualizado nos últimos 2 segundos;
- Loop nunca termina — apenas se o processo encerra.

---

### 5. `HealthStatus` (Response Model)

Resposta do endpoint `GET /health`. Snapshot do estado operacional do backend.

| Campo | Tipo | Descrição |
|---|---|---|
| `status` | `Literal["ok", "degraded"]` | `"ok"` se ZMQ ativo e ≥ 1 frame recente; `"degraded"` caso contrário |
| `zmq_connected` | `bool` | `True` se frame recebido do ZMQ nos últimos 2 segundos |
| `peers_active` | `int` | Número de PeerSessions no estado `"connected"` |
| `fps_recent` | `float` | Último `fps_measured` recebido do ZMQ (metadados do vision service); `0.0` se nenhum frame recebido |
| `fps_below_threshold` | `bool` | `True` se `fps_recent < 24.0` — sinaliza violação do Princípio IV da Constituição |
| `frames_received` | `int` | Total de frames recebidos do ZMQ desde o start do processo |
| `frames_distributed` | `int` | Total de frames distribuídos para peers |
| `uptime_seconds` | `float` | Tempo em segundos desde o start do processo |

---

### 6. `OfferRequest` (Request Model)

Corpo do `POST /offer`. Enviado pelo browser React durante a sinalização WebRTC.

| Campo | Tipo | Descrição |
|---|---|---|
| `sdp` | `str` | SDP offer gerado pelo browser via `RTCPeerConnection.createOffer()` |
| `type` | `Literal["offer"]` | Sempre `"offer"` |

---

### 7. `AnswerResponse` (Response Model)

Resposta do `POST /offer`. Devolvida ao browser após ICE gathering completo no servidor.

| Campo | Tipo | Descrição |
|---|---|---|
| `sdp` | `str` | SDP answer gerado com ICE candidates bundled |
| `type` | `Literal["answer"]` | Sempre `"answer"` |

---

## Diagrama de Relacionamentos

```
ZMQ PUSH (service)
    │ tcp://127.0.0.1:5555 (multipart: jpeg_bytes + metadata_json)
    ▼
ZMQSubscriber (asyncio Task)
    │ InboundFrame (jpeg_bytes + metadata)
    ▼
FrameDistributor (singleton)
    ├── PeerSession[peer_id_A].frame_queue ──► QueuedVideoTrack[A] ──► RTCPeerConnection[A] ──► Browser A
    └── PeerSession[peer_id_B].frame_queue ──► QueuedVideoTrack[B] ──► RTCPeerConnection[B] ──► Browser B

FastAPI
    ├── POST /offer  ──► cria PeerSession ──► adiciona ao FrameDistributor ──► retorna AnswerResponse
    └── GET /health  ──► consulta ZMQSubscriber + FrameDistributor ──► retorna HealthStatus
```

---

## Considerações de Estado

- **Stateless a quente**: nenhum dado persiste em disco; restart do processo zera contadores e peers;
- **Sem autenticação**: rede local cabeada, única LAN — sem necessidade de autenticação nas rotas;
- **Sem banco de dados**: pipeline inteiramente em memória durante execução.
