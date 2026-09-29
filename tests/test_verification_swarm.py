import pytest
import asyncio
from trading_bot.core.verification.swarm import VerificationSwarm, EvidenceGraphGate
from trading_bot.core.verification.interface import VerifierVerdict

@pytest.mark.asyncio
async def test_verification_swarm_execution():
    swarm = VerificationSwarm()
    # Snapshot satisfying the falsification swarm's evidentiary bar:
    # tail-risk reasoning, regime alignment, and liquidity evidence.
    snapshot = {
        "entry_id": "test_123",
        "reasoning_steps": [
            "Assessed tail risk and black swan scenarios",
            "Current regime supports the proposed action",
        ],
        "evidence_graph_snapshot": {
            "nodes": {
                "n1": {"content": "liquidity depth is sufficient"},
                "n2": {"content": "volume profile supports entry"},
            }
        },
    }

    verdicts = await swarm.run_swarm(snapshot)

    assert len(verdicts) == len(swarm.verifiers)
    assert any(v.agent_name == "CausalVerifier" for v in verdicts)
    assert all(isinstance(v, VerifierVerdict) for v in verdicts)
    assert all(v.is_valid is True for v in verdicts)

def test_evidence_graph_gate_consensus():
    verdicts = [
        VerifierVerdict(agent_name="V1", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V2", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V3", is_valid=False, confidence=0.5),
    ]
    # 2/3 = 66% < 80% -> Should fail
    assert EvidenceGraphGate.verify_evidence_first({}, verdicts) is False

    verdicts_pass = [
        VerifierVerdict(agent_name="V1", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V2", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V3", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V4", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V5", is_valid=False, confidence=0.1),
    ]
    # 4/5 = 80% -> Should pass
    assert EvidenceGraphGate.verify_evidence_first({}, verdicts_pass) is True

def test_evidence_graph_gate_veto():
    verdicts = [
        VerifierVerdict(agent_name="V1", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V2", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V3", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V4", is_valid=True, confidence=0.9),
        VerifierVerdict(agent_name="V5", is_valid=False, confidence=0.99, critique="FATAL Hallucination"),
    ]
    # High confidence rejection (0.99 > 0.85) -> Should fail despite 80% consensus
    assert EvidenceGraphGate.verify_evidence_first({}, verdicts) is False
