# Tasks: Backend ZMQ → WebRTC

**Input**: Design documents from `/specs/002-zmq-app/backend/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: N/A — Demo-Mode (Princípio VII da Constituição)

**Organization**: Tasks agrupadas por user story para implementação e teste independentes.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências incompletas)
- **[Story]**: User story à qual a task pertence (US1, US2, US3)
- Caminhos de arquivo exatos incluídos em todas as descrições

---

## Phase 1: Setup

**Purpose**: Inicialização do projeto `backend`

- [X] T001 Criar estrutura de diretório `app/backend/` com `logs/.gitkeep` na raiz do repositório
- [X] T002 Criar `app/backend/requirements.txt` com dependências: fastapi>=0.100, uvicorn[standard]>=0.23, aiortc>=1.9, pyzmq>=25, opencv-python-headless>=4.8, numpy>=1.24, pydantic>=2.0, python-dotenv>=1.0, av>=10.0

---

## Phase 2: Foundational (Pré-requisitos Bloqueantes)

**Purpose**: Módulos de base que DEVEM existir antes de qualquer user story ser implementada

**⚠️ CRÍTICO**: Nenhum trabalho de user story pode iniciar até esta fase estar completa

- [X] T003 [P] Criar `app/backend/config.py` com `Settings` via `python-dotenv`: campos `ZMQ_ENDPOINT` (default `tcp://127.0.0.1:5555`), `HTTP_PORT` (default `8080`), `HTTP_HOST` (default `0.0.0.0`), `ICE_TIMEOUT` (default `3.0`), `ZMQ_CONNECTED_THRESHOLD_S` (default `2.0`), `LOG_LEVEL` (default `INFO`); instância singleton `settings = Settings()`
- [X] T004 [P] Criar `app/backend/models.py` com modelos Pydantic: `OfferRequest` (sdp: str, type: Literal["offer"]), `AnswerResponse` (sdp: str, type: Literal["answer"]), `HealthStatus` (status: Literal["ok","degraded"], zmq_connected: bool, peers_active: int, fps_recent: float, **fps_below_threshold: bool** (True se fps_recent < 24.0 — Princípio IV), frames_received: int, frames_distributed: int, uptime_seconds: float) — `InboundFrame` **não** deve ser criada: o pipeline passa `bytes` diretamente, a entidade é conceitual

**Checkpoint**: config.py e models.py prontos — implementação das user stories pode iniciar

---

## Phase 3: User Story 1 — Stream de Vídeo Anotado no Browser (Priority: P1) 🎯 MVP

**Goal**: Pipeline completo ZMQ PULL → FrameDistributor → QueuedVideoTrack → RTCPeerConnection → browser; o vídeo YOLO anotado é exibido no browser React com ≥ 24 FPS e latência < 300ms.

**Independent Test**: Com `service` publicando via ZMQ, iniciar `python main.py`, abrir `test.html` no browser, clicar "Conectar WebRTC", confirmar vídeo anotado fluindo com ≤ 2s de delay no estabelecimento.

### Implementation — User Story 1

- [X] T005 [P] [US1] Criar `app/backend/distributor.py` com `FrameDistributor`: dict `_sessions: dict[str, asyncio.Queue]` protegido por `asyncio.Lock`; métodos `async add_session(peer_id, queue)`, `async remove_session(peer_id)`, `async distribute(jpeg_bytes: bytes)` (fan-out via `asyncio.gather(..., return_exceptions=True)` com swap atômico `get_nowait()+put_nowait()` para `Queue(maxsize=1)`); propriedades `session_count: int`, `frames_distributed: int`, `last_frame_ts: float`
- [X] T006 [P] [US1] Criar `app/backend/webrtc_track.py` com `QueuedVideoTrack(VideoStreamTrack)`: construtor recebe `frame_queue: asyncio.Queue`; método `async recv()` chama `await self.next_timestamp()`, tenta `await asyncio.wait_for(queue.get(), timeout=0.05)`, em `TimeoutError` reutiliza `self._last_frame` (frame preto 1×1 px se não houver anterior); converte JPEG via `cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)` → `av.VideoFrame.from_ndarray(bgr, format="bgr24")` → `frame.pts = pts; frame.time_base = time_base; return frame`
- [X] T007 [US1] Criar `app/backend/zmq_subscriber.py` com `ZMQSubscriber`: construtor recebe `endpoint: str` e `distributor: FrameDistributor`; método `async start()` cria `zmq.asyncio.Context()`, socket PULL com `RCVHWM=1`, `CONFLATE=1`, chama `socket.connect(endpoint)`; loop `while True: parts = await socket.recv_multipart(); await distributor.distribute(parts[0])` — **obrigatório**: parsear também `parts[1]` como JSON (`json.loads(parts[1].decode())`) e persistir `self._last_fps_measured = meta["fps_measured"]`; em `json.JSONDecodeError` ou `KeyError`, manter valor anterior de `_last_fps_measured`; expõe `frames_received: int`, `last_recv_ts: float`, `last_fps_measured: float` (inicializado em 0.0), `is_connected: bool` (True se `time.monotonic() - last_recv_ts < threshold`)
- [X] T008 [US1] Criar `app/backend/api.py` com FastAPI app + CORS (`allow_origins=["*"]`): endpoint `POST /offer` que cria `RTCPeerConnection`, gera `peer_id = uuid4()`, cria `asyncio.Queue(maxsize=1)`, registra no `distributor`, cria `QueuedVideoTrack(queue)`, faz `pc.addTrack(track)`, `await pc.setRemoteDescription(offer)`, `await pc.createAnswer()`, `await pc.setLocalDescription(answer)`, aguarda `pc.iceGatheringState == "complete"` com `asyncio.wait_for(..., timeout=settings.ICE_TIMEOUT)`, retorna `AnswerResponse`; registra `on("connectionstatechange")` callback que chama `await distributor.remove_session(peer_id)` + `await pc.close()` quando estado for `"failed"`, `"closed"` ou `"disconnected"`
- [X] T009 [US1] Criar `app/backend/main.py` com lifespan assíncrono FastAPI: no startup, configura logging via `LOG_LEVEL`, instancia `FrameDistributor` singleton, instancia `ZMQSubscriber(settings.ZMQ_ENDPOINT, distributor)`, inicia task `asyncio.create_task(subscriber.start())`; injeta referências em `api.py` via variáveis de módulo; chama `uvicorn.run(app, host=settings.HTTP_HOST, port=settings.HTTP_PORT)` como entry point

**Checkpoint**: User Story 1 completa — stream WebRTC funcional de ponta a ponta

---

## Phase 4: User Story 2 — Resiliência a Reinício do Serviço de Visão (Priority: P2)

**Goal**: O backend sobrevive ao reinício do `service` sem intervenção manual: loop ZMQ não crasha em frames malformados, peers desconectados são liberados imediatamente, peers stale são coletados após 5 minutos.

**Independent Test**: Com stream WebRTC ativo no browser, executar `supervisorctl restart service`; o stream deve retornar automaticamente em ≤ 5 segundos sem fechar o browser.

### Implementation — User Story 2

- [X] T010 [P] [US2] Adicionar tratamento de erros no loop de recepção em `app/backend/zmq_subscriber.py`: envolver `recv_multipart()` em try/except capturando `zmq.ZMQError` (log warning, `await asyncio.sleep(0.1)`, continuar loop) e `Exception` genérica (log warning, continuar); validar `len(parts) >= 1` e `len(parts[0]) > 0` antes de chamar `distributor.distribute()`, descartando silenciosamente frames inválidos; manter `frames_received` e `last_recv_ts` atualizados apenas em frames válidos
- [X] T011 [P] [US2] Reforçar cleanup em `app/backend/api.py`: garantir que o callback `connectionstatechange` também trate `"disconnected"` com log explícito do `peer_id`; adicionar try/except ao redor do `pc.close()` no callback para evitar erro caso a conexão já esteja fechada; registrar `peer_connections: dict[str, tuple[RTCPeerConnection, float]]` em nível de módulo onde o `float` é `time.monotonic()` no momento da criação do peer — **obrigatório para TTL**: `peer_connections[peer_id] = (pc, time.monotonic())` no POST /offer
- [X] T012 [US2] Adicionar background task de TTL em `app/backend/main.py`: função `async cleanup_stale_peers()` com loop `while True: await asyncio.sleep(30); now = time.monotonic()` que itera sobre `peer_connections` e chama `await pc.close()` + remove do dict para entradas com `created_at` há mais de 300 segundos E `connectionState != "connected"`; iniciar como `asyncio.create_task(cleanup_stale_peers())` no lifespan

**Checkpoint**: User Story 2 completa — resiliência validada com restart manual do `service`

---

## Phase 5: User Story 3 — Monitoramento de Saúde e Auto-restart (Priority: P3)

**Goal**: `GET /health` retorna estado operacional completo em < 200ms; `supervisord` gerencia o processo com `autorestart=true`, garantindo operação autônoma de 8h.

**Independent Test**: Executar `curl http://localhost:8080/health` e confirmar `status: "ok"` com `zmq_connected: true`; matar o processo com `kill -9` e confirmar que o supervisor o relança em < 10 segundos.

### Implementation — User Story 3

- [X] T013 [P] [US3] Implementar `GET /health` em `app/backend/api.py`: endpoint que consulta `subscriber.is_connected`, `subscriber.frames_received`, `subscriber.last_fps_measured` (campo `fps_recent`), `distributor.session_count`, `distributor.frames_distributed`, `time.monotonic() - _start_time` para `uptime_seconds`; calcula `fps_below_threshold = subscriber.last_fps_measured < 24.0`; retorna `HealthStatus` com `status="ok"` se `zmq_connected=True`, senão `status="degraded"`; resposta sempre HTTP 200 — **restrição de performance**: endpoint não deve adquirir nenhum lock blocante; todas as leituras devem ser O(1) garantindo resposta < 200ms (SC-005)
- [X] T014 [US3] Adicionar stanza `[program:backend]` em `app/service/supervisord.conf`: `command=python main.py`, `directory=%(here)s/../backend`, `autostart=true`, `autorestart=true`, `startretries=10`, `stopwaitsecs=5`, `stdout_logfile=%(here)s/../app/backend/logs/backend.log`, `stderr_logfile=%(here)s/../app/backend/logs/backend-error.log`, `environment=PYTHONUNBUFFERED="1"`

**Checkpoint**: Todas as user stories completas — sistema pronto para demo de 8h

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificação manual e arquivo de teste manual para validação pré-feira

- [X] T015 [P] Criar `app/backend/test.html` — página HTML mínima de teste com `RTCPeerConnection` que chama `POST /offer`, exibe o stream WebRTC em `<video autoplay playsinline>` e mostra contador de FPS via `requestAnimationFrame`; arquivo standalone sem dependência de build (HTML+JS puro)

---

## Dependencies (User Story Completion Order)

```
Phase 1 (Setup)
    └── Phase 2 (Foundational: config.py + models.py)
            └── Phase 3 (US1: distributor → webrtc_track → zmq_subscriber → api → main)
                    ├── Phase 4 (US2: resilience additions — depende dos arquivos de US1)
                    └── Phase 5 (US3: /health + supervisord — depende dos singletons de US1)
                            └── Phase 6 (Polish: test.html — depende de tudo estar rodando)
```

**US1 é pré-requisito de US2 e US3** (resilience e health só fazem sentido com o pipeline funcionando). US2 e US3 são independentes entre si.

---

## Parallel Execution Examples

### Fase 2 — execução paralela (T003 ‖ T004)
```
Agent A: T003 — config.py
Agent B: T004 — models.py
```

### Fase 3 — execução parcialmente paralela
```
Sequência obrigatória:
  1. T005 ‖ T006  (distributor.py ‖ webrtc_track.py — independentes entre si, dependem só de T004)
  2. T007          (zmq_subscriber.py — depende de distributor.py de T005)
  3. T008          (api.py — depende de distributor.py, webrtc_track.py, models.py, config.py)
  4. T009          (main.py — depende de api.py e zmq_subscriber.py)
```

### Fase 4 — execução paralela (T010 ‖ T011 → T012)
```
Agent A: T010 — exception handling em zmq_subscriber.py
Agent B: T011 — cleanup reforçado em api.py
  → Ambos completos → T012 — TTL cleanup em main.py
```

### Fase 5 — execução paralela (T013 ‖ T014)
```
Agent A: T013 — GET /health em api.py
Agent B: T014 — supervisord.conf
```

---

## Implementation Strategy

**MVP = Fase 1 + Fase 2 + Fase 3 (US1)** — apenas 7 tasks (T001–T009)

Com apenas US1 completa, é possível demonstrar o stream de vídeo anotado no browser. As fases 4 e 5 adicionam robustez operacional para a demo de 8h, mas não são necessárias para validar o pipeline de vídeo.

**Entrega incremental sugerida**:
1. **T001–T004** (~30min): estrutura + dependências + base models
2. **T005–T009** (~60min): pipeline completo funcionando, stream no browser
3. **T010–T012** (~20min): resiliência — testes manuais de restart
4. **T013–T014** (~20min): health check + supervisor
5. **T015** (~15min): test.html para validação pré-feira

---

## Format Validation

Confirmação de conformidade com o formato obrigatório (`- [ ] [TaskID] [P?] [Story?] Descrição com file path`):

| Task | Checkbox | ID | [P] | [Story] | File path |
|---|---|---|---|---|---|
| T001 | ✅ | ✅ | — | — | ✅ `app/backend/` |
| T002 | ✅ | ✅ | — | — | ✅ `app/backend/requirements.txt` |
| T003 | ✅ | ✅ | ✅ | — | ✅ `app/backend/config.py` |
| T004 | ✅ | ✅ | ✅ | — | ✅ `app/backend/models.py` |
| T005 | ✅ | ✅ | ✅ | ✅ US1 | ✅ `app/backend/distributor.py` |
| T006 | ✅ | ✅ | ✅ | ✅ US1 | ✅ `app/backend/webrtc_track.py` |
| T007 | ✅ | ✅ | — | ✅ US1 | ✅ `app/backend/zmq_subscriber.py` |
| T008 | ✅ | ✅ | — | ✅ US1 | ✅ `app/backend/api.py` |
| T009 | ✅ | ✅ | — | ✅ US1 | ✅ `app/backend/main.py` |
| T010 | ✅ | ✅ | ✅ | ✅ US2 | ✅ `app/backend/zmq_subscriber.py` |
| T011 | ✅ | ✅ | ✅ | ✅ US2 | ✅ `app/backend/api.py` |
| T012 | ✅ | ✅ | — | ✅ US2 | ✅ `app/backend/main.py` |
| T013 | ✅ | ✅ | ✅ | ✅ US3 | ✅ `app/backend/api.py` |
| T014 | ✅ | ✅ | — | ✅ US3 | ✅ `app/service/supervisord.conf` |
| T015 | ✅ | ✅ | ✅ | — | ✅ `app/backend/test.html` |

**Total de tasks**: 15  
**US1**: 5 tasks (T005–T009)  
**US2**: 3 tasks (T010–T012)  
**US3**: 2 tasks (T013–T014)  
**Setup/Foundational/Polish**: 5 tasks (T001–T004, T015)  
**Oportunidades de paralelismo**: 5 pares (T003‖T004, T005‖T006, T010‖T011, T013‖T014, T015 independente)  
**Testes automatizados**: 0 (Demo-Mode — Princípio VII ✅)
