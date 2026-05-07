"""Fail when two detector modules export the same public symbol via __all__."""
import importlib
import pkgutil
from collections import defaultdict


def _walk(package_name: str):
    pkg = importlib.import_module(package_name)
    yield package_name, pkg
    for info in pkgutil.walk_packages(pkg.__path__, prefix=f"{package_name}."):
        yield info.name, importlib.import_module(info.name)


def test_no_duplicate_public_symbols_in_detector():
    seen = defaultdict(list)
    for mod_name, mod in _walk("detector"):
        for sym in getattr(mod, "__all__", []):
            seen[sym].append(mod_name)
    duplicates = {sym: mods for sym, mods in seen.items() if len(mods) > 1}
    assert not duplicates, f"Duplicate public symbols across detector modules: {duplicates}"
