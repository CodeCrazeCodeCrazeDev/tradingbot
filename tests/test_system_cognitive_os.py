from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "trading_bot" / "cos" / "system_cognitive_os.py"
SPEC = importlib.util.spec_from_file_location("system_cognitive_os_under_test", MODULE_PATH)
cos = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cos
SPEC.loader.exec_module(cos)


def _strategy():
    return cos.Strategy(
        name="PHCE-D paper candidate review",
        precondition={"symbol": "AAPL", "volatility": {"lt": 0.2}},
        action_schema={
            "action": "PAPER_REVIEW",
            "properties": {"symbol": {"type": "string"}, "volatility": {"type": "number"}},
        },
        success_metrics=["paper_trade_sharpe_delta", "false_positive_reduction"],
        playbook={"steps": ["retrieve", "verify", "paper_log"]},
    )


def test_knowledge_graph_requires_typed_nodes_and_blocks_raw_notes():
    kg = cos.PropertyKnowledgeGraph()

    node_id = kg.add_node(
        cos.COSNodeType.BELIEF,
        {"name": "costs matter", "prior": 0.7},
        confidence=0.7,
        source="unit-test",
    )

    assert kg.nodes[node_id].node_type == cos.COSNodeType.BELIEF

    try:
        kg.add_node(cos.COSNodeType.CONCEPT, {"notes": "freeform markdown blob"})
    except ValueError as exc:
        assert "raw text property" in str(exc)
    else:
        raise AssertionError("raw text notes should be rejected")


def test_strategy_library_matches_by_precondition():
    system = cos.SystemCognitiveOperatingSystem()
    strategy_id = system.strategy_library.add_strategy(_strategy())

    matches = system.strategy_library.match_strategies({"symbol": "AAPL", "volatility": 0.12})

    assert matches
    assert matches[0].id == strategy_id


def test_observe_think_test_learn_success_reinforces_strategy():
    system = cos.SystemCognitiveOperatingSystem()
    strategy = _strategy()
    system.strategy_library.add_strategy(strategy)

    cycle = system.run_cycle(
        event={
            "kind": "market_context",
            "symbol": "AAPL",
            "volatility": 0.12,
            "concepts": ["cost_adjusted_edge"],
            "source": "unit-test",
        },
        objectives=["paper trade candidate review"],
        actual_outcome={"measured_result": 1.0, "success_flag": True},
    )

    assert cycle.plan.strategy is not None
    assert cycle.integration_result.mode == cos.COSActionMode.SHADOW
    assert cycle.decision_record.id in system.decision_memory.records
    assert strategy.performance["successes"] == 1
    assert not cycle.learned_failures


def test_failure_memory_blocks_repeated_edge_case():
    system = cos.SystemCognitiveOperatingSystem()
    strategy = _strategy()
    system.strategy_library.add_strategy(strategy)
    system.failure_memory.log_failure(
        cos.FailureRecord(
            failed_strategy_ref=strategy.strategy_node_ref or strategy.id,
            edge_case_conditions={"symbol": "AAPL", "volatility": {"gt": 0.1}},
            severity=5,
            derived_constraint={"avoid_if": {"symbol": "AAPL", "volatility": {"gt": 0.1}}},
        )
    )

    _, subgraph = system.observe(
        {"kind": "market_context", "symbol": "AAPL", "volatility": 0.12, "source": "unit-test"}
    )
    plan = system.think({"symbol": "AAPL", "volatility": 0.12, "context_nodes": list(subgraph.nodes)}, ["review"])

    assert plan.strategy is None
    assert plan.blocked_by_failures
    assert plan.confidence == 0.0


def test_bayesian_update_invalidates_low_posterior_belief():
    system = cos.SystemCognitiveOperatingSystem()
    belief_id = system.kg.add_node(
        cos.COSNodeType.BELIEF,
        {"name": "signal survives costs", "prior": 0.7},
        confidence=0.7,
        source="unit-test",
    )

    posterior = system.evolution_layer.bayesian_update_belief(
        belief_id,
        likelihood_outcome_given_belief=0.1,
        probability_outcome=0.7,
    )

    assert posterior < 0.3
    invalid_edges = [edge for edge in system.kg.edges if edge.subject == belief_id and edge.predicate == cos.COSEdgeType.CONTRADICTS]
    assert invalid_edges
