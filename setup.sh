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

# ── Resumo ─────────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════"
echo "  Setup concluído com sucesso ✓"
echo "══════════════════════════════════════"
echo ""
echo "Próximos passos:"
echo "  1. cp app/service/.env.example app/service/.env   # ajustar CAMERA_DEVICE_INDEX"
echo "  2. bash start.sh                                  # iniciar todos os serviços"
echo ""

