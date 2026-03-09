"""
Herramientas para gestionar el blog de cada usuario.
Usa el repo propio del usuario: jb-{user_id}
"""

import json
from tools.github_tools import get_owner, get_repo_name, get_user_site_url, file_put, file_get_json


def publicar_post_y_actualizar_indice(
    user_id: str,
    nombre_usuario: str,
    filename: str,
    fecha: str,
    titulo: str,
    excerpt: str,
    tiene_foto: bool,
    blog_html: str,
) -> str:
    """Publica el post y regenera el índice del blog en el repo propio del usuario."""
    owner = get_owner()
    repo = get_repo_name(user_id)
    base_url = get_user_site_url(user_id).rstrip("/")

    # 1. Publicar el post individual
    file_put(owner, repo, f"blog/{filename}", blog_html, f"Nuevo post: {titulo[:50]}")

    # 2. Actualizar posts.json
    posts = file_get_json(owner, repo, "blog/posts.json")
    post_url = f"{base_url}/blog/{filename}"
    posts.insert(0, {
        "filename": filename,
        "url": post_url,
        "fecha": fecha,
        "titulo": titulo,
        "excerpt": excerpt,
        "tiene_foto": tiene_foto,
    })
    file_put(owner, repo, "blog/posts.json",
             json.dumps(posts, ensure_ascii=False, indent=2),
             "Actualizar índice del blog")

    # 3. Regenerar blog/index.html
    cards = ""
    for p in posts:
        foto_badge = "📸 " if p.get("tiene_foto") else ""
        cards += f"""
        <article class="card">
          <div class="card-meta">{foto_badge}{p['fecha']}</div>
          <h2 class="card-titulo"><a href="{p['url']}">{p['titulo']}</a></h2>
          <p class="card-excerpt">{p['excerpt']}</p>
          <a href="{p['url']}" class="card-link">Leer →</a>
        </article>"""

    blog_index = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blog — {nombre_usuario}</title>
<style>
  :root {{ --bg:#FDFBF7; --text:#2D2926; --accent:#A0522D; --muted:#7a6f68; --border:#e8e0d5; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Georgia',serif;
         max-width:720px; margin:0 auto; padding:48px 24px; }}
  .back {{ font-size:13px; color:var(--accent); text-decoration:none;
           letter-spacing:1px; text-transform:uppercase; }}
  h1 {{ font-size:36px; font-weight:normal; margin:24px 0 8px; }}
  .subtitulo {{ font-size:16px; color:var(--muted); margin-bottom:48px; }}
  .card {{ border-top:1px solid var(--border); padding:32px 0; }}
  .card:last-child {{ border-bottom:1px solid var(--border); }}
  .card-meta {{ font-size:12px; color:var(--muted); letter-spacing:1px;
                text-transform:uppercase; margin-bottom:10px; }}
  .card-titulo {{ font-size:22px; font-weight:normal; margin-bottom:10px; }}
  .card-titulo a {{ color:var(--text); text-decoration:none; }}
  .card-titulo a:hover {{ color:var(--accent); }}
  .card-excerpt {{ font-size:15px; color:var(--muted); line-height:1.7; margin-bottom:14px; }}
  .card-link {{ font-size:14px; color:var(--accent); text-decoration:none; }}
  footer {{ margin-top:64px; text-align:center; font-size:13px; color:var(--muted); }}
  footer a {{ color:var(--accent); text-decoration:none; }}
</style>
</head>
<body>
  <a href="{base_url}/" class="back">← Volver al sitio</a>
  <h1>Blog</h1>
  <p class="subtitulo">{nombre_usuario} · {len(posts)} {"entrada" if len(posts) == 1 else "entradas"}</p>
  <main>{cards}</main>
  <footer><a href="{base_url}/">{nombre_usuario}</a> · ilPostino</footer>
</body>
</html>"""

    file_put(owner, repo, "blog/index.html", blog_index,
             f"Actualizar índice del blog ({len(posts)} posts)")

    return post_url
