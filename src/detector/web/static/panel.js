const BASE = '';
const counters = { BEACON_FLOOD: 0, DEAUTH: 0, EVIL_TWIN: 0, CADENA_OFENSIVA: 0 };
let totalAlerts = 0;
let ws = null;
let _detectorRunning = false;
let _networkPollInterval = null;

function toggleAdvanced() {
  const el = document.getElementById('advanced-inputs');
  el.classList.toggle('hidden');
}

async function refreshNetworks() {
  try {
    const resp = await fetch('/api/networks');
    const data = await resp.json();
    populateNetworkSelect(data.networks || []);
  } catch(e) {
    document.getElementById('network-scan-status').textContent = 'Error al obtener redes.';
  }
}

function populateNetworkSelect(networks) {
  const sel = document.getElementById('input-network');
  const current = sel.value;
  sel.innerHTML = networks.length
    ? '<option value="">-- Seleccione una red --</option>'
    : '<option value="">-- Sin redes detectadas aun --</option>';
  networks.forEach(n => {
    const opt = document.createElement('option');
    opt.value = n.bssid;
    opt.dataset.ssid = n.ssid || '';
    opt.dataset.channel = n.channel || '';
    opt.textContent = `${n.ssid || '(oculta)'} (${n.bssid}) — ch${n.channel || '?'}, ${n.rssi != null ? n.rssi + ' dBm' : '?'}`;
    sel.appendChild(opt);
  });
  // Restore selection if still available
  if (current && [...sel.options].some(o => o.value === current)) {
    sel.value = current;
  }
  const status = document.getElementById('network-scan-status');
  status.textContent = networks.length ? `${networks.length} redes detectadas` : '';
}

async function refreshScannerStatus() {
  const el = document.getElementById('scanner-state');
  if (!el) return;
  try {
    const r = await fetch(BASE + '/api/scanner/status');
    const data = await r.json();
    const sc = data.scanner || {};
    if (sc.last_error) {
      el.innerHTML = `<span class="text-red-400">Error de captura: ${sc.last_error}</span>`;
      return;
    }
    if (!sc.running) {
      el.textContent = 'Escaner detenido';
      return;
    }
    const line = `Escaner: corriendo en ${sc.iface}, ${sc.packets_seen} paquetes, ${data.networks_count} redes`;
    el.textContent = line;
  } catch (e) {
    // ignore fetch errors — non-critical status
  }
}

function startNetworkPolling() {
  stopNetworkPolling();
  refreshNetworks();
  refreshScannerStatus();
  _networkPollInterval = setInterval(() => { refreshNetworks(); refreshScannerStatus(); }, 2000);
}

function stopNetworkPolling() {
  if (_networkPollInterval) {
    clearInterval(_networkPollInterval);
    _networkPollInterval = null;
  }
  const el = document.getElementById('scanner-state');
  if (el) el.textContent = '';
}

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
    } else if (msg.tipo === 'diag') {
      updateDiagPanel(msg);
    }
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}

async function startDetector() {
  // If dropdown has a selection, use it to fill manual inputs
  const sel = document.getElementById('input-network');
  if (sel && sel.value) {
    const selectedOpt = sel.options[sel.selectedIndex];
    document.getElementById('input-bssid').value = sel.value;
    document.getElementById('input-ssid').value = selectedOpt.dataset.ssid || '';
  }
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
    okEl.textContent = 'Monitoreando ' + ssid + ' (' + bssid + ') — ch' + canal;
    okEl.classList.remove('hidden');
    // Mark running immediately so refreshIfaceStatus won't restart the hopper
    _detectorRunning = true;
    // Stop scanning/hopping — card is now locked to target channel
    stopNetworkPolling();
    document.getElementById('input-network').disabled = true;
    // Update badge immediately to show locked channel
    await refreshIfaceStatus();
  }
}

async function stopDetector() {
  await fetch(BASE + '/api/detector/stop', { method: 'POST' });
  document.getElementById('input-network').disabled = false;
  document.getElementById('detector-success').classList.add('hidden');
  // Restart scanner so dropdown repopulates and hopping resumes
  const sr = await fetch(BASE + '/api/scanner/start', { method: 'POST' });
  if ((await sr.json()).ok) startNetworkPolling();
}

async function resetSession() {
  await fetch(BASE + '/api/session/reset', { method: 'POST' });
  resetCounters(); // reset UI immediately, don't depend on WS round-trip
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
      if (!_networkPollInterval && !_detectorRunning) {
        await fetch(BASE + '/api/scanner/start', { method: 'POST' });
        startNetworkPolling();
      }
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
  } else {
    startNetworkPolling();
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
  } else {
    stopNetworkPolling();
    populateNetworkSelect([]);
  }
  await refreshIfaceStatus();
}

function updateDiagPanel(data) {
  const el = document.getElementById('detector-activity');
  if (!el) return;
  el.innerHTML = `<table class="w-full text-xs text-gray-400 mt-2">
    <tr><th class="text-left">Detector</th><th class="text-right">Observados</th><th class="text-right">Info</th></tr>
    <tr><td>Beacon Flood</td><td class="text-right">${data.beacon_flood?.observed_total ?? 0}</td><td class="text-right">-</td></tr>
    <tr><td>Deauth</td><td class="text-right">${data.deauth?.observed_total ?? 0}</td><td class="text-right">drop:${data.deauth?.dropped_wrong_bssid ?? 0}</td></tr>
    <tr><td>Evil Twin</td><td class="text-right">${data.evil_twin?.observed_total ?? 0}</td><td class="text-right">-</td></tr>
    <tr><td>Correlador</td><td class="text-right">-</td><td class="text-right">${(data.correlator?.timestamps_seen ?? []).join(', ') || '-'}</td></tr>
  </table>`;
}

document.addEventListener('DOMContentLoaded', () => {
  connectWS();
  refreshIfaceStatus();
  setInterval(refreshIfaceStatus, 5000);
});
