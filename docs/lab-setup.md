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
4. Flash `src/attacker/` via USB at 115200 baud.

## Lab network

- Router SSID: `LAB_WARDEN_UTP`, channel 6, WPA2 (no internet, isolated VLAN if possible).
- `WARDEN_CONTROL` AP is created by the ESP32 after boot: SSID `WARDEN_CONTROL`, WPA2-PSK `warden-control-pwd`, channel 1, IP `192.168.4.1`.
- Evil Twin AP (during attack phase 3): SSID cloned from target, IP `10.0.0.1`, DHCP `10.0.0.10-10.0.0.50`.
