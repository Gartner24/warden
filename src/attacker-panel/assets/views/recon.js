let _clientPollTimer = null;
let _pollBssid = null;
let _scanStartMs = null;

function renderRecon() {
  const el = document.getElementById('view-recon');
  el.innerHTML = `
    <h2 class="text-xl font-bold mb-4">Reconocimiento</h2>
    <button id="btn-scan" onclick="doScan()"
      class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg mb-4">
      Escanear Redes
    </button>
    <div id="scan-status" class="text-sm text-gray-400 mb-4"></div>
    <div id="network-table"></div>
    <div id="client-table" class="mt-6"></div>
  `;
}

async function doScan() {
  document.getElementById('scan-status').textContent = 'Escaneando...';
  document.getElementById('btn-scan').disabled = true;
  try {
    const data = await api.scan();
    document.getElementById('scan-status').textContent =
      `${data.redes_encontradas || 0} redes encontradas — haga clic en una fila para seleccionarla`;
    renderNetworkTable(data.redes || []);
  } catch(e) {
    document.getElementById('scan-status').textContent = 'Error: ' + e.message;
  } finally {
    document.getElementById('btn-scan').disabled = false;
  }
}

function renderNetworkTable(redes) {
  const el = document.getElementById('network-table');
  if (!redes.length) { el.innerHTML = '<p class="text-gray-500 text-sm">Sin redes.</p>'; return; }
  const selected = state.get('selectedNetwork');
  const rows = redes.map((r, i) => {
    const isSel = selected && selected.bssid_objetivo === r.bssid_objetivo;
    return `
    <tr class="hover:bg-gray-700 cursor-pointer transition-colors ${isSel ? 'bg-blue-900' : ''}"
        onclick="selectNetwork(${i})" id="net-row-${i}">
      <td class="px-3 py-2">
        ${r.ssid_objetivo || ''}
        ${isSel ? '<span class="ml-2 text-xs bg-blue-600 text-white px-1 rounded">&#10003; Seleccionada</span>' : ''}
      </td>
      <td class="px-3 py-2 font-mono text-xs">${r.bssid_objetivo || ''}</td>
      <td class="px-3 py-2">${r.canal || ''}</td>
      <td class="px-3 py-2">${r.rssi_dbm || ''}dBm</td>
      <td class="px-3 py-2">${r.cifrado || ''}</td>
    </tr>`;
  }).join('');
  el.innerHTML = `
    <table class="w-full text-sm bg-gray-800 rounded-lg overflow-hidden">
      <thead class="bg-gray-700">
        <tr>
          <th class="px-3 py-2 text-left">SSID</th>
          <th class="px-3 py-2 text-left">BSSID</th>
          <th class="px-3 py-2 text-left">Canal</th>
          <th class="px-3 py-2 text-left">RSSI</th>
          <th class="px-3 py-2 text-left">Cifrado</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
  window._recon_redes = redes;
}

async function selectNetwork(idx) {
  const red = window._recon_redes[idx];
  const prevSelected = state.get('selectedNetwork');
  const sameBssid = prevSelected && prevSelected.bssid_objetivo === red.bssid_objetivo;

  state.set('selectedNetwork', red);
  state.set('selectedVictim', null);
  document.getElementById('scan-status').textContent =
    `Seleccionada: ${red.ssid_objetivo} (${red.bssid_objetivo}) — continuar en Etica`;
  renderNetworkTable(window._recon_redes);

  if (sameBssid) {
    const byBssid = state.get('clientsByBssid') || {};
    renderClientTable(Object.values(byBssid[red.bssid_objetivo] || {}), _clientPollTimer !== null);
    return;
  }

  try { await api.clientsStop(); } catch(e) {}
  const byBssid = state.get('clientsByBssid') || {};
  byBssid[red.bssid_objetivo] = {};
  state.set('clientsByBssid', byBssid);

  _startClientPoll(red.bssid_objetivo, red.canal);
}

function _startClientPoll(bssid, canal) {
  _stopClientPoll();
  _pollBssid = bssid;
  _scanStartMs = Date.now();
  const clientEl = document.getElementById('client-table');
  if (clientEl) {
    clientEl.innerHTML = '<p class="text-gray-400 text-sm">Iniciando escaneo de clientes... 0/15s</p>';
  }

  api.clients(bssid, canal).catch(() => {});

  _clientPollTimer = setInterval(async () => {
    if (_pollBssid !== bssid) return;
    try {
      const data = await api.clientsResult();
      const scanning = data.scanning !== false;
      const elapsed = data.elapsed_ms != null
        ? Math.round(data.elapsed_ms / 1000)
        : Math.round((Date.now() - _scanStartMs) / 1000);
      const timeout = data.scan_timeout_ms != null
        ? Math.round(data.scan_timeout_ms / 1000)
        : 15;
      const incoming = data.clientes || [];
      const byBssid = state.get('clientsByBssid') || {};
      const map = byBssid[bssid] || {};
      incoming.forEach(c => {
        if (!map[c.mac]) map[c.mac] = c;
        else map[c.mac].frames_observados = c.frames_observados;
      });
      byBssid[bssid] = map;
      state.set('clientsByBssid', byBssid);
      const sel = state.get('selectedNetwork');
      if (sel && sel.bssid_objetivo === bssid) {
        renderClientTable(Object.values(map), scanning, elapsed, timeout);
      }
      if (!scanning) _stopClientPoll();
    } catch(e) {}
  }, 1500);
}

function _stopClientPoll() {
  if (_clientPollTimer) {
    clearInterval(_clientPollTimer);
    _clientPollTimer = null;
  }
  _pollBssid = null;
}

function stopReconScan() {
  _stopClientPoll();
  api.clientsStop().catch(() => {});
}

function renderClientTable(clientes, scanning = true, elapsed = 0, timeout = 15) {
  const el = document.getElementById('client-table');
  const rescanBtn = `<button onclick="rescanClients()" class="ml-2 px-2 py-0.5 bg-gray-600 hover:bg-gray-700 rounded text-xs font-normal">Re-escanear</button>`;

  if (!clientes.length) {
    if (scanning) {
      el.innerHTML = `<p class="text-gray-400 text-sm mt-2">Buscando clientes... ${elapsed}/${timeout}s</p>`;
    } else {
      el.innerHTML = `<div class="mt-2">
        <p class="text-gray-500 text-sm">Sin clientes detectados — los clientes inactivos no emiten tramas.</p>
        ${rescanBtn}
      </div>`;
    }
    return;
  }

  const statusText = scanning
    ? `<span class="text-yellow-400">buscando... ${elapsed}/${timeout}s</span>`
    : `<span class="text-green-400">escaneo completo</span>${rescanBtn}`;

  const selectedVictim = state.get('selectedVictim');
  const rows = clientes.map(c => {
    const isSel = selectedVictim && selectedVictim === c.mac;
    return `
    <tr class="hover:bg-gray-700 cursor-pointer transition-colors ${isSel ? 'bg-green-900' : ''}"
        onclick="selectVictim('${c.mac}')">
      <td class="px-3 py-2 font-mono text-xs">
        ${c.mac || ''}
        ${isSel ? '<span class="ml-2 text-xs bg-green-600 text-white px-1 rounded">&#10003; Victima</span>' : ''}
      </td>
      <td class="px-3 py-2">${c.frames_observados || 0}</td>
      <td class="px-3 py-2 text-xs text-gray-400" id="oui-${c.mac}">...</td>
    </tr>`;
  }).join('');

  el.innerHTML = `
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-semibold">Clientes asociados
        <span class="text-xs text-gray-400 font-normal ml-1">${clientes.length} detectados — ${statusText}</span>
      </h3>
      <span class="text-xs text-gray-400">Haga clic para seleccionar victima</span>
    </div>
    <table class="w-full text-sm bg-gray-800 rounded-lg overflow-hidden">
      <thead class="bg-gray-700">
        <tr>
          <th class="px-3 py-2 text-left">MAC</th>
          <th class="px-3 py-2 text-left">Frames</th>
          <th class="px-3 py-2 text-left">Fabricante</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
  window._recon_clientes = clientes;
  clientes.forEach((c, i) => setTimeout(() => lookupOui(c.mac), i * 1100));
}

async function rescanClients() {
  const sel = state.get('selectedNetwork');
  if (!sel) return;
  try { await api.clientsStop(); } catch(e) {}
  const byBssid = state.get('clientsByBssid') || {};
  byBssid[sel.bssid_objetivo] = {};
  state.set('clientsByBssid', byBssid);
  _startClientPoll(sel.bssid_objetivo, sel.canal);
}

function selectVictim(mac) {
  state.set('selectedVictim', mac);
  renderClientTable(window._recon_clientes);
  document.getElementById('scan-status').textContent =
    'Victima: ' + mac + ' — continue en Etica';
}

async function lookupOui(mac) {
  const el = document.getElementById('oui-' + mac);
  if (!el) return;
  const vendor = await api.ouiLookupCached(mac);
  el.textContent = vendor;
}
