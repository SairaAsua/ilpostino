"""
Panel interno de Il Postino Bot.
Genera un HTML estático con el estado de todos los usuarios.
"""

from datetime import datetime
from pathlib import Path
from . import cloud_storage as storage

_KEY_USUARIOS = "usuarios.json"
_KEY_LOG = "log_cambios.json"
DASHBOARD_FILE = Path(__file__).parent.parent / "data" / "dashboard.html"


def _cargar_usuarios() -> dict:
    return storage.leer_json(_KEY_USUARIOS, {})


def _cargar_log() -> list:
    return storage.leer_json(_KEY_LOG, [])


def registrar_cambio(user_id: str, tipo: str, seccion: str, mensaje: str):
    """Guarda un registro de cambio en el historial."""
    log = _cargar_log()
    log.append({
        "fecha": datetime.now().isoformat(),
        "user_id": user_id,
        "tipo": tipo,
        "seccion": seccion,
        "mensaje": mensaje[:200],
    })
    # Mantener solo los últimos 500 registros
    log = log[-500:]
    storage.escribir_json(_KEY_LOG, log)


def generar_dashboard() -> str:
    """Genera el HTML del panel interno y lo guarda en data/dashboard.html."""
    usuarios = _cargar_usuarios()
    log = _cargar_log()

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Filas de la tabla
    filas = ""
    for chat_id, u in usuarios.items():
        uid = u.get("user_id", "")
        nombre = u.get("nombre", "")
        email = u.get("email", "")
        repo = f"jb-{uid.lower().replace('_', '-')}"
        site_url = f"https://ilPostinob0t.github.io/{repo}/"
        estado = u.get("estado", "publicado")
        fecha_creacion = u.get("fecha_creacion", "—")
        fecha_edicion = u.get("fecha_ultima_edicion", "—")
        observaciones = u.get("observaciones", "")

        estado_color = {
            "publicado": "#2a7a3e",
            "iniciado": "#c07a00",
            "en construcción": "#1a5eb8",
            "faltan datos": "#c0390b",
            "pausado": "#888",
        }.get(estado, "#555")

        filas += f"""
        <tr>
          <td><strong>{nombre}</strong><br><small style="color:#888">{chat_id}</small></td>
          <td><a href="mailto:{email}">{email}</a></td>
          <td>
            <span style="background:{estado_color};color:#fff;padding:3px 10px;border-radius:20px;font-size:12px">
              {estado}
            </span>
          </td>
          <td><a href="https://github.com/ilPostinob0t/{repo}" target="_blank">{repo}</a></td>
          <td><a href="{site_url}" target="_blank">Ver sitio ↗</a><br>
              <a href="{site_url}blog/" target="_blank" style="font-size:12px;color:#888">Blog ↗</a></td>
          <td style="font-size:12px">{fecha_creacion}</td>
          <td style="font-size:12px">{fecha_edicion}</td>
          <td style="font-size:12px;max-width:200px">{observaciones}</td>
        </tr>"""

    # Log de cambios recientes (últimos 20)
    log_reciente = log[-20:][::-1]
    filas_log = ""
    for entrada in log_reciente:
        fecha = entrada.get("fecha", "")[:16].replace("T", " ")
        filas_log += f"""
        <tr>
          <td style="font-size:12px">{fecha}</td>
          <td style="font-size:12px">{entrada.get('user_id','')}</td>
          <td style="font-size:12px">{entrada.get('tipo','')}</td>
          <td style="font-size:12px">{entrada.get('seccion','')}</td>
          <td style="font-size:12px">{entrada.get('mensaje','')}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Panel — Il Postino Bot</title>
<style>
  :root{{--bg:#FDFBF7;--text:#2D2926;--accent:#A0522D;--border:#e8e0d5;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;padding:32px;}}
  h1{{font-size:1.6rem;font-weight:600;margin-bottom:4px;color:var(--accent);}}
  .meta{{font-size:13px;color:#888;margin-bottom:32px;}}
  h2{{font-size:1rem;font-weight:600;margin-bottom:16px;text-transform:uppercase;letter-spacing:1px;color:#555;}}
  .card{{background:#fff;border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:32px;overflow-x:auto;}}
  table{{width:100%;border-collapse:collapse;min-width:700px;}}
  th{{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:#888;padding:8px 12px;border-bottom:2px solid var(--border);}}
  td{{padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top;}}
  tr:hover td{{background:#faf7f4;}}
  a{{color:var(--accent);text-decoration:none;}}
  a:hover{{text-decoration:underline;}}
  .stats{{display:flex;gap:16px;margin-bottom:32px;flex-wrap:wrap;}}
  .stat{{background:#fff;border:1px solid var(--border);border-radius:8px;padding:16px 24px;}}
  .stat-num{{font-size:2rem;font-weight:700;color:var(--accent);}}
  .stat-label{{font-size:12px;color:#888;margin-top:4px;}}
</style>
</head>
<body>
  <h1>✉ Il Postino Bot — Panel interno</h1>
  <p class="meta">Última actualización: {ahora} · {len(usuarios)} usuarios registrados</p>

  <div class="stats">
    <div class="stat">
      <div class="stat-num">{len(usuarios)}</div>
      <div class="stat-label">Usuarios totales</div>
    </div>
    <div class="stat">
      <div class="stat-num">{sum(1 for u in usuarios.values() if u.get('estado','publicado') == 'publicado')}</div>
      <div class="stat-label">Sitios publicados</div>
    </div>
    <div class="stat">
      <div class="stat-num">{len(log)}</div>
      <div class="stat-label">Cambios registrados</div>
    </div>
  </div>

  <div class="card">
    <h2>Usuarios</h2>
    <table>
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Email</th>
          <th>Estado</th>
          <th>Repo</th>
          <th>GitHub Pages</th>
          <th>Creado</th>
          <th>Última edición</th>
          <th>Notas</th>
        </tr>
      </thead>
      <tbody>
        {filas if filas else '<tr><td colspan="8" style="text-align:center;color:#888;padding:32px">Sin usuarios registrados aún</td></tr>'}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Últimos cambios</h2>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Usuario</th>
          <th>Tipo</th>
          <th>Sección</th>
          <th>Detalle</th>
        </tr>
      </thead>
      <tbody>
        {filas_log if filas_log else '<tr><td colspan="5" style="text-align:center;color:#888;padding:32px">Sin cambios registrados aún</td></tr>'}
      </tbody>
    </table>
  </div>
</body>
</html>"""

    # Guardar también en storage (para Cloud Run sin filesystem persistente)
    storage.escribir_bytes("dashboard.html", html.encode("utf-8"))
    # Guardar local si es posible (para dashboard_server.py)
    try:
        DASHBOARD_FILE.parent.mkdir(exist_ok=True)
        DASHBOARD_FILE.write_text(html, encoding="utf-8")
    except Exception:
        pass
    return html
