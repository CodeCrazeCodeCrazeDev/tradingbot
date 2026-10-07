"""Suite-wide guard: no test in tests/core may invoke a real package
install. dependency_manager is a legacy/quarantined component whose
install_* methods shell out to pip; auto-generated smoke tests call them
transitively (check_dependencies -> ensure_dependencies -> pip) and a real
`pip install torch` from this directory previously corrupted the venv.
"""

import subprocess

import pytest


@pytest.fixture(autouse=True)
def _block_real_package_installs(monkeypatch):
    completed = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr="")

    class _ImportlibShim:
        """check_dependency probes real optional packages (transformers
        import alone exceeds the suite timeout). In tests, every importable
        probe just succeeds."""
        @staticmethod
        def import_module(name, package=None):
            import types
            return types.SimpleNamespace(__name__=name)

    for mod in ("trading_bot.core.dependency_manager",
                "trading_bot.dependency_manager"):
        try:
            monkeypatch.setattr(
                f"{mod}.subprocess.run", lambda *a, **k: completed)
        except Exception:
            pass
        try:
            monkeypatch.setattr(f"{mod}.importlib", _ImportlibShim)
        except Exception:
            continue
