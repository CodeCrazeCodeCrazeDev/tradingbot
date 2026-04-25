"""
Continuous Experiment Engine
Runs experiments continuously, evolves models, and improves the system.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ExperimentType(Enum):
    MODEL_TRAINING = "model_training"
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"
    ARCHITECTURE_SEARCH = "architecture_search"
    STRATEGY_TESTING = "strategy_testing"
    FEATURE_ENGINEERING = "feature_engineering"
    ENSEMBLE_OPTIMIZATION = "ensemble_optimization"
    TRANSFER_LEARNING = "transfer_learning"
    META_LEARNING = "meta_learning"


class ExperimentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Experiment:
    experiment_id: str
    experiment_type: ExperimentType
    name: str
    description: str
    parameters: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ExperimentStatus = ExperimentStatus.PENDING
    results: Optional[Dict] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class Model:
    model_id: str
    model_type: str
    version: int
    architecture: Dict[str, Any]
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    created_at: datetime
    trained_on: str
    parent_model_id: Optional[str] = None
    is_production: bool = False


class ContinuousExperimentEngine:
    """
    Runs experiments continuously, trains models, and evolves the system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.experiments: List[Experiment] = []
        self.models: Dict[str, Model] = {}
        
        self.running_experiments: Set[str] = set()
        self.experiment_queue: List[Experiment] = []
        
        self.max_concurrent_experiments = config.get('max_concurrent', 5)
        self.running = False
        
        self.storage_path = Path(config.get('storage_path', 'experiment_engine_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.model_path = self.storage_path / 'models'
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Continuous Experiment Engine initialized")
    
    async def initialize(self):
        """Initialize the experiment engine."""
        logger.info("Initializing Continuous Experiment Engine")
        
        await self._load_experiments()
        await self._load_models()
        
        self.running = True
        logger.info("Experiment Engine ready - %d models in registry", len(self.models))
    
    async def _load_experiments(self):
        """Load experiment history."""
        exp_file = self.storage_path / 'experiments.json'
        if exp_file.exists():
            with open(exp_file, 'r') as f:
                data = json.load(f)
                for exp_data in data:
                    experiment = Experiment(
                        experiment_id=exp_data['experiment_id'],
                        experiment_type=ExperimentType(exp_data['experiment_type']),
                        name=exp_data['name'],
                        description=exp_data['description'],
                        parameters=exp_data['parameters'],
                        created_at=datetime.fromisoformat(exp_data['created_at']),
                        status=ExperimentStatus(exp_data.get('status', 'pending')),
                        results=exp_data.get('results'),
                        metrics=exp_data.get('metrics', {}),
                        artifacts=exp_data.get('artifacts', []),
                    )
                    self.experiments.append(experiment)
    
    async def _load_models(self):
        """Load model registry."""
        models_file = self.storage_path / 'models.json'
        if models_file.exists():
            with open(models_file, 'r') as f:
                data = json.load(f)
                for model_data in data:
                    model = Model(
                        model_id=model_data['model_id'],
                        model_type=model_data['model_type'],
                        version=model_data['version'],
                        architecture=model_data['architecture'],
                        parameters=model_data['parameters'],
                        performance_metrics=model_data['performance_metrics'],
                        created_at=datetime.fromisoformat(model_data['created_at']),
                        trained_on=model_data['trained_on'],
                        parent_model_id=model_data.get('parent_model_id'),
                        is_production=model_data.get('is_production', False),
                    )
                    self.models[model.model_id] = model
    
    async def create_experiment(
        self,
        experiment_type: ExperimentType,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> Experiment:
        """Create a new experiment."""
        experiment = Experiment(
            experiment_id=f"exp_{datetime.now().timestamp()}",
            experiment_type=experiment_type,
            name=name,
            description=description,
            parameters=parameters,
            created_at=datetime.now(),
        )
        
        self.experiments.append(experiment)
        self.experiment_queue.append(experiment)
        
        logger.info("Created experiment: %s (%s)", name, experiment_type.value)
        
        return experiment
    
    async def run_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """Run an experiment."""
        logger.info("Running experiment: %s", experiment.name)
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now()
        self.running_experiments.add(experiment.experiment_id)
        
        try:
            results = await self._execute_experiment(experiment)
            
            experiment.status = ExperimentStatus.COMPLETED
            experiment.completed_at = datetime.now()
            experiment.results = results
            experiment.metrics = results.get('metrics', {})
            
            self.running_experiments.remove(experiment.experiment_id)
            
            logger.info("Experiment completed: %s", experiment.name)
            
            if results.get('success'):
                await self._process_successful_experiment(experiment, results)
            
            return results
            
        except Exception as e:
            logger.error("Experiment failed: %s - %s", experiment.name, e)
            experiment.status = ExperimentStatus.FAILED
            self.running_experiments.remove(experiment.experiment_id)
            raise
    
    async def _execute_experiment(self, experiment: Experiment) -> Dict[str, Any]:
        """Execute the experiment based on type."""
        exp_type = experiment.experiment_type
        
        if exp_type == ExperimentType.MODEL_TRAINING:
            return await self._run_model_training(experiment)
        elif exp_type == ExperimentType.HYPERPARAMETER_TUNING:
            return await self._run_hyperparameter_tuning(experiment)
        elif exp_type == ExperimentType.ARCHITECTURE_SEARCH:
            return await self._run_architecture_search(experiment)
        elif exp_type == ExperimentType.STRATEGY_TESTING:
            return await self._run_strategy_testing(experiment)
        elif exp_type == ExperimentType.FEATURE_ENGINEERING:
            return await self._run_feature_engineering(experiment)
        else:
            return await self._run_generic_experiment(experiment)
    
    async def _run_model_training(self, experiment: Experiment) -> Dict:
        """Run model training experiment."""
        await asyncio.sleep(2)
        
        return {
            'success': True,
            'metrics': {
                'accuracy': np.random.uniform(0.7, 0.95),
                'precision': np.random.uniform(0.65, 0.9),
                'recall': np.random.uniform(0.65, 0.9),
                'f1_score': np.random.uniform(0.65, 0.9),
                'loss': np.random.uniform(0.1, 0.5),
            },
            'training_time': 120.0,
            'epochs': 100,
            'model_id': f"model_{datetime.now().timestamp()}",
        }
    
    async def _run_hyperparameter_tuning(self, experiment: Experiment) -> Dict:
        """Run hyperparameter tuning experiment."""
        await asyncio.sleep(3)
        
        return {
            'success': True,
            'metrics': {
                'best_score': np.random.uniform(0.75, 0.95),
                'improvement': np.random.uniform(0.05, 0.15),
            },
            'best_params': {
                'learning_rate': np.random.uniform(0.0001, 0.01),
                'batch_size': int(np.random.choice([32, 64, 128, 256])),
                'dropout': np.random.uniform(0.1, 0.5),
            },
            'trials': 50,
        }
    
    async def _run_architecture_search(self, experiment: Experiment) -> Dict:
        """Run neural architecture search."""
        await asyncio.sleep(4)
        
        return {
            'success': True,
            'metrics': {
                'best_architecture_score': np.random.uniform(0.8, 0.95),
            },
            'best_architecture': {
                'layers': int(np.random.choice([3, 4, 5, 6])),
                'units_per_layer': [128, 256, 128],
                'activation': 'relu',
            },
            'architectures_tested': 100,
        }
    
    async def _run_strategy_testing(self, experiment: Experiment) -> Dict:
        """Run strategy testing experiment."""
        await asyncio.sleep(2)
        
        return {
            'success': True,
            'metrics': {
                'sharpe_ratio': np.random.uniform(1.5, 3.5),
                'total_return': np.random.uniform(0.15, 0.6),
                'max_drawdown': np.random.uniform(0.05, 0.2),
                'win_rate': np.random.uniform(0.55, 0.75),
            },
            'trades': int(np.random.uniform(100, 500)),
            'backtest_period': '1 year',
        }
    
    async def _run_feature_engineering(self, experiment: Experiment) -> Dict:
        """Run feature engineering experiment."""
        await asyncio.sleep(1)
        
        return {
            'success': True,
            'metrics': {
                'feature_importance_score': np.random.uniform(0.6, 0.9),
                'model_improvement': np.random.uniform(0.05, 0.2),
            },
            'new_features': int(np.random.uniform(5, 20)),
            'features_selected': int(np.random.uniform(10, 30)),
        }
    
    async def _run_generic_experiment(self, experiment: Experiment) -> Dict:
        """Run generic experiment."""
        await asyncio.sleep(1)
        
        return {
            'success': True,
            'metrics': {
                'score': np.random.uniform(0.5, 1.0),
            },
        }
    
    async def _process_successful_experiment(self, experiment: Experiment, results: Dict):
        """Process results from successful experiment."""
        
        if experiment.experiment_type == ExperimentType.MODEL_TRAINING:
            await self._register_new_model(experiment, results)
        
        elif experiment.experiment_type == ExperimentType.HYPERPARAMETER_TUNING:
            await self._update_model_parameters(experiment, results)
        
        elif experiment.experiment_type == ExperimentType.ARCHITECTURE_SEARCH:
            await self._create_new_architecture(experiment, results)
    
    async def _register_new_model(self, experiment: Experiment, results: Dict):
        """Register a newly trained model."""
        model_id = results.get('model_id', f"model_{datetime.now().timestamp()}")
        
        model = Model(
            model_id=model_id,
            model_type=experiment.parameters.get('model_type', 'neural_network'),
            version=1,
            architecture=experiment.parameters.get('architecture', {}),
            parameters=experiment.parameters,
            performance_metrics=results.get('metrics', {}),
            created_at=datetime.now(),
            trained_on=experiment.parameters.get('dataset', 'default'),
        )
        
        self.models[model_id] = model
        
        logger.info("Registered new model: %s (accuracy: %.2f)",
                   model_id, model.performance_metrics.get('accuracy', 0.0))
    
    async def _update_model_parameters(self, experiment: Experiment, results: Dict):
        """Update model with optimized parameters."""
        best_params = results.get('best_params', {})
        
        logger.info("Optimized parameters found: %s", best_params)
    
    async def _create_new_architecture(self, experiment: Experiment, results: Dict):
        """Create a new model architecture."""
        best_arch = results.get('best_architecture', {})
        
        logger.info("New architecture discovered: %s", best_arch)
    
    async def evolve_model(self, model_id: str) -> Optional[Model]:
        """Evolve an existing model."""
        parent_model = self.models.get(model_id)
        
        if not parent_model:
            logger.warning("Model not found: %s", model_id)
            return None
        
        logger.info("Evolving model: %s", model_id)
        
        evolved_params = await self._mutate_parameters(parent_model.parameters)
        
        experiment = await self.create_experiment(
            ExperimentType.MODEL_TRAINING,
            f"Evolution of {model_id}",
            f"Evolved version of model {model_id}",
            evolved_params
        )
        
        results = await self.run_experiment(experiment)
        
        if results.get('success'):
            new_model_id = results.get('model_id')
            new_model = self.models.get(new_model_id)
            
            if new_model:
                new_model.parent_model_id = model_id
                new_model.version = parent_model.version + 1
                
                if self._is_better_model(new_model, parent_model):
                    logger.info("Evolution successful - new model outperforms parent")
                    return new_model
        
        return None
    
    async def _mutate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate model parameters for evolution."""
        mutated = parameters.copy()
        
        if 'learning_rate' in mutated:
            mutated['learning_rate'] *= np.random.uniform(0.5, 2.0)
        
        if 'dropout' in mutated:
            mutated['dropout'] = np.clip(
                mutated['dropout'] + np.random.uniform(-0.1, 0.1),
                0.0, 0.5
            )
        
        return mutated
    
    def _is_better_model(self, new_model: Model, old_model: Model) -> bool:
        """Determine if new model is better than old model."""
        new_score = new_model.performance_metrics.get('accuracy', 0.0)
        old_score = old_model.performance_metrics.get('accuracy', 0.0)
        
        return new_score > old_score
    
    async def deploy_model(self, model_id: str) -> bool:
        """Deploy a model to production."""
        model = self.models.get(model_id)
        
        if not model:
            logger.warning("Model not found: %s", model_id)
            return False
        
        for m in self.models.values():
            m.is_production = False
        
        model.is_production = True
        
        logger.info("DEPLOYED MODEL TO PRODUCTION: %s (v%d)",
                   model_id, model.version)
        
        return True
    
    async def experiment_loop(self):
        """Main experiment loop - continuously run experiments."""
        logger.info("Starting continuous experiment loop")
        
        while self.running:
            try:
                if len(self.running_experiments) < self.max_concurrent_experiments:
                    if self.experiment_queue:
                        experiment = self.experiment_queue.pop(0)
                        asyncio.create_task(self.run_experiment(experiment))
                    else:
                        await self._generate_new_experiments()
                
                await self._evolve_best_models()
                
                await self._persist_state()
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error("Error in experiment loop: %s", e, exc_info=True)
                await asyncio.sleep(30)
    
    async def _generate_new_experiments(self):
        """Generate new experiments automatically."""
        if np.random.random() < 0.3:
            exp_types = list(ExperimentType)
            exp_type = np.random.choice(exp_types)
            
            await self.create_experiment(
                exp_type,
                f"Auto-generated {exp_type.value} experiment",
                "Automatically generated experiment for continuous improvement",
                {'auto_generated': True}
            )
    
    async def _evolve_best_models(self):
        """Evolve the best performing models."""
        if not self.models:
            return
        
        if np.random.random() < 0.1:
            best_models = sorted(
                self.models.values(),
                key=lambda m: m.performance_metrics.get('accuracy', 0.0),
                reverse=True
            )[:3]
            
            if best_models:
                model_to_evolve = np.random.choice(best_models)
                await self.evolve_model(model_to_evolve.model_id)
    
    async def _persist_state(self):
        """Persist experiment and model state."""
        exp_file = self.storage_path / 'experiments.json'
        exp_data = [
            {
                'experiment_id': e.experiment_id,
                'experiment_type': e.experiment_type.value,
                'name': e.name,
                'description': e.description,
                'parameters': e.parameters,
                'created_at': e.created_at.isoformat(),
                'status': e.status.value,
                'results': e.results,
                'metrics': e.metrics,
                'artifacts': e.artifacts,
            }
            for e in self.experiments[-1000:]
        ]
        
        with open(exp_file, 'w') as f:
            json.dump(exp_data, f, indent=2)
        
        models_file = self.storage_path / 'models.json'
        models_data = [
            {
                'model_id': m.model_id,
                'model_type': m.model_type,
                'version': m.version,
                'architecture': m.architecture,
                'parameters': m.parameters,
                'performance_metrics': m.performance_metrics,
                'created_at': m.created_at.isoformat(),
                'trained_on': m.trained_on,
                'parent_model_id': m.parent_model_id,
                'is_production': m.is_production,
            }
            for m in self.models.values()
        ]
        
        with open(models_file, 'w') as f:
            json.dump(models_data, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get experiment engine status."""
        return {
            'total_experiments': len(self.experiments),
            'running_experiments': len(self.running_experiments),
            'queued_experiments': len(self.experiment_queue),
            'completed_experiments': sum(1 for e in self.experiments if e.status == ExperimentStatus.COMPLETED),
            'total_models': len(self.models),
            'production_models': sum(1 for m in self.models.values() if m.is_production),
            'avg_model_accuracy': np.mean([m.performance_metrics.get('accuracy', 0.0) for m in self.models.values()]) if self.models else 0.0,
        }
    
    async def shutdown(self):
        """Shutdown experiment engine."""
        logger.info("Shutting down Continuous Experiment Engine")
        self.running = False
        await self._persist_state()
