<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0 — Initial ratification; no prior version exists.

Modified principles: N/A
Added sections:
  - Core Principles (6 principles → 7 principles)
  - VII. Demo-Mode: Sem Testes Automatizados (1.1.0)
  - Restrições Técnicas de Stack Mandatório
  - Critérios de Aceitação e Gestão de Riscos
  - Governance

Removed sections: N/A

Templates requiring updates:
  - .specify/templates/plan-template.md  ✅ Aligned — Constitution Check gate é genérico e aplica
  - .specify/templates/spec-template.md  ✅ Aligned — Success Criteria mapeia para AC-001/AC-002
  - .specify/templates/tasks-template.md ✅ Aligned — Não gerar tarefas de teste por padrão (Princípio VII)

Follow-up TODOs: Remover tasks de teste do tasks.md da 001-python-vision-service quando gerado.
-->

# Feira CV Demo Constitution

## Core Principles

### I. Demo-First: Impacto Visual é o Objetivo

Toda decisão de arquitetura, tecnologia ou funcionalidade DEVE ser avaliada pelo critério:
"isso contribui para a experiência 'uau' do visitante?". Complexidade técnica que não se
traduz em qualidade visual, fluidez de vídeo ou riqueza de inferência é proibida.
Funcionalidades de back-office, dashboards administrativos e logs verbosos não podem
adicionar overhead perceptível ao pipeline de demonstração.

**Rationale**: O sistema existe para 8 horas de feira. O sucesso é medido por visitantes
impressionados, não por elegância de código. Cada tradeoff deve favorecer a demo.

### II. Latência Zero-Compromisso (NON-NEGOTIABLE)

A cadeia de transporte de vídeo DEVE usar exclusivamente **ZMQ** (frames Python → FastAPI)
e **WebRTC** (FastAPI → browser React). Protocolos alternativos como HLS, MJPEG, RTSP
ou WebSocket com payload base64 são PROIBIDOS no caminho crítico de vídeo. Nenhuma
conveniência de desenvolvimento ou facilidade de prototipagem justifica a substituição
desses protocolos.

**Rationale**: HLS introduz buffer de latência de 2–30s; MJPEG satura largura de banda
com latência variável elevada. A premissa da demo é "em tempo real" — qualquer atraso
visível destrói a percepção de IA ativa diante do visitante.

### III. Estabilidade de 8 Horas (NON-NEGOTIABLE)

O sistema DEVE operar de forma contínua e autônoma durante toda a duração da feira
(mínimo 8 horas consecutivas) sem intervenção manual. Todo serviço DEVE implementar:

- Health-check endpoint com auto-restart via supervisor (systemd ou supervisord);
- Tratamento de exceções em todos os loops de captura e inferência;
- Graceful degradation: falha de inferência não pode travar o stream de vídeo.

**Rationale**: A equipe técnica não pode monitorar continuamente durante a feira.
Uma falha sem recovery automático encerra a demo publicamente e de forma definitiva.

### IV. 24 FPS Mínimo no Browser

A pipeline completa YOLO → ZMQ → FastAPI → WebRTC DEVE entregar ≥ 24 FPS medidos
no cliente React. Otimizações de modelo (quantização, ajuste de resolução de inferência,
redução de batch size) são válidas e encorajadas se mantiverem ou aumentarem o FPS.
Degradações abaixo desse limiar DEVEM acionar alertas visíveis no painel de operação.

**Rationale**: Abaixo de 24 FPS o vídeo deixa de parecer "tempo real" para o visitante,
comprometendo diretamente o objetivo de impacto e a credibilidade da solução.

### V. Infraestrutura Controlada: Rede Cabeada Obrigatória

Todo hardware do stand (servidor de inferência, display, câmera) DEVE estar conectado
via **Ethernet cabeada**. Wi-Fi é PROIBIDO no caminho crítico de dados. Dependências de
redes públicas do pavilhão (DNS externo, APIs em nuvem) são proibidas durante a demo.
Todos os modelos YOLO e assets visuais DEVEM ser carregados e armazenados localmente.

**Rationale**: Redes Wi-Fi de pavilhões industriais estão sujeitas a saturação severa
com centenas de dispositivos simultâneos. Uma queda de rede derrubaria toda a demo.

### VI. Degradação Graciosa sob Condições Adversas

O serviço YOLO DEVE expor um endpoint de configuração em runtime para ajuste de
`confidence_threshold`, `brightness_offset` e parâmetros de exposição/foco da webcam
via controles de câmera por software (macOS: `cv2.CAP_PROP_*` via AVFoundation; Linux: v4l2-ctl / UVC). O operador DEVE conseguir reconfigurar esses parâmetros sem reiniciar
nenhum serviço. O stream de vídeo DEVE continuar exibindo frames mesmo que a taxa de
detecção caia a zero.

**Rationale**: A iluminação de pavilhões industriais é imprevisível — luz fluorescente
pulsante, excesso de backlight e sombras dinâmicas são comuns. Ajuste em runtime é a
única forma de correção sem interromper a demo perante o público.

### VII. Demo-Mode: Sem Testes Automatizados (NON-NEGOTIABLE)

Este projeto é uma **demonstração** com prazo de entrega imediato para uma feira
industrial. Testes automatizados (unitários, de integração, de contrato) **NÃO DEVEM
ser escritos ou cobrados** em nenhuma feature. O investimento de tempo em testes
automatizados é proibido enquanto esta constituição estiver vigente.

A validação de qualidade é feita exclusivamente por:
- Execução manual do serviço com a câmera conectada;
- Verificação visual de bounding boxes e FPS no stream;
- Checklist de validação pré-feira (soak test de 8h operado manualmente).

O campo `Testing` no `plan.md` DEVE ser preenchido com `N/A — Demo-Mode (Princípio VII)`.
O `tasks.md` NÃO DEVE conter nenhuma tarefa de teste.

**Rationale**: O custo de escrever testes confiáveis para um pipeline de vídeo em tempo
real (mock de câmera, sincronização ZMQ, timing de FPS) é desproporcional ao benefício
numa demo de 8 horas. O tempo é melhor investido em robustez operacional do pipeline.

## Restrições Técnicas de Stack Mandatório

O stack abaixo é fixo e não pode ser substituído sem aprovação formal de emenda a esta
constituição. Qualquer desvio DEVE ser registrado na tabela de violações do `plan.md`.

| Camada | Tecnologia | Versão Mínima | Justificativa |
|---|---|---|---|
| Captura | Webcam Logitech USB (UVC) | — | Suporte nativo a foco e exposição via software (V4L2/UVC) |
| Engine IA | Python + YOLO (Ultralytics) | YOLOv8+ | Inferência em tempo real; suporte a GPU e CPU |
| Mensageria | ZMQ (PyZMQ) | 25+ | Latência < 5ms frame-to-frame em loopback local |
| Backend API | FastAPI | 0.100+ | I/O assíncrono nativo; integração direta com aiortc/WebRTC |
| Streaming | WebRTC (aiortc ou equivalente) | — | Latência ponta-a-ponta < 300ms câmera → browser |
| Frontend | React | 18+ | Interface responsiva, reativa e de alto desempenho visual |

**Proibições explícitas**:

- Nenhum broker de mensageria pesado (RabbitMQ, Kafka) para o pipeline de frames;
- Nenhum protocolo de vídeo com buffering (HLS, DASH, RTSP com buffer);
- Nenhuma dependência obrigatória de serviços externos em runtime de demo.

## Critérios de Aceitação e Gestão de Riscos

### Critérios de Aceitação (Definition of Done para a Demo)

| ID | Critério | Como Medir |
|---|---|---|
| AC-001 | Sistema opera por 8h sem intervenção manual | Teste de soak local pré-feira: rodar 8h + inspecionar logs |
| AC-002 | FPS ≥ 24 no browser React | Overlay de FPS no frontend ou DevTools do browser |
| AC-003 | Latência percebida câmera → browser < 300ms | Relógio físico na cena comparado ao timestamp exibido |
| AC-004 | Auto-restart em crash de qualquer serviço | Matar processos manualmente em teste pré-feira e observar recovery |
| AC-005 | Ajuste de parâmetros YOLO sem restart de serviço | Chamar endpoint de configuração e confirmar efeito no stream ao vivo |

### Registro de Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| R-001 | Iluminação instável do pavilhão degradando YOLO | Alta | Alto | Princípio VI: ajuste runtime; testar com luz adversa pré-feira |
| R-002 | Saturação de Wi-Fi no pavilhão | Alta | Crítico | Princípio V: Ethernet obrigatória; Wi-Fi proibido no caminho crítico |
| R-003 | Queda de FPS por CPU/GPU sobrecarregado | Média | Alto | Princípio IV: monitorar FPS; quantizar model se necessário |
| R-004 | Crash silencioso de serviço durante demo | Baixa | Crítico | Princípio III: supervisor com auto-restart + health-check endpoint |
| R-005 | Desconexão USB da webcam durante o evento | Baixa | Alto | Porta USB 3.0 dedicada; cabo USB travado fisicamente ao stand |

## Governance

Esta constituição é o documento de mais alta autoridade técnica do projeto. DEVE ser
consultada antes de qualquer decisão de arquitetura, escolha de tecnologia ou adição de
dependência. Em caso de conflito entre esta constituição e qualquer outro documento,
esta constituição prevalece.

**Procedimento de Emenda**:

1. Proposta escrita descrevendo a mudança e o impacto nos princípios existentes;
2. Análise de impacto nos critérios de aceitação (AC-001 a AC-005);
3. Aprovação explícita do Product Owner Técnico;
4. Incremento de versão conforme política abaixo;
5. Atualização dos templates dependentes (plan, spec, tasks).

**Política de Versionamento** (SemVer):

- **MAJOR**: Remoção ou redefinição incompatível de princípio ou proibição explícita;
- **MINOR**: Adição de princípio, seção ou expansão material de critério de aceitação;
- **PATCH**: Revisões de texto, clarificações, correções sem mudança semântica.

**Revisão de Compliance**:

- Cada feature DEVE passar pelo "Constitution Check" no `plan.md` antes de iniciar implementação;
- O checklist DEVE validar: stack mandatório respeitado, latência garantida, estabilidade prevista.

**Version**: 1.1.0 | **Ratified**: 2026-03-08 | **Last Amended**: 2026-03-08
