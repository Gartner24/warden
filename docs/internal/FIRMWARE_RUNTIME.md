# FIRMWARE_RUNTIME

Internal reference for the FreeRTOS task model, Wi-Fi state machine, and data buffer policies.

---

## 1. FreeRTOS Task Table

| Task | Priority | Stack (bytes) | Core | Created at | Suspended during |
|---|---|---|---|---|---|
| `serial_listener` | tskIDLE_PRIORITY+1 | 4096 | 0 | boot | never |
| `chain_controller` | tskIDLE_PRIORITY+3 | 4096 | 0 | boot | never |
| `beacon_emitter` | tskIDLE_PRIORITY+4 | 4096 | 1 | start of FASE_1 | end of FASE_1 |
| `deauth_emitter` | tskIDLE_PRIORITY+4 | 4096 | 1 | start of FASE_2 | end of FASE_2 |
| `dhcp_server` | tskIDLE_PRIORITY+2 | 3072 | 0 | start of FASE_3 | end of FASE_3 |
| `dns_server` | tskIDLE_PRIORITY+2 | 3072 | 0 | start of FASE_3 | end of FASE_3 |
| `captive_portal` | tskIDLE_PRIORITY+2 | 6144 | 0 | start of FASE_3 | end of FASE_3 |
| `api_server` (ESPAsyncWebServer) | (managed by lib) | (lib default) | 0 | boot | during FASE_3 only |
| `recon` | tskIDLE_PRIORITY+2 | 4096 | 0 | on demand | when not scanning |
| `control_ap` | (Wi-Fi mgr) | n/a | n/a | boot | during FASE_3 |

**Mutex:** Single `radio_mutex` (`SemaphoreHandle_t`) held by anything calling `esp_wifi_80211_tx` or `esp_wifi_set_channel`. No other function may call these without holding the mutex.

---

## 2. Wi-Fi Mode Transition Diagram

```
BOOT
  -> WIFI_MODE_AP (ch1)
     Calls: esp_wifi_set_mode(WIFI_MODE_AP),
            esp_wifi_set_config(AP, {WARDEN_CONTROL, warden-control-pwd}),
            esp_wifi_start()
     Skip consequence: no control network, panel cannot connect

WIFI_MODE_AP (ch1) [control up]
  -> WIFI_MODE_APSTA (ch1+scan)
     Calls: esp_wifi_set_mode(WIFI_MODE_APSTA),
            WiFi.scanNetworks()
     Skip consequence: STA mode missing, scan returns empty

  -> WIFI_MODE_NULL + raw injection [FASE_1 beacon flood]
     Calls: esp_wifi_stop(),
            esp_wifi_set_mode(WIFI_MODE_NULL),
            esp_wifi_start(),
            esp_wifi_set_channel(attack_channel, WIFI_SECOND_CHAN_NONE)
     Skip consequence: raw frames injected on wrong channel or fail silently

WIFI_MODE_APSTA (ch1+scan)
  -> WIFI_MODE_AP (ch1) [scan complete]
     Calls: esp_wifi_set_mode(WIFI_MODE_AP)
     Skip consequence: STA interface left open, wastes power,
                       may cause beacon flood interference

WIFI_MODE_NULL + raw injection [FASE_1]
  -> WIFI_MODE_NULL + raw injection [FASE_2 deauth]
     Calls: esp_wifi_set_channel(victim_channel, WIFI_SECOND_CHAN_NONE)
     Skip consequence: deauths on wrong channel, victims ignore them

  -> WIFI_MODE_AP (ch6, SSID=cloned, OPEN) [FASE_3 evil twin]
     Calls: esp_wifi_stop(),
            esp_wifi_set_mode(WIFI_MODE_AP),
            esp_wifi_set_config(AP, {cloned_ssid, "", ch6}),
            esp_wifi_start(),
            tcpip_adapter_set_ip_info(10.0.0.1)
     Skip consequence: captive portal unreachable, DHCP fails

  -> WIFI_MODE_AP (ch1) [FASE_3 end / attack stop]
     Calls: esp_wifi_stop(),
            esp_wifi_set_mode(WIFI_MODE_AP),
            esp_wifi_set_config(AP, {WARDEN_CONTROL, warden-control-pwd, ch1}),
            esp_wifi_start()
     Skip consequence: control AP down, panel disconnected
```

---

## 3. Credentials Buffer Policy

- 16-slot circular buffer in RAM: `CredencialCapturada credenciales[16]`
- On overflow: oldest entry overwritten (no error, no notification)
- Cleared on `POST /attack/stop` ONLY when `auto_clear_on_stop` flag is set in config (default: false)
- Operator MUST call `GET /credentials` before `POST /attack/stop` to safely retrieve credentials
- Never persisted to flash - reboot clears all credentials
- `clientes_evil_twin` counter in status tracks connected clients, not credential count

---

## 4. asyncio.Queue Policy (Defender Panel)

- Queue bounded: `asyncio.Queue(maxsize=2048)`
- Drop policy: oldest-drop when full
  - Implementation: try `put_nowait`; on `QueueFull`, call `get_nowait` (discard oldest), then `put_nowait` again
- Drop counter: increment `_drops` on each drop
- Warning rate: log `WARNING` every 1000 drops via Python `logging`
- Reasoning: beacon flood at 50 frames/s generates up to 1500 frames in 30s window; queue fits with margin; CADENA_OFENSIVA alerts must never be dropped (they arrive late, after three phase alerts, so the queue must still have room)
