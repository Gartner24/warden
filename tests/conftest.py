import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PCAP_DIR = Path(__file__).resolve().parent / "fixtures" / "pcap"
API_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "api"


@pytest.fixture
def pcap_path():
    def _loader(name: str) -> Path:
        path = PCAP_DIR / name
        assert path.exists(), f"missing fixture {path}"
        return path
    return _loader


@pytest.fixture
def api_fixture():
    def _loader(name: str) -> dict:
        import json
        path = API_FIXTURE_DIR / name
        return json.loads(path.read_text())
    return _loader
