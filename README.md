# WARDEN

**Wireless Attack Reproduction and Detection Environment**

Academic WiFi security project for UTP. WARDEN is a dual-subsystem lab that reproduces a three-phase WiFi attack chain (Beacon Flood -> Deauthentication -> Evil Twin with captive portal) using an ESP32, and detects the same chain in real time using a Python/Scapy sensor paired with a FastAPI dashboard. An in-firmware Ethical Validator restricts all offensive operations to lab-owned BSSIDs and MACs.

> **Academic / lab use only.** See [`deliverables/warden-fundamentos.tex`](deliverables/warden-fundamentos.tex) for the full ethical and legal scope.

---

## Hardware required

| Component | Role |
|---|---|
| ESP32-WROOM-32 (4 MB flash) | Offensive subsystem |
| Panda Wireless PAU0B (MT7610U, `panda0`) | Monitor-mode capture adapter |
| Lab WiFi router | Victim AP |
| Android phone (MIUI / stock) | Victim device |

---

## Repository layout

```
warden/
|-- src/
|   |-- attacker/          # ESP32 firmware (C++ / Arduino-ESP32 3.x)
|   |-- attacker-panel/    # Browser UI for attack operator (static HTML/JS)
|   `-- detector/          # Python detector + FastAPI defender panel
|-- scripts/               # Shell helpers
|-- tests/                 # Automated acceptance and unit tests
|-- captures/              # Reference PCAPs (gitignored content)
|-- deliverables/          # LaTeX academic submissions
`-- docs/                  # Architecture, ADRs, API reference
```

---

## 1. ESP32 firmware

### Compile

```bash
arduino-cli compile \
  --fqbn esp32:esp32:esp32 \
  --build-path /tmp/warden-build \
  --build-property "compiler.cpp.extra_flags=-DCONFIG_ASYNC_TCP_RUNNING_CORE=1" \
  --build-property "compiler.c.extra_flags=-DCONFIG_ASYNC_TCP_RUNNING_CORE=1" \
  src/attacker
```

### Flash

```bash
arduino-cli upload \
  --fqbn esp32:esp32:esp32 \
  --port /dev/ttyUSB0 \
  --input-dir /tmp/warden-build \
  src/attacker
```

### Compile + flash in one shot

```bash
arduino-cli compile \
  --fqbn esp32:esp32:esp32 \
  --build-path /tmp/warden-build \
  --build-property "compiler.cpp.extra_flags=-DCONFIG_ASYNC_TCP_RUNNING_CORE=1" \
  --build-property "compiler.c.extra_flags=-DCONFIG_ASYNC_TCP_RUNNING_CORE=1" \
  src/attacker && \
arduino-cli upload \
  --fqbn esp32:esp32:esp32 \
  --port /dev/ttyUSB0 \
  --input-dir /tmp/warden-build \
  src/attacker
```

### Serial monitor (ESP32 logs)

```bash
python3 -c "
import serial, sys
s = serial.Serial('/dev/ttyUSB0', 115200)
[sys.stdout.write(s.readline().decode(errors='replace')) for _ in iter(int,1)]
"
```

After boot the ESP32 broadcasts `WARDEN_CONTROL` (WPA2, password `warden-control-pwd`) at `192.168.4.1`.

---

## 2. Attacker panel

Connect your laptop to the `WARDEN_CONTROL` WiFi network first.

```bash
cd src/attacker-panel
python3 -m http.server 8080
```

Open `http://localhost:8080` in a browser. The panel talks to the ESP32 at `http://192.168.4.1`.

**Workflow:**
1. **Recon** tab — scan for nearby networks, pick the target, select victim device MAC
2. **Ethics** tab — confirm the target BSSID is lab-owned to unlock attack controls
3. **Attack** tab — configure phase durations, choose mode (`cadena_automatica` runs all three phases in sequence), start attack
4. **Summary** tab — view captured credentials after FASE_3 completes

---

## 3. Panda0 monitor mode

### Set monitor mode on a specific channel

```bash
sudo bash scripts/setup-monitor-mode.sh panda0 <channel>
# Example: channel 1
sudo bash scripts/setup-monitor-mode.sh panda0 1
```

Or manually:

```bash
sudo ip link set panda0 down
sudo iw dev panda0 set type monitor
sudo ip link set panda0 up
sudo iw dev panda0 set channel <channel>
```

### Check current mode and channel

```bash
iw dev panda0 info
```

Output shows `type monitor` and `channel X` when in monitor mode.

### Restore to managed (normal) mode

```bash
sudo ip link set panda0 down
sudo iw dev panda0 set type managed
sudo ip link set panda0 up
```

### Prevent NetworkManager from taking over panda0

```bash
nmcli dev set panda0 managed no
```

### sudoers entry (run monitor script without password prompt)

Add to `/etc/sudoers.d/warden`:

```
<your-user> ALL=(ALL) NOPASSWD: /usr/bin/bash /path/to/warden/scripts/setup-monitor-mode.sh
<your-user> ALL=(ALL) NOPASSWD: /usr/bin/ip, /usr/bin/iw
```

---

## 4. Defender panel

### Install dependencies (once)

```bash
cd /path/to/warden
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Start the defender panel

```bash
source .venv/bin/activate
uvicorn detector.web.server:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in a browser.

**Workflow in the panel:**
1. Set **Canal a monitorear** to match the victim AP channel (e.g. `1`)
2. Click **Activar modo monitor** — `panda0` badge should show `monitor ch 1`
3. Fill in **BSSID protegido** and **SSID protegido** of the victim AP
4. Click **Iniciar detector**
5. Watch alerts appear in real time as the attacker runs its chain
6. Click **Resetear sesion** between runs to clear counters

> **Important:** the panda0 channel must match the victim AP channel and the attacker channel. If they differ, most deauth frames will be invisible to the detector.

---

## 5. Full attack demo (end-to-end)

**Terminal 1 — serial monitor:**
```bash
python3 -c "
import serial, sys
s = serial.Serial('/dev/ttyUSB0', 115200)
[sys.stdout.write(s.readline().decode(errors='replace')) for _ in iter(int,1)]
"
```

**Terminal 2 — attacker panel:**
```bash
cd src/attacker-panel && python3 -m http.server 8080
```

**Terminal 3 — defender panel:**
```bash
source .venv/bin/activate && uvicorn detector.web.server:app --host 0.0.0.0 --port 8000
```

**Steps:**
1. Flash firmware to ESP32
2. Connect laptop to `WARDEN_CONTROL` WiFi
3. Open attacker panel at `http://localhost:8080`
4. Open defender panel at `http://localhost:8000`
5. In defender panel: set channel, activate monitor mode, start detector
6. In attacker panel: scan, pick target, confirm ethics, start `cadena_automatica`
7. Watch serial for phase transitions: `FASE_1` -> `FASE_2` -> `FASE_3`
8. When `FASE_3` starts, connect victim phone to the cloned SSID
9. The OS captive portal popup appears — victim enters credentials
10. Credentials appear in attacker panel Summary tab and `GET http://192.168.4.1/credentials`
11. Defender panel shows BEACON_FLOOD, DEAUTH, EVIL_TWIN, and CADENA_OFENSIVA alerts

---

## 6. Useful one-liners

**Check ESP32 port:**
```bash
ls /dev/ttyUSB*
```

**Fetch attack status from ESP32:**
```bash
curl http://192.168.4.1/attack/status
```

**Fetch captured credentials from ESP32:**
```bash
curl http://192.168.4.1/credentials
```

**Fetch current attacker config:**
```bash
curl http://192.168.4.1/config
```

**Stop attack manually:**
```bash
curl -X POST http://192.168.4.1/attack/stop
```

**Scan networks from ESP32:**
```bash
curl http://192.168.4.1/scan
```

**Start detector via API (offline/pcap mode):**
```bash
curl -X POST http://localhost:8000/api/detector/start \
  -H "content-type: application/json" \
  -d '{"bssid_protegido":"E4:AB:89:D6:9B:80","ssid_protegido":"RVGREDES 2.4","canal":1,"pcap":"captures/session.pcap"}'
```

**Run acceptance tests:**
```bash
source .venv/bin/activate
pytest tests/ -v
```

**Check panda0 is in monitor mode:**
```bash
iw dev panda0 info | grep type
# should print: type monitor
```

**Kill anything holding the serial port:**
```bash
fuser /dev/ttyUSB0
```

---

## 7. Attack phases reference

| Phase | Duration (default) | What happens |
|---|---|---|
| FASE_1: Beacon Flood | 30 s | ESP32 broadcasts ~50 fake SSIDs/s to saturate victim's network list |
| FASE_2: Deauth | 30 s | ESP32 injects deauth frames spoofed from target AP, disconnecting victim |
| FASE_3: Evil Twin | 120 s | ESP32 brings up cloned AP; victim connects; captive portal captures credentials |

Default config values are in `src/attacker/config.cpp`. Phase durations can be changed via `POST http://192.168.4.1/config`.

---

## 8. Detection thresholds (defaults)

| Parameter | Default | Meaning |
|---|---|---|
| `umbral_beacons_por_seg` | 30 | Beacons/s above this triggers BEACON_FLOOD alert |
| `ventana_beacon_seg` | 5 | Window size for beacon rate measurement |
| `umbral_deauth_por_seg` | 5 | Deauths/s above this triggers DEAUTH alert |
| `ventana_deauth_seg` | 3 | Window size for deauth rate measurement |
| `cooldown_alerta_seg` | 5 | Minimum seconds between alerts of the same type |

Thresholds can be changed at runtime via `POST http://localhost:8000/api/config`.

---

## License

TBD
