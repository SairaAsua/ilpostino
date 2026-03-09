# ilPostino — Arquitectura del sistema

## Descripción del sistema

ilPostino es un sistema multi-agente que toma datos crudos de un usuario (nombre, bio, proyectos, links, preferencias de estilo) y genera, publica y mantiene vivo un sitio web personal estático en GitHub Pages. El sistema tiene dos entradas: un bot de Telegram (canal principal) y un servidor HTTP que puede recibir datos de Google Forms. La publicación es automática: el usuario nunca toca código ni GitHub.

Cada usuario recibe su propio repositorio GitHub (`jb-{user_id}`), activado con GitHub Pages desde el primer momento.

---

## Diagrama ASCII del flujo completo

```
ONBOARDING (nuevo usuario)
─────────────────────────────────────────────────────────────────

Usuario Telegram
     │
     │ /start → 6 preguntas conversacionales
     │ (nombre, email, bio, proyectos, links, estilo, foto)
     ▼
telegram_bot.py  ──────────────────►  main.py::ejecutar_onboarding()
                                              │
                                              ▼
                                     Google ADK Runner
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │    DIRECTOR      │  (LlmAgent)
                                    │  detecta tipo    │
                                    │  de solicitud    │
                                    └────────┬─────────┘
                                             │ onboarding_pipeline
                                             ▼
                              ┌──────────────────────────────┐
                              │     SequentialAgent           │
                              │  onboarding_pipeline          │
                              └──────────────────────────────┘
                                    │
                        ┌───────────▼────────────┐
                        │      brief_agent        │  raw_form_data → brief
                        └───────────┬────────────┘
                        ┌───────────▼────────────┐
                        │     content_agent       │  brief → web_copy
                        └───────────┬────────────┘
                        ┌───────────▼────────────┐
                        │     design_agent        │  brief → design_tokens
                        └───────────┬────────────┘
                        ┌───────────▼────────────┐
                        │   web_builder_agent     │  copy + tokens → HTML
                        └───────────┬────────────┘
                        ┌───────────▼────────────┐
                        │    publisher_agent      │  HTML → GitHub Pages
                        │  crea repo jb-{user_id} │  + README.md
                        └───────────┬────────────┘
                        ┌───────────▼────────────┐
                        │      email_agent        │  email de confirmación
                        └───────────┬────────────┘
                                    │
                                    ▼
                    Usuario recibe en Telegram:
                    "🎉 Tu sitio está listo → https://..."
                    + email con link y CTA


BLOG POST (/post)
─────────────────────────────────────────────────────────────────

Usuario Telegram
     │
     │ /post → foto (opcional) → texto
     ▼
telegram_bot.py::recibir_copy_blog()
     │
     │  genera HTML del post con CSS inline
     ▼
blog_tools.py::publicar_post_y_actualizar_indice()
     │
     ├── GitHub: sube blog/{timestamp}.html
     ├── GitHub: actualiza blog/posts.json
     └── GitHub: regenera blog/index.html
     │
     ▼
Usuario recibe en Telegram:
"✅ Entrada publicada → URL del post + URL del blog"


ACTUALIZACIÓN TELEGRAM (usuario existente, texto libre)
─────────────────────────────────────────────────────────────────

Usuario Telegram
     │ mensaje de texto (ej: "lancé un nuevo proyecto...")
     ▼
main.py::ejecutar_actualizacion_telegram()
     │
     ▼
DIRECTOR → update_pipeline (SequentialAgent)
     │
     ├── telegram_agent_update  → classify_update() → structured_update
     ├── content_agent_update   → structured_update → update_copy
     ├── web_builder_update     → update_copy → HTML
     └── publisher_update       → guarda update_latest.html en disco


ENTRADA VÍA HTTP (Google Forms)
─────────────────────────────────────────────────────────────────

Google Apps Script
     │
     │ POST /onboarding  (JSON con datos del form)
     ▼
server.py  ──────────► main.py::ejecutar_onboarding()  (mismo pipeline)
     │
     │ responde inmediato: {"status": "procesando"}
     └── pipeline corre en background (asyncio.create_task)
```

---

## Mapa de agentes

| Nombre | Modelo | Rol | Input (session state) | Output (session state) |
|--------|--------|-----|-----------------------|------------------------|
| `director` | gemini-3.1-flash-lite-preview | Orquestador. Detecta si es onboarding o actualización y deriva al pipeline correcto. | `raw_form_data` o `telegram_raw` + `user_id` | — |
| `brief_agent` | gemini-3.1-flash-lite-preview | Analiza el formulario crudo y produce un brief estructurado con headline, bio pulida, proyectos y tono. | `raw_form_data` | `brief` (StructuredBrief) |
| `content_agent` | gemini-3.1-flash-lite-preview | Copywriter. Genera hero, about, proyectos y tagline para el sitio. | `brief` | `web_copy` (JSON) |
| `design_agent` | gemini-3.1-flash-lite-preview | Diseñador. Elige paleta de colores, tipografía y layout según el tono del usuario. Respeta WCAG AA. | `brief` | `design_tokens` (DesignTokens) |
| `web_builder_agent` | gemini-3.1-flash-lite-preview | Desarrollador. Genera el HTML/CSS completo del sitio (una sola página, responsive, sin JS externo). | `web_copy`, `design_tokens`, `brief` | `html_output` |
| `publisher_agent` | gemini-3.1-flash-lite-preview | Publicador. Crea el repo `jb-{user_id}`, activa GitHub Pages, sube `index.html` y genera `README.md` personalizado. Fallback: guarda en disco. | `html_output`, `brief` | — |
| `email_agent` | gemini-3.1-flash-lite-preview | Notificador. Envía email HTML de confirmación con el link al sitio publicado. | `brief`, `raw_form_data` | — |
| `telegram_agent_update` | gemini-3.1-flash-lite-preview | Parser. Clasifica el mensaje de Telegram (blog_post, project_update, bio_update, news) usando `classify_update`. | `telegram_raw` | `structured_update` |
| `content_agent_update` | gemini-3.1-flash-lite-preview | Copywriter de actualizaciones. Convierte el mensaje clasificado en contenido web listo. | `structured_update` | `update_copy` |
| `web_builder_update` | gemini-3.1-flash-lite-preview | Genera bloque HTML para la actualización. | `update_copy` | `html_output` |
| `publisher_update` | gemini-3.1-flash-lite-preview | Guarda la actualización en disco como `update_latest.html`. | `html_output`, `user_id` | — |

**Pipelines:**

- `onboarding_pipeline` — `SequentialAgent`: brief → content → design → web_builder → publisher → email
- `update_pipeline` — `SequentialAgent`: telegram_agent_update → content_agent_update → web_builder_update → publisher_update

---

## Estructura de archivos

```
ilpostino/
│
├── main.py                  # Punto de entrada. Define ejecutar_onboarding() y
│                            # ejecutar_actualizacion_telegram(). Instancia el Runner de ADK.
│
├── telegram_bot.py          # Bot de Telegram (python-telegram-bot).
│                            # Maneja dos ConversationHandler:
│                            #   - onboarding: /start → 6 preguntas → confirmar
│                            #   - blog: /post → foto → texto → publicar
│
├── server.py                # Servidor HTTP aiohttp.
│                            # Endpoints: POST /onboarding, GET /sitio/{user_id}, GET /status
│
├── iniciar-todo.sh          # Script de arranque: inicia server.py en background,
│                            # levanta ngrok en :8080, imprime la URL del webhook.
│
├── .env                     # Variables de entorno (no commitear)
│
├── agents/
│   ├── director.py          # LlmAgent raíz. Sub-agentes: onboarding_pipeline, update_pipeline
│   ├── brief_agent.py       # LlmAgent → StructuredBrief. Output key: "brief"
│   ├── content_agent.py     # LlmAgent (copy onboarding) + LlmAgent (copy updates)
│   ├── design_agent.py      # LlmAgent → DesignTokens. Output key: "design_tokens"
│   ├── web_builder_agent.py # LlmAgent. Usa tool: render_html_template. Output key: "html_output"
│   ├── publisher_agent.py   # LlmAgent. Usa tools: publish_site_to_github, save_site_to_disk
│   ├── email_agent.py       # LlmAgent. Usa tool: send_site_ready_email
│   └── telegram_agent.py    # LlmAgent standalone (no usado en pipelines activos)
│
├── pipelines/
│   ├── onboarding.py        # SequentialAgent: 6 agentes en cadena para nuevo usuario
│   └── update.py            # SequentialAgent: 4 agentes para actualización vía Telegram texto
│
├── schemas/
│   └── brief.py             # Modelos Pydantic: GoogleFormData, StructuredBrief,
│                            # Project, SocialLink, DesignTokens
│
├── tools/
│   ├── github_tools.py      # GitHub API: crear repo, activar Pages, subir archivos,
│                            # publish_site_to_github, publish_file_to_user_repo
│   ├── blog_tools.py        # publicar_post_y_actualizar_indice: sube post HTML,
│                            # actualiza posts.json y regenera blog/index.html
│   ├── email_tools.py       # send_site_ready_email: SMTP Gmail con email HTML
│   ├── file_tools.py        # render_html_template, save_site_to_disk (backup local)
│   └── telegram_tools.py    # classify_update: clasifica tipo de mensaje por keywords
│
├── data/
│   └── usuarios.json        # Mapeo chat_id → {user_id, nombre, email}. Persiste en disco.
│
└── sites/
    └── {user_id}/
        └── index.html       # Backup local del sitio generado (si falla GitHub)
```

---

## Variables de entorno requeridas

| Variable | Descripción | Dónde se usa |
|----------|-------------|--------------|
| `GOOGLE_API_KEY` | API key de Google AI Studio para los modelos Gemini | ADK Runner, todos los agentes |
| `GITHUB_TOKEN` | Personal Access Token de GitHub con permisos `repo` | `github_tools.py`: crear repos, subir archivos |
| `GITHUB_OWNER` | Usuario u organización de GitHub donde se crean los repos | `github_tools.py`: `get_owner()` → default `anyprinter001-source` |
| `GITHUB_REPO` | Nombre del repo raíz (referencia histórica, los sitios van en repos individuales `jb-{user_id}`) | `.env` |
| `GMAIL_USER` | Dirección Gmail desde la que se envían los emails de confirmación | `email_tools.py` |
| `GMAIL_APP_PASSWORD` | App Password de Gmail (no la contraseña normal, generada en Cuenta Google → Seguridad) | `email_tools.py` |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram obtenido de @BotFather | `telegram_bot.py` |

**Archivo `.env` de ejemplo:**
```
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
GITHUB_OWNER="tu-usuario-github"
GITHUB_REPO="sites"
GMAIL_USER="tu@gmail.com"
GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
TELEGRAM_BOT_TOKEN="123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

`GOOGLE_API_KEY` se carga por separado en `iniciar-todo.sh` desde el entorno del sistema o de otro `.env`.

---

## Comandos exactos para arrancar el sistema

### Modo completo (servidor HTTP + ngrok + variables de entorno)

```bash
cd /home/saira/amapola/ilpostino
bash iniciar-todo.sh
```

El script:
1. Carga `GOOGLE_API_KEY` desde el `.env` del agente de memoria
2. Carga `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO` desde `ilpostino/.env`
3. Mata procesos previos de `server.py` y `ngrok`
4. Inicia `server.py` en background (log en `/tmp/ilpostino-server.log`)
5. Inicia ngrok en puerto 8080 (log en `/tmp/ngrok.log`)
6. Imprime la URL pública del webhook

### Solo el bot de Telegram

```bash
cd /home/saira/amapola/ilpostino
source ../.venv/bin/activate
export GOOGLE_API_KEY="tu-api-key"
export GITHUB_TOKEN="..."   # o cargar desde .env
export GMAIL_USER="..."
export GMAIL_APP_PASSWORD="..."
export TELEGRAM_BOT_TOKEN="..."
python telegram_bot.py
```

### Solo el servidor HTTP

```bash
cd /home/saira/amapola/ilpostino
source ../.venv/bin/activate
export GOOGLE_API_KEY="..."
export GITHUB_TOKEN="..."
python server.py
# Escucha en http://localhost:8080
```

### Prueba de onboarding con datos de ejemplo (sin Telegram)

```bash
cd /home/saira/amapola/ilpostino
source ../.venv/bin/activate
export GOOGLE_API_KEY="..."
python main.py
```

### Ver logs en tiempo real

```bash
tail -f /tmp/ilpostino-server.log
tail -f /tmp/ngrok.log
```

---

## URLs y endpoints

### Servidor HTTP local (server.py)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `http://localhost:8080/onboarding` | Recibe JSON con datos del usuario desde Google Apps Script. Responde inmediato, genera el sitio en background. |
| `GET` | `http://localhost:8080/sitio/{user_id}` | Sirve el `index.html` local del usuario. Si no existe aún, muestra página de espera con auto-reload. |
| `GET` | `http://localhost:8080/status` | Healthcheck. Devuelve lista de sitios generados localmente. |

**Ejemplo de payload para `POST /onboarding`:**
```json
{
  "user_id": "maria_gomez",
  "name": "María Gómez",
  "email": "maria@ejemplo.com",
  "bio": "Consultora de marca personal...",
  "projects": ["Proyecto A", "Proyecto B"],
  "links": ["https://linkedin.com/in/maria"],
  "style_preferences": "Moderno y minimalista",
  "photo_urls": []
}
```

### GitHub Pages (sitios publicados)

| URL | Descripción |
|-----|-------------|
| `https://{GITHUB_OWNER}.github.io/jb-{user_id}/` | Sitio personal del usuario |
| `https://{GITHUB_OWNER}.github.io/jb-{user_id}/blog/` | Índice del blog del usuario |
| `https://{GITHUB_OWNER}.github.io/jb-{user_id}/blog/{timestamp}.html` | Entrada individual de blog |

**Ejemplo real con owner `anyprinter001-source` y user_id `asuasaira`:**
- Sitio: `https://anyprinter001-source.github.io/jb-asuasaira/`
- Blog: `https://anyprinter001-source.github.io/jb-asuasaira/blog/`

### Telegram

- Bot activo: `@journalBord_bot`
- Comandos disponibles:
  - `/start` — inicia onboarding o muestra el sitio si ya existe
  - `/nuevo` — fuerza un onboarding nuevo
  - `/post` — inicia flujo de blog post (foto + texto)
  - `/sinFotoPerfil` — omite foto de perfil en onboarding
  - `/sinFoto` — omite foto en blog post
  - `/cancelar` — cancela cualquier conversación activa

### ngrok (webhook externo para Google Apps Script)

```
https://{url-ngrok-dinamica}/onboarding
```
La URL se imprime al ejecutar `iniciar-todo.sh`. Debe configurarse en el Google Apps Script que procesa el formulario de Google.
