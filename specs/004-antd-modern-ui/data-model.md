# Data Model: Interface Moderna com Ant Design e CSS Modules

**Feature**: 004-antd-modern-ui  
**Phase**: 1 — Design  
**Date**: 2026-03-09

---

## Contexto

Este feature é puramente visual — não introduz entidades de domínio novas. Os tipos de dados existentes em `types.ts` permanecem inalterados. O "modelo de dados" aqui descreve a **estrutura de componentes, tokens de tema e configuração de estilo** que governam a apresentação.

---

## Entidades Existentes (inalteradas)

### `ConnectionState` — `src/types.ts`

```
'idle' | 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'failed'
```

**Uso na UI**: Mapeado para `Tag` do antd com `color` semântico.

| Estado | Cor antd Tag | Ícone antd |
|---|---|---|
| idle | `default` | — |
| connecting | `processing` | `LoadingOutlined` |
| connected | `success` | `CheckCircleOutlined` |
| disconnected | `default` | — |
| reconnecting | `processing` | `LoadingOutlined` |
| failed | `error` | `CloseCircleOutlined` |

---

### `HealthData` — `src/types.ts`

| Campo | Tipo | Componente antd |
|---|---|---|
| `status` | `'ok' \| 'degraded'` | `Badge` com `status` semântico |
| `zmq_connected` | `boolean` | `Badge` + `Tag` |
| `peers_active` | `number` | `Statistic` |
| `fps_recent` | `number` | `Statistic` com `valueStyle` condicional |
| `fps_below_threshold` | `boolean` | Altera cor do `Statistic` para warning |
| `frames_received` | `number` | `Statistic` |
| `uptime_seconds` | `number` | `Statistic` (formatado para hh:mm:ss) |

---

### `StreamStats` — `src/types.ts`

| Campo | Tipo | Componente antd |
|---|---|---|
| `fps` | `number` | `Typography.Text` com `type` condicional |
| `lastFrameAt` | `number \| null` | Não exibido diretamente |

---

## Estrutura de Tema (Design Tokens)

Ponto único de configuração em `src/theme.ts` (novo arquivo).

### Seed Tokens — mapeamento da identidade atual

| CSS Var atual | Token antd | Valor |
|---|---|---|
| `--brand-green: #5FED00` | `colorPrimary` | `#5FED00` |
| `--bg-page: #0a0a0a` | `colorBgBase` | `#0a0a0a` |
| `--bg-surface: #141414` | `colorBgContainer` | `#141414` |
| `--bg-surface-2: #1c1c1c` | `colorBgElevated` | `#1c1c1c` |
| `--text-primary: #ffffff` | Derivado automático do `darkAlgorithm` | — |
| `--border-subtle: rgba(95,237,0,0.22)` | `colorBorder` | Customizado se necessário |

### Algoritmo de Tema

```
algorithm: [theme.darkAlgorithm]
```

### Component Tokens (override por componente se necessário)

| Componente | Token | Valor |
|---|---|---|
| `Layout.Header` | `colorBgHeader` | `#ffffff` (mantém header branco conforme design atual) |
| `Statistic` | Tipografia | `fontSizeHeading5` para valores de métricas |

---

## Estrutura de Arquivos CSS Modules

Cada componente recebe um arquivo `.module.css` colocado no mesmo diretório:

```
src/
├── components/
│   ├── Header.tsx
│   ├── Header.module.css         ← logo sizing, accent bar
│   ├── VideoPlayer.tsx
│   ├── VideoPlayer.module.css    ← wrapper, fullscreen btn overlay
│   ├── StatusBar.tsx
│   ├── StatusBar.module.css      ← layout flex row, gap
│   ├── HealthPanel.tsx
│   └── HealthPanel.module.css    ← grid de métricas, wrap
├── App.tsx
├── theme.ts                      ← ConfigProvider tokens centralizados
└── vite-env.d.ts                 ← declare module '*.module.css'
```

---

## Estados de UI e Transições Visuais

### HealthPanel — estados de carregamento

| Estado | `health` | `healthError` | Renderização |
|---|---|---|---|
| Carregando | `null` | `false` | `Skeleton` do antd |
| Erro Backend | `*` | `true` | `Alert` com `type="error"` |
| Dados OK | objeto | `false` | Grid de `Statistic` + `Badge` |

### StatusBar — estados da conexão

| Renderização | `connectionState` |
|---|---|
| `<Tag color="processing">` | connecting, reconnecting |
| `<Tag color="success">` | connected |
| `<Tag color="error">` | failed |
| `<Tag color="default">` | idle, disconnected |

---

## Validações e Constraints

- `fps_recent < threshold` → `Statistic.valueStyle = { color: '#faad14' }` (amarelo warning antd)
- `fps_recent >= threshold` → `Statistic.valueStyle = { color: '#5FED00' }` (verde marca)
- `uptime` formatado para string legível (função `fmtUptime` existente mantida)
- `streamStats.fps > 0` E `connectionState === 'connected'` → exibir FPS na StatusBar
