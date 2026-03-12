"""
AutoML Pipeline and Advanced ML Components
============================================

Comprehensive ML infrastructure:
- AutoML pipeline with automatic model selection
- Feature store for centralized feature management
- Model registry with versioning
- A/B testing framework
- Concept drift detection
- Model ensemble optimizer

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
import hashlib
import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Union, Set
from enum import Enum, auto
from collections import defaultdict, deque
import threading
import numpy as np
from pathlib import Path
from scipy import stats

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    from sklearn.model_selection import cross_val_score, TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


class ModelType(Enum):
    """Model types"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    LOGISTIC_REGRESSION = "logistic_regression"
    NEURAL_NETWORK = "neural_network"
    LSTM = "lstm"
    TRANSFORMER = "transformer"
    ENSEMBLE = "ensemble"


class ModelStatus(Enum):
    """Model status"""
    TRAINING = "training"
    VALIDATING = "validating"
    READY = "ready"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class DriftType(Enum):
    """Drift types"""
    NO_DRIFT = "no_drift"
    GRADUAL = "gradual"
    SUDDEN = "sudden"
    RECURRING = "recurring"


@dataclass
class Feature:
    """Feature definition"""
    name: str
    description: str
    data_type: str  # "numeric", "categorical", "boolean"
    source: str
    
    # Computation
    computation: Optional[str] = None  # SQL or Python expression
    dependencies: List[str] = field(default_factory=list)
    
    # Statistics
    mean: float = 0.0
    std: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    null_rate: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'data_type': self.data_type,
            'source': self.source,
            'computation': self.computation,
            'dependencies': self.dependencies,
            'statistics': {
                'mean': self.mean,
                'std': self.std,
                'min': self.min_val,
                'max': self.max_val,
                'null_rate': self.null_rate
            },
            'version': self.version
        }


@dataclass
class ModelVersion:
    """Model version"""
    model_id: str
    version: int
    model_type: ModelType
    status: ModelStatus
    
    # Performance metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Training info
    training_samples: int = 0
    training_time_seconds: float = 0.0
    features_used: List[str] = field(default_factory=list)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    deployed_at: Optional[datetime] = None
    
    # Model artifact
    model_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'model_id': self.model_id,
            'version': self.version,
            'model_type': self.model_type.value,
            'status': self.status.value,
            'metrics': {
                'accuracy': self.accuracy,
                'precision': self.precision,
                'recall': self.recall,
                'f1': self.f1,
                'sharpe_ratio': self.sharpe_ratio
            },
            'training_samples': self.training_samples,
            'training_time_seconds': self.training_time_seconds,
            'features_used': self.features_used,
            'hyperparameters': self.hyperparameters,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ABTestResult:
    """A/B test result"""
    test_id: str
    model_a: str
    model_b: str
    start_time: datetime
    end_time: Optional[datetime]
    
    # Results
    model_a_trades: int = 0
    model_b_trades: int = 0
    model_a_pnl: float = 0.0
    model_b_pnl: float = 0.0
    model_a_win_rate: float = 0.0
    model_b_win_rate: float = 0.0
    
    # Statistical significance
    p_value: float = 1.0
    is_significant: bool = False
    winner: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'test_id': self.test_id,
            'model_a': self.model_a,
            'model_b': self.model_b,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'model_a_trades': self.model_a_trades,
            'model_b_trades': self.model_b_trades,
            'model_a_pnl': self.model_a_pnl,
            'model_b_pnl': self.model_b_pnl,
            'p_value': self.p_value,
            'is_significant': self.is_significant,
            'winner': self.winner
        }


@dataclass
class DriftReport:
    """Drift detection report"""
    feature_name: str
    timestamp: datetime
    drift_type: DriftType
    drift_score: float
    
    # Statistics
    reference_mean: float = 0.0
    current_mean: float = 0.0
    reference_std: float = 0.0
    current_std: float = 0.0
    
    # Distribution comparison
    ks_statistic: float = 0.0
    ks_pvalue: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            'feature_name': self.feature_name,
            'timestamp': self.timestamp.isoformat(),
            'drift_type': self.drift_type.value,
            'drift_score': self.drift_score,
            'reference_mean': self.reference_mean,
            'current_mean': self.current_mean,
            'ks_statistic': self.ks_statistic,
            'ks_pvalue': self.ks_pvalue
        }


class FeatureStore:
    """
    Centralized feature management
    """
    
    def __init__(self, storage_path: str = "./feature_store"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Feature registry
        self.features: Dict[str, Feature] = {}
        
        # Feature values cache
        self.feature_cache: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Feature groups
        self.feature_groups: Dict[str, List[str]] = {}
        
        self._lock = threading.RLock()
        
        # Load existing features
        self._load_features()
        
        logger.info("FeatureStore initialized")
    
    def _load_features(self):
        """Load features from storage"""
        feature_file = self.storage_path / "features.json"
        if feature_file.exists():
            try:
                with open(feature_file, 'r') as f:
                    data = json.load(f)
                    for name, feat_data in data.items():
                        self.features[name] = Feature(
                            name=feat_data['name'],
                            description=feat_data['description'],
                            data_type=feat_data['data_type'],
                            source=feat_data['source'],
                            computation=feat_data.get('computation'),
                            dependencies=feat_data.get('dependencies', []),
                            version=feat_data.get('version', 1)
                        )
            except Exception as e:
                logger.error(f"Failed to load features: {e}")
    
    def _save_features(self):
        """Save features to storage"""
        feature_file = self.storage_path / "features.json"
        try:
            with open(feature_file, 'w') as f:
                data = {name: feat.to_dict() for name, feat in self.features.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save features: {e}")
    
    def register_feature(self, feature: Feature):
        """Register a new feature"""
        with self._lock:
            if feature.name in self.features:
                # Update version
                feature.version = self.features[feature.name].version + 1
            
            self.features[feature.name] = feature
            self._save_features()
            
            logger.info(f"Feature registered: {feature.name} v{feature.version}")
    
    def get_feature(self, name: str) -> Optional[Feature]:
        """Get a feature definition"""
        return self.features.get(name)
    
    def get_feature_value(self, name: str, entity_id: str) -> Optional[Any]:
        """Get feature value for an entity"""
        with self._lock:
            return self.feature_cache.get(name, {}).get(entity_id)
    
    def set_feature_value(self, name: str, entity_id: str, value: Any):
        """Set feature value for an entity"""
        with self._lock:
            self.feature_cache[name][entity_id] = value
    
    def get_feature_vector(
        self,
        feature_names: List[str],
        entity_id: str
    ) -> Dict[str, Any]:
        """Get multiple feature values"""
        with self._lock:
            return {
                name: self.feature_cache.get(name, {}).get(entity_id)
                for name in feature_names
            }
    
    def create_feature_group(self, group_name: str, feature_names: List[str]):
        """Create a feature group"""
        with self._lock:
            self.feature_groups[group_name] = feature_names
    
    def get_feature_group(self, group_name: str) -> List[str]:
        """Get features in a group"""
        return self.feature_groups.get(group_name, [])
    
    def compute_statistics(self, name: str, values: List[float]):
        """Compute and update feature statistics"""
        if name not in self.features:
            return
        
        feature = self.features[name]
        
        if values:
            feature.mean = np.mean(values)
            feature.std = np.std(values)
            feature.min_val = min(values)
            feature.max_val = max(values)
            feature.null_rate = sum(1 for v in values if v is None) / len(values)
            feature.updated_at = datetime.now()
            
            self._save_features()
    
    def list_features(self) -> List[Dict]:
        """List all features"""
        return [f.to_dict() for f in self.features.values()]


class ModelRegistry:
    """
    Model versioning and registry
    """
    
    def __init__(self, storage_path: str = "./model_registry"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Model versions
        self.models: Dict[str, List[ModelVersion]] = defaultdict(list)
        
        # Currently deployed models
        self.deployed: Dict[str, ModelVersion] = {}
        
        self._lock = threading.RLock()
        
        # Load existing models
        self._load_registry()
        
        logger.info("ModelRegistry initialized")
    
    def _load_registry(self):
        """Load registry from storage"""
        registry_file = self.storage_path / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    for model_id, versions in data.get('models', {}).items():
                        for v in versions:
                            mv = ModelVersion(
                                model_id=v['model_id'],
                                version=v['version'],
                                model_type=ModelType(v['model_type']),
                                status=ModelStatus(v['status']),
                                accuracy=v.get('metrics', {}).get('accuracy', 0),
                                precision=v.get('metrics', {}).get('precision', 0),
                                recall=v.get('metrics', {}).get('recall', 0),
                                f1=v.get('metrics', {}).get('f1', 0),
                                features_used=v.get('features_used', []),
                                hyperparameters=v.get('hyperparameters', {}),
                                model_path=v.get('model_path')
                            )
                            self.models[model_id].append(mv)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
    
    def _save_registry(self):
        """Save registry to storage"""
        registry_file = self.storage_path / "registry.json"
        try:
            data = {
                'models': {
                    model_id: [v.to_dict() for v in versions]
                    for model_id, versions in self.models.items()
                },
                'deployed': {
                    model_id: v.to_dict()
                    for model_id, v in self.deployed.items()
                }
            }
            with open(registry_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def register_model(
        self,
        model_id: str,
        model_type: ModelType,
        model_object: Any,
        metrics: Dict[str, float],
        features_used: List[str],
        hyperparameters: Dict[str, Any]
    ) -> ModelVersion:
        """Register a new model version"""
        with self._lock:
            # Get next version
            existing = self.models.get(model_id, [])
            version = len(existing) + 1
            
            # Save model artifact
            model_path = self.storage_path / f"{model_id}_v{version}.pkl"
            try:
                with open(model_path, 'wb') as f:
                    pickle.dump(model_object, f)
            except Exception as e:
                logger.error(f"Failed to save model: {e}")
                model_path = None
            
            # Create version
            mv = ModelVersion(
                model_id=model_id,
                version=version,
                model_type=model_type,
                status=ModelStatus.READY,
                accuracy=metrics.get('accuracy', 0),
                precision=metrics.get('precision', 0),
                recall=metrics.get('recall', 0),
                f1=metrics.get('f1', 0),
                sharpe_ratio=metrics.get('sharpe_ratio', 0),
                features_used=features_used,
                hyperparameters=hyperparameters,
                model_path=str(model_path) if model_path else None
            )
            
            self.models[model_id].append(mv)
            self._save_registry()
            
            logger.info(f"Model registered: {model_id} v{version}")
            
            return mv
    
    def get_model(self, model_id: str, version: Optional[int] = None) -> Optional[ModelVersion]:
        """Get a model version"""
        with self._lock:
            versions = self.models.get(model_id, [])
            
            if not versions:
                return None
            
            if version:
                for v in versions:
                    if v.version == version:
                        return v
                return None
            
            # Return latest
            return versions[-1]
    
    def load_model(self, model_id: str, version: Optional[int] = None) -> Optional[Any]:
        """Load a model object"""
        mv = self.get_model(model_id, version)
        
        if not mv or not mv.model_path:
            return None
        try:
        
            with open(mv.model_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    def deploy_model(self, model_id: str, version: int) -> bool:
        """Deploy a model version"""
        with self._lock:
            mv = self.get_model(model_id, version)
            
            if not mv:
                return False
            
            # Deprecate current deployment
            if model_id in self.deployed:
                self.deployed[model_id].status = ModelStatus.DEPRECATED
            
            # Deploy new version
            mv.status = ModelStatus.DEPLOYED
            mv.deployed_at = datetime.now()
            self.deployed[model_id] = mv
            
            self._save_registry()
            
            logger.info(f"Model deployed: {model_id} v{version}")
            
            return True
    
    def get_deployed_model(self, model_id: str) -> Optional[ModelVersion]:
        """Get currently deployed model"""
        return self.deployed.get(model_id)
    
    def list_models(self) -> Dict[str, List[Dict]]:
        """List all models"""
        return {
            model_id: [v.to_dict() for v in versions]
            for model_id, versions in self.models.items()
        }


class AutoMLPipeline:
    """
    Automatic machine learning pipeline
    """
    
    def __init__(
        self,
        feature_store: Optional[FeatureStore] = None,
        model_registry: Optional[ModelRegistry] = None
    ):
        self.feature_store = feature_store or FeatureStore()
        self.model_registry = model_registry or ModelRegistry()
        
        # Model configurations to try
        self.model_configs = [
            {
                'type': ModelType.RANDOM_FOREST,
                'params': {'n_estimators': 100, 'max_depth': 10}
            },
            {
                'type': ModelType.GRADIENT_BOOSTING,
                'params': {'n_estimators': 100, 'max_depth': 5}
            },
            {
                'type': ModelType.LOGISTIC_REGRESSION,
                'params': {'C': 1.0, 'max_iter': 1000}
            }
        ]
        
        # Best model tracking
        self.best_model: Optional[ModelVersion] = None
        
        self._lock = threading.RLock()
        
        logger.info("AutoMLPipeline initialized")
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_id: str,
        feature_names: List[str]
    ) -> ModelVersion:
        """Train and select best model"""
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn not available")
        
        best_score = -float('inf')
        best_model = None
        best_config = None
        
        # Try each model configuration
        for config in self.model_configs:
            try:
                model = self._create_model(config['type'], config['params'])
                
                # Cross-validation
                tscv = TimeSeriesSplit(n_splits=5)
                scores = cross_val_score(model, X, y, cv=tscv, scoring='f1')
                avg_score = np.mean(scores)
                
                logger.info(f"{config['type'].value}: CV F1 = {avg_score:.4f}")
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_model = model
                    best_config = config
                    
            except Exception as e:
                logger.error(f"Failed to train {config['type'].value}: {e}")
        
        if best_model is None:
            raise RuntimeError("All model training failed")
        
        # Train best model on full data
        best_model.fit(X, y)
        
        # Calculate metrics
        y_pred = best_model.predict(X)
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y, y_pred, average='weighted', zero_division=0),
            'f1': f1_score(y, y_pred, average='weighted', zero_division=0)
        }
        
        # Register model
        mv = self.model_registry.register_model(
            model_id=model_id,
            model_type=best_config['type'],
            model_object=best_model,
            metrics=metrics,
            features_used=feature_names,
            hyperparameters=best_config['params']
        )
        
        with self._lock:
            self.best_model = mv
        
        return mv
    
    def _create_model(self, model_type: ModelType, params: Dict) -> Any:
        """Create a model instance"""
        if model_type == ModelType.RANDOM_FOREST:
            return RandomForestClassifier(**params)
        elif model_type == ModelType.GRADIENT_BOOSTING:
            return GradientBoostingClassifier(**params)
        elif model_type == ModelType.LOGISTIC_REGRESSION:
            return LogisticRegression(**params)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def predict(self, model_id: str, X: np.ndarray) -> np.ndarray:
        """Make predictions using deployed model"""
        model = self.model_registry.load_model(model_id)
        
        if model is None:
            raise RuntimeError(f"Model not found: {model_id}")
        
        return model.predict(X)
    
    def predict_proba(self, model_id: str, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities"""
        model = self.model_registry.load_model(model_id)
        
        if model is None:
            raise RuntimeError(f"Model not found: {model_id}")
        
        return model.predict_proba(X)


class ABTestingFramework:
    """
    A/B testing for model comparison
    """
    
    def __init__(self, min_samples: int = 100, significance_level: float = 0.05):
        self.min_samples = min_samples
        self.significance_level = significance_level
        
        # Active tests
        self.active_tests: Dict[str, ABTestResult] = {}
        
        # Completed tests
        self.completed_tests: List[ABTestResult] = []
        
        # Trade results per test
        self.trade_results: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: {'a': [], 'b': []}
        )
        
        self._lock = threading.RLock()
        
        logger.info("ABTestingFramework initialized")
    
    def start_test(self, test_id: str, model_a: str, model_b: str) -> ABTestResult:
        """Start a new A/B test"""
        with self._lock:
            result = ABTestResult(
                test_id=test_id,
                model_a=model_a,
                model_b=model_b,
                start_time=datetime.now(),
                end_time=None
            )
            
            self.active_tests[test_id] = result
            self.trade_results[test_id] = {'a': [], 'b': []}
            
            logger.info(f"A/B test started: {test_id}")
            
            return result
    
    def record_trade(self, test_id: str, model: str, pnl: float):
        """Record a trade result"""
        with self._lock:
            if test_id not in self.active_tests:
                return
            
            variant = 'a' if model == self.active_tests[test_id].model_a else 'b'
            self.trade_results[test_id][variant].append(pnl)
            
            # Update counts
            result = self.active_tests[test_id]
            if variant == 'a':
                result.model_a_trades += 1
                result.model_a_pnl += pnl
            else:
                result.model_b_trades += 1
                result.model_b_pnl += pnl
            
            # Check if we have enough samples
            if (len(self.trade_results[test_id]['a']) >= self.min_samples and
                len(self.trade_results[test_id]['b']) >= self.min_samples):
                self._evaluate_test(test_id)
    
    def _evaluate_test(self, test_id: str):
        """Evaluate test results"""
        with self._lock:
            result = self.active_tests[test_id]
            trades_a = self.trade_results[test_id]['a']
            trades_b = self.trade_results[test_id]['b']
            
            # Calculate win rates
            result.model_a_win_rate = sum(1 for t in trades_a if t > 0) / len(trades_a) if trades_a else 0
            result.model_b_win_rate = sum(1 for t in trades_b if t > 0) / len(trades_b) if trades_b else 0
            
            try:
                # Statistical test (t-test)
                t_stat, p_value = stats.ttest_ind(trades_a, trades_b)
                result.p_value = p_value
                result.is_significant = p_value < self.significance_level
                
                if result.is_significant:
                    if np.mean(trades_a) > np.mean(trades_b):
                        result.winner = result.model_a
                    else:
                        result.winner = result.model_b
            except Exception as e:
                logger.error(f"Statistical test failed: {e}")
    
    def end_test(self, test_id: str) -> Optional[ABTestResult]:
        """End an A/B test"""
        with self._lock:
            if test_id not in self.active_tests:
                return None
            
            result = self.active_tests.pop(test_id)
            result.end_time = datetime.now()
            
            self._evaluate_test(test_id)
            self.completed_tests.append(result)
            
            logger.info(f"A/B test ended: {test_id}, winner: {result.winner}")
            
            return result
    
    def get_assignment(self, test_id: str) -> str:
        """Get model assignment for a new trade (50/50 split)"""
        with self._lock:
            if test_id not in self.active_tests:
                return ""
            
            result = self.active_tests[test_id]
            
            # Simple 50/50 split
            if result.model_a_trades <= result.model_b_trades:
                return result.model_a
            else:
                return result.model_b
    
    def get_test_status(self, test_id: str) -> Optional[Dict]:
        """Get current test status"""
        with self._lock:
            if test_id in self.active_tests:
                return self.active_tests[test_id].to_dict()
            
            for test in self.completed_tests:
                if test.test_id == test_id:
                    return test.to_dict()
            
            return None


class ConceptDriftDetector:
    """
    Detects concept drift in features and model performance
    """
    
    def __init__(
        self,
        window_size: int = 1000,
        drift_threshold: float = 0.05
    ):
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        
        # Reference distributions
        self.reference_data: Dict[str, np.ndarray] = {}
        
        # Current windows
        self.current_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        
        # Drift history
        self.drift_history: List[DriftReport] = []
        
        # Callbacks
        self.on_drift: List[Callable] = []
        
        self._lock = threading.RLock()
        
        logger.info("ConceptDriftDetector initialized")
    
    def set_reference(self, feature_name: str, data: np.ndarray):
        """Set reference distribution for a feature"""
        with self._lock:
            self.reference_data[feature_name] = data
    
    def add_observation(self, feature_name: str, value: float) -> Optional[DriftReport]:
        """Add an observation and check for drift"""
        with self._lock:
            self.current_windows[feature_name].append(value)
            
            # Check if we have enough data
            if len(self.current_windows[feature_name]) < self.window_size // 2:
                return None
            
            # Check for drift
            return self._check_drift(feature_name)
    
    def _check_drift(self, feature_name: str) -> Optional[DriftReport]:
        """Check for drift using KS test"""
        reference = self.reference_data.get(feature_name)
        
        if reference is None:
            return None
        
        current = np.array(list(self.current_windows[feature_name]))
        
        try:
            ks_stat, ks_pvalue = stats.ks_2samp(reference, current)
            
            # Determine drift type
            if ks_pvalue >= self.drift_threshold:
                drift_type = DriftType.NO_DRIFT
            elif ks_stat > 0.3:
                drift_type = DriftType.SUDDEN
            else:
                drift_type = DriftType.GRADUAL
            
            report = DriftReport(
                feature_name=feature_name,
                timestamp=datetime.now(),
                drift_type=drift_type,
                drift_score=ks_stat,
                reference_mean=np.mean(reference),
                current_mean=np.mean(current),
                reference_std=np.std(reference),
                current_std=np.std(current),
                ks_statistic=ks_stat,
                ks_pvalue=ks_pvalue
            )
            
            if drift_type != DriftType.NO_DRIFT:
                self.drift_history.append(report)
                
                # Fire callbacks
                for callback in self.on_drift:
                    try:
                        callback(report)
                    except Exception as e:
                        logger.error(f"Drift callback error: {e}")
            
            return report
            
        except Exception as e:
            logger.error(f"Drift detection failed: {e}")
            return None
    
    def get_drift_summary(self) -> Dict[str, Any]:
        """Get drift summary"""
        with self._lock:
            recent = [d for d in self.drift_history if d.timestamp > datetime.now() - timedelta(hours=24)]
            
            return {
                'total_drifts_detected': len(self.drift_history),
                'drifts_last_24h': len(recent),
                'features_with_drift': list(set(d.feature_name for d in recent)),
                'recent_reports': [d.to_dict() for d in recent[-10:]]
            }


class EnsembleOptimizer:
    """
    Optimizes model ensemble weights
    """
    
    def __init__(self, model_registry: Optional[ModelRegistry] = None):
        self.model_registry = model_registry or ModelRegistry()
        
        # Ensemble weights
        self.weights: Dict[str, float] = {}
        
        # Performance history
        self.performance_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        self._lock = threading.RLock()
        
        logger.info("EnsembleOptimizer initialized")
    
    def add_model(self, model_id: str, initial_weight: float = 1.0):
        """Add a model to the ensemble"""
        with self._lock:
            self.weights[model_id] = initial_weight
            self._normalize_weights()
    
    def remove_model(self, model_id: str):
        """Remove a model from the ensemble"""
        with self._lock:
            if model_id in self.weights:
                del self.weights[model_id]
                self._normalize_weights()
    
    def _normalize_weights(self):
        """Normalize weights to sum to 1"""
        total = sum(self.weights.values())
        if total > 0:
            for model_id in self.weights:
                self.weights[model_id] /= total
    
    def record_performance(self, model_id: str, score: float):
        """Record model performance"""
        with self._lock:
            self.performance_history[model_id].append(score)
    
    def optimize_weights(self, method: str = "performance") -> Dict[str, float]:
        """Optimize ensemble weights"""
        with self._lock:
            if method == "performance":
                return self._optimize_by_performance()
            elif method == "equal":
                return self._optimize_equal()
            else:
                return dict(self.weights)
    
    def _optimize_by_performance(self) -> Dict[str, float]:
        """Optimize weights based on recent performance"""
        new_weights = {}
        
        for model_id in self.weights:
            history = list(self.performance_history.get(model_id, []))
            
            if history:
                # Use exponentially weighted average
                weights = np.exp(np.linspace(-1, 0, len(history)))
                weights /= weights.sum()
                avg_performance = np.average(history, weights=weights)
                new_weights[model_id] = max(0.01, avg_performance)
            else:
                new_weights[model_id] = 0.01
        
        # Normalize
        total = sum(new_weights.values())
        if total > 0:
            for model_id in new_weights:
                new_weights[model_id] /= total
        
        self.weights = new_weights
        return dict(self.weights)
    
    def _optimize_equal(self) -> Dict[str, float]:
        """Equal weights for all models"""
        n = len(self.weights)
        if n > 0:
            equal_weight = 1.0 / n
            for model_id in self.weights:
                self.weights[model_id] = equal_weight
        
        return dict(self.weights)
    
    def predict_ensemble(
        self,
        predictions: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Make ensemble prediction"""
        with self._lock:
            weighted_preds = None
            
            for model_id, preds in predictions.items():
                weight = self.weights.get(model_id, 0)
                
                if weighted_preds is None:
                    weighted_preds = weight * preds
                else:
                    weighted_preds += weight * preds
            
            return weighted_preds if weighted_preds is not None else np.array([])
    
    def get_weights(self) -> Dict[str, float]:
        """Get current weights"""
        return dict(self.weights)


# Singleton instances
_feature_store: Optional[FeatureStore] = None
_model_registry: Optional[ModelRegistry] = None
_automl: Optional[AutoMLPipeline] = None


def get_feature_store() -> FeatureStore:
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
    return _feature_store


def get_model_registry() -> ModelRegistry:
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry


def get_automl_pipeline() -> AutoMLPipeline:
    global _automl
    if _automl is None:
        _automl = AutoMLPipeline()
    return _automl


# Export
__all__ = [
    'AutoMLPipeline',
    'FeatureStore',
    'ModelRegistry',
    'ABTestingFramework',
    'ConceptDriftDetector',
    'EnsembleOptimizer',
    'Feature',
    'ModelVersion',
    'ModelType',
    'ModelStatus',
    'ABTestResult',
    'DriftReport',
    'DriftType',
    'get_feature_store',
    'get_model_registry',
    'get_automl_pipeline'
]
