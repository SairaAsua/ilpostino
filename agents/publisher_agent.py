from google.adk.agents import LlmAgent
from tools.github_tools import publish_site_to_github
from tools.file_tools import save_site_to_disk

publisher_agent = LlmAgent(
    name="publisher_agent",
    model="gemini-3.1-flash-lite-preview",
    description="Crea el repo del usuario, activa GitHub Pages, publica el sitio y el README personalizado.",
    instruction="""
Publicá el sitio del usuario en su propio repositorio de GitHub Pages.

HTML a publicar:
{html_output}

Datos del usuario:
- user_id: {brief[user_id]}
- nombre: {brief[full_name]}
- headline: {brief[headline]}
- bio (primera línea): {brief[bio_paragraphs]}

Llamá a publish_site_to_github con:
- html_content: el HTML completo de arriba
- user_id: {brief[user_id]}
- nombre_usuario: {brief[full_name]}
- headline: {brief[headline]}
- bio: el primer párrafo de {brief[bio_paragraphs]}

Si falla, usá save_site_to_disk como backup:
- html_content: el HTML
- user_id: {brief[user_id]}
- filename: "index.html"

Confirmá la URL pública y el nombre del repo creado.
""",
    tools=[publish_site_to_github, save_site_to_disk],
)
