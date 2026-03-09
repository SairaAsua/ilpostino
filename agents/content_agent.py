from google.adk.agents import LlmAgent

content_agent = LlmAgent(
    name="content_agent",
    model="gemini-3.1-flash-lite-preview",
    description="Genera el copy del sitio web a partir del brief estructurado.",
    instruction="""
Eres un copywriter profesional especializado en sitios web personales.

Brief del usuario:
{brief}

Genera copy pulido para el sitio web incluyendo:
- hero: {headline, subheadline, cta_text}
- about: 3 párrafos que suenen humanos y específicos
- projects: lista con {name, short_description, highlight} para cada proyecto
- tagline: frase corta para el footer

El tono debe ser: {brief[tone]}

Devuelve SOLO JSON válido con las claves: hero, about (lista de strings), projects (lista), tagline.
""",
    output_key="web_copy",
)

content_agent_update = LlmAgent(
    name="content_agent_update",
    model="gemini-3.1-flash-lite-preview",
    description="Convierte una actualización de Telegram en contenido pulido para el sitio.",
    instruction="""
Eres un copywriter que convierte mensajes informales de Telegram en contenido web pulido.

Actualización recibida:
{structured_update}

Genera el contenido formateado para insertar en el sitio:
- Si es blog_post: title, body (markdown), excerpt
- Si es project_update: project_name, update_text, date
- Si es bio_update: new_bio_text
- Si es news: headline, body, date

Devuelve SOLO JSON con el contenido listo para publicar.
""",
    output_key="update_copy",
)
