import pytest
from trading_bot.core.security.defense import EvidenceLineageEvaluator

def test_colluding_majority_single_lineage_collapse():
    votes = [
        {"agent_id": "rogue_1", "proposal": "BUY_RISKY_ASSET", "evidence_refs": ["obs_999"]},
        {"agent_id": "rogue_2", "proposal": "BUY_RISKY_ASSET", "evidence_refs": ["obs_999"]},
        {"agent_id": "rogue_3", "proposal": "BUY_RISKY_ASSET", "evidence_refs": ["obs_999"]},
        {"agent_id": "rogue_4", "proposal": "BUY_RISKY_ASSET", "evidence_refs": ["obs_999"]},
        {"agent_id": "honest_1", "proposal": "HOLD_POSITION", "evidence_refs": ["obs_001", "obs_002"]},
    ]

    res = EvidenceLineageEvaluator.evaluate_consensus(votes)

    assert res["total_agent_votes"] == 5
    assert res["unique_lineage_count"] == 2
    assert res["lineage_weight"] == 1.0
    assert res["effective_consensus_ratio"] == 0.2
