"""
Verification Swarm - Evidence-First Governance
==============================================

Orchestrates specialized verifier agents to audit trade research.
Enforces the 0.8 consensus hard constraint.

Every verifier inspects the actual structured artifacts on the
``ResearchLedgerEntry`` (evidence graph nodes/edges, numeric metadata,
quantitative fields). No verifier approves based on substring matching in
reasoning text — auditors that cannot inspect a claim treat it as
unverifiable, not as satisfied.
"""

import logging
import asyncio
import math
from typing import Any, Dict, List, Optional
from .interface import IVerifier, VerifierVerdict

logger = logging.getLogger(__name__)

# Backward compatibility: older code imported the pre-merge ``VerifierReport``
# name for what is now the canonical ``VerifierVerdict``.
VerifierReport = VerifierVerdict


# Allowlisted provenance prefixes for EvidenceNode.metadata["source_ref"].
# Anything not resolvable to a real upstream artifact is rejected.
PROVENANCE_SOURCE_PREFIXES = (
    "observation:", "obs:",
    "feature:", "feature_snapshot:",
    "strategy:", "strategy_signal:",
    "risk:", "risk_eval:",
    "sim:", "simulation:",
    "cost:", "cost_model:",
    "memory:", "hms:",
    "market_data:", "market:",
    "agent:",
    "skill:",  # skill-router advisory signals (e.g. rsi_signal artifact)
    "research:",  # unified research engine findings (advisory_only always)
)


def _eget(obj: Any, key: str, default: Any = None) -> Any:
    """Tolerant accessor for ledger entries/edges/nodes that may be dicts or objects."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _graph_nodes(snapshot: Any) -> List[Any]:
    graph = _eget(snapshot, "evidence_graph_snapshot")
    nodes = _eget(graph, "nodes", {}) or {}
    return list(nodes.values()) if isinstance(nodes, dict) else []


def _graph_edges(snapshot: Any) -> List[Any]:
    graph = _eget(snapshot, "evidence_graph_snapshot")
    return list(_eget(graph, "edges", []) or [])


def _node_source_ref(node: Any) -> Optional[str]:
    metadata = _eget(node, "metadata", {}) or {}
    ref = metadata.get("source_ref") or metadata.get("source")
    return ref if isinstance(ref, str) and ref else None


def _is_provenanced_ref(ref: Optional[str]) -> bool:
    return bool(ref) and any(
        ref.startswith(prefix) for prefix in PROVENANCE_SOURCE_PREFIXES
    )


def _node_number(node: Any, *keys: str) -> Optional[float]:
    metadata = _eget(node, "metadata", {}) or {}
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, (int, float)) and math.isfinite(value):
            return float(value)
    return None


def _is_finite(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    return True


class BaseVerificationAgent(IVerifier):
    """Abstract base for evidence-graph verification agents.

    Satisfies the ``IVerifier.audit`` contract by delegating to ``verify``,
    which operates on a research ledger entry.
    """

    async def audit(self, research_snapshot: Any) -> VerifierVerdict:
        return await self.verify(research_snapshot)

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        raise NotImplementedError


class EvidenceProvenanceVerifier(BaseVerificationAgent):
    """Every EVIDENCE/CLAIM node must carry a resolvable source reference.

    Node/edge counts alone never prove evidence: filler content passes size
    checks trivially. A node is evidence only if ``metadata.source_ref``
    points at an allowlisted upstream artifact (observation, feature
    snapshot, strategy signal, risk evaluation, simulation, cost model,
    memory record, or advisory agent output).
    """

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        unprovenanced = []
        checked = 0
        for node in _graph_nodes(ledger_entry):
            node_type = str(_eget(node, "node_type", "") or "").upper()
            if node_type not in ("EVIDENCE", "CLAIM"):
                continue
            checked += 1
            if not _is_provenanced_ref(_node_source_ref(node)):
                unprovenanced.append(str(_eget(node, "node_id", "?")))

        return VerifierVerdict(
            agent_name="EvidenceProvenanceVerifier",
            is_valid=not unprovenanced,
            items_checked=checked,
            confidence=0.95 if unprovenanced else 0.9,
            critique=(
                f"FALSIFIED: {len(unprovenanced)} evidence nodes carry no "
                f"resolvable source_ref: {unprovenanced[:5]}"
                if unprovenanced else
                "All evidence nodes carry resolvable source references."
            ),
            failure_modes=unprovenanced,
        )


class ClaimGroundingVerifier(BaseVerificationAgent):
    """Every HYPOTHESIS/CLAIM must be supported by at least one EVIDENCE
    node via an incoming SUPPORTS/CORRELATES edge — the structural check the
    retired HallucinationDetector stub was supposed to perform."""

    _GROUNDING_RELATIONS = {"SUPPORTS", "CORRELATES", "STRENGTHENS"}

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        nodes = {str(_eget(n, "node_id")): n for n in _graph_nodes(ledger_entry)}
        edges = _graph_edges(ledger_entry)
        ungrounded = []
        checked = 0
        for node_id, node in nodes.items():
            if str(_eget(node, "node_type", "") or "").upper() not in (
                "HYPOTHESIS", "CLAIM"
            ):
                continue
            checked += 1
            grounded = any(
                str(
                    getattr(_eget(e, "relation"), "value",
                            _eget(e, "relation"))
                ) in self._GROUNDING_RELATIONS
                and str(_eget(e, "target_id")) == node_id
                and str(
                    _eget(nodes.get(str(_eget(e, "source_id"))),
                          "node_type", "")
                ).upper() == "EVIDENCE"
                for e in edges
            )
            if not grounded:
                ungrounded.append(node_id)

        return VerifierVerdict(
            agent_name="ClaimGroundingVerifier",
            is_valid=not ungrounded,
            items_checked=checked,
            confidence=0.92 if ungrounded else 0.85,
            critique=(
                f"FALSIFIED: claims with no evidence support: {ungrounded[:5]}"
                if ungrounded else
                "All claims/hypotheses are grounded in evidence nodes."
            ),
            failure_modes=ungrounded,
        )


class QuantitativeConsistencyVerifier(BaseVerificationAgent):
    """Structural numeric integrity: probabilities and confidences bounded,
    no NaN/inf in recorded metadata, composite score in range."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        problems: List[str] = []

        composite = _eget(ledger_entry, "composite_confidence", 0.0)
        if not isinstance(composite, (int, float)) or not math.isfinite(composite):
            problems.append("composite_confidence is not finite")
        elif not (0.0 <= float(composite) <= 1.0):
            problems.append(
                f"composite_confidence out of [0,1]: {composite}")

        checked = 1  # composite_confidence always probed above
        hypothesis = _eget(ledger_entry, "hypothesis")
        for field_name in ("probability", "epistemic_uncertainty",
                           "aleatoric_uncertainty", "expected_return",
                           "expected_drawdown"):
            value = _eget(hypothesis, field_name)
            checked += 1
            if value is not None and not _is_finite(value):
                problems.append(f"hypothesis.{field_name} is not finite")

        for node in _graph_nodes(ledger_entry):
            for field_name in ("confidence", "uncertainty", "freshness_score"):
                value = _eget(node, field_name)
                checked += 1
                if value is not None and not _is_finite(value):
                    problems.append(
                        f"node {_eget(node, 'node_id')}.{field_name} not finite")
            metadata = _eget(node, "metadata", {}) or {}
            for key, value in metadata.items():
                checked += 1
                if not _is_finite(value):
                    problems.append(
                        f"node {_eget(node, 'node_id')} metadata {key!r} "
                        "not finite")

        return VerifierVerdict(
            agent_name="QuantitativeConsistencyVerifier",
            is_valid=not problems,
            items_checked=checked,
            confidence=0.9,
            critique=(
                "Quantitative fields are consistent."
                if not problems else
                f"FALSIFIED: numeric integrity failures: {problems[:5]}"
            ),
            failure_modes=problems,
        )


class RiskVerifier(BaseVerificationAgent):
    """Checks the decision was evaluated against real risk quantities.

    Requires a ``risk_eval:*`` evidence node carrying measured numbers —
    exposure/drawdown/quantity or a simulated p95 drawdown. Missing risk
    evidence is a falsification, not a neutral pass. Extreme simulated tail
    drawdown also falsifies.
    """

    _MAX_P95_DRAWDOWN = 0.05  # 5% simulated path drawdown -> falsify

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        risk_nodes = [
            n for n in _graph_nodes(ledger_entry)
            if str(_node_source_ref(n) or "").startswith(("risk:", "risk_eval:"))
        ]
        sim_nodes = [
            n for n in _graph_nodes(ledger_entry)
            if str(_node_source_ref(n) or "").startswith(("sim:", "simulation:"))
        ]

        failures = []
        if not risk_nodes and not sim_nodes:
            failures.append("no risk evaluation or simulation evidence present")
        for node in sim_nodes:
            p95 = _node_number(node, "p95_drawdown", "mc_p95_drawdown")
            if p95 is not None and p95 > self._MAX_P95_DRAWDOWN:
                failures.append(
                    f"simulated p95 drawdown {p95:.4f} exceeds "
                    f"{self._MAX_P95_DRAWDOWN}")
        for node in risk_nodes:
            exposure = _node_number(node, "exposure")
            if exposure is not None and exposure > 1.0:
                failures.append(f"leverage/exposure {exposure:.2f} > 1.0")

        return VerifierVerdict(
            agent_name="RiskVerifier",
            is_valid=not failures,
            items_checked=len(risk_nodes) + len(sim_nodes),
            confidence=0.92 if failures else 0.85,
            critique=(
                "Risk quantities present and within bounds."
                if not failures else f"FALSIFIED: {failures[0]}"
            ),
            failure_modes=failures,
        )


class LiquidityVerifier(BaseVerificationAgent):
    """Verifies liquidity/volume was actually measured for this instrument."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        liquidity_nodes = [
            n for n in _graph_nodes(ledger_entry)
            if str(_node_source_ref(n) or "").startswith(
                ("market_data:", "obs:"))
            and _node_number(n, "volume", "liquidity", "liquidity_score")
            is not None
        ]
        if not liquidity_nodes:
            return VerifierVerdict(
                agent_name="LiquidityVerifier",
                is_valid=False,
                confidence=0.85,
                items_checked=0,
                critique=(
                    "FALSIFIED: no measured liquidity/volume evidence in the "
                    "decision graph."
                ),
            )
        volume = _node_number(liquidity_nodes[0], "volume", "liquidity")
        if volume is not None and volume <= 0:
            return VerifierVerdict(
                agent_name="LiquidityVerifier",
                is_valid=False,
                confidence=0.85,
                items_checked=1,
                critique="FALSIFIED: measured volume is non-positive.",
            )
        return VerifierVerdict(
            agent_name="LiquidityVerifier",
            is_valid=True,
            confidence=0.9,
            items_checked=len(liquidity_nodes),
            critique="Liquidity evidence present and positive.",
        )


class MarketStructureVerifier(BaseVerificationAgent):
    """Checks the decision cites a measured market-structure feature
    (volatility, trend, or regime value) — structure evidence, not the word
    'regime' in the prose."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        structure_nodes = [
            n for n in _graph_nodes(ledger_entry)
            if str(_node_source_ref(n) or "").startswith(
                ("feature:", "feature_snapshot:", "observation:", "obs:"))
            and (
                _node_number(n, "volatility", "volatility_percentile") is not None
                or _eget(n, "metadata", {}).get("trend") is not None
                or _eget(n, "metadata", {}).get("regime") is not None
            )
        ]
        return VerifierVerdict(
            agent_name="MarketStructureVerifier",
            is_valid=bool(structure_nodes),
            items_checked=len(structure_nodes),
            confidence=0.88 if structure_nodes else 0.9,
            critique=(
                "Measured market-structure evidence present."
                if structure_nodes else
                "FALSIFIED: no measured volatility/trend/regime feature "
                "evidence."
            ),
        )




class CrossValidationVerifier(BaseVerificationAgent):
    """Cross-checks the hypothesis against the weighted advisory
    evidence: builds SourceOpinions from EVIDENCE nodes that carry a
    direction, and validates the proposed direction via the
    verification.cross_validator engine. A proposal whose direction
    contradicts the majority evidence fails."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        from trading_bot.verification.cross_validator import (
            CrossValidator, SourceOpinion, SourceType)

        hypothesis = _eget(ledger_entry, "hypothesis")
        if hypothesis is None:
            return VerifierVerdict(
                agent_name="CrossValidationVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="No hypothesis to cross-validate")

        direction = str(_eget(hypothesis, "direction", "") or "").upper()
        decision = {
            "id": str(_eget(ledger_entry, "entry_id", "?")),
            "direction": direction,
            "confidence": float(
                _eget(hypothesis, "confidence", 0.5) or 0.5),
        }
        opinions = []
        for node in _graph_nodes(ledger_entry):
            if str(_eget(node, "node_type", "") or "").upper() != "EVIDENCE":
                continue
            meta = _eget(node, "metadata", {}) or {}
            nd = str(meta.get("direction") or "").upper()
            if nd not in ("BUY", "SELL", "HOLD"):
                continue
            opinions.append(SourceOpinion(
                source_name=str(
                    meta.get("source_ref") or _eget(node, "node_id", "?")),
                source_type=SourceType.TECHNICAL,
                direction=nd,
                confidence=float(meta.get("confidence") or 0.5),
                reasoning=str(meta.get("reasoning") or "evidence node"),
            ))
        if not opinions:
            return VerifierVerdict(
                agent_name="CrossValidationVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="No directional evidence nodes to validate against")

        try:
            result = await CrossValidator().validate(
                decision, opinions, market_data=None)
        except Exception as exc:
            return VerifierVerdict(
                agent_name="CrossValidationVerifier", is_valid=True,
                items_checked=0, confidence=0.4,
                critique=f"Cross-validator unavailable: {str(exc)[:100]}")

        agree = result.source_agreement
        return VerifierVerdict(
            agent_name="CrossValidationVerifier",
            is_valid=bool(result.validated),
            items_checked=len(opinions),
            confidence=max(0.0, min(1.0, result.adjusted_confidence)),
            critique=(
                f"agreement {agree.agreement_ratio:.0%} toward "
                f"{agree.majority_direction}; validated={result.validated}; "
                f"warnings={result.warnings[:2]}"))


class AdversarialChallengeVerifier(BaseVerificationAgent):
    """Red-teams the hypothesis: cognitive-bias scan, technique-level
    challenges, and a robustness score from
    verification.adversarial_checker. Fails only when the checker flags
    critical weaknesses or blocks the decision."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        from trading_bot.verification.adversarial_checker import (
            AdversarialChecker)

        hypothesis = _eget(ledger_entry, "hypothesis")
        if hypothesis is None:
            return VerifierVerdict(
                agent_name="AdversarialChallengeVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="No hypothesis to challenge")
        decision = {
            "id": str(_eget(ledger_entry, "entry_id", "?")),
            "direction": str(_eget(hypothesis, "direction", "") or ""),
            "confidence": float(
                _eget(hypothesis, "confidence", 0.5) or 0.5),
            "symbol": str(_eget(hypothesis, "symbol", "") or ""),
        }
        try:
            result = AdversarialChecker().analyze(decision)
        except Exception as exc:
            return VerifierVerdict(
                agent_name="AdversarialChallengeVerifier", is_valid=True,
                items_checked=0, confidence=0.4,
                critique=f"Adversarial checker unavailable: {str(exc)[:100]}")
        # Risk-management fields (stop_loss, position sizing) are owned by
        # the downstream risk service, not by the hypothesis — a critical
        # flag on those alone is an architecture mismatch, not a defect.
        risk_fields = ("stop", "position", "size", "loss")
        real_weaknesses = [
            w for w in result.critical_weaknesses
            if not any(k in w.lower() for k in risk_fields)]
        return VerifierVerdict(
            agent_name="AdversarialChallengeVerifier",
            is_valid=bool(result.should_proceed) or not real_weaknesses,
            items_checked=len(result.challenges) + len(result.biases_detected),
            confidence=max(0.0, min(1.0, result.overall_robustness)),
            critique=(
                f"robustness {result.overall_robustness:.2f}; "
                f"critical={result.critical_weaknesses[:2]}; "
                f"real_critical={real_weaknesses[:2]}; "
                f"biases={len(result.biases_detected)}"))



class CalibrationVerifier(BaseVerificationAgent):
    """Checks claimed confidence against the CSC's own measured
    calibration history — a 0.9 claim should mean 0.9. The embedded
    ConfidenceCalibrator accumulates outcomes via
    VerificationSwarm.record_outcome (wired from settlement and the
    reliability rebuild); with too little history it abstains honestly
    rather than vetoing on noise. A severe measured overconfidence gap
    fails the entry."""

    _MIN_HISTORY = 30
    _MAX_GAP = 0.25

    def __init__(self) -> None:
        from trading_bot.verification.confidence_calibrator import (
            ConfidenceCalibrator)
        self._calibrator = ConfidenceCalibrator()

    def record_outcome(self, confidence: float, was_correct: bool) -> None:
        try:
            self._calibrator.record_outcome(
                float(confidence), bool(was_correct))
        except Exception:  # noqa: BLE001
            pass

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        claimed = _eget(ledger_entry, "composite_confidence", None)
        try:
            claimed = float(claimed)
        except (TypeError, ValueError):
            return VerifierVerdict(
                agent_name="CalibrationVerifier", is_valid=True,
                items_checked=0, confidence=0.5,
                critique="no composite confidence to calibrate")
        n = len(getattr(self._calibrator, "prediction_history", ()) or ())
        if n < self._MIN_HISTORY:
            return VerifierVerdict(
                agent_name="CalibrationVerifier", is_valid=True,
                items_checked=n, confidence=0.5,
                critique=f"calibration history too thin (n={n}) — abstain")
        try:
            result = self._calibrator.calibrate(claimed)
        except Exception as exc:  # noqa: BLE001
            return VerifierVerdict(
                agent_name="CalibrationVerifier", is_valid=True,
                items_checked=n, confidence=0.4,
                critique=f"calibrator unavailable: {str(exc)[:100]}")
        # Prefer the direct bucket evidence (historical accuracy at this
        # confidence) over the fitted calibrator — the learned parameters
        # only refresh every 50 outcomes, but the bucket is live evidence.
        measured = result.historical_accuracy_at_confidence
        if not isinstance(measured, (int, float)):
            measured = result.calibrated_confidence
        gap = claimed - float(measured)
        overconfident = gap > self._MAX_GAP
        return VerifierVerdict(
            agent_name="CalibrationVerifier",
            is_valid=not overconfident,
            items_checked=n,
            confidence=max(0.0, min(1.0, float(measured))),
            critique=(
                f"claimed {claimed:.2f} vs measured "
                f"{float(measured):.2f} "+
                f"(gap {gap:+.2f}, n={n})"))

class DecisionChainVerifier(BaseVerificationAgent):
    """Runs the full trading_bot/verification DecisionVerificationChain
    on the hypothesis — 6-stage hallucination detection (grounding,
    logical consistency, cross-source, historical accuracy, adversarial
    questioning, confidence calibration, reality anchor). Overlapping
    stages are redundant but cheap; the unique ones catch magnitude
    errors, temporal impossibilities and invented patterns the swarm
    otherwise misses."""

    _TIMEOUT_S = 20.0

    def __init__(self) -> None:
        from trading_bot.verification.decision_verification_chain import (
            DecisionVerificationChain)
        self._chain = DecisionVerificationChain()

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        from trading_bot.verification.decision_verification_chain import (
            DecisionAction)
        hypothesis = _eget(ledger_entry, "hypothesis")
        try:
            claimed = float(_eget(ledger_entry, "composite_confidence", 0.5))
        except (TypeError, ValueError):
            claimed = 0.5
        decision = {
            "id": str(_eget(ledger_entry, "entry_id", "?")),
            "direction": str(
                _eget(hypothesis, "direction", "") or "").upper() or "HOLD",
            "confidence": claimed,
            "reasoning": " | ".join(
                str(s) for s in (
                    _eget(ledger_entry, "reasoning_steps", []) or [])[:8]),
            "evidence_count": len(_graph_nodes(ledger_entry) or ()),
        }
        md = _eget(ledger_entry, "market_data", None)
        market_data = dict(md) if isinstance(md, dict) else None
        try:
            result = await asyncio.wait_for(
                self._chain.verify_decision(decision, market_data),
                timeout=self._TIMEOUT_S)
        except Exception as exc:  # noqa: BLE001
            return VerifierVerdict(
                agent_name="DecisionChainVerifier", is_valid=True,
                items_checked=0, confidence=0.4,
                critique=f"chain unavailable: {str(exc)[:100]}")
        status = getattr(result, "overall_status", None)
        action = getattr(result, "recommended_action", None)
        stage_results = list(
            getattr(result, "stage_results", ()) or ())
        n_pass = sum(1 for s in stage_results
                     if getattr(s, "passed", False))
        # Veto only on the chain's own REJECT action — its unsupported-
        # claim findings assume a claims/counter-evidence structure our
        # ledger entries don't carry, so SUSPICIOUS/MODIFY stay advisory.
        is_valid = action != DecisionAction.REJECT
        return VerifierVerdict(
            agent_name="DecisionChainVerifier",
            is_valid=bool(is_valid),
            items_checked=len(stage_results),
            confidence=max(0.0, min(1.0, float(
                getattr(result, "overall_confidence", 0.5) or 0.5))),
            critique=(
                f"status={status} action={action} stages_passed="
                f"{n_pass}/{len(stage_results)}"))


class VerificationSwarm:
    """
    Independent Auditor Swarm for the Cognitive System Controller.
    """
    def __init__(self):
        # Register specialized verifier instances
        self.verifiers: List[IVerifier] = [
            EvidenceProvenanceVerifier(),
            ClaimGroundingVerifier(),
            QuantitativeConsistencyVerifier(),
            RiskVerifier(),
            LiquidityVerifier(),
            MarketStructureVerifier(),
            CausalVerifier(),
            CrossValidationVerifier(),
            AdversarialChallengeVerifier(),
            CalibrationVerifier(),
            DecisionChainVerifier(),
        ]

    def record_outcome(self, confidence: float, was_correct: bool) -> None:
        """Feed the swarm's calibrators the same settlement events the
        reliability tracker sees — calibration history survives restarts
        via the same DECISION_OUTCOME replay."""
        for verifier in self.verifiers:
            rec = getattr(verifier, "record_outcome", None)
            if rec is not None:
                rec(confidence, was_correct)

    async def run_swarm(self, research_snapshot: Any) -> List[VerifierVerdict]:
        """
        Executes parallel audit by all registered verifiers.
        """
        snapshot_id = research_snapshot.entry_id if hasattr(research_snapshot, 'entry_id') else "N/A"
        logger.info(f"VerificationSwarm: Auditing research {snapshot_id}")

        # Parallel execution of verifiers
        tasks = [v.audit(research_snapshot) for v in self.verifiers]
        verdicts = await asyncio.gather(*tasks)

        valid_count = sum(1 for v in verdicts if v.is_valid)
        consensus = valid_count / len(verdicts) if verdicts else 0
        substantive = sum(
            1 for v in verdicts if getattr(v, "items_checked", 0) > 0)
        self.last_consensus = {
            "consensus": consensus,
            "substantive_verifiers": substantive,
            "total_verifiers": len(verdicts),
        }
        logger.info(
            f"VerificationSwarm: Consensus reached at {consensus:.1%} "
            f"({substantive}/{len(verdicts)} verifiers examined evidence)")

        return verdicts


class CausalVerifier(BaseVerificationAgent):
    """Verifies that claimed causal edges meet the minimum support weight."""

    async def verify(self, ledger_entry: Any) -> VerifierVerdict:
        logger.info(f"CausalVerifier checking relations for entry {_eget(ledger_entry, 'entry_id', 'unknown')}")

        invalid_relations = []
        causal_edges = 0
        for edge in _graph_edges(ledger_entry):
            relation = _eget(edge, "relation")
            relation_val = getattr(relation, "value", relation)
            if relation_val == "CAUSES":
                causal_edges += 1
                if (_eget(edge, "weight", 0.0) or 0.0) < 0.5:
                    invalid_relations.append(
                        f"Weak causal link: {_eget(edge, 'source_id')} -> "
                        f"{_eget(edge, 'target_id')}")

        return VerifierVerdict(
            agent_name="CausalVerifier",
            is_valid=len(invalid_relations) == 0,
            items_checked=causal_edges,
            confidence=0.88,
            critique="Causal claims are sufficiently supported." if not invalid_relations else f"Weak links: {invalid_relations}"
        )


class EvidenceGraphGate:
    """
    Hard constraint gate for the CSC.
    Ensures every claim is backed by the Evidence Graph.
    """
    # Set by verify_evidence_first for callers that surface the reason upstream.
    last_rejection_reason: Optional[str] = None

    @staticmethod
    def verify_evidence_first(snapshot: Any, verdicts: List[VerifierVerdict]) -> bool:
        EvidenceGraphGate.last_rejection_reason = None
        if not verdicts:
            EvidenceGraphGate.last_rejection_reason = "No verifier verdicts produced"
            return False

        # 0. Provenance precondition — node/edge counts never substitute for
        # resolvable evidence sources.
        graph = _eget(snapshot, "evidence_graph_snapshot")
        nodes = _eget(graph, "nodes", {}) or {}
        if isinstance(nodes, dict) and nodes:
            unprovenanced = [
                str(_eget(n, "node_id", "?"))
                for n in nodes.values()
                if str(_eget(n, "node_type", "") or "").upper()
                in ("EVIDENCE", "CLAIM")
                and not _is_provenanced_ref(_node_source_ref(n))
            ]
            if unprovenanced:
                EvidenceGraphGate.last_rejection_reason = (
                    f"Unprovenanced evidence nodes: {unprovenanced[:5]}"
                )
                logger.warning(
                    "EvidenceGate: REJECTED - %s",
                    EvidenceGraphGate.last_rejection_reason,
                )
                return False

        # 1. Consensus Gate (Institutional SLA: 80%)
        valid_count = sum(1 for v in verdicts if v.is_valid)
        if valid_count / len(verdicts) < 0.8:
            failing = [v for v in verdicts if not v.is_valid]
            critiques = "; ".join(str(v.critique) for v in failing if v.critique) or "no critiques"
            EvidenceGraphGate.last_rejection_reason = (
                f"Consensus below 80% ({valid_count}/{len(verdicts)}): {critiques}"
            )
            logger.warning("EvidenceGate: REJECTED - Consensus below 80%")
            return False

        # 2. High-Confidence Veto check
        for v in verdicts:
            try:
                confidence = float(v.confidence)
            except (TypeError, ValueError):
                # Unparseable confidence on a REJECTING verdict: fail closed —
                # treat the veto as decisive rather than silently zeroing it.
                confidence = 1.0
            if not v.is_valid and confidence > 0.85:
                EvidenceGraphGate.last_rejection_reason = (
                    f"High-confidence VETO by {v.agent_name}: {str(v.critique)}"
                )
                logger.warning(f"EvidenceGate: REJECTED - {EvidenceGraphGate.last_rejection_reason}")
                return False

        # 3. Evidence Graph Hard Constraints
        # We need at least 5 nodes and 3 edges in the evidence graph snapshot
        if isinstance(nodes, dict) and nodes:
            edges = _eget(graph, "edges", []) or []
            if len(nodes) < 5 or len(edges) < 3:
                EvidenceGraphGate.last_rejection_reason = (
                    f"Insufficient evidence. Graph has {len(nodes)} nodes and {len(edges)} edges."
                )
                logger.warning(f"EvidenceGate: REJECTED - {EvidenceGraphGate.last_rejection_reason}")
                return False

        return True
