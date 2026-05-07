# Hardware Bring-Up Runbook

Step-by-step procedure for the first time you have ESP32 + Panda PAU0B connected.

## Prerequisites

- Arduino IDE 2.x with esp32 board package installed
- Panda PAU0B plugged into USB
- Operator laptop on the same physical desk as ESP32

---

## Step 1: Flash the firmware

1. Open Arduino IDE
2. File -> Open -> select `src/attacker/attacker.ino`
3. Tools -> Board -> ESP32 Arduino -> ESP32 Dev Module
4. Tools -> Upload Speed -> 115200
5. Tools -> Port -> select the ESP32 COM/tty port
6. Click Upload (arrow icon)
7. Wait for "Done uploading"

## Step 2: Open Serial Monitor

1. Tools -> Serial Monitor
2. Set baud rate to 115200
3. Wait for: `[INFO] [0] WARDEN ready`

If you see garbled output, check the baud rate.

## Step 3: Connect to WARDEN_CONTROL

1. On operator laptop, open Wi-Fi settings
2. Connect to SSID: `WARDEN_CONTROL`
3. Password: `warden-control-pwd`
4. Wait for IP assignment (192.168.4.x range)

## Step 4: Verify API responds

```bash
curl http://192.168.4.1/status
```

Expected: JSON with `estado_cadena: "IDLE"`.

If no response: check that laptop is on WARDEN_CONTROL network, not another Wi-Fi.

## Step 5: Open Attacker Panel

1. From the project root: `cd src/attacker-panel && python3 -m http.server 8080`
2. Open browser: `http://localhost:8080`
3. Change `API_BASE` in `assets/api-client.js` to `http://192.168.4.1`
4. The "Conectado" chip should turn green after page loads

## Step 6: Run recon

1. Click "Reconocimiento" tab
2. Click "Escanear Redes"
3. Verify your lab router appears in the list
4. Note its BSSID for the detector config

## Set up Monitor Mode (detector laptop)

```bash
sudo scripts/setup-monitor-mode.sh panda0 6
```

## Start the Detector

```bash
source .venv/bin/activate
python3 -m detector.main --iface panda0 --bssid <LAB_BSSID> --ssid LAB_WARDEN_UTP
```

Replace `<LAB_BSSID>` with the BSSID from the recon step (e.g. `E4:AB:89:D6:9B:80`).

Open the Defender Panel in another terminal:

```bash
uvicorn detector.web.server:app --host 127.0.0.1 --port 8000 --reload
```

Navigate to `http://127.0.0.1:8000/`.

---

## Troubleshooting

**SoftAP not visible:** Check that the ESP32 is powered and Serial Monitor shows `WARDEN ready`. Try reset button.

**Scan returns empty list:** Wi-Fi may be in wrong mode. Use serial command `status` to check state. Flash again if needed.

**Validator rejects valid BSSID:** Type `set bssid <MAC> confirm` in Serial Monitor to bypass confirmation.

**Detector not detecting attacks:** Verify panda0 is in monitor mode (`iw dev panda0 info` should show `type monitor`). Check channel matches attack channel.
