"""
Feature Registry for Research OS.
Manages engineered features, pipeline tracking, importance metrics, and feature lifecycle states.
"""

from typing import Dict, Optional, Any
import logging
from datetime import datetime
from trading_bot.research.core.interfaces import FeatureRegistry, EngineeredFeature

logger = logging.getLogger(__name__)


class StandardFeatureRegistry(FeatureRegistry):
    """
    Standard in-memory Feature Registry tracking lineage,
    pipeline code, historical importance scores, and usage states.
    """

    def __init__(self):
        self._features: Dict[str, EngineeredFeature] = {}
        self._feature_metadata: Dict[str, Dict[str, Any]] = {}

    def register_feature(self, feature: EngineeredFeature) -> None:
        feature_id = feature.feature_id
        self._features[feature_id] = feature

        # Initialize registry entry metadata if not exists
        if feature_id not in self._feature_metadata:
            self._feature_metadata[feature_id] = {
                "name": feature.name,
                "origin": feature.metadata.get("type", "unknown_origin"),
                "pipeline_code": feature.pipeline_code or "",
                "dependencies": feature.dependencies,
                "importance_history": [],
                "usage_history": [],
                "status": "active",  # active, retired, deprecated
                "registered_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat()
            }
        else:
            self._feature_metadata[feature_id]["last_accessed"] = datetime.utcnow().isoformat()

        logger.info(f"Feature '{feature_id}' successfully registered in Feature Registry.")

    def get_feature(self, feature_id: str) -> Optional[EngineeredFeature]:
        if feature_id in self._features:
            self._feature_metadata[feature_id]["last_accessed"] = datetime.utcnow().isoformat()
            return self._features[feature_id]
        return None

    def record_importance(self, feature_id: str, score: float, metric_name: str = "MutualInformation") -> None:
        """Track feature importance scores over time."""
        if feature_id in self._feature_metadata:
            self._feature_metadata[feature_id]["importance_history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "metric": metric_name,
                "score": float(score)
            })

    def record_usage(self, feature_id: str, strategy_id: str, context: str = "backtest") -> None:
        """Track feature usage in models and strategies."""
        if feature_id in self._feature_metadata:
            self._feature_metadata[feature_id]["usage_history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "strategy_id": strategy_id,
                "context": context
            })

    def retire_feature(self, feature_id: str, reason: str) -> None:
        """Retire a feature to prevent its downstream usage."""
        if feature_id in self._feature_metadata:
            self._feature_metadata[feature_id]["status"] = "retired"
            self._feature_metadata[feature_id]["retirement_reason"] = reason
            logger.info(f"Feature '{feature_id}' retired: {reason}")

    def get_metadata(self, feature_id: str) -> Optional[Dict[str, Any]]:
        return self._feature_metadata.get(feature_id)
