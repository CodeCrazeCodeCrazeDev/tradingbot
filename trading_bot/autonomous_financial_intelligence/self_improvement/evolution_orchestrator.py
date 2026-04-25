"""
Evolution Orchestrator

Coordinates continuous evolution and recursive self-improvement across all
infrastructure components. Manages the complete improvement lifecycle.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

from .experiment_registry import ExperimentRegistry, ExperimentType, ExperimentStatus
from .promotion_gates import PromotionGates
from .risk_governance import RiskGovernance, RiskLevel
from .compute_budget_controller import ComputeBudgetController, AllocationPriority, ResourceType
from .self_improvement_engine import SelfImprovementEngine, ImprovementType, ImprovementStatus

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    """Phases of evolution cycle."""
    ANALYSIS = "analysis"
    PROPOSAL = "proposal"
    EXPERIMENTATION = "experimentation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    LEARNING = "learning"


@dataclass
class EvolutionMetrics:
    """Metrics for evolution tracking."""
    total_improvements_proposed: int = 0
    total_improvements_deployed: int = 0
    total_experiments_run: int = 0
    successful_experiments: int = 0
    average_improvement_percentage: float = 0.0
    total_compute_used: float = 0.0
    total_risk_mitigated: float = 0.0
    hallucination_rate_reduction: float = 0.0
    verification_accuracy_gain: float = 0.0
    system_efficiency_gain: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_improvements_proposed': self.total_improvements_proposed,
            'total_improvements_deployed': self.total_improvements_deployed,
            'total_experiments_run': self.total_experiments_run,
            'successful_experiments': self.successful_experiments,
            'average_improvement_percentage': self.average_improvement_percentage,
            'total_compute_used': self.total_compute_used,
            'total_risk_mitigated': self.total_risk_mitigated,
            'hallucination_rate_reduction': self.hallucination_rate_reduction,
            'verification_accuracy_gain': self.verification_accuracy_gain,
            'system_efficiency_gain': self.system_efficiency_gain,
        }


@dataclass
class EvolutionCycle:
    """A complete cycle of evolution."""
    cycle_id: str
    started_at: datetime
    current_phase: EvolutionPhase
    completed_at: Optional[datetime] = None
    improvements_identified: List[str] = field(default_factory=list)
    experiments_launched: List[str] = field(default_factory=list)
    improvements_deployed: List[str] = field(default_factory=list)
    risks_identified: List[str] = field(default_factory=list)
    risks_mitigated: List[str] = field(default_factory=list)
    compute_allocated: float = 0.0
    cycle_metrics: Optional[EvolutionMetrics] = None
    lessons_learned: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_id': self.cycle_id,
            'started_at': self.started_at.isoformat(),
            'current_phase': self.current_phase.value,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'improvements_identified': self.improvements_identified,
            'experiments_launched': self.experiments_launched,
            'improvements_deployed': self.improvements_deployed,
            'risks_identified': self.risks_identified,
            'risks_mitigated': self.risks_mitigated,
            'compute_allocated': self.compute_allocated,
            'cycle_metrics': self.cycle_metrics.to_dict() if self.cycle_metrics else None,
            'lessons_learned': self.lessons_learned,
        }


class EvolutionOrchestrator:
    """
    Orchestrates continuous evolution and recursive self-improvement.
    
    Coordinates:
    - Experiment Registry
    - Promotion Gates
    - Risk Governance
    - Compute Budget Controller
    - Self-Improvement Engine
    
    Provides:
    - Automated improvement cycles
    - Resource-aware evolution
    - Risk-managed deployment
    - Continuous learning
    - Performance tracking
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'evolution_orchestrator_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._experiment_registry: Optional[ExperimentRegistry] = None
        self._promotion_gates: Optional[PromotionGates] = None
        self._risk_governance: Optional[RiskGovernance] = None
        self._compute_controller: Optional[ComputeBudgetController] = None
        self._improvement_engine: Optional[SelfImprovementEngine] = None
        
        self._cycles: Dict[str, EvolutionCycle] = {}
        self._current_cycle: Optional[EvolutionCycle] = None
        self._cumulative_metrics = EvolutionMetrics()
        
        self._evolution_config = {
            'cycle_interval_hours': 168,
            'auto_evolution_enabled': True,
            'max_concurrent_experiments': 5,
            'auto_deploy_threshold': 0.15,
            'learning_enabled': True,
        }
        
        self._is_running = False
        
        logger.info("Evolution Orchestrator created")
    
    async def initialize(self):
        """Initialize all evolution components."""
        logger.info("=" * 80)
        logger.info("INITIALIZING EVOLUTION ORCHESTRATOR")
        logger.info("=" * 80)
        
        base_config = {'storage_path': self.storage_path}
        
        self._experiment_registry = ExperimentRegistry({**base_config, 'storage_path': self.storage_path / 'experiments'})
        logger.info("✅ Experiment Registry initialized")
        
        self._promotion_gates = PromotionGates({**base_config, 'storage_path': self.storage_path / 'promotions'})
        logger.info("✅ Promotion Gates initialized")
        
        self._risk_governance = RiskGovernance({**base_config, 'storage_path': self.storage_path / 'risk'})
        logger.info("✅ Risk Governance initialized")
        
        self._compute_controller = ComputeBudgetController({**base_config, 'storage_path': self.storage_path / 'compute'})
        logger.info("✅ Compute Budget Controller initialized")
        
        self._improvement_engine = SelfImprovementEngine({**base_config, 'storage_path': self.storage_path / 'improvements'})
        logger.info("✅ Self-Improvement Engine initialized")
        
        logger.info("=" * 80)
        logger.info("EVOLUTION ORCHESTRATOR READY FOR CONTINUOUS IMPROVEMENT")
        logger.info("=" * 80)
    
    async def start_evolution_cycle(self) -> EvolutionCycle:
        """Start a new evolution cycle."""
        cycle_id = f"EVOL-{uuid.uuid4().hex[:12]}"
        
        cycle = EvolutionCycle(
            cycle_id=cycle_id,
            started_at=datetime.now(timezone.utc),
            current_phase=EvolutionPhase.ANALYSIS,
        )
        
        self._cycles[cycle_id] = cycle
        self._current_cycle = cycle
        
        logger.info(f"🔄 Started evolution cycle {cycle_id}")
        
        return cycle
    
    async def run_evolution_cycle(
        self,
        component_metrics: Dict[str, Dict[str, float]],
    ) -> EvolutionCycle:
        """
        Run a complete evolution cycle.
        
        Args:
            component_metrics: Current metrics for all components
        
        Returns:
            Completed EvolutionCycle
        """
        if not self._current_cycle:
            await self.start_evolution_cycle()
        
        cycle = self._current_cycle
        
        cycle.current_phase = EvolutionPhase.ANALYSIS
        logger.info(f"📊 Phase: ANALYSIS")
        proposals = await self._improvement_engine.analyze_for_improvements(component_metrics)
        cycle.improvements_identified = [p.proposal_id for p in proposals]
        self._cumulative_metrics.total_improvements_proposed += len(proposals)
        
        cycle.current_phase = EvolutionPhase.PROPOSAL
        logger.info(f"💡 Phase: PROPOSAL - {len(proposals)} improvements identified")
        
        approved_proposals = []
        for proposal in proposals:
            risk_assessment = await self._risk_governance.assess_risk(
                target_id=proposal.proposal_id,
                target_type='improvement',
                change_description={
                    'type': proposal.improvement_type.value,
                    'affects_verification': 'verification' in proposal.target_component.lower(),
                    'sample_size': 0,
                    'metrics': {},
                },
            )
            
            cycle.risks_identified.append(risk_assessment.assessment_id)
            
            if risk_assessment.is_acceptable:
                approved_proposals.append(proposal)
                await self._improvement_engine.propose_improvement(proposal.proposal_id)
        
        logger.info(f"✅ {len(approved_proposals)} proposals approved after risk assessment")
        
        cycle.current_phase = EvolutionPhase.EXPERIMENTATION
        logger.info(f"🧪 Phase: EXPERIMENTATION")
        
        experiments = []
        for proposal in approved_proposals[:self._evolution_config['max_concurrent_experiments']]:
            compute_resources = {
                ResourceType.CPU: 4.0,
                ResourceType.MEMORY: 8.0,
                ResourceType.GPU: 0.5,
            }
            
            allocation = await self._compute_controller.request_allocation(
                task_id=proposal.proposal_id,
                task_type='improvement_experiment',
                resources=compute_resources,
                priority=AllocationPriority.HIGH,
                duration_hours=48,
            )
            
            if allocation:
                cycle.compute_allocated += sum(compute_resources.values())
                
                experiment = await self._experiment_registry.propose_experiment(
                    experiment_type=ExperimentType.VERIFICATION_IMPROVEMENT,
                    name=proposal.description,
                    description=proposal.hypothesis,
                    hypothesis=proposal.hypothesis,
                    configuration=proposal.implementation_plan,
                    proposed_by='evolution_orchestrator',
                    target_sample_size=1000,
                )
                
                await self._experiment_registry.approve_experiment(
                    experiment.experiment_id,
                    approved_by='evolution_orchestrator',
                )
                
                await self._experiment_registry.start_experiment(experiment.experiment_id)
                
                experiments.append(experiment)
                cycle.experiments_launched.append(experiment.experiment_id)
                
                logger.info(f"🚀 Launched experiment {experiment.experiment_id}")
        
        self._cumulative_metrics.total_experiments_run += len(experiments)
        
        cycle.current_phase = EvolutionPhase.VALIDATION
        logger.info(f"🔍 Phase: VALIDATION")
        
        validated_experiments = []
        for experiment in experiments:
            comparison = await self._experiment_registry.compare_experiments(experiment.experiment_id)
            
            if comparison.recommendation == "PROMOTE":
                promotion_result = await self._promotion_gates.validate_for_promotion(
                    experiment_id=experiment.experiment_id,
                    experiment_data=experiment.to_dict(),
                )
                
                if promotion_result.approved_for_production:
                    validated_experiments.append(experiment)
                    logger.info(f"✅ Experiment {experiment.experiment_id} validated for deployment")
                elif promotion_result.recommendation == "APPROVE WITH CANARY DEPLOYMENT":
                    canary = await self._promotion_gates.start_canary_deployment(
                        experiment_id=experiment.experiment_id,
                        traffic_percentage=5.0,
                        duration_hours=24,
                    )
                    logger.info(f"🐤 Started canary deployment {canary.canary_id}")
        
        cycle.current_phase = EvolutionPhase.DEPLOYMENT
        logger.info(f"🚀 Phase: DEPLOYMENT")
        
        for experiment in validated_experiments:
            promoted = await self._experiment_registry.promote_experiment(
                experiment.experiment_id,
                promoted_by='evolution_orchestrator',
            )
            
            if promoted:
                cycle.improvements_deployed.append(experiment.experiment_id)
                self._cumulative_metrics.total_improvements_deployed += 1
                self._cumulative_metrics.successful_experiments += 1
                
                logger.info(f"✅ Deployed improvement {experiment.experiment_id}")
        
        cycle.current_phase = EvolutionPhase.MONITORING
        logger.info(f"👁️ Phase: MONITORING")
        
        for experiment_id in cycle.improvements_deployed:
            should_rollback, reason = await self._risk_governance.monitor_deployment_risk(
                deployment_id=experiment_id,
                metrics=component_metrics.get('infrastructure', {}),
            )
            
            if should_rollback:
                await self._experiment_registry.rollback_experiment(experiment_id, reason)
                logger.warning(f"⚠️ Rolled back {experiment_id}: {reason}")
        
        cycle.current_phase = EvolutionPhase.LEARNING
        logger.info(f"🧠 Phase: LEARNING")
        
        for proposal_id in cycle.improvements_identified:
            await self._improvement_engine.learn_from_results(proposal_id)
        
        cycle.lessons_learned = [
            f"Identified {len(cycle.improvements_identified)} improvement opportunities",
            f"Launched {len(cycle.experiments_launched)} experiments",
            f"Deployed {len(cycle.improvements_deployed)} improvements",
            f"Used {cycle.compute_allocated:.1f} compute units",
        ]
        
        cycle.cycle_metrics = EvolutionMetrics(
            total_improvements_proposed=len(cycle.improvements_identified),
            total_improvements_deployed=len(cycle.improvements_deployed),
            total_experiments_run=len(cycle.experiments_launched),
            successful_experiments=len(cycle.improvements_deployed),
            total_compute_used=cycle.compute_allocated,
        )
        
        cycle.completed_at = datetime.now(timezone.utc)
        
        await self._persist_cycle(cycle)
        
        logger.info(f"✅ Completed evolution cycle {cycle.cycle_id}")
        logger.info(f"📈 Results: {len(cycle.improvements_deployed)} improvements deployed")
        
        self._current_cycle = None
        
        return cycle
    
    async def continuous_evolution_loop(self):
        """Run continuous evolution in a loop."""
        self._is_running = True
        
        logger.info("🔄 Starting continuous evolution loop")
        
        while self._is_running:
            try:
                component_metrics = await self._gather_component_metrics()
                
                cycle = await self.run_evolution_cycle(component_metrics)
                
                logger.info(f"💤 Waiting {self._evolution_config['cycle_interval_hours']} hours until next cycle")
                
                await asyncio.sleep(self._evolution_config['cycle_interval_hours'] * 3600)
                
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}", exc_info=True)
                await asyncio.sleep(3600)
    
    async def _gather_component_metrics(self) -> Dict[str, Dict[str, float]]:
        """Gather current metrics from all components."""
        return {
            'hallucination_detector': {
                'accuracy': 0.92,
                'precision': 0.90,
                'recall': 0.88,
                'f1_score': 0.89,
                'latency_ms': 120.0,
                'error_rate': 0.04,
                'hallucination_rate': 0.015,
            },
            'fact_checker': {
                'accuracy': 0.94,
                'precision': 0.93,
                'recall': 0.91,
                'f1_score': 0.92,
                'latency_ms': 180.0,
                'error_rate': 0.03,
            },
            'evidence_verification': {
                'accuracy': 0.96,
                'precision': 0.95,
                'recall': 0.94,
                'f1_score': 0.945,
                'latency_ms': 150.0,
                'error_rate': 0.02,
            },
            'consensus_engine': {
                'accuracy': 0.93,
                'latency_ms': 200.0,
                'error_rate': 0.035,
            },
        }
    
    async def stop_evolution(self):
        """Stop the continuous evolution loop."""
        self._is_running = False
        logger.info("🛑 Stopping evolution loop")
    
    def get_cumulative_metrics(self) -> EvolutionMetrics:
        """Get cumulative evolution metrics."""
        return self._cumulative_metrics
    
    def get_cycle(self, cycle_id: str) -> Optional[EvolutionCycle]:
        """Get an evolution cycle by ID."""
        return self._cycles.get(cycle_id)
    
    def get_current_cycle(self) -> Optional[EvolutionCycle]:
        """Get the current active cycle."""
        return self._current_cycle
    
    async def _persist_cycle(self, cycle: EvolutionCycle):
        """Persist evolution cycle to storage."""
        cycle_file = self.storage_path / 'cycles' / f"{cycle.cycle_id}.json"
        cycle_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cycle_file, 'w') as f:
            json.dump(cycle.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evolution orchestrator statistics."""
        return {
            'total_cycles': len(self._cycles),
            'current_cycle': self._current_cycle.cycle_id if self._current_cycle else None,
            'is_running': self._is_running,
            'cumulative_metrics': self._cumulative_metrics.to_dict(),
            'config': self._evolution_config,
            'components': {
                'experiment_registry': self._experiment_registry.get_statistics() if self._experiment_registry else {},
                'promotion_gates': self._promotion_gates.get_statistics() if self._promotion_gates else {},
                'risk_governance': self._risk_governance.get_statistics() if self._risk_governance else {},
                'compute_controller': self._compute_controller.get_statistics() if self._compute_controller else {},
                'improvement_engine': self._improvement_engine.get_statistics() if self._improvement_engine else {},
            },
        }
    
    @property
    def experiment_registry(self) -> ExperimentRegistry:
        return self._experiment_registry
    
    @property
    def promotion_gates(self) -> PromotionGates:
        return self._promotion_gates
    
    @property
    def risk_governance(self) -> RiskGovernance:
        return self._risk_governance
    
    @property
    def compute_controller(self) -> ComputeBudgetController:
        return self._compute_controller
    
    @property
    def improvement_engine(self) -> SelfImprovementEngine:
        return self._improvement_engine
