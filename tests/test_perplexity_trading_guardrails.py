#!/usr/bin/env python3
"""Tests for Perplexity trading research guardrails."""

from datetime import datetime, timedelta
import importlib.util
import sys
import types
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent.parent / "trading_bot" / "perplexity_trading"
PACKAGE_NAME = "perplexity_guard_direct"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PACKAGE_ROOT)]
sys.modules[PACKAGE_NAME] = package

core_spec = importlib.util.spec_from_file_location(
    f"{PACKAGE_NAME}.core_types",
    PACKAGE_ROOT / "core_types.py",
)
core = importlib.util.module_from_spec(core_spec)
sys.modules[f"{PACKAGE_NAME}.core_types"] = core
core_spec.loader.exec_module(core)

guard_spec = importlib.util.spec_from_file_location(
    f"{PACKAGE_NAME}.research_guardrails",
    PACKAGE_ROOT / "research_guardrails.py",
)
guard_module = importlib.util.module_from_spec(guard_spec)
sys.modules[f"{PACKAGE_NAME}.research_guardrails"] = guard_module
guard_spec.loader.exec_module(guard_module)

ApprovalStatus = core.ApprovalStatus
Citation = core.Citation
QACheckResult = core.QACheckResult
RetrievalSource = core.RetrievalSource
TradingDecision = core.TradingDecision
PerplexityTradingGuard = guard_module.PerplexityTradingGuard
ResearchGuardConfig = guard_module.ResearchGuardConfig


def _citation(confidence=0.9, age_seconds=10, source=RetrievalSource.NEWS, raw_data=None, data_point="EURUSD macro update"):
    return Citation(
        source_type=source,
        source_name="test-source",
        timestamp=datetime.utcnow() - timedelta(seconds=age_seconds),
        data_point=data_point,
        confidence=confidence,
        url="https://example.com/research",
        raw_data=raw_data,
    )


def test_guard_blocks_trade_with_insufficient_or_stale_citations():
    guard = PerplexityTradingGuard(
        ResearchGuardConfig(min_citations_for_trade=2, max_data_age_seconds=60)
    )
    decision = TradingDecision(
        query_id="q1",
        action="BUY",
        symbol="EURUSD",
        confidence=0.9,
        citations=[_citation(age_seconds=120)],
        approval_status=ApprovalStatus.PENDING,
    )

    guarded, report = guard.apply(decision)

    assert not report.accepted
    assert report.final_action == "NO_TRADE"
    assert report.stale_citation_count == 1
    assert guarded.action == "NO_TRADE"
    assert guarded.approval_status == ApprovalStatus.REJECTED
    assert any("RESEARCH_GUARD" in step for step in guarded.reasoning_chain)


def test_guard_blocks_failed_qa_and_low_confidence_trade():
    guard = PerplexityTradingGuard()
    decision = TradingDecision(
        query_id="q2",
        action="SELL",
        symbol="GBPJPY",
        confidence=0.55,
        citations=[_citation(), _citation()],
        qa_results=[QACheckResult(False, "consistency_check", ["conflicting sources"])],
        approval_status=ApprovalStatus.APPROVED,
    )

    report = guard.validate_decision(decision)

    assert not report.accepted
    assert "consistency_check" in report.failed_qa_methods
    assert any("confidence" in reason for reason in report.reasons)


def test_guard_allows_well_supported_paper_trade_but_requires_governance_for_live():
    guard = PerplexityTradingGuard()
    decision = TradingDecision(
        query_id="q3",
        action="BUY",
        symbol="BTCUSD",
        confidence=0.82,
        entry_price=65000.0,
        stop_loss=64000.0,
        take_profit=68000.0,
        position_size=0.1,
        citations=[
            _citation(),
            _citation(confidence=0.8, source=RetrievalSource.MARKET_DATA),
        ],
        approval_status=ApprovalStatus.APPROVED,
    )

    paper_report = guard.validate_decision(decision, live_mode=False)
    live_blocked = guard.validate_decision(decision, live_mode=True, governance_approved=False)
    live_allowed = guard.validate_decision(decision, live_mode=True, governance_approved=True)

    assert paper_report.accepted
    assert not live_blocked.accepted
    assert any("governance" in reason for reason in live_blocked.reasons)
    assert live_allowed.accepted


def test_guard_requires_source_diversity_and_complete_risk_plan_for_trade():
    guard = PerplexityTradingGuard()
    decision = TradingDecision(
        query_id="q4",
        action="BUY",
        symbol="EURUSD",
        confidence=0.9,
        citations=[_citation(), _citation(confidence=0.85)],
        approval_status=ApprovalStatus.APPROVED,
    )

    report = guard.validate_decision(decision)

    assert not report.accepted
    assert report.source_type_count == 1
    assert "stop_loss" in report.missing_risk_fields
    assert any("distinct source types" in reason for reason in report.reasons)
    assert any("missing risk fields" in reason for reason in report.reasons)


def test_guard_blocks_conflicting_research_even_when_confidence_is_high():
    guard = PerplexityTradingGuard()
    decision = TradingDecision(
        query_id="q5",
        action="SELL",
        symbol="ETHUSD",
        confidence=0.9,
        entry_price=3200.0,
        stop_loss=3300.0,
        take_profit=2900.0,
        position_size=1.0,
        citations=[
            _citation(source=RetrievalSource.NEWS, raw_data={"signal": "bearish"}, data_point="bearish macro impulse"),
            _citation(source=RetrievalSource.MARKET_DATA, raw_data={"signal": "bullish"}, data_point="bullish breakout"),
        ],
        approval_status=ApprovalStatus.APPROVED,
    )

    report = guard.validate_decision(decision)

    assert not report.accepted
    assert report.conflicting_evidence_count >= 2
    assert any("conflicting evidence" in reason for reason in report.reasons)


def test_guard_research_only_mode_never_allows_trade_actions():
    guard = PerplexityTradingGuard(ResearchGuardConfig(research_only_mode=True))
    decision = TradingDecision(
        query_id="q6",
        action="BUY",
        symbol="XAUUSD",
        confidence=0.95,
        entry_price=2300.0,
        stop_loss=2280.0,
        take_profit=2360.0,
        position_size=0.5,
        citations=[
            _citation(source=RetrievalSource.NEWS),
            _citation(source=RetrievalSource.MARKET_DATA),
        ],
        approval_status=ApprovalStatus.APPROVED,
    )

    guarded, report = guard.apply(decision)

    assert not report.accepted
    assert report.final_action == "NO_TRADE"
    assert guarded.action == "NO_TRADE"
    assert any("research-only" in reason for reason in report.reasons)
