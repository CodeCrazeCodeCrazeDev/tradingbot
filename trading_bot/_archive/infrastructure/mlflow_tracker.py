"""
MLflow experiment tracking for trading models
"""

import logging
from typing import Any, Dict, Optional
import time

logger = logging.getLogger(__name__)

# Lazy import flags
_mlflow = None
_mlflow_pytorch = None
_mlflow_sklearn = None
MLFLOW_AVAILABLE = False

def _lazy_import_mlflow():
    """Lazy import mlflow to avoid import-time errors with pytorch/torchvision"""
    global _mlflow, _mlflow_pytorch, _mlflow_sklearn, MLFLOW_AVAILABLE
    if _mlflow is not None:
        return MLFLOW_AVAILABLE
    try:
    
        import mlflow as _ml
        _mlflow = _ml
        MLFLOW_AVAILABLE = True
        
        try:
            # Try to import pytorch support, but don't fail if unavailable
            import mlflow.pytorch as _mlp
            _mlflow_pytorch = _mlp
        except (ImportError, RuntimeError) as e:
            logger.debug(f"MLflow pytorch support not available: {e}")
            _mlflow_pytorch = None
        # Try to import sklearn support
            import mlflow.sklearn as _mls
            _mlflow_sklearn = _mls
        except ImportError as e:
            logger.debug(f"MLflow sklearn support not available: {e}")
            _mlflow_sklearn = None
            
    except ImportError:
        logger.warning("MLflow not available. Install with: pip install mlflow")
        MLFLOW_AVAILABLE = False
    
    return MLFLOW_AVAILABLE


class MLflowTracker:
    """
    MLflow experiment tracker for trading models
    """
    
    def __init__(self, experiment_name: str = "alphaalgo_trading", tracking_uri: Optional[str] = None):
        """
        Initialize MLflow tracker
        
        Args:
            experiment_name: Name of experiment
            tracking_uri: MLflow tracking server URI
        """
        # Lazy import mlflow
        if not _lazy_import_mlflow():
            logger.warning("MLflow not available - tracking disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.experiment_name = experiment_name
        
        if tracking_uri:
            _mlflow.set_tracking_uri(tracking_uri)
        
        _mlflow.set_experiment(experiment_name)
        logger.info(f"MLflow tracker initialized: {experiment_name}")
    
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """Start new MLflow run"""
        if not self.enabled:
            return None
        
        return _mlflow.start_run(run_name=run_name, tags=tags)
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters"""
        if not self.enabled:
            return
        
        _mlflow.log_params(params)
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics"""
        if not self.enabled:
            return
        
        _mlflow.log_metrics(metrics, step=step)
    
    def log_model(self, model: Any, artifact_path: str, model_type: str = "pytorch"):
        """Log model artifact"""
        if not self.enabled:
            return
        
        if model_type == "pytorch" and _mlflow_pytorch:
            _mlflow_pytorch.log_model(model, artifact_path)
        elif model_type == "sklearn" and _mlflow_sklearn:
            _mlflow_sklearn.log_model(model, artifact_path)
        else:
            _mlflow.log_artifact(model, artifact_path)
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log artifact file"""
        if not self.enabled:
            return
        
        _mlflow.log_artifact(local_path, artifact_path)
    
    def log_training_run(
        self,
        model_name: str,
        model: Any,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        model_type: str = "pytorch"
    ):
        """Log complete training run"""
        if not self.enabled:
            return
        
        with _mlflow.start_run(run_name=f"{model_name}_{int(time.time())}"):
            _mlflow.log_params(params)
            _mlflow.log_metrics(metrics)
            self.log_model(model, model_name, model_type)
            
            logger.info(f"Logged training run for {model_name}")
    
    def load_best_model(self, metric: str = "val_loss", ascending: bool = True):
        """Load best model based on metric"""
        if not self.enabled:
            return None
        
        runs = _mlflow.search_runs(
            experiment_names=[self.experiment_name],
            order_by=[f"metrics.{metric} {'ASC' if ascending else 'DESC'}"]
        )
        
        if len(runs) == 0:
            logger.warning("No runs found")
            return None
        
        best_run_id = runs.iloc[0].run_id
        model_uri = f"runs:/{best_run_id}/model"
        
        try:
            model = _mlflow_pytorch.load_model(model_uri) if _mlflow_pytorch else None
            if model is None:
                raise Exception("PyTorch support not available")
            logger.info(f"Loaded best model from run {best_run_id}")
            return model
        except Exception:
            try:
                model = _mlflow_sklearn.load_model(model_uri) if _mlflow_sklearn else None
                if model is None:
                    raise Exception("Sklearn support not available")
                logger.info(f"Loaded best sklearn model from run {best_run_id}")
                return model
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                return None
    
    def get_run_metrics(self, run_id: str) -> Dict[str, float]:
        """Get metrics for specific run"""
        if not self.enabled:
            return {}
        
        run = _mlflow.get_run(run_id)
        return run.data.metrics
    
    def compare_models(self, metric: str = "val_loss", top_n: int = 5) -> list:
        """Compare top N models"""
        if not self.enabled:
            return []
        
        runs = _mlflow.search_runs(
            experiment_names=[self.experiment_name],
            order_by=[f"metrics.{metric} ASC"]
        )
        
        return runs.head(top_n).to_dict('records')


_tracker: Optional[MLflowTracker] = None


def get_tracker(experiment_name: str = "alphaalgo_trading") -> MLflowTracker:
    """Get global MLflow tracker"""
    global _tracker
    
    if _tracker is None:
        _tracker = MLflowTracker(experiment_name)
    
    return _tracker


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if MLFLOW_AVAILABLE:
        tracker = MLflowTracker("test_experiment")
        
        # Test logging
        with tracker.start_run(run_name="test_run"):
            tracker.log_params({"learning_rate": 0.001, "batch_size": 32})
            tracker.log_metrics({"loss": 0.5, "accuracy": 0.85})
        
        logger.info("✅ MLflow tracker test passed!")
    else:
        logger.info("❌ MLflow not available")
