"""
from typing import Any, List, Optional, Set
MLflow Experiment Tracking Integration

This module provides comprehensive MLflow integration for:
1. Experiment tracking
2. Model versioning
3. Parameter logging
4. Metrics tracking
5. Artifact storage
6. Model registry
"""

import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import pickle

logger = logging.getLogger(__name__)

# Try to import MLflow
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    from mlflow.models.signature import infer_signature
    MLFLOW_AVAILABLE = True
except ImportError:
    logger.warning("MLflow not available. Install with: pip install mlflow")
    MLFLOW_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class ExperimentConfig:
    """Configuration for an experiment"""
    experiment_name: str
    tracking_uri: str = "mlruns"  # Local directory or remote URI
    artifact_location: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class RunConfig:
    """Configuration for a run"""
    run_name: str
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    nested: bool = False


@dataclass
class ModelInfo:
    """Information about a registered model"""
    name: str
    version: int
    stage: str
    description: str
    run_id: str
    metrics: Dict[str, float] = field(default_factory=dict)


class MLflowTracker:
    """
    MLflow Experiment Tracker for Trading Bot
    """
    
    def __init__(
        self,
        experiment_name: str = "trading_bot",
        tracking_uri: str = "mlruns"
    ):
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        self.current_run = None
        self.experiment_id = None
        
        if MLFLOW_AVAILABLE:
            self._initialize_mlflow()
        else:
            logger.warning("MLflow not available - using fallback logging")
            self._initialize_fallback()
    
    def _initialize_mlflow(self):
        """Initialize MLflow tracking"""
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Create or get experiment
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            self.experiment_id = mlflow.create_experiment(
                self.experiment_name,
                tags={"project": "trading_bot", "version": "3.0"}
            )
        else:
            self.experiment_id = experiment.experiment_id
        
        mlflow.set_experiment(self.experiment_name)
        
        self.client = MlflowClient()
        
        logger.info(f"MLflow initialized: experiment={self.experiment_name}, "
                   f"tracking_uri={self.tracking_uri}")
    
    def _initialize_fallback(self):
        """Initialize fallback logging when MLflow is not available"""
        self.fallback_dir = Path("mlflow_fallback")
        self.fallback_dir.mkdir(exist_ok=True)
        self.fallback_runs = []
        logger.info(f"Using fallback logging at {self.fallback_dir}")
    
    def start_run(
        self,
        run_name: str,
        description: str = "",
        tags: Dict[str, str] = None,
        nested: bool = False
    ) -> str:
        """Start a new run"""
        if MLFLOW_AVAILABLE:
            self.current_run = mlflow.start_run(
                run_name=run_name,
                nested=nested,
                description=description,
                tags=tags or {}
            )
            run_id = self.current_run.info.run_id
            logger.info(f"Started MLflow run: {run_name} (ID: {run_id})")
            return run_id
        else:
            run_id = f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_run = {
                'run_id': run_id,
                'run_name': run_name,
                'description': description,
                'tags': tags or {},
                'params': {},
                'metrics': {},
                'artifacts': [],
                'start_time': datetime.now().isoformat()
            }
            self.fallback_runs.append(self.current_run)
            logger.info(f"Started fallback run: {run_name} (ID: {run_id})")
            return run_id
    
    def end_run(self, status: str = "FINISHED"):
        """End the current run"""
        if MLFLOW_AVAILABLE and self.current_run:
            mlflow.end_run(status=status)
            logger.info(f"Ended MLflow run with status: {status}")
        elif self.current_run:
            self.current_run['end_time'] = datetime.now().isoformat()
            self.current_run['status'] = status
            
            # Save to file
            run_file = self.fallback_dir / f"{self.current_run['run_id']}.json"
            with open(run_file, 'w') as f:
                json.dump(self.current_run, f, indent=2)
            
            logger.info(f"Ended fallback run with status: {status}")
        
        self.current_run = None
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters"""
        if MLFLOW_AVAILABLE:
            # MLflow requires string values
            str_params = {k: str(v) for k, v in params.items()}
            mlflow.log_params(str_params)
        elif self.current_run:
            self.current_run['params'].update(params)
        
        logger.debug(f"Logged params: {list(params.keys())}")
    
    def log_param(self, key: str, value: Any):
        """Log a single parameter"""
        self.log_params({key: value})
    
    def log_metrics(self, metrics: Dict[str, float], step: int = None):
        """Log metrics"""
        if MLFLOW_AVAILABLE:
            mlflow.log_metrics(metrics, step=step)
        elif self.current_run:
            for key, value in metrics.items():
                if key not in self.current_run['metrics']:
                    self.current_run['metrics'][key] = []
                self.current_run['metrics'][key].append({
                    'value': value,
                    'step': step,
                    'timestamp': datetime.now().isoformat()
                })
        
        logger.debug(f"Logged metrics: {list(metrics.keys())}")
    
    def log_metric(self, key: str, value: float, step: int = None):
        """Log a single metric"""
        self.log_metrics({key: value}, step=step)
    
    def log_artifact(self, local_path: str, artifact_path: str = None):
        """Log an artifact file"""
        if MLFLOW_AVAILABLE:
            mlflow.log_artifact(local_path, artifact_path)
        elif self.current_run:
            self.current_run['artifacts'].append({
                'local_path': local_path,
                'artifact_path': artifact_path,
                'timestamp': datetime.now().isoformat()
            })
        
        logger.debug(f"Logged artifact: {local_path}")
    
    def log_artifacts(self, local_dir: str, artifact_path: str = None):
        """Log all artifacts in a directory"""
        if MLFLOW_AVAILABLE:
            mlflow.log_artifacts(local_dir, artifact_path)
        elif self.current_run:
            for file in Path(local_dir).iterdir():
                self.log_artifact(str(file), artifact_path)
        
        logger.debug(f"Logged artifacts from: {local_dir}")
    
    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: str = None,
        signature: Any = None,
        input_example: Any = None
    ):
        """Log a model"""
        if MLFLOW_AVAILABLE:
            # Determine model flavor
            model_type = type(model).__name__
            
            if hasattr(model, 'save') and hasattr(model, 'load'):
                # Custom model with save/load
                mlflow.pyfunc.log_model(
                    artifact_path=artifact_path,
                    python_model=model,
                    registered_model_name=registered_model_name,
                    signature=signature,
                    input_example=input_example
                )
            else:
                # Try sklearn flavor
                try:
                    mlflow.sklearn.log_model(
                        model,
                        artifact_path,
                        registered_model_name=registered_model_name,
                        signature=signature,
                        input_example=input_example
                    )
                except Exception:
                    # Fallback to pickle
                    model_path = Path(artifact_path) / "model.pkl"
                    model_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(model_path, 'wb') as f:
                        pickle.dump(model, f)
                    self.log_artifact(str(model_path))
            
            logger.info(f"Logged model: {artifact_path}")
        else:
            # Fallback: save model locally
            model_dir = self.fallback_dir / "models" / artifact_path
            model_dir.mkdir(parents=True, exist_ok=True)
            
            model_path = model_dir / "model.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            if self.current_run:
                self.current_run['artifacts'].append({
                    'type': 'model',
                    'path': str(model_path),
                    'name': registered_model_name,
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"Saved model to fallback: {model_path}")
    
    def log_figure(self, figure: Any, artifact_file: str):
        """Log a matplotlib figure"""
        if MLFLOW_AVAILABLE:
            mlflow.log_figure(figure, artifact_file)
        else:
            # Save figure locally
            fig_path = self.fallback_dir / "figures" / artifact_file
            fig_path.parent.mkdir(parents=True, exist_ok=True)
            figure.savefig(fig_path)
            
            if self.current_run:
                self.current_run['artifacts'].append({
                    'type': 'figure',
                    'path': str(fig_path),
                    'timestamp': datetime.now().isoformat()
                })
        
        logger.debug(f"Logged figure: {artifact_file}")
    
    def log_dict(self, dictionary: Dict, artifact_file: str):
        """Log a dictionary as JSON"""
        if MLFLOW_AVAILABLE:
            mlflow.log_dict(dictionary, artifact_file)
        else:
            dict_path = self.fallback_dir / "dicts" / artifact_file
            dict_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dict_path, 'w') as f:
                json.dump(dictionary, f, indent=2, default=str)
            
            if self.current_run:
                self.current_run['artifacts'].append({
                    'type': 'dict',
                    'path': str(dict_path),
                    'timestamp': datetime.now().isoformat()
                })
        
        logger.debug(f"Logged dict: {artifact_file}")
    
    def set_tag(self, key: str, value: str):
        """Set a tag on the current run"""
        if MLFLOW_AVAILABLE:
            mlflow.set_tag(key, value)
        elif self.current_run:
            self.current_run['tags'][key] = value
    
    def set_tags(self, tags: Dict[str, str]):
        """Set multiple tags"""
        for key, value in tags.items():
            self.set_tag(key, value)


class TradingExperimentTracker:
    """
    Specialized experiment tracker for trading strategies
    """
    
    def __init__(
        self,
        experiment_name: str = "trading_strategies",
        tracking_uri: str = "mlruns"
    ):
        self.tracker = MLflowTracker(experiment_name, tracking_uri)
        self.active_experiments: Dict[str, str] = {}  # strategy_id -> run_id
    
    def start_strategy_experiment(
        self,
        strategy_id: str,
        strategy_name: str,
        strategy_params: Dict[str, Any]
    ) -> str:
        """Start tracking a strategy experiment"""
        run_id = self.tracker.start_run(
            run_name=f"{strategy_name}_{datetime.now().strftime('%Y%m%d')}",
            description=f"Trading strategy: {strategy_name}",
            tags={
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "type": "trading_strategy"
            }
        )
        
        # Log strategy parameters
        self.tracker.log_params(strategy_params)
        
        self.active_experiments[strategy_id] = run_id
        
        logger.info(f"Started strategy experiment: {strategy_name}")
        
        return run_id
    
    def log_trade(
        self,
        strategy_id: str,
        trade: Dict[str, Any],
        step: int = None
    ):
        """Log a trade"""
        if strategy_id not in self.active_experiments:
            logger.warning(f"No active experiment for strategy: {strategy_id}")
            return
        
        # Log trade metrics
        metrics = {
            "trade_pnl": trade.get('pnl', 0),
            "trade_return": trade.get('return_pct', 0),
            "position_size": trade.get('position_size', 0)
        }
        
        self.tracker.log_metrics(metrics, step=step)
    
    def log_performance_metrics(
        self,
        strategy_id: str,
        metrics: Dict[str, float],
        step: int = None
    ):
        """Log performance metrics"""
        if strategy_id not in self.active_experiments:
            logger.warning(f"No active experiment for strategy: {strategy_id}")
            return
        
        # Prefix metrics with 'perf_'
        prefixed_metrics = {f"perf_{k}": v for k, v in metrics.items()}
        self.tracker.log_metrics(prefixed_metrics, step=step)
    
    def log_risk_metrics(
        self,
        strategy_id: str,
        metrics: Dict[str, float],
        step: int = None
    ):
        """Log risk metrics"""
        if strategy_id not in self.active_experiments:
            logger.warning(f"No active experiment for strategy: {strategy_id}")
            return
        
        # Prefix metrics with 'risk_'
        prefixed_metrics = {f"risk_{k}": v for k, v in metrics.items()}
        self.tracker.log_metrics(prefixed_metrics, step=step)
    
    def log_model_metrics(
        self,
        strategy_id: str,
        model_name: str,
        metrics: Dict[str, float],
        step: int = None
    ):
        """Log ML model metrics"""
        if strategy_id not in self.active_experiments:
            logger.warning(f"No active experiment for strategy: {strategy_id}")
            return
        
        # Prefix metrics with model name
        prefixed_metrics = {f"model_{model_name}_{k}": v for k, v in metrics.items()}
        self.tracker.log_metrics(prefixed_metrics, step=step)
    
    def log_strategy_model(
        self,
        strategy_id: str,
        model: Any,
        model_name: str
    ):
        """Log a strategy's ML model"""
        if strategy_id not in self.active_experiments:
            logger.warning(f"No active experiment for strategy: {strategy_id}")
            return
        
        self.tracker.log_model(
            model=model,
            artifact_path=f"models/{model_name}",
            registered_model_name=f"{strategy_id}_{model_name}"
        )
    
    def log_equity_curve(
        self,
        strategy_id: str,
        equity_curve: List[float],
        timestamps: List[datetime] = None
    ):
        """Log equity curve"""
        if strategy_id not in self.active_experiments:
            logger.warning(f"No active experiment for strategy: {strategy_id}")
            return
        
        data = {
            'equity_curve': equity_curve,
            'timestamps': [t.isoformat() for t in timestamps] if timestamps else None
        }
        
        self.tracker.log_dict(data, f"equity_curve_{strategy_id}.json")
    
    def end_strategy_experiment(
        self,
        strategy_id: str,
        final_metrics: Dict[str, float] = None,
        status: str = "FINISHED"
    ):
        """End a strategy experiment"""
        if strategy_id not in self.active_experiments:
            logger.warning(f"No active experiment for strategy: {strategy_id}")
            return
        
        if final_metrics:
            self.tracker.log_metrics(final_metrics)
        
        self.tracker.end_run(status=status)
        del self.active_experiments[strategy_id]
        
        logger.info(f"Ended strategy experiment: {strategy_id}")
    
    def compare_strategies(self, strategy_ids: List[str] = None) -> Dict:
        """Compare multiple strategies"""
        if not MLFLOW_AVAILABLE:
            return {"error": "MLflow not available for comparison"}
        
        client = MlflowClient()
        
        # Get all runs for the experiment
        experiment = mlflow.get_experiment_by_name(self.tracker.experiment_name)
        if not experiment:
            return {"error": "Experiment not found"}
        
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="" if not strategy_ids else 
                " or ".join([f"tags.strategy_id = '{sid}'" for sid in strategy_ids])
        )
        
        comparison = {
            'strategies': [],
            'best_by_return': None,
            'best_by_sharpe': None
        }
        
        for run in runs:
            strategy_data = {
                'run_id': run.info.run_id,
                'strategy_id': run.data.tags.get('strategy_id', 'unknown'),
                'strategy_name': run.data.tags.get('strategy_name', 'unknown'),
                'metrics': run.data.metrics,
                'params': run.data.params
            }
            comparison['strategies'].append(strategy_data)
        
        # Find best performers
        if comparison['strategies']:
            by_return = sorted(
                comparison['strategies'],
                key=lambda x: x['metrics'].get('perf_total_return', 0),
                reverse=True
            )
            comparison['best_by_return'] = by_return[0]['strategy_name']
            
            by_sharpe = sorted(
                comparison['strategies'],
                key=lambda x: x['metrics'].get('perf_sharpe_ratio', 0),
                reverse=True
            )
            comparison['best_by_sharpe'] = by_sharpe[0]['strategy_name']
        
        return comparison


class ModelRegistry:
    """
    Model registry for versioning and deployment
    """
    
    def __init__(self, tracking_uri: str = "mlruns"):
        self.tracking_uri = tracking_uri
        
        if MLFLOW_AVAILABLE:
            mlflow.set_tracking_uri(tracking_uri)
            self.client = MlflowClient()
        else:
            self.client = None
            self.local_registry: Dict[str, List[Dict]] = {}
    
    def register_model(
        self,
        model_name: str,
        run_id: str,
        artifact_path: str,
        description: str = ""
    ) -> Optional[ModelInfo]:
        """Register a model"""
        if MLFLOW_AVAILABLE:
            model_uri = f"runs:/{run_id}/{artifact_path}"
            
            result = mlflow.register_model(model_uri, model_name)
            
            # Update description
            self.client.update_model_version(
                name=model_name,
                version=result.version,
                description=description
            )
            
            logger.info(f"Registered model: {model_name} v{result.version}")
            
            return ModelInfo(
                name=model_name,
                version=int(result.version),
                stage=result.current_stage,
                description=description,
                run_id=run_id
            )
        else:
            # Fallback: local registry
            if model_name not in self.local_registry:
                self.local_registry[model_name] = []
            
            version = len(self.local_registry[model_name]) + 1
            
            model_info = {
                'version': version,
                'run_id': run_id,
                'artifact_path': artifact_path,
                'description': description,
                'stage': 'None',
                'registered_at': datetime.now().isoformat()
            }
            
            self.local_registry[model_name].append(model_info)
            
            logger.info(f"Registered model (local): {model_name} v{version}")
            
            return ModelInfo(
                name=model_name,
                version=version,
                stage='None',
                description=description,
                run_id=run_id
            )
    
    def transition_model_stage(
        self,
        model_name: str,
        version: int,
        stage: str  # "Staging", "Production", "Archived"
    ):
        """Transition a model to a new stage"""
        if MLFLOW_AVAILABLE:
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage
            )
            logger.info(f"Transitioned {model_name} v{version} to {stage}")
        else:
            if model_name in self.local_registry:
                for model in self.local_registry[model_name]:
                    if model['version'] == version:
                        model['stage'] = stage
                        logger.info(f"Transitioned {model_name} v{version} to {stage} (local)")
                        break
    
    def get_latest_model(
        self,
        model_name: str,
        stage: str = None
    ) -> Optional[ModelInfo]:
        """Get the latest model version"""
        if MLFLOW_AVAILABLE:
            if stage:
                versions = self.client.get_latest_versions(model_name, stages=[stage])
            else:
                versions = self.client.get_latest_versions(model_name)
            
            if versions:
                v = versions[0]
                return ModelInfo(
                    name=model_name,
                    version=int(v.version),
                    stage=v.current_stage,
                    description=v.description or "",
                    run_id=v.run_id
                )
        else:
            if model_name in self.local_registry:
                models = self.local_registry[model_name]
                if stage:
                    models = [m for m in models if m['stage'] == stage]
                if models:
                    latest = max(models, key=lambda x: x['version'])
                    return ModelInfo(
                        name=model_name,
                        version=latest['version'],
                        stage=latest['stage'],
                        description=latest['description'],
                        run_id=latest['run_id']
                    )
        
        return None
    
    def load_model(
        self,
        model_name: str,
        version: int = None,
        stage: str = None
    ) -> Any:
        """Load a model from the registry"""
        if MLFLOW_AVAILABLE:
            if version:
                model_uri = f"models:/{model_name}/{version}"
            elif stage:
                model_uri = f"models:/{model_name}/{stage}"
            else:
                model_uri = f"models:/{model_name}/latest"
            
            return mlflow.pyfunc.load_model(model_uri)
        else:
            logger.warning("Model loading not available without MLflow")
            return None
    
    def list_models(self) -> List[str]:
        """List all registered models"""
        if MLFLOW_AVAILABLE:
            models = self.client.search_registered_models()
            return [m.name for m in models]
        else:
            return list(self.local_registry.keys())


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create tracker
    tracker = TradingExperimentTracker(
        experiment_name="trading_strategies_test",
        tracking_uri="mlruns"
    )
    
    # Start strategy experiment
    tracker.start_strategy_experiment(
        strategy_id="momentum_v1",
        strategy_name="Momentum Strategy",
        strategy_params={
            "lookback_period": 20,
            "entry_threshold": 0.02,
            "exit_threshold": 0.01,
            "position_size": 0.1
        }
    )
    
    # Log some trades
    for i in range(10):
        trade = {
            'pnl': np.random.randn() * 100,
            'return_pct': np.random.randn() * 0.02,
            'position_size': 1000
        }
        tracker.log_trade("momentum_v1", trade, step=i)
    
    # Log performance metrics
    tracker.log_performance_metrics("momentum_v1", {
        'total_return': 0.15,
        'sharpe_ratio': 1.5,
        'max_drawdown': 0.08,
        'win_rate': 0.55
    })
    
    # End experiment
    tracker.end_strategy_experiment(
        "momentum_v1",
        final_metrics={'final_equity': 11500}
    )
    
    print("\n" + "="*60)
    logger.info("MLFLOW EXPERIMENT TRACKING")
    print("="*60)
    logger.info("Experiment completed successfully!")
    logger.info("View results at: mlruns/")
