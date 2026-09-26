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
        contract: Optional[Mapping[str, Any]] = None,
        contract_signature: str = "",
        operator_public_key: Any = None,
        verifier_public_key: Any = None,
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
        self.contract = contract
        self.contract_signature = contract_signature
        self.operator_public_key = operator_public_key
        self.verifier_public_key = verifier_public_key
        self.archive: Dict[str, ImprovementGenome] = {}
        self.evidence: Dict[str, EvaluationEvidence] = {}
        self.decisions: List[PromotionDecision] = []

    async def run_cycle(self, domains: Optional[Iterable[ImprovementDomain]] = None) -> List[PromotionDecision]:
        """Run observe -> propose -> dream/replay -> evaluate -> approve -> stage."""
        decisions: List[PromotionDecision] = []
        selected = list(domains or ImprovementDomain)
        remaining = max(0, self.policy.max_candidates_per_cycle)
        for domain in selected:
            if remaining == 0:
                break
            baseline = await self._call(self.observer, domain)
            proposals = await self._call(self.proposer, domain, baseline)
            if isinstance(proposals, ImprovementGenome):
                proposals = [proposals]
            for genome in list(proposals or [])[:remaining]:
                remaining -= 1
                if genome.domain is not domain:
                    decisions.append(self._reject(genome, "domain mismatch"))
                    continue
                self.archive[genome.genome_id] = genome
                raw_evidence = await self._call(self.evaluator, genome, baseline)
                from .evaluation import EvaluationEngine
                signed_report = raw_evidence if isinstance(raw_evidence, Mapping) else {}
                verdict = EvaluationEngine().evaluate_verified(
                    genome, self.contract or {}, self.contract_signature, self.operator_public_key,
                    signed_report.get("report", {}), signed_report.get("signature", ""),
                    self.verifier_public_key,
                )
                if self.memory is None:
                    if verdict.get("status") == "eligible_for_operator_review":
                        verdict = {"status": "insufficient_evidence", "reason": "durable experiment ledger unavailable",
                                   "promotion_eligible": False}
                else:
                    try:
                        report = signed_report.get("report", {})
                        trial_id = report.get("trial_id") or genome.genome_id
                        self.memory.record_experiment(trial_id, genome.domain.value, genome.objective,
                                                      dict(genome.change_set),
                                                      {"contract_id": (self.contract or {}).get("contract_id"),
                                                       "genome_id": genome.genome_id})
                        self.memory.update_experiment_result(trial_id, verdict["status"], 0.0, verdict)
                        append = getattr(self.memory, "append_evidence", None)
                        if append is None:
                            raise RuntimeError("durable evidence ledger unavailable")
                        append(trial_id=trial_id, nonce=str(report.get("nonce") or trial_id),
                               payload={"verdict": verdict, "genome_id": genome.genome_id},
                               status=verdict["status"])
                    except Exception:
                        verdict = {"status": "insufficient_evidence", "reason": "trial replay or ledger write failure",
                                   "promotion_eligible": False}
                decision = PromotionDecision(
                    genome_id=genome.genome_id, status=verdict["status"],
                    reason=verdict["reason"], evidence=verdict,
                )
                decisions.append(decision)
        self.decisions.extend(decisions)
        return decisions

    async def _decide(
        self,
        genome: ImprovementGenome,
        evidence: EvaluationEvidence,
        baseline: Mapping[str, Any],
    ) -> PromotionDecision:
        return self._reject(genome, "legacy unverified evaluation path disabled", evidence)

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
