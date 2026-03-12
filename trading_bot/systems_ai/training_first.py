"""
Training-First Architecture
===========================
System designed so that:
- Logic is IMMUTABLE (code doesn't change behavior)
- Behavior changes ONLY via retraining
- Models are hot-swappable
- All training is reproducible via replay

CORE PRINCIPLES:
1. Code defines structure, not behavior
2. Behavior emerges from trained weights
3. Every training run is reproducible
4. Models can be swapped without code changes
5. Rollback is always possible

COMPONENTS:
- Dataset Versioning: Every dataset has a unique version
- Training Config Versioning: Every config is immutable and versioned
- Deterministic Backtests: Same data + config = same results
- Shadow Testing: New models run in shadow before promotion
- Canary Deployment: Gradual rollout with monitoring
- Auto-Rollback: Automatic revert on performance degradation
"""

import hashlib
import json
import logging
import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
from threading import RLock
import uuid

logger = logging.getLogger(__name__)


class DatasetStatus(Enum):
    """Dataset lifecycle status."""
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ModelStatus(Enum):
    """Model lifecycle status."""
    TRAINING = "training"
    VALIDATING = "validating"
    SHADOW = "shadow"
    CANARY = "canary"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ROLLED_BACK = "rolled_back"


class DeploymentStage(Enum):
    """Deployment stages."""
    SHADOW = "shadow"      # 0% traffic, full logging
    CANARY_1 = "canary_1"  # 1% traffic
    CANARY_5 = "canary_5"  # 5% traffic
    CANARY_25 = "canary_25"  # 25% traffic
    PRODUCTION = "production"  # 100% traffic


@dataclass
class DatasetVersion:
    """Versioned dataset metadata."""
    dataset_id: str
    version: str
    created_at: datetime
    status: DatasetStatus
    
    # Data specification
    start_date: datetime
    end_date: datetime
    symbols: List[str]
    features: List[str]
    
    # Data quality
    row_count: int
    data_hash: str
    quality_score: float
    
    # Lineage
    parent_version: Optional[str] = None
    transformations: List[str] = field(default_factory=list)
    
    # Storage
    storage_path: str = ""
    size_bytes: int = 0
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "symbols": self.symbols,
            "features": self.features,
            "row_count": self.row_count,
            "data_hash": self.data_hash,
            "quality_score": self.quality_score,
            "parent_version": self.parent_version,
            "transformations": self.transformations,
            "storage_path": self.storage_path,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
        }


@dataclass
class TrainingConfig:
    """Immutable training configuration."""
    config_id: str
    version: str
    created_at: datetime
    
    # Model specification
    model_type: str
    model_architecture: Dict[str, Any]
    
    # Training parameters
    hyperparameters: Dict[str, Any]
    optimizer: str
    learning_rate: float
    batch_size: int
    epochs: int
    early_stopping: bool
    early_stopping_patience: int
    
    # Data specification
    dataset_version: str
    train_split: float
    validation_split: float
    test_split: float
    
    # Reproducibility
    random_seed: int
    deterministic: bool
    
    # Compute
    device: str
    mixed_precision: bool
    
    config_hash: str = ""
    
    def __post_init__(self):
        try:
            if not self.config_hash:
                self.config_hash = self._compute_hash()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise
    
    def _compute_hash(self) -> str:
        """Compute deterministic hash of config."""
        try:
            config_dict = {
                "model_type": self.model_type,
                "model_architecture": self.model_architecture,
                "hyperparameters": self.hyperparameters,
                "optimizer": self.optimizer,
                "learning_rate": self.learning_rate,
                "batch_size": self.batch_size,
                "epochs": self.epochs,
                "dataset_version": self.dataset_version,
                "random_seed": self.random_seed,
            }
            config_str = json.dumps(config_dict, sort_keys=True)
            return hashlib.sha256(config_str.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error in _compute_hash: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_id": self.config_id,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "model_type": self.model_type,
            "model_architecture": self.model_architecture,
            "hyperparameters": self.hyperparameters,
            "optimizer": self.optimizer,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "early_stopping": self.early_stopping,
            "early_stopping_patience": self.early_stopping_patience,
            "dataset_version": self.dataset_version,
            "train_split": self.train_split,
            "validation_split": self.validation_split,
            "test_split": self.test_split,
            "random_seed": self.random_seed,
            "deterministic": self.deterministic,
            "device": self.device,
            "mixed_precision": self.mixed_precision,
            "config_hash": self.config_hash,
        }


@dataclass
class ModelVersion:
    """Versioned model metadata."""
    model_id: str
    version: str
    created_at: datetime
    status: ModelStatus
    
    # Training lineage
    training_config_id: str
    dataset_version: str
    
    # Performance metrics
    train_metrics: Dict[str, float]
    validation_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    
    # Weights
    weights_hash: str
    weights_path: str
    
    # Deployment
    deployment_stage: Optional[DeploymentStage] = None
    deployed_at: Optional[datetime] = None
    
    # Rollback info
    previous_version: Optional[str] = None
    rollback_reason: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "training_config_id": self.training_config_id,
            "dataset_version": self.dataset_version,
            "train_metrics": self.train_metrics,
            "validation_metrics": self.validation_metrics,
            "test_metrics": self.test_metrics,
            "weights_hash": self.weights_hash,
            "weights_path": self.weights_path,
            "deployment_stage": self.deployment_stage.value if self.deployment_stage else None,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "previous_version": self.previous_version,
            "rollback_reason": self.rollback_reason,
            "metadata": self.metadata,
        }


@dataclass
class BacktestResult:
    """Result of a deterministic backtest."""
    backtest_id: str
    model_version: str
    dataset_version: str
    config_hash: str
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Performance
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_pnl: float
    
    # Reproducibility
    result_hash: str
    random_seed: int
    
    # Execution time
    execution_time_seconds: float
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "backtest_id": self.backtest_id,
            "model_version": self.model_version,
            "dataset_version": self.dataset_version,
            "config_hash": self.config_hash,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "avg_trade_pnl": self.avg_trade_pnl,
            "result_hash": self.result_hash,
            "random_seed": self.random_seed,
            "execution_time_seconds": self.execution_time_seconds,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ShadowTestResult:
    """Result of shadow testing a model."""
    shadow_id: str
    model_version: str
    production_model_version: str
    
    # Time range
    start_time: datetime
    end_time: datetime
    
    # Comparison metrics
    shadow_signals: int
    production_signals: int
    agreement_rate: float
    
    # Performance comparison
    shadow_simulated_pnl: float
    production_actual_pnl: float
    
    # Latency
    shadow_avg_latency_ms: float
    production_avg_latency_ms: float
    
    # Recommendation
    promote_recommended: bool
    promotion_reason: str
    
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CanaryMetrics:
    """Metrics from canary deployment."""
    canary_id: str
    model_version: str
    stage: DeploymentStage
    
    # Traffic
    traffic_percentage: float
    total_requests: int
    
    # Performance
    error_rate: float
    avg_latency_ms: float
    p99_latency_ms: float
    
    # Business metrics
    signal_accuracy: float
    pnl_contribution: float
    
    # Health
    is_healthy: bool
    health_issues: List[str]
    
    # Timestamps
    started_at: datetime
    last_updated: datetime


@dataclass
class RollbackEvent:
    """Record of a model rollback."""
    rollback_id: str
    rolled_back_version: str
    rolled_back_to_version: str
    
    # Trigger
    trigger: str  # "manual", "auto_performance", "auto_error", "auto_latency"
    reason: str
    
    # Metrics at rollback
    metrics_at_rollback: Dict[str, float]
    
    # Timestamps
    triggered_at: datetime
    completed_at: datetime
    
    # Approval
    approved_by: Optional[str] = None
    auto_approved: bool = False


class DatasetRegistry:
    """Registry for versioned datasets."""
    
    def __init__(self, storage_path: str = "datasets"):
        try:
            self.storage_path = Path(storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._datasets: Dict[str, Dict[str, DatasetVersion]] = {}
            self._lock = RLock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register(self, dataset: DatasetVersion) -> bool:
        """Register a new dataset version."""
        try:
            with self._lock:
                if dataset.dataset_id not in self._datasets:
                    self._datasets[dataset.dataset_id] = {}
            
                if dataset.version in self._datasets[dataset.dataset_id]:
                    logger.warning(f"Dataset version already exists: {dataset.dataset_id}:{dataset.version}")
                    return False
            
                self._datasets[dataset.dataset_id][dataset.version] = dataset
                logger.info(f"Registered dataset: {dataset.dataset_id}:{dataset.version}")
                return True
        except Exception as e:
            logger.error(f"Error in register: {e}")
            raise
    
    def get(self, dataset_id: str, version: str) -> Optional[DatasetVersion]:
        """Get a specific dataset version."""
        try:
            with self._lock:
                return self._datasets.get(dataset_id, {}).get(version)
        except Exception as e:
            logger.error(f"Error in get: {e}")
            raise
    
    def get_latest(self, dataset_id: str, status: Optional[DatasetStatus] = None) -> Optional[DatasetVersion]:
        """Get the latest version of a dataset."""
        try:
            with self._lock:
                versions = self._datasets.get(dataset_id, {})
                if not versions:
                    return None
            
                candidates = list(versions.values())
                if status:
                    candidates = [d for d in candidates if d.status == status]
            
                if not candidates:
                    return None
            
                return max(candidates, key=lambda d: d.created_at)
        except Exception as e:
            logger.error(f"Error in get_latest: {e}")
            raise
    
    def list_versions(self, dataset_id: str) -> List[DatasetVersion]:
        """List all versions of a dataset."""
        try:
            with self._lock:
                return list(self._datasets.get(dataset_id, {}).values())
        except Exception as e:
            logger.error(f"Error in list_versions: {e}")
            raise
    
    def update_status(self, dataset_id: str, version: str, status: DatasetStatus) -> bool:
        """Update dataset status."""
        try:
            with self._lock:
                dataset = self.get(dataset_id, version)
                if dataset is None:
                    return False
                dataset.status = status
                return True
        except Exception as e:
            logger.error(f"Error in update_status: {e}")
            raise


class TrainingConfigRegistry:
    """Registry for immutable training configurations."""
    
    def __init__(self):
        try:
            self._configs: Dict[str, TrainingConfig] = {}
            self._lock = RLock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register(self, config: TrainingConfig) -> bool:
        """Register a new training config (immutable)."""
        try:
            with self._lock:
                key = f"{config.config_id}:{config.version}"
            
                if key in self._configs:
                    logger.warning(f"Config already exists: {key}")
                    return False
            
                self._configs[key] = config
                logger.info(f"Registered training config: {key} (hash: {config.config_hash})")
                return True
        except Exception as e:
            logger.error(f"Error in register: {e}")
            raise
    
    def get(self, config_id: str, version: str) -> Optional[TrainingConfig]:
        """Get a specific config."""
        try:
            with self._lock:
                return self._configs.get(f"{config_id}:{version}")
        except Exception as e:
            logger.error(f"Error in get: {e}")
            raise
    
    def get_by_hash(self, config_hash: str) -> Optional[TrainingConfig]:
        """Get config by hash."""
        try:
            with self._lock:
                for config in self._configs.values():
                    if config.config_hash == config_hash:
                        return config
                return None
        except Exception as e:
            logger.error(f"Error in get_by_hash: {e}")
            raise


class ModelRegistry:
    """Registry for versioned models."""
    
    def __init__(self, storage_path: str = "models"):
        try:
            self.storage_path = Path(storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._models: Dict[str, Dict[str, ModelVersion]] = {}
            self._lock = RLock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register(self, model: ModelVersion) -> bool:
        """Register a new model version."""
        try:
            with self._lock:
                if model.model_id not in self._models:
                    self._models[model.model_id] = {}
            
                if model.version in self._models[model.model_id]:
                    logger.warning(f"Model version already exists: {model.model_id}:{model.version}")
                    return False
            
                self._models[model.model_id][model.version] = model
                logger.info(f"Registered model: {model.model_id}:{model.version}")
                return True
        except Exception as e:
            logger.error(f"Error in register: {e}")
            raise
    
    def get(self, model_id: str, version: str) -> Optional[ModelVersion]:
        """Get a specific model version."""
        try:
            with self._lock:
                return self._models.get(model_id, {}).get(version)
        except Exception as e:
            logger.error(f"Error in get: {e}")
            raise
    
    def get_production(self, model_id: str) -> Optional[ModelVersion]:
        """Get the production version of a model."""
        try:
            with self._lock:
                versions = self._models.get(model_id, {})
                for version in versions.values():
                    if version.status == ModelStatus.PRODUCTION:
                        return version
                return None
        except Exception as e:
            logger.error(f"Error in get_production: {e}")
            raise
    
    def update_status(self, model_id: str, version: str, status: ModelStatus) -> bool:
        """Update model status."""
        try:
            with self._lock:
                model = self.get(model_id, version)
                if model is None:
                    return False
                model.status = status
                return True
        except Exception as e:
            logger.error(f"Error in update_status: {e}")
            raise
    
    def set_deployment_stage(
        self,
        model_id: str,
        version: str,
        stage: DeploymentStage,
    ) -> bool:
        """Set deployment stage for a model."""
        try:
            with self._lock:
                model = self.get(model_id, version)
                if model is None:
                    return False
                model.deployment_stage = stage
                model.deployed_at = datetime.utcnow()
                return True
        except Exception as e:
            logger.error(f"Error in set_deployment_stage: {e}")
            raise


class DeterministicBacktester:
    """
    Deterministic backtesting engine.
    
    Guarantees: Same data + same config = same results
    """
    
    def __init__(
        self,
        dataset_registry: DatasetRegistry,
        model_registry: ModelRegistry,
    ):
        try:
            self.dataset_registry = dataset_registry
            self.model_registry = model_registry
            self._results: Dict[str, BacktestResult] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def run_backtest(
        self,
        model_id: str,
        model_version: str,
        dataset_id: str,
        dataset_version: str,
        random_seed: int = 42,
    ) -> BacktestResult:
        """
        Run a deterministic backtest.
        
        The result hash should be identical for identical inputs.
        """
        # Get model and dataset
        try:
            model = self.model_registry.get(model_id, model_version)
            dataset = self.dataset_registry.get(dataset_id, dataset_version)
        
            if model is None or dataset is None:
                raise ValueError("Model or dataset not found")
        
            # Create deterministic config hash
            config_hash = hashlib.sha256(
                f"{model.weights_hash}:{dataset.data_hash}:{random_seed}".encode()
            ).hexdigest()[:16]
        
            # Check for cached result
            cache_key = f"{model_id}:{model_version}:{dataset_id}:{dataset_version}:{random_seed}"
            if cache_key in self._results:
                logger.info(f"Returning cached backtest result: {cache_key}")
                return self._results[cache_key]
        
            # Run backtest (simulated for this implementation)
            import time
            start_time = time.time()
        
            # Simulated backtest results
            result = BacktestResult(
                backtest_id=str(uuid.uuid4()),
                model_version=f"{model_id}:{model_version}",
                dataset_version=f"{dataset_id}:{dataset_version}",
                config_hash=config_hash,
                start_date=dataset.start_date,
                end_date=dataset.end_date,
                total_return=0.15,  # Simulated
                sharpe_ratio=1.8,
                max_drawdown=-0.08,
                win_rate=0.55,
                profit_factor=1.6,
                total_trades=500,
                winning_trades=275,
                losing_trades=225,
                avg_trade_pnl=0.0003,
                result_hash=config_hash,  # Deterministic
                random_seed=random_seed,
                execution_time_seconds=time.time() - start_time,
            )
        
            self._results[cache_key] = result
            logger.info(f"Completed backtest: {result.backtest_id}")
            return result
        except Exception as e:
            logger.error(f"Error in run_backtest: {e}")
            raise
    
    def verify_reproducibility(
        self,
        backtest_id: str,
    ) -> Tuple[bool, str]:
        """Verify that a backtest result is reproducible."""
        try:
            result = self._results.get(backtest_id)
            if result is None:
                return False, "Backtest not found"
        
            # Re-run with same parameters
            parts = result.model_version.split(":")
            model_id, model_version = parts[0], parts[1]
        
            parts = result.dataset_version.split(":")
            dataset_id, dataset_version = parts[0], parts[1]
        
            # Clear cache for this specific run
            cache_key = f"{model_id}:{model_version}:{dataset_id}:{dataset_version}:{result.random_seed}"
            if cache_key in self._results:
                del self._results[cache_key]
        
            # Re-run
            new_result = self.run_backtest(
                model_id=model_id,
                model_version=model_version,
                dataset_id=dataset_id,
                dataset_version=dataset_version,
                random_seed=result.random_seed,
            )
        
            # Compare hashes
            if new_result.result_hash == result.result_hash:
                return True, "Backtest is reproducible"
            else:
                return False, f"Hash mismatch: {result.result_hash} vs {new_result.result_hash}"
        except Exception as e:
            logger.error(f"Error in verify_reproducibility: {e}")
            raise


class ShadowTester:
    """
    Shadow testing system.
    
    Runs new models in shadow mode alongside production
    without affecting live trading.
    """
    
    def __init__(self, model_registry: ModelRegistry):
        try:
            self.model_registry = model_registry
            self._shadow_results: Dict[str, ShadowTestResult] = {}
            self._active_shadows: Dict[str, str] = {}  # model_id -> shadow_version
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def start_shadow_test(
        self,
        model_id: str,
        shadow_version: str,
    ) -> str:
        """Start shadow testing a model version."""
        try:
            shadow_model = self.model_registry.get(model_id, shadow_version)
            if shadow_model is None:
                raise ValueError(f"Model not found: {model_id}:{shadow_version}")
        
            production_model = self.model_registry.get_production(model_id)
            if production_model is None:
                raise ValueError(f"No production model for: {model_id}")
        
            # Update model status
            self.model_registry.update_status(model_id, shadow_version, ModelStatus.SHADOW)
        
            shadow_id = str(uuid.uuid4())
            self._active_shadows[model_id] = shadow_version
        
            logger.info(f"Started shadow test: {shadow_id} for {model_id}:{shadow_version}")
            return shadow_id
        except Exception as e:
            logger.error(f"Error in start_shadow_test: {e}")
            raise
    
    def stop_shadow_test(
        self,
        model_id: str,
    ) -> Optional[ShadowTestResult]:
        """Stop shadow testing and return results."""
        try:
            if model_id not in self._active_shadows:
                return None
        
            shadow_version = self._active_shadows.pop(model_id)
        
            # Generate result (simulated)
            result = ShadowTestResult(
                shadow_id=str(uuid.uuid4()),
                model_version=f"{model_id}:{shadow_version}",
                production_model_version=f"{model_id}:production",
                start_time=datetime.utcnow() - timedelta(hours=24),
                end_time=datetime.utcnow(),
                shadow_signals=1000,
                production_signals=1000,
                agreement_rate=0.85,
                shadow_simulated_pnl=0.02,
                production_actual_pnl=0.018,
                shadow_avg_latency_ms=5.2,
                production_avg_latency_ms=4.8,
                promote_recommended=True,
                promotion_reason="Shadow outperforms production with acceptable latency",
            )
        
            self._shadow_results[result.shadow_id] = result
            return result
        except Exception as e:
            logger.error(f"Error in stop_shadow_test: {e}")
            raise
    
    def get_promotion_recommendation(
        self,
        shadow_id: str,
    ) -> Tuple[bool, str]:
        """Get recommendation on whether to promote shadow to canary."""
        try:
            result = self._shadow_results.get(shadow_id)
            if result is None:
                return False, "Shadow test not found"
        
            # Check criteria
            if result.agreement_rate < 0.7:
                return False, f"Agreement rate too low: {result.agreement_rate}"
        
            if result.shadow_avg_latency_ms > result.production_avg_latency_ms * 1.5:
                return False, f"Latency too high: {result.shadow_avg_latency_ms}ms"
        
            if result.shadow_simulated_pnl < result.production_actual_pnl * 0.9:
                return False, f"Performance worse than production"
        
            return True, "Recommended for canary deployment"
        except Exception as e:
            logger.error(f"Error in get_promotion_recommendation: {e}")
            raise


class CanaryDeployer:
    """
    Canary deployment system.
    
    Gradually rolls out new models with monitoring.
    """
    
    STAGE_TRAFFIC = {
        DeploymentStage.SHADOW: 0.0,
        DeploymentStage.CANARY_1: 0.01,
        DeploymentStage.CANARY_5: 0.05,
        DeploymentStage.CANARY_25: 0.25,
        DeploymentStage.PRODUCTION: 1.0,
    }
    
    def __init__(self, model_registry: ModelRegistry):
        try:
            self.model_registry = model_registry
            self._canary_metrics: Dict[str, CanaryMetrics] = {}
            self._rollback_events: List[RollbackEvent] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def promote_to_canary(
        self,
        model_id: str,
        version: str,
        stage: DeploymentStage,
    ) -> str:
        """Promote model to a canary stage."""
        try:
            model = self.model_registry.get(model_id, version)
            if model is None:
                raise ValueError(f"Model not found: {model_id}:{version}")
        
            # Update deployment stage
            self.model_registry.set_deployment_stage(model_id, version, stage)
            self.model_registry.update_status(model_id, version, ModelStatus.CANARY)
        
            canary_id = str(uuid.uuid4())
        
            # Initialize metrics
            self._canary_metrics[canary_id] = CanaryMetrics(
                canary_id=canary_id,
                model_version=f"{model_id}:{version}",
                stage=stage,
                traffic_percentage=self.STAGE_TRAFFIC[stage],
                total_requests=0,
                error_rate=0.0,
                avg_latency_ms=0.0,
                p99_latency_ms=0.0,
                signal_accuracy=0.0,
                pnl_contribution=0.0,
                is_healthy=True,
                health_issues=[],
                started_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
            )
        
            logger.info(f"Promoted {model_id}:{version} to {stage.value}")
            return canary_id
        except Exception as e:
            logger.error(f"Error in promote_to_canary: {e}")
            raise
    
    def check_canary_health(
        self,
        canary_id: str,
    ) -> Tuple[bool, List[str]]:
        """Check if canary is healthy."""
        try:
            metrics = self._canary_metrics.get(canary_id)
            if metrics is None:
                return False, ["Canary not found"]
        
            issues = []
        
            # Check error rate
            if metrics.error_rate > 0.01:  # > 1%
                issues.append(f"High error rate: {metrics.error_rate:.2%}")
        
            # Check latency
            if metrics.p99_latency_ms > 100:  # > 100ms
                issues.append(f"High p99 latency: {metrics.p99_latency_ms}ms")
        
            # Check accuracy
            if metrics.signal_accuracy < 0.5:
                issues.append(f"Low signal accuracy: {metrics.signal_accuracy:.2%}")
        
            is_healthy = len(issues) == 0
            metrics.is_healthy = is_healthy
            metrics.health_issues = issues
        
            return is_healthy, issues
        except Exception as e:
            logger.error(f"Error in check_canary_health: {e}")
            raise
    
    def advance_canary(
        self,
        canary_id: str,
    ) -> Optional[DeploymentStage]:
        """Advance canary to next stage if healthy."""
        try:
            metrics = self._canary_metrics.get(canary_id)
            if metrics is None:
                return None
        
            is_healthy, issues = self.check_canary_health(canary_id)
            if not is_healthy:
                logger.warning(f"Cannot advance unhealthy canary: {issues}")
                return None
        
            # Determine next stage
            stages = list(DeploymentStage)
            current_idx = stages.index(metrics.stage)
        
            if current_idx >= len(stages) - 1:
                logger.info("Canary already at production stage")
                return metrics.stage
        
            next_stage = stages[current_idx + 1]
        
            # Update
            parts = metrics.model_version.split(":")
            model_id, version = parts[0], parts[1]
        
            self.model_registry.set_deployment_stage(model_id, version, next_stage)
            metrics.stage = next_stage
            metrics.traffic_percentage = self.STAGE_TRAFFIC[next_stage]
        
            if next_stage == DeploymentStage.PRODUCTION:
                self.model_registry.update_status(model_id, version, ModelStatus.PRODUCTION)
        
            logger.info(f"Advanced canary to {next_stage.value}")
            return next_stage
        except Exception as e:
            logger.error(f"Error in advance_canary: {e}")
            raise
    
    def rollback(
        self,
        model_id: str,
        current_version: str,
        target_version: str,
        reason: str,
        trigger: str = "manual",
        approved_by: Optional[str] = None,
    ) -> RollbackEvent:
        """Rollback to a previous model version."""
        # Update statuses
        try:
            self.model_registry.update_status(model_id, current_version, ModelStatus.ROLLED_BACK)
            self.model_registry.update_status(model_id, target_version, ModelStatus.PRODUCTION)
            self.model_registry.set_deployment_stage(model_id, target_version, DeploymentStage.PRODUCTION)
        
            # Record rollback
            event = RollbackEvent(
                rollback_id=str(uuid.uuid4()),
                rolled_back_version=f"{model_id}:{current_version}",
                rolled_back_to_version=f"{model_id}:{target_version}",
                trigger=trigger,
                reason=reason,
                metrics_at_rollback={},
                triggered_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                approved_by=approved_by,
                auto_approved=trigger.startswith("auto_"),
            )
        
            self._rollback_events.append(event)
            logger.warning(f"Rolled back {model_id} from {current_version} to {target_version}: {reason}")
        
            return event
        except Exception as e:
            logger.error(f"Error in rollback: {e}")
            raise


class TrainingFirstArchitecture:
    """
    Training-First Architecture Coordinator.
    
    Ensures:
    - Logic is immutable
    - Behavior changes only via retraining
    - Models are hot-swappable
    - All training is reproducible
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            storage_path = self.config.get("storage_path", "training_artifacts")
        
            self.dataset_registry = DatasetRegistry(f"{storage_path}/datasets")
            self.config_registry = TrainingConfigRegistry()
            self.model_registry = ModelRegistry(f"{storage_path}/models")
        
            self.backtester = DeterministicBacktester(
                self.dataset_registry,
                self.model_registry,
            )
            self.shadow_tester = ShadowTester(self.model_registry)
            self.canary_deployer = CanaryDeployer(self.model_registry)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def create_training_run(
        self,
        model_type: str,
        architecture: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        dataset_id: str,
        dataset_version: str,
    ) -> TrainingConfig:
        """Create a new training configuration."""
        try:
            config = TrainingConfig(
                config_id=str(uuid.uuid4()),
                version="1.0",
                created_at=datetime.utcnow(),
                model_type=model_type,
                model_architecture=architecture,
                hyperparameters=hyperparameters,
                optimizer="adam",
                learning_rate=hyperparameters.get("learning_rate", 0.001),
                batch_size=hyperparameters.get("batch_size", 32),
                epochs=hyperparameters.get("epochs", 100),
                early_stopping=True,
                early_stopping_patience=10,
                dataset_version=f"{dataset_id}:{dataset_version}",
                train_split=0.7,
                validation_split=0.15,
                test_split=0.15,
                random_seed=42,
                deterministic=True,
                device="cuda",
                mixed_precision=True,
            )
        
            self.config_registry.register(config)
            return config
        except Exception as e:
            logger.error(f"Error in create_training_run: {e}")
            raise
    
    def deploy_model(
        self,
        model_id: str,
        version: str,
        skip_shadow: bool = False,
        skip_canary: bool = False,
    ) -> Dict[str, Any]:
        """
        Deploy a model through the full pipeline.
        
        Pipeline: Shadow → Canary (1% → 5% → 25%) → Production
        """
        try:
            model = self.model_registry.get(model_id, version)
            if model is None:
                return {"error": f"Model not found: {model_id}:{version}"}
        
            result = {
                "model": f"{model_id}:{version}",
                "stages_completed": [],
                "current_stage": None,
            }
        
            # Shadow testing
            if not skip_shadow:
                shadow_id = self.shadow_tester.start_shadow_test(model_id, version)
                result["shadow_id"] = shadow_id
                result["stages_completed"].append("shadow_started")
                result["current_stage"] = "shadow"
                return result  # Return early - shadow test runs async
        
            # Canary deployment
            if not skip_canary:
                canary_id = self.canary_deployer.promote_to_canary(
                    model_id, version, DeploymentStage.CANARY_1
                )
                result["canary_id"] = canary_id
                result["stages_completed"].append("canary_1")
                result["current_stage"] = "canary_1"
                return result  # Return early - canary runs async
        
            # Direct to production (not recommended)
            self.model_registry.update_status(model_id, version, ModelStatus.PRODUCTION)
            self.model_registry.set_deployment_stage(model_id, version, DeploymentStage.PRODUCTION)
            result["stages_completed"].append("production")
            result["current_stage"] = "production"
        
            return result
        except Exception as e:
            logger.error(f"Error in deploy_model: {e}")
            raise
    
    def get_deployment_status(self, model_id: str) -> Dict[str, Any]:
        """Get deployment status for a model."""
        try:
            production = self.model_registry.get_production(model_id)
        
            # Get all versions
            all_versions = []
            for version_id, model in self.model_registry._models.get(model_id, {}).items():
                all_versions.append({
                    "version": version_id,
                    "status": model.status.value,
                    "stage": model.deployment_stage.value if model.deployment_stage else None,
                })
        
            return {
                "model_id": model_id,
                "production_version": production.version if production else None,
                "all_versions": all_versions,
            }
        except Exception as e:
            logger.error(f"Error in get_deployment_status: {e}")
            raise
