from google.adk.agents import LlmAgent, SequentialAgent
from tools.file_tools import render_html_template, save_site_to_disk
from tools.telegram_tools import classify_update
from agents.content_agent import content_agent_update

telegram_agent = LlmAgent(
    name="telegram_agent_update",
    model="gemini-3.1-flash-lite-preview",
    description="Parsea mensajes de Telegram y los convierte en actualizaciones estructuradas.",
    instruction="""
Recibiste un mensaje de Telegram del dueño del sitio:
{telegram_raw}

1. Llama a classify_update para determinar el tipo de actualización
2. Según la clasificación, estructura la actualización como JSON:
   - "blog_post": {title, body, date}
   - "project_update": {project_name, update_text}
   - "bio_update": {new_bio_text}
   - "news": {headline, body}

Devuelve SOLO JSON con las claves: update_type, content, target_section.
""",
    tools=[classify_update],
    output_key="structured_update",
)

web_builder_update = LlmAgent(
    name="web_builder_update",
    model="gemini-3.1-flash-lite-preview",
    description="Genera HTML actualizado con el nuevo contenido.",
    instruction="""
Genera el bloque HTML para insertar en el sitio del usuario.

Contenido actualizado:
{update_copy}

Genera un bloque HTML completo y autocontenido (con su CSS inline) listo para publicar.
Llama a render_html_template con el HTML generado.
""",
    tools=[render_html_template],
    output_key="html_output",
)

publisher_update = LlmAgent(
    name="publisher_update",
    model="gemini-3.1-flash-lite-preview",
    description="Guarda la actualización en disco.",
    instruction="""
Guarda el contenido actualizado en disco para el usuario {user_id}.

HTML a guardar:
{html_output}

Llama a save_site_to_disk con:
- html_content: el HTML de arriba
- user_id: {user_id}
- filename: "update_latest.html"

Confirma el path donde quedó guardado.
""",
    tools=[save_site_to_disk],
)

update_pipeline = SequentialAgent(
    name="update_pipeline",
    description="Mensaje de Telegram -> sección del sitio actualizada.",
    sub_agents=[
        telegram_agent,
        content_agent_update,
        web_builder_update,
        publisher_update,
    ],
)
