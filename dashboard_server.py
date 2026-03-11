"""
Dashboard local de Il Postino Bot.
Correr con: python dashboard_server.py
Abrir en: http://localhost:7788
"""

import sys
from pathlib import Path
from flask import Flask, jsonify, render_template_string

sys.path.insert(0, str(Path(__file__).parent))
import tools.cloud_storage as storage

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Il Postino — Dashboard</title>
<style>
  :root{--bg:#0f0f0f;--surface:#1a1a1a;--border:#2a2a2a;--text:#e8e0d5;
        --accent:#c17a50;--green:#4caf80;--yellow:#f0b429;--red:#e05a5a;--muted:#666;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:'SF Mono',monospace;font-size:13px;}
  header{padding:20px 32px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:16px;}
  header h1{font-size:16px;font-weight:600;color:var(--accent);}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
  .grid{display:grid;grid-template-columns:320px 1fr;height:calc(100vh - 61px);}
  .panel{border-right:1px solid var(--border);overflow-y:auto;padding:16px;}
  .panel h2{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:12px;}
  .user-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px;cursor:pointer;transition:.15s;}
  .user-card:hover{border-color:var(--accent);}
  .user-card.active{border-color:var(--accent);background:#231a13;}
  .user-name{font-weight:600;color:var(--text);margin-bottom:4px;}
  .user-meta{color:var(--muted);font-size:11px;}
  .badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600;margin-top:6px;}
  .badge-green{background:#1a3a2a;color:var(--green);}
  .badge-yellow{background:#2a2010;color:var(--yellow);}
  .badge-red{background:#2a1515;color:var(--red);}
  .main{overflow-y:auto;padding:16px 24px;}
  .stats{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;}
  .stat{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 20px;min-width:120px;}
  .stat-num{font-size:28px;font-weight:700;color:var(--accent);}
  .stat-label{color:var(--muted);font-size:11px;margin-top:2px;text-transform:uppercase;letter-spacing:.5px;}
  .section{margin-bottom:24px;}
  .section h2{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border);}
  .event-row{display:grid;grid-template-columns:140px 80px 1fr 120px;gap:8px;padding:8px 0;border-bottom:1px solid #1e1e1e;align-items:start;}
  .event-row:last-child{border-bottom:none;}
  .ts{color:var(--muted);font-size:11px;}
  .tipo-pill{font-size:10px;padding:2px 6px;border-radius:4px;font-weight:600;text-align:center;}
  .tipo-pipeline_iniciado{background:#1a2535;color:#60a0d0;}
  .tipo-pipeline_completado{background:#1a3a2a;color:var(--green);}
  .tipo-pipeline_error{background:#2a1515;color:var(--red);}
  .tipo-email_enviado{background:#2a2535;color:#a080d0;}
  .tipo-blog_publicado{background:#2a3520;color:#80c060;}
  .tipo-mensaje_recibido{background:#252520;color:var(--yellow);}
  .tipo-site_url{background:#1a2a1a;color:#60d060;}
  .detalle{color:var(--text);line-height:1.4;}
  .url-link{color:var(--accent);text-decoration:none;font-size:11px;}
  .url-link:hover{text-decoration:underline;}
  .refresh-info{color:var(--muted);font-size:11px;margin-left:auto;}
  #last-update{color:var(--muted);}
  .site-link{color:var(--accent);text-decoration:none;}
  .site-link:hover{text-decoration:underline;}
  .empty{color:var(--muted);padding:24px 0;text-align:center;}
</style>
</head>
<body>
<header>
  <div class="dot"></div>
  <h1>✉ Il Postino Bot — Dashboard</h1>
  <span class="refresh-info">Actualiza cada 10s · <span id="last-update">—</span></span>
</header>
<div class="grid">
  <div class="panel" id="users-panel">
    <h2>Usuarios (<span id="user-count">0</span>)</h2>
    <div id="users-list"></div>
  </div>
  <div class="main">
    <div class="stats" id="stats"></div>
    <div class="section">
      <h2>Actividad reciente</h2>
      <div id="events-list"></div>
    </div>
  </div>
</div>

<script>
let data = {usuarios: {}, eventos: []};

function badge(estado) {
  const map = {publicado:'green', iniciado:'yellow', 'en construcción':'yellow',
                'faltan datos':'red', pausado:'red', error:'red'};
  const c = map[estado] || 'yellow';
  return `<span class="badge badge-${c}">${estado}</span>`;
}

function tipoPill(tipo) {
  return `<span class="tipo-pill tipo-${tipo}">${tipo.replace(/_/g,' ')}</span>`;
}

function render() {
  // Stats
  const total = Object.keys(data.usuarios).length;
  const publicados = Object.values(data.usuarios).filter(u=>u.estado==='publicado'||!u.estado).length;
  const hoy = data.eventos.filter(e=>e.ts.startsWith(new Date().toISOString().slice(0,10))).length;
  const errores = data.eventos.filter(e=>e.estado==='error').length;

  document.getElementById('stats').innerHTML = `
    <div class="stat"><div class="stat-num">${total}</div><div class="stat-label">Usuarios</div></div>
    <div class="stat"><div class="stat-num">${publicados}</div><div class="stat-label">Publicados</div></div>
    <div class="stat"><div class="stat-num">${hoy}</div><div class="stat-label">Eventos hoy</div></div>
    <div class="stat"><div class="stat-num">${errores}</div><div class="stat-label">Errores</div></div>
  `;
  document.getElementById('user-count').textContent = total;

  // Usuarios
  const ul = document.getElementById('users-list');
  ul.innerHTML = Object.entries(data.usuarios).map(([cid, u]) => `
    <div class="user-card">
      <div class="user-name">${u.nombre || u.user_id}</div>
      <div class="user-meta">${u.email || ''}</div>
      <div class="user-meta">ID: ${u.user_id}</div>
      ${u.user_id ? `<div class="user-meta"><a class="site-link" href="https://anyprinter001-source.github.io/jb-${u.user_id.toLowerCase().replace(/_/g,'-')}/" target="_blank">Ver sitio ↗</a></div>` : ''}
      ${badge(u.estado || 'publicado')}
    </div>`).join('') || '<div class="empty">Sin usuarios aún</div>';

  // Eventos
  const el = document.getElementById('events-list');
  const evs = [...data.eventos].reverse().slice(0, 80);
  el.innerHTML = evs.map(e => `
    <div class="event-row">
      <span class="ts">${e.ts.replace('T',' ')}</span>
      ${tipoPill(e.tipo)}
      <span class="detalle">
        <strong>${e.nombre || e.user_id}</strong>
        ${e.detalle ? ' — '+e.detalle : ''}
        ${e.url ? `<br><a class="url-link" href="${e.url}" target="_blank">${e.url}</a>` : ''}
      </span>
      <span class="ts">${e.estado !== 'ok' ? '<span style="color:var(--red)">'+e.estado+'</span>' : ''}</span>
    </div>`).join('') || '<div class="empty">Sin eventos registrados aún</div>';

  document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
}

async function poll() {
  try {
    const r = await fetch('/api/data');
    data = await r.json();
    render();
  } catch(e) { console.error(e); }
}

poll();
setInterval(poll, 10000);
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/data")
def api_data():
    usuarios = storage.leer_json("usuarios.json", {})
    eventos = storage.leer_json("eventos.json", [])
    return jsonify({"usuarios": usuarios, "eventos": eventos})


if __name__ == "__main__":
    print("✉ Il Postino Dashboard corriendo en http://localhost:7788")
    app.run(host="0.0.0.0", port=7788, debug=False)
