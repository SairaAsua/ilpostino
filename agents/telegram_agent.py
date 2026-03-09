from google.adk.agents import LlmAgent
from tools.telegram_tools import classify_update

telegram_agent = LlmAgent(
    name="telegram_agent",
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
