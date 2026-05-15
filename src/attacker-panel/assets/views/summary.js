function renderSummary() {
  const el = document.getElementById('view-summary');
  el.innerHTML = `
    <div class="max-w-xl">
      <h2 class="text-xl font-bold mb-6">Resumen de Sesion</h2>
      <div id="summary-content" class="bg-gray-800 rounded-xl p-6 mb-6">
        <p class="text-gray-400">Cargando...</p>
      </div>
      <div class="flex gap-3">
        <button onclick="newSession()" class="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg">
          Nueva Sesion
        </button>
        <button onclick="exportSession()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg">
          Exportar JSON
        </button>
      </div>
    </div>`;

  loadSummary();
}

async function loadSummary(attempt = 0) {
  const cachedCnt = state.get('lastSessionCounters');
  const cachedCreds = state.get('lastSessionCreds');

  let cnt, creds;

  if (cachedCnt && attempt === 0) {
    cnt = cachedCnt;
    creds = cachedCreds || [];
  } else {
    try {
      const [statusData, credData] = await Promise.all([api.status(), api.credentials()]);
      cnt = statusData.contadores || {};
      creds = credData.credenciales || [];
    } catch(e) {
      if (attempt < 4) {
        const el = document.getElementById('summary-content');
        if (el) el.innerHTML = `<p class="text-gray-400 text-sm">Conectando con ESP32... (${attempt + 1}/4)</p>`;
        setTimeout(() => loadSummary(attempt + 1), 1500);
        return;
      }
      const el = document.getElementById('summary-content');
      if (el) el.innerHTML = `
        <p class="text-red-400 text-sm mb-3">No se pudo cargar el resumen. Verifica conexion con el ESP32.</p>
        <button onclick="loadSummary(0)" class="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm">Reintentar</button>`;
      return;
    }
  }

  const startMs = state.get('startTimeMs') ?? Number(localStorage.getItem('warden.startTimeMs') ?? 0) || null;
  const durationSeg = startMs ? Math.round((Date.now() - startMs) / 1000) : 0;

  document.getElementById('summary-content').innerHTML = `
    <div class="space-y-3 text-sm">
      <div class="flex justify-between"><span class="text-gray-400">Duracion total:</span><span>${durationSeg}s</span></div>
      <div class="flex justify-between"><span class="text-gray-400">Beacons emitidos:</span><span class="text-yellow-400">${cnt.beacons_emitidos || 0}</span></div>
      <div class="flex justify-between"><span class="text-gray-400">Deauths emitidos:</span><span class="text-orange-400">${cnt.deauths_emitidos || 0}</span></div>
      <div class="flex justify-between"><span class="text-gray-400">Clientes Evil Twin:</span><span class="text-blue-400">${cnt.clientes_evil_twin || 0}</span></div>
      <div class="flex justify-between"><span class="text-gray-400">Credenciales:</span><span class="text-green-400">${creds.length}</span></div>
      ${creds.length > 0 ? '<hr class="border-gray-600"/><p class="font-semibold mt-2">Credenciales capturadas:</p>' +
        creds.map(c => `<div class="font-mono bg-gray-700 rounded p-2 mt-1">${c.usuario} / ${c.password}</div>`).join('') : ''}
    </div>`;
}

function newSession() {
  state.reset();
  localStorage.removeItem('warden.startTimeMs');
  showView('recon');
}

function exportSession() {
  const data = {
    exportedAt: new Date().toISOString(),
    selectedNetwork: state.get('selectedNetwork'),
    attackPhase: state.get('attackPhase'),
    startTimeMs: state.get('startTimeMs'),
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `session-${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
