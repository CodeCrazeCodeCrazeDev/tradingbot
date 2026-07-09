import pytest
import asyncio
from trading_bot.core.verification.swarm import VerificationSwarm, VerifierReport, EvidenceGraphGate

@pytest.mark.asyncio
async def test_swarm_veto_logic():
    """Verifies that the Verification Swarm can block flawed trades via high-confidence veto."""
    swarm = VerificationSwarm()

    # Simulate a research snapshot with a flaw
    snapshot = {"id": "R123", "causal_link": "invalid"}

    # Mock individual reports
    reports = [
        VerifierReport("V1", True, 0.9, "OK", []),
        VerifierReport("V2", True, 0.9, "OK", []),
        VerifierReport("V3", True, 0.9, "OK", []),
        # High confidence VETO
        VerifierReport("V4", False, 0.95, "Causal link is invalid", ["causal_hallucination"])
    ]

    # The EvidenceGraphGate should reject even if consensus is 75% because of high-conf veto
    gate_passed = EvidenceGraphGate.verify_evidence_first(snapshot, reports)
    assert gate_passed == False

@pytest.mark.asyncio
async def test_swarm_consensus_requirement():
    """Verifies that the 80% consensus threshold is enforced."""
    swarm = VerificationSwarm()
    snapshot = {"id": "R456"}

    # 2 out of 4 agree = 50% consensus
    reports = [
        VerifierReport("V1", True, 0.7, "OK", []),
        VerifierReport("V2", True, 0.7, "OK", []),
        VerifierReport("V3", False, 0.7, "Weak", []),
        VerifierReport("V4", False, 0.7, "Weak", [])
    ]

    gate_passed = EvidenceGraphGate.verify_evidence_first(snapshot, reports)
    assert gate_passed == False

    # 4 out of 4 agree = 100% consensus
    reports_ok = [VerifierReport(f"V{i}", True, 0.9, "OK", []) for i in range(4)]
    gate_passed_ok = EvidenceGraphGate.verify_evidence_first(snapshot, reports_ok)
    assert gate_passed_ok == True

@pytest.mark.asyncio
async def test_swarm_latency():
    """Measures swarm latency to ensure institutional responsiveness."""
    swarm = VerificationSwarm()
    snapshot = {"id": "R789"}

    import time
    start = time.time()
    reports = await swarm.run_swarm(snapshot)
    end = time.time()

    latency = end - start
    assert latency < 1.0 # Target: < 1s
    assert len(reports) == len(swarm.verifiers)
