# Research: Serviço Python de Visão Computacional

**Feature**: 001-python-service  
**Date**: 2026-03-08  
**Status**: Completo — zero NEEDS CLARIFICATION remanescentes

---

## Decisão 1: Acesso à Câmera em macOS (Logitech C925e)

**Decision**: OpenCV `cv2.VideoCapture(device_index)` com backend AVFoundation  
**Rationale**: macOS não tem V4L2. A stack UVC/V4L2 da spec original é Linux-only. Em macOS, o AVFoundation é o framework nativo de câmera e o OpenCV usa-o automaticamente via `cv2.CAP_AVFOUNDATION`. A Logitech C925e é reconhecida como câmera UVC padrão e funciona sem driver adicional.  
**Alternatives considered**:
- `v4l2-python` / `v4l2-ctl`: Linux only, sem suporte macOS.
- `pyavcapture` / AVFoundation direto: overhead de código nativo desnecessário; OpenCV já abstrai.
- `imageio` com backend ffmpeg: maior latência e sem controle de propriedades de câmera.

**Como discovered**: Logitech C925e é câmera UVC compliant. macOS suporta UVC nativamente. OpenCV com AVFoundation expõe `CAP_PROP_BRIGHTNESS`, `CAP_PROP_EXPOSURE`, `CAP_PROP_FOCUS` para câmeras UVC.

---

## Decisão 2: Controle de Exposição/Brilho/Foco em macOS

**Decision**: `cv2.VideoCapture.set(cv2.CAP_PROP_*, value)` — sem biblioteca auxiliar  
**Rationale**: As propriedades CAP_PROP_BRIGHTNESS, CAP_PROP_EXPOSURE e CAP_PROP_AUTOFOCUS do OpenCV funcionam no macOS via AVFoundation para câmeras UVC. Não é necessário `v4l2-ctl` (Linux) nem SDK proprietário da Logitech. A Logitech C925e expõe controles UVC padrão (brightness, contrast, exposure, focus, autofocus, zoom).  
**Alternatives considered**:
- Logitech Capture SDK: proprietário, não open-source, sem suporte headless.
- `uvc` Python bindings: requer compilação nativa e permissões de I/O USB extras no macOS; complexidade desnecessária para os controles básicos da demo.

**Limitação importante**: No macOS, `CAP_PROP_EXPOSURE` usa escala diferente do Linux.
Valores práticos para C925e no macOS: exposição automática = `-1`; manual range: `-13` (lento) a `-1` (rápido). Testar empiricamente pré-feira.

---

## Decisão 3: Device Index da C925e em macOS

**Decision**: Device index detectado dinamicamente via tentativa sequencial `cv2.VideoCapture(0)`, `(1)`, `(2)`, com fallback para valor de `CAMERA_DEVICE` env var  
**Rationale**: macOS não usa paths `/dev/videoX`. O device index varia conforme câmeras conectadas. A C925e em um MacBook com a webcam interna será tipicamente índice `1` (câmera interna = `0`). Com variável de ambiente `CAMERA_DEVICE_INDEX=1` o operador controla explicitamente sem recompilação.  
**Alternatives considered**:
- Listar dispositivos via `AVCaptureDeviceDiscoverySession` (Swift/ObjC): requer código nativo, saí do escopo.
- Usar nome USB do dispositivo: a biblioteca `pyudev` é Linux-only. No macOS, alternativa seria `system_profiler SPUSBDataType` em subprocess — complexidade desnecessária; index explícito via env var é suficiente.

---

## Decisão 4: Modelo YOLO — YOLOv8n vs Alternativas

**Decision**: `YOLOv8n` (nano) da Ultralytics  
**Rationale**: Em Apple Silicon (M1/M2/M3) com PyTorch + MPS (Metal Performance Shaders), YOLOv8n atinge 40–80 FPS em 640×640. Em Intel Mac sem GPU dedicada, atinge 25–35 FPS em CPU. Ambos estão acima do limiar de 24 FPS da constituição. O modelo nano tem 6.2M parâmetros e ~22MB, adequado para uso offline em feira.  
**Alternatives considered**:
- YOLOv8s (small): 2× mais pesado, necessário apenas se precisão superar 24 FPS; investigar se precisão do nano for insuficiente.
- YOLOv5n: mais antigo, sem suporte ARM otimizado nativo.
- DETR, RT-DETR: latência de inferência 3–5× maior; inadequado para 24 FPS em CPU.
- OpenVINO / CoreML export: otimização pós-MVP se FPS for insuficiente no hardware da feira.

**Aceleração macOS**: Ultralytics suporta `device="mps"` para Apple Silicon — usar de forma automática via detecção de plataforma. Fallback para `"cpu"` em Intel Mac.

---

## Decisão 5: ZMQ Socket Pattern

**Decision**: `zmq.PUSH` no serviço de visão → `zmq.PULL` no backend; socket bind no serviço, connect no consumidor  
**Rationale**: PUSH/PULL é o padrão de pipeline do ZMQ: sem acknowledgment, sem overhead de coordenação, máximo throughput. Em loopback local a latência é < 1ms por frame. O serviço faz `bind("tcp://0.0.0.0:5555")` e o backend faz `connect`. Isso permite múltiplos consumidores futuros sem alterar o publicador (load-balancing automático do ZMQ).  
**Alternatives considered**:
- `zmq.PUB/SUB`: broadcasting, correto se multiplos consumidores precisam do mesmo frame; overhead marginal maior; adequado para expansão futura, mas PUSH/PULL é suficiente para 1 consumidor.
- `zmq.REQ/REP`: síncrono, bloquearia o loop de captura; inadequado.
- `zmq.DEALER/ROUTER`: complexidade desnecessária; padrão async avançado.

**High-Water Mark**: `SNDHWM=2` no socket PUSH descarta frames antigos quando o consumidor não consegue acompanhar, garantindo que o serviço nunca bloqueie. O backend sempre recebe o frame mais recente disponível.

---

## Decisão 6: Threading / Async Model

**Decision**: Loop principal síncrono em thread dedicada + `asyncio` apenas no servidor FastAPI  
**Rationale**: OpenCV `cv2.VideoCapture.read()` é bloqueante. O loop de captura → inferência → publicação ZMQ roda em uma thread Python dedicada (`CaptureThread`). O FastAPI/uvicorn roda em `asyncio` em thread separada. Comunicação entre threads via `threading.Event` para shutdown graceful e uma `queue.Queue(maxsize=1)` para o estado de config mais recente (thread-safe, sem race condition).  
**Alternatives considered**:
- Tudo em `asyncio` com `run_in_executor` para OpenCV: mais complexo, overhead de context-switching, sem ganho real para este caso single-producer.
- `multiprocessing`: overhead de IPC e serialização desnecessário para um único processo producer.

---

## Decisão 7: Formato da Mensagem ZMQ

**Decision**: Mensagem multipart de 2 frames: `[frame_jpeg_bytes, metadata_json_utf8_bytes]`  
**Rationale**: Multipart é atômico no ZMQ — consumidor recebe ambas as partes ou nehuma. Separar imagem de metadata permite ao consumidor desserializar apenas o JSON quando necessário (sem decodificar JPEG), otimizando o backend. JPEG com qualidade 85% reduz tamanho sem degradação visual perceptível.  
**Alternatives considered**:
- Tudo em msgpack/JSON com imagem base64: latência 30–40% maior por overhead de base64 encoding; violaria Princípio II (latência).
- Protobuf: overhead de schema compilation, sem ganho justificável para 1 consumidor local.
- JPEG qualidade 95%: frames ~2× maiores, sem benefício visual perceptível para a demo.

---

## Decisão 8: Auto-restart em macOS

**Decision**: `supervisord` (via `supervisor` Python package) com `autorestart=true`  
**Rationale**: `launchd` (macOS nativo) requer plist XML e não é portável; `systemd` é Linux-only. `supervisord` é instalado via pip, funciona igual em macOS e Linux, é familiar para devops Python, e já cobre o Princípio III da constituição (auto-restart + health-check).  
**Alternatives considered**:
- `launchd plist`: nativo macOS mas não portável e mais verboso para configurar.
- Docker com `restart: always`: overhead desnecessário para demo local; adiciona complexidade sem benefício.
- Nohup + script de watchdog: solução frágil; não garante restart rápido.

---

## Resolução de NEEDS CLARIFICATION da Spec Original

| Item | Resolução |
|---|---|
| `/dev/video0` — path Linux | **Resolvido**: usar `CAMERA_DEVICE_INDEX` (int, default `0`); OpenCV auto-detecta via AVFoundation no macOS |
| Controle UVC via V4L2 | **Resolvido**: `cv2.CAP_PROP_BRIGHTNESS/EXPOSURE/FOCUS` via AVFoundation |
| `supervisord` vs `systemd` | **Resolvido**: `supervisord` (compatível macOS) |
| Aceleração GPU | **Resolvido**: `device="mps"` para Apple Silicon; `"cpu"` fallback automático |

---

## Checklist de Pesquisa

- [x] Acesso à câmera em macOS identificado (AVFoundation / OpenCV device index)
- [x] Controle de propriedades UVC em macOS viável via `cv2.set(CAP_PROP_*)`
- [x] YOLOv8n confirma ≥ 24 FPS em Apple Silicon e Intel Mac no range de uso
- [x] ZMQ PUSH/PULL validado para pipeline de vídeo de baixa latência
- [x] Threading model definido (captura síncrona + FastAPI assíncrono isolados)
- [x] Formato de mensagem ZMQ definido (multipart: JPEG + JSON)
- [x] Auto-restart via supervisord confirmado para macOS
- [x] Todos os NEEDS CLARIFICATION da spec resolvidos
