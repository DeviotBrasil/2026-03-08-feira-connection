# Tasks: Interface Moderna com Ant Design e CSS Modules

**Feature**: 004-antd-modern-ui  
**Branch**: `004-antd-modern-ui`  
**Input**: Design documents de `/specs/004-antd-modern-ui/`  
**Date**: 2026-03-09  
**Tests**: N/A — Demo-Mode (Princípio VII da Constitution)  
**Organization**: Tarefas agrupadas por user story para entrega incremental independente

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode executar em paralelo (arquivos diferentes, sem dependências incompletas)
- **[Story]**: User story correspondente (US1, US2, US3)
- Todos os caminhos relativos a `app/frontend/`

---

## Phase 1: Setup (Infraestrutura Compartilhada)

**Purpose**: Instalar dependências e preparar a base técnica que todos os componentes precisam

- [X] T001 Instalar antd@6 e @ant-design/icons@6 em `app/frontend/package.json` via `npm install antd @ant-design/icons`
- [X] T002 Adicionar declaração TypeScript para CSS Modules em `app/frontend/src/vite-env.d.ts`
- [X] T003 Criar arquivo de tema centralizado em `app/frontend/src/theme.ts` com `darkAlgorithm`, `colorPrimary: '#5FED00'`, `colorBgBase: '#0a0a0a'`
- [X] T004 Envolver `<App />` com `<ConfigProvider theme={appTheme}>` em `app/frontend/src/main.tsx`

**Checkpoint**: `npm run dev` sobe sem erros; tokens de tema aplicados globalmente

---

## Phase 2: Fundacional (Pré-requisito bloqueante)

**Purpose**: Reestruturar o `App.tsx` com `Layout` do antd antes de migrar os componentes filhos

**⚠️ CRÍTICO**: Nenhum componente filho pode ser migrado com segurança enquanto o `App.tsx` usa `style` inline para o layout raiz

- [X] T005 Refatorar `app/frontend/src/App.tsx`: substituir `div` com `style={{display:'flex', flexDirection:'column'}}` por `<Layout>` e `<Layout.Content>` do antd, removendo todos os `style={{}}` de layout estrutural e mantendo intactos os hooks `useWebRTC` e `useHealthPolling`

**Checkpoint**: Aplicação renderiza com Layout antd; hooks de WebRTC e health polling continuam funcionando

---

## Phase 3: User Story 1 — Dashboard Modernizado (Priority: P1) 🎯 MVP

**Goal**: Todos os 4 componentes usam Ant Design + CSS Modules; zero `style={{}}` estrutural; estados de erro/loading explícitos com componentes antd

**Independent Test**: `npm run dev` → abrir browser → validar layout com cabeçalho, vídeo, painel de saúde e status bar visíveis e estilizados; testar com backend offline para validar estados de erro/loading

### Implementação — User Story 1

- [X] T006 [P] [US1] Criar `app/frontend/src/components/Header.module.css` com estilos de logo, accent bar e sticky positioning
- [X] T007 [P] [US1] Criar `app/frontend/src/components/VideoPlayer.module.css` com estilos de wrapper, overlay do botão fullscreen e proporção do vídeo
- [X] T008 [P] [US1] Criar `app/frontend/src/components/StatusBar.module.css` com estilos de layout flex e espaçamento do container
- [X] T009 [P] [US1] Criar `app/frontend/src/components/HealthPanel.module.css` com estilos de grid de métricas e wrap responsivo
- [X] T010 [US1] Migrar `app/frontend/src/components/Header.tsx`: substituir `<header>` por `<Layout.Header>`, importar `styles` do CSS Module, remover classes CSS globais e `style` inline (depende de T006)
- [X] T011 [US1] Migrar `app/frontend/src/components/VideoPlayer.tsx`: substituir botão fullscreen inline por `<Button>` + `<Tooltip>` do antd com ícones `FullscreenOutlined`/`FullscreenExitOutlined`, importar CSS Module, remover todos os `style={{}}` estruturais (depende de T007)
- [X] T012 [US1] Migrar `app/frontend/src/components/StatusBar.tsx`: substituir status dot + texto por `<Tag color={...}>` do antd mapeado por `connectionState`, exibir FPS via `<Typography.Text>`, importar CSS Module, remover `style={{}}` (depende de T008)
- [X] T013 [US1] Migrar `app/frontend/src/components/HealthPanel.tsx`: substituir `<div className="health-panel">` por `<Card>` ou container com CSS Module; renderizar métricas com `<Statistic>` e status com `<Badge>`; implementar estado de erro com `<Alert type="error">` e loading com `<Skeleton>`, remover `style={{}}` inline (depende de T009)

**Checkpoint**: `grep -rn 'style={{' app/frontend/src/components/` retorna vazio; todos os estados (loading, erro, dados) de `HealthPanel` renderizam corretamente

---

## Phase 4: User Story 2 — Responsividade (Priority: P2)

**Goal**: Layout funciona em qualquer viewport de 320px a 2560px sem overflow horizontal nem elementos sobrepostos

**Independent Test**: DevTools → modo responsivo → testar 320px, 768px e 1280px → nenhum scroll horizontal, todos os elementos visíveis e legíveis

**Prerequisite**: Phase 3 (US1) completa — os componentes precisam existir em antd antes de adicionar breakpoints de Grid

### Implementação — User Story 2

- [X] T014 [US2] Atualizar `app/frontend/src/App.tsx`: envolver área principal com `<Row>` e `<Col>` do antd com breakpoints `xs`, `sm`, `md`, `lg`; garantir que `VideoPlayer` e painéis se reorganizam em mobile (depende de T005)
- [X] T015 [P] [US2] Atualizar `app/frontend/src/components/HealthPanel.module.css` e `HealthPanel.tsx`: adicionar `<Row gutter={[8,8]}>` + `<Col xs={12} sm={8} md={4}>` para que métricas empilhem 2-por-linha em mobile (depende de T013)
- [X] T016 [P] [US2] Atualizar `app/frontend/src/components/VideoPlayer.module.css`: definir `max-width: 960px` via CSS Module e remover qualquer `maxWidth` hardcoded inline (depende de T011)

**Checkpoint**: DevTools em 320px → sem rolagem horizontal; 768px → painéis visíveis; 1280px → vídeo centralizado com largura máxima respeitada

---

## Phase 5: User Story 3 — Tema Centralizado e Personalizável (Priority: P3)

**Goal**: Alterar `colorPrimary` em `theme.ts` reflete em todos os componentes com uma única mudança

**Independent Test**: Alterar `colorPrimary: '#5FED00'` para `colorPrimary: '#FF4D4F'` (vermelho) em `src/theme.ts` → salvar → HMR atualiza → todos os botões, tags e indicadores mudam de cor

**Prerequisite**: Phase 3 (US1) completa

### Implementação — User Story 3

- [X] T017 [P] [US3] Revisar todos os componentes migrados e substituir qualquer hardcode de `#5FED00` por `colorPrimary` via `useToken()` do antd ou por variável CSS derivada do tema em `app/frontend/src/components/*.tsx`
- [X] T018 [P] [US3] Limpar `app/frontend/src/index.css`: remover classes de componentes já migradas para CSS Modules (`.health-panel`, `.health-item`, `.status-bar`, `.status-dot`, `.site-header`); manter apenas reset global e variáveis `:root`
- [X] T019 [US3] Verificar e remover `app/frontend/src/App.css` se estilos migrados; garantir que não há importação de CSS global desnecessária em `app/frontend/src/App.tsx`

**Checkpoint**: `grep -rn '#5FED00\|--brand-green' app/frontend/src/components/` retorna apenas usos via token ou CSS var de `theme.ts`; `theme.ts` é o único local para mudar a cor de marca

---

## Phase Final: Polish e Verificação Cruzada

**Purpose**: Verificar Success Criteria da spec e garantir consistência visual

- [X] T020 [P] Validação SC-001: confirmar existência de `Header.module.css`, `VideoPlayer.module.css`, `StatusBar.module.css`, `HealthPanel.module.css` via `ls app/frontend/src/components/*.module.css`
- [X] T021 [P] Validação SC-002: executar `grep -rn 'style={{' app/frontend/src/components/` e confirmar resultado vazio (apenas `valueStyle` de `Statistic` é permitido)
- [X] T022 Validação SC-003/SC-005: rodar `npm run build` em `app/frontend/` sem erros TypeScript; validar visualmente em 320px, 768px e 1280px via DevTools
- [ ] T023 Validação SC-004: (validação manual — alterar colorPrimary em theme.ts, verificar propagação, reverter) alterar `colorPrimary` em `src/theme.ts`, confirmar propagação em todos os componentes, reverter para `#5FED00`

---

## Grafo de Dependências

```
T001 → T003 → T004 → T005 (Setup bloqueante)
                           ↓
              T006 → T010  ┐
              T007 → T011  ├─ US1 (Phase 3) → T014, T015, T016 (US2/Phase 4)
              T008 → T012  │                → T017, T018, T019 (US3/Phase 5)
              T009 → T013  ┘                → T020..T023 (Polish)
T002 (independente — pode rodar paralelo com T001)
```

**Nota**: T006–T009 (criação dos CSS Modules) podem rodar em paralelo entre si (arquivos diferentes). T010–T013 (migração dos componentes) dependem dos respectivos CSS Modules mas são independentes entre si.

---

## Execução Paralela por User Story

### Phase 3 (US1) — paralelismo máximo

```
# Rodadas paralelas
Rodada A (paralelo): T006, T007, T008, T009  ← criar todos os CSS Modules
Rodada B (paralelo): T010, T011, T012, T013  ← migrar componentes (após rodada A)
```

### Phase 4 (US2) — após US1 completo

```
Rodada A (sequencial): T014  ← App.tsx layout responsivo
Rodada B (paralelo):   T015, T016  ← ajustes responsivos nos componentes
```

### Phase 5 (US3) — após US1 completo

```
Rodada A (paralelo): T017, T018  ← limpeza de tokens e CSS global
Rodada B:            T019  ← remover App.css se vazio
```

---

## Sugestão de Escopo MVP

O **MVP** é a conclusão da **Phase 3 (US1)** — um dashboard funcional com antd + CSS Modules em todos os componentes, sem nenhum `style={{}}` estrutural. Isso já entrega:

- UI moderna com componentes Ant Design
- Tema escuro com identidade de marca preservada
- Estados de erro e loading explícitos
- Funcionalidades WebRTC e health polling intactas

US2 (responsividade) e US3 (tema personalizável) são incrementos que podem ser entregues após o MVP.

---

## Resumo de Contagem

| Fase | Tarefas | Paralelizáveis |
|---|---|---|
| Setup (Phase 1) | 4 | T002 paralelo com T001 |
| Fundacional (Phase 2) | 1 | — |
| US1 — Dashboard (Phase 3) | 8 | T006–T009 paralelas; T010–T013 paralelas |
| US2 — Responsividade (Phase 4) | 3 | T015, T016 paralelas |
| US3 — Tema (Phase 5) | 3 | T017, T018 paralelas |
| Polish (Phase Final) | 4 | T020, T021 paralelas |
| **Total** | **23** | **14 paralelizáveis** |
