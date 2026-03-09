#!/bin/bash
set -e

VENV=/home/saira/amapola/.venv
DIR=/home/saira/amapola/ilpostino
ENV_FILE="$DIR/.env"

# Cargar variables
export GOOGLE_API_KEY=$(grep GOOGLE_API_KEY "$DIR/../generative-ai/gemini/agents/always-on-memory-agent/.env" | cut -d'"' -f2)
export GITHUB_TOKEN=$(grep GITHUB_TOKEN "$ENV_FILE" | cut -d'"' -f2)
export GITHUB_OWNER=$(grep GITHUB_OWNER "$ENV_FILE" | cut -d'"' -f2)
export GITHUB_REPO=$(grep GITHUB_REPO "$ENV_FILE" | cut -d'"' -f2)

echo "🧠 ilPostino iniciando..."
pkill -f "python server.py" 2>/dev/null || true
pkill -f "ngrok http" 2>/dev/null || true
sleep 1

cd "$DIR"
GOOGLE_API_KEY="$GOOGLE_API_KEY" GITHUB_TOKEN="$GITHUB_TOKEN" \
GITHUB_OWNER="$GITHUB_OWNER" GITHUB_REPO="$GITHUB_REPO" \
"$VENV/bin/python" server.py > /tmp/ilpostino-server.log 2>&1 &
echo "✅ Servidor iniciado"
sleep 2

ngrok http 8080 --log=stdout > /tmp/ngrok.log 2>&1 &
sleep 3

URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json; t=json.load(sys.stdin)['tunnels']; print([x for x in t if x['proto']=='https'][0]['public_url'])" 2>/dev/null)

echo ""
echo "======================================================"
echo "🌐 Webhook para Apps Script:"
echo "   $URL/onboarding"
echo ""
echo "🐙 Sitios en GitHub Pages:"
echo "   https://anyprinter001-source.github.io/sites/{user_id}/"
echo "======================================================"
