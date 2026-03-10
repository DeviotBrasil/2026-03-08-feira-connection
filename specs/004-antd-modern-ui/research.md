# Research: Interface Moderna com Ant Design e CSS Modules

**Feature**: 004-antd-modern-ui  
**Phase**: 0 — Research  
**Date**: 2026-03-09  
**Status**: Complete — todos os NEEDS CLARIFICATION resolvidos

---

## Decisão 1: Versão do Ant Design

**Decision**: Usar **antd v6** (`antd@6`, `@ant-design/icons@6`)

**Rationale**:
- antd v6 é a versão mais recente (v6.3.2 no momento da pesquisa) e suporta React 18+ oficialmente.
- antd v5 + React 19 exigia um patch adicional (`@ant-design/v5-patch-for-react-19`); o antd v6 remove essa necessidade.
- O projeto usa React 19.2.0 — antd v6 é o caminho suportado e sem friction.
- `@ant-design/icons@6` é incompatível com `antd@5`; usar a mesma major evita conflitos de peer dependency.

**Alternatives considered**:
- antd v5: funciona com React 19 mas com ressalvas histórias de patches; considerado legado para novos projetos.

---

## Decisão 2: CSS Modules — configuração necessária

**Decision**: **Nenhuma configuração adicional** em `vite.config.ts` é necessária.

**Rationale**:
- Vite suporta CSS Modules nativamente. Arquivos `*.module.css` são processados automaticamente com hash de escopo local.
- Não há conflito entre o CSS-in-JS interno do antd (via `@ant-design/cssinjs`) e CSS Modules customizados — eles operam em camadas independentes.
- O `tsconfig.app.json` do projeto já referencia `vite/client`, que inclui a tipagem para módulos CSS. Uma declaração explícita em `vite-env.d.ts` melhora IntelliSense mas não é obrigatória.

**Alternatives considered**:
- styled-components ou emotion: mais pesados, não justificados quando antd já traz CSS-in-JS built-in.
- Tailwind CSS: conflitaria com o sistema de tokens do antd e adicionaria overhead de configuração.

---

## Decisão 3: Tema escuro — estratégia de mapeamento

**Decision**: Usar `ConfigProvider` com `theme.darkAlgorithm` + customização de **Seed Tokens** para preservar a identidade de marca atual.

**Rationale**:
- O antd v6 oferece `theme.darkAlgorithm` que inverte a paleta de tons automaticamente.
- A cor de marca atual (`--brand-green: #5FED00`) e fundo (`--bg-page: #0a0a0a`) serão mapeados para tokens de seed:
  - `colorPrimary: '#5FED00'` — aplica o verde em todos os controles interativos
  - `colorBgBase: '#0a0a0a'` — define o tom base do dark theme
- O tema centralizado no `ConfigProvider` garante que a troca de qualquer token reflita em todos os componentes (Success Criteria SC-004).
- CSS Modules com variáveis CSS globais (`var(--brand-green)`) continuam funcionando em paralelo para estilos de layout não cobertos pelo antd.

**Alternatives considered**:
- Tema claro do antd: descartado — a identidade existente é dark e o contexto de feira (ambiente de pavilhão) favorece UI escura.
- Customizar via Less variables (v4): obsoleto no v5/v6 que usa CSS-in-JS design tokens.

---

## Decisão 4: Padrão de coexistência antd + CSS Modules

**Decision**: **antd para componentes UI**, **CSS Modules para layout e wrapper estrutural**.

**Rationale**:
- antd fornece componentes prontos (`Layout`, `Tag`, `Badge`, `Button`, `Typography`, `Card`, `Statistic`).
- CSS Modules cobrem os containers específicos da aplicação: proporções do vídeo, grid de painéis, espaçamentos fora do sistema padrão antd.
- Nenhum componente mantém `style={{}}` inline para estilização estrutural — regra imposta pelo requisito FR-003.

**Mapping de componentes antd para cada componente existente**:

| Componente existente | Componentes antd | CSS Module |
|---|---|---|
| `Header.tsx` | `Layout.Header` | `Header.module.css` (logo, accent line) |
| `VideoPlayer.tsx` | `Button` (fullscreen), `Tooltip` | `VideoPlayer.module.css` (wrapper, controles) |
| `StatusBar.tsx` | `Tag`, `Badge`, `Typography.Text` | `StatusBar.module.css` (layout flex) |
| `HealthPanel.tsx` | `Statistic`, `Tag`, `Badge`, `Card` | `HealthPanel.module.css` (grid de itens) |
| `App.tsx` | `Layout`, `Layout.Content`, `ConfigProvider` | N/A (flexbox via tokens antd) |

---

## Decisão 5: Responsividade

**Decision**: Usar o **Grid system do antd** (`Row`/`Col`) combinado com breakpoints nativos (`xs`, `sm`, `md`, `lg`) para garantir adaptação de 320px até 2560px+.

**Rationale**:
- O antd Grid é baseado em 24 colunas com breakpoints predefinidos (xs:0, sm:576, md:768, lg:992, xl:1280, xxl:1600).
- Elimina a necessidade de media queries manuais nos CSS Modules para os layouts principais.
- O `VideoPlayer` mantém `maxWidth: 960px` via token — o Grid reduz as colunas automaticamente em telas menores.

**Alternatives considered**:
- CSS Grid customizado via CSS Modules: funciona mas duplica esforço quando antd já fornece a solução.

---

## Decisão 6: TypeScript — declaração de módulos CSS

**Decision**: Adicionar declaração explícita de `*.module.css` no `vite-env.d.ts` existente.

**Rationale**:
- O `vite/client` types já inclui suporte básico, mas uma declaração explícita melhora IntelliSense com autocompletion de classes CSS.
- Custo: 3 linhas de código. Benefício: elimina erros de tipo em `import styles from './X.module.css'`.

**Alternatives considered**:
- typescript-plugin-css-modules: plugin adicional que não é necessário dado que o Vite já provê o essencial.

---

## Resumo de Dependências a Instalar

```
antd@6
@ant-design/icons@6
```

Sem modificações em `vite.config.ts`. Sem loaders adicionais.
