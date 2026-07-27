"""
Model Registry for Research OS.
Tracks ML/DL model weights, hyperparameters, training datasets, and deployment histories.
"""

from typing import Dict, Optional, Any
import logging
from datetime import datetime
from trading_bot.research.core.interfaces import ModelRegistry

logger = logging.getLogger(__name__)


class StandardModelRegistry(ModelRegistry):
    """
    Standard Model Registry managing trained research models.
    """

    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {}

    def register_model(self, model_id: str, model_data: Dict[str, Any]) -> None:
        record = {
            "model_id": model_id,
            "training_metadata": model_data.get("training_metadata", {}),
            "hyperparameters": model_data.get("hyperparameters", {}),
            "datasets": model_data.get("datasets", []),
            "experiments": model_data.get("experiments", []),
            "evaluation_metrics": model_data.get("evaluation_metrics", {}),
            "deployment_history": model_data.get("deployment_history", []),
            "status": model_data.get("status", "draft"),  # draft, champion, challenger, retired
            "registered_at": datetime.utcnow().isoformat()
        }
        self._models[model_id] = record
        logger.info(f"Registered model '{model_id}' successfully in Model Registry.")

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self._models.get(model_id)

    def update_deployment(self, model_id: str, environment: str, status: str) -> None:
        if model_id in self._models:
            self._models[model_id]["deployment_history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "environment": environment,
                "status": status
            })
            self._models[model_id]["status"] = status
