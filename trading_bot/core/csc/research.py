"""Unified research engine — the one research capability of the system.

First principles: research is a question about the world answered by
evidence, counterfactual test, and adversarial verification — not by a
second brain. This engine is a *subordinate service*: the CognitiveSystemController
composes it from the same grounded components the trading pipeline already
uses, invokes it through a single entry point, and consumes its reports as
advisory evidence. It has no order surface, no risk authority, and no path
to the execution bus — every report carries ``advisory_only=True`` and
``promotion_eligible=False`` (only the signed RSI contract/evaluator flow
may authorize strategy promotion).

Pipeline (reuses the canonical machinery rather than duplicating it):

    question ──► competing hypotheses (HypothesisGenerator, grounded
                 evidence graphs, real provenance)
             ──► counterfactual simulation (CounterfactualSimulator)
             ──► adversarial verification (VerificationSwarm +
                 EvidenceGraphGate)
             ──► measured confidence (ledger + swarm consensus)
             ──► ResearchReport ──► durable audit + memory (HMS/folder)

Verdict semantics:
    CONFIRMED             — swarm consensus passed the evidence gate
    FALSIFIED             — at least one verifier invalidated the thesis
    INCONCLUSIVE          — gate rejected on insufficient evidence
    INSUFFICIENT_EVIDENCE — no usable evidence nodes at all
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from trading_bot.core.governance.determinism import determinism as _determinism

from ..hms.models import (
    ResearchLedgerEntry,
    EvidenceGraph,
    InstitutionalProvenance,
)

logger = logging.getLogger(__name__)


@dataclass
class ResearchReport:
    """A verified research finding. Advisory-only by construction — the
    dataclass has no field that can carry authority."""

    research_id: str
    question: str
    verdict: str                      # CONFIRMED / FALSIFIED / INCONCLUSIVE /
                                      # INSUFFICIENT_EVIDENCE
    created_at: float
    symbol: str = "unknown"
    branches_considered: int = 0
    surviving_branch: Optional[str] = None
    evidence_node_count: int = 0
    verifier_verdicts: List[Dict[str, Any]] = field(default_factory=list)
    sim_summary: Dict[str, Any] = field(default_factory=dict)
    composite_confidence: float = 0.0
    comparison: Optional[Dict[str, Any]] = None
    advisory_only: bool = True
    promotion_eligible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "research_id": self.research_id,
            "question": self.question,
            "verdict": self.verdict,
            "created_at": self.created_at,
            "symbol": self.symbol,
            "branches_considered": self.branches_considered,
            "surviving_branch": self.surviving_branch,
            "evidence_node_count": self.evidence_node_count,
            "verifier_verdicts": list(self.verifier_verdicts),
            "sim_summary": dict(self.sim_summary),
            "composite_confidence": self.composite_confidence,
            "comparison": dict(self.comparison) if self.comparison else None,
            "advisory_only": True,
            "promotion_eligible": False,
        }

    def to_advisory_artifact(self) -> Dict[str, Any]:
        """Shape consumed by the observation pipeline's advisory channel:
        the artifact enters evidence graphs as an ``agent:research_engine``
        node marked advisory_only — evidence, never authority."""
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


class ResearchEngine:
    """One research pipeline, composed of the CSC's canonical components.

    Constructed by the controller via ``configure_research``; may also be
    instantiated directly with the same component contracts for isolated
    testing."""

    def __init__(
        self,
        hypothesis_gen: Any,
        verifier_swarm: Any,
        hms: Any = None,
        folder: Any = None,
        git_sha: str = "unknown",
    ) -> None:
        self.hypothesis_gen = hypothesis_gen
        self.verifier_swarm = verifier_swarm
        self.hms = hms
        self.folder = folder
        self.git_sha = git_sha or "unknown"

    # ------------------------------------------------------------------

    def _create_ledger_entry(self, branch: Any) -> ResearchLedgerEntry:
        """Same provenance contract as the trading pipeline — real git sha,
        real evidence graph, measured branch confidence."""
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
        """Same measured-harm contract as the trading stage: invalidation
        triggers or negative simulated expected value fail a directional
        branch; weak win probability merely discounts confidence."""
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

    async def investigate(
        self,
        question: str,
        market_data: Dict[str, Any],
        evidence_chain: Optional[List[Any]] = None,
        advisory_artifacts: Optional[List[Any]] = None,
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

        # 1-2. Grounded competing hypotheses + counterfactual simulation.
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

        # 3. Rank and select the best branch surviving simulation.
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

        # 4. Adversarial verification on a real ledger entry.
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

        # 5. Evidence gate + verdict.
        from ..verification.swarm import EvidenceGraphGate
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

        # 6. Measured confidence + sim summary.
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

        # 7. Memory: verified ledgers fold into the same store the trading
        # pipeline uses — research is queryable memory, not floating prose.
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
    ) -> ResearchReport:
        """Evidence-backed strategy evaluation: candidate vs frozen baseline
        on identical bars and identical costs. The report is diagnostic —
        promotion stays False; only the signed RSI evaluator with a sealed
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
            "insufficient_evidence": "INSUFFICIENT_EVIDENCE",
            "no_activity": "INSUFFICIENT_EVIDENCE",
        }
        return ResearchReport(
            research_id=_determinism.get_uuid(),
            question=str(question or "strategy evaluation"),
            verdict=verdict_map.get(
                comparison.get("verdict"), "INCONCLUSIVE"),
            created_at=time.time(),
            comparison=comparison,
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
        begin, never authorization. ``target`` is the instrument/scope
        (e.g. ``"EURUSD+GBPUSD"``); ``horizon`` is the trading-horizon
        class (``scalp`` / ``intraday`` / ``swing``)."""
        from trading_bot.evaluation.horizon_gate import (
            check_expansion_readiness)

        gate = check_expansion_readiness(
            target, dataset_bars=dataset_bars, horizon=horizon,
            has_paired_oos_evidence=has_paired_oos_evidence,
            has_cost_model=has_cost_model,
            measured_max_drawdown=measured_max_drawdown,
            drawdown_budget=drawdown_budget)
        return ResearchReport(
            research_id=_determinism.get_uuid(),
            question=f"expansion readiness: {target}",
            verdict="CONFIRMED" if gate.get("ready") else "INCONCLUSIVE",
            created_at=time.time(),
            comparison=gate,
        )
