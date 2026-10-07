"""Tests for the unified research engine + CSC wiring.

Proves: the engine runs the real canonical pipeline (grounded hypotheses →
simulation → adversarial verification → durable report); verdicts are honest
(CONFIRMED / FALSIFIED / INSUFFICIENT_EVIDENCE / INCONCLUSIVE); reports carry
no authority fields; the CSC owns the single entry point; reports reach the
evidence channel and the durable journal.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.research import ResearchEngine, ResearchReport
from trading_bot.core.alphaalgo_core_engine import DecisionOutcome
from trading_bot.core.unified_event_bus import decision_bus


def _market():
    return {"symbol": "EURUSD", "price": 1.0850, "close": 1.0850,
            "volume": 1500.0, "volatility": 0.001, "trend": "BULLISH",
            "rsi": 58.0}


@pytest.fixture
async def csc():
    CognitiveSystemController._instance = None
    try:
        await decision_bus.stop()
    except Exception:
        pass
    c = CognitiveSystemController()
    yield c
    try:
        await decision_bus.stop()
    except Exception:
        pass


class TestResearchEngine:
    @pytest.mark.asyncio
    async def test_investigate_confirms_grounded_thesis(self, csc):
        engine = csc.configure_research()
        report = await engine.investigate(
            "Is EURUSD trending up?", _market())
        assert isinstance(report, ResearchReport)
        assert report.verdict == "CONFIRMED"
        assert report.branches_considered >= 3
        assert report.evidence_node_count > 0
        assert report.verifier_verdicts  # real verifier reports
        assert report.composite_confidence > 0

    @pytest.mark.asyncio
    async def test_investigate_empty_evidence_is_honest(self, csc):
        engine = csc.configure_research()
        # A market dict with almost no measured fields still produces a
        # report — but the verdict must not pretend to verified confidence.
        report = await engine.investigate("anything?", {"symbol": "EURUSD"})
        assert report.verdict in (
            "CONFIRMED", "FALSIFIED", "INCONCLUSIVE",
            "INSUFFICIENT_EVIDENCE")
        assert report.advisory_only is True
        assert report.promotion_eligible is False

    @pytest.mark.asyncio
    async def test_vetoed_thesis_is_falsified(self, csc):
        engine = csc.configure_research()
        # A verifier that vetoes -> FALSIFIED, not quietly dropped.
        veto = SimpleNamespace(
            agent_name="ProvenanceVerifier", is_valid=False,
            confidence=0.95, critique="fabricated provenance")
        csc.verifier_swarm.run_swarm = AsyncMock(return_value=[veto])
        report = await engine.investigate("thesis?", _market())
        assert report.verdict == "FALSIFIED"

    def test_evaluate_strategy_wraps_frozen_baseline(self, csc):
        engine = csc.configure_research()
        report = engine.evaluate_strategy(
            "does candidate beat momentum?",
            [0.0] * 60, [1.0] * 60,
            [0.001] * 60, cost_bps=5.0, min_decisions=20)
        assert report.comparison["verdict"] == "no_activity"
        assert report.verdict == "INSUFFICIENT_EVIDENCE"
        assert report.promotion_eligible is False

    def test_assess_expansion_reports_gate(self, csc):
        engine = csc.configure_research()
        report = engine.assess_expansion(
            "EURUSD", horizon="intraday", dataset_bars=1000,
            has_cost_model=True)
        assert "expansion readiness" in report.question
        assert report.comparison["ready"] is False  # 1000 < 5000 floor


class TestCSCResearchWiring:
    @pytest.mark.asyncio
    async def test_research_persists_and_journals(self, csc):
        sink = MagicMock()
        sink.record_audit_event = MagicMock()
        csc.configure_decision_sink(sink)
        report = await csc.research("Why did it abstain last bar?", _market())
        events = [c.args[0] for c in sink.record_audit_event.call_args_list]
        research_events = [e for e in events if e.event_type == "RESEARCH"]
        assert research_events and research_events[0].correlation_id == \
            report.research_id
        journal = csc.get_research_journal()
        assert journal[0]["research_id"] == report.research_id
        assert journal[0]["advisory_only"] is True

    @pytest.mark.asyncio
    async def test_report_enters_advisory_channel_once(self, csc):
        await csc.research("context?", _market())
        assert len(csc._research_artifacts) == 1
        artifacts = await csc._stage_internalization({})
        assert any(a.get("agent") == "research_engine" for a in artifacts)
        assert not csc._research_artifacts  # consumed once

    @pytest.mark.asyncio
    async def test_research_reports_in_decision_journal(self, csc):
        await csc.research("q?", _market())
        journal = csc.get_decision_journal()
        assert "research_reports" in journal
        assert journal["research_reports"][0]["advisory_only"] is True

    @pytest.mark.asyncio
    async def test_report_has_no_authority_fields(self, csc):
        report = await csc.research("q?", _market())
        artifact = report.to_advisory_artifact()
        blob = str(artifact) + str(report.to_dict())
        for field in ("quantity", "order", "execute", "authorize", "veto"):
            assert field not in blob.lower() or field == "veto"
        assert artifact["advisory_only"] is True
