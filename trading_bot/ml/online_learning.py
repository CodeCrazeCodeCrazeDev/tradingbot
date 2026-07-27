"""Online learning capabilities for continuous model updates.

This module provides utilities for updating ML models in real-time as new data
becomes available, including incremental learning, concept drift detection,
and adaptive model selection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional, Any, Callable
from loguru import logger
import os
import time
import json
import pickle
import datetime
from collections import deque
import threading
import queue
import copy


class OnlineLearner:
    """Base class for online learning algorithms."""
    
    def __init__(self, model: Any, window_size: int = 1000, 
                 update_frequency: int = 100, performance_threshold: float = 0.1,
                 feature_cols: Optional[List[str]] = None,
                 target_col: str = 'close'):
        """Initialize the online learner.
        
        Args:
            model: Pre-trained model to update
            window_size: Size of the sliding window for recent data
            update_frequency: How often to update the model (in samples)
            performance_threshold: Threshold for performance degradation to trigger update
            feature_cols: List of feature column names
            target_col: Target column name
        """
        self.model = model
        self.window_size = window_size
        self.update_frequency = update_frequency
        self.performance_threshold = performance_threshold
        self.feature_cols = feature_cols
        self.target_col = target_col
        
        # Initialize data buffer
        self.data_buffer = deque(maxlen=window_size)
        
        # Performance tracking
        self.baseline_performance = None
        self.current_performance = None
        self.performance_history = []
        
        # Sample counter
        self.samples_since_update = 0
        
        # Update history
        self.update_history = []
        
        logger.info(f"Initialized {self.__class__.__name__} with window_size={window_size}, "
                   f"update_frequency={update_frequency}")
    
    def add_sample(self, sample: Union[Dict[str, float], pd.Series, pd.DataFrame]) -> None:
        """Add a new data sample to the buffer.
        
        Args:
            sample: New data sample (dict, Series, or single-row DataFrame)
        """
        # Convert to appropriate format
        if isinstance(sample, dict):
            sample = pd.Series(sample)
        elif isinstance(sample, pd.DataFrame):
            if len(sample) > 1:
                # Multiple rows, add them one by one
                for i in range(len(sample)):
                    self.add_sample(sample.iloc[i])
                return
            else:
                # Single row DataFrame
                sample = sample.iloc[0]
        
        # Add to buffer
        self.data_buffer.append(sample)
        
        # Increment counter
        self.samples_since_update += 1
        
        # Check if update is needed
        if self.samples_since_update >= self.update_frequency:
            self._check_performance()
    
    def _check_performance(self) -> None:
        """Check model performance and update if needed."""
        # Convert buffer to DataFrame
        buffer_df = pd.DataFrame(list(self.data_buffer))
        
        # Calculate current performance
        self.current_performance = self._evaluate_performance(buffer_df)
        self.performance_history.append({
            'timestamp': datetime.datetime.now(),
            'performance': self.current_performance
        })
        
        # Initialize baseline if not set
        if self.baseline_performance is None:
            self.baseline_performance = self.current_performance
            logger.info(f"Initialized baseline performance: {self.baseline_performance:.6f}")
            try:
                # Perform an initial update using the current buffer
                self._update_model()
                # Base class may not implement; subclasses should override
                logger.debug("_update_model not implemented in base class during initial update")
            finally:
                # Reset counter even on first initialization to satisfy update cadence
                self.samples_since_update = 0
            return
        
        # Check if performance degraded
        if self._detect_performance_degradation():
            logger.info(f"Performance degradation detected: {self.baseline_performance:.6f} -> "
                       f"{self.current_performance:.6f}")
            self._update_model()
        else:
            logger.debug(f"No significant performance degradation: {self.current_performance:.6f}")
        
        # Reset counter
        self.samples_since_update = 0
    
    def _evaluate_performance(self, data: pd.DataFrame) -> float:
        """Evaluate model performance on recent data.
        
        Args:
            data: DataFrame with recent data
            
        Returns:
            Performance metric (higher is better)
        """
        # Default implementation: return accuracy if available
        if hasattr(self, 'model') and hasattr(self.model, 'score'):
            return self.model.score(features, labels)
        return 0.5  # Neutral performance
    
    def _detect_performance_degradation(self) -> bool:
        """Detect if performance has degraded significantly.
        
        Returns:
            True if performance has degraded, False otherwise
        """
        if self.baseline_performance is None or self.current_performance is None:
            return False
        
        # Calculate relative performance change
        relative_change = (self.baseline_performance - self.current_performance) / abs(self.baseline_performance)
        
        # Check if degradation exceeds threshold
        return relative_change > self.performance_threshold
    
    def _update_model(self) -> None:
        """Update the model with recent data."""
        if not self.data_buffer:
            return
        
        # Extract features and labels from buffer
        buffer_df = pd.DataFrame(list(self.data_buffer))
        if self.feature_cols is None:
            X = buffer_df.drop(columns=[self.target_col], errors='ignore').values
        else:
            X = buffer_df[self.feature_cols].values
        y = buffer_df[self.target_col].values if self.target_col in buffer_df.columns else np.zeros(len(buffer_df))
        
        # Update model if it has partial_fit method
        if hasattr(self, 'model') and hasattr(self.model, 'partial_fit'):
            self.model.partial_fit(X, y)
            logger.info(f"Model updated with {len(self.data_buffer)} samples")

    def predict(self, features: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Make predictions using the current model.
        
        Args:
            features: Feature data
            
        Returns:
            Model predictions
        """
        return self.model.predict(features)
    
    def save(self, path: str) -> None:
        """Save the online learner to a file.
        
        Args:
            path: Path to save the learner
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save the learner
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        
        logger.info(f"Saved online learner to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'OnlineLearner':
        """Load an online learner from a file.
        
        Args:
            path: Path to load the learner from
            
        Returns:
            Loaded online learner
        """
        with open(path, 'rb') as f:
            learner = pickle.load(f)
        
        logger.info(f"Loaded online learner from {path}")
        return learner


class IncrementalLearner(OnlineLearner):
    """Incremental learning for models that support partial_fit."""
    
    def __init__(self, model: Any, window_size: int = 1000, 
                 update_frequency: int = 100, performance_threshold: float = 0.1,
                 feature_cols: Optional[List[str]] = None,
                 target_col: str = 'close', batch_size: int = 32,
                 error_metric: str = 'mse'):
        """Initialize the incremental learner.
        
        Args:
            model: Pre-trained model with partial_fit method
            window_size: Size of the sliding window for recent data
            update_frequency: How often to update the model (in samples)
            performance_threshold: Threshold for performance degradation to trigger update
            feature_cols: List of feature column names
            target_col: Target column name
            batch_size: Batch size for incremental updates
            error_metric: Error metric to use ('mse', 'mae', 'rmse')
        """
        super().__init__(model, window_size, update_frequency, 
                        performance_threshold, feature_cols, target_col)
        
        self.batch_size = batch_size
        self.error_metric = error_metric
        
        # Check if model supports partial_fit
        if not hasattr(self.model, 'partial_fit'):
            raise ValueError("Model must support partial_fit method for incremental learning")
    
    def _evaluate_performance(self, data: pd.DataFrame) -> float:
        """Evaluate model performance on recent data.
        
        Args:
            data: DataFrame with recent data
            
        Returns:
            Negative error (higher is better)
        """
        # Extract features and target
        if self.feature_cols is None:
            # Use all columns except target
            X = data.drop(columns=[self.target_col]).values
        else:
            X = data[self.feature_cols].values
        
        y = data[self.target_col].values
        
        # Make predictions
        y_pred = self.model.predict(X)
        
        # Calculate error
        if self.error_metric == 'mse':
            error = np.mean((y - y_pred) ** 2)
        elif self.error_metric == 'mae':
            error = np.mean(np.abs(y - y_pred))
        elif self.error_metric == 'rmse':
            error = np.sqrt(np.mean((y - y_pred) ** 2))
        else:
            raise ValueError(f"Unknown error metric: {self.error_metric}")
        
        # Return negative error (higher is better)
        return -error
    
    def _update_model(self) -> None:
        """Update the model with recent data using partial_fit."""
        # Convert buffer to DataFrame
        buffer_df = pd.DataFrame(list(self.data_buffer))
        
        # Extract features and target
        if self.feature_cols is None:
            # Use all columns except target
            X = buffer_df.drop(columns=[self.target_col]).values
        else:
            X = buffer_df[self.feature_cols].values
        
        y = buffer_df[self.target_col].values
        
        # Update model in batches
        n_samples = len(X)
        n_batches = (n_samples + self.batch_size - 1) // self.batch_size
        
        for i in range(n_batches):
            start_idx = i * self.batch_size
            end_idx = min((i + 1) * self.batch_size, n_samples)
            
            X_batch = X[start_idx:end_idx]
            y_batch = y[start_idx:end_idx]
            
            # Update model
            self.model.partial_fit(X_batch, y_batch)
        
        # Update baseline performance
        self.baseline_performance = self.current_performance
        
        # Record update
        self.update_history.append({
            'timestamp': datetime.datetime.now(),
            'samples': n_samples,
            'performance_before': self.current_performance,
            'performance_after': self.baseline_performance
        })
        
        logger.info(f"Updated model with {n_samples} samples in {n_batches} batches")


class EnsembleOnlineLearner(OnlineLearner):
    """Online learning with ensemble of models."""
    
    def __init__(self, models: List[Any], weights: Optional[List[float]] = None,
                 window_size: int = 1000, update_frequency: int = 100, 
                 performance_threshold: float = 0.1,
                 feature_cols: Optional[List[str]] = None,
                 target_col: str = 'close', error_metric: str = 'mse',
                 dynamic_weighting: bool = True):
        """Initialize the ensemble online learner.
        
        Args:
            models: List of pre-trained models
            weights: Initial weights for each model (normalized to sum to 1)
            window_size: Size of the sliding window for recent data
            update_frequency: How often to update the model (in samples)
            performance_threshold: Threshold for performance degradation to trigger update
            feature_cols: List of feature column names
            target_col: Target column name
            error_metric: Error metric to use ('mse', 'mae', 'rmse')
            dynamic_weighting: Whether to dynamically adjust model weights
        """
        # Use the first model as the base model for OnlineLearner
        super().__init__(models[0], window_size, update_frequency, 
                        performance_threshold, feature_cols, target_col)
        
        self.models = models
        self.n_models = len(models)
        
        # Initialize weights
        if weights is None:
            # Equal weights
            self.weights = np.ones(self.n_models) / self.n_models
        else:
            # Normalize weights
            self.weights = np.array(weights) / np.sum(weights)
        
        self.error_metric = error_metric
        self.dynamic_weighting = dynamic_weighting
        
        # Performance tracking for each model
        self.model_performances = [None] * self.n_models
        
        logger.info(f"Initialized ensemble with {self.n_models} models")
    
    def _evaluate_performance(self, data: pd.DataFrame) -> float:
        """Evaluate ensemble performance on recent data.
        
        Args:
            data: DataFrame with recent data
            
        Returns:
            Negative error (higher is better)
        """
        # Extract features and target
        if self.feature_cols is None:
            # Use all columns except target
            X = data.drop(columns=[self.target_col]).values
        else:
            X = data[self.feature_cols].values
        
        y = data[self.target_col].values
        
        # Make predictions with each model
        predictions = []
        for i, model in enumerate(self.models):
            y_pred = model.predict(X)
            predictions.append(y_pred)
            
            # Calculate individual model performance
            if self.error_metric == 'mse':
                error = np.mean((y - y_pred) ** 2)
            elif self.error_metric == 'mae':
                error = np.mean(np.abs(y - y_pred))
            elif self.error_metric == 'rmse':
                error = np.sqrt(np.mean((y - y_pred) ** 2))
            else:
                raise ValueError(f"Unknown error metric: {self.error_metric}")
            
            self.model_performances[i] = -error
        
        # Weighted ensemble prediction
        y_pred_ensemble = np.zeros_like(y)
        for i, pred in enumerate(predictions):
            y_pred_ensemble += self.weights[i] * pred
        
        # Calculate ensemble error
        if self.error_metric == 'mse':
            error = np.mean((y - y_pred_ensemble) ** 2)
        elif self.error_metric == 'mae':
            error = np.mean(np.abs(y - y_pred_ensemble))
        elif self.error_metric == 'rmse':
            error = np.sqrt(np.mean((y - y_pred_ensemble) ** 2))
        else:
            raise ValueError(f"Unknown error metric: {self.error_metric}")
        
        # Return negative error (higher is better)
        return -error
    
    def _update_model(self) -> None:
        """Update the ensemble by adjusting weights or updating individual models."""
        if self.dynamic_weighting and all(p is not None for p in self.model_performances):
            # Convert performances to positive values
            performances = np.array(self.model_performances)
            performances = performances - np.min(performances)
            
            # Add small epsilon to avoid division by zero
            performances = performances + 1e-10
            
            # Update weights based on performance
            new_weights = performances / np.sum(performances)
            
            logger.info(f"Updated ensemble weights: {self.weights} -> {new_weights}")
            self.weights = new_weights
        
        # Update individual models if they support partial_fit
        buffer_df = pd.DataFrame(list(self.data_buffer))
        
        # Extract features and target
        if self.feature_cols is None:
            # Use all columns except target
            X = buffer_df.drop(columns=[self.target_col]).values
        else:
            X = buffer_df[self.feature_cols].values
        
        y = buffer_df[self.target_col].values
        
        # Update models that support partial_fit
        for i, model in enumerate(self.models):
            if hasattr(model, 'partial_fit'):
                model.partial_fit(X, y)
                logger.info(f"Updated model {i} with {len(X)} samples")
        
        # Update baseline performance
        self.baseline_performance = self.current_performance
        
        # Record update
        self.update_history.append({
            'timestamp': datetime.datetime.now(),
            'samples': len(X),
            'performance_before': self.current_performance,
            'performance_after': self.baseline_performance,
            'weights': self.weights.tolist()
        })
    
    def predict(self, features: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Make predictions using the weighted ensemble.
        
        Args:
            features: Feature data
            
        Returns:
            Ensemble predictions
        """
        # Make predictions with each model
        predictions = []
        for model in self.models:
            y_pred = model.predict(features)
            predictions.append(y_pred)
        
        # Weighted ensemble prediction
        y_pred_ensemble = np.zeros_like(predictions[0])
        for i, pred in enumerate(predictions):
            y_pred_ensemble += self.weights[i] * pred
        
        return y_pred_ensemble


class ConceptDriftDetector:
    """Detect concept drift in data streams."""
    
    def __init__(self, window_size: int = 100, alpha: float = 0.05,
                 drift_threshold: float = 0.1):
        """Initialize the concept drift detector.
        
        Args:
            window_size: Size of the sliding window
            alpha: Significance level for drift detection
            drift_threshold: Threshold for drift magnitude
        """
        self.window_size = window_size
        self.alpha = alpha
        self.drift_threshold = drift_threshold
        
        # Reference window
        self.reference_window = deque(maxlen=window_size)
        self.reference_mean = None
        self.reference_std = None
        
        # Current window
        self.current_window = deque(maxlen=window_size)
        
        # Drift history
        self.drift_history = []
        
        logger.info(f"Initialized concept drift detector with window_size={window_size}, "
                   f"alpha={alpha}, drift_threshold={drift_threshold}")
    
    def add_sample(self, value: float) -> bool:
        """Add a new sample and check for drift.
        
        Args:
            value: New sample value
            
        Returns:
            True if drift detected, False otherwise
        """
        # Initialize reference window if empty
        if len(self.reference_window) == 0:
            self._initialize_reference(value)
            return False
        
        # Add to current window
        self.current_window.append(value)
        
        # Check for drift if current window is full
        if len(self.current_window) == self.window_size:
            return self._check_drift()
        
        return False
    
    def _initialize_reference(self, value: float) -> None:
        """Initialize reference window with first value.
        
        Args:
            value: Initial value
        """
        self.reference_window.append(value)
        self.reference_mean = value
        self.reference_std = 1.0  # Avoid division by zero
    
    def _check_drift(self) -> bool:
        """Check if drift has occurred.
        
        Returns:
            True if drift detected, False otherwise
        """
        # Calculate statistics
        current_mean = np.mean(self.current_window)
        current_std = np.std(self.current_window)
        
        if self.reference_mean is None or self.reference_std is None:
            # Calculate reference statistics
            self.reference_mean = np.mean(self.reference_window)
            self.reference_std = np.std(self.reference_window)
            return False
        
        # Calculate z-score
        z_score = abs(current_mean - self.reference_mean) / (
            self.reference_std / np.sqrt(self.window_size)
        )
        
        # Calculate p-value
        from scipy import stats
        p_value = 2 * (1 - stats.norm.cdf(z_score))
        
        # Calculate drift magnitude
        drift_magnitude = abs(current_mean - self.reference_mean) / abs(self.reference_mean)
        
        # Check for significant drift
        drift_detected = (p_value < self.alpha) and (drift_magnitude > self.drift_threshold)
        
        # Record drift event
        self.drift_history.append({
            'timestamp': datetime.datetime.now(),
            'reference_mean': self.reference_mean,
            'current_mean': current_mean,
            'p_value': p_value,
            'drift_magnitude': drift_magnitude,
            'drift_detected': drift_detected
        })
        
        # If drift detected, update reference window
        if drift_detected:
            logger.info(f"Concept drift detected: magnitude={drift_magnitude:.4f}, "
                       f"p_value={p_value:.6f}")
            self.reference_window = copy.copy(self.current_window)
            self.reference_mean = current_mean
            self.reference_std = current_std
        
        # Clear current window
        self.current_window.clear()
        
        return drift_detected


class AsyncOnlineLearner:
    """Asynchronous online learning with background updates."""
    
    def __init__(self, model: Any, window_size: int = 1000,
                 update_frequency: int = 100, feature_cols: Optional[List[str]] = None,
                 target_col: str = 'close'):
        """Initialize the asynchronous online learner.
        
        Args:
            model: Pre-trained model
            window_size: Size of the sliding window for recent data
            update_frequency: How often to update the model (in samples)
            feature_cols: List of feature column names
            target_col: Target column name
        """
        self.model = model
        self.window_size = window_size
        self.update_frequency = update_frequency
        self.feature_cols = feature_cols
        self.target_col = target_col
        
        # Initialize data buffer
        self.data_buffer = deque(maxlen=window_size)
        
        # Sample counter
        self.samples_since_update = 0
        
        # Update history
        self.update_history = []
        
        # Threading
        self.update_queue = queue.Queue()
        self.update_thread = None
        self.stop_event = threading.Event()
        
        # Model lock for thread safety
        self.model_lock = threading.RLock()
        
        logger.info(f"Initialized {self.__class__.__name__} with window_size={window_size}, "
                   f"update_frequency={update_frequency}")
    
    def start(self) -> None:
        """Start the background update thread."""
        if self.update_thread is not None and self.update_thread.is_alive():
            logger.warning("Update thread is already running")
            return
        
        # Reset stop event
        self.stop_event.clear()
        
        # Start update thread
        self.update_thread = threading.Thread(
            target=self._update_loop,
            daemon=True
        )
        self.update_thread.start()
        
        logger.info("Started background update thread")
    
    def stop(self) -> None:
        """Stop the background update thread."""
        if self.update_thread is None or not self.update_thread.is_alive():
            logger.warning("Update thread is not running")
            return
        
        # Set stop event
        self.stop_event.set()
        
        # Wait for thread to finish
        self.update_thread.join(timeout=5.0)
        
        if self.update_thread.is_alive():
            logger.warning("Update thread did not stop gracefully")
        else:
            logger.info("Stopped background update thread")
    
    def add_sample(self, sample: Union[Dict[str, float], pd.Series, pd.DataFrame]) -> None:
        """Add a new data sample to the buffer.
        
        Args:
            sample: New data sample (dict, Series, or single-row DataFrame)
        """
        # Convert to appropriate format
        if isinstance(sample, dict):
            sample = pd.Series(sample)
        elif isinstance(sample, pd.DataFrame):
            if len(sample) > 1:
                # Multiple rows, add them one by one
                for i in range(len(sample)):
                    self.add_sample(sample.iloc[i])
                return
            else:
                # Single row DataFrame
                sample = sample.iloc[0]
        
        # Add to buffer
        self.data_buffer.append(sample)
        
        # Increment counter
        self.samples_since_update += 1
        
        # Check if update is needed
        if self.samples_since_update >= self.update_frequency:
            # Reset counter
            self.samples_since_update = 0
            
            # Queue update
            buffer_df = pd.DataFrame(list(self.data_buffer))
            self.update_queue.put(buffer_df)
    
    def _update_loop(self) -> None:
        """Background thread for model updates."""
        logger.info("Update thread started")
        
        while not self.stop_event.is_set():
            try:
                # Get data from queue with timeout
                data = self.update_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            # Update model
            self._update_model(data)
            
            # Mark task as done
            self.update_queue.task_done()
        
        logger.info("Update thread stopped")
    
    def _update_model(self, data: pd.DataFrame) -> None:
        """Update the model with recent data.
        
        Args:
            data: DataFrame with recent data
        """
        # Extract features and target
        if self.feature_cols is None:
            # Use all columns except target
            X = data.drop(columns=[self.target_col]).values
        else:
            X = data[self.feature_cols].values
        
        y = data[self.target_col].values
        
        # Update model if it supports partial_fit
        if hasattr(self.model, 'partial_fit'):
            with self.model_lock:
                self.model.partial_fit(X, y)
            
            # Record update
            self.update_history.append({
                'timestamp': datetime.datetime.now(),
                'samples': len(X)
            })
            
            logger.info(f"Updated model with {len(X)} samples")
        else:
            logger.warning("Model does not support partial_fit, skipping update")
    
    def predict(self, features: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Make predictions using the current model.
        
        Args:
            features: Feature data
            
        Returns:
            Model predictions
        """
        with self.model_lock:
            return self.model.predict(features)
    
    def __getstate__(self):
        """Customize pickling by removing unpicklable threading primitives."""
        state = self.__dict__.copy()
        # Do not pickle active threading and synchronization objects
        state['update_thread'] = None
        state['stop_event'] = None
        state['update_queue'] = None
        state['model_lock'] = None
        return state
    
    def __setstate__(self, state):
        """Restore state and reinitialize threading primitives after unpickling."""
        self.__dict__.update(state)
        # Recreate threading and synchronization objects
        self.update_queue = queue.Queue()
        self.update_thread = None
        self.stop_event = threading.Event()
        self.model_lock = threading.RLock()
    
    def save(self, path: str) -> None:
        """Save the online learner to a file.
        
        Args:
            path: Path to save the learner
        """
        # Stop the update thread
        was_running = False
        if self.update_thread is not None and self.update_thread.is_alive():
            was_running = True
            self.stop()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save the learner
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        
        logger.info(f"Saved online learner to {path}")
        
        # Restart the update thread if it was running
        if was_running:
            self.start()
    
    @classmethod
    def load(cls, path: str) -> 'AsyncOnlineLearner':
        """Load an online learner from a file.
        
        Args:
            path: Path to load the learner from
            
        Returns:
            Loaded online learner
        """
        with open(path, 'rb') as f:
            learner = pickle.load(f)
        
        logger.info(f"Loaded online learner from {path}")
        return learner
