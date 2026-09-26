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
from typing import Dict, Any, List, Optional, Tuple, Set
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
