"""Human-guided, safety-gated recursive self-improvement loop.

The loop improves proposals and policies, not live trading code. Candidate
changes are evaluated against immutable evaluators and replay evidence before a
human can promote them to a staged configuration.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from .improvement_genome import (
    EvaluationEvidence,
    ImprovementDomain,
    ImprovementGenome,
    PromotionDecision,
)

logger = logging.getLogger(__name__)

Observer = Callable[[ImprovementDomain], Any]
Proposer = Callable[[ImprovementDomain, Mapping[str, Any]], Any]
Evaluator = Callable[[ImprovementGenome, Mapping[str, Any]], Any]
Approver = Callable[[ImprovementGenome, EvaluationEvidence], Any]
Promoter = Callable[[ImprovementGenome, EvaluationEvidence], Any]


@dataclass(frozen=True)
class ImprovementPolicy:
    """Hard defaults for safe recursive improvement."""

    min_candidate_gain: float = 0.02
    min_oos_gain: float = 0.0
    max_drawdown_increase: float = 0.0
    min_robustness: float = 0.5
    require_deterministic_replay: bool = True
    require_data_provenance: bool = True
    require_human_approval: bool = True
    max_candidates_per_cycle: int = 3
    dry_run: bool = True


class HumanGuidedRecursiveImprovementLoop:
    """Bounded RSI coordinator with archive, dream evaluation, and rollback seams."""

    def __init__(
        self,
        *,
        observer: Observer,
        proposer: Proposer,
        evaluator: Evaluator,
        approver: Optional[Approver] = None,
        promoter: Optional[Promoter] = None,
        policy: Optional[ImprovementPolicy] = None,
        evolution_gate: Any = None,
        rollback_manager: Any = None,
        memory: Any = None,
    ) -> None:
        self.observer = observer
        self.proposer = proposer
        self.evaluator = evaluator
        self.approver = approver
        self.promoter = promoter
        self.policy = policy or ImprovementPolicy()
        self.evolution_gate = evolution_gate
        self.rollback_manager = rollback_manager
        self.memory = memory
        self.archive: Dict[str, ImprovementGenome] = {}
        self.evidence: Dict[str, EvaluationEvidence] = {}
        self.decisions: List[PromotionDecision] = []

    async def run_cycle(self, domains: Optional[Iterable[ImprovementDomain]] = None) -> List[PromotionDecision]:
        """Run observe -> propose -> dream/replay -> evaluate -> approve -> stage."""
        decisions: List[PromotionDecision] = []
        selected = list(domains or ImprovementDomain)
        for domain in selected:
            baseline = await self._call(self.observer, domain)
            proposals = await self._call(self.proposer, domain, baseline)
            if isinstance(proposals, ImprovementGenome):
                proposals = [proposals]
            for genome in list(proposals or [])[: self.policy.max_candidates_per_cycle]:
                if genome.domain is not domain:
                    decisions.append(self._reject(genome, "domain mismatch"))
                    continue
                self.archive[genome.genome_id] = genome
                raw_evidence = await self._call(self.evaluator, genome, baseline)
                evidence = self._coerce_evidence(genome, raw_evidence)
                self.evidence[genome.genome_id] = evidence
                decision = await self._decide(genome, evidence, baseline)
                decisions.append(decision)
                if decision.approved and not self.policy.dry_run and self.promoter is not None:
                    await self._call(self.promoter, genome, evidence)
        self.decisions.extend(decisions)
        return decisions

    async def _decide(
        self,
        genome: ImprovementGenome,
        evidence: EvaluationEvidence,
        baseline: Mapping[str, Any],
    ) -> PromotionDecision:
        violations = list(evidence.violations)
        if not evidence.safety_passed:
            violations.append("safety evaluator failed")
        if self.policy.require_deterministic_replay and not evidence.deterministic_replay_passed:
            violations.append("deterministic replay failed")
        if self.policy.require_data_provenance and not evidence.data_provenance:
            violations.append("missing data provenance")
        if evidence.candidate_gain < self.policy.min_candidate_gain:
            violations.append("candidate gain below threshold")
        if evidence.oos_gain < self.policy.min_oos_gain:
            violations.append("out-of-sample gain is not positive")
        if evidence.robustness_metrics.get("score", 0.0) < self.policy.min_robustness:
            violations.append("robustness below threshold")
        baseline_dd = float(baseline.get("max_drawdown", 0.0))
        candidate_dd = float(evidence.oos_metrics.get("max_drawdown", baseline_dd))
        if candidate_dd > baseline_dd + self.policy.max_drawdown_increase:
            violations.append("drawdown regression")

        if self.evolution_gate is not None and not await self._evolution_gate(genome, evidence):
            violations.append("EvolutionGate rejected candidate")
        if violations:
            return self._reject(genome, "; ".join(dict.fromkeys(violations)), evidence)

        if self.policy.require_human_approval:
            if self.approver is None:
                return self._reject(genome, "human approval is required but no approver is configured", evidence)
            approved = bool(await self._call(self.approver, genome, evidence))
            if not approved:
                return self._reject(genome, "human approval rejected or unavailable", evidence)

        snapshot_id = ""
        if self.rollback_manager is not None:
            snapshot_id = self.rollback_manager.create_snapshot(
                genome.domain.value,
                genome.genome_id,
                dict(genome.change_set),
                metadata={"fingerprint": genome.fingerprint},
            )
        return PromotionDecision(
            genome_id=genome.genome_id,
            status="approved",
            reason="all safety, replay, OOS, robustness, and human gates passed",
            requires_human_approval=self.policy.require_human_approval,
            human_approved_by="human_gate",
            rollback_snapshot_id=snapshot_id,
            evidence=evidence.to_dict(),
        )

    async def _evolution_gate(self, genome: ImprovementGenome, evidence: EvaluationEvidence) -> bool:
        validator = getattr(self.evolution_gate, "validate_improvement", None)
        if validator is None:
            return False
        candidate = {
            "reward": evidence.candidate_metrics.get("score", 0.0),
            "oos_score": evidence.oos_metrics.get("score", 0.0),
            "safety_score": 1.0 if evidence.safety_passed else 0.0,
            "deterministic_replay_success": 1.0 if evidence.deterministic_replay_passed else 0.0,
            **dict(genome.safety_constraints),
        }
        baseline = {"reward": evidence.baseline_metrics.get("score", 0.0)}
        result = validator(genome.genome_id, candidate, baseline)
        return bool(await result) if inspect.isawaitable(result) else bool(result)

    @staticmethod
    def _coerce_evidence(genome: ImprovementGenome, raw: Any) -> EvaluationEvidence:
        if isinstance(raw, EvaluationEvidence):
            return raw
        raw = raw if isinstance(raw, Mapping) else {}
        return EvaluationEvidence(
            genome_id=genome.genome_id,
            baseline_metrics=raw.get("baseline_metrics", {}),
            candidate_metrics=raw.get("candidate_metrics", {}),
            oos_metrics=raw.get("oos_metrics", {}),
            robustness_metrics=raw.get("robustness_metrics", {}),
            safety_passed=bool(raw.get("safety_passed", False)),
            deterministic_replay_passed=bool(raw.get("deterministic_replay_passed", False)),
            data_provenance=raw.get("data_provenance", {}),
            violations=list(raw.get("violations", [])),
            evaluator_version=str(raw.get("evaluator_version", "alphaalgo-evaluator-v1")),
        )

    @staticmethod
    def _reject(
        genome: ImprovementGenome,
        reason: str,
        evidence: Optional[EvaluationEvidence] = None,
    ) -> PromotionDecision:
        return PromotionDecision(
            genome_id=genome.genome_id,
            status="rejected",
            reason=reason,
            evidence=evidence.to_dict() if evidence else {},
        )

    @staticmethod
    async def _call(function: Callable[..., Any], *args: Any) -> Any:
        result = function(*args)
        return await result if inspect.isawaitable(result) else result
