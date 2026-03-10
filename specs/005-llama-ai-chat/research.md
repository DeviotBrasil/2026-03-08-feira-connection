# Research: Chat de IA Generativa com Llama 3.1

**Feature**: `005-llama-ai-chat`  
**Date**: 2026-03-09  
**Status**: Complete — todos os unknowns resolvidos

---

## 1. Runtime do Modelo: Ollama

### Decision
Usar **Ollama** como runtime local para servir o modelo Llama 3.1.

### Rationale
- Ollama expõe API REST compatível com o protocolo OpenAI em `http://localhost:11434`
- Zero dependências de rede externa durante a demo — alinhado com Princípio V (Infraestrutura Controlada)
- `ollama pull llama3.1` baixa o modelo uma vez; depois opera 100% offline
- API de chat nativa com suporte a histórico de mensagens e streaming

### Alternatives Considered
- **Hugging Face Transformers direto em Python**: descartado — requer código de inferência customizado, gestão de GPU/CPU manual e não tem API REST pronta
- **LM Studio** (GUI): descartado — não expõe API REST programaticamente de forma confiável
- **API externa OpenAI/Groq**: descartado — viola Princípio V (sem dependências externas em runtime)

---

## 2. Endpoint Ollama para Chat

### Decision
`POST http://localhost:11434/api/chat` com streaming habilitado.

### Request Format
```json
{
  "model": "llama3.1",
  "messages": [
    { "role": "user", "content": "Olá" },
    { "role": "assistant", "content": "Olá! Como posso ajudar?" },
    { "role": "user", "content": "Me fale sobre detecção de objetos" }
  ],
  "stream": true
}
```

### Response Format (streaming — NDJSON)
Cada linha é um objeto JSON separado por `\n`:
```json
{"model":"llama3.1","created_at":"...","message":{"role":"assistant","content":"A "},"done":false}
{"model":"llama3.1","created_at":"...","message":{"role":"assistant","content":"detecção "},"done":false}
{"model":"llama3.1","created_at":"...","message":{"role":"assistant","content":""},"done":true,"total_duration":1234567890}
```

### Alternatives Considered
- `POST /api/generate` (API legada): descartado — não gerencia histórico de mensagens nativamente; requer serialização manual do contexto
- `POST /v1/chat/completions` (OpenAI-compat): válido, mas `/api/chat` é mais simples e idiomático para Ollama

---

## 3. Protocolo de Streaming FastAPI → Browser

### Decision
**Server-Sent Events (SSE)** via `StreamingResponse` do FastAPI, consumido no frontend com `fetch` + `ReadableStream` nativo.

### Rationale
- SSE é unidirecional (servidor → cliente), exato para streaming de tokens
- `fetch` + `ReadableStream` disponível em todos os browsers modernos sem biblioteca extra
- Permite streaming de POST (necessário para enviar o histórico), diferente de `EventSource` (que só suporta GET)
- Não adiciona nenhuma dependência ao frontend (sem `@microsoft/fetch-event-source` ou similar)

### FastAPI SSE Format (por evento)
```
data: {"content": "A ", "done": false}\n\n
data: {"content": "detecção ", "done": false}\n\n
data: {"content": "", "done": true}\n\n
```

### Frontend Consumption Pattern
```typescript
const response = await fetch('/chat', { method: 'POST', body: JSON.stringify({messages}) });
const reader = response.body!.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const lines = decoder.decode(value).split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const chunk = JSON.parse(line.slice(6));
      // atualizar estado do componente com chunk.content
    }
  }
}
```

### Alternatives Considered
- **WebSocket**: descartado — bidirecional desnecessário; mais complexo (handshake, reconnect logic)
- **Polling**: descartado — introduz latência perceptível e overhead de múltiplas requisições
- **`sse-starlette` biblioteca**: válido mas adiciona dependência; `StreamingResponse` nativo do FastAPI é suficiente

---

## 4. Cliente HTTP Assíncrono (Backend → Ollama)

### Decision
**`httpx`** com suporte a `AsyncClient` e streaming via `.aiter_lines()`.

### Rationale
- `httpx` é o cliente async recomendado para FastAPI — integra nativamente com `asyncio`
- Suporte nativo a streaming de resposta sem bloquear o event loop
- Já é compatível com o ambiente Python existente

### Pattern
```python
async with httpx.AsyncClient() as client:
    async with client.stream("POST", ollama_url, json=payload, timeout=None) as resp:
        async for line in resp.aiter_lines():
            if line:
                chunk = json.loads(line)
                yield f"data: {json.dumps({'content': chunk['message']['content'], 'done': chunk['done']})}\n\n"
```

### Alternatives Considered
- **`aiohttp`**: válido mas `httpx` é mais idiomático no ecossistema FastAPI/Pydantic
- **`requests` (síncrono)**: proibido — bloquearia o event loop do FastAPI

---

## 5. Ant Design: Componentes de Chat UI

### Decision
Usar componentes padrão do Ant Design 6 existente: `List`, `Input.TextArea`, `Button`, `Typography`, `Spin`.

### Rationale
- Ant Design 6 não inclui componente de Chat dedicado nativamente (existe `ProChat` do Ant Design X, biblioteca separada)
- Adicionar `@ant-design/x` apenas para o componente de chat seria over-engineering para uma demo
- `List` + `Input.TextArea` + `Button` são suficientes para uma UI limpa e profissional
- Mantém consistência com o stack frontend existente sem novas dependências

### UI Layout
```
┌─────────────────────────────────────┐
│  [Nova Conversa]                    │  ← header da tela
├─────────────────────────────────────┤
│                                     │
│  [Usuário] Pergunta aqui            │
│  [Assistente] Resposta...           │  ← lista de mensagens (scroll)
│  [Assistente] digitando... ●●●      │
│                                     │
├─────────────────────────────────────┤
│  [Input textarea...]    [Enviar]    │  ← área de input
└─────────────────────────────────────┘
```

### Alternatives Considered
- **`@ant-design/x` + ProChat**: válido mas adiciona ~300KB de dependência para um componente demo
- **`react-markdown`**: não necessário — respostas do Llama serão exibidas como texto simples

---

## 6. Gestão de Contexto da Conversa

### Decision
Histórico mantido **apenas no estado React** (array de mensagens em memória). A cada envio, o frontend submete o histórico completo ao backend, que o repassa ao Ollama.

### Rationale
- Sem banco de dados, sem persistência — alinhado com a spec (sessão em memória)
- Backend stateless: cada requisição `/chat` é independente; facilita deployment e evita memory leaks
- Ollama gerencia o contexto via `messages[]` no payload — não requer ninguna lógica adicional de janela de contexto no backend

### Alternatives Considered
- **Sessão no servidor (session_id)**: descartado — adiciona estado ao backend, complexidade de TTL e cleanup
- **localStorage**: descartado — desnecessário para uma demo; adiciona edge case de dados "sujos" entre sessões

---

## 7. Configuração do Ollama no Backend

### Decision
URL e modelo configuráveis via variáveis de ambiente com defaults para desenvolvimento local.

```python
OLLAMA_URL: str = Field(default="http://localhost:11434")
OLLAMA_MODEL: str = Field(default="llama3.1")
OLLAMA_TIMEOUT: float = Field(default=60.0)  # segundos para primeira resposta
```

### Rationale
- Permite sobrescrever a URL se o Ollama rodar em outro host (ex: GPU server separado no stand)
- Timeout de 60s cobre modelos maiores em hardware com menos VRAM

---

## Summary: Stack de Integração

```
Browser (React/TypeScript)
  └── fetch POST /chat  ──►  FastAPI (Python/asyncio)
                                └── httpx async stream  ──►  Ollama :11434
                                                                └── Llama 3.1 (local)
```

**Novas dependências**:
- Backend: `httpx>=0.25` (único pacote novo)
- Frontend: nenhuma (usa `fetch` nativo)
- Runtime: Ollama instalado no host (não é dependência de código)
