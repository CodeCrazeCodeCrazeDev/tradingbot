"""
Model Registry for versioning and managing ML models
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for registered models."""
    model_id: str
    version: str
    model_type: str
    created_at: str
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    tags: List[str]
    status: str  # 'active', 'archived', 'deprecated'


class ModelRegistry:
    """
    Central registry for ML model versioning and management.
    
    Features:
    - Model versioning and tracking
    - Metadata storage
    - Model promotion (dev -> staging -> production)
    - Model comparison and rollback
    """
    
    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.registry_path / "registry.json"
        self.models: Dict[str, ModelMetadata] = {}
        self._load_registry()
        logger.info(f"ModelRegistry initialized at {self.registry_path}")
    
    def _load_registry(self):
        """Load registry from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.models = {
                        k: ModelMetadata(**v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.models)} models from registry")
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
    
    def _save_registry(self):
        """Save registry to disk."""
        try:
            data = {k: asdict(v) for k, v in self.models.items()}
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register_model(
        self,
        model: Any,
        model_id: str,
        version: str,
        model_type: str,
        metrics: Dict[str, float],
        parameters: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Register a new model version.
        
        Args:
            model: The model object to register
            model_id: Unique identifier for the model
            version: Version string (e.g., 'v1.0.0')
            model_type: Type of model (e.g., 'transformer', 'rl_agent')
            metrics: Performance metrics
            parameters: Model hyperparameters
            tags: Optional tags for categorization
        
        Returns:
            Full model key (model_id:version)
        """
        model_key = f"{model_id}:{version}"
        
        # Save model to disk
        model_path = self.registry_path / f"{model_key}.pkl"
        try:
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        except Exception as e:
            logger.error(f"Error saving model {model_key}: {e}")
            raise
        
        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            version=version,
            model_type=model_type,
            created_at=datetime.now().isoformat(),
            metrics=metrics,
            parameters=parameters,
            tags=tags or [],
            status='active'
        )
        
        self.models[model_key] = metadata
        self._save_registry()
        
        logger.info(f"Registered model {model_key} with metrics: {metrics}")
        return model_key
    
    def load_model(self, model_id: str, version: Optional[str] = None) -> Any:
        """
        Load a model from the registry.
        
        Args:
            model_id: Model identifier
            version: Specific version, or None for latest
        
        Returns:
            The loaded model object
        """
        if version is None:
            # Get latest version
            versions = [k for k in self.models.keys() if k.startswith(f"{model_id}:")]
            if not versions:
                raise ValueError(f"No models found for {model_id}")
            model_key = sorted(versions)[-1]
        else:
            model_key = f"{model_id}:{version}"
        
        if model_key not in self.models:
            raise ValueError(f"Model {model_key} not found in registry")
        
        model_path = self.registry_path / f"{model_key}.pkl"
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded model {model_key}")
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_key}: {e}")
            raise
    
    def get_metadata(self, model_id: str, version: Optional[str] = None) -> ModelMetadata:
        """Get metadata for a model."""
        if version is None:
            versions = [k for k in self.models.keys() if k.startswith(f"{model_id}:")]
            if not versions:
                raise ValueError(f"No models found for {model_id}")
            model_key = sorted(versions)[-1]
        else:
            model_key = f"{model_id}:{version}"
        
        return self.models.get(model_key)
    
    def list_models(self, model_type: Optional[str] = None) -> List[ModelMetadata]:
        """List all registered models, optionally filtered by type."""
        models = list(self.models.values())
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        return sorted(models, key=lambda m: m.created_at, reverse=True)
    
    def compare_models(self, model_keys: List[str], metric: str) -> Dict[str, float]:
        """Compare models by a specific metric."""
        results = {}
        for key in model_keys:
            if key in self.models:
                metadata = self.models[key]
                results[key] = metadata.metrics.get(metric, float('-inf'))
        return results
    
    def promote_model(self, model_id: str, version: str, new_status: str):
        """Promote a model to a new status (e.g., 'production')."""
        model_key = f"{model_id}:{version}"
        if model_key in self.models:
            self.models[model_key].status = new_status
            self._save_registry()
            logger.info(f"Promoted {model_key} to {new_status}")
    
    def archive_model(self, model_id: str, version: str):
        """Archive a model version."""
        self.promote_model(model_id, version, 'archived')
    
    def get_best_model(self, model_id: str, metric: str, maximize: bool = True) -> str:
        """Get the best model version based on a metric."""
        versions = [k for k in self.models.keys() if k.startswith(f"{model_id}:")]
        if not versions:
            raise ValueError(f"No models found for {model_id}")
        
        metric_values = {k: self.models[k].metrics.get(metric, float('-inf')) for k in versions}
        best_key = max(metric_values.items(), key=lambda x: x[1] if maximize else -x[1])[0]
        return best_key
