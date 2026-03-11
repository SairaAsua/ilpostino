"""
Script único para notificar a todos los usuarios de su nuevo link de sitio.
Ejecutar UNA SOLA VEZ después del cambio de nombre a ilPostinob0t.

Uso:
    python notificar_usuarios.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tools.cloud_storage as storage
from tools.github_tools import get_user_site_url

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")


async def notificar():
    from telegram import Bot

    if not TELEGRAM_BOT_TOKEN:
        print("❌ Falta TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    usuarios = storage.leer_json("usuarios.json", {})

    if not usuarios:
        print("No hay usuarios registrados.")
        return

    print(f"Notificando a {len(usuarios)} usuarios...")

    for chat_id, u in usuarios.items():
        user_id = u.get("user_id", "")
        nombre = u.get("nombre", "").split()[0]
        site_url = get_user_site_url(user_id)

        try:
            await bot.send_message(
                chat_id=int(chat_id),
                text=(
                    f"👋 Hola *{nombre}*!\n\n"
                    f"Te avisamos que actualizamos la dirección de Il Postino Bot. "
                    f"Tu sitio web sigue siendo exactamente el mismo, "
                    f"solo cambió el link:\n\n"
                    f"👉 *{site_url}*\n\n"
                    f"Guardalo o compartilo donde quieras 🚀\n\n"
                    f"_— El equipo de Il Postino_"
                ),
                parse_mode="Markdown",
            )
            print(f"  ✅ {nombre} ({chat_id}) → {site_url}")
        except Exception as e:
            print(f"  ⚠️  {nombre} ({chat_id}): {e}")

    print("\nListo.")


if __name__ == "__main__":
    asyncio.run(notificar())
