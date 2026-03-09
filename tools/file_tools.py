from pathlib import Path

SITES_DIR = Path("/home/saira/amapola/ilpostino/sites")


def render_html_template(html_content: str) -> dict:
    """Recibe el HTML generado y lo retorna para que el publisher lo guarde.

    Args:
        html_content: HTML completo del sitio personal.

    Returns:
        dict con status y cantidad de caracteres.
    """
    return {"status": "ready", "html": html_content, "chars": len(html_content)}


def save_site_to_disk(html_content: str, user_id: str, filename: str = "index.html") -> dict:
    """Guarda el HTML en el directorio del usuario.

    Args:
        html_content: HTML completo a guardar.
        user_id: Identificador del usuario para nombrar la carpeta.
        filename: Nombre del archivo, por defecto index.html.

    Returns:
        dict con path y status.
    """
    user_dir = SITES_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    target = user_dir / filename
    target.write_text(html_content, encoding="utf-8")
    return {"status": "saved", "path": str(target)}
