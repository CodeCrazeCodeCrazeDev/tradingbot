"""
Experiment Registry
====================

Central registry for all AI experiments and self-programming attempts.
Tracks experiments from proposal through execution to promotion.

Features:
1. Experiment lifecycle management
2. Version control for experiments
3. Result tracking and comparison
4. Reproducibility guarantees
5. Audit trail for all experiments

Author: AlphaAlgo Trading System
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Status of an experiment."""
    PROPOSED = auto()        # Initial proposal
    REVIEWING = auto()       # Under safety review
    APPROVED = auto()        # Approved for execution
    REJECTED = auto()        # Rejected by safety review
    QUEUED = auto()          # Waiting for resources
    RUNNING = auto()         # Currently executing
    COMPLETED = auto()       # Finished successfully
    FAILED = auto()          # Failed during execution
    CANCELLED = auto()       # Cancelled by user/system
    PROMOTED = auto()        # Promoted to production


class ExperimentType(Enum):
    """Types of experiments."""
    STRATEGY = "strategy"              # Trading strategy
    INDICATOR = "indicator"            # Technical indicator
    MODEL = "model"                    # ML model
    FEATURE = "feature"                # Feature engineering
    RISK_RULE = "risk_rule"            # Risk management rule
    OPTIMIZATION = "optimization"      # Parameter optimization
    ARCHITECTURE = "architecture"      # System architecture change
    DATA_SOURCE = "data_source"        # New data source
    INTEGRATION = "integration"        # System integration


class ExperimentCategory(Enum):
    """Categories for experiment classification."""
    ALPHA_GENERATION = "alpha_generation"
    RISK_MANAGEMENT = "risk_management"
    EXECUTION = "execution"
    DATA_PIPELINE = "data_pipeline"
    INFRASTRUCTURE = "infrastructure"
    MONITORING = "monitoring"


@dataclass
class ExperimentMetrics:
    """Metrics from experiment execution."""
    # Performance Metrics
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    total_return: Optional[float] = None
    
    # Statistical Metrics
    p_value: Optional[float] = None
    t_statistic: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    
    # ML Metrics
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    
    # Resource Metrics
    execution_time_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_time_seconds: float = 0.0
    
    # Custom Metrics
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'total_return': self.total_return,
            'p_value': self.p_value,
            't_statistic': self.t_statistic,
            'confidence_interval': self.confidence_interval,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'auc_roc': self.auc_roc,
            'execution_time_seconds': self.execution_time_seconds,
            'memory_peak_mb': self.memory_peak_mb,
            'cpu_time_seconds': self.cpu_time_seconds,
            'custom': self.custom,
        }
    
    def get_score(self) -> float:
        """Calculate overall experiment score."""
        score = 0.0
        weights = 0.0
        
        if self.sharpe_ratio is not None:
            score += min(1.0, self.sharpe_ratio / 3.0) * 0.3
            weights += 0.3
        
        if self.win_rate is not None:
            score += self.win_rate * 0.2
            weights += 0.2
        
        if self.max_drawdown is not None:
            score += (1.0 - min(1.0, self.max_drawdown)) * 0.2
            weights += 0.2
        
        if self.accuracy is not None:
            score += self.accuracy * 0.15
            weights += 0.15
        
        if self.p_value is not None and self.p_value < 0.05:
            score += 0.15
            weights += 0.15
        
        return score / weights if weights > 0 else 0.0


@dataclass
class Experiment:
    """An experiment in the registry."""
    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    category: ExperimentCategory
    
    # Code and Configuration
    code: str
    code_hash: str
    config: Dict[str, Any]
    
    # Metadata
    created_by: str  # Agent ID
    created_at: datetime
    updated_at: datetime
    
    # Status
    status: ExperimentStatus = ExperimentStatus.PROPOSED
    
    # Versioning
    version: int = 1
    parent_experiment_id: Optional[str] = None
    
    # Execution
    sandbox_id: Optional[str] = None
    allocation_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    metrics: Optional[ExperimentMetrics] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Review
    safety_review_passed: bool = False
    safety_review_notes: List[str] = field(default_factory=list)
    reviewer_id: Optional[str] = None
    
    # Promotion
    promotion_eligible: bool = False
    promotion_score: float = 0.0
    promoted_at: Optional[datetime] = None
    
    # Tags and Labels
    tags: Set[str] = field(default_factory=set)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'experiment_type': self.experiment_type.value,
            'category': self.category.value,
            'code_hash': self.code_hash,
            'config': self.config,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status.name,
            'version': self.version,
            'parent_experiment_id': self.parent_experiment_id,
            'sandbox_id': self.sandbox_id,
            'allocation_id': self.allocation_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metrics': self.metrics.to_dict() if self.metrics else None,
            'output': self.output,
            'error': self.error,
            'safety_review_passed': self.safety_review_passed,
            'safety_review_notes': self.safety_review_notes,
            'promotion_eligible': self.promotion_eligible,
            'promotion_score': self.promotion_score,
            'tags': list(self.tags),
            'labels': self.labels,
        }
    
    def get_duration(self) -> Optional[timedelta]:
        """Get experiment duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class ExperimentComparison:
    """Comparison between experiments."""
    comparison_id: str
    experiment_ids: List[str]
    created_at: datetime
    
    # Comparison Results
    winner_id: Optional[str] = None
    rankings: List[Tuple[str, float]] = field(default_factory=list)
    metric_comparisons: Dict[str, Dict[str, float]] = field(default_factory=dict)
    statistical_significance: Dict[str, float] = field(default_factory=dict)
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'comparison_id': self.comparison_id,
            'experiment_ids': self.experiment_ids,
            'created_at': self.created_at.isoformat(),
            'winner_id': self.winner_id,
            'rankings': self.rankings,
            'metric_comparisons': self.metric_comparisons,
            'statistical_significance': self.statistical_significance,
            'notes': self.notes,
        }


class ExperimentRegistry:
    """
    Central registry for all AI experiments.
    
    Provides:
    1. Experiment registration and tracking
    2. Version control and lineage
    3. Result storage and comparison
    4. Promotion eligibility assessment
    5. Full audit trail
    """
    
    def __init__(self, storage_path: str = "experiment_registry"):
        """
        Initialize the experiment registry.
        
        Args:
            storage_path: Path for experiment storage
        """
        self._experiments: Dict[str, Experiment] = {}
        self._comparisons: Dict[str, ExperimentComparison] = {}
        
        # Indices
        self._by_status: Dict[ExperimentStatus, Set[str]] = {s: set() for s in ExperimentStatus}
        self._by_type: Dict[ExperimentType, Set[str]] = {t: set() for t in ExperimentType}
        self._by_agent: Dict[str, Set[str]] = {}
        self._by_tag: Dict[str, Set[str]] = {}
        
        # Callbacks
        self._status_callbacks: List[Callable] = []
        
        # Storage
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("ExperimentRegistry initialized")
    
    async def register_experiment(
        self,
        name: str,
        description: str,
        experiment_type: ExperimentType,
        category: ExperimentCategory,
        code: str,
        config: Dict[str, Any],
        created_by: str,
        parent_experiment_id: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Experiment:
        """
        Register a new experiment.
        
        Args:
            name: Experiment name
            description: Description
            experiment_type: Type of experiment
            category: Category
            code: Experiment code
            config: Configuration
            created_by: Agent ID
            parent_experiment_id: Parent experiment for versioning
            tags: Optional tags
            labels: Optional labels
        
        Returns:
            Registered Experiment
        """
        experiment_id = f"EXP-{uuid.uuid4().hex[:12]}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        
        # Determine version
        version = 1
        if parent_experiment_id and parent_experiment_id in self._experiments:
            parent = self._experiments[parent_experiment_id]
            version = parent.version + 1
        
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            experiment_type=experiment_type,
            category=category,
            code=code,
            code_hash=code_hash,
            config=config,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            version=version,
            parent_experiment_id=parent_experiment_id,
            tags=tags or set(),
            labels=labels or {},
        )
        
        self._experiments[experiment_id] = experiment
        
        # Update indices
        self._by_status[ExperimentStatus.PROPOSED].add(experiment_id)
        self._by_type[experiment_type].add(experiment_id)
        
        if created_by not in self._by_agent:
            self._by_agent[created_by] = set()
        self._by_agent[created_by].add(experiment_id)
        
        for tag in experiment.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = set()
            self._by_tag[tag].add(experiment_id)
        
        # Persist
        await self._persist_experiment(experiment)
        
        logger.info(f"Registered experiment: {experiment_id} - {name}")
        
        return experiment
    
    async def update_status(
        self,
        experiment_id: str,
        new_status: ExperimentStatus,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Update experiment status.
        
        Args:
            experiment_id: Experiment ID
            new_status: New status
            notes: Optional notes
        
        Returns:
            True if updated successfully
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return False
        
        old_status = experiment.status
        
        # Update indices
        self._by_status[old_status].discard(experiment_id)
        self._by_status[new_status].add(experiment_id)
        
        # Update experiment
        experiment.status = new_status
        experiment.updated_at = datetime.now(timezone.utc)
        
        if notes:
            experiment.safety_review_notes.append(f"[{new_status.name}] {notes}")
        
        # Set timestamps
        if new_status == ExperimentStatus.RUNNING:
            experiment.started_at = datetime.now(timezone.utc)
        elif new_status in [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED]:
            experiment.completed_at = datetime.now(timezone.utc)
        
        # Notify callbacks
        for callback in self._status_callbacks:
            try:
                await callback(experiment, old_status, new_status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
        
        # Persist
        await self._persist_experiment(experiment)
        
        logger.info(f"Experiment {experiment_id} status: {old_status.name} -> {new_status.name}")
        
        return True
    
    async def record_results(
        self,
        experiment_id: str,
        metrics: ExperimentMetrics,
        output: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record experiment results.
        
        Args:
            experiment_id: Experiment ID
            metrics: Experiment metrics
            output: Optional output data
        
        Returns:
            True if recorded successfully
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return False
        
        experiment.metrics = metrics
        experiment.output = output
        experiment.updated_at = datetime.now(timezone.utc)
        
        # Calculate promotion score
        experiment.promotion_score = metrics.get_score()
        
        # Check promotion eligibility
        experiment.promotion_eligible = self._check_promotion_eligibility(experiment)
        
        # Persist
        await self._persist_experiment(experiment)
        
        logger.info(f"Recorded results for {experiment_id}: score={experiment.promotion_score:.3f}")
        
        return True
    
    async def record_error(
        self,
        experiment_id: str,
        error: str,
    ) -> bool:
        """
        Record experiment error.
        
        Args:
            experiment_id: Experiment ID
            error: Error message
        
        Returns:
            True if recorded successfully
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return False
        
        experiment.error = error
        experiment.updated_at = datetime.now(timezone.utc)
        
        await self.update_status(experiment_id, ExperimentStatus.FAILED, error)
        
        return True
    
    def _check_promotion_eligibility(self, experiment: Experiment) -> bool:
        """Check if experiment is eligible for promotion."""
        if not experiment.metrics:
            return False
        
        if not experiment.safety_review_passed:
            return False
        
        metrics = experiment.metrics
        
        # Minimum requirements
        if metrics.sharpe_ratio is not None and metrics.sharpe_ratio < 1.0:
            return False
        
        if metrics.max_drawdown is not None and metrics.max_drawdown > 0.20:
            return False
        
        if metrics.p_value is not None and metrics.p_value > 0.05:
            return False
        
        # Score threshold
        if experiment.promotion_score < 0.6:
            return False
        
        return True
    
    async def compare_experiments(
        self,
        experiment_ids: List[str],
        notes: str = "",
    ) -> ExperimentComparison:
        """
        Compare multiple experiments.
        
        Args:
            experiment_ids: List of experiment IDs to compare
            notes: Optional notes
        
        Returns:
            ExperimentComparison
        """
        comparison_id = f"CMP-{uuid.uuid4().hex[:8]}"
        
        experiments = [self._experiments.get(eid) for eid in experiment_ids]
        experiments = [e for e in experiments if e and e.metrics]
        
        if len(experiments) < 2:
            raise ValueError("Need at least 2 experiments with metrics to compare")
        
        # Calculate rankings
        rankings = []
        for exp in experiments:
            score = exp.metrics.get_score() if exp.metrics else 0
            rankings.append((exp.experiment_id, score))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        winner_id = rankings[0][0] if rankings else None
        
        # Compare metrics
        metric_comparisons = {}
        metric_names = ['sharpe_ratio', 'win_rate', 'max_drawdown', 'accuracy']
        
        for metric in metric_names:
            metric_comparisons[metric] = {}
            for exp in experiments:
                if exp.metrics:
                    value = getattr(exp.metrics, metric, None)
                    if value is not None:
                        metric_comparisons[metric][exp.experiment_id] = value
        
        comparison = ExperimentComparison(
            comparison_id=comparison_id,
            experiment_ids=experiment_ids,
            created_at=datetime.now(timezone.utc),
            winner_id=winner_id,
            rankings=rankings,
            metric_comparisons=metric_comparisons,
            notes=notes,
        )
        
        self._comparisons[comparison_id] = comparison
        
        logger.info(f"Created comparison {comparison_id}: winner={winner_id}")
        
        return comparison
    
    async def get_lineage(self, experiment_id: str) -> List[Experiment]:
        """
        Get experiment lineage (version history).
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            List of experiments in lineage (oldest first)
        """
        lineage = []
        current_id = experiment_id
        
        while current_id:
            experiment = self._experiments.get(current_id)
            if not experiment:
                break
            lineage.append(experiment)
            current_id = experiment.parent_experiment_id
        
        return list(reversed(lineage))
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self._experiments.get(experiment_id)
    
    def get_experiments_by_status(self, status: ExperimentStatus) -> List[Experiment]:
        """Get experiments by status."""
        return [self._experiments[eid] for eid in self._by_status.get(status, set())]
    
    def get_experiments_by_type(self, experiment_type: ExperimentType) -> List[Experiment]:
        """Get experiments by type."""
        return [self._experiments[eid] for eid in self._by_type.get(experiment_type, set())]
    
    def get_experiments_by_agent(self, agent_id: str) -> List[Experiment]:
        """Get experiments by agent."""
        return [self._experiments[eid] for eid in self._by_agent.get(agent_id, set())]
    
    def get_experiments_by_tag(self, tag: str) -> List[Experiment]:
        """Get experiments by tag."""
        return [self._experiments[eid] for eid in self._by_tag.get(tag, set())]
    
    def get_promotion_candidates(self) -> List[Experiment]:
        """Get experiments eligible for promotion."""
        return [
            exp for exp in self._experiments.values()
            if exp.promotion_eligible and exp.status == ExperimentStatus.COMPLETED
        ]
    
    def search_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        experiment_type: Optional[ExperimentType] = None,
        category: Optional[ExperimentCategory] = None,
        agent_id: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        min_score: Optional[float] = None,
        created_after: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Experiment]:
        """
        Search experiments with filters.
        
        Args:
            status: Filter by status
            experiment_type: Filter by type
            category: Filter by category
            agent_id: Filter by agent
            tags: Filter by tags (any match)
            min_score: Minimum promotion score
            created_after: Created after date
            limit: Maximum results
        
        Returns:
            List of matching experiments
        """
        results = []
        
        for experiment in self._experiments.values():
            if status and experiment.status != status:
                continue
            if experiment_type and experiment.experiment_type != experiment_type:
                continue
            if category and experiment.category != category:
                continue
            if agent_id and experiment.created_by != agent_id:
                continue
            if tags and not tags.intersection(experiment.tags):
                continue
            if min_score is not None and experiment.promotion_score < min_score:
                continue
            if created_after and experiment.created_at < created_after:
                continue
            
            results.append(experiment)
            
            if len(results) >= limit:
                break
        
        return results
    
    def register_status_callback(self, callback: Callable):
        """Register callback for status changes."""
        self._status_callbacks.append(callback)
    
    async def _persist_experiment(self, experiment: Experiment):
        """Persist experiment to disk."""
        try:
            exp_file = self._storage_path / f"{experiment.experiment_id}.json"
            
            data = experiment.to_dict()
            data['code'] = experiment.code  # Include code in persistence
            
            with open(exp_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist experiment: {e}")
    
    async def load_experiments(self):
        """Load experiments from disk."""
        for exp_file in self._storage_path.glob("EXP-*.json"):
            try:
                with open(exp_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct experiment
                experiment = Experiment(
                    experiment_id=data['experiment_id'],
                    name=data['name'],
                    description=data['description'],
                    experiment_type=ExperimentType(data['experiment_type']),
                    category=ExperimentCategory(data['category']),
                    code=data.get('code', ''),
                    code_hash=data['code_hash'],
                    config=data['config'],
                    created_by=data['created_by'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at']),
                    status=ExperimentStatus[data['status']],
                    version=data['version'],
                    parent_experiment_id=data.get('parent_experiment_id'),
                    tags=set(data.get('tags', [])),
                    labels=data.get('labels', {}),
                )
                
                self._experiments[experiment.experiment_id] = experiment
                
                # Update indices
                self._by_status[experiment.status].add(experiment.experiment_id)
                self._by_type[experiment.experiment_type].add(experiment.experiment_id)
                
            except Exception as e:
                logger.error(f"Failed to load experiment from {exp_file}: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        status_counts = {s.name: len(ids) for s, ids in self._by_status.items()}
        type_counts = {t.value: len(ids) for t, ids in self._by_type.items()}
        
        completed = self.get_experiments_by_status(ExperimentStatus.COMPLETED)
        avg_score = (
            sum(e.promotion_score for e in completed) / len(completed)
            if completed else 0
        )
        
        return {
            'total_experiments': len(self._experiments),
            'by_status': status_counts,
            'by_type': type_counts,
            'total_agents': len(self._by_agent),
            'total_tags': len(self._by_tag),
            'promotion_candidates': len(self.get_promotion_candidates()),
            'average_score': avg_score,
            'total_comparisons': len(self._comparisons),
        }
