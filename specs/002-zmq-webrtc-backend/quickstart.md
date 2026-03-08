# Quickstart: backend

**Feature**: 002-zmq-backend  
**Pré-requisito**: `service` da feature 001 em execução e publicando frames ZMQ.

---

## Pré-requisitos

- Python 3.11+
- `service` rodando e publicando via ZMQ em `tcp://127.0.0.1:5555`
- Porta `8080` disponível no host

---

## Instalação

```bash
cd app/backend
pip install -r requirements.txt
```

Dependências principais:
```
fastapi>=0.100
uvicorn[standard]>=0.23
aiortc>=1.9
pyzmq>=25
opencv-python-headless>=4.8
numpy>=1.24
pydantic>=2.0
python-dotenv>=1.0
av>=10.0
```

---

## Configuração

Todas as configurações são opcionais — os defaults funcionam sem nenhum ajuste. Crie `.env` em `app/backend/` se precisar customizar:

```env
ZMQ_ENDPOINT=tcp://127.0.0.1:5555   # endereço do service
HTTP_PORT=8080                       # porta do backend
HTTP_HOST=0.0.0.0                    # interface de escuta
ICE_TIMEOUT=3.0                      # timeout ICE gathering (s)
LOG_LEVEL=INFO                       # nível de log
```

---

## Execução direta (sem supervisor)

```bash
cd app/backend
python main.py
```

Saída esperada no startup:
```
INFO:     ZMQ PULL conectado em tcp://127.0.0.1:5555
INFO:     Iniciando servidor em http://0.0.0.0:8080
INFO:     Application startup complete.
```

---

## Execução via supervisord (integrado ao service)

Adicionar ao `app/service/supervisord.conf`:

```ini
[program:backend]
command=python main.py
directory=%(here)s/../backend
autostart=true
autorestart=true
startretries=10
stopwaitsecs=5
stdout_logfile=%(here)s/../app/backend/logs/backend.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
stderr_logfile=%(here)s/../app/backend/logs/backend-error.log
stderr_logfile_maxbytes=5MB
stderr_logfile_backups=3
environment=PYTHONUNBUFFERED="1"
```

Criar diretório de logs:
```bash
mkdir -p app/backend/logs
```

Iniciar/recarregar supervisor:
```bash
# Iniciar (se supervisor não estiver rodando)
cd app/service
supervisord -c supervisord.conf

# Ou recarregar config se já estiver rodando
supervisorctl -c supervisord.conf reread
supervisorctl -c supervisord.conf update
```

---

## Verificação de saúde

```bash
curl http://localhost:8080/health
```

Resposta esperada quando tudo está funcionando:
```json
{
  "status": "ok",
  "zmq_connected": true,
  "peers_active": 0,
  "fps_recent": 27.4,
  "frames_received": 1240,
  "frames_distributed": 0,
  "uptime_seconds": 42.1
}
```

Se `zmq_connected` for `false`, o `service` não está publicando. Verificar:
```bash
# Checar se o service está rodando
supervisorctl -c app/service/supervisord.conf status

# Checar se a porta ZMQ está aberta
lsof -i :5555
```

---

## Verificação do stream WebRTC (browser)

Abrir o frontend React e verificar que o vídeo aparece. Para teste rápido sem frontend, usar a página HTML de teste inclusa (ver `app/backend/test.html`):

```bash
# Servir arquivo de teste localmente
python3 -m http.server 9000 --directory backend
# Abrir http://localhost:9000/test.html no browser
```

Passos de verificação visual:
1. Abrir `http://localhost:9000/test.html`
2. Clicar em "Conectar WebRTC"
3. Vídeo com bounding boxes deve aparecer em ≤ 2 segundos
4. Verificar FPS overlay na página (deve ser ≥ 24 FPS)
5. Verificar latência visual: mover mão à frente da câmera e confirmar delay < 300ms

---

## Testes de resiliência (pré-feira)

### Teste 1 — restart do service (FR-006)
```bash
# Com stream ativo no browser, reiniciar o service:
supervisorctl -c app/service/supervisord.conf restart service
# Observar: stream deve retornar automaticamente em ≤ 5 segundos
```

### Teste 2 — restart do backend (AC-004)
```bash
# Matar o processo:
supervisorctl -c app/service/supervisord.conf stop backend
# Aguardar: supervisor deve relançar automaticamente
supervisorctl -c app/service/supervisord.conf status
# Verificar: backend RUNNING novamente
```

### Teste 3 — múltiplos peers (FR-004)
```bash
# Abrir o stream em 2 abas diferentes do browser
# Verificar: ambas mostram vídeo fluido simultaneamente
curl http://localhost:8080/health | python3 -m json.tool
# Verificar: peers_active == 2
```

### Teste 4 — soak test 8h (AC-001)
```bash
# Iniciar o backend e deixar rodando com câmera ativa
# Checar a cada hora:
watch -n 3600 'curl -s http://localhost:8080/health | python3 -m json.tool'
# Verificar: uptime_seconds crescendo, zmq_connected sempre true
```
