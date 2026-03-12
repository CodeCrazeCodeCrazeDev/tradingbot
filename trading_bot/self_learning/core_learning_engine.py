"""
Core Self-Learning Engine for Market Analysis and Profit Optimization

This module implements advanced online learning, adaptive modeling, and continuous
improvement specifically optimized for financial market prediction and trading.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import json

logger = logging.getLogger(__name__)


class LearningMode(Enum):
    """Learning modes for different market conditions"""
    AGGRESSIVE = "aggressive"  # Fast adaptation, high learning rate
    BALANCED = "balanced"      # Moderate adaptation
    CONSERVATIVE = "conservative"  # Slow, stable learning
    EXPLORATION = "exploration"  # Focus on discovering new patterns
    EXPLOITATION = "exploitation"  # Focus on proven strategies


class ModelType(Enum):
    """Types of predictive models"""
    PRICE_DIRECTION = "price_direction"
    VOLATILITY = "volatility"
    REGIME = "regime"
    PROFIT_PROBABILITY = "profit_probability"
    OPTIMAL_POSITION = "optimal_position"
    RISK_ADJUSTED_RETURN = "risk_adjusted_return"


@dataclass
class LearningMetrics:
    """Metrics tracking learning performance"""
    total_samples: int = 0
    correct_predictions: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    avg_prediction_error: float = 0.0
    model_confidence: float = 0.0
    learning_rate: float = 0.01
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def accuracy(self) -> float:
        if self.total_samples == 0:
            return 0.0
        return self.correct_predictions / self.total_samples
    
    @property
    def profit_factor(self) -> float:
        if self.total_loss == 0:
            return float('inf') if self.total_profit > 0 else 0.0
        return self.total_profit / abs(self.total_loss)


@dataclass
class MarketPattern:
    """Discovered market pattern"""
    pattern_id: str
    pattern_type: str
    features: Dict[str, float]
    success_rate: float
    avg_profit: float
    sample_count: int
    confidence: float
    discovered_at: datetime
    last_seen: datetime


class OnlinePredictor:
    """Online learning predictor with incremental updates"""
    
    def __init__(self, model_type: ModelType, learning_rate: float = 0.01):
        self.model_type = model_type
        self.learning_rate = learning_rate
        self.model = SGDRegressor(
            learning_rate='adaptive',
            eta0=learning_rate,
            max_iter=1,
            warm_start=True,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.sample_count = 0
        self.prediction_history = deque(maxlen=1000)
        self.error_history = deque(maxlen=1000)
        
    def partial_fit(self, X: np.ndarray, y: np.ndarray):
        """Incrementally update model with new data"""
        if not self.is_fitted:
            self.scaler.fit(X)
            self.is_fitted = True
        
        X_scaled = self.scaler.transform(X)
        self.model.partial_fit(X_scaled, y)
        self.sample_count += len(y)
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_fitted:
            return np.zeros(len(X))
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        self.prediction_history.extend(predictions)
        return predictions
    
    def update_with_feedback(self, X: np.ndarray, y_true: np.ndarray, y_pred: np.ndarray):
        """Update model based on prediction feedback"""
        error = np.mean(np.abs(y_true - y_pred))
        self.error_history.append(error)
        
        # Adaptive learning rate based on recent errors
        if len(self.error_history) > 10:
            recent_errors = list(self.error_history)[-10:]
            if np.mean(recent_errors) > np.mean(list(self.error_history)):
                self.learning_rate *= 1.1  # Increase learning rate if errors increasing
            else:
                self.learning_rate *= 0.95  # Decrease if improving
        
        self.partial_fit(X, y_true)
    
    def get_confidence(self) -> float:
        """Calculate model confidence based on recent performance"""
        if len(self.error_history) < 10:
            return 0.5
        
        recent_errors = list(self.error_history)[-50:]
        avg_error = np.mean(recent_errors)
        error_std = np.std(recent_errors)
        
        # Lower error and lower variance = higher confidence
        confidence = 1.0 / (1.0 + avg_error + error_std)
        return min(max(confidence, 0.0), 1.0)


class EnsembleLearner:
    """Ensemble of multiple learning models for robust predictions"""
    
    def __init__(self, n_models: int = 5):
        self.n_models = n_models
        self.models: List[OnlinePredictor] = []
        self.model_weights: List[float] = []
        self.model_performances: List[float] = []
        
    def initialize(self, model_type: ModelType):
        """Initialize ensemble models"""
        learning_rates = [0.001, 0.005, 0.01, 0.05, 0.1]
        for lr in learning_rates[:self.n_models]:
            model = OnlinePredictor(model_type, learning_rate=lr)
            self.models.append(model)
            self.model_weights.append(1.0 / self.n_models)
            self.model_performances.append(0.5)
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, float]:
        """Make ensemble prediction with confidence"""
        if not self.models:
            return np.zeros(len(X)), 0.0
        
        predictions = []
        confidences = []
        
        for model, weight in zip(self.models, self.model_weights):
            pred = model.predict(X)
            conf = model.get_confidence()
            predictions.append(pred * weight * conf)
            confidences.append(conf * weight)
        
        ensemble_pred = np.sum(predictions, axis=0)
        ensemble_conf = np.mean(confidences)
        
        return ensemble_pred, ensemble_conf
    
    def update(self, X: np.ndarray, y_true: np.ndarray):
        """Update all models and reweight based on performance"""
        for i, model in enumerate(self.models):
            y_pred = model.predict(X)
            error = np.mean(np.abs(y_true - y_pred))
            
            # Update model
            model.update_with_feedback(X, y_true, y_pred)
            
            # Update performance tracking
            self.model_performances[i] = 0.9 * self.model_performances[i] + 0.1 * (1.0 / (1.0 + error))
        
        # Reweight models based on performance
        total_perf = sum(self.model_performances)
        if total_perf > 0:
            self.model_weights = [p / total_perf for p in self.model_performances]


class PatternDiscovery:
    """Discovers and tracks profitable market patterns"""
    
    def __init__(self, min_samples: int = 20, min_success_rate: float = 0.6):
        self.min_samples = min_samples
        self.min_success_rate = min_success_rate
        self.patterns: Dict[str, MarketPattern] = {}
        self.pattern_buffer: Dict[str, List[Dict]] = {}
        
    def observe_pattern(self, pattern_type: str, features: Dict[str, float], 
                       outcome: float, profit: float):
        """Observe a pattern occurrence and outcome"""
        pattern_id = self._generate_pattern_id(pattern_type, features)
        
        if pattern_id not in self.pattern_buffer:
            self.pattern_buffer[pattern_id] = []
        
        self.pattern_buffer[pattern_id].append({
            'features': features,
            'outcome': outcome,
            'profit': profit,
            'timestamp': datetime.utcnow()
        })
        
        # Check if pattern is significant
        if len(self.pattern_buffer[pattern_id]) >= self.min_samples:
            self._evaluate_pattern(pattern_id, pattern_type)
    
    def _generate_pattern_id(self, pattern_type: str, features: Dict[str, float]) -> str:
        """Generate unique pattern ID from features"""
        # Discretize features for pattern matching
        discretized = []
        for key, value in sorted(features.items()):
            bucket = int(value * 10) / 10  # Round to 1 decimal
            discretized.append(f"{key}:{bucket}")
        return f"{pattern_type}:{'_'.join(discretized)}"
    
    def _evaluate_pattern(self, pattern_id: str, pattern_type: str):
        """Evaluate if pattern is profitable and significant"""
        observations = self.pattern_buffer[pattern_id]
        
        successes = sum(1 for obs in observations if obs['outcome'] > 0)
        success_rate = successes / len(observations)
        avg_profit = np.mean([obs['profit'] for obs in observations])
        
        if success_rate >= self.min_success_rate and avg_profit > 0:
            # Create or update pattern
            if pattern_id in self.patterns:
                pattern = self.patterns[pattern_id]
                pattern.success_rate = success_rate
                pattern.avg_profit = avg_profit
                pattern.sample_count = len(observations)
                pattern.last_seen = datetime.utcnow()
            else:
                self.patterns[pattern_id] = MarketPattern(
                    pattern_id=pattern_id,
                    pattern_type=pattern_type,
                    features=observations[0]['features'],
                    success_rate=success_rate,
                    avg_profit=avg_profit,
                    sample_count=len(observations),
                    confidence=min(success_rate * (len(observations) / 100), 1.0),
                    discovered_at=datetime.utcnow(),
                    last_seen=datetime.utcnow()
                )
                logger.info(f"Discovered new pattern: {pattern_id} with {success_rate:.2%} success rate")
    
    def get_matching_patterns(self, features: Dict[str, float], 
                            min_confidence: float = 0.7) -> List[MarketPattern]:
        """Get patterns matching current features"""
        matching = []
        for pattern in self.patterns.values():
            similarity = self._calculate_similarity(features, pattern.features)
            if similarity > 0.8 and pattern.confidence >= min_confidence:
                matching.append(pattern)
        
        return sorted(matching, key=lambda p: p.confidence * p.success_rate, reverse=True)
    
    def _calculate_similarity(self, features1: Dict[str, float], 
                            features2: Dict[str, float]) -> float:
        """Calculate similarity between feature sets"""
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0
        
        differences = [abs(features1[k] - features2[k]) for k in common_keys]
        avg_diff = np.mean(differences)
        return 1.0 / (1.0 + avg_diff)


class CoreLearningEngine:
    """Main self-learning engine for market analysis and profit optimization"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.learning_mode = LearningMode.BALANCED
        self.metrics: Dict[ModelType, LearningMetrics] = {}
        self.ensembles: Dict[ModelType, EnsembleLearner] = {}
        self.pattern_discovery = PatternDiscovery()
        self.experience_buffer = deque(maxlen=10000)
        self.profit_history = deque(maxlen=1000)
        self.learning_callbacks: List[Callable] = []
        
        # Initialize models for different prediction tasks
        for model_type in ModelType:
            self.metrics[model_type] = LearningMetrics()
            ensemble = EnsembleLearner(n_models=5)
            ensemble.initialize(model_type)
            self.ensembles[model_type] = ensemble
    
    async def learn_from_market(self, market_data: pd.DataFrame, 
                               outcomes: Optional[Dict[str, float]] = None):
        """Learn from market data and trading outcomes"""
        try:
            # Extract features
            features = self._extract_features(market_data)
            
            # If we have outcomes, update models
            if outcomes:
                await self._update_models(features, outcomes)
            
            # Discover patterns
            if outcomes and 'profit' in outcomes:
                pattern_features = self._extract_pattern_features(market_data)
                self.pattern_discovery.observe_pattern(
                    pattern_type='market_state',
                    features=pattern_features,
                    outcome=outcomes.get('success', 0),
                    profit=outcomes['profit']
                )
            
            # Store experience
            self.experience_buffer.append({
                'timestamp': datetime.utcnow(),
                'features': features,
                'outcomes': outcomes,
                'market_data': market_data.tail(10).to_dict()
            })
            
            # Adapt learning mode based on performance
            await self._adapt_learning_mode()
            
        except Exception as e:
            logger.error(f"Error in learn_from_market: {e}")
    
    def _extract_features(self, market_data: pd.DataFrame) -> np.ndarray:
        """Extract features from market data"""
        features = []
        
        if 'close' in market_data.columns:
            close = market_data['close'].values
            
            # Price-based features
            returns = np.diff(close) / close[:-1] if len(close) > 1 else [0]
            features.extend([
                close[-1] if len(close) > 0 else 0,
                np.mean(returns) if len(returns) > 0 else 0,
                np.std(returns) if len(returns) > 0 else 0,
                np.max(returns) if len(returns) > 0 else 0,
                np.min(returns) if len(returns) > 0 else 0,
            ])
            
            # Momentum features
            if len(close) >= 10:
                features.extend([
                    (close[-1] - close[-10]) / close[-10],
                    (close[-1] - close[-5]) / close[-5] if len(close) >= 5 else 0,
                ])
            else:
                features.extend([0, 0])
        
        if 'volume' in market_data.columns:
            volume = market_data['volume'].values
            features.extend([
                volume[-1] if len(volume) > 0 else 0,
                np.mean(volume) if len(volume) > 0 else 0,
            ])
        
        return np.array(features).reshape(1, -1)
    
    def _extract_pattern_features(self, market_data: pd.DataFrame) -> Dict[str, float]:
        """Extract pattern-specific features"""
        features = {}
        
        if 'close' in market_data.columns and len(market_data) >= 10:
            close = market_data['close'].values
            returns = np.diff(close) / close[:-1]
            
            features['trend'] = (close[-1] - close[-10]) / close[-10]
            features['volatility'] = np.std(returns)
            features['momentum'] = np.mean(returns[-5:]) if len(returns) >= 5 else 0
            features['volume_trend'] = (market_data['volume'].iloc[-1] / 
                                       market_data['volume'].mean() if 'volume' in market_data.columns else 1.0)
        
        return features
    
    async def _update_models(self, features: np.ndarray, outcomes: Dict[str, float]):
        """Update all models with new outcomes"""
        for model_type, ensemble in self.ensembles.items():
            if model_type.value in outcomes:
                y_true = np.array([outcomes[model_type.value]])
                ensemble.update(features, y_true)
                
                # Update metrics
                metrics = self.metrics[model_type]
                metrics.total_samples += 1
                metrics.last_update = datetime.utcnow()
                
                if 'profit' in outcomes:
                    if outcomes['profit'] > 0:
                        metrics.total_profit += outcomes['profit']
                        metrics.correct_predictions += 1
                    else:
                        metrics.total_loss += abs(outcomes['profit'])
    
    async def _adapt_learning_mode(self):
        """Adapt learning mode based on recent performance"""
        if len(self.profit_history) < 50:
            return
        
        recent_profits = list(self.profit_history)[-50:]
        win_rate = sum(1 for p in recent_profits if p > 0) / len(recent_profits)
        avg_profit = np.mean(recent_profits)
        
        if win_rate > 0.7 and avg_profit > 0:
            self.learning_mode = LearningMode.EXPLOITATION
        elif win_rate < 0.4:
            self.learning_mode = LearningMode.EXPLORATION
        elif avg_profit < 0:
            self.learning_mode = LearningMode.CONSERVATIVE
        else:
            self.learning_mode = LearningMode.BALANCED
    
    async def predict(self, market_data: pd.DataFrame, 
                     model_type: ModelType) -> Tuple[float, float]:
        """Make prediction with confidence"""
        features = self._extract_features(market_data)
        ensemble = self.ensembles[model_type]
        prediction, confidence = ensemble.predict(features)
        
        # Adjust confidence based on learning mode
        if self.learning_mode == LearningMode.CONSERVATIVE:
            confidence *= 0.8
        elif self.learning_mode == LearningMode.AGGRESSIVE:
            confidence *= 1.2
        
        return float(prediction[0]), min(confidence, 1.0)
    
    async def get_pattern_insights(self, market_data: pd.DataFrame) -> List[MarketPattern]:
        """Get matching patterns for current market state"""
        features = self._extract_pattern_features(market_data)
        return self.pattern_discovery.get_matching_patterns(features)
    
    def get_learning_status(self) -> Dict[str, Any]:
        """Get comprehensive learning status"""
        return {
            'learning_mode': self.learning_mode.value,
            'total_experiences': len(self.experience_buffer),
            'discovered_patterns': len(self.pattern_discovery.patterns),
            'model_metrics': {
                model_type.value: {
                    'accuracy': metrics.accuracy,
                    'profit_factor': metrics.profit_factor,
                    'total_samples': metrics.total_samples,
                    'confidence': metrics.model_confidence
                }
                for model_type, metrics in self.metrics.items()
            },
            'recent_performance': {
                'win_rate': sum(1 for p in self.profit_history if p > 0) / len(self.profit_history) 
                           if self.profit_history else 0,
                'avg_profit': np.mean(list(self.profit_history)) if self.profit_history else 0
            }
        }
    
    def register_callback(self, callback: Callable):
        """Register callback for learning events"""
        self.learning_callbacks.append(callback)
    
    async def save_state(self, filepath: str):
        """Save learning state"""
        state = {
            'learning_mode': self.learning_mode.value,
            'metrics': {k.value: v.__dict__ for k, v in self.metrics.items()},
            'patterns': {k: v.__dict__ for k, v in self.pattern_discovery.patterns.items()},
            'experience_count': len(self.experience_buffer),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"Learning state saved to {filepath}")


async def create_learning_engine(config: Optional[Dict] = None) -> CoreLearningEngine:
    """Factory function to create learning engine"""
    engine = CoreLearningEngine(config)
    logger.info("Core learning engine initialized")
    return engine
