#!/usr/bin/env python3
"""Generate deterministic synthetic PCAPs for unit + integration tests."""
import random
from pathlib import Path

from scapy.all import wrpcap, RadioTap, Dot11, Dot11Beacon, Dot11Deauth, Dot11Elt

PROTECTED_BSSID = "aa:bb:cc:dd:ee:ff"
PROTECTED_SSID = "LAB_WARDEN_UTP"


def beacon_flood(out: Path, count: int = 200, span_s: float = 4.0, seed: int = 1) -> None:
    rng = random.Random(seed)
    pkts = []
    for i in range(count):
        bssid = ":".join(f"{rng.randint(0, 255):02x}" for _ in range(6))
        p = (
            RadioTap()
            / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=bssid, addr3=bssid)
            / Dot11Beacon()
            / Dot11Elt(ID=0, info=f"FakeNet_{i}".encode())
        )
        p.time = 1000.0 + i * (span_s / count)
        pkts.append(p)
    wrpcap(str(out), pkts)


def deauth(out: Path, count: int = 80, span_s: float = 3.0, seed: int = 2) -> None:
    rng = random.Random(seed)
    pkts = []
    for i in range(count):
        src = ":".join(f"{rng.randint(0, 255):02x}" for _ in range(6))
        p = (
            RadioTap()
            / Dot11(addr1=src, addr2="ee:ee:ee:ee:ee:ee", addr3=PROTECTED_BSSID)
            / Dot11Deauth(reason=7)
        )
        p.time = 1100.0 + i * (span_s / count)
        pkts.append(p)
    wrpcap(str(out), pkts)


def evil_twin(out: Path) -> None:
    rogue = (
        RadioTap()
        / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2="00:11:22:33:44:55", addr3="00:11:22:33:44:55")
        / Dot11Beacon()
        / Dot11Elt(ID=0, info=PROTECTED_SSID.encode())
    )
    rogue.time = 1200.0
    wrpcap(str(out), [rogue])


def chain(out: Path) -> None:
    """All three phases sequenced within a 60s window."""
    pkts = []
    rng = random.Random(11)
    for i in range(200):
        bssid = ":".join(f"{rng.randint(0, 255):02x}" for _ in range(6))
        p = (
            RadioTap()
            / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=bssid, addr3=bssid)
            / Dot11Beacon()
            / Dot11Elt(ID=0, info=f"FakeNet_{i}".encode())
        )
        p.time = 1000.0 + i * 0.02
        pkts.append(p)
    for i in range(80):
        p = (
            RadioTap()
            / Dot11(addr1="aa:11:22:33:44:55", addr2="ee:ee:ee:ee:ee:ee", addr3=PROTECTED_BSSID)
            / Dot11Deauth(reason=7)
        )
        p.time = 1010.0 + i * 0.04
        pkts.append(p)
    rogue = (
        RadioTap()
        / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2="00:11:22:33:44:55", addr3="00:11:22:33:44:55")
        / Dot11Beacon()
        / Dot11Elt(ID=0, info=PROTECTED_SSID.encode())
    )
    rogue.time = 1030.0
    pkts.append(rogue)
    wrpcap(str(out), pkts)


def quiet(out: Path) -> None:
    """Legitimate-looking traffic only - no attack signatures."""
    pkts = []
    for i in range(20):
        p = (
            RadioTap()
            / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=PROTECTED_BSSID, addr3=PROTECTED_BSSID)
            / Dot11Beacon()
            / Dot11Elt(ID=0, info=PROTECTED_SSID.encode())
        )
        p.time = 2000.0 + i * 30
        pkts.append(p)
    wrpcap(str(out), pkts)


def live_parity(out: Path) -> None:
    """One beacon + one deauth with explicit RadioTap; used to gate hardware-day dispatch."""
    pkts = [
        RadioTap()
        / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=PROTECTED_BSSID, addr3=PROTECTED_BSSID)
        / Dot11Beacon()
        / Dot11Elt(ID=0, info=PROTECTED_SSID.encode()),
        RadioTap()
        / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2="ee:ee:ee:ee:ee:ee", addr3=PROTECTED_BSSID)
        / Dot11Deauth(reason=7),
    ]
    pkts[0].time = 1.0
    pkts[1].time = 2.0
    wrpcap(str(out), pkts)


def main() -> int:
    out_dir = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pcap"
    out_dir.mkdir(parents=True, exist_ok=True)
    beacon_flood(out_dir / "beacon-flood.pcap")
    deauth(out_dir / "deauth.pcap")
    evil_twin(out_dir / "evil-twin.pcap")
    chain(out_dir / "chain.pcap")
    quiet(out_dir / "quiet.pcap")
    live_parity(out_dir / "live-parity-radiotap.pcap")
    print(f"Wrote 6 fixtures to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
