"""
Adaptive Intelligence
=====================

Real-time learning and strategy adaptation system.
Continuously adapts to changing market conditions without human intervention.

Features:
- Online learning from recent trades and market data
- Dynamic parameter optimization
- Strategy adaptation based on performance
- Market condition-specific strategy selection
- Continuous model updating
- Performance-based weight adjustment
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque

logger = logging.getLogger(__name__)

try:
    from sklearn.linear_model import SGDRegressor, PassiveAggressiveRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.debug("scikit-learn not available for online learning")


class AdaptationMode(Enum):
    """Adaptation modes"""
    CONSERVATIVE = "conservative"  # Slow adaptation
    MODERATE = "moderate"  # Balanced adaptation
    AGGRESSIVE = "aggressive"  # Fast adaptation
    EMERGENCY = "emergency"  # Immediate adaptation


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy"""
    strategy_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    avg_profit_per_trade: float = 0.0
    recent_performance: float = 0.0  # Last 20 trades
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AdaptiveParameter:
    """Adaptive parameter that adjusts based on performance"""
    name: str
    current_value: float
    min_value: float
    max_value: float
    adaptation_rate: float = 0.1
    performance_sensitivity: float = 1.0
    history: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LearningUpdate:
    """Record of a learning update"""
    timestamp: datetime
    update_type: str
    parameters_changed: Dict[str, float]
    performance_before: float
    performance_after: float
    reason: str


class AdaptiveIntelligence:
    """
    Real-time adaptive learning system.
    
    Continuously learns from:
    - Trade outcomes
    - Market conditions
    - Strategy performance
    - Parameter effectiveness
    
    Adapts:
    - Strategy parameters
    - Position sizing
    - Risk levels
    - Entry/exit rules
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Adaptation settings
        self.adaptation_mode = AdaptationMode(
            self.config.get('adaptation_mode', 'moderate')
        )
        self.learning_rate = self.config.get('learning_rate', 0.01)
        self.min_samples_for_adaptation = self.config.get('min_samples', 20)
        
        # Performance tracking
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        self.adaptive_parameters: Dict[str, AdaptiveParameter] = {}
        self.learning_history: deque = deque(maxlen=1000)
        
        # Online learning models
        self._init_learning_models()
        
        # Recent data buffer
        self.recent_trades = deque(maxlen=100)
        self.recent_market_states = deque(maxlen=100)
        
        logger.info(f"Adaptive Intelligence initialized (mode: {self.adaptation_mode.value})")
    
    def _init_learning_models(self):
        """Initialize online learning models"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available - using simplified adaptation")
            self.profit_predictor = None
            self.risk_predictor = None
            self.scaler = None
            return
        
        # Online learning for profit prediction
        self.profit_predictor = SGDRegressor(
            learning_rate='adaptive',
            eta0=self.learning_rate,
            random_state=42
        )
        
        # Online learning for risk prediction
        self.risk_predictor = PassiveAggressiveRegressor(
            C=1.0,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        self.models_initialized = False
    
    async def learn_from_trade(
        self,
        trade_data: Dict[str, Any],
        market_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Learn from a completed trade.
        
        Args:
            trade_data: Trade information (entry, exit, profit, etc.)
            market_state: Market conditions during trade
        
        Returns:
            Learning insights and adaptations made
        """
        try:
            # Store trade
            self.recent_trades.append({
                'timestamp': datetime.now(),
                'trade': trade_data,
                'market_state': market_state
            })
            
            # Update strategy performance
            strategy_name = trade_data.get('strategy', 'default')
            self._update_strategy_performance(strategy_name, trade_data)
            
            # Adapt parameters based on performance
            adaptations = await self._adapt_parameters(trade_data, market_state)
            
            # Update online models
            if SKLEARN_AVAILABLE and len(self.recent_trades) >= self.min_samples_for_adaptation:
                self._update_online_models()
            
            return {
                'learned': True,
                'adaptations': adaptations,
                'strategy_performance': self.strategy_performance.get(strategy_name).__dict__ if strategy_name in self.strategy_performance else {},
                'total_trades_learned': len(self.recent_trades)
            }
            
        except Exception as e:
            logger.error(f"Error learning from trade: {e}")
            return {'learned': False, 'error': str(e)}
    
    def _update_strategy_performance(
        self,
        strategy_name: str,
        trade_data: Dict[str, Any]
    ):
        """Update performance metrics for a strategy"""
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = StrategyPerformance(
                strategy_name=strategy_name
            )
        
        perf = self.strategy_performance[strategy_name]
        profit = trade_data.get('profit', 0.0)
        
        perf.total_trades += 1
        
        if profit > 0:
            perf.winning_trades += 1
            perf.total_profit += profit
        else:
            perf.losing_trades += 1
            perf.total_loss += abs(profit)
        
        # Calculate metrics
        if perf.total_trades > 0:
            perf.win_rate = perf.winning_trades / perf.total_trades
        
        if perf.total_loss > 0:
            perf.profit_factor = perf.total_profit / perf.total_loss
        
        perf.avg_profit_per_trade = (perf.total_profit - perf.total_loss) / perf.total_trades
        
        # Recent performance (last 20 trades)
        recent_trades = list(self.recent_trades)[-20:]
        if recent_trades:
            recent_profits = [t['trade'].get('profit', 0) for t in recent_trades]
            perf.recent_performance = sum(recent_profits) / len(recent_profits)
        
        perf.last_updated = datetime.now()
    
    async def _adapt_parameters(
        self,
        trade_data: Dict[str, Any],
        market_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Adapt strategy parameters based on trade outcome"""
        adaptations = {}
        
        try:
            profit = trade_data.get('profit', 0.0)
            
            # Get or create adaptive parameters
            if 'position_size_multiplier' not in self.adaptive_parameters:
                self._initialize_default_parameters()
            
            # Adapt based on performance
            for param_name, param in self.adaptive_parameters.items():
                old_value = param.current_value
                new_value = self._calculate_adapted_value(
                    param=param,
                    profit=profit,
                    market_state=market_state
                )
                
                if new_value != old_value:
                    param.current_value = new_value
                    param.history.append(new_value)
                    param.last_updated = datetime.now()
                    adaptations[param_name] = new_value
            
            # Record learning update
            if adaptations:
                self.learning_history.append(LearningUpdate(
                    timestamp=datetime.now(),
                    update_type='parameter_adaptation',
                    parameters_changed=adaptations,
                    performance_before=0.0,  # Would track actual performance
                    performance_after=profit,
                    reason=f"Adapting to {'profitable' if profit > 0 else 'losing'} trade"
                ))
            
            return adaptations
            
        except Exception as e:
            logger.error(f"Error adapting parameters: {e}")
            return {}
    
    def _initialize_default_parameters(self):
        """Initialize default adaptive parameters"""
        self.adaptive_parameters = {
            'position_size_multiplier': AdaptiveParameter(
                name='position_size_multiplier',
                current_value=1.0,
                min_value=0.5,
                max_value=2.0,
                adaptation_rate=0.05,
                performance_sensitivity=1.0
            ),
            'risk_multiplier': AdaptiveParameter(
                name='risk_multiplier',
                current_value=1.0,
                min_value=0.5,
                max_value=1.5,
                adaptation_rate=0.03,
                performance_sensitivity=1.5
            ),
            'entry_confidence_threshold': AdaptiveParameter(
                name='entry_confidence_threshold',
                current_value=0.6,
                min_value=0.4,
                max_value=0.8,
                adaptation_rate=0.02,
                performance_sensitivity=0.8
            ),
            'stop_loss_multiplier': AdaptiveParameter(
                name='stop_loss_multiplier',
                current_value=1.0,
                min_value=0.8,
                max_value=1.5,
                adaptation_rate=0.04,
                performance_sensitivity=1.2
            ),
            'take_profit_multiplier': AdaptiveParameter(
                name='take_profit_multiplier',
                current_value=1.0,
                min_value=0.8,
                max_value=2.0,
                adaptation_rate=0.04,
                performance_sensitivity=1.0
            ),
        }
    
    def _calculate_adapted_value(
        self,
        param: AdaptiveParameter,
        profit: float,
        market_state: Dict[str, Any]
    ) -> float:
        """Calculate new parameter value based on performance"""
        
        # Get adaptation rate based on mode
        adaptation_rate = param.adaptation_rate
        if self.adaptation_mode == AdaptationMode.CONSERVATIVE:
            adaptation_rate *= 0.5
        elif self.adaptation_mode == AdaptationMode.AGGRESSIVE:
            adaptation_rate *= 2.0
        elif self.adaptation_mode == AdaptationMode.EMERGENCY:
            adaptation_rate *= 5.0
        
        # Calculate adjustment based on profit
        if profit > 0:
            # Winning trade - slightly increase aggressive parameters
            adjustment = adaptation_rate * param.performance_sensitivity
        else:
            # Losing trade - reduce aggressive parameters
            adjustment = -adaptation_rate * param.performance_sensitivity * 1.5
        
        # Apply adjustment
        new_value = param.current_value * (1 + adjustment)
        
        # Clamp to bounds
        new_value = max(param.min_value, min(param.max_value, new_value))
        
        return new_value
    
    def _update_online_models(self):
        """Update online learning models with recent data"""
        try:
            if not SKLEARN_AVAILABLE or len(self.recent_trades) < 10:
                return
            
            # Prepare training data
            X = []
            y_profit = []
            
            for trade_record in list(self.recent_trades)[-50:]:
                trade = trade_record['trade']
                market = trade_record['market_state']
                
                # Feature vector
                features = [
                    market.get('volatility', 0.0),
                    market.get('trend_strength', 0.0),
                    market.get('momentum', 0.0),
                    trade.get('entry_confidence', 0.5),
                    trade.get('position_size', 1.0),
                ]
                
                X.append(features)
                y_profit.append(trade.get('profit', 0.0))
            
            X = np.array(X)
            y_profit = np.array(y_profit)
            
            # Initialize or update scaler
            if not self.models_initialized:
                self.scaler.fit(X)
                self.models_initialized = True
            
            X_scaled = self.scaler.transform(X)
            
            # Partial fit (online learning)
            self.profit_predictor.partial_fit(X_scaled, y_profit)
            
            logger.debug("Updated online learning models")
            
        except Exception as e:
            logger.error(f"Error updating online models: {e}")
    
    async def predict_trade_outcome(
        self,
        market_state: Dict[str, Any],
        trade_params: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Predict expected trade outcome using learned models.
        
        Args:
            market_state: Current market conditions
            trade_params: Proposed trade parameters
        
        Returns:
            Predicted outcomes (profit, risk, confidence)
        """
        try:
            if not SKLEARN_AVAILABLE or not self.models_initialized:
                return {
                    'predicted_profit': 0.0,
                    'confidence': 0.5,
                    'recommendation': 'neutral'
                }
            
            # Prepare features
            features = np.array([[
                market_state.get('volatility', 0.0),
                market_state.get('trend_strength', 0.0),
                market_state.get('momentum', 0.0),
                trade_params.get('entry_confidence', 0.5),
                trade_params.get('position_size', 1.0),
            ]])
            
            features_scaled = self.scaler.transform(features)
            
            # Predict
            predicted_profit = self.profit_predictor.predict(features_scaled)[0]
            
            # Calculate confidence based on recent model performance
            confidence = self._calculate_prediction_confidence()
            
            # Generate recommendation
            if predicted_profit > 0.001 and confidence > 0.6:
                recommendation = 'take_trade'
            elif predicted_profit < -0.001:
                recommendation = 'avoid_trade'
            else:
                recommendation = 'neutral'
            
            return {
                'predicted_profit': float(predicted_profit),
                'confidence': float(confidence),
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error predicting trade outcome: {e}")
            return {
                'predicted_profit': 0.0,
                'confidence': 0.0,
                'recommendation': 'error'
            }
    
    def _calculate_prediction_confidence(self) -> float:
        """Calculate confidence in model predictions based on recent accuracy"""
        try:
            if len(self.recent_trades) < 10:
                return 0.5
            
            # Simple confidence based on recent win rate
            recent_trades = list(self.recent_trades)[-20:]
            wins = sum(1 for t in recent_trades if t['trade'].get('profit', 0) > 0)
            
            win_rate = wins / len(recent_trades)
            
            # Confidence scales with win rate
            confidence = 0.3 + (win_rate * 0.7)
            
            return confidence
            
        except Exception:
            return 0.5
    
    async def get_optimal_parameters(
        self,
        market_state: Dict[str, Any],
        strategy_name: str
    ) -> Dict[str, float]:
        """
        Get optimal parameters for current market conditions.
        
        Args:
            market_state: Current market state
            strategy_name: Strategy to optimize for
        
        Returns:
            Optimized parameters
        """
        try:
            if not self.adaptive_parameters:
                self._initialize_default_parameters()
            
            # Get current adaptive parameters
            optimal_params = {
                name: param.current_value
                for name, param in self.adaptive_parameters.items()
            }
            
            # Adjust based on market conditions
            volatility = market_state.get('volatility', 0.01)
            
            # High volatility - reduce position size, widen stops
            if volatility > 0.02:
                optimal_params['position_size_multiplier'] *= 0.8
                optimal_params['stop_loss_multiplier'] *= 1.2
            
            # Low volatility - can increase position size
            elif volatility < 0.005:
                optimal_params['position_size_multiplier'] *= 1.1
                optimal_params['stop_loss_multiplier'] *= 0.9
            
            return optimal_params
            
        except Exception as e:
            logger.error(f"Error getting optimal parameters: {e}")
            return {}
    
    def set_adaptation_mode(self, mode: AdaptationMode):
        """Change adaptation mode"""
        self.adaptation_mode = mode
        logger.info(f"Adaptation mode changed to: {mode.value}")
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning and adaptation statistics"""
        return {
            'total_trades_learned': len(self.recent_trades),
            'strategies_tracked': len(self.strategy_performance),
            'adaptive_parameters': len(self.adaptive_parameters),
            'learning_updates': len(self.learning_history),
            'adaptation_mode': self.adaptation_mode.value,
            'models_initialized': self.models_initialized if SKLEARN_AVAILABLE else False,
            'recent_adaptations': [
                {
                    'timestamp': update.timestamp.isoformat(),
                    'type': update.update_type,
                    'parameters': update.parameters_changed,
                    'reason': update.reason
                }
                for update in list(self.learning_history)[-5:]
            ],
            'strategy_performance': {
                name: {
                    'win_rate': perf.win_rate,
                    'profit_factor': perf.profit_factor,
                    'total_trades': perf.total_trades,
                    'recent_performance': perf.recent_performance
                }
                for name, perf in self.strategy_performance.items()
            }
        }
