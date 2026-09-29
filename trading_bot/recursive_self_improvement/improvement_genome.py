"""Versioned improvement genomes for human-governed AlphaAlgo RSI."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping
from uuid import uuid4


class ImprovementDomain(str, Enum):
    WORLD_MODEL = "world_model"
    ALPHA_STRATEGY_DISCOVERY = "alpha_strategy_discovery"
    TRADING_POLICY = "trading_policy"
    RISK_INTELLIGENCE = "risk_intelligence"
    MARKET_ANALYSIS = "market_analysis"
    SENTIMENT_INTELLIGENCE = "sentiment_intelligence"
    RESEARCH_INTELLIGENCE = "research_intelligence"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    EXPERIMENT_DESIGN = "experiment_design"
    EVALUATION_INTELLIGENCE = "evaluation_intelligence"
    AGENT_INTELLIGENCE = "agent_intelligence"
    PLANNING = "planning"
    MEMORY = "memory"
    FEATURE_ENGINEERING = "feature_engineering"
    MODEL_ARCHITECTURE = "model_architecture"
    MODEL_SELECTION_ROUTING = "model_selection_routing"
    UNCERTAINTY_ESTIMATION = "uncertainty_estimation"
    EXECUTION_INTELLIGENCE = "execution_intelligence"
    PORTFOLIO_INTELLIGENCE = "portfolio_intelligence"
    DATA_INTELLIGENCE = "data_intelligence"
    SIMULATION_ENVIRONMENT = "simulation_environment"
    BACKTESTING_VALIDATION = "backtesting_validation"
    STRATEGY_LIFECYCLE = "strategy_lifecycle"
    FAILURE_DIAGNOSIS = "failure_diagnosis"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    GOVERNANCE = "governance"
    SELF_DEBUGGING = "self_debugging"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    TOOL_SELECTION = "tool_selection"
    KNOWLEDGE_GRAPH = "knowledge_graph_institutional_knowledge"
    RESEARCH_ENGINEERING_TRANSFER = "research_engineering_transfer"
    RESEARCH_PRIORITIZATION = "research_prioritization"
    META_LEARNING = "meta_learning"
    ARCHITECTURE = "architecture"
    REASONING = "reasoning"


@dataclass(frozen=True)
class ImprovementGenome:
    """A bounded, auditable candidate; never executable code by itself."""

    domain: ImprovementDomain
    objective: str
    change_set: Mapping[str, Any]
    evaluation_plan: Mapping[str, Any]
    safety_constraints: Mapping[str, Any]
    parent_id: str = "baseline"
    genome_id: str = field(default_factory=lambda: f"GEN-{uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    mutation_index: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "parent_id": self.parent_id,
            "domain": self.domain.value,
            "objective": self.objective,
            "change_set": dict(self.change_set),
            "evaluation_plan": dict(self.evaluation_plan),
            "safety_constraints": dict(self.safety_constraints),
            "created_at": self.created_at.isoformat(),
            "mutation_index": self.mutation_index,
            "metadata": dict(self.metadata),
        }

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EvaluationEvidence:
    genome_id: str
    baseline_metrics: Mapping[str, float]
    candidate_metrics: Mapping[str, float]
    oos_metrics: Mapping[str, float]
    robustness_metrics: Mapping[str, float]
    safety_passed: bool
    deterministic_replay_passed: bool
    data_provenance: Mapping[str, Any]
    violations: List[str] = field(default_factory=list)
    evaluator_version: str = "alphaalgo-evaluator-v1"

    @property
    def candidate_gain(self) -> float:
        baseline = float(self.baseline_metrics.get("score", 0.0))
        candidate = float(self.candidate_metrics.get("score", 0.0))
        return candidate - baseline

    @property
    def oos_gain(self) -> float:
        baseline = float(self.baseline_metrics.get("oos_score", self.baseline_metrics.get("score", 0.0)))
        candidate = float(self.oos_metrics.get("score", 0.0))
        return candidate - baseline

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "baseline_metrics": dict(self.baseline_metrics),
            "candidate_metrics": dict(self.candidate_metrics),
            "oos_metrics": dict(self.oos_metrics),
            "robustness_metrics": dict(self.robustness_metrics),
            "safety_passed": self.safety_passed,
            "deterministic_replay_passed": self.deterministic_replay_passed,
            "data_provenance": dict(self.data_provenance),
            "violations": list(self.violations),
            "evaluator_version": self.evaluator_version,
        }


@dataclass(frozen=True)
class PromotionDecision:
    genome_id: str
    status: str
    reason: str
    requires_human_approval: bool = True
    human_approved_by: str = ""
    rollback_snapshot_id: str = ""
    evidence: Mapping[str, Any] = field(default_factory=dict)

    @property
    def approved(self) -> bool:
        return self.status == "approved"
