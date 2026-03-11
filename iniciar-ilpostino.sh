#!/bin/bash
# Inicia il Postino Bot + Dashboard local
# Uso: ./iniciar-ilpostino.sh

DIR=/home/saira/amapola/ilpostino
VENV=/home/saira/amapola/.venv
ENV_FILE="$DIR/.env"
ADK_ENV=/home/saira/amapola/generative-ai/gemini/agents/always-on-memory-agent/.env

# Cargar variables
export GOOGLE_API_KEY=$(grep GOOGLE_API_KEY "$ADK_ENV" | cut -d'"' -f2)
export GITHUB_TOKEN=$(grep GITHUB_TOKEN "$ENV_FILE" | cut -d'"' -f2)
export GITHUB_OWNER=$(grep GITHUB_OWNER "$ENV_FILE" | cut -d'"' -f2)
export GITHUB_REPO=$(grep GITHUB_REPO "$ENV_FILE" | cut -d'"' -f2)
export GMAIL_USER=$(grep GMAIL_USER "$ENV_FILE" | cut -d'"' -f2)
export GMAIL_APP_PASSWORD=$(grep GMAIL_APP_PASSWORD "$ENV_FILE" | cut -d'"' -f2)
export TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN "$ENV_FILE" | cut -d'"' -f2)

cd "$DIR"

# Matar instancias previas
pkill -f "telegram_bot.py" 2>/dev/null
pkill -f "dashboard_server.py" 2>/dev/null
sleep 1

# Iniciar bot
nohup "$VENV/bin/python" telegram_bot.py >> /tmp/ilpostino-bot.log 2>&1 &
BOT_PID=$!

# Iniciar dashboard
nohup "$VENV/bin/python" dashboard_server.py >> /tmp/ilpostino-dashboard.log 2>&1 &
DASH_PID=$!

sleep 3

echo ""
echo "======================================================"
echo "✉  Il Postino Bot — ACTIVO"
echo ""
echo "🤖 Bot:       @ilpostino_bot (PID $BOT_PID)"
echo "📊 Dashboard: http://localhost:7788  (PID $DASH_PID)"
echo ""
echo "Logs en tiempo real:"
echo "  Bot:       tail -f /tmp/ilpostino-bot.log"
echo "  Dashboard: tail -f /tmp/ilpostino-dashboard.log"
echo "======================================================"
