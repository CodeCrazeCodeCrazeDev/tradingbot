"""
Experiment Infrastructure - Logging, Versioning, Tracking
==========================================================

CRITICAL: Rule 3 - All experiments must be logged

Provides:
- Experiment tracking
- Version control
- Metrics logging
- Reproducibility
- Audit trail
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Experiment:
    """An experiment run"""
    experiment_id: str
    name: str
    description: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Artifacts
    artifacts: Dict[str, str] = field(default_factory=dict)
    
    # Status
    status: str = "running"  # running, completed, failed
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'config': self.config,
            'metrics': self.metrics,
            'artifacts': self.artifacts,
            'status': self.status,
            'tags': self.tags,
            'notes': self.notes,
        }


@dataclass
class ExperimentVersion:
    """A version of code/config"""
    version_id: str
    timestamp: datetime
    version_number: str
    changes: List[str]
    code_hash: str
    config_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'version_id': self.version_id,
            'timestamp': self.timestamp.isoformat(),
            'version_number': self.version_number,
            'changes': self.changes,
            'code_hash': self.code_hash,
            'config_hash': self.config_hash,
        }


class ExperimentInfrastructure:
    """
    Experiment Infrastructure
    
    ENFORCES RULE 3: All experiments must be logged
    
    Provides comprehensive experiment tracking, versioning, and reproducibility.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.infra_id = f"INFRA-{uuid.uuid4().hex[:8]}"
        
        # Storage
        self.storage_path = Path(storage_path) if storage_path else Path("./experiment_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Experiments
        self.experiments: Dict[str, Experiment] = {}
        self.experiment_history: List[Experiment] = []
        
        # Versions
        self.versions: List[ExperimentVersion] = []
        self.current_version = "1.0.0"
        
        # Metrics
        self.total_experiments = 0
        self.completed_experiments = 0
        self.failed_experiments = 0
        
        logger.info(f"ExperimentInfrastructure initialized: {self.infra_id}")
    
    def create_experiment(
        self,
        name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Experiment:
        """
        Create a new experiment.
        
        ENFORCES RULE 3: All experiments must be logged.
        """
        experiment = Experiment(
            experiment_id=f"EXP-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            started_at=datetime.now(timezone.utc),
            config=config or {},
            tags=tags or [],
        )
        
        self.experiments[experiment.experiment_id] = experiment
        self.total_experiments += 1
        
        # Save to disk
        self._save_experiment(experiment)
        
        logger.info(f"Created experiment: {experiment.experiment_id} - {name}")
        
        return experiment
    
    def log_metric(
        self,
        experiment_id: str,
        metric_name: str,
        metric_value: Any,
        step: Optional[int] = None,
    ):
        """Log a metric for an experiment"""
        if experiment_id not in self.experiments:
            logger.warning(f"Experiment not found: {experiment_id}")
            return
        
        experiment = self.experiments[experiment_id]
        
        if metric_name not in experiment.metrics:
            experiment.metrics[metric_name] = []
        
        metric_entry = {
            'value': metric_value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        if step is not None:
            metric_entry['step'] = step
        
        experiment.metrics[metric_name].append(metric_entry)
        
        # Save to disk
        self._save_experiment(experiment)
    
    def log_artifact(
        self,
        experiment_id: str,
        artifact_name: str,
        artifact_data: Any,
    ):
        """Log an artifact (model, plot, etc.)"""
        if experiment_id not in self.experiments:
            logger.warning(f"Experiment not found: {experiment_id}")
            return
        
        experiment = self.experiments[experiment_id]
        
        # Save artifact to disk
        artifact_path = self.storage_path / experiment_id / f"{artifact_name}.json"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(artifact_path, 'w') as f:
            json.dump(artifact_data, f, indent=2)
        
        experiment.artifacts[artifact_name] = str(artifact_path)
        
        # Save experiment
        self._save_experiment(experiment)
    
    def complete_experiment(
        self,
        experiment_id: str,
        status: str = "completed",
        notes: str = "",
    ):
        """Mark an experiment as complete"""
        if experiment_id not in self.experiments:
            logger.warning(f"Experiment not found: {experiment_id}")
            return
        
        experiment = self.experiments[experiment_id]
        experiment.ended_at = datetime.now(timezone.utc)
        experiment.status = status
        experiment.notes = notes
        
        if status == "completed":
            self.completed_experiments += 1
        elif status == "failed":
            self.failed_experiments += 1
        
        # Move to history
        self.experiment_history.append(experiment)
        
        # Save to disk
        self._save_experiment(experiment)
        
        logger.info(f"Completed experiment: {experiment_id} - {status}")
    
    def create_version(
        self,
        version_number: str,
        changes: List[str],
        code_hash: str = "",
        config_hash: str = "",
    ) -> ExperimentVersion:
        """Create a new version"""
        version = ExperimentVersion(
            version_id=f"VER-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            version_number=version_number,
            changes=changes,
            code_hash=code_hash or uuid.uuid4().hex,
            config_hash=config_hash or uuid.uuid4().hex,
        )
        
        self.versions.append(version)
        self.current_version = version_number
        
        # Save version
        version_path = self.storage_path / "versions" / f"{version_number}.json"
        version_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(version_path, 'w') as f:
            json.dump(version.to_dict(), f, indent=2)
        
        logger.info(f"Created version: {version_number}")
        
        return version
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get an experiment by ID"""
        return self.experiments.get(experiment_id)
    
    def list_experiments(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Experiment]:
        """List experiments with optional filters"""
        experiments = list(self.experiments.values()) + self.experiment_history
        
        if status:
            experiments = [e for e in experiments if e.status == status]
        
        if tags:
            experiments = [e for e in experiments if any(t in e.tags for t in tags)]
        
        return experiments
    
    def get_experiment_metrics(
        self,
        experiment_id: str,
        metric_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get metrics for an experiment"""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return {}
        
        if metric_name:
            return {metric_name: experiment.metrics.get(metric_name, [])}
        
        return experiment.metrics
    
    def compare_experiments(
        self,
        experiment_ids: List[str],
        metric_name: str,
    ) -> Dict[str, Any]:
        """Compare metrics across experiments"""
        comparison = {}
        
        for exp_id in experiment_ids:
            experiment = self.get_experiment(exp_id)
            if experiment and metric_name in experiment.metrics:
                metric_values = [m['value'] for m in experiment.metrics[metric_name]]
                comparison[exp_id] = {
                    'name': experiment.name,
                    'values': metric_values,
                    'latest': metric_values[-1] if metric_values else None,
                    'mean': sum(metric_values) / len(metric_values) if metric_values else None,
                }
        
        return comparison
    
    def _save_experiment(self, experiment: Experiment):
        """Save experiment to disk"""
        exp_path = self.storage_path / f"{experiment.experiment_id}.json"
        
        with open(exp_path, 'w') as f:
            json.dump(experiment.to_dict(), f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get infrastructure status"""
        return {
            'infra_id': self.infra_id,
            'storage_path': str(self.storage_path),
            'total_experiments': self.total_experiments,
            'completed_experiments': self.completed_experiments,
            'failed_experiments': self.failed_experiments,
            'active_experiments': len(self.experiments),
            'current_version': self.current_version,
            'total_versions': len(self.versions),
        }
