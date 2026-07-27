"""
Experiment Registry for Research OS.
Tracks the complete history of every quantitative experiment, keeping failed attempts for knowledge acquisition.
"""

from typing import Dict, Optional, Any, List
import logging
from datetime import datetime
from trading_bot.research.core.interfaces import ExperimentRegistry

logger = logging.getLogger(__name__)


class StandardExperimentRegistry(ExperimentRegistry):
    """
    In-memory Experiment Registry supporting complete reproducible experiment logs,
    parameters, code checkpoints, metrics, and outcomes.
    """

    def __init__(self):
        self._experiments: Dict[str, Dict[str, Any]] = {}

    def register_experiment(self, experiment_id: str, experiment_data: Dict[str, Any]) -> None:
        """
        Stores reproducible logs of a quant research experiment.
        """
        # Ensure critical reproducibility fields are documented
        experiment_record = {
            "experiment_id": experiment_id,
            "hypothesis_id": experiment_data.get("hypothesis_id", "unknown_hyp"),
            "dataset_version": experiment_data.get("dataset_version", "1.0.0"),
            "feature_version": experiment_data.get("feature_version", "1.0.0"),
            "parameters": experiment_data.get("parameters", {}),
            "random_seed": experiment_data.get("random_seed", 42),
            "code_version": experiment_data.get("code_version", "git_head_placeholder"),
            "metrics": experiment_data.get("metrics", {}),
            "conclusions": experiment_data.get("conclusions", "Inconclusive"),
            "success": experiment_data.get("success", False),
            "registered_at": datetime.utcnow().isoformat()
        }

        self._experiments[experiment_id] = experiment_record
        logger.info(f"Registered experiment '{experiment_id}' in Experiment Registry (Success: {experiment_record['success']}).")

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        return self._experiments.get(experiment_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self._experiments.values())
