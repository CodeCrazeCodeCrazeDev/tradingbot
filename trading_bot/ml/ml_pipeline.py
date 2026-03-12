"""
ML Pipeline: Model Versioning, Retraining, and Feature Engineering

Production-ready ML infrastructure:
- Model versioning and registry
- Automated retraining pipeline
- Feature engineering framework
- Model deployment and rollback
- A/B testing for models
- Performance monitoring
"""

import asyncio
import logging
import json
import hashlib
import pickle
import os
from typing import Any, Callable, Dict, List, Optional, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ModelStatus(Enum):
    """Model lifecycle status"""
    TRAINING = "training"
    VALIDATING = "validating"
    READY = "ready"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class ModelType(Enum):
    """Types of ML models"""
    SIGNAL_GENERATOR = "signal_generator"
    RISK_PREDICTOR = "risk_predictor"
    PRICE_FORECASTER = "price_forecaster"
    REGIME_CLASSIFIER = "regime_classifier"
    POSITION_SIZER = "position_sizer"
    EXECUTION_OPTIMIZER = "execution_optimizer"


@dataclass
class ModelMetadata:
    """Model metadata"""
    model_id: str
    name: str
    version: str
    model_type: ModelType
    status: ModelStatus
    created_at: datetime
    updated_at: datetime
    
    # Training info
    training_data_start: Optional[datetime] = None
    training_data_end: Optional[datetime] = None
    training_samples: int = 0
    training_duration_seconds: float = 0
    
    # Performance metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Feature info
    features: List[str] = field(default_factory=list)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    
    # Deployment info
    deployed_at: Optional[datetime] = None
    deployment_count: int = 0
    
    # Lineage
    parent_model_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'model_id': self.model_id,
            'name': self.name,
            'version': self.version,
            'model_type': self.model_type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'training_samples': self.training_samples,
            'metrics': self.metrics,
            'validation_metrics': self.validation_metrics,
            'features': self.features,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'tags': self.tags
        }


@dataclass
class FeatureDefinition:
    """Feature definition"""
    name: str
    description: str
    feature_type: str  # numeric, categorical, boolean
    computation: Optional[str] = None  # Expression or function name
    dependencies: List[str] = field(default_factory=list)
    lookback_periods: int = 1
    is_target: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'feature_type': self.feature_type,
            'computation': self.computation,
            'dependencies': self.dependencies,
            'lookback_periods': self.lookback_periods,
            'is_target': self.is_target
        }


class FeatureStore:
    """
    Feature store for managing and computing features.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Feature definitions
        self.features: Dict[str, FeatureDefinition] = {}
        
        # Feature cache
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5 minutes
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Storage
        self.storage_path = Path(self.config.get('storage_path', 'data/features'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Register default features
        self._register_default_features()
        
        logger.info("FeatureStore initialized")
    
    def _register_default_features(self):
        """Register default trading features"""
        default_features = [
            FeatureDefinition(
                name='returns',
                description='Price returns',
                feature_type='numeric',
                computation='(close - close.shift(1)) / close.shift(1)',
                lookback_periods=1
            ),
            FeatureDefinition(
                name='volatility',
                description='Rolling volatility',
                feature_type='numeric',
                computation='returns.rolling(20).std()',
                dependencies=['returns'],
                lookback_periods=20
            ),
            FeatureDefinition(
                name='rsi',
                description='Relative Strength Index',
                feature_type='numeric',
                lookback_periods=14
            ),
            FeatureDefinition(
                name='macd',
                description='MACD indicator',
                feature_type='numeric',
                lookback_periods=26
            ),
            FeatureDefinition(
                name='volume_ratio',
                description='Volume relative to average',
                feature_type='numeric',
                computation='volume / volume.rolling(20).mean()',
                lookback_periods=20
            ),
            FeatureDefinition(
                name='price_momentum',
                description='Price momentum',
                feature_type='numeric',
                computation='close / close.shift(10) - 1',
                lookback_periods=10
            ),
            FeatureDefinition(
                name='trend_strength',
                description='Trend strength indicator',
                feature_type='numeric',
                lookback_periods=20
            ),
            FeatureDefinition(
                name='market_regime',
                description='Market regime classification',
                feature_type='categorical',
                lookback_periods=50
            )
        ]
        
        for feature in default_features:
            self.register_feature(feature)
    
    def register_feature(self, feature: FeatureDefinition):
        """Register a feature definition"""
        self.features[feature.name] = feature
        logger.debug(f"Feature registered: {feature.name}")
    
    def compute_features(
        self,
        data: Any,  # DataFrame
        feature_names: Optional[List[str]] = None
    ) -> Any:
        """Compute features from data"""
        if not PANDAS_AVAILABLE:
            logger.warning("pandas not available for feature computation")
            return data
        
        feature_names = feature_names or list(self.features.keys())
        result = data.copy()
        
        for name in feature_names:
            if name not in self.features:
                continue
            
            feature = self.features[name]
            
            try:
                if feature.computation:
                    # Evaluate computation expression
                    result[name] = eval(feature.computation, {'close': data.get('close'), 
                                                               'volume': data.get('volume'),
                                                               'returns': result.get('returns')})
                elif name == 'rsi':
                    result[name] = self._compute_rsi(data['close'], feature.lookback_periods)
                elif name == 'macd':
                    result[name] = self._compute_macd(data['close'])
                elif name == 'trend_strength':
                    result[name] = self._compute_trend_strength(data['close'], feature.lookback_periods)
                    
            except Exception as e:
                logger.error(f"Failed to compute feature {name}: {e}")
        
        return result
    
    def _compute_rsi(self, prices, period: int = 14):
        """Compute RSI"""
        if not PANDAS_AVAILABLE:
            return None
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _compute_macd(self, prices, fast: int = 12, slow: int = 26, signal: int = 9):
        """Compute MACD"""
        if not PANDAS_AVAILABLE:
            return None
        
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        return macd
    
    def _compute_trend_strength(self, prices, period: int = 20):
        """Compute trend strength"""
        if not PANDAS_AVAILABLE:
            return None
        
        returns = prices.pct_change()
        return returns.rolling(period).mean() / returns.rolling(period).std()
    
    def get_feature_names(self) -> List[str]:
        """Get all registered feature names"""
        return list(self.features.keys())
    
    def get_feature_info(self, name: str) -> Optional[FeatureDefinition]:
        """Get feature definition"""
        return self.features.get(name)


class ModelRegistry:
    """
    Model registry for versioning and management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Storage
        self.storage_path = Path(self.config.get('storage_path', 'models'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Model metadata
        self.models: Dict[str, ModelMetadata] = {}
        
        # Active deployments
        self.deployments: Dict[ModelType, str] = {}  # model_type -> model_id
        
        # Load existing models
        self._load_registry()
        
        logger.info("ModelRegistry initialized")
    
    def _load_registry(self):
        """Load model registry from disk"""
        registry_file = self.storage_path / 'registry.json'
        
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    
                for model_data in data.get('models', []):
                    metadata = ModelMetadata(
                        model_id=model_data['model_id'],
                        name=model_data['name'],
                        version=model_data['version'],
                        model_type=ModelType(model_data['model_type']),
                        status=ModelStatus(model_data['status']),
                        created_at=datetime.fromisoformat(model_data['created_at']),
                        updated_at=datetime.fromisoformat(model_data['updated_at']),
                        training_samples=model_data.get('training_samples', 0),
                        metrics=model_data.get('metrics', {}),
                        validation_metrics=model_data.get('validation_metrics', {}),
                        features=model_data.get('features', []),
                        tags=model_data.get('tags', [])
                    )
                    self.models[metadata.model_id] = metadata
                
                for model_type, model_id in data.get('deployments', {}).items():
                    self.deployments[ModelType(model_type)] = model_id
                    
                logger.info(f"Loaded {len(self.models)} models from registry")
                
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
    
    def _save_registry(self):
        """Save model registry to disk"""
        registry_file = self.storage_path / 'registry.json'
        
        try:
            data = {
                'models': [m.to_dict() for m in self.models.values()],
                'deployments': {k.value: v for k, v in self.deployments.items()},
                'updated_at': datetime.now().isoformat()
            }
            
            with open(registry_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def register_model(
        self,
        name: str,
        model_type: ModelType,
        model_object: Any,
        version: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None,
        features: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> ModelMetadata:
        """Register a new model"""
        # Generate version if not provided
        if version is None:
            existing = [m for m in self.models.values() if m.name == name]
            version = f"v{len(existing) + 1}"
        
        # Generate model ID
        model_id = hashlib.md5(f"{name}_{version}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            name=name,
            version=version,
            model_type=model_type,
            status=ModelStatus.READY,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metrics=metrics or {},
            features=features or [],
            tags=tags or []
        )
        
        # Save model artifact
        model_path = self.storage_path / model_id
        model_path.mkdir(exist_ok=True)
        
        with open(model_path / 'model.pkl', 'wb') as f:
            pickle.dump(model_object, f)
        
        with open(model_path / 'metadata.json', 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        # Register
        self.models[model_id] = metadata
        self._save_registry()
        
        logger.info(f"Model registered: {name} {version} ({model_id})")
        return metadata
    
    def load_model(self, model_id: str) -> Optional[Any]:
        """Load model artifact"""
        model_path = self.storage_path / model_id / 'model.pkl'
        
        if not model_path.exists():
            logger.error(f"Model not found: {model_id}")
            return None
        try:
        
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return None
    
    def deploy_model(self, model_id: str) -> bool:
        """Deploy a model"""
        if model_id not in self.models:
            logger.error(f"Model not found: {model_id}")
            return False
        
        metadata = self.models[model_id]
        
        # Update previous deployment
        if metadata.model_type in self.deployments:
            old_id = self.deployments[metadata.model_type]
            if old_id in self.models:
                self.models[old_id].status = ModelStatus.DEPRECATED
        
        # Deploy new model
        metadata.status = ModelStatus.DEPLOYED
        metadata.deployed_at = datetime.now()
        metadata.deployment_count += 1
        metadata.updated_at = datetime.now()
        
        self.deployments[metadata.model_type] = model_id
        self._save_registry()
        
        logger.info(f"Model deployed: {metadata.name} {metadata.version}")
        return True
    
    def rollback(self, model_type: ModelType) -> bool:
        """Rollback to previous model version"""
        # Find previous deployed model
        candidates = [
            m for m in self.models.values()
            if m.model_type == model_type 
            and m.status == ModelStatus.DEPRECATED
            and m.deployment_count > 0
        ]
        
        if not candidates:
            logger.error(f"No previous model found for {model_type.value}")
            return False
        
        # Get most recently deployed
        previous = max(candidates, key=lambda m: m.deployed_at or datetime.min)
        
        return self.deploy_model(previous.model_id)
    
    def get_deployed_model(self, model_type: ModelType) -> Optional[Any]:
        """Get currently deployed model"""
        model_id = self.deployments.get(model_type)
        if model_id:
            return self.load_model(model_id)
        return None
    
    def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata"""
        return self.models.get(model_id)
    
    def list_models(
        self,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None
    ) -> List[ModelMetadata]:
        """List models"""
        models = list(self.models.values())
        
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        
        if status:
            models = [m for m in models if m.status == status]
        
        return sorted(models, key=lambda m: m.created_at, reverse=True)
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model"""
        if model_id not in self.models:
            return False
        
        metadata = self.models[model_id]
        
        if metadata.status == ModelStatus.DEPLOYED:
            logger.error("Cannot delete deployed model")
            return False
        
        # Remove files
        model_path = self.storage_path / model_id
        if model_path.exists():
            shutil.rmtree(model_path)
        
        # Remove from registry
        del self.models[model_id]
        self._save_registry()
        
        logger.info(f"Model deleted: {model_id}")
        return True


class RetrainingPipeline:
    """
    Automated model retraining pipeline.
    """
    
    def __init__(
        self,
        registry: ModelRegistry,
        feature_store: FeatureStore,
        config: Optional[Dict[str, Any]] = None
    ):
        self.registry = registry
        self.feature_store = feature_store
        self.config = config or {}
        
        # Retraining settings
        self.retrain_interval_hours = self.config.get('retrain_interval_hours', 24)
        self.min_samples = self.config.get('min_samples', 1000)
        self.validation_split = self.config.get('validation_split', 0.2)
        
        # Performance thresholds
        self.min_accuracy = self.config.get('min_accuracy', 0.55)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)
        
        # Training callbacks
        self.training_functions: Dict[ModelType, Callable] = {}
        
        # Scheduler
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info("RetrainingPipeline initialized")
    
    def register_trainer(self, model_type: ModelType, trainer: Callable):
        """Register training function for model type"""
        self.training_functions[model_type] = trainer
        logger.info(f"Trainer registered for {model_type.value}")
    
    async def start(self):
        """Start retraining scheduler"""
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Retraining scheduler started")
    
    async def stop(self):
        """Stop retraining scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Retraining scheduler stopped")
    
    async def _scheduler_loop(self):
        """Scheduler loop"""
        while self._running:
            try:
                await self._check_and_retrain()
                await asyncio.sleep(3600)  # Check every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(3600)
    
    async def _check_and_retrain(self):
        """Check if retraining is needed"""
        for model_type in ModelType:
            model_id = self.registry.deployments.get(model_type)
            
            if not model_id:
                continue
            
            metadata = self.registry.get_model_metadata(model_id)
            
            if not metadata:
                continue
            
            # Check if retraining is needed
            hours_since_training = (datetime.now() - metadata.created_at).total_seconds() / 3600
            
            if hours_since_training >= self.retrain_interval_hours:
                logger.info(f"Triggering retraining for {model_type.value}")
                await self.retrain(model_type)
    
    async def retrain(
        self,
        model_type: ModelType,
        training_data: Optional[Any] = None
    ) -> Optional[ModelMetadata]:
        """Retrain a model"""
        if model_type not in self.training_functions:
            logger.error(f"No trainer registered for {model_type.value}")
            return None
        
        trainer = self.training_functions[model_type]
        
        try:
            # Get current model for comparison
            current_id = self.registry.deployments.get(model_type)
            current_metadata = self.registry.get_model_metadata(current_id) if current_id else None
            
            # Train new model
            logger.info(f"Training new {model_type.value} model...")
            start_time = datetime.now()
            
            result = await trainer(training_data, self.feature_store)
            
            training_duration = (datetime.now() - start_time).total_seconds()
            
            if not result or 'model' not in result:
                logger.error("Training failed - no model returned")
                return None
            
            # Validate new model
            metrics = result.get('metrics', {})
            
            if not self._validate_model(metrics):
                logger.warning("New model failed validation")
                return None
            
            # Check if new model is better
            if current_metadata and not self._is_better(metrics, current_metadata.metrics):
                logger.info("New model is not better than current")
                return None
            
            # Register new model
            new_version = f"v{int(datetime.now().timestamp())}"
            
            metadata = self.registry.register_model(
                name=f"{model_type.value}_model",
                model_type=model_type,
                model_object=result['model'],
                version=new_version,
                metrics=metrics,
                features=result.get('features', []),
                tags=['auto-retrained']
            )
            
            metadata.training_duration_seconds = training_duration
            metadata.training_samples = result.get('samples', 0)
            
            # Deploy if validation passed
            self.registry.deploy_model(metadata.model_id)
            
            logger.info(f"New model deployed: {metadata.name} {metadata.version}")
            return metadata
            
        except Exception as e:
            logger.error(f"Retraining failed: {e}")
            return None
    
    def _validate_model(self, metrics: Dict[str, float]) -> bool:
        """Validate model meets minimum requirements"""
        accuracy = metrics.get('accuracy', 0)
        max_dd = metrics.get('max_drawdown', 1)
        
        if accuracy < self.min_accuracy:
            logger.warning(f"Accuracy {accuracy:.2f} below threshold {self.min_accuracy}")
            return False
        
        if max_dd > self.max_drawdown:
            logger.warning(f"Max drawdown {max_dd:.2f} above threshold {self.max_drawdown}")
            return False
        
        return True
    
    def _is_better(self, new_metrics: Dict, old_metrics: Dict) -> bool:
        """Check if new model is better than old"""
        # Compare key metrics
        new_score = (
            new_metrics.get('accuracy', 0) * 0.4 +
            new_metrics.get('sharpe_ratio', 0) * 0.3 +
            (1 - new_metrics.get('max_drawdown', 1)) * 0.3
        )
        
        old_score = (
            old_metrics.get('accuracy', 0) * 0.4 +
            old_metrics.get('sharpe_ratio', 0) * 0.3 +
            (1 - old_metrics.get('max_drawdown', 1)) * 0.3
        )
        
        return new_score > old_score


class MLPipeline:
    """
    Main ML pipeline coordinating all components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.feature_store = FeatureStore(config.get('feature_store', {}))
        self.registry = ModelRegistry(config.get('registry', {}))
        self.retraining = RetrainingPipeline(
            self.registry,
            self.feature_store,
            config.get('retraining', {})
        )
        
        logger.info("MLPipeline initialized")
    
    async def start(self):
        """Start ML pipeline"""
        await self.retraining.start()
        logger.info("ML pipeline started")
    
    async def stop(self):
        """Stop ML pipeline"""
        await self.retraining.stop()
        logger.info("ML pipeline stopped")
    
    def get_model(self, model_type: ModelType) -> Optional[Any]:
        """Get deployed model"""
        return self.registry.get_deployed_model(model_type)
    
    def compute_features(self, data: Any, features: Optional[List[str]] = None) -> Any:
        """Compute features"""
        return self.feature_store.compute_features(data, features)
    
    def register_model(self, **kwargs) -> ModelMetadata:
        """Register a model"""
        return self.registry.register_model(**kwargs)
    
    def deploy_model(self, model_id: str) -> bool:
        """Deploy a model"""
        return self.registry.deploy_model(model_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            'models': {
                'total': len(self.registry.models),
                'deployed': len(self.registry.deployments),
                'by_type': {
                    mt.value: len([m for m in self.registry.models.values() if m.model_type == mt])
                    for mt in ModelType
                }
            },
            'features': {
                'registered': len(self.feature_store.features)
            },
            'deployments': {
                mt.value: self.registry.get_model_metadata(mid).to_dict() if mid else None
                for mt, mid in self.registry.deployments.items()
            }
        }


# Export
__all__ = [
    'MLPipeline',
    'ModelRegistry',
    'FeatureStore',
    'RetrainingPipeline',
    'ModelMetadata',
    'FeatureDefinition',
    'ModelStatus',
    'ModelType'
]
