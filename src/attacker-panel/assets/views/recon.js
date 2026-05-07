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
      <td class="px-3 py-2 text-xs text-gray-400">${r.fabricante || ''}</td>
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
          <th class="px-3 py-2 text-left">Fabricante</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
  window._recon_redes = redes;
}

async function selectNetwork(idx) {
  const red = window._recon_redes[idx];
  state.set('selectedNetwork', red);
  state.set('selectedVictim', null);
  document.getElementById('scan-status').textContent =
    `Seleccionada: ${red.ssid_objetivo} (${red.bssid_objetivo}) — continuar en Etica`;
  renderNetworkTable(window._recon_redes);

  const clientEl = document.getElementById('client-table');
  clientEl.innerHTML = '<p class="text-gray-400 text-sm">Iniciando escaneo de clientes (~7 s)...</p>';

  // Kick off async scan — connection may drop briefly while ESP32 switches channel
  try {
    await api.clients(red.bssid_objetivo);
  } catch(e) { /* expected: connection resets while ESP32 sniffs */ }

  // Poll until scanning:false
  clientEl.innerHTML = '<p class="text-gray-400 text-sm">Escaneando clientes... (la conexion puede recuperarse en unos segundos)</p>';
  for (let attempt = 0; attempt < 15; attempt++) {
    await new Promise(r => setTimeout(r, 1500));
    try {
      const data = await api.clientsResult();
      if (!data.scanning) {
        renderClientTable(data.clientes || []);
        return;
      }
    } catch(e) { /* AP may still be recovering */ }
  }
  clientEl.innerHTML = '<p class="text-gray-500 text-sm">No se detectaron clientes. Intente de nuevo.</p>';
}

function renderClientTable(clientes) {
  const el = document.getElementById('client-table');
  if (!clientes.length) {
    el.innerHTML = '<p class="text-gray-500 text-sm mt-2">Sin clientes detectados en este momento.</p>';
    return;
  }
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
      <h3 class="font-semibold">Clientes asociados</h3>
      <span class="text-xs text-gray-400">Haga clic en un cliente para seleccionarlo como victima del deauth</span>
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
  clientes.forEach(c => lookupOui(c.mac));
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
  try {
    const data = await api.ouiLookup(mac);
    el.textContent = data.fabricante || 'Desconocido';
  } catch(e) { el.textContent = 'Error'; }
}
