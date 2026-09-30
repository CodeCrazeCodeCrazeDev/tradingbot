"""P0 conformance: test evidence for runtime-reachable adapter modules.

Every module here sits inside the live import graph but was classified as a
generic ``adapter`` with zero test evidence. These tests prove each one is
either (a) subordinate to a typed port, (b) an advisory stub with no worker
or capital authority, or (c) a definition surface — never a parallel
production authority.
"""

from __future__ import annotations

import threading
import warnings

import pytest

from trading_bot.foundation import (
    DecisionProposal,
    Instrument,
    InstrumentType,
    PortfolioSnapshot,
    RiskState,
    Signal,
)


def _proposal(direction: str, quantity: float, entry: float,
              stop: float, tp: float | None) -> DecisionProposal:
    instrument = Instrument("EURUSD", InstrumentType.FX, "paper")
    signal = Signal(
        "sig-p0",
        instrument,
        direction,
        0.8,
        metadata={
            "quantity": quantity,
            "entry_price": entry,
            "stop_loss": stop,
            "take_profit": tp or 0.0,
        },
    )
    state = RiskState("acct", 10000, 0.01, 0.0, 0.01, 0)
    return DecisionProposal("dec-p0", signal, PortfolioSnapshot("acct", 10000, 10000), state)


# ---------------------------------------------------------------------------
# risk_management/risk_engine.py -> TradeAssessmentPolicyAdapter (veto-only)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_risk_engine_vetoes_breach_through_policy_adapter() -> None:
    from trading_bot.risk.policy_adapters import TradeAssessmentPolicyAdapter
    from trading_bot.risk_management.risk_engine import RiskEngine

    engine = RiskEngine({"portfolio_value": 10000.0})
    adapter = TradeAssessmentPolicyAdapter("legacy_risk_engine", engine)

    # 4.5% single-trade loss vs the 2.0% default limit -> veto.
    risky = _proposal("long", quantity=10000.0, entry=1.10, stop=1.05, tp=None)
    result = await adapter.evaluate(risky, risky.risk_state)
    assert result["approved"] is False
    assert result["alert_count"] >= 1


@pytest.mark.asyncio
async def test_risk_engine_passes_sane_trade_as_evidence() -> None:
    from trading_bot.risk.policy_adapters import TradeAssessmentPolicyAdapter
    from trading_bot.risk_management.risk_engine import RiskEngine

    engine = RiskEngine({"portfolio_value": 10000.0})
    adapter = TradeAssessmentPolicyAdapter("legacy_risk_engine", engine)

    sane = _proposal("long", quantity=1000.0, entry=1.10, stop=1.09, tp=1.12)
    result = await adapter.evaluate(sane, sane.risk_state)
    # Admissible evidence only — the adapter never produces a size or executes.
    assert result["approved"] is True
    assert "approved_quantity" not in result


# ---------------------------------------------------------------------------
# world_model/v2_core.py -> ScenarioWorldModelAdapter (advisory only)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scenario_simulator_adapts_to_world_model_port() -> None:
    torch = pytest.importorskip("torch")
    from trading_bot.foundation.ports import WorldModelPort
    from trading_bot.world_model.port_adapter import ScenarioWorldModelAdapter
    from trading_bot.world_model.v2_core import (
        FutureScenarioSimulator,
        PredictiveMarketCore,
    )

    core = PredictiveMarketCore(latent_dim=16, n_heads=2, n_layers=1)
    simulator = FutureScenarioSimulator(core, horizon=4)
    adapter = ScenarioWorldModelAdapter(simulator)
    assert isinstance(adapter, WorldModelPort)

    result = await adapter.simulate(
        {"latent": torch.zeros(1, 16).tolist()}, horizon=4
    )
    assert result["advisory_only"] is True
    assert result["scenarios"], "simulator produced no scenarios"
    for scenario in result["scenarios"]:
        assert 0.0 <= scenario["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_scenario_simulator_has_no_intervention_authority() -> None:
    pytest.importorskip("torch")
    from trading_bot.world_model.port_adapter import ScenarioWorldModelAdapter
    from trading_bot.world_model.v2_core import (
        FutureScenarioSimulator,
        PredictiveMarketCore,
    )

    adapter = ScenarioWorldModelAdapter(
        FutureScenarioSimulator(PredictiveMarketCore(latent_dim=16, n_heads=2, n_layers=1))
    )
    with pytest.raises(PermissionError):
        await adapter.intervene({}, {"do": "set_price"})


# ---------------------------------------------------------------------------
# ml/offline_rl/alphaalgo_autonomous_system.py — advisory; no worker threads
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_autonomous_system_start_spawns_no_threads() -> None:
    np = pytest.importorskip("numpy")
    pytest.importorskip("pandas")
    from trading_bot.ml.offline_rl.alphaalgo_autonomous_system import (
        AlphaAlgoAutonomousSystem,
    )

    baseline = set(threading.enumerate())
    system = AlphaAlgoAutonomousSystem(state_dim=4, action_dim=3)
    system.start()  # de-looped: start() is now synchronous and thread-free
    try:
        assert set(threading.enumerate()) - baseline == set()
        assert system.training_thread is None
        assert system.monitoring_thread is None
    finally:
        system.stop()

    # The legacy inference delegation is broken (fails closed — it cannot
    # fabricate an action); canonical capabilities own inference.
    with pytest.raises(AttributeError):
        system.get_action(np.zeros(4, dtype=np.float32))


# ---------------------------------------------------------------------------
# Stub orchestrators + broker interface — deprecation + no authority
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evolution_layer_stub_warns_and_starts_no_workers() -> None:
    from trading_bot.evolution_layer import EvolutionLayerOrchestrator

    baseline = set(threading.enumerate())
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        orch = EvolutionLayerOrchestrator()
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    await orch.start()
    assert set(threading.enumerate()) - baseline == set()
    await orch.stop()


def test_human_layer_orchestrator_warns_on_construction() -> None:
    from trading_bot.human_layer import HumanLayerOrchestrator

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        HumanLayerOrchestrator()
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_telemetry_manager_stub_warns_on_construction() -> None:
    from trading_bot.telemetry import TelemetryManager

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        TelemetryManager()
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


@pytest.mark.asyncio
async def test_broker_interface_base_warns_and_holds_no_session() -> None:
    """The live-capable base is a definition surface: construction warns and
    no network session exists until connect() is called explicitly."""
    # Async test: importing trading_bot.broker pulls ib_insync/eventkit, which
    # requires an active event loop.
    from trading_bot.broker.broker_interface import BrokerInterface

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        broker = BrokerInterface("k", "s", "https://example.invalid", testnet=True)
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert broker.session is None
