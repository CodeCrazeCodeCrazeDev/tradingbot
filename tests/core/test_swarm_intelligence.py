"""Swarm-intelligence subsystem tests.

The swarm is the CSC's advisory deliberation substrate: advisory services
are nodes, directional calls are votes, four voting mechanisms aggregate
them, emergent signals attach, and a knowledge base learns per-node
skill from measured outcomes. The consensus is evidence — it must never
carry decision authority.
"""
import pytest

from trading_bot.core.csc.swarm_intelligence import (
    SwarmIntelligenceService, SwarmKnowledgeBase, domain_for)
from trading_bot.core.csc.swarm_intelligence.aggregation import (
    aggregate_all, bayesian, borda, majority, weighted)
from trading_bot.core.csc.swarm_intelligence.models import SwarmVote


def _vote(node, direction, conf=0.8, weight=1.0):
    return SwarmVote(node_id=node, direction=direction, confidence=conf,
                     domain=domain_for(node), weight=weight)


# ---------------------------------------------------------------- voting


def test_majority_picks_plurality():
    votes = [_vote("trend_a", "BUY"), _vote("momentum_b", "BUY"),
             _vote("rsi_c", "SELL")]
    r = majority(votes)
    assert r.direction == "BUY"
    assert r.confidence == pytest.approx(2 / 3)


def test_majority_tie_falls_to_hold():
    votes = [_vote("trend_a", "BUY"), _vote("momentum_b", "SELL")]
    r = majority(votes)
    assert r.direction == "HOLD"


def test_weighted_performance_dominates():
    votes = [_vote("trend_a", "BUY", conf=0.6, weight=0.4),
             _vote("momentum_b", "SELL", conf=0.9, weight=2.0)]
    r = weighted(votes)
    assert r.direction == "SELL"
    assert r.confidence > 0.0


def test_weighted_empty_is_hold():
    assert weighted([]).direction == "HOLD"
    assert weighted([]).confidence == 0.0


def test_bayesian_reliable_sensor_moves_posterior():
    votes = [_vote("a", "BUY"), _vote("b", "BUY"), _vote("c", "SELL")]
    r = bayesian(votes, {"a": 0.9, "b": 0.9, "c": 0.6})
    assert r.direction == "BUY"
    assert r.detail["p_buy"] > 0.5


def test_bayesian_unmeasured_nodes_floor_at_chance():
    # Unknown reliabilities: floor of 0.51 — inform, never dominate.
    votes = [_vote("x", "BUY", conf=0.9)]
    r = bayesian(votes, {})
    assert r.direction == "BUY"
    assert r.confidence < 0.15  # small log-odds move only


def test_bayesian_no_directional_votes_is_hold():
    votes = [_vote("a", "HOLD")]
    r = bayesian(votes, {})
    assert r.direction == "HOLD" and r.confidence == 0.0


def test_borda_ranked_ballot():
    votes = [_vote("a", "BUY", conf=0.9), _vote("b", "SELL", conf=0.4)]
    r = borda(votes)
    # BUY: 0.9; HOLD: 0.1 + 0.6=0.7 -> wait: b ranks SELL 0.4, HOLD 0.6
    # scores: BUY=0.9, SELL=0.4, HOLD=0.1+0.6=0.7 -> BUY wins
    assert r.direction == "BUY"
    assert r.detail["scores"]["HOLD"] == pytest.approx(0.7)


def test_aggregate_all_returns_four_methods():
    votes = [_vote("trend_a", "BUY"), _vote("rsi_b", "SELL"),
             _vote("momentum_c", "BUY")]
    results = aggregate_all(votes, {"trend_a": 0.8})
    assert set(results) == {"majority", "weighted", "bayesian", "borda"}


# ---------------------------------------------------------------- service


def _service():
    return SwarmIntelligenceService(reliability_tracker=None)


def test_deliberate_produces_consensus_and_methods():
    svc = _service()
    calls = [
        {"capability_id": "trend_alpha", "direction": "BUY",
         "confidence": 0.9},
        {"capability_id": "momentum_beta", "direction": "BUY",
         "confidence": 0.7},
        {"capability_id": "rsi_gamma", "direction": "SELL",
         "confidence": 0.6},
    ]
    c = svc.deliberate(calls, regime="UP", symbol="EURUSD")
    assert c.direction == "BUY"
    assert 0.0 < c.confidence <= 1.0
    assert len(c.methods) == 4
    assert len(c.votes) == 3


def test_deliberate_thin_electorate_is_hold():
    svc = _service()
    c = svc.deliberate(
        [{"capability_id": "trend_a", "direction": "BUY",
          "confidence": 0.9}],
        regime="UP")
    assert c.direction == "HOLD" and c.confidence == 0.0


def test_emergent_method_agreement():
    svc = _service()
    calls = [{"capability_id": f"trend_{i}", "direction": "BUY",
              "confidence": 0.8} for i in range(4)]
    c = svc.deliberate(calls, regime="UP")
    assert c.emergent.method_agreement == 1.0   # all 4 methods agree
    assert c.emergent.alignment == pytest.approx(1.0)


def test_emergent_cross_domain_split_lowers_agreement():
    svc = _service()
    calls = [
        {"capability_id": "trend_a", "direction": "BUY",
         "confidence": 0.8},
        {"capability_id": "rsi_b", "direction": "SELL",
         "confidence": 0.8},
        {"capability_id": "volume_c", "direction": "BUY",
         "confidence": 0.8},
    ]
    c = svc.deliberate(calls, regime="UP")
    # trend + volume -> BUY, mean_reversion -> SELL => 2/3 domains agree
    assert c.emergent.cross_domain_agreement == pytest.approx(2 / 3)
    assert c.emergent.alignment < 1.0


def test_emergent_high_confidence_cluster():
    svc = _service()
    calls = [{"capability_id": f"trend_{i}", "direction": "BUY",
              "confidence": 0.9} for i in range(3)]
    c = svc.deliberate(calls, regime="UP")
    assert c.emergent.cluster_strength == pytest.approx(1.0)
    assert c.emergent.dominant_nodes


def test_consensus_confidence_drops_with_split_methods():
    svc = _service()
    # borda may pick a different direction on engineered splits
    calls = [
        {"capability_id": "trend_a", "direction": "BUY",
         "confidence": 0.51},
        {"capability_id": "rsi_b", "direction": "SELL",
         "confidence": 0.9},
    ]
    c = svc.deliberate(calls, regime="UP")
    assert c.confidence <= 0.6  # floor-bound by method disagreement


# ------------------------------------------------------------ learning


def test_knowledge_base_learns_node_skill():
    kb = SwarmKnowledgeBase()
    for _ in range(9):
        kb.record_node_outcome("node_a", "UP", True)
    kb.record_node_outcome("node_a", "UP", False)
    # Beta(1,1) prior: a=10, b=2 -> mean 10/12
    assert kb.node_posterior("node_a", "UP") == pytest.approx(10 / 12)
    assert kb.node_posterior("node_a", "DOWN") > 0.5  # pooled fallback
    assert kb.node_posterior("unknown_node", "UP") == 0.5


def test_bayesian_uses_learned_reliability():
    svc = _service()
    # Teach the KB that node_a is reliable in UP
    for _ in range(20):
        svc.kb.record_node_outcome("trend_a", "UP", True)
    calls = [{"capability_id": "trend_a", "direction": "BUY",
              "confidence": 0.9}]
    c = svc.deliberate(calls, regime="UP")
    bay = c.methods["bayesian"]
    assert bay.direction == "BUY"
    assert bay.detail["p_buy"] > 0.8


def test_consensus_outcome_records_strategy():
    svc = _service()
    svc.record_consensus_outcome("UP", "BUY", True)
    rec = svc.kb.strategy_records["UP|BUY"]
    assert rec["n"] == 1 and rec["wins"] == 1


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "swarm_kb.json"
    svc = SwarmIntelligenceService()
    svc.set_persistence(str(path))
    svc.kb.record_node_outcome("trend_a", "UP", True)
    svc._persist()
    kb2 = SwarmKnowledgeBase.load(str(path))
    assert kb2.node_posterior("trend_a", "UP") > 0.5


def test_record_outcome_scores_pending_votes():
    svc = _service()
    calls = [
        {"capability_id": "trend_a", "direction": "BUY",
         "confidence": 0.8},
        {"capability_id": "trend_c", "direction": "BUY",
         "confidence": 0.8},
        {"capability_id": "rsi_b", "direction": "SELL",
         "confidence": 0.8},
    ]
    svc.deliberate(calls, regime="UP", symbol="EURUSD")
    svc.record_outcome("EURUSD", "BUY", "UP")
    assert svc.kb.node_posterior("trend_a", "UP") > 0.5
    assert svc.kb.node_posterior("rsi_b", "UP") < 0.5
    assert svc.kb.strategy_records["UP|BUY"]["wins"] == 1


# ------------------------------------------------------------- domains


def test_domain_classification():
    assert domain_for("trend_following_x") == "trend"
    assert domain_for("rsi_reversion") == "mean_reversion"
    assert domain_for("atr_volatility_model") == "volatility"
    assert domain_for("order_flow_depth") == "volume_liquidity"
    assert domain_for("news_sentiment") == "sentiment"
    assert domain_for("some_unclassified_svc") == "other"


# ------------------------------------------------------------ authority


def test_consensus_is_evidence_not_authority():
    """The consensus artifact carries no execution fields — no quantity,
    no order id, no veto flag. It is a description of the electorate."""
    svc = _service()
    calls = [{"capability_id": "trend_a", "direction": "BUY",
              "confidence": 0.99}]
    c = svc.deliberate(calls, regime="UP")
    d = c.to_dict()
    for forbidden in ("quantity", "order_id", "veto", "execute",
                      "stop_loss", "take_profit"):
        assert forbidden not in d
    # votes are transparent and auditable
    assert d["votes"][0]["node_id"] == "trend_a"


def test_feature_dict_is_point_in_time_safe():
    svc = _service()
    calls = [{"capability_id": "trend_a", "direction": "BUY",
              "confidence": 0.9},
             {"capability_id": "momentum_b", "direction": "BUY",
              "confidence": 0.8}]
    c = svc.deliberate(calls, regime="UP")
    feats = c.feature_dict()
    assert feats["swarm_signed_direction"] == 1.0
    assert feats["swarm_voter_count"] == 2.0
    assert 0.0 <= feats["swarm_consensus_confidence"] <= 1.0


# ------------------------------------------------- controller integration


@pytest.fixture
def csc(tmp_path):
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


def test_csc_constructs_with_swarm(csc):
    assert isinstance(csc._swarm_intel, SwarmIntelligenceService)
    # The swarm shares the measured reliability tracker — one source of
    # weights, not a competing performance memory.
    assert csc._swarm_intel._tracker is csc.reliability_tracker


@pytest.mark.asyncio
async def test_settlement_scores_swarm_nodes(csc):
    csc._pending_predictions["t-swarm"] = {
        "action": "BUY", "symbol": "EURUSD", "entry_price": 1.0,
        "confidence": 0.7, "regime": "bull",
        "advisory_calls": [
            {"capability_id": "trend_a", "direction": "BUY",
             "confidence": 0.8},
            {"capability_id": "rsi_b", "direction": "SELL",
             "confidence": 0.8},
        ],
    }
    result = await csc.record_outcome("t-swarm", exit_price=1.01)
    assert result["was_correct"] is True
    kb = csc._swarm_intel.kb
    assert kb.node_posterior("trend_a", "bull") > 0.5
    assert kb.node_posterior("rsi_b", "bull") < 0.5
    assert kb.strategy_records["bull|BUY"]["wins"] == 1


def test_swarm_snapshot_enriches_next_obs(csc):
    csc._last_swarm_snapshot = {
        "swarm_signed_direction": -1.0,
        "swarm_consensus_confidence": 0.7,
        "swarm_alignment": 0.9,
        "swarm_method_agreement": 1.0,
        "swarm_cross_domain": 0.5,
        "swarm_cluster_strength": 0.6,
        "swarm_voter_count": 3.0,
    }
    obs = {"symbol": "EURUSD", "price": 1.0, "volume": 1.0}
    csc._enrich_derived_features(obs)
    assert obs["swarm_signed_direction"] == -1.0
    assert obs["swarm_method_agreement"] == 1.0
    assert "swarm_alignment" in obs["_derived_features"]


def test_swarm_state_persistence_wires(tmp_path):
    path = tmp_path / "swarm_kb.json"
    csc_file = None
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    csc = CognitiveSystemController()
    try:
        csc.configure_swarm_state(str(path))
        csc._swarm_intel.kb.record_node_outcome("n", "UP", True)
        csc._swarm_intel._persist()
        assert path.exists()
    finally:
        CognitiveSystemController._instance = None
        del csc, csc_file


def test_swarm_report_shape(csc):
    report = csc.swarm_intelligence_report()
    assert set(report) >= {"deliberations", "nodes_measured",
                           "patterns_seen", "strategy_records"}
