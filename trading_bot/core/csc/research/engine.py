"""Research Engine — the one research capability, CSC-subordinate.

Objective: not answers or experiment count, but *decision-relevant,
reproducible knowledge per unit of compute, time, risk, and attention*.

The loop (all stages run on canonical machinery, never parallel brains):

    uncertainty map ─> question formation ─> knowledge-graph lookup
      ─> competing hypotheses ─> falsification (swarm + sim)
      ─> VoI experiment selection ─> locked contract ─> investigation
      ─> verdict ─> KG + uncertainty + policy update
      ─> optional CapabilityProposal (advisory-only; RSI signed flow
         remains the only promotion path)

Contradictions are research objects, boundary conditions are recorded,
and 'we don't know' / 'don't change anything' are first-class verdicts.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np

from trading_bot.core.governance.determinism import determinism as _determinism

from ...hms.models import (
    ResearchLedgerEntry,
    EvidenceGraph,
    InstitutionalProvenance,
)
from .state import (
    ConfidenceProfile, EvidenceTier, ReplicationLevel,
    UncertaintyEntry, UncertaintyMap,
)
from .graph import KnowledgeGraph, KGNode
from .questions import ResearchQuestion, generate_questions
from .experiments import (
    ExperimentCandidate, ExperimentContract, VoIEngine, make_contract,
)
from .policy import ResearchPolicy

logger = logging.getLogger(__name__)


@dataclass
class ResearchReport:
    """A verified research finding. Advisory-only by construction."""
    research_id: str
    question: str
    verdict: str                      # CONFIRMED / FALSIFIED /
                                      # INCONCLUSIVE / INSUFFICIENT_EVIDENCE
    created_at: float
    symbol: str = "unknown"
    question_type: str = "market_edge"  # market_edge | operational
    branches_considered: int = 0
    surviving_branch: Optional[str] = None
    evidence_node_count: int = 0
    verifier_verdicts: List[Dict[str, Any]] = field(default_factory=list)
    sim_summary: Dict[str, Any] = field(default_factory=dict)
    composite_confidence: float = 0.0
    comparison: Optional[Dict[str, Any]] = None
    confidence_profile: Optional[ConfidenceProfile] = None
    boundary_conditions: Dict[str, List[str]] = field(default_factory=dict)
    advisory_only: bool = True
    promotion_eligible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "research_id": self.research_id,
            "question": self.question,
            "verdict": self.verdict,
            "created_at": self.created_at,
            "symbol": self.symbol,
            "question_type": self.question_type,
            "branches_considered": self.branches_considered,
            "surviving_branch": self.surviving_branch,
            "evidence_node_count": self.evidence_node_count,
            "verifier_verdicts": list(self.verifier_verdicts),
            "sim_summary": dict(self.sim_summary),
            "composite_confidence": self.composite_confidence,
            "comparison": dict(self.comparison) if self.comparison else None,
            "confidence_profile": (
                self.confidence_profile.__dict__
                if self.confidence_profile else None),
            "boundary_conditions": dict(self.boundary_conditions),
            "advisory_only": True,
            "promotion_eligible": False,
        }

    def to_advisory_artifact(self) -> Dict[str, Any]:
        """Shape consumed by the observation pipeline's advisory channel."""
        return {
            "agent": "research_engine",
            "source": f"research:{self.research_id}",
            "artifact": {
                "question": self.question,
                "verdict": self.verdict,
                "confidence": self.composite_confidence,
            },
            "advisory_only": True,
        }


def _classify_question(question: str, market_data: Dict[str, Any]
                       ) -> str:
    """Route the question to a matching experiment type. A market
    simulation cannot answer 'why did our own advisor degrade' —
    operational questions get a measured-state diagnostic instead of
    branch simulation. Explicit routing beats keyword guessing: a caller
    may set market_data['question_type']."""
    explicit = str((market_data or {}).get("question_type") or "")
    if explicit in ("market_edge", "operational"):
        return explicit
    q = (question or "").lower()
    op_markers = ("degrad", "health", "suppressed", "failure", "error",
                  "advisor", "component", "our own", "self_",
                  "sprt", "rollback", "drift", "latency", "pipeline")
    if any(m in q for m in op_markers):
        return "operational"
    return "market_edge"


def _content_overlap(a: str, b: str) -> float:
    """Token-overlap (Jaccard) between two claim texts — honest heuristic
    for 'same topic' without NLP embeddings."""
    wa = {w.lower() for w in a.split() if len(w) > 3}
    wb = {w.lower() for w in b.split() if len(w) > 3}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


@dataclass
class CapabilityProposal:
    """Validated knowledge proposed for engineering consideration.

    This is the research→engineering boundary: the proposal carries the
    evidence profile, never authority. Only the signed RSI
    contract/evaluator flow (sealed holdout) may turn a proposal into a
    promoted strategy — this object cannot."""
    proposal_id: str
    claim_id: str
    summary: str
    confidence_profile: ConfidenceProfile
    boundary_conditions: Dict[str, List[str]]
    requires_engineering_validation: bool = True
    advisory_only: bool = True
    promotion_eligible: bool = False


class ResearchEngine:
    """One research pipeline, composed of the CSC's canonical components.

    Construction is via ``CognitiveSystemController.configure_research`` —
    or directly with the same component contracts for isolated testing."""

    def __init__(
        self,
        hypothesis_gen: Any,
        verifier_swarm: Any,
        hms: Any = None,
        folder: Any = None,
        git_sha: str = "unknown",
        persist_fn: Any = None,
    ) -> None:
        self.hypothesis_gen = hypothesis_gen
        self.verifier_swarm = verifier_swarm
        self.hms = hms
        self.folder = folder
        self.git_sha = git_sha or "unknown"
        # KG persistence is sync (emit during reasoning); events buffer here
        # and the controller drains them into the durable audit log.
        self._persist_buffer: "deque" = deque(maxlen=512)
        self.knowledge_graph = KnowledgeGraph(
            persist_fn=lambda kind, payload: self._persist_buffer.append(
                (kind, payload)))
        self.uncertainty_map = UncertaintyMap()
        self.policy = ResearchPolicy()
        self.voi = VoIEngine()
        self._claims: Dict[str, KGNode] = {}

    def drain_persisted_events(self) -> List[Tuple[str, Dict[str, Any]]]:
        out = []
        while self._persist_buffer:
            out.append(self._persist_buffer.popleft())
        return out

    def rehydrate(self, events: List[Any]) -> Dict[str, int]:
        """Rebuild knowledge state from the durable RESEARCH_KG audit
        stream. Events arrive newest-first from the repository — replay in
        chronological order. Rebuilds the claims index and the uncertainty
        map alongside the graph."""
        restored = self.knowledge_graph.replay_events(list(reversed(events)))
        self._claims = {
            nid: n for nid, n in self.knowledge_graph.nodes.items()
            if n.kind == "claim" and n.status == "active"}
        self._rebuild_uncertainty_from_kg()
        return restored

    def _rebuild_uncertainty_from_kg(self) -> None:
        """Derive the uncertainty map from graph structure: external claims
        are unvalidated by definition; contradiction edges are consequential
        open questions."""
        for node in self._claims.values():
            if node.metadata.get("external"):
                self.uncertainty_map.register(UncertaintyEntry(
                    topic=f"external_claim:{node.node_id}",
                    state="unvalidated_assumption",
                    confidence=node.confidence,
                    consequence=0.4 if node.metadata.get("quantified") else 0.3))
        for src, rel, dst in self.knowledge_graph.edges:
            if rel != "contradicts":
                continue
            refs = [src, dst]
            src_meta = self.knowledge_graph.nodes.get(src)
            src_id = (src_meta or KGNode(src, "claim", "")).metadata.get(
                "source_id") or src
            self.uncertainty_map.register_contradiction(
                topic=f"rehydrated_conflict:{src_id}", refs=refs,
                consequence=0.5)

    def rebuild_policy(self, events: List[Any]) -> int:
        """Rebuild method-level yield stats from persisted RESEARCH verdict
        events. Only verdict-producing actions count — container events
        ('cycle') and KG writes don't."""
        methods = {"investigate", "evaluate_strategy", "assess_expansion"}
        verdicts = {"CONFIRMED", "FALSIFIED", "INCONCLUSIVE",
                    "INSUFFICIENT_EVIDENCE"}
        restored = 0
        for ev in events:
            action = str(self.knowledge_graph._ev_field(ev, "action") or "")
            outcome = str(self.knowledge_graph._ev_field(ev, "outcome") or "")
            if action in methods and outcome in verdicts:
                self.policy.record(action, outcome)
                restored += 1
        return restored

    # ------------------------------------------------------------------
    # Stage helpers
    # ------------------------------------------------------------------

    def _create_ledger_entry(self, branch: Any) -> ResearchLedgerEntry:
        branch_conf = getattr(branch, "confidence", 0.5)
        if not isinstance(branch_conf, (int, float)) or not np.isfinite(branch_conf):
            branch_conf = 0.5
        evidence_graph = getattr(branch, "evidence_graph", None)
        if not hasattr(evidence_graph, "nodes"):
            evidence_graph = EvidenceGraph()
        hypotheses = getattr(branch, "hypotheses", None) or []
        return ResearchLedgerEntry(
            entry_id=_determinism.get_uuid(),
            hypothesis=hypotheses[0] if hypotheses else None,
            reasoning_steps=getattr(branch, "reasoning_trace", []),
            evidence_graph_snapshot=evidence_graph,
            composite_confidence=float(branch_conf),
            provenance=InstitutionalProvenance(
                pipeline_version="UCA-V6-RESEARCH",
                git_sha=self.git_sha,
            ),
        )

    @staticmethod
    def _fails_simulation(branch: Any, simulations: Dict[str, Any]) -> bool:
        """Measured-harm contract — identical to the trading stage."""
        sim = simulations.get(getattr(branch, "branch_id", ""), {})
        if not isinstance(sim, dict):
            return False
        action = str(
            (getattr(branch, "execution_plan", None) or {})
            .get("action", "")).upper()
        if action not in ("BUY", "SELL"):
            return False
        triggers = sim.get("invalidation_triggers") or []
        ev = sim.get("expected_value")
        return bool(triggers) or (
            isinstance(ev, (int, float)) and ev < 0)

    def _record_claim(
        self, report: ResearchReport, question_id: Optional[str] = None,
        tier: EvidenceTier = EvidenceTier.CONTROLLED,
        direction: Optional[str] = None,
    ) -> KGNode:
        """Every investigation lands in the KG as a claim + evidence
        linkage — cumulative memory, not a document pile."""
        claim = self.knowledge_graph.add_node(KGNode(
            node_id=f"claim:{report.research_id}",
            kind="claim",
            content=f"{report.question} -> {report.verdict}",
            tier=tier,
            confidence=report.composite_confidence,
            metadata={"verdict": report.verdict,
                      "symbol": report.symbol,
                      "direction": direction,
                      "sim": report.sim_summary},
        ))
        self._claims[claim.node_id] = claim
        evidence = self.knowledge_graph.add_node(KGNode(
            node_id=f"ev:{report.research_id}",
            kind="evidence",
            content=f"{report.evidence_node_count} verified evidence nodes",
            tier=tier,
            confidence=report.composite_confidence,
            metadata={"verdict": report.verdict},
        ))
        rel = ("supports" if report.verdict == "CONFIRMED"
               else "contradicts" if report.verdict == "FALSIFIED"
               else "depends_on")
        self.knowledge_graph.add_edge(evidence.node_id, rel, claim.node_id)
        if question_id and question_id in self.knowledge_graph.nodes:
            self.knowledge_graph.add_edge(
                claim.node_id, "derived_from", question_id)
        # Contradiction surfacing: a FALSIFIED verdict against a previously
        # CONFIRMED claim on the same topic becomes a contradiction edge —
        # never averaged away — and the older claim is retired from the
        # working set (knowledge hygiene: supersession, not accumulation).
        if report.verdict == "FALSIFIED":
            for other in list(self._claims.values()):
                if (other.node_id != claim.node_id
                        and other.status == "active"
                        and other.metadata.get("verdict") == "CONFIRMED"
                        and other.metadata.get("symbol") == report.symbol):
                    self.knowledge_graph.add_edge(
                        claim.node_id, "contradicts", other.node_id)
                    self.knowledge_graph.add_edge(
                        claim.node_id, "invalidates", other.node_id)
                    self.knowledge_graph.retire(other.node_id)
                    self._claims.pop(other.node_id, None)
                    self.uncertainty_map.register_contradiction(
                        topic=f"claim_conflict:{report.symbol}",
                        refs=[claim.node_id, other.node_id])
        return claim

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    def _investigate_operational(self, report: ResearchReport,
                                 market_data: Dict[str, Any]
                                 ) -> ResearchReport:
        """Operational-diagnostic experiment: questions about the system's
        own state (degraded model, suppressed action, unhealthy component)
        are answered from MEASURED state passed as
        ``market_data['operational_context']`` — not from market branch
        simulation, which cannot falsify a claim about our own pipeline.

        The caller supplies measured facts; the engine's job is honest
        verdict mapping:
          CONFIRMED — the questioned condition is supported by measured
                      evidence (e.g. a SPRT-degraded model really is
                      degraded in the monitor's verdict)
          FALSIFIED — measured state contradicts the question's premise
          INSUFFICIENT_EVIDENCE — no measured context was supplied"""
        ctx = (market_data or {}).get("operational_context")
        if not isinstance(ctx, Mapping):
            report.verdict = "INSUFFICIENT_EVIDENCE"
            report.sim_summary = {
                "experiment": "operational_diagnostic",
                "reason": "no measured operational_context supplied"}
            return report
        report.sim_summary = {"experiment": "operational_diagnostic",
                              "evidence": dict(ctx)}
        findings = ctx.get("findings")
        if isinstance(findings, list) and findings:
            supported = [f for f in findings
                         if isinstance(f, Mapping) and f.get("supported")]
            refuted = [f for f in findings
                       if isinstance(f, Mapping)
                       and f.get("supported") is False]
            if supported:
                report.verdict = "CONFIRMED"
                report.evidence_node_count = len(supported)
                report.composite_confidence = float(
                    ctx.get("confidence") or 0.6)
            elif refuted and len(refuted) == len(findings):
                report.verdict = "FALSIFIED"
                report.evidence_node_count = len(refuted)
            else:
                report.verdict = "INCONCLUSIVE"
                report.evidence_node_count = len(findings)
        elif ctx.get("evidence"):
            report.verdict = "CONFIRMED"
            report.evidence_node_count = 1
            report.composite_confidence = float(
                ctx.get("confidence") or 0.5)
        else:
            report.verdict = "INSUFFICIENT_EVIDENCE"
            report.sim_summary["reason"] = (
                "operational_context carried no findings or evidence")
        return report

    async def investigate(
        self,
        question: str,
        market_data: Dict[str, Any],
        evidence_chain: Optional[List[Any]] = None,
        advisory_artifacts: Optional[List[Any]] = None,
        question_id: Optional[str] = None,
    ) -> ResearchReport:
        """Run the full research pipeline for one question and return a
        verified, advisory-only report."""
        report = ResearchReport(
            research_id=_determinism.get_uuid(),
            question=str(question or ""),
            verdict="INCONCLUSIVE",
            created_at=time.time(),
            symbol=str((market_data or {}).get("symbol") or "unknown"),
        )
        report.question_type = _classify_question(question, market_data)

        if report.question_type == "operational":
            return self._investigate_operational(report, market_data)

        branches = await self.hypothesis_gen.generate_competing_branches(
            market_data,
            evidence_chain=evidence_chain or [],
            advisory_artifacts=advisory_artifacts or [])
        report.branches_considered = len(branches or [])
        if not branches:
            report.verdict = "INSUFFICIENT_EVIDENCE"
            return report

        sim_results: Dict[str, Any] = {}
        if hasattr(self.hypothesis_gen, "simulate_branches"):
            try:
                sim_results = await self.hypothesis_gen.simulate_branches(
                    branches, market_data=market_data) or {}
            except Exception as exc:
                logger.warning("ResearchEngine: simulation failed: %s", exc)

        ranked = sorted(
            branches,
            key=lambda b: b.confidence * b.probability * (1.0 - b.uncertainty),
            reverse=True)
        best = next(
            (b for b in ranked if not self._fails_simulation(b, sim_results)),
            None)
        if best is None:
            report.verdict = "FALSIFIED"
            report.sim_summary = {
                "reason": "every branch failed measured simulation"}
            return report
        report.surviving_branch = best.branch_id

        ledger = self._create_ledger_entry(best)
        reports = await self.verifier_swarm.run_swarm(ledger) \
            if self.verifier_swarm is not None else []
        if not isinstance(reports, list):
            reports = []
        ledger.verifier_reports = reports
        report.verifier_verdicts = [
            {
                "agent": getattr(r, "agent_name", "verifier"),
                "valid": bool(getattr(r, "is_valid", True)),
                "confidence": getattr(r, "confidence", None),
                "critique": getattr(r, "critique", None),
            }
            for r in reports]

        nodes = getattr(ledger.evidence_graph_snapshot, "nodes", {}) or {}
        report.evidence_node_count = len(nodes)
        if report.evidence_node_count == 0:
            report.verdict = "INSUFFICIENT_EVIDENCE"
            return report

        from ...verification.swarm import EvidenceGraphGate
        gate_passed = EvidenceGraphGate.verify_evidence_first(
            ledger, reports)
        vetoed = any(
            getattr(r, "is_valid", True) is False for r in reports)
        if vetoed:
            report.verdict = "FALSIFIED"
        elif not gate_passed:
            report.verdict = "INCONCLUSIVE"
        else:
            report.verdict = "CONFIRMED"

        graph_nodes = list(nodes.values()) if isinstance(nodes, dict) \
            else list(nodes)
        conf = getattr(best, "confidence", 0.0)
        conf = float(conf) if isinstance(conf, (int, float)) else 0.0
        sim_for_best = sim_results.get(best.branch_id) or {}
        win_p = sim_for_best.get("win_probability")
        ev = sim_for_best.get("expected_value")
        report.composite_confidence = float(np.clip(
            conf * (float(win_p) if isinstance(win_p, (int, float)) else 1.0),
            0.0, 1.0))
        report.sim_summary = {
            "graph_nodes": report.evidence_node_count,
            "win_probability": win_p,
            "expected_value": ev,
            "invalidation_triggers": sim_for_best.get(
                "invalidation_triggers", []),
            "consensus_valid": sum(
                1 for v in report.verifier_verdicts if v["valid"]),
            "consensus_total": len(report.verifier_verdicts),
        }

        # Knowledge + policy bookkeeping — every verdict is recorded.
        direction = str((getattr(best, "execution_plan", None) or {})
                        .get("action") or "").upper()
        claim = self._record_claim(
            report, question_id,
            direction=direction if direction in ("BUY", "SELL") else None)
        report.boundary_conditions = self.knowledge_graph.boundary_conditions(
            claim.node_id)
        self.policy.record("investigate", report.verdict)

        if self.hms is not None and hasattr(self.hms, "store_ledger_entry"):
            try:
                self.hms.store_ledger_entry(ledger)
            except Exception as exc:
                logger.warning("ResearchEngine: HMS store failed: %s", exc)
        if self.folder is not None and hasattr(self.folder, "fold_history"):
            try:
                self.folder.fold_history(ledger)
            except Exception as exc:
                logger.warning("ResearchEngine: fold failed: %s", exc)
        return report

    # ------------------------------------------------------------------
    # Evaluation / expansion / replication
    # ------------------------------------------------------------------

    def evaluate_strategy(
        self,
        question: str,
        candidate_positions: List[float],
        baseline_positions: List[float],
        bar_returns: List[float],
        cost_bps: float = 5.0,
        min_decisions: int = 30,
        fraction: float = 0.01,
        max_dd_regression: float = 0.0,
        dataset_id: str = "unlabelled",
        tier: EvidenceTier = EvidenceTier.CONTROLLED,
    ) -> ResearchReport:
        """Candidate vs frozen baseline on identical bars/costs. Diagnostic:
        promotion stays False — only the signed RSI evaluator with a sealed
        holdout attestation may authorize promotion."""
        from trading_bot.evaluation.frozen_baseline import (
            compare_candidate_vs_baseline)

        comparison = compare_candidate_vs_baseline(
            candidate_positions, baseline_positions, bar_returns,
            cost_bps=cost_bps, fraction=fraction,
            min_decisions=min_decisions,
            max_dd_regression=max_dd_regression)
        verdict_map = {
            "candidate_superior": "CONFIRMED",
            "not_superior": "FALSIFIED",
            "unprofitable": "FALSIFIED",
            "insufficient_evidence": "INSUFFICIENT_EVIDENCE",
            "no_activity": "INSUFFICIENT_EVIDENCE",
        }
        report = ResearchReport(
            research_id=_determinism.get_uuid(),
            question=str(question or "strategy evaluation"),
            verdict=verdict_map.get(
                comparison.get("verdict"), "INCONCLUSIVE"),
            created_at=time.time(),
            comparison=comparison,
        )
        claim = self._record_claim(report, tier=tier)
        claim.metadata["dataset_id"] = dataset_id
        self.policy.record("evaluate_strategy", report.verdict)
        return report

    def replicate(
        self,
        claim_id: str,
        evaluation_fn,
        level: ReplicationLevel = ReplicationLevel.INDEPENDENT_REPRODUCTION,
    ) -> ResearchReport:
        """Independent replication: re-run the claim's evaluation on a
        different slice/implementation. A single success never becomes
        accepted knowledge — replications accumulate."""
        replication = evaluation_fn()
        replicated_superior = replication.get("verdict") == "candidate_superior"
        node = self.knowledge_graph.add_node(KGNode(
            node_id=f"repl:{_determinism.get_uuid()}",
            kind="replication",
            content=f"replication of {claim_id} at level {level.name}",
            level=level,
            tier=(EvidenceTier.OOD_VALIDATED
                  if level >= ReplicationLevel.DISTRIBUTION_SHIFT
                  else EvidenceTier.REPLICATION),
            confidence=float(replicated_superior),
            metadata=dict(replication),
        ))
        if claim_id in self.knowledge_graph.nodes:
            self.knowledge_graph.add_edge(
                node.node_id, "replicates", claim_id)
        # Tier escalation is earned, not assumed: a claim only reaches
        # OOD_VALIDATED when a distribution-shift replication reproduced
        # the superior verdict.
        claim_node = (self._claims.get(claim_id)
                      or self.knowledge_graph.nodes.get(claim_id))
        if (claim_node is not None and replicated_superior
                and level >= ReplicationLevel.DISTRIBUTION_SHIFT):
            claim_node.tier = max(claim_node.tier, EvidenceTier.OOD_VALIDATED)
        profile = self.knowledge_graph.assess_claim(claim_id)
        verdict = ("CONFIRMED" if profile.level in ("HIGH", "MODERATE")
                   else "INCONCLUSIVE")
        return ResearchReport(
            research_id=node.node_id,
            question=f"replication of {claim_id}",
            verdict=verdict,
            created_at=time.time(),
            confidence_profile=profile,
            comparison=dict(replication),
        )

    def assess_expansion(
        self, target: str, *, horizon: str, dataset_bars: int = 0,
        has_paired_oos_evidence: bool = False,
        has_cost_model: bool = False,
        measured_max_drawdown: Optional[float] = None,
        drawdown_budget: Optional[float] = None,
    ) -> ResearchReport:
        """Readiness check for a new horizon/instrument — reports what the
        evidence gates require; ``ready=True`` means paper evaluation may
        begin, never authorization."""
        from trading_bot.evaluation.horizon_gate import (
            check_expansion_readiness)

        gate = check_expansion_readiness(
            target, dataset_bars=dataset_bars, horizon=horizon,
            has_paired_oos_evidence=has_paired_oos_evidence,
            has_cost_model=has_cost_model,
            measured_max_drawdown=measured_max_drawdown,
            drawdown_budget=drawdown_budget)
        report = ResearchReport(
            research_id=_determinism.get_uuid(),
            question=f"expansion readiness: {target} @ {horizon}",
            verdict="CONFIRMED" if gate.get("ready") else "INCONCLUSIVE",
            created_at=time.time(),
            comparison=gate,
        )
        self.policy.record("assess_expansion", report.verdict)
        return report

    # ------------------------------------------------------------------
    # Literature ingestion — claim-centric, not summarize-and-move-on
    # ------------------------------------------------------------------

    def ingest_literature(
        self, documents: List[Any],
    ) -> Dict[str, Any]:
        """Decompose external sources into claims. Each becomes a THEORETICAL-
        tier claim node (external assertions are untested by definition) plus
        an ``unvalidated_assumption`` uncertainty entry — the system now
        *knows it doesn't know* this claim, which is exactly what the
        research loop is for."""
        from .sources import extract_claims

        ingested = {"documents": 0, "claims": 0, "claim_ids": []}
        for doc in documents or []:
            for claim in extract_claims(doc):
                node = self.knowledge_graph.add_node(KGNode(
                    node_id=f"ext:{_determinism.get_uuid()}",
                    kind="claim",
                    content=claim.text,
                    tier=EvidenceTier.THEORETICAL,
                    confidence=claim.confidence,
                    metadata={
                        "source_id": doc.source_id,
                        "title": doc.title,
                        "extraction": claim.extraction,
                        "quantified": claim.quantified,
                        "hedged": claim.hedged,
                        "polarity": claim.polarity,
                        "external": True,
                    }))
                self._claims[node.node_id] = node
                self.uncertainty_map.register(
                    UncertaintyEntry(
                        topic=f"external_claim:{node.node_id}",
                        state="unvalidated_assumption",
                        confidence=claim.confidence,
                        consequence=0.4 if claim.quantified else 0.3))
                # Polarity-aware contradiction: an external claim with the
                # opposite polarity and strong content overlap contradicts
                # an existing external claim instead of duplicating it.
                for other in self._claims.values():
                    if (other.node_id == node.node_id
                            or not other.metadata.get("external")):
                        continue
                    other_pol = other.metadata.get("polarity", "positive")
                    if (other_pol != claim.polarity
                            and _content_overlap(node.content,
                                                 other.content) >= 0.5):
                        self.knowledge_graph.add_edge(
                            node.node_id, "contradicts", other.node_id)
                        self.uncertainty_map.register_contradiction(
                            topic=f"literature_conflict:{doc.source_id}",
                            refs=[node.node_id, other.node_id],
                            consequence=0.5)
                ingested["claim_ids"].append(node.node_id)
            ingested["documents"] += 1
            ingested["claims"] = len(ingested["claim_ids"])
        return ingested

    def ingest_path(self, path: str) -> Dict[str, Any]:
        """Load a directory/file of sources and ingest each."""
        from .sources import load_documents
        return self.ingest_literature(load_documents(path))

    # ------------------------------------------------------------------
    # Forward outcomes — real-world evidence feeding back into claims
    # ------------------------------------------------------------------

    def observe_forward_result(
        self, symbol: str, realized_return: float, regime: str,
        trade_ids: Optional[List[str]] = None,
        venue: str = "paper",
    ) -> List[str]:
        """A settled position is forward evidence: attach a REAL_WORLD-tier
        evidence node to every claim about that symbol — supporting or
        contradicting depending on the direction the claim asserted."""
        touched: List[str] = []
        direction = "BUY" if realized_return > 0 else "SELL"
        for claim in self._claims.values():
            meta = claim.metadata
            if meta.get("external") or meta.get("symbol") != symbol:
                continue
            claimed_direction = (meta.get("direction")
                                 or meta.get("sim", {}).get("direction"))
            evidence = self.knowledge_graph.add_node(KGNode(
                node_id=f"fwd:{_determinism.get_uuid()}",
                kind="evidence",
                content=(f"forward outcome on {symbol}: "
                         f"{realized_return:+.5f} ({regime})"),
                tier=EvidenceTier.REAL_WORLD,
                level=ReplicationLevel.REAL_WORLD_FORWARD,
                # Paper fills prove market-data logic but not live-market
                # execution — confidence capped below live-venue evidence.
                confidence=min(0.7 if venue == "paper" else 0.9,
                               0.5 + abs(realized_return) * 100),
                metadata={"realized_return": realized_return,
                          "regime": regime, "venue": venue,
                          "trade_ids": list(trade_ids or [])}))
            supports = (claimed_direction == direction
                        if claimed_direction in ("BUY", "SELL")
                        else realized_return > 0)
            self.knowledge_graph.add_edge(
                evidence.node_id,
                "supports" if supports else "contradicts",
                claim.node_id)
            if not supports:
                claim.failure_modes.append(
                    f"forward loss {realized_return:+.5f} in {regime}")
            touched.append(claim.node_id)
        return touched

    # ------------------------------------------------------------------
    # The full loop
    # ------------------------------------------------------------------

    def observe_signals(
        self,
        reliability: Optional[Dict[str, Any]] = None,
        anomalies: Optional[List[Tuple[str, float]]] = None,
    ) -> None:
        """Continuous-observation input: fold measured reliability and
        unexplained anomalies into the uncertainty map."""
        if reliability:
            self.uncertainty_map.update_from_reliability(reliability)
        for topic, consequence in (anomalies or []):
            self.uncertainty_map.register_unexplained(
                topic, consequence=consequence)

    def _replication_target(
        self, question: Any, market_data: Dict[str, Any],
    ) -> Optional[KGNode]:
        """Choose which claim a replication design would test: prefer a
        CONFIRMED claim on the observed symbol — replicating an established
        claim is higher-value than re-testing an already-falsified one."""
        symbol = str((market_data or {}).get("symbol") or "")
        confirmed = [n for n in self._claims.values()
                     if n.metadata.get("verdict") == "CONFIRMED"
                     and (not symbol or n.metadata.get("symbol") == symbol)]
        if confirmed:
            return max(confirmed, key=lambda n: n.confidence)
        return max(self._claims.values(), key=lambda n: n.confidence,
                   default=None)

    def capability_proposals(self) -> List[CapabilityProposal]:
        """All advisory proposals derivable from current knowledge —
        the journal's delivery surface for validated knowledge."""
        proposals = []
        for claim_id in list(self._claims):
            prop = self.propose_capability(claim_id)
            if prop is not None:
                proposals.append(prop)
        return proposals

    def propose_capability(self, claim_id: str
                           ) -> Optional[CapabilityProposal]:
        """The research→engineering boundary. Only claims with at least
        MODERATE confidence produce a proposal; the proposal itself carries
        no promotion authority."""
        claim_node = self.knowledge_graph.nodes.get(claim_id)
        if claim_node is not None and claim_node.status != "active":
            return None  # retired/superseded knowledge proposes nothing
        profile = self.knowledge_graph.assess_claim(claim_id)
        if profile.level not in ("MODERATE", "HIGH"):
            return None
        claim = self.knowledge_graph.nodes.get(claim_id)
        return CapabilityProposal(
            proposal_id=_determinism.get_uuid(),
            claim_id=claim_id,
            summary=getattr(claim, "content", claim_id),
            confidence_profile=profile,
            boundary_conditions=self.knowledge_graph.boundary_conditions(
                claim_id))

    async def research_cycle(
        self,
        market_data: Dict[str, Any],
        max_questions: int = 1,
        reliability: Optional[Dict[str, Any]] = None,
        anomalies: Optional[List[Tuple[str, float]]] = None,
    ) -> Dict[str, Any]:
        """One full loop iteration:

        observe → rank uncertainty → formalize question(s) → VoI selection
        → locked contract → investigate → verdict → KG/uncertainty/policy
        update → optional capability proposal.

        Returns a structured cycle record — honest about what was asked,
        what was learned, and what remains unknown."""
        self.observe_signals(reliability=reliability, anomalies=anomalies)

        # 2. Question formation from the top of the uncertainty map.
        questions = generate_questions(
            self.uncertainty_map, n=max(1, max_questions))
        questions = self.policy.rank_questions(questions)
        if not questions:
            snap = self.uncertainty_map.snapshot()
            return {"status": "no_consequential_uncertainty",
                    "reason": ("no tracked unknown cleared the "
                               "consequence/priority threshold"),
                    "tracked_uncertainties": len(snap),
                    "reliability_signals": len(reliability or {}),
                    "anomaly_signals": len(anomalies or []),
                    "uncertainty_map": snap}

        # 2b. Experiment-design search — per question, every executable
        # design competes on VoI: a fresh investigation, an independent
        # replication of an existing claim (when data supplies an
        # evaluation function), or a frozen-baseline evaluation (when
        # position series are supplied). "What should we run next?",
        # not "what can we run?"
        designs: List[Tuple[Any, ExperimentCandidate, str, Any]] = []
        for q in questions:
            base = dict(
                expected_info_gain=self.policy.estimate_info_gain(q.topic),
                decision_relevance=min(1.0, q.priority),
                compute_cost=float(q.resource_budget.get("observations", 60)),
                time_cost=1.0,
                risk_cost={"low": 0.2, "medium": 0.5, "high": 1.0}.get(
                    q.risk_level, 0.5))
            designs.append((q, ExperimentCandidate(
                description=f"investigate: {q.objective}", contract=None,
                capability_impact=0.7 if q.risk_level == "high" else
                    (0.5 if q.risk_level == "medium" else 0.3),
                replication_value=0.8 if q.unknowns else 0.5,
                **base), "investigate", None))
            repl_fn = market_data.get("replication_fn")
            if callable(repl_fn) and self._claims:
                target = self._replication_target(q, market_data)
                if target is not None:
                    designs.append((q, ExperimentCandidate(
                        description=f"replicate {target.node_id}",
                        contract=None,
                        capability_impact=0.8,
                        replication_value=0.95,
                        compute_cost=base["compute_cost"] * 0.4,
                        time_cost=0.5,
                        expected_info_gain=min(
                            0.95, base["expected_info_gain"] + 0.1),
                        decision_relevance=base["decision_relevance"],
                        risk_cost=base["risk_cost"]),
                        "replicate", target))
            positions = market_data.get("positions")
            if isinstance(positions, dict):
                designs.append((q, ExperimentCandidate(
                    description=f"evaluate: {q.objective}", contract=None,
                    capability_impact=0.75,
                    replication_value=0.7,
                    compute_cost=base["compute_cost"] * 0.3,
                    time_cost=0.4,
                    expected_info_gain=base["expected_info_gain"] * 0.9,
                    decision_relevance=base["decision_relevance"],
                    risk_cost=base["risk_cost"]),
                    "evaluate", positions))
        selected = sorted(designs, key=lambda t: self.voi.score(t[1]),
                          reverse=True)[:max_questions]

        cycle = {"questions": [q.question_id for q, _, _, _ in selected],
                 "voi_scores": [round(self.voi.score(c), 4)
                                for _, c, _, _ in selected],
                 "experiments": [{"type": k, "question_id": q.question_id}
                                 for q, _, k, _ in selected],
                 "reports": [], "contracts": []}
        for q, _candidate, kind, payload in selected:
            q_node = self.knowledge_graph.add_node(KGNode(
                node_id=f"q:{q.question_id}", kind="question",
                content=q.objective,
                confidence=1.0 - min(0.9, q.priority),
                metadata={"scope": q.scope,
                          "falsification_criteria": q.falsification_criteria,
                          "risk_level": q.risk_level,
                          "experiment_type": kind}))
            # 3. VoI-selected experiment — the design is a locked contract
            # committed before execution regardless of type.
            contract = make_contract(
                hypothesis_id=q.topic,
                baseline_id="frozen_baseline",
                treatment_id=f"research_{kind}",
                dataset_id=str(market_data.get("symbol", "unknown")),
                primary_metric="verified_verdict",
                expected_effect=0.0,
                minimum_meaningful_effect=0.0,
                falsification_criteria=tuple(q.falsification_criteria),
                compute_budget=float(
                    q.resource_budget.get("observations", 60)),
            )
            cycle["contracts"].append({
                "contract_id": contract.contract_id,
                "seal_hash": contract.seal_hash,
                "experiment_type": kind,
            })
            if kind == "replicate":
                report = self.replicate(
                    payload.node_id, market_data["replication_fn"],
                    level=ReplicationLevel.DIFFERENT_DATASET)
            elif kind == "evaluate":
                report = self.evaluate_strategy(
                    q.objective, **payload)
            else:
                report = await self.investigate(
                    q.objective, market_data, question_id=q_node.node_id)
            report.sim_summary["contract_seal"] = contract.seal_hash
            report.sim_summary["experiment_type"] = kind
            cycle["reports"].append(report.to_dict())

            # 4. Resolve the uncertainty cell with the measured confidence.
            self.uncertainty_map.resolve(
                q.topic, confidence=report.composite_confidence,
                evidence_ref=report.research_id)

        cycle["uncertainty_map"] = self.uncertainty_map.snapshot()
        cycle["contradictions"] = [
            [s, d] for s, d, _ in self.knowledge_graph.contradictions()]
        cycle["policy"] = self.policy.snapshot()
        cycle["status"] = "ok"
        return cycle
