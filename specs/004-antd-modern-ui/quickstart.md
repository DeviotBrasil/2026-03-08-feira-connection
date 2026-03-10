# Quickstart: Interface Moderna com Ant Design e CSS Modules

**Feature**: 004-antd-modern-ui  
**Branch**: `004-antd-modern-ui`  
**Date**: 2026-03-09

---

## Pré-requisitos

- Node.js >= 18
- npm >= 9
- Projeto frontend em `app/frontend/` (React 19 + Vite + TypeScript)
- Backend rodando em `localhost:8000` (ou outro host configurado via `?backend=` na URL)

---

## 1. Instalar dependências

```bash
cd app/frontend
npm install antd @ant-design/icons
```

> Isso instala `antd@6` e `@ant-design/icons@6`, compatíveis com React 19.2.0.

---

## 2. Adicionar declaração TypeScript para CSS Modules

Edite `src/vite-env.d.ts` e adicione ao final:

```typescript
declare module '*.module.css' {
  const classes: Record<string, string>;
  export default classes;
}
```

---

## 3. Criar o arquivo de tema centralizado

Crie `src/theme.ts`:

```typescript
import { theme } from 'antd';
import type { ThemeConfig } from 'antd';

export const appTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#5FED00',
    colorBgBase: '#0a0a0a',
    colorBgContainer: '#141414',
    colorBgElevated: '#1c1c1c',
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
    },
  },
};
```

---

## 4. Envolver o App com ConfigProvider

Edite `src/main.tsx`:

```tsx
import { ConfigProvider } from 'antd';
import { appTheme } from './theme';

root.render(
  <ConfigProvider theme={appTheme}>
    <App />
  </ConfigProvider>
);
```

---

## 5. Migrar componentes — exemplo: Header

Crie `src/components/Header.module.css`:

```css
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 24px 0;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.5);
}

.logo {
  height: 56px;
  width: auto;
  object-fit: contain;
}

.accent {
  width: 100%;
  height: 3px;
  margin-top: 14px;
  background: #5FED00;
  box-shadow: 0 0 12px rgba(95, 237, 0, 0.35);
}
```

Edite `src/components/Header.tsx`:

```tsx
import { Layout } from 'antd';
import logo from '../assets/logo.png';
import styles from './Header.module.css';

export function Header() {
  return (
    <Layout.Header className={styles.header}>
      <img src={logo} alt="Logo da empresa" className={styles.logo} />
      <div className={styles.accent} />
    </Layout.Header>
  );
}
```

---

## 6. Rodar o projeto

```bash
npm run dev
```

Acesse `http://localhost:5173` e valide:

- [ ] Layout renderiza sem erros no console
- [ ] Header com fundo branco e faixa verde
- [ ] HealthPanel com Statistic e Badge
- [ ] StatusBar com Tag colorida por estado
- [ ] VideoPlayer com botão fullscreen ao hover
- [ ] Layout responsivo em 320px (DevTools → modo responsivo)

---

## 7. Verificar ausência de style inline

```bash
grep -rn 'style={{' src/components/
```

O resultado deve ser vazio (ou apenas usos não-estruturais como `valueStyle` do `Statistic`).

---

## Referências

- [Ant Design v6 — Getting Started](https://ant.design/docs/react/getting-started)
- [Ant Design — Theme Customization](https://ant.design/docs/react/customize-theme)
- Spec: [specs/004-antd-modern-ui/spec.md](../spec.md)
- Contratos: [specs/004-antd-modern-ui/contracts/ui-component-contracts.md](../contracts/ui-component-contracts.md)
- Data Model: [specs/004-antd-modern-ui/data-model.md](../data-model.md)
