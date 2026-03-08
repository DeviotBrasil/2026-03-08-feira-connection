# Tasks: Frontend React — Visualização de Vídeo WebRTC

**Input**: Design documents from `/specs/003-video-frontend/`  
**Branch**: `003-video-frontend`  
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/frontend-serving.md ✅  
**Tests**: N/A — Demo-Mode (Princípio VII da Constituição)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Pode ser executada em paralelo (arquivos distintos, sem dependências incompletas)
- **[Story]**: User story a que pertence (US1, US2, US3)
- Todos os caminhos de arquivo são absolutos a partir da raiz do repositório

---

## Phase 1: Setup — Scaffolding do Projeto

**Purpose**: Criar toda a estrutura de arquivos do frontend a partir do zero.

- [x] T001 Inicializar projeto Vite com template React + TypeScript em `app/frontend/` (`npm create vite@latest frontend -- --template react-ts`)
- [x] T002 [P] Configurar `app/frontend/vite.config.ts`: `base: '/'`, `outDir: 'dist'`, proxy de dev `/offer` e `/health` → `http://localhost:8080`
- [x] T003 [P] Substituir `app/frontend/tsconfig.json` com configuração strict (`"strict": true`, `"target": "ES2020"`, `"lib": ["ES2020","DOM","DOM.Iterable"]`)

**Checkpoint**: `cd app/frontend && npm install && npm run dev` deve abrir página em branco sem erros de compilação.

---

## Phase 2: Foundational — Tipos Compartilhados e Integração com o Backend

**Purpose**: Criar os tipos TypeScript que todas as stories dependem e integrar o serving estático no `backend`.

**⚠️ CRÍTICO**: Nenhuma tarefa de user story pode começar antes desta fase estar completa.

- [x] T004 Criar `app/frontend/src/types.ts` com os tipos: `ConnectionState` (union type dos 6 estados), `HealthData` (interface mapeando o modelo `HealthStatus` do `app/backend/models.py`), `StreamStats`, `BackendConfig`
- [x] T005 Integrar serving estático em `app/backend/api.py`: importar `Path`, `StaticFiles`, `FileResponse`; montar `/assets` com `StaticFiles(directory=_FRONTEND_DIST / "assets")`; adicionar catch-all `GET /{full_path:path}` retornando `_FRONTEND_DIST / "index.html"` (dentro de bloco `if _FRONTEND_DIST.exists()`)

**Checkpoint**: Após `npm run build`, `python main.py` no `app/backend/` e `GET http://localhost:8080/` deve retornar `index.html`.

---

## Phase 3: User Story 1 — Visualização do Stream de Vídeo ao Vivo (Priority: P1) 🎯 MVP

**Goal**: O browser abre `http://localhost:8080`, conecta WebRTC automaticamente e exibe o stream de vídeo anotado com bounding boxes em até 5 segundos.

**Independent Test**: Com `service` e `backend` rodando, abrir `http://localhost:8080` e confirmar que o vídeo aparece continuamente. Verificar bounding boxes visíveis quando um objeto entra no campo da câmera.

### Implementação

- [x] T006 [US1] Implementar `app/frontend/src/hooks/useWebRTC.ts`: `useRef` para `RTCPeerConnection` e `videoRef`; `connect()` async com flag `cancelled`; `addTransceiver('video', { direction: 'recvonly' })`; `createOffer` → `setLocalDescription`; `POST /offer` com `fetch`; `setRemoteDescription(answer)`; `ontrack` atribuindo `event.streams[0]` (ou `new MediaStream([event.track])`) a `videoRef.current.srcObject`; retornar `{ videoRef, connectionState }`; cleanup no unmount (null handlers → stop receivers → stop transceivers → `pc.close()` → null `srcObject`)
- [x] T007 [P] [US1] Criar `app/frontend/src/components/VideoPlayer.tsx`: aceita `videoRef: RefObject<HTMLVideoElement>`; renderiza `<video ref={videoRef} autoPlay muted playsInline style={{ width: '100%', maxHeight: '100vh', objectFit: 'contain', background: '#000' }} />`
- [x] T008 [P] [US1] Criar `app/frontend/src/main.tsx`: `ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)`
- [x] T009 [US1] Criar `app/frontend/src/App.tsx`: resolver `BackendConfig` de `new URLSearchParams(window.location.search).get('backend') ?? window.location.origin`; chamar `useWebRTC(backendUrl)`; renderizar `<VideoPlayer videoRef={videoRef} />`; layout CSS fullscreen escuro

**Checkpoint**: US1 funcional e testável de forma independente. O vídeo é exibido ao vivo ao abrir `http://localhost:8080`.

---

## Phase 4: User Story 2 — Indicadores de Status da Conexão e do Sistema (Priority: P2)

**Goal**: O operador visualiza na tela: contador de FPS, status colorido da conexão WebRTC, métricas do `/health` (status ZMQ, peers, FPS do backend) e alerta vermelho quando o service para de publicar.

**Independent Test**: Com o stream ativo, verificar contador de FPS ≥ 24 na tela. Parar o `service` e confirmar que o alerta ZMQ aparece em vermelho em até 10 segundos.

### Implementação

- [x] T010 [P] [US2] Criar `app/frontend/src/hooks/useHealthPolling.ts`: `setInterval` a cada 5000ms chamando `GET {backendUrl}/health`; retornar `HealthData | null`; `clearInterval` no unmount; tratar erros de fetch silenciosamente (retornar `null` em falha)
- [x] T011 [P] [US2] Criar `app/frontend/src/components/StatusBar.tsx`: aceita `connectionState: ConnectionState` e `health: HealthData | null`; badge colorido (cinza=`idle`/`connecting`, verde=`connected`, amarelo=`disconnected`, vermelho=`failed`/`reconnecting`); alerta em bloco vermelho quando `health?.status === 'degraded'` ou `health?.zmq_connected === false`
- [x] T012 [P] [US2] Criar `app/frontend/src/components/HealthPanel.tsx`: aceita `health: HealthData | null`; exibe tabela com campos: Status, ZMQ, Peers ativos, FPS (backend), Uptime; "Carregando..." enquanto `health === null`; alerta de FPS baixo quando `health?.fps_below_threshold`
- [x] T013 [US2] Adicionar medição de FPS via `requestVideoFrameCallback` (com fallback `requestAnimationFrame`) em `app/frontend/src/components/VideoPlayer.tsx`: efeito separado com deps `[]`; calcular FPS a cada 1000ms; chamar prop `onFpsUpdate?: (fps: number) => void`
- [x] T014 [US2] Integrar indicadores em `app/frontend/src/App.tsx`: chamar `useHealthPolling(backendUrl)`; adicionar estado `fps`; passar `onFpsUpdate` ao `VideoPlayer`; renderizar `<StatusBar>`, overlay de FPS no canto superior direito do vídeo e `<HealthPanel>`

**Checkpoint**: US1 e US2 funcionais. Operador vê FPS, status da conexão e métricas do backend na mesma tela.

---

## Phase 5: User Story 3 — Reconexão Automática após Desconexão (Priority: P3)

**Goal**: Após reinício do `backend`, o stream é restabelecido automaticamente pelo frontend em até 10 segundos sem intervenção do operador.

**Independent Test**: Com o stream ativo, `kill` o processo do `backend` e observar que: (1) o indicador muda para "Reconectando…", (2) ao reiniciar o backend, o stream volta em ≤ 10s sem reload da página.

### Implementação

- [x] T015 [US3] Adicionar backoff exponencial em `app/frontend/src/hooks/useWebRTC.ts`: `retryDelayRef` iniciando em 2000ms, dobrando até cap de 15000ms; `retryTimerRef` para `clearTimeout` no cleanup; `scheduleReconnect()` que atualiza estado para `'reconnecting'` e agenda nova chamada a `connect()`; reset de `retryDelayRef` para 2000ms ao atingir estado `connected`
- [x] T016 [US3] Implementar zombie prevention em `app/frontend/src/hooks/useWebRTC.ts`: `mountedRef.current = false` no cleanup **antes** de qualquer `clearTimeout`; em `connect()` anular `pc.onconnectionstatechange = null` antes de `pc.close()` ao criar nova conexão; verificar `mountedRef.current` antes de qualquer `setState` em callbacks assíncronos
- [x] T017 [US3] Atualizar `app/frontend/src/components/StatusBar.tsx`: exibir texto "Reconectando…" com ícone de loading (CSS `@keyframes spin`) quando `connectionState === 'reconnecting'`; exibir mensagem "Backend indisponível — tentando reconectar" quando o estado permanecer em `reconnecting` por mais de 30s (controle via `Date.now()` no StatusBar)

**Checkpoint**: Todas as 3 user stories funcionais. Sistema opera de forma autônoma por 8 horas sem intervenção.

---

## Phase 6: Polish & Validação Final

**Purpose**: Build final, ajustes visuais e validação do quickstart.

- [x] T018 [P] Executar `cd app/frontend && npm run build` e confirmar que `app/frontend/dist/` é gerado sem erros de TypeScript; iniciar `backend` e validar `GET http://localhost:8080/` retorna o app React compilado
- [x] T019 [P] Validar fluxo completo conforme `specs/003-video-frontend/quickstart.md`: `service` em execução → `backend` em execução → `npm run build` → abrir browser → confirmar vídeo ao vivo, FPS ≥ 24, status "ok" em verde, alerta ZMQ funcional ao parar o `service`

---

## Dependencies & Execution Order

### Dependências de Fase

- **Setup (Phase 1)**: Sem dependências — pode começar imediatamente
- **Foundational (Phase 2)**: Depende de Phase 1 — **bloqueia** todas as user stories
- **US1 (Phase 3)**: Depende de Phase 2 — MVP independente
- **US2 (Phase 4)**: Depende de Phase 2; integra com US1 (adiciona indicadores ao `App.tsx` e `VideoPlayer.tsx`)
- **US3 (Phase 5)**: Depende de US1 completa (expande `useWebRTC.ts` e `StatusBar.tsx`)
- **Polish (Phase 6)**: Depende de todas as stories completas

### Dependências Entre User Stories

- **US1 (P1)**: Independente após Phase 2 — entrega o MVP completo (vídeo ao vivo)
- **US2 (P2)**: Depende de US1 estar funcional (adiciona indicadores ao layout já criado)
- **US3 (P3)**: Depende de US1 estar funcional (expande `useWebRTC.ts` com lógica de backoff)

### Oportunidades de Paralelismo

Dentro da Phase 1:
- **T002 e T003** são paralelos (arquivos distintos)

Dentro da Phase 3 (US1):
- **T007 e T008** são paralelos (arquivos distintos, sem dependências entre si)

Dentro da Phase 4 (US2):
- **T010, T011 e T012** são paralelos entre si (hooks e componentes distintos)

Dentro da Phase 6:
- **T018 e T019** podem ser executadas em sequência rápida após completar T018

---

## Exemplo de Execução Paralela — User Story 1

```bash
# Duas tarefas em paralelo (arquivos diferentes):
# Fio A:
vim app/frontend/src/hooks/useWebRTC.ts    # T006

# Fio B (ao mesmo tempo):
vim app/frontend/src/components/VideoPlayer.tsx   # T007
vim app/frontend/src/main.tsx                     # T008

# Depois (depende de T006, T007, T008 completos):
vim app/frontend/src/App.tsx               # T009
```

---

## Implementation Strategy

**MVP recomendado**: Completar Phase 1 + Phase 2 + Phase 3 (US1) para um frontend funcional mínimo que exibe o vídeo. As phases 4 e 5 são incrementos sobre o MVP.

**Entrega incremental**:

1. **Phase 1 + 2 + 3** → MVP: vídeo ao vivo sem indicadores (US1) — demonstrável ao visitante
2. **+ Phase 4** → Operacional: vídeo + painel de saúde (US1 + US2) — operador consegue monitorar
3. **+ Phase 5** → Robusto: operação autônoma por 8h (US1 + US2 + US3) — pronto para a feira

---

## Contagem de Tasks

| Fase | Tasks | User Story |
|---|---|---|
| Phase 1 — Setup | T001–T003 | — |
| Phase 2 — Foundational | T004–T005 | — |
| Phase 3 — US1 Stream | T006–T009 | US1 (P1) |
| Phase 4 — US2 Status | T010–T014 | US2 (P2) |
| Phase 5 — US3 Reconexão | T015–T017 | US3 (P3) |
| Phase 6 — Polish | T018–T019 | — |
| **Total** | **19 tasks** | 3 user stories |

**Tasks [P] (paralelizáveis)**: T002, T003, T007, T008, T010, T011, T012, T018, T019 — **9 tasks**  
**Scope do MVP** (Phase 1 + 2 + 3): **9 tasks**
