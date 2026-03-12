"""
Institutional Footprint DNA Module
Detects and analyzes institutional trading patterns using ML and order flow analysis.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import logging
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
try:
    import tensorflow as tf
except ImportError:
    tf = None
from tensorflow.keras import layers, models
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class OrderFlowPattern:
    """A detected institutional order flow pattern."""
    pattern_type: str  # accumulation, distribution, absorption, etc.
    start_time: datetime
    end_time: datetime
    price_range: Tuple[float, float]
    volume: float
    confidence: float
    features: Dict[str, float]
    metadata: Dict[str, Any]


class InstitutionalFootprintDNA:
    """
    Detects institutional trading patterns using ML and order flow analysis.
    
    Features:
    - Order flow pattern recognition
    - Volume profile analysis
    - Institutional cluster detection
    - Smart money footprint tracking
    - Neural network pattern matching
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the institutional footprint detector."""
        self.config = config or {}
        
        # Pattern detection parameters (must be set before building model)
        self.min_cluster_size = self.config.get('min_cluster_size', 10)
        self.volume_threshold = self.config.get('volume_threshold', 0.8)
        self.time_window = self.config.get('time_window', 100)
        
        # Neural network for pattern recognition
        self.pattern_model = self._build_pattern_model()
        
        # Historical patterns storage
        self.detected_patterns: List[OrderFlowPattern] = []
    
    def _build_pattern_model(self) -> tf.keras.Model:
        """Build neural network for pattern recognition."""
        try:
            # Input features: OHLCV + derived features
            inputs = layers.Input(shape=(self.time_window, 10))
            
            # CNN layers for pattern detection
            x = layers.Conv1D(64, 5, activation='relu')(inputs)
            x = layers.MaxPooling1D(2)(x)
            x = layers.Conv1D(128, 3, activation='relu')(x)
            x = layers.MaxPooling1D(2)(x)
            
            # LSTM layers for temporal patterns
            x = layers.LSTM(64, return_sequences=True)(x)
            x = layers.LSTM(32)(x)
            
            # Dense layers for classification
            x = layers.Dense(32, activation='relu')(x)
            x = layers.Dropout(0.3)(x)
            outputs = layers.Dense(4, activation='softmax')(x)  # 4 pattern types
            
            model = models.Model(inputs=inputs, outputs=outputs)
            model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
            
            return model
            
        except Exception as e:
            logger.error(f"Error building pattern model: {e}")
            return None
    
    def detect_patterns(self, data: pd.DataFrame, timeframe: str) -> List[OrderFlowPattern]:
        """
        Detect institutional trading patterns in market data.
        
        Args:
            data: OHLCV data with order flow information
            timeframe: Current timeframe
            
        Returns:
            List of detected patterns
        """
        try:
            # Extract features
            features = self._extract_features(data)
            
            # Detect clusters
            clusters = self._detect_clusters(features)
            
            # Analyze patterns
            patterns = []
            for cluster_id in np.unique(clusters):
                if cluster_id == -1:  # Noise points
                    continue
                
                cluster_mask = clusters == cluster_id
                cluster_data = data[cluster_mask]
                cluster_features = features[cluster_mask]
                
                # Analyze cluster characteristics
                pattern = self._analyze_cluster(cluster_data, cluster_features, timeframe)
                if pattern:
                    patterns.append(pattern)
                    self.detected_patterns.append(pattern)
            
            # Limit pattern history
            if len(self.detected_patterns) > 1000:
                self.detected_patterns = self.detected_patterns[-1000:]
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []
    
    def _extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract features for pattern detection."""
        features = []
        
        try:
            # Volume features
            features.append(data['volume'].values)
            features.append(data['volume'].pct_change().values)
            features.append(data['volume'].rolling(5).mean().values)
            
            # Price features
            features.append(data['close'].pct_change().values)
            features.append((data['high'] - data['low']).values)
            features.append((data['close'] - data['open']).values)
            
            # Order flow features
            if 'buy_volume' in data.columns and 'sell_volume' in data.columns:
                features.append(data['buy_volume'].values / data['sell_volume'].values)
            
            # Volatility features
            returns = data['close'].pct_change()
            features.append(returns.rolling(20).std().values)
            
            # Stack and normalize features
            features = np.column_stack(features)
            features = StandardScaler().fit_transform(features)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.array([])
    
    def _detect_clusters(self, features: np.ndarray) -> np.ndarray:
        """Detect clusters in feature space using DBSCAN."""
        try:
            clustering = DBSCAN(
                eps=0.3,
                min_samples=self.min_cluster_size,
                metric='euclidean'
            ).fit(features)
            
            return clustering.labels_
            
        except Exception as e:
            logger.error(f"Error detecting clusters: {e}")
            return np.array([])
    
    def _analyze_cluster(self, cluster_data: pd.DataFrame, 
                        cluster_features: np.ndarray,
                        timeframe: str) -> Optional[OrderFlowPattern]:
        """Analyze a cluster to identify the pattern type."""
        try:
            # Prepare features for neural network
            if len(cluster_features) < self.time_window:
                return None
            
            # Use sliding window to get features
            feature_windows = []
            for i in range(len(cluster_features) - self.time_window + 1):
                window = cluster_features[i:i + self.time_window]
                feature_windows.append(window)
            
            feature_windows = np.array(feature_windows)
            
            # Get pattern predictions
            if self.pattern_model is not None:
                predictions = self.pattern_model.predict(feature_windows)
                pattern_probs = np.mean(predictions, axis=0)
                pattern_type = ['accumulation', 'distribution', 
                              'absorption', 'neutral'][np.argmax(pattern_probs)]
                confidence = float(np.max(pattern_probs))
            else:
                # Fallback to simple heuristics
                pattern_type = self._classify_pattern_heuristic(cluster_data)
                confidence = 0.6
            
            # Create pattern object
            pattern = OrderFlowPattern(
                pattern_type=pattern_type,
                start_time=cluster_data.index[0],
                end_time=cluster_data.index[-1],
                price_range=(cluster_data['low'].min(), cluster_data['high'].max()),
                volume=cluster_data['volume'].sum(),
                confidence=confidence,
                features={
                    'avg_volume': float(cluster_data['volume'].mean()),
                    'price_range': float(cluster_data['high'].max() - cluster_data['low'].min()),
                    'duration': len(cluster_data)
                },
                metadata={
                    'timeframe': timeframe,
                    'num_trades': len(cluster_data)
                }
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error analyzing cluster: {e}")
            return None
    
    def _classify_pattern_heuristic(self, data: pd.DataFrame) -> str:
        """Simple heuristic pattern classification."""
        try:
            # Calculate basic metrics
            price_trend = data['close'].iloc[-1] - data['close'].iloc[0]
            volume_trend = data['volume'].iloc[-1] - data['volume'].iloc[0]
            avg_volume = data['volume'].mean()
            
            if price_trend > 0 and volume_trend > 0 and data['volume'].max() > avg_volume * 1.5:
                return 'accumulation'
            elif price_trend < 0 and volume_trend > 0 and data['volume'].max() > avg_volume * 1.5:
                return 'distribution'
            elif abs(price_trend) < data['close'].std() and volume_trend > 0:
                return 'absorption'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Error in heuristic classification: {e}")
            return 'neutral'
    
    def get_active_patterns(self, current_time: datetime, 
                          max_age_minutes: int = 60) -> List[OrderFlowPattern]:
        """Get currently active patterns."""
        active_patterns = []
        
        for pattern in self.detected_patterns:
            age_minutes = (current_time - pattern.end_time).total_seconds() / 60
            if age_minutes <= max_age_minutes:
                active_patterns.append(pattern)
        
        return active_patterns
