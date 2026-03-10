# API Contract: Chat de IA — Backend FastAPI ↔ Frontend

**Feature**: `005-llama-ai-chat`  
**Protocol**: HTTP/1.1 + Server-Sent Events  
**Base URL**: `{window.location.origin}` (mesmo origin da app)  
**Date**: 2026-03-09

---

## Endpoints

### `POST /chat`

Recebe o histórico de mensagens da conversa atual e transmite a resposta gerada pelo modelo Llama 3.1 via Server-Sent Events (SSE).

#### Request

| Campo | Valor |
|-------|-------|
| Method | `POST` |
| Path | `/chat` |
| Content-Type | `application/json` |
| Body | `ChatRequest` |

**Body Schema — `ChatRequest`**:
```json
{
  "messages": [
    { "role": "user" | "assistant", "content": "string" }
  ]
}
```

**Regras de validação do request**:
- `messages` DEVE conter ao menos 1 item
- Cada item DEVE ter `role` ∈ `{"user", "assistant"}` e `content` não-vazio
- O último item DEVE ter `role: "user"` (é a mensagem sendo respondida)

**Exemplo de request**:
```http
POST /chat HTTP/1.1
Content-Type: application/json

{
  "messages": [
    { "role": "user", "content": "O que é YOLOv8?" },
    { "role": "assistant", "content": "YOLOv8 é um modelo de detecção de objetos em tempo real..." },
    { "role": "user", "content": "Quantas classes ele detecta por padrão?" }
  ]
}
```

---

#### Response — Sucesso (200)

| Campo | Valor |
|-------|-------|
| Status | `200 OK` |
| Content-Type | `text/event-stream` |
| Cache-Control | `no-cache` |
| Transfer-Encoding | `chunked` |

**Formato SSE** — cada evento:
```
data: <JSON>\n\n
```

**Schema do evento — `ChatChunk`**:
```json
{ "content": "string", "done": boolean }
```

- `done: false` → token(s) gerados; `content` contém o texto do chunk
- `done: true` → geração concluída; `content` é string vazia

**Exemplo de resposta streaming**:
```
data: {"content": "O YOLOv8 ", "done": false}

data: {"content": "detecta ", "done": false}

data: {"content": "80 classes ", "done": false}

data: {"content": "por padrão.", "done": false}

data: {"content": "", "done": true}

```

---

#### Response — Erro (4xx/5xx)

| Status | Situação | Response Body |
|--------|----------|---------------|
| `422 Unprocessable Entity` | Validação falhou (messages vazio, role inválido) | `{ "detail": [...] }` (Pydantic padrão) |
| `503 Service Unavailable` | Ollama indisponível ou modelo não carregado | `{ "detail": "Ollama service unavailable" }` |
| `504 Gateway Timeout` | Ollama não respondeu dentro do timeout | `{ "detail": "Model response timeout" }` |
| `500 Internal Server Error` | Erro inesperado no servidor | `{ "detail": "Internal server error" }` |

> **Nota sobre erros durante streaming**: Se o Ollama falhar *após* o início do streaming, o backend deve emitir um evento SSE de erro antes de fechar a conexão:
> ```
> data: {"error": "Stream interrupted", "done": true}
> 
> ```

---

### `GET /health` (existente — sem alteração)

Endpoint de health check existente. Não é modificado por esta feature.

---

## Comportamento do Frontend

### Consumo do SSE via `fetch`

```typescript
const response = await fetch('/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ messages }),
});

if (!response.ok) {
  // tratar erro HTTP (503, 504, 422)
  throw new Error(`HTTP ${response.status}`);
}

const reader = response.body!.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value, { stream: true });
  for (const line of text.split('\n')) {
    if (!line.startsWith('data: ')) continue;
    const chunk: ChatChunk = JSON.parse(line.slice(6));
    if (chunk.done) {
      // finalizar streaming
      break;
    }
    // append chunk.content à mensagem do assistente em construção
  }
}
```

---

## Considerações de Segurança

- O endpoint `/chat` não requer autenticação (alinhado com a spec — demo mode)
- O backend NÃO deve injetar input do usuário em comandos shell ou queries de banco
- `content` das mensagens é tratado como texto puro; sem interpretação de HTML ou markdown pelo backend
- CORS já configurado globalmente no FastAPI existente (`allow_origins=["*"]`)
- O backend encaminha mensagens ao Ollama local via loopback — sem exposição de dados a serviços externos
