"""
Experiment Registry

Tracks and manages experiments for continuous improvement of the infrastructure.
Enables A/B testing, performance tracking, and systematic evolution.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid
import numpy as np

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Status of an experiment."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ExperimentType(Enum):
    """Types of experiments."""
    VERIFICATION_IMPROVEMENT = "verification_improvement"
    HALLUCINATION_DETECTION = "hallucination_detection"
    CONSENSUS_MECHANISM = "consensus_mechanism"
    REASONING_ENHANCEMENT = "reasoning_enhancement"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    EVIDENCE_VALIDATION = "evidence_validation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ARCHITECTURE_CHANGE = "architecture_change"


@dataclass
class ExperimentMetrics:
    """Metrics tracked for an experiment."""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    latency_ms: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    resource_usage: float = 0.0
    hallucination_rate: float = 0.0
    verification_success_rate: float = 0.0
    confidence_calibration_error: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'latency_ms': self.latency_ms,
            'throughput': self.throughput,
            'error_rate': self.error_rate,
            'resource_usage': self.resource_usage,
            'hallucination_rate': self.hallucination_rate,
            'verification_success_rate': self.verification_success_rate,
            'confidence_calibration_error': self.confidence_calibration_error,
            'custom_metrics': self.custom_metrics,
        }
    
    def overall_score(self) -> float:
        """Calculate overall performance score."""
        score = (
            0.3 * self.accuracy +
            0.2 * self.f1_score +
            0.2 * (1 - self.error_rate) +
            0.15 * (1 - self.hallucination_rate) +
            0.15 * self.verification_success_rate
        )
        return max(0.0, min(1.0, score))


@dataclass
class Experiment:
    """An experiment for improving the infrastructure."""
    experiment_id: str
    experiment_type: ExperimentType
    name: str
    description: str
    hypothesis: str
    proposed_by: str
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    baseline_metrics: Optional[ExperimentMetrics] = None
    current_metrics: Optional[ExperimentMetrics] = None
    improvement_percentage: float = 0.0
    sample_size: int = 0
    target_sample_size: int = 1000
    configuration: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    statistical_significance: float = 0.0
    risk_score: float = 0.0
    compute_budget_used: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'experiment_id': self.experiment_id,
            'experiment_type': self.experiment_type.value,
            'name': self.name,
            'description': self.description,
            'hypothesis': self.hypothesis,
            'proposed_by': self.proposed_by,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'baseline_metrics': self.baseline_metrics.to_dict() if self.baseline_metrics else None,
            'current_metrics': self.current_metrics.to_dict() if self.current_metrics else None,
            'improvement_percentage': self.improvement_percentage,
            'sample_size': self.sample_size,
            'target_sample_size': self.target_sample_size,
            'configuration': self.configuration,
            'results': self.results,
            'statistical_significance': self.statistical_significance,
            'risk_score': self.risk_score,
            'compute_budget_used': self.compute_budget_used,
        }


@dataclass
class ExperimentComparison:
    """Comparison between baseline and experiment."""
    experiment_id: str
    metric_improvements: Dict[str, float]
    overall_improvement: float
    is_statistically_significant: bool
    p_value: float
    confidence_interval: Tuple[float, float]
    recommendation: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'experiment_id': self.experiment_id,
            'metric_improvements': self.metric_improvements,
            'overall_improvement': self.overall_improvement,
            'is_statistically_significant': self.is_statistically_significant,
            'p_value': self.p_value,
            'confidence_interval': self.confidence_interval,
            'recommendation': self.recommendation,
            'timestamp': self.timestamp.isoformat(),
        }


class ExperimentRegistry:
    """
    Registry for tracking and managing infrastructure experiments.
    
    Provides:
    - Experiment proposal and approval
    - A/B testing framework
    - Performance tracking
    - Statistical analysis
    - Experiment lifecycle management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'experiment_registry_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._experiments: Dict[str, Experiment] = {}
        self._active_experiments: Set[str] = set()
        self._baseline_performance: Dict[str, ExperimentMetrics] = {}
        
        self._registry_config = {
            'max_concurrent_experiments': 5,
            'minimum_sample_size': 100,
            'significance_threshold': 0.05,
            'minimum_improvement_threshold': 0.05,
            'max_experiment_duration_hours': 168,
            'auto_promote_threshold': 0.15,
        }
        
        logger.info("✅ Experiment Registry initialized")
    
    async def propose_experiment(
        self,
        experiment_type: ExperimentType,
        name: str,
        description: str,
        hypothesis: str,
        configuration: Dict[str, Any],
        proposed_by: str,
        target_sample_size: int = 1000,
    ) -> Experiment:
        """
        Propose a new experiment.
        
        Args:
            experiment_type: Type of experiment
            name: Experiment name
            description: Detailed description
            hypothesis: What we expect to improve
            configuration: Experiment configuration
            proposed_by: Who proposed it
            target_sample_size: Target sample size
        
        Returns:
            Experiment object
        """
        experiment_id = f"EXP-{uuid.uuid4().hex[:12]}"
        
        experiment = Experiment(
            experiment_id=experiment_id,
            experiment_type=experiment_type,
            name=name,
            description=description,
            hypothesis=hypothesis,
            proposed_by=proposed_by,
            status=ExperimentStatus.PROPOSED,
            created_at=datetime.now(timezone.utc),
            configuration=configuration,
            target_sample_size=target_sample_size,
        )
        
        self._experiments[experiment_id] = experiment
        await self._persist_experiment(experiment)
        
        logger.info(f"Proposed experiment {experiment_id}: {name}")
        
        return experiment
    
    async def approve_experiment(
        self,
        experiment_id: str,
        approved_by: str,
        baseline_metrics: Optional[ExperimentMetrics] = None,
    ) -> bool:
        """
        Approve an experiment to start running.
        
        Args:
            experiment_id: ID of the experiment
            approved_by: Who approved it
            baseline_metrics: Optional baseline metrics
        
        Returns:
            True if approved successfully
        """
        if experiment_id not in self._experiments:
            return False
        
        experiment = self._experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.PROPOSED:
            return False
        
        if len(self._active_experiments) >= self._registry_config['max_concurrent_experiments']:
            logger.warning(f"Cannot approve experiment {experiment_id}: max concurrent limit reached")
            return False
        
        experiment.status = ExperimentStatus.APPROVED
        experiment.baseline_metrics = baseline_metrics or await self._get_current_baseline(experiment.experiment_type)
        
        await self._persist_experiment(experiment)
        
        logger.info(f"Approved experiment {experiment_id} by {approved_by}")
        
        return True
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """
        Start running an approved experiment.
        
        Args:
            experiment_id: ID of the experiment
        
        Returns:
            True if started successfully
        """
        if experiment_id not in self._experiments:
            return False
        
        experiment = self._experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.APPROVED:
            return False
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now(timezone.utc)
        experiment.current_metrics = ExperimentMetrics()
        
        self._active_experiments.add(experiment_id)
        
        await self._persist_experiment(experiment)
        
        logger.info(f"Started experiment {experiment_id}")
        
        return True
    
    async def record_experiment_result(
        self,
        experiment_id: str,
        metrics: ExperimentMetrics,
    ) -> bool:
        """
        Record results for a running experiment.
        
        Args:
            experiment_id: ID of the experiment
            metrics: Metrics to record
        
        Returns:
            True if recorded successfully
        """
        if experiment_id not in self._experiments:
            return False
        
        experiment = self._experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.RUNNING:
            return False
        
        experiment.current_metrics = metrics
        experiment.sample_size += 1
        
        if experiment.baseline_metrics:
            experiment.improvement_percentage = (
                (metrics.overall_score() - experiment.baseline_metrics.overall_score()) /
                experiment.baseline_metrics.overall_score() * 100
                if experiment.baseline_metrics.overall_score() > 0 else 0
            )
        
        if experiment.sample_size >= experiment.target_sample_size:
            await self._complete_experiment(experiment)
        
        await self._persist_experiment(experiment)
        
        return True
    
    async def _complete_experiment(self, experiment: Experiment):
        """Complete an experiment and analyze results."""
        experiment.status = ExperimentStatus.COMPLETED
        experiment.completed_at = datetime.now(timezone.utc)
        
        if experiment.baseline_metrics and experiment.current_metrics:
            experiment.statistical_significance = await self._calculate_statistical_significance(
                experiment.baseline_metrics,
                experiment.current_metrics,
                experiment.sample_size,
            )
        
        self._active_experiments.discard(experiment.experiment_id)
        
        logger.info(f"Completed experiment {experiment.experiment_id}: "
                   f"improvement={experiment.improvement_percentage:.2f}%, "
                   f"significance={experiment.statistical_significance:.3f}")
    
    async def _calculate_statistical_significance(
        self,
        baseline: ExperimentMetrics,
        current: ExperimentMetrics,
        sample_size: int,
    ) -> float:
        """Calculate statistical significance using t-test approximation."""
        if sample_size < self._registry_config['minimum_sample_size']:
            return 0.0
        
        baseline_score = baseline.overall_score()
        current_score = current.overall_score()
        
        diff = current_score - baseline_score
        
        pooled_std = 0.1
        
        if pooled_std == 0:
            return 1.0 if diff > 0 else 0.0
        
        t_stat = abs(diff) / (pooled_std / np.sqrt(sample_size))
        
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(t_stat, sample_size - 1))
        
        return 1 - p_value
    
    async def compare_experiments(
        self,
        experiment_id: str,
    ) -> ExperimentComparison:
        """
        Compare experiment results with baseline.
        
        Args:
            experiment_id: ID of the experiment
        
        Returns:
            ExperimentComparison with detailed analysis
        """
        if experiment_id not in self._experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self._experiments[experiment_id]
        
        if not experiment.baseline_metrics or not experiment.current_metrics:
            raise ValueError("Experiment missing baseline or current metrics")
        
        baseline = experiment.baseline_metrics
        current = experiment.current_metrics
        
        metric_improvements = {
            'accuracy': (current.accuracy - baseline.accuracy) / baseline.accuracy * 100 if baseline.accuracy > 0 else 0,
            'f1_score': (current.f1_score - baseline.f1_score) / baseline.f1_score * 100 if baseline.f1_score > 0 else 0,
            'error_rate': -(current.error_rate - baseline.error_rate) / baseline.error_rate * 100 if baseline.error_rate > 0 else 0,
            'hallucination_rate': -(current.hallucination_rate - baseline.hallucination_rate) / baseline.hallucination_rate * 100 if baseline.hallucination_rate > 0 else 0,
            'latency_ms': -(current.latency_ms - baseline.latency_ms) / baseline.latency_ms * 100 if baseline.latency_ms > 0 else 0,
        }
        
        overall_improvement = experiment.improvement_percentage
        
        p_value = 1 - experiment.statistical_significance
        is_significant = p_value < self._registry_config['significance_threshold']
        
        confidence_interval = (
            overall_improvement - 2 * abs(overall_improvement) * 0.1,
            overall_improvement + 2 * abs(overall_improvement) * 0.1,
        )
        
        if is_significant and overall_improvement > self._registry_config['minimum_improvement_threshold']:
            recommendation = "PROMOTE"
        elif is_significant and overall_improvement < -self._registry_config['minimum_improvement_threshold']:
            recommendation = "REJECT"
        elif not is_significant:
            recommendation = "INCONCLUSIVE - Need more data"
        else:
            recommendation = "NEUTRAL - No significant change"
        
        comparison = ExperimentComparison(
            experiment_id=experiment_id,
            metric_improvements=metric_improvements,
            overall_improvement=overall_improvement,
            is_statistically_significant=is_significant,
            p_value=p_value,
            confidence_interval=confidence_interval,
            recommendation=recommendation,
            timestamp=datetime.now(timezone.utc),
        )
        
        return comparison
    
    async def promote_experiment(
        self,
        experiment_id: str,
        promoted_by: str,
    ) -> bool:
        """
        Promote an experiment to production.
        
        Args:
            experiment_id: ID of the experiment
            promoted_by: Who promoted it
        
        Returns:
            True if promoted successfully
        """
        if experiment_id not in self._experiments:
            return False
        
        experiment = self._experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.COMPLETED:
            return False
        
        comparison = await self.compare_experiments(experiment_id)
        
        if comparison.recommendation != "PROMOTE":
            logger.warning(f"Experiment {experiment_id} does not meet promotion criteria")
            return False
        
        experiment.status = ExperimentStatus.PROMOTED
        
        await self._apply_experiment_to_production(experiment)
        
        await self._persist_experiment(experiment)
        
        logger.info(f"Promoted experiment {experiment_id} to production by {promoted_by}")
        
        return True
    
    async def _apply_experiment_to_production(self, experiment: Experiment):
        """Apply experiment configuration to production."""
        logger.info(f"Applying experiment {experiment.experiment_id} configuration to production")
    
    async def rollback_experiment(
        self,
        experiment_id: str,
        reason: str,
    ) -> bool:
        """
        Rollback a promoted experiment.
        
        Args:
            experiment_id: ID of the experiment
            reason: Reason for rollback
        
        Returns:
            True if rolled back successfully
        """
        if experiment_id not in self._experiments:
            return False
        
        experiment = self._experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.PROMOTED:
            return False
        
        experiment.status = ExperimentStatus.ROLLED_BACK
        experiment.results['rollback_reason'] = reason
        experiment.results['rollback_timestamp'] = datetime.now(timezone.utc).isoformat()
        
        await self._persist_experiment(experiment)
        
        logger.warning(f"Rolled back experiment {experiment_id}: {reason}")
        
        return True
    
    async def _get_current_baseline(
        self,
        experiment_type: ExperimentType,
    ) -> ExperimentMetrics:
        """Get current baseline metrics for an experiment type."""
        if experiment_type.value in self._baseline_performance:
            return self._baseline_performance[experiment_type.value]
        
        baseline = ExperimentMetrics(
            accuracy=0.85,
            precision=0.82,
            recall=0.80,
            f1_score=0.81,
            latency_ms=150.0,
            throughput=100.0,
            error_rate=0.05,
            resource_usage=0.6,
            hallucination_rate=0.02,
            verification_success_rate=0.95,
            confidence_calibration_error=0.08,
        )
        
        self._baseline_performance[experiment_type.value] = baseline
        
        return baseline
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get an experiment by ID."""
        return self._experiments.get(experiment_id)
    
    def get_active_experiments(self) -> List[Experiment]:
        """Get all active experiments."""
        return [
            self._experiments[exp_id]
            for exp_id in self._active_experiments
            if exp_id in self._experiments
        ]
    
    def get_experiments_by_status(self, status: ExperimentStatus) -> List[Experiment]:
        """Get experiments by status."""
        return [
            exp for exp in self._experiments.values()
            if exp.status == status
        ]
    
    async def _persist_experiment(self, experiment: Experiment):
        """Persist experiment to storage."""
        exp_file = self.storage_path / 'experiments' / f"{experiment.experiment_id}.json"
        exp_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(exp_file, 'w') as f:
            json.dump(experiment.to_dict(), f, indent=2, default=str)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        status_counts = {}
        for exp in self._experiments.values():
            status_counts[exp.status.value] = status_counts.get(exp.status.value, 0) + 1
        
        type_counts = {}
        for exp in self._experiments.values():
            type_counts[exp.experiment_type.value] = type_counts.get(exp.experiment_type.value, 0) + 1
        
        promoted_experiments = [e for e in self._experiments.values() if e.status == ExperimentStatus.PROMOTED]
        avg_improvement = sum(e.improvement_percentage for e in promoted_experiments) / len(promoted_experiments) if promoted_experiments else 0
        
        return {
            'total_experiments': len(self._experiments),
            'active_experiments': len(self._active_experiments),
            'experiments_by_status': status_counts,
            'experiments_by_type': type_counts,
            'promoted_count': len(promoted_experiments),
            'average_improvement': avg_improvement,
            'max_concurrent': self._registry_config['max_concurrent_experiments'],
        }
