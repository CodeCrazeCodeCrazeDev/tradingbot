"""
Dynamic Risk Neural Matrix
==========================
Real-time neural network-based risk adjustment system.

Features:
- Real-time leverage adjustment
- Dynamic position sizing
- Adaptive stop-loss width
- Take-profit style optimization
- Hedging intensity control
- Neural network risk prediction
- Multi-factor risk assessment

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import GradientBoostingRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications"""
    MINIMAL = auto()
    LOW = auto()
    MODERATE = auto()
    ELEVATED = auto()
    HIGH = auto()
    EXTREME = auto()
    CRITICAL = auto()


class HedgingMode(Enum):
    """Hedging intensity modes"""
    NONE = auto()
    LIGHT = auto()
    MODERATE = auto()
    AGGRESSIVE = auto()
    FULL = auto()


class TakeProfitStyle(Enum):
    """Take profit styles"""
    FIXED = auto()
    TRAILING = auto()
    SCALED = auto()
    ATR_BASED = auto()
    VOLATILITY_ADJUSTED = auto()
    MOMENTUM_BASED = auto()


@dataclass
class RiskState:
    """Current risk state"""
    timestamp: datetime
    
    # Overall risk
    risk_level: RiskLevel = RiskLevel.MODERATE
    risk_score: float = 0.5  # 0-1
    
    # Position parameters
    max_leverage: float = 1.0
    position_size_multiplier: float = 1.0
    
    # Stop loss
    stop_loss_width_bps: float = 100  # basis points
    stop_loss_style: str = "fixed"
    
    # Take profit
    take_profit_style: TakeProfitStyle = TakeProfitStyle.FIXED
    take_profit_multiplier: float = 2.0  # Risk:Reward
    
    # Hedging
    hedging_mode: HedgingMode = HedgingMode.NONE
    hedge_ratio: float = 0.0
    
    # Exposure limits
    max_single_position: float = 0.02  # 2% of capital
    max_sector_exposure: float = 0.10  # 10%
    max_correlation_exposure: float = 0.30  # 30%
    
    # Neural network outputs
    predicted_volatility: float = 0.0
    predicted_drawdown: float = 0.0
    predicted_var_95: float = 0.0


@dataclass
class RiskFactors:
    """Input factors for risk assessment"""
    # Market factors
    volatility: float = 0.0
    volatility_regime: str = "normal"
    trend_strength: float = 0.0
    market_regime: str = "normal"
    
    # Portfolio factors
    current_drawdown: float = 0.0
    portfolio_heat: float = 0.0  # % of capital at risk
    correlation_risk: float = 0.0
    concentration_risk: float = 0.0
    
    # Performance factors
    recent_win_rate: float = 0.5
    recent_profit_factor: float = 1.0
    sharpe_ratio: float = 0.0
    
    # External factors
    vix_level: float = 20.0
    news_sentiment: float = 0.0
    economic_calendar_risk: float = 0.0


class RiskNeuralNetwork(nn.Module):
    """Neural network for risk prediction"""
    
    def __init__(self, input_dim: int = 15, hidden_dim: int = 64):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 5)  # 5 outputs: risk_score, vol, drawdown, var, hedge_ratio
        )
        
    def forward(self, x):
        return self.network(x)


class RiskPredictor:
    """ML-based risk prediction"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.neural_net = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
        
        # Fallback model
        self.fallback_model = None
        
        if TORCH_AVAILABLE:
            self.neural_net = RiskNeuralNetwork()
        
    def train(self, X: np.ndarray, y: np.ndarray):
        """Train risk prediction model"""
        
        if self.scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        if TORCH_AVAILABLE and self.neural_net:
            # Train neural network
            X_tensor = torch.FloatTensor(X_scaled)
            y_tensor = torch.FloatTensor(y)
            
            optimizer = torch.optim.Adam(self.neural_net.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            for epoch in range(100):
                self.neural_net.train()
                optimizer.zero_grad()
                output = self.neural_net(X_tensor)
                loss = criterion(output, y_tensor)
                loss.backward()
                optimizer.step()
            
            self.is_trained = True
        
        elif SKLEARN_AVAILABLE:
            # Train gradient boosting as fallback
            self.fallback_model = GradientBoostingRegressor(n_estimators=50)
            self.fallback_model.fit(X_scaled, y[:, 0])  # Predict risk score
            self.is_trained = True
    
    def predict(self, factors: RiskFactors) -> Dict[str, float]:
        """Predict risk metrics"""
        
        # Convert factors to array
        X = self._factors_to_array(factors)
        
        if self.scaler:
            X_scaled = self.scaler.transform(X.reshape(1, -1))
        else:
            X_scaled = X.reshape(1, -1)
        
        if TORCH_AVAILABLE and self.neural_net and self.is_trained:
            self.neural_net.eval()
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X_scaled)
                output = self.neural_net(X_tensor).numpy()[0]
            
            return {
                'risk_score': float(np.clip(output[0], 0, 1)),
                'predicted_volatility': float(np.clip(output[1], 0, 1)),
                'predicted_drawdown': float(np.clip(output[2], 0, 1)),
                'predicted_var_95': float(np.clip(output[3], 0, 0.5)),
                'hedge_ratio': float(np.clip(output[4], 0, 1))
            }
        
        elif self.fallback_model and self.is_trained:
            risk_score = self.fallback_model.predict(X_scaled)[0]
            return {
                'risk_score': float(np.clip(risk_score, 0, 1)),
                'predicted_volatility': factors.volatility,
                'predicted_drawdown': factors.current_drawdown,
                'predicted_var_95': factors.volatility * 1.65,
                'hedge_ratio': 0.0
            }
        
        else:
            # Rule-based fallback
            return self._rule_based_prediction(factors)
    
    def _factors_to_array(self, factors: RiskFactors) -> np.ndarray:
        """Convert RiskFactors to numpy array"""
        return np.array([
            factors.volatility,
            1 if factors.volatility_regime == 'high' else 0,
            factors.trend_strength,
            1 if factors.market_regime == 'trending' else 0,
            factors.current_drawdown,
            factors.portfolio_heat,
            factors.correlation_risk,
            factors.concentration_risk,
            factors.recent_win_rate,
            factors.recent_profit_factor,
            factors.sharpe_ratio,
            factors.vix_level / 100,
            factors.news_sentiment,
            factors.economic_calendar_risk,
            0  # Padding
        ])
    
    def _rule_based_prediction(self, factors: RiskFactors) -> Dict[str, float]:
        """Rule-based risk prediction fallback"""
        
        # Calculate risk score from factors
        risk_score = 0.5
        
        # Volatility impact
        if factors.volatility > 0.03:
            risk_score += 0.2
        elif factors.volatility < 0.01:
            risk_score -= 0.1
        
        # Drawdown impact
        risk_score += factors.current_drawdown * 2
        
        # VIX impact
        if factors.vix_level > 30:
            risk_score += 0.15
        elif factors.vix_level > 40:
            risk_score += 0.3
        
        # Performance impact
        if factors.recent_win_rate < 0.4:
            risk_score += 0.1
        if factors.sharpe_ratio < 0:
            risk_score += 0.1
        
        risk_score = np.clip(risk_score, 0, 1)
        
        return {
            'risk_score': risk_score,
            'predicted_volatility': factors.volatility,
            'predicted_drawdown': factors.current_drawdown,
            'predicted_var_95': factors.volatility * 1.65,
            'hedge_ratio': min(risk_score, 0.5)
        }


class LeverageController:
    """Dynamic leverage adjustment"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_leverage = self.config.get('max_leverage', 3.0)
        self.min_leverage = self.config.get('min_leverage', 0.5)
        
    def calculate_leverage(
        self,
        risk_score: float,
        volatility: float,
        drawdown: float,
        win_rate: float
    ) -> float:
        """Calculate optimal leverage"""
        
        # Base leverage from risk score
        base_leverage = self.max_leverage * (1 - risk_score)
        
        # Volatility adjustment
        vol_factor = 1 / (1 + volatility * 10)
        
        # Drawdown adjustment
        dd_factor = 1 - drawdown * 2
        
        # Performance adjustment
        perf_factor = 0.5 + win_rate
        
        # Combined leverage
        leverage = base_leverage * vol_factor * dd_factor * perf_factor
        
        # Clip to bounds
        leverage = np.clip(leverage, self.min_leverage, self.max_leverage)
        
        return leverage


class PositionSizer:
    """Dynamic position sizing"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_risk_per_trade = self.config.get('base_risk_per_trade', 0.02)
        
    def calculate_position_size(
        self,
        capital: float,
        risk_score: float,
        volatility: float,
        stop_loss_pct: float,
        kelly_fraction: float = 0.5
    ) -> float:
        """Calculate optimal position size"""
        
        # Risk-adjusted base size
        risk_budget = capital * self.base_risk_per_trade * (1 - risk_score)
        
        # Volatility adjustment
        vol_adjusted = risk_budget / (volatility * 100 + 1)
        
        # Stop loss based sizing
        if stop_loss_pct > 0:
            sl_based = risk_budget / stop_loss_pct
        else:
            sl_based = vol_adjusted
        
        # Kelly criterion adjustment
        kelly_size = capital * kelly_fraction * 0.5  # Half Kelly
        
        # Take minimum of all methods
        position_size = min(vol_adjusted, sl_based, kelly_size)
        
        # Max position limit
        max_position = capital * 0.1  # 10% max
        position_size = min(position_size, max_position)
        
        return position_size
    
    def calculate_kelly_fraction(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """Calculate Kelly criterion fraction"""
        
        if avg_loss == 0:
            return 0
        
        win_loss_ratio = avg_win / abs(avg_loss)
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win rate, q = 1-p, b = win/loss ratio
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Use fractional Kelly (safer)
        kelly = max(0, kelly) * 0.5
        
        return kelly


class StopLossOptimizer:
    """Dynamic stop loss optimization"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_stop_bps = self.config.get('min_stop_bps', 20)
        self.max_stop_bps = self.config.get('max_stop_bps', 300)
        
    def calculate_stop_loss(
        self,
        volatility: float,
        atr: float,
        risk_score: float,
        market_regime: str
    ) -> Tuple[float, str]:
        """Calculate optimal stop loss width and style"""
        
        # ATR-based stop
        atr_stop = atr * 2.0
        
        # Volatility-based stop
        vol_stop = volatility * 100 * 1.5  # 1.5x daily vol in bps
        
        # Risk-adjusted stop
        risk_factor = 1 + risk_score  # Wider stops in high risk
        
        # Regime adjustment
        if market_regime == 'trending':
            regime_factor = 1.2  # Wider stops in trends
            style = 'trailing'
        elif market_regime == 'ranging':
            regime_factor = 0.8  # Tighter stops in ranges
            style = 'fixed'
        else:
            regime_factor = 1.0
            style = 'atr_based'
        
        # Combined stop
        stop_bps = max(atr_stop, vol_stop) * risk_factor * regime_factor
        
        # Clip to bounds
        stop_bps = np.clip(stop_bps, self.min_stop_bps, self.max_stop_bps)
        
        return stop_bps, style


class TakeProfitOptimizer:
    """Dynamic take profit optimization"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def calculate_take_profit(
        self,
        stop_loss_bps: float,
        volatility: float,
        trend_strength: float,
        momentum: float
    ) -> Tuple[TakeProfitStyle, float]:
        """Calculate optimal take profit style and multiplier"""
        
        # Base risk:reward from volatility
        if volatility > 0.03:
            base_rr = 1.5  # Lower R:R in high vol
        elif volatility < 0.01:
            base_rr = 3.0  # Higher R:R in low vol
        else:
            base_rr = 2.0
        
        # Trend adjustment
        if abs(trend_strength) > 0.5:
            style = TakeProfitStyle.TRAILING
            rr_multiplier = 1.5  # Let winners run
        elif abs(momentum) > 0.7:
            style = TakeProfitStyle.MOMENTUM_BASED
            rr_multiplier = 1.3
        else:
            style = TakeProfitStyle.SCALED
            rr_multiplier = 1.0
        
        final_rr = base_rr * rr_multiplier
        
        return style, final_rr


class HedgingController:
    """Dynamic hedging intensity control"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def calculate_hedge(
        self,
        risk_score: float,
        correlation_risk: float,
        drawdown: float,
        vix_level: float
    ) -> Tuple[HedgingMode, float]:
        """Calculate hedging mode and ratio"""
        
        # Determine hedging need
        hedge_score = (
            0.3 * risk_score +
            0.2 * correlation_risk +
            0.3 * drawdown * 5 +
            0.2 * (vix_level - 20) / 30
        )
        
        hedge_score = np.clip(hedge_score, 0, 1)
        
        # Determine mode
        if hedge_score < 0.2:
            mode = HedgingMode.NONE
            ratio = 0.0
        elif hedge_score < 0.4:
            mode = HedgingMode.LIGHT
            ratio = 0.2
        elif hedge_score < 0.6:
            mode = HedgingMode.MODERATE
            ratio = 0.4
        elif hedge_score < 0.8:
            mode = HedgingMode.AGGRESSIVE
            ratio = 0.6
        else:
            mode = HedgingMode.FULL
            ratio = 0.8
        
        return mode, ratio
    
    def get_hedge_instruments(
        self,
        portfolio_positions: List[Dict],
        mode: HedgingMode
    ) -> List[Dict]:
        """Get recommended hedge instruments"""
        
        hedges = []
        
        if mode == HedgingMode.NONE:
            return hedges
        
        # Calculate portfolio beta
        total_value = sum(p.get('value', 0) for p in portfolio_positions)
        
        if total_value > 0:
            # Recommend index hedge
            hedges.append({
                'instrument': 'SPY_PUT',
                'type': 'option',
                'ratio': 0.1 if mode == HedgingMode.LIGHT else 0.2,
                'reason': 'Portfolio beta hedge'
            })
        
        # Volatility hedge
        if mode in [HedgingMode.AGGRESSIVE, HedgingMode.FULL]:
            hedges.append({
                'instrument': 'VIX_CALL',
                'type': 'option',
                'ratio': 0.05,
                'reason': 'Volatility spike protection'
            })
        
        return hedges


class DynamicRiskMatrix:
    """
    Complete Dynamic Risk Neural Matrix.
    
    Real-time engine that adjusts:
    - Leverage
    - Position size
    - Stop-loss width
    - Take-profit style
    - Hedging intensity
    
    Uses neural networks and ML for prediction.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.risk_predictor = RiskPredictor(config)
        self.leverage_controller = LeverageController(config)
        self.position_sizer = PositionSizer(config)
        self.stop_optimizer = StopLossOptimizer(config)
        self.tp_optimizer = TakeProfitOptimizer(config)
        self.hedge_controller = HedgingController(config)
        
        # State
        self.current_state: Optional[RiskState] = None
        self.state_history: List[RiskState] = []
        self.max_history = 1000
        
        # Risk limits
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.05)
        self.max_daily_loss = self.config.get('max_daily_loss', 0.03)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)
        
        logger.info("DynamicRiskMatrix initialized")
    
    def update(
        self,
        factors: RiskFactors,
        capital: float,
        current_positions: List[Dict] = None
    ) -> RiskState:
        """Update risk state based on current factors"""
        
        timestamp = datetime.now()
        
        # Get ML predictions
        predictions = self.risk_predictor.predict(factors)
        risk_score = predictions['risk_score']
        
        # Determine risk level
        risk_level = self._score_to_level(risk_score)
        
        # Calculate leverage
        leverage = self.leverage_controller.calculate_leverage(
            risk_score,
            factors.volatility,
            factors.current_drawdown,
            factors.recent_win_rate
        )
        
        # Calculate position size multiplier
        kelly = self.position_sizer.calculate_kelly_fraction(
            factors.recent_win_rate,
            factors.recent_profit_factor,
            1.0  # Normalized loss
        )
        position_mult = 1 - risk_score + kelly * 0.5
        position_mult = np.clip(position_mult, 0.2, 1.5)
        
        # Calculate stop loss
        atr = factors.volatility * 100  # Approximate ATR in bps
        stop_bps, stop_style = self.stop_optimizer.calculate_stop_loss(
            factors.volatility,
            atr,
            risk_score,
            factors.market_regime
        )
        
        # Calculate take profit
        tp_style, tp_mult = self.tp_optimizer.calculate_take_profit(
            stop_bps,
            factors.volatility,
            factors.trend_strength,
            0.0  # Momentum placeholder
        )
        
        # Calculate hedging
        hedge_mode, hedge_ratio = self.hedge_controller.calculate_hedge(
            risk_score,
            factors.correlation_risk,
            factors.current_drawdown,
            factors.vix_level
        )
        
        # Create state
        state = RiskState(
            timestamp=timestamp,
            risk_level=risk_level,
            risk_score=risk_score,
            max_leverage=leverage,
            position_size_multiplier=position_mult,
            stop_loss_width_bps=stop_bps,
            stop_loss_style=stop_style,
            take_profit_style=tp_style,
            take_profit_multiplier=tp_mult,
            hedging_mode=hedge_mode,
            hedge_ratio=hedge_ratio,
            predicted_volatility=predictions['predicted_volatility'],
            predicted_drawdown=predictions['predicted_drawdown'],
            predicted_var_95=predictions['predicted_var_95']
        )
        
        # Apply emergency overrides
        state = self._apply_emergency_overrides(state, factors)
        
        # Update history
        self.state_history.append(state)
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
        
        self.current_state = state
        
        return state
    
    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert risk score to level"""
        
        if score < 0.15:
            return RiskLevel.MINIMAL
        elif score < 0.3:
            return RiskLevel.LOW
        elif score < 0.45:
            return RiskLevel.MODERATE
        elif score < 0.6:
            return RiskLevel.ELEVATED
        elif score < 0.75:
            return RiskLevel.HIGH
        elif score < 0.9:
            return RiskLevel.EXTREME
        else:
            return RiskLevel.CRITICAL
    
    def _apply_emergency_overrides(
        self,
        state: RiskState,
        factors: RiskFactors
    ) -> RiskState:
        """Apply emergency risk overrides"""
        
        # Drawdown override
        if factors.current_drawdown > self.max_drawdown:
            state.risk_level = RiskLevel.CRITICAL
            state.max_leverage = 0.5
            state.position_size_multiplier = 0.25
            state.hedging_mode = HedgingMode.FULL
            state.hedge_ratio = 0.8
        
        # VIX spike override
        if factors.vix_level > 40:
            state.risk_level = max(state.risk_level, RiskLevel.HIGH)
            state.max_leverage = min(state.max_leverage, 1.0)
            state.stop_loss_width_bps *= 1.5
        
        # Extreme volatility override
        if factors.volatility > 0.05:
            state.risk_level = max(state.risk_level, RiskLevel.EXTREME)
            state.max_leverage = min(state.max_leverage, 0.5)
            state.position_size_multiplier *= 0.5
        
        return state
    
    def get_position_parameters(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        capital: float
    ) -> Dict[str, Any]:
        """Get complete position parameters"""
        
        if self.current_state is None:
            return self._default_parameters(capital)
        
        state = self.current_state
        
        # Calculate position size
        base_size = self.position_sizer.calculate_position_size(
            capital,
            state.risk_score,
            state.predicted_volatility,
            state.stop_loss_width_bps / 10000,
            0.5
        )
        
        adjusted_size = base_size * state.position_size_multiplier
        
        # Calculate stop loss price
        stop_distance = entry_price * (state.stop_loss_width_bps / 10000)
        if side == 'buy':
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance
        
        # Calculate take profit price
        tp_distance = stop_distance * state.take_profit_multiplier
        if side == 'buy':
            take_profit = entry_price + tp_distance
        else:
            take_profit = entry_price - tp_distance
        
        return {
            'position_size': adjusted_size,
            'max_leverage': state.max_leverage,
            'stop_loss': stop_loss,
            'stop_loss_style': state.stop_loss_style,
            'take_profit': take_profit,
            'take_profit_style': state.take_profit_style.name,
            'risk_reward_ratio': state.take_profit_multiplier,
            'hedge_ratio': state.hedge_ratio,
            'risk_level': state.risk_level.name,
            'risk_score': state.risk_score
        }
    
    def _default_parameters(self, capital: float) -> Dict[str, Any]:
        """Default parameters when no state available"""
        return {
            'position_size': capital * 0.02,
            'max_leverage': 1.0,
            'stop_loss': None,
            'stop_loss_style': 'fixed',
            'take_profit': None,
            'take_profit_style': 'FIXED',
            'risk_reward_ratio': 2.0,
            'hedge_ratio': 0.0,
            'risk_level': 'MODERATE',
            'risk_score': 0.5
        }
    
    def should_reduce_exposure(self) -> Tuple[bool, str, float]:
        """Check if exposure should be reduced"""
        
        if self.current_state is None:
            return False, "", 0.0
        
        state = self.current_state
        
        if state.risk_level == RiskLevel.CRITICAL:
            return True, "Critical risk level", 0.75
        
        if state.risk_level == RiskLevel.EXTREME:
            return True, "Extreme risk level", 0.5
        
        if state.predicted_drawdown > 0.1:
            return True, "High predicted drawdown", 0.3
        
        return False, "", 0.0
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Get comprehensive risk report"""
        
        if self.current_state is None:
            return {'status': 'No state available'}
        
        state = self.current_state
        
        return {
            'timestamp': state.timestamp.isoformat(),
            'risk_level': state.risk_level.name,
            'risk_score': state.risk_score,
            'parameters': {
                'max_leverage': state.max_leverage,
                'position_multiplier': state.position_size_multiplier,
                'stop_loss_bps': state.stop_loss_width_bps,
                'take_profit_rr': state.take_profit_multiplier
            },
            'hedging': {
                'mode': state.hedging_mode.name,
                'ratio': state.hedge_ratio
            },
            'predictions': {
                'volatility': state.predicted_volatility,
                'drawdown': state.predicted_drawdown,
                'var_95': state.predicted_var_95
            },
            'limits': {
                'max_single_position': state.max_single_position,
                'max_sector_exposure': state.max_sector_exposure,
                'max_correlation_exposure': state.max_correlation_exposure
            }
        }


# Factory function
def create_risk_matrix(config: Optional[Dict] = None) -> DynamicRiskMatrix:
    """Create and return a DynamicRiskMatrix instance"""
    return DynamicRiskMatrix(config)
