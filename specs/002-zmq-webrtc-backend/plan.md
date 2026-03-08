# Implementation Plan: Backend ZMQ → WebRTC

**Branch**: `002-zmq-backend` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/002-zmq-app/backend/spec.md`

## Summary

Implementar o serviço `backend` — um processo FastAPI independente que consome frames JPEG anotados do `service` via socket ZMQ PULL e os distribui em tempo real a browsers clientes via WebRTC (aiortc). O pipeline é: **ZMQ PULL → FrameDistributor → QueuedVideoTrack → RTCPeerConnection → browser React**, como exige o Princípio II da Constituição.

O serviço expõe dois endpoints HTTP: `POST /offer` (sinalização WebRTC offer/answer com ICE bundled, sem trickle ICE) e `GET /health` (estado ZMQ, peers ativos, FPS). É gerenciado pelo supervisord com auto-restart e não requer reinício para reconectar ao ZMQ quando o `service` reinicia.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI 0.100+, aiortc 1.9+, PyZMQ 25+ (`zmq.asyncio`), PyAV 10+ (via aiortc), OpenCV headless 4.8+, Pydantic 2.0+, Uvicorn, python-dotenv  
**Storage**: N/A — pipeline inteiramente stateless em memória; sem persistência de dados  
**Testing**: N/A — Demo-Mode (Princípio VII)  
**Target Platform**: macOS (desenvolvimento) / Linux (produção), mesmo host ou mesma LAN que o `service`  
**Project Type**: web-service (backend API de transporte de vídeo)  
**Performance Goals**: ≥ 24 FPS entregues ao browser React (SC-002); latência câmera→browser < 300ms (SC-001)  
**Constraints**: CPU mínima no backend — frames JPEG passados diretamente ao WebRTC sem re-codificação de vídeo; sem dependências de serviços externos em runtime (Princípio V)  
**Scale/Scope**: 2 peers WebRTC simultâneos; 1 câmera upstream; operação contínua de 8 horas

## Constitution Check

*GATE: verificado antes da Phase 0 e reconfirmado após Phase 1.*

| Princípio | Critério de Compliance | Status |
|---|---|---|
| I — Demo-First | Feature entrega o stream YOLO anotado ao browser visitante — é o objetivo direto da demo | ✅ PASS |
| II — Latência Zero-Compromisso | ZMQ PULL (vision→backend) + WebRTC aiortc (backend→browser); nenhum protocolo alternativo | ✅ PASS |
| III — Estabilidade 8h | supervisord `autorestart=true`; `GET /health`; reconexão ZMQ automática via CONFLATE; cleanup de peers stale | ✅ PASS |
| IV — 24 FPS Mínimo | `CONFLATE=1` no PULL descarta frames velhos; `asyncio.Queue(maxsize=1)` por peer; sem re-codificação | ✅ PASS |
| V — Rede Cabeada | Sem Wi-Fi, sem APIs externas; operação `localhost`/LAN apenas; sem STUN/TURN externos | ✅ PASS |
| VI — Degradação Graciosa | Stream continua mesmo sem detecções (frames JPEG sem bboxes ainda são distribuídos); health expõe FPS | ✅ PASS |
| VII — Sem Testes Automatizados | Nenhuma task de teste; validação por execução manual e checklist | ✅ PASS |
| Stack Mandatório | aiortc (WebRTC), PyZMQ (mensageria), FastAPI (backend) — todos na tabela de stack | ✅ PASS |

**Resultado pós-Phase 1**: APROVADO — nenhuma violação detectada. Sem registro na tabela de Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/002-zmq-app/backend/
├── plan.md                        ← este arquivo
├── research.md                    ← Phase 0 — decisões técnicas
├── data-model.md                  ← Phase 1 — entidades e relacionamentos
├── quickstart.md                  ← Phase 1 — como rodar e verificar
├── contracts/
│   └── webrtc-signaling.md        ← Phase 1 — contrato HTTP da API
└── tasks.md                       ← Phase 2 (/speckit.tasks — não criado aqui)
```

### Source Code (repository root)

```text
app/backend/                        ← novo serviço (processo independente)
├── main.py                            # Entry point: inicia ZMQ task + Uvicorn
├── api.py                             # FastAPI app: POST /offer, GET /health, CORS
├── zmq_subscriber.py                  # Async ZMQ PULL consumer (zmq.asyncio)
├── distributor.py                     # FrameDistributor: fan-out para peer queues
├── webrtc_track.py                    # QueuedVideoTrack (VideoStreamTrack aiortc)
├── models.py                          # Pydantic: OfferRequest, AnswerResponse, HealthStatus
├── config.py                          # Config via env vars + python-dotenv
├── requirements.txt                   # Dependências Python
└── logs/                              # Criado em runtime pelo supervisor

app/service/                        ← existente, sem alterações de código
└── supervisord.conf                   # ← adicionar stanza [program:backend]
```

**Structure Decision**: Serviço independente em `app/backend/` na raiz do repositório, paralelo a `app/service/`. Separação em processo próprio permite restart independente via supervisord, isola dependências (aiortc não precisa de ultralytics) e clarifica responsabilidades (visão vs. transporte). A stanza do supervisor é adicionada ao `supervisord.conf` existente para manter operação unificada sob um único daemon.

## Complexity Tracking

> Sem violações da Constituição — tabela não aplicável.
