function showView(name) {
  if (name !== 'recon' && typeof stopReconScan === 'function') {
    stopReconScan();
  }
  document.querySelectorAll('.view').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  const viewEl = document.getElementById('view-' + name);
  const navEl = document.getElementById('nav-' + name);
  if (viewEl) viewEl.classList.remove('hidden');
  if (navEl) navEl.classList.add('active');

  if (name === 'recon')   renderRecon();
  if (name === 'ethics')  renderEthics();
  if (name === 'attack')  renderAttack();
  if (name === 'summary') renderSummary();
}

async function checkConnection() {
  try {
    await api.status();
    document.getElementById('conn-status').textContent = 'Conectado';
    document.getElementById('conn-status').className = 'text-xs px-2 py-1 rounded bg-green-900 text-green-300';
  } catch {
    document.getElementById('conn-status').textContent = 'Desconectado';
    document.getElementById('conn-status').className = 'text-xs px-2 py-1 rounded bg-gray-700 text-gray-400';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  showView('recon');
  checkConnection();
  setInterval(checkConnection, 5000);
});
