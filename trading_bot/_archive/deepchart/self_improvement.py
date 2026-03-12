"""
DeepChart Self-Improvement Loop - Low-Cost Model Evolution

Designed for:
- Offline weekly/monthly retraining
- Archived cheap data only
- Auto-validation via backtests
- Drift detection for calibration
- Stable model size
- Safety gates before deployment

Components:
1. DriftDetector - Detects model/data drift
2. TrainingPipeline - Offline retraining
3. SafetyGate - Deployment validation
4. SelfImprovementLoop - Orchestrates evolution

Reward Function:
- Primary: Directional accuracy on next N bars
- Secondary: Calibration (predicted prob vs actual)
- Penalty: Overconfidence, excessive trading signals
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
import logging
import json
import os
import time
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class RetrainFrequency(Enum):
    """Retraining frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class DriftType(Enum):
    """Types of drift detected."""
    NONE = "none"
    DATA_DRIFT = "data_drift"
    CONCEPT_DRIFT = "concept_drift"
    PERFORMANCE_DRIFT = "performance_drift"
    CALIBRATION_DRIFT = "calibration_drift"


@dataclass
class TrainingConfig:
    """Configuration for training pipeline."""
    # Data settings
    data_dir: str = "data/deepchart"
    min_training_samples: int = 10000
    max_training_samples: int = 100000
    validation_split: float = 0.2
    
    # Training settings
    batch_size: int = 64
    epochs: int = 10
    learning_rate: float = 0.001
    early_stopping_patience: int = 3
    
    # Retraining
    retrain_frequency: RetrainFrequency = RetrainFrequency.WEEKLY
    min_days_between_retrain: int = 7
    
    # Model constraints
    max_model_size_mb: float = 10.0
    max_parameters: int = 1_000_000
    
    # Validation
    min_backtest_sharpe: float = 0.5
    min_directional_accuracy: float = 0.52
    max_calibration_error: float = 0.1
    
    # Safety
    require_human_approval: bool = False
    auto_rollback_threshold: float = 0.1  # 10% performance drop
    
    # Paths
    model_dir: str = "models/deepchart"
    checkpoint_dir: str = "models/deepchart/checkpoints"
    archive_dir: str = "models/deepchart/archive"


@dataclass
class DriftMetrics:
    """Metrics for drift detection."""
    data_drift_score: float = 0.0
    concept_drift_score: float = 0.0
    performance_drift_score: float = 0.0
    calibration_error: float = 0.0
    
    drift_type: DriftType = DriftType.NONE
    drift_detected: bool = False
    
    # Details
    feature_drift: Dict[str, float] = field(default_factory=dict)
    performance_history: List[float] = field(default_factory=list)
    
    timestamp: float = 0.0


@dataclass
class ValidationResult:
    """Result from model validation."""
    passed: bool = False
    
    # Metrics
    directional_accuracy: float = 0.0
    calibration_error: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    # Comparison to baseline
    accuracy_vs_baseline: float = 0.0
    sharpe_vs_baseline: float = 0.0
    
    # Details
    validation_samples: int = 0
    backtest_trades: int = 0
    
    # Failure reasons
    failure_reasons: List[str] = field(default_factory=list)
    
    timestamp: float = 0.0


# =============================================================================
# DRIFT DETECTOR
# =============================================================================

class DriftDetector:
    """
    Detects various types of drift in model performance.
    
    Drift Types:
    1. Data Drift - Input feature distribution changes
    2. Concept Drift - Relationship between features and target changes
    3. Performance Drift - Model accuracy degrades
    4. Calibration Drift - Predicted probabilities become miscalibrated
    
    Methods:
    - KS test for data drift
    - ADWIN for concept drift
    - Rolling performance tracking
    - Reliability diagrams for calibration
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        
        # Reference distributions (from training)
        self._reference_stats: Dict[str, Dict[str, float]] = {}
        
        # Rolling windows
        self._feature_window: List[np.ndarray] = []
        self._prediction_window: List[Tuple[float, float, int]] = []  # (pred_prob, actual, direction)
        self._performance_window: List[float] = []
        
        # Window sizes
        self._window_size = 1000
        self._min_samples = 100
        
        # Thresholds
        self._data_drift_threshold = 0.1
        self._concept_drift_threshold = 0.15
        self._performance_drift_threshold = 0.1
        self._calibration_threshold = 0.1
        
        logger.info("DriftDetector initialized")
    
    def set_reference(self, features: np.ndarray):
        """
        Set reference distribution from training data.
        
        Args:
            features: Training feature matrix (n_samples, n_features)
        """
        self._reference_stats = {}
        
        for i in range(features.shape[1]):
            col = features[:, i]
            self._reference_stats[f'feature_{i}'] = {
                'mean': float(np.mean(col)),
                'std': float(np.std(col)),
                'min': float(np.min(col)),
                'max': float(np.max(col)),
                'q25': float(np.percentile(col, 25)),
                'q50': float(np.percentile(col, 50)),
                'q75': float(np.percentile(col, 75)),
            }
        
        logger.info(f"Reference set with {len(self._reference_stats)} features")
    
    def update(self, 
               features: np.ndarray,
               prediction: float,
               actual: float,
               direction_correct: bool):
        """
        Update drift detector with new observation.
        
        Args:
            features: Feature vector
            prediction: Predicted probability
            actual: Actual outcome (0 or 1)
            direction_correct: Whether direction prediction was correct
        """
        # Update windows
        self._feature_window.append(features)
        self._prediction_window.append((prediction, actual, int(direction_correct)))
        self._performance_window.append(float(direction_correct))
        
        # Trim windows
        if len(self._feature_window) > self._window_size:
            self._feature_window = self._feature_window[-self._window_size:]
        if len(self._prediction_window) > self._window_size:
            self._prediction_window = self._prediction_window[-self._window_size:]
        if len(self._performance_window) > self._window_size:
            self._performance_window = self._performance_window[-self._window_size:]
    
    def detect(self) -> DriftMetrics:
        """
        Detect drift based on accumulated observations.
        
        Returns:
            DriftMetrics with drift scores and type
        """
        metrics = DriftMetrics(timestamp=time.time())
        
        if len(self._feature_window) < self._min_samples:
            return metrics
        
        # Data drift detection
        metrics.data_drift_score, metrics.feature_drift = self._detect_data_drift()
        
        # Concept drift detection
        metrics.concept_drift_score = self._detect_concept_drift()
        
        # Performance drift detection
        metrics.performance_drift_score = self._detect_performance_drift()
        
        # Calibration drift detection
        metrics.calibration_error = self._detect_calibration_drift()
        
        # Determine overall drift type
        metrics.drift_type, metrics.drift_detected = self._determine_drift_type(metrics)
        
        return metrics
    
    def _detect_data_drift(self) -> Tuple[float, Dict[str, float]]:
        """
        Detect data drift using statistical tests.
        
        Uses simplified KS-like test comparing current vs reference distributions.
        """
        if not self._reference_stats:
            return 0.0, {}
        
        current_features = np.array(self._feature_window)
        feature_drift = {}
        drift_scores = []
        
        for i in range(current_features.shape[1]):
            feature_name = f'feature_{i}'
            if feature_name not in self._reference_stats:
                continue
            
            ref = self._reference_stats[feature_name]
            current = current_features[:, i]
            
            # Compare statistics
            mean_diff = abs(np.mean(current) - ref['mean']) / max(ref['std'], 1e-8)
            std_ratio = np.std(current) / max(ref['std'], 1e-8)
            
            # Drift score for this feature
            drift = (mean_diff + abs(1 - std_ratio)) / 2
            feature_drift[feature_name] = float(drift)
            drift_scores.append(drift)
        
        overall_drift = np.mean(drift_scores) if drift_scores else 0.0
        return float(overall_drift), feature_drift
    
    def _detect_concept_drift(self) -> float:
        """
        Detect concept drift using ADWIN-like approach.
        
        Compares accuracy in recent window vs older window.
        """
        if len(self._performance_window) < self._min_samples:
            return 0.0
        
        # Split into two windows
        mid = len(self._performance_window) // 2
        old_window = self._performance_window[:mid]
        new_window = self._performance_window[mid:]
        
        old_accuracy = np.mean(old_window)
        new_accuracy = np.mean(new_window)
        
        # Concept drift = significant accuracy change
        drift = abs(new_accuracy - old_accuracy)
        
        return float(drift)
    
    def _detect_performance_drift(self) -> float:
        """
        Detect performance drift using rolling accuracy.
        """
        if len(self._performance_window) < self._min_samples:
            return 0.0
        
        # Compare recent performance to overall
        recent_size = min(100, len(self._performance_window) // 4)
        recent_accuracy = np.mean(self._performance_window[-recent_size:])
        overall_accuracy = np.mean(self._performance_window)
        
        # Drift = drop in recent performance
        drift = max(0, overall_accuracy - recent_accuracy)
        
        return float(drift)
    
    def _detect_calibration_drift(self) -> float:
        """
        Detect calibration drift using reliability diagram approach.
        
        Compares predicted probabilities to actual outcomes.
        """
        if len(self._prediction_window) < self._min_samples:
            return 0.0
        
        predictions = np.array(self._prediction_window)
        pred_probs = predictions[:, 0]
        actuals = predictions[:, 1]
        
        # Bin predictions
        n_bins = 10
        bin_edges = np.linspace(0, 1, n_bins + 1)
        
        calibration_errors = []
        for i in range(n_bins):
            mask = (pred_probs >= bin_edges[i]) & (pred_probs < bin_edges[i + 1])
            if np.sum(mask) < 10:
                continue
            
            bin_pred = np.mean(pred_probs[mask])
            bin_actual = np.mean(actuals[mask])
            calibration_errors.append(abs(bin_pred - bin_actual))
        
        if not calibration_errors:
            return 0.0
        
        return float(np.mean(calibration_errors))
    
    def _determine_drift_type(self, metrics: DriftMetrics) -> Tuple[DriftType, bool]:
        """Determine the primary drift type."""
        drift_detected = False
        drift_type = DriftType.NONE
        
        # Check each drift type
        if metrics.data_drift_score > self._data_drift_threshold:
            drift_type = DriftType.DATA_DRIFT
            drift_detected = True
        
        if metrics.concept_drift_score > self._concept_drift_threshold:
            drift_type = DriftType.CONCEPT_DRIFT
            drift_detected = True
        
        if metrics.performance_drift_score > self._performance_drift_threshold:
            drift_type = DriftType.PERFORMANCE_DRIFT
            drift_detected = True
        
        if metrics.calibration_error > self._calibration_threshold:
            drift_type = DriftType.CALIBRATION_DRIFT
            drift_detected = True
        
        return drift_type, drift_detected
    
    def reset(self):
        """Reset drift detector state."""
        self._feature_window.clear()
        self._prediction_window.clear()
        self._performance_window.clear()


# =============================================================================
# SAFETY GATE
# =============================================================================

class SafetyGate:
    """
    Safety gate for model deployment.
    
    Validates new models before deployment:
    1. Performance validation (backtest)
    2. Comparison to baseline
    3. Stability checks
    4. Size constraints
    
    Auto-rollback conditions:
    - Performance drops below threshold
    - Excessive prediction changes
    - Model instability detected
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        
        # Baseline metrics
        self._baseline_metrics: Optional[Dict[str, float]] = None
        
        # Deployment history
        self._deployment_history: List[Dict[str, Any]] = []
        
        logger.info("SafetyGate initialized")
    
    def set_baseline(self, metrics: Dict[str, float]):
        """Set baseline metrics for comparison."""
        self._baseline_metrics = metrics.copy()
        logger.info(f"Baseline set: {metrics}")
    
    def validate(self, 
                 model_path: str,
                 validation_data: Tuple[np.ndarray, np.ndarray],
                 backtest_results: Optional[Dict[str, float]] = None) -> ValidationResult:
        """
        Validate a model for deployment.
        
        Args:
            model_path: Path to model file
            validation_data: Tuple of (features, labels)
            backtest_results: Optional backtest metrics
        
        Returns:
            ValidationResult with pass/fail and metrics
        """
        result = ValidationResult(timestamp=time.time())
        
        features, labels = validation_data
        result.validation_samples = len(labels)
        
        # Check model size
        if not self._check_model_size(model_path, result):
            return result
        
        # Run validation inference
        predictions = self._run_validation_inference(model_path, features)
        if predictions is None:
            result.failure_reasons.append("Inference failed")
            return result
        
        # Calculate metrics
        result.directional_accuracy = self._calculate_accuracy(predictions, labels)
        result.calibration_error = self._calculate_calibration_error(predictions, labels)
        
        # Backtest metrics
        if backtest_results:
            result.sharpe_ratio = backtest_results.get('sharpe_ratio', 0.0)
            result.max_drawdown = backtest_results.get('max_drawdown', 0.0)
            result.backtest_trades = backtest_results.get('num_trades', 0)
        
        # Compare to baseline
        if self._baseline_metrics:
            result.accuracy_vs_baseline = result.directional_accuracy - self._baseline_metrics.get('accuracy', 0.5)
            result.sharpe_vs_baseline = result.sharpe_ratio - self._baseline_metrics.get('sharpe', 0.0)
        
        # Check thresholds
        result.passed = self._check_thresholds(result)
        
        return result
    
    def _check_model_size(self, model_path: str, result: ValidationResult) -> bool:
        """Check if model size is within limits."""
        if not os.path.exists(model_path):
            result.failure_reasons.append(f"Model file not found: {model_path}")
            return False
        
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        if size_mb > self.config.max_model_size_mb:
            result.failure_reasons.append(
                f"Model size {size_mb:.2f}MB exceeds limit {self.config.max_model_size_mb}MB"
            )
            return False
        
        return True
    
    def _run_validation_inference(self, model_path: str, features: np.ndarray) -> Optional[np.ndarray]:
        """Run inference on validation data."""
        try:
            try:
                # Try ONNX first
                import onnxruntime as ort
                session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                input_name = session.get_inputs()[0].name
                
                # Run in batches
                batch_size = 64
                predictions = []
                for i in range(0, len(features), batch_size):
                    batch = features[i:i+batch_size].astype(np.float32)
                    if len(batch.shape) == 2:
                        batch = batch[:, np.newaxis, :]  # Add sequence dim
                    pred = session.run(None, {input_name: batch})[0]
                    predictions.append(pred)
                
                return np.concatenate(predictions, axis=0)
            except Exception as e:
                logger.error(f"Error: {e}")
                pass
            
            # Fallback to numpy model
            from .lightweight_models import DeepChartModel
            model = DeepChartModel()
            
            predictions = []
            for feature in features:
                output = model.predict(feature)
                predictions.append([
                    output.trend_confidence,
                    output.breakout_probability,
                    output.reversion_probability,
                ])
            
            return np.array(predictions)
            
        except Exception as e:
            logger.error(f"Validation inference failed: {e}")
            return None
    
    def _calculate_accuracy(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """Calculate directional accuracy."""
        # Assume first column is trend prediction
        pred_direction = np.sign(predictions[:, 0] - 0.5)
        actual_direction = np.sign(labels)
        
        accuracy = np.mean(pred_direction == actual_direction)
        return float(accuracy)
    
    def _calculate_calibration_error(self, predictions: np.ndarray, labels: np.ndarray) -> float:
        """Calculate expected calibration error."""
        # Assume first column is probability
        probs = predictions[:, 0]
        actuals = (labels > 0).astype(float)
        
        # Bin and calculate ECE
        n_bins = 10
        bin_edges = np.linspace(0, 1, n_bins + 1)
        
        ece = 0.0
        for i in range(n_bins):
            mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
            if np.sum(mask) == 0:
                continue
            
            bin_accuracy = np.mean(actuals[mask])
            bin_confidence = np.mean(probs[mask])
            bin_size = np.sum(mask) / len(probs)
            
            ece += bin_size * abs(bin_accuracy - bin_confidence)
        
        return float(ece)
    
    def _check_thresholds(self, result: ValidationResult) -> bool:
        """Check if result passes all thresholds."""
        passed = True
        
        if result.directional_accuracy < self.config.min_directional_accuracy:
            result.failure_reasons.append(
                f"Accuracy {result.directional_accuracy:.3f} < {self.config.min_directional_accuracy}"
            )
            passed = False
        
        if result.calibration_error > self.config.max_calibration_error:
            result.failure_reasons.append(
                f"Calibration error {result.calibration_error:.3f} > {self.config.max_calibration_error}"
            )
            passed = False
        
        if result.sharpe_ratio < self.config.min_backtest_sharpe:
            result.failure_reasons.append(
                f"Sharpe {result.sharpe_ratio:.3f} < {self.config.min_backtest_sharpe}"
            )
            passed = False
        
        # Check vs baseline (must not be significantly worse)
        if self._baseline_metrics and result.accuracy_vs_baseline < -self.config.auto_rollback_threshold:
            result.failure_reasons.append(
                f"Accuracy dropped {result.accuracy_vs_baseline:.3f} vs baseline"
            )
            passed = False
        
        return passed
    
    def should_rollback(self, current_metrics: Dict[str, float]) -> Tuple[bool, str]:
        """
        Check if model should be rolled back.
        
        Args:
            current_metrics: Current live performance metrics
        
        Returns:
            Tuple of (should_rollback, reason)
        """
        if not self._baseline_metrics:
            return False, ""
        
        # Check accuracy drop
        accuracy_drop = self._baseline_metrics.get('accuracy', 0.5) - current_metrics.get('accuracy', 0.5)
        if accuracy_drop > self.config.auto_rollback_threshold:
            return True, f"Accuracy dropped by {accuracy_drop:.3f}"
        
        # Check Sharpe drop
        sharpe_drop = self._baseline_metrics.get('sharpe', 0.0) - current_metrics.get('sharpe', 0.0)
        if sharpe_drop > self.config.auto_rollback_threshold * 2:
            return True, f"Sharpe dropped by {sharpe_drop:.3f}"
        
        return False, ""
    
    def record_deployment(self, 
                         model_version: str,
                         validation_result: ValidationResult,
                         deployed: bool):
        """Record deployment decision."""
        self._deployment_history.append({
            'version': model_version,
            'timestamp': time.time(),
            'deployed': deployed,
            'metrics': {
                'accuracy': validation_result.directional_accuracy,
                'calibration_error': validation_result.calibration_error,
                'sharpe': validation_result.sharpe_ratio,
            },
            'failure_reasons': validation_result.failure_reasons,
        })


# =============================================================================
# TRAINING PIPELINE
# =============================================================================

class TrainingPipeline:
    """
    Offline training pipeline for model updates.
    
    Features:
    - Uses archived cheap data only
    - Incremental training support
    - Model versioning
    - Checkpoint management
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        
        # Ensure directories exist
        os.makedirs(config.model_dir, exist_ok=True)
        os.makedirs(config.checkpoint_dir, exist_ok=True)
        os.makedirs(config.archive_dir, exist_ok=True)
        
        # Training state
        self._last_train_time: Optional[float] = None
        self._current_version: str = "v0.0.0"
        
        logger.info("TrainingPipeline initialized")
    
    def should_retrain(self, drift_metrics: Optional[DriftMetrics] = None) -> Tuple[bool, str]:
        """
        Check if retraining should be triggered.
        
        Returns:
            Tuple of (should_retrain, reason)
        """
        # Check time since last training
        if self._last_train_time:
            days_since = (time.time() - self._last_train_time) / (24 * 3600)
            
            if days_since < self.config.min_days_between_retrain:
                return False, f"Only {days_since:.1f} days since last training"
            
            # Check frequency
            freq_days = {
                RetrainFrequency.DAILY: 1,
                RetrainFrequency.WEEKLY: 7,
                RetrainFrequency.BIWEEKLY: 14,
                RetrainFrequency.MONTHLY: 30,
            }
            
            if days_since >= freq_days[self.config.retrain_frequency]:
                return True, f"Scheduled retrain ({self.config.retrain_frequency.value})"
        else:
            return True, "Initial training"
        
        # Check drift
        if drift_metrics and drift_metrics.drift_detected:
            return True, f"Drift detected: {drift_metrics.drift_type.value}"
        
        return False, ""
    
    def prepare_data(self) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
        """
        Prepare training data from archived files.
        
        Returns:
            Tuple of (X_train, y_train, X_val, y_val) or None if insufficient data
        """
        # Look for data files
        data_files = []
        if os.path.exists(self.config.data_dir):
            for f in os.listdir(self.config.data_dir):
                if f.endswith('.npz') or f.endswith('.npy'):
                    data_files.append(os.path.join(self.config.data_dir, f))
        
        if not data_files:
            logger.warning("No training data files found")
            return None
        
        # Load and combine data
        all_features = []
        all_labels = []
        
        for data_file in data_files:
            try:
                data = np.load(data_file, allow_pickle=True)
                if isinstance(data, np.lib.npyio.NpzFile):
                    features = data['features']
                    labels = data['labels']
                else:
                    # Assume it's a structured array
                    features = data[:, :-1]
                    labels = data[:, -1]
                
                all_features.append(features)
                all_labels.append(labels)
            except Exception as e:
                logger.warning(f"Failed to load {data_file}: {e}")
        
        if not all_features:
            return None
        
        # Combine
        X = np.concatenate(all_features, axis=0)
        y = np.concatenate(all_labels, axis=0)
        
        # Check size
        if len(X) < self.config.min_training_samples:
            logger.warning(f"Insufficient data: {len(X)} < {self.config.min_training_samples}")
            return None
        
        # Limit size
        if len(X) > self.config.max_training_samples:
            indices = np.random.choice(len(X), self.config.max_training_samples, replace=False)
            X = X[indices]
            y = y[indices]
        
        # Split
        n_val = int(len(X) * self.config.validation_split)
        indices = np.random.permutation(len(X))
        
        X_train = X[indices[n_val:]]
        y_train = y[indices[n_val:]]
        X_val = X[indices[:n_val]]
        y_val = y[indices[:n_val]]
        
        logger.info(f"Prepared data: train={len(X_train)}, val={len(X_val)}")
        
        return X_train, y_train, X_val, y_val
    
    def train(self, 
              X_train: np.ndarray, 
              y_train: np.ndarray,
              X_val: np.ndarray,
              y_val: np.ndarray) -> Optional[str]:
        """
        Train model on prepared data.
        
        Returns:
            Path to trained model or None if training failed
        """
        try:
            # Generate version
            version = self._generate_version()
            model_path = os.path.join(self.config.model_dir, f'model_{version}.onnx')
            
            # Try PyTorch training
            try:
                import torch
                import torch.nn as nn
                import torch.optim as optim
                from .lightweight_models import TemporalCNNTorch, ModelConfig
                
                # Create model
                config = ModelConfig(input_dim=X_train.shape[-1])
                model = TemporalCNNTorch(config)
                
                # Training setup
                criterion = nn.MSELoss()
                optimizer = optim.Adam(model.parameters(), lr=self.config.learning_rate)
                
                # Convert data
                X_train_t = torch.from_numpy(X_train.astype(np.float32))
                y_train_t = torch.from_numpy(y_train.astype(np.float32))
                X_val_t = torch.from_numpy(X_val.astype(np.float32))
                y_val_t = torch.from_numpy(y_val.astype(np.float32))
                
                # Add sequence dimension if needed
                if len(X_train_t.shape) == 2:
                    X_train_t = X_train_t.unsqueeze(1)
                    X_val_t = X_val_t.unsqueeze(1)
                
                # Training loop
                best_val_loss = float('inf')
                patience_counter = 0
                
                for epoch in range(self.config.epochs):
                    model.train()
                    
                    # Mini-batch training
                    indices = np.random.permutation(len(X_train_t))
                    total_loss = 0
                    n_batches = 0
                    
                    for i in range(0, len(indices), self.config.batch_size):
                        batch_idx = indices[i:i+self.config.batch_size]
                        X_batch = X_train_t[batch_idx]
                        y_batch = y_train_t[batch_idx]
                        
                        optimizer.zero_grad()
                        outputs = model(X_batch)
                        loss = criterion(outputs[:, 0], y_batch)
                        loss.backward()
                        optimizer.step()
                        
                        total_loss += loss.item()
                        n_batches += 1
                    
                    # Validation
                    model.eval()
                    with torch.no_grad():
                        val_outputs = model(X_val_t)
                        val_loss = criterion(val_outputs[:, 0], y_val_t).item()
                    
                    logger.info(f"Epoch {epoch+1}: train_loss={total_loss/n_batches:.4f}, val_loss={val_loss:.4f}")
                    
                    # Early stopping
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        patience_counter = 0
                        
                        # Save checkpoint
                        checkpoint_path = os.path.join(self.config.checkpoint_dir, f'best_{version}.pt')
                        torch.save(model.state_dict(), checkpoint_path)
                    else:
                        patience_counter += 1
                        if patience_counter >= self.config.early_stopping_patience:
                            logger.info(f"Early stopping at epoch {epoch+1}")
                            break
                
                # Export to ONNX
                model.eval()
                dummy_input = torch.randn(1, X_train_t.shape[1], X_train_t.shape[2])
                torch.onnx.export(
                    model, dummy_input, model_path,
                    input_names=['input'],
                    output_names=['output'],
                    dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}},
                    opset_version=11,
                )
                
                logger.info(f"Model exported to {model_path}")
                
            except ImportError:
                # Fallback: save numpy weights
                logger.warning("PyTorch not available, saving numpy weights")
                model_path = os.path.join(self.config.model_dir, f'model_{version}.npz')
                
                # Simple linear model as fallback
                weights = {
                    'W': np.random.randn(X_train.shape[-1], 13) * 0.1,
                    'b': np.zeros(13),
                }
                np.savez(model_path, **weights)
            
            self._last_train_time = time.time()
            self._current_version = version
            
            return model_path
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return None
    
    def _generate_version(self) -> str:
        """Generate unique version string."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
        return f"v{timestamp}_{hash_suffix}"
    
    def archive_model(self, model_path: str):
        """Archive a model file."""
        if not os.path.exists(model_path):
            return
        
        filename = os.path.basename(model_path)
        archive_path = os.path.join(self.config.archive_dir, filename)
        
        import shutil
        shutil.copy2(model_path, archive_path)
        logger.info(f"Archived model to {archive_path}")


# =============================================================================
# SELF-IMPROVEMENT LOOP
# =============================================================================

class SelfImprovementLoop:
    """
    Main orchestrator for self-improvement.
    
    Coordinates:
    1. Drift detection
    2. Retraining decisions
    3. Validation
    4. Safe deployment
    5. Rollback if needed
    """
    
    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        
        # Components
        self.drift_detector = DriftDetector(self.config)
        self.safety_gate = SafetyGate(self.config)
        self.training_pipeline = TrainingPipeline(self.config)
        
        # State
        self._current_model_path: Optional[str] = None
        self._previous_model_path: Optional[str] = None
        self._improvement_history: List[Dict[str, Any]] = []
        
        # Callbacks
        self._on_model_updated: Optional[Callable[[str], None]] = None
        self._on_rollback: Optional[Callable[[str], None]] = None
        
        logger.info("SelfImprovementLoop initialized")
    
    def set_callbacks(self,
                      on_model_updated: Optional[Callable[[str], None]] = None,
                      on_rollback: Optional[Callable[[str], None]] = None):
        """Set callbacks for model events."""
        self._on_model_updated = on_model_updated
        self._on_rollback = on_rollback
    
    def update(self,
               features: np.ndarray,
               prediction: float,
               actual: float,
               direction_correct: bool):
        """
        Update with new observation.
        
        Call this after each prediction to track performance.
        """
        self.drift_detector.update(features, prediction, actual, direction_correct)
    
    def check_and_improve(self) -> Dict[str, Any]:
        """
        Check if improvement is needed and execute if so.
        
        Returns:
            Dict with improvement status and details
        """
        result = {
            'action': 'none',
            'reason': '',
            'drift_metrics': None,
            'validation_result': None,
            'new_model_path': None,
        }
        
        # Detect drift
        drift_metrics = self.drift_detector.detect()
        result['drift_metrics'] = drift_metrics
        
        # Check if retraining needed
        should_retrain, reason = self.training_pipeline.should_retrain(drift_metrics)
        
        if not should_retrain:
            result['reason'] = reason
            return result
        
        result['action'] = 'retrain'
        result['reason'] = reason
        
        # Prepare data
        data = self.training_pipeline.prepare_data()
        if data is None:
            result['action'] = 'failed'
            result['reason'] = 'Insufficient training data'
            return result
        
        X_train, y_train, X_val, y_val = data
        
        # Train new model
        new_model_path = self.training_pipeline.train(X_train, y_train, X_val, y_val)
        if new_model_path is None:
            result['action'] = 'failed'
            result['reason'] = 'Training failed'
            return result
        
        # Validate
        validation_result = self.safety_gate.validate(
            new_model_path,
            (X_val, y_val),
        )
        result['validation_result'] = validation_result
        
        if not validation_result.passed:
            result['action'] = 'rejected'
            result['reason'] = f"Validation failed: {validation_result.failure_reasons}"
            
            # Archive failed model
            self.training_pipeline.archive_model(new_model_path)
            return result
        
        # Check if human approval required
        if self.config.require_human_approval:
            result['action'] = 'pending_approval'
            result['new_model_path'] = new_model_path
            return result
        
        # Deploy
        self._deploy_model(new_model_path)
        result['action'] = 'deployed'
        result['new_model_path'] = new_model_path
        
        # Record
        self._improvement_history.append({
            'timestamp': time.time(),
            'action': 'deployed',
            'model_path': new_model_path,
            'metrics': {
                'accuracy': validation_result.directional_accuracy,
                'sharpe': validation_result.sharpe_ratio,
            },
        })
        
        return result
    
    def _deploy_model(self, model_path: str):
        """Deploy a new model."""
        # Archive current model
        if self._current_model_path:
            self._previous_model_path = self._current_model_path
            self.training_pipeline.archive_model(self._current_model_path)
        
        self._current_model_path = model_path
        
        # Trigger callback
        if self._on_model_updated:
            self._on_model_updated(model_path)
        
        logger.info(f"Deployed new model: {model_path}")
    
    def check_rollback(self, current_metrics: Dict[str, float]) -> bool:
        """
        Check if rollback is needed based on current performance.
        
        Returns:
            True if rollback was executed
        """
        should_rollback, reason = self.safety_gate.should_rollback(current_metrics)
        
        if should_rollback and self._previous_model_path:
            logger.warning(f"Rolling back: {reason}")
            
            # Swap models
            self._current_model_path, self._previous_model_path = \
                self._previous_model_path, self._current_model_path
            
            # Trigger callback
            if self._on_rollback:
                self._on_rollback(self._current_model_path)
            
            # Record
            self._improvement_history.append({
                'timestamp': time.time(),
                'action': 'rollback',
                'reason': reason,
                'model_path': self._current_model_path,
            })
            
            return True
        
        return False
    
    def approve_deployment(self, model_path: str) -> bool:
        """
        Manually approve a pending deployment.
        
        Args:
            model_path: Path to model awaiting approval
        
        Returns:
            True if deployment succeeded
        """
        if not os.path.exists(model_path):
            logger.error(f"Model not found: {model_path}")
            return False
        
        self._deploy_model(model_path)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of improvement loop."""
        return {
            'current_model': self._current_model_path,
            'previous_model': self._previous_model_path,
            'drift_detected': self.drift_detector.detect().drift_detected,
            'improvement_count': len(self._improvement_history),
            'last_improvement': self._improvement_history[-1] if self._improvement_history else None,
        }
    
    def reset(self):
        """Reset improvement loop state."""
        self.drift_detector.reset()
        self._improvement_history.clear()


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_improvement_loop(config: Optional[Dict] = None) -> SelfImprovementLoop:
    """Factory function to create improvement loop."""
    if config:
        training_config = TrainingConfig(**config)
    else:
        training_config = TrainingConfig()
    return SelfImprovementLoop(training_config)


if __name__ == "__main__":
    # Test the self-improvement loop
    loop = SelfImprovementLoop()
    
    # Simulate observations
    np.random.seed(42)
    
    for i in range(500):
        features = np.random.randn(32)
        prediction = np.random.random()
        actual = float(np.random.random() > 0.5)
        direction_correct = (prediction > 0.5) == (actual > 0.5)
        
        loop.update(features, prediction, actual, direction_correct)
    
    # Check drift
    drift = loop.drift_detector.detect()
    print(f"Drift detected: {drift.drift_detected}")
    print(f"Drift type: {drift.drift_type.value}")
    print(f"Data drift score: {drift.data_drift_score:.3f}")
    print(f"Calibration error: {drift.calibration_error:.3f}")
    
    # Check improvement
    result = loop.check_and_improve()
    print(f"\nImprovement result: {result['action']}")
    print(f"Reason: {result['reason']}")
