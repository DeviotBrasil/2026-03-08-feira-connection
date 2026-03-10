# Data Model: Chat de IA Generativa com Llama 3.1

**Feature**: `005-llama-ai-chat`  
**Date**: 2026-03-09

---

## Entidades

### ChatMessage

Unidade atômica de comunicação na conversa.

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `role` | `"user" \| "assistant"` | Sim | Origem da mensagem |
| `content` | `string` | Sim | Conteúdo textual da mensagem |
| `id` | `string` (UUID) | Sim (frontend only) | Identificador único para React key |
| `timestamp` | `number` (ms epoch) | Sim (frontend only) | Momento de criação da mensagem |
| `streaming` | `boolean` | Não (frontend only) | `true` quando a mensagem do assistente ainda está sendo gerada |

> Nota: `id`, `timestamp` e `streaming` existem apenas no estado do frontend. O backend e o Ollama recebem somente `role` + `content`.

---

### ChatRequest (Backend — request body)

Payload enviado pelo frontend ao endpoint `POST /chat`.

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `messages` | `ChatMessage[]` | Sim | Histórico completo da conversa (inclui a nova mensagem do usuário) |

**Exemplo**:
```json
{
  "messages": [
    { "role": "user", "content": "O que é YOLO?" },
    { "role": "assistant", "content": "YOLO é um algoritmo de detecção de objetos..." },
    { "role": "user", "content": "Qual a versão mais recente?" }
  ]
}
```

---

### ChatChunk (Backend — SSE response)

Evento SSE emitido pelo backend durante o streaming.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `content` | `string` | Token(s) gerado(s) neste chunk (pode ser string vazia no chunk final) |
| `done` | `boolean` | `true` apenas no último chunk da geração |

**Formato do evento SSE**:
```
data: {"content": "YOLO ", "done": false}

data: {"content": "v8 é ", "done": false}

data: {"content": "a mais recente.", "done": false}

data: {"content": "", "done": true}

```

---

## Estado do Frontend (Hook `useChat`)

```typescript
interface ChatState {
  messages: ChatMessage[];   // histórico completo exibido na UI
  input: string;             // texto atual no campo de input
  streaming: boolean;        // true enquanto o assistente está gerando
}
```

---

## Fluxo de Dados

```
[Usuário digita] 
  → input state atualiza
  
[Usuário pressiona Enviar]
  → valida input não-vazio
  → adiciona { role: "user", content, id, timestamp } ao messages state
  → adiciona placeholder { role: "assistant", content: "", streaming: true } ao messages state
  → streaming = true
  → envia POST /chat com messages[]
  
[Streaming ativo — por chunk recebido]
  → atualiza content do placeholder do assistente (append)
  
[Chunk done: true recebido]
  → streaming = false
  → remove flag streaming do último ChatMessage
  
[Reset da conversa]
  → messages = []
  → streaming = false
```

---

## Validações

| Regra | Onde | Tipo |
|-------|------|------|
| `content` não pode ser vazio ou somente whitespace | Frontend, antes do envio | Bloqueio silencioso (desabilita botão) |
| `messages.length` deve ser ≥ 1 antes de enviar ao backend | Backend | HTTP 422 |
| `role` deve ser `"user"` ou `"assistant"` | Backend (Pydantic) | HTTP 422 |
| Último item em `messages` deve ter `role: "user"` | Backend | HTTP 422 |

---

## Mapeamento para Ollama

O backend transforma `ChatMessage[]` em:
```json
{
  "model": "llama3.1",
  "messages": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "stream": true
}
```

Campos `id`, `timestamp` e `streaming` são descartados antes do envio ao Ollama.
