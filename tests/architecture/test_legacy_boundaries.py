"""Wave-0 legacy inventory and boundary-rule tests."""

from pathlib import Path

from trading_bot.foundation.legacy_convergence import (
    boundary_violations,
    build_manifest,
    scan_source,
)


def test_boundary_scanner_flags_direct_capital_calls_outside_execution() -> None:
    source = """
from broker.client import broker

def emit(signal):
    return broker.place_order(signal)
"""

    violations = boundary_violations(source, "trading_bot/strategies/legacy.py")

    assert "direct capital call outside execution/broker adapter" in violations


def test_boundary_scanner_allows_capital_calls_inside_adapter() -> None:
    source = """
class Adapter:
    def submit(self, order):
        return self.broker.place_order(order)
"""

    assert boundary_violations(source, "trading_bot/execution/legacy_adapter.py") == []


def test_boundary_scanner_flags_archive_imports_and_loops() -> None:
    source = """
from trading_bot._archive.old import Legacy
import asyncio
asyncio.create_task(run())
"""

    result = scan_source(source, "trading_bot/legacy/controller.py")
    violations = boundary_violations(source, "trading_bot/legacy/controller.py")

    assert "archive_import" in result["secondary_tags"]
    assert "starts_loop" in result["secondary_tags"]
    assert "active module imports from _archive" in violations
    assert "independent lifecycle/worker loop" in violations


def test_manifest_classifies_canonical_parse_error_and_adapter(tmp_path: Path) -> None:
    package = tmp_path / "trading_bot"
    package.mkdir()
    (package / "__init__.py").write_text("from .unified_bot import UnifiedTradingBot\n")
    (package / "unified_bot.py").write_text("class UnifiedTradingBot: pass\n")
    (package / "legacy_strategy.py").write_text("class Strategy: pass\n")
    (package / "broken_orchestrator.py").write_text("def broken(:\n")

    manifest = build_manifest(tmp_path)
    rows = {row["path"]: row for row in manifest["modules"]}

    assert rows["trading_bot/unified_bot.py"]["classification"] == "canonical"
    assert rows["trading_bot/legacy_strategy.py"]["classification"] == "adapter"
    assert rows["trading_bot/broken_orchestrator.py"]["classification"] == "quarantine"
    assert manifest["scope"]["physical_moves_performed"] is False


def test_legacy_alphaalgo_orchestrator_is_a_runtime_facade() -> None:
    import warnings

    from trading_bot.alphaalgo_orchestrator import AlphaAlgoOrchestrator

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        legacy = AlphaAlgoOrchestrator()

    assert any(item.category is DeprecationWarning for item in captured)
    assert legacy.get_status()["canonical_runtime"] == "ModularMonolithRuntime"


def test_generated_manifest_quarantines_unapproved_capital_paths() -> None:
    import json

    manifest_path = Path(__file__).resolve().parents[2] / "ARCHITECTURE_LEGACY_CLASSIFICATION.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    allowed_prefixes = (
        "trading_bot/execution/",
        "trading_bot/broker/",
        "trading_bot/brokers/",
    )
    from trading_bot.foundation.legacy_convergence import (
        EXECUTION_BOUNDARY_PATHS,
        SIMULATED_CAPITAL_PATHS,
    )

    approved_paths = EXECUTION_BOUNDARY_PATHS | SIMULATED_CAPITAL_PATHS
    for row in manifest["modules"]:
        if row["direct_capital_path"] and not row["path"].startswith(allowed_prefixes):
            if row["path"] in approved_paths:
                continue
            assert row["classification"] == "quarantine"


def test_legacy_risk_manager_warns_and_preserves_api() -> None:
    import warnings

    from trading_bot.risk.risk_manager import RiskManager

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        manager = RiskManager(config={"enable_ml": False})

    assert manager is not None
    assert any(item.category is DeprecationWarning for item in captured)


def test_master_orchestrator_delegates_to_canonical_runtime() -> None:
    import warnings

    from trading_bot.orchestration.master_orchestrator import MasterOrchestrator

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        legacy = MasterOrchestrator()

    assert legacy.get_status()["canonical_runtime"] == "ModularMonolithRuntime"
    assert any(item.category is DeprecationWarning for item in captured)
