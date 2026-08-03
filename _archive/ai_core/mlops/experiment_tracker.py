"""
Experiment Tracker for ML experiments and hyperparameter tuning
"""

import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class Experiment:
    """Experiment metadata and results."""
    experiment_id: str
    name: str
    description: str
    created_at: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    status: str = 'running'  # 'running', 'completed', 'failed'
    tags: List[str] = field(default_factory=list)


class ExperimentTracker:
    """
    Track ML experiments, hyperparameters, and results.
    
    Features:
    - Experiment logging and tracking
    - Hyperparameter recording
    - Metrics tracking over time
    - Artifact management
    - Experiment comparison
    """
    
    def __init__(self, experiments_path: str = "experiments"):
        self.experiments_path = Path(experiments_path)
        self.experiments_path.mkdir(parents=True, exist_ok=True)
        self.experiments_file = self.experiments_path / "experiments.json"
        self.experiments: Dict[str, Experiment] = {}
        self._load_experiments()
        logger.info(f"ExperimentTracker initialized at {self.experiments_path}")
    
    def _load_experiments(self):
        """Load experiments from disk."""
        if self.experiments_file.exists():
            try:
                with open(self.experiments_file, 'r') as f:
                    data = json.load(f)
                    self.experiments = {
                        k: Experiment(**v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.experiments)} experiments")
            except Exception as e:
                logger.error(f"Error loading experiments: {e}")
    
    def _save_experiments(self):
        """Save experiments to disk."""
        try:
            data = {k: asdict(v) for k, v in self.experiments.items()}
            with open(self.experiments_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving experiments: {e}")
    
    def create_experiment(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Create a new experiment.
        
        Args:
            name: Experiment name
            description: Experiment description
            parameters: Hyperparameters and configuration
            tags: Optional tags for categorization
        
        Returns:
            Experiment ID
        """
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            parameters=parameters,
            tags=tags or []
        )
        
        self.experiments[experiment_id] = experiment
        self._save_experiments()
        
        logger.info(f"Created experiment {experiment_id}: {name}")
        return experiment_id
    
    def log_metric(self, experiment_id: str, metric_name: str, value: float):
        """Log a metric for an experiment."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        self.experiments[experiment_id].metrics[metric_name] = value
        self._save_experiments()
        logger.debug(f"Logged {metric_name}={value} for {experiment_id}")
    
    def log_metrics(self, experiment_id: str, metrics: Dict[str, float]):
        """Log multiple metrics at once."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        self.experiments[experiment_id].metrics.update(metrics)
        self._save_experiments()
        logger.info(f"Logged {len(metrics)} metrics for {experiment_id}")
    
    def log_artifact(self, experiment_id: str, artifact_path: str):
        """Log an artifact (file) for an experiment."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        self.experiments[experiment_id].artifacts.append(artifact_path)
        self._save_experiments()
        logger.info(f"Logged artifact {artifact_path} for {experiment_id}")
    
    def complete_experiment(self, experiment_id: str, status: str = 'completed'):
        """Mark an experiment as completed or failed."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        self.experiments[experiment_id].status = status
        self._save_experiments()
        logger.info(f"Experiment {experiment_id} marked as {status}")
    
    def get_experiment(self, experiment_id: str) -> Experiment:
        """Get experiment details."""
        return self.experiments.get(experiment_id)
    
    def list_experiments(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Experiment]:
        """List experiments, optionally filtered."""
        experiments = list(self.experiments.values())
        
        if status:
            experiments = [e for e in experiments if e.status == status]
        
        if tags:
            experiments = [e for e in experiments if any(t in e.tags for t in tags)]
        
        return sorted(experiments, key=lambda e: e.created_at, reverse=True)
    
    def compare_experiments(
        self,
        experiment_ids: List[str],
        metric: str
    ) -> Dict[str, float]:
        """Compare experiments by a specific metric."""
        results = {}
        for exp_id in experiment_ids:
            if exp_id in self.experiments:
                exp = self.experiments[exp_id]
                results[exp_id] = exp.metrics.get(metric, float('-inf'))
        return results
    
    def get_best_experiment(self, metric: str, maximize: bool = True) -> str:
        """Get the best experiment based on a metric."""
        if not self.experiments:
            raise ValueError("No experiments found")
        
        metric_values = {
            k: v.metrics.get(metric, float('-inf'))
            for k, v in self.experiments.items()
        }
        
        best_id = max(
            metric_values.items(),
            key=lambda x: x[1] if maximize else -x[1]
        )[0]
        
        return best_id
