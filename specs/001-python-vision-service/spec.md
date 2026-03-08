# Feature Specification: Serviço Python de Visão Computacional

**Feature Branch**: `001-python-service`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "preciso criar um servico python para se conectar a uma camera usb identificar uma pessoa e disponibilizar o video analisando para um backend"

## Assumptions

- O modelo YOLO padrão usado é **YOLOv8n** (nano), otimizado para velocidade em CPU/GPU sem GPU obrigatória.
- O protocolo de transporte de frames entre este serviço e o backend é **ZMQ PUSH/PULL** (socket pattern um-para-um), conforme definido na constituição do projeto.
- Cada mensagem ZMQ é **multipart**: `[frame_bytes (JPEG), metadata_json]`, onde `metadata_json` contém as detecções do frame.
- A resolução de captura é **1280×720**; a resolução de inferência YOLO é **640×480** (redimensionamento interno para performance).
- A câmera é uma **Webcam Logitech USB (UVC)**, acessível via device index OpenCV (`cv2.VideoCapture(index)`) no macOS por meio do backend AVFoundation; o índice padrão é `1` (índice `0` = webcam interna do MacBook), configurável via variável de ambiente `CAMERA_DEVICE_INDEX`.
- A classe de detecção de interesse principal é **"person"** (COCO class 0), mas o serviço não filtra outras classes — inclui todas as detecções no payload.
- O serviço é gerenciado por **supervisord ou systemd** para auto-restart em crash.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stream de Detecção em Tempo Real (Priority: P1)

O operador inicia o serviço apontando para a câmera USB. O serviço captura frames continuamente,
executa inferência YOLO para detectar pessoas (e outros objetos) em cada frame, sobrepõe
bounding boxes e scores de confiança no frame, e publica via ZMQ o frame anotado junto com
os metadados de detecção estruturados para o backend consumir.

**Why this priority**: É o núcleo do produto. Sem este fluxo nenhuma outra funcionalidade
faz sentido. Entrega valor imediato e completo como MVP standalone — o backend pode consumir
e exibir resultados sem mais nada implementado.

**Independent Test**: Iniciar o serviço com uma câmera USB conectada e um consumidor ZMQ simples
(script Python com `zmq.PULL`). Confirmar que mensagens chegam com ≥ 24 FPS, que os frames
contêm bounding boxes visíveis ao redor de pessoas presentes na cena, e que o JSON de metadados
contém campos `detections`, `frame_id` e `timestamp`.

**Acceptance Scenarios**:

1. **Given** o serviço está rodando e a câmera USB está conectada, **When** uma pessoa entra no campo de visão, **Then** o serviço publica via ZMQ um frame JPEG com bounding box desenhado sobre a pessoa e um JSON com `class: "person"`, `confidence`, `bbox` dentro de 100ms da captura do frame.
2. **Given** nenhuma pessoa está no campo de visão, **When** o serviço está ativo, **Then** frames continuam sendo publicados via ZMQ com o campo `detections` como array vazio, sem interrupção do stream.
3. **Given** múltiplas pessoas estão no campo de visão simultaneamente, **When** o frame é processado, **Then** o JSON contém uma entrada de detecção para cada pessoa identificada, com bounding boxes individuais e scores de confiança distintos.
4. **Given** o sistema está sob carga contínua, **When** medido ao longo de 60 segundos, **Then** a taxa de publicação é de ≥ 24 mensagens por segundo no canal ZMQ.

---

### User Story 2 - Configuração de Câmera e YOLO em Runtime (Priority: P2)

O operador, durante a feira, percebe que a iluminação do pavilhão está degradando a qualidade
das detecções. Sem interromper o stream, ele acessa o endpoint de configuração do serviço,
ajusta o threshold de confiança do YOLO e os parâmetros de exposição da câmera. A mudança
tem efeito nos frames seguintes sem necessidade de reiniciar o serviço.

**Why this priority**: A iluminação de pavilhões industriais é imprevisível (Risco R-001 da
constituição). Sem ajuste em runtime, qualquer degradação exige parar a demo publicamente.
Implementável de forma independente como uma camada de controle sobre o US1.

**Independent Test**: Com o serviço rodando (US1 ativo), enviar uma requisição POST ao endpoint
de configuração alterando `confidence_threshold` de 0.5 para 0.3. Confirmar que nos frames
subsequentes (dentro de 1 segundo) detecções de menor confiança começam a aparecer no payload
ZMQ, sem nenhuma interrupção no stream de vídeo.

**Acceptance Scenarios**:

1. **Given** o serviço está publicando frames, **When** o operador envia `POST /config` com novo `confidence_threshold`, **Then** o serviço aplica o novo valor dentro de 500ms e retorna HTTP 200 com o estado atual da configuração.
2. **Given** o serviço está rodando, **When** o operador envia `POST /config` com parâmetros de exposição da câmera (brilho, exposição), **Then** a câmera ajusta esses parâmetros via controle UVC e o efeito é visível nos frames seguintes.
3. **Given** o operador envia um valor de configuração inválido (ex.: `confidence_threshold: 1.5`), **When** o serviço recebe a requisição, **Then** retorna HTTP 422 com descrição do erro e mantém a configuração anterior inalterada.
4. **Given** o operador reinicia o serviço após ajustar configurações, **When** o serviço sobe novamente, **Then** carrega as últimas configurações salvas (não volta aos defaults).

---

### User Story 3 - Resiliência e Health Monitoring (Priority: P3)

O operador precisa saber se o serviço está saudável durante as 8 horas da feira. Um monitor
externo (ou painel do backend) consulta periodicamente o health endpoint. Se a câmera for
desconectada acidentalmente (cabo puxado), o serviço entra em modo de reconexão e retoma
automaticamente quando a câmera é plugada novamente, sem intervenção do operador.

**Why this priority**: Crítico para a promessa de 8 horas da constituição (Princípio III),
mas depende dos US1 e US2 para ter algo a monitorar. Pode ser demonstrado de forma independente
simulando uma desconexão.

**Independent Test**: Com o serviço rodando, desconectar fisicamente a câmera USB. Confirmar
que o serviço não trava, que `GET /health` retorna `status: "reconnecting"` com HTTP 200,
e que ao reconectar a câmera o serviço retoma o stream em até 10 segundos sem nenhuma ação manual.

**Acceptance Scenarios**:

1. **Given** o serviço está rodando normalmente, **When** `GET /health` é chamado, **Then** retorna JSON com `status: "ok"`, `fps_measured`, `uptime_seconds` e `inference_ok`.
2. **Given** a câmera USB é desconectada, **When** o serviço detecta a perda de dispositivo, **Then** muda o status de health para `"reconnecting"`, registra o evento em log, e continua tentando reconectar a cada 2 segundos sem travar.
3. **Given** o serviço está em modo `"reconnecting"`, **When** a câmera é reconectada, **Then** o serviço retoma a captura e publicação ZMQ em até 10 segundos, voltando ao status `"ok"` sem intervenção do operador.
4. **Given** o processo do serviço é terminado abruptamente (kill -9), **When** o supervisor detecta o encerramento, **Then** o supervisor reinicia o processo em até 5 segundos.

---

### Edge Cases

- **Câmera não encontrada na inicialização**: Se a câmera não estiver acessível ao iniciar, o serviço loga o erro, aguarda em loop de retry (a cada 2 segundos) e NÃO termina com erro fatal — permitindo que a câmera seja conectada após o start do serviço.
- **Arquivo do modelo YOLO ausente**: Se o arquivo do modelo não existir no path configurado, o serviço termina imediatamente com código de saída não-zero e mensagem de erro clara no log (falha rápida e explícita, não silenciosa).
- **Backend ZMQ desconectado (sem consumer)**: O serviço continua publicando. O socket ZMQ PUSH com `SNDHWM` configurado descarta frames antigos se o buffer estourar, nunca bloqueando o loop de captura.
- **Queda de FPS por CPU sobrecarregado**: Quando FPS medido cai abaixo de 24, o serviço registra um warning no log a cada 30 segundos. O stream não é interrompido.
- **Inferência YOLO falha em um frame**: O frame é publicado com `detections: []` e `inference_error: true` no metadata. O loop continua sem interrupção.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O serviço DEVE capturar frames de uma câmera USB (UVC) a uma taxa alvo de ≥ 24 FPS.
- **FR-002**: O serviço DEVE executar inferência YOLO em cada frame capturado para detectar objetos, com foco em pessoas.
- **FR-003**: O serviço DEVE sobrepor nos frames as bounding boxes e scores de confiança de todas as detecções.
- **FR-004**: O serviço DEVE publicar cada frame processado via ZMQ como mensagem multipart contendo o frame codificado (JPEG) e um JSON com os metadados de detecção.
- **FR-005**: Os metadados de detecção DEVEM incluir: `frame_id`, `timestamp`, `fps_measured`, e array `detections` com `class`, `confidence`, `bbox (x, y, w, h)` por detecção.
- **FR-006**: O serviço DEVE expor um endpoint `GET /health` retornando status operacional, FPS medido, uptime e estado da inferência.
- **FR-007**: O serviço DEVE expor um endpoint `POST /config` para ajuste em runtime de `confidence_threshold` e parâmetros de câmera (brilho, exposição) **sem reiniciar o processo**.
- **FR-008**: O serviço DEVE persistir a configuração atual em arquivo local para que seja restaurada após restart.
- **FR-009**: O serviço DEVE tratar desconexão da câmera USB com retry automático a cada 2 segundos, sem travar nem encerrar.
- **FR-010**: O serviço DEVE continuar publicando frames (com `detections: []`) mesmo quando a inferência YOLO falhar temporariamente em um frame específico.
- **FR-011**: O serviço DEVE ser configurável via variáveis de ambiente: `CAMERA_DEVICE_INDEX`, `ZMQ_ENDPOINT`, `YOLO_MODEL_PATH`, `CONFIDENCE_THRESHOLD`, `INFERENCE_WIDTH`, `INFERENCE_HEIGHT`, `CAPTURE_WIDTH`, `CAPTURE_HEIGHT`, `JPEG_QUALITY`, `HTTP_PORT`.
- **FR-012**: O serviço DEVE emitir logs estruturados (JSON) com nível de severidade, para facilitar diagnóstico durante a feira.

### Key Entities

- **Frame**: Unidade de dado publicada via ZMQ. Contém o timestamp de captura, identificador sequencial, a imagem JPEG anotada e a lista de detecções.
- **Detection**: Resultado de uma detecção YOLO num frame. Possui classe identificada, score de confiança e coordenadas do bounding box (x, y, largura, altura) relativas à resolução do frame publicado.
- **ServiceConfig**: Estado de configuração mutável em runtime. Contém device da câmera, endpoint ZMQ, path do modelo, threshold de confiança, parâmetros de exposição/brilho e resolução de inferência. Persistido em arquivo local.
- **HealthStatus**: Snapshot do estado operacional em um instante. Contém status (ok/reconnecting/degraded), FPS médio dos últimos 30 frames, uptime em segundos e indicador de saúde da inferência (`inference_ok: bool`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O serviço entrega ≥ 24 frames anotados por segundo no canal ZMQ em condições normais de operação (câmera conectada, iluminação adequada).
- **SC-002**: O serviço opera por 8 horas consecutivas sem nenhuma intervenção manual, sem crash não-recuperado, confirmado por teste de soak pré-feira com log contínuo.
- **SC-003**: Alterações de configuração via `POST /config` têm efeito visível nos frames dentro de 500ms do recebimento da requisição.
- **SC-004**: Após reconexão física da câmera USB, o serviço retoma o stream em ≤ 10 segundos sem ação do operador.
- **SC-005**: Durante falha de inferência em frames individuais, zero frames são descartados — o stream de vídeo publicado no ZMQ é contínuo.
- **SC-006**: O endpoint `GET /health` responde em ≤ 100ms mesmo sob carga máxima de captura e inferência.
