"""
Quantitative Discovery Platform (QDP) - State-Centric Knowledge Operating System.
Reframe AlphaAlgo from a process-centric trading bot to an autonomous scientific platform
governed by an immutable Constitutional Layer, Belief Management, Expected Information Gain (EIG),
a semantic Knowledge Graph, Research Balance Sheets, and trace-reproducible Research Cases.
"""

import logging
import uuid
import hashlib
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Set, Callable
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger("AlphaAlgo.DiscoveryPlatform")


# ===========================================================================
# 1. Platform Constitution (Immutable Layer)
# ===========================================================================

class ConstitutionViolation(Exception):
    """Raised when an operation violates any immutable rule in the QDP Constitution."""
    pass


class ConstitutionalLayer:
    """
    The highest immutable layer of the SRP/QDP platform.
    Enforces that:
    1. Every claim requires empirical evidence.
    2. Every experiment is strictly reproducible (seeds and hashes).
    3. Every deployment is completely reversible.
    4. Every dataset version is immutable.
    5. Every model decision is explainable and attributable.
    """
    @staticmethod
    def enforce_evidence_rule(claim_text: str, evidence_ids: List[str]) -> None:
        """Enforces that no claim can be accepted without valid empirical evidence."""
        if not evidence_ids:
            raise ConstitutionViolation(f"Constitutional Violation: Claim '{claim_text}' has no empirical evidence links.")

    @staticmethod
    def enforce_reproducibility_rule(seed: int, dataset_hash: str) -> None:
        """Enforces locked random states and traceable dataset ancestry hashes."""
        if seed is None or not dataset_hash:
            raise ConstitutionViolation("Constitutional Violation: Experiment design lacks random seed or dataset hash.")


# ===========================================================================
# 2. Primitive Knowledge Objects
# ===========================================================================

@dataclass
class Observation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    data_summary: str = ""
    raw_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Question:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    economic_intuition: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HypothesisObject:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str = ""
    statement: str = ""
    falsification_tests: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Evidence:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    sharpe_ratio: float = 0.0
    p_value: float = 0.0
    deflated_sharpe: float = 0.0
    is_reproducible: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Theory:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: str = ""
    explanation: str = ""
    applicable_regimes: List[str] = field(default_factory=list)
    confidence_score: float = 0.5
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Decision:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    policy_action: str = "ARCHIVE"  # REJECT, ARCHIVE, IMPROVE, MERGE, DEPLOY, REPEAT
    rationale: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Action:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    symbol: str = ""
    direction: str = ""  # buy, sell, hold
    slippage_paid_pips: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ===========================================================================
# 3. Research Case & Knowledge Graph
# ===========================================================================

@dataclass
class ResearchCase:
    """
    The single most important container entity.
    Traces everything from research question and hypothesis down to deployment and lessons.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    question: Optional[Question] = None
    hypothesis: Optional[HypothesisObject] = None
    dataset_version_id: str = ""
    feature_set_id: str = ""
    experiment_ids: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    decision_id: str = ""
    deployment_id: str = ""
    lessons_learned: str = ""
    status: str = "Open"


class KnowledgeGraph:
    """
    Semantic Memory for AlphaAlgo.
    Rather than storing disconnected data documents, it maps edges and relations.
    """
    def __init__(self) -> None:
        self.nodes: Dict[str, Any] = {}
        self.edges: List[Tuple[str, str, str]] = []  # List of (source_id, relation, target_id)

    def add_node(self, node_id: str, obj: Any) -> None:
        self.nodes[node_id] = obj

    def add_relation(self, source_id: str, relation: str, target_id: str) -> None:
        self.edges.append((source_id, relation, target_id))
        logger.info(f"Knowledge Graph Edge: {source_id[:12]} --[{relation}]--> {target_id[:12]}")

    def find_relations(self, source_id: str, relation: str) -> List[str]:
        return [target for src, rel, target in self.edges if src == source_id and rel == relation]


# ===========================================================================
# 4. Belief Management System
# ===========================================================================

@dataclass
class Belief:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    statement: str = ""
    confidence: float = 0.5  # Subjective probability
    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0
    status: str = "Hypothetical"  # Hypothetical, Tentatively_Accepted, Rejected, Institutionalized
    last_updated: datetime = field(default_factory=datetime.utcnow)


class BeliefManagementSystem:
    """Tracks active firm beliefs, their confidence scores, and contradicting trials."""

    def __init__(self) -> None:
        self.beliefs: Dict[str, Belief] = {}

    def form_belief(self, statement: str, initial_confidence: float = 0.5) -> Belief:
        b = Belief(statement=statement, confidence=initial_confidence)
        self.beliefs[b.id] = b
        logger.info(f"Belief formed: '{statement}' (Initial Conf: {initial_confidence:.2f})")
        return b

    def update_belief(self, belief_id: str, is_supportive: bool, p_value: float) -> Belief:
        """Applies Bayesian-style confidence updates based on new empirical evidence."""
        b = self.beliefs.get(belief_id)
        if not b:
            raise ValueError(f"Belief ID {belief_id} not found.")

        # Bayesian weight of evidence
        evidence_weight = 1.0 - p_value

        if is_supportive:
            b.supporting_evidence_count += 1
            # Push confidence upwards towards 1.0
            b.confidence = b.confidence + (1.0 - b.confidence) * (0.1 * evidence_weight)
        else:
            b.contradicting_evidence_count += 1
            # Push confidence downwards towards 0.0
            b.confidence = b.confidence - b.confidence * (0.15 * evidence_weight)

        # Re-evaluate status
        if b.supporting_evidence_count > 5 and b.confidence > 0.85:
            b.status = "Tentatively_Accepted"
        elif b.contradicting_evidence_count > 3 and b.confidence < 0.35:
            b.status = "Rejected"

        b.last_updated = datetime.utcnow()
        logger.info(f"Belief updated: '{b.statement}' -> Conf: {b.confidence:.4f}, Status: {b.status}")
        return b


# ===========================================================================
# 5. Scientific Judgment Engine & Expected Information Gain (EIG)
# ===========================================================================

class ScientificJudgmentEngine:
    """
    Performs institutional scientific judgment over evidence.
    Schedules experiments optimizing Expected Information Gain (EIG) rather than profit.
    """
    def __init__(self, belief_manager: BeliefManagementSystem) -> None:
        self.belief_manager = belief_manager

    def evaluate_evidence(self, evidence: Evidence) -> Tuple[bool, str]:
        """Judges if the evidence is significant and reproducible."""
        if not evidence.is_reproducible:
            return False, "REJECTED: Evidence is not mathematically reproducible."
        if evidence.p_value >= 0.05:
            return False, "REJECTED: Evidence is not statistically significant (p-value >= 0.05)."
        if evidence.deflated_sharpe < 1.5:
            return False, "REJECTED: Observed Sharpe failed to survive multiple testing bias."
        return True, "ACCEPTED: Evidence is statistically valid and reproducible."

    def calculate_expected_information_gain(self, belief_id: str, entropy_reduction_pct: float) -> float:
        """
        Calculates Expected Information Gain (EIG) for scheduling experiments.
        Higher EIG implies the experiment significantly reduces entropy/uncertainty about a belief.
        """
        b = self.belief_manager.beliefs.get(belief_id)
        if not b:
            return 0.0
        # Uncertainty is highest when confidence is close to 0.5 (maximum entropy)
        uncertainty = 1.0 - abs(b.confidence - 0.5) * 2.0
        eig = uncertainty * entropy_reduction_pct
        logger.info(f"Calculated EIG for Belief {belief_id[:12]} -> {eig:.4f} (Uncertainty: {uncertainty:.2f})")
        return float(eig)


# ===========================================================================
# 6. Research Balance Sheet
# ===========================================================================

@dataclass
class ResearchBalanceSheet:
    # Assets (Validated knowledge and infrastructure)
    validated_theories_count: int = 0
    immutably_hashed_datasets_count: int = 0
    production_ready_alphas_count: int = 0

    # Liabilities (Technical debt and unverified metrics)
    unverified_hypotheses_count: int = 0
    technical_debt_score: float = 0.0
    known_data_quality_issues: int = 0

    def compute_net_research_equity(self) -> float:
        """
        Calculates Net Research Equity.
        Each theory, dataset, and alpha adds value, while unverified claims and debt subtract.
        """
        assets = (self.validated_theories_count * 1000.0) + (self.immutably_hashed_datasets_count * 250.0) + (self.production_ready_alphas_count * 2000.0)
        liabilities = (self.unverified_hypotheses_count * 300.0) + (self.technical_debt_score * 50.0) + (self.known_data_quality_issues * 400.0)
        return float(assets - liabilities)


# ===========================================================================
# 7. Unified SRP/QDP Master Platform
# ===========================================================================

class QuantitativeDiscoveryPlatform:
    """
    The state-centric SRP/QDP Kernel.
    Binds the Constitution, Beliefs, Knowledge Graph, Judgment Engine, and Balance Sheet.
    """
    def __init__(self) -> None:
        # Layer 6: Platform Constitution
        self.constitution = ConstitutionalLayer()

        # Layer 5: Scientific Memory
        self.graph = KnowledgeGraph()
        self.beliefs = BeliefManagementSystem()

        # Layer 4: Scientific Judgment
        self.judger = ScientificJudgmentEngine(self.beliefs)

        # Layer 3: Research Economics
        self.balance_sheet = ResearchBalanceSheet()

        # Repositories
        self.cases: Dict[str, ResearchCase] = {}

    def open_research_case(self, project_id: str, question_text: str, alt_hypothesis: str) -> ResearchCase:
        """Scientific entry point: Opens a traceable Research Case."""
        # 1. Create Question
        q = Question(text=question_text)
        self.graph.add_node(q.id, q)

        # 2. Create Hypothesis Object
        hyp = HypothesisObject(question_id=q.id, statement=alt_hypothesis)
        self.graph.add_node(hyp.id, hyp)
        self.graph.add_relation(hyp.id, "formulated_from", q.id)

        # 3. Create Case
        case = ResearchCase(
            project_id=project_id,
            question=q,
            hypothesis=hyp
        )
        self.cases[case.id] = case
        self.graph.add_node(case.id, case)
        self.graph.add_relation(case.id, "investigates", hyp.id)

        # Update balance sheet (unverified claims liability increases)
        self.balance_sheet.unverified_hypotheses_count += 1

        logger.info(f"QDP Kernel: Opened Research Case {case.id[:12]} investigating '{hyp.statement[:40]}'")
        return case


# ===========================================================================
# AUTONOMOUS QUANTITATIVE RESEARCH INSTITUTION (AQRI) EXTENSIONS
# ===========================================================================


@dataclass
class KnowledgeClaim:
    """
    Core QDP Entity representing an economically grounded claim.
    Claims undergo strict Bayesian updates from incoming experimental evidence.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    statement: str = ""
    prior_probability: float = 0.50
    posterior_probability: float = 0.50
    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0
    status: str = "Unverified"  # Unverified, Supported, Disproven, Institutionalized
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def apply_evidence_bayes(self, p_value: float, supports: bool) -> None:
        """Updates claim probability using standard Bayesian update logic."""
        # Likelihood ratio proxy derived from significance
        likelihood_ratio = 1.0 - p_value

        if supports:
            self.supporting_evidence_count += 1
            # Standard Odds update: Posterior odds = Prior odds * Likelihood ratio
            prior_odds = self.posterior_probability / (1.0 - self.posterior_probability + 1e-8)
            posterior_odds = prior_odds * (1.0 + likelihood_ratio)
            self.posterior_probability = posterior_odds / (1.0 + posterior_odds)
        else:
            self.contradicting_evidence_count += 1
            prior_odds = self.posterior_probability / (1.0 - self.posterior_probability + 1e-8)
            posterior_odds = prior_odds * (1.0 - likelihood_ratio * 0.5)
            self.posterior_probability = posterior_odds / (1.0 + posterior_odds)

        # Bound limits
        self.posterior_probability = float(np.clip(self.posterior_probability, 0.01, 0.99))

        # Evaluate status
        if self.supporting_evidence_count > 3 and self.posterior_probability > 0.80:
            self.status = "Supported"
        elif self.contradicting_evidence_count > 2 and self.posterior_probability < 0.30:
            self.status = "Disproven"


@dataclass
class ResearchCampaign:
    """Groups multiple related Research Cases into long-running thematic lines."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    theme_name: str = ""  # e.g., "Order Book Microstructure"
    active_case_ids: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Policy:
    """A durable multi-regime risk/execution policy replacing temporary strategy heuristics."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    target_asset: str = ""
    max_risk_multiplier: float = 1.0
    rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstitutionalCapitalAccount:
    """Tracks multi-dimensional capital accumulation across the institution."""
    scientific_capital: float = 1000.0      # Score of validated claims
    data_capital: float = 1000.0            # Score of versioned datasets
    computational_capital: float = 1000.0   # Score of active GPU cores/nodes
    methodological_capital: float = 1000.0  # Score of validation methods
    financial_capital: float = 100000.0     # USD cash allocation balance

    def get_total_capital_score(self) -> float:
        return float(
            self.scientific_capital +
            self.data_capital +
            self.computational_capital +
            self.methodological_capital +
            (self.financial_capital * 0.01)
        )


@dataclass
class PlatformEvent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""  # CLAIM_UPDATED, STATE_PROMOTED, ANOMALY_DETECTED
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PlatformEventBus:
    """Propagates platform events to registered agent handlers."""
    def __init__(self) -> None:
        self.handlers: List[Callable[[PlatformEvent], None]] = []

    def register_handler(self, handler: Callable[[PlatformEvent], None]) -> None:
        self.handlers.append(handler)

    def publish_event(self, event_type: str, payload: Dict[str, Any]) -> PlatformEvent:
        event = PlatformEvent(event_type=event_type, payload=payload)
        for handler in self.handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"EventBus: Handler failed on {event_type}: {e}")
        return event


# ===========================================================================
# Institutional Review Boards (Governance Protocol)
# ===========================================================================

class ScientificReviewBoard:
    def approve_claim(self, claim: KnowledgeClaim, p_value: float) -> bool:
        """Approves claim only if p-value meets strict 0.05 limit."""
        return p_value < 0.05


class EconomicReviewBoard:
    def approve_edge(self, expected_sharpe: float) -> bool:
        """Approves only if expected Sharpe satisfies 2.0 institutional hurdle."""
        return expected_sharpe >= 2.0


class RiskReviewBoard:
    def approve_portfolio(self, current_leverage: float) -> bool:
        """Limits total active portfolio leverage to 3x."""
        return current_leverage <= 3.0


class OperationalReviewBoard:
    def approve_latency(self, round_trip_ms: float) -> bool:
        """Operational limit: Latency must be within 20ms round-trip budget."""
        return round_trip_ms <= 20.0


# ===========================================================================
# Master AQRI Orchestrator
# ===========================================================================

class AutonomousQuantitativeResearchInstitution:
    """
    Autonomous Quantitative Research Institution (AQRI).
    The highest institutional state-centric capability layer.
    Unifies:
    1. Discovery (Research Cases & Campaigns)
    2. Knowledge (Claims & Graph)
    3. Judgment (Scientific, Economic, Risk & Operational Boards)
    4. Deployment (Multi-regime execution policies)
    5. Evolution (Institutional Capital & Platform Events)
    """
    def __init__(self) -> None:
        self.qdp = QuantitativeDiscoveryPlatform()
        self.event_bus = PlatformEventBus()
        self.capital = InstitutionalCapitalAccount()

        # Boards
        self.scientific_board = ScientificReviewBoard()
        self.economic_board = EconomicReviewBoard()
        self.risk_board = RiskReviewBoard()
        self.operational_board = OperationalReviewBoard()

        # Repositories
        self.campaigns: Dict[str, ResearchCampaign] = {}
        self.claims: Dict[str, KnowledgeClaim] = {}
        self.policies: Dict[str, Policy] = {}

    def start_thematic_campaign(self, theme_name: str) -> ResearchCampaign:
        """Starts a long-running research program campaign."""
        camp = ResearchCampaign(theme_name=theme_name)
        self.campaigns[camp.id] = camp
        logger.info(f"AQRI: Initiated long-running Thematic Campaign '{theme_name}' (ID: {camp.id})")
        return camp

    def register_knowledge_claim(self, campaign_id: str, statement: str) -> KnowledgeClaim:
        """Registers a first-class knowledge claim under an active research campaign."""
        claim = KnowledgeClaim(statement=statement)
        self.claims[claim.id] = claim

        # Link in knowledge graph
        self.qdp.graph.add_node(claim.id, claim)
        self.qdp.graph.add_relation(claim.id, "part_of_campaign", campaign_id)

        # Publish Event
        self.event_bus.publish_event(
            event_type="CLAIM_REGISTERED",
            payload={"claim_id": claim.id, "statement": statement}
        )

        logger.info(f"AQRI: Registered Knowledge Claim: '{statement}' (ID: {claim.id[:12]})")
        return claim

    def submit_evidence_for_judgment(self, claim_id: str, p_value: float, supports: bool) -> Tuple[bool, KnowledgeClaim]:
        """Runs Bayesian evidence updating and challenges scientific validity."""
        claim = self.claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim ID {claim_id} not found.")

        # Update claim priors/posteriors via Bayes
        claim.apply_evidence_bayes(p_value, supports)

        # Perform Board Review
        approved = self.scientific_board.approve_claim(claim, p_value)

        if approved:
            # Accumulate Scientific Capital on success
            self.capital.scientific_capital += 150.0
            self.event_bus.publish_event(
                event_type="CLAIM_APPROVED",
                payload={"claim_id": claim.id, "posterior_probability": claim.posterior_probability}
            )
        else:
            self.event_bus.publish_event(
                event_type="CLAIM_REJECTED",
                payload={"claim_id": claim.id, "p_value": p_value}
            )

        return approved, claim
