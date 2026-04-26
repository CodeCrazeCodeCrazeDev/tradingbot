#!/usr/bin/env python3
"""Tests for the governed APEX-FI to Aletheia bridge."""

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).parent.parent / "trading_bot" / "apex_fi" / "aletheia_bridge.py"
SPEC = importlib.util.spec_from_file_location("apex_aletheia_bridge_direct", MODULE_PATH)
bridge = importlib.util.module_from_spec(SPEC)
sys.modules["apex_aletheia_bridge_direct"] = bridge
SPEC.loader.exec_module(bridge)


def _evidence():
    return (
        bridge.ApexEvidence("news-wire", "news", 0.91, "macro catalyst confirmed"),
        bridge.ApexEvidence("exchange-feed", "market_data", 0.93, "liquidity and spread stable"),
        bridge.ApexEvidence("filing-parser", "fundamental", 0.88, "earnings revision supports bias"),
    )


def _risk_parameters():
    return {
        "max_position_size": 0.02,
        "max_daily_loss": 0.015,
        "max_drawdown": 0.05,
        "stop_loss": 0.012,
        "take_profit": 0.028,
    }


def _validation():
    return {
        "invariant_tests_passed": True,
        "adversarial_tests_passed": True,
        "hidden_tests_passed": True,
        "out_of_sample_passed": True,
        "lookahead_bias_check_passed": True,
        "stress_tests_passed": True,
    }


def _safe_proposal(**overrides):
    payload = {
        "proposal_id": "apex-proposal-1",
        "symbol": "AAPL",
        "action": "BUY",
        "confidence": 0.91,
        "rationale": (
            "APEX model parliament agrees with liquidity-aware momentum, "
            "and Aletheia verifier requires constrained downside before promotion."
        ),
        "risk_parameters": _risk_parameters(),
        "validation": _validation(),
        "evidence": _evidence(),
        "risk_envelope": bridge.ApexRiskEnvelope(
            position_value=25_000,
            portfolio_nav=1_000_000,
            order_quantity=5_000,
            avg_daily_volume_20d=500_000,
            expected_drawdown=0.04,
            leverage=1.4,
        ),
        "expected_return": 0.03,
        "approval_evidence": "approval-ticket-123",
        "rollback_plan": "disable strategy, flatten exposure, notify risk desk",
    }
    payload.update(overrides)
    return bridge.ApexProposal(**payload)


def test_bridge_blocks_thin_evidence_and_missing_validation():
    controller = bridge.ApexAletheiaBridge()
    proposal = _safe_proposal(
        confidence=0.72,
        evidence=(_evidence()[0],),
        validation={"invariant_tests_passed": True},
    )

    decision = controller.evaluate(proposal, target_stage="paper")

    assert not decision.accepted
    assert decision.final_action == "NO_TRADE"
    assert any("too few evidence" in issue for issue in decision.issues)
    assert any("hidden tests" in issue for issue in decision.issues)


def test_bridge_allows_well_validated_paper_trade_promotion():
    controller = bridge.ApexAletheiaBridge()

    decision = controller.evaluate(_safe_proposal(), target_stage="paper")

    assert decision.accepted
    assert decision.final_action == "BUY"
    assert "paper_trade_validation" in decision.promotion_path
    assert decision.audit.evidence_count == 3


def test_bridge_requires_independent_governance_and_paper_metrics_for_live():
    controller = bridge.ApexAletheiaBridge()
    proposal = _safe_proposal()

    blocked = controller.evaluate(proposal, target_stage="live", approved_by="apex_fi")

    assert not blocked.accepted
    assert blocked.final_action == "NO_TRADE"
    assert any("independent human approval" in issue for issue in blocked.issues)
    assert any("paper trading Sharpe" in issue for issue in blocked.issues)

    approved = controller.evaluate(
        proposal,
        target_stage="live",
        governance_approved=True,
        approved_by="Jane Risk Officer",
        paper_trade_metrics={"sharpe_ratio": 1.55, "max_drawdown": 0.035},
    )

    assert approved.accepted
    assert approved.final_action == "BUY"
    assert "G0_governance_approval" in approved.promotion_path
    assert "rollback_armed" in approved.promotion_path


def test_bridge_blocks_protected_risk_limit_weakening():
    controller = bridge.ApexAletheiaBridge()
    proposal = _safe_proposal(
        protected_risk_changes={
            "MAX_POSITION_CONCENTRATION": {"old": 0.03, "new": 0.05},
            "MIN_VALIDATION_TSTAT": (2.0, 1.2),
        }
    )

    decision = controller.evaluate(proposal, target_stage="paper")

    assert not decision.accepted
    assert any("MAX_POSITION_CONCENTRATION" in issue for issue in decision.protected_risk_issues)
    assert any("MIN_VALIDATION_TSTAT" in issue for issue in decision.protected_risk_issues)


def test_bridge_blocks_constitutional_risk_breaches():
    controller = bridge.ApexAletheiaBridge()
    proposal = _safe_proposal(
        risk_envelope=bridge.ApexRiskEnvelope(
            position_value=50_000,
            portfolio_nav=1_000_000,
            order_quantity=25_000,
            avg_daily_volume_20d=200_000,
            expected_drawdown=0.09,
            leverage=6.0,
        )
    )

    decision = controller.evaluate(proposal, target_stage="paper")

    assert not decision.accepted
    assert any("position concentration" in issue for issue in decision.constitutional_issues)
    assert any("market impact" in issue for issue in decision.constitutional_issues)
    assert any("expected drawdown" in issue for issue in decision.constitutional_issues)
    assert any("leverage" in issue for issue in decision.constitutional_issues)


def test_bridge_adapts_aletheia_strategy_hypothesis_into_apex_proposal():
    controller = bridge.ApexAletheiaBridge()
    hypothesis = SimpleNamespace(
        hypothesis_id="hyp-1",
        confidence_score=0.9,
        rationale="Momentum hypothesis with explicit downside controls.",
        entry_rules=["enter long when signal persists for two sessions"],
        exit_rules=["exit on stop loss or failed momentum confirmation"],
        risk_parameters=_risk_parameters(),
        expected_performance={"expected_max_drawdown": 4.0, "expected_return": 3.0},
    )

    proposal = controller.from_strategy_hypothesis(
        hypothesis,
        symbol="MSFT",
        action="BUY",
        evidence=_evidence(),
        validation=_validation(),
    )
    decision = controller.evaluate(proposal, target_stage="paper")

    assert proposal.proposal_id == "hyp-1"
    assert proposal.risk_envelope.expected_drawdown == 0.04
    assert decision.accepted
