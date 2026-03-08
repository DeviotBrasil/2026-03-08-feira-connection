# frontend — Interface Web

SPA React que recebe o stream de vídeo anotado via **WebRTC** a partir do backend e o exibe ao vivo com bounding boxes do YOLO, contador de FPS e painel de saúde do sistema.

---

## Pré-requisitos

> **Node.js é necessário apenas para o build.** Após gerar `dist/`, o backend Python serve
> os arquivos estáticos — Node não precisa estar rodando em produção/demo.

- Node.js 18 LTS+ (somente para o build)
- `app/backend` em execução em `http://localhost:8080`

---

## Build (passo único, pré-demo)

```bash
cd app/frontend
npm install
npm run build       # gera app/frontend/dist/
```

Após o build, o backend detecta `dist/` automaticamente e serve o frontend em `http://localhost:8080`. Node.js pode ser desligado.

---

## Acesso

```bash
# Abrir no browser (macOS)
open http://localhost:8080

# Em outro dispositivo na LAN
open http://192.168.x.x:8080
```

O frontend conecta ao WebRTC automaticamente ao carregar e exibe o stream em até 5 segundos.

---

## Desenvolvimento com hot-reload

```bash
# Terminal 1 — backend
cd app/backend && python main.py

# Terminal 2 — Vite dev server (localhost:5173)
cd app/frontend && npm run dev
```

O `vite.config.ts` inclui proxy que redireciona `/offer` e `/health` para `localhost:8080`.

---

## Funcionalidades

- Stream de vídeo ao vivo com bounding boxes YOLO
- Contador de FPS em tempo real (`requestVideoFrameCallback`)
- Reconexão automática com backoff exponencial (2s → 15s)
- Painel de saúde: status ZMQ, peers ativos, FPS do backend
- Alerta visual quando o service para de publicar
- Backend configurável via `?backend=http://192.168.x.x:8080`


## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
