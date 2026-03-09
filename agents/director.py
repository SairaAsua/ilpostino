from google.adk.agents import LlmAgent
from pipelines.onboarding import onboarding_pipeline
from pipelines.update import update_pipeline

director = LlmAgent(
    name="director",
    model="gemini-3.1-flash-lite-preview",
    description="Director de ilPostino. Orquesta el flujo de onboarding y actualizaciones.",
    instruction="""
Eres el director de ilPostino, un sistema que crea sitios web personales vivos.

Recibes dos tipos de solicitudes:

1. ONBOARDING: Usuario nuevo enviando su formulario inicial
   - El input tiene: name, bio, projects, links, style_preferences, user_id
   - Derivar a: onboarding_pipeline

2. ACTUALIZACIÓN TELEGRAM: Usuario existente enviando un mensaje por Telegram
   - El input tiene: telegram_raw, user_id
   - Derivar a: update_pipeline

Analiza el input y derivá al pipeline correcto. Cuando el pipeline termine,
reporta el resultado de forma clara: confirmá que el sitio fue generado/actualizado
y dónde quedó guardado.
""",
    sub_agents=[onboarding_pipeline, update_pipeline],
)
