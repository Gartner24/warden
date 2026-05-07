const state = (() => {
  let _s = {
    selectedNetwork: null,
    selectedClient: null,
    confirmKeyword: '',
    attackPhase: 'IDLE',
    counters: { beacons_emitidos: 0, deauths_emitidos: 0, clientes_evil_twin: 0, credenciales_capturadas: 0 },
    credentials: [],
    startTimeMs: null,
  };
  const _listeners = {};

  return {
    get(key) { return _s[key]; },
    set(key, val) {
      _s[key] = val;
      if (_listeners[key]) _listeners[key].forEach(fn => fn(val));
    },
    subscribe(key, fn) {
      if (!_listeners[key]) _listeners[key] = [];
      _listeners[key].push(fn);
    },
    reset() {
      _s = { selectedNetwork: null, selectedClient: null, confirmKeyword: '',
             attackPhase: 'IDLE', counters: { beacons_emitidos: 0, deauths_emitidos: 0,
             clientes_evil_twin: 0, credenciales_capturadas: 0 }, credentials: [], startTimeMs: null };
    },
  };
})();
