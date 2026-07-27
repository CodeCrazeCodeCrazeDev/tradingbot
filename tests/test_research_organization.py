"""
Rigorous tests validating the institutional Quantitative Research Organization Platform.
Verifies Scientific Philosophy boundaries, thematic Program assignments, Scientific Reviews,
Knowledge integration hubs, Technology Transfer schema packaging, and Meta-Research analytics.
"""

import pytest
import pandas as pd
import numpy as np

from trading_bot.research.research_organization import (
    ScientificPhilosophy,
    PhilosophySpecification,
    ResearchProgramManager,
    ScientificReviewer,
    KnowledgeIntegrationHub,
    TechnologyTransferOfficer,
    MetaResearchEngine,
    AlphaAlgoResearchOrganization
)


def test_scientific_philosophy_enforcement():
    """Verifies that the Scientific Philosophy rejects models violating complexity or significance boundaries."""
    philosophy = ScientificPhilosophy()

    # Case 1: High significance, acceptable parameters, has falsifications -> Passes
    is_valid, msg = philosophy.challenge_scientific_validity(
        p_value=0.012,
        param_count=150,
        has_falsifications=True
    )
    assert is_valid is True
    assert "PASS" in msg

    # Case 2: Insignificant p-value -> Rejected
    is_valid, msg = philosophy.challenge_scientific_validity(
        p_value=0.15,
        param_count=150,
        has_falsifications=True
    )
    assert is_valid is False
    assert "p-value" in msg

    # Case 3: Over-complex model parameters -> Rejected
    is_valid, msg = philosophy.challenge_scientific_validity(
        p_value=0.01,
        param_count=5000,  # exceeds default limit of 1000
        has_falsifications=True
    )
    assert is_valid is False
    assert "complexity" in msg


def test_research_program_grouping():
    """Verifies assignment of projects to long-running institutional research programs."""
    manager = ResearchProgramManager()

    # Assign project to Microstructure program
    manager.assign_to_program("MICROSTRUCTURE", "proj-obi-2026")

    program = manager.programs["MICROSTRUCTURE"]
    assert "proj-obi-2026" in program.active_project_ids
    assert program.director == "Quant_Dir_HFT"


def test_scientific_peer_review():
    """Verifies that the Scientific Reviewer challenges methodology and checks assumptions."""
    reviewer = ScientificReviewer()

    # Case 1: Complete assumptions and out-of-sample metrics -> Approved
    verdict_approved = reviewer.perform_review(
        experiment_id="exp-fvg-99",
        assumptions=["Stationarity verified", "Zero look-ahead checks passed"],
        metrics={"is_sharpe": 2.2, "oos_sharpe": 1.95}
    )
    assert verdict_approved.verdict == "APPROVED"
    assert verdict_approved.methodology_valid is True

    # Case 2: Incomplete assumptions -> Rejected
    verdict_rejected = reviewer.perform_review(
        experiment_id="exp-ema-01",
        assumptions=["Technical trends hold"],  # only 1 assumption, fails checklist
        metrics={"is_sharpe": 1.5, "oos_sharpe": 0.5}
    )
    assert verdict_rejected.verdict == "REJECT"
    assert verdict_rejected.methodology_valid is False


def test_knowledge_integration_synthesis():
    """Verifies cross-experiment synthesis of features and predictable markets."""
    hub = KnowledgeIntegrationHub()

    # Register 2 successful microstructure experiments
    hub.integrate_experiment_findings(
        feature_names=["obi_score", "vwap_dist"],
        market="EURUSD",
        was_successful=True
    )
    hub.integrate_experiment_findings(
        feature_names=["obi_score"],
        market="EURUSD",
        was_successful=True
    )

    # Register 1 failed indicators experiment
    hub.integrate_experiment_findings(
        feature_names=["ema_cross_lag"],
        market="EURUSD",
        was_successful=False
    )

    efficacy = hub.query_integrated_efficacy()
    assert "obi_score" in efficacy["top_integrated_features"]
    assert "EURUSD" in efficacy["most_predictable_markets"]
    # Failed feature should be lower in priority/rank
    assert "ema_cross_lag" not in efficacy["top_integrated_features"]


def test_technology_transfer_packaging():
    """Verifies production-ready model packaging, API schemas, and rollback hashes."""
    officer = TechnologyTransferOfficer()

    pkg = officer.package_model_for_production(
        model_uuid="model-xgboost-992",
        code_hash="sha256-abcdef8812a"
    )

    assert pkg.model_uuid == "model-xgboost-992"
    assert pkg.reversion_rollback_hash == "sha256-abcdef8812a"
    assert pkg.runbook_generated is True
    assert "endpoint" in pkg.api_schema
    assert pkg.api_schema["endpoint"] == "/api/v1/predict/model-xgboost-992"


def test_meta_research_live_correlation_monitoring():
    """Verifies Meta-Research metrics tracking validation-to-live performance correlations."""
    hub = KnowledgeIntegrationHub()
    engine = MetaResearchEngine(hub)

    # Case 1: Validation method predicts live results perfectly (<0.50 Sharpe delta) -> increases accuracy
    accuracy1 = engine.record_validation_live_correlation(
        validation_method="WalkForward_Bailey_3_Split",
        predicted_sharpe=2.45,
        live_sharpe=2.15
    )
    assert accuracy1 == 100.0

    # Case 2: Fails prediction -> accuracy drops
    accuracy2 = engine.record_validation_live_correlation(
        validation_method="WalkForward_Bailey_3_Split",
        predicted_sharpe=2.45,
        live_sharpe=1.12  # large delta of 1.33 Sharpe
    )
    assert accuracy2 == 50.0  # 1 out of 2 accurate


def test_research_organization_unification():
    """Verifies that the AlphaAlgoResearchOrganization class initializes and binds components."""
    org = AlphaAlgoResearchOrganization()
    assert org is not None
    assert org.philosophy is not None
    assert org.program_manager is not None
    assert org.reviewer is not None
    assert org.transfer_officer is not None
    assert org.meta_research is not None
