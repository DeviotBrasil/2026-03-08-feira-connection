# Research: Frontend React — Visualização de Vídeo WebRTC

**Feature**: 003-video-frontend  
**Date**: 2026-03-08  
**Status**: Complete — todos os NEEDS CLARIFICATION resolvidos

---

## Decisão 1: Biblioteca de Frontend — React 18 + Vite

- **Decision**: React 18 + TypeScript 5 com Vite 5 como ferramenta de build.
- **Rationale**: A Constituição (Restrições de Stack Mandatório) exige React 18+ para o frontend. Vite é a ferramenta de build padrão do ecossistema React atual — build production em segundos, zero configuração para SPA. TypeScript adiciona segurança de tipos sem overhead em runtime.
- **Alternatives considered**:
  - *Vanilla HTML+JS* (como test.html existente) — rejeitado por violar o stack mandatório da Constituição que exige React 18+.
  - *Create React App* — rejeitado por estar obsoleto (não mantido desde 2023); Vite é o substituto oficial.
  - *Next.js* — rejeitado por requerer servidor Node.js em runtime para SSR; a spec exige artefatos estáticos servíveis.

---

## Decisão 2: Estratégia de Serving — FastAPI StaticFiles

- **Decision**: O build `app/frontend/dist/` é servido diretamente pelo `backend` via `fastapi.staticfiles.StaticFiles`. Adicionar ao final de `api.py`: mount `/assets`, mais um catch-all GET que retorna `index.html` para qualquer rota não reconhecida (padrão SPA).
- **Rationale**: Uma única URL, um único processo, zero configuração de CORS para o frontend. Ideal para demo LAN presencial. O operador abre `http://192.168.x.x:8080` e vê imediatamente o vídeo — sem portas diferentes, sem proxy, sem configuração de reverse proxy.
- **Alternatives considered**:
  - *`python -m http.server`* — rejeitado porque o `http.server` retorna 404 em qualquer rota diferente de `/` (quebra navegação SPA com F5); requer duas portas e dois processos.
  - *Nginx como servidor de arquivos estáticos* — rejeitado por custo de configuração desproporcionalmente alto para uma demo; adiciona processo extra sem benefício.
- **CORS**: O middleware já está configurado com `allow_origins=["*"]` em `api.py` — sem alteração necessária. Em demo LAN com frontend no mesmo origin, CORS não é disparado de qualquer forma.

---

## Decisão 3: Gerenciamento de Estado WebRTC no React — `useRef`

- **Decision**: `RTCPeerConnection` armazenada em `useRef`, nunca em `useState`. Estado de UI (label de status, FPS) em `useState`.
- **Rationale**: `RTCPeerConnection` é um objeto stateful imperativo. Guardar em `useState` provoca re-renders que recriam closures, causando race conditions onde callbacks de eventos antigos disparam sobre objetos novos. `useRef` é um container mutável sem disparo de render — o container correto para objetos imperativos de longa duração.
- **Gotcha StrictMode**: No React 18 StrictMode (dev), os effects executam duas vezes (mount → unmount → remount). A flag `cancelled` no `connect()` async garante que a primeira corrida async abandona o resultado; o cleanup destrói o objeto órfão antes do segundo mount.

---

## Decisão 4: Detecção de Desconexão — `onconnectionstatechange`

- **Decision**: Usar `pc.onconnectionstatechange`, monitorando o estado `failed` para disparar reconexão. O estado `disconnected` é transitório — aguardar transição para `failed` antes de reconectar (ICE pode se recuperar sozinho em LAN cabeada).
- **Rationale**: `onconnectionstatechange` agrega ICE + DTLS + mídia — mais confiável que `oniceconnectionstatechange` (ICE layer apenas). Em LAN cabeada, `disconnected` geralmente se resolve em < 5s sem intervenção. Forçar reconexão em `disconnected` causaria reconexões desnecessárias.
- **Alternatives considered**:
  - *Polling `getStats()` por bytes recebidos zerados* — rejeitado por latência de detecção = intervalo de polling, overhead de CPU, e complexidade desnecessária quando `onconnectionstatechange` é confiável.

---

## Decisão 5: Medição de FPS — `requestVideoFrameCallback`

- **Decision**: Usar `video.requestVideoFrameCallback` (rVFC) para contar frames reais do stream. Fallback para `requestAnimationFrame` em browsers sem suporte (Firefox < 132).
- **Rationale**: rVFC dispara exatamente quando um novo frame de vídeo é apresentado — mede o FPS real do stream, não o FPS da tela. Se o stream vier a 24 fps e a tela rodar a 60 Hz, rAF contaria 60 "frames" por segundo (incorreto); rVFC conta 24 (correto).
- **Suporte (2026)**: Chrome 83+, Firefox 132+, Safari 15.4+ — cobertura adequada para browsers atualizados.

---

## Decisão 6: Reconexão Automática — Exponential Backoff

- **Decision**: Backoff exponencial: 2s → 4s → 8s → 15s (cap). Reset para 2s ao atingir estado `connected`. Gerenciado via `useRef` + `setTimeout`.
- **Rationale**: Backoff evita flood de requisições `POST /offer` em caso de backend indisponível. O cap de 15s garante reconexão rápida quando o backend volta. Reset em `connected` garante que uma reconexão bem-sucedida recomeça com o menor delay.
- **Zombie prevention**: O handler `onconnectionstatechange` da conexão antiga é anulado (`pc.onconnectionstatechange = null`) antes do `pc.close()`. Sem isso, o evento `closed` do objeto antigo chamaria `scheduleReconnect` depois que a nova conexão já foi criada.

---

## Decisão 7: Backend URL Configurável — `?backend=...` ou `VITE_BACKEND_URL`

- **Decision**: O endereço do backend é lido em runtime de `window.location.origin` por padrão (funciona quando frontend é servido pelo próprio FastAPI) com override via parâmetro de URL `?backend=http://...`.
- **Rationale**: Em demo, o padrão de "mesmo origin" cobre quase todos os casos. O override via URL param permite apontar para outro host sem rebuild — útil se o display/browser estiver em outro dispositivo da LAN.
- **Alternatives considered**:
  - *`VITE_BACKEND_URL` como único mecanismo* — rejeitado porque requer rebuild para cada troca de IP. URL param não requer rebuild.

---

## Estrutura de Componentes React

```text
src/
├── main.tsx                     # Entry point: ReactDOM.createRoot
├── App.tsx                      # Layout: VideoPlayer + StatusBar + HealthPanel
├── types.ts                     # ConnectionState, HealthData, StreamStats
├── hooks/
│   ├── useWebRTC.ts             # RTCPeerConnection lifecycle, reconexão, FPS
│   └── useHealthPolling.ts      # Polling periódico de GET /health (5s)
└── components/
    ├── VideoPlayer.tsx          # <video> element, rVFC FPS counter overlay
    ├── StatusBar.tsx            # Status label + alerta ZMQ degraded
    └── HealthPanel.tsx          # Tabela com dados do /health
```

---

## Dependências de Build (Node.js — dev only)

| Pacote | Versão | Propósito |
|---|---|---|
| react | 18.x | UI framework (mandatório pela Constituição) |
| react-dom | 18.x | Renderização DOM |
| vite | 5.x | Build tool + dev server |
| @vitejs/plugin-react | 4.x | Plugin Vite para React (SWC transform) |
| typescript | 5.x | Tipagem estática |
| @types/react | 18.x | Types para TS |
| @types/react-dom | 18.x | Types para TS |

**Nenhuma dependência de runtime em CDN externo** — todos os módulos são bundlados pelo Vite em tempo de build (Princípio V).
