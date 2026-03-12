"""
from typing import Any, List, Optional, Set
MLflow integration for experiment tracking
Tracks model training, parameters, and performance
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MLflowTracker:
    """
    MLflow experiment tracking wrapper
    Gracefully handles missing MLflow installation
    """
    
    def __init__(self, tracking_uri: Optional[str] = None, experiment_name: str = "alphaalgo"):
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.mlflow_available = False
        self.current_run = None
        
        try:
            # Try to import MLflow
            import mlflow
            self.mlflow = mlflow
            self.mlflow_available = True
            
            if tracking_uri:
                mlflow.set_tracking_uri(tracking_uri)
            
            # Set or create experiment
            try:
                mlflow.set_experiment(experiment_name)
            except Exception:
                mlflow.create_experiment(experiment_name)
                mlflow.set_experiment(experiment_name)
            
            logger.info(f"MLflow tracker initialized: {experiment_name}")
            
        except ImportError:
            logger.warning("MLflow not installed, using mock tracker")
            self.mlflow = None
    
    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """Start a new MLflow run"""
        if not self.mlflow_available:
            logger.debug(f"Mock MLflow run started: {run_name}")
            return
        try:
        
            self.current_run = self.mlflow.start_run(run_name=run_name, tags=tags)
            logger.info(f"MLflow run started: {run_name or 'unnamed'}")
        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
    
    def end_run(self):
        """End current MLflow run"""
        if not self.mlflow_available:
            return
        try:
        
            self.mlflow.end_run()
            self.current_run = None
            logger.info("MLflow run ended")
        except Exception as e:
            logger.error(f"Failed to end MLflow run: {e}")
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters"""
        if not self.mlflow_available:
            logger.debug(f"Mock log params: {params}")
            return
        try:
        
            for key, value in params.items():
                self.mlflow.log_param(key, value)
        except Exception as e:
            logger.error(f"Failed to log params: {e}")
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics"""
        if not self.mlflow_available:
            logger.debug(f"Mock log metrics: {metrics}")
            return
        try:
        
            for key, value in metrics.items():
                self.mlflow.log_metric(key, value, step=step)
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")
    
    def log_model(self, model: Any, artifact_path: str = "model"):
        """Log model artifact"""
        if not self.mlflow_available:
            logger.debug(f"Mock log model: {artifact_path}")
            return
        try:
        
            # Try different model logging methods
            if hasattr(model, 'save'):
                # Keras/TensorFlow model
                self.mlflow.keras.log_model(model, artifact_path)
            elif hasattr(model, 'save_model'):
                # XGBoost/LightGBM
                self.mlflow.sklearn.log_model(model, artifact_path)
            else:
                # Generic sklearn
                self.mlflow.sklearn.log_model(model, artifact_path)
            
            logger.info(f"Model logged: {artifact_path}")
        except Exception as e:
            logger.error(f"Failed to log model: {e}")
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log file artifact"""
        if not self.mlflow_available:
            logger.debug(f"Mock log artifact: {local_path}")
            return
        try:
        
            self.mlflow.log_artifact(local_path, artifact_path)
        except Exception as e:
            logger.error(f"Failed to log artifact: {e}")
    
    def log_dict(self, dictionary: Dict[str, Any], filename: str):
        """Log dictionary as JSON artifact"""
        if not self.mlflow_available:
            logger.debug(f"Mock log dict: {filename}")
            return
        try:
        
            self.mlflow.log_dict(dictionary, filename)
        except Exception as e:
            logger.error(f"Failed to log dict: {e}")
    
    def set_tags(self, tags: Dict[str, str]):
        """Set run tags"""
        if not self.mlflow_available:
            return
        try:
        
            for key, value in tags.items():
                self.mlflow.set_tag(key, value)
        except Exception as e:
            logger.error(f"Failed to set tags: {e}")
    
    def log_training_session(self, model_name: str, params: Dict[str, Any], 
                            metrics: Dict[str, float], model: Optional[Any] = None):
        """
        Log complete training session
        
        Args:
            model_name: Name of the model
            params: Training parameters
            metrics: Performance metrics
            model: Trained model object (optional)
        """
        run_name = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.start_run(run_name=run_name, tags={'model_type': model_name})
        
        try:
            # Log parameters
            self.log_params(params)
            
            # Log metrics
            self.log_metrics(metrics)
            
            # Log model if provided
            if model is not None:
                self.log_model(model, artifact_path=model_name)
            
            # Log metadata
            metadata = {
                'model_name': model_name,
                'timestamp': datetime.now().isoformat(),
                'params': params,
                'metrics': metrics
            }
            self.log_dict(metadata, 'metadata.json')
            
            logger.info(f"Training session logged: {run_name}")
            
        finally:
            self.end_run()
    
    def get_best_run(self, metric_name: str, ascending: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get best run based on metric
        
        Args:
            metric_name: Metric to optimize
            ascending: If True, lower is better
            
        Returns:
            Best run info or None
        """
        if not self.mlflow_available:
            return None
        try:
        
            experiment = self.mlflow.get_experiment_by_name(self.experiment_name)
            if not experiment:
                return None
            
            runs = self.mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{metric_name} {'ASC' if ascending else 'DESC'}"],
                max_results=1
            )
            
            if len(runs) > 0:
                return runs.iloc[0].to_dict()
            
        except Exception as e:
            logger.error(f"Failed to get best run: {e}")
        
        return None


class ExperimentTracker:
    """
    High-level experiment tracking interface
    Combines MLflow with local logging
    """
    
    def __init__(self, mlflow_tracker: Optional[MLflowTracker] = None):
        self.mlflow_tracker = mlflow_tracker or MLflowTracker()
        self.experiments: List[Dict[str, Any]] = []
        
    def track_experiment(self, name: str, config: Dict[str, Any], 
                        results: Dict[str, float], model: Optional[Any] = None):
        """
        Track complete experiment
        
        Args:
            name: Experiment name
            config: Configuration/parameters
            results: Results/metrics
            model: Trained model (optional)
        """
        experiment = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'config': config,
            'results': results
        }
        
        # Store locally
        self.experiments.append(experiment)
        
        # Log to MLflow
        self.mlflow_tracker.log_training_session(name, config, results, model)
        
        logger.info(f"Experiment tracked: {name}")
    
    def get_experiments(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent experiments"""
        if limit:
            return self.experiments[-limit:]
        return self.experiments
    
    def compare_experiments(self, metric: str) -> List[Dict[str, Any]]:
        """Compare experiments by metric"""
        sorted_experiments = sorted(
            self.experiments,
            key=lambda x: x['results'].get(metric, float('-inf')),
            reverse=True
        )
        return sorted_experiments
    
    def export_experiments(self, filepath: str):
        """Export experiments to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.experiments, f, indent=2)
            logger.info(f"Experiments exported to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to export experiments: {e}")
