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

async function loadSummary() {
  try {
    const [statusData, credData] = await Promise.all([api.attackStatus(), api.credentials()]);
    const cnt = statusData.contadores || {};
    const creds = credData.credenciales || [];
    const startMs = state.get('startTimeMs');
    const durationSeg = startMs ? Math.round((Date.now() - startMs) / 1000) : 0;

    document.getElementById('summary-content').innerHTML = `
      <div class="space-y-3 text-sm">
        <div class="flex justify-between"><span class="text-gray-400">Duracion total:</span><span>${durationSeg}s</span></div>
        <div class="flex justify-between"><span class="text-gray-400">Beacons emitidos:</span><span class="text-yellow-400">${cnt.beacons_emitidos || 0}</span></div>
        <div class="flex justify-between"><span class="text-gray-400">Deauths emitidos:</span><span class="text-orange-400">${cnt.deauths_emitidos || 0}</span></div>
        <div class="flex justify-between"><span class="text-gray-400">Clientes Evil Twin:</span><span class="text-blue-400">${cnt.clientes_evil_twin || 0}</span></div>
        <div class="flex justify-between"><span class="text-gray-400">Credenciales:</span><span class="text-green-400">${creds.length}</span></div>
        ${creds.length > 0 ? '<hr class="border-gray-600"/><p class="font-semibold">Credenciales:</p>' +
          creds.map(c => `<div class="font-mono bg-gray-700 rounded p-2">${c.usuario} / ${c.password}</div>`).join('') : ''}
      </div>`;
  } catch(e) {
    document.getElementById('summary-content').innerHTML = '<p class="text-red-400">Error cargando resumen.</p>';
  }
}

function newSession() {
  state.reset();
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
