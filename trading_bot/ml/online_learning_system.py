"""
Online learning system for continuous model adaptation.
Enables models to learn from new data without full retraining.
"""

import numpy as np
try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
from collections import deque
from typing import Dict, Optional, Tuple
from loguru import logger
import numpy

import logging
logger = logging.getLogger(__name__)



class OnlineLearningSystem:
    """Online learning wrapper for continuous adaptation."""
    
    def __init__(self, model: nn.Module, learning_rate: float = 0.0001,
                 buffer_size: int = 10000, update_frequency: int = 100):
        """
        Initialize online learning system.
        
        Args:
            model: PyTorch model to train online
            learning_rate: Learning rate for online updates
            buffer_size: Size of experience replay buffer
            update_frequency: Update model every N samples
        """
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        # Experience replay buffer
        self.buffer = deque(maxlen=buffer_size)
        self.update_frequency = update_frequency
        self.samples_seen = 0
        
        # Performance tracking
        self.online_losses = []
        self.adaptation_metrics = {
            'updates': 0,
            'avg_loss': 0.0,
            'samples_processed': 0
        }
        
        logger.info(f"Online learning system initialized (buffer: {buffer_size})")
    
    def add_experience(self, state: np.ndarray, target: float):
        """Add new experience to buffer."""
        self.buffer.append((state, target))
        self.samples_seen += 1
        
        # Trigger update if frequency reached
        if self.samples_seen % self.update_frequency == 0:
            self.update_model()
    
    def update_model(self, batch_size: int = 32):
        """Update model with recent experiences."""
        if len(self.buffer) < batch_size:
            return
        
        # Sample batch from buffer
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[i] for i in indices]
        
        states = torch.FloatTensor([s for s, _ in batch])
        targets = torch.FloatTensor([[t] for _, t in batch])
        
        # Forward pass
        self.model.train()
        predictions = self.model(states)
        loss = self.criterion(predictions, targets)
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        # Track metrics
        self.online_losses.append(loss.item())
        self.adaptation_metrics['updates'] += 1
        self.adaptation_metrics['avg_loss'] = np.mean(self.online_losses[-100:])
        self.adaptation_metrics['samples_processed'] = self.samples_seen
        
        if self.adaptation_metrics['updates'] % 10 == 0:
            logger.info(f"Online update #{self.adaptation_metrics['updates']}: "
                       f"Loss={loss.item():.6f}, Avg={self.adaptation_metrics['avg_loss']:.6f}")
    
    def get_metrics(self) -> Dict:
        """Get online learning metrics."""
        return self.adaptation_metrics.copy()


class ConceptDriftDetector:
    """Detect concept drift in data distribution."""
    
    def __init__(self, window_size: int = 1000, threshold: float = 0.05):
        """
        Initialize drift detector.
        
        Args:
            window_size: Size of sliding window
            threshold: Drift detection threshold
        """
        self.window_size = window_size
        self.threshold = threshold
        self.reference_window = deque(maxlen=window_size)
        self.current_window = deque(maxlen=window_size)
        self.drift_detected = False
        
        logger.info(f"Concept drift detector initialized (window: {window_size})")
    
    def add_sample(self, error: float):
        """Add prediction error sample."""
        if len(self.reference_window) < self.window_size:
            self.reference_window.append(error)
        else:
            self.current_window.append(error)
            
            if len(self.current_window) >= self.window_size // 2:
                self._check_drift()
    
    def _check_drift(self):
        """Check for concept drift using statistical test."""
        if len(self.current_window) < 10:
            return
        
        # Calculate statistics
        ref_mean = np.mean(self.reference_window)
        ref_std = np.std(self.reference_window)
        curr_mean = np.mean(self.current_window)
        
        # Z-test for mean difference
        if ref_std > 0:
            z_score = abs(curr_mean - ref_mean) / (ref_std / np.sqrt(len(self.current_window)))
            
            if z_score > 2.0:  # 95% confidence
                self.drift_detected = True
                logger.warning(f"Concept drift detected! Z-score: {z_score:.2f}")
                
                # Reset windows
                self.reference_window = self.current_window.copy()
                self.current_window.clear()
    
    def has_drift(self) -> bool:
        """Check if drift was detected."""
        if self.drift_detected:
            self.drift_detected = False  # Reset flag
            return True
        return False


class AdaptiveModelManager:
    """Manage model adaptation and retraining."""
    
    def __init__(self, model: nn.Module, retrain_threshold: int = 10000):
        """
        Initialize adaptive model manager.
        
        Args:
            model: Model to manage
            retrain_threshold: Trigger full retrain after N samples
        """
        self.model = model
        self.retrain_threshold = retrain_threshold
        
        self.online_learner = OnlineLearningSystem(model)
        self.drift_detector = ConceptDriftDetector()
        
        self.samples_since_retrain = 0
        self.retrain_count = 0
        
        logger.info("Adaptive model manager initialized")
    
    def process_sample(self, state: np.ndarray, target: float, 
                      prediction: float) -> Dict:
        """
        Process new sample with online learning and drift detection.
        
        Args:
            state: Input features
            target: True target value
            prediction: Model prediction
            
        Returns:
            Status dictionary
        """
        # Calculate error
        error = abs(prediction - target)
        
        # Add to online learner
        self.online_learner.add_experience(state, target)
        
        # Check for drift
        self.drift_detector.add_sample(error)
        
        self.samples_since_retrain += 1
        
        status = {
            'samples_since_retrain': self.samples_since_retrain,
            'drift_detected': self.drift_detector.has_drift(),
            'needs_retrain': self.samples_since_retrain >= self.retrain_threshold,
            'online_metrics': self.online_learner.get_metrics()
        }
        
        # Trigger retrain if needed
        if status['needs_retrain'] or status['drift_detected']:
            logger.warning("Model retrain triggered")
            status['retrain_triggered'] = True
            self.samples_since_retrain = 0
            self.retrain_count += 1
        
        return status
    
    def get_status(self) -> Dict:
        """Get manager status."""
        return {
            'retrain_count': self.retrain_count,
            'samples_since_retrain': self.samples_since_retrain,
            'online_metrics': self.online_learner.get_metrics()
        }


class IncrementalFeatureSelector:
    """Incremental feature selection for online learning."""
    
    def __init__(self, n_features: int, selection_frequency: int = 1000):
        """
        Initialize incremental feature selector.
        
        Args:
            n_features: Number of features
            selection_frequency: Update selection every N samples
        """
        self.n_features = n_features
        self.selection_frequency = selection_frequency
        
        # Track feature importance
        self.feature_importance = np.ones(n_features)
        self.feature_usage = np.zeros(n_features)
        self.samples_seen = 0
        
        logger.info(f"Incremental feature selector initialized ({n_features} features)")
    
    def update_importance(self, features: np.ndarray, gradient: np.ndarray):
        """Update feature importance based on gradients."""
        # Use gradient magnitude as importance signal
        importance = np.abs(gradient)
        
        # Exponential moving average
        alpha = 0.1
        self.feature_importance = (1 - alpha) * self.feature_importance + alpha * importance
        self.feature_usage += 1
        self.samples_seen += 1
    
    def get_top_features(self, k: int) -> np.ndarray:
        """Get indices of top k features."""
        return np.argsort(self.feature_importance)[-k:]
    
    def get_feature_mask(self, threshold: float = 0.1) -> np.ndarray:
        """Get binary mask for important features."""
        normalized_importance = self.feature_importance / (self.feature_importance.max() + 1e-10)
        return (normalized_importance > threshold).astype(float)
