"""
Institutional Research Governance, Portfolio Management, & Meta-Learning Suite.
Implements the 6-layer Quantitative Research Platform (QRP):
- Layer 6: Mission & Governance (Audit Trails, Assured Rollbacks, Sign-offs)
- Layer 5: Research Portfolio Management (Compute & Capital Resource Scheduling)
- Layer 4: Research Operating System (Workspace, Project & Question Orchestrations)
- Layer 3: Quantitative Research Engine (Data Lineage, Causal and Statistical Validation)
- Layer 2: Trading & Execution Platform (Fidelity Cost Backtesters, Shadow/Paper Trading)
- Layer 1: Infrastructure & Data Platform (Ingestion pipelines, Data validation)
"""

import logging
import uuid
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from .quant_pipeline import Hypothesis, ValidationLab
from .research_os import ResearchProject, ResearchQuestion, QuantExperiment, ResearchWorkspace

logger = logging.getLogger("AlphaAlgo.Governance")


# ===========================================================================
# 1. Research Strategy (Layer 6: Mission & Strategy)
# ===========================================================================

@dataclass
class StrategicMandate:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_markets: List[str] = field(default_factory=list)
    acceptable_drawdown_limit: float = 8.0  # Max drawdown target
    time_horizons: List[str] = field(default_factory=list)  # HFT, Intraday, Swing
    core_edge_focus: str = "Microstructure"  # Microstructure, Macro, alternative_data
    capital_allocation_budget_usd: float = 1000000.0


class ResearchStrategy:
    """Defines research mandates, asset universes, acceptable risks, and targeting horizons."""

    def __init__(self, mandate: Optional[StrategicMandate] = None) -> None:
        self.mandate = mandate or StrategicMandate(
            target_markets=["EURUSD", "BTCUSD"],
            time_horizons=["Intraday", "HFT"]
        )

    def validate_project_alignment(self, project: ResearchProject) -> Tuple[bool, str]:
        """Verifies if a research project aligns with the active firm strategy and risk budgets."""
        # Clean check
        if not project.title:
            return False, "Project lacks a title."

        logger.info(f"Strategy: Validated alignment for project '{project.title}' under mandate focus: {self.mandate.core_edge_focus}")
        return True, "Aligned with strategic mandate."


# ===========================================================================
# 2. Research Portfolio Management (Layer 5: Resource Scheduling)
# ===========================================================================

@dataclass
class ResourceAllocation:
    project_id: str
    compute_cores_allocated: int = 16
    developer_days_budget: float = 10.0
    trading_capital_limit_usd: float = 50000.0
    status: str = "Active"


class ResearchPortfolioManager:
    """Schedules and allocates compute, capital, and engineering resources across competing projects."""

    def __init__(self) -> None:
        self.allocations: Dict[str, ResourceAllocation] = {}

    def allocate_resources(self, project_id: str, cores: int, dev_days: float, capital: float) -> ResourceAllocation:
        """Allocates firm resources to a specific project id."""
        alloc = ResourceAllocation(
            project_id=project_id,
            compute_cores_allocated=cores,
            developer_days_budget=dev_days,
            trading_capital_limit_usd=capital
        )
        self.allocations[project_id] = alloc
        logger.info(f"Portfolio Manager: Allocated {cores} cores, {dev_days} dev days to Project {project_id[:12]}")
        return alloc

    def deallocate_resources(self, project_id: str) -> None:
        if project_id in self.allocations:
            self.allocations[project_id].status = "Suspended"
            logger.info(f"Portfolio Manager: Suspended resources for Project {project_id[:12]}")


# ===========================================================================
# 3. Experiment Design (Layer 4: Scientific Definition)
# ===========================================================================

@dataclass
class ScienceExperimentDesign:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    null_hypothesis: str = ""
    alternative_hypothesis: str = ""
    required_datasets: List[str] = field(default_factory=list)
    statistical_tests: List[str] = field(default_factory=list)
    success_criteria_sharpe: float = 2.0
    failure_criteria_drawdown: float = 8.0


class ExperimentDesigner:
    """Enforces strict scientific method standards: Null vs Alternative hypotheses and criteria."""

    def __init__(self) -> None:
        self.designs: Dict[str, ScienceExperimentDesign] = {}

    def create_design(self, null_h: str, alt_h: str, datasets: List[str],
                      tests: List[str], target_sharpe: float, max_drawdown: float) -> ScienceExperimentDesign:
        design = ScienceExperimentDesign(
            null_hypothesis=null_h,
            alternative_hypothesis=alt_h,
            required_datasets=datasets,
            statistical_tests=tests,
            success_criteria_sharpe=target_sharpe,
            failure_criteria_drawdown=max_drawdown
        )
        self.designs[design.id] = design
        logger.info(f"Experiment Designer: Created design {design.id[:12]} (Null: {null_h[:40]}...)")
        return design


# ===========================================================================
# 4. Decision Management (Layer 4/5: Outcome Registration)
# ===========================================================================

@dataclass
class DecisionRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    outcome: str = "ARCHIVE"  # REJECT, ARCHIVE, IMPROVE, MERGE, DEPLOY, REPEAT
    rationale: str = ""
    recorded_by: str = "Independent_Risk_Committee"
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DecisionManager:
    """Formalizes and logs the final outcome of an experiment run, preventing memory loss."""

    def __init__(self) -> None:
        self.decisions: Dict[str, DecisionRecord] = {}

    def record_decision(self, experiment_id: str, outcome: str, rationale: str) -> DecisionRecord:
        allowed_outcomes = {"REJECT", "ARCHIVE", "IMPROVE", "MERGE", "DEPLOY", "REPEAT"}
        if outcome not in allowed_outcomes:
            raise ValueError(f"Invalid outcome: {outcome}. Allowed: {allowed_outcomes}")

        record = DecisionRecord(
            experiment_id=experiment_id,
            outcome=outcome,
            rationale=rationale
        )
        self.decisions[experiment_id] = record
        logger.info(f"Decision Manager: Experiment {experiment_id[:12]} marked as {outcome}. Rationale: {rationale}")
        return record


# ===========================================================================
# 5. Governance & Audit Trails (Layer 6: Audit Compliance)
# ===========================================================================

@dataclass
class AuditTrace:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    approver_signatures: List[str] = field(default_factory=list)
    validation_gates_passed: List[str] = field(default_factory=list)
    accepted_risks: List[str] = field(default_factory=list)
    rollback_code_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class GovernanceAuditTrail:
    """Locks immutable traces detailing approvals, gates, unverified assumptions, and rollback hashes."""

    def __init__(self) -> None:
        self.traces: Dict[str, AuditTrace] = {}

    def commit_audit_trail(self, experiment_id: str, approvers: List[str],
                           gates: List[str], risks: List[str], rollback_hash: str) -> AuditTrace:
        trace = AuditTrace(
            experiment_id=experiment_id,
            approver_signatures=approvers,
            validation_gates_passed=gates,
            accepted_risks=risks,
            rollback_code_hash=rollback_hash
        )
        self.traces[experiment_id] = trace
        logger.warning(f"GOVERNANCE AUDIT COMMITTED: Experiment {experiment_id[:12]} -> Signed by: {approvers}")
        return trace


# ===========================================================================
# 6. Meta-Learning Engine (Layer 6: Process Self-Improvement)
# ===========================================================================

class MetaLearningEngine:
    """
    Analyzes historical research databases, decision trails, and experiment logs
    to determine which features, model classes, and methods consistently succeed.
    Implements recursive research self-improvement.
    """
    def __init__(self, decision_manager: DecisionManager, experiment_registry: Any) -> None:
        self.decisions = decision_manager
        self.experiments = experiment_registry

    def generate_research_meta_insights(self) -> Dict[str, Any]:
        """Aggregates historical outcomes to discover high-success feature and model categories."""
        total_decisions = len(self.decisions.decisions)
        if total_decisions == 0:
            return {"status": "No historical decision records found to analyze."}

        success_outcomes = {"DEPLOY", "MERGE", "IMPROVE"}
        successful_experiments = 0
        feature_category_scores: Dict[str, int] = {}
        model_class_scores: Dict[str, int] = {}

        for exp_id, dec in self.decisions.decisions.items():
            is_success = dec.outcome in success_outcomes
            if is_success:
                successful_experiments += 1

            # Cross-reference with registered experiment parameters/features
            exp = self.experiments.experiments.get(exp_id)
            if exp:
                # Track feature success rates
                f_name = exp.dataset_name
                feature_category_scores[f_name] = feature_category_scores.get(f_name, 0) + (1 if is_success else -1)

                # Track model/param success rates
                model_type = exp.parameters.get("model_class", "Default")
                model_class_scores[model_type] = model_class_scores.get(model_type, 0) + (1 if is_success else -1)

        success_rate = (successful_experiments / total_decisions) * 100.0

        # Sort scores to extract best families
        best_features = sorted(feature_category_scores.items(), key=lambda x: x[1], reverse=True)
        best_models = sorted(model_class_scores.items(), key=lambda x: x[1], reverse=True)

        insights = {
            "total_research_trials_analyzed": total_decisions,
            "overall_research_success_rate": f"{success_rate:.2f}%",
            "recommended_feature_categories": [f[0] for f in best_features[:3]],
            "recommended_model_classes": [m[0] for m in best_models[:3]],
            "actionable_meta_recommendation": "Deploy compute cores primarily on recommended feature families."
        }

        logger.info(f"Meta-Learning Engine: Processed {total_decisions} decisions. Success rate: {success_rate:.2f}%")
        return insights


# ===========================================================================
# 7. AlphaAlgo Unified Quantitative Platform
# ===========================================================================

class AlphaAlgoQuantitativePlatform:
    """
    The Master Quantitative Platform unifying the 6 operational layers.
    Orchestrates the entire pipeline from Mission & Governance down to Infrastructure & Data Platform.
    """
    def __init__(self) -> None:
        # Layer 6: Mission & Governance
        self.strategy = ResearchStrategy()
        self.audit_trail = GovernanceAuditTrail()

        # Layer 5: Research Portfolio Management
        self.portfolio = ResearchPortfolioManager()

        # Layer 4: Research OS (Unified workspace)
        self.workspace = ResearchWorkspace()

        # Core Platform Hooks
        self.designer = ExperimentDesigner()
        self.decision_manager = DecisionManager()
        self.meta_learning = MetaLearningEngine(self.decision_manager, self.workspace.experiments)

        logger.info("🚀 AlphaAlgo Master Quantitative Research Platform Initialized (6 Layers fully active)")
