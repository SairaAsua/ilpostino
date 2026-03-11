# ilPostino — Producto

## Qué es ilPostino

ilPostino es un sistema de agentes de IA que convierte una conversación de Telegram en un sitio web personal publicado y vivo. El usuario responde 6 preguntas, confirma sus datos, y en menos de 60 segundos tiene su propio dominio en GitHub Pages con diseño personalizado, bio pulida, proyectos y blog. Después lo actualiza mandando fotos y texto desde el mismo chat.

**No requiere código. No requiere diseñador. No requiere hosting.**

---

## Propuesta de valor

| Para quién | Qué resuelve |
|------------|--------------|
| Profesional independiente, freelancer, consultora | Tener presencia web sin saber diseño ni programación |
| Creativa, emprendedora, artista | Publicar novedades y proyectos en segundos desde el celular |
| Quien tiene LinkedIn pero no web propia | Convertir su perfil en una web de marca personal real |

**Diferencia concreta frente a Linktree, Notion pública o Carrd:**
- El sitio es tuyo: repo propio en GitHub, URL propia, código descargable
- La IA genera el copy profesional a partir de lo que contás, no lo que escribís
- Se actualiza desde Telegram, no desde un panel de administración
- Incluye blog publicado automáticamente, con fotos, desde el celular

---

## Flujo de experiencia del cliente — Sitio web (/start)

```
1. El cliente escribe /start en @ilpostino_bot
   └─ Si ya tiene sitio: recibe el link directo + instrucciones para /post
   └─ Si es nuevo: comienza onboarding

2. El bot hace 6 preguntas, una por vez:
   ├─ "¿Cuál es tu nombre completo?"
   ├─ "¿Cuál es tu email?"  ← único campo técnico
   ├─ "¿Quién sos y qué hacés?"  ← texto libre, el tono que quieran
   ├─ "¿Cuáles son tus proyectos o trabajos principales?"  ← uno por línea
   ├─ "¿Tus links y redes sociales?"  ← LinkedIn, Instagram, etc.
   └─ "¿Cómo querés que se vea tu sitio?"
      [Moderno y minimalista] [Editorial y elegante]
      [Creativo y colorido]   [Profesional y sobrio]

3. El bot pide una foto de perfil
   └─ Si no tiene: /sinFotoPerfil y sigue igual

4. El bot muestra un resumen y pregunta "¿Todo bien?"
   ├─ ✅ Sí, generar mi sitio → dispara el pipeline
   └─ ❌ Empezar de nuevo → vuelve al paso 2

5. El bot confirma que está generando
   "Nuestros agentes de IA están trabajando. Te mando el link en ~60 segundos ✨"

6. Los agentes trabajan en cadena:
   brief → copy → diseño → HTML → GitHub Pages → email

7. El cliente recibe en Telegram:
   "🎉 ¡Tu sitio está listo!
    👉 https://anyprinter001-source.github.io/jb-{user_id}/
    También te enviamos un email con el link.
    💡 Tip: Para publicar novedades usá /post"

8. El cliente recibe un email HTML de confirmación con botón "Ver mi sitio web →"
```

**Tiempo total desde /start hasta sitio publicado: 2-3 minutos.**

---

## Flujo de blog post (/post)

```
1. El cliente escribe /post
   └─ Si no tiene sitio aún: "Primero necesitás crear tu sitio. Escribí /start"

2. El bot pide una foto
   └─ Si no quiere: /sinFoto

3. El bot pide el texto de la entrada
   "Puede ser un título + descripción, una novedad, un proyecto nuevo, lo que quieras."

4. El bot confirma que está procesando
   "🔄 Generando tu entrada de blog..."

5. El sistema:
   ├─ Genera el HTML del post con imagen embebida (base64) y CSS inline
   ├─ Sube blog/{fecha-hora}.html al repo del usuario en GitHub
   ├─ Actualiza blog/posts.json con los metadatos del post
   └─ Regenera blog/index.html con todas las entradas ordenadas por fecha

6. El cliente recibe en Telegram:
   "✅ ¡Entrada publicada!
    📄 Este post: https://.../blog/20260309-143022.html
    📚 Índice del blog: https://.../blog/
    Compartí donde quieras 🚀"
```

**Tiempo total desde /post hasta entrada publicada en la web: menos de 30 segundos.**

---

## Qué genera el sistema por usuario

Cada usuario genera una identidad digital completa y autónoma:

### Repositorio propio en GitHub
- **Nombre:** `jb-{user_id}` (ej: `jb-anyscigliano`)
- **Visibilidad:** público
- **GitHub Pages:** activado automáticamente desde `main` branch

### Archivos creados en el repo

| Archivo | Descripción |
|---------|-------------|
| `index.html` | Sitio personal completo: hero, bio, proyectos, contacto, redes. CSS inline con design tokens personalizados. Sin dependencias externas. |
| `README.md` | README del repo con nombre, headline, bio, links al sitio y al blog. Generado automáticamente con los datos del usuario. |
| `blog/index.html` | Índice del blog con todas las entradas ordenadas por fecha. Se regenera en cada nuevo post. |
| `blog/{timestamp}.html` | Entrada individual de blog con foto (si se envió), título, fecha, texto y footer con link al sitio principal. |
| `blog/posts.json` | Índice de posts en JSON. Persiste el historial del blog aunque se regenere el `index.html`. |

### Email de confirmación

Email HTML enviado desde Gmail con:
- Saludo personalizado con el nombre del cliente
- Botón "Ver mi sitio web →" apuntando a la URL de GitHub Pages
- URL del sitio en texto plano (copiable)
- Instrucciones para actualizar desde Telegram
- Diseño editorial coherente con la paleta del sistema (fondo crema, acento terracota)

### Mapeo persistente en el sistema

El archivo `data/usuarios.json` registra el mapeo `chat_id → {user_id, nombre, email}`, lo que permite que el bot reconozca al usuario en futuras sesiones sin volver a pedir datos.

---

## Stack tecnológico

| Capa | Tecnología | Rol |
|------|-----------|-----|
| Agentes IA | Google ADK (Agent Development Kit) | Framework de orquestación multi-agente |
| Modelos | Gemini 3.1 Flash Lite Preview | Todos los LlmAgent del sistema |
| Bot de Telegram | python-telegram-bot | Conversación, onboarding, blog posts |
| Servidor HTTP | aiohttp | Webhook para Google Forms |
| Publicación | GitHub API v3 + GitHub Pages | Hosting estático gratuito, repo por usuario |
| Email | SMTP Gmail (smtplib) | Email de confirmación HTML |
| Schemas | Pydantic v2 | Validación estructurada de brief y design tokens |
| Runtime | Python 3.12, asyncio | Todo el sistema es async |
| Túnel local | ngrok | Expone el servidor local para Google Apps Script |
| Almacenamiento | Disco local + GitHub | Backup en `sites/` + fuente de verdad en GitHub |

---

## Próximos pasos sugeridos

### Funcionalidad inmediata

1. **Correr bot y servidor en paralelo** — Hoy son dos procesos separados. Unificar en un único comando con `asyncio.gather()` o `supervisord`.

2. **Persistencia de sesión con base de datos** — `usuarios.json` escala mal. Migrar a SQLite o un JSON por usuario en el repo para tener historial de posts y datos del brief.

3. **Edición del sitio desde Telegram** — El update_pipeline guarda en disco pero no actualiza el `index.html` en GitHub. Conectar `publisher_update` con `publish_file_to_user_repo`.

4. **Foto de perfil en el sitio** — La foto se recibe como base64 y se pasa al pipeline, pero el `web_builder_agent` la incluye solo si `brief.photo_urls` no está vacío. Verificar que el base64 llegue correctamente al HTML final.

### Producto

5. **Dominio personalizado** — GitHub Pages soporta dominios propios via `CNAME`. Agregar flujo para que el usuario configure su propio dominio (`/dominio midominio.com`).

6. **Múltiples secciones actualizables** — Hoy el update_pipeline clasifica el mensaje pero no edita el `index.html` principal. Implementar edición quirúrgica de secciones (proyectos, bio, links).

7. **Previsualización antes de publicar** — En el flujo de blog, mostrar el título inferido y pedir confirmación antes de publicar al repo.

8. **Analytics básico** — Agregar Plausible o un pixel de conteo en el `index.html` generado para que el usuario vea visitas desde Telegram.

### Infraestructura

9. **Deploy en servidor fijo** — Reemplazar ngrok por un servidor con IP pública (VPS, Railway, Fly.io). El webhook de Google Apps Script necesita una URL estable.

10. **Variables de entorno seguras** — Mover las credenciales del `.env` a un gestor de secretos (Doppler, 1Password CLI, o variables de entorno del hosting) para no tenerlas en disco en texto plano.
