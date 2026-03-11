"""
Edición del sitio web de un usuario vía prompts de IA.
Usa Gemini directamente para editar, agregar o eliminar contenido del HTML.
"""

import base64
import os

import requests
from google import genai

_MODEL = "gemini-2.0-flash-lite"


def _headers() -> dict:
    return {
        "Authorization": f"token {os.environ.get('GITHUB_TOKEN', '')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def obtener_html(owner: str, repo: str, path: str = "index.html") -> str | None:
    """Descarga el HTML actual del repo de GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=_headers(), timeout=15)
    if r.status_code == 200:
        return base64.b64decode(r.json()["content"]).decode("utf-8")
    return None


def _limpiar_html(texto: str) -> str:
    """Elimina markdown code fences si Gemini los incluyó."""
    t = texto.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        t = "\n".join(lines[start:end]).strip()
    return t


def _gemini(prompt: str) -> str:
    client = genai.Client()
    r = client.models.generate_content(model=_MODEL, contents=prompt)
    return _limpiar_html(r.text)


def editar_html(html: str, instruccion: str) -> str:
    """Edita el HTML según la instrucción del usuario."""
    return _gemini(f"""Sos un editor experto en HTML y CSS para sitios web personales.

HTML actual del sitio:
{html}

Cambio solicitado por el usuario: {instruccion}

Reglas:
- Aplicá EXACTAMENTE lo que pidió, sin inventar cambios extra
- Mantené el diseño, estructura y estilo general del sitio
- Devolvé SOLO el HTML completo y válido, sin explicaciones ni markdown
- El HTML debe comenzar con <!DOCTYPE html>""")


def agregar_seccion(html: str, descripcion: str) -> str:
    """Agrega una nueva sección al HTML manteniendo el estilo del sitio."""
    return _gemini(f"""Sos un desarrollador web experto en sitios personales estáticos.

HTML actual del sitio:
{html}

El usuario quiere agregar esta nueva sección: {descripcion}

Reglas:
- Creá la sección manteniendo exactamente el mismo estilo visual (colores, fuentes, espaciado, bordes)
- Insertala en el lugar más lógico del documento
- Si hay barra de navegación, agregá el link correspondiente
- Devolvé SOLO el HTML completo y válido, sin explicaciones ni markdown
- El HTML debe comenzar con <!DOCTYPE html>""")


def eliminar_contenido(html: str, descripcion: str) -> str:
    """Elimina contenido del HTML según la descripción del usuario."""
    return _gemini(f"""Sos un editor de HTML experto en sitios web personales.

HTML actual del sitio:
{html}

El usuario quiere eliminar: {descripcion}

Reglas:
- Eliminá SOLO lo que pidió, sin tocar nada más
- Si hay un link de navegación para lo eliminado, removelo también
- Mantené el HTML válido y bien estructurado
- Devolvé SOLO el HTML completo y válido, sin explicaciones ni markdown
- El HTML debe comenzar con <!DOCTYPE html>""")
