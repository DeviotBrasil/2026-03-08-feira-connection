# Feature Specification: Backend ZMQ → WebRTC

**Feature Branch**: `002-zmq-backend`  
**Created**: 2026-03-08  
**Status**: Ready for Implementation  
**Input**: User description: "criar backend para consultar video em ZMQ e disponibilizar em WebRTC"

## Contexto

O serviço de visão computacional (feature 001) captura frames da webcam, executa inferência YOLO e publica frames anotados via ZMQ. Esta feature implementa o backend FastAPI responsável por:

1. Subscrever os frames anotados publicados via ZMQ pelo serviço de visão;
2. Disponibilizá-los em tempo real no browser por meio de WebRTC.

Este backend é o elo central da cadeia de transporte de vídeo definida na constituição: **ZMQ → FastAPI → WebRTC → React**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stream de Vídeo Anotado no Browser (Priority: P1)

O operador da demo acessa a URL do backend no browser e visualiza imediatamente o feed de vídeo ao vivo com bounding boxes do YOLO sobrepostos, em tempo real e sem atraso perceptível.

**Why this priority**: Este é o objetivo central da demo. Sem este fluxo funcionando, não há produto demonstrável para o visitante da feira.

**Independent Test**: Com o serviço de visão publicando frames via ZMQ, abrir a página do frontend React, completar o handshake WebRTC e confirmar que o vídeo anotado aparece fluidamente no browser.

**Acceptance Scenarios**:

1. **Given** o serviço de visão está publicando frames via ZMQ e o backend está em execução, **When** o browser React realiza o handshake WebRTC (offer/answer), **Then** o vídeo anotado com bounding boxes é exibido continuamente no browser com latência ≤ 300ms câmera→browser (conforme SC-001).
2. **Given** o stream WebRTC está ativo no browser, **When** a câmera captura movimento ao vivo, **Then** o movimento aparece no browser com atraso máximo de 300ms percebido visualmente.
3. **Given** o stream está ativo, **When** o YOLO detecta um objeto, **Then** o bounding box aparece no frame exibido no browser no mesmo instante em que o objeto está visível.

---

### User Story 2 - Resiliência a Reinício do Serviço de Visão (Priority: P2)

O backend se recupera automaticamente quando o serviço de visão (ZMQ publisher) é reiniciado, sem necessidade de reiniciar o backend ou reconectar o browser manualmente.

**Why this priority**: Durante 8 horas de feira, o serviço de visão pode reiniciar por crash ou recarga de configuração. O backend não pode exigir intervenção manual para restabelecer o stream.

**Independent Test**: Com o stream WebRTC ativo no browser, reiniciar o processo do serviço de visão e observar que o stream retorna automaticamente sem fechar/reabrir o browser.

**Acceptance Scenarios**:

1. **Given** o stream WebRTC está ativo no browser, **When** o serviço de visão é reiniciado (processo encerrado e relançado), **Then** o backend reconecta ao ZMQ automaticamente e o stream é retomado no browser em até 5 segundos sem ação do operador.
2. **Given** o serviço de visão está indisponível no startup do backend, **When** o serviço de visão fica disponível posteriormente, **Then** o backend detecta a disponibilidade e inicia a subscrição ZMQ sem restart manual.

---

### User Story 3 - Monitoramento de Saúde e Auto-restart (Priority: P3)

O supervisor (supervisord) monitora a saúde do backend e o reinicia automaticamente em caso de falha, sem intervenção humana durante a demo.

**Why this priority**: A demo precisa operar autônoma por 8h. O backend deve ser tão resiliente quanto qualquer outro serviço do sistema.

**Independent Test**: Matar o processo do backend manualmente e confirmar que o supervisord o relança e o endpoint `/health` volta a responder dentro de 10 segundos.

**Acceptance Scenarios**:

1. **Given** o backend está em execução, **When** uma requisição GET é feita ao endpoint `/health`, **Then** a resposta indica o estado atual do backend (ativo, status da conexão ZMQ, número de peers WebRTC conectados).
2. **Given** o backend encerrou inesperadamente, **When** o supervisord detecta a falha, **Then** o backend é relançado automaticamente e retoma o funcionamento normal sem intervenção manual.

---

### Edge Cases

- O serviço de visão não está disponível quando o backend inicia → backend aguarda e reativa a conexão ZMQ automaticamente quando o publisher aparecer.
- Um browser desconecta abruptamente (aba fechada, queda de rede) → backend libera o peer connection sem crash e outros streams continuam normais.
- A fila ZMQ acumula frames (consumer lento) → backend descarta frames antigos para manter latência mínima; jamais bloqueia em espera de fila.
- Dois browsers abrem conexão WebRTC simultaneamente → ambos recebem o mesmo stream com qualidade equivalente.
- O serviço de visão envia um frame malformado ou vazio → backend ignora/descarta o frame sem encerrar o loop de leitura.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O backend DEVE subscrever o socket ZMQ publicado pelo serviço de visão e receber continuamente os frames anotados.
- **FR-002**: O backend DEVE expor endpoints de sinalização WebRTC (offer/answer SDP e troca de ICE candidates) para que browsers React possam estabelecer conexão.
- **FR-003**: O backend DEVE encaminhar cada frame recebido via ZMQ para todas as peer connections WebRTC ativas, mantendo throughput mínimo de 24 FPS no caminho de saída.
- **FR-004**: O backend DEVE suportar ao menos 2 peer connections WebRTC simultâneas sem degradação de qualidade em nenhuma delas.
- **FR-005**: O backend DEVE expor um endpoint `/health` que retorna o estado do serviço: status da conexão ZMQ, número de peers ativos e FPS recente.
- **FR-006**: O backend DEVE reconectar ao ZMQ automaticamente, sem restart do processo, sempre que a conexão for interrompida.
- **FR-007**: O backend DEVE ser configurável via supervisor (supervisord) com auto-restart em caso de crash.
- **FR-008**: O backend DEVE liberar recursos de peer connection WebRTC quando um browser se desconectar, seja por encerramento normal ou queda abrupta.
- **FR-009**: O backend DEVE descartar frames ZMQ acumulados na fila quando estiver atrasado, priorizando sempre o frame mais recente para minimizar latência.
- **FR-010**: O backend DEVE continuar operando (recebendo ZMQ, servindo health) mesmo que não haja nenhum peer WebRTC conectado no momento.

### Key Entities

- **VideoFrame**: Frame de vídeo anotado recebido via ZMQ; contém os bytes da imagem codificada e o timestamp de captura.
- **PeerConnection**: Representa uma conexão WebRTC ativa com um browser cliente; mantém o estado do canal de mídia e o ciclo de vida da negociação SDP/ICE.
- **ZMQSubscriber**: Componente responsável pela subscrição do socket ZMQ, recebimento contínuo de frames e notificação ao distribuidor de peers.
- **FrameDistributor**: Componente que recebe frames do ZMQSubscriber e os encaminha para todas as PeerConnections ativas.

## Assumptions

- O serviço de visão (001) publica frames em um socket ZMQ no endereço e porta configurados por variável de ambiente (padrão: `tcp://localhost:5555`).
- O formato dos frames ZMQ segue o contrato definido em `specs/001-python-app/service/contracts/zmq-frame-contract.md`.
- A sinalização WebRTC (offer/answer/ICE) ocorre via requisições HTTP ao backend FastAPI; não é necessário um servidor de sinalização separado.
- A demo opera em rede local cabeada; não há NAT traversal complexo — ICE com candidatos host é suficiente.
- O backend roda na mesma máquina ou na mesma LAN que o serviço de visão.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A latência ponta-a-ponta câmera → browser medida visualmente é inferior a 300ms (conforme AC-003 da constituição).
- **SC-002**: O stream WebRTC entrega ≥ 24 FPS medidos no browser cliente com o overlay de FPS do frontend React (conforme AC-002 da constituição).
- **SC-003**: O backend retoma automaticamente o stream ZMQ em até 5 segundos após reinício do serviço de visão, sem ação do operador.
- **SC-004**: O backend opera continuamente por 8 horas seguidas sem intervenção manual em condições de demo (conforme AC-001 da constituição).
- **SC-005**: O endpoint `/health` responde em menos de 200ms à qualquer momento durante a operação normal.
