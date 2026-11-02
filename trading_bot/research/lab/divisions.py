"""
Institutional Research Lab - Org Chart of Divisions.

Canonical mapping between the SovereignResearchOrchestrator pipeline stages and the
named divisions of the institutional research lab. The kernel emits stage events;
this module is the single source of truth for which division owns each stage.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ResearchDivision:
    """A named division of the institutional research lab."""
    key: str
    name: str
    mandate: str
    stages: List[str] = field(default_factory=list)
    subsystems: List[str] = field(default_factory=list)


# Ordered stage -> division attribution for the 14-stage quantitative lifecycle
# plus the literature ingestion sub-pipeline.
STAGE_TO_DIVISION: Dict[str, str] = {
    # Literature & Discovery Desk
    "literature_discovery": "literature_desk",
    "literature_intake": "literature_desk",
    "duplicate_check": "literature_desk",
    "graph_persistence": "literature_desk",
    # Hypothesis & Ideation Lab
    "hypothesis_generation": "hypothesis_lab",
    "proposal_prioritization": "hypothesis_lab",
    # Data Operations Desk
    "data_ingestion": "data_operations",
    "data_validation": "data_operations",
    "active_learning": "data_operations",
    # Feature Laboratory
    "feature_engineering": "feature_lab",
    "feature_selection": "feature_lab",
    "causal_discovery": "feature_lab",
    # Statistical Review Office
    "statistical_validation": "statistics_office",
    # Alpha & Strategy Lab
    "alpha_generation": "alpha_lab",
    "strategy_synthesis": "alpha_lab",
    "experiment_registration": "alpha_lab",
    # Validation & Replication Desk
    "world_modeling": "validation_desk",
    "backtesting": "validation_desk",
    "robustness_testing": "validation_desk",
    "digital_twin_stress": "validation_desk",
    # Portfolio & Capital Allocation Office
    "portfolio_optimization": "portfolio_office",
    # Peer Review Board
    "peer_review": "peer_review_board",
    # Governance & Promotion Office
    "promotion_governance": "governance_office",
    "decision_audit": "governance_office",
    "strategy_registration": "governance_office",
    # Knowledge Archive
    "meta_research": "knowledge_archive",
    "knowledge_archival": "knowledge_archive",
}


def build_org_chart() -> List[ResearchDivision]:
    """Return the canonical institutional lab org chart, in pipeline order."""
    return [
        ResearchDivision(
            key="literature_desk",
            name="Literature & Discovery Desk",
            mandate="Discover, ingest, deduplicate and embed-map scientific literature "
                    "into the Cognitive Research Graph.",
            stages=["literature_discovery", "literature_intake", "duplicate_check", "graph_persistence"],
            subsystems=["literature_provider", "embedding_provider", "duplicate_detector"],
        ),
        ResearchDivision(
            key="hypothesis_lab",
            name="Hypothesis & Ideation Lab",
            mandate="Convert literature claims into falsifiable hypotheses and prioritize "
                    "proposals by Bayesian Expected Value of Information.",
            stages=["hypothesis_generation", "proposal_prioritization"],
            subsystems=["hypothesis_generator", "prioritization_policy", "experiment_scheduler"],
        ),
        ResearchDivision(
            key="data_operations",
            name="Data Operations Desk",
            mandate="Ingest, validate and version market datasets; scan regime gaps "
                    "for active-learning acquisition.",
            stages=["data_ingestion", "data_validation", "active_learning"],
            subsystems=["data_provider", "dataset_validator", "dataset_registry", "active_learner"],
        ),
        ResearchDivision(
            key="feature_lab",
            name="Feature Laboratory",
            mandate="Engineer candidate features, score predictive value, prune redundancy "
                    "and build causal structure.",
            stages=["feature_engineering", "feature_selection", "causal_discovery"],
            subsystems=["feature_engine", "feature_registry", "causal_engine"],
        ),
        ResearchDivision(
            key="statistics_office",
            name="Statistical Review Office",
            mandate="Gate hypotheses on stationarity, causality and multiple-testing rigor "
                    "before any capital-relevant conclusion.",
            stages=["statistical_validation"],
            subsystems=["statistics_tests"],
        ),
        ResearchDivision(
            key="alpha_lab",
            name="Alpha & Strategy Lab",
            mandate="Synthesize alpha signals from validated features, assemble executable "
                    "strategies and register reproducible experiments.",
            stages=["alpha_generation", "strategy_synthesis", "experiment_registration"],
            subsystems=["alpha_generator", "strategy_synthesizer", "experiment_registry", "model_registry"],
        ),
        ResearchDivision(
            key="validation_desk",
            name="Validation & Replication Desk",
            mandate="Independently re-test every candidate: realistic backtests, walk-forward "
                    "validation, regime stress and adversarial digital-twin scenarios.",
            stages=["world_modeling", "backtesting", "robustness_testing", "digital_twin_stress"],
            subsystems=["backtester", "robustness_tester", "world_model", "digital_twin"],
        ),
        ResearchDivision(
            key="portfolio_office",
            name="Portfolio & Capital Allocation Office",
            mandate="Assess marginal portfolio contribution and hierarchical risk-parity "
                    "allocation for promoted candidates.",
            stages=["portfolio_optimization"],
            subsystems=["portfolio_optimizer"],
        ),
        ResearchDivision(
            key="peer_review_board",
            name="Peer Review Board",
            mandate="Convene the multi-agent reviewer marketplace; derive a "
                    "confidence-weighted scientific consensus and objections.",
            stages=["peer_review"],
            subsystems=["debate_engine"],
        ),
        ResearchDivision(
            key="governance_office",
            name="Governance & Promotion Office",
            mandate="Enforce promotion gates, sign decision audit records and control "
                    "the only path from research artifact to deployable strategy.",
            stages=["promotion_governance", "decision_audit", "strategy_registration"],
            subsystems=["gatekeeper", "decision_auditor", "strategy_registry"],
        ),
        ResearchDivision(
            key="knowledge_archive",
            name="Knowledge Archive & Meta-Research",
            mandate="Archive proceedings and post-mortems into the institutional "
                    "knowledge base; calibrate reviewers from realized outcomes.",
            stages=["meta_research", "knowledge_archival"],
            subsystems=["knowledge_registry", "meta_research_engine", "graph_store", "monitor"],
        ),
    ]


def division_for_stage(stage: str) -> str:
    """Return the division key owning a pipeline stage ('unassigned' if unknown)."""
    return STAGE_TO_DIVISION.get(stage, "unassigned")
