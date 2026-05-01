from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "trading_bot" / "decision_governance" / "epistemic_governance.py"
SPEC = importlib.util.spec_from_file_location("epistemic_governance_under_test", MODULE_PATH)
eg = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = eg
SPEC.loader.exec_module(eg)


def _claim(evidence_refs=None):
    return eg.GovernanceClaim(
        claim_id="claim-1",
        kind=eg.ClaimKind.THESIS,
        statement="BUY AAPL is justified",
        confidence=0.72,
        critical=True,
        evidence_refs=list(evidence_refs or ["evidence-1"]),
    )


def _evidence(state=None, strength=0.8):
    return eg.GovernanceEvidence(
        evidence_id="evidence-1",
        claim_id="claim-1",
        source="unit-test",
        observed_at=1_000.0,
        strength=strength,
        state=state or eg.EvidenceState.PRESENT,
        payload={"symbol": "AAPL"},
    )


def _verifier(passed=True, severity=0.0):
    return eg.ProofCheck(
        check_id="check-1",
        claim_id="claim-1",
        check_type="deterministic_verifier",
        passed=passed,
        severity=severity,
        details={"cost_adjusted_edge": 1.2},
    )


def _engine():
    return eg.EpistemicGovernanceEngine(clock=lambda: 1_000.0)


def test_sufficient_trade_claim_becomes_paper_only_proof_trace():
    engine = _engine()

    trace = engine.govern(
        action_candidate={"action": "BUY", "symbol": "AAPL", "confidence": 0.72},
        claims=[_claim()],
        evidence=[_evidence()],
        verifier_results=[_verifier()],
        uncertainty_profile={"ambiguity": 0.2},
        downstream_action="paper_trade_log",
    )

    assert trace.final_decision == eg.ProofDecision.PAPER_ONLY
    assert trace.proof_status == eg.ProofStatus.SUFFICIENT
    assert trace.graph_sufficient is True
    assert trace.trace_hash


def test_missing_evidence_defers_action():
    engine = _engine()

    trace = engine.govern(
        action_candidate={"action": "BUY", "symbol": "AAPL"},
        claims=[_claim(evidence_refs=["missing-evidence"])],
        evidence=[],
        verifier_results=[_verifier()],
    )

    assert trace.final_decision == eg.ProofDecision.DEFER
    assert trace.graph_sufficient is False
    assert "missing-evidence" in trace.missing_evidence


def test_unresolved_adversarial_challenge_rejects_action():
    engine = _engine()

    trace = engine.govern(
        action_candidate={"action": "BUY", "symbol": "AAPL"},
        claims=[_claim()],
        evidence=[_evidence()],
        verifier_results=[_verifier()],
        adversarial_challenges=[
            eg.ProofCheck(
                check_id="challenge-1",
                claim_id="claim-1",
                check_type="base_rate_objection",
                passed=False,
                severity=0.9,
                details={},
            )
        ],
    )

    assert trace.final_decision == eg.ProofDecision.REJECT
    assert trace.proof_status == eg.ProofStatus.INSUFFICIENT
    assert trace.graph_sufficient is False


def test_no_verifier_results_are_unverified():
    engine = _engine()

    trace = engine.govern(
        action_candidate={"action": "BUY", "symbol": "AAPL"},
        claims=[_claim()],
        evidence=[_evidence()],
    )

    assert trace.proof_status == eg.ProofStatus.UNVERIFIED
    assert trace.graph_sufficient is False
