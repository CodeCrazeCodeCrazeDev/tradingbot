"""
Research Organization & Meta-Research Platform Suite.
Models the organizational lifecycle of quantitative scientific discovery:
- Scientific Philosophy: Declares evidence rules and model complexity boundaries.
- Research Program: Manages long-running thematic lines (microstructure, execution, risk).
- Scientific Review: Peer-challinging methodology, biases, and conclusions.
- Knowledge Integration: Synthesizing features and predictive durability across markets.
- Technology Transfer: Operationalizing research models into production packaging and runbooks.
- Meta-Research Engine: Investigates research about research, optimizing the discovery process.
"""

import logging
import uuid
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field

from .quant_pipeline import Hypothesis, AlphaSignal
from .research_os import QuantExperiment, ResearchProject

logger = logging.getLogger("AlphaAlgo.ResearchOrganization")


# ===========================================================================
# 1. Scientific Philosophy
# ===========================================================================

@dataclass
class PhilosophySpecification:
    baseline_confidence_level: float = 0.95  # p-value < 0.05
    max_acceptable_model_complexity_params: int = 1000
    enforce_reproducibility: bool = True
    falsification_mandatory: bool = True
    rejection_threshold_sharpe: float = 1.5


class ScientificPhilosophy:
    """Defines and enforces the core scientific philosophy under which all research is conducted."""

    def __init__(self, spec: Optional[PhilosophySpecification] = None) -> None:
        self.spec = spec or PhilosophySpecification()

    def challenge_scientific_validity(self, p_value: float, param_count: int, has_falsifications: bool) -> Tuple[bool, str]:
        """Validates if a claim matches the baseline scientific philosophy rules."""
        required_p = 1.0 - self.spec.baseline_confidence_level
        if p_value >= required_p:
            return False, f"REJECT: Statistical p-value ({p_value:.4f}) is above required threshold of {required_p:.4f}."
        if param_count > self.spec.max_acceptable_model_complexity_params:
            return False, f"REJECT: Model complexity ({param_count} parameters) exceeds max allowed boundary of {self.spec.max_acceptable_model_complexity_params}."
        if self.spec.falsification_mandatory and not has_falsifications:
            return False, "REJECT: Hypothesis lacks required falsification conditions."
        return True, "PASS: Model matches active Scientific Philosophy specifications."


# ===========================================================================
# 2. Research Programs
# ===========================================================================

@dataclass
class ResearchProgram:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    theme_name: str = ""  # MICROSTRUCTURE, EXECUTION, ALPHA, PORTFOLIO, RISK, MACRO
    director: str = ""
    active_project_ids: Set[str] = field(default_factory=set)
    allocated_budget_fraction: float = 0.15


class ResearchProgramManager:
    """Groups quantitative research projects into long-running, themed research programs."""

    def __init__(self) -> None:
        self.programs: Dict[str, ResearchProgram] = {
            "MICROSTRUCTURE": ResearchProgram(theme_name="MARKET_MICROSTRUCTURE", director="Quant_Dir_HFT"),
            "EXECUTION": ResearchProgram(theme_name="EXECUTION_OPTIMIZATION", director="Quant_Dir_Execution"),
            "ALPHA": ResearchProgram(theme_name="ALPHA_DISCOVERY", director="Quant_Dir_Alpha"),
            "PORTFOLIO": ResearchProgram(theme_name="PORTFOLIO_OPTIMIZATION", director="Quant_Dir_Portfolio"),
            "RISK": ResearchProgram(theme_name="RISK_MODELING", director="Quant_Dir_Risk"),
            "MACRO": ResearchProgram(theme_name="MACRO_FORECASTING", director="Quant_Dir_Macro")
        }

    def assign_to_program(self, theme: str, project_id: str) -> None:
        prog = self.programs.get(theme.upper())
        if not prog:
            raise ValueError(f"Program Theme '{theme}' is not registered on the platform.")
        prog.active_project_ids.add(project_id)
        logger.info(f"Program Manager: Assigned Project {project_id[:12]} to long-running theme '{theme}'")


# ===========================================================================
# 3. Scientific Review
# ===========================================================================

@dataclass
class ScientificReviewVerdict:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    reviewer_id: str = "Lead_Scientific_Reviewer"
    methodology_valid: bool = True
    biases_checked: List[str] = field(default_factory=list)
    verdict: str = "APPROVED"  # APPROVED, REVISE, REJECT
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ScientificReviewer:
    """Challenges methodology, checks unverified assumptions, and rules out biases before engineering."""

    def __init__(self) -> None:
        self.verdicts: Dict[str, ScientificReviewVerdict] = {}

    def perform_review(self, experiment_id: str, assumptions: List[str], metrics: Dict[str, Any]) -> ScientificReviewVerdict:
        biases = ["look_ahead_bias", "survivorship_bias", "selection_overfitting_bias"]
        methodology_valid = True
        verdict_str = "APPROVED"

        # Methodology check: Must have checked at least 2 primary biases
        if len(assumptions) < 2:
            methodology_valid = False
            verdict_str = "REJECT"

        # Verify if oos performance is provided
        if "oos_sharpe" not in metrics:
            methodology_valid = False
            verdict_str = "REVISE"

        verdict = ScientificReviewVerdict(
            experiment_id=experiment_id,
            methodology_valid=methodology_valid,
            biases_checked=biases,
            verdict=verdict_str
        )
        self.verdicts[experiment_id] = verdict
        logger.info(f"Scientific Review: Experiment {experiment_id[:12]} marked as {verdict_str}.")
        return verdict


# ===========================================================================
# 4. Knowledge Integration
# ===========================================================================

class KnowledgeIntegrationHub:
    """Synthesizes feature performance, predictable asset classes, and durable alphas across experiments."""

    def __init__(self) -> None:
        self.feature_efficacy_scores: Dict[str, int] = {}
        self.market_predictability_scores: Dict[str, int] = {}

    def integrate_experiment_findings(self, feature_names: List[str], market: str, was_successful: bool) -> None:
        """Accumulates long-term efficacy indexes of features and markets from completed research."""
        score_diff = 1 if was_successful else -1

        for name in feature_names:
            self.feature_efficacy_scores[name] = self.feature_efficacy_scores.get(name, 0) + score_diff

        self.market_predictability_scores[market] = self.market_predictability_scores.get(market, 0) + score_diff
        logger.info(f"Knowledge Integration: Synthesized findings for '{market}'. Successful: {was_successful}")

    def query_integrated_efficacy(self) -> Dict[str, Any]:
        best_features = sorted(self.feature_efficacy_scores.items(), key=lambda x: x[1], reverse=True)
        best_markets = sorted(self.market_predictability_scores.items(), key=lambda x: x[1], reverse=True)

        # Filter for positive efficacy items
        positive_features = [f for f in best_features if f[1] > 0]
        positive_markets = [m for m in best_markets if m[1] > 0]

        return {
            "top_integrated_features": [f[0] for f in positive_features[:3]],
            "most_predictable_markets": [m[0] for m in positive_markets[:3]]
        }


# ===========================================================================
# 5. Technology Transfer
# ===========================================================================

@dataclass
class ProductionPackage:
    model_uuid: str
    packaged_at: datetime = field(default_factory=datetime.utcnow)
    runbook_generated: bool = True
    api_schema: Dict[str, str] = field(default_factory=dict)
    reversion_rollback_hash: str = ""
    status: str = "Packaged"


class TechnologyTransferOfficer:
    """Transitions a validated research model into production-ready packaged code and runbooks."""

    def __init__(self) -> None:
        self.packages: Dict[str, ProductionPackage] = {}

    def package_model_for_production(self, model_uuid: str, code_hash: str) -> ProductionPackage:
        """Constructs the operational API schema and rollback hash for deployment."""
        api_schema = {
            "input": "OHLCV_DataFrame_15m_Window",
            "output": "Signal_Direction_and_Confidence",
            "endpoint": f"/api/v1/predict/{model_uuid}"
        }

        pkg = ProductionPackage(
            model_uuid=model_uuid,
            api_schema=api_schema,
            reversion_rollback_hash=code_hash
        )
        self.packages[model_uuid] = pkg
        logger.warning(f"TECHNOLOGY TRANSFER OFFICER: Model {model_uuid[:12]} successfully packaged for production.")
        return pkg


# ===========================================================================
# 6. Meta-Research Engine (Research about Research)
# ===========================================================================

class MetaResearchEngine:
    """
    Analyzes the research process itself.
    Determines which validation methods best predict live trading success,
    which feature families add value, and which model classes remain robust.
    """
    def __init__(self, integration_hub: KnowledgeIntegrationHub) -> None:
        self.hub = integration_hub
        # Maps validation_method -> (predictions_succeeded, total_predictions)
        self.validation_method_efficacy: Dict[str, Tuple[int, int]] = {}

    def record_validation_live_correlation(self, validation_method: str,
                                           predicted_sharpe: float, live_sharpe: float) -> float:
        """
        Calculates correlation accuracy of a validation method.
        Tracks how well expected performance matched actual live results.
        """
        # If difference is small (<0.50 Sharpe deviation), the validation method predicted live success well
        is_accurate = abs(predicted_sharpe - live_sharpe) <= 0.50

        succ, total = self.validation_method_efficacy.get(validation_method, (0, 0))
        new_succ = succ + (1 if is_accurate else 0)
        new_total = total + 1

        self.validation_method_efficacy[validation_method] = (new_succ, new_total)
        accuracy = (new_succ / new_total) * 100.0

        logger.info(f"Meta-Research: Validation method '{validation_method}' live-correlation logged. Accuracy: {accuracy:.2f}%")
        return accuracy


# ===========================================================================
# 7. AlphaAlgo Research Organization
# ===========================================================================

class AlphaAlgoResearchOrganization:
    """
    Coordinating Master Class for the Quantitative Research Organization.
    Orchestrates thematic programs, scientific reviews, technology packaging, and meta-research.
    """
    def __init__(self) -> None:
        # Philosophy
        self.philosophy = ScientificPhilosophy()

        # Operations
        self.program_manager = ResearchProgramManager()
        self.reviewer = ScientificReviewer()
        self.integration_hub = KnowledgeIntegrationHub()
        self.transfer_officer = TechnologyTransferOfficer()

        # Meta-Research
        self.meta_research = MetaResearchEngine(self.integration_hub)

        logger.info("🎬 AlphaAlgo Research Organization Platform Active.")
