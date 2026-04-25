"""
World Model - Market State Representation & Prediction
=======================================================

Implements a predictive world model for markets:
1. Market State: Current representation of market conditions
2. State Transitions: Model how markets evolve
3. Counterfactual Reasoning: "What-if" scenario analysis
4. Prediction: Forecast future states

Based on the Foundation Agents paper (arXiv:2504.01990) world modeling.
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import deque

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class AssetClass(Enum):
    """Asset class types"""
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    COMMODITY = "commodity"
    CURRENCY = "currency"
    CRYPTO = "crypto"
    DERIVATIVE = "derivative"


@dataclass
class MarketState:
    """
    Representation of current market state
    
    Captures all relevant market information at a point in time.
    """
    timestamp: datetime
    
    # Price data
    prices: Dict[str, float] = field(default_factory=dict)
    returns: Dict[str, float] = field(default_factory=dict)
    volumes: Dict[str, float] = field(default_factory=dict)
    
    # Regime
    regime: MarketRegime = MarketRegime.UNKNOWN
    regime_confidence: float = 0.5
    
    # Volatility
    volatility: Dict[str, float] = field(default_factory=dict)
    implied_volatility: Dict[str, float] = field(default_factory=dict)
    
    # Correlations
    correlations: Dict[Tuple[str, str], float] = field(default_factory=dict)
    
    # Sentiment
    sentiment_score: float = 0.0  # -1 to 1
    fear_greed_index: float = 50.0  # 0 to 100
    
    # Macro indicators
    macro_indicators: Dict[str, float] = field(default_factory=dict)
    
    # Liquidity
    liquidity_score: float = 1.0  # 0 to 1
    bid_ask_spreads: Dict[str, float] = field(default_factory=dict)
    
    # Anomalies detected
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    data_quality: float = 1.0  # 0 to 1
    
    def to_vector(self, assets: List[str]) -> np.ndarray:
        """Convert state to feature vector for ML"""
        features = []
        
        for asset in assets:
            features.extend([
                self.prices.get(asset, 0),
                self.returns.get(asset, 0),
                self.volumes.get(asset, 0),
                self.volatility.get(asset, 0)
            ])
        
        features.extend([
            self.regime_confidence,
            self.sentiment_score,
            self.fear_greed_index / 100,
            self.liquidity_score
        ])
        
        return np.array(features)
    
    def copy(self) -> 'MarketState':
        """Create a copy of this state"""
        return MarketState(
            timestamp=self.timestamp,
            prices=self.prices.copy(),
            returns=self.returns.copy(),
            volumes=self.volumes.copy(),
            regime=self.regime,
            regime_confidence=self.regime_confidence,
            volatility=self.volatility.copy(),
            implied_volatility=self.implied_volatility.copy(),
            correlations=self.correlations.copy(),
            sentiment_score=self.sentiment_score,
            fear_greed_index=self.fear_greed_index,
            macro_indicators=self.macro_indicators.copy(),
            liquidity_score=self.liquidity_score,
            bid_ask_spreads=self.bid_ask_spreads.copy(),
            anomalies=self.anomalies.copy(),
            data_quality=self.data_quality
        )


@dataclass
class Prediction:
    """A prediction about future market state"""
    prediction_id: str
    target: str  # What is being predicted
    horizon: timedelta  # How far ahead
    
    # Prediction values
    point_estimate: float
    confidence_interval: Tuple[float, float]
    probability_distribution: Optional[Dict[str, float]] = None
    
    # Confidence
    confidence: float = 0.5
    
    # Basis
    reasoning: str = ""
    supporting_evidence: List[str] = field(default_factory=list)
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    actual_value: Optional[float] = None
    error: Optional[float] = None
    
    def evaluate(self, actual: float) -> float:
        """Evaluate prediction accuracy"""
        self.actual_value = actual
        self.error = abs(actual - self.point_estimate)
        
        # Check if within confidence interval
        in_interval = self.confidence_interval[0] <= actual <= self.confidence_interval[1]
        
        return self.error


@dataclass
class StateTransition:
    """Model of state transition"""
    from_state: MarketState
    to_state: MarketState
    action: Optional[str] = None  # Action that caused transition
    probability: float = 1.0
    duration: timedelta = field(default_factory=lambda: timedelta(hours=1))


class WorldModel:
    """
    World Model for Market Understanding
    
    Maintains an internal model of how markets work:
    - Current state representation
    - State transition dynamics
    - Counterfactual reasoning
    - Future state prediction
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Current state
        self.current_state: Optional[MarketState] = None
        
        # State history
        self.state_history: deque = deque(maxlen=self.config.get('history_size', 1000))
        
        # Transition model
        self.transition_history: List[StateTransition] = []
        self.transition_probabilities: Dict[Tuple[MarketRegime, MarketRegime], float] = {}
        
        # Predictions
        self.active_predictions: List[Prediction] = []
        self.prediction_history: List[Prediction] = []
        
        # Regime detection
        self.regime_detector = self._create_regime_detector()
        
        # Statistics
        self.stats = {
            'state_updates': 0,
            'predictions_made': 0,
            'predictions_evaluated': 0,
            'avg_prediction_error': 0.0,
            'counterfactuals_generated': 0
        }
        
        logger.info("World Model initialized")
    
    def _create_regime_detector(self) -> Callable:
        """Create regime detection function"""
        def detect_regime(state: MarketState) -> Tuple[MarketRegime, float]:
            # Simple rule-based regime detection
            # In production, would use ML model
            
            avg_return = np.mean(list(state.returns.values())) if state.returns else 0
            avg_vol = np.mean(list(state.volatility.values())) if state.volatility else 0.02
            
            if avg_vol > 0.03:  # High volatility threshold
                if avg_return < -0.02:
                    return MarketRegime.CRISIS, 0.8
                return MarketRegime.HIGH_VOLATILITY, 0.7
            
            if avg_vol < 0.01:
                return MarketRegime.LOW_VOLATILITY, 0.7
            
            if avg_return > 0.01:
                return MarketRegime.TRENDING_UP, 0.6
            elif avg_return < -0.01:
                return MarketRegime.TRENDING_DOWN, 0.6
            
            return MarketRegime.RANGING, 0.5
        
        return detect_regime
    
    def update_state(
        self,
        prices: Dict[str, float],
        volumes: Optional[Dict[str, float]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> MarketState:
        """Update the world model with new market data"""
        timestamp = datetime.utcnow()
        
        # Calculate returns if we have previous state
        returns = {}
        if self.current_state and self.current_state.prices:
            for asset, price in prices.items():
                if asset in self.current_state.prices and self.current_state.prices[asset] > 0:
                    returns[asset] = (price - self.current_state.prices[asset]) / self.current_state.prices[asset]
        
        # Calculate volatility (simple rolling std)
        volatility = self._calculate_volatility(prices)
        
        # Create new state
        new_state = MarketState(
            timestamp=timestamp,
            prices=prices,
            returns=returns,
            volumes=volumes or {},
            volatility=volatility
        )
        
        # Add additional data
        if additional_data:
            if 'sentiment_score' in additional_data:
                new_state.sentiment_score = additional_data['sentiment_score']
            if 'fear_greed_index' in additional_data:
                new_state.fear_greed_index = additional_data['fear_greed_index']
            if 'macro_indicators' in additional_data:
                new_state.macro_indicators = additional_data['macro_indicators']
        
        # Detect regime
        regime, confidence = self.regime_detector(new_state)
        new_state.regime = regime
        new_state.regime_confidence = confidence
        
        # Record transition
        if self.current_state:
            transition = StateTransition(
                from_state=self.current_state,
                to_state=new_state,
                duration=timestamp - self.current_state.timestamp
            )
            self.transition_history.append(transition)
            self._update_transition_probabilities(self.current_state.regime, new_state.regime)
        
        # Update current state
        self.current_state = new_state
        self.state_history.append(new_state)
        self.stats['state_updates'] += 1
        
        # Evaluate any predictions that have expired
        self._evaluate_predictions()
        
        return new_state
    
    def _calculate_volatility(self, prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate volatility for each asset"""
        volatility = {}
        
        if len(self.state_history) < 2:
            return {asset: 0.02 for asset in prices}  # Default volatility
        
        for asset in prices:
            returns = []
            for state in list(self.state_history)[-20:]:  # Last 20 states
                if asset in state.returns:
                    returns.append(state.returns[asset])
            
            if returns:
                volatility[asset] = np.std(returns) if len(returns) > 1 else 0.02
            else:
                volatility[asset] = 0.02
        
        return volatility
    
    def _update_transition_probabilities(self, from_regime: MarketRegime, to_regime: MarketRegime):
        """Update regime transition probability estimates"""
        key = (from_regime, to_regime)
        
        # Count transitions
        transition_counts: Dict[Tuple[MarketRegime, MarketRegime], int] = {}
        from_counts: Dict[MarketRegime, int] = {}
        
        for trans in self.transition_history[-100:]:  # Last 100 transitions
            t_key = (trans.from_state.regime, trans.to_state.regime)
            transition_counts[t_key] = transition_counts.get(t_key, 0) + 1
            from_counts[trans.from_state.regime] = from_counts.get(trans.from_state.regime, 0) + 1
        
        # Calculate probabilities
        for (f, t), count in transition_counts.items():
            if from_counts.get(f, 0) > 0:
                self.transition_probabilities[(f, t)] = count / from_counts[f]
    
    def predict(
        self,
        target: str,
        horizon: timedelta,
        method: str = "ensemble"
    ) -> Prediction:
        """Make a prediction about future market state"""
        if not self.current_state:
            raise ValueError("No current state available for prediction")
        
        prediction_id = f"pred_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{target}"
        
        # Generate prediction based on method
        if method == "trend":
            point_estimate, ci = self._predict_trend(target, horizon)
        elif method == "mean_reversion":
            point_estimate, ci = self._predict_mean_reversion(target, horizon)
        elif method == "regime":
            point_estimate, ci = self._predict_regime_based(target, horizon)
        else:  # ensemble
            point_estimate, ci = self._predict_ensemble(target, horizon)
        
        prediction = Prediction(
            prediction_id=prediction_id,
            target=target,
            horizon=horizon,
            point_estimate=point_estimate,
            confidence_interval=ci,
            confidence=0.5 + 0.3 * self.current_state.regime_confidence,
            reasoning=f"Prediction using {method} method",
            expires_at=datetime.utcnow() + horizon
        )
        
        self.active_predictions.append(prediction)
        self.stats['predictions_made'] += 1
        
        return prediction
    
    def _predict_trend(self, target: str, horizon: timedelta) -> Tuple[float, Tuple[float, float]]:
        """Predict based on trend continuation"""
        if target not in self.current_state.prices:
            return 0.0, (-1.0, 1.0)
        
        current_price = self.current_state.prices[target]
        
        # Calculate recent trend
        recent_returns = []
        for state in list(self.state_history)[-10:]:
            if target in state.returns:
                recent_returns.append(state.returns[target])
        
        if not recent_returns:
            return current_price, (current_price * 0.95, current_price * 1.05)
        
        avg_return = np.mean(recent_returns)
        volatility = self.current_state.volatility.get(target, 0.02)
        
        # Project forward
        hours = horizon.total_seconds() / 3600
        projected_return = avg_return * hours
        projected_price = current_price * (1 + projected_return)
        
        # Confidence interval
        ci_width = volatility * np.sqrt(hours) * 1.96
        ci = (current_price * (1 + projected_return - ci_width),
              current_price * (1 + projected_return + ci_width))
        
        return projected_price, ci
    
    def _predict_mean_reversion(self, target: str, horizon: timedelta) -> Tuple[float, Tuple[float, float]]:
        """Predict based on mean reversion"""
        if target not in self.current_state.prices:
            return 0.0, (-1.0, 1.0)
        
        current_price = self.current_state.prices[target]
        
        # Calculate historical mean
        prices = [s.prices.get(target, current_price) for s in self.state_history if target in s.prices]
        if not prices:
            return current_price, (current_price * 0.95, current_price * 1.05)
        
        mean_price = np.mean(prices)
        volatility = self.current_state.volatility.get(target, 0.02)
        
        # Mean reversion speed
        reversion_speed = 0.1  # 10% reversion per period
        hours = horizon.total_seconds() / 3600
        
        # Project toward mean
        reversion = (mean_price - current_price) * reversion_speed * min(hours, 24) / 24
        projected_price = current_price + reversion
        
        # Confidence interval
        ci_width = volatility * np.sqrt(hours) * 1.96
        ci = (projected_price - current_price * ci_width,
              projected_price + current_price * ci_width)
        
        return projected_price, ci
    
    def _predict_regime_based(self, target: str, horizon: timedelta) -> Tuple[float, Tuple[float, float]]:
        """Predict based on current regime"""
        if target not in self.current_state.prices:
            return 0.0, (-1.0, 1.0)
        
        current_price = self.current_state.prices[target]
        regime = self.current_state.regime
        
        # Regime-specific return expectations
        regime_returns = {
            MarketRegime.TRENDING_UP: 0.001,
            MarketRegime.TRENDING_DOWN: -0.001,
            MarketRegime.RANGING: 0.0,
            MarketRegime.HIGH_VOLATILITY: 0.0,
            MarketRegime.LOW_VOLATILITY: 0.0002,
            MarketRegime.CRISIS: -0.003,
            MarketRegime.RECOVERY: 0.002,
            MarketRegime.UNKNOWN: 0.0
        }
        
        expected_return = regime_returns.get(regime, 0.0)
        hours = horizon.total_seconds() / 3600
        
        projected_price = current_price * (1 + expected_return * hours)
        
        # Wider CI for uncertain regimes
        volatility = self.current_state.volatility.get(target, 0.02)
        regime_uncertainty = 1.0 if regime == MarketRegime.UNKNOWN else 0.5
        ci_width = volatility * np.sqrt(hours) * 1.96 * (1 + regime_uncertainty)
        
        ci = (projected_price - current_price * ci_width,
              projected_price + current_price * ci_width)
        
        return projected_price, ci
    
    def _predict_ensemble(self, target: str, horizon: timedelta) -> Tuple[float, Tuple[float, float]]:
        """Ensemble prediction combining multiple methods"""
        trend_pred, trend_ci = self._predict_trend(target, horizon)
        mr_pred, mr_ci = self._predict_mean_reversion(target, horizon)
        regime_pred, regime_ci = self._predict_regime_based(target, horizon)
        
        # Weighted average
        weights = [0.4, 0.3, 0.3]  # Trend, MR, Regime
        point_estimate = weights[0] * trend_pred + weights[1] * mr_pred + weights[2] * regime_pred
        
        # Combined CI (conservative)
        ci_low = min(trend_ci[0], mr_ci[0], regime_ci[0])
        ci_high = max(trend_ci[1], mr_ci[1], regime_ci[1])
        
        return point_estimate, (ci_low, ci_high)
    
    def _evaluate_predictions(self):
        """Evaluate predictions that have expired"""
        now = datetime.utcnow()
        still_active = []
        
        for pred in self.active_predictions:
            if pred.expires_at and pred.expires_at <= now:
                # Get actual value
                if pred.target in self.current_state.prices:
                    actual = self.current_state.prices[pred.target]
                    error = pred.evaluate(actual)
                    
                    # Update running average error
                    n = self.stats['predictions_evaluated']
                    self.stats['avg_prediction_error'] = (
                        (self.stats['avg_prediction_error'] * n + error) / (n + 1)
                    )
                    self.stats['predictions_evaluated'] += 1
                
                self.prediction_history.append(pred)
            else:
                still_active.append(pred)
        
        self.active_predictions = still_active
    
    def simulate_counterfactual(
        self,
        scenario: Dict[str, Any],
        horizon: timedelta
    ) -> List[MarketState]:
        """
        Simulate a counterfactual scenario
        
        "What would happen if X occurred?"
        """
        if not self.current_state:
            return []
        
        self.stats['counterfactuals_generated'] += 1
        
        # Start from current state
        simulated_states = []
        current = self.current_state.copy()
        
        # Apply scenario modifications
        if 'price_shock' in scenario:
            for asset, shock in scenario['price_shock'].items():
                if asset in current.prices:
                    current.prices[asset] *= (1 + shock)
        
        if 'volatility_multiplier' in scenario:
            for asset in current.volatility:
                current.volatility[asset] *= scenario['volatility_multiplier']
        
        if 'regime_change' in scenario:
            current.regime = MarketRegime(scenario['regime_change'])
        
        simulated_states.append(current)
        
        # Simulate forward
        steps = int(horizon.total_seconds() / 3600)  # Hourly steps
        for _ in range(min(steps, 24)):  # Max 24 steps
            next_state = self._simulate_step(current, scenario)
            simulated_states.append(next_state)
            current = next_state
        
        return simulated_states
    
    def _simulate_step(self, state: MarketState, scenario: Dict[str, Any]) -> MarketState:
        """Simulate one step forward"""
        new_state = state.copy()
        new_state.timestamp = state.timestamp + timedelta(hours=1)
        
        # Simulate price changes based on regime
        regime_drift = {
            MarketRegime.TRENDING_UP: 0.001,
            MarketRegime.TRENDING_DOWN: -0.001,
            MarketRegime.CRISIS: -0.005,
            MarketRegime.RECOVERY: 0.003,
        }.get(state.regime, 0.0)
        
        for asset in new_state.prices:
            vol = new_state.volatility.get(asset, 0.02)
            random_return = np.random.normal(regime_drift, vol)
            new_state.prices[asset] *= (1 + random_return)
            new_state.returns[asset] = random_return
        
        return new_state
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current world state"""
        if not self.current_state:
            return {'status': 'no_state'}
        
        return {
            'timestamp': self.current_state.timestamp.isoformat(),
            'regime': self.current_state.regime.value,
            'regime_confidence': self.current_state.regime_confidence,
            'num_assets': len(self.current_state.prices),
            'avg_return': np.mean(list(self.current_state.returns.values())) if self.current_state.returns else 0,
            'avg_volatility': np.mean(list(self.current_state.volatility.values())) if self.current_state.volatility else 0,
            'sentiment': self.current_state.sentiment_score,
            'liquidity': self.current_state.liquidity_score,
            'anomalies': len(self.current_state.anomalies),
            'active_predictions': len(self.active_predictions),
            'prediction_accuracy': 1 - self.stats['avg_prediction_error'] if self.stats['predictions_evaluated'] > 0 else None
        }
    
    def get_transition_matrix(self) -> Dict[str, Dict[str, float]]:
        """Get regime transition probability matrix"""
        matrix = {}
        
        for regime in MarketRegime:
            matrix[regime.value] = {}
            for to_regime in MarketRegime:
                prob = self.transition_probabilities.get((regime, to_regime), 0.0)
                matrix[regime.value][to_regime.value] = prob
        
        return matrix
