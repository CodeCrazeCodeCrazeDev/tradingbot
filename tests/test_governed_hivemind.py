import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "trading_bot" / "hivemind" / "governed_hivemind.py"
SPEC = importlib.util.spec_from_file_location("governed_hivemind", MODULE_PATH)
governed_hivemind = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = governed_hivemind
SPEC.loader.exec_module(governed_hivemind)


AgentSignalProfile = governed_hivemind.AgentSignalProfile
HivemindCapabilityStatus = governed_hivemind.HivemindCapabilityStatus
HivemindGateDecision = governed_hivemind.HivemindGateDecision
HivemindGovernanceConfig = governed_hivemind.HivemindGovernanceConfig
create_governed_hivemind = governed_hivemind.create_governed_hivemind


def _profile(
    agent_id,
    family,
    features,
    modalities,
    history,
    drawdown,
    exposure,
    regimes=None,
    failures=None,
):
    return AgentSignalProfile(
        agent_id=agent_id,
        signal_family=family,
        feature_set=set(features),
        data_modalities=set(modalities),
        signal_history=list(history),
        drawdown_signature=list(drawdown),
        exposure_vector=dict(exposure),
        regime_performance=regimes or {"trend": 0.2, "chop": 0.1},
        failure_tags=set(failures or []),
    )


def test_registry_includes_twenty_patterns_and_prohibits_self_replication():
    engine = create_governed_hivemind()

    specs = engine.list_capabilities()
    autopoietic = engine.get_capability("self_replicating_autopoietic_bot")
    social_report = engine.reject_dao_trade_control()

    assert len(specs) == 20
    assert autopoietic.status == HivemindCapabilityStatus.PROHIBITED
    assert social_report.decision == HivemindGateDecision.REJECT
    assert not social_report.direct_trade_allowed


def test_signal_diversity_rejects_correlated_price_transform_democracy():
    engine = create_governed_hivemind(
        HivemindGovernanceConfig(strict_missing_measurements=True)
    )
    profiles = [
        _profile(
            "rsi_agent",
            "technical",
            ["close", "rsi", "sma"],
            ["price_volume"],
            [0.1, 0.2, 0.4, 0.5, 0.6],
            [-0.01, -0.02, -0.04, -0.05],
            {"SPY": 1.0},
            failures=["trend_chop"],
        ),
        _profile(
            "macd_agent",
            "momentum",
            ["close", "ema", "macd"],
            ["price_volume"],
            [0.11, 0.19, 0.39, 0.52, 0.61],
            [-0.01, -0.021, -0.041, -0.052],
            {"SPY": 0.98},
            failures=["trend_chop"],
        ),
        _profile(
            "bollinger_agent",
            "mean_reversion",
            ["close", "sma", "bollinger"],
            ["price_volume"],
            [0.09, 0.21, 0.41, 0.49, 0.59],
            [-0.011, -0.019, -0.039, -0.051],
            {"SPY": 1.02},
            failures=["trend_chop"],
        ),
    ]

    audit = engine.audit_signal_diversity(profiles)
    guard = engine.guard_collective_vote(profiles, "BUY", proof_trace_id="trace_ok")

    assert not audit.passed
    assert "signal correlation is too high" in audit.rejection_reasons
    assert "too few independent data modalities" in audit.rejection_reasons
    assert guard.final_action == "HOLD"
    assert guard.decision == HivemindGateDecision.HOLD


def test_signal_diversity_allows_measured_independent_modalities():
    engine = create_governed_hivemind(
        HivemindGovernanceConfig(strict_missing_measurements=True)
    )
    profiles = [
        _profile(
            "macro_agent",
            "macro",
            ["rates", "dxy"],
            ["macro"],
            [0.8, -0.3, 0.1, -0.5, 0.2],
            [-0.01, -0.05, -0.02, -0.04, -0.03],
            {"USD": 0.4, "SPY": -0.1},
            regimes={"risk_on": 0.2, "risk_off": 0.4},
        ),
        _profile(
            "order_flow_agent",
            "order_flow",
            ["imbalance", "toxicity"],
            ["order_flow"],
            [-0.2, 0.7, -0.4, 0.1, 0.5],
            [-0.03, -0.01, -0.04, -0.02, -0.05],
            {"SPY": 0.2, "QQQ": 0.1},
            regimes={"open": 0.3, "close": 0.2},
        ),
        _profile(
            "options_agent",
            "options",
            ["skew", "iv_rank"],
            ["derivatives"],
            [0.1, 0.2, 0.8, -0.6, -0.3],
            [-0.05, -0.03, -0.01, -0.04, -0.02],
            {"VIX": 0.3, "SPY": -0.2},
            regimes={"high_vol": 0.3, "low_vol": 0.1},
        ),
    ]

    audit = engine.audit_signal_diversity(profiles)
    guard = engine.guard_collective_vote(profiles, "BUY", proof_trace_id="trace_ok")

    assert audit.passed
    assert guard.final_action == "BUY"
    assert guard.decision == HivemindGateDecision.APPROVE


def test_evolution_gate_quarantines_instead_of_naive_culling():
    engine = create_governed_hivemind()

    report = engine.evaluate_agent_evolution(
        "mean_reversion_bot",
        {
            "recent_sharpe": -0.8,
            "long_run_sharpe": 1.1,
            "regime_expected": False,
            "paper_trades": 80,
            "oos_windows": 5,
            "validation_passed": True,
            "cost_adjusted_edge": 0.002,
        },
    )

    assert report.decision == HivemindGateDecision.QUARANTINE
    assert report.quarantine_required
    assert any("regime mismatch" in reason for reason in report.reasons)


def test_ml_ensemble_rejects_missing_hard_validation_controls():
    engine = create_governed_hivemind()

    report = engine.validate_ml_ensemble(
        {
            "purged_walk_forward_validation": True,
            "transaction_cost_model": False,
            "slippage_model": False,
            "paper_sharpe_delta": 0.02,
            "cost_adjusted_edge": -0.001,
        }
    )

    assert report.decision == HivemindGateDecision.REJECT
    assert "transaction cost model" in report.missing_controls
    assert "slippage model" in report.missing_controls
    assert not report.direct_trade_allowed


def test_social_sentiment_is_capped_input_not_execution_authority():
    engine = create_governed_hivemind()

    report = engine.govern_social_sentiment(
        {
            "direct_execution_requested": True,
            "sentiment_velocity": True,
            "source_credibility": 0.9,
            "bot_manipulation_score": 0.1,
            "price_volume_confirmation": True,
            "event_classified": True,
            "position_size_pct": 0.01,
        }
    )

    assert report.decision == HivemindGateDecision.REJECT
    assert "social sentiment cannot directly control execution" in report.reasons
    assert not report.direct_trade_allowed


def test_manipulation_hivemind_rejects_front_running_intent():
    engine = create_governed_hivemind()

    report = engine.review_capability(
        "manipulation_anomaly_hivemind",
        {
            "proof_trace_id": "trace",
            "validation_gateway_passed": True,
            "paper_trading_passed": True,
            "cost_model_passed": True,
            "leakage_check_passed": True,
            "front_run_manipulation": True,
        },
    )

    assert report.decision == HivemindGateDecision.REJECT
    assert any("front-running manipulation" in reason for reason in report.reasons)
    assert not report.direct_trade_allowed
