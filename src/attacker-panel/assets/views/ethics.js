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
      </div>
      <div class="mb-4">
        <label class="block text-sm text-gray-400 mb-2">
          Escriba <strong class="text-white">confirm</strong> para autorizar:
        </label>
        <input id="confirm-input" type="text" placeholder="confirm"
          class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          oninput="checkConfirm()" />
      </div>
      <button id="btn-launch" onclick="launchAttack()" disabled
        class="px-6 py-3 bg-red-700 hover:bg-red-600 rounded-lg font-bold w-full
               disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
        Lanzar Ataque
      </button>
    </div>`;
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
  // POST config first
  try {
    await api.postConfig({
      bssid_objetivo: net.bssid_objetivo,
      ssid_clonar: net.ssid_objetivo,
      canal: net.canal,
      confirm_provided: true,
    });
    state.set('startTimeMs', Date.now());
    showView('attack');
  } catch(e) {
    alert('Error al configurar: ' + e.message);
  }
}
