"""
Herramientas para publicar sitios en GitHub Pages via API.
Cada usuario tiene su propio repositorio: jb-{user_id}
URL resultante: https://{owner}.github.io/jb-{user_id}/
"""

import base64
import os
import time

import requests

GITHUB_API = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"token {os.environ.get('GITHUB_TOKEN', '')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_owner() -> str:
    return os.environ.get("GITHUB_OWNER", "anyprinter001-source")


def get_repo_name(user_id: str) -> str:
    """Nombre del repo para cada usuario: jb-{user_id}"""
    return f"jb-{user_id.lower().replace('_', '-')}"


def get_user_site_url(user_id: str) -> str:
    return f"https://{get_owner()}.github.io/{get_repo_name(user_id)}/"


def file_put(owner: str, repo: str, path: str, content: str, message: str) -> bool:
    """Crea o actualiza un archivo en un repo de GitHub."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    check = requests.get(url, headers=_headers())
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
    }
    if check.status_code == 200:
        payload["sha"] = check.json()["sha"]
    r = requests.put(url, headers=_headers(), json=payload)
    return r.status_code in (200, 201)


def file_get_json(owner: str, repo: str, path: str) -> list:
    """Lee un JSON de GitHub, devuelve [] si no existe."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=_headers())
    if r.status_code != 200:
        return []
    content = base64.b64decode(r.json()["content"]).decode()
    import json
    return json.loads(content)


def _crear_repo_usuario(owner: str, repo: str, nombre_usuario: str) -> bool:
    """Crea el repo y activa GitHub Pages."""
    check = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=_headers())
    if check.status_code == 200:
        return True

    create = requests.post(
        f"{GITHUB_API}/user/repos",
        headers=_headers(),
        json={
            "name": repo,
            "description": f"Sitio personal de {nombre_usuario} — ilPostino",
            "private": False,
            "auto_init": True,
        },
    )
    if create.status_code != 201:
        return False

    time.sleep(2)

    requests.post(
        f"{GITHUB_API}/repos/{owner}/{repo}/pages",
        headers=_headers(),
        json={"source": {"branch": "main", "path": "/"}},
    )
    return True


def _generar_readme(nombre: str, headline: str, bio: str, site_url: str, repo: str) -> str:
    """Genera un README.md personalizado para el repo del usuario."""
    bio_corta = bio[:280] + "..." if len(bio) > 280 else bio
    return f"""# {nombre}

> {headline}

{bio_corta}

---

🌐 **Sitio web personal:** [{site_url}]({site_url})

📚 **Blog:** [{site_url}blog/]({site_url}blog/)

---

*Este sitio fue creado con [ilPostino](https://github.com/anyprinter001-source) — marca personal viva, actualizable desde Telegram.*
"""


def publish_site_to_github(
    html_content: str,
    user_id: str,
    nombre_usuario: str = "",
    headline: str = "",
    bio: str = "",
) -> dict:
    """Crea el repo del usuario, activa GitHub Pages, publica el sitio y el README.

    Args:
        html_content: HTML completo del sitio personal.
        user_id: Identificador del usuario.
        nombre_usuario: Nombre real para la descripción del repo y el README.
        headline: Frase de una línea del usuario para el README.
        bio: Bio del usuario para el README.

    Returns:
        dict con public_url y status.
    """
    owner = get_owner()
    repo = get_repo_name(user_id)

    ok = _crear_repo_usuario(owner, repo, nombre_usuario or user_id)
    if not ok:
        return {"status": "error", "detail": f"No se pudo crear el repo {repo}"}

    public_url = get_user_site_url(user_id)

    # Publicar index.html
    ok = file_put(owner, repo, "index.html", html_content,
                  f"Publicar sitio de {nombre_usuario or user_id}")
    if not ok:
        return {"status": "error", "detail": "No se pudo subir index.html"}

    # Actualizar README.md personalizado
    readme = _generar_readme(
        nombre=nombre_usuario or user_id,
        headline=headline or f"Sitio personal de {nombre_usuario or user_id}",
        bio=bio or "",
        site_url=public_url,
        repo=repo,
    )
    file_put(owner, repo, "README.md", readme, f"Actualizar README de {nombre_usuario or user_id}")

    return {
        "status": "published",
        "public_url": public_url,
        "repo": repo,
        "user_id": user_id,
    }


def publish_file_to_user_repo(user_id: str, path: str, content: str, message: str) -> str:
    """Publica cualquier archivo en el repo del usuario."""
    owner = get_owner()
    repo = get_repo_name(user_id)
    file_put(owner, repo, path, content, message)
    return f"https://{owner}.github.io/{repo}/{path}"
