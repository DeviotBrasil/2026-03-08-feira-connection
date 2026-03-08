# Implementation Plan: Frontend React — Visualização de Vídeo WebRTC

**Branch**: `003-video-frontend` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/003-video-frontend/spec.md`

## Summary

Implementar o `frontend` — uma SPA React que recebe o stream de vídeo anotado pelo YOLO via WebRTC a partir do `backend` e o exibe continuamente ao operador/visitante da feira. O pipeline completo é: **câmera → YOLO → ZMQ → backend → WebRTC → React → tela**.

O frontend é buildado com Vite + TypeScript e servido pelo próprio `backend` via `FastAPI.StaticFiles` — um único processo, uma única porta (8080), zero configuração extra. Conecta automaticamente ao WebRTC ao carregar, exibe FPS em tempo real via `requestVideoFrameCallback`, monitora saúde do backend via polling `/health` a cada 5s e reconecta automaticamente com backoff exponencial (2s → 15s) em caso de desconexão.

## Technical Context

**Language/Version**: TypeScript 5 + React 18 (frontend); Python 3.11+ (backend, sem alterações de versão)  
**Primary Dependencies**: React 18, ReactDOM 18, Vite 5, @vitejs/plugin-react (build-time apenas); `fastapi[standard]` já existente (adição de `StaticFiles` no `api.py`)  
**Storage**: N/A — stateless; sem localStorage, IndexedDB ou cookies  
**Testing**: N/A — Demo-Mode (Princípio VII)  
**Target Platform**: Browser Chromium-based (Chrome/Edge) moderno, macOS/Linux, LAN cabeada  
**Project Type**: web-application (SPA frontend + integração com backend existente)  
**Performance Goals**: ≥ 24 FPS exibidos no browser (AC-002); conexão estabelecida em ≤ 5s após carregar a página (SC-001)  
**Constraints**: Zero dependências de CDN externo em runtime — todos os módulos bundlados pelo Vite (Princípio V); Node.js necessário apenas em build-time; sem autenticação (LAN fechada, Princípio V)  
**Scale/Scope**: 1–3 visitantes simultâneos no display; 8h contínuas sem reload (AC-001)

## Constitution Check

*GATE: verificado antes da Phase 0 e reconfirmado após Phase 1.*

| Princípio | Critério de Compliance | Status |
|---|---|---|
| I — Demo-First | Frontend exibe o stream YOLO anotado ao vivo — é o produto final visível pelo visitante | ✅ PASS |
| II — Latência Zero-Compromisso | Transporte WebRTC a partir do `backend`; sem HLS, MJPEG ou WebSocket com base64 | ✅ PASS |
| III — Estabilidade 8h | Reconexão automática com backoff; health polling detecta degradação; sem leak de memória (cleanup completo de RTCPeerConnection) | ✅ PASS |
| IV — 24 FPS Mínimo | FPS medido via `requestVideoFrameCallback`; alerta visual quando `fps < 24` ou `HealthData.fps_below_threshold` | ✅ PASS |
| V — Rede Cabeada / Offline | Build bundled pelo Vite — zero CDN externo em runtime; servido dentro do `backend` (mesma LAN) | ✅ PASS |
| VI — Degradação Graciosa | Alerta ZMQ visível quando `status === "degraded"`; stream de vídeo continua exibindo o que chegar do backend | ✅ PASS |
| VII — Sem Testes Automatizados | Nenhuma tarefa de teste; validação por execução manual com câmera conectada | ✅ PASS |
| Stack Mandatório | React 18 (frontend) — obrigatório pela tabela de stack; FastAPI já em uso | ✅ PASS |

**Resultado pós-Phase 1**: APROVADO — nenhuma violação detectada. Sem registro na tabela de Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-video-frontend/
├── plan.md                        ← este arquivo
├── research.md                    ← Phase 0 — decisões técnicas
├── data-model.md                  ← Phase 1 — entidades de estado
├── quickstart.md                  ← Phase 1 — como buildar e acessar
├── contracts/
│   └── frontend-serving.md        ← Phase 1 — contrato HTTP do serving estático
└── tasks.md                       ← Phase 2 (/speckit.tasks — não criado aqui)
```

### Source Code (repository root)

```text
app/frontend/                               ← novo diretório (esta feature)
├── index.html                          # Shell HTML da SPA
├── vite.config.ts                      # Vite: build + proxy dev → :8080
├── tsconfig.json                       # TypeScript config
├── package.json                        # Dependências e scripts
└── src/
    ├── main.tsx                        # Entry point: ReactDOM.createRoot
    ├── App.tsx                         # Layout raiz: VideoPlayer + StatusBar + HealthPanel
    ├── types.ts                        # ConnectionState, HealthData, StreamStats, BackendConfig
    ├── hooks/
    │   ├── useWebRTC.ts                # RTCPeerConnection lifecycle, reconexão backoff, FPS
    │   └── useHealthPolling.ts         # Polling periódico de GET /health (5s)
    └── components/
        ├── VideoPlayer.tsx             # <video> element + rVFC FPS counter overlay
        ├── StatusBar.tsx               # Status label colorido + alerta ZMQ degraded
        └── HealthPanel.tsx             # Tabela com dados do /health

app/backend/
└── api.py                              ← adicionar StaticFiles + catch-all no final
```

**Structure Decision**: Frontend em `app/frontend/` na raiz do repositório, paralelo a `app/backend/`. Esta separação segue o mesmo padrão de `app/service/` e `app/backend/` — cada camada vive em seu próprio diretório de primeiro nível. O build gerado em `app/frontend/dist/` é detectado automaticamente pelo `backend` via `Path(__file__).parent.parent / "frontend" / "dist"`, mantendo o backend como único processo a gerenciar.

## Complexity Tracking

> Sem violações da Constituição — tabela não aplicável.
