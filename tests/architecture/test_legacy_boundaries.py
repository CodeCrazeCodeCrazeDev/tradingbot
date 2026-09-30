"""Wave-0 legacy inventory and boundary-rule tests."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

import pytest

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


def test_wave7_interface_facades_have_no_loop_or_capital_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for relative in (
        "trading_bot/api.py",
        "trading_bot/api/__init__.py",
        "trading_bot/unified_main.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert boundary_violations(source, relative) == []


@pytest.mark.asyncio
async def test_legacy_event_bus_is_a_no_worker_facade() -> None:
    from trading_bot.core.event_bus import Event, EventBus, EventPriority

    delivered = []
    forwarded = []

    class CanonicalBus:
        async def publish(self, event):
            forwarded.append(event)

    async def handler(event):
        delivered.append(event)

    bus = EventBus()
    bus.unified_bus = CanonicalBus()
    await bus.start()
    bus.subscribe("legacy_subscriber", ["market.tick"], handler)
    await bus.publish(Event(
        event_type="market.tick",
        payload={"symbol": "EURUSD"},
        source="legacy_test",
        priority=EventPriority.NORMAL,
    ))

    assert [event.payload["symbol"] for event in delivered] == ["EURUSD"]
    assert [event.event_type for event in forwarded] == ["market.tick"]
    assert bus.get_stats()["queue_size"] == 0
    assert boundary_violations(
        Path("trading_bot/core/event_bus.py").read_text(encoding="utf-8"),
        "trading_bot/core/event_bus.py",
    ) == []


@pytest.mark.asyncio
async def test_master_integration_delegates_trade_path_to_runtime() -> None:
    import warnings

    from trading_bot.master_integration import MasterTradingSystem

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        system = MasterTradingSystem({"mode": "paper"})

    calls = []

    async def fake_start() -> None:
        system.runtime.bot.running = True

    async def fake_cycle(observation):
        calls.append(observation)
        return {"outcome": "hold"}

    system.runtime.start = fake_start
    system.runtime.bot.run_cycle = fake_cycle
    result = await system.execute_complete_trade({"symbol": "EURUSD", "price": 1.1})

    assert result["status"] == "DELEGATED"
    assert calls[0]["symbol"] == "EURUSD"
    assert result["canonical_runtime"] == "ModularMonolithRuntime"
    assert any(item.category is DeprecationWarning for item in captured)
    assert boundary_violations(
        Path("trading_bot/master_integration.py").read_text(encoding="utf-8"),
        "trading_bot/master_integration.py",
    ) == []


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


def test_sentient_orchestrator_facade_is_fail_closed() -> None:
    """Sentient facade never constructs subsystems and cannot size/trade."""
    import warnings

    from trading_bot.sentient_core.sentient_orchestrator import SentientOrchestrator

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        facade = SentientOrchestrator()

    assert any(item.category is DeprecationWarning for item in captured)
    assert facade.is_running is False
    assert facade.is_ready() is False
    assert facade.calculate_position_size("EURUSD", 1.1, 0.005) == 0.0
    allowed, _reason = facade.should_trade(0.99)
    assert allowed is False
    status = facade.get_status()
    assert status.total_pnl == 0.0
    # Legacy subsystems with side effects must not be constructed.
    assert not hasattr(facade, "network_sentinel")
    assert not hasattr(facade, "profit_maximizer")
    assert not hasattr(facade, "code_evolver")


@pytest.mark.asyncio
async def test_recursive_improvement_orchestrator_cannot_self_deploy() -> None:
    """Legacy RSIE facade spawns no loops and no approval-deploy watcher."""
    import warnings

    from trading_bot.recursive_improvement.orchestrator import (
        RecursiveImprovementOrchestrator,
    )

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        facade = RecursiveImprovementOrchestrator()

    assert any(item.category is DeprecationWarning for item in captured)
    await facade.start()
    assert facade.is_running is False
    assert facade.background_tasks == []
    # Introspection stubs remain, but cannot run or deploy.
    assert set(facade.loops) == {"evaluation", "strategy", "risk", "feature", "meta"}
    with pytest.raises(PermissionError):
        await facade.loops["strategy"].run_cycle()
    with pytest.raises(PermissionError):
        await facade.loops["strategy"].deploy_improvement(object())
    summary = facade.get_comprehensive_summary()
    assert summary["is_running"] is False
    assert "recursive_self_improvement" in summary["canonical_rsi"]


@pytest.mark.asyncio
async def test_orchestration_event_bus_rejects_trading_events() -> None:
    """Legacy pub/sub bus cannot route decision/capital events."""
    from trading_bot.orchestration.event_bus import Event, EventBus

    bus = EventBus()
    with pytest.raises(PermissionError):
        await bus.publish(Event(type="TRADE_EXECUTION", data={}))
    with pytest.raises(PermissionError):
        await bus.publish(Event(type="ORDER_SUBMIT", data={}))
    # Non-trading service events still work.
    await bus.publish(Event(type="service_initialized", data={}))
    assert bus.get_statistics()["events_published"] == 1


def test_service_manager_health_loop_is_disabled() -> None:
    """ServiceManager cannot spawn its parallel health-monitor task."""
    import warnings

    from trading_bot.orchestration.service_managers import DataServiceManager

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        manager = DataServiceManager()
        manager._start_health_monitoring()

    assert manager._health_check_task is None
    assert any(item.category is DeprecationWarning for item in captured)


def test_master_risk_manager_warns_no_authority() -> None:
    """MASTER_risk_manager is an analyzer, not a sizing authority."""
    import warnings

    from trading_bot.risk.MASTER_risk_manager import MasterRiskManager

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        manager = MasterRiskManager(config={"enable_ml": False})

    assert manager is not None
    assert any(item.category is DeprecationWarning for item in captured)


def test_ingestion_orchestrator_standalone_main_is_disabled() -> None:
    """The standalone ingestion pipeline entry point must refuse to run."""
    import asyncio

    try:
        from trading_bot.ingestion.orchestrator import main
    except Exception as exc:  # pragma: no cover - optional deps missing
        pytest.skip(f"ingestion orchestrator not importable: {exc}")

    with pytest.raises(SystemExit):
        asyncio.run(main())


@pytest.mark.asyncio
async def test_csc_governance_stage_fails_closed_on_denial() -> None:
    """A missing/denying governance gate rejects before shield/bus."""
    from trading_bot.core.csc.controller import CognitiveSystemController

    class Deny:
        async def authorize(self, action, payload, context):
            return None

    csc = CognitiveSystemController()
    csc.governance_gate = Deny()
    csc._governance_gate_resolved = True

    terminal = await csc._stage_governance({"trade_id": "t1"}, {}, None, "t1")
    assert terminal is not None
    assert "Governance" in terminal.decision.dominant_rejection_reason


@pytest.mark.asyncio
async def test_csc_governance_stage_binds_receipt_on_approval() -> None:
    from trading_bot.core.csc.controller import CognitiveSystemController
    from trading_bot.foundation.contracts import ApprovalDecision

    class Approve:
        async def authorize(self, action, payload, context):
            return ApprovalDecision(True, "req-1", "approved")

    csc = CognitiveSystemController()
    csc.governance_gate = Approve()
    csc._governance_gate_resolved = True

    proposal = {"trade_id": "t2", "quantity": 1.0}
    terminal = await csc._stage_governance(proposal, {}, None, "t2")
    assert terminal is None
    assert proposal["governance_receipt"]


@pytest.mark.asyncio
async def test_csc_risk_check_clamps_to_approved_quantity() -> None:
    """CanonicalRiskService sizing authority wins over the proposal."""
    from trading_bot.core.csc.controller import CognitiveSystemController
    from trading_bot.foundation.contracts import RiskDecision

    class Risk:
        async def evaluate_action(self, proposal, obs):
            return RiskDecision(True, "d1", "ok", approved_quantity=0.5)

    csc = CognitiveSystemController()
    csc.risk_engine = Risk()

    proposal = {"trade_id": "t3", "quantity": 1.0}
    terminal, decision = await csc._stage_risk_check(proposal, {}, "t3")
    assert terminal is None
    assert proposal["quantity"] == 0.5
    assert proposal["quantity_clamped_by_risk"] is True


def test_strategy_portfolio_families_have_no_reachable_capital_or_loops() -> None:
    """Wave-4 gate: signal/strategy/portfolio families may advise only —
    capital-path members must be quarantined and none may be runtime-reachable
    or start loops."""
    import json

    manifest_path = Path(__file__).resolve().parents[2] / "ARCHITECTURE_LEGACY_CLASSIFICATION.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    families = (
        "trading_bot/strategies/",
        "trading_bot/portfolio",
        "trading_bot/position",
        "trading_bot/signals/",
        "trading_bot/alpha_engine",
    )
    violations = []
    for row in manifest["modules"]:
        path = row["path"]
        if not path.startswith(families):
            continue
        if row.get("runtime_reachable") and (
            row.get("direct_capital_path") or row.get("starts_loop")
        ):
            violations.append((path, "reachable capital/loop"))
        if row.get("direct_capital_path") and row.get("classification") != "quarantine":
            violations.append((path, "capital path not quarantined"))
    assert violations == []


@pytest.mark.parametrize(
    "relative",
    [
        "trading_bot/adaptive_systems/master_controller.py",
        "trading_bot/brain/central_controller.py",
        "trading_bot/critical_fixes/master_safety_orchestrator.py",
        "trading_bot/ingestion/orchestrator.py",
        "trading_bot/integration/master_engine.py",
        "trading_bot/integration/master_integrator.py",
        "trading_bot/orchestration/master_orchestrator.py",
        "trading_bot/recursive_improvement/orchestrator.py",
        "trading_bot/sentient_core/sentient_orchestrator.py",
        # Wave-2 risk/governance/service monitors — advisory only
        "trading_bot/services/risk_service.py",
        "trading_bot/services/compliance_service.py",
        "trading_bot/services/approval_service.py",
        "trading_bot/safety/autonomous_safety_enforcer.py",
        "trading_bot/safety/runtime_risk_monitor.py",
        "trading_bot/realtime/realtime_risk.py",
        "trading_bot/decision_governance/governance_governor.py",
        "trading_bot/decision_governance/monitoring.py",
        "trading_bot/decision_governance/self_inspection.py",
        "trading_bot/decision_governance/continuous_capability_discovery.py",
        "trading_bot/decision_governance/unified_intelligence.py",
        "trading_bot/meta_governance/meta_agent_governance.py",
        "trading_bot/unified_approval/notification_system.py",
        # Wave-3 service/monitor surfaces (adapter plumbing stays exempt)
        "trading_bot/services/broker_service.py",
        "trading_bot/services/brokers_service.py",
        "trading_bot/connectors/exchange_monitor.py",
        "trading_bot/connectivity/venue_outage_detector.py",
        # Wave-6 research surfaces — research_only, no detached workers
        "trading_bot/autonomous_superintelligence/experiment_engine.py",
        "trading_bot/services/alpha_research_service.py",
        "trading_bot/services/backtesting_service.py",
        # Wave-4 strategy/signal/position loops — advisory/research only
        "trading_bot/alpha_evolve/parallel_evaluator.py",
        "trading_bot/alphaalgo_core/alphaalgo_meta_system.py",
        "trading_bot/apex_fi/alpha_mining.py",
        "trading_bot/auto_optimizer/strategy_optimizer.py",
        "trading_bot/critical_fixes/position_state_manager.py",
        "trading_bot/ml/offline_rl/alphaalgo_autonomous_system.py",
        "trading_bot/position/realtime_pnl.py",
        "trading_bot/realtime/realtime_signal_engine.py",
        "trading_bot/services/alpha_engine_service.py",
        "trading_bot/services/alphaalgo_core_service.py",
        "trading_bot/services/alphaalgo_institutional_service.py",
        "trading_bot/services/alphaalgo_v2_service.py",
        "trading_bot/services/portfolio_service.py",
        "trading_bot/services/position_service.py",
        "trading_bot/services/signals_service.py",
        "trading_bot/services/strategy_service.py",
        "trading_bot/signals/signal_lifecycle.py",
        "trading_bot/trading/position_reconciliation.py",
        # Wave-5 AI/agent loops — advisory capabilities, never authorities
        "trading_bot/autonomous_superintelligence/agent_coordinator.py",
        "trading_bot/autonomous_superintelligence/autonomous_trading_bridge.py",
        "trading_bot/autonomous_superintelligence/enhanced_integration.py",
        "trading_bot/autonomous_superintelligence/trading_integration.py",
        "trading_bot/brain/brain_architecture.py",
        "trading_bot/core_agent_system/integrated_system.py",
        "trading_bot/core_agent_system/memory_system.py",
        "trading_bot/intelligence/knowledge_action_bridge.py",
        "trading_bot/market_intelligence/data_monitoring.py",
        "trading_bot/market_intelligence/performance_optimization.py",
        "trading_bot/services/agents2_service.py",
        "trading_bot/services/agents_service.py",
        "trading_bot/services/brain_service.py",
        "trading_bot/services/integrated_brain_service.py",
        "trading_bot/services/intelligence_directorate_service.py",
        "trading_bot/services/market_intelligence_service.py",
    ],
)
def test_legacy_orchestrators_have_no_worker_spawn(relative: str) -> None:
    """Wave-1 gate: no legacy orchestrator/master/controller may retain a
    live loop, worker, or thread spawn — even inside preserved _Legacy*
    classes."""
    root = Path(__file__).resolve().parents[2]
    source = (root / relative).read_text(encoding="utf-8")
    assert boundary_violations(source, relative) == []
    assert "create_task" not in source or "_Legacy" not in source


def test_aamis_shim_warns_and_abstains() -> None:
    """AAMIS compatibility shim warns and returns a non-authoritative HOLD."""
    import asyncio
    import warnings

    try:
        from trading_bot.aamis_v3.aamis_master_orchestrator import (
            AAMISMasterOrchestrator,
        )
    except Exception as exc:  # pragma: no cover - optional deps missing
        pytest.skip(f"aamis shim not importable: {exc}")

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        shim = AAMISMasterOrchestrator()

    assert any(item.category is DeprecationWarning for item in captured)
    report = asyncio.run(shim.analyze_market({"price": 1.1}))
    assert report.decision.action == "HOLD"
    assert report.decision.position_size_multiplier == 0.0
    assert shim.get_status()["authoritative"] is False


@pytest.mark.asyncio
async def test_unified_trading_system_is_runtime_facade() -> None:
    """UnifiedTradingSystem delegates lifecycle to ModularMonolithRuntime and
    cannot analyze-to-execute outside the canonical path."""
    import warnings

    try:
        from trading_bot.unified_architecture.unified_trading_system import (
            UnifiedTradingSystem,
        )
    except Exception as exc:  # pragma: no cover - optional deps missing
        pytest.skip(f"unified trading system not importable: {exc}")

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        system = UnifiedTradingSystem()

    assert any(item.category is DeprecationWarning for item in captured)
    decision = await system.analyze_symbol("EURUSD")
    assert decision.action == "HOLD"
    assert decision.position_size == 0
    result = await system.execute_decision(decision)
    assert result["executed"] is False
    assert system.get_status()["canonical_runtime"] == "ModularMonolithRuntime"
    assert system.get_status()["authoritative"] is False


@pytest.mark.asyncio
async def test_legacy_rsie_start_spawns_no_workers(tmp_path: Path) -> None:
    """The preserved _Legacy RSIE class must not create background tasks."""
    from trading_bot.recursive_improvement.orchestrator import (
        _LegacyRecursiveImprovementOrchestrator,
    )

    legacy = _LegacyRecursiveImprovementOrchestrator(
        config={"storage_path": str(tmp_path / "rsie")}
    )
    await legacy.start()
    assert legacy.background_tasks == []


def test_manifest_records_external_surfaces_and_dynamic_imports() -> None:
    """Regenerated manifest must cover root/scripts surfaces + dynamic loads."""
    import json

    manifest_path = Path(__file__).resolve().parents[2] / "ARCHITECTURE_LEGACY_CLASSIFICATION.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    surfaces = manifest["external_surfaces"]
    assert len(surfaces) >= 200
    for row in surfaces:
        if row["direct_capital_path"]:
            assert row["classification"] == "quarantine"
    assert manifest["summary"]["external_capital_paths"] > 0
    assert manifest["summary"]["dynamic_import_modules"] >= 0
    assert manifest["summary"]["credential_access_modules"] >= 0


@pytest.mark.asyncio
async def test_legacy_experiment_engine_cannot_self_deploy() -> None:
    """Autonomous model deployment is the parallel-promotion path RSI must
    never have: deploy_model refuses unconditionally."""
    from trading_bot.autonomous_superintelligence.experiment_engine import (
        ContinuousExperimentEngine,
    )
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        engine = ContinuousExperimentEngine({"storage_path": tmp})
        with pytest.raises(PermissionError):
            await engine.deploy_model("any-model")


def test_external_capital_surfaces_are_quarantined_and_guarded() -> None:
    """Every standalone surface that can move capital must be quarantined
    AND refuse/delegate at entry — an unguarded capital launcher is a live
    bypass of the canonical runtime."""
    manifest = json.loads(
        (ROOT / "ARCHITECTURE_LEGACY_CLASSIFICATION.json").read_text(encoding="utf-8")
    )
    unguarded = [
        r["path"]
        for r in manifest["external_surfaces"]
        if r["direct_capital_path"]
        and (r["classification"] != "quarantine" or not r.get("guarded_at_entry"))
    ]
    assert unguarded == [], f"unguarded capital-capable surfaces: {unguarded}"
    assert manifest["summary"].get("unguarded_capital_surfaces", 0) == 0
    # Loop-spawning CLIs that touch trading_bot must also be guarded;
    # pure standalone monitors (no trading_bot imports) are external ops
    # tools and cannot reach runtime authority.
    unguarded_loops = [
        r["path"]
        for r in manifest["external_surfaces"]
        if r["starts_loop"] and r["cli_entrypoint"] and not r.get("guarded_at_entry")
        and any(
            imp == "trading_bot" or imp.startswith("trading_bot.")
            for imp in r["imports"]
        )
    ]
    assert unguarded_loops == [], f"unguarded loop-spawning CLIs: {unguarded_loops}"
    assert manifest["summary"].get("unguarded_loop_surfaces", 0) == 0


def test_adapter_review_queue_covers_all_adapters() -> None:
    """Every adapter-classified module must carry a review_priority in 0..3
    and the queue counts must partition the adapter set."""
    manifest = json.loads(
        (ROOT / "ARCHITECTURE_LEGACY_CLASSIFICATION.json").read_text(encoding="utf-8")
    )
    adapters = [r for r in manifest["modules"] if r["classification"] == "adapter"]
    assert adapters, "manifest has no adapter rows to prioritize"
    queue = manifest["summary"]["adapter_review_queue"]
    assert set(queue) == {"0", "1", "2", "3"}
    assert sum(queue.values()) == len(adapters)
    for row in adapters:
        assert row.get("review_priority") in (0, 1, 2, 3)
        if row["runtime_reachable"]:
            assert row["review_priority"] == 0, f"reachable adapter not P0: {row['path']}"
        elif "credential_access" in row["secondary_tags"]:
            assert row["review_priority"] == 1


def test_adapter_worker_exemptions_do_not_hide_capital_violations() -> None:
    """ADAPTER_WORKER_PATHS exempts connection-plumbing loops only — a
    capital call in an exempted file outside the broker prefix must still
    violate."""
    from trading_bot.foundation.legacy_convergence import ADAPTER_WORKER_PATHS

    loop_source = "import asyncio\nasyncio.create_task(run())\n"
    for path in ADAPTER_WORKER_PATHS:
        assert "independent lifecycle/worker loop" not in boundary_violations(
            loop_source, path
        )
    capital_source = "broker.place_order(x)\nasyncio.create_task(run())\n"
    violations = boundary_violations(
        capital_source, "trading_bot/production/interactive_brokers_live.py"
    )
    assert "direct capital call outside execution/broker adapter" in violations
    assert "independent lifecycle/worker loop" not in violations


def test_scanner_flags_credential_access() -> None:
    """Secret reads outside declared boundaries must be review-visible."""
    source = """
import os
api_key = os.getenv("BROKER_API_KEY")
"""
    result = scan_source(source, "trading_bot/strategies/needs_key.py")
    assert "credential_access" in result["secondary_tags"]

    clean = """
def compute(x):
    return x * 2
"""
    result = scan_source(clean, "trading_bot/strategies/pure.py")
    assert "credential_access" not in result["secondary_tags"]
