import asyncio
import io
from contextlib import redirect_stdout
from pathlib import Path
from scapy.all import wrpcap, RadioTap, Dot11, Dot11Beacon, Dot11Deauth, Dot11Elt

from detector.main import run_pcap_session


def _build_chain_pcap(tmp_path: Path) -> Path:
    """Build a synthetic chain.pcap with all three attack phases."""
    pkts = []
    # Phase 1: 200 unique beacon BSSIDs in 5s (40/s > threshold of 30/s)
    for i in range(200):
        bssid = f"aa:bb:{i // 256:02x}:00:01:{i % 256:02x}"
        p = RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=bssid, addr3=bssid) \
            / Dot11Beacon() / Dot11Elt(ID=0, info=f"FakeNet_{i}".encode())
        p.time = 1000.0 + i * 0.025  # 200 packets over 5s
        pkts.append(p)
    # Phase 2: 60 deauths to protected BSSID (aa:bb:cc:dd:ee:ff) over 3s = 20/s > threshold 5/s
    for i in range(60):
        p = RadioTap() / Dot11(addr1="aa:bb:cc:dd:ee:ff",
                               addr2=f"ee:ee:ee:ee:ee:{i % 256:02x}",
                               addr3="aa:bb:cc:dd:ee:ff") / Dot11Deauth(reason=7)
        p.time = 1010.0 + i * 0.05
        pkts.append(p)
    # Phase 3: rogue AP cloning protected SSID
    rogue = RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff",
                               addr2="00:11:22:33:44:55",
                               addr3="00:11:22:33:44:55") \
        / Dot11Beacon() / Dot11Elt(ID=0, info=b"LAB_WARDEN_UTP")
    rogue.time = 1030.0
    pkts.append(rogue)
    pcap = tmp_path / "chain.pcap"
    wrpcap(str(pcap), pkts)
    return pcap


def test_run_pcap_session_emits_all_alert_types(tmp_path):
    pcap = _build_chain_pcap(tmp_path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        asyncio.run(run_pcap_session([
            "--pcap", str(pcap),
            "--bssid", "AA:BB:CC:DD:EE:FF",
            "--ssid", "LAB_WARDEN_UTP",
            "--ventana-corr", "120",
            "--umbral-beacons", "30",
            "--umbral-deauth", "5",
        ]))
    out = buf.getvalue()
    assert "BEACON_FLOOD" in out, f"Expected BEACON_FLOOD in output:\n{out}"
    assert "DEAUTH" in out, f"Expected DEAUTH in output:\n{out}"
    assert "EVIL_TWIN" in out, f"Expected EVIL_TWIN in output:\n{out}"
    assert "CADENA_OFENSIVA" in out, f"Expected CADENA_OFENSIVA in output:\n{out}"
