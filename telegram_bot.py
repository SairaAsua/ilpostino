"""
ilPostino — Bot de Telegram
Dos funciones:
1. Onboarding: guía al cliente y genera su sitio web
2. Blog: el cliente manda foto + texto y se crea una entrada de blog
"""

import asyncio
import base64
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

sys.path.insert(0, str(Path(__file__).parent))
from main import ejecutar_onboarding
from tools.github_tools import publish_site_to_github

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("ilpostino-bot")

# Estados onboarding
NOMBRE, EMAIL, BIO, PROYECTOS, LINKS, ESTILO, FOTO, CONFIRMAR = range(8)
# Estados blog
BLOG_FOTO, BLOG_COPY = range(10, 12)

ESTILOS = [
    ["Moderno y minimalista", "Editorial y elegante"],
    ["Creativo y colorido", "Profesional y sobrio"],
]

# Mapeo chat_id → user_id (persiste en disco)
USUARIOS_FILE = Path(__file__).parent / "data" / "usuarios.json"


def cargar_usuarios() -> dict:
    USUARIOS_FILE.parent.mkdir(exist_ok=True)
    if USUARIOS_FILE.exists():
        return json.loads(USUARIOS_FILE.read_text())
    return {}


def guardar_usuario(chat_id: int, user_id: str, nombre: str, email: str):
    usuarios = cargar_usuarios()
    usuarios[str(chat_id)] = {"user_id": user_id, "nombre": nombre, "email": email}
    USUARIOS_FILE.write_text(json.dumps(usuarios, ensure_ascii=False, indent=2))


def obtener_usuario(chat_id: int) -> dict | None:
    return cargar_usuarios().get(str(chat_id))


# ─────────────────────────────────────────────
# ONBOARDING
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    usuario = obtener_usuario(update.effective_chat.id)
    if usuario:
        await update.message.reply_text(
            f"👋 Hola de nuevo *{usuario['nombre'].split()[0]}*!\n\n"
            f"Tu sitio está en:\n"
            f"https://anyprinter001-source.github.io/sites/{usuario['user_id']}/\n\n"
            f"Para publicar una entrada de blog usá /post\n"
            f"Para crear un sitio nuevo escribí /nuevo",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "✨ *¡Bienvenida a ilPostino!*\n\n"
        "Te voy a hacer 6 preguntas para construir tu sitio web personal.\n"
        "En menos de 2 minutos tu sitio estará publicado y online 🚀\n\n"
        "¿Cuál es tu *nombre completo*?",
        parse_mode="Markdown",
    )
    return NOMBRE


async def nuevo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Empecemos de cero 🙌\n\n¿Cuál es tu *nombre completo*?",
        parse_mode="Markdown",
    )
    return NOMBRE


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        f"Hola *{context.user_data['name'].split()[0]}* 👋\n\n"
        "¿Cuál es tu *email*?\n_Te mando el link cuando esté listo._",
        parse_mode="Markdown",
    )
    return EMAIL


async def recibir_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["email"] = update.message.text.strip()
    await update.message.reply_text(
        "Perfecto.\n\n"
        "*¿Quién sos y qué hacés?*\n\n"
        "_Escribí como quieras, informal está bien. Lo pulimos nosotros._",
        parse_mode="Markdown",
    )
    return BIO


async def recibir_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["bio"] = update.message.text.strip()
    await update.message.reply_text(
        "Excelente 🙌\n\n"
        "*¿Cuáles son tus proyectos o trabajos principales?*\n\n"
        "_Uno por línea o separados por coma._",
        parse_mode="Markdown",
    )
    return PROYECTOS


async def recibir_proyectos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    context.user_data["projects"] = [p.strip() for p in texto.replace(",", "\n").split("\n") if p.strip()]
    await update.message.reply_text(
        "Genial 🚀\n\n"
        "*¿Tus links y redes sociales?*\n\n"
        "_LinkedIn, Instagram, portfolio, YouTube... uno por línea._",
        parse_mode="Markdown",
    )
    return LINKS


async def recibir_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    context.user_data["links"] = [l.strip() for l in texto.replace(",", "\n").split("\n") if l.strip()]
    await update.message.reply_text(
        "Última pregunta 🎨\n\n*¿Cómo querés que se vea tu sitio?*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(ESTILOS, one_time_keyboard=True, resize_keyboard=True),
    )
    return ESTILO


async def recibir_estilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["style_preferences"] = update.message.text.strip()
    await update.message.reply_text(
        "📸 *¡Casi terminamos!*\n\n"
        "Mandame una *foto tuya* para poner en tu sitio.\n\n"
        "_Si no tenés una ahora, escribí_ /sinFotoPerfil _y la agregamos después._",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return FOTO


async def recibir_foto_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    foto = update.message.photo[-1]
    file = await foto.get_file()
    foto_bytes = await file.download_as_bytearray()
    context.user_data["foto_perfil_b64"] = base64.b64encode(foto_bytes).decode()
    context.user_data["photo_urls"] = ["data:image/jpeg;base64," + context.user_data["foto_perfil_b64"]]
    await update.message.reply_text("✅ Foto recibida!\n\nAhora confirmá tus datos:")
    return await mostrar_resumen(update, context)


async def sin_foto_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["photo_urls"] = []
    await update.message.reply_text("Sin problema, podés agregarla después con /post\n\nConfirmá tus datos:")
    return await mostrar_resumen(update, context)


async def mostrar_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    datos = context.user_data
    resumen = (
        f"✅ *Confirmá tus datos:*\n\n"
        f"👤 *Nombre:* {datos['name']}\n"
        f"📧 *Email:* {datos['email']}\n"
        f"📝 *Bio:* {datos['bio'][:80]}{'...' if len(datos['bio']) > 80 else ''}\n"
        f"🗂 *Proyectos:* {', '.join(datos['projects'][:3])}\n"
        f"🎨 *Estilo:* {datos['style_preferences']}\n"
        f"📸 *Foto:* {'✅ incluida' if datos.get('photo_urls') else '—'}\n\n"
        f"¿Todo bien?"
    )
    await update.message.reply_text(
        resumen,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["✅ Sí, generar mi sitio", "❌ Empezar de nuevo"]],
            one_time_keyboard=True, resize_keyboard=True,
        ),
    )
    return CONFIRMAR


async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "empezar" in update.message.text.lower():
        return await start(update, context)

    await update.message.reply_text(
        "🔄 *¡Generando tu sitio web!*\n\n"
        "Nuestros agentes de IA están trabajando.\n"
        "Te mando el link en ~60 segundos ✨",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    datos = context.user_data
    email = datos["email"]
    user_id = email.split("@")[0].replace(".", "_").replace("+", "_")
    chat_id = update.effective_chat.id
    app = context.application

    form_data = {
        "user_id": user_id,
        "name": datos["name"],
        "email": email,
        "bio": datos["bio"],
        "projects": datos["projects"],
        "links": datos["links"],
        "style_preferences": datos["style_preferences"],
        "photo_urls": datos.get("photo_urls", []),
    }

    async def pipeline_y_notificar():
        try:
            await ejecutar_onboarding(form_data)
            guardar_usuario(chat_id, user_id, datos["name"], email)
            from tools.github_tools import get_user_site_url
            site_url = get_user_site_url(user_id)
            await app.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🎉 *¡Tu sitio está listo!*\n\n"
                    f"👉 {site_url}\n\n"
                    f"_También te enviamos un email con el link._\n\n"
                    f"💡 *Tip:* Para publicar novedades o entradas de blog "
                    f"mandame una foto con texto usando /post"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            log.error(f"Error en pipeline: {e}")
            await app.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Hubo un error generando tu sitio. Ya estamos revisando.",
            )

    asyncio.create_task(pipeline_y_notificar())
    return ConversationHandler.END


# ─────────────────────────────────────────────
# BLOG POST
# ─────────────────────────────────────────────

async def post_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    usuario = obtener_usuario(update.effective_chat.id)
    if not usuario:
        await update.message.reply_text(
            "Primero necesitás crear tu sitio. Escribí /start 😊"
        )
        return ConversationHandler.END

    context.user_data["blog_usuario"] = usuario
    await update.message.reply_text(
        "📸 *Nueva entrada de blog*\n\n"
        "Mandame la *foto* que querés usar en la entrada.\n"
        "_Si no querés foto, escribí_ /sinFoto",
        parse_mode="Markdown",
    )
    return BLOG_FOTO


async def recibir_foto_blog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    foto = update.message.photo[-1]  # la de mayor resolución
    file = await foto.get_file()
    foto_bytes = await file.download_as_bytearray()
    context.user_data["blog_foto_b64"] = base64.b64encode(foto_bytes).decode()
    context.user_data["blog_tiene_foto"] = True

    await update.message.reply_text(
        "📝 Ahora escribí el *texto de la entrada*.\n\n"
        "_Puede ser un título + descripción, una novedad, un proyecto nuevo, lo que quieras._",
        parse_mode="Markdown",
    )
    return BLOG_COPY


async def sin_foto_blog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["blog_tiene_foto"] = False
    await update.message.reply_text(
        "📝 Escribí el *texto de la entrada*.\n\n"
        "_Puede ser un título, una novedad, un proyecto nuevo, lo que quieras._",
        parse_mode="Markdown",
    )
    return BLOG_COPY


async def recibir_copy_blog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    copy = update.message.text.strip()
    usuario = context.user_data["blog_usuario"]
    user_id = usuario["user_id"]
    tiene_foto = context.user_data.get("blog_tiene_foto", False)
    foto_b64 = context.user_data.get("blog_foto_b64", "")
    fecha = datetime.now().strftime("%d de %B, %Y")
    chat_id = update.effective_chat.id
    app = context.application

    await update.message.reply_text(
        "🔄 *Generando tu entrada de blog...*",
        parse_mode="Markdown",
    )

    async def generar_blog():
        try:
            from tools.blog_tools import publicar_post_y_actualizar_indice

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"blog-{timestamp}.html"

            # Imagen en data URI si hay foto
            img_tag = ""
            if tiene_foto and foto_b64:
                img_tag = f'<img src="data:image/jpeg;base64,{foto_b64}" style="width:100%;max-width:700px;border-radius:12px;margin-bottom:24px;" alt="imagen">'

            # Título = primera línea del copy
            lineas = [l.strip() for l in copy.strip().split("\n") if l.strip()]
            titulo = lineas[0][:80] if lineas else "Nueva entrada"
            excerpt = copy[:160].replace("\n", " ") + ("..." if len(copy) > 160 else "")

            # HTML del post individual
            blog_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo} — {usuario['nombre']}</title>
<style>
  :root {{ --bg:#FDFBF7; --text:#2D2926; --accent:#A0522D; --muted:#7a6f68; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Georgia',serif;
         max-width:700px; margin:0 auto; padding:48px 24px; }}
  .back {{ font-size:13px; color:var(--accent); text-decoration:none;
           letter-spacing:1px; text-transform:uppercase; display:inline-block; margin-bottom:40px; }}
  .fecha {{ font-size:13px; color:var(--muted); letter-spacing:1px; text-transform:uppercase; margin-bottom:24px; }}
  h1 {{ font-size:28px; font-weight:normal; margin-bottom:24px; line-height:1.4; }}
  img {{ width:100%; border-radius:12px; margin-bottom:32px; }}
  .copy {{ font-size:18px; line-height:1.85; white-space:pre-wrap; }}
  hr {{ border:none; border-top:1px solid #e8e0d5; margin:48px 0; }}
  footer {{ font-size:13px; color:var(--muted); text-align:center; }}
  footer a {{ color:var(--accent); text-decoration:none; }}
</style>
</head>
<body>
  <a href="../" class="back">← Blog</a>
  <p class="fecha">{fecha}</p>
  <h1>{titulo}</h1>
  {img_tag}
  <div class="copy">{copy}</div>
  <hr>
  <footer>
    <a href="../../">{usuario['nombre']}</a>
    &nbsp;·&nbsp; ilPostino
  </footer>
</body>
</html>"""

            # Publicar post + actualizar índice
            post_url = publicar_post_y_actualizar_indice(
                user_id=user_id,
                nombre_usuario=usuario["nombre"],
                filename=filename,
                fecha=fecha,
                titulo=titulo,
                excerpt=excerpt,
                tiene_foto=tiene_foto,
                blog_html=blog_html,
            )

            from tools.github_tools import get_user_site_url
            blog_index_url = get_user_site_url(user_id) + "blog/"

            await app.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"✅ *¡Entrada publicada!*\n\n"
                    f"📄 Este post:\n{post_url}\n\n"
                    f"📚 Índice del blog:\n{blog_index_url}\n\n"
                    f"_Compartí donde quieras 🚀_"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            log.error(f"Error en blog: {e}")
            await app.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Error publicando la entrada. Intentá de nuevo.",
            )

    asyncio.create_task(generar_blog())
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelado. Escribí /start cuando quieras.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

def crear_bot(token: str) -> Application:
    app = Application.builder().token(token).build()

    # Conversación de onboarding
    onboarding = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("nuevo", nuevo),
        ],
        states={
            NOMBRE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            EMAIL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_email)],
            BIO:       [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_bio)],
            PROYECTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_proyectos)],
            LINKS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_links)],
            ESTILO:    [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_estilo)],
            FOTO: [
                MessageHandler(filters.PHOTO, recibir_foto_perfil),
                CommandHandler("sinFotoPerfil", sin_foto_perfil),
            ],
            CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    # Conversación de blog
    blog = ConversationHandler(
        entry_points=[CommandHandler("post", post_start)],
        states={
            BLOG_FOTO: [
                MessageHandler(filters.PHOTO, recibir_foto_blog),
                CommandHandler("sinFoto", sin_foto_blog),
            ],
            BLOG_COPY: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_copy_blog)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(onboarding)
    app.add_handler(blog)
    return app


if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("❌ Falta TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    print("🤖 ilPostino Bot corriendo en @journalBord_bot")
    print("   /start  → crear sitio web")
    print("   /post   → publicar entrada de blog")
    crear_bot(token).run_polling(drop_pending_updates=True)
