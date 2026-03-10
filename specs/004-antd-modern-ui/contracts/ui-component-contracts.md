# UI Component Contract: Frontend com Ant Design

**Feature**: 004-antd-modern-ui  
**Type**: UI Contracts — contratos de interface de usuário  
**Date**: 2026-03-09

---

## Visão Geral

Este documento define os contratos visuais e comportamentais de cada componente após a migração para Ant Design v6 + CSS Modules. Contratos especificam **o que cada componente expõe e garante**, não como é implementado internamente.

---

## Contrato: `<Header>`

### Props (inalteradas)
```
nenhuma prop — componente sem estado externo
```

### Garantias visuais
- Exibe logotipo da empresa centralizado com `height: 56px`
- Faixa de acento verde (`#5FED00`) de `height: 3px` na borda inferior
- Fundo branco (`#ffffff`) independente do tema escuro global
- Posição `sticky` no topo com `z-index` elevado (permanece visível durante scroll)
- Responsivo: logotipo se centraliza em viewports menores sem overflow

### Componentes antd utilizados
- `Layout.Header` — container semântico

### Breakpoints responsivos
| Viewport | Comportamento |
|---|---|
| < 576px (xs) | Header mantém altura mínima; logo reduz padding horizontal |
| ≥ 576px | Logo full size (56px) |

---

## Contrato: `<VideoPlayer>`

### Props
```typescript
{ videoRef: RefObject<HTMLVideoElement | null> }
```

### Garantias visuais
- Vídeo ocupa 100% da largura do container pai, máximo de 960px
- Fundo `#000` quando stream não está disponível
- Botão fullscreen aparece sobre o vídeo ao hover do mouse (desktop) ou sempre visível em touch
- Ícone fullscreen usa `FullscreenOutlined` / `FullscreenExitOutlined` do `@ant-design/icons`
- Nenhum overflow horizontal na peça <video>

### Comportamento fullscreen
- Clique no botão → `requestFullscreen()` no `<video>` element
- Estado sincronizado com evento `fullscreenchange` do browser (sem disco de estado derivado)

### Componentes antd utilizados
- `Button` (ghost, shape="circle") — botão fullscreen
- `Tooltip` — hint de texto ao hover do botão

---

## Contrato: `<StatusBar>`

### Props
```typescript
{
  connectionState: ConnectionState;
  streamStats: StreamStats;
}
```

### Garantias visuais
- Exibe sempre o estado atual da conexão como `Tag` do antd com `color` semântico
- Tag `"processing"` (com spinner animado) para estados transitórios (connecting, reconnecting)
- Exibe FPS como `Typography.Text` verde quando `connectionState === 'connected' && streamStats.fps > 0`
- Layout horizontal; wrap natural em telas menores

### Mapeamento de cores de Tag
| Estado | `color` da Tag antd |
|---|---|
| idle | `default` |
| connecting | `processing` |
| connected | `success` |
| disconnected | `default` |
| reconnecting | `processing` |
| failed | `error` |

### Componentes antd utilizados
- `Tag` com `color` prop  
- `Typography.Text` para FPS

---

## Contrato: `<HealthPanel>`

### Props
```typescript
{
  health: HealthData | null;
  healthError: boolean;
}
```

### Estados de renderização

| Condição | Renderização |
|---|---|
| `healthError === true` | `Alert` antd, `type="error"`, mensagem "Backend inacessível" |
| `health === null && !healthError` | `Skeleton` antd (placeholder de carregamento) |
| Dados disponíveis | Grid de `Statistic` + `Badge` conforme tabela abaixo |

### Métricas exibidas (modo dados)

| Label | Campo `HealthData` | Componente antd | Cor value |
|---|---|---|---|
| Backend | `health.status` | `Badge` + texto | verde/ amarelo |
| ZMQ | `health.zmq_connected` | `Badge` | verde / vermelho |
| Peers | `health.peers_active` | `Statistic` | padrão |
| FPS ZMQ | `health.fps_recent` | `Statistic` | verde se ok, amarelo se abaixo |
| Frames | `health.frames_received` | `Statistic` | padrão |
| Uptime | `health.uptime_seconds` | `Statistic` formatter | padrão |

### Responsividade
- Em viewports `< 768px`: métricas empilhadas em 2 colunas (antd `Row/Col`)
- Em viewports `≥ 768px`: linha horizontal com todos os itens visíveis

### Componentes antd utilizados
- `Alert` — estado de erro
- `Skeleton` — estado de carregamento
- `Statistic` — métricas numéricas
- `Badge` — status ok/erro/warning
- `Row`, `Col` — grid responsivo

---

## Contrato: `<App>` — Layout Global

### Estrutura visual garantida
```
ConfigProvider (dark theme + token overrides)
└── Layout (antd)
    ├── Layout.Header → <Header />
    └── Layout.Content
        ├── wrapper do vídeo (max 960px, centralizado)
        │   ├── <VideoPlayer />
        │   └── <StatusBar />
        └── <HealthPanel />
```

### Responsividade garantida
- `min-width: 320px` — sem scroll horizontal em nenhum breakpoint
- Layout usa `flexDirection: column` em mobile; preserva a hierarquia de informação
- `Layout.Content` usa padding responsivo: 24px desktop, 12px mobile (`xs`)

---

## Contrato: Tema Global (`theme.ts`)

### Interface pública do módulo
```typescript
export const appTheme: ThemeConfig
```

### Garantias
- Ponto único de customização de tokens de marca
- `algorithm: theme.darkAlgorithm` sempre ativo
- `colorPrimary: '#5FED00'` é o único token de cor de marca que precisa ser alterado para mudar toda a interface
- Nenhum componente importa tokens de cor diretamente — todos derivam via `useToken()` ou className antd
