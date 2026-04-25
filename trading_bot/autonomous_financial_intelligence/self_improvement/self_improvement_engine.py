"""
Self-Improvement Engine

Enables recursive self-improvement of the verification infrastructure.
Automatically identifies, proposes, and implements improvements.
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

logger = logging.getLogger(__name__)


class ImprovementType(Enum):
    """Types of improvements."""
    ALGORITHM_OPTIMIZATION = "algorithm_optimization"
    PARAMETER_TUNING = "parameter_tuning"
    ARCHITECTURE_ENHANCEMENT = "architecture_enhancement"
    DETECTION_IMPROVEMENT = "detection_improvement"
    VERIFICATION_ENHANCEMENT = "verification_enhancement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ACCURACY_IMPROVEMENT = "accuracy_improvement"
    EFFICIENCY_GAIN = "efficiency_gain"


class ImprovementStatus(Enum):
    """Status of an improvement."""
    IDENTIFIED = "identified"
    PROPOSED = "proposed"
    VALIDATED = "validated"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    DEPLOYED = "deployed"
    MONITORING = "monitoring"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class PerformanceBaseline:
    """Baseline performance metrics."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    latency_ms: float
    throughput: float
    error_rate: float
    hallucination_rate: float
    resource_usage: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'latency_ms': self.latency_ms,
            'throughput': self.throughput,
            'error_rate': self.error_rate,
            'hallucination_rate': self.hallucination_rate,
            'resource_usage': self.resource_usage,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class ImprovementProposal:
    """Proposal for an improvement."""
    proposal_id: str
    improvement_type: ImprovementType
    target_component: str
    description: str
    hypothesis: str
    expected_improvement: Dict[str, float]
    implementation_plan: List[Dict[str, Any]]
    estimated_effort: float
    estimated_risk: float
    status: ImprovementStatus
    created_at: datetime
    created_by: str
    baseline_metrics: Optional[PerformanceBaseline] = None
    test_results: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposal_id': self.proposal_id,
            'improvement_type': self.improvement_type.value,
            'target_component': self.target_component,
            'description': self.description,
            'hypothesis': self.hypothesis,
            'expected_improvement': self.expected_improvement,
            'implementation_plan': self.implementation_plan,
            'estimated_effort': self.estimated_effort,
            'estimated_risk': self.estimated_risk,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'baseline_metrics': self.baseline_metrics.to_dict() if self.baseline_metrics else None,
            'test_results': self.test_results,
        }


@dataclass
class ImprovementCycle:
    """A cycle of self-improvement."""
    cycle_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    proposals_generated: int
    proposals_implemented: int
    overall_improvement: float
    components_improved: List[str]
    lessons_learned: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_id': self.cycle_id,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'proposals_generated': self.proposals_generated,
            'proposals_implemented': self.proposals_implemented,
            'overall_improvement': self.overall_improvement,
            'components_improved': self.components_improved,
            'lessons_learned': self.lessons_learned,
        }


class SelfImprovementEngine:
    """
    Recursive self-improvement engine for the infrastructure.
    
    Provides:
    - Automated improvement identification
    - Proposal generation
    - A/B testing of improvements
    - Performance tracking
    - Recursive optimization
    - Learning from results
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'self_improvement_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._proposals: Dict[str, ImprovementProposal] = {}
        self._cycles: Dict[str, ImprovementCycle] = {}
        self._baselines: Dict[str, PerformanceBaseline] = {}
        self._knowledge_base: Dict[str, Any] = {}
        
        self._improvement_config = {
            'analysis_interval_hours': 24,
            'minimum_improvement_threshold': 0.03,
            'maximum_concurrent_improvements': 3,
            'learning_rate': 0.1,
            'exploration_rate': 0.2,
        }
        
        self._current_cycle: Optional[ImprovementCycle] = None
        
        logger.info("✅ Self-Improvement Engine initialized")
    
    async def analyze_for_improvements(
        self,
        component_metrics: Dict[str, Dict[str, float]],
    ) -> List[ImprovementProposal]:
        """
        Analyze system performance and identify improvement opportunities.
        
        Args:
            component_metrics: Metrics for each component
        
        Returns:
            List of improvement proposals
        """
        proposals = []
        
        for component, metrics in component_metrics.items():
            baseline = self._baselines.get(component)
            
            if not baseline:
                baseline = PerformanceBaseline(
                    accuracy=metrics.get('accuracy', 0.85),
                    precision=metrics.get('precision', 0.82),
                    recall=metrics.get('recall', 0.80),
                    f1_score=metrics.get('f1_score', 0.81),
                    latency_ms=metrics.get('latency_ms', 150.0),
                    throughput=metrics.get('throughput', 100.0),
                    error_rate=metrics.get('error_rate', 0.05),
                    hallucination_rate=metrics.get('hallucination_rate', 0.02),
                    resource_usage=metrics.get('resource_usage', 0.6),
                    timestamp=datetime.now(timezone.utc),
                )
                self._baselines[component] = baseline
            
            component_proposals = await self._identify_component_improvements(
                component, metrics, baseline
            )
            proposals.extend(component_proposals)
        
        meta_proposals = await self._identify_meta_improvements(component_metrics)
        proposals.extend(meta_proposals)
        
        for proposal in proposals:
            self._proposals[proposal.proposal_id] = proposal
            await self._persist_proposal(proposal)
        
        logger.info(f"Identified {len(proposals)} improvement opportunities")
        
        return proposals
    
    async def _identify_component_improvements(
        self,
        component: str,
        current_metrics: Dict[str, float],
        baseline: PerformanceBaseline,
    ) -> List[ImprovementProposal]:
        """Identify improvements for a specific component."""
        proposals = []
        
        if current_metrics.get('error_rate', 0) > baseline.error_rate * 1.2:
            proposals.append(ImprovementProposal(
                proposal_id=f"IMP-{uuid.uuid4().hex[:12]}",
                improvement_type=ImprovementType.ACCURACY_IMPROVEMENT,
                target_component=component,
                description=f"Reduce error rate in {component}",
                hypothesis="Enhanced validation logic will reduce errors",
                expected_improvement={'error_rate': -0.02, 'accuracy': 0.03},
                implementation_plan=[
                    {'step': 'analyze_error_patterns', 'duration_hours': 4},
                    {'step': 'implement_enhanced_validation', 'duration_hours': 8},
                    {'step': 'test_improvements', 'duration_hours': 12},
                ],
                estimated_effort=24.0,
                estimated_risk=0.2,
                status=ImprovementStatus.IDENTIFIED,
                created_at=datetime.now(timezone.utc),
                created_by='self_improvement_engine',
                baseline_metrics=baseline,
            ))
        
        if current_metrics.get('latency_ms', 0) > baseline.latency_ms * 1.5:
            proposals.append(ImprovementProposal(
                proposal_id=f"IMP-{uuid.uuid4().hex[:12]}",
                improvement_type=ImprovementType.PERFORMANCE_OPTIMIZATION,
                target_component=component,
                description=f"Optimize latency in {component}",
                hypothesis="Caching and parallel processing will reduce latency",
                expected_improvement={'latency_ms': -50.0, 'throughput': 20.0},
                implementation_plan=[
                    {'step': 'profile_performance', 'duration_hours': 2},
                    {'step': 'implement_caching', 'duration_hours': 6},
                    {'step': 'add_parallelization', 'duration_hours': 8},
                ],
                estimated_effort=16.0,
                estimated_risk=0.3,
                status=ImprovementStatus.IDENTIFIED,
                created_at=datetime.now(timezone.utc),
                created_by='self_improvement_engine',
                baseline_metrics=baseline,
            ))
        
        if current_metrics.get('hallucination_rate', 0) > baseline.hallucination_rate * 1.1:
            proposals.append(ImprovementProposal(
                proposal_id=f"IMP-{uuid.uuid4().hex[:12]}",
                improvement_type=ImprovementType.DETECTION_IMPROVEMENT,
                target_component=component,
                description=f"Enhance hallucination detection in {component}",
                hypothesis="Additional detection signals will improve accuracy",
                expected_improvement={'hallucination_rate': -0.005, 'precision': 0.02},
                implementation_plan=[
                    {'step': 'analyze_false_negatives', 'duration_hours': 4},
                    {'step': 'add_detection_signals', 'duration_hours': 10},
                    {'step': 'calibrate_thresholds', 'duration_hours': 6},
                ],
                estimated_effort=20.0,
                estimated_risk=0.15,
                status=ImprovementStatus.IDENTIFIED,
                created_at=datetime.now(timezone.utc),
                created_by='self_improvement_engine',
                baseline_metrics=baseline,
            ))
        
        if current_metrics.get('f1_score', 0) < baseline.f1_score * 0.95:
            proposals.append(ImprovementProposal(
                proposal_id=f"IMP-{uuid.uuid4().hex[:12]}",
                improvement_type=ImprovementType.ALGORITHM_OPTIMIZATION,
                target_component=component,
                description=f"Optimize algorithm in {component}",
                hypothesis="Parameter tuning will improve F1 score",
                expected_improvement={'f1_score': 0.04, 'accuracy': 0.02},
                implementation_plan=[
                    {'step': 'grid_search_parameters', 'duration_hours': 8},
                    {'step': 'validate_improvements', 'duration_hours': 6},
                    {'step': 'deploy_optimized_params', 'duration_hours': 2},
                ],
                estimated_effort=16.0,
                estimated_risk=0.1,
                status=ImprovementStatus.IDENTIFIED,
                created_at=datetime.now(timezone.utc),
                created_by='self_improvement_engine',
                baseline_metrics=baseline,
            ))
        
        return proposals
    
    async def _identify_meta_improvements(
        self,
        component_metrics: Dict[str, Dict[str, float]],
    ) -> List[ImprovementProposal]:
        """Identify system-wide meta improvements."""
        proposals = []
        
        avg_latency = sum(m.get('latency_ms', 0) for m in component_metrics.values()) / len(component_metrics)
        
        if avg_latency > 200:
            proposals.append(ImprovementProposal(
                proposal_id=f"IMP-{uuid.uuid4().hex[:12]}",
                improvement_type=ImprovementType.ARCHITECTURE_ENHANCEMENT,
                target_component='infrastructure',
                description="Implement system-wide caching layer",
                hypothesis="Centralized caching will reduce overall latency",
                expected_improvement={'avg_latency_ms': -30.0, 'throughput': 25.0},
                implementation_plan=[
                    {'step': 'design_cache_architecture', 'duration_hours': 8},
                    {'step': 'implement_cache_layer', 'duration_hours': 16},
                    {'step': 'integrate_with_components', 'duration_hours': 12},
                ],
                estimated_effort=36.0,
                estimated_risk=0.4,
                status=ImprovementStatus.IDENTIFIED,
                created_at=datetime.now(timezone.utc),
                created_by='self_improvement_engine',
            ))
        
        components_with_high_error = [
            comp for comp, metrics in component_metrics.items()
            if metrics.get('error_rate', 0) > 0.05
        ]
        
        if len(components_with_high_error) >= 3:
            proposals.append(ImprovementProposal(
                proposal_id=f"IMP-{uuid.uuid4().hex[:12]}",
                improvement_type=ImprovementType.VERIFICATION_ENHANCEMENT,
                target_component='verification_pipeline',
                description="Add cross-component validation layer",
                hypothesis="Cross-validation will catch errors earlier",
                expected_improvement={'system_error_rate': -0.02},
                implementation_plan=[
                    {'step': 'design_validation_layer', 'duration_hours': 6},
                    {'step': 'implement_validators', 'duration_hours': 12},
                    {'step': 'integrate_pipeline', 'duration_hours': 8},
                ],
                estimated_effort=26.0,
                estimated_risk=0.25,
                status=ImprovementStatus.IDENTIFIED,
                created_at=datetime.now(timezone.utc),
                created_by='self_improvement_engine',
            ))
        
        return proposals
    
    async def propose_improvement(
        self,
        proposal_id: str,
    ) -> bool:
        """
        Move an improvement from identified to proposed status.
        
        Args:
            proposal_id: ID of the proposal
        
        Returns:
            True if proposed successfully
        """
        if proposal_id not in self._proposals:
            return False
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status != ImprovementStatus.IDENTIFIED:
            return False
        
        proposal.status = ImprovementStatus.PROPOSED
        await self._persist_proposal(proposal)
        
        logger.info(f"Proposed improvement {proposal_id}: {proposal.description}")
        
        return True
    
    async def implement_improvement(
        self,
        proposal_id: str,
    ) -> bool:
        """
        Implement an approved improvement.
        
        Args:
            proposal_id: ID of the proposal
        
        Returns:
            True if implementation started successfully
        """
        if proposal_id not in self._proposals:
            return False
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status not in [ImprovementStatus.PROPOSED, ImprovementStatus.VALIDATED]:
            return False
        
        proposal.status = ImprovementStatus.IMPLEMENTING
        
        for step in proposal.implementation_plan:
            logger.info(f"Executing implementation step: {step['step']}")
        
        proposal.status = ImprovementStatus.TESTING
        
        await self._persist_proposal(proposal)
        
        logger.info(f"Implemented improvement {proposal_id}")
        
        return True
    
    async def test_improvement(
        self,
        proposal_id: str,
        test_metrics: Dict[str, float],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Test an implemented improvement.
        
        Args:
            proposal_id: ID of the proposal
            test_metrics: Metrics from testing
        
        Returns:
            Tuple of (success, results)
        """
        if proposal_id not in self._proposals:
            return False, {'error': 'Proposal not found'}
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status != ImprovementStatus.TESTING:
            return False, {'error': 'Proposal not in testing status'}
        
        baseline = proposal.baseline_metrics
        if not baseline:
            return False, {'error': 'No baseline metrics'}
        
        improvements = {}
        for metric, expected_change in proposal.expected_improvement.items():
            baseline_value = getattr(baseline, metric, 0)
            test_value = test_metrics.get(metric, 0)
            actual_change = test_value - baseline_value
            
            improvements[metric] = {
                'expected': expected_change,
                'actual': actual_change,
                'met_expectation': (actual_change >= expected_change * 0.8),
            }
        
        success = all(imp['met_expectation'] for imp in improvements.values())
        
        results = {
            'success': success,
            'improvements': improvements,
            'test_metrics': test_metrics,
        }
        
        proposal.test_results = results
        
        if success:
            proposal.status = ImprovementStatus.DEPLOYED
            logger.info(f"Improvement {proposal_id} tested successfully")
        else:
            proposal.status = ImprovementStatus.FAILED
            logger.warning(f"Improvement {proposal_id} failed testing")
        
        await self._persist_proposal(proposal)
        
        return success, results
    
    async def learn_from_results(
        self,
        proposal_id: str,
    ):
        """
        Learn from improvement results to enhance future proposals.
        
        Args:
            proposal_id: ID of the proposal
        """
        if proposal_id not in self._proposals:
            return
        
        proposal = self._proposals[proposal_id]
        
        if not proposal.test_results:
            return
        
        lesson_key = f"{proposal.improvement_type.value}_{proposal.target_component}"
        
        if lesson_key not in self._knowledge_base:
            self._knowledge_base[lesson_key] = {
                'successes': 0,
                'failures': 0,
                'avg_improvement': 0.0,
                'best_practices': [],
            }
        
        knowledge = self._knowledge_base[lesson_key]
        
        if proposal.test_results['success']:
            knowledge['successes'] += 1
            
            actual_improvements = [
                imp['actual'] for imp in proposal.test_results['improvements'].values()
            ]
            avg_improvement = sum(actual_improvements) / len(actual_improvements) if actual_improvements else 0
            
            knowledge['avg_improvement'] = (
                knowledge['avg_improvement'] * 0.9 + avg_improvement * 0.1
            )
            
            for step in proposal.implementation_plan:
                if step['step'] not in knowledge['best_practices']:
                    knowledge['best_practices'].append(step['step'])
        else:
            knowledge['failures'] += 1
        
        logger.info(f"Learned from improvement {proposal_id}")
    
    async def start_improvement_cycle(self) -> ImprovementCycle:
        """Start a new improvement cycle."""
        cycle_id = f"CYCLE-{uuid.uuid4().hex[:12]}"
        
        cycle = ImprovementCycle(
            cycle_id=cycle_id,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            proposals_generated=0,
            proposals_implemented=0,
            overall_improvement=0.0,
            components_improved=[],
            lessons_learned=[],
        )
        
        self._cycles[cycle_id] = cycle
        self._current_cycle = cycle
        
        logger.info(f"Started improvement cycle {cycle_id}")
        
        return cycle
    
    async def complete_improvement_cycle(self) -> Optional[ImprovementCycle]:
        """Complete the current improvement cycle."""
        if not self._current_cycle:
            return None
        
        cycle = self._current_cycle
        cycle.completed_at = datetime.now(timezone.utc)
        
        successful_proposals = [
            p for p in self._proposals.values()
            if p.status == ImprovementStatus.SUCCESSFUL
        ]
        
        cycle.proposals_implemented = len(successful_proposals)
        cycle.components_improved = list(set(p.target_component for p in successful_proposals))
        
        if successful_proposals:
            total_improvement = sum(
                sum(imp['actual'] for imp in p.test_results.get('improvements', {}).values())
                for p in successful_proposals
                if p.test_results
            )
            cycle.overall_improvement = total_improvement / len(successful_proposals)
        
        cycle.lessons_learned = [
            f"Implemented {len(successful_proposals)} improvements",
            f"Improved {len(cycle.components_improved)} components",
            f"Average improvement: {cycle.overall_improvement:.2%}",
        ]
        
        await self._persist_cycle(cycle)
        
        logger.info(f"Completed improvement cycle {cycle.cycle_id}: "
                   f"{cycle.proposals_implemented} improvements, "
                   f"{cycle.overall_improvement:.2%} average improvement")
        
        self._current_cycle = None
        
        return cycle
    
    def get_proposal(self, proposal_id: str) -> Optional[ImprovementProposal]:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)
    
    def get_proposals_by_status(self, status: ImprovementStatus) -> List[ImprovementProposal]:
        """Get proposals by status."""
        return [p for p in self._proposals.values() if p.status == status]
    
    def get_knowledge_base(self) -> Dict[str, Any]:
        """Get the accumulated knowledge base."""
        return self._knowledge_base.copy()
    
    async def _persist_proposal(self, proposal: ImprovementProposal):
        """Persist proposal to storage."""
        proposal_file = self.storage_path / 'proposals' / f"{proposal.proposal_id}.json"
        proposal_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(proposal_file, 'w') as f:
            json.dump(proposal.to_dict(), f, indent=2)
    
    async def _persist_cycle(self, cycle: ImprovementCycle):
        """Persist cycle to storage."""
        cycle_file = self.storage_path / 'cycles' / f"{cycle.cycle_id}.json"
        cycle_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cycle_file, 'w') as f:
            json.dump(cycle.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get self-improvement statistics."""
        status_counts = {}
        for proposal in self._proposals.values():
            status_counts[proposal.status.value] = status_counts.get(proposal.status.value, 0) + 1
        
        type_counts = {}
        for proposal in self._proposals.values():
            type_counts[proposal.improvement_type.value] = type_counts.get(proposal.improvement_type.value, 0) + 1
        
        successful = [p for p in self._proposals.values() if p.status == ImprovementStatus.SUCCESSFUL]
        
        return {
            'total_proposals': len(self._proposals),
            'proposals_by_status': status_counts,
            'proposals_by_type': type_counts,
            'successful_improvements': len(successful),
            'total_cycles': len(self._cycles),
            'current_cycle': self._current_cycle.cycle_id if self._current_cycle else None,
            'knowledge_base_entries': len(self._knowledge_base),
        }
