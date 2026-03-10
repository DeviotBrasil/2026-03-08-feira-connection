#!/bin/bash

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Helpers ───────────────────────────────────────────────────────────────────
SERVICE_PID=""
BACKEND_PID=""
FRONTEND_PID=""

OLLAMA_PID=""

stop_all() {
  echo ""
  echo "Encerrando processos..."
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null
  [ -n "$SERVICE_PID" ]  && kill "$SERVICE_PID"  2>/dev/null
  [ -n "$OLLAMA_PID" ]   && kill "$OLLAMA_PID"   2>/dev/null
  wait 2>/dev/null
  echo "Encerrado."
  exit 0
}
trap stop_all INT TERM

# Aguarda um endpoint HTTP responder (máx N segundos)
wait_http() {
  local url="$1"
  local label="$2"
  local max="${3:-30}"
  local i=0
  echo -n "   aguardando $label..."
  while ! curl -sf "$url" > /dev/null 2>&1; do
    sleep 1
    i=$((i + 1))
    if [ "$i" -ge "$max" ]; then
      echo " timeout!"
      echo "Erro: $label não ficou disponível em ${max}s. Abortando."
      stop_all
    fi
    echo -n "."
  done
  echo " pronto"
}

# ── 0. Ollama ─────────────────────────────────────────────────────
if command -v ollama &>/dev/null; then
  # Só inicia se ainda não estiver respondendo
  if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "▶  [0/3] Ollama já está rodando."
  else
    echo "▶  [0/3] Iniciando Ollama (Llama 3.1)..."
    ollama serve &
    OLLAMA_PID=$!
    wait_http "http://localhost:11434/api/tags" "ollama" 30
  fi
else
  echo "⚠️  Ollama não encontrado — chat de IA indisponível (execute setup.sh para instalar)."
fi

# ── 1. Service ─────────────────────────────────────────────────────────────────
echo ""
echo "▶  [1/3] Iniciando app/service..."
cd "$ROOT/app/service"
"$ROOT/app/service/.venv/bin/python3" main.py &
SERVICE_PID=$!
wait_http "http://localhost:8000/health" "service"

# ── 2. Backend ─────────────────────────────────────────────────────────────────
echo "▶  [2/3] Iniciando app/backend..."
cd "$ROOT/app/backend"
"$ROOT/app/backend/.venv/bin/python" main.py &
BACKEND_PID=$!
wait_http "http://localhost:8080/health" "backend"

# ── 3. Frontend ────────────────────────────────────────────────────────────────
echo "▶  [3/3] Iniciando app/frontend (npm run dev)..."
cd "$ROOT/app/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Sistema em execução:"
echo "  ollama    PID ${OLLAMA_PID:-(externo)}  →  http://localhost:11434"
echo "  service   PID $SERVICE_PID   →  http://localhost:8000/health"
echo "  backend   PID $BACKEND_PID   →  http://localhost:8080/health"
echo "  frontend  PID $FRONTEND_PID  →  http://localhost:5173"
echo ""
echo "Pressione Ctrl+C para encerrar todos os processos."
echo ""

wait

