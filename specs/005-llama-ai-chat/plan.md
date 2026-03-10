# Implementation Plan: Chat de IA Generativa com Llama 3.1

**Branch**: `005-llama-ai-chat` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/005-llama-ai-chat/spec.md`

## Summary

Adicionar um chat de IA generativa usando o modelo Llama 3.1 à interface existente. O backend FastAPI será estendido com um endpoint `POST /chat` que encaminha mensagens ao Ollama (runtime local) e transmite a resposta via Server-Sent Events (SSE). O frontend substituirá a página `ChatPage` placeholder por uma UI funcional de chat construída com Ant Design 6, consumindo o stream via `fetch` + `ReadableStream` nativo — sem novas dependências de frontend.

## Technical Context

**Language/Version**: Python 3.11+ (backend) · TypeScript 5.9 / React 19 (frontend)  
**Primary Dependencies**: FastAPI 0.100+, httpx>=0.25 (novo), Ollama (runtime externo local), Ant Design 6  
**Storage**: N/A — histórico de conversa apenas em memória de sessão do frontend (React state)  
**Testing**: N/A — Demo-Mode (Princípio VII)  
**Target Platform**: macOS/Linux local (demo stand) · browser moderno (Chrome/Firefox)  
**Project Type**: web-service (backend) + web-app (frontend)  
**Performance Goals**: Primeira parte da resposta visível em < 3s em hardware local sem GPU dedicada  
**Constraints**: 100% offline — sem APIs externas em runtime; Ollama em loopback (localhost:11434)  
**Scale/Scope**: 1 usuário simultâneo (demo stand); sessão única sem persistência

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Observação |
|-----------|--------|------------|
| **I. Demo-First** | ✅ PASS | Chat com IA agrega impacto "uau" direto ao visitante; não é overhead técnico |
| **II. Latência Zero-Compromisso** | ✅ PASS | Chat não usa ZMQ/WebRTC — é um canal adicional, não substitui o pipeline de vídeo |
| **III. Estabilidade 8h** | ✅ PASS | Endpoint `/chat` é stateless; falhas do Ollama são isoladas com tratamento de erro gracioso |
| **IV. 24 FPS** | ✅ PASS | Chat não interfere no pipeline de vídeo; opera em threads/coroutines separadas |
| **V. Infraestrutura Controlada** | ✅ PASS | Ollama roda localmente no loopback (127.0.0.1:11434); zero dependências de rede externa |
| **VI. Degradação Graciosa** | ✅ PASS | Se Ollama falhar, o sistema retorna 503 com mensagem de erro — o stream de vídeo continua |
| **VII. Sem Testes** | ✅ PASS | Testing = N/A; nenhuma tarefa de teste será criada |

**Stack Mandatório Check**:
- FastAPI ✅ (backend existente estendido)
- React 18+ ✅ (React 19 em uso)
- Novo componente: Ollama (runtime local) — não viola nenhuma proibição explícita da constitution
- Nenhum broker de mensageria pesado adicionado ✅
- Nenhum protocolo de vídeo com buffering adicionado ✅

**Complexidade**: Nenhuma violação. Sem entrada na tabela de Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/005-llama-ai-chat/
├── plan.md              ← este arquivo
├── spec.md              ← especificação funcional
├── research.md          ← decisões técnicas e rationale
├── data-model.md        ← entidades e fluxo de dados
├── quickstart.md        ← como rodar localmente
├── contracts/
│   └── chat-api.md      ← contrato SSE: POST /chat
├── checklists/
│   └── requirements.md  ← checklist de qualidade da spec
└── tasks.md             ← gerado por /speckit.tasks (ainda não criado)
```

### Source Code

```text
app/
├── backend/
│   ├── api.py              ← MODIFICAR: adicionar endpoint POST /chat com RAG
│   ├── config.py           ← MODIFICAR: adicionar OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, KB_PATH
│   ├── models.py           ← MODIFICAR: adicionar ChatMessage, ChatRequest
│   ├── main.py             ← MODIFICAR: chamar load_kb() no lifespan
│   ├── rag.py              ← CRIAR: loader KB + build_system_prompt()
│   ├── knowledge_base.md   ← CRIAR: conteúdo editável da base de conhecimento
│   └── requirements.txt    ← MODIFICAR: adicionar httpx>=0.25
└── frontend/
    └── src/
        ├── types.ts                    ← MODIFICAR: adicionar ChatMessage, ChatChunk
        ├── hooks/
        │   └── useChat.ts              ← CRIAR: hook de estado e streaming do chat
        └── pages/
            ├── ChatPage.tsx            ← SUBSTITUIR: implementar UI de chat
            └── ChatPage.module.css     ← MODIFICAR: estilos da UI de chat
```

**Structure Decision**: Opção 2 (Web Application) — reutiliza a estrutura `app/backend` + `app/frontend` já existente. Nenhum novo serviço ou projeto criado. O backend FastAPI é estendido com 3 novos modelos Pydantic + 1 endpoint + 1 dependência (`httpx`). O frontend substitui 2 arquivos e cria 1 hook.

## Complexity Tracking

> Nenhuma violação de Constitution Check. Tabela vazia.

---

## Design Detalhado

### Backend — Novos Modelos Pydantic (`models.py`)

```python
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError("messages must not be empty")
        if v[-1].role != "user":
            raise ValueError("last message must have role 'user'")
        return v
```

### Backend — Novas Configurações (`config.py`)

```python
OLLAMA_URL: str = Field(default="http://localhost:11434")
OLLAMA_MODEL: str = Field(default="llama3.1")
OLLAMA_TIMEOUT: float = Field(default=60.0)
```

### Backend — Endpoint de Chat (`api.py`)

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    """Encaminha mensagens ao Ollama e transmite resposta via SSE."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [m.model_dump() for m in request.messages],
        "stream": True,
    }

    async def event_stream():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{settings.OLLAMA_URL}/api/chat",
                    json=payload,
                    timeout=settings.OLLAMA_TIMEOUT,
                ) as resp:
                    if resp.status_code != 200:
                        yield f'data: {{"error": "Ollama returned {resp.status_code}", "done": true}}\n\n'
                        return
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        done = chunk.get("done", False)
                        yield f'data: {json.dumps({"content": content, "done": done})}\n\n'
                        if done:
                            break
        except httpx.ConnectError:
            yield f'data: {{"error": "Ollama service unavailable", "done": true}}\n\n'
        except httpx.TimeoutException:
            yield f'data: {{"error": "Model response timeout", "done": true}}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

### Frontend — Hook `useChat.ts`

Responsabilidades:
- Gerenciar estado de `messages: ChatMessage[]`, `input: string`, `streaming: boolean`
- Função `sendMessage()`: appenda mensagem do usuário + placeholder do assistente, aciona fetch SSE, atualiza conteúdo chunk a chunk
- Função `resetConversation()`: limpa o array de mensagens
- Tratamento de erros de rede/streaming (exibe notificação via Ant Design `message.error`)

### Frontend — UI `ChatPage.tsx`

Layout com Ant Design 6:
```
<div className={styles.container}>
  <div className={styles.header}>
    <Typography.Title level={4}>Chat IA</Typography.Title>
    <Button onClick={resetConversation} disabled={streaming}>Nova Conversa</Button>
  </div>

  <div className={styles.messages} ref={scrollRef}>
    {messages.map(msg => (
      <div key={msg.id} className={msg.role === 'user' ? styles.userMsg : styles.assistantMsg}>
        <Typography.Text>{msg.content}</Typography.Text>
        {msg.streaming && <span className={styles.cursor}>▋</span>}
      </div>
    ))}
  </div>

  <div className={styles.inputArea}>
    <Input.TextArea
      value={input}
      onChange={e => setInput(e.target.value)}
      onPressEnter={handleEnter}
      disabled={streaming}
      autoSize={{ minRows: 1, maxRows: 4 }}
      placeholder="Digite sua mensagem..."
    />
    <Button
      type="primary"
      onClick={sendMessage}
      disabled={!input.trim() || streaming}
      loading={streaming}
    >
      Enviar
    </Button>
  </div>
</div>
```

---

## Diagrama de Sequência

```
Browser (React)          FastAPI              Ollama (local)
     │                     │                       │
     │  POST /chat          │                       │
     │  {messages: [...]}   │                       │
     │─────────────────────►│                       │
     │                      │  POST /api/chat       │
     │                      │  {model, messages,    │
     │                      │   stream: true}       │
     │                      │──────────────────────►│
     │                      │                       │
     │  SSE: data: chunk1   │◄── NDJSON chunk 1 ────│
     │◄─────────────────────│                       │
     │  SSE: data: chunk2   │◄── NDJSON chunk 2 ────│
     │◄─────────────────────│                       │
     │  SSE: data: {done}   │◄── NDJSON {done:true} │
     │◄─────────────────────│                       │
```

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Ollama não instalado/rodando na demo | Média | Médio | Documentar em `quickstart.md`; checklist pré-feira inclui verificação do Ollama |
| Hardware lento → resposta demorada | Alta | Baixo (demo) | Streaming visible imediato reduz percepção de lentidão; timeout configurável |
| Mensagem muito longa → context overflow | Baixa | Baixo | Llama 3.1 tem janela de 128k tokens; improvável na demo |
| Erro durante streaming após início | Baixa | Médio | Backend emite evento SSE de erro `{"error": "...", "done": true}` |

---

## Post-Design Constitution Check

| Princípio | Status Final |
|-----------|-------------|
| I. Demo-First | ✅ Impacto visual: chat de IA no stand impressiona visitantes |
| II. Latência Zero-Compromisso | ✅ Chat opera em channel separado; pipeline ZMQ/WebRTC inalterado |
| III. Estabilidade 8h | ✅ Endpoint stateless; Ollama falha isolada; graceful error handling |
| IV. 24 FPS | ✅ Sem interferência no pipeline de vídeo |
| V. Infraestrutura Controlada | ✅ Ollama local em loopback; zero internet necessário |
| VI. Degradação Graciosa | ✅ Chat falha independentemente do vídeo |
| VII. Sem Testes | ✅ Nenhuma tarefa de teste será criada |
