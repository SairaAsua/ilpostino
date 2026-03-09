from google.adk.agents import LlmAgent
from tools.file_tools import render_html_template

web_builder_agent = LlmAgent(
    name="web_builder_agent",
    model="gemini-3.1-flash-lite-preview",
    description="Genera el sitio HTML/CSS completo y lo pasa al publisher.",
    instruction="""
Eres un desarrollador web experto generando un sitio personal estático y hermoso.

Copy del sitio:
{web_copy}

Tokens de diseño:
{design_tokens}

Datos del usuario:
{brief}

Llama a render_html_template con el HTML completo. Requisitos:
- Todo el CSS inline usando CSS custom properties con los design tokens
- HTML5 semántico: header, main, section, footer
- Diseño responsive mobile-first con flexbox/grid
- Sin dependencias de JavaScript externas
- Meta tags Open Graph
- Secciones: hero, sobre mí, proyectos, contacto, redes sociales
- Si hay photo_urls, incluir la primera como foto de perfil
- Diseño moderno, limpio y profesional

El resultado debe ser un sitio web completo y funcional en un solo archivo HTML.
""",
    tools=[render_html_template],
    output_key="html_output",
)
