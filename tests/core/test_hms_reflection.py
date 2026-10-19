"""HMS reflective memory — failure memory + self-improvement memory.

Contract: failures recorded by the CSC are durable, categorized, and
recallable through the evidence plane; RSI artifacts land in
self-improvement memory; none of it carries authority.
"""

import json

import pytest

from trading_bot.core.hms.memory import HierarchicalMemorySystem
from trading_bot.core.hms.reflection import (
    FAILURE_KINDS,
    FailureMemory,
    FailureRecord,
    ImprovementRecord,
    SelfImprovementMemory,
)


@pytest.fixture
def hms(tmp_path):
    HierarchicalMemorySystem.reset()
    inst = HierarchicalMemorySystem(base_path=str(tmp_path / "hms"))
    yield inst
    HierarchicalMemorySystem.reset()


# -- FailureMemory ----------------------------------------------------------


def test_failure_record_and_recall(hms):
    fid = hms.record_failure(
        "prediction_incorrect", "BUY call failed",
        trade_id="T1", symbol="EURUSD", regime="trend", confidence=0.8)
    assert fid.startswith("FAIL-")
    recs = hms.recall_failures(regime="trend")
    assert len(recs) == 1
    assert recs[0]["kind"] == "prediction_incorrect"
    assert recs[0]["trade_id"] == "T1"


def test_failure_kind_normalized(hms):
    hms.record_failure("not_a_kind", "misc")
    recs = hms.recall_failures()
    assert recs[0]["kind"] == "other"
    assert recs[0]["kind"] in FAILURE_KINDS


def test_failure_filters(hms):
    hms.record_failure("advisor_error", "a", symbol="EURUSD", regime="r1")
    hms.record_failure("decision_rejected", "b", symbol="GBPUSD", regime="r2")
    assert len(hms.recall_failures(kind="advisor_error")) == 1
    assert len(hms.recall_failures(regime="r2")) == 1
    assert len(hms.recall_failures(symbol="EURUSD")) == 1
    assert hms.recall_failures(symbol="USDJPY") == []


def test_failure_persistence(tmp_path):
    fm = FailureMemory(str(tmp_path / "fm"))
    fm.record(FailureRecord(kind="execution_fault", summary="x",
                            regime="volatile"))
    fm2 = FailureMemory(str(tmp_path / "fm"))
    assert fm2.summary()["by_kind"]["execution_fault"] == 1


def test_failure_summary_counts(hms):
    for _ in range(3):
        hms.record_failure("advisor_error", "x", regime="r")
    hms.record_failure("decision_rejected", "y", regime="r")
    s = hms.failure_summary()
    assert s["total"] == 4
    assert s["by_kind"]["advisor_error"] == 3
    assert s["by_regime"]["r"] == 4


# -- SelfImprovementMemory --------------------------------------------------


def test_improvement_record_and_lessons(hms):
    rid = hms.record_improvement(
        "decision", "trading_policy", "GEN-1 rejected — no gain",
        status="rejected", genome_id="GEN-1")
    assert rid.startswith("IMP-")
    recs = hms.recall_lessons(domain="trading_policy")
    assert len(recs) == 1
    assert recs[0]["status"] == "rejected"


def test_improvement_summary(hms):
    hms.record_improvement("proposal", "memory", "widen window")
    hms.record_improvement("decision", "memory", "ok", status="eligible_for_operator_review")
    s = hms.improvement_summary()
    assert s["total"] == 2
    assert s["by_domain"]["memory"] == 2
    assert s["decisions_by_status"]["eligible_for_operator_review"] == 1


def test_improvement_persistence(tmp_path):
    sm = SelfImprovementMemory(str(tmp_path / "si"))
    sm.record(ImprovementRecord(record_type="lesson", domain="risk",
                              summary="lesson"))
    sm2 = SelfImprovementMemory(str(tmp_path / "si"))
    assert sm2.lessons(domain="risk")


# -- Reflective context joins the evidence chain -----------------------------


def test_reflective_context_shape(hms):
    hms.record_failure("decision_rejected", "risk cap", regime="trend",
                       symbol="EURUSD")
    hms.record_improvement("lesson", "trading_policy", "lesson-x")
    ctx = hms.retrieve_reflective_context(regime="trend", symbol="EURUSD")
    relations = {c["relation"] for c in ctx}
    assert "FAILED_IN_KIND" in relations
    assert "LESSON_IN_DOMAIN" in relations
    # Same shape as SAGE subgraph results — joins the evidence chain
    for c in ctx:
        assert {"source", "target", "relation", "weight",
                "context"} <= set(c)


# -- CSC hooks ----------------------------------------------------------------


@pytest.fixture
def csc_with_hms(hms):
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    inst = CognitiveSystemController(hms=hms)
    yield inst
    CognitiveSystemController._instance = None


@pytest.mark.asyncio
async def test_incorrect_outcome_writes_failure(csc_with_hms):
    csc = csc_with_hms
    csc._pending_predictions["T1"] = {
        "action": "BUY", "entry_price": 1.10, "confidence": 0.8,
        "regime": "trend", "symbol": "EURUSD", "advisory_calls": []}
    result = await csc.record_outcome("T1", exit_price=1.09)
    assert result["was_correct"] is False
    recs = csc.hms.recall_failures(kind="prediction_incorrect")
    assert len(recs) == 1
    assert recs[0]["trade_id"] == "T1"


@pytest.mark.asyncio
async def test_correct_outcome_no_failure(csc_with_hms):
    csc = csc_with_hms
    csc._pending_predictions["T2"] = {
        "action": "BUY", "entry_price": 1.10, "confidence": 0.6,
        "regime": "trend", "symbol": "EURUSD", "advisory_calls": []}
    await csc.record_outcome("T2", exit_price=1.11)
    assert csc.hms.recall_failures(kind="prediction_incorrect") == []


@pytest.mark.asyncio
async def test_advisor_error_writes_failure(csc_with_hms):
    csc = csc_with_hms

    class BadAdvisor:
        capability_id = "bad_cap"

        async def analyze(self, ctx):
            raise RuntimeError("boom")

    csc._advisory_services = [BadAdvisor()]
    csc._advisory_failures = {}
    artifacts = await csc._consult_agent_population({"symbol": "EURUSD"})
    # PCA artifacts may be present — the advisor's own artifact is not.
    assert not any(a.get("agent") == "bad_cap" for a in artifacts)
    recs = csc.hms.recall_failures(kind="advisor_error")
    assert len(recs) == 1
    assert recs[0]["context"]["capability_id"] == "bad_cap"


@pytest.mark.asyncio
async def test_rejected_decision_writes_failure(csc_with_hms):
    from trading_bot.core.csc.controller import CoreDecision, DecisionOutcome
    csc = csc_with_hms

    async def fake_pipeline(obs):
        return CoreDecision(
            outcome=DecisionOutcome.TRADE_REJECTED,
            trade_id="T3",
            dominant_rejection_reason="shield veto")

    csc._process_observation_pipeline = fake_pipeline
    decision = await csc.process_market_observation(
        {"symbol": "EURUSD", "regime": "trend"})
    assert decision.outcome is DecisionOutcome.TRADE_REJECTED
    recs = csc.hms.recall_failures(kind="decision_rejected")
    assert len(recs) == 1
    assert "shield veto" in recs[0]["summary"]


# -- RSI bridge ---------------------------------------------------------------


def test_gaps_from_failure_summary():
    from trading_bot.recursive_self_improvement.hms_bridge import (
        gaps_from_failure_summary)
    summary = {"by_kind": {"prediction_incorrect": 5,
                           "advisor_error": 1},
               "by_regime": {"trend": 6}}
    gaps = gaps_from_failure_summary(summary, min_count=3)
    # advisor_error (1) below threshold -> dropped
    assert len(gaps) == 1
    assert gaps[0].metric == "directional_precision"
    assert gaps[0].regime == "trend"


def test_decisions_to_lessons():
    from trading_bot.recursive_self_improvement.hms_bridge import (
        decisions_to_lessons)
    from trading_bot.recursive_self_improvement.improvement_genome import (
        PromotionDecision)
    decs = [PromotionDecision(genome_id="GEN-1", status="rejected",
                              reason="no gain", evidence={"domain": "risk"})]
    recs = decisions_to_lessons(decs)
    types = {r["record_type"] for r in recs}
    assert types == {"decision", "lesson"}
    assert all(r["domain"] == "risk" for r in recs)


def test_bridge_mirror_round_trip(hms):
    from trading_bot.recursive_self_improvement.hms_bridge import (
        RSIHMSBridge)
    from trading_bot.recursive_self_improvement.improvement_genome import (
        PromotionDecision)
    bridge = RSIHMSBridge(hms=hms)
    ids = bridge.mirror_decisions([
        PromotionDecision(genome_id="GEN-9", status="rejected",
                          reason="flat", evidence={})])
    assert ids  # at least one record id
    assert hms.recall_lessons()


# -- Counterfactual queries (EvidenceGraph do-calculus) -----------------------


def _cf_graph():
    from trading_bot.core.hms.models import (
        EvidenceEdge, EvidenceGraph, EvidenceNode, RelationType)
    g = EvidenceGraph()
    g.add_node(EvidenceNode("cause", "strong trend", "EVIDENCE",
                            confidence=0.8))
    g.add_node(EvidenceNode("effect", "rally continues", "HYPOTHESIS",
                            confidence=0.6))
    g.add_node(EvidenceNode("sibling", "noise", "CLAIM",
                            confidence=0.5))
    g.add_edge(EvidenceEdge("cause", "effect", RelationType.CAUSES,
                            weight=0.9, is_causal=True))
    g.add_edge(EvidenceEdge("sibling", "effect", RelationType.CORRELATES,
                            weight=0.5, is_causal=False))
    g.add_edge(EvidenceEdge("sibling", "cause", RelationType.CAUSES,
                            weight=1.0, is_causal=True))
    return g


def test_counterfactual_severs_incoming_and_propagates():
    g = _cf_graph()
    cf = g.query_counterfactual({"cause": 0.1})
    # intervened node forced, incoming causal edge severed
    assert cf.nodes["cause"].confidence == 0.1
    assert not any(e.is_causal and e.target_id == "cause"
                   for e in cf.edges)
    # downstream attenuated: 0.6 * (0.1/0.8) * 0.9 = 0.0675
    assert cf.nodes["effect"].confidence == pytest.approx(0.0675)
    # original graph untouched
    assert g.nodes["cause"].confidence == 0.8
    assert len(g.edges) == 3


def test_counterfactual_skips_noncausal_edges():
    from trading_bot.core.hms.models import (
        EvidenceEdge, EvidenceGraph, EvidenceNode, RelationType)
    g = EvidenceGraph()
    g.add_node(EvidenceNode("a", "x", "EVIDENCE", confidence=0.5))
    g.add_node(EvidenceNode("b", "y", "HYPOTHESIS", confidence=0.5))
    g.add_edge(EvidenceEdge("a", "b", RelationType.CORRELATES,
                          weight=1.0, is_causal=False))
    cf = g.query_counterfactual({"a": 0.0})
    assert cf.nodes["b"].confidence == 0.5


def test_counterfactual_context_mask():
    from trading_bot.core.hms.models import (
        EvidenceEdge, EvidenceGraph, EvidenceNode, RelationType)
    g = EvidenceGraph()
    g.add_node(EvidenceNode("a", "x", "EVIDENCE", confidence=0.5))
    g.add_node(EvidenceNode("b", "y", "HYPOTHESIS", confidence=0.5))
    g.add_edge(EvidenceEdge("a", "b", RelationType.CAUSES, weight=1.0,
                          is_causal=True,
                          context_validity_mask={"regime": "trend"}))
    # edge invalid in this context -> no propagation
    cf = g.query_counterfactual({"a": 1.0}, context={"regime": "range"})
    assert cf.nodes["b"].confidence == 0.5
    # valid context -> propagates (factor 2.0 * weight 1.0, clipped at 1.0)
    cf2 = g.query_counterfactual({"a": 1.0}, context={"regime": "trend"})
    assert cf2.nodes["b"].confidence == 1.0


# -- Full ledger persistence ---------------------------------------------------


def test_ledger_entry_persists_verifier_reports(hms, tmp_path):
    import glob
    import os
    from trading_bot.core.hms.models import (
        EvidenceGraph, EvidenceNode, Hypothesis, ResearchLedgerEntry,
        VerifierReport)
    entry = ResearchLedgerEntry(trade_id="T-LEDGER")
    entry.hypothesis = Hypothesis(description="bull continuation",
                                  probability=0.7, expected_return=0.02,
                                  invalidation_conditions=["close < X"])
    entry.verifier_reports = [
        VerifierReport(agent_name="v1", is_valid=True, confidence=0.9,
                       critique="sound"),
        VerifierReport(agent_name="v2", is_valid=False, confidence=0.95,
                       critique="unsupported claim",
                       detected_hallucinations=["h1"])]
    entry.evidence_graph_snapshot.add_node(
        EvidenceNode("n1", "evidence", "EVIDENCE", confidence=0.8))
    hms.store_ledger_entry(entry)
    files = glob.glob(os.path.join(hms.ledger_path, "*.json"))
    assert files
    data = json.load(open(files[0]))
    assert data["verifier_reports"][1]["detected_hallucinations"] == ["h1"]
    assert data["hypothesis"]["description"] == "bull continuation"
    assert data["evidence_graph"]["node_count"] == 1
    assert data["trade_id"] == "T-LEDGER"
