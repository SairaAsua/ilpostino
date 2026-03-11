"""
ilPostino — Bot de Telegram
Dos funciones:
1. Onboarding: guía al cliente y genera su sitio web
2. Blog: el cliente manda foto + texto y se crea una entrada de blog
"""

import asyncio
import base64
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
from tools.github_tools import publish_site_to_github, upload_photo_to_repo
from tools.qr_tools import generar_qr_estampilla
from tools.dashboard import generar_dashboard, registrar_cambio
from tools.eventos import registrar_evento
import tools.cloud_storage as storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("ilpostino-bot")

# Semáforo: solo un pipeline a la vez, con pausa de 2 minutos entre ellos
_pipeline_lock = asyncio.Lock()
EMAIL_DELAY_SECONDS = 600   # 10 minutos antes de enviar el mail
PIPELINE_COOLDOWN_SECONDS = 120  # 2 minutos entre pipelines

# Estados onboarding
NOMBRE, EMAIL, BIO, PROYECTOS, LINKS, ESTILO, FOTO, CONFIRMAR = range(8)
# Estados blog inicial (dentro del onboarding)
BLOG_PREGUNTA, BLOG_TITULO, BLOG_FOTO_ONBOARDING = range(8, 11)
# Estados blog post (/post)
BLOG_FOTO, BLOG_COPY = range(20, 22)
# Estados edición
EDITAR_PROMPT = 40
NUEVA_SECCION_DESC = 41
ELIMINAR_DESC = 42

ESTILO_MSG = """🎨 *¿Cómo querés que se vea tu sitio?*

Podés elegir una de estas combinaciones o escribir lo que quieras:

🟫 *Tierra & Calma* — Beige + Terracota · Georgia
🖤 *Noche Digital* — Negro + Verde eléctrico · Space Grotesk
🌸 *Rosa Editorial* — Blush + Ciruela · Playfair Display
🌿 *Verde Bosque* — Crema + Verde musgo · DM Serif
🔵 *Azul Estudio* — Blanco + Azul marino · Inter

O describí lo que tenés en mente, por ejemplo:
_"Fondo negro, textos en dorado, tipografía serif"_
_"Colores pasteles, estilo japonés minimalista"_
_"Verde salvia, tipografía moderna sans-serif"_"""

# Mapeo chat_id → user_id (persiste en GCS o disco local)
_USUARIOS_KEY = "usuarios.json"


def cargar_usuarios() -> dict:
    return storage.leer_json(_USUARIOS_KEY, {})


def guardar_usuario(chat_id: int, user_id: str, nombre: str, email: str):
    usuarios = cargar_usuarios()
    usuarios[str(chat_id)] = {"user_id": user_id, "nombre": nombre, "email": email}
    storage.escribir_json(_USUARIOS_KEY, usuarios)


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
        ESTILO_MSG,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
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
    registrar_evento("mensaje_recibido", "", context.user_data.get("name", ""),
                     "Usuario confirmó datos de onboarding")

    nombre_corto = context.user_data["name"].split()[0]
    await update.message.reply_text(
        f"¡Perfecto, {nombre_corto}! 🎉\n\n"
        f"📝 *¿Querés crear tu primera entrada de blog ahora?*\n\n"
        f"Si decís que sí, te pido el título y una foto.\n"
        f"Si no, creamos una entrada de bienvenida automática.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["✍️ Sí, creo mi primer blog", "⏭ No, hacelo automático"]],
            one_time_keyboard=True, resize_keyboard=True,
        ),
    )
    return BLOG_PREGUNTA


async def blog_pregunta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text.lower()
    if "sí" in respuesta or "si" in respuesta or "creo" in respuesta:
        await update.message.reply_text(
            "✍️ *¿Cuál es el título de tu primera entrada?*\n\n"
            "_Por ejemplo: \"Hola, soy [nombre] y esto es lo que hago\" "
            "o cualquier tema que quieras compartir._",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return BLOG_TITULO
    else:
        # Sin blog manual → entrada automática de bienvenida
        context.user_data["blog_inicial_titulo"] = None
        context.user_data["blog_inicial_foto_b64"] = None
        return await _lanzar_pipeline(update, context)


async def blog_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["blog_inicial_titulo"] = update.message.text.strip()
    await update.message.reply_text(
        "📸 *Mandame una foto para la entrada.*\n\n"
        "_Si no tenés una ahora, escribí_ /sinFotoBlog",
        parse_mode="Markdown",
    )
    return BLOG_FOTO_ONBOARDING


async def blog_foto_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    foto = update.message.photo[-1]
    file = await foto.get_file()
    foto_bytes = await file.download_as_bytearray()
    context.user_data["blog_inicial_foto_b64"] = base64.b64encode(foto_bytes).decode()
    await update.message.reply_text("✅ Foto recibida. Arrancando...")
    return await _lanzar_pipeline(update, context)


async def sin_foto_blog_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["blog_inicial_foto_b64"] = None
    await update.message.reply_text("Sin foto, entendido.")
    return await _lanzar_pipeline(update, context)


async def _lanzar_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Punto de entrada al pipeline después de recolectar todos los datos."""
    await update.message.reply_text(
        "🔄 *¡Generando tu sitio web!*\n\n"
        "Nuestros agentes de IA están trabajando.\n"
        "En unos *10 minutos* tu sitio estará publicado y online ✨\n\n"
        "_Te aviso por acá cuando esté listo y también te mando un email._",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    datos = context.user_data
    email = datos["email"]
    user_id = email.split("@")[0].replace(".", "_").replace("+", "_")
    chat_id = update.effective_chat.id
    app = context.application

    from tools.github_tools import _crear_repo_usuario, get_repo_name, get_owner

    # Crear el repo antes de subir fotos
    try:
        _crear_repo_usuario(get_owner(), get_repo_name(user_id), datos["name"])
    except Exception as repo_err:
        log.warning(f"Error creando repo: {repo_err}")

    # Subir foto de perfil si existe (evitar pasar base64 por el pipeline)
    photo_urls = []
    foto_b64 = datos.get("foto_perfil_b64", "")
    if foto_b64:
        try:
            photo_url = upload_photo_to_repo(user_id, foto_b64)
            if photo_url:
                photo_urls = [photo_url]
        except Exception as photo_err:
            log.warning(f"No se pudo subir foto de perfil: {photo_err}")

    # Subir foto del blog inicial si existe
    blog_foto_url = ""
    blog_foto_b64 = datos.get("blog_inicial_foto_b64", "")
    if blog_foto_b64:
        try:
            from tools.github_tools import file_put
            import time as _time
            owner = get_owner()
            repo = get_repo_name(user_id)
            b64_content = blog_foto_b64
            file_put(owner, repo, "blog/assets/post-001.jpg", b64_content,
                     "Foto primera entrada de blog")
            blog_foto_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/blog/assets/post-001.jpg"
        except Exception as bf_err:
            log.warning(f"No se pudo subir foto de blog: {bf_err}")

    form_data = {
        "user_id": user_id,
        "name": datos["name"],
        "email": email,
        "bio": datos["bio"],
        "projects": datos["projects"],
        "links": datos["links"],
        "style_preferences": datos["style_preferences"],
        "photo_urls": photo_urls,
        "blog_inicial_titulo": datos.get("blog_inicial_titulo"),
        "blog_inicial_foto_url": blog_foto_url,
    }

    async def pipeline_y_notificar():
        async with _pipeline_lock:
            try:
                registrar_evento("pipeline_iniciado", user_id, datos["name"],
                                 f"Onboarding iniciado para {email}")
                await ejecutar_onboarding(form_data)
                guardar_usuario(chat_id, user_id, datos["name"], email)
                registrar_cambio(user_id, "onboarding", "sitio completo",
                                 f"Sitio creado para {datos['name']}")
                from tools.github_tools import get_user_site_url
                site_url = get_user_site_url(user_id)
                registrar_evento("pipeline_completado", user_id, datos["name"],
                                 "Sitio generado y publicado en GitHub Pages", url=site_url)

                # Avisar que el sitio está generado y el email llega en 10 min
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"✅ *¡Tu sitio fue generado!*\n\n"
                        f"👉 {site_url}\n\n"
                        f"_GitHub Pages está desplegando tu sitio. "
                        f"En 10 minutos te mando el email de confirmación "
                        f"y el sitio estará completamente online._\n\n"
                        f"💡 *Tip:* Para publicar entradas de blog usá /post"
                    ),
                    parse_mode="Markdown",
                )

                # Esperar 10 minutos a que GitHub Pages despliegue
                log.info(f"Esperando {EMAIL_DELAY_SECONDS}s para enviar email a {user_id}...")
                await asyncio.sleep(EMAIL_DELAY_SECONDS)

                # Enviar email y notificación final
                try:
                    from tools.email_tools import send_site_ready_email
                    send_site_ready_email(email, datos["name"], site_url)
                    registrar_evento("email_enviado", user_id, datos["name"],
                                     f"Email enviado a {email}", url=site_url)
                except Exception as mail_err:
                    log.warning(f"Email no enviado: {mail_err}")
                    registrar_evento("email_enviado", user_id, datos["name"],
                                     f"Error enviando email: {mail_err}", estado="error")

                await app.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"📬 *¡Tu sitio ya está online!*\n\n"
                        f"👉 {site_url}\n\n"
                        f"_Te enviamos el link también por email._\n\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"*Comandos para editar tu sitio:*\n\n"
                        f"✏️ /edit — Editar texto o estilo de cualquier parte\n"
                        f"➕ /nuevaseccion — Agregar una sección nueva\n"
                        f"🗑 /eliminar — Eliminar secciones o contenido\n"
                        f"✍️ /post — Publicar una entrada de blog\n"
                        f"🔄 /nuevo — Crear un sitio nuevo desde cero\n"
                        f"❌ /cancelar — Cancelar lo que estés haciendo\n\n"
                        f"━━━━━━━━━━━━━━━"
                    ),
                    parse_mode="Markdown",
                )

                # Generar y enviar QR estampilla
                try:
                    qr_bytes = generar_qr_estampilla(site_url, datos["name"])
                    await app.bot.send_photo(
                        chat_id=chat_id,
                        photo=qr_bytes,
                        caption=(
                            "✉ *Tu carta digital ya fue enviada al mundo.*\n\n"
                            "Guardá este QR para compartir tu sitio fácilmente 🚀"
                        ),
                        parse_mode="Markdown",
                    )
                except Exception as qr_err:
                    log.warning(f"QR no generado: {qr_err}")

            except Exception as e:
                log.error(f"Error en pipeline: {e}")
                registrar_evento("pipeline_error", user_id, datos["name"],
                                 str(e)[:200], estado="error")
                await app.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Hubo un error generando tu sitio. Ya estamos revisando.",
                )
            finally:
                # Pausa de 2 minutos antes de liberar el lock para el siguiente
                log.info(f"Cooldown de {PIPELINE_COOLDOWN_SECONDS}s antes del próximo pipeline...")
                await asyncio.sleep(PIPELINE_COOLDOWN_SECONDS)

    context.application.create_task(pipeline_y_notificar())
    return ConversationHandler.END


# ─────────────────────────────────────────────
# EDITAR / NUEVA SECCIÓN / ELIMINAR
# ─────────────────────────────────────────────

def _check_usuario(update):
    """Devuelve el usuario o None si no tiene sitio."""
    return obtener_usuario(update.effective_chat.id)


async def _no_tiene_sitio(update):
    await update.message.reply_text(
        "Primero necesitás crear tu sitio. Escribí /start 😊"
    )


async def _aplicar_edicion_html(app, chat_id, usuario, fn_edicion, prompt, tipo):
    """Helper: descarga HTML, aplica fn_edicion, sube resultado."""
    from tools.edit_tools import obtener_html
    from tools.github_tools import get_owner, get_repo_name, file_put, get_user_site_url

    user_id = usuario["user_id"]
    owner = get_owner()
    repo = get_repo_name(user_id)

    html_actual = obtener_html(owner, repo)
    if not html_actual:
        await app.bot.send_message(chat_id=chat_id,
            text="⚠️ No pude obtener tu sitio. Intentá de nuevo.")
        return

    html_nuevo = fn_edicion(html_actual, prompt)
    file_put(owner, repo, "index.html", html_nuevo, f"{tipo}: {prompt[:60]}")

    site_url = get_user_site_url(user_id)
    registrar_cambio(user_id, tipo, "sitio", prompt[:100])
    registrar_evento("blog_publicado", user_id, usuario["nombre"],
                     f"{tipo}: {prompt[:100]}")

    await app.bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ *¡Listo!*\n\n"
            f"👉 {site_url}\n\n"
            f"_Los cambios pueden tardar 1-2 minutos en verse._"
        ),
        parse_mode="Markdown",
    )


# /edit ──────────────────────────────────────

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    usuario = _check_usuario(update)
    if not usuario:
        await _no_tiene_sitio(update)
        return ConversationHandler.END
    context.user_data["edit_usuario"] = usuario
    await update.message.reply_text(
        "✏️ *¿Qué querés editar?*\n\n"
        "Describilo con tus palabras. Por ejemplo:\n"
        "• _Cambiá mi bio por: \"Diseñadora y fotógrafa en CABA\"_\n"
        "• _Actualizá mi email de contacto_\n"
        "• _Cambiá el color del título a azul marino_\n"
        "• _Renombrá la sección Proyectos como Trabajos_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return EDITAR_PROMPT


async def recibir_edit_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prompt = update.message.text.strip()
    usuario = context.user_data["edit_usuario"]
    chat_id = update.effective_chat.id
    app = context.application

    await update.message.reply_text("🔄 Aplicando cambios con IA...")

    async def _hacer():
        try:
            from tools.edit_tools import editar_html
            await _aplicar_edicion_html(app, chat_id, usuario, editar_html, prompt, "edit")
        except Exception as e:
            log.error(f"Error en /edit: {e}")
            await app.bot.send_message(chat_id=chat_id,
                text="⚠️ Error aplicando el cambio. Intentá de nuevo.")

    context.application.create_task(_hacer())
    return ConversationHandler.END


# /nuevaseccion ───────────────────────────────

async def nuevaseccion_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    usuario = _check_usuario(update)
    if not usuario:
        await _no_tiene_sitio(update)
        return ConversationHandler.END
    context.user_data["edit_usuario"] = usuario
    await update.message.reply_text(
        "➕ *¿Qué sección querés agregar?*\n\n"
        "Describí el contenido. Por ejemplo:\n"
        "• _Una sección de testimonios con 3 frases de clientes_\n"
        "• _Una galería de fotos de mis últimos trabajos_\n"
        "• _Una sección de servicios con precios_\n"
        "• _Un formulario de contacto_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NUEVA_SECCION_DESC


async def recibir_nuevaseccion_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prompt = update.message.text.strip()
    usuario = context.user_data["edit_usuario"]
    chat_id = update.effective_chat.id
    app = context.application

    await update.message.reply_text("🔄 Creando la nueva sección...")

    async def _hacer():
        try:
            from tools.edit_tools import agregar_seccion
            await _aplicar_edicion_html(app, chat_id, usuario, agregar_seccion, prompt, "nueva_seccion")
        except Exception as e:
            log.error(f"Error en /nuevaseccion: {e}")
            await app.bot.send_message(chat_id=chat_id,
                text="⚠️ Error creando la sección. Intentá de nuevo.")

    context.application.create_task(_hacer())
    return ConversationHandler.END


# /eliminar ──────────────────────────────────

async def eliminar_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    usuario = _check_usuario(update)
    if not usuario:
        await _no_tiene_sitio(update)
        return ConversationHandler.END
    context.user_data["edit_usuario"] = usuario
    await update.message.reply_text(
        "🗑 *¿Qué querés eliminar?*\n\n"
        "Describí qué sacar. Por ejemplo:\n"
        "• _La sección de proyectos_\n"
        "• _Mi foto de perfil_\n"
        "• _El proyecto que dice \"Amapola Studio\"_\n"
        "• _El link de Instagram_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ELIMINAR_DESC


async def recibir_eliminar_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prompt = update.message.text.strip()
    usuario = context.user_data["edit_usuario"]
    chat_id = update.effective_chat.id
    app = context.application

    await update.message.reply_text("🔄 Eliminando el contenido...")

    async def _hacer():
        try:
            from tools.edit_tools import eliminar_contenido
            await _aplicar_edicion_html(app, chat_id, usuario, eliminar_contenido, prompt, "eliminar")
        except Exception as e:
            log.error(f"Error en /eliminar: {e}")
            await app.bot.send_message(chat_id=chat_id,
                text="⚠️ Error eliminando el contenido. Intentá de nuevo.")

    context.application.create_task(_hacer())
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

    context.application.create_task(generar_blog())
    return ConversationHandler.END


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera y envía el panel interno. Solo para el admin."""
    ADMIN_CHAT_ID = 2083458641  # chat_id de Saira
    if update.effective_chat.id != ADMIN_CHAT_ID:
        await update.message.reply_text("Este comando es solo para el administrador.")
        return
    try:
        html = generar_dashboard()
        html_bytes = html.encode("utf-8") if isinstance(html, str) else html
        await update.message.reply_document(
            document=html_bytes,
            filename="panel-ilpostino.html",
            caption=f"📊 Panel actualizado — {len(cargar_usuarios())} usuarios",
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error generando panel: {e}")


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
            BLOG_PREGUNTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, blog_pregunta)],
            BLOG_TITULO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, blog_titulo)],
            BLOG_FOTO_ONBOARDING: [
                MessageHandler(filters.PHOTO, blog_foto_onboarding),
                CommandHandler("sinFotoBlog", sin_foto_blog_onboarding),
            ],
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

    # Conversación de edición
    editar = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_start)],
        states={
            EDITAR_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_edit_prompt)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    # Conversación nueva sección
    nueva_seccion = ConversationHandler(
        entry_points=[CommandHandler("nuevaseccion", nuevaseccion_start)],
        states={
            NUEVA_SECCION_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nuevaseccion_desc)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    # Conversación eliminar
    eliminar = ConversationHandler(
        entry_points=[CommandHandler("eliminar", eliminar_start)],
        states={
            ELIMINAR_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_eliminar_desc)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(onboarding)
    app.add_handler(blog)
    app.add_handler(editar)
    app.add_handler(nueva_seccion)
    app.add_handler(eliminar)
    app.add_handler(CommandHandler("panel", panel))
    return app


if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("❌ Falta TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    webhook_url = os.environ.get("WEBHOOK_URL", "")
    port = int(os.environ.get("PORT", "8080"))

    bot = crear_bot(token)

    if webhook_url:
        print(f"🤖 ilPostino Bot en modo webhook → {webhook_url}")
        bot.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )
    else:
        # En Cloud Run sin WEBHOOK_URL: polling + health check HTTP en background
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
            def log_message(self, *args):
                pass  # silenciar logs

        def _health_server():
            HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

        threading.Thread(target=_health_server, daemon=True).start()
        print(f"🤖 ilPostino Bot corriendo en @ilpostino_bot (polling + health:{port})")
        bot.run_polling(drop_pending_updates=True)
