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
      `${data.redes_encontradas || 0} redes encontradas`;
    const redes = data.redes || [];
    renderNetworkTable(redes);
  } catch(e) {
    document.getElementById('scan-status').textContent = 'Error: ' + e.message;
  } finally {
    document.getElementById('btn-scan').disabled = false;
  }
}

function renderNetworkTable(redes) {
  const el = document.getElementById('network-table');
  if (!redes.length) { el.innerHTML = '<p class="text-gray-500 text-sm">Sin redes.</p>'; return; }
  let rows = redes.map((r, i) => `
    <tr class="hover:bg-gray-700 cursor-pointer" onclick="selectNetwork(${i})">
      <td class="px-3 py-2">${r.ssid_objetivo || ''}</td>
      <td class="px-3 py-2 font-mono text-xs">${r.bssid_objetivo || ''}</td>
      <td class="px-3 py-2">${r.canal || ''}</td>
      <td class="px-3 py-2">${r.rssi_dbm || ''}dBm</td>
      <td class="px-3 py-2">${r.cifrado || ''}</td>
      <td class="px-3 py-2 text-xs text-gray-400">${r.fabricante || ''}</td>
    </tr>`).join('');
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
  document.getElementById('scan-status').textContent =
    `Seleccionado: ${red.ssid_objetivo} (${red.bssid_objetivo})`;
  // Probe clients
  try {
    const data = await api.clients(red.bssid_objetivo);
    renderClientTable(data.clientes || []);
  } catch(e) {}
}

function renderClientTable(clientes) {
  const el = document.getElementById('client-table');
  if (!clientes.length) { el.innerHTML = '<p class="text-gray-500 text-sm">Sin clientes detectados.</p>'; return; }
  let rows = clientes.map(c => `
    <tr>
      <td class="px-3 py-2 font-mono text-xs">${c.mac || ''}</td>
      <td class="px-3 py-2">${c.frames_observados || 0}</td>
      <td class="px-3 py-2 text-xs" id="oui-${c.mac}">
        <button onclick="lookupOui('${c.mac}')" class="text-blue-400 hover:text-blue-300">Lookup</button>
      </td>
    </tr>`).join('');
  el.innerHTML = `
    <h3 class="font-semibold mb-2">Clientes</h3>
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
}

async function lookupOui(mac) {
  const el = document.getElementById('oui-' + mac);
  if (!el) return;
  try {
    const data = await api.ouiLookup(mac);
    el.textContent = data.fabricante || 'Desconocido';
  } catch(e) { el.textContent = 'Error'; }
}
