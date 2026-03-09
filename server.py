"""
ilPostino — Servidor Web
Recibe el formulario de Google y sirve los sitios generados.

Endpoints:
    POST /onboarding        ← Google Apps Script envía aquí los datos del form
    GET  /sitio/{user_id}   ← URL pública del sitio generado
    GET  /status            ← healthcheck
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from aiohttp import web

sys.path.insert(0, str(Path(__file__).parent))

from main import ejecutar_onboarding

SITES_DIR = Path(__file__).parent / "sites"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("ilpostino")


async def handle_onboarding(request: web.Request) -> web.Response:
    """Recibe datos del Google Form y genera el sitio."""
    try:
        data = await request.json()
        log.info(f"📥 Onboarding recibido para: {data.get('name', 'desconocido')}")
    except Exception:
        return web.json_response({"error": "JSON inválido"}, status=400)

    user_id = data.get("user_id") or data.get("email", "").split("@")[0].replace(".", "_")
    if not user_id:
        return web.json_response({"error": "Falta user_id o email"}, status=400)

    datos = {
        "user_id": user_id,
        "name": data.get("name", ""),
        "bio": data.get("bio", ""),
        "projects": data.get("projects", []),
        "links": data.get("links", []),
        "style_preferences": data.get("style_preferences", ""),
        "photo_urls": data.get("photo_urls", []),
    }

    asyncio.create_task(ejecutar_onboarding(datos))

    return web.json_response({
        "status": "procesando",
        "message": "Tu sitio está siendo generado. Listo en ~60 segundos.",
        "sitio_url": f"/sitio/{user_id}",
        "user_id": user_id,
    })


async def handle_site(request: web.Request) -> web.Response:
    """Sirve el sitio generado de un usuario."""
    user_id = request.match_info["user_id"]
    index = SITES_DIR / user_id / "index.html"

    if not index.exists():
        return web.Response(
            text=f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>body{{font-family:sans-serif;text-align:center;padding:80px;background:#fdfbf7}}</style>
</head><body>
<h2>🔄 Tu sitio está siendo generado...</h2>
<p>Usuario: <strong>{user_id}</strong></p>
<p>Volvé en unos segundos y recargá la página.</p>
<script>setTimeout(()=>location.reload(), 8000)</script>
</body></html>""",
            content_type="text/html", status=202,
        )

    return web.Response(
        text=index.read_text(encoding="utf-8"),
        content_type="text/html",
    )


async def handle_status(request: web.Request) -> web.Response:
    sites = [d.name for d in SITES_DIR.iterdir() if d.is_dir()] if SITES_DIR.exists() else []
    return web.json_response({"status": "ok", "sitios": sites})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/onboarding", handle_onboarding)
    app.router.add_get("/sitio/{user_id}", handle_site)
    app.router.add_get("/status", handle_status)
    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    log.info(f"🌐 ilPostino servidor en http://localhost:{port}")
    web.run_app(create_app(), port=port)
