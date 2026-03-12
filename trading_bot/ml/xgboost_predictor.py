"""
XGBOOST PREDICTOR - PHASE 4 ML ENHANCEMENT #1
============================================================

Implements XGBoost-based price movement prediction.

Features:
- Feature engineering
- Model training
- Price movement prediction
- Confidence scoring
- Model persistence

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available - using fallback predictions")


@dataclass
class PredictionResult:
    """XGBoost prediction result."""
    symbol: str
    prediction: float  # -1 (down), 0 (neutral), 1 (up)
    confidence: float  # 0-1
    probability_up: float
    probability_down: float
    probability_neutral: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class XGBoostPredictor:
    """XGBoost-based price movement predictor."""
    
    def __init__(self, lookback_period: int = 50):
        """
        Initialize XGBoost predictor.
        
        Args:
            lookback_period: Number of candles for features
        """
        self.lookback_period = lookback_period
        self.model = None
        self.feature_names = []
        self.is_trained = False
        
        # Training data
        self.X_train = []
        self.y_train = []
        
        logger.info("XGBoost predictor initialized")
    
    def engineer_features(self, closes: List[float], highs: List[float],
                         lows: List[float], volumes: List[float]) -> Optional[np.ndarray]:
        """
        Engineer features for prediction.
        
        Returns:
            Feature array or None if insufficient data
        """
        if len(closes) < self.lookback_period + 1:
            return None
        
        features = []
        
        # Price features
        recent_closes = closes[-self.lookback_period:]
        features.append(np.mean(recent_closes))  # Mean price
        features.append(np.std(recent_closes))   # Volatility
        features.append(recent_closes[-1] - recent_closes[0])  # Price change
        
        # Momentum features
        roc = (recent_closes[-1] - recent_closes[-10]) / recent_closes[-10] if len(recent_closes) >= 10 else 0
        features.append(roc)  # Rate of change
        
        # Trend features
        trend = 1 if recent_closes[-1] > recent_closes[-5] else -1
        features.append(trend)  # Trend direction
        
        # Volume features
        recent_volumes = volumes[-self.lookback_period:]
        features.append(np.mean(recent_volumes))  # Mean volume
        
        # Range features
        recent_highs = highs[-self.lookback_period:]
        recent_lows = lows[-self.lookback_period:]
        range_width = np.mean(recent_highs) - np.mean(recent_lows)
        features.append(range_width)  # Average range
        
        # RSI-like feature
        gains = sum(1 for i in range(1, len(recent_closes)) if recent_closes[i] > recent_closes[i-1])
        losses = len(recent_closes) - 1 - gains
        rsi_like = gains / (gains + losses) if (gains + losses) > 0 else 0.5
        features.append(rsi_like)
        
        self.feature_names = [
            'mean_price', 'volatility', 'price_change', 'roc',
            'trend', 'mean_volume', 'range_width', 'rsi_like'
        ]
        
        return np.array(features).reshape(1, -1)
    
    def prepare_training_data(self, closes: List[float], highs: List[float],
                             lows: List[float], volumes: List[float]):
        """Prepare training data from historical prices."""
        self.X_train = []
        self.y_train = []
        
        for i in range(len(closes) - self.lookback_period - 1):
            window_closes = closes[i:i+self.lookback_period]
            window_highs = highs[i:i+self.lookback_period]
            window_lows = lows[i:i+self.lookback_period]
            window_volumes = volumes[i:i+self.lookback_period]
            
            features = self.engineer_features(
                window_closes, window_highs, window_lows, window_volumes
            )
            
            if features is not None:
                self.X_train.append(features[0])
                
                # Label: next candle direction
                next_close = closes[i + self.lookback_period + 1]
                current_close = closes[i + self.lookback_period]
                
                if next_close > current_close * 1.001:
                    label = 1  # Up
                elif next_close < current_close * 0.999:
                    label = -1  # Down
                else:
                    label = 0  # Neutral
                
                self.y_train.append(label)
        
        logger.info(f"Training data prepared: {len(self.X_train)} samples")
    
    def train(self):
        """Train XGBoost model."""
        if not XGBOOST_AVAILABLE:
            logger.warning("XGBoost not available - skipping training")
            return False
        
        if len(self.X_train) < 10:
            logger.warning("Insufficient training data")
            return False
        try:
        
            X = np.array(self.X_train)
            y = np.array(self.y_train)
            
            # Create XGBoost classifier
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
                verbosity=0
            )
            
            # Train model
            self.model.fit(X, y)
            self.is_trained = True
            
            logger.info("XGBoost model trained successfully")
            return True
        
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def predict(self, closes: List[float], highs: List[float],
               lows: List[float], volumes: List[float],
               symbol: str = "UNKNOWN") -> Optional[PredictionResult]:
        """
        Predict next candle direction.
        
        Returns:
            PredictionResult or None
        """
        features = self.engineer_features(closes, highs, lows, volumes)
        
        if features is None:
            return None
        
        if not self.is_trained or self.model is None:
            # Fallback: simple trend prediction
            return self._fallback_predict(closes, symbol)
        try:
        
            # Get prediction
            prediction = self.model.predict(features)[0]
            
            # Get prediction probabilities
            probabilities = self.model.predict_proba(features)[0]
            
            # Map to probabilities
            prob_down = probabilities[0] if len(probabilities) > 0 else 0
            prob_neutral = probabilities[1] if len(probabilities) > 1 else 0
            prob_up = probabilities[2] if len(probabilities) > 2 else 0
            
            # Calculate confidence
            confidence = max(prob_up, prob_neutral, prob_down)
            
            return PredictionResult(
                symbol=symbol,
                prediction=prediction,
                confidence=confidence,
                probability_up=prob_up,
                probability_down=prob_down,
                probability_neutral=prob_neutral
            )
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return self._fallback_predict(closes, symbol)
    
    def _fallback_predict(self, closes: List[float], symbol: str) -> PredictionResult:
        """Fallback prediction using simple trend."""
        if len(closes) < 2:
            return PredictionResult(
                symbol=symbol,
                prediction=0,
                confidence=0.5,
                probability_up=0.33,
                probability_down=0.33,
                probability_neutral=0.34
            )
        
        # Simple trend
        trend = 1 if closes[-1] > closes[-5] else -1 if closes[-1] < closes[-5] else 0
        confidence = 0.55
        
        return PredictionResult(
            symbol=symbol,
            prediction=trend,
            confidence=confidence,
            probability_up=0.4 if trend == 1 else 0.3,
            probability_down=0.3 if trend == -1 else 0.4,
            probability_neutral=0.3
        )
    
    def get_prediction_summary(self, result: PredictionResult) -> str:
        """Get prediction summary."""
        direction_map = {1: "UP ↑", -1: "DOWN ↓", 0: "NEUTRAL →"}
        
        summary = f"XGBOOST PREDICTION - {result.symbol}\n"
        summary += "=" * 50 + "\n"
        summary += f"Prediction: {direction_map[result.prediction]}\n"
        summary += f"Confidence: {result.confidence:.1%}\n"
        summary += f"Probability UP: {result.probability_up:.1%}\n"
        summary += f"Probability DOWN: {result.probability_down:.1%}\n"
        summary += f"Probability NEUTRAL: {result.probability_neutral:.1%}\n"
        summary += "=" * 50 + "\n"
        
        return summary
    
    def reset(self):
        """Reset predictor."""
        self.model = None
        self.X_train = []
        self.y_train = []
        self.is_trained = False
        logger.info("XGBoost predictor reset")
