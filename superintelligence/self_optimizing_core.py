"""Self-optimizing engine for strategy and infrastructure evolution."""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OptimizationExperiment:
    """Represents one continuous-improvement experiment."""

    name: str
    hypothesis: str
    target_metric: str
    candidate_config: Dict[str, Any]
    observed_gain: float = 0.0
    status: str = "planned"


@dataclass
class InfrastructurePlan:
    """Compute and agent-allocation plan produced from opportunities."""

    total_compute_budget: float
    domain_allocation: Dict[str, float] = field(default_factory=dict)
    agent_deployments: List[Dict[str, Any]] = field(default_factory=list)


class SelfOptimizingCore:
    """Optimizes methods, structures, and compute/resource allocation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.current_architecture = {
            "execution_graph": ["signal", "risk", "execution"],
            "meta_controller": "adaptive_bandit",
        }
        self.performance_history: List[Dict[str, Any]] = []
        self.active_experiments: List[OptimizationExperiment] = []
        logger.info("%s initialized", self.__class__.__name__)

    def initialize(self) -> bool:
        self.initialized = True
        return True

    def process(self, data: Any) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()
        payload = data if isinstance(data, dict) else {"input": data}
        return {
            "architecture": self.current_architecture,
            "optimization_actions": self.optimize_system(payload),
        }

    def optimize_system(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Run a full optimization cycle over methods + architecture."""
        baseline = float(telemetry.get("baseline_metric", 0.0))
        candidate = float(telemetry.get("candidate_metric", baseline))
        gain = candidate - baseline

        experiment = OptimizationExperiment(
            name=telemetry.get("experiment_name", "adaptive-tuning"),
            hypothesis=telemetry.get(
                "hypothesis", "A tighter feedback loop increases risk-adjusted returns"
            ),
            target_metric=telemetry.get("target_metric", "sharpe"),
            candidate_config=copy.deepcopy(telemetry.get("candidate_config", {})),
            observed_gain=gain,
            status="accepted" if gain > 0 else "rejected",
        )
        self.active_experiments.append(experiment)

        architecture_changed = False
        if gain > 0:
            self.current_architecture = self._evolve_architecture(experiment)
            architecture_changed = True

        self.performance_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "baseline": baseline,
                "candidate": candidate,
                "gain": gain,
            }
        )

        return {
            "experiment": experiment,
            "architecture_changed": architecture_changed,
        }

    def allocate_infrastructure(
        self, opportunities: List[Dict[str, Any]], total_compute_budget: float
    ) -> InfrastructurePlan:
        """Allocate compute globally based on opportunity intensity."""
        if total_compute_budget <= 0:
            return InfrastructurePlan(total_compute_budget=0.0)

        weighted = []
        for item in opportunities:
            score = max(float(item.get("score", 0.0)), 0.0)
            domain = item.get("domain", "unknown")
            weighted.append((domain, score))

        total_score = sum(score for _, score in weighted)
        if total_score == 0:
            equal = total_compute_budget / max(len(weighted), 1)
            domain_allocation = {d: equal for d, _ in weighted} if weighted else {}
        else:
            domain_allocation = {
                d: total_compute_budget * (score / total_score) for d, score in weighted
            }

        deploys = [
            {
                "agent_name": f"research-{domain}-agent",
                "domain": domain,
                "compute": round(budget, 4),
            }
            for domain, budget in domain_allocation.items()
            if budget > 0
        ]

        return InfrastructurePlan(
            total_compute_budget=total_compute_budget,
            domain_allocation=domain_allocation,
            agent_deployments=deploys,
        )

    def _evolve_architecture(self, experiment: OptimizationExperiment) -> Dict[str, Any]:
        evolved = copy.deepcopy(self.current_architecture)
        evolved["meta_controller"] = "hierarchical-self-play"
        evolved["last_promoted_experiment"] = experiment.name
        return evolved

    def get_status(self) -> Dict[str, Any]:
        return {
            "initialized": self.initialized,
            "timestamp": datetime.now().isoformat(),
            "architecture": self.current_architecture,
            "active_experiments": len(self.active_experiments),
        }


def create_self_optimizing_core(config: Optional[Dict[str, Any]] = None) -> SelfOptimizingCore:
    return SelfOptimizingCore(config)
