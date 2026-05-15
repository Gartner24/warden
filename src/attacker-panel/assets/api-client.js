// Change to 'http://localhost:8081' for mock-esp32 development
const API_BASE = 'http://192.168.4.1';

const api = {
  async status() {
    const r = await fetch(API_BASE + '/status');
    return r.json();
  },
  async attackStatus() {
    const r = await fetch(API_BASE + '/attack/status');
    return r.json();
  },
  async scan() {
    const r = await fetch(API_BASE + '/scan');
    return r.json();
  },
  async clients(bssid, canal) {
    const url = `${API_BASE}/clients?bssid=${encodeURIComponent(bssid)}&canal=${encodeURIComponent(canal)}`;
    const r = await fetch(url);
    return r.json();
  },
  async clientsStop() {
    const r = await fetch(`${API_BASE}/clients/stop`, { method: 'POST' });
    return r.json().catch(() => ({}));
  },
  async clientsResult() {
    const r = await fetch(`${API_BASE}/clients`);
    return r.json();
  },
  async ouiLookup(mac) {
    const r = await fetch(`${API_BASE}/oui-lookup?mac=${encodeURIComponent(mac)}`);
    return r.json();
  },
  async ouiLookupCached(mac) {
    const cache = state.get('ouiCache') || {};
    const prefix = mac.substring(0, 8).toUpperCase();
    if (cache[prefix] !== undefined) return cache[prefix];
    try {
      const r = await fetch(`${API_BASE}/oui-lookup?mac=${encodeURIComponent(mac)}`);
      const data = await r.json();
      const vendor = data.encontrado ? data.fabricante : 'Desconocido';
      cache[prefix] = vendor;
      state.set('ouiCache', cache);
      return vendor;
    } catch(e) {
      return 'Desconocido';
    }
  },
  async getConfig() {
    const r = await fetch(API_BASE + '/config');
    return r.json();
  },
  async postConfig(body) {
    const r = await fetch(API_BASE + '/config', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.json();
  },
  async attackStart(body) {
    const r = await fetch(API_BASE + '/attack/start', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.json();
  },
  async attackStop() {
    const r = await fetch(API_BASE + '/attack/stop', { method: 'POST' });
    return r.json();
  },
  async credentials() {
    const r = await fetch(API_BASE + '/credentials');
    return r.json();
  },
};
