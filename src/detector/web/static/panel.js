const BASE = '';
const counters = { BEACON_FLOOD: 0, DEAUTH: 0, EVIL_TWIN: 0, CADENA_OFENSIVA: 0 };
let totalAlerts = 0;
let ws = null;

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
  } else {
    el.classList.add('threat-green', 'rounded-xl', 'p-6', 'mb-6', 'flex', 'items-center', 'gap-4');
    label.textContent = 'Sin amenazas detectadas';
    sub.textContent = 'Monitor activo';
  }
}

function recomputeThreat() {
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
  setThreatState('green');
}

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(proto + '://' + location.host + '/ws');
  ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch { return; }
    if (msg.tipo === 'alerta') addAlert(msg);
    else if (msg.tipo === 'session_reset') resetCounters();
    else if (msg.tipo === 'detector_status') {
      const chip = document.getElementById('detector-status');
      chip.textContent = msg.estado === 'corriendo' ? 'Corriendo' : 'Detenido';
      chip.className = chip.className.replace(/bg-\w+-\d+/, msg.estado === 'corriendo' ? 'bg-green-700' : 'bg-gray-700');
    } else if (msg.tipo === 'init' && msg.alertas_recientes) {
      msg.alertas_recientes.forEach(addAlert);
    }
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}

async function startDetector() {
  const bssid = prompt('BSSID protegido (ej. AA:BB:CC:DD:EE:FF):');
  const ssid = prompt('SSID protegido (ej. LAB_WARDEN_UTP):');
  if (!bssid || !ssid) return;
  const r = await fetch(BASE + '/api/detector/start', {
    method: 'POST',
    headers: {'content-type': 'application/json'},
    body: JSON.stringify({ bssid_protegido: bssid, ssid_protegido: ssid }),
  });
  const data = await r.json();
  if (!data.ok) alert('Error: ' + (data.error || JSON.stringify(data)));
}

async function stopDetector() {
  await fetch(BASE + '/api/detector/stop', { method: 'POST' });
}

async function resetSession() {
  await fetch(BASE + '/api/session/reset', { method: 'POST' });
}

document.addEventListener('DOMContentLoaded', connectWS);
