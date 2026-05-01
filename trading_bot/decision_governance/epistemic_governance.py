"""Epistemic governance proof-trace engine.

This module is the code-level home for the claim -> evidence -> proof -> action
pipeline. It does not execute trades. It formalizes candidates into claims,
checks evidence and critical logic, attacks weak conclusions, and refuses action
when the reasoning graph is insufficient.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence
from uuid import uuid4


class ProofDecision(str, Enum):
    """Governance-level decision after proof review."""

    APPROVE = "APPROVE"
    PAPER_ONLY = "PAPER_ONLY"
    ABSTAIN = "ABSTAIN"
    DEFER = "DEFER"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ProofStatus(str, Enum):
    """Reasoning graph sufficiency status."""

    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    CONTRADICTED = "contradicted"
    UNVERIFIED = "unverified"


class ClaimKind(str, Enum):
    """Structured claim kinds used by the proof trace."""

    THESIS = "thesis"
    ASSUMPTION = "assumption"
    EVIDENCE = "evidence"
    CAUSAL_LINK = "causal_link"
    PREDICTED_OUTCOME = "predicted_outcome"
    INVALIDATION_CONDITION = "invalidation_condition"


class EvidenceState(str, Enum):
    """Evidence condition."""

    PRESENT = "present"
    MISSING = "missing"
    STALE = "stale"
    CONFLICTING = "conflicting"
    WEAK = "weak"


@dataclass(frozen=True)
class GovernanceClaim:
    """A formal claim in the reasoning graph."""

    claim_id: str
    kind: ClaimKind
    statement: str
    confidence: float
    critical: bool = True
    evidence_refs: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    invalidation_conditions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class GovernanceEvidence:
    """Evidence attached to a formal claim."""

    evidence_id: str
    claim_id: str
    source: str
    observed_at: float
    strength: float
    state: EvidenceState = EvidenceState.PRESENT
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProofCheck:
    """Verifier or adversarial challenge result."""

    check_id: str
    claim_id: str
    check_type: str
    passed: bool
    severity: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProofTrace:
    """Auditable proof trace shared across DGS, PHCE-D, COS, and gates."""

    trace_id: str
    action_candidate: Dict[str, Any]
    claims: List[GovernanceClaim]
    assumptions: List[GovernanceClaim]
    evidence_refs: List[str]
    missing_evidence: List[str]
    contradictions: List[str]
    adversarial_challenges: List[ProofCheck]
    verifier_results: List[ProofCheck]
    uncertainty_profile: Dict[str, Any]
    refusal_or_approval_reason: str
    final_decision: ProofDecision
    downstream_action: str
    outcome_ref: Optional[str]
    proof_status: ProofStatus
    graph_sufficient: bool
    created_at: float
    trace_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True)
class EpistemicGovernanceConfig:
    """Thresholds for proof sufficiency."""

    min_claim_confidence: float = 0.50
    min_evidence_strength: float = 0.50
    max_staleness_seconds: float = 86_400.0
    max_critical_failure_severity: float = 0.40
    max_uncertainty: float = 0.50
    require_evidence_for_critical_claims: bool = True
    trade_outputs_are_paper_only: bool = True


class EpistemicGovernanceEngine:
    """Self-auditing proof engine for governed autonomous decisions."""

    def __init__(
        self,
        config: Optional[EpistemicGovernanceConfig] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self.config = config or EpistemicGovernanceConfig()
        self.clock = clock or time.time
        self.traces: Dict[str, ProofTrace] = {}

    def govern(
        self,
        action_candidate: Mapping[str, Any],
        claims: Sequence[GovernanceClaim],
        evidence: Sequence[GovernanceEvidence],
        verifier_results: Optional[Sequence[ProofCheck]] = None,
        adversarial_challenges: Optional[Sequence[ProofCheck]] = None,
        uncertainty_profile: Optional[Mapping[str, Any]] = None,
        downstream_action: str = "none",
        outcome_ref: Optional[str] = None,
    ) -> ProofTrace:
        """Evaluate a candidate and return a proof trace."""

        now = self.clock()
        evidence_by_id = {item.evidence_id: item for item in evidence}
        verifier_list = list(verifier_results or [])
        challenge_list = list(adversarial_challenges or [])
        uncertainty = dict(uncertainty_profile or {})

        missing: List[str] = []
        contradictions: List[str] = []
        refusal_reasons: List[str] = []

        for claim in claims:
            if claim.critical and claim.confidence < self.config.min_claim_confidence:
                refusal_reasons.append(f"critical claim {claim.claim_id} confidence below threshold")

            if claim.critical and self.config.require_evidence_for_critical_claims and not claim.evidence_refs:
                missing.append(claim.claim_id)
                refusal_reasons.append(f"critical claim {claim.claim_id} has no evidence")

            for evidence_ref in claim.evidence_refs:
                item = evidence_by_id.get(evidence_ref)
                if item is None:
                    missing.append(evidence_ref)
                    refusal_reasons.append(f"referenced evidence {evidence_ref} is missing")
                    continue
                age = max(0.0, now - item.observed_at)
                if item.state == EvidenceState.MISSING:
                    missing.append(item.evidence_id)
                    refusal_reasons.append(f"evidence {item.evidence_id} is missing")
                elif item.state == EvidenceState.STALE or age > self.config.max_staleness_seconds:
                    refusal_reasons.append(f"evidence {item.evidence_id} is stale")
                elif item.state == EvidenceState.CONFLICTING:
                    contradictions.append(item.evidence_id)
                    refusal_reasons.append(f"evidence {item.evidence_id} is conflicting")
                elif item.state == EvidenceState.WEAK or item.strength < self.config.min_evidence_strength:
                    refusal_reasons.append(f"evidence {item.evidence_id} is weak")

        failed_verifiers = [
            check
            for check in verifier_list
            if not check.passed and check.severity > self.config.max_critical_failure_severity
        ]
        failed_challenges = [
            check
            for check in challenge_list
            if not check.passed and check.severity > self.config.max_critical_failure_severity
        ]

        for check in failed_verifiers:
            refusal_reasons.append(f"verifier {check.check_type} failed for claim {check.claim_id}")
        for challenge in failed_challenges:
            refusal_reasons.append(f"adversarial challenge {challenge.check_type} unresolved for claim {challenge.claim_id}")

        uncertainty_value = float(uncertainty.get("ambiguity", uncertainty.get("uncertainty", 0.0)) or 0.0)
        if uncertainty_value > self.config.max_uncertainty:
            refusal_reasons.append("uncertainty exceeds proof threshold")

        if contradictions:
            proof_status = ProofStatus.CONTRADICTED
        elif missing or failed_verifiers or failed_challenges:
            proof_status = ProofStatus.INSUFFICIENT
        elif not verifier_list:
            proof_status = ProofStatus.UNVERIFIED
            refusal_reasons.append("no verifier results attached")
        else:
            proof_status = ProofStatus.SUFFICIENT

        graph_sufficient = proof_status == ProofStatus.SUFFICIENT and not refusal_reasons
        final_decision = self._final_decision(action_candidate, graph_sufficient, refusal_reasons, uncertainty_value)
        reason = "proof graph sufficient" if graph_sufficient else "; ".join(refusal_reasons)

        trace_id = str(action_candidate.get("proof_trace_id") or f"proof-{uuid4().hex}")
        trace_without_hash = {
            "trace_id": trace_id,
            "action_candidate": dict(action_candidate),
            "claims": list(claims),
            "assumptions": [claim for claim in claims if claim.kind == ClaimKind.ASSUMPTION],
            "evidence_refs": sorted(evidence_by_id),
            "missing_evidence": sorted(set(missing)),
            "contradictions": sorted(set(contradictions)),
            "adversarial_challenges": challenge_list,
            "verifier_results": verifier_list,
            "uncertainty_profile": uncertainty,
            "refusal_or_approval_reason": reason,
            "final_decision": final_decision,
            "downstream_action": downstream_action if graph_sufficient else "refuse",
            "outcome_ref": outcome_ref,
            "proof_status": proof_status,
            "graph_sufficient": graph_sufficient,
            "created_at": now,
        }
        trace_hash = _stable_hash(trace_without_hash)
        trace = ProofTrace(trace_hash=trace_hash, **trace_without_hash)
        self.traces[trace.trace_id] = trace
        return trace

    def evaluate_action_candidate(
        self,
        action_candidate: Mapping[str, Any],
        evidence_payload: Mapping[str, Any],
        verifier_payload: Optional[Mapping[str, Any]] = None,
    ) -> ProofTrace:
        """Convenience path for one candidate with basic generated claims."""

        now = self.clock()
        action = str(action_candidate.get("action", action_candidate.get("decision", "UNKNOWN")))
        symbol = str(action_candidate.get("symbol", evidence_payload.get("symbol", "UNKNOWN")))
        thesis_id = f"claim-{_stable_hash({'action': action, 'symbol': symbol})[:12]}"
        evidence_id = f"evidence-{_stable_hash(evidence_payload)[:12]}"

        claims = [
            GovernanceClaim(
                claim_id=thesis_id,
                kind=ClaimKind.THESIS,
                statement=f"{action} is justified for {symbol}",
                confidence=float(action_candidate.get("confidence", 0.5) or 0.5),
                evidence_refs=[evidence_id],
                invalidation_conditions=["evidence weak", "verifier fails", "uncertainty too high"],
            )
        ]
        evidence = [
            GovernanceEvidence(
                evidence_id=evidence_id,
                claim_id=thesis_id,
                source=str(evidence_payload.get("source", "candidate_evidence")),
                observed_at=float(evidence_payload.get("observed_at", now)),
                strength=float(evidence_payload.get("strength", evidence_payload.get("confidence", 0.5)) or 0.5),
                state=EvidenceState(evidence_payload.get("state", EvidenceState.PRESENT.value)),
                payload=dict(evidence_payload),
            )
        ]
        verifier_results = [
            ProofCheck(
                check_id=f"check-{_stable_hash(verifier_payload or {})[:12]}",
                claim_id=thesis_id,
                check_type=str((verifier_payload or {}).get("check_type", "basic_verifier")),
                passed=bool((verifier_payload or {}).get("passed", True)),
                severity=float((verifier_payload or {}).get("severity", 0.0) or 0.0),
                details=dict(verifier_payload or {}),
            )
        ]
        return self.govern(action_candidate, claims, evidence, verifier_results=verifier_results)

    def _final_decision(
        self,
        action_candidate: Mapping[str, Any],
        graph_sufficient: bool,
        refusal_reasons: Sequence[str],
        uncertainty: float,
    ) -> ProofDecision:
        if graph_sufficient:
            action = str(action_candidate.get("action", action_candidate.get("decision", ""))).upper()
            if self.config.trade_outputs_are_paper_only and action in {"BUY", "SELL", "TRADE", "PAPER_TRADE_CANDIDATE"}:
                return ProofDecision.PAPER_ONLY
            return ProofDecision.APPROVE
        if any("missing" in reason or "stale" in reason for reason in refusal_reasons):
            return ProofDecision.DEFER
        if uncertainty > self.config.max_uncertainty:
            return ProofDecision.ABSTAIN
        return ProofDecision.REJECT


def create_epistemic_governance_engine(
    config: Optional[EpistemicGovernanceConfig] = None,
) -> EpistemicGovernanceEngine:
    """Factory for the epistemic governance engine."""

    return EpistemicGovernanceEngine(config=config)


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(inner) for inner in value]
    return value
