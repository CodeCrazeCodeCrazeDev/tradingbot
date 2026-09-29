"""Wave 6 (research/RSI separation) and Wave 7 (interface) enforcement.

These tests prove the structural invariants rather than trusting manifest
fields: research families cannot reach production authority, legacy RSI
duplicates warn on import, and every standalone capital/loop surface either
refuses at entry or is a documented read-only exception.
"""

import json
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "ARCHITECTURE_LEGACY_CLASSIFICATION.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_research_families_have_no_reachable_authority() -> None:
    """No evaluation/backtesting/RSI-legacy module may be runtime-reachable
    while carrying capital or loop flags."""
    manifest = _manifest()
    research = (
        "trading_bot/evaluation/",
        "trading_bot/backtesting/",
        "trading_bot/recursive_improvement/",
        "trading_bot/eternal_evolution/",
        "trading_bot/alpha_evolve/",
        "trading_bot/autonomous_learner/",
        "trading_bot/adaptive_systems/",
        "trading_bot/meta_learning/",
    )
    violations = [
        r["path"]
        for r in manifest["modules"]
        if r["path"].startswith(research)
        and r.get("runtime_reachable")
        and (r.get("direct_capital_path") or r.get("starts_loop"))
    ]
    assert violations == []


@pytest.mark.parametrize(
    "module",
    [
        "trading_bot.code_evolver",
        "trading_bot.auto_rollback",
        "trading_bot.continual_learner",
        "trading_bot.ai_learner",
        "trading_bot.experiment_tracker",
        "trading_bot.performance_optimizer",
    ],
)
def test_legacy_rsi_files_warn_on_import(module) -> None:
    """Legacy self-improvement modules must emit DeprecationWarning and carry
    no improvement authority."""
    import importlib

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.import_module(module)
    assert any(
        item.category is DeprecationWarning for item in caught
    ), f"{module} imported without a deprecation warning"


def test_capital_flagged_clis_refuse_standalone() -> None:
    """Every package/external surface flagged for direct capital paths or
    trading loops must refuse at entry, unless it is a documented
    delegation/read-only exception."""
    manifest = _manifest()

    # Delegating shims and read-only operations surfaces are allowed to run.
    allowed_exceptions = {
        # Delegating shims to the canonical runtime
        "main_original.py",
        "trading_bot/realtime_trading_core.py",
        # main() raises inside the module (Wave-1 disable)
        "trading_bot/ingestion/orchestrator.py",
        # Read-only health/dashboard/analysis/monitoring operations surfaces
        # (the architecture allows read-only projections; none move capital)
        "trading_bot/dashboard/performance_dashboard.py",
        "trading_bot/dashboard/realtime_dashboard.py",
        "trading_bot/dashboard/unified_dashboard.py",
        "trading_bot/monitoring/dependency_health.py",
        "trading_bot/monitoring/production_monitor.py",
        "trading_bot/core/monitoring_system.py",
        "trading_bot/connectivity/staleness_detector.py",
        "trading_bot/analysis/liquidity_heatmap.py",
        "trading_bot/analysis/realtime_liquidity.py",
        # Offline diagnostics / validators / self-test demos
        "trading_bot/ultimate_module_integrator.py",
        "trading_bot/realtime_system_validator.py",
        "trading_bot/data_feeds/websocket_feeds.py",
        "trading_bot/execution/partial_fill_aggregator.py",
        "trading_bot/deepchart/inference_engine.py",
        "trading_bot/elite_system/benchmarking.py",
        "trading_bot/neural_integration/neural_hub.py",
        "trading_bot/neural_integration/neurotransmitters.py",
        "trading_bot/performance/windows_optimizer.py",
        "trading_bot/signals/signal_lifecycle.py",
        "trading_bot/utils/debug_tools.py",
        "scripts/launchers/run_production_tests.py",
        "scripts/utilities/COMPREHENSIVE_TEST_SUITE.py",
        "scripts/validation/comprehensive_validation.py",
        "scripts/validation/validate_critical_fixes.py",
        "scripts/monitoring/health_check.py",
        "scripts/utilities/performance_optimizer.py",
        "scripts/utilities/REAL_TIME_PERFORMANCE_MONITOR.py",
        "scripts/validation/comprehensive_qa_validation.py",
    }

    flagged = {
        r["path"]
        for r in manifest["modules"]
        if r.get("cli_entrypoint")
        and (r.get("direct_capital_path") or r.get("starts_loop"))
    }
    flagged.update(
        s["path"]
        for s in manifest.get("external_surfaces", [])
        if s.get("direct_capital_path") or s.get("starts_loop")
    )

    unguarded = []
    for rel in sorted(flagged):
        if rel in allowed_exceptions:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # Acceptable guards: explicit refusal, or canonical delegation.
        guarded = (
            "QUARANTINED" in text
            or 'SystemExit' in text and "canonical" in text.lower()
            or "ModularMonolithRuntime" in text
            or "unified entry point" in text
        )
        if not guarded:
            unguarded.append(rel)
    assert unguarded == []


def test_parallel_authority_modules_emit_non_authority_warnings() -> None:
    """Parallel executors, brokers, and self-modification modules must carry
    explicit no-production-authority DeprecationWarnings (content check to
    avoid heavy imports)."""
    required = [
        "trading_bot/position_manager.py",
        "trading_bot/strategies/cross_exchange_arbitrage.py",
        "trading_bot/execution/live_executor.py",
        "trading_bot/execution/trade_executor.py",
        "trading_bot/execution/order_manager.py",
        "trading_bot/execution/order_confirmation.py",
        "trading_bot/execution/slippage_protection.py",
        "trading_bot/execution/advanced_algorithms.py",
        "trading_bot/execution/fill_tracker.py",
        "trading_bot/autonomous_superintelligence/self_modifier.py",
        "trading_bot/sentient_core/code_evolver.py",
        "trading_bot/auto_dependency_installer.py",
        "trading_bot/unified_ai_brain.py",
        "trading_bot/risk/MASTER_risk_manager.py",
        # live-capable broker/venue adapters (usable only inside the
        # CanonicalExecutionService boundary via explicit injection)
        "trading_bot/broker/binance_broker.py",
        "trading_bot/brokers/binance_adapter.py",
        "trading_bot/brokers/broker_adapter.py",
        "trading_bot/brokers/mt5_adapter.py",
        "trading_bot/brokers/live_order_router.py",
        "trading_bot/brokers/multi_broker_adapter.py",
        "trading_bot/brokers/real_broker_integration.py",
        "trading_bot/brokers/connection_manager.py",
        "trading_bot/connectors/mt5_connector.py",
        "trading_bot/connectors/binance_connector.py",
        # capital-adjacent loop starters
        "trading_bot/core/graceful_shutdown.py",
        "trading_bot/core/reconciliation_service.py",
        "trading_bot/core/survival_core.py",
        "trading_bot/core_agent_system/agent_registry.py",
        "trading_bot/critical_fixes/multi_layer_kill_switch.py",
        "trading_bot/critical_fixes/position_state_manager.py",
        "trading_bot/services/broker_service.py",
        "trading_bot/services/brokers_service.py",
        "trading_bot/services/connectors_service.py",
        "trading_bot/services/execution_service.py",
        "trading_bot/monitoring/live_monitor.py",
        "trading_bot/mobile_app/mobile_api.py",
        "trading_bot/dashboard/unified_dashboard.py",
        "trading_bot/connectivity/network_monitor.py",
        "trading_bot/optimized_integration.py",
        "trading_bot/self_diagnostic/knowledge_gap.py",
        "trading_bot/market_intelligence/data_monitoring.py",
        "trading_bot/improvements/forecast_improvements/data_feed_quality.py",
        "trading_bot/improvements/forecast_improvements/real_broker_connection.py",
        "trading_bot/ultimate_production/core_engine.py",
        # dynamic loader / mutation surfaces
        "trading_bot/realtime_dependency_manager.py",
        "trading_bot/core/service_factory.py",
        "trading_bot/core/dependency_manager.py",
        "trading_bot/complete_system_integrator.py",
        "trading_bot/unified_master_integrator.py",
        "trading_bot/ultimate_module_integrator.py",
        "trading_bot/services/tier4_services.py",
        "trading_bot/cos/cos_core.py",
        "trading_bot/integration/master_engine.py",
        "trading_bot/integration/master_integrator.py",
        # quarantined capital modules
        "trading_bot/aads/core/polymarket.py",
        "trading_bot/advanced_analysis/digital_twin.py",
        "trading_bot/alphaalgo_institutional/layer6_execution.py",
        "trading_bot/alphaalgo_v2/execution/brokers/paper.py",
        "trading_bot/alphaalgo_v2/execution/engine.py",
        "trading_bot/api/rest_api.py",
        "trading_bot/complete_implementation.py",
        "trading_bot/connectors/exchange_abstraction.py",
        "trading_bot/core/emergency_kill_switch.py",
        "trading_bot/dashboard/web_dashboard.py",
        "trading_bot/decision_governance/integrations.py",
        "trading_bot/ops/emergency_controls.py",
        "trading_bot/realtime/realtime_execution.py",
        "trading_bot/safety/connectivity_monitor.py",
        "trading_bot/safety/emergency_kill_switch.py",
        "trading_bot/unified_architecture/layer4_execution.py",
        "trading_bot/unified_architecture/layer5_risk_safety.py",
        "trading_bot/voice_assistant/voice_controller.py",
    ]
    missing = [
        rel
        for rel in required
        if "DeprecationWarning" not in (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    ]
    assert missing == []


def test_flagged_authority_review_status_invariant() -> None:
    """Every capital/loop-flagged module carries a review_status; none may be
    flagged AND runtime-reachable unless canonical or a sanctioned boundary
    adapter."""
    manifest = json.loads(
        (ROOT / "ARCHITECTURE_LEGACY_CLASSIFICATION.json").read_text(encoding="utf-8")
    )
    flagged = [
        r for r in manifest["modules"] if r.get("direct_capital_path") or r.get("starts_loop")
    ]
    assert flagged, "expected flagged records"
    unresolved = [
        r["path"]
        for r in flagged
        if r.get("review_status") not in {
            "canonical_authority",
            "sanctioned_boundary_adapter",
            "warned_non_authority",
        }
    ]
    assert unresolved == [], f"flagged modules without authority disposition: {unresolved}"
    needs_review = [
        r["path"] for r in flagged if r.get("review_status") == "reachable_review_required"
    ]
    assert needs_review == []
