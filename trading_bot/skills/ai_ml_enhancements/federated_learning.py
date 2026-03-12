"""
Skill #22: Federated Learning Client
====================================

Privacy-preserving distributed learning across multiple
data sources without sharing raw data.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LocalUpdate:
    """Local model update from federated client."""
    client_id: str
    gradients: np.ndarray
    num_samples: int
    local_loss: float


@dataclass
class FederatedResult:
    """Federated learning result."""
    global_model: np.ndarray
    client_contributions: Dict[str, float]
    aggregated_loss: float
    privacy_budget: float
    trading_signal: str


class FederatedLearningClient:
    """Federated learning client for privacy-preserving model training."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.client_id = self.config.get('client_id', 'client_0')
            self.privacy_epsilon = self.config.get('privacy_epsilon', 1.0)
            self.model_weights = np.random.randn(10) * 0.1
            self.local_data: List[np.ndarray] = []
            logger.info(f"FederatedLearningClient {self.client_id} initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_local_data(self, prices: np.ndarray, volumes: np.ndarray):
        """Add local training data."""
        try:
            features = self._extract_features(prices, volumes)
            self.local_data.append(features)
        except Exception as e:
            logger.error(f"Error in add_local_data: {e}")
            raise
    
    def _extract_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Extract features from local data."""
        try:
            if len(prices) < 10:
                return np.zeros(10)
            returns = np.diff(prices) / prices[:-1]
            return np.array([
                np.mean(returns), np.std(returns),
                np.min(returns), np.max(returns),
                prices[-1] / prices[0] - 1,
                np.mean(volumes) / 1000,
                len(prices), 0, 0, 0
            ])
        except Exception as e:
            logger.error(f"Error in _extract_features: {e}")
            raise
    
    def compute_local_update(self) -> LocalUpdate:
        """Compute local gradient update."""
        try:
            if not self.local_data:
                return LocalUpdate(self.client_id, np.zeros(10), 0, 0)
        
            # Compute gradients (simplified)
            X = np.array(self.local_data)
            gradients = np.mean(X, axis=0) - self.model_weights
        
            # Add differential privacy noise
            noise = np.random.laplace(0, 1/self.privacy_epsilon, gradients.shape)
            private_gradients = gradients + noise
        
            loss = np.mean((X - self.model_weights) ** 2)
        
            return LocalUpdate(
                client_id=self.client_id,
                gradients=private_gradients,
                num_samples=len(self.local_data),
                local_loss=loss
            )
        except Exception as e:
            logger.error(f"Error in compute_local_update: {e}")
            raise
    
    def apply_global_update(self, global_weights: np.ndarray):
        """Apply global model update."""
        try:
            self.model_weights = global_weights
        except Exception as e:
            logger.error(f"Error in apply_global_update: {e}")
            raise
    
    def predict(self, prices: np.ndarray, volumes: np.ndarray) -> FederatedResult:
        """Make prediction using federated model."""
        try:
            features = self._extract_features(prices, volumes)
            prediction = np.dot(features, self.model_weights)
        
            signal = "BUY" if prediction > 0 else "SELL" if prediction < 0 else "NEUTRAL"
        
            return FederatedResult(
                global_model=self.model_weights,
                client_contributions={self.client_id: 1.0},
                aggregated_loss=0,
                privacy_budget=self.privacy_epsilon,
                trading_signal=f"{signal}: Federated prediction {prediction:.4f}"
            )
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            raise


class FederatedServer:
    """Federated learning server for aggregating updates."""
    
    def __init__(self):
        try:
            self.global_model = np.random.randn(10) * 0.1
            self.client_weights: Dict[str, float] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def aggregate_updates(self, updates: List[LocalUpdate]) -> np.ndarray:
        """Aggregate client updates using FedAvg."""
        try:
            if not updates:
                return self.global_model
        
            total_samples = sum(u.num_samples for u in updates)
            if total_samples == 0:
                return self.global_model
        
            weighted_gradients = np.zeros_like(self.global_model)
            for update in updates:
                weight = update.num_samples / total_samples
                weighted_gradients += weight * update.gradients
                self.client_weights[update.client_id] = weight
        
            self.global_model += 0.1 * weighted_gradients
            return self.global_model
        except Exception as e:
            logger.error(f"Error in aggregate_updates: {e}")
            raise
