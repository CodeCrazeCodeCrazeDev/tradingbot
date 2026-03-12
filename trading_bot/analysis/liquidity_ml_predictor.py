import logging
logger = logging.getLogger(__name__)
"""
Machine Learning-Based Liquidity Prediction System

This module provides ML models for predicting liquidity events, order block reactions,
and fair value gap behavior using advanced feature engineering and ensemble methods.
"""

import pickle
import time
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import threading

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, mean_squared_error, r2_score
from loguru import logger

from .liquidity import LiquidityPool, OrderBlock, FairValueGap, LiquidityType, OrderBlockType
from .order_block_tracker import MitigationEvent, MitigationType, ReactionType
from .market_structure import TimeFrame
import numpy
import pandas


class PredictionType(Enum):
    """Types of liquidity predictions."""
    POOL_FORMATION = "pool_formation"
    ORDER_BLOCK_REACTION = "order_block_reaction"
    FVG_FILLING = "fvg_filling"
    MITIGATION_SUCCESS = "mitigation_success"
    LIQUIDITY_GRAB = "liquidity_grab"


@dataclass
class PredictionResult:
    """Result of a liquidity prediction."""
    prediction_type: PredictionType
    probability: float
    confidence: float
    features_used: List[str]
    model_version: str
    timestamp: float
    metadata: Dict[str, Any]


@dataclass
class TrainingData:
    """Training data for ML models."""
    features: np.ndarray
    labels: np.ndarray
    feature_names: List[str]
    sample_weights: Optional[np.ndarray] = None


class LiquidityFeatureEngineer:
    """Feature engineering for liquidity prediction models."""
    
    def __init__(self):
        """Initialize the feature engineer."""
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        
    def extract_pool_features(self, pool: LiquidityPool, market_data: pd.DataFrame,
                            context_data: Dict[str, Any]) -> np.ndarray:
        """Extract features for liquidity pool analysis."""
        features = []
        
        # Pool characteristics
        features.extend([
            pool.strength,
            len(pool.swing_idxs),
            pool.volume or 0.0,
            float(pool.kind == LiquidityType.BUY)
        ])
        
        # Market context features
        if not market_data.empty:
            recent_data = market_data.tail(20)
            
            # Price action features
            features.extend([
                recent_data['close'].std(),  # Volatility
                recent_data['volume'].mean(),  # Average volume
                (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0],  # Price change
                recent_data['high'].max() - recent_data['low'].min(),  # Range
                len(recent_data[recent_data['close'] > recent_data['open']]) / len(recent_data)  # Bullish ratio
            ])
            
            # Technical indicators
            rsi = self._calculate_rsi(recent_data['close'])
            features.append(rsi)
            
            # Distance to pool
            current_price = recent_data['close'].iloc[-1]
            distance_to_pool = abs(current_price - pool.price) / current_price
            features.append(distance_to_pool)
        else:
            features.extend([0.0] * 7)  # Placeholder values
        
        # Time-based features
        if pool.created_at:
            age_hours = (time.time() - pool.created_at.timestamp()) / 3600
            features.append(age_hours)
        else:
            features.append(0.0)
        
        # Context features
        features.extend([
            context_data.get('nearby_pools_count', 0),
            context_data.get('market_regime', 0),  # 0=ranging, 1=trending
            context_data.get('session_time', 0)  # 0=asian, 1=london, 2=ny
        ])
        
        return np.array(features)
    
    def extract_order_block_features(self, order_block: OrderBlock, market_data: pd.DataFrame,
                                   mitigation_event: Optional[MitigationEvent] = None) -> np.ndarray:
        """Extract features for order block reaction prediction."""
        features = []
        
        # Order block characteristics
        ob_size = order_block.high - order_block.low
        features.extend([
            order_block.strength,
            ob_size,
            order_block.volume or 0.0,
            float(order_block.type == OrderBlockType.BULLISH),
            float(order_block.mitigated)
        ])
        
        # Market data features
        if not market_data.empty:
            recent_data = market_data.tail(20)
            current_price = recent_data['close'].iloc[-1]
            
            # Position relative to order block
            if order_block.type == OrderBlockType.BULLISH:
                distance_to_ob = (current_price - order_block.high) / ob_size
            else:
                distance_to_ob = (order_block.low - current_price) / ob_size
            
            features.extend([
                distance_to_ob,
                recent_data['volume'].mean(),
                recent_data['close'].std(),
                self._calculate_rsi(recent_data['close'])
            ])
            
            # Momentum features
            momentum_5 = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[-5]) / recent_data['close'].iloc[-5]
            momentum_10 = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[-10]) / recent_data['close'].iloc[-10]
            features.extend([momentum_5, momentum_10])
        else:
            features.extend([0.0] * 6)
        
        # Mitigation event features
        if mitigation_event:
            features.extend([
                mitigation_event.max_penetration,
                mitigation_event.volume_at_mitigation or 0.0,
                mitigation_event.duration_bars,
                float(mitigation_event.mitigation_type == MitigationType.PARTIAL),
                float(mitigation_event.mitigation_type == MitigationType.FULL)
            ])
        else:
            features.extend([0.0] * 5)
        
        # Time features
        if order_block.created_at:
            age_hours = (time.time() - order_block.created_at.timestamp()) / 3600
            features.append(age_hours)
        else:
            features.append(0.0)
        
        return np.array(features)
    
    def extract_fvg_features(self, fvg: FairValueGap, market_data: pd.DataFrame) -> np.ndarray:
        """Extract features for FVG filling prediction."""
        features = []
        
        # FVG characteristics
        features.extend([
            fvg.size,
            fvg.size_pct,
            fvg.strength,
            float(fvg.type.value == 'bullish'),
            float(fvg.filled)
        ])
        
        # Market context
        if not market_data.empty:
            recent_data = market_data.tail(20)
            current_price = recent_data['close'].iloc[-1]
            
            # Distance to FVG
            fvg_center = (fvg.high + fvg.low) / 2
            distance_to_fvg = abs(current_price - fvg_center) / fvg.size
            
            features.extend([
                distance_to_fvg,
                recent_data['volume'].mean(),
                recent_data['close'].std(),
                self._calculate_rsi(recent_data['close'])
            ])
        else:
            features.extend([0.0] * 4)
        
        # Time since creation
        if fvg.created_at:
            age_hours = (time.time() - fvg.created_at.timestamp()) / 3600
            features.append(age_hours)
        else:
            features.append(0.0)
        
        return np.array(features)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0
    
    def normalize_features(self, features: np.ndarray, feature_name: str) -> np.ndarray:
        """Normalize features using StandardScaler."""
        if feature_name not in self.scalers:
            self.scalers[feature_name] = StandardScaler()
            return self.scalers[feature_name].fit_transform(features.reshape(-1, 1)).flatten()
        else:
            return self.scalers[feature_name].transform(features.reshape(-1, 1)).flatten()


class LiquidityMLPredictor:
    """
    Machine learning-based liquidity prediction system.
    
    Provides predictions for:
    - Liquidity pool formation probability
    - Order block reaction success
    - Fair value gap filling likelihood
    - Mitigation event outcomes
    """
    
    def __init__(self, enable_training: bool = True):
        """Initialize the ML predictor."""
        self.enable_training = enable_training
        self.feature_engineer = LiquidityFeatureEngineer()
        
        # ML models
        self.models: Dict[PredictionType, Any] = {}
        self.model_performance: Dict[PredictionType, Dict[str, float]] = {}
        
        # Training data storage
        self.training_data: Dict[PredictionType, List[Tuple[np.ndarray, float]]] = defaultdict(list)
        self.max_training_samples = 10000
        
        # Prediction history
        self.prediction_history: deque = deque(maxlen=1000)
        
        # Threading
        self.training_lock = threading.RLock()
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for different prediction types."""
        # Pool formation classifier
        self.models[PredictionType.POOL_FORMATION] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        # Order block reaction classifier
        self.models[PredictionType.ORDER_BLOCK_REACTION] = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            random_state=42,
            class_weight='balanced'
        )
        
        # FVG filling regressor
        self.models[PredictionType.FVG_FILLING] = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )
        
        # Mitigation success classifier
        self.models[PredictionType.MITIGATION_SUCCESS] = RandomForestClassifier(
            n_estimators=120,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
    
    def predict_pool_formation(self, market_data: pd.DataFrame, 
                             context_data: Dict[str, Any]) -> PredictionResult:
        """Predict probability of liquidity pool formation."""
        try:
            # Extract features for current market state
            features = self._extract_market_state_features(market_data, context_data)
            
            # Get model prediction
            model = self.models[PredictionType.POOL_FORMATION]
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba([features])[0]
                probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            else:
                probability = 0.5  # Default if model not trained
            
            # Calculate confidence based on model certainty
            confidence = abs(probability - 0.5) * 2
            
            result = PredictionResult(
                prediction_type=PredictionType.POOL_FORMATION,
                probability=probability,
                confidence=confidence,
                features_used=['market_volatility', 'volume_profile', 'price_momentum'],
                model_version='v1.0',
                timestamp=time.time(),
                metadata={'feature_count': len(features)}
            )
            
            self.prediction_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in pool formation prediction: {e}")
            return self._create_default_prediction(PredictionType.POOL_FORMATION)
    
    def predict_order_block_reaction(self, order_block: OrderBlock, 
                                   market_data: pd.DataFrame,
                                   mitigation_event: Optional[MitigationEvent] = None) -> PredictionResult:
        """Predict order block reaction success probability."""
        try:
            features = self.feature_engineer.extract_order_block_features(
                order_block, market_data, mitigation_event
            )
            
            model = self.models[PredictionType.ORDER_BLOCK_REACTION]
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba([features])[0]
                probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            else:
                # Use heuristic if model not trained
                probability = min(0.8, order_block.strength / 2.0)
            
            confidence = abs(probability - 0.5) * 2
            
            result = PredictionResult(
                prediction_type=PredictionType.ORDER_BLOCK_REACTION,
                probability=probability,
                confidence=confidence,
                features_used=['ob_strength', 'market_position', 'volume', 'momentum'],
                model_version='v1.0',
                timestamp=time.time(),
                metadata={
                    'order_block_type': order_block.type.value,
                    'order_block_strength': order_block.strength
                }
            )
            
            self.prediction_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in order block reaction prediction: {e}")
            return self._create_default_prediction(PredictionType.ORDER_BLOCK_REACTION)
    
    def predict_fvg_filling(self, fvg: FairValueGap, market_data: pd.DataFrame) -> PredictionResult:
        """Predict FVG filling probability and timeframe."""
        try:
            features = self.feature_engineer.extract_fvg_features(fvg, market_data)
            
            model = self.models[PredictionType.FVG_FILLING]
            if hasattr(model, 'predict'):
                probability = model.predict([features])[0]
                probability = max(0.0, min(1.0, probability))  # Clamp to [0,1]
            else:
                # Use heuristic based on FVG characteristics
                probability = min(0.9, fvg.strength * 0.6)
            
            confidence = 0.7  # Fixed confidence for regression models
            
            result = PredictionResult(
                prediction_type=PredictionType.FVG_FILLING,
                probability=probability,
                confidence=confidence,
                features_used=['fvg_size', 'market_distance', 'age', 'momentum'],
                model_version='v1.0',
                timestamp=time.time(),
                metadata={
                    'fvg_type': fvg.type.value,
                    'fvg_size_pct': fvg.size_pct
                }
            )
            
            self.prediction_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in FVG filling prediction: {e}")
            return self._create_default_prediction(PredictionType.FVG_FILLING)
    
    def predict_mitigation_success(self, mitigation_event: MitigationEvent,
                                 market_data: pd.DataFrame) -> PredictionResult:
        """Predict mitigation event success probability."""
        try:
            # Extract features from mitigation event
            features = np.array([
                mitigation_event.max_penetration,
                mitigation_event.volume_at_mitigation or 0.0,
                mitigation_event.duration_bars,
                mitigation_event.order_block.strength,
                float(mitigation_event.mitigation_type == MitigationType.PARTIAL),
                float(mitigation_event.reaction_type == ReactionType.BOUNCE)
            ])
            
            model = self.models[PredictionType.MITIGATION_SUCCESS]
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba([features])[0]
                probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            else:
                # Heuristic based on penetration and strength
                probability = (1.0 - mitigation_event.max_penetration) * mitigation_event.order_block.strength / 2.0
                probability = max(0.1, min(0.9, probability))
            
            confidence = abs(probability - 0.5) * 2
            
            result = PredictionResult(
                prediction_type=PredictionType.MITIGATION_SUCCESS,
                probability=probability,
                confidence=confidence,
                features_used=['penetration', 'volume', 'duration', 'ob_strength'],
                model_version='v1.0',
                timestamp=time.time(),
                metadata={
                    'mitigation_type': mitigation_event.mitigation_type.value,
                    'reaction_type': mitigation_event.reaction_type.value
                }
            )
            
            self.prediction_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in mitigation success prediction: {e}")
            return self._create_default_prediction(PredictionType.MITIGATION_SUCCESS)
    
    def add_training_sample(self, prediction_type: PredictionType, 
                          features: np.ndarray, label: float, weight: float = 1.0):
        """Add a training sample for model improvement."""
        if not self.enable_training:
            return
        
        with self.training_lock:
            self.training_data[prediction_type].append((features, label, weight))
            
            # Limit training data size
            if len(self.training_data[prediction_type]) > self.max_training_samples:
                self.training_data[prediction_type] = self.training_data[prediction_type][-self.max_training_samples:]
    
    def retrain_models(self, min_samples: int = 100):
        """Retrain models with accumulated training data."""
        if not self.enable_training:
            logger.warning("Training is disabled")
            return
        
        with self.training_lock:
            for prediction_type, samples in self.training_data.items():
                if len(samples) < min_samples:
                    logger.info(f"Insufficient samples for {prediction_type.value}: {len(samples)}")
                    continue
                try:
                
                    # Prepare training data
                    features = np.array([sample[0] for sample in samples])
                    labels = np.array([sample[1] for sample in samples])
                    weights = np.array([sample[2] if len(sample) > 2 else 1.0 for sample in samples])
                    
                    # Split data
                    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
                        features, labels, weights, test_size=0.2, random_state=42
                    )
                    
                    # Train model
                    model = self.models[prediction_type]
                    
                    if hasattr(model, 'fit'):
                        if 'sample_weight' in model.fit.__code__.co_varnames:
                            model.fit(X_train, y_train, sample_weight=w_train)
                        else:
                            model.fit(X_train, y_train)
                    
                    # Evaluate model
                    if hasattr(model, 'score'):
                        train_score = model.score(X_train, y_train)
                        test_score = model.score(X_test, y_test)
                        
                        self.model_performance[prediction_type] = {
                            'train_score': train_score,
                            'test_score': test_score,
                            'samples_used': len(samples),
                            'last_trained': time.time()
                        }
                        
                        logger.info(f"Retrained {prediction_type.value} model: "
                                  f"train={train_score:.3f}, test={test_score:.3f}")
                    
                except Exception as e:
                    logger.error(f"Error retraining {prediction_type.value} model: {e}")
    
    def _extract_market_state_features(self, market_data: pd.DataFrame, 
                                     context_data: Dict[str, Any]) -> np.ndarray:
        """Extract features representing current market state."""
        features = []
        
        if not market_data.empty:
            recent_data = market_data.tail(20)
            
            # Volatility features
            features.extend([
                recent_data['close'].std(),
                recent_data['high'].max() - recent_data['low'].min(),
                recent_data['volume'].std()
            ])
            
            # Momentum features
            momentum_5 = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[-5]) / recent_data['close'].iloc[-5]
            momentum_10 = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[-10]) / recent_data['close'].iloc[-10]
            features.extend([momentum_5, momentum_10])
            
            # Technical indicators
            rsi = self.feature_engineer._calculate_rsi(recent_data['close'])
            features.append(rsi)
        else:
            features.extend([0.0] * 6)
        
        # Context features
        features.extend([
            context_data.get('market_regime', 0),
            context_data.get('session_time', 0),
            context_data.get('volatility_regime', 0)
        ])
        
        return np.array(features)
    
    def _create_default_prediction(self, prediction_type: PredictionType) -> PredictionResult:
        """Create a default prediction when errors occur."""
        return PredictionResult(
            prediction_type=prediction_type,
            probability=0.5,
            confidence=0.1,
            features_used=[],
            model_version='default',
            timestamp=time.time(),
            metadata={'error': True}
        )
    
    def get_model_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all models."""
        return {pt.value: perf for pt, perf in self.model_performance.items()}
    
    def save_models(self, filepath: str):
        """Save trained models to file."""
        try:
            model_data = {
                'models': self.models,
                'performance': self.model_performance,
                'scalers': self.feature_engineer.scalers,
                'encoders': self.feature_engineer.encoders
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Models saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self, filepath: str):
        """Load trained models from file."""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data.get('models', {})
            self.model_performance = model_data.get('performance', {})
            self.feature_engineer.scalers = model_data.get('scalers', {})
            self.feature_engineer.encoders = model_data.get('encoders', {})
            
            logger.info(f"Models loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")


# Factory function
def create_ml_predictor(enable_training: bool = True) -> LiquidityMLPredictor:
    """Create an ML predictor with default configuration."""
    return LiquidityMLPredictor(enable_training=enable_training)


if __name__ == "__main__":
    # Example usage
    predictor = create_ml_predictor()
    
    # Create sample market data
    dates = pd.date_range('2023-01-01', periods=100, freq='15min')
    market_data = pd.DataFrame({
        'open': np.random.uniform(1.1000, 1.1100, 100),
        'high': np.random.uniform(1.1000, 1.1100, 100),
        'low': np.random.uniform(1.1000, 1.1100, 100),
        'close': np.random.uniform(1.1000, 1.1100, 100),
        'volume': np.random.uniform(100, 1000, 100)
    }, index=dates)
    
    # Test predictions
    context_data = {'market_regime': 1, 'session_time': 1, 'volatility_regime': 0}
    
    pool_pred = predictor.predict_pool_formation(market_data, context_data)
    logger.info(f"Pool formation prediction: {pool_pred.probability:.3f} (confidence: {pool_pred.confidence:.3f})")
    
    # Get model performance
    performance = predictor.get_model_performance()
    logger.info(f"Model performance: {performance}")
