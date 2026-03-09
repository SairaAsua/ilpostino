from google.adk.agents import LlmAgent
from schemas.brief import DesignTokens

design_agent = LlmAgent(
    name="design_agent",
    model="gemini-3.1-flash-lite-preview",
    description="Selecciona paleta de colores, tipografía y layout según las preferencias del usuario.",
    instruction="""
Eres un diseñador web eligiendo tokens de diseño para un sitio personal.

Preferencias y tono del usuario:
- Keywords de estilo: {brief[style_keywords]}
- Tono: {brief[tone]}
- Descripción de preferencias: {brief[style_preferences]}

Selecciona tokens de diseño. Reglas obligatorias:
- El contraste debe cumplir WCAG AA (mínimo 4.5:1 para texto)
- tono "professional" -> fuentes: Inter o DM Sans, paleta sobria
- tono "creative" -> fuentes: Plus Jakarta Sans, acento vibrante
- tono "minimal" -> fuentes: system-ui, monocromático con un único acento
- layout "single-column" para minimal, "portfolio-grid" para creative, "two-column" para professional

Usa colores en formato hex (#RRGGBB).

Devuelve SOLO JSON válido que coincida con el esquema DesignTokens.
""",
    output_schema=DesignTokens,
    output_key="design_tokens",
)
