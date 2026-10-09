import pytest
import asyncio
from trading_bot.core.verification.swarm import VerificationSwarm, EvidenceGraphGate
from trading_bot.core.verification.interface import VerifierVerdict

@pytest.mark.asyncio
async def test_verification_swarm_execution():
    swarm = VerificationSwarm()
    # Snapshot satisfying the falsification swarm's evidentiary bar: every
    # EVIDENCE/CLAIM node carries a provenance-allowlisted source_ref, the
    # claim is grounded by an evidence edge, and risk/liquidity/structure
    # quantities are measured numbers — not prose.
    snapshot = {
        "entry_id": "test_123",
        "composite_confidence": 0.7,
        "hypothesis": {"probability": 0.6},
        "reasoning_steps": [
            "Assessed tail risk and black swan scenarios",
            "Current regime supports the proposed action",
        ],
        "evidence_graph_snapshot": {
            "nodes": {
                "obs1": {
                    "node_id": "obs1",
                    "node_type": "EVIDENCE",
                    "metadata": {
                        "source_ref": "obs:EURUSD:m15",
                        "volume": 1200.0,
                        "volatility": 0.0021,
                        "trend": "up",
                        "regime": "trending",
                    },
                },
                "risk1": {
                    "node_id": "risk1",
                    "node_type": "EVIDENCE",
                    "metadata": {
                        "source_ref": "risk_eval:risk1",
                        "exposure": 0.4,
                    },
                },
                "sim1": {
                    "node_id": "sim1",
                    "node_type": "EVIDENCE",
                    "metadata": {
                        "source_ref": "sim:sim1",
                        "p95_drawdown": 0.01,
                    },
                },
                "claim1": {
                    "node_id": "claim1",
                    "node_type": "CLAIM",
                    "metadata": {"source_ref": "strategy:test_hyp"},
                },
            },
            "edges": [
                {"source_id": "obs1", "target_id": "claim1",
                 "relation": "SUPPORTS"},
            ],
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
