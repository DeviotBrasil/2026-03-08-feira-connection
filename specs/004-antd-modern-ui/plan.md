# Implementation Plan: Interface Moderna com Ant Design e CSS Modules

**Branch**: `004-antd-modern-ui` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/004-antd-modern-ui/spec.md`

## Summary

Migração visual completa do frontend React 19 + Vite para usar **Ant Design v6** como sistema de componentes e **CSS Modules** para estilos de layout/estrutura com escopo local. A identidade de marca (tema escuro, verde `#5FED00`) é preservada via `ConfigProvider` com `darkAlgorithm` + tokens customizados. Nenhuma lógica de negócio (WebRTC, health polling) é alterada — apenas a camada de apresentação dos 4 componentes existentes (`Header`, `VideoPlayer`, `StatusBar`, `HealthPanel`).

## Technical Context

**Language/Version**: TypeScript 5.9 + React 19.2.0  
**Primary Dependencies**: antd@6, @ant-design/icons@6, Vite 7.3.1  
**Storage**: N/A — aplicação stateless, sem persistência  
**Testing**: N/A — Demo-Mode (Princípio VII)  
**Target Platform**: Browser moderno (Chrome >= 100, Safari >= 15) — desktop e tablet  
**Project Type**: Web application (SPA frontend)  
**Performance Goals**: Sem regressão de FPS — UI não deve adicionar overhead perceptível ao WebRTC player; bundle size delta aceitável até +300KB gzip  
**Constraints**: Layout funcional a partir de 320px de largura; dark theme obrigatório; sem uso de `style={{}}` inline estrutural após migração  
**Scale/Scope**: 4 componentes a migrar; 1 arquivo de tema centralizado; 1 arquivo de declaração TypeScript

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Justificativa |
|---|---|---|
| I. Demo-First: Impacto Visual | ✅ PASS | Feature é inteiramente visual — contribui diretamente para experiência de visitante |
| II. Latência Zero-Compromisso (WebRTC obrigatório) | ✅ PASS | Não altera o pipeline de vídeo; ZMQ e WebRTC permanecem intactos |
| III. Estabilidade de 8 Horas | ✅ PASS | Migração só afeta renderização; não introduz loops ou timers novos |
| IV. 24 FPS Mínimo no Browser | ✅ PASS | antd usa CSS-in-JS eficiente; nenhum cálculo de layout pesado adicionado ao caminho crítico do video |
| V. Infraestrutura Cabeada | N/A | Princípio de rede; não aplicável a mudanças visuais |
| VI. Degradação Graciosa | ✅ PASS | Componentes antd com estados de erro/loading explícitos (Alert, Skeleton) — melhora degradação |
| VII. Sem Testes Automatizados | ✅ PASS | Nenhum teste criado; Testing = N/A |
| Stack Mandatório: React >= 18 | ✅ PASS | Projeto usa React 19.2.0; antd v6 exige React >= 18 |
| Stack Mandatório: WebRTC (aiortc) | ✅ PASS | Não alterado |
| Stack Mandatório: ZMQ | ✅ PASS | Não alterado |
| Stack Mandatório: FastAPI | ✅ PASS | Não alterado |

**Resultado: APROVADO — nenhuma violação. Feature pode avançar para implementação.**

## Project Structure

### Documentation (this feature)

```text
specs/004-antd-modern-ui/
├── plan.md                          # Este arquivo
├── research.md                      # Decisões de stack e coexistência CSS
├── data-model.md                    # Mapeamento de tipos → componentes antd
├── quickstart.md                    # Guia de setup e validação
├── contracts/
│   └── ui-component-contracts.md   # Contratos de interface de cada componente
├── checklists/
│   └── requirements.md             # Checklist de qualidade da spec
└── tasks.md                        # (gerado por /speckit.tasks — próximo passo)
```

### Source Code (app/frontend/)

```text
app/frontend/
├── package.json                     # + antd@6, @ant-design/icons@6
└── src/
    ├── vite-env.d.ts                # + declare module '*.module.css'
    ├── theme.ts                     # NOVO — ConfigProvider tokens centralizados
    ├── main.tsx                     # ALTERAR — adicionar ConfigProvider wrapper
    ├── App.tsx                      # ALTERAR — usar Layout antd, remover style inline
    ├── index.css                    # MANTER — variáveis CSS globais de reset/base
    └── components/
        ├── Header.tsx               # ALTERAR — usar Layout.Header + CSS Module
        ├── Header.module.css        # NOVO
        ├── VideoPlayer.tsx          # ALTERAR — usar Button antd + CSS Module
        ├── VideoPlayer.module.css   # NOVO
        ├── StatusBar.tsx            # ALTERAR — usar Tag antd + CSS Module
        ├── StatusBar.module.css     # NOVO
        ├── HealthPanel.tsx          # ALTERAR — usar Statistic, Badge, Alert, Skeleton
        └── HealthPanel.module.css   # NOVO
```

**Structure Decision**: Estrutura de aplicação web SPA existente mantida. Novos arquivos CSS Modules colocados co-localizados com seus componentes. Arquivo `theme.ts` centralizado em `src/` para evitar distribuir tokens em múltiplos locais.
