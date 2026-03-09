from google.adk.agents import SequentialAgent
from agents.brief_agent import brief_agent
from agents.content_agent import content_agent
from agents.design_agent import design_agent
from agents.web_builder_agent import web_builder_agent
from agents.publisher_agent import publisher_agent
from agents.email_agent import email_agent

onboarding_pipeline = SequentialAgent(
    name="onboarding_pipeline",
    description="Pipeline completo: datos del formulario -> sitio publicado -> email al cliente.",
    sub_agents=[
        brief_agent,
        content_agent,
        design_agent,
        web_builder_agent,
        publisher_agent,
        email_agent,
    ],
)
