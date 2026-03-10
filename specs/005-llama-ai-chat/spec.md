# Feature Specification: Chat de IA Generativa com Llama 3.1

**Feature Branch**: `005-llama-ai-chat`  
**Created**: 2026-03-09  
**Status**: Draft  
**Input**: User description: "adcionar um chat de ia generativa usando o modelo do llama 3.1"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversa básica com o assistente de IA (Priority: P1)

O usuário acessa a aba "Chat" na interface principal, digita uma pergunta em linguagem natural e recebe uma resposta gerada pelo modelo Llama 3.1. A resposta aparece na tela de forma progressiva (streaming), sem necessidade de recarregar a página.

**Why this priority**: É o núcleo da funcionalidade. Sem este fluxo funcionando, nada mais tem valor. A página de Chat já existe no frontend como placeholder ("Em construção"), tornando esta story um substituto direto.

**Independent Test**: Pode ser testado acessando a página Chat, digitando qualquer pergunta e verificando que uma resposta coerente é exibida. Entrega valor imediato ao usuário sem depender de nenhuma outra story.

**Acceptance Scenarios**:

1. **Given** o usuário está na página Chat e o modelo está disponível, **When** o usuário digita uma mensagem e pressiona Enviar, **Then** o sistema exibe a resposta do modelo de forma progressiva no chat.
2. **Given** o usuário enviou uma mensagem, **When** o modelo está processando, **Then** um indicador visual de "digitando..." ou similar é exibido.
3. **Given** o usuário recebe uma resposta, **When** a geração é concluída, **Then** o texto completo da resposta fica visível e o campo de entrada é reabilitado.

---

### User Story 2 - Histórico de conversa no contexto da sessão (Priority: P2)

O usuário envia múltiplas mensagens em sequência e o assistente mantém o contexto da conversa, respondendo de forma coerente às perguntas anteriores dentro da mesma sessão.

**Why this priority**: Um chat sem histórico de contexto é pouco útil para perguntas encadeadas. Agrega valor significativo à experiência sem requerer persistência permanente de dados.

**Independent Test**: Pode ser testado enviando uma pergunta sobre um tópico, depois fazendo uma pergunta de follow-up que depende da resposta anterior, verificando que a resposta faz sentido no contexto.

**Acceptance Scenarios**:

1. **Given** o usuário trocou ao menos duas mensagens com o assistente, **When** o usuário faz uma pergunta que referencia a conversa anterior, **Then** o assistente responde levando em conta o contexto acumulado.
2. **Given** o usuário recarrega a página, **When** o chat é reaberto, **Then** o histórico da sessão anterior não é exibido (sessão limpa por padrão).

---

### User Story 3 - Limpeza e reset da conversa (Priority: P3)

O usuário pode, a qualquer momento, iniciar uma nova conversa, descartando o histórico atual e começando do zero.

**Why this priority**: Funcionalidade de suporte à usabilidade. Permite ao usuário mudar de tópico sem que o contexto anterior interfira nas novas respostas.

**Independent Test**: Pode ser testado após uma conversa em andamento, clicando no botão de reset e verificando que a área de mensagens é limpa e que novas perguntas são respondidas sem contexto anterior.

**Acceptance Scenarios**:

1. **Given** uma conversa está em andamento, **When** o usuário clica em "Nova conversa" ou equivalente, **Then** o histórico de mensagens é apagado da tela e o contexto é reiniciado.
2. **Given** o usuário resetou a conversa, **When** envia uma nova mensagem, **Then** o assistente responde sem referências ao histórico anterior.

---

### Edge Cases

- O que acontece quando o modelo Llama não está disponível ou demora a responder? → O sistema deve exibir mensagem de erro amigável com opção de tentar novamente.
- O que acontece se o usuário enviar uma mensagem vazia? → O envio deve ser bloqueado e nenhuma requisição deve ser feita ao modelo.
- O que acontece se o usuário enviar uma mensagem muito longa (ex: >4000 tokens)? → **[Fora de escopo — iteração 1]** O Llama 3.1 suporta 128k tokens; um input de usuário típico em demo não atingirá este limite. Sem validação ativa nesta versão.
- O que acontece se o usuário tentar enviar uma nova mensagem enquanto o modelo ainda está gerando resposta? → O botão de envio permanece desabilitado até a resposta ser concluída.
- O que acontece se a conexão for perdida durante a geração da resposta? → O sistema exibe uma notificação de falha e mantém a mensagem parcialmente gerada visível.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE disponibilizar uma interface de chat na página "Chat" já existente no frontend, substituindo o conteúdo placeholder atual.
- **FR-002**: O sistema DEVE processar mensagens do usuário através do modelo Llama 3.1 e retornar respostas geradas.
- **FR-003**: O sistema DEVE exibir as respostas do modelo de forma progressiva (streaming de tokens) para reduzir o tempo percebido de espera.
- **FR-004**: O sistema DEVE manter o histórico de mensagens da conversa atual no contexto enviado ao modelo durante toda a sessão.
- **FR-005**: O sistema DEVE fornecer um endpoint no backend existente (FastAPI) para receber mensagens e retornar respostas do modelo Llama 3.1.
- **FR-006**: O sistema DEVE exibir indicador visual enquanto o modelo está processando/gerando a resposta.
- **FR-007**: O sistema DEVE desabilitar o envio de novas mensagens enquanto a geração da resposta anterior não for concluída.
- **FR-008**: O sistema DEVE permitir ao usuário iniciar uma nova conversa, limpando o histórico da sessão atual.
- **FR-009**: O sistema DEVE rejeitar mensagens vazias no frontend, sem acionar o backend.
- **FR-010**: O sistema DEVE exibir mensagens de erro claras quando o modelo estiver indisponível ou ocorrer falha na geração.
- **FR-011**: O sistema DEVE integrar com o Ollama como runtime local para servir o modelo Llama 3.1, mantendo a arquitetura offline/local do projeto.
- **FR-012**: O sistema DEVE distinguir visualmente mensagens do usuário e respostas do assistente na interface.
- **FR-013**: O sistema DEVE carregar um arquivo Markdown (`knowledge_base.md`) na inicialização do backend e mantê-lo em memória durante toda a execução.
- **FR-014**: O sistema DEVE injetar o conteúdo do `knowledge_base.md` como mensagem `system` em toda requisição enviada ao Ollama, antes do histórico do usuário.
- **FR-015**: O sistema DEVE instruir o modelo, via system prompt, a responder **somente** com informações presentes no documento carregado, declarando explicitamente quando uma pergunta não for coberta pela base de conhecimento.

### Key Entities

- **Mensagem**: Unidade de comunicação com papel (usuário ou assistente), conteúdo textual e timestamp. Compõe o histórico da conversa.
- **Conversa**: Sequência ordenada de mensagens trocadas em uma sessão. Mantida em memória enquanto a página está aberta; descartada ao fechar ou resetar.
- **Sessão de Chat**: Contexto de uma interação contínua entre usuário e modelo. Contém o histórico de mensagens enviado ao modelo a cada nova requisição.

### Assumptions

- O modelo Llama 3.1 será servido localmente via **Ollama**, ferramenta de runtime de LLMs já comum em ambientes de desenvolvimento local — sem necessidade de API key externa ou internet.
- O backend FastAPI existente será estendido com novos endpoints de chat, sem criação de serviço separado.
- Não há requisito de autenticação de usuário para acessar o chat nesta fase.
- O histórico de conversa não será persistido em banco de dados — apenas em memória de sessão do frontend.
- O comprimento máximo do histórico enviado ao modelo (context window) seguirá os limites padrão do Llama 3.1 (128k tokens).
- A interface de chat usará os componentes da biblioteca Ant Design já adotada no projeto.
- O conteúdo da base de conhecimento é definido exclusivamente pelo arquivo `app/backend/knowledge_base.md`, editável sem alteração de código.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O usuário consegue enviar uma mensagem e receber a primeira parte da resposta em menos de 3 segundos em hardware local padrão.
- **SC-002**: O assistente responde de forma contextualmente coerente em pelo menos 4 trocas consecutivas de mensagens em uma mesma sessão.
- **SC-003**: 100% das tentativas de envio de mensagem vazia são bloqueadas no frontend sem gerar requisição ao backend.
- **SC-004**: Em caso de falha do modelo, o usuário recebe feedback visual de erro em menos de 5 segundos após o timeout.
- **SC-005**: O usuário consegue iniciar uma nova conversa em no máximo 2 cliques a partir da tela de chat.
- **SC-006**: A interface de chat é responsiva e utilizável em telas com largura mínima de 320px.
