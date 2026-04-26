# Lab Setup

Source: `deliverables/warden-laboratorio.tex`, `deliverables/warden-srs.tex` lines 366-399

## Hardware

| Component | Notes |
|---|---|
| ESP32-WROOM-32 | 4 MB flash, 520 KB RAM, USB cable for flashing and serial |
| Panda Wireless PAU0B AC600 | MediaTek MT7610U chipset, driver `mt76x0u`, USB |
| Lab WiFi router | SSID `LAB_WARDEN_UTP`, channel 6, WPA2, no internet |
| Operator laptop (attacker) | Any OS with a modern browser; must have Arduino IDE 2.x |
| Defender laptop (detector) | Arch Linux or Ubuntu 22.04 LTS; Python 3.10+ |
| Victim 1 | Redmi Note 7 (MIUI 12.5) |
| Victim 2 | Dell Latitude E6220 (Ubuntu Server 22.04.5 LTS) |

## Defender laptop setup

### Arch Linux

```bash
sudo pacman -S python python-pip aircrack-ng mdk3 wireshark-qt tcpdump iw hostapd dnsmasq
yay -S panda-wireless-pac600   # if needed for mt76x0u firmware
```

### Ubuntu 22.04

```bash
sudo apt install python3 python3-pip aircrack-ng mdk4 wireshark tshark tcpdump iw hostapd dnsmasq
```

### Persistent adapter name (udev)

Create `/etc/udev/rules.d/70-warden-adapters.rules`:

```
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="<PANDA_MAC>", NAME="panda0"
```

Replace `<PANDA_MAC>` with the MAC address of the Panda PAU0B. Reload udev and replug the adapter:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Disable MAC randomization for the Panda adapter

NetworkManager randomizes MACs by default on many distros. Because the udev rule above matches by MAC address, randomization causes the rule to fail (the adapter boots with a random MAC and never matches `<PANDA_MAC>`).

First, get the permanent MAC:
```bash
ethtool -P <iface>   # use the current name before the udev rule renames it
```

Create `/etc/NetworkManager/conf.d/99-panda-no-randomize.conf`:
```ini
[device-mac-randomization]
match-device=mac:<PANDA_PERMANENT_MAC>
wifi.scan-rand-mac-address=no

[connection-mac-randomization]
match-device=mac:<PANDA_PERMANENT_MAC>
wifi.cloned-mac-address=permanent
ethernet.cloned-mac-address=permanent
```

Replace `<PANDA_PERMANENT_MAC>` with the value from `ethtool -P`. Then:
```bash
sudo systemctl restart NetworkManager
# unplug and replug the Panda adapter
iw dev panda0 info   # verify addr matches the permanent MAC
```

### Monitor mode

```bash
sudo ip link set panda0 down
sudo iw dev panda0 set type monitor
sudo ip link set panda0 up
sudo iw dev panda0 set channel 6
```

## Attacker laptop setup

1. Install Arduino IDE 2.x.
2. Add the ESP32 board package: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`.
3. Select board: **ESP32 Dev Module**.
4. Install required libraries from the Arduino Library Manager: `ESPAsyncWebServer` (latest), `AsyncTCP` (dependency of ESPAsyncWebServer), `ArduinoJson` 7.0+. These are required by the `Servidor API REST` and `Portal Cautivo` firmware modules.
5. Flash `src/attacker/` via USB at 115200 baud.

### Verify ESP32 detection and grant serial port access

Install `esptool`:
- Arch: `sudo pacman -S esptool`
- Ubuntu: `pip install esptool`

With the ESP32 connected via USB, verify the Silicon Labs USB-Serial bridge appears:
```bash
lsusb | grep -i 'CP210\|CH340\|FT232'
```

Confirm the kernel created the serial device:
```bash
ls /dev/ttyUSB*   # expected: /dev/ttyUSB0
```

Check chip details (expected: `ESP32-D0WD-V3`, revision v3.1, 4 MB flash):
```bash
esptool --port /dev/ttyUSB0 flash-id
```

Add your user to the serial port group so `esptool` and Arduino IDE work without `sudo`:
- Arch: `sudo usermod -aG uucp $USER`
- Ubuntu: `sudo usermod -aG dialout $USER`

Log out and back in (or reboot) for the group change to take effect.

If `/dev/ttyUSB0` does not appear, the most common causes are a charge-only USB cable (replace with a data cable) or the user not yet in the correct group.

## Lab network

- Router SSID: `LAB_WARDEN_UTP`, channel 6, WPA2 (no internet, isolated VLAN if possible).
- `WARDEN_CONTROL` AP is created by the ESP32 after boot: SSID `WARDEN_CONTROL`, WPA2-PSK `warden-control-pwd`, channel 1, IP `192.168.4.1`.
- Evil Twin AP (during attack phase 3): SSID cloned from target, IP `10.0.0.1`, DHCP `10.0.0.10-10.0.0.50`.
