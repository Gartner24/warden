const BASE = '';
const counters = { BEACON_FLOOD: 0, DEAUTH: 0, EVIL_TWIN: 0, CADENA_OFENSIVA: 0 };
let totalAlerts = 0;
let ws = null;
let _detectorRunning = false;

function setThreatState(level) {
  const el = document.getElementById('threat-state');
  const label = document.getElementById('threat-label');
  const sub = document.getElementById('threat-sublabel');
  el.className = el.className.replace(/threat-\w+/, '');
  if (level === 'red') {
    el.classList.add('threat-red', 'rounded-xl', 'p-6', 'mb-6', 'flex', 'items-center', 'gap-4');
    label.textContent = 'CADENA OFENSIVA DETECTADA';
    sub.textContent = 'Ataque completo en progreso';
  } else if (level === 'yellow') {
    el.classList.add('threat-yellow', 'rounded-xl', 'p-6', 'mb-6', 'flex', 'items-center', 'gap-4');
    label.textContent = 'Amenaza parcial detectada';
    sub.textContent = 'Monitoreando fases del ataque';
  } else if (level === 'green') {
    el.classList.add('threat-green', 'rounded-xl', 'p-6', 'mb-6', 'flex', 'items-center', 'gap-4');
    label.textContent = 'Sin amenazas detectadas';
    sub.textContent = 'Monitor activo';
  } else {
    el.classList.add('threat-idle', 'rounded-xl', 'p-6', 'mb-6', 'flex', 'items-center', 'gap-4');
    label.textContent = 'Detector no iniciado';
    sub.textContent = 'Configure y pulse Iniciar';
  }
}

function recomputeThreat() {
  if (!_detectorRunning) return setThreatState('idle');
  if (counters.CADENA_OFENSIVA > 0) return setThreatState('red');
  if (counters.BEACON_FLOOD > 0 || counters.DEAUTH > 0 || counters.EVIL_TWIN > 0) return setThreatState('yellow');
  setThreatState('green');
}

function addAlert(alert) {
  const tipo = alert.tipo || 'UNKNOWN';
  const sev = alert.severidad || 'INFO';
  totalAlerts++;
  if (tipo in counters) {
    counters[tipo]++;
    const el = document.getElementById('count-' + tipo);
    if (el) el.textContent = counters[tipo];
  }
  document.getElementById('alert-total').textContent = totalAlerts + ' total';
  document.getElementById('no-alerts').style.display = 'none';
  const li = document.createElement('li');
  li.className = 'text-xs p-2 rounded bg-gray-700 border-l-2 ' +
    (sev === 'CRITICAL' ? 'border-red-500' : sev === 'ALERT' ? 'border-orange-500' : 'border-yellow-500');
  li.textContent = '[' + (alert.timestamp || '') + '] [' + sev + '] ' + tipo + ': ' + (alert.mensaje || '');
  const list = document.getElementById('alerts');
  list.insertBefore(li, list.firstChild);
  recomputeThreat();
}

function resetCounters() {
  for (const k in counters) counters[k] = 0;
  totalAlerts = 0;
  document.getElementById('alert-total').textContent = '0 total';
  document.getElementById('alerts').innerHTML = '';
  document.getElementById('no-alerts').style.display = '';
  Object.keys(counters).forEach(k => {
    const el = document.getElementById('count-' + k);
    if (el) el.textContent = '0';
  });
  recomputeThreat();
}

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(proto + '://' + location.host + '/ws');
  ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    const ALERT_TIPOS = new Set(['BEACON_FLOOD', 'DEAUTH', 'EVIL_TWIN', 'CADENA_OFENSIVA']);
    if (msg.tipo === 'alerta' || ALERT_TIPOS.has(msg.tipo)) addAlert(msg);
    else if (msg.tipo === 'session_reset') resetCounters();
    else if (msg.tipo === 'detector_status') {
      const running = msg.estado === 'corriendo';
      _detectorRunning = running;
      const chip = document.getElementById('detector-status');
      chip.textContent = running ? 'Activo' : 'Inactivo';
      chip.className = 'px-3 py-1 rounded-full text-sm font-medium ' +
        (running ? 'bg-green-700 text-white' : 'bg-gray-700 text-gray-300');
      recomputeThreat();
    } else if (msg.tipo === 'init' && msg.alertas_recientes) {
      msg.alertas_recientes.forEach(addAlert);
    }
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}

async function startDetector() {
  const bssid = document.getElementById('input-bssid').value.trim();
  const ssid = document.getElementById('input-ssid').value.trim();
  const errEl = document.getElementById('detector-error');
  const okEl = document.getElementById('detector-success');
  errEl.classList.add('hidden');
  okEl.classList.add('hidden');

  if (!bssid || !ssid) {
    errEl.textContent = 'Complete el BSSID y el SSID antes de iniciar.';
    errEl.classList.remove('hidden');
    return;
  }
  if (!/^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/.test(bssid)) {
    errEl.textContent = 'Formato de BSSID invalido. Ejemplo: E4:AB:89:D6:9B:80';
    errEl.classList.remove('hidden');
    return;
  }

  const canal = parseInt(document.getElementById('input-channel').value) || 6;
  const r = await fetch(BASE + '/api/detector/start', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ bssid_protegido: bssid, ssid_protegido: ssid, canal }),
  });
  const data = await r.json();
  if (!data.ok) {
    errEl.textContent = 'Error al iniciar: ' + (data.error || JSON.stringify(data));
    errEl.classList.remove('hidden');
  } else {
    okEl.textContent = 'Monitoreando ' + ssid + ' (' + bssid + ')';
    okEl.classList.remove('hidden');
  }
}

async function stopDetector() {
  await fetch(BASE + '/api/detector/stop', { method: 'POST' });
}

async function resetSession() {
  await fetch(BASE + '/api/session/reset', { method: 'POST' });
}

async function refreshIfaceStatus() {
  const badge = document.getElementById('iface-mode-badge');
  try {
    const r = await fetch(BASE + '/api/interface/status');
    const data = await r.json();
    const mode = data.mode || 'unknown';
    const ch = data.channel ? ' ch ' + data.channel : '';
    if (mode === 'monitor') {
      badge.textContent = 'monitor' + ch;
      badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-blue-700 text-white';
    } else if (mode === 'managed') {
      badge.textContent = 'normal (managed)';
      badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-gray-700 text-gray-300';
    } else {
      badge.textContent = mode + ch;
      badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-yellow-800 text-yellow-300';
    }
  } catch {
    badge.textContent = 'no disponible';
    badge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-red-900 text-red-300';
  }
}

async function setMonitorMode() {
  const errEl = document.getElementById('iface-error');
  errEl.classList.add('hidden');
  const channel = parseInt(document.getElementById('input-channel').value) || 6;
  const r = await fetch(BASE + '/api/interface/monitor', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ canal: channel }),
  });
  const data = await r.json();
  if (!data.ok) {
    errEl.textContent = 'Error: ' + (data.error || JSON.stringify(data));
    errEl.classList.remove('hidden');
  }
  await refreshIfaceStatus();
}

async function setManagedMode() {
  const errEl = document.getElementById('iface-error');
  errEl.classList.add('hidden');
  const r = await fetch(BASE + '/api/interface/managed', { method: 'POST' });
  const data = await r.json();
  if (!data.ok) {
    errEl.textContent = 'Error: ' + (data.error || JSON.stringify(data));
    errEl.classList.remove('hidden');
  }
  await refreshIfaceStatus();
}

document.addEventListener('DOMContentLoaded', () => {
  connectWS();
  refreshIfaceStatus();
  setInterval(refreshIfaceStatus, 5000);
});
