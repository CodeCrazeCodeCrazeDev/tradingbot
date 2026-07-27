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

from .quant_pipeline import Hypothesis

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


# ===========================================================================
# ADVANCED RESEARCH OS ENGINES (High Ceiling Operational Infrastructure)
# ===========================================================================


@dataclass
class DatasetVersionNode:
    version_id: str
    source_name: str
    lineage_parent_ids: List[str]
    transformation_applied: str
    hash_value: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DataLineageRegistry:
    """
    Enforces strict Data Governance and Lineage tracking.
    Guarantees every feature and backtest is traceable to its raw, uncleaned base source.
    """
    def __init__(self) -> None:
        self.lineage_graph: Dict[str, DatasetVersionNode] = {}

    def register_version(self, source_name: str, parent_ids: List[str],
                         transformation: str, df: pd.DataFrame) -> DatasetVersionNode:
        """Saves a new dataset node in the lineage graph with strict SHA-256 validation."""
        df_json = json.dumps(df.to_dict(orient="split"), default=str)
        hash_val = hashlib.sha256(df_json.encode("utf-8")).hexdigest()

        node = DatasetVersionNode(
            version_id=str(uuid.uuid4()),
            source_name=source_name,
            lineage_parent_ids=parent_ids,
            transformation_applied=transformation,
            hash_value=hash_val
        )
        self.lineage_graph[node.version_id] = node
        logger.info(f"Data Lineage Registered: {source_name} -> {node.version_id[:12]} (Hash: {hash_val[:12]})")
        return node


class CausalityAndStructuralBreakTester:
    """
    Verifies that alphas are causally linked to price returns, rather than simple correlation.
    Includes Granger Causality proxy tests and structural break tests (Chow test proxy).
    """
    def __init__(self) -> None:
        pass

    def test_granger_causality_score(self, cause: pd.Series, effect: pd.Series, max_lag: int = 3) -> float:
        """
        Computes a F-statistic proxy for Granger Causality.
        Tests whether the lagged values of 'cause' provide statistically significant
        incremental predictive power over lagged 'effect' returns.
        """
        aligned = pd.concat([cause, effect], axis=1).dropna()
        if len(aligned) < (max_lag * 2 + 5):
            return 0.0

        # Standard regression model: effect_t = c + b1 * effect_t-1 + b2 * cause_t-1
        eff_curr = aligned.iloc[1:, 1].values
        eff_lag = aligned.iloc[:-1, 1].values
        cause_lag = aligned.iloc[:-1, 0].values

        # Fit model with both lagged variables
        X_full = np.column_stack([np.ones_like(eff_lag), eff_lag, cause_lag])
        y = eff_curr
        beta_full = np.linalg.lstsq(X_full, y, rcond=None)[0]
        residuals_full = y - X_full.dot(beta_full)
        rss_full = np.sum(residuals_full**2)

        # Fit restricted model with only lagged effect
        X_rest = np.column_stack([np.ones_like(eff_lag), eff_lag])
        beta_rest = np.linalg.lstsq(X_rest, y, rcond=None)[0]
        residuals_rest = y - X_rest.dot(beta_rest)
        rss_rest = np.sum(residuals_rest**2)

        # Calculate Granger F-statistic proxy
        if rss_full == 0:
            return 0.0
        n_obs = len(y)
        f_stat = ((rss_rest - rss_full) / 1.0) / (rss_full / (n_obs - 3.0))
        return float(f_stat if f_stat > 0 else 0.0)

    def detect_structural_break_chow(self, series: pd.Series, split_idx: int) -> float:
        """
        Computes a Chow Test proxy statistic to detect structural regime breaks in data.
        Returns F-stat score; high values suggest a transition in the underlying pricing process.
        """
        if len(series) < 10 or split_idx < 5 or split_idx > (len(series) - 5):
            return 0.0

        y = series.values
        X = np.column_stack([np.ones_like(y), np.arange(len(y))])

        # 1. Total Residual Sum of Squares (RSS_pooled)
        beta_pooled = np.linalg.lstsq(X, y, rcond=None)[0]
        rss_pooled = np.sum((y - X.dot(beta_pooled))**2)

        # 2. Split RSS
        y1, X1 = y[:split_idx], X[:split_idx]
        beta1 = np.linalg.lstsq(X1, y1, rcond=None)[0]
        rss1 = np.sum((y1 - X1.dot(beta1))**2)

        y2, X2 = y[split_idx:], X[split_idx:]
        beta2 = np.linalg.lstsq(X2, y2, rcond=None)[0]
        rss2 = np.sum((y2 - X2.dot(beta2))**2)

        # Chow F-stat formula
        rss_combined = rss1 + rss2
        if rss_combined == 0:
            return 0.0

        k = 2  # number of parameters (intercept + slope)
        n = len(y)
        chow_f = ((rss_pooled - rss_combined) / k) / (rss_combined / (n - 2 * k))
        return float(chow_f if chow_f > 0 else 0.0)


class ExplainabilityAndAttributionEngine:
    """
    Provides explainability (SHAP-like) decomposition for black-box machine learning alphas.
    Breaks down signal predictions into discrete feature attribution weights.
    """
    def __init__(self) -> None:
        pass

    def compute_feature_attributions(self, feature_values: Dict[str, float],
                                    model_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calculates feature attributions (SHAP Proxy value) on a specific model prediction.
        Attribution = FeatureValue * ModelWeight, normalized to sum to the prediction.
        """
        attributions = {}
        total_p = sum(val * model_weights.get(name, 0.0) for name, val in feature_values.items())

        for name, val in feature_values.items():
            weight = model_weights.get(name, 0.0)
            attributions[name] = float(val * weight)

        attributions["total_prediction_raw"] = float(total_p)
        return attributions


class UncertaintyEstimator:
    """
    Models mathematical uncertainty bounds [P_lower, P_upper] for predictions.
    Prevents overconfident execution and sizing during ambiguous/OOD regimes.
    """
    def __init__(self, confidence_interval: float = 0.95) -> None:
        self.confidence_interval = confidence_interval

    def estimate_credal_bounds(self, predictions_trials: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculates Credal Bounds based on prediction dispersion.
        Returns (mean_prediction, lower_bound, upper_bound).
        """
        if len(predictions_trials) == 0:
            return 0.0, 0.0, 0.0

        mean_p = float(np.mean(predictions_trials))
        std_p = float(np.std(predictions_trials))

        # Z-value proxy
        z = 1.96 if self.confidence_interval == 0.95 else 2.58
        margin = z * (std_p / np.sqrt(max(len(predictions_trials), 1)))

        return mean_p, float(mean_p - margin), float(mean_p + margin)


class StrategyEvolutionEngine:
    """
    Genetic Algorithm Engine for Strategy Evolution (Phase 66).
    Mutates, recombines, and evolves active alpha signals to survive new regimes.
    """
    def __init__(self, mutation_rate: float = 0.15) -> None:
        self.mutation_rate = mutation_rate

    def crossover_alphas(self, alpha_a: np.ndarray, alpha_b: np.ndarray) -> np.ndarray:
        """Performs uniform crossover genetic recombination of two parent alphas."""
        size = min(len(alpha_a), len(alpha_b))
        child = np.zeros(size)

        for i in range(size):
            # 50/50 parent genetic mix
            child[i] = alpha_a[i] if np.random.rand() > 0.5 else alpha_b[i]

        return child

    def mutate_alpha(self, alpha_signal: np.ndarray) -> np.ndarray:
        """Applies Gaussian noise alpha mutation based on active mutation rates."""
        mutated = alpha_signal.copy()
        for i in range(len(mutated)):
            if np.random.rand() < self.mutation_rate:
                mutated[i] += np.random.normal(0, 0.05)
        return mutated


# ===========================================================================
# QUANTITATIVE RESEARCH PLATFORM (QRP) ENTITIES & WORKSPACE ORCHESTRATOR
# ===========================================================================


@dataclass
class ResearchProject:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    objective: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "Active"  # Active, Completed, Suspended


@dataclass
class ResearchQuestion:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    question_text: str = ""
    economic_foundation: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FeatureSet:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    feature_names: List[str] = field(default_factory=list)
    dataset_version_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ValidationReport:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    deflated_sharpe: float = 0.0
    p_value: float = 0.0
    is_statistically_significant: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Deployment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    mode: str = "shadow"  # shadow, paper, small_live, scaled_production
    risk_limit_pips: float = 0.0
    max_capital_usd: float = 0.0
    deployed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceReport:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deployment_id: str = ""
    total_return_usd: float = 0.0
    live_drawdown_pct: float = 0.0
    realized_sharpe: float = 0.0
    slippage_drag_pips: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str = ""  # hypothesis, experiment, deployment
    source_id: str = ""
    lessons_learned: str = ""
    recommendation: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ResearchWorkspace:
    """
    Unified central orchestrator for the Quantitative Research Platform (QRP).
    Serves as the primary workspace API connecting researchers, the Hypothesis Lab,
    the Experiment Manager, the Knowledge Base, and the underlying Research OS.
    """
    def __init__(self, target_sharpe: float = 2.0, max_drawdown: float = 8.0) -> None:
        self.target_sharpe = target_sharpe
        self.max_drawdown = max_drawdown

        # Operational Backbones
        self.ideas = IdeaRegistry()
        self.experiments = ExperimentRegistry()
        self.lineage = DataLineageRegistry()
        self.causality = CausalityAndStructuralBreakTester()
        self.explainability = ExplainabilityAndAttributionEngine()
        self.uncertainty = UncertaintyEstimator()
        self.evolution = StrategyEvolutionEngine()
        self.peer_review = PeerReviewBoard()
        self.knowledge = KnowledgeArchive()
        self.feedback = ProductionFeedbackLoop(self.ideas)

        # Platform Repositories
        self.projects: Dict[str, ResearchProject] = {}
        self.questions: Dict[str, ResearchQuestion] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.feature_sets: Dict[str, FeatureSet] = {}
        self.validation_reports: Dict[str, ValidationReport] = {}
        self.deployments: Dict[str, Deployment] = {}
        self.performance_reports: Dict[str, PerformanceReport] = {}
        self.knowledge_entries: Dict[str, KnowledgeEntry] = {}

    def create_project(self, title: str, objective: str) -> ResearchProject:
        """Starts a new quantitative research project on the platform."""
        project = ResearchProject(title=title, objective=objective)
        self.projects[project.id] = project
        logger.info(f"QRP: Created Research Project '{title}' (ID: {project.id})")
        return project

    def formulate_question(self, project_id: str, question: str, foundation: str) -> ResearchQuestion:
        """Formulates a granular, economically grounded research question under a project."""
        q = ResearchQuestion(project_id=project_id, question_text=question, economic_foundation=foundation)
        self.questions[q.id] = q
        logger.info(f"QRP: Formulated Research Question under project {project_id[:12]} -> {question}")
        return q

    def record_hypothesis(self, question_id: str, name: str, description: str,
                          rationale: str, counterparty: str, falsifications: List[str]) -> Hypothesis:
        """Proposes and stores a formalized hypothesis under a research question."""
        hyp = Hypothesis(
            name=name,
            description=description,
            economic_rationale=rationale,
            counterparty_profile=counterparty,
            falsification_conditions=falsifications
        )
        self.hypotheses[hyp.id] = hyp
        logger.info(f"QRP: Hypothesis Formed: '{name}' (ID: {hyp.id})")
        return hyp

    def create_feature_set(self, name: str, features: List[str], dataset_version_id: str) -> FeatureSet:
        """Registers a candidate feature set trace linked to a clean dataset version."""
        f_set = FeatureSet(name=name, feature_names=features, dataset_version_id=dataset_version_id)
        self.feature_sets[f_set.id] = f_set
        logger.info(f"QRP: Feature Set registered: '{name}' containing {len(features)} features.")
        return f_set

    def log_validation_report(self, experiment_id: str, deflated_sharpe: float, p_value: float) -> ValidationReport:
        """Records mathematical statistical validation for an experiment."""
        is_sig = p_value < 0.05 and deflated_sharpe >= self.target_sharpe
        report = ValidationReport(
            experiment_id=experiment_id,
            deflated_sharpe=deflated_sharpe,
            p_value=p_value,
            is_statistically_significant=is_sig
        )
        self.validation_reports[report.id] = report
        logger.info(f"QRP: Validation Report Logged for {experiment_id[:12]} -> Deflated Sharpe: {deflated_sharpe:.2f}, Significance: {is_sig}")
        return report

    def execute_promotion_gate(self, validation_report_id: str) -> Tuple[bool, Optional[Deployment]]:
        """
        Promotion Gate: Promotes an experiment to simulated shadow trading
        only if it is statistically significant and has passed peer review.
        """
        report = self.validation_reports.get(validation_report_id)
        if not report:
            return False, None

        # Verify statistical significance
        if not report.is_statistically_significant:
            logger.warning(f"Promotion Denied: Report {validation_report_id[:12]} is not statistically significant.")
            return False, None

        # Verify Peer Review history
        reviews = self.peer_review.review_history.get(report.experiment_id, [])
        if not reviews or not any(r.verdict == "APPROVED" for r in reviews):
            logger.warning(f"Promotion Denied: Experiment {report.experiment_id[:12]} has not passed peer review.")
            return False, None

        # Create Deployment node
        deployment = Deployment(
            experiment_id=report.experiment_id,
            mode="shadow",
            risk_limit_pips=15.0,
            max_capital_usd=50000.0
        )
        self.deployments[deployment.id] = deployment
        logger.info(f"PROMOTION SUCCESSFUL: Experiment {report.experiment_id[:12]} promoted to SHADOW TRADING.")
        return True, deployment

    def record_knowledge_entry(self, source_type: str, source_id: str,
                               lessons: str, recommendation: str) -> KnowledgeEntry:
        """Appends a searchable knowledge entry to the platform's long-term Knowledge Base."""
        entry = KnowledgeEntry(
            source_type=source_type,
            source_id=source_id,
            lessons_learned=lessons,
            recommendation=recommendation
        )
        self.knowledge_entries[entry.id] = entry
        logger.info(f"QRP Knowledge Base: Logged entry from {source_type} {source_id[:12]}.")
        return entry
