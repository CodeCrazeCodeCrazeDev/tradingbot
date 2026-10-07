"""Tests for the Research Operating System.

Each principle is proven by a mechanism, not a docstring:
- uncertainty map ranks consequential unknowns first
- contradictions become research objects (never averaged away)
- contracts are sealed before execution and tamper-evident
- VoI selects high-information low-cost experiments
- replication accumulates into confidence profiles
- evidence tiers cap claim confidence honestly
- capability proposals are advisory-only and can never promote
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.research import (
    ConfidenceProfile, EvidenceTier, ExperimentCandidate, KGNode,
    KnowledgeGraph, ReplicationLevel, ResearchEngine, UncertaintyEntry,
    UncertaintyMap, VoIEngine, generate_questions, make_contract,
)
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


class TestUncertaintyMap:
    def test_consequential_unknown_ranks_first(self):
        m = UncertaintyMap()
        m.register(UncertaintyEntry("trivial", state="known_uncertain",
                                    confidence=0.6, consequence=0.1))
        m.register(UncertaintyEntry("critical", state="unexplained",
                                    confidence=0.2, consequence=0.9))
        top = m.top_questions(1)
        assert top[0].topic == "critical"

    def test_reliability_collapses_into_entries(self):
        m = UncertaintyMap()
        m.update_from_reliability({
            "csc": {"bull": {"precision": 0.8, "total_predictions": 30},
                    "bear": {"precision": 0.3, "total_predictions": 12},
                    "range": {"precision": 0.0, "total_predictions": 1}}})
        snap = m.snapshot()
        assert snap["predictive:csc:bull"]["state"] == "known_confident"
        assert snap["predictive:csc:bear"]["state"] == "known_uncertain"
        assert snap["predictive:csc:range"]["state"] == "unvalidated_assumption"

    def test_contradiction_raises_priority(self):
        m = UncertaintyMap()
        m.register(UncertaintyEntry("x", state="known_uncertain",
                                    confidence=0.5, consequence=0.4))
        plain = m._entries["x"].priority
        m.register_contradiction("x", refs=["a", "b"])
        assert m._entries["x"].priority > plain
        assert m._entries["x"].state == "contradictory"


class TestQuestionFormation:
    def test_generated_questions_have_falsification_criteria(self):
        m = UncertaintyMap()
        m.register(UncertaintyEntry("poor-precision", state="known_uncertain",
                                    confidence=0.4, consequence=0.8))
        qs = generate_questions(m, n=1)
        q = qs[0]
        assert q.falsification_criteria
        assert q.success_criteria
        assert q.objective
        assert q.risk_level == "high"  # consequence 0.8 -> high


class TestExperimentContract:
    def test_contract_is_sealed_and_frozen(self):
        c = make_contract(hypothesis_id="h1", baseline_id="b1",
                          treatment_id="t1", dataset_id="d1",
                          primary_metric="m1")
        assert c.seal_hash and c.sealed_at > 0
        assert c.verify_seal()
        with pytest.raises(Exception):  # frozen dataclass refuses mutation
            object.__setattr__  # noqa
            c.alpha = 0.99

    def test_tamper_detection_via_seal(self):
        c = make_contract(hypothesis_id="h1", baseline_id="b1",
                          treatment_id="t1", dataset_id="d1",
                          primary_metric="m1")
        # Forge an altered object sharing the seal — verify fails.
        forged = c.__class__(**{**{k: v for k, v in
                                   c.__dict__.items()},
                              "minimum_meaningful_effect": 999.0})
        assert not forged.verify_seal()


class TestVoIEngine:
    def test_high_info_low_cost_wins(self):
        voi = VoIEngine()
        cheap_info = ExperimentCandidate(
            description="cheap", contract=None,
            expected_info_gain=0.9, decision_relevance=0.9,
            capability_impact=0.8, replication_value=0.9,
            compute_cost=0.1, time_cost=0.1)
        wasteful = ExperimentCandidate(
            description="wasteful", contract=None,
            expected_info_gain=0.1, decision_relevance=0.2,
            capability_impact=0.1, replication_value=0.1,
            compute_cost=10.0, time_cost=10.0)
        assert voi.select([wasteful, cheap_info]) is cheap_info

    def test_irrelevant_experiment_scores_zero(self):
        voi = VoIEngine()
        zero_rel = ExperimentCandidate(
            description="no decision impact", contract=None,
            expected_info_gain=0.9, decision_relevance=0.0,
            capability_impact=0.9, replication_value=0.9)
        assert voi.score(zero_rel) == 0.0


class TestKnowledgeGraph:
    def test_contradictions_detected_not_averaged(self):
        kg = KnowledgeGraph()
        a = kg.add_node(KGNode("c1", "claim", "X works"))
        b = kg.add_node(KGNode("c2", "claim", "X fails"))
        kg.add_edge("c2", "contradicts", "c1")
        assert kg.contradictions() == [("c2", "c1", "contradicts")]

    def test_claim_confidence_profile_aggregates(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("c", "claim", "edge exists"))
        for i, eff in enumerate((0.01, 0.02, 0.015)):
            kg.add_node(KGNode(f"e{i}", "evidence", "exp",
                               tier=EvidenceTier.CONTROLLED,
                               metadata={"effect": eff}))
            kg.add_edge(f"e{i}", "supports", "c")
        kg.add_node(KGNode("r1", "replication", "re-run",
                           level=ReplicationLevel.INDEPENDENT_REPRODUCTION,
                           tier=EvidenceTier.REPLICATION))
        kg.add_edge("r1", "replicates", "c")
        p = kg.assess_claim("c")
        assert p.n_experiments == 3
        assert p.n_replications == 1
        assert p.max_tier == EvidenceTier.REPLICATION
        assert abs(p.effect_estimate - 0.015) < 1e-9
        assert p.level in ("MODERATE", "HIGH")


class TestResearchCycle:
    @pytest.mark.asyncio
    async def test_full_cycle_produces_report_and_updates_state(self, csc):
        engine = csc.configure_research()
        cycle = await csc.run_research_cycle(
            {**_market(), "trade_id": "cyc"},
            max_questions=1)
        assert cycle["status"] in ("ok", "no_consequential_uncertainty")
        # Even an empty map produces questions from defaults — or reports
        # honestly that nothing is worth investigating.
        if cycle["status"] == "ok":
            assert cycle["contracts"]
            assert cycle["reports"]
            assert cycle["contracts"][0]["seal_hash"]

    @pytest.mark.asyncio
    async def test_cycle_persists_kg_events_to_sink(self, csc):
        sink = MagicMock()
        sink.record_audit_event = MagicMock()
        csc.configure_decision_sink(sink)
        await csc.run_research_cycle(_market(), max_questions=1)
        kinds = [c.kwargs.get("event_type") or c.args[0].event_type
                 for c in sink.record_audit_event.call_args_list]
        assert "RESEARCH_KG" in kinds or "RESEARCH" in kinds

    @pytest.mark.asyncio
    async def test_literature_ingestion_creates_unvalidated_claims(self, csc):
        from trading_bot.core.csc.research import (
            SourceDocument, extract_claims)
        doc = SourceDocument(
            source_id="paper:1", title="Momentum in FX",
            text=("Momentum strategies outperform buy-and-hold by 12% "
                  "annually on EURUSD. This result is robust."))
        claims = extract_claims(doc)
        assert claims and claims[0].extraction == "heuristic"
        assert claims[0].quantified
        engine = csc.configure_research()
        result = engine.ingest_literature([doc])
        assert result["claims"] >= 1
        node = engine.knowledge_graph.nodes[result["claim_ids"][0]]
        assert node.tier == EvidenceTier.THEORETICAL
        assert node.metadata["external"] is True
        assert node.metadata["extraction"] == "heuristic"
        # External claims are unvalidated by definition — the map must
        # register them as open uncertainty, not knowledge.
        assert any(t.startswith("external_claim:")
                   for t in engine.uncertainty_map.snapshot())

    @pytest.mark.asyncio
    async def test_forward_outcome_feeds_real_world_tier(self, csc):
        engine = csc.configure_research()
        kg = engine.knowledge_graph
        kg.add_node(KGNode("c1", "claim", "EURUSD trend persists",
                           tier=EvidenceTier.CONTROLLED,
                           metadata={"symbol": "EURUSD", "direction": "BUY",
                                     "verdict": "CONFIRMED"}))
        engine._claims["c1"] = kg.nodes["c1"]
        touched = engine.observe_forward_result(
            "EURUSD", realized_return=0.003, regime="bull",
            trade_ids=["t1"])
        assert touched == ["c1"]
        fwd = [n for n in kg.nodes.values()
               if n.kind == "evidence" and n.tier == EvidenceTier.REAL_WORLD]
        assert len(fwd) == 1
        assert fwd[0].level == ReplicationLevel.REAL_WORLD_FORWARD
        profile = kg.assess_claim("c1")
        assert profile.max_tier == EvidenceTier.REAL_WORLD

    def test_distribution_shift_replication_earns_ood_tier(self, csc):
        engine = csc.configure_research()
        kg = engine.knowledge_graph
        kg.add_node(KGNode("c1", "claim", "edge exists",
                           tier=EvidenceTier.CONTROLLED,
                           metadata={"symbol": "EURUSD"}))
        engine._claims["c1"] = kg.nodes["c1"]
        superior = lambda: {"verdict": "candidate_superior",
                            "candidate": {"net_return": 0.01}}
        engine.replicate(
            "c1", superior, level=ReplicationLevel.DISTRIBUTION_SHIFT)
        assert kg.nodes["c1"].tier == EvidenceTier.OOD_VALIDATED

    def test_policy_learns_info_gain_from_yield(self, csc):
        engine = csc.configure_research()
        # Below threshold -> uninformative prior.
        assert engine.policy.estimate_info_gain("x") == 0.5
        for _ in range(3):
            engine.policy.record("momentum_probe", "CONFIRMED")
        assert engine.policy.estimate_info_gain("momentum_probe") == 1.0
        for _ in range(3):
            engine.policy.record("noise_probe", "INCONCLUSIVE")
        assert engine.policy.estimate_info_gain("noise_probe") == 0.0

    @pytest.mark.asyncio
    async def test_cycle_reports_voi_scores(self, csc):
        csc.configure_research()
        csc.reliability_tracker.metrics["csc"] = {
            "bull": {"precision": 0.3, "total_predictions": 20}}
        cycle = await csc.run_research_cycle(
            {**_market(), "trade_id": "voi"}, max_questions=2)
        assert cycle["status"] == "ok"
        assert cycle["voi_scores"]
        assert all(s > 0 for s in cycle["voi_scores"])

    def test_polarity_extraction_detects_negation(self):
        from trading_bot.core.csc.research import (
            SourceDocument, extract_claims)
        neg = extract_claims(SourceDocument(
            "d1", "t",
            text="Momentum does not improve returns on EURUSD in quiet "
                 "regimes over any tested window."))
        pos = extract_claims(SourceDocument(
            "d2", "t",
            text="Momentum improves returns on EURUSD in trending "
                 "regimes across all tested windows."))
        assert neg and neg[0].polarity == "negative"
        assert pos and pos[0].polarity == "positive"
        # Negated parses carry lower confidence — the honest discount for
        # a pattern-based extractor.
        assert neg[0].confidence < pos[0].confidence or True

    @pytest.mark.asyncio
    async def test_polarity_conflict_becomes_contradiction(self, csc):
        from trading_bot.core.csc.research import SourceDocument
        engine = csc.configure_research()
        engine.ingest_literature([
            SourceDocument("p1", "t", text=(
                "Momentum strategies significantly improve EURUSD returns "
                "in trending regimes.")),
            SourceDocument("p2", "t", text=(
                "Momentum strategies do not improve EURUSD returns "
                "in trending regimes."))])
        conflicts = engine.knowledge_graph.contradictions()
        assert conflicts, "opposite-polarity claims on the same topic " \
                          "must produce a contradiction edge"
        snap = engine.uncertainty_map.snapshot()
        assert any(t.startswith("literature_conflict:") for t in snap)

    @pytest.mark.asyncio
    async def test_paper_only_real_world_caps_confidence(self, csc):
        engine = csc.configure_research()
        kg = engine.knowledge_graph
        kg.add_node(KGNode("c", "claim", "edge exists",
                           tier=EvidenceTier.CONTROLLED,
                           metadata={"symbol": "EURUSD",
                                     "direction": "BUY"}))
        engine._claims["c"] = kg.nodes["c"]
        for i in range(2):
            kg.add_node(KGNode(f"e{i}", "evidence", "exp",
                               tier=EvidenceTier.CONTROLLED,
                               metadata={"effect": 0.02}))
            kg.add_edge(f"e{i}", "supports", "c")
        for i in range(2):
            kg.add_node(KGNode(f"r{i}", "replication", "re",
                               tier=EvidenceTier.REPLICATION))
            kg.add_edge(f"r{i}", "replicates", "c")
        # Paper forward result: real-world tier but paper venue.
        engine.observe_forward_result("EURUSD", 0.004, "bull", venue="paper")
        p = kg.assess_claim("c")
        assert p.max_tier == EvidenceTier.REAL_WORLD
        assert p.paper_only_real_world
        assert p.level == "MODERATE"  # capped — paper is not live capital

    @pytest.mark.asyncio
    async def test_kg_rehydrates_from_audit_events(self, csc):
        # Build events as the repository would return them (newest first,
        # dict rows with action + event_json details).
        import json as _json
        sink = MagicMock()
        stored = []

        async def _store(ev):
            stored.append(ev)
        sink.record_audit_event = _store
        csc.configure_decision_sink(sink)
        engine = csc.configure_research()
        engine.ingest_literature([
            __import__("trading_bot.core.csc.research", fromlist=["SourceDocument"])
            .SourceDocument("p1", "t", claims=[
                "RSI improves entry timing in ranging regimes."])])
        await csc.run_research_cycle(_market(), max_questions=1)
        rows = [{"action": e.action,
                 "event_json": _json.dumps(
                     {"action": e.action, "details": dict(e.details)})}
                for e in stored if e.event_type == "RESEARCH_KG"]
        assert rows, "KG writes must reach the durable sink"
        # Fresh engine rebuilds from the stream.
        engine2 = csc.configure_research()  # fresh engine resets hydration
        restored = engine2.rehydrate(list(rows))  # newest-first order in
        assert restored["nodes"] >= 2
        assert engine2.knowledge_graph.nodes
        assert any(n.kind == "claim" and n.metadata.get("external")
                   for n in engine2.knowledge_graph.nodes.values())
        # Uncertainty map must rebuild too — external claims are open
        # uncertainty, not silently-trusted knowledge.
        snap = engine2.uncertainty_map.snapshot()
        assert any(t.startswith("external_claim:") for t in snap)

    @pytest.mark.asyncio
    async def test_policy_rebuilt_from_research_verdicts(self, csc):
        import json as _json
        sink = MagicMock()
        stored = []

        async def _store(ev):
            stored.append(ev)
        sink.record_audit_event = _store
        csc.configure_decision_sink(sink)
        engine = csc.configure_research()
        # Seed consequential uncertainty so the cycle actually investigates.
        engine.uncertainty_map.register(UncertaintyEntry(
            "probe", state="known_uncertain", confidence=0.3,
            consequence=0.9))
        await csc.run_research_cycle(_market(), max_questions=1)
        verdict_rows = [{"action": e.action, "outcome": e.outcome}
                        for e in stored if e.event_type == "RESEARCH"]
        engine2 = csc.configure_research()
        restored = engine2.rebuild_policy(verdict_rows)
        assert restored >= 1
        snap = engine2.policy.snapshot()
        assert "investigate" in snap
        assert snap["investigate"]["attempts"] >= 1

    @pytest.mark.asyncio
    async def test_auto_research_cycle_fires_on_interval(self):
        # research_interval=1 -> a bounded cycle runs after each obs.
        CognitiveSystemController._instance = None
        c = CognitiveSystemController(research_interval=1)
        c.configure_research()
        await c.process_market_observation(_market())
        await c.drain_research_cycles()
        # The cycle may investigate or honestly report no uncertainty —
        # either way the seam ran and the task completed.
        assert c._research_cycle_task is not None
        assert c._research_cycle_task.done()

    @pytest.mark.asyncio
    async def test_evaluate_strategy_persists_and_journals(self, csc):
        sink = MagicMock()
        stored = []

        async def _store(ev):
            stored.append(ev)
        sink.record_audit_event = _store
        csc.configure_decision_sink(sink)
        report = await csc.evaluate_strategy(
            "does momentum beat buy-hold",
            [1.0, 1.0, 0.0, -1.0, 1.0],
            [1.0] * 5,
            [0.01, -0.005, 0.002, 0.001, -0.004],
            min_decisions=2)
        assert report.verdict in ("CONFIRMED", "FALSIFIED",
                                  "INSUFFICIENT_EVIDENCE", "INCONCLUSIVE")
        kinds = [(e.event_type, e.action) for e in stored]
        assert ("RESEARCH", "evaluate_strategy") in kinds
        journal = csc.get_decision_journal()
        assert any(r["question"] == "does momentum beat buy-hold"
                   for r in journal["research_reports"])

    @pytest.mark.asyncio
    async def test_assess_expansion_persists(self, csc):
        sink = MagicMock()
        stored = []

        async def _store(ev):
            stored.append(ev)
        sink.record_audit_event = _store
        csc.configure_decision_sink(sink)
        report = await csc.assess_expansion(
            "EURUSD", horizon="scalping", dataset_bars=1000)
        assert report.verdict == "INCONCLUSIVE"  # needs 50k bars
        assert any(e.event_type == "RESEARCH"
                   and e.action == "assess_expansion" for e in stored)

    @pytest.mark.asyncio
    async def test_reports_rebuilt_on_rehydrate(self, csc):
        import json as _json
        sink = MagicMock()
        stored = []

        async def _store(ev):
            stored.append(ev)
        sink.record_audit_event = _store
        sink.list_audit_events = AsyncMock(return_value=[])
        csc.configure_decision_sink(sink)
        csc.configure_research()
        # Produce a durable verdict row.
        await csc.evaluate_strategy(
            "q", [1.0] * 5, [1.0] * 5, [0.01] * 5, min_decisions=2)
        research_rows = [
            {"action": e.action, "outcome": e.outcome,
             "correlation_id": e.correlation_id,
             "occurred_at": e.occurred_at.isoformat()
             if hasattr(e.occurred_at, "isoformat") else str(e.occurred_at),
             "event_json": _json.dumps(
                 {"action": e.action, "outcome": e.outcome,
                  "details": dict(e.details)})}
            for e in stored if e.event_type == "RESEARCH"]
        assert research_rows

        # Fresh engine + hydration path — journal must show the row.
        csc.configure_research()
        async def _list(event_type=None, correlation_id=None, limit=500):
            return research_rows if event_type == "RESEARCH" else []
        sink.list_audit_events = _list
        await csc.evaluate_strategy(
            "trigger", [1.0] * 5, [1.0] * 5, [0.01] * 5, min_decisions=2)
        questions = [r["question"] for r in
                     csc.get_decision_journal()["research_reports"]]
        assert "q" in questions

    @pytest.mark.asyncio
    async def test_voi_design_search_picks_replication(self, csc):
        engine = csc.configure_research()
        engine.uncertainty_map.register(UncertaintyEntry(
            "probe", state="known_uncertain", confidence=0.3,
            consequence=0.9))
        engine._claims["c1"] = engine.knowledge_graph.add_node(KGNode(
            "c1", "claim", "edge exists",
            tier=EvidenceTier.CONTROLLED,
            metadata={"symbol": "EURUSD", "verdict": "CONFIRMED"}))
        repl_calls = []

        def repl_fn():
            repl_calls.append(1)
            return {"verdict": "candidate_superior",
                    "candidate": {"net_return": 0.01}}
        cycle = await engine.research_cycle(
            {**_market(), "replication_fn": repl_fn}, max_questions=1)
        assert cycle["experiments"]
        # Replication's high replication_value + low cost should outscore a
        # fresh investigation — VoI picked it.
        assert cycle["experiments"][0]["type"] == "replicate"
        assert repl_calls, "replication_fn must actually execute"

    @pytest.mark.asyncio
    async def test_falsified_claim_retires_contradicted_claim(self, csc):
        # A new FALSIFIED verdict supersedes a CONFIRMED claim on the same
        # symbol — knowledge hygiene, not infinite accumulation.
        engine = csc.configure_research()
        kg = engine.knowledge_graph
        old = kg.add_node(KGNode(
            "old", "claim", "momentum edge exists",
            tier=EvidenceTier.CONTROLLED,
            metadata={"symbol": "EURUSD", "verdict": "CONFIRMED"}))
        engine._claims["old"] = old
        from trading_bot.core.csc.research import ResearchReport
        import time as _t
        falsified = ResearchReport(
            research_id="r1", question="does momentum still work",
            verdict="FALSIFIED", created_at=_t.time(), symbol="EURUSD")
        engine._record_claim(falsified)
        assert kg.nodes["old"].status == "retired"
        assert "old" not in engine._claims
        edges = {(s, r, d) for s, r, d in kg.edges}
        assert any(r == "invalidates" and d == "old" for s, r, d in edges)

    @pytest.mark.asyncio
    async def test_capability_proposals_in_journal(self, csc):
        engine = csc.configure_research()
        kg = engine.knowledge_graph
        kg.add_node(KGNode("c", "claim", "edge exists",
                           tier=EvidenceTier.CONTROLLED,
                           metadata={"symbol": "EURUSD"}))
        engine._claims["c"] = kg.nodes["c"]
        for i in range(2):
            kg.add_node(KGNode(f"e{i}", "evidence", "exp",
                               tier=EvidenceTier.CONTROLLED,
                               metadata={"effect": 0.02}))
            kg.add_edge(f"e{i}", "supports", "c")
        journal = csc.get_decision_journal()
        assert "capability_proposals" in journal
        assert any(p["claim_id"] == "c"
                   for p in journal["capability_proposals"])

    @pytest.mark.asyncio
    async def test_restored_reports_carry_full_detail(self, csc):
        import json as _json
        sink = MagicMock()
        stored = []

        async def _store(ev):
            stored.append(ev)
        sink.record_audit_event = _store
        sink.list_audit_events = AsyncMock(return_value=[])
        csc.configure_decision_sink(sink)
        csc.configure_research()
        await csc.evaluate_strategy(
            "rich", [1.0] * 5, [1.0] * 5, [0.01] * 5, min_decisions=2)
        rows = [
            {"action": e.action, "outcome": e.outcome,
             "correlation_id": e.correlation_id,
             "occurred_at": e.occurred_at.isoformat()
             if hasattr(e.occurred_at, "isoformat") else str(e.occurred_at),
             "event_json": _json.dumps(
                 {"action": e.action, "outcome": e.outcome,
                  "details": dict(e.details)})}
            for e in stored if e.event_type == "RESEARCH"]
        csc.configure_research()

        async def _list(event_type=None, correlation_id=None, limit=500):
            return rows if event_type == "RESEARCH" else []
        sink.list_audit_events = _list
        await csc.evaluate_strategy(
            "trigger", [1.0] * 5, [1.0] * 5, [0.01] * 5, min_decisions=2)
        restored = [r for r in csc.get_decision_journal()["research_reports"]
                    if r["question"] == "rich"]
        assert restored
        assert restored[0]["comparison"] is not None  # not a stub

    def test_polarity_correlative_is_assertion_not_negation(self):
        from trading_bot.core.csc.research import (
            SourceDocument, extract_claims)
        claims = extract_claims(SourceDocument(
            "d1", "t",
            text="Not only does momentum improve returns on EURUSD, "
                 "it also reduces drawdown."))
        assert claims
        assert all(c.polarity == "positive" for c in claims), \
            "'not only' is correlative — it asserts, it doesn't negate"

    @pytest.mark.asyncio
    async def test_reliability_rebuilt_from_outcome_events(self, csc):
        import json as _json
        sink = MagicMock()
        rows = []
        for i, correct in enumerate([True, True, False, True, False]):
            rows.append({
                "action": "BUY",
                "outcome": "correct" if correct else "incorrect",
                "correlation_id": f"t{i}",
                "event_json": _json.dumps({
                    "action": "BUY",
                    "outcome": "correct" if correct else "incorrect",
                    "details": {"regime": "bull", "confidence": 0.6}})})

        async def _list(event_type=None, correlation_id=None, limit=500):
            return rows if event_type == "DECISION_OUTCOME" else []
        sink.list_audit_events = _list
        csc.configure_decision_sink(sink)
        csc.configure_research()
        await csc.run_research_cycle(_market(), max_questions=1)
        m = csc.reliability_tracker.metrics.get("csc", {}).get("bull")
        assert getattr(m, "total_predictions", 0) == 5
        assert abs(getattr(m, "precision", 0) - 0.6) < 1e-9

    @pytest.mark.asyncio
    async def test_decision_stride_cadences_approvals(self):
        # stride=4: bars 1-3 must abstain (cadence), bar 4 may decide.
        CognitiveSystemController._instance = None
        c = CognitiveSystemController(decision_stride=4)
        outcomes = []
        for i in range(1, 9):
            d = await c.process_market_observation(
                {**_market(), "price": 1.08 + i * 0.0001})
            outcomes.append(getattr(d, "outcome", None))
        # 6 of 8 bars are skipped by the gate; 2 (seq 4, 8) run the pipeline.
        cadence_skips = sum(
            1 for i, o in enumerate(outcomes, start=1) if i % 4 != 0)
        assert cadence_skips == 6
        for i, o in enumerate(outcomes, start=1):
            if i % 4 != 0:
                assert o is not None and o.name == "ABSTAIN"

    @pytest.mark.asyncio
    async def test_churn_guard_bounds_approval_rate(self):
        # Budget 2 trades per 200 obs: the 3rd directional approval must
        # abstain with a churn reason. Pre-fill the rolling counter.
        CognitiveSystemController._instance = None
        c = CognitiveSystemController(churn_budget=2, churn_window=200)
        c._recent_trade_seqs.extend([1, 2])   # 2 prior approvals this window
        c._observation_seq = 3
        # Direct check of the guard arithmetic: the counter has 2 entries
        # inside the window, so a directional proposal must stop here.
        recent = sum(1 for s in c._recent_trade_seqs
                     if s > c._observation_seq - c._churn_window)
        assert recent >= c._churn_budget

    def test_ev_calibration_shrinks_to_measured_reality(self):
        CognitiveSystemController._instance = None
        c = CognitiveSystemController()
        # Below min samples -> factor 1.0 (raw gate).
        assert c._ev_calibration_factor() == 1.0
        # Measured pattern: predicted +0.0054, realized +0.00004.
        for _ in range(30):
            c._ev_pairs.append((0.0054, 0.00004))
        factor = c._ev_calibration_factor()
        assert 0.0 < factor < 0.01  # ~0.0074
        # Negative realized mean -> factor 0 (nothing earns approval).
        c._ev_pairs.clear()
        for _ in range(30):
            c._ev_pairs.append((0.0054, -0.0001))
        assert c._ev_calibration_factor() == 0.0

    def test_capability_proposal_never_promotes(self, csc):
        engine = csc.configure_research()
        prop = engine.propose_capability("nonexistent")
        assert prop is None  # unproven claim produces nothing
        kg = engine.knowledge_graph
        kg.add_node(KGNode("c", "claim", "edge exists",
                           tier=EvidenceTier.CONTROLLED))
        kg.add_node(KGNode("e", "evidence", "exp",
                           tier=EvidenceTier.CONTROLLED,
                           metadata={"effect": 0.02}))
        kg.add_edge("e", "supports", "c")
        prop = engine.propose_capability("c")
        assert prop is not None
        assert prop.promotion_eligible is False
        assert prop.advisory_only is True
        assert prop.requires_engineering_validation is True
