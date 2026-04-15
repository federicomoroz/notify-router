def render_spa() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>notify-router</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet"/>
  <style>
    :root {
      --green:  #15ff00;
      --dim:    #0a9900;
      --red:    #ff3c3c;
      --yellow: #ffcc00;
      --cyan:   #00ffcc;
      --bg:     #080808;
      --panel:  #0d0d0d;
      --border: #1a3300;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--green);
      font-family: 'Share Tech Mono', monospace;
      font-size: 14px;
      min-height: 100vh;
    }
    header {
      padding: 24px 32px 16px;
      border-bottom: 1px solid var(--border);
    }
    h1 {
      font-family: 'VT323', monospace;
      font-size: 3rem;
      letter-spacing: 4px;
      text-shadow: 0 0 14px rgba(21,255,0,0.5);
    }
    .subtitle { color: var(--dim); font-size: 12px; margin-top: 2px; }
    nav {
      display: flex;
      padding: 0 24px;
      border-bottom: 1px solid var(--border);
      gap: 0;
    }
    .tab-btn {
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--dim);
      font-family: 'VT323', monospace;
      font-size: 1.35rem;
      letter-spacing: 2px;
      padding: 12px 18px;
      cursor: pointer;
      transition: color .15s, border-color .15s;
    }
    .tab-btn:hover { color: var(--green); }
    .tab-btn.active { color: var(--green); border-bottom-color: var(--green); text-shadow: 0 0 6px rgba(21,255,0,0.4); }
    .tab-panel { display: none; padding: 28px 32px; }
    .tab-panel.active { display: block; }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 14px;
      margin-bottom: 32px;
    }
    .stat-card {
      background: var(--panel);
      border: 1px solid var(--border);
      padding: 14px 18px;
      transition: border-color .15s;
    }
    .stat-card:hover { border-color: var(--dim); }
    .stat-card .label { color: var(--dim); font-size: 10px; text-transform: uppercase; letter-spacing: 2px; }
    .stat-card .value { font-family: 'VT323', monospace; font-size: 2.6rem; line-height: 1; margin-top: 4px; }
    .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    h2 { font-family: 'VT323', monospace; font-size: 1.55rem; letter-spacing: 2px; }
    .btn {
      background: none;
      border: 1px solid var(--green);
      color: var(--green);
      font-family: 'Share Tech Mono', monospace;
      font-size: 12px;
      padding: 6px 14px;
      cursor: pointer;
      transition: background .12s, color .12s, box-shadow .12s;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .btn:hover { background: var(--green); color: var(--bg); box-shadow: 0 0 8px rgba(21,255,0,0.5); }
    .btn.danger { border-color: var(--red); color: var(--red); }
    .btn.danger:hover { background: var(--red); color: var(--bg); box-shadow: 0 0 8px rgba(255,60,60,0.5); }
    .btn.sm { padding: 3px 8px; font-size: 11px; }
    table { width: 100%; border-collapse: collapse; }
    th {
      color: var(--dim);
      text-align: left;
      padding: 8px 12px;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 1px;
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: 7px 12px;
      border-bottom: 1px solid #0f0f0f;
      font-size: 13px;
      max-width: 280px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    td.ok  { color: var(--green); }
    td.err { color: var(--red); }
    .toggle { display: inline-flex; align-items: center; cursor: pointer; }
    .toggle input { display: none; }
    .toggle-track {
      width: 30px; height: 15px;
      background: #222;
      border: 1px solid #444;
      border-radius: 8px;
      position: relative;
      transition: background .2s;
    }
    .toggle input:checked + .toggle-track { background: #0a3300; border-color: var(--green); }
    .toggle-thumb {
      width: 9px; height: 9px;
      background: #555;
      border-radius: 50%;
      position: absolute;
      top: 2px; left: 2px;
      transition: left .2s, background .2s;
    }
    .toggle input:checked + .toggle-track .toggle-thumb { left: 17px; background: var(--green); }
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; color: var(--dim); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
    input, select, textarea {
      background: #050505;
      border: 1px solid var(--border);
      color: var(--green);
      font-family: 'Share Tech Mono', monospace;
      font-size: 13px;
      padding: 7px 10px;
      width: 100%;
      outline: none;
      transition: border-color .15s, box-shadow .15s;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--green);
      box-shadow: 0 0 5px rgba(21,255,0,0.15);
    }
    textarea { resize: vertical; min-height: 72px; }
    select option { background: var(--bg); }
    #modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.85);
      display: flex; align-items: center; justify-content: center;
      z-index: 100;
    }
    #modal-overlay.hidden { display: none; }
    #modal {
      background: var(--panel);
      border: 1px solid var(--border);
      width: 500px;
      max-width: 96vw;
      max-height: 90vh;
      display: flex; flex-direction: column;
      box-shadow: 0 0 32px rgba(21,255,0,0.08);
    }
    #modal-title {
      font-family: 'VT323', monospace;
      font-size: 1.55rem;
      letter-spacing: 2px;
      padding: 14px 20px;
      border-bottom: 1px solid var(--border);
    }
    #modal-body { padding: 20px; overflow-y: auto; flex: 1; }
    #modal-footer {
      padding: 14px 20px;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }
    #toast {
      position: fixed;
      bottom: 24px; right: 24px;
      background: var(--panel);
      border: 1px solid var(--green);
      color: var(--green);
      font-size: 13px;
      padding: 10px 16px;
      z-index: 200;
      opacity: 0;
      transform: translateY(6px);
      transition: opacity .2s, transform .2s;
      pointer-events: none;
    }
    #toast.show { opacity: 1; transform: translateY(0); }
    #toast.err { border-color: var(--red); color: var(--red); }
    #dispatch-result {
      background: var(--panel);
      border: 1px solid var(--border);
      padding: 14px 16px;
      margin-top: 16px;
      min-height: 56px;
      font-size: 13px;
      white-space: pre-wrap;
      word-break: break-all;
      line-height: 1.6;
    }
    .loading { color: var(--dim); font-size: 12px; padding: 20px 0; text-align: center; letter-spacing: 2px; }
    .empty   { color: #2a2a2a; text-align: center; padding: 20px 0; font-size: 13px; }
    .filter-bar { display: flex; gap: 8px; align-items: center; }
    .filter-bar input, .filter-bar select { width: auto; }
  </style>
</head>
<body>

<header>
  <h1>&gt; NOTIFY-ROUTER</h1>
  <p class="subtitle" id="clock">multi-channel notification routing engine</p>
</header>

<nav>
  <button class="tab-btn" data-tab="dashboard" onclick="showTab('dashboard')">DASHBOARD</button>
  <button class="tab-btn" data-tab="channels"  onclick="showTab('channels')">CHANNELS</button>
  <button class="tab-btn" data-tab="rules"     onclick="showTab('rules')">RULES</button>
  <button class="tab-btn" data-tab="events"    onclick="showTab('events')">EVENTS</button>
  <button class="tab-btn" data-tab="logs"      onclick="showTab('logs')">LOGS</button>
</nav>

<!-- DASHBOARD -->
<div id="tab-dashboard" class="tab-panel">
  <div id="stats-grid" class="stats-grid"></div>
  <h2 style="margin-bottom:14px">&gt; RECENT DISPATCHES</h2>
  <div id="recent-dispatches"></div>
</div>

<!-- CHANNELS -->
<div id="tab-channels" class="tab-panel">
  <div class="section-header">
    <h2>&gt; CHANNELS</h2>
    <button class="btn" onclick="openCreateChannel()">+ NEW CHANNEL</button>
  </div>
  <div id="channels-table"></div>
</div>

<!-- RULES -->
<div id="tab-rules" class="tab-panel">
  <div class="section-header">
    <h2>&gt; RULES</h2>
    <button class="btn" onclick="openCreateRule()">+ NEW RULE</button>
  </div>
  <div id="rules-table"></div>
</div>

<!-- EVENTS -->
<div id="tab-events" class="tab-panel">
  <h2 style="margin-bottom:20px">&gt; SEND TEST EVENT</h2>
  <div style="max-width:480px">
    <div class="form-group">
      <label>Source</label>
      <input id="ev-source" type="text" value="monitor" placeholder="e.g. monitor"/>
    </div>
    <div class="form-group">
      <label>Event Type</label>
      <input id="ev-type" type="text" value="alert" placeholder="e.g. alert"/>
    </div>
    <div class="form-group">
      <label>Payload (JSON)</label>
      <textarea id="ev-payload" rows="4">{"severity": "critical", "message": "disk 95%"}</textarea>
    </div>
    <button class="btn" onclick="sendEvent()">SEND EVENT</button>
  </div>
  <div id="dispatch-result"><span style="color:#222">— result will appear here —</span></div>
  <div style="margin-top:32px">
    <h2 style="margin-bottom:14px">&gt; RECENT EVENTS</h2>
    <div id="events-table"></div>
  </div>
</div>

<!-- LOGS -->
<div id="tab-logs" class="tab-panel">
  <div class="section-header">
    <h2>&gt; AUDIT LOG</h2>
    <div class="filter-bar">
      <select id="log-status-filter" style="width:130px" onchange="refreshLogs()">
        <option value="">ALL STATUS</option>
        <option value="success">SUCCESS</option>
        <option value="failed">FAILED</option>
      </select>
      <input id="log-event-filter" type="number" placeholder="Event ID" style="width:100px" oninput="refreshLogs()"/>
      <button class="btn" onclick="refreshLogs()">REFRESH</button>
    </div>
  </div>
  <div id="logs-table"></div>
</div>

<!-- Modal -->
<div id="modal-overlay" class="hidden" onclick="handleOverlayClick(event)">
  <div id="modal">
    <div id="modal-title"></div>
    <div id="modal-body"></div>
    <div id="modal-footer">
      <button class="btn" onclick="closeModal()">CANCEL</button>
      <button class="btn" id="modal-save-btn" onclick="handleModalSave()">SAVE</button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
// ── API ────────────────────────────────────────────────────────────────────
const API = {
  async _req(url, opts = {}) {
    const r = await fetch(url, opts);
    if (r.status === 204) return null;
    const data = await r.json().catch(() => ({ detail: r.statusText }));
    if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
    return data;
  },
  get:  url        => API._req(url),
  post: (url, body) => API._req(url, { method: 'POST',   headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  put:  (url, body) => API._req(url, { method: 'PUT',    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  del:  url        => API._req(url, { method: 'DELETE' }),
};

// ── Shared state ───────────────────────────────────────────────────────────
const S = { channels: [], rules: [] };
let _modalSave = null;

// ── Utils ──────────────────────────────────────────────────────────────────
const esc = s => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function toast(msg, isErr = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = isErr ? 'err show' : 'show';
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = ''; }, 3200);
}

// ── Tabs ───────────────────────────────────────────────────────────────────
const TAB_LOADERS = {
  dashboard: loadDashboard,
  channels:  loadChannels,
  rules:     loadRules,
  events:    loadEvents,
  logs:      loadLogs,
};

function showTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  localStorage.setItem('nr-tab', name);
  TAB_LOADERS[name]?.();
}

// ── Modal ──────────────────────────────────────────────────────────────────
function openModal(title, html, onSave) {
  document.getElementById('modal-title').textContent = '> ' + title;
  document.getElementById('modal-body').innerHTML = html;
  _modalSave = onSave;
  document.getElementById('modal-overlay').classList.remove('hidden');
}
function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  _modalSave = null;
}
function handleOverlayClick(e) {
  if (e.target.id === 'modal-overlay') closeModal();
}
async function handleModalSave() {
  if (!_modalSave) return;
  const btn = document.getElementById('modal-save-btn');
  btn.disabled = true;
  btn.textContent = 'SAVING...';
  try {
    await _modalSave();
    closeModal();
  } catch (e) {
    toast(e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = 'SAVE';
  }
}

// ── Dashboard ──────────────────────────────────────────────────────────────
async function loadDashboard() {
  document.getElementById('stats-grid').innerHTML = '<p class="loading">LOADING...</p>';
  document.getElementById('recent-dispatches').innerHTML = '';
  try {
    const [channels, rules, events, logs] = await Promise.all([
      API.get('/channels'),
      API.get('/rules'),
      API.get('/events?limit=1000'),
      API.get('/logs?limit=1000'),
    ]);
    S.channels = channels;
    S.rules    = rules;

    const success = logs.filter(l => l.status === 'success').length;
    const failed  = logs.filter(l => l.status === 'failed').length;
    const rate    = logs.length > 0 ? (success / logs.length * 100).toFixed(1) + '%' : 'N/A';

    document.getElementById('stats-grid').innerHTML = `
      <div class="stat-card"><div class="label">Events</div><div class="value">${events.length}</div></div>
      <div class="stat-card"><div class="label">Dispatches</div><div class="value">${logs.length}</div></div>
      <div class="stat-card"><div class="label">Successful</div><div class="value" style="color:var(--green)">${success}</div></div>
      <div class="stat-card"><div class="label">Failed</div><div class="value" style="color:var(--red)">${failed}</div></div>
      <div class="stat-card"><div class="label">Success Rate</div><div class="value" style="color:var(--cyan)">${rate}</div></div>
      <div class="stat-card"><div class="label">Channels</div><div class="value">${channels.length}</div></div>
      <div class="stat-card"><div class="label">Rules</div><div class="value">${rules.length}</div></div>
    `;

    const recent = logs.slice(0, 10);
    document.getElementById('recent-dispatches').innerHTML =
      recent.length ? renderLogsTable(recent) : '<p class="empty">— no dispatches yet —</p>';
  } catch (e) {
    document.getElementById('stats-grid').innerHTML = `<p style="color:var(--red);padding:12px">${esc(e.message)}</p>`;
  }
}

// ── Channels ───────────────────────────────────────────────────────────────
async function loadChannels() {
  document.getElementById('channels-table').innerHTML = '<p class="loading">LOADING...</p>';
  try {
    S.channels = await API.get('/channels');
    renderChannelsTable();
  } catch (e) {
    document.getElementById('channels-table').innerHTML = `<p style="color:var(--red);padding:12px">${esc(e.message)}</p>`;
  }
}

function renderChannelsTable() {
  if (!S.channels.length) {
    document.getElementById('channels-table').innerHTML = '<p class="empty">— no channels yet —</p>';
    return;
  }
  const rows = S.channels.map(c => `
    <tr>
      <td style="color:var(--dim)">${c.id}</td>
      <td>${esc(c.name)}</td>
      <td style="color:var(--cyan)">${esc(c.type)}</td>
      <td style="color:var(--dim)">${esc(JSON.stringify(c.config))}</td>
      <td style="white-space:nowrap">
        <button class="btn sm" onclick="openEditChannel(${c.id})">EDIT</button>
        <button class="btn sm danger" style="margin-left:4px" onclick="deleteChannel(${c.id})">DEL</button>
      </td>
    </tr>`).join('');
  document.getElementById('channels-table').innerHTML = `
    <table>
      <thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Config</th><th>Actions</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function _cfgFields(type, cfg = {}) {
  const v = (k, fb = '') => esc(cfg[k] ?? fb);
  if (type === 'email') return `
    <div class="form-group"><label>To</label><input id="cfg-to" value="${v('to')}"/></div>
    <div class="form-group"><label>Subject Template</label><input id="cfg-subject_template" value="${v('subject_template', '{event_type} from {source}')}"/></div>`;
  if (type === 'telegram') return `
    <div class="form-group"><label>Bot Token</label><input id="cfg-bot_token" value="${v('bot_token')}"/></div>
    <div class="form-group"><label>Chat ID</label><input id="cfg-chat_id" value="${v('chat_id')}"/></div>`;
  if (type === 'slack') return `
    <div class="form-group"><label>Webhook URL</label><input id="cfg-webhook_url" value="${v('webhook_url')}"/></div>`;
  if (type === 'webhook') return `
    <div class="form-group"><label>URL</label><input id="cfg-url" value="${v('url')}"/></div>
    <div class="form-group"><label>Method</label>
      <select id="cfg-method">
        ${['POST','GET','PUT','PATCH','DELETE'].map(m => `<option${cfg.method === m ? ' selected' : ''}>${m}</option>`).join('')}
      </select>
    </div>
    <div class="form-group"><label>Headers (JSON object)</label>
      <textarea id="cfg-headers" rows="3">${esc(JSON.stringify(cfg.headers || {}, null, 2))}</textarea>
    </div>`;
  return '';
}

function _readCfg(type) {
  const g = id => (document.getElementById(id)?.value ?? '').trim();
  if (type === 'email')    return { to: g('cfg-to'), subject_template: g('cfg-subject_template') };
  if (type === 'telegram') return { bot_token: g('cfg-bot_token'), chat_id: g('cfg-chat_id') };
  if (type === 'slack')    return { webhook_url: g('cfg-webhook_url') };
  if (type === 'webhook')  {
    let headers = {};
    try { headers = JSON.parse(g('cfg-headers') || '{}'); } catch { throw new Error('Headers must be valid JSON'); }
    return { url: g('cfg-url'), method: g('cfg-method'), headers };
  }
  return {};
}

function _channelModalHTML(c = {}) {
  const type = c.type || 'webhook';
  return `
    <div class="form-group"><label>Name</label><input id="ch-name" value="${esc(c.name || '')}"/></div>
    <div class="form-group"><label>Type</label>
      <select id="ch-type" onchange="document.getElementById('ch-cfg').innerHTML=_cfgFields(this.value)">
        ${['email', 'telegram', 'slack', 'webhook'].map(t => `<option${type === t ? ' selected' : ''}>${t}</option>`).join('')}
      </select>
    </div>
    <div id="ch-cfg">${_cfgFields(type, c.config || {})}</div>`;
}

function openCreateChannel() {
  openModal('NEW CHANNEL', _channelModalHTML(), async () => {
    const name   = document.getElementById('ch-name').value.trim();
    const type   = document.getElementById('ch-type').value;
    const config = _readCfg(type);
    if (!name) throw new Error('Name is required');
    await API.post('/channels', { name, type, config });
    toast('Channel created');
    loadChannels();
  });
}

function openEditChannel(id) {
  const c = S.channels.find(x => x.id === id);
  if (!c) return;
  openModal('EDIT CHANNEL', _channelModalHTML(c), async () => {
    const name   = document.getElementById('ch-name').value.trim();
    const type   = document.getElementById('ch-type').value;
    const config = _readCfg(type);
    if (!name) throw new Error('Name is required');
    await API.put(`/channels/${id}`, { name, type, config });
    toast('Channel updated');
    loadChannels();
  });
}

async function deleteChannel(id) {
  if (!confirm(`Delete channel ${id}?`)) return;
  try {
    await API.del(`/channels/${id}`);
    toast('Channel deleted');
    loadChannels();
  } catch (e) { toast(e.message, true); }
}

// ── Rules ──────────────────────────────────────────────────────────────────
async function loadRules() {
  document.getElementById('rules-table').innerHTML = '<p class="loading">LOADING...</p>';
  try {
    [S.channels, S.rules] = await Promise.all([API.get('/channels'), API.get('/rules')]);
    renderRulesTable();
  } catch (e) {
    document.getElementById('rules-table').innerHTML = `<p style="color:var(--red);padding:12px">${esc(e.message)}</p>`;
  }
}

function renderRulesTable() {
  if (!S.rules.length) {
    document.getElementById('rules-table').innerHTML = '<p class="empty">— no rules yet —</p>';
    return;
  }
  const chName = id => S.channels.find(c => c.id === id)?.name ?? String(id);
  const rows = S.rules.map(r => `
    <tr>
      <td style="color:var(--dim)">${r.id}</td>
      <td>${esc(r.name)}</td>
      <td style="color:var(--dim)">${esc(r.source_filter)}</td>
      <td style="color:var(--dim)">${esc(r.event_type_filter)}</td>
      <td style="color:var(--dim)">${r.condition_key ? esc(r.condition_key) + '=' + esc(r.condition_value) : '—'}</td>
      <td style="color:var(--cyan)">${esc(chName(r.channel_id))}</td>
      <td style="color:var(--dim)">${r.priority}</td>
      <td>
        <label class="toggle" title="${r.enabled ? 'Disable' : 'Enable'}">
          <input type="checkbox" ${r.enabled ? 'checked' : ''} onchange="toggleRule(${r.id}, this.checked)"/>
          <span class="toggle-track"><span class="toggle-thumb"></span></span>
        </label>
      </td>
      <td><button class="btn sm danger" onclick="deleteRule(${r.id})">DEL</button></td>
    </tr>`).join('');
  document.getElementById('rules-table').innerHTML = `
    <table>
      <thead><tr><th>ID</th><th>Name</th><th>Source</th><th>Event Type</th><th>Condition</th><th>Channel</th><th>Pri</th><th>On</th><th></th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function _ruleModalHTML() {
  const opts = S.channels.length
    ? S.channels.map(c => `<option value="${c.id}">${esc(c.name)} (${esc(c.type)})</option>`).join('')
    : '<option disabled>No channels available</option>';
  return `
    <div class="form-group"><label>Name</label><input id="rl-name"/></div>
    <div class="form-group"><label>Source Filter  (* = any)</label><input id="rl-source" value="*"/></div>
    <div class="form-group"><label>Event Type Filter (* = any)</label><input id="rl-etype" value="*"/></div>
    <div class="form-group"><label>Condition Key (optional)</label><input id="rl-ckey" placeholder="e.g. severity"/></div>
    <div class="form-group"><label>Condition Value (required if key set)</label><input id="rl-cval" placeholder="e.g. critical"/></div>
    <div class="form-group"><label>Channel</label><select id="rl-channel">${opts}</select></div>
    <div class="form-group"><label>Priority</label><input id="rl-priority" type="number" value="0"/></div>`;
}

function openCreateRule() {
  if (!S.channels.length) { toast('Create a channel first', true); return; }
  openModal('NEW RULE', _ruleModalHTML(), async () => {
    const name  = document.getElementById('rl-name').value.trim();
    const ckey  = document.getElementById('rl-ckey').value.trim();
    const cval  = document.getElementById('rl-cval').value.trim();
    if (!name) throw new Error('Name is required');
    if (ckey && !cval) throw new Error('Condition value required when key is set');
    await API.post('/rules', {
      name,
      source_filter:     document.getElementById('rl-source').value.trim() || '*',
      event_type_filter: document.getElementById('rl-etype').value.trim()  || '*',
      condition_key:     ckey || null,
      condition_value:   ckey ? cval : null,
      channel_id:        parseInt(document.getElementById('rl-channel').value),
      priority:          parseInt(document.getElementById('rl-priority').value) || 0,
    });
    toast('Rule created');
    loadRules();
  });
}

async function toggleRule(id, enabled) {
  try {
    await API.put(`/rules/${id}`, { enabled });
    toast(enabled ? 'Rule enabled' : 'Rule disabled');
  } catch (e) {
    toast(e.message, true);
    loadRules();
  }
}

async function deleteRule(id) {
  if (!confirm(`Delete rule ${id}?`)) return;
  try {
    await API.del(`/rules/${id}`);
    toast('Rule deleted');
    loadRules();
  } catch (e) { toast(e.message, true); }
}

// ── Events ─────────────────────────────────────────────────────────────────
async function loadEvents() {
  document.getElementById('events-table').innerHTML = '<p class="loading">LOADING...</p>';
  try {
    const events = await API.get('/events');
    document.getElementById('events-table').innerHTML = events.length
      ? renderEventsTable(events)
      : '<p class="empty">— no events yet —</p>';
  } catch (e) {
    document.getElementById('events-table').innerHTML = `<p style="color:var(--red);padding:12px">${esc(e.message)}</p>`;
  }
}

function renderEventsTable(events) {
  const rows = events.map(e => `
    <tr>
      <td style="color:var(--dim)">${e.id}</td>
      <td style="color:var(--cyan)">${esc(e.source)}</td>
      <td>${esc(e.event_type)}</td>
      <td style="color:var(--dim)">${esc(JSON.stringify(e.payload))}</td>
      <td style="color:var(--dim)">${esc((e.received_at || '').replace('T', ' ').slice(0, 19))}</td>
    </tr>`).join('');
  return `<table>
    <thead><tr><th>ID</th><th>Source</th><th>Type</th><th>Payload</th><th>Received At</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

async function sendEvent() {
  const src  = document.getElementById('ev-source').value.trim();
  const type = document.getElementById('ev-type').value.trim();
  const raw  = document.getElementById('ev-payload').value.trim();
  let payload;
  try { payload = JSON.parse(raw || '{}'); } catch { toast('Invalid JSON payload', true); return; }

  const result = document.getElementById('dispatch-result');
  result.innerHTML = '<span style="color:var(--dim)">SENDING...</span>';

  try {
    const res = await API.post('/events', { source: src, event_type: type, payload });
    const dispatches = res.dispatches || [];
    const lines = dispatches.map(d => {
      const ok = d.status === 'success';
      const tag = ok ? '<span style="color:var(--green)">OK</span>' : '<span style="color:var(--red)">FAIL</span>';
      return `  [${tag}] rule=${d.rule_id} channel=${d.channel_id} (${esc(d.channel_type)}) — ${esc(d.info || '')}`;
    }).join('\\n');
    result.innerHTML =
      `<span style="color:var(--dim)">event_id=${res.event_id}  matched=${res.matched_rules}  dispatches=${dispatches.length}</span>\\n` +
      (lines || '<span style="color:#333">no rules matched</span>');
    toast(`Event ${res.event_id} dispatched`);
    loadEvents();
  } catch (e) {
    result.innerHTML = `<span style="color:var(--red)">ERROR: ${esc(e.message)}</span>`;
    toast(e.message, true);
  }
}

// ── Logs ───────────────────────────────────────────────────────────────────
async function loadLogs() {
  document.getElementById('logs-table').innerHTML = '<p class="loading">LOADING...</p>';
  await refreshLogs();
}

async function refreshLogs() {
  const status  = document.getElementById('log-status-filter')?.value || '';
  const eventId = document.getElementById('log-event-filter')?.value  || '';
  let url = '/logs?limit=200';
  if (status)  url += `&status=${encodeURIComponent(status)}`;
  if (eventId) url += `&event_id=${encodeURIComponent(eventId)}`;
  try {
    const logs = await API.get(url);
    document.getElementById('logs-table').innerHTML = logs.length
      ? renderLogsTable(logs)
      : '<p class="empty">— no log entries —</p>';
  } catch (e) {
    document.getElementById('logs-table').innerHTML = `<p style="color:var(--red);padding:12px">${esc(e.message)}</p>`;
  }
}

function renderLogsTable(logs) {
  const rows = logs.map(l => `
    <tr>
      <td style="color:var(--dim)">${l.id}</td>
      <td>${l.event_id}</td>
      <td style="color:var(--dim)">${l.rule_id}</td>
      <td style="color:var(--dim)">${l.channel_id}</td>
      <td style="color:var(--cyan)">${esc(l.channel_type)}</td>
      <td class="${l.status === 'success' ? 'ok' : 'err'}">${esc(l.status.toUpperCase())}</td>
      <td style="color:var(--dim)">${esc(l.response_info || '')}</td>
      <td style="color:var(--dim)">${esc((l.dispatched_at || '').replace('T', ' ').slice(0, 19))}</td>
    </tr>`).join('');
  return `<table>
    <thead><tr><th>ID</th><th>Event</th><th>Rule</th><th>Ch</th><th>Type</th><th>Status</th><th>Info</th><th>Time</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

// ── Clock ──────────────────────────────────────────────────────────────────
function _tick() {
  const ts = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
  document.getElementById('clock').textContent = 'multi-channel notification routing engine — ' + ts;
}
setInterval(_tick, 1000);
_tick();

// ── Init ───────────────────────────────────────────────────────────────────
showTab(localStorage.getItem('nr-tab') || 'dashboard');
</script>
</body>
</html>"""
