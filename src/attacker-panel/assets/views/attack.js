let _attackPollInterval = null;

function renderAttack() {
  const el = document.getElementById('view-attack');
  el.innerHTML = `
    <div class="max-w-2xl">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold">Ataque en Progreso</h2>
        <button onclick="stopAttack()"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-bold">
          DETENER
        </button>
      </div>
      <div class="bg-gray-800 rounded-xl p-6 mb-6">
        <div class="text-4xl font-bold text-center mb-2" id="attack-phase">INICIANDO</div>
        <div class="text-sm text-center text-gray-400" id="attack-timer">00:00</div>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-gray-800 rounded-lg p-3 text-center">
          <div id="cnt-beacons" class="text-2xl font-bold text-yellow-400">0</div>
          <div class="text-xs text-gray-400">Beacons</div>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 text-center">
          <div id="cnt-deauths" class="text-2xl font-bold text-orange-400">0</div>
          <div class="text-xs text-gray-400">Deauths</div>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 text-center">
          <div id="cnt-clients" class="text-2xl font-bold text-blue-400">0</div>
          <div class="text-xs text-gray-400">Clientes ET</div>
        </div>
        <div class="bg-gray-800 rounded-lg p-3 text-center">
          <div id="cnt-creds" class="text-2xl font-bold text-green-400">0</div>
          <div class="text-xs text-gray-400">Credenciales</div>
        </div>
      </div>
      <div class="bg-gray-800 rounded-xl p-4">
        <h3 class="font-semibold mb-3">Credenciales Capturadas</h3>
        <ul id="cred-list" class="space-y-2 text-sm font-mono"></ul>
        <p id="no-creds" class="text-gray-500 text-sm">Sin credenciales aun.</p>
      </div>
    </div>`;

  // Start attack + poll
  api.attackStart({ modo: 'cadena_automatica' });
  if (_attackPollInterval) clearInterval(_attackPollInterval);
  _attackPollInterval = setInterval(pollAttackStatus, 1000);
}

async function pollAttackStatus() {
  try {
    const data = await api.attackStatus();
    const fase = data.estado_cadena || 'IDLE';
    document.getElementById('attack-phase').textContent = fase;
    const elapsed = data.tiempo_transcurrido_seg || 0;
    const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const ss = String(elapsed % 60).padStart(2, '0');
    document.getElementById('attack-timer').textContent = `${mm}:${ss}`;

    const cnt = data.contadores || {};
    document.getElementById('cnt-beacons').textContent = cnt.beacons_emitidos || 0;
    document.getElementById('cnt-deauths').textContent = cnt.deauths_emitidos || 0;
    document.getElementById('cnt-clients').textContent = cnt.clientes_evil_twin || 0;
    document.getElementById('cnt-creds').textContent = cnt.credenciales_capturadas || 0;

    // Fetch credentials periodically
    if ((cnt.credenciales_capturadas || 0) > 0) {
      const cdata = await api.credentials();
      renderCredentials(cdata.credenciales || []);
    }

    if (fase === 'FINALIZADO') {
      clearInterval(_attackPollInterval);
      _attackPollInterval = null;
      setTimeout(() => showView('summary'), 1000);
    }
  } catch(e) {}
}

function renderCredentials(creds) {
  const list = document.getElementById('cred-list');
  const none = document.getElementById('no-creds');
  if (!creds.length) return;
  none.style.display = 'none';
  list.innerHTML = creds.map(c =>
    `<li class="bg-gray-700 rounded p-2">${c.usuario} / ${c.password} <span class="text-gray-400">(${c.cliente_ip})</span></li>`
  ).join('');
}

async function stopAttack() {
  clearInterval(_attackPollInterval);
  _attackPollInterval = null;
  await api.attackStop();
  showView('summary');
}
