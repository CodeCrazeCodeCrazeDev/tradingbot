"""
Experiment Registry
===================

Tracks all autonomous AI experiments with full audit trail.
Provides:
1. Experiment lifecycle management
2. Version control for experiments
3. Reproducibility tracking
4. Performance metrics
5. Approval workflow
6. Rollback capabilities

CRITICAL: All experiments MUST be registered before execution.
"""

import json
import hashlib
import threading
from typing import Dict, Any, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
import logging
import uuid
import copy

logger = logging.getLogger(__name__)


class ExperimentPhase(Enum):
    """Phases of an experiment lifecycle."""
    PROPOSED = auto()      # Initial proposal
    APPROVED = auto()      # Approved for execution
    PREPARING = auto()     # Setting up environment
    RUNNING = auto()       # Currently executing
    VALIDATING = auto()    # Validating results
    COMPLETED = auto()     # Successfully completed
    FAILED = auto()        # Failed during execution
    REJECTED = auto()      # Rejected during approval
    ROLLED_BACK = auto()   # Rolled back after completion
    ARCHIVED = auto()      # Archived for reference


class ExperimentType(Enum):
    """Types of experiments."""
    STRATEGY_EVOLUTION = auto()
    MODEL_TRAINING = auto()
    FEATURE_DISCOVERY = auto()
    PARAMETER_OPTIMIZATION = auto()
    ARCHITECTURE_SEARCH = auto()
    CODE_GENERATION = auto()
    INTEGRATION_TEST = auto()
    PERFORMANCE_TEST = auto()


class ExperimentOutcome(Enum):
    """Possible outcomes of an experiment."""
    SUCCESS = auto()
    PARTIAL_SUCCESS = auto()
    FAILURE = auto()
    INCONCLUSIVE = auto()
    TIMEOUT = auto()
    ERROR = auto()
    CANCELLED = auto()


@dataclass
class ExperimentHypothesis:
    """Hypothesis being tested by experiment."""
    hypothesis_id: str
    description: str
    expected_outcome: str
    success_criteria: Dict[str, float]
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hypothesis_id': self.hypothesis_id,
            'description': self.description,
            'expected_outcome': self.expected_outcome,
            'success_criteria': self.success_criteria,
            'confidence': self.confidence,
        }


@dataclass
class ExperimentMetrics:
    """Metrics collected during experiment."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cpu_time_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    iterations: int = 0
    samples_processed: int = 0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time else 0
            ),
            'cpu_time_seconds': self.cpu_time_seconds,
            'memory_peak_mb': self.memory_peak_mb,
            'iterations': self.iterations,
            'samples_processed': self.samples_processed,
            'custom_metrics': self.custom_metrics,
        }


@dataclass
class ExperimentArtifact:
    """Artifact produced by experiment."""
    artifact_id: str
    artifact_type: str  # 'model', 'code', 'data', 'report', 'config'
    path: str
    checksum: str
    size_bytes: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'artifact_id': self.artifact_id,
            'artifact_type': self.artifact_type,
            'path': self.path,
            'checksum': self.checksum,
            'size_bytes': self.size_bytes,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class Experiment:
    """A registered experiment."""
    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    hypothesis: ExperimentHypothesis
    
    # Lifecycle
    phase: ExperimentPhase = ExperimentPhase.PROPOSED
    outcome: Optional[ExperimentOutcome] = None
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "autonomous_ai"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    metrics: ExperimentMetrics = field(default_factory=ExperimentMetrics)
    artifacts: List[ExperimentArtifact] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    
    # Audit
    version: int = 1
    parent_experiment_id: Optional[str] = None
    child_experiment_ids: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    notes: List[str] = field(default_factory=list)
    
    # Safety
    sandbox_id: Optional[str] = None
    budget_allocation_id: Optional[str] = None
    safety_scan_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'experiment_type': self.experiment_type.name,
            'hypothesis': self.hypothesis.to_dict(),
            'phase': self.phase.name,
            'outcome': self.outcome.name if self.outcome else None,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'config': self.config,
            'parameters': self.parameters,
            'metrics': self.metrics.to_dict(),
            'artifacts': [a.to_dict() for a in self.artifacts],
            'results': self.results,
            'version': self.version,
            'parent_experiment_id': self.parent_experiment_id,
            'child_experiment_ids': self.child_experiment_ids,
            'tags': list(self.tags),
            'notes': self.notes,
        }


@dataclass
class ExperimentTransition:
    """Record of experiment phase transition."""
    transition_id: str
    experiment_id: str
    from_phase: ExperimentPhase
    to_phase: ExperimentPhase
    timestamp: datetime = field(default_factory=datetime.utcnow)
    actor: str = "system"
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'transition_id': self.transition_id,
            'experiment_id': self.experiment_id,
            'from_phase': self.from_phase.name,
            'to_phase': self.to_phase.name,
            'timestamp': self.timestamp.isoformat(),
            'actor': self.actor,
            'reason': self.reason,
        }


class ExperimentRegistry:
    """
    Central registry for all autonomous AI experiments.
    
    Provides complete lifecycle management, audit trail,
    and reproducibility tracking for experiments.
    """
    
    # Valid phase transitions
    VALID_TRANSITIONS = {
        ExperimentPhase.PROPOSED: {ExperimentPhase.APPROVED, ExperimentPhase.REJECTED},
        ExperimentPhase.APPROVED: {ExperimentPhase.PREPARING, ExperimentPhase.REJECTED},
        ExperimentPhase.PREPARING: {ExperimentPhase.RUNNING, ExperimentPhase.FAILED},
        ExperimentPhase.RUNNING: {ExperimentPhase.VALIDATING, ExperimentPhase.FAILED},
        ExperimentPhase.VALIDATING: {ExperimentPhase.COMPLETED, ExperimentPhase.FAILED},
        ExperimentPhase.COMPLETED: {ExperimentPhase.ROLLED_BACK, ExperimentPhase.ARCHIVED},
        ExperimentPhase.FAILED: {ExperimentPhase.ARCHIVED},
        ExperimentPhase.REJECTED: {ExperimentPhase.ARCHIVED},
        ExperimentPhase.ROLLED_BACK: {ExperimentPhase.ARCHIVED},
        ExperimentPhase.ARCHIVED: set(),
    }
    
    def __init__(self, 
                 storage_path: Optional[Path] = None,
                 max_concurrent_experiments: int = 5,
                 auto_archive_days: int = 30):
        """
        Initialize experiment registry.
        
        Args:
            storage_path: Path for persistent storage
            max_concurrent_experiments: Maximum concurrent running experiments
            auto_archive_days: Days after which to auto-archive completed experiments
        """
        self.storage_path = storage_path or Path("experiment_registry")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.max_concurrent_experiments = max_concurrent_experiments
        self.auto_archive_days = auto_archive_days
        
        self.experiments: Dict[str, Experiment] = {}
        self.transitions: List[ExperimentTransition] = []
        
        self._lock = threading.RLock()
        self._transition_counter = 0
        
        # Callbacks
        self._phase_callbacks: Dict[ExperimentPhase, List[Callable]] = {
            phase: [] for phase in ExperimentPhase
        }
        
        # Load existing experiments
        self._load_experiments()
        
        logger.info(f"ExperimentRegistry initialized with {len(self.experiments)} experiments")
    
    def register_experiment(self,
                            name: str,
                            description: str,
                            experiment_type: ExperimentType,
                            hypothesis: ExperimentHypothesis,
                            config: Optional[Dict[str, Any]] = None,
                            parameters: Optional[Dict[str, Any]] = None,
                            parent_id: Optional[str] = None,
                            tags: Optional[Set[str]] = None) -> str:
        """
        Register a new experiment.
        
        Args:
            name: Experiment name
            description: Detailed description
            experiment_type: Type of experiment
            hypothesis: Hypothesis being tested
            config: Experiment configuration
            parameters: Experiment parameters
            parent_id: Parent experiment ID (for derived experiments)
            tags: Tags for categorization
            
        Returns:
            Experiment ID
        """
        with self._lock:
            experiment_id = f"exp_{uuid.uuid4().hex[:12]}"
            
            experiment = Experiment(
                experiment_id=experiment_id,
                name=name,
                description=description,
                experiment_type=experiment_type,
                hypothesis=hypothesis,
                config=config or {},
                parameters=parameters or {},
                parent_experiment_id=parent_id,
                tags=tags or set(),
            )
            
            # Link to parent
            if parent_id and parent_id in self.experiments:
                self.experiments[parent_id].child_experiment_ids.append(experiment_id)
            
            self.experiments[experiment_id] = experiment
            
            # Record transition
            self._record_transition(
                experiment_id,
                ExperimentPhase.PROPOSED,
                ExperimentPhase.PROPOSED,
                "Experiment registered"
            )
            
            self._save_experiment(experiment)
            
            logger.info(f"Experiment registered: {experiment_id} - {name}")
            
            return experiment_id
    
    def approve_experiment(self, 
                           experiment_id: str, 
                           approver: str,
                           notes: Optional[str] = None) -> bool:
        """
        Approve an experiment for execution.
        
        Args:
            experiment_id: ID of experiment to approve
            approver: Who is approving
            notes: Optional approval notes
            
        Returns:
            True if approved successfully
        """
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                logger.error(f"Unknown experiment: {experiment_id}")
                return False
            
            if experiment.phase != ExperimentPhase.PROPOSED:
                logger.error(f"Cannot approve experiment in phase {experiment.phase.name}")
                return False
            
            # Check concurrent limit
            running_count = sum(
                1 for e in self.experiments.values()
                if e.phase in {ExperimentPhase.PREPARING, ExperimentPhase.RUNNING, ExperimentPhase.VALIDATING}
            )
            
            if running_count >= self.max_concurrent_experiments:
                logger.warning(f"Max concurrent experiments ({self.max_concurrent_experiments}) reached")
                return False
            
            # Transition to approved
            self._transition_phase(
                experiment_id,
                ExperimentPhase.APPROVED,
                approver,
                notes or "Approved for execution"
            )
            
            experiment.approved_by = approver
            experiment.approved_at = datetime.utcnow()
            
            if notes:
                experiment.notes.append(f"[Approval] {notes}")
            
            self._save_experiment(experiment)
            
            return True
    
    def reject_experiment(self,
                          experiment_id: str,
                          rejector: str,
                          reason: str) -> bool:
        """
        Reject an experiment.
        
        Args:
            experiment_id: ID of experiment to reject
            rejector: Who is rejecting
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            if experiment.phase not in {ExperimentPhase.PROPOSED, ExperimentPhase.APPROVED}:
                return False
            
            self._transition_phase(
                experiment_id,
                ExperimentPhase.REJECTED,
                rejector,
                reason
            )
            
            experiment.notes.append(f"[Rejection] {reason}")
            experiment.outcome = ExperimentOutcome.CANCELLED
            
            self._save_experiment(experiment)
            
            return True
    
    def start_experiment(self, experiment_id: str) -> bool:
        """
        Start experiment execution.
        
        Args:
            experiment_id: ID of experiment to start
            
        Returns:
            True if started successfully
        """
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            if experiment.phase != ExperimentPhase.APPROVED:
                return False
            
            # Transition to preparing
            self._transition_phase(
                experiment_id,
                ExperimentPhase.PREPARING,
                "system",
                "Starting experiment preparation"
            )
            
            experiment.metrics.start_time = datetime.utcnow()
            
            self._save_experiment(experiment)
            
            return True
    
    def set_running(self, experiment_id: str) -> bool:
        """Mark experiment as running."""
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            if experiment.phase != ExperimentPhase.PREPARING:
                return False
            
            self._transition_phase(
                experiment_id,
                ExperimentPhase.RUNNING,
                "system",
                "Experiment execution started"
            )
            
            self._save_experiment(experiment)
            
            return True
    
    def update_metrics(self, 
                       experiment_id: str,
                       metrics: Dict[str, Any]) -> bool:
        """
        Update experiment metrics.
        
        Args:
            experiment_id: ID of experiment
            metrics: Metrics to update
            
        Returns:
            True if updated successfully
        """
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            if 'cpu_time_seconds' in metrics:
                experiment.metrics.cpu_time_seconds = metrics['cpu_time_seconds']
            if 'memory_peak_mb' in metrics:
                experiment.metrics.memory_peak_mb = metrics['memory_peak_mb']
            if 'iterations' in metrics:
                experiment.metrics.iterations = metrics['iterations']
            if 'samples_processed' in metrics:
                experiment.metrics.samples_processed = metrics['samples_processed']
            if 'custom_metrics' in metrics:
                experiment.metrics.custom_metrics.update(metrics['custom_metrics'])
            
            self._save_experiment(experiment)
            
            return True
    
    def add_artifact(self,
                     experiment_id: str,
                     artifact_type: str,
                     path: str,
                     metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Add an artifact to experiment.
        
        Args:
            experiment_id: ID of experiment
            artifact_type: Type of artifact
            path: Path to artifact
            metadata: Optional metadata
            
        Returns:
            Artifact ID or None
        """
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return None
            
            # Calculate checksum
            path_obj = Path(path)
            if path_obj.exists():
                with open(path_obj, 'rb') as f:
                    checksum = hashlib.sha256(f.read()).hexdigest()
                size_bytes = path_obj.stat().st_size
            else:
                checksum = "NOT_FOUND"
                size_bytes = 0
            
            artifact_id = f"art_{uuid.uuid4().hex[:8]}"
            
            artifact = ExperimentArtifact(
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                path=path,
                checksum=checksum,
                size_bytes=size_bytes,
                metadata=metadata or {},
            )
            
            experiment.artifacts.append(artifact)
            
            self._save_experiment(experiment)
            
            return artifact_id
    
    def complete_experiment(self,
                            experiment_id: str,
                            outcome: ExperimentOutcome,
                            results: Dict[str, Any]) -> bool:
        """
        Complete an experiment.
        
        Args:
            experiment_id: ID of experiment
            outcome: Experiment outcome
            results: Experiment results
            
        Returns:
            True if completed successfully
        """
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            if experiment.phase not in {ExperimentPhase.RUNNING, ExperimentPhase.VALIDATING}:
                return False
            
            # Transition through validating if needed
            if experiment.phase == ExperimentPhase.RUNNING:
                self._transition_phase(
                    experiment_id,
                    ExperimentPhase.VALIDATING,
                    "system",
                    "Validating results"
                )
            
            # Complete
            self._transition_phase(
                experiment_id,
                ExperimentPhase.COMPLETED,
                "system",
                f"Completed with outcome: {outcome.name}"
            )
            
            experiment.outcome = outcome
            experiment.results = results
            experiment.metrics.end_time = datetime.utcnow()
            
            # Check hypothesis
            self._evaluate_hypothesis(experiment)
            
            self._save_experiment(experiment)
            
            # Trigger callbacks
            self._trigger_callbacks(ExperimentPhase.COMPLETED, experiment)
            
            return True
    
    def fail_experiment(self,
                        experiment_id: str,
                        error: str) -> bool:
        """
        Mark experiment as failed.
        
        Args:
            experiment_id: ID of experiment
            error: Error description
            
        Returns:
            True if marked successfully
        """
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            self._transition_phase(
                experiment_id,
                ExperimentPhase.FAILED,
                "system",
                error
            )
            
            experiment.outcome = ExperimentOutcome.ERROR
            experiment.metrics.end_time = datetime.utcnow()
            experiment.notes.append(f"[Error] {error}")
            
            self._save_experiment(experiment)
            
            return True
    
    def rollback_experiment(self,
                            experiment_id: str,
                            reason: str) -> bool:
        """
        Rollback a completed experiment.
        
        Args:
            experiment_id: ID of experiment
            reason: Reason for rollback
            
        Returns:
            True if rolled back successfully
        """
        with self._lock:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            if experiment.phase != ExperimentPhase.COMPLETED:
                return False
            
            self._transition_phase(
                experiment_id,
                ExperimentPhase.ROLLED_BACK,
                "system",
                reason
            )
            
            experiment.notes.append(f"[Rollback] {reason}")
            
            self._save_experiment(experiment)
            
            return True
    
    def _transition_phase(self,
                          experiment_id: str,
                          to_phase: ExperimentPhase,
                          actor: str,
                          reason: str):
        """Internal method to transition experiment phase."""
        experiment = self.experiments[experiment_id]
        from_phase = experiment.phase
        
        # Validate transition
        if to_phase not in self.VALID_TRANSITIONS.get(from_phase, set()):
            if from_phase != to_phase:  # Allow same-phase for initial registration
                raise ValueError(
                    f"Invalid transition: {from_phase.name} -> {to_phase.name}"
                )
        
        experiment.phase = to_phase
        experiment.version += 1
        
        self._record_transition(experiment_id, from_phase, to_phase, reason, actor)
        
        logger.info(
            f"Experiment {experiment_id}: {from_phase.name} -> {to_phase.name} ({reason})"
        )
    
    def _record_transition(self,
                           experiment_id: str,
                           from_phase: ExperimentPhase,
                           to_phase: ExperimentPhase,
                           reason: str,
                           actor: str = "system"):
        """Record a phase transition."""
        self._transition_counter += 1
        
        transition = ExperimentTransition(
            transition_id=f"trans_{self._transition_counter:08d}",
            experiment_id=experiment_id,
            from_phase=from_phase,
            to_phase=to_phase,
            actor=actor,
            reason=reason,
        )
        
        self.transitions.append(transition)
        
        # Keep transitions bounded
        if len(self.transitions) > 10000:
            self.transitions = self.transitions[-5000:]
    
    def _evaluate_hypothesis(self, experiment: Experiment):
        """Evaluate if hypothesis was confirmed."""
        hypothesis = experiment.hypothesis
        results = experiment.results
        
        criteria_met = 0
        total_criteria = len(hypothesis.success_criteria)
        
        for metric, threshold in hypothesis.success_criteria.items():
            if metric in results:
                if results[metric] >= threshold:
                    criteria_met += 1
        
        if total_criteria > 0:
            success_rate = criteria_met / total_criteria
            hypothesis.confidence = success_rate
            
            if success_rate >= 0.8:
                experiment.notes.append("[Hypothesis] CONFIRMED")
            elif success_rate >= 0.5:
                experiment.notes.append("[Hypothesis] PARTIALLY CONFIRMED")
            else:
                experiment.notes.append("[Hypothesis] NOT CONFIRMED")
    
    def _trigger_callbacks(self, phase: ExperimentPhase, experiment: Experiment):
        """Trigger registered callbacks for phase."""
        for callback in self._phase_callbacks.get(phase, []):
            try:
                callback(experiment)
            except Exception as e:
                logger.error(f"Callback error for {phase.name}: {e}")
    
    def register_callback(self, 
                          phase: ExperimentPhase, 
                          callback: Callable[[Experiment], None]):
        """Register callback for phase transitions."""
        self._phase_callbacks[phase].append(callback)
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self.experiments.get(experiment_id)
    
    def get_experiments_by_phase(self, phase: ExperimentPhase) -> List[Experiment]:
        """Get all experiments in a phase."""
        return [e for e in self.experiments.values() if e.phase == phase]
    
    def get_experiments_by_type(self, exp_type: ExperimentType) -> List[Experiment]:
        """Get all experiments of a type."""
        return [e for e in self.experiments.values() if e.experiment_type == exp_type]
    
    def get_running_experiments(self) -> List[Experiment]:
        """Get all currently running experiments."""
        running_phases = {
            ExperimentPhase.PREPARING,
            ExperimentPhase.RUNNING,
            ExperimentPhase.VALIDATING,
        }
        return [e for e in self.experiments.values() if e.phase in running_phases]
    
    def get_experiment_history(self, experiment_id: str) -> List[ExperimentTransition]:
        """Get transition history for an experiment."""
        return [t for t in self.transitions if t.experiment_id == experiment_id]
    
    def search_experiments(self,
                           name_contains: Optional[str] = None,
                           experiment_type: Optional[ExperimentType] = None,
                           phase: Optional[ExperimentPhase] = None,
                           outcome: Optional[ExperimentOutcome] = None,
                           tags: Optional[Set[str]] = None,
                           created_after: Optional[datetime] = None,
                           created_before: Optional[datetime] = None) -> List[Experiment]:
        """Search experiments with filters."""
        results = list(self.experiments.values())
        
        if name_contains:
            results = [e for e in results if name_contains.lower() in e.name.lower()]
        
        if experiment_type:
            results = [e for e in results if e.experiment_type == experiment_type]
        
        if phase:
            results = [e for e in results if e.phase == phase]
        
        if outcome:
            results = [e for e in results if e.outcome == outcome]
        
        if tags:
            results = [e for e in results if tags.issubset(e.tags)]
        
        if created_after:
            results = [e for e in results if e.created_at >= created_after]
        
        if created_before:
            results = [e for e in results if e.created_at <= created_before]
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        experiments = list(self.experiments.values())
        
        by_phase = {}
        for phase in ExperimentPhase:
            by_phase[phase.name] = sum(1 for e in experiments if e.phase == phase)
        
        by_type = {}
        for exp_type in ExperimentType:
            by_type[exp_type.name] = sum(1 for e in experiments if e.experiment_type == exp_type)
        
        by_outcome = {}
        for outcome in ExperimentOutcome:
            by_outcome[outcome.name] = sum(
                1 for e in experiments if e.outcome == outcome
            )
        
        completed = [e for e in experiments if e.phase == ExperimentPhase.COMPLETED]
        success_rate = (
            sum(1 for e in completed if e.outcome == ExperimentOutcome.SUCCESS) / len(completed)
            if completed else 0
        )
        
        return {
            'total_experiments': len(experiments),
            'by_phase': by_phase,
            'by_type': by_type,
            'by_outcome': by_outcome,
            'success_rate': success_rate,
            'total_transitions': len(self.transitions),
            'running_experiments': len(self.get_running_experiments()),
        }
    
    def _save_experiment(self, experiment: Experiment):
        """Save experiment to storage."""
        try:
            file_path = self.storage_path / f"{experiment.experiment_id}.json"
            with open(file_path, 'w') as f:
                json.dump(experiment.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save experiment {experiment.experiment_id}: {e}")
    
    def _load_experiments(self):
        """Load experiments from storage."""
        try:
            for file_path in self.storage_path.glob("exp_*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Reconstruct experiment (simplified)
                    experiment_id = data['experiment_id']
                    
                    hypothesis = ExperimentHypothesis(
                        hypothesis_id=data['hypothesis']['hypothesis_id'],
                        description=data['hypothesis']['description'],
                        expected_outcome=data['hypothesis']['expected_outcome'],
                        success_criteria=data['hypothesis']['success_criteria'],
                        confidence=data['hypothesis'].get('confidence', 0.5),
                    )
                    
                    experiment = Experiment(
                        experiment_id=experiment_id,
                        name=data['name'],
                        description=data['description'],
                        experiment_type=ExperimentType[data['experiment_type']],
                        hypothesis=hypothesis,
                        phase=ExperimentPhase[data['phase']],
                        outcome=ExperimentOutcome[data['outcome']] if data.get('outcome') else None,
                        config=data.get('config', {}),
                        parameters=data.get('parameters', {}),
                        results=data.get('results', {}),
                        version=data.get('version', 1),
                        tags=set(data.get('tags', [])),
                        notes=data.get('notes', []),
                    )
                    
                    self.experiments[experiment_id] = experiment
                    
                except Exception as e:
                    logger.error(f"Failed to load experiment from {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load experiments: {e}")
    
    def archive_old_experiments(self):
        """Archive experiments older than auto_archive_days."""
        cutoff = datetime.utcnow() - timedelta(days=self.auto_archive_days)
        
        archived = 0
        for experiment in self.experiments.values():
            if experiment.phase in {ExperimentPhase.COMPLETED, ExperimentPhase.FAILED, 
                                    ExperimentPhase.REJECTED, ExperimentPhase.ROLLED_BACK}:
                if experiment.created_at < cutoff:
                    experiment.phase = ExperimentPhase.ARCHIVED
                    self._save_experiment(experiment)
                    archived += 1
        
        if archived > 0:
            logger.info(f"Archived {archived} old experiments")
        
        return archived
