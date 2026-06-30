"""
RSIE Infrastructure and Adapters

Standardized interfaces and adapters for shared components:
- ExperimentManager (adapts ContinuousExperimentEngine)
- EvaluationPipeline (adapts EvaluationEngine and trading validation)
- ImprovementMemory (standardized persistence)
- GovernanceController (adapts GovernanceSystem)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

# Local imports with deferred loading for heavy components
from .recursive_core import ImprovementProposal, ImprovementDimension

logger = logging.getLogger(__name__)

class ExperimentManager:
    """Adapts ContinuousExperimentEngine for RSIE use"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._engine = None
        self._initialized = False

    async def _ensure_engine(self):
        if not self._initialized:
            try:
                from trading_bot.autonomous_superintelligence.experiment_engine import ContinuousExperimentEngine
                self._engine = ContinuousExperimentEngine(self.config)
                await self._engine.initialize()
                self._initialized = True
            except ImportError:
                logger.error("ContinuousExperimentEngine not found in autonomous_superintelligence")
                raise

    async def run_improvement_experiment(
        self,
        proposal: ImprovementProposal,
        test_data: Any
    ) -> Dict[str, Any]:
        """Run an experiment for a given improvement proposal"""
        await self._ensure_engine()

        # Map RSIE proposal to ExperimentEngine format
        from trading_bot.autonomous_superintelligence.experiment_engine import ExperimentType

        # Map dimension to experiment type
        exp_type_map = {
            ImprovementDimension.STRATEGY: ExperimentType.STRATEGY_TESTING,
            ImprovementDimension.ARCHITECTURE: ExperimentType.ARCHITECTURE_SEARCH,
            ImprovementDimension.FEATURE: ExperimentType.FEATURE_ENGINEERING,
            # Fallback
        }
        exp_type = exp_type_map.get(proposal.dimension, ExperimentType.MODEL_TRAINING)

        experiment = await self._engine.create_experiment(
            experiment_type=exp_type,
            name=f"RSIE_{proposal.proposal_id}",
            description=proposal.description,
            parameters={
                **proposal.proposed_changes,
                'rsie_metadata': proposal.metadata,
                'test_data_context': str(test_data)[:100] # Simplified
            }
        )

        results = await self._engine.run_experiment(experiment)
        return results

class EvaluationPipeline:
    """Adapts EvaluationEngine and provides unified validation gates"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._engine = None
        self._initialized = False

    async def _ensure_engine(self):
        if not self._initialized:
            try:
                from trading_bot.radar_ai.evaluation_engine import EvaluationEngine
                self._engine = EvaluationEngine()
                self._initialized = True
            except ImportError:
                logger.error("EvaluationEngine not found in radar_ai")
                raise

    async def evaluate_improvement(
        self,
        proposal: ImprovementProposal,
        experiment_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Unified evaluation of an improvement after experimentation"""
        await self._ensure_engine()

        # 1. Component Evaluation (Radar AI)
        # Radar AI expects returns, benchmark, portfolio, market_data
        # We need to extract these from experiment_results or context

        # Placeholder for extraction logic
        returns = experiment_results.get('metrics', {}).get('returns', [])
        if not returns and 'sharpe_ratio' in experiment_results.get('metrics', {}):
            # Synthesize or extract if returns not direct
            pass

        # 2. Hard Validation Gates (RSIE specific)
        validation_results = {
            'passed_all_gates': False,
            'gates': {
                'statistical_significance': False,
                'out_of_sample': False,
                'robustness': False,
                'risk_check': False,
                'regression_check': False
            },
            'radar_evaluation': {}
        }

        # Mocking gate logic for now - will be expanded in validation.py
        metrics = experiment_results.get('metrics', {})

        # Basic gates based on available metrics
        if 'sharpe_ratio' in metrics:
            validation_results['gates']['risk_check'] = metrics['sharpe_ratio'] > 1.0

        if 'p_value' in metrics:
            validation_results['gates']['statistical_significance'] = metrics['p_value'] < 0.05

        # ... logic for other gates ...

        validation_results['passed_all_gates'] = all(validation_results['gates'].values())

        return validation_results

class ImprovementMemory:
    """Standardized persistence for improvements"""

    def __init__(self, storage_path: str = "recursive_improvement_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.proposals_file = self.storage_path / "proposals.json"
        self.patterns_file = self.storage_path / "successful_patterns.json"

    async def store_proposal(self, proposal: ImprovementProposal):
        data = self._load_json(self.proposals_file)
        # Update or add
        # Convert proposal to dict
        prop_dict = self._proposal_to_dict(proposal)
        data[proposal.proposal_id] = prop_dict
        self._save_json(self.proposals_file, data)

    async def get_proposal(self, proposal_id: str) -> Optional[ImprovementProposal]:
        data = self._load_json(self.proposals_file)
        prop_dict = data.get(proposal_id)
        if prop_dict:
            # Reconstruct - omitted for brevity, would use constructor
            pass
        return None

    def _proposal_to_dict(self, proposal: ImprovementProposal) -> Dict[str, Any]:
        return {
            'proposal_id': proposal.proposal_id,
            'dimension': proposal.dimension.value,
            'level': proposal.level,
            'description': proposal.description,
            'status': proposal.status,
            'created_at': proposal.created_at.isoformat(),
            'proposed_changes': proposal.proposed_changes,
            'metrics': proposal.validation_results
        }

    def _load_json(self, path: Path) -> Dict:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def _save_json(self, path: Path, data: Dict):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

class GovernanceController:
    """Adapts GovernanceSystem for RSIE boundary enforcement"""

    def __init__(self):
        self._governance = None
        self._initialized = False

    async def _ensure_governance(self):
        if not self._initialized:
            try:
                from trading_bot.core_agent_system.governance_system import GovernanceSystem
                self._governance = GovernanceSystem()
                self._initialized = True
            except ImportError:
                logger.error("GovernanceSystem not found in core_agent_system")
                raise

    async def check_proposal(self, proposal: ImprovementProposal) -> Tuple[bool, List[str]]:
        """Verify proposal against governance policies"""
        await self._ensure_governance()

        # Levels 6-7 always require human approval (handled at orchestrator level)
        # This check is for automated safety boundaries

        action = {
            'type': 'improvement_deployment',
            'dimension': proposal.dimension.value,
            'level': proposal.level,
            'changes': proposal.proposed_changes
        }

        compliant, violations = await self._governance.check_compliance(
            agent_id="RSIE_Orchestrator",
            action=action,
            context={'risk_analysis': proposal.risk_analysis}
        )

        return compliant, violations
