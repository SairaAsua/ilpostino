from google.adk.agents import SequentialAgent
from agents.brief_agent import brief_agent
from agents.content_agent import content_agent
from agents.design_agent import design_agent
from agents.web_builder_agent import web_builder_agent
from agents.publisher_agent import publisher_agent

# El email se envía desde telegram_bot.py con un delay de 10 minutos
# para asegurarse de que GitHub Pages ya esté desplegado.
onboarding_pipeline = SequentialAgent(
    name="onboarding_pipeline",
    description="Pipeline completo: datos del formulario -> sitio publicado en GitHub Pages.",
    sub_agents=[
        brief_agent,
        content_agent,
        design_agent,
        web_builder_agent,
        publisher_agent,
    ],
)
