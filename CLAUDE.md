# Il Postino Bot — Guía para Claude

## Qué es este proyecto
Bot de Telegram que genera sitios web personales vía IA y los publica en GitHub Pages.
El usuario completa un onboarding por chat y en ~10 minutos tiene su sitio online.

## Stack
- **python-telegram-bot 22.6** — bot y ConversationHandlers
- **Google ADK 1.26** — pipeline de agentes IA (brief → web → publish)
- **Gemini** — modelo `gemini-3.1-flash-lite-preview` para agentes, `gemini-2.0-flash-lite` para edición directa
- **GitHub API** — crea repos, publica archivos, activa GitHub Pages
- **Google Cloud Run** — hosting 24/7 con polling
- **Google Cloud Storage** — persistencia en producción (detectado por `GCS_BUCKET` env var)

## Estructura de repos de usuarios
- Owner: `anyprinter001-source`
- Repo: `jb-{user_id}` donde `user_id = email.split("@")[0]` con `.` y `+` → `_`
- URL: `https://anyprinter001-source.github.io/jb-{user_id}/`

## Variables de entorno requeridas
```
TELEGRAM_BOT_TOKEN
GOOGLE_API_KEY
GITHUB_TOKEN
GCS_BUCKET          # en producción: ilpostino-data-ilpostino-489904
GITHUB_OWNER        # default: anyprinter001-source
```

## Deploy
```bash
GITHUB_TOKEN=$(gh auth token) \
TELEGRAM_BOT_TOKEN="..." \
GOOGLE_API_KEY="..." \
CLOUDSDK_PYTHON=/usr/bin/python3 \
PATH="/home/saira/google-cloud-sdk/bin:$PATH" \
bash deploy-cloudrun.sh
```

## Convenciones de código
- Todas las funciones de persistencia usan `tools/cloud_storage.py` (nunca Path directamente)
- Los handlers async usan `context.application.create_task()` para background tasks (no `asyncio.create_task()`)
- Un solo pipeline a la vez: `_pipeline_lock = asyncio.Lock()`
- Siempre verificar que el usuario tiene sitio antes de comandos de edición

## Comandos del bot
| Comando | Estado | Descripción |
|---------|--------|-------------|
| /start | ✅ | Onboarding completo |
| /nuevo | ✅ | Sitio nuevo desde cero |
| /post | ✅ | Entrada de blog (foto + texto) |
| /edit | ✅ | Editar texto/estilo/colores vía prompt libre |
| /nuevaseccion | ✅ | Agregar sección nueva con IA |
| /eliminar | ✅ | Eliminar secciones o contenido |
| /panel | ✅ | Dashboard admin (chat_id 2083458641) |
| /cancelar | ✅ | Cancelar conversación |

## Estilos disponibles en onboarding
No hay teclado fijo — el usuario recibe 5 combinaciones sugeridas y puede escribir lo que quiera:
- 🟫 Tierra & Calma (Beige + Terracota, Georgia)
- 🖤 Noche Digital (Negro + Verde eléctrico, Space Grotesk)
- 🌸 Rosa Editorial (Blush + Ciruela, Playfair Display)
- 🌿 Verde Bosque (Crema + Verde musgo, DM Serif)
- 🔵 Azul Estudio (Blanco + Azul marino, Inter)

## Edición IA (tools/edit_tools.py)
- Modelo: `gemini-2.0-flash-lite` directo (no ADK)
- `editar_html()`, `agregar_seccion()`, `eliminar_contenido()`
- Helper `_aplicar_edicion_html()` en `telegram_bot.py` maneja todo el flujo GitHub

## Flujo del pipeline de onboarding
1. `telegram_bot.py` recolecta datos → sube fotos a GitHub antes de pasar al pipeline
2. `main.py:ejecutar_onboarding()` → ADK Runner con `director`
3. `agents/brief_agent.py` → procesa y estructura el brief
4. `agents/web_builder_agent.py` → genera HTML completo (4 secciones)
5. `agents/publisher_agent.py` → publica index.html + primer blog post
6. Bot notifica → espera 10 min → envía email + QR

## Notas importantes
- Las fotos de perfil y blog se suben a GitHub ANTES del pipeline para evitar pasar base64 a los agentes (causa 429 o error de Pydantic)
- El pipeline tiene retry automático en 429 (3 intentos, backoff 60s)
- Cloud Run corre en **polling mode** + health check HTTP en thread separado (webhook mode falla por timeout de startup)
- `deploy-cloudrun.sh` NO activa webhook — borra el webhook al final para asegurar polling
- `tools/cloud_storage.py` detecta entorno por la variable `GCS_BUCKET`
