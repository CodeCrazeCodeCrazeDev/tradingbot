"""
Rigorous platform tests validating the state-centric Quantitative Discovery Platform (QDP) Kernel.
Verifies QDP Constitution enforcements, semantic Knowledge Graph edges, Belief Management Updates,
Scientific Judgment F-significance & Expected Information Gain (EIG), and Net Research Equity.
"""

import pytest
import numpy as np
import pandas as pd

from trading_bot.research.discovery_platform import (
    QuantitativeDiscoveryPlatform,
    ConstitutionalLayer,
    ConstitutionViolation,
    Observation,
    Question,
    HypothesisObject,
    Evidence,
    Theory,
    Decision,
    Action,
    ResearchCase,
    KnowledgeGraph,
    Belief,
    BeliefManagementSystem,
    ScientificJudgmentEngine,
    ResearchBalanceSheet
)


def test_qdp_constitution_enforcement():
    """Verifies that the Constitutional Layer rejects unverified claims or non-reproducible runs."""
    const = ConstitutionalLayer()

    # 1. Claim without evidence must raise ConstitutionViolation
    with pytest.raises(ConstitutionViolation):
        const.enforce_evidence_rule("EMA Cross always produces alpha.", evidence_ids=[])

    # Claim with evidence must pass cleanly
    const.enforce_evidence_rule("OBI predicts intraday FX drift.", evidence_ids=["evidence-obi-2026"])

    # 2. Experiment without seed or dataset version must raise ConstitutionViolation
    with pytest.raises(ConstitutionViolation):
        const.enforce_reproducibility_rule(seed=None, dataset_hash="")

    # Perfect reproducible experiment passes cleanly
    const.enforce_reproducibility_rule(seed=42, dataset_hash="abc998124ef")


def test_knowledge_graph_semantic_relations():
    """Verifies storing primitive nodes and asserting multi-hop semantic edges."""
    graph = KnowledgeGraph()

    obs = Observation(source="Tick_Data_Feed", data_summary="Raw market ticks")
    q = Question(text="Does volume profile reveal unmitigated order blocks?")
    hyp = HypothesisObject(question_id=q.id, statement="Unmitigated order blocks act as liquidity gravity wells.")

    graph.add_node(obs.id, obs)
    graph.add_node(q.id, q)
    graph.add_node(hyp.id, hyp)

    # Connect relations
    graph.add_relation(obs.id, "suggests_question", q.id)
    graph.add_relation(hyp.id, "formulated_from", q.id)

    suggested = graph.find_relations(obs.id, "suggests_question")
    assert q.id in suggested

    formulated = graph.find_relations(hyp.id, "formulated_from")
    assert q.id in formulated


def test_bayesian_belief_management_system():
    """Verifies belief formation, Bayesian evidence updates, and status transitions."""
    bms = BeliefManagementSystem()

    # Form initial belief
    b = bms.form_belief(statement="Liquidity sweep precedes mean reversion.", initial_confidence=0.50)
    assert b.status == "Hypothetical"
    assert b.supporting_evidence_count == 0

    # 1. Apply supportive empirical evidence (confidence increases towards 1.0)
    bms.update_belief(b.id, is_supportive=True, p_value=0.01)
    assert b.confidence > 0.50
    assert b.supporting_evidence_count == 1
    assert b.contradicting_evidence_count == 0

    # 2. Apply contradicting evidence (confidence decreases towards 0.0)
    old_conf = b.confidence
    bms.update_belief(b.id, is_supportive=False, p_value=0.02)
    assert b.confidence < old_conf
    assert b.contradicting_evidence_count == 1

    # 3. Simulate multiple trials resulting in tentative acceptance
    for _ in range(15):
        bms.update_belief(b.id, is_supportive=True, p_value=0.005)

    assert b.confidence > 0.85
    assert b.status == "Tentatively_Accepted"


def test_scientific_judgment_and_expected_information_gain():
    """Verifies empirical evidence acceptance and Expected Information Gain scheduling."""
    bms = BeliefManagementSystem()
    b = bms.form_belief(statement="High book imbalance leads to spread compression.", initial_confidence=0.50)

    judger = ScientificJudgmentEngine(bms)

    # Evidence 1: Fails reproducibility -> Rejected
    ev_corrupted = Evidence(experiment_id="exp-1", sharpe_ratio=2.5, p_value=0.01, deflated_sharpe=2.1, is_reproducible=False)
    is_valid, msg = judger.evaluate_evidence(ev_corrupted)
    assert is_valid is False
    assert "reproducible" in msg

    # Evidence 2: Fails p-value significance -> Rejected
    ev_insig = Evidence(experiment_id="exp-1", sharpe_ratio=2.5, p_value=0.12, deflated_sharpe=2.1, is_reproducible=True)
    is_valid, msg = judger.evaluate_evidence(ev_insig)
    assert is_valid is False
    assert "significant" in msg

    # Evidence 3: Passes validation -> Accepted
    ev_clean = Evidence(experiment_id="exp-1", sharpe_ratio=2.5, p_value=0.012, deflated_sharpe=2.1, is_reproducible=True)
    is_valid, msg = judger.evaluate_evidence(ev_clean)
    assert is_valid is True
    assert "ACCEPTED" in msg

    # Calculate Expected Information Gain (EIG)
    # Uncertainty is maximum at confidence=0.50 (entropy=1.0). Expected reduction is 40%
    eig = judger.calculate_expected_information_gain(b.id, entropy_reduction_pct=0.40)
    # EIG should be 1.0 * 0.40 = 0.40
    assert abs(eig - 0.40) < 1e-5


def test_research_balance_sheet_equity():
    """Verifies Net Research Equity calculations."""
    sheet = ResearchBalanceSheet(
        validated_theories_count=3,        # 3 * 1000 = $3000
        immutably_hashed_datasets_count=4, # 4 * 250  = $1000
        production_ready_alphas_count=1,   # 1 * 2000 = $2000
        unverified_hypotheses_count=2,     # 2 * 300  = $600
        technical_debt_score=10.0,         # 10 * 50  = $500
        known_data_quality_issues=1        # 1 * 400  = $400
    )

    # Net Equity = (3000+1000+2000) - (600+500+400) = 6000 - 1500 = $4500
    equity = sheet.compute_net_research_equity()
    assert equity == 4500.0


def test_quantitative_discovery_platform_lifecycle():
    """Verifies end-to-end SRP/QDP kernel opening traceable research cases."""
    qdp = QuantitativeDiscoveryPlatform()

    case = qdp.open_research_case(
        project_id="proj-hft-2026",
        question_text="Does microstructural imbalance predict high-frequency EURUSD moves?",
        alt_hypothesis="Yes, book asymmetry matches inventory positioning flows."
    )

    assert case.project_id == "proj-hft-2026"
    assert case.question.text == "Does microstructural imbalance predict high-frequency EURUSD moves?"
    assert case.hypothesis.statement == "Yes, book asymmetry matches inventory positioning flows."

    # Assert balance sheet unverified hypotheses liability increased by 1
    assert qdp.balance_sheet.unverified_hypotheses_count == 1
    assert qdp.balance_sheet.compute_net_research_equity() < 0.0  # liability outweighs zero assets initially
