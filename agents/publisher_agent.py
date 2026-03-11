from google.adk.agents import LlmAgent
from tools.github_tools import publish_site_to_github, publish_welcome_blog_post
from tools.file_tools import save_site_to_disk

publisher_agent = LlmAgent(
    name="publisher_agent",
    model="gemini-3.1-flash-lite-preview",
    description="Crea el repo, activa GitHub Pages, publica el sitio, el primer post real y el README.",
    instruction="""
Publicá el sitio del usuario en su repositorio de GitHub Pages.

HTML a publicar:
{html_output}

Datos del usuario (brief):
{brief}

Datos del formulario original:
{raw_form_data}

## PASO 1: Publicar index.html

Llamá a publish_site_to_github con:
- html_content: el HTML completo de {html_output}
- user_id: el campo user_id del brief
- nombre_usuario: el campo full_name del brief
- headline: el campo headline del brief
- bio: el primer elemento de bio_paragraphs del brief

## PASO 2: Publicar el primer post del blog

Llamá a publish_welcome_blog_post con:
- user_id: el campo user_id del brief
- nombre_usuario: el campo full_name del brief
- titulo: el campo blog_inicial_titulo de raw_form_data (puede ser vacío o None)
- foto_url: el campo blog_inicial_foto_url de raw_form_data (puede ser vacío)

Si blog_inicial_titulo está vacío o None, la función crea automáticamente
un post de bienvenida "Hola, soy [nombre]".

## PASO 3: Confirmar

Devolvé la URL pública del sitio.
""",
    tools=[publish_site_to_github, publish_welcome_blog_post, save_site_to_disk],
)
