from google.adk.agents import LlmAgent
from schemas.brief import StructuredBrief

brief_agent = LlmAgent(
    name="brief_agent",
    model="gemini-3.1-flash-lite-preview",
    description="Analiza los datos del formulario y produce un brief estructurado.",
    instruction="""
Recibiste los datos crudos del formulario de onboarding:
{raw_form_data}

Analiza toda esa información y produce un brief estructurado con:
- full_name: nombre completo del usuario
- headline: una frase potente de una línea que define quién es profesionalmente
- bio_paragraphs: 2-3 párrafos de bio pulidos, humanos y específicos
- projects: lista de proyectos [{name, description, url, status}]
- social_links: lista de redes [{platform, url}]
- tone: uno de "professional", "creative", "minimal" según las preferencias de estilo
- style_keywords: 3-5 palabras clave visuales
- photo_urls: lista de URLs de fotos si existen
- user_id: el mismo user_id del formulario
Devuelve SOLO JSON válido que coincida con el esquema StructuredBrief.
El campo initial_blog_posts debe ser una lista vacía [].
""",
    output_schema=StructuredBrief,
    output_key="brief",
)
