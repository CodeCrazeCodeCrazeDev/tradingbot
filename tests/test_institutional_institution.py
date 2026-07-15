"""
Unit tests validating Autonomous Quantitative Research Institution (AQRI) capabilities.
Verifies Bayesian claims updates, multi-board governance reviews, platform events propagation,
and thematic campaign resource allocation inside AQRI.
"""

import pytest
import numpy as np
import pandas as pd

from trading_bot.research.discovery_platform import (
    AutonomousQuantitativeResearchInstitution,
    KnowledgeClaim,
    ResearchCampaign,
    Policy,
    InstitutionalCapitalAccount,
    PlatformEvent,
    ScientificReviewBoard,
    EconomicReviewBoard,
    RiskReviewBoard,
    OperationalReviewBoard
)


def test_knowledge_claim_bayesian_updating():
    """Verifies that KnowledgeClaims undergo robust Bayesian updates on incoming evidence."""
    claim = KnowledgeClaim(
        statement="Order flow imbalance predicts short-term spread dynamics.",
        prior_probability=0.40,
        posterior_probability=0.40
    )

    assert claim.status == "Unverified"

    # 1. Apply strong supportive evidence (p_value=0.01)
    claim.apply_evidence_bayes(p_value=0.01, supports=True)
    assert claim.posterior_probability > 0.40
    assert claim.supporting_evidence_count == 1

    # 2. Apply contradicting evidence (posterior probability decreases)
    post_before = claim.posterior_probability
    claim.apply_evidence_bayes(p_value=0.03, supports=False)
    assert claim.posterior_probability < post_before
    assert claim.contradicting_evidence_count == 1

    # 3. Apply multiple supportive trials to promote status to "Supported"
    for _ in range(5):
        claim.apply_evidence_bayes(p_value=0.005, supports=True)

    assert claim.posterior_probability > 0.80
    assert claim.status == "Supported"


def test_review_board_governance_protocols():
    """Verifies strict institutional limits across scientific, economic, risk, and operational boards."""
    s_board = ScientificReviewBoard()
    e_board = EconomicReviewBoard()
    r_board = RiskReviewBoard()
    o_board = OperationalReviewBoard()

    # 1. Scientific: p-value < 0.05
    claim = KnowledgeClaim(statement="Anomalies are persistent")
    assert s_board.approve_claim(claim, p_value=0.012) is True
    assert s_board.approve_claim(claim, p_value=0.089) is False

    # 2. Economic: Expected Sharpe >= 2.0
    assert e_board.approve_edge(expected_sharpe=2.45) is True
    assert e_board.approve_edge(expected_sharpe=1.45) is False

    # 3. Risk: Max active leverage <= 3.0x
    assert r_board.approve_portfolio(current_leverage=1.5) is True
    assert r_board.approve_portfolio(current_leverage=4.2) is False

    # 4. Operational: Latency round-trip <= 20ms
    assert o_board.approve_latency(round_trip_ms=12.5) is True
    assert o_board.approve_latency(round_trip_ms=35.0) is False


def test_platform_events_propagation():
    """Verifies that platform events trigger and propagate properly to handlers."""
    aqri = AutonomousQuantitativeResearchInstitution()

    events_logged = []
    def dummy_handler(event: PlatformEvent) -> None:
        events_logged.append(event)

    aqri.event_bus.register_handler(dummy_handler)

    # Trigger event
    aqri.event_bus.publish_event(
        event_type="STATE_PROMOTED",
        payload={"object_id": "obj-1", "to_state": "SHADOW"}
    )

    assert len(events_logged) == 1
    assert events_logged[0].event_type == "STATE_PROMOTED"
    assert events_logged[0].payload["to_state"] == "SHADOW"


def test_aqri_orchestrator_complete_lifecycle():
    """Verifies that AQRI orchestrator initializes campaigns, registers claims, and update capitals."""
    aqri = AutonomousQuantitativeResearchInstitution()
    assert aqri is not None
    assert aqri.capital.get_total_capital_score() > 0.0

    # 1. Start Campaign
    campaign = aqri.start_thematic_campaign("Order Book Dynamics")
    assert campaign.theme_name == "Order Book Dynamics"
    assert campaign.id in aqri.campaigns

    # 2. Register Knowledge Claim under active campaign
    claim = aqri.register_knowledge_claim(
        campaign_id=campaign.id,
        statement="OBI correlates positively with forward 15m returns."
    )
    assert claim.id in aqri.claims

    # Check graph edge relation was established
    relations = aqri.qdp.graph.find_relations(claim.id, "part_of_campaign")
    assert campaign.id in relations

    # 3. Submit evidence for scientific judgment -> APPROVED
    # Should update Bayesian posterior, trigger event, and increase Scientific Capital Account
    initial_sci_cap = aqri.capital.scientific_capital

    approved, updated_claim = aqri.submit_evidence_for_judgment(
        claim_id=claim.id,
        p_value=0.012,
        supports=True
    )

    assert approved is True
    assert updated_claim.posterior_probability > 0.50
    assert aqri.capital.scientific_capital == initial_sci_cap + 150.0
