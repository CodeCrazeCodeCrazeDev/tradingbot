"""
Research Operating System (Research OS) for Ultra-High-Ceiling Quantitative Lifecycles.
Manages research intake, experiment tracking, reproducibility guarantees,
peer review governance, knowledge archiving, and production feedback loops.
"""

import logging
import uuid
import hashlib
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger("AlphaAlgo.ResearchOS")


# ===========================================================================
# 1. Research Intake & Prioritization (Idea Registry)
# ===========================================================================

@dataclass
class QuantitativeIdea:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    research_question: str = ""
    target_asset_class: str = ""
    expected_sharpe: float = 0.0
    implementation_cost_days: float = 0.0
    data_feasibility_score: float = 0.0  # 1.0 to 10.0
    priority_score: float = 0.0
    status: str = "Intake"  # Intake, Prioritized, Active_Experiment, Archived


class IdeaRegistry:
    """Manages quantitative idea intake and statistical prioritization scoring."""

    def __init__(self) -> None:
        self.ideas: Dict[str, QuantitativeIdea] = {}

    def record_idea(self, title: str, question: str, target_asset_class: str,
                    expected_sharpe: float, cost_days: float, feasibility: float) -> QuantitativeIdea:
        """Structured intake of a new quantitative idea."""
        # Prioritization formula: Sharpe * Feasibility / Cost
        priority = (expected_sharpe * feasibility) / max(cost_days, 1.0)

        idea = QuantitativeIdea(
            title=title,
            research_question=question,
            target_asset_class=target_asset_class,
            expected_sharpe=expected_sharpe,
            implementation_cost_days=cost_days,
            data_feasibility_score=feasibility,
            priority_score=float(priority),
            status="Prioritized" if priority > 1.5 else "Intake"
        )
        self.ideas[idea.id] = idea
        logger.info(f"Recorded Idea: {title} (Priority: {idea.priority_score:.2f})")
        return idea


# ===========================================================================
# 2. Experiment Registry & Reproducibility Assurer
# ===========================================================================

@dataclass
class QuantExperiment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idea_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    dataset_name: str = ""
    dataset_hash: str = ""
    code_version: str = "v1.0.0"
    random_seed: int = 42
    parameters: Dict[str, Any] = field(default_factory=dict)
    outcome_metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "Registered"  # Registered, Running, Completed, Failed


class ExperimentRegistry:
    """Rigorous registry tracking every quantitative experiment to guarantee exact reproducibility."""

    def __init__(self) -> None:
        self.experiments: Dict[str, QuantExperiment] = {}

    def register_experiment(self, idea_id: str, dataset_name: str, dataset_df: pd.DataFrame,
                            parameters: Dict[str, Any], seed: int = 42) -> QuantExperiment:
        """Registers a new experiment, hashing the input dataset to lock reproducibility."""
        # Calculate SHA-256 hash of dataset to guarantee lineage
        df_json = json.dumps(dataset_df.to_dict(orient="split"), default=str)
        dataset_hash = hashlib.sha256(df_json.encode("utf-8")).hexdigest()

        exp = QuantExperiment(
            idea_id=idea_id,
            dataset_name=dataset_name,
            dataset_hash=dataset_hash,
            parameters=parameters,
            random_seed=seed
        )
        self.experiments[exp.id] = exp
        logger.info(f"Registered Experiment: {exp.id} (Dataset Hash: {dataset_hash[:12]})")
        return exp


class ReproducibilityAssurer:
    """Enforces mathematical reproducibility of pseudo-random models across research runs."""

    @staticmethod
    def seed_random_state(seed: int) -> None:
        """Locks standard random number generators to ensure identical paths."""
        np.random.seed(seed)
        import random
        random.seed(seed)
        logger.info(f"Locked global random seeds to: {seed}")

    @staticmethod
    def verify_lineage(exp: QuantExperiment, current_df: pd.DataFrame) -> bool:
        """Verifies if the current dataset is mathematically identical to the original experiment's."""
        df_json = json.dumps(current_df.to_dict(orient="split"), default=str)
        current_hash = hashlib.sha256(df_json.encode("utf-8")).hexdigest()
        return current_hash == exp.dataset_hash


# ===========================================================================
# 3. Peer Review & Model Governance (Review Board)
# ===========================================================================

@dataclass
class ReviewVerdict:
    approver_id: str
    checklist_passed: bool
    challenges_documented: List[str]
    verdict: str  # APPROVED, CONDITIONAL_REVISION, REJECTED
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PeerReviewBoard:
    """
    Simulates institutional model governance and peer review before production promotion.
    Challenges overfitting, data mining bias, look-ahead bias, and transaction modeling.
    """
    def __init__(self) -> None:
        self.review_history: Dict[str, List[ReviewVerdict]] = {}

    def submit_for_peer_review(self, experiment_id: str, metrics: Dict[str, float]) -> ReviewVerdict:
        """Runs the checklist challenging implementation and statistical outcomes."""
        challenges = []
        checklist_passed = True

        # 1. Challenge Sharpe Overfitting
        if metrics.get("sharpe_ratio", 0.0) > 4.5:
            challenges.append("WARNING: Observed Sharpe is > 4.5. High probability of look-ahead leak or cost modeling omissions.")
            checklist_passed = False

        # 2. Challenge Backtest Duration
        if metrics.get("num_bars", 0) < 100:
            challenges.append("WARNING: Sample size is too small (<100 bars) for statistical validation.")
            checklist_passed = False

        # 3. Check for Out-Of-Sample (OOS) degradation
        if metrics.get("oos_sharpe", 0.0) < metrics.get("is_sharpe", 0.0) * 0.40:
            challenges.append("WARNING: Out-Of-Sample Sharpe drops by more than 60% compared to In-Sample. Indicator of severe overfitting.")
            checklist_passed = False

        verdict_str = "APPROVED" if checklist_passed else "CONDITIONAL_REVISION"
        if len(challenges) >= 3:
            verdict_str = "REJECTED"

        verdict = ReviewVerdict(
            approver_id="Independent_Risk_Committee_V5",
            checklist_passed=checklist_passed,
            challenges_documented=challenges,
            verdict=verdict_str
        )

        if experiment_id not in self.review_history:
            self.review_history[experiment_id] = []
        self.review_history[experiment_id].append(verdict)

        logger.info(f"Peer Review Verdict for {experiment_id}: {verdict_str} (Passed checklist: {checklist_passed})")
        return verdict


# ===========================================================================
# 4. Knowledge Management (Failed Ideas Archive)
# ===========================================================================

@dataclass
class FailedIdeaRecord:
    idea_id: str
    title: str
    rejection_reason: str
    archived_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeArchive:
    """Indexes failed ideas, research paths, and rejections to prevent duplicate effort."""

    def __init__(self) -> None:
        self.archive: Dict[str, FailedIdeaRecord] = {}

    def archive_failed_idea(self, idea_id: str, title: str, reason: str) -> FailedIdeaRecord:
        record = FailedIdeaRecord(
            idea_id=idea_id,
            title=title,
            rejection_reason=reason
        )
        self.archive[idea_id] = record
        logger.warning(f"Knowledge Archive: Logged failed idea '{title}' -> Reason: {reason}")
        return record

    def search_archive(self, title_query: str) -> Optional[FailedIdeaRecord]:
        """Scans archived failures to determine if this path has been explored before."""
        for record in self.archive.values():
            if title_query.lower() in record.title.lower():
                return record
        return None


# ===========================================================================
# 5. Production-to-Research Feedback Loop
# ===========================================================================

@dataclass
class ProductionAnomalyAlert:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy_id: str = ""
    anomaly_type: str = ""  # DRAWDOWN_BREACH, SLIPPAGE_DEGRADATION, VOLATILITY_SPIKE
    observed_value: float = 0.0
    limit_value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ProductionFeedbackLoop:
    """Logs production performance anomalies and translates them back into new prioritized research questions."""

    def __init__(self, idea_registry: IdeaRegistry) -> None:
        self.idea_registry = idea_registry
        self.alerts: List[ProductionAnomalyAlert] = []

    def trigger_anomaly_alert(self, strategy_id: str, anomaly_type: str, observed: float, limit: float) -> QuantitativeIdea:
        """Detects live degradation and automatically spawns a remedial research project."""
        alert = ProductionAnomalyAlert(
            strategy_id=strategy_id,
            anomaly_type=anomaly_type,
            observed_value=observed,
            limit_value=limit
        )
        self.alerts.append(alert)

        # Spawn structured intake idea
        title = f"Post-Mortem: {strategy_id} {anomaly_type}"
        question = f"How can we evolve strategy {strategy_id} to protect against {anomaly_type} (Observed: {observed}, Limit: {limit})?"

        new_idea = self.idea_registry.record_idea(
            title=title,
            question=question,
            target_asset_class="FX/Equities",
            expected_sharpe=1.8,  # Restoration target
            cost_days=5.0,        # Standard rapid response budget
            feasibility=8.0       # High feasibility since data is already live
        )

        logger.info(f"Production Feedback Loop: Automatically created prioritized research idea {new_idea.id} for post-mortem.")
        return new_idea
