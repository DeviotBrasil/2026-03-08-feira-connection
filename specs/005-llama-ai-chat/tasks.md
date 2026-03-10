# Tasks: Chat de IA Generativa com Llama 3.1

**Input**: Design documents from `/specs/005-llama-ai-chat/`
**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/chat-api.md ✅
**Branch**: `005-llama-ai-chat`
**Tests**: N/A — Demo-Mode (Princípio VII da Constitution)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Pode rodar em paralelo (arquivo diferente, sem dependências incompletas)
- **[Story]**: User story a que pertence (US1, US2, US3)
- Caminhos de arquivo sempre relativos à raiz do workspace

---

## Phase 1: Setup (Dependências e Configuração)

**Purpose**: Instalar nova dependência do backend e configurar as variáveis de ambiente para o Ollama.

- [x] T001 Adicionar `httpx>=0.25` ao `app/backend/requirements.txt`
- [x] T002 [P] Adicionar variáveis `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT` à classe `Settings` em `app/backend/config.py`

**Checkpoint**: `pip install -r requirements.txt` completa sem erros; `settings.OLLAMA_URL` acessível.

---

## Phase 2: Foundational (Modelos e Tipos Compartilhados)

**Purpose**: Criar as entidades de dados que o backend e o frontend precisam antes de qualquer user story ser implementada.

**⚠️ CRÍTICO**: Backend e frontend dependem destes modelos/tipos. Nenhuma implementação de US pode começar sem eles.

- [x] T003 Adicionar modelos Pydantic `ChatMessage` e `ChatRequest` (com validador `messages_not_empty`) em `app/backend/models.py`
- [x] T004 [P] Adicionar interfaces TypeScript `ChatMessage` e `ChatChunk` em `app/frontend/src/types.ts`

**Checkpoint**: Backend importa `ChatRequest` sem erros de importação; tipos TS compilam sem erros (`tsc --noEmit`).

---

## Phase 3: User Story 1 — Conversa básica com streaming (Priority: P1) 🎯 MVP

**Goal**: O usuário envia uma mensagem na aba Chat e recebe a resposta do Llama 3.1 em streaming progressivo na tela.

**Independent Test**: Acessar `http://localhost:5173`, clicar na aba Chat, digitar "Olá" e pressionar Enviar. Verificar que tokens aparecem progressivamente na tela sem travar o input.

### Implementação Backend (US1)

- [x] T005 [US1] Implementar endpoint `POST /chat` com `StreamingResponse` SSE em `app/backend/api.py` (depende de T003, T002)
  - Acionar `httpx.AsyncClient` em modo streaming para `{OLLAMA_URL}/api/chat`
  - Emitir eventos `data: {"content": "...", "done": false/true}\n\n`
  - Tratar `httpx.ConnectError` → evento SSE `{"error": "Ollama service unavailable", "done": true}`
  - Tratar `httpx.TimeoutException` → evento SSE `{"error": "Model response timeout", "done": true}`
  - Tratar status HTTP ≠ 200 do Ollama → evento SSE com código de erro

### Implementação Frontend (US1)

- [x] T006 [P] [US1] Criar hook `useChat.ts` em `app/frontend/src/hooks/useChat.ts` (depende de T004)
  - Estado: `messages: ChatMessage[]`, `input: string`, `streaming: boolean`
  - `sendMessage()`: valida input não-vazio → append mensagem usuário → append placeholder assistente com `streaming: true` → fetch `POST /chat` → consumir `ReadableStream` chunk a chunk → atualizar `content` do placeholder → ao `done: true`, marcar `streaming: false`
  - Tratar erro HTTP (4xx/5xx): exibir notificação via `message.error` do Ant Design
  - Tratar evento SSE com campo `error`: exibir notificação e marcar `streaming: false`
  - Auto-scroll para última mensagem via `useRef` no container de mensagens
- [x] T007 [US1] Substituir conteúdo de `app/frontend/src/pages/ChatPage.tsx` pela UI funcional de chat (depende de T006)
  - Layout: header (título "Chat IA") + área de mensagens (scroll) + área de input
  - Renderizar `messages` distinguindo visualmente `role: "user"` vs `role: "assistant"` (alinhamento, cor de fundo)
  - Exibir cursor piscante `▋` na mensagem do assistente quando `streaming: true`
  - Input: `Input.TextArea` com `autoSize`, desabilitado quando `streaming: true`
  - Botão Enviar: desabilitado quando `!input.trim() || streaming`, com `loading={streaming}`
  - Enter sem Shift envia a mensagem; Shift+Enter insere nova linha
- [x] T008 [US1] Atualizar estilos em `app/frontend/src/pages/ChatPage.module.css` (depende de T007)
  - `.container`: flex column, altura 100%, sem overflow
  - `.header`: flex row, justify-content space-between, align-center, padding
  - `.messages`: flex-grow 1, overflow-y auto, display flex, flex-direction column, gap entre mensagens, padding
  - `.userMsg`: alinhado à direita, background token de cor primária suave, border-radius, max-width 75%
  - `.assistantMsg`: alinhado à esquerda, background token neutro, border-radius, max-width 85%
  - `.inputArea`: flex row, gap, padding, border-top, align-flex-end
  - `.cursor`: animação `blink` 1s step-end infinite

**Checkpoint**: Conversa básica funciona end-to-end. Tokens do Llama aparecem progressivamente. Botão bloqueado durante geração. FR-001, FR-002, FR-003, FR-005, FR-006, FR-007, FR-009 satisfeitos.

---

## Phase 4: User Story 2 — Histórico de contexto na sessão (Priority: P2)

**Goal**: O assistente responde levando em conta as mensagens anteriores da sessão; usuário pode fazer perguntas encadeadas.

**Independent Test**: Enviar "Meu nome é João". Em seguida, enviar "Qual é o meu nome?". Verificar que a resposta menciona "João".

### Implementação Backend + Frontend (US2)

- [x] T009 [P] [US2] Garantir que `POST /chat` recebe e repassa o histórico completo de `messages[]` ao Ollama em `app/backend/api.py` (depende de T005 — verificar e validar que `messages` com múltiplos items é corretamente serializado no payload Ollama)
- [x] T010 [P] [US2] Garantir que `useChat.ts` acumula todas as mensagens trocadas no array `messages` e as inclui no body de cada `POST /chat` em `app/frontend/src/hooks/useChat.ts` (depende de T006 — verificar que o histórico completo, não só a última mensagem, é enviado)

**Checkpoint**: Após 2+ trocas de mensagem, o assistente demonstra memória de contexto. FR-004 satisfeito.

---

## Phase 5: User Story 3 — Reset da conversa (Priority: P3)

**Goal**: Botão "Nova Conversa" limpa o histórico e reinicia o contexto da sessão.

**Independent Test**: Após uma conversa, clicar em "Nova Conversa". Verificar que a área de mensagens fica vazia. Enviar nova mensagem — o assistente não referencia a conversa anterior.

### Implementação Frontend (US3)

- [x] T011 [US3] Implementar `resetConversation()` no hook `useChat.ts` em `app/frontend/src/hooks/useChat.ts` (depende de T006)
  - Limpa `messages` para `[]`
  - Limpa `input` para `""`
  - Garante `streaming: false` (cancela fetch em andamento se houver, via `AbortController`)
- [x] T012 [US3] Conectar `resetConversation()` ao botão "Nova Conversa" em `app/frontend/src/pages/ChatPage.tsx` (depende de T011)
  - Botão desabilitado quando `streaming: true`
  - Após reset, exibir estado vazio com call-to-action (ex: `Empty` do Ant Design ou mensagem de boas-vindas)

**Checkpoint**: Botão Nova Conversa visível, operacional em ≤ 2 cliques, limpa histórico completamente. FR-008 satisfeito.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Robustez, acessibilidade e consistência visual.

- [x] T013 [P] Adicionar mensagem de boas-vindas inicial no estado do hook `useChat.ts` em `app/frontend/src/hooks/useChat.ts`
  - Ex: mensagem de sistema `role: "assistant"` com `"Olá! Sou o assistente de IA da demonstração. Como posso ajudar?"` exibida ao montar o componente (não enviada ao Ollama como histórico)
- [x] T014 [P] Adicionar tratamento de erro de conexão no `POST /chat` em `app/frontend/src/hooks/useChat.ts`
  - Se `fetch` lançar `TypeError` (rede offline, backend down): exibir `message.error` do Ant Design e restaurar `streaming: false`
  - Remover o placeholder do assistente se nenhum chunk foi recebido
- [x] T015 Validar responsividade da UI de chat em `app/frontend/src/pages/ChatPage.module.css`
  - Testar em viewport 320px de largura
  - Input e botão empilham verticalmente se necessário (flex-wrap ou media query)
- [x] T016 [P] Atualizar `app/backend/main.py` para importar `httpx` somente onde necessário e verificar que o lifespan não é afetado pelo novo endpoint (verificação de regressão — endpoint de chat não deve interferir no ciclo de vida do ZMQ subscriber)
- [x] T017 [P] Atualizar `setup.sh` e `start.sh` na raiz do projeto com suporte ao Ollama
  - `setup.sh`: verificar se `ollama` está no PATH; se sim, executar `ollama pull llama3.1` caso o modelo ainda não esteja presente; exibir aviso se Ollama não estiver instalado
  - `start.sh`: iniciar `ollama serve` em background antes dos outros serviços (se Ollama estiver instalado e não estiver já rodando); incluir `OLLAMA_PID` no `stop_all`; exibir endpoint Ollama no resumo de processos

- [x] T018 [P] Criar `app/backend/knowledge_base.md` com conteúdo de demonstração (sobre o projeto, tecnologias, FAQ, limitações)
- [x] T019 [P] Criar `app/backend/rag.py` — `load_kb(path)` lê o MD para memória; `build_system_prompt()` monta o system prompt com instrução de restrição ao documento
- [x] T020 Atualizar `app/backend/config.py` — adicionar `KB_PATH: Path` apontando para `knowledge_base.md` (depende de T018, T019)
- [x] T021 Atualizar `app/backend/api.py` — injetar `build_system_prompt()` como primeira mensagem `{"role": "system"}` no payload Ollama no `POST /chat` (depende de T019, T020)
- [x] T022 Atualizar `app/backend/main.py` — chamar `load_kb(settings.KB_PATH)` no lifespan antes de injetar os singletons (depende de T019, T020)

**Checkpoint**: A feature está completa. Todos os FRs (FR-001 a FR-015) e SCs (SC-001 a SC-006) podem ser verificados manualmente. O assistente recusa perguntas fora do escopo do `knowledge_base.md`.

---

## Dependency Graph

```
T001 ──► T005 (backend endpoint)
T002 ──► T005

T003 ──► T005
T004 ──►─────────────► T006 ──► T007 ──► T008
                        │
                        ├──►──► T009 (US2 - verificação)
                        ├──►──► T010 (US2 - verificação)
                        └──►──► T011 ──► T012 (US3)

T005 ─────────────────────────────────────── (backend pronto para T006 consumir)

T006 ──► T013 (polish - boas-vindas)
T006 ──► T014 (polish - error handling)
T007/T008 ──► T015 (polish - responsividade)
T001/T002 ──► T016 (polish - regressão backend)
```

**Ordem de story completion**: US1 (T001→T008) → US2 (T009, T010) → US3 (T011, T012) → Polish (T013–T016)

---

## Parallel Execution por Story

### US1 (MVP) — pode paralelizar após T003 e T004:
```
[T001, T002] → [T003, T004] → [T005 ‖ T006] → T007 → T008
```

### US2 — verificações independentes, podem rodar em paralelo:
```
[T009 ‖ T010]
```

### US3 — sequencial simples:
```
T011 → T012
```

### Polish — tudo em paralelo após US3:
```
[T013 ‖ T014 ‖ T015 ‖ T016]
```

---

## Implementation Strategy

**MVP (US1 apenas — T001 a T008)**: Chat funcional básico com streaming. Substitui o placeholder. Entrega impacto imediato na demo. Estimativa: menor escopo possível para uma feature end-to-end.

**Incremento 2 (+ US2 — T009, T010)**: Contexto de conversa funcional. Requer apenas revisão/validação de código já escrito — se T005 e T006 foram implementados corretamente, US2 já funciona por construção.

**Incremento 3 (+ US3 — T011, T012)**: Reset de conversa. Uma função no hook + conexão ao botão existente.

**Incremento 4 (+ Polish — T013 a T016)**: Robustez, boas-vindas e responsividade.

---

## Summary

| Fase | Tasks | User Story | Arquivos |
|------|-------|-----------|---------|
| Phase 1: Setup | T001, T002 | — | `requirements.txt`, `config.py` |
| Phase 2: Foundation | T003, T004 | — | `models.py`, `types.ts` |
| Phase 3: US1 MVP | T005–T008 | US1 (P1) | `api.py`, `useChat.ts`, `ChatPage.tsx`, `ChatPage.module.css` |
| Phase 4: US2 | T009, T010 | US2 (P2) | `api.py` (verify), `useChat.ts` (verify) |
| Phase 5: US3 | T011, T012 | US3 (P3) | `useChat.ts`, `ChatPage.tsx` |
| Phase 6: Polish | T013–T022 | — | `useChat.ts`, `ChatPage.module.css`, `main.py`, `setup.sh`, `start.sh`, `rag.py`, `knowledge_base.md`, `config.py`, `api.py` |

**Total**: 22 tarefas · 9 paralelas marcadas · 3 user stories cobertas · 0 tarefas de teste (Demo-Mode)

**MVP sugerido**: T001–T008 (Phase 1 + 2 + 3) — chat funcional com streaming end-to-end.
