#!/bin/bash
# ─────────────────────────────────────────────────────
#  Il Postino Bot — Deploy a Google Cloud Run
#  Ejecutá este script una sola vez para desplegar.
#  Requiere tener gcloud instalado y configurado.
# ─────────────────────────────────────────────────────

set -e

PROJECT_ID="${GCLOUD_PROJECT:-ilpostino-489904}"
REGION="us-central1"
SERVICE_NAME="ilpostino-bot"
BUCKET_NAME="ilpostino-data-${PROJECT_ID}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Desplegando Il Postino Bot"
echo "   Proyecto: ${PROJECT_ID}"
echo "   Región:   ${REGION}"
echo ""

# ── 1. Verificar variables de entorno requeridas ──────
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "❌ Falta TELEGRAM_BOT_TOKEN"
  echo "   Ejecutá: export TELEGRAM_BOT_TOKEN='tu-token'"
  exit 1
fi
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "❌ Falta GOOGLE_API_KEY"
  echo "   Ejecutá: export GOOGLE_API_KEY='tu-api-key'"
  exit 1
fi
if [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ Falta GITHUB_TOKEN"
  echo "   Ejecutá: export GITHUB_TOKEN='tu-token-github'"
  exit 1
fi

# ── 2. Crear bucket GCS si no existe ─────────────────
echo "📦 Creando bucket GCS: gs://${BUCKET_NAME}"
gcloud storage buckets create "gs://${BUCKET_NAME}" \
  --location="${REGION}" \
  --uniform-bucket-level-access \
  2>/dev/null || echo "   (bucket ya existe, continuando)"

# ── 3. Build y push imagen Docker ────────────────────
echo "🐳 Construyendo imagen Docker..."
gcloud builds submit --tag "${IMAGE}" .

# ── 4. Deploy a Cloud Run ─────────────────────────────
echo "☁️  Desplegando en Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --min-instances 1 \
  --max-instances 3 \
  --memory 512Mi \
  --timeout 3600 \
  --set-env-vars "GCS_BUCKET=${BUCKET_NAME}" \
  --set-env-vars "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}" \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
  --set-env-vars "GITHUB_TOKEN=${GITHUB_TOKEN}" \
  --allow-unauthenticated

# ── 5. Obtener URL del servicio ───────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format "value(status.url)")

# ── 6. Asegurarse de que no haya webhook activo (modo polling) ────
echo "🔗 Eliminando webhook de Telegram (modo polling)..."
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" \
  | python3 -m json.tool

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ¡Il Postino Bot está online!"
echo "   Servicio: ${SERVICE_URL}"
echo "   Modo:     polling (siempre activo)"
echo "   Bucket:   gs://${BUCKET_NAME}"
echo ""
echo "Para ver logs en tiempo real:"
echo "   gcloud run services logs tail ${SERVICE_NAME} --region ${REGION}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
