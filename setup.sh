#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Helpers ────────────────────────────────────────────────────────────────────
step()  { echo ""; echo "┌─ $*"; }
ok()    { echo "└─ ✓ $*"; }
info()  { echo "│  $*"; }

# ── Verificar pré-requisitos ───────────────────────────────────────────────────
step "Verificando pré-requisitos..."

PY_VERSION=$(python3 --version 2>&1)
info "Python → $PY_VERSION"
python3 -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ necessário'" \
  || { echo "└─ ✗ Python 3.11+ é necessário. Abortar."; exit 1; }

NODE_VERSION=$(node --version 2>&1) || { echo "└─ ✗ Node.js não encontrado. Instale Node 18 LTS+."; exit 1; }
NPM_VERSION=$(npm --version 2>&1)
info "Node.js → $NODE_VERSION"
info "npm     → $NPM_VERSION"
ok "Pré-requisitos OK"

# ── app/service ────────────────────────────────────────────────────────────────
step "[1/3] Setup: app/service"
cd "$ROOT/app/service"

info "Criando virtualenv (.venv)..."
python3 -m venv .venv
info "Virtualenv criado em app/service/.venv"

info "Atualizando pip..."
.venv/bin/pip install --quiet --upgrade pip

info "Instalando dependências (requirements.txt)..."
.venv/bin/pip install -r requirements.txt
PKGS=$(. .venv/bin/activate && pip list --format=columns | wc -l | tr -d ' ')
info "$((PKGS - 2)) pacotes instalados"

ok "app/service pronto"

# ── app/backend ────────────────────────────────────────────────────────────────
step "[2/3] Setup: app/backend"
cd "$ROOT/app/backend"

info "Criando virtualenv (.venv)..."
python3 -m venv .venv
info "Virtualenv criado em app/backend/.venv"

info "Atualizando pip..."
.venv/bin/pip install --quiet --upgrade pip

info "Instalando dependências (requirements.txt)..."
.venv/bin/pip install -r requirements.txt
PKGS=$(. .venv/bin/activate && pip list --format=columns | wc -l | tr -d ' ')
info "$((PKGS - 2)) pacotes instalados"

ok "app/backend pronto"

# ── app/frontend ───────────────────────────────────────────────────────────────
step "[3/3] Setup: app/frontend"
cd "$ROOT/app/frontend"

info "Executando npm install..."
npm install
MODS=$(ls node_modules | wc -l | tr -d ' ')
info "$MODS módulos instalados em node_modules/"

ok "app/frontend pronto"

# ── Ollama (runtime do Llama 3.1) ─────────────────────────────────────────────
step "[4/4] Setup: Ollama + Llama 3.1"

if ! command -v ollama &>/dev/null; then
  echo "│  AVISO: ollama não encontrado no PATH."
  echo "│  Instale via: brew install ollama  (macOS) ou  curl -fsSL https://ollama.com/install.sh | sh  (Linux)"
  echo "└─ ⚠️  Ollama não instalado — o chat de IA não estará disponível."
else
  OLLAMA_VERSION=$(ollama --version 2>&1 | head -1)
  info "Ollama → $OLLAMA_VERSION"

  # Verifica se o modelo já está baixado
  if ollama list 2>/dev/null | grep -q 'llama3.1'; then
    info "Modelo llama3.1 já presente."
  else
    info "Baixando modelo llama3.1 (~4.7 GB) — pode demorar alguns minutos..."
    ollama pull llama3.1
  fi

  ok "Ollama + Llama 3.1 pronto"
fi───────────────────
echo ""
echo "══════════════════════════════════════"
echo "  Setup concluído com sucesso ✓"
echo "══════════════════════════════════════"
echo ""
echo "Próximos passos:"
echo "  1. cp app/service/.env.example app/service/.env   # ajustar CAMERA_DEVICE_INDEX"
echo "  2. bash start.sh                                  # iniciar todos os serviços"
echo "  Obs: o chat de IA requer o Ollama rodando (iniciado automaticamente por start.sh)"
echo ""

