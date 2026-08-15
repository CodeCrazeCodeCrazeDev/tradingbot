"""
Unit tests validating state-centric Research Kernel and Object lifecycles.
Verifies ResearchObject payload hashing, immutability locks under validation/production,
directed dependency graph multi-hop relations, economic priority scores,
and validation gate enforcements in ResearchKernel transitions.
"""

import pytest
import pandas as pd
import numpy as np

from trading_bot.research.research_kernel import (
    LifecycleState,
    StateTransition,
    ImmutabilityViolation,
    ResearchObject,
    ResearchDependencyGraph,
    ResearchCost,
    ResearchEconomicsEngine,
    ResearchKernel
)


def test_research_object_immutability():
    """Verifies that payload locks prevent illegal modifications to validated/production objects."""
    raw_payload = {"formula": "log(close/open)", "parameters": [10, 20]}
    obj = ResearchObject(name="Log_Return_Feature", obj_type="FEATURE", raw_payload=raw_payload)

    assert obj.version == 1
    assert len(obj.payload_hash) == 64
    assert obj.payload["parameters"] == [10, 20]

    # 1. Modification in DRAFT state is allowed (and increases version)
    draft_payload = {"formula": "log(close/open)", "parameters": [5, 10]}
    obj.update_payload(draft_payload)
    assert obj.version == 2
    assert obj.payload["parameters"] == [5, 10]

    # 2. Re-assign state to VALIDATED
    obj.state = LifecycleState.VALIDATED

    # 3. Modification in VALIDATED state must raise ImmutabilityViolation
    with pytest.raises(ImmutabilityViolation):
        obj.update_payload({"formula": "corrupted"})


def test_research_dependency_graph():
    """Verifies storing nodes, connecting relations, and tracing multi-hop ancestry."""
    network = ResearchDependencyGraph()

    # Create mock hypothesis, experiment, and feature objects
    hyp = ResearchObject("Hyp1", "HYPOTHESIS", {"text": "OBI predicts drift"})
    exp = ResearchObject("Exp1", "EXPERIMENT", {"seed": 101})
    feat = ResearchObject("Feat1", "FEATURE", {"col": "obi_pips"})

    network.add_object_node(hyp)
    network.add_object_node(exp)
    network.add_object_node(feat)

    # Register directed edge connections
    network.add_relation_edge(hyp.id, exp.id, "derived_to")
    network.add_relation_edge(exp.id, feat.id, "derived_to")

    # Trace ancestral provenance: hyp must be ancestor of feat
    ancestors = network.get_provenance_trail(feat.id)
    assert hyp.id in ancestors
    assert exp.id in ancestors
    assert len(ancestors) == 2


def test_research_economics_prioritization():
    """Verifies financial cost calculation and EIG-to-Cost priority scores."""
    engine = ResearchEconomicsEngine(dev_hour_rate=100.0, core_hour_rate=0.20)

    cost_cheap = ResearchCost(developer_hours=5.0, compute_cores_hours=100.0, data_acquisition_cost_usd=50.0)
    cost_expensive = ResearchCost(developer_hours=50.0, compute_cores_hours=1000.0, data_acquisition_cost_usd=500.0)

    cheap_usd = engine.calculate_total_cost_usd(cost_cheap)
    # dev = 500, compute = 20, data = 50 -> 570 USD
    assert cheap_usd == 570.0

    expensive_usd = engine.calculate_total_cost_usd(cost_expensive)
    # dev = 5000, compute = 200, data = 500 -> 5700 USD
    assert expensive_usd == 5700.0

    # Compute priority scores for an experiment with 10.0 expected information gain (EIG)
    score_cheap = engine.calculate_priority_score(expected_information_gain=10.0, cost=cost_cheap)
    score_expensive = engine.calculate_priority_score(expected_information_gain=10.0, cost=cost_expensive)

    # Cheap experiment must rank significantly higher in priority
    assert score_cheap > score_expensive


def test_research_kernel_promotion_gates():
    """Verifies that the core kernel enforces lineage verification before promoting objects."""
    kernel = ResearchKernel()

    # Register parent source node
    parent = ResearchObject("Raw_Source_OBI", "DATASET", {"source": "ticks"})
    kernel.register_object(parent)

    # Case 1: Promoting object with verified parent lineage -> Success
    derived = ResearchObject("Cleaned_OBI_Features", "FEATURE", {"normalize": True})
    kernel.register_object(derived, parent_ids=[parent.id])

    # Transition to VALIDATED (constitutional check passes because parent_ids exists)
    kernel.execute_state_transition(
        obj_id=derived.id,
        target_state=LifecycleState.VALIDATED,
        approver="Risk_Committee_Officer",
        rationale="Passed cost-modeled walk forward."
    )

    assert derived.state == LifecycleState.VALIDATED
    assert len(derived.transition_history) == 1
    assert derived.transition_history[0].approved_by == "Risk_Committee_Officer"

    # Case 2: Attempting to validate a DRAFT object that lacks ANY parent lineage -> Denied (raises ImmutabilityViolation)
    lonely_obj = ResearchObject("Speculative_Alpha_Indicator", "ALPHA", {"tech": "MACD"})
    kernel.register_object(lonely_obj)

    with pytest.raises(ImmutabilityViolation):
        kernel.execute_state_transition(
            obj_id=lonely_obj.id,
            target_state=LifecycleState.VALIDATED,
            approver="Risk_Committee_Officer",
            rationale="Speculative indicator validation."
        )
