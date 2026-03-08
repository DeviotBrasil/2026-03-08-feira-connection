# 2026-03-08-feira-connection
Demo de apresentacao para feira 2026

cd app/service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Descobrir índice da C925e
python discover_camera.py

# Copiar e ajustar .env
cp .env.example .env

# Iniciar
python main.py

# Ou via supervisord (auto-restart)
supervisord -c supervisord.conf

# cliente para testar servico
cd app/service
python zmq_consumer.py
