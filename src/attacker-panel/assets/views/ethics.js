function renderEthics() {
  const net = state.get('selectedNetwork');
  const el = document.getElementById('view-ethics');
  if (!net) {
    el.innerHTML = `<div class="bg-yellow-900 border border-yellow-600 rounded-lg p-4">
      <p class="text-yellow-300">Seleccione una red en la vista de Reconocimiento primero.</p>
    </div>`;
    return;
  }
  el.innerHTML = `
    <div class="max-w-xl">
      <div class="bg-red-950 border border-red-700 rounded-lg p-4 mb-6">
        <h3 class="font-bold text-red-400 mb-2">ADVERTENCIA ETICA</h3>
        <p class="text-sm text-gray-300">Este sistema es exclusivamente para uso en laboratorio autorizado.
        El uso no autorizado contra redes reales constituye un delito. Confirme que tiene autorizacion
        expresa del propietario de la red objetivo.</p>
      </div>
      <div class="bg-gray-800 rounded-lg p-4 mb-6">
        <p class="text-sm text-gray-400 mb-1">Red seleccionada:</p>
        <p class="font-mono">${net.ssid_objetivo} / ${net.bssid_objetivo}</p>
        <p class="text-sm text-gray-400">Canal ${net.canal} &bull; ${net.cifrado}</p>
        ${state.get('selectedVictim')
          ? `<p class="text-sm text-green-400 mt-2">Victima: <span class="font-mono">${state.get('selectedVictim')}</span></p>`
          : `<div class="mt-2">
    <p class="text-sm text-yellow-400 mb-2">Sin victima seleccionada — elija un cliente en Reconocimiento o ingrese el MAC manualmente:</p>
    <div class="flex gap-2">
      <input id="manual-victim-input" type="text"
        placeholder="AA:BB:CC:DD:EE:FF"
        pattern="^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
        class="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm font-mono text-white"
        oninput="validateManualVictim()" />
      <button id="btn-set-victim" onclick="setManualVictim()" disabled
        class="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed">
        Usar este MAC
      </button>
    </div>
    <p id="manual-victim-error" class="text-xs text-red-400 mt-1 hidden">MAC invalido. Formato: AA:BB:CC:DD:EE:FF</p>
  </div>`
        }
      </div>
      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-2">
          Escriba <strong class="text-white">confirm</strong> para autorizar:
        </label>
        <input id="confirm-input" type="text" placeholder="confirm"
          class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          oninput="checkConfirm()" />
      </div>
      <div id="ethics-error" class="hidden mb-4 bg-red-900 border border-red-600 rounded p-3 text-sm text-red-300"></div>
      <button id="btn-launch" onclick="launchAttack()" disabled
        class="px-6 py-3 bg-red-700 hover:bg-red-600 rounded-lg font-bold w-full
               disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
        Lanzar Ataque
      </button>
    </div>`;
}

const _MAC_RE = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/;

function validateManualVictim() {
  const input = document.getElementById('manual-victim-input');
  const btn = document.getElementById('btn-set-victim');
  const err = document.getElementById('manual-victim-error');
  if (!input || !btn) return;
  const valid = _MAC_RE.test(input.value.trim());
  btn.disabled = !valid;
  if (err) err.classList.toggle('hidden', valid || input.value === '');
}

function setManualVictim() {
  const input = document.getElementById('manual-victim-input');
  if (!input) return;
  const mac = input.value.trim().toUpperCase();
  if (!_MAC_RE.test(mac)) return;
  state.set('selectedVictim', mac);
  renderEthics();
}

function checkConfirm() {
  const val = document.getElementById('confirm-input').value;
  const btn = document.getElementById('btn-launch');
  btn.disabled = (val !== 'confirm');
  state.set('confirmKeyword', val);
}

async function launchAttack() {
  const net = state.get('selectedNetwork');
  if (!net) return;
  const victim = state.get('selectedVictim');
  const errEl = document.getElementById('ethics-error');
  const btn = document.getElementById('btn-launch');
  errEl.classList.add('hidden');
  if (!victim) {
    errEl.textContent = 'Seleccione un dispositivo victima en la vista de Reconocimiento.';
    errEl.classList.remove('hidden');
    return;
  }
  btn.disabled = true;
  btn.textContent = 'Configurando...';
  try {
    const resp = await api.postConfig({
      bssid_objetivo: net.bssid_objetivo,
      mac_victima: victim,
      ssid_clonar: net.ssid_objetivo,
      canal: net.canal,
      confirm_provided: true,
    });
    if (resp.ok === false) {
      errEl.textContent = 'Rechazado por el validador etico: ' + (resp.error || resp.codigo);
      errEl.classList.remove('hidden');
      btn.disabled = false;
      btn.textContent = 'Lanzar Ataque';
      return;
    }
    const nowMs = Date.now();
    state.set('startTimeMs', nowMs);
    localStorage.setItem('warden.startTimeMs', String(nowMs));
    showView('attack');
  } catch(e) {
    errEl.textContent = 'No se pudo contactar el ESP32 (192.168.4.1). Verifique que esta conectado a WARDEN_CONTROL.';
    errEl.classList.remove('hidden');
    btn.disabled = false;
    btn.textContent = 'Lanzar Ataque';
  }
}
