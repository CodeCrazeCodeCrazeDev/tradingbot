import logging
logger = logging.getLogger(__name__)
"""Ensemble Learning System for Strategy Combination.

Advanced ensemble methods to combine multiple trading strategies adaptively:
- Weighted voting ensembles
- Stacking models
- Bayesian model averaging
- Dynamic strategy selection
- Performance-based weighting
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
from pathlib import Path
from loguru import logger
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
import asyncio
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        """
        decorator function.

    Args:
        func: Description

    Returns:
        Result of operation
        """
        async def wrapper(*args, **kwargs):
            """
            wrapper function.

    Auto-documented by QwenCodeMender.
            """
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator




class EnsembleMethod(Enum):
    """Ensemble combination methods."""
    WEIGHTED_VOTING = "weighted_voting"
    STACKING = "stacking"
    BAYESIAN_AVERAGING = "bayesian_averaging"
    DYNAMIC_SELECTION = "dynamic_selection"
    PERFORMANCE_WEIGHTED = "performance_weighted"


class StrategyType(Enum):
    """Individual strategy types."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"
    SENTIMENT_BASED = "sentiment_based"
    PATTERN_RECOGNITION = "pattern_recognition"
    MICROSTRUCTURE = "microstructure"
    REGIME_ADAPTIVE = "regime_adaptive"


@dataclass
class StrategyPrediction:
    """Individual strategy prediction."""
    strategy_type: StrategyType
    signal: str  # 'buy', 'sell', 'hold'
    confidence: float
    expected_return: float
    risk_score: float
    reasoning: str
    timestamp: datetime


@dataclass
class EnsemblePrediction:
    """Combined ensemble prediction."""
    final_signal: str
    confidence: float
    expected_return: float
    risk_score: float
    contributing_strategies: List[StrategyPrediction]
    ensemble_method: EnsembleMethod
    weights: Dict[str, float]
    uncertainty: float


@dataclass
class StrategyPerformance:
    """Strategy performance metrics."""
    strategy_type: StrategyType
    accuracy: float
    precision: float
    recall: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    avg_return: float
    volatility: float
    last_updated: datetime


class EnsembleLearningSystem:
    """Advanced ensemble learning system for strategy combination."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize ensemble learning system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db_path = Path(config.get('db_path', 'data/ensemble_learning.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensemble parameters
        self.min_strategies = config.get('min_strategies', 3)
        self.performance_window = config.get('performance_window', 100)
        self.rebalance_frequency = config.get('rebalance_frequency', 50)
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
        
        # Strategy performance tracking
        self.strategy_performances = {}
        self.strategy_weights = {}
        self.prediction_history = []
        
        # ML models for ensemble
        self.meta_learner = LogisticRegression()
        self.stacking_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.models_trained = False
        
        # Initialize database
        self._init_database()
        
        # Initialize strategy weights
        self._initialize_strategy_weights()
        
        logger.info("Ensemble Learning System initialized")
    
    def _init_database(self):
        """Initialize SQLite database for ensemble data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS strategy_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    strategy_type TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    expected_return REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ensemble_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    final_signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    expected_return REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    ensemble_method TEXT NOT NULL,
                    weights TEXT NOT NULL,
                    uncertainty REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_type TEXT NOT NULL,
                    accuracy REAL NOT NULL,
                    precision_score REAL NOT NULL,
                    recall_score REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    win_rate REAL NOT NULL,
                    avg_return REAL NOT NULL,
                    volatility REAL NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def _initialize_strategy_weights(self):
        """Initialize equal weights for all strategies."""
        strategies = list(StrategyType)
        equal_weight = 1.0 / len(strategies)
        
        for strategy in strategies:
            self.strategy_weights[strategy.value] = equal_weight
            self.strategy_performances[strategy.value] = StrategyPerformance(
                strategy_type=strategy,
                accuracy=0.5,
                precision=0.5,
                recall=0.5,
                sharpe_ratio=0.0,
                max_drawdown=0.1,
                total_trades=0,
                win_rate=0.5,
                avg_return=0.0,
                volatility=0.02,
                last_updated=datetime.now()
            )
    
    async def generate_ensemble_prediction(self, market_data: Dict[str, Any], 
                                         strategy_predictions: List[StrategyPrediction]) -> EnsemblePrediction:
        """Generate ensemble prediction from individual strategy predictions.
        
        Args:
            market_data: Current market data
            strategy_predictions: List of individual strategy predictions
            
        Returns:
            Combined ensemble prediction
        """
        try:
            if len(strategy_predictions) < self.min_strategies:
                logger.warning(f"Insufficient strategies for ensemble: {len(strategy_predictions)}")
                return self._create_default_prediction()
            
            # Store individual predictions
            await self._store_strategy_predictions(strategy_predictions)
            
            # Generate ensemble using different methods
            ensemble_methods = [
                EnsembleMethod.WEIGHTED_VOTING,
                EnsembleMethod.PERFORMANCE_WEIGHTED,
                EnsembleMethod.BAYESIAN_AVERAGING
            ]
            
            best_prediction = None
            best_confidence = 0
            
            for method in ensemble_methods:
                prediction = await self._combine_predictions(strategy_predictions, method)
                
                if prediction.confidence > best_confidence:
                    best_confidence = prediction.confidence
                    best_prediction = prediction
            
            # Store ensemble prediction
            await self._store_ensemble_prediction(best_prediction)
            
            # Update prediction history
            self.prediction_history.append(best_prediction)
            if len(self.prediction_history) > 1000:
                self.prediction_history = self.prediction_history[-1000:]
            
            logger.info(f"Generated ensemble prediction: {best_prediction.final_signal} "
                       f"(confidence: {best_prediction.confidence:.2f})")
            
            return best_prediction
            
        except Exception as e:
            logger.error(f"Error generating ensemble prediction: {e}")
            return self._create_default_prediction()
    
    async def _combine_predictions(self, predictions: List[StrategyPrediction], 
                                 method: EnsembleMethod) -> EnsemblePrediction:
        """Combine predictions using specified ensemble method."""
        
        if method == EnsembleMethod.WEIGHTED_VOTING:
            return await self._weighted_voting(predictions)
        elif method == EnsembleMethod.PERFORMANCE_WEIGHTED:
            return await self._performance_weighted_combination(predictions)
        elif method == EnsembleMethod.BAYESIAN_AVERAGING:
            return await self._bayesian_averaging(predictions)
        elif method == EnsembleMethod.STACKING:
            return await self._stacking_combination(predictions)
        else:
            return await self._dynamic_selection(predictions)
    
    async def _weighted_voting(self, predictions: List[StrategyPrediction]) -> EnsemblePrediction:
        """Combine predictions using confidence-weighted voting."""
        
        # Calculate weighted signals
        signal_weights = {'buy': 0, 'sell': 0, 'hold': 0}
        total_weight = 0
        expected_returns = []
        risk_scores = []
        
        for pred in predictions:
            weight = pred.confidence
            signal_weights[pred.signal] += weight
            total_weight += weight
            expected_returns.append(pred.expected_return * weight)
            risk_scores.append(pred.risk_score * weight)
        
        # Normalize weights
        if total_weight > 0:
            for signal in signal_weights:
                signal_weights[signal] /= total_weight
        
        # Determine final signal
        final_signal = max(signal_weights, key=signal_weights.get)
        confidence = signal_weights[final_signal]
        
        # Calculate ensemble metrics
        expected_return = sum(expected_returns) / total_weight if total_weight > 0 else 0
        risk_score = sum(risk_scores) / total_weight if total_weight > 0 else 0.5
        
        # Calculate uncertainty
        uncertainty = 1 - confidence
        
        # Create weights dict
        weights = {pred.strategy_type.value: pred.confidence for pred in predictions}
        
        return EnsemblePrediction(
            final_signal=final_signal,
            confidence=confidence,
            expected_return=expected_return,
            risk_score=risk_score,
            contributing_strategies=predictions,
            ensemble_method=EnsembleMethod.WEIGHTED_VOTING,
            weights=weights,
            uncertainty=uncertainty
        )
    
    async def _performance_weighted_combination(self, predictions: List[StrategyPrediction]) -> EnsemblePrediction:
        """Combine predictions using historical performance weights."""
        
        signal_weights = {'buy': 0, 'sell': 0, 'hold': 0}
        total_weight = 0
        expected_returns = []
        risk_scores = []
        weights = {}
        
        for pred in predictions:
            # Get strategy performance
            perf = self.strategy_performances.get(pred.strategy_type.value)
            if perf:
                # Calculate performance-based weight
                performance_weight = (
                    perf.accuracy * 0.3 +
                    perf.sharpe_ratio * 0.2 +
                    perf.win_rate * 0.2 +
                    (1 - perf.max_drawdown) * 0.3
                )
                performance_weight = max(0.1, performance_weight)  # Minimum weight
            else:
                performance_weight = 0.5  # Default weight
            
            # Combine with prediction confidence
            final_weight = performance_weight * pred.confidence
            
            signal_weights[pred.signal] += final_weight
            total_weight += final_weight
            expected_returns.append(pred.expected_return * final_weight)
            risk_scores.append(pred.risk_score * final_weight)
            weights[pred.strategy_type.value] = final_weight
        
        # Normalize
        if total_weight > 0:
            for signal in signal_weights:
                signal_weights[signal] /= total_weight
            for strategy in weights:
                weights[strategy] /= total_weight
        
        final_signal = max(signal_weights, key=signal_weights.get)
        confidence = signal_weights[final_signal]
        expected_return = sum(expected_returns) / total_weight if total_weight > 0 else 0
        risk_score = sum(risk_scores) / total_weight if total_weight > 0 else 0.5
        
        return EnsemblePrediction(
            final_signal=final_signal,
            confidence=confidence,
            expected_return=expected_return,
            risk_score=risk_score,
            contributing_strategies=predictions,
            ensemble_method=EnsembleMethod.PERFORMANCE_WEIGHTED,
            weights=weights,
            uncertainty=1 - confidence
        )
    
    async def _bayesian_averaging(self, predictions: List[StrategyPrediction]) -> EnsemblePrediction:
        """Combine predictions using Bayesian model averaging."""
        
        # Prior probabilities (can be updated based on market regime)
        prior_probs = {'buy': 0.33, 'sell': 0.33, 'hold': 0.34}
        
        # Calculate posterior probabilities
        posterior_probs = {'buy': 0, 'sell': 0, 'hold': 0}
        
        for pred in predictions:
            # Get strategy reliability (accuracy)
            perf = self.strategy_performances.get(pred.strategy_type.value)
            reliability = perf.accuracy if perf else 0.5
            
            # Bayesian update
            likelihood = reliability if pred.signal != 'hold' else 1 - reliability
            
            for signal in posterior_probs:
                if signal == pred.signal:
                    posterior_probs[signal] += prior_probs[signal] * likelihood * pred.confidence
                else:
                    posterior_probs[signal] += prior_probs[signal] * (1 - likelihood) * (1 - pred.confidence)
        
        # Normalize
        total_prob = sum(posterior_probs.values())
        if total_prob > 0:
            for signal in posterior_probs:
                posterior_probs[signal] /= total_prob
        
        final_signal = max(posterior_probs, key=posterior_probs.get)
        confidence = posterior_probs[final_signal]
        
        # Calculate weighted returns and risks
        total_weight = sum(pred.confidence for pred in predictions)
        expected_return = sum(pred.expected_return * pred.confidence for pred in predictions) / total_weight if total_weight > 0 else 0
        risk_score = sum(pred.risk_score * pred.confidence for pred in predictions) / total_weight if total_weight > 0 else 0.5
        
        weights = {pred.strategy_type.value: pred.confidence for pred in predictions}
        
        return EnsemblePrediction(
            final_signal=final_signal,
            confidence=confidence,
            expected_return=expected_return,
            risk_score=risk_score,
            contributing_strategies=predictions,
            ensemble_method=EnsembleMethod.BAYESIAN_AVERAGING,
            weights=weights,
            uncertainty=1 - confidence
        )
    
    async def _stacking_combination(self, predictions: List[StrategyPrediction]) -> EnsemblePrediction:
        """Combine predictions using stacking meta-learner."""
        
        if not self.models_trained:
            # Use weighted voting as fallback
            return await self._weighted_voting(predictions)
        
        # Prepare features for meta-learner
        features = []
        for pred in predictions:
            features.extend([
                1 if pred.signal == 'buy' else 0,
                1 if pred.signal == 'sell' else 0,
                1 if pred.signal == 'hold' else 0,
                pred.confidence,
                pred.expected_return,
                pred.risk_score
            ])
        
        # Pad or truncate features to fixed size
        target_size = len(list(StrategyType)) * 6  # 6 features per strategy
        if len(features) < target_size:
            features.extend([0] * (target_size - len(features)))
        else:
            pass
        try:
            features = features[:target_size]
        
            # Get meta-learner prediction
            prediction_proba = self.meta_learner.predict_proba([features])[0]
            classes = self.meta_learner.classes_
            
            # Map to signals
            signal_probs = {}
            for i, cls in enumerate(classes):
                signal_probs[cls] = prediction_proba[i]
            
            final_signal = max(signal_probs, key=signal_probs.get)
            confidence = signal_probs[final_signal]
            
        except Exception as e:
            logger.error(f"Error in stacking prediction: {e}")
            return await self._weighted_voting(predictions)
        
        # Calculate ensemble metrics
        total_weight = sum(pred.confidence for pred in predictions)
        expected_return = sum(pred.expected_return * pred.confidence for pred in predictions) / total_weight if total_weight > 0 else 0
        risk_score = sum(pred.risk_score * pred.confidence for pred in predictions) / total_weight if total_weight > 0 else 0.5
        
        weights = {pred.strategy_type.value: pred.confidence for pred in predictions}
        
        return EnsemblePrediction(
            final_signal=final_signal,
            confidence=confidence,
            expected_return=expected_return,
            risk_score=risk_score,
            contributing_strategies=predictions,
            ensemble_method=EnsembleMethod.STACKING,
            weights=weights,
            uncertainty=1 - confidence
        )
    
    async def _dynamic_selection(self, predictions: List[StrategyPrediction]) -> EnsemblePrediction:
        """Dynamically select best performing strategies."""
        
        # Sort predictions by strategy performance and confidence
        scored_predictions = []
        for pred in predictions:
            perf = self.strategy_performances.get(pred.strategy_type.value)
            if perf:
                score = (perf.accuracy * 0.4 + perf.sharpe_ratio * 0.3 + 
                        perf.win_rate * 0.3) * pred.confidence
            else:
                score = pred.confidence * 0.5
            
            scored_predictions.append((score, pred))
        
        # Select top performing strategies
        scored_predictions.sort(key=lambda x: x[0], reverse=True)
        top_predictions = [pred for score, pred in scored_predictions[:3]]  # Top 3
        
        # Use weighted voting on selected strategies
        return await self._weighted_voting(top_predictions)
    
    async def update_strategy_performance(self, strategy_type: StrategyType, 
                                        actual_outcome: Dict[str, Any]):
        """Update strategy performance based on actual outcomes.
        
        Args:
            strategy_type: Strategy that made the prediction
            actual_outcome: Actual trade outcome
        """
        try:
            perf = self.strategy_performances.get(strategy_type.value)
            if not perf:
                return
            
            # Update performance metrics
            perf.total_trades += 1
            
            # Update accuracy (simplified)
            if actual_outcome.get('correct_prediction', False):
                perf.accuracy = (perf.accuracy * (perf.total_trades - 1) + 1) / perf.total_trades
            else:
                perf.accuracy = (perf.accuracy * (perf.total_trades - 1)) / perf.total_trades
            
            # Update win rate
            if actual_outcome.get('pnl', 0) > 0:
                wins = perf.win_rate * (perf.total_trades - 1) + 1
                perf.win_rate = wins / perf.total_trades
            else:
                wins = perf.win_rate * (perf.total_trades - 1)
                perf.win_rate = wins / perf.total_trades
            
            # Update average return
            pnl = actual_outcome.get('pnl', 0)
            perf.avg_return = (perf.avg_return * (perf.total_trades - 1) + pnl) / perf.total_trades
            
            # Update Sharpe ratio (simplified)
            if perf.volatility > 0:
                perf.sharpe_ratio = perf.avg_return / perf.volatility
            
            perf.last_updated = datetime.now()
            
            # Store updated performance
            await self._store_strategy_performance(perf)
            
            # Rebalance weights if needed
            if perf.total_trades % self.rebalance_frequency == 0:
                await self._rebalance_strategy_weights()
            
            logger.debug(f"Updated {strategy_type.value} performance: "
                        f"accuracy={perf.accuracy:.2f}, win_rate={perf.win_rate:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating strategy performance: {e}")
    
    async def _rebalance_strategy_weights(self):
        """Rebalance strategy weights based on recent performance."""
        try:
            total_score = 0
            strategy_scores = {}
            
            # Calculate performance scores
            for strategy_name, perf in self.strategy_performances.items():
                score = (
                    perf.accuracy * 0.3 +
                    perf.win_rate * 0.2 +
                    max(0, perf.sharpe_ratio) * 0.2 +
                    (1 - perf.max_drawdown) * 0.3
                )
                strategy_scores[strategy_name] = max(0.1, score)  # Minimum weight
                total_score += strategy_scores[strategy_name]
            
            # Normalize weights
            if total_score > 0:
                for strategy_name in strategy_scores:
                    self.strategy_weights[strategy_name] = strategy_scores[strategy_name] / total_score
            
            logger.info("Strategy weights rebalanced based on performance")
            
        except Exception as e:
            logger.error(f"Error rebalancing strategy weights: {e}")
    
    def _create_default_prediction(self) -> EnsemblePrediction:
        """Create default prediction when ensemble fails."""
        return EnsemblePrediction(
            final_signal='hold',
            confidence=0.5,
            expected_return=0.0,
            risk_score=0.5,
            contributing_strategies=[],
            ensemble_method=EnsembleMethod.WEIGHTED_VOTING,
            weights={},
            uncertainty=0.5
        )
    
    async def _store_strategy_predictions(self, predictions: List[StrategyPrediction]):
        """Store individual strategy predictions."""
        with sqlite3.connect(self.db_path) as conn:
            for pred in predictions:
                conn.execute('''
                    INSERT INTO strategy_predictions 
                    (timestamp, strategy_type, signal, confidence, expected_return, 
                     risk_score, reasoning)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pred.timestamp, pred.strategy_type.value, pred.signal,
                    pred.confidence, pred.expected_return, pred.risk_score, pred.reasoning
                ))
            conn.commit()
    
    async def _store_ensemble_prediction(self, prediction: EnsemblePrediction):
        """Store ensemble prediction."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO ensemble_predictions 
                (timestamp, final_signal, confidence, expected_return, risk_score,
                 ensemble_method, weights, uncertainty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(), prediction.final_signal, prediction.confidence,
                prediction.expected_return, prediction.risk_score,
                prediction.ensemble_method.value, str(prediction.weights), prediction.uncertainty
            ))
            conn.commit()
    
    async def _store_strategy_performance(self, performance: StrategyPerformance):
        """Store strategy performance metrics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO strategy_performance 
                (strategy_type, accuracy, precision_score, recall_score, sharpe_ratio,
                 max_drawdown, total_trades, win_rate, avg_return, volatility, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                performance.strategy_type.value, performance.accuracy, performance.precision,
                performance.recall, performance.sharpe_ratio, performance.max_drawdown,
                performance.total_trades, performance.win_rate, performance.avg_return,
                performance.volatility, performance.last_updated
            ))
            conn.commit()
    
    def get_ensemble_summary(self) -> Dict[str, Any]:
        """Get ensemble system summary.
        
        Returns:
            Ensemble system summary
        """
        recent_predictions = self.prediction_history[-10:] if self.prediction_history else []
        
        if not recent_predictions:
            return {
                'total_predictions': 0,
                'avg_confidence': 0,
                'signal_distribution': {},
                'best_performing_strategy': 'none',
                'ensemble_accuracy': 0
            }
        
        # Calculate summary statistics
        avg_confidence = np.mean([p.confidence for p in recent_predictions])
        
        signal_counts = {'buy': 0, 'sell': 0, 'hold': 0}
        for pred in recent_predictions:
            signal_counts[pred.final_signal] += 1
        
        # Find best performing strategy
        best_strategy = 'none'
        best_accuracy = 0
        for strategy_name, perf in self.strategy_performances.items():
            if perf.accuracy > best_accuracy:
                best_accuracy = perf.accuracy
                best_strategy = strategy_name
        
        return {
            'total_predictions': len(self.prediction_history),
            'avg_confidence': avg_confidence,
            'signal_distribution': signal_counts,
            'best_performing_strategy': best_strategy,
            'ensemble_accuracy': best_accuracy,
            'strategy_weights': dict(self.strategy_weights)
        }
