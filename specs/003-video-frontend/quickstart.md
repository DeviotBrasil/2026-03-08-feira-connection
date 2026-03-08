# Quickstart: Frontend React — Visualização de Vídeo WebRTC

**Feature**: 003-video-frontend  
**Date**: 2026-03-08

---

## Pré-requisitos

| Ferramenta | Versão Mínima | Propósito |
|---|---|---|
| Node.js | 18 LTS+ | Build do frontend (apenas dev / CI) |
| npm | 9+ | Gerenciador de pacotes JavaScript |
| Python | 3.11+ | Já exigido pelo `backend` |

Verificar node e npm:

```bash
node --version   # deve retornar v18.x ou superior
npm --version    # deve retornar 9.x ou superior
```

---

## Estrutura de Diretórios

```text
/
├── app/frontend/                   ← novo diretório (esta feature)
│   ├── src/
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── dist/                   ← gerado por "npm run build" (gitignored)
│
└── app/backend/
    └── api.py                  ← recebe adição de StaticFiles no final
```

---

## 1. Build do Frontend (único passo extra em relação ao backend)

```bash
cd app/frontend
npm install          # instala dependências (apenas na primeira vez)
npm run build        # gera app/frontend/dist/
```

Após o build, o diretório `app/frontend/dist/` estará pronto. O `backend` o detecta automaticamente na inicialização.

---

## 2. Iniciar o Backend (inclui serving do frontend)

Nenhuma mudança no processo de inicialização:

```bash
cd app/backend
python main.py
```

O backend inicia na porta `8080` (ou conforme `HTTP_PORT` no `.env`) e passa a servir também o frontend React via `/`.

---

## 3. Acessar o Frontend

Com o sistema completo em execução (service + backend):

```bash
# Abrir no browser padrão (macOS)
open http://localhost:8080

# Em outro dispositivo da LAN
open http://192.168.x.x:8080   # substituir pelo IP do servidor
```

O frontend:
1. Carrega a interface React
2. Inicia automaticamente a conexão WebRTC com o backend
3. Exibe o stream de vídeo ao vivo com bounding boxes do YOLO em até 5 segundos
4. Mostra o contador de FPS e o painel de saúde do backend

---

## 4. Desenvolvimento com Hot-Reload (opcional)

Para editar o frontend com hot-reload sem rebuild a cada alteração:

```bash
# Terminal 1 — backend FastAPI (com reload automático)
cd app/backend
uvicorn api:app --reload --port 8080

# Terminal 2 — Vite dev server (hot module replacement)
cd app/frontend
npm run dev   # inicia em localhost:5173
```

O `vite.config.ts` inclui um proxy que redireciona `/offer` e `/health` para `localhost:8080`. Acessar o frontend em `http://localhost:5173` durante desenvolvimento.

---

## 5. Verificação Rápida do Sistema

Com tudo em execução:

| Verificação | Como testar | Resultado esperado |
|---|---|---|
| Frontend carregado | `GET http://localhost:8080/` | Página React renderizada no browser |
| Stream ativo | Olhar o elemento de vídeo | Vídeo ao vivo com bounding boxes visíveis |
| FPS ≥ 24 | Contador no canto superior direito da tela | Número ≥ 24 |
| Status ZMQ ok | Painel de saúde | Status "ok" em verde |
| Reconexão automática | Reiniciar `backend` | Stream volta em até 10s sem reload |

---

## 6. Supervisord — Adição ao supervisord.conf (opcional)

Para gerenciar o rebuild automático com supervisord (não recomendado para demo — o build é um passo único pré-feira):

```ini
; Adicionar em app/service/supervisord.conf
[program:frontend-build]
command=npm run build
directory=%(here)s/../frontend
autostart=false    ; executar manualmente antes da demo
autorestart=false
stdout_logfile=%(here)s/../app/frontend/logs/build.log
stderr_logfile=%(here)s/../app/frontend/logs/build.err
```

> **Nota**: O `backend` já é gerenciado pelo `supervisord.conf` existente (feature 002). Nenhuma nova entrada é necessária para servir o frontend — o serving é feito pelo processo já supervisionado.

---

## Variáveis de Ambiente `.env` (backend)

Nenhuma variável nova é necessária. As variáveis existentes continuam válidas:

```env
HTTP_PORT=8080
HTTP_HOST=0.0.0.0
ZMQ_ENDPOINT=tcp://127.0.0.1:5555
```

---

## Solução de Problemas

| Problema | Causa Provável | Solução |
|---|---|---|
| Tela em branco ao acessar `localhost:8080` | Build não executado | `cd app/frontend && npm run build` |
| `dist/` não encontrado pelo backend | Diretório `app/frontend/dist/` ausente | Idem acima |
| Stream ficou preto | service não está publicando | Verificar painel de saúde — alerta ZMQ aparecerá |
| FPS < 24 | CPU sobrecarregado ou câmera lenta | Ajustar parâmetros YOLO via endpoint de configuração (feature 001 — Princípio VI) |
| Erro de conexão no `POST /offer` | Backend não acessível | Verificar se `python main.py` está rodando e na porta correta |
