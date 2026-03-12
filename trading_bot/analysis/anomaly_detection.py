"""
Advanced Anomaly Detection Module
Detects market anomalies using statistical and ML-based methods.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
try:
    from scipy import stats
except ImportError:
    stats = None

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    torch = None
    nn = None
    F = None

logger = logging.getLogger(__name__)


@dataclass
class AnomalySignal:
    """Detected market anomaly signal."""
    timestamp: datetime
    anomaly_type: str
    severity: float
    confidence: float
    features: Dict[str, float]
    metadata: Dict[str, Any]


class AutoEncoder(nn.Module):
    """Neural autoencoder for anomaly detection."""
    
    def __init__(self, input_dim: int, hidden_dim: int = 10):
        """Initialize autoencoder."""
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, input_dim),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class AdvancedAnomalyDetector:
    """
    Advanced anomaly detection using multiple methods.
    
    Features:
    - Statistical anomaly detection
    - Isolation Forest
    - Autoencoder-based detection
    - Ensemble approach
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize anomaly detector."""
        self.config = config or {}
        
        # Parameters
        self.lookback_window = self.config.get('lookback_window', 100)
        self.anomaly_threshold = self.config.get('anomaly_threshold', 2.5)
        self.min_samples = self.config.get('min_samples', 50)
        
        # Initialize models
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% variance
        
        # Initialize autoencoder
        self.autoencoder = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Store anomaly history
        self.anomaly_history: List[AnomalySignal] = []
    
    def detect_anomalies(self, data: pd.DataFrame) -> List[AnomalySignal]:
        """
        Detect anomalies in market data using multiple methods.
        
        Args:
            data: Market data with OHLCV and other features
            
        Returns:
            List of detected anomalies
        """
        if len(data) < self.min_samples:
            return []
        try:
        
            # Extract features
            features = self._extract_features(data)
            
            # Detect anomalies using different methods
            statistical_anomalies = self._detect_statistical_anomalies(features)
            isolation_anomalies = self._detect_isolation_forest_anomalies(features)
            autoencoder_anomalies = self._detect_autoencoder_anomalies(features)
            
            # Combine anomalies
            all_anomalies = (
                statistical_anomalies +
                isolation_anomalies +
                autoencoder_anomalies
            )
            
            # Store in history
            self.anomaly_history.extend(all_anomalies)
            if len(self.anomaly_history) > 1000:
                self.anomaly_history = self.anomaly_history[-1000:]
            
            return all_anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract features for anomaly detection."""
        features = pd.DataFrame()
        
        # Price features
        features['returns'] = data['close'].pct_change()
        features['log_returns'] = np.log(data['close']).diff()
        features['volatility'] = features['returns'].rolling(20).std()
        
        # Volume features
        features['volume_change'] = data['volume'].pct_change()
        features['relative_volume'] = data['volume'] / data['volume'].rolling(20).mean()
        
        # Price range features
        features['high_low_range'] = (data['high'] - data['low']) / data['close']
        features['body_size'] = abs(data['close'] - data['open']) / data['close']
        
        # Momentum features
        features['rsi'] = self._calculate_rsi(data['close'])
        features['momentum'] = data['close'].diff(5) / data['close']
        
        # Clean and normalize features
        features = features.replace([np.inf, -np.inf], np.nan)
        features = features.fillna(method='ffill')
        features = features.fillna(0)
        
        return features
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _detect_statistical_anomalies(self, features: pd.DataFrame) -> List[AnomalySignal]:
        """Detect anomalies using statistical methods."""
        anomalies = []
        
        for column in features.columns:
            series = features[column].values
            if len(series) < self.lookback_window:
                continue
            
            # Calculate z-scores
            rolling_mean = pd.Series(series).rolling(self.lookback_window).mean()
            rolling_std = pd.Series(series).rolling(self.lookback_window).std()
            z_scores = (series - rolling_mean) / rolling_std
            
            # Detect anomalies
            anomaly_points = np.where(abs(z_scores) > self.anomaly_threshold)[0]
            
            for idx in anomaly_points:
                if idx < len(features):
                    anomalies.append(AnomalySignal(
                        timestamp=features.index[idx],
                        anomaly_type='statistical',
                        severity=abs(z_scores[idx]),
                        confidence=min(abs(z_scores[idx]) / (self.anomaly_threshold * 2), 0.95),
                        features={
                            'feature': column,
                            'value': float(series[idx]),
                            'z_score': float(z_scores[idx])
                        },
                        metadata={
                            'method': 'z_score',
                            'threshold': self.anomaly_threshold
                        }
                    ))
        
        return anomalies
    
    def _detect_isolation_forest_anomalies(self, features: pd.DataFrame) -> List[AnomalySignal]:
        """Detect anomalies using Isolation Forest."""
        try:
            # Scale features
            scaled_features = self.scaler.fit_transform(features)
            
            # Reduce dimensionality
            pca_features = self.pca.fit_transform(scaled_features)
            
            # Fit and predict
            predictions = self.isolation_forest.fit_predict(pca_features)
            scores = self.isolation_forest.score_samples(pca_features)
            
            anomalies = []
            
            # Find anomalies
            for idx in range(len(predictions)):
                if predictions[idx] == -1:  # Anomaly
                    anomaly_score = -scores[idx]  # Convert to anomaly score
                    
                    anomalies.append(AnomalySignal(
                        timestamp=features.index[idx],
                        anomaly_type='isolation_forest',
                        severity=float(anomaly_score),
                        confidence=min(anomaly_score / 2, 0.95),
                        features={
                            'anomaly_score': float(anomaly_score),
                            'principal_components': pca_features[idx].tolist()
                        },
                        metadata={
                            'method': 'isolation_forest',
                            'n_components': pca_features.shape[1]
                        }
                    ))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in isolation forest detection: {e}")
            return []
    
    def _detect_autoencoder_anomalies(self, features: pd.DataFrame) -> List[AnomalySignal]:
        """Detect anomalies using autoencoder."""
        try:
            # Initialize autoencoder if needed
            if self.autoencoder is None:
                input_dim = features.shape[1]
                self.autoencoder = AutoEncoder(input_dim).to(self.device)
            
            # Scale features
            scaled_features = self.scaler.fit_transform(features)
            
            # Convert to tensor
            X = torch.FloatTensor(scaled_features).to(self.device)
            
            # Get reconstruction error
            self.autoencoder.eval()
            with torch.no_grad():
                reconstructed = self.autoencoder(X)
                reconstruction_errors = F.mse_loss(reconstructed, X, reduction='none')
                reconstruction_errors = reconstruction_errors.mean(dim=1).cpu().numpy()
            
            # Calculate threshold
            error_threshold = np.mean(reconstruction_errors) + self.anomaly_threshold * np.std(reconstruction_errors)
            
            anomalies = []
            
            # Detect anomalies
            for idx in range(len(reconstruction_errors)):
                if reconstruction_errors[idx] > error_threshold:
                    anomalies.append(AnomalySignal(
                        timestamp=features.index[idx],
                        anomaly_type='autoencoder',
                        severity=float(reconstruction_errors[idx]),
                        confidence=min(reconstruction_errors[idx] / (error_threshold * 2), 0.95),
                        features={
                            'reconstruction_error': float(reconstruction_errors[idx]),
                            'threshold': float(error_threshold)
                        },
                        metadata={
                            'method': 'autoencoder',
                            'model_type': 'neural_network'
                        }
                    ))
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in autoencoder detection: {e}")
            return []
    
    def get_active_anomalies(self, current_time: datetime,
                           max_age_minutes: int = 60) -> List[AnomalySignal]:
        """Get currently active anomalies."""
        active_anomalies = []
        
        for anomaly in self.anomaly_history:
            age_minutes = (current_time - anomaly.timestamp).total_seconds() / 60
            if age_minutes <= max_age_minutes:
                active_anomalies.append(anomaly)
        
        return active_anomalies
    
    def train_autoencoder(self, training_data: pd.DataFrame,
                         epochs: int = 100,
                         batch_size: int = 32):
        """Train autoencoder on historical data."""
        try:
            # Extract and scale features
            features = self._extract_features(training_data)
            scaled_features = self.scaler.fit_transform(features)
            
            # Convert to tensor
            X = torch.FloatTensor(scaled_features).to(self.device)
            
            # Initialize autoencoder
            input_dim = features.shape[1]
            self.autoencoder = AutoEncoder(input_dim).to(self.device)
            optimizer = torch.optim.Adam(self.autoencoder.parameters())
            
            # Training loop
            self.autoencoder.train()
            for epoch in range(epochs):
                total_loss = 0
                for i in range(0, len(X), batch_size):
                    batch = X[i:i+batch_size]
                    
                    # Forward pass
                    reconstructed = self.autoencoder(batch)
                    loss = F.mse_loss(reconstructed, batch)
                    
                    # Backward pass
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(X):.6f}")
            
            logger.info("Autoencoder training completed")
            
        except Exception as e:
            logger.error(f"Error training autoencoder: {e}")
    
    def save_state(self, filepath: str):
        """Save detector state to file."""
        try:
            state = {
                'scaler': self.scaler,
                'pca': self.pca,
                'isolation_forest': self.isolation_forest,
                'autoencoder_state': self.autoencoder.state_dict() if self.autoencoder else None,
                'config': self.config
            }
            torch.save(state, filepath)
            logger.info(f"Detector state saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving detector state: {e}")
    
    def load_state(self, filepath: str):
        """Load detector state from file."""
        try:
            state = torch.load(filepath)
            self.scaler = state['scaler']
            self.pca = state['pca']
            self.isolation_forest = state['isolation_forest']
            
            if state['autoencoder_state']:
                input_dim = next(iter(state['autoencoder_state'].values())).shape[1]
                self.autoencoder = AutoEncoder(input_dim).to(self.device)
                self.autoencoder.load_state_dict(state['autoencoder_state'])
            
            self.config = state['config']
            logger.info(f"Detector state loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading detector state: {e}")


# Alias for backward compatibility
AnomalyDetector = AdvancedAnomalyDetector
