"""
Multidimensional Intelligence Layer
Orchestrates cross-domain scientific principles for trading and self-improvement.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import IntelligenceDomain, Hypothesis, MultidimensionalExperiment, MultidimensionalModule
from .memory import MultidimensionalKnowledgeMemory
from .hypothesis_engine import HypothesisEngine

logger = logging.getLogger(__name__)


class MultidimensionalIntelligenceLayer:
    """
    Multidimensional Intelligence Layer
    Integrates Biology, Physics, Chemistry, Mathematics, and Nature modules.
    """

    def __init__(self, config: Optional[Dict] = None, improvement_registry: Any = None):
        self.config = config or {}
        self.modules: Dict[IntelligenceDomain, MultidimensionalModule] = {}

        self.storage_path = Path(self.config.get('storage_path', 'multidimensional_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.memory = MultidimensionalKnowledgeMemory(self.storage_path)
        self.hypothesis_engine = HypothesisEngine(config)
        self.experiments: List[MultidimensionalExperiment] = []
        self.improvement_registry = improvement_registry

        logger.info("Multidimensional Intelligence Layer initialized")

    async def initialize(self):
        """Initialize all modules and load state."""
        logger.info("Initializing Multidimensional Intelligence Layer modules...")
        self.memory.load()

    def register_module(self, module: MultidimensionalModule):
        """Register a new domain module."""
        self.modules[module.domain] = module
        logger.info(f"Registered multidimensional module: {module.domain.value}")

    async def process_market_context(self, market_context: Dict[str, Any]):
        """Process market context through all modules to generate hypotheses."""
        all_hypotheses = []
        for domain, module in self.modules.items():
            try:
                raw_hypotheses = await module.generate_hypotheses(market_context)
                for h in raw_hypotheses:
                    # Use HypothesisEngine to ensure proper ID and registration
                    registered_h = await self.hypothesis_engine.pose_hypothesis(
                        domain=h.domain,
                        concept=h.concept,
                        mathematical_representation=h.mathematical_representation,
                        description=h.description,
                        expected_outcome=h.expected_outcome,
                        priority=h.priority
                    )
                    all_hypotheses.append(registered_h)
            except Exception as e:
                logger.error(f"Error generating hypotheses in {domain.value}: {e}")

        return all_hypotheses

    async def run_improvement_cycle(self, market_context: Dict[str, Any]):
        """Run the full Scientific Self-Improvement Loop."""
        logger.info("Starting Multidimensional Improvement Cycle")

        # 1. Observe & Generate Hypotheses
        new_hypotheses = await self.process_market_context(market_context)

        # 2. Select and Create Experiments
        for hypothesis in new_hypotheses:
            if hypothesis.priority > 0.7:
                experiment = await self._create_experiment(hypothesis)
                await self._run_experiment(experiment)

        # 3. Evaluate and Persist
        await self._evaluate_experiments()
        await self._persist_state()

    async def _create_experiment(self, hypothesis: Hypothesis) -> MultidimensionalExperiment:
        experiment = MultidimensionalExperiment(
            experiment_id=f"mexp_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            parameters={'hypothesis': hypothesis.concept},
            started_at=datetime.now(),
            status="running"
        )
        self.experiments.append(experiment)
        return experiment

    async def _run_experiment(self, experiment: MultidimensionalExperiment):
        """Placeholder for running the actual experiment (backtest/validation)."""
        logger.info(f"Running experiment {experiment.experiment_id} for hypothesis {experiment.hypothesis_id}")
        # In a real implementation, this would trigger a backtest or statistical validation
        await asyncio.sleep(0.1)
        experiment.status = "completed"
        experiment.completed_at = datetime.now()
        # Mock results for initialization
        experiment.results = {"success": True, "significance": 0.85}
        experiment.performance_metrics = {"sharpe_improvement": 0.05}

    async def _evaluate_experiments(self):
        """Evaluate completed experiments and update knowledge graph."""
        all_hypotheses = self.hypothesis_engine.get_all_hypotheses()
        for experiment in self.experiments:
            if experiment.status == "completed":
                hypothesis = next((h for h in all_hypotheses if h.hypothesis_id == experiment.hypothesis_id), None)
                if hypothesis and hypothesis.status == "pending":
                    sharpe_imp = experiment.performance_metrics.get("sharpe_improvement", 0)
                    if sharpe_imp > 0.02:
                        self.hypothesis_engine.update_hypothesis_status(hypothesis.hypothesis_id, "validated")
                        await self._add_to_knowledge_graph(hypothesis, experiment)

                        # Bridge to Unified Improvement Registry
                        if self.improvement_registry:
                            from ..improvement.registry import ImprovementType
                            self.improvement_registry.register_proposal(
                                type=ImprovementType.TRADING,
                                domain=hypothesis.domain.value,
                                source="MultidimensionalResearchAgent",
                                proposal={
                                    "hypothesis_id": hypothesis.hypothesis_id,
                                    "concept": hypothesis.concept,
                                    "math_rep": hypothesis.mathematical_representation,
                                    "experiment_id": experiment.experiment_id,
                                    "sharpe_improvement": sharpe_imp
                                }
                            )
                    else:
                        self.hypothesis_engine.update_hypothesis_status(hypothesis.hypothesis_id, "rejected")

    async def _add_to_knowledge_graph(self, hypothesis: Hypothesis, experiment: MultidimensionalExperiment):
        """Update the knowledge graph with validated findings."""
        self.memory.add_insight(
            domain=hypothesis.domain.value,
            concept=hypothesis.concept,
            math_rep=hypothesis.mathematical_representation,
            application=f"Trading strategy derived from {hypothesis.concept}",
            result=experiment.results or {},
            performance=experiment.performance_metrics
        )
        logger.info(f"Added validated insight to Knowledge Graph: {hypothesis.concept}")

    async def _persist_state(self):
        """Persist state to storage."""
        self.memory.save()

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_modules": [d.value for d in self.modules.keys()],
            "total_hypotheses": len(self.hypothesis_engine.get_all_hypotheses()),
            "validated_insights": len(self.memory.knowledge_graph),
            "experiments_run": len(self.experiments)
        }
