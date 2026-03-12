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
      ${u.user_id ? `<div class="user-meta"><a class="site-link" href="https://ilPostinob0t.github.io/jb-${u.user_id.toLowerCase().replace(/_/g,'-')}/" target="_blank">Ver sitio ↗</a></div>` : ''}
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


MISION_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OPERATION BRIEF — Il Postino</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

:root {
  --bg: #020810;
  --surface: #030d1a;
  --border: #0a3a5a;
  --glow: #00d4ff;
  --glow2: #00ff9d;
  --warn: #ff9500;
  --danger: #ff3860;
  --text: #c8e8f8;
  --muted: #3a6a8a;
  --done: #00ff9d;
  --wip: #00d4ff;
  --pending: #ff9500;
  --dim: #081828;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  overflow-x: hidden;
  min-height: 100vh;
}

/* Scanlines overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.08) 2px,
    rgba(0,0,0,0.08) 4px
  );
  pointer-events: none;
  z-index: 1000;
}

/* Grid background */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* ── HEADER ── */
header {
  position: relative;
  z-index: 10;
  padding: 16px 32px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 20px;
  background: linear-gradient(90deg, rgba(0,212,255,0.05) 0%, transparent 60%);
}

.header-id {
  font-family: 'Orbitron', monospace;
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 3px;
  text-transform: uppercase;
}

.header-title {
  font-family: 'Orbitron', monospace;
  font-size: 18px;
  font-weight: 900;
  color: var(--glow);
  text-shadow: 0 0 20px rgba(0,212,255,0.8), 0 0 40px rgba(0,212,255,0.4);
  letter-spacing: 4px;
}

.header-sub {
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 2px;
}

.status-live {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--glow2);
}

.status-live::before {
  content: '';
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--glow2);
  box-shadow: 0 0 8px var(--glow2);
  animation: blink 1.4s infinite;
}

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }

.nav-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  position: relative;
  z-index: 10;
}

.tab {
  padding: 10px 24px;
  font-family: 'Orbitron', monospace;
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--muted);
  cursor: pointer;
  border-right: 1px solid var(--border);
  transition: .2s;
  text-decoration: none;
  display: block;
}

.tab:hover, .tab.active {
  color: var(--glow);
  background: rgba(0,212,255,0.05);
  text-shadow: 0 0 10px rgba(0,212,255,0.6);
}

.tab.active {
  border-bottom: 2px solid var(--glow);
}

/* ── MAIN LAYOUT ── */
.main {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 0;
  height: calc(100vh - 105px);
  overflow: hidden;
}

.col-left {
  overflow-y: auto;
  padding: 24px 28px;
  border-right: 1px solid var(--border);
}

.col-right {
  overflow-y: auto;
  padding: 20px 20px;
}

/* ── SECTION TITLE ── */
.sec-title {
  font-family: 'Orbitron', monospace;
  font-size: 9px;
  letter-spacing: 3px;
  color: var(--muted);
  text-transform: uppercase;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
}

.sec-title::before {
  content: '//';
  color: var(--glow);
  opacity: .6;
}

/* ── AGENT NETWORK ── */
.agent-network {
  margin-bottom: 32px;
}

.pipeline-label {
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--glow);
  margin-bottom: 12px;
  opacity: .7;
}

.flow {
  display: flex;
  align-items: center;
  gap: 0;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.agent-node {
  position: relative;
  background: var(--dim);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 14px;
  min-width: 120px;
  transition: .2s;
  cursor: default;
}

.agent-node:hover {
  border-color: var(--glow);
  box-shadow: 0 0 12px rgba(0,212,255,0.2), inset 0 0 12px rgba(0,212,255,0.03);
}

.agent-node.active {
  border-color: var(--glow2);
  box-shadow: 0 0 16px rgba(0,255,157,0.25);
}

.agent-node.director-node {
  border-color: var(--glow);
  box-shadow: 0 0 20px rgba(0,212,255,0.3);
  min-width: 140px;
}

.node-name {
  font-family: 'Orbitron', monospace;
  font-size: 9px;
  letter-spacing: 1px;
  color: var(--glow);
  margin-bottom: 4px;
}

.node-name.green { color: var(--glow2); }
.node-name.warn { color: var(--warn); }

.node-desc {
  font-size: 10px;
  color: var(--muted);
  line-height: 1.4;
}

.node-model {
  margin-top: 6px;
  font-size: 9px;
  color: #1a4a6a;
  display: flex;
  align-items: center;
  gap: 4px;
}

.node-model .gem { color: #2a6a9a; }

.arrow {
  padding: 0 6px;
  color: var(--border);
  font-size: 14px;
  flex-shrink: 0;
}

.branch-container {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.branch {
  flex: 1;
  background: rgba(0,212,255,0.02);
  border: 1px solid rgba(0,212,255,0.08);
  border-radius: 8px;
  padding: 12px;
}

.branch-title {
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--muted);
  margin-bottom: 10px;
  text-align: center;
}

.flow-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.arrow-down {
  color: var(--border);
  font-size: 12px;
  line-height: 1;
  padding: 2px 0;
}

.parallel-row {
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: flex-start;
}

/* ── INTENT MODULE ── */
.intent-module {
  background: var(--dim);
  border: 1px solid rgba(0,255,157,0.2);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 24px;
}

.intent-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.intent-tag {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 10px;
  border: 1px solid;
}

.intent-tag.post   { border-color: #00ff9d44; color: var(--glow2); background: rgba(0,255,157,0.05); }
.intent-tag.edit   { border-color: #00d4ff44; color: var(--glow);  background: rgba(0,212,255,0.05); }
.intent-tag.new    { border-color: #ff950044; color: var(--warn);  background: rgba(255,149,0,0.05); }
.intent-tag.del    { border-color: #ff386044; color: var(--danger);background: rgba(255,56,96,0.05); }
.intent-tag.sec    { border-color: #aa80ff44; color: #aa80ff;      background: rgba(170,128,255,0.05); }
.intent-tag.other  { border-color: #3a6a8a44; color: var(--muted); background: transparent; }

/* ── TASKS ── */
.task-list { display: flex; flex-direction: column; gap: 8px; }

.task-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid transparent;
  transition: .2s;
}

.task-item:hover { background: rgba(0,212,255,0.03); }

.task-item.done   { border-color: rgba(0,255,157,0.15); }
.task-item.wip    { border-color: rgba(0,212,255,0.2); background: rgba(0,212,255,0.03); }
.task-item.next   { border-color: rgba(255,149,0,0.15); }
.task-item.idea   { border-color: rgba(58,106,138,0.2); }

.task-icon { font-size: 14px; flex-shrink: 0; margin-top: 1px; }

.task-text { flex: 1; }
.task-name { font-size: 11px; color: var(--text); margin-bottom: 2px; }
.task-item.done .task-name { color: var(--muted); text-decoration: line-through; text-decoration-color: #1a4a3a; }
.task-meta { font-size: 10px; color: var(--muted); }

.pill {
  font-size: 9px;
  padding: 2px 8px;
  border-radius: 10px;
  letter-spacing: 1px;
  flex-shrink: 0;
  align-self: flex-start;
}
.pill.done  { background: #0a2a1a; color: var(--glow2); border: 1px solid rgba(0,255,157,0.3); }
.pill.wip   { background: #0a1a2a; color: var(--glow);  border: 1px solid rgba(0,212,255,0.3); }
.pill.next  { background: #1a1000; color: var(--warn);  border: 1px solid rgba(255,149,0,0.3); }
.pill.idea  { background: #0a0a14; color: var(--muted); border: 1px solid var(--border); }

/* ── SYSTEM STATUS ── */
.sys-grid { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }

.sys-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: var(--dim);
  border: 1px solid var(--border);
  border-radius: 4px;
}

.sys-label { font-size: 10px; color: var(--muted); letter-spacing: 1px; }
.sys-val   { font-size: 10px; color: var(--text); }
.sys-ok    { color: var(--glow2); }
.sys-warn  { color: var(--warn); }

/* ── STATS ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}

.stat-box {
  background: var(--dim);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}

.stat-num {
  font-family: 'Orbitron', monospace;
  font-size: 22px;
  font-weight: 700;
  color: var(--glow);
  text-shadow: 0 0 12px rgba(0,212,255,0.5);
}

.stat-lbl {
  font-size: 9px;
  letter-spacing: 1px;
  color: var(--muted);
  margin-top: 4px;
  text-transform: uppercase;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ── CORNER DECOR ── */
.corner-tl, .corner-tr {
  position: fixed;
  width: 20px; height: 20px;
  z-index: 999;
  opacity: .4;
}
.corner-tl { top: 0; left: 0; border-top: 2px solid var(--glow); border-left: 2px solid var(--glow); }
.corner-tr { top: 0; right: 0; border-top: 2px solid var(--glow); border-right: 2px solid var(--glow); }
</style>
</head>
<body>
<div class="corner-tl"></div>
<div class="corner-tr"></div>

<header>
  <div>
    <div class="header-id">SYS-ILP · REV 007 · 2026</div>
    <div class="header-title">OPERATION BRIEF</div>
    <div class="header-sub">IL POSTINO · AGENT NETWORK · MISSION CONTROL</div>
  </div>
  <div class="status-live">SISTEMA ACTIVO</div>
</header>

<div class="nav-tabs">
  <a href="/" class="tab">◈ DASHBOARD</a>
  <a href="/mision" class="tab active">◉ OPERATION BRIEF</a>
</div>

<div class="main">

  <!-- ══ COL IZQUIERDA: ARQUITECTURA ══ -->
  <div class="col-left">

    <div class="sec-title">AGENT NETWORK TOPOLOGY</div>

    <div class="agent-network">

      <!-- DIRECTOR -->
      <div class="pipeline-label">▸ CORE DIRECTOR</div>
      <div class="flow" style="margin-bottom:20px;">
        <div class="agent-node director-node">
          <div class="node-name">DIRECTOR</div>
          <div class="node-desc">Orquesta todos los pipelines</div>
          <div class="node-model"><span class="gem">◆</span> gemini-3.1-flash-lite</div>
        </div>
        <div class="arrow">──▶</div>
        <div style="display:flex;gap:12px;">
          <div style="text-align:center;font-size:9px;color:var(--muted);">
            <div>ONBOARDING</div>
            <div style="color:var(--border);">pipeline</div>
          </div>
          <div style="font-size:10px;color:var(--border);align-self:center;">/</div>
          <div style="text-align:center;font-size:9px;color:var(--muted);">
            <div>UPDATE</div>
            <div style="color:var(--border);">pipeline</div>
          </div>
        </div>
      </div>

      <!-- PIPELINES -->
      <div class="pipeline-label">▸ ONBOARDING PIPELINE — sitio nuevo desde cero</div>
      <div class="flow" style="flex-wrap:wrap; gap:4px; margin-bottom:24px;">
        <div class="agent-node">
          <div class="node-name">BRIEF</div>
          <div class="node-desc">Estructura datos del formulario</div>
          <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
        </div>
        <div class="arrow">→</div>
        <div class="branch-container" style="flex-wrap:wrap; gap:4px; align-items:flex-start;">
          <div class="agent-node">
            <div class="node-name">CONTENT</div>
            <div class="node-desc">Genera copy del sitio</div>
            <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
          </div>
          <div class="arrow" style="align-self:center;">+</div>
          <div class="agent-node">
            <div class="node-name">DESIGN</div>
            <div class="node-desc">Paleta, tipografía, layout</div>
            <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
          </div>
        </div>
        <div class="arrow">→</div>
        <div class="agent-node active">
          <div class="node-name green">WEB BUILDER</div>
          <div class="node-desc">HTML/CSS completo</div>
          <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
        </div>
        <div class="arrow">→</div>
        <div class="agent-node active">
          <div class="node-name green">PUBLISHER</div>
          <div class="node-desc">GitHub Pages + README</div>
          <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
        </div>
        <div class="arrow">→</div>
        <div class="agent-node">
          <div class="node-name">EMAIL</div>
          <div class="node-desc">Confirma al usuario</div>
          <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
        </div>
      </div>

      <!-- UPDATE PIPELINE -->
      <div class="pipeline-label">▸ UPDATE PIPELINE — actualizaciones de Telegram</div>
      <div class="flow" style="flex-wrap:wrap; gap:4px; margin-bottom:16px;">
        <div class="agent-node">
          <div class="node-name">TELEGRAM</div>
          <div class="node-desc">Parsea mensajes entrantes</div>
          <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
        </div>
        <div class="arrow">→</div>
        <div class="agent-node">
          <div class="node-name">CONTENT UPDATE</div>
          <div class="node-desc">Convierte en contenido web</div>
          <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
        </div>
        <div class="arrow">→</div>
        <div class="agent-node active">
          <div class="node-name green">PUBLISHER</div>
          <div class="node-desc">Publica a GitHub</div>
          <div class="node-model"><span class="gem">◆</span> gemini-3.1</div>
        </div>
      </div>

    </div><!-- /agent-network -->

    <!-- INTENT MODULE -->
    <div class="sec-title" style="margin-top:8px;">MÓDULO DE INTENCIÓN LIBRE — nuevo</div>
    <div class="intent-module">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="font-family:'Orbitron',monospace;font-size:9px;color:var(--glow2);letter-spacing:2px;">MENSAJE_LIBRE HANDLER</div>
        <span class="pill wip">ACTIVO</span>
      </div>
      <div style="font-size:10px;color:var(--muted);line-height:1.6;">
        Captura mensajes fuera de cualquier conversación activa.<br>
        Clasifica la intención con <span style="color:var(--glow);">gemini-2.0-flash-lite</span> y ejecuta el flujo correspondiente sin volver a preguntar.
      </div>
      <div class="intent-tags">
        <span class="intent-tag post">POST → blog directo</span>
        <span class="intent-tag edit">EDITAR → aplica cambio</span>
        <span class="intent-tag sec">NUEVA SECCIÓN → agrega</span>
        <span class="intent-tag del">ELIMINAR → borra</span>
        <span class="intent-tag new">NUEVO → onboarding</span>
        <span class="intent-tag other">OTRO → menú ayuda</span>
      </div>
      <div style="margin-top:10px;display:flex;gap:6px;align-items:center;font-size:9px;color:var(--muted);">
        <span style="color:var(--border);">EDIT TOOLS:</span>
        <span style="color:#2a6a9a;">gemini-2.0-flash-lite</span>
        <span style="color:var(--border);margin:0 4px;">·</span>
        <span style="color:var(--border);">TOOLS:</span>
        <span style="color:#2a4a6a;">edit_tools.py · blog_tools.py · github_tools.py</span>
      </div>
    </div>

  </div><!-- /col-left -->

  <!-- ══ COL DERECHA: TASKS + STATUS ══ -->
  <div class="col-right">

    <!-- STATS -->
    <div class="sec-title">MÉTRICAS</div>
    <div class="stats-row" id="stats-row">
      <div class="stat-box"><div class="stat-num" id="s-usuarios">—</div><div class="stat-lbl">Usuarios</div></div>
      <div class="stat-box"><div class="stat-num" id="s-publicados">—</div><div class="stat-lbl">Publicados</div></div>
      <div class="stat-box"><div class="stat-num" id="s-eventos">—</div><div class="stat-lbl">Eventos hoy</div></div>
      <div class="stat-box"><div class="stat-num" id="s-errores" style="color:var(--danger)">—</div><div class="stat-lbl">Errores</div></div>
    </div>

    <!-- SYSTEM STATUS -->
    <div class="sec-title">SYSTEM STATUS</div>
    <div class="sys-grid">
      <div class="sys-row">
        <span class="sys-label">BOT TELEGRAM</span>
        <span class="sys-val sys-ok">✓ POLLING</span>
      </div>
      <div class="sys-row">
        <span class="sys-label">CLOUD RUN</span>
        <span class="sys-val sys-ok">✓ us-central1</span>
      </div>
      <div class="sys-row">
        <span class="sys-label">GITHUB PAGES</span>
        <span class="sys-val sys-ok">✓ ilPostinob0t</span>
      </div>
      <div class="sys-row">
        <span class="sys-label">GCS BUCKET</span>
        <span class="sys-val sys-ok">✓ ilpostino-data</span>
      </div>
      <div class="sys-row">
        <span class="sys-label">ADK VERSION</span>
        <span class="sys-val" style="color:var(--glow);">1.26</span>
      </div>
      <div class="sys-row">
        <span class="sys-label">MODEL / AGENTS</span>
        <span class="sys-val" style="color:#2a6a9a;">gemini-3.1-flash-lite</span>
      </div>
      <div class="sys-row">
        <span class="sys-label">MODEL / EDIT</span>
        <span class="sys-val" style="color:#2a6a9a;">gemini-2.0-flash-lite</span>
      </div>
      <div class="sys-row">
        <span class="sys-label">REVISION</span>
        <span class="sys-val" style="color:var(--muted);">00007-tzn</span>
      </div>
    </div>

    <!-- ROADMAP TASKS -->
    <div class="sec-title">ROADMAP · MISSION TASKS</div>
    <div class="task-list">

      <div class="task-item done">
        <span class="task-icon">✓</span>
        <div class="task-text">
          <div class="task-name">Onboarding completo (ADK pipeline)</div>
          <div class="task-meta">brief → design → build → publish → email</div>
        </div>
        <span class="pill done">DONE</span>
      </div>

      <div class="task-item done">
        <span class="task-icon">✓</span>
        <div class="task-text">
          <div class="task-name">/post — entradas de blog con foto</div>
          <div class="task-meta">blog_tools · GitHub Pages</div>
        </div>
        <span class="pill done">DONE</span>
      </div>

      <div class="task-item done">
        <span class="task-icon">✓</span>
        <div class="task-text">
          <div class="task-name">/edit — edición libre con IA</div>
          <div class="task-meta">edit_tools · gemini-2.0-flash-lite</div>
        </div>
        <span class="pill done">DONE</span>
      </div>

      <div class="task-item done">
        <span class="task-icon">✓</span>
        <div class="task-text">
          <div class="task-name">/nuevaseccion · /eliminar</div>
          <div class="task-meta">edición estructural del HTML</div>
        </div>
        <span class="pill done">DONE</span>
      </div>

      <div class="task-item done">
        <span class="task-icon">✓</span>
        <div class="task-text">
          <div class="task-name">Deploy Cloud Run — polling mode</div>
          <div class="task-meta">min-instances 1 · health check HTTP</div>
        </div>
        <span class="pill done">DONE</span>
      </div>

      <div class="task-item wip">
        <span class="task-icon">◉</span>
        <div class="task-text">
          <div class="task-name">Mensaje libre → detección de intención</div>
          <div class="task-meta">gemini clasifica y ejecuta sin preguntar</div>
        </div>
        <span class="pill wip">HOY</span>
      </div>

      <div class="task-item wip">
        <span class="task-icon">◉</span>
        <div class="task-text">
          <div class="task-name">Operation Brief — panel de misión</div>
          <div class="task-meta">este panel · arquitectura + roadmap</div>
        </div>
        <span class="pill wip">HOY</span>
      </div>

      <div class="task-item next">
        <span class="task-icon">▷</span>
        <div class="task-text">
          <div class="task-name">Multiusuario — onboarding paralelo</div>
          <div class="task-meta">queue de pipelines por chat_id</div>
        </div>
        <span class="pill next">NEXT</span>
      </div>

      <div class="task-item next">
        <span class="task-icon">▷</span>
        <div class="task-text">
          <div class="task-name">Preview antes de publicar</div>
          <div class="task-meta">captura screenshot + confirma con el usuario</div>
        </div>
        <span class="pill next">NEXT</span>
      </div>

      <div class="task-item next">
        <span class="task-icon">▷</span>
        <div class="task-text">
          <div class="task-name">Dominio custom — CNAME automático</div>
          <div class="task-meta">detecta si el usuario tiene dominio propio</div>
        </div>
        <span class="pill next">NEXT</span>
      </div>

      <div class="task-item idea">
        <span class="task-icon">◌</span>
        <div class="task-text">
          <div class="task-name">Analíticas del sitio — visitas</div>
          <div class="task-meta">embed simple counter · reporta al usuario</div>
        </div>
        <span class="pill idea">IDEA</span>
      </div>

      <div class="task-item idea">
        <span class="task-icon">◌</span>
        <div class="task-text">
          <div class="task-name">Edición por voz — Whisper transcribe</div>
          <div class="task-meta">audio → texto → intención → acción</div>
        </div>
        <span class="pill idea">IDEA</span>
      </div>

    </div>
  </div><!-- /col-right -->

</div><!-- /main -->

<script>
async function loadStats() {
  try {
    const r = await fetch('/api/data');
    const d = await r.json();
    const total = Object.keys(d.usuarios).length;
    const publicados = Object.values(d.usuarios).filter(u => u.estado === 'publicado' || !u.estado).length;
    const hoy = d.eventos.filter(e => e.ts && e.ts.startsWith(new Date().toISOString().slice(0,10))).length;
    const errores = d.eventos.filter(e => e.estado === 'error').length;
    document.getElementById('s-usuarios').textContent = total;
    document.getElementById('s-publicados').textContent = publicados;
    document.getElementById('s-eventos').textContent = hoy;
    document.getElementById('s-errores').textContent = errores;
  } catch(e) {}
}
loadStats();
setInterval(loadStats, 15000);
</script>

</body>
</html>"""


@app.route("/mision")
def mision():
    return render_template_string(MISION_HTML)


if __name__ == "__main__":
    print("✉ Il Postino Dashboard corriendo en http://localhost:7788")
    app.run(host="0.0.0.0", port=7788, debug=False)
