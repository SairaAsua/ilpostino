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
    return os.environ.get("GITHUB_OWNER", "ilPostinob0t")


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

    # Esperar a que el repo esté listo antes de activar Pages
    for _ in range(6):
        time.sleep(5)
        check2 = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=_headers())
        if check2.status_code == 200:
            break

    pages_r = requests.post(
        f"{GITHUB_API}/repos/{owner}/{repo}/pages",
        headers=_headers(),
        json={"source": {"branch": "main", "path": "/"}},
    )
    # Si ya existe Pages (409) está bien también
    return pages_r.status_code in (201, 409)


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

*Este sitio fue creado con [ilPostino](https://github.com/ilPostinob0t) — marca personal viva, actualizable desde Telegram.*
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


def fetch_github_profile(github_url: str) -> dict:
    """Obtiene el perfil público de un usuario de GitHub dado su URL de perfil.

    Args:
        github_url: URL del perfil, e.g. https://github.com/sairaasua

    Returns:
        dict con avatar_url, name, bio, followers, public_repos, url
    """
    try:
        username = github_url.rstrip("/").split("/")[-1]
        r = requests.get(f"https://api.github.com/users/{username}",
                         headers={"Accept": "application/vnd.github+json"}, timeout=5)
        if r.status_code == 200:
            d = r.json()
            return {
                "username": username,
                "name": d.get("name") or username,
                "bio": d.get("bio") or "",
                "avatar_url": d.get("avatar_url") or "",
                "followers": d.get("followers", 0),
                "public_repos": d.get("public_repos", 0),
                "url": github_url,
            }
    except Exception:
        pass
    return {"username": github_url.rstrip("/").split("/")[-1], "url": github_url}


def upload_photo_to_repo(user_id: str, photo_b64: str) -> str:
    """Sube la foto de perfil al repo del usuario y devuelve la URL raw."""
    owner = get_owner()
    repo = get_repo_name(user_id)
    path = "assets/profile.jpg"
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    check = requests.get(url, headers=_headers())
    payload = {"message": "Foto de perfil", "content": photo_b64}
    if check.status_code == 200:
        payload["sha"] = check.json()["sha"]
    r = requests.put(url, headers=_headers(), json=payload)
    if r.status_code in (200, 201):
        return f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
    return ""


def publish_file_to_user_repo(user_id: str, path: str, content: str, message: str) -> str:
    """Publica cualquier archivo en el repo del usuario."""
    owner = get_owner()
    repo = get_repo_name(user_id)
    file_put(owner, repo, path, content, message)
    return f"https://{owner}.github.io/{repo}/{path}"


def publish_welcome_blog_post(user_id: str, nombre_usuario: str,
                               titulo: str = "", foto_url: str = "") -> dict:
    """Publica el primer post del blog: real si hay título, bienvenida si no.

    Args:
        user_id: ID del usuario.
        nombre_usuario: Nombre real del usuario.
        titulo: Título elegido por el usuario. Si vacío, crea post de bienvenida.
        foto_url: URL de la foto (ya subida a GitHub). Puede ser vacía.

    Returns:
        dict con status y URLs.
    """
    from datetime import datetime as _dt
    owner = get_owner()
    repo = get_repo_name(user_id)
    site_url = get_user_site_url(user_id)
    fecha = _dt.now().strftime("%d de %B, %Y")
    nombre_corto = nombre_usuario.split()[0] if nombre_usuario else usuario

    if titulo:
        post_titulo = titulo
        post_body = (
            f"<p>Esta es mi primera entrada en mi blog personal. "
            f"Bienvenido/a a mi espacio digital.</p>"
            f"<p>Desde acá voy a ir compartiendo novedades, proyectos y pensamientos. "
            f"Seguí leyendo para saber más sobre lo que hago.</p>"
        )
        post_excerpt = f"Primera entrada de {nombre_usuario}."
    else:
        post_titulo = f"Hola, soy {nombre_corto} 👋"
        post_body = (
            f"<p>Bienvenido/a a mi sitio personal, creado con "
            f"<a href='https://ilPostinob0t.github.io'>Il Postino Bot</a>.</p>"
            f"<p>Acá vas a encontrar mis proyectos, novedades y todo lo que quiera "
            f"compartir con el mundo. ¡Gracias por visitar!</p>"
        )
        post_excerpt = f"Primera entrada de blog de {nombre_usuario} en Il Postino."

    img_tag = ""
    if foto_url:
        img_tag = f'<img src="{foto_url}" style="width:100%;max-width:700px;border-radius:12px;margin-bottom:32px;" alt="foto">'

    post_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{post_excerpt}">
<title>{post_titulo} — {nombre_usuario}</title>
<style>
  :root {{--bg:#FDFBF7;--text:#2D2926;--accent:#A0522D;--muted:#7a6f68;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'Georgia',serif;max-width:720px;margin:0 auto;padding:48px 24px;line-height:1.7;}}
  .back{{font-size:13px;color:var(--accent);text-decoration:none;letter-spacing:1px;text-transform:uppercase;display:inline-block;margin-bottom:40px;}}
  .back:hover{{text-decoration:underline;}}
  .fecha{{font-size:13px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:24px;}}
  h1{{font-size:2rem;font-weight:normal;margin-bottom:32px;line-height:1.3;}}
  .copy p{{font-size:1.1rem;margin-bottom:1.4em;}}
  .copy a{{color:var(--accent);}}
  hr{{border:none;border-top:1px solid #e8e0d5;margin:48px 0;}}
  footer{{font-size:13px;color:var(--muted);text-align:center;}}
  footer a{{color:var(--accent);text-decoration:none;}}
</style>
</head>
<body>
  <a href="../" class="back">← Volver al inicio</a>
  <p class="fecha">{fecha}</p>
  <h1>{post_titulo}</h1>
  {img_tag}
  <div class="copy">{post_body}</div>
  <hr>
  <footer>
    <a href="../">{nombre_usuario}</a>
    &nbsp;·&nbsp;
    <a href="../#blog">Blog</a>
    &nbsp;·&nbsp;
    <a href="https://ilPostinob0t.github.io">Il Postino Bot</a>
  </footer>
</body>
</html>"""

    ok = file_put(owner, repo, "blog/post-001.html", post_html,
                  f"Primera entrada del blog de {nombre_usuario}")

    # Blog index con ese único post
    blog_index = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blog — {nombre_usuario}</title>
<style>
  :root{{--bg:#FDFBF7;--text:#2D2926;--accent:#A0522D;--muted:#7a6f68;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'Georgia',serif;max-width:800px;margin:0 auto;padding:48px 24px;}}
  .back{{font-size:13px;color:var(--accent);text-decoration:none;letter-spacing:1px;text-transform:uppercase;display:inline-block;margin-bottom:40px;}}
  h1{{font-size:2rem;font-weight:normal;margin-bottom:48px;}}
  .card{{padding:28px;border:1px solid #e8e0d5;border-radius:12px;margin-bottom:24px;}}
  .card:hover{{box-shadow:0 4px 20px rgba(0,0,0,0.08);}}
  .fecha{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;}}
  .card h2{{font-size:1.2rem;font-weight:normal;margin-bottom:12px;line-height:1.4;}}
  .card h2 a{{color:var(--text);text-decoration:none;}}
  .card h2 a:hover{{color:var(--accent);}}
  .excerpt{{font-size:.95rem;color:var(--muted);line-height:1.6;margin-bottom:16px;}}
  .leer-mas{{font-size:13px;color:var(--accent);text-decoration:none;}}
  hr{{border:none;border-top:1px solid #e8e0d5;margin:48px 0;}}
  footer{{font-size:13px;color:var(--muted);text-align:center;}}
  footer a{{color:var(--accent);text-decoration:none;}}
</style>
</head>
<body>
  <a href="../" class="back">← {nombre_usuario}</a>
  <h1>Blog</h1>
  <div class="card">
    <p class="fecha">{fecha}</p>
    <h2><a href="post-001.html">{post_titulo}</a></h2>
    <p class="excerpt">{post_excerpt}</p>
    <a href="post-001.html" class="leer-mas">Leer más →</a>
  </div>
  <hr>
  <footer>
    <a href="../">{nombre_usuario}</a>
    &nbsp;·&nbsp;
    <a href="https://ilPostinob0t.github.io">Il Postino Bot</a>
    &nbsp;·&nbsp;
    <a href="https://cafecito.app/ilpostino">☕ Invitame un café</a>
  </footer>
</body>
</html>"""

    file_put(owner, repo, "blog/index.html", blog_index,
             f"Índice del blog de {nombre_usuario}")

    post_url = f"{site_url}blog/post-001.html"
    return {
        "status": "published" if ok else "error",
        "post_url": post_url,
        "blog_index": f"{site_url}blog/",
    }


def publish_initial_blog_posts(user_id: str, nombre_usuario: str, posts_json: str) -> dict:
    """Genera y publica los 4 posts iniciales del blog y el índice del blog.

    Args:
        user_id: ID del usuario.
        nombre_usuario: Nombre real para mostrar en los posts.
        posts_json: JSON string con lista de posts [{title, excerpt, body, date}].

    Returns:
        dict con status y URLs.
    """
    import json as _json
    owner = get_owner()
    repo = get_repo_name(user_id)
    site_url = get_user_site_url(user_id)

    try:
        posts = _json.loads(posts_json) if isinstance(posts_json, str) else posts_json
    except Exception:
        return {"status": "error", "detail": "posts_json inválido"}

    post_urls = []

    # HTML template para cada post
    for i, post in enumerate(posts[:4], 1):
        titulo = post.get("title", f"Entrada {i}")
        fecha = post.get("date", "")
        cuerpo = post.get("body", "")
        excerpt = post.get("excerpt", "")
        filename = f"post-{i:03d}.html"

        # Convertir saltos de línea en párrafos
        parrafos = "".join(
            f"<p>{p.strip()}</p>" for p in cuerpo.split("\n") if p.strip()
        )

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{excerpt}">
<title>{titulo} — {nombre_usuario}</title>
<style>
  :root {{--bg:#FDFBF7;--text:#2D2926;--accent:#A0522D;--muted:#7a6f68;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'Georgia',serif;max-width:720px;margin:0 auto;padding:48px 24px;line-height:1.7;}}
  .back{{font-size:13px;color:var(--accent);text-decoration:none;letter-spacing:1px;text-transform:uppercase;display:inline-block;margin-bottom:40px;}}
  .back:hover{{text-decoration:underline;}}
  .fecha{{font-size:13px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:24px;}}
  h1{{font-size:2rem;font-weight:normal;margin-bottom:32px;line-height:1.3;}}
  .copy p{{font-size:1.1rem;margin-bottom:1.4em;}}
  hr{{border:none;border-top:1px solid #e8e0d5;margin:48px 0;}}
  footer{{font-size:13px;color:var(--muted);text-align:center;}}
  footer a{{color:var(--accent);text-decoration:none;}}
</style>
</head>
<body>
  <a href="../" class="back">← Volver al inicio</a>
  <p class="fecha">{fecha}</p>
  <h1>{titulo}</h1>
  <div class="copy">
    {parrafos}
  </div>
  <hr>
  <footer>
    <a href="../">{nombre_usuario}</a>
    &nbsp;·&nbsp;
    <a href="../#blog">Blog</a>
    &nbsp;·&nbsp;
    <a href="https://ilPostinob0t.github.io">Il Postino Bot</a>
  </footer>
</body>
</html>"""

        ok = file_put(owner, repo, f"blog/{filename}", html,
                      f"Post inicial {i}: {titulo}")
        if ok:
            post_urls.append(f"{site_url}blog/{filename}")

    # Publicar blog/index.html con las 4 tarjetas
    cards = ""
    for i, post in enumerate(posts[:4], 1):
        titulo = post.get("title", f"Entrada {i}")
        excerpt = post.get("excerpt", "")
        fecha = post.get("date", "")
        filename = f"post-{i:03d}.html"
        cards += f"""
        <article class="card">
          <p class="fecha">{fecha}</p>
          <h2><a href="{filename}">{titulo}</a></h2>
          <p class="excerpt">{excerpt}</p>
          <a href="{filename}" class="leer-mas">Leer más →</a>
        </article>"""

    blog_index = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blog — {nombre_usuario}</title>
<style>
  :root{{--bg:#FDFBF7;--text:#2D2926;--accent:#A0522D;--muted:#7a6f68;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'Georgia',serif;max-width:800px;margin:0 auto;padding:48px 24px;}}
  .back{{font-size:13px;color:var(--accent);text-decoration:none;letter-spacing:1px;text-transform:uppercase;display:inline-block;margin-bottom:40px;}}
  h1{{font-size:2rem;font-weight:normal;margin-bottom:48px;}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:32px;}}
  .card{{padding:28px;border:1px solid #e8e0d5;border-radius:12px;}}
  .card:hover{{box-shadow:0 4px 20px rgba(0,0,0,0.08);}}
  .fecha{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;}}
  .card h2{{font-size:1.2rem;font-weight:normal;margin-bottom:12px;line-height:1.4;}}
  .card h2 a{{color:var(--text);text-decoration:none;}}
  .card h2 a:hover{{color:var(--accent);}}
  .excerpt{{font-size:.95rem;color:var(--muted);line-height:1.6;margin-bottom:16px;}}
  .leer-mas{{font-size:13px;color:var(--accent);text-decoration:none;letter-spacing:.5px;}}
  hr{{border:none;border-top:1px solid #e8e0d5;margin:48px 0;}}
  footer{{font-size:13px;color:var(--muted);text-align:center;}}
  footer a{{color:var(--accent);text-decoration:none;}}
</style>
</head>
<body>
  <a href="../" class="back">← {nombre_usuario}</a>
  <h1>Novedades</h1>
  <div class="grid">
    {cards}
  </div>
  <hr>
  <footer>
    <a href="../">{nombre_usuario}</a>
    &nbsp;·&nbsp;
    <a href="https://ilPostinob0t.github.io">Il Postino Bot</a>
    &nbsp;·&nbsp;
    <a href="https://cafecito.app/ilpostino">☕ Invitame un café</a>
  </footer>
</body>
</html>"""

    file_put(owner, repo, "blog/index.html", blog_index,
             f"Crear índice del blog de {nombre_usuario}")

    return {
        "status": "published",
        "posts_count": len(post_urls),
        "post_urls": post_urls,
        "blog_index": f"{site_url}blog/",
    }
