"""Read 802.11 frames from a PCAP file. Supports radiotap-prefixed captures."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from scapy.all import rdpcap  # type: ignore[import-untyped]

__all__ = ["iter_packets"]


def iter_packets(pcap_path: str | Path) -> Iterator[Any]:
    p = Path(pcap_path)
    if not p.exists():
        raise FileNotFoundError(p)
    for pkt in rdpcap(str(p)):
        yield pkt
