from google.adk.agents import LlmAgent
from tools.email_tools import send_site_ready_email

email_agent = LlmAgent(
    name="email_agent",
    model="gemini-3.1-flash-lite-preview",
    description="Envía email de confirmación al cliente con el link a su sitio publicado.",
    instruction="""
El sitio del cliente acaba de ser publicado. Enviá el email de confirmación.

Datos del cliente:
- Nombre: {brief[full_name]}
- Email: busca el email en {raw_form_data}

URL del sitio: buscá la public_url en el resultado del publisher, o construila como:
https://ilPostinob0t.github.io/sites/{brief[user_id]}/

Llamá a send_site_ready_email con:
- recipient_email: el email del cliente
- recipient_name: {brief[full_name]}
- site_url: la URL pública del sitio

Confirmá que el email fue enviado.
""",
    tools=[send_site_ready_email],
)
