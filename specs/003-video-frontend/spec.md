# Feature Specification: Frontend React — Visualização de Vídeo WebRTC

**Feature Branch**: `003-video-frontend`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "implementar um frontend para exibir o video do backend"

## Contexto

O sistema de visão computacional (feature 001) captura frames da webcam com inferência YOLO e os publica via ZMQ. O backend (feature 002) consome esses frames e os disponibiliza via WebRTC. Esta feature implementa a camada final da cadeia de transporte: a interface web que o operador e os visitantes da feira utilizam para visualizar o feed de vídeo ao vivo com as anotações do YOLO.

A cadeia completa é: **câmera → YOLO → ZMQ → WebRTC Backend → Frontend Web → Visitante da feira**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualização do Stream de Vídeo ao Vivo (Priority: P1)

O operador ou visitante da feira abre a página web do frontend e visualiza imediatamente o feed de vídeo ao vivo com as detecções YOLO sobrepostas, sem necessidade de configuração ou conhecimento técnico.

**Why this priority**: É o objetivo central da demo. Sem exibir o vídeo, o frontend não entrega valor algum. Todas as demais stories são melhorias incrementais sobre essa funcionalidade central.

**Independent Test**: Com o backend em execução e o service publicando frames, abrir o frontend em um browser, aguardar a conexão WebRTC ser estabelecida automaticamente e confirmar que o vídeo anotado aparece continuamente na tela.

**Acceptance Scenarios**:

1. **Given** o backend está em execução na rede local e o service está publicando frames via ZMQ, **When** o usuário abre o frontend no browser, **Then** o stream de vídeo começa a ser exibido em até 5 segundos sem nenhuma interação do usuário.
2. **Given** o stream de vídeo está sendo exibido, **When** um objeto é detectado pelo YOLO, **Then** o bounding box do objeto é visível no vídeo exibido no frontend.
3. **Given** o stream está ativo, **When** o usuário observa o vídeo, **Then** o atraso percebido entre o movimento real e o movimento na tela é menor que 300ms.
4. **Given** o stream está ativo, **When** a página é carregada em uma tela de projeção ou monitor grande, **Then** o vídeo ocupa a maior parte da área útil da tela de forma responsiva.

---

### User Story 2 - Indicadores de Status da Conexão e do Sistema (Priority: P2)

O operador da demo consegue verificar a qualquer momento se o sistema está funcionando corretamente, sem precisar acessar logs ou terminais.

**Why this priority**: Durante 8 horas de feira, o operador precisa monitorar visualmente que tudo está funcionando. Indicadores claros permitem detectar e resolver problemas rapidamente.

**Independent Test**: Com o stream ativo, o operador observa o contador de FPS e o indicador de status ZMQ. Ao parar o service, o frontend indica imediatamente a degradação do sistema.

**Acceptance Scenarios**:

1. **Given** o stream WebRTC está ativo, **When** o operador olha para o frontend, **Then** um contador de FPS atualizado ao vivo é visível na tela.
2. **Given** o service pára de publicar frames (ZMQ desconectado), **When** o frontend consulta o endpoint `/health`, **Then** um alerta visível indica que o serviço de visão está indisponível.
3. **Given** o backend está respondendo ao `/health`, **When** o frontend exibe o painel de status, **Then** são exibidos: status geral (ok/degraded), número de peers conectados e FPS medido pelo backend.
4. **Given** o stream WebRTC foi interrompido (conexão perdida), **When** o frontend detecta a desconexão, **Then** um indicador visual de status muda para "desconectado" em vermelho.

---

### User Story 3 - Reconexão Automática após Desconexão (Priority: P3)

Quando a conexão WebRTC é perdida (por reinício do backend, oscilação de rede ou timeout), o frontend tenta reconectar automaticamente sem necessidade de intervenção do operador.

**Why this priority**: Em uma demo de 8 horas, interrupções e reconexões manuais são inaceitáveis. A autonomia operacional é fundamental para exibições em feiras.

**Independent Test**: Com o stream ativo, reiniciar o backend e observar que o frontend detecta a desconexão, exibe um indicador de "reconectando" e restabelece o stream automaticamente em até 10 segundos.

**Acceptance Scenarios**:

1. **Given** o stream WebRTC está ativo, **When** o backend é reiniciado, **Then** o frontend detecta a desconexão e inicia tentativas de reconexão automáticas.
2. **Given** o frontend está tentando reconectar, **When** o backend fica disponível novamente, **Then** o stream é restabelecido automaticamente e o vídeo volta a ser exibido em até 10 segundos.
3. **Given** o frontend está tentando reconectar, **When** o backend permanece indisponível por mais de 30 segundos, **Then** o frontend exibe uma mensagem clara indicando que o backend não está acessível e continua tentando em intervalos regulares.

---

### Edge Cases

- O que acontece se o backend retornar erro HTTP ao receber o offer WebRTC?
- O que acontece se o browser não suportar WebRTC?
- O que acontece se o stream de vídeo chegar com resolução diferente da esperada?
- O que acontece se o usuário fechar a aba e reabrir (nova conexão WebRTC)?
- O que acontece se dois usuários acessarem o frontend simultaneamente (múltiplos peers)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O frontend DEVE estabelecer a conexão WebRTC com o backend via handshake offer/answer no endpoint `/offer` sem interação do usuário ao carregar a página.
- **FR-002**: O frontend DEVE exibir o stream de vídeo ao vivo recebido via WebRTC em um elemento de vídeo visível na página.
- **FR-003**: O frontend DEVE exibir um contador de FPS calculado a partir dos frames de vídeo recebidos, atualizado pelo menos a cada segundo.
- **FR-004**: O frontend DEVE exibir o status atual da conexão WebRTC (conectando, conectado, desconectado, reconectando) com diferenciação visual por cor.
- **FR-005**: O frontend DEVE consultar o endpoint `/health` do backend periodicamente (a cada 5 segundos) e exibir as métricas retornadas (status ZMQ, peers ativos, FPS do backend).
- **FR-006**: O frontend DEVE exibir um alerta visível quando o status ZMQ do backend for `degraded`.
- **FR-007**: O frontend DEVE tentar reconectar automaticamente quando a conexão WebRTC for perdida, com espera de 3 segundos entre tentativas.
- **FR-008**: O frontend DEVE funcionar nos browsers modernos (Chrome, Firefox, Safari) sem nenhuma instalação ou plugin adicional.
- **FR-009**: O frontend DEVE adaptar o tamanho do vídeo à tela disponível, priorizando a exibição em telas grandes (projetores, monitores).
- **FR-010**: O frontend DEVE exibir o endereço do backend configurável via variável de ambiente ou parâmetro de URL, permitindo apontar para diferentes instâncias sem alterar o código.

### Assumptions

- O backend WebRTC está acessível via HTTP em `localhost:8080` por padrão.
- O frontend é servido como arquivo estático (HTML + JS) sem necessidade de servidor Node.js dedicado.
- Não há autenticação entre frontend e backend — ambos estão na mesma rede local da feira (LAN).
- O browser que executa o frontend tem suporte completo a WebRTC (Chrome/Edge/Firefox modernos).
- O vídeo é sempre exibido sem som (stream mudo — apenas vídeo).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O vídeo começa a ser exibido em até 5 segundos após o carregamento da página, sem nenhuma interação do usuário.
- **SC-002**: O atraso percebido entre o movimento real na câmera e a exibição no browser é menor que 300ms (ponta a ponta: câmera → frontend).
- **SC-003**: O frontend exibe corretamente o stream em resolução nativa sem distorção em telas de até 1920×1080.
- **SC-004**: Após reinício do backend, o stream é restabelecido automaticamente em até 10 segundos.
- **SC-005**: O contador de FPS no frontend fica dentro de ±2 FPS do FPS reportado pelo backend no endpoint `/health`.
- **SC-006**: O frontend opera continuamente por 8 horas sem travar, vazar memória ou exigir reload manual.
- **SC-007**: Um visitante sem nenhum treinamento consegue entender o que está sendo exibido na tela (vídeo com detecções) em menos de 10 segundos.
