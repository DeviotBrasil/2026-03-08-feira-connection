---
description: "Task list — 001-python-service"
---

# Tasks: Serviço Python de Visão Computacional

**Input**: Design documents de `/specs/001-python-app/service/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅

**Testes**: N/A — Demo-Mode (Princípio VII da constituição). Nenhuma tarefa de teste gerada.

**Organização**: Tarefas agrupadas por User Story para implementação e validação manual independente.

## Formato: `[ID] [P?] [Story] Descrição`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências incompletas)
- **[Story]**: A qual User Story a tarefa pertence (US1, US2, US3)
- Todos os paths relativos à raiz do repositório

---

## Phase 1: Setup (Infraestrutura do Projeto)

**Objetivo**: Criar estrutura de diretórios, dependências e arquivos de configuração base.

- [X] T001 Criar diretório `app/service/` e inicializar estrutura do projeto
- [X] T002 Criar `app/service/requirements.txt` com dependências fixadas: `ultralytics>=8.0`, `opencv-python-headless>=4.8`, `pyzmq>=25`, `fastapi>=0.100`, `uvicorn[standard]>=0.23`, `pydantic>=2.0`, `numpy>=1.24`, `supervisor>=4.2`, `python-dotenv>=1.0`
- [X] T003 [P] Criar `app/service/.env.example` documentando todas as variáveis de ambiente: `CAMERA_DEVICE_INDEX`, `ZMQ_ENDPOINT`, `YOLO_MODEL_PATH`, `CONFIDENCE_THRESHOLD`, `CAPTURE_WIDTH`, `CAPTURE_HEIGHT`, `INFERENCE_WIDTH`, `INFERENCE_HEIGHT`, `JPEG_QUALITY`, `HTTP_PORT`
- [X] T004 [P] Criar `app/service/.gitignore` excluindo: `config.json`, `.venv/`, `__pycache__/`, `*.pyc`, `yolov8n.pt`, `.env`

**Checkpoint**: Estrutura base pronta — virtualenv pode ser criado e dependências instaladas com `pip install -r requirements.txt`

---

## Phase 2: Fundacional (Modelos e Configuração)

**Objetivo**: Implementar as entidades Pydantic e a camada de configuração que todos os módulos dependem.

⚠️ **CRÍTICO**: Nenhuma User Story pode ser implementada antes desta fase.

- [X] T005 Criar `app/service/models.py` com todos os modelos Pydantic: `BoundingBox`, `Detection`, `FrameMetadata`, `ServiceConfig` (com todos os campos e validações do data-model.md), `HealthStatus` (com enum `status: ok|reconnecting|degraded`), `ConfigRequest` (campos opcionais para PATCH parcial via `POST /config`)
- [X] T006 [P] Criar `app/service/config.py` implementando: carregamento de `ServiceConfig` a partir de `config.json` (se existir) com fallback para defaults, override por variáveis de ambiente (`CAMERA_DEVICE_INDEX`, `ZMQ_ENDPOINT`, etc.), função `save_config(config: ServiceConfig)` que persiste em `config.json`, função `load_config() -> ServiceConfig`

**Checkpoint**: Fundação pronta — `from models import ServiceConfig, FrameMetadata` funciona; `from config import load_config` retorna ServiceConfig com valores de env vars

---

## Phase 3: User Story 1 — Stream de Detecção em Tempo Real (Priority: P1) 🎯 MVP

**Objetivo**: Pipeline completo câmera → YOLO → bounding boxes → ZMQ publicando frames anotados com metadados.

**Validação manual**: Abrir dois terminais. No primeiro: `python3 main.py`. No segundo: consumer ZMQ do quickstart.md. Confirmar que frames chegam com ≥ 24 FPS e bounding boxes visíveis ao redor de pessoas.

### Implementação User Story 1

- [X] T007 [P] [US1] Criar `app/service/camera.py` com classe `CameraCapture`: inicializar `cv2.VideoCapture(device_index)` com backend AVFoundation (macOS), configurar resolução de captura via `CAP_PROP_FRAME_WIDTH/HEIGHT`; **se `cap.isOpened()` == False no construtor**, entrar em loop de retry a cada 2 segundos (sem lançar exceção fatal) logando cada tentativa — câmera pode ser conectada após o start do serviço; método `read() -> np.ndarray | None` que retorna o frame ou `None` em caso de falha; método `apply_camera_props(config: ServiceConfig)` que aplica `CAP_PROP_BRIGHTNESS`, `CAP_PROP_EXPOSURE`, `CAP_PROP_AUTOFOCUS`
- [X] T008 [P] [US1] Criar `app/service/inference.py` com classe `YOLOInference`: no `__init__`, carregar modelo via `YOLO(model_path)` com auto-detecção de device (`"mps"` em Apple Silicon, `"cpu"` fallback); **se o arquivo do modelo não existir ou o carregamento falhar, lançar exceção imediatamente (fail-fast) — o processo deve encerrar com exit code não-zero e mensagem de erro clara no log**; método `run(frame: np.ndarray, conf: float, infer_size: tuple) -> tuple[list[Detection], bool]` que redimensiona frame para resolução de inferência, executa YOLO, converte coordenadas de volta para resolução original (1280×720), retorna `(detections, inference_error)` — exceções por frame são capturadas e retornam `([], True)` sem propagar
- [X] T009 [P] [US1] Criar `app/service/annotator.py` com classe `FrameAnnotator`: método `draw(frame: np.ndarray, detections: list[Detection]) -> np.ndarray` que desenha bounding boxes coloridos por classe (pessoa = verde), label com `class_name + confidence` em fonte legível, contador `"Pessoas: N"` no canto superior esquerdo do frame
- [X] T010 [P] [US1] Criar `app/service/publisher.py` com classe `ZMQPublisher`: inicializar socket `zmq.PUSH` com bind no endpoint configurado, definir `SNDHWM=2`, `LINGER=0`, `SNDTIMEO=100`, método `publish(frame: np.ndarray, metadata: FrameMetadata, jpeg_quality: int)` que codifica frame em JPEG, serializa metadata em JSON UTF-8, envia mensagem multipart `[jpeg_bytes, json_bytes]`, captura `zmq.ZMQError` de timeout sem propagar
- [X] T011 [US1] Criar `app/service/main.py` com o loop principal de captura: instanciar `CameraCapture`, `YOLOInference`, `FrameAnnotator`, `ZMQPublisher` a partir da `ServiceConfig` carregada; implementar contador `frame_id` (int, monotônico), janela deslizante de 30 frames para cálculo de `fps_measured`; loop: `camera.read()` → `inference.run()` → `annotator.draw()` → construir `FrameMetadata` com todos os campos do data-model.md → `publisher.publish()`; capturar exceções por frame (frame com `inference_error=True` ainda é publicado)

**Checkpoint US1**: `python3 main.py` + consumer ZMQ confirmam ≥ 24 FPS com bounding boxes desenhados. US1 entregue como MVP standalone.

---

## Phase 4: User Story 2 — Configuração de Câmera e YOLO em Runtime (Priority: P2)

**Objetivo**: Expor API HTTP para ajuste de parâmetros YOLO e câmera sem reiniciar o processo.

**Validação manual**: Com serviço rodando, executar `curl -X POST http://127.0.0.1:8000/config -H "Content-Type: application/json" -d '{"confidence_threshold": 0.3}'` e confirmar que detecções de menor confiança aparecem nos frames seguintes sem interrupção do stream.

### Implementação User Story 2

- [X] T012 [P] [US2] Criar `app/service/api.py` com app FastAPI: estrutura base com `app = FastAPI()`, importar `ServiceConfig`, `HealthStatus`, `ConfigRequest`; implementar `GET /health` retornando `HealthStatus` com todos os campos do data-model.md (lê estado compartilhado via `threading.Event` / variável global thread-safe); placeholder para `POST /config`
- [X] T013 [US2] Implementar `POST /config` em `app/service/api.py`: receber `ConfigRequest` (campos opcionais), aplicar apenas os campos enviados sobre a `ServiceConfig` ativa, chamar `save_config()` para persistir, retornar `ServiceConfig` completa atualizada; Pydantic valida automaticamente os ranges definidos no data-model.md (HTTP 422 em caso de violação)
- [X] T014 [US2] Integrar reconfiguração em runtime em `app/service/main.py`: usar `threading.Event` e `queue.Queue(maxsize=1)` para comunicação thread-safe entre FastAPI (thread de API) e o loop de captura (thread principal); quando `POST /config` for chamado, a thread de captura aplica o novo `confidence_threshold` na próxima inferência e chama `camera.apply_camera_props()` com os novos parâmetros de câmera
- [X] T015 [US2] Iniciar servidor FastAPI/uvicorn em thread daemon separada em `app/service/main.py`: `threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": "127.0.0.1", "port": HTTP_PORT}, daemon=True).start()` antes do loop de captura

**Checkpoint US2**: `curl POST /config` com novos parâmetros retorna 200 e efeito visível nos frames em < 500ms. `curl POST /config` com valor inválido retorna 422 e config não muda.

---

## Phase 5: User Story 3 — Resiliência e Health Monitoring (Priority: P3)

**Objetivo**: Auto-reconexão de câmera, transições de estado de saúde, e supervisord para auto-restart do processo.

**Validação manual**: Com serviço rodando, desconectar USB da C925e. Confirmar que `GET /health` retorna `status: "reconnecting"`. Reconectar câmera. Confirmar que stream retoma em ≤ 10s e status volta para `"ok"`.

### Implementação User Story 3

- [X] T016 [P] [US3] Implementar loop de reconexão de câmera em `app/service/camera.py`: quando `camera.read()` retornar `None` consecutivamente (threshold: 5 frames), chamar `camera.release()` e entrar em loop de retry `cv2.VideoCapture(device_index)` a cada 2 segundos; expor propriedade `is_connected: bool`; logar evento de desconexão e reconexão em JSON estruturado
- [X] T017 [P] [US3] Implementar máquina de estados `HealthStatus` em `app/service/api.py`: estado compartilhado (thread-safe com `threading.Lock`) contendo `status`, `uptime_seconds`, `fps_measured`, `fps_below_threshold`, `camera_connected`, `inference_ok`, `frames_published`; transições: `ok → reconnecting` quando `camera.is_connected == False`; `ok → degraded` quando FPS < 24 por mais de 10s; `reconnecting/degraded → ok` quando condição normaliza
- [X] T018 [US3] Implementar tracking de métricas em `app/service/main.py`: `frames_published` (counter global, incrementado a cada `publisher.publish()`), `uptime_seconds` calculado a partir de `time.time()` no start do processo; atualizar estado compartilhado do `HealthStatus` a cada frame
- [X] T019 [US3] Criar `app/service/supervisord.conf` com: `[program:service]`, `command=python3 main.py`, `directory=%(here)s`, `autorestart=true`, `startretries=10`, `stopwaitsecs=5`, `stdout_logfile=logs/service.log`, `stderr_logfile=logs/service-err.log`, `environment=PYTHONUNBUFFERED=1`

**Checkpoint US3**: `supervisorctl status` mostra serviço rodando; `kill -9` no processo → supervisord reinicia em < 5s; desconexão USB → reconexão automática sem intervenção.

---

## Phase Final: Polish e Operação

**Objetivo**: Shutdown gracioso, logging estruturado e script de diagnóstico para uso na feira.

- [X] T020 [P] Implementar shutdown gracioso em `app/service/main.py`: capturar `SIGINT` e `SIGTERM` com `signal.signal()`; ao receber sinal: parar loop de captura, fechar socket ZMQ (`publisher.close()`), liberar câmera (`camera.release()`), aguardar thread FastAPI finalizar com timeout de 2s, logar shutdown com uptime total
- [X] T021 [P] Implementar logging estruturado JSON em `app/service/main.py` e todos os módulos: cada log entry contém `timestamp`, `level`, `module`, `message` e campos extras relevantes (ex: `fps`, `device_index`, `frames_published`); usar `logging.getLogger(__name__)` com `json` formatter; nível configurável via env var `LOG_LEVEL` (default: `INFO`)
- [X] T022 Criar `app/service/discover_camera.py` — script standalone de diagnóstico: itera índices 0–9 com `cv2.VideoCapture(i)`, imprime índice, resolução detectada e nome do dispositivo quando disponível; usado pelo operador na feira para confirmar índice correto da C925e antes de iniciar o serviço

---

## Dependências entre User Stories

```
Phase 1 (Setup)
    └── Phase 2 (Fundacional: models.py + config.py)
            ├── Phase 3 (US1: MVP — camera + inference + annotator + publisher + main)
            │       └── Phase 4 (US2: api.py + config runtime — depende de main.py existir)
            │               └── Phase 5 (US3: reconexão + health state machine + supervisord)
            │                       └── Phase Final (shutdown gracioso + logging + discover)
            └── (Phase 4 e 5 também dependem de Phase 3)
```

## Exemplos de Execução em Paralelo

### Dentro de Phase 3 (US1)
T007 (`camera.py`), T008 (`inference.py`), T009 (`annotator.py`), T010 (`publisher.py`) são todos independentes entre si — podem ser implementados em paralelo. T011 (`main.py`) depende de todos os quatro.

### Dentro de Phase 4 (US2)
T012 (`api.py` esqueleto) e T013 (`POST /config`) podem ser feitos em sequência dentro de `api.py`. T014 e T015 dependem de T012/T013 e do `main.py` (T011).

### Dentro de Phase 5 (US3)
T016 (`camera reconnect`) e T017 (`health state machine`) são independentes entre si — podem ser implementados em paralelo.

## Estratégia de Implementação

**MVP (Phase 1 + 2 + 3)**: 10 tarefas — entrega um serviço funcional que captura, processa e publica via ZMQ. Validável manualmente com o consumer de referência do `quickstart.md`. Suficiente para demonstrar a demo para o backend.

**Incremento 2 (Phase 4)**: +4 tarefas — adiciona controle em runtime para ajuste durante a feira (Risco R-001 da constituição).

**Incremento 3 (Phase 5 + Final)**: +6 tarefas — garante estabilidade de 8h (Princípio III da constituição).

## Resumo

| Fase | Tarefas | User Story | Paralelizáveis |
|---|---|---|---|
| Setup | T001–T004 | — | T003, T004 |
| Fundacional | T005–T006 | — | T006 |
| US1 MVP | T007–T011 | US1 | T007, T008, T009, T010 |
| US2 | T012–T015 | US2 | T012 |
| US3 | T016–T019 | US3 | T016, T017 |
| Polish | T020–T022 | — | T020, T021 |
| **Total** | **22 tarefas** | **3 stories** | **10 paralelizáveis** |
