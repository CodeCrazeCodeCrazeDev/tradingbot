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
        self.config = config or {}
        self.client_id = self.config.get('client_id', 'client_0')
        self.privacy_epsilon = self.config.get('privacy_epsilon', 1.0)
        self.model_weights = np.random.randn(10) * 0.1
        self.local_data: List[np.ndarray] = []
        logger.info(f"FederatedLearningClient {self.client_id} initialized")
    
    def add_local_data(self, prices: np.ndarray, volumes: np.ndarray):
        """Add local training data."""
        features = self._extract_features(prices, volumes)
        self.local_data.append(features)
    
    def _extract_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Extract features from local data."""
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
    
    def compute_local_update(self) -> LocalUpdate:
        """Compute local gradient update."""
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
    
    def apply_global_update(self, global_weights: np.ndarray):
        """Apply global model update."""
        self.model_weights = global_weights
    
    def predict(self, prices: np.ndarray, volumes: np.ndarray) -> FederatedResult:
        """Make prediction using federated model."""
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


class FederatedServer:
    """Federated learning server for aggregating updates."""
    
    def __init__(self):
        self.global_model = np.random.randn(10) * 0.1
        self.client_weights: Dict[str, float] = {}
    
    def aggregate_updates(self, updates: List[LocalUpdate]) -> np.ndarray:
        """Aggregate client updates using FedAvg."""
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
