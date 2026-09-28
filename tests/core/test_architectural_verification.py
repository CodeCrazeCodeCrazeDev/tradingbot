import sys
import os
import ast
import pytest
from pathlib import Path

# Authoritative singletons list
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.unified_registry import UnifiedComponentRegistry
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, decision_bus

def test_singleton_integrity():
    """Verify system-wide singletons maintain unique instance identity."""
    csc1 = CognitiveSystemController()
    csc2 = CognitiveSystemController()
    assert csc1 is csc2

    registry1 = UnifiedComponentRegistry()
    registry2 = UnifiedComponentRegistry()
    assert registry1 is registry2

    bus1 = UnifiedDecisionBus()
    bus2 = UnifiedDecisionBus()
    assert bus1 is bus2
    assert decision_bus is bus1

@pytest.mark.timeout(600)  # AST-walks every .py in trading_bot/ — slow on this disk
def test_no_archive_imports_in_production():
    """Verify that no production files in trading_bot import from the _archive directory."""
    root_dir = Path(__file__).parent.parent.parent / "trading_bot"

    for path in root_dir.glob("**/*.py"):
        if "_archive" in path.parts:
            continue

        with open(path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(path))
                for node in ast.walk(tree):
                    # Check direct imports (e.g., import _archive)
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            assert "_archive" not in name.name, f"Forbidden import of _archive in {path}: {name.name}"
                    # Check from imports (e.g., from _archive import ...)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            assert "_archive" not in node.module, f"Forbidden from-import of _archive in {path}: {node.module}"
            except SyntaxError:
                # Skip files with syntax errors (legacy or templates)
                continue

def test_clean_dependency_resolution():
    """Verify that core modules can be imported cleanly without circular import errors."""
    import trading_bot.core.csc.controller
    import trading_bot.core.unified_event_bus
    import trading_bot.core.unified_registry
    import trading_bot.database.shared_memory_manager
    assert True


_REPO_ROOT = Path(__file__).parent.parent.parent


def _env_keys(env) -> set:
    """Return the variable names of a compose ``environment`` block (list or
    dict form) without exposing any values in assertion output."""
    if env is None:
        return set()
    if isinstance(env, dict):
        return set(env)
    names = set()
    for item in env:
        names.add(str(item).split("=", 1)[0])
    return names


def test_paper_compose_services_carry_no_broker_credentials():
    """MP-040: paper/smoke workers must not receive broker or arbitrary
    secret injection — the canonical path simulates fills locally and does
    not consume MT5 variables."""
    import yaml

    compose_files = [
        "docker-compose.yml",
        "docker-compose.production.yml",
        "config/docker-compose.yml",
    ]
    forbidden = {"MT5_LOGIN", "MT5_PASSWORD", "MT5_INVESTOR", "MT5_SERVER"}

    for rel in compose_files:
        path = _REPO_ROOT / rel
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        services = doc.get("services", {})
        assert "trading-bot" in services, f"{rel}: trading-bot service missing"
        for service_name in ("trading-bot", "test"):
            service = services.get(service_name)
            if service is None:
                continue
            keys = _env_keys(service.get("environment"))
            leaked = sorted(keys & forbidden | {k for k in keys if k.startswith("MT5_")})
            assert not leaked, f"{rel}: {service_name} still declares broker vars {leaked}"
        assert not services["trading-bot"].get("env_file"), (
            f"{rel}: trading-bot must not inject a whole env file into the paper worker"
        )
        worker_env = _env_keys(services["trading-bot"].get("environment"))
        assert "PAPER_TRADING" in worker_env, f"{rel}: trading-bot must declare paper mode"


def test_legacy_config_compose_resolves_repo_root():
    """config/docker-compose.yml lives one level deep — its build context
    and volume mounts must resolve to the repository root, not config/."""
    import yaml

    path = _REPO_ROOT / "config" / "docker-compose.yml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    worker = doc["services"]["trading-bot"]

    build = worker.get("build")
    context = build.get("context") if isinstance(build, dict) else build
    assert context, "legacy compose: trading-bot has no build context"
    resolved = (path.parent / context).resolve()
    assert resolved == _REPO_ROOT.resolve(), (
        "legacy compose: build context does not resolve to repo root"
    )

    mounts = [v.split(":")[0] for v in worker.get("volumes", [])]
    assert any("market_data.db" in m for m in mounts), (
        "legacy compose: trading-bot must mount market_data.db for replay"
    )

    test_cmd = str(doc["services"].get("test", {}).get("command", ""))
    assert "main.py" in test_cmd and "--synthetic" in test_cmd, (
        "legacy compose: test service must run the canonical synthetic smoke"
    )
