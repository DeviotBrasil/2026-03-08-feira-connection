# Feature Specification: Interface Moderna com Ant Design e CSS Modules

**Feature Branch**: `004-antd-modern-ui`  
**Created**: 2026-03-09  
**Status**: Draft  
**Input**: User description: "quero adcionar lib do antdesign e css module no projeto de front deixe a aplicacao moderna e responsiva"

## Contexto

O frontend atual (React 19 + Vite + TypeScript) exibe um stream de vídeo WebRTC com painel de saúde e barra de status. A estilização é 100% feita via `style` inline e variáveis CSS globais no `App.tsx`. Este feature substitui esse padrão por Ant Design como sistema de componentes e CSS Modules como solução de escopo de estilo, tornando a interface moderna, responsiva e fácil de manter.

## Assumptions

- O projeto permanece com React 19 + Vite + TypeScript без substituição do bundler.
- Ant Design v5 (versão LTS atual) será utilizada — suporta CSS-in-JS nativo e tema via `ConfigProvider`.
- CSS Modules são suportados nativamente pelo Vite (sem configuração extra).
- Os componentes `Header`, `VideoPlayer`, `StatusBar` e `HealthPanel` serão migrados individualmente.
- O backend não é alterado — apenas a camada visual do frontend.
- A identidade visual atual (tema escuro, esquema de cores) será preservada e mapeada para tokens do Ant Design.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualizar Dashboard Modernizado (Priority: P1)

Um operador abre o dashboard de monitoramento de câmeras no navegador e encontra uma interface organizada com componentes visuais consistentes (cabeçalho, painel de saúde, player de vídeo e barra de status) que comunicam claramente o estado do sistema.

**Why this priority**: É a entrega nuclear do feature — sem isso, nenhuma melhoria visual existe. Qualquer outro story depende desta base estar funcionando.

**Independent Test**: Pode ser testado subindo apenas o frontend (`npm run dev`), abrindo o browser e verificando se a página renderiza com layout estruturado e sem erros visuais.

**Acceptance Scenarios**:

1. **Given** o usuário abre a aplicação no navegador, **When** a página carrega, **Then** o layout exibe cabeçalho, área de vídeo, painel de saúde e barra de status dispostos de forma legível e sem sobreposição.
2. **Given** o usuário abre a aplicação, **When** o carregamento completa, **Then** nenhum estilo inline bruto é visível — todos os componentes usam classes do sistema de design.
3. **Given** o sistema está com backend offline, **When** o usuário abre a página, **Then** os componentes de status exibem indicadores visuais claros de indisponibilidade (badges de erro, ícones).

---

### User Story 2 - Experiência Responsiva em Diferentes Dispositivos (Priority: P2)

Um usuário acessa o dashboard em um tablet ou tela menor e a interface se adapta automaticamente — o vídeo redimensiona, os painéis não transbordam e o texto permanece legível.

**Why this priority**: O deploy do sistema pode acontecer em estações de controle com monitores variados. Responsividade evita que a UI quebre em resoluções menores.

**Independent Test**: Pode ser testado abrindo o DevTools do browser, ativando modo responsivo e alternando entre larguras de 320px, 768px e 1280px — validável independentemente de backend.

**Acceptance Scenarios**:

1. **Given** o usuário acessa em viewport de 768px ou menor, **When** a página carrega, **Then** todos os elementos são visíveis sem rolagem horizontal.
2. **Given** o usuário acessa em viewport de 1280px ou maior, **When** a página carrega, **Then** o player de vídeo ocupa o espaço central com proporção adequada e os painéis laterais ou inferiores são visíveis.
3. **Given** qualquer tamanho de tela, **When** o usuário redimensiona a janela, **Then** o layout se reorganiza fluidamente sem elementos sobrepostos.

---

### User Story 3 - Tema Visual Consistente e Personalizável (Priority: P3)

Um desenvolvedor do time deseja ajustar cores primárias ou tokens do tema (ex: cor de destaque, tom de fundo) sem ter que alterar CSS em vários arquivos espalhados pelo projeto.

**Why this priority**: Garante manutenibilidade futura. O time precisará ajustar a identidade visual conforme o produto evolui. Depende do P1 estar concluído.

**Independent Test**: Pode ser testado alterando um único token de tema (ex: cor primária) e verificando se todos os componentes refletem a mudança sem edições adicionais.

**Acceptance Scenarios**:

1. **Given** o desenvolvedor altera a cor primária no ponto central de configuração de tema, **When** o app é recarregado, **Then** todos os componentes que usam cor primária refletem a nova cor.
2. **Given** o tema escuro está ativo, **When** o usuário visualiza o dashboard, **Then** todos os componentes mantêm contraste adequado de leitura (texto sobre fundo).

---

### Edge Cases

- O que acontece quando o componente `VideoPlayer` recebe `null` como ref antes do stream conectar? Os placeholders visuais devem ser exibidos corretamente.
- Como o layout se comporta quando o `HealthPanel` recebe uma lista vazia ou undefined de serviços? Deve exibir um estado vazio explícito.
- Em telas muito largas (>2560px, monitores 4K), o vídeo não deve se esticar além de sua largura máxima definida.
- Se o Ant Design não carregar (CDN offline, erro de build), a página não deve quebrar completamente — conteúdo textual deve permanecer legível.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A aplicação DEVE ter o Ant Design v5 instalado e configurado como biblioteca de componentes principal.
- **FR-002**: Cada componente (`Header`, `VideoPlayer`, `StatusBar`, `HealthPanel`) DEVE ter seu próprio arquivo `.module.css` para escopar estilos locais.
- **FR-003**: Nenhum componente DEVE usar atributo `style` inline para estilização estrutural — apenas CSS Modules ou tokens do Ant Design.
- **FR-004**: A aplicação DEVE ter um ponto centralizado de configuração de tema (cores, tipografia, espaçamento) via `ConfigProvider` do Ant Design.
- **FR-005**: O tema DEVE preservar o esquema escuro atual do projeto, mapeado para tokens do Ant Design.
- **FR-006**: O layout DEVE ser responsivo, adaptando-se a viewports a partir de 320px de largura.
- **FR-007**: O `HealthPanel` DEVE usar componentes visuais de status (badges, tags ou indicadores) para representar saúde dos serviços.
- **FR-008**: A `StatusBar` DEVE usar componentes de alerta ou tag para exibir o estado da conexão WebRTC.
- **FR-009**: O `Header` DEVE usar o componente de Layout/Header do Ant Design mantendo o título e identidade do projeto.
- **FR-010**: A aplicação DEVE manter todas as funcionalidades existentes (WebRTC, health polling) — nenhuma lógica de negócio deve ser alterada, apenas a camada visual.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Todos os 4 componentes principais (`Header`, `VideoPlayer`, `StatusBar`, `HealthPanel`) possuem arquivo `.module.css` correspondente — verificável por inspeção de arquivos.
- **SC-002**: Nenhum atributo `style={{...}}` de estilização estrutural permanece nos componentes após a migração — verificável por busca textual no código.
- **SC-003**: A aplicação renderiza sem erros no console em viewport de 320px, 768px e 1280px — verificável via DevTools.
- **SC-004**: A troca da cor primária no `ConfigProvider` reflete em todos os componentes com uma única alteração — verificável por teste manual.
- **SC-005**: A aplicação mantém todas as funcionalidades originais (stream de vídeo, painéis de saúde, status de conexão) após a migração visual — verificável por teste funcional end-to-end com backend ativo.
