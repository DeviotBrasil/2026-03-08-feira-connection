# Contrato HTTP — Frontend Serving

**Feature**: 003-video-frontend  
**Serviço**: `backend` (integração de serving de arquivos estáticos)  
**Base URL**: `http://127.0.0.1:8080` (configurável via `HTTP_PORT`)  
**Date**: 2026-03-08

---

## Visão Geral

O `backend` passa a servir os assets estáticos do frontend React além dos endpoints de API existentes. O frontend consome os endpoints já documentados em [002 — webrtc-signaling.md](../../002-zmq-app/backend/contracts/webrtc-signaling.md).

| Endpoint | Método | Propósito |
|---|---|---|
| `/` | GET | Retorna `index.html` — shell da SPA React |
| `/assets/*` | GET | Serve JS/CSS/imagens bundlados pelo Vite |
| `/<qualquer-rota>` | GET | Catch-all: retorna `index.html` (SPA client-side routing) |
| `/offer` | POST | **Já documentado** em 002 — sinalização WebRTC |
| `/health` | GET | **Já documentado** em 002 — métricas do backend |

A ordem de registro importa: `/offer` e `/health` são registrados **antes** do catch-all, portanto nunca são interceptados por ele.

---

## GET / → `index.html`

### Propósito

Serve o ponto de entrada da SPA React. O browser carrega `index.html`, que referencia os bundles JS/CSS em `/assets/`.

### Request

Sem parâmetros obrigatórios.

**Query parameter opcional**:

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `backend` | `string (URL)` | `window.location.origin` | Override do endereço do backend a ser usado pelo frontend |

**Exemplo**: `http://192.168.1.10:8080/?backend=http://192.168.1.10:8080`

### Response

**Status 200 OK**  
**Content-Type**: `text/html; charset=utf-8`

Retorna o arquivo `app/frontend/dist/index.html`.

---

## GET /assets/* → arquivos estáticos

### Propósito

Serve os bundles JavaScript, CSS, fontes e imagens gerados pelo `npm run build` do Vite.

### Cache Headers

FastAPI `StaticFiles` serve arquivos com cabeçalho `Cache-Control` padrão. Em demo LAN, sem impacto prático — os assets são carregados uma única vez por sessão de browser.

### Response

**Status 200 OK** com o Content-Type apropriado ao arquivo (`.js` → `application/javascript`, `.css` → `text/css`, etc.).

**Status 404 Not Found** para assets não existentes no build.

---

## Alterações em `app/backend/api.py`

Para habilitar o serving do frontend, as seguintes linhas são adicionadas ao **final** de `api.py`, após os endpoints `/offer` e `/health`:

```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        return FileResponse(_FRONTEND_DIST / "index.html")
```

**Nota**: O bloco `if _FRONTEND_DIST.exists()` garante que o backend continue funcionando normalmente se o frontend ainda não tiver sido buildado (ex: primeiro boot sem `npm run build`).

---

## Fluxo Completo de Inicialização

```
Browser abre http://192.168.1.10:8080
    │
    │── GET / ────────────────────────────────────►  FastAPI retorna index.html
    │── GET /assets/index-<hash>.js ──────────────►  FastAPI retorna bundle React
    │── GET /assets/index-<hash>.css ────────────►   FastAPI retorna CSS
    │
    │  [React monta, useWebRTC inicia conexão]
    │
    │── POST /offer { sdp, type:"offer" } ────────►  FastAPI /offer (WebRTC)
    │◄── 200 { sdp, type:"answer" } ───────────────  SDP answer com ICE
    │
    │  [WebRTC conectado — stream de vídeo ativo]
    │
    │── GET /health ──────────────────────────────►  FastAPI /health (polling 5s)
    │◄── 200 { status, zmq_connected, fps, ... } ──  Métricas do backend
```
