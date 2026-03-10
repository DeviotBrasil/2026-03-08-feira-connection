# Quickstart: Chat de IA com Llama 3.1

**Feature**: `005-llama-ai-chat`  
**Date**: 2026-03-09

---

## Pré-requisitos

### 1. Instalar Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Baixar o modelo Llama 3.1

```bash
# Modelo 8B (recomendado para hardware sem GPU dedicada — ~4.7 GB)
ollama pull llama3.1

# Verificar se o modelo está disponível
ollama list
```

> **Hardware mínimo**: 8 GB RAM para rodar `llama3.1` (8B params, quantização Q4). Com GPU, a latência melhora significativamente.

### 3. Iniciar o serviço Ollama

```bash
# Iniciar em background (porta padrão: 11434)
ollama serve
```

Verificar que está rodando:
```bash
curl http://localhost:11434/api/tags
# Deve retornar JSON listando os modelos disponíveis
```

---

## Configuração

### Backend — variáveis de ambiente

Adicionar ao `.env` em `app/backend/` (ou exportar no shell):

```env
# Ollama — valores padrão (podem ser omitidos se usando configuração padrão)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TIMEOUT=60.0
```

### Backend — instalar nova dependência

```bash
cd app/backend
pip install httpx>=0.25
# Ou adicionar ao requirements.txt e reinstalar
pip install -r requirements.txt
```

---

## Executando

### Passo 1: Iniciar Ollama (se não estiver rodando)

```bash
ollama serve &
```

### Passo 2: Iniciar o backend

```bash
cd app/backend
python main.py
# Ou via uvicorn diretamente:
uvicorn api:app --host 0.0.0.0 --port 8080 --reload
```

### Passo 3: Iniciar o frontend

```bash
cd app/frontend
npm run dev
```

### Passo 4: Acessar o chat

Abrir `http://localhost:5173`, navegar para a aba **Chat** na sidebar e iniciar uma conversa.

---

## Testar o endpoint diretamente

```bash
# Teste de chat simples (sem streaming)
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Olá, o que você pode fazer?"}]}'

# Com streaming visível
curl -N -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Descreva YOLO em uma frase"}]}'
```

---

## Troubleshooting

| Problema | Causa Provável | Solução |
|----------|---------------|---------|
| `503 Service Unavailable` | Ollama não está rodando | Executar `ollama serve` |
| `llama3.1` não encontrado | Modelo não baixado | Executar `ollama pull llama3.1` |
| Resposta muito lenta | Hardware sem GPU ou RAM insuficiente | Usar `llama3.1:8b-instruct-q4_0` (mais leve) ou reduzir `num_ctx` |
| `504 Gateway Timeout` | Modelo demorando mais que 60s | Aumentar `OLLAMA_TIMEOUT` no `.env` |
| Erro de CORS no browser | Backend não configurado | Verificar que o CORS está habilitado no FastAPI (`allow_origins=["*"]`) |
| Chat não aparece na sidebar | Frontend não atualizado | Verificar se o `npm run dev` está rodando e recarregar a página |

---

## Estrutura de Arquivos Modificados

```
app/
├── backend/
│   ├── api.py              # + endpoint POST /chat
│   ├── config.py           # + OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
│   ├── models.py           # + ChatMessage, ChatRequest
│   └── requirements.txt    # + httpx>=0.25
└── frontend/
    └── src/
        ├── types.ts                    # + ChatMessage, ChatChunk
        ├── hooks/
        │   └── useChat.ts              # novo hook
        └── pages/
            ├── ChatPage.tsx            # substituído (era placeholder)
            └── ChatPage.module.css     # atualizado
```
