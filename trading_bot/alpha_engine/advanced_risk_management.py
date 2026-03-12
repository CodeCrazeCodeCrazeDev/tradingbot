"""
Advanced Risk Management Module
================================

Comprehensive ML-based risk management:
- HMM Volatility Regime Detection (4 states)
- Dynamic Position Sizing with ML Kelly Criterion
- Correlation-Based Portfolio Hedging
- Tail Risk Protection (Convexity Strategies)
- Real-time Risk Monitoring
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import math

logger = logging.getLogger(__name__)

# Try importing ML libraries
try:
    from hmmlearn import hmm
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False

try:
    from sklearn.covariance import LedoitWolf
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class VolatilityRegime(Enum):
    """Volatility regime states"""
    LOW_VOL_TRENDING = "low_vol_trending"  # Best for DC strategy
    LOW_VOL_RANGING = "low_vol_ranging"  # Moderate for DC
    HIGH_VOL_TRENDING = "high_vol_trending"  # Adjust thresholds
    HIGH_VOL_RANGING = "high_vol_ranging"  # Reduce positions


class RiskLevel(Enum):
    """Risk levels"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class RegimeState:
    """Current regime state"""
    regime: VolatilityRegime
    probability: float
    duration_days: int
    transition_probability: Dict[str, float]
    
    # Trading adjustments
    position_size_multiplier: float
    dc_threshold_multiplier: float
    stop_loss_multiplier: float


@dataclass
class PositionRecommendation:
    """Position sizing recommendation"""
    symbol: str
    base_size: float
    adjusted_size: float
    kelly_fraction: float
    max_allowed: float
    risk_per_trade: float
    reason: str
    adjustments: Dict[str, float] = field(default_factory=dict)


@dataclass
class HedgeRecommendation:
    """Hedge recommendation"""
    primary_symbol: str
    hedge_symbol: str
    hedge_ratio: float
    correlation: float
    hedge_size: float
    expected_var_reduction: float
    reason: str


@dataclass
class TailRiskMetrics:
    """Tail risk metrics"""
    var_95: float
    var_99: float
    cvar_95: float  # Expected Shortfall
    cvar_99: float
    max_drawdown: float
    tail_ratio: float  # 95th percentile gain / 5th percentile loss


class HMMRegimeDetector:
    """
    Hidden Markov Model for Volatility Regime Detection
    
    4 States:
    1. Low Volatility, Trending (Best for DC)
    2. Low Volatility, Ranging (Moderate for DC)
    3. High Volatility, Trending (Adjust thresholds)
    4. High Volatility, Ranging (Reduce positions)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # HMM parameters
        self.n_states = 4
        self.model = None
        
        # State mappings
        self.state_to_regime = {
            0: VolatilityRegime.LOW_VOL_TRENDING,
            1: VolatilityRegime.LOW_VOL_RANGING,
            2: VolatilityRegime.HIGH_VOL_TRENDING,
            3: VolatilityRegime.HIGH_VOL_RANGING,
        }
        
        # Trading adjustments per regime
        self.regime_adjustments = {
            VolatilityRegime.LOW_VOL_TRENDING: {
                'position_multiplier': 1.2,
                'threshold_multiplier': 0.9,
                'stop_multiplier': 1.0,
            },
            VolatilityRegime.LOW_VOL_RANGING: {
                'position_multiplier': 1.0,
                'threshold_multiplier': 1.0,
                'stop_multiplier': 1.0,
            },
            VolatilityRegime.HIGH_VOL_TRENDING: {
                'position_multiplier': 0.8,
                'threshold_multiplier': 1.5,
                'stop_multiplier': 0.8,
            },
            VolatilityRegime.HIGH_VOL_RANGING: {
                'position_multiplier': 0.5,
                'threshold_multiplier': 1.5,
                'stop_multiplier': 0.75,
            },
        }
        
        # Data history
        self.returns_history: deque = deque(maxlen=1000)
        self.volatility_history: deque = deque(maxlen=1000)
        
        # Current state
        self.current_state = 0
        self.state_history: deque = deque(maxlen=100)
        
        self.is_fitted = False
    
    def _prepare_features(self) -> np.ndarray:
        """Prepare features for HMM"""
        if len(self.returns_history) < 50:
            return None
        
        returns = np.array(list(self.returns_history))
        
        # Calculate features
        # 1. Rolling volatility (20-day)
        vol_20 = pd.Series(returns).rolling(20).std().values
        
        # 2. Rolling volatility (5-day)
        vol_5 = pd.Series(returns).rolling(5).std().values
        
        # 3. Trend strength (absolute return over 20 days)
        trend = pd.Series(returns).rolling(20).sum().abs().values
        
        # Combine features
        features = np.column_stack([
            vol_20[19:],
            vol_5[19:],
            trend[19:],
        ])
        
        # Remove NaN
        features = features[~np.isnan(features).any(axis=1)]
        
        return features
    
    def fit(self):
        """Fit HMM model"""
        features = self._prepare_features()
        
        if features is None or len(features) < 100:
            logger.warning("Insufficient data for HMM fitting")
            return
        
        if HMM_AVAILABLE:
            try:
                self.model = hmm.GaussianHMM(
                    n_components=self.n_states,
                    covariance_type='full',
                    n_iter=100,
                    random_state=42,
                )
                self.model.fit(features)
                self.is_fitted = True
                logger.info("HMM regime detector fitted successfully")
            except Exception as e:
                logger.error(f"HMM fitting failed: {e}")
                self.is_fitted = False
        else:
            # Use simple rule-based detection
            self.is_fitted = True
    
    def update(self, returns: float):
        """Update with new return data"""
        self.returns_history.append(returns)
        
        # Calculate current volatility
        if len(self.returns_history) >= 20:
            recent_vol = np.std(list(self.returns_history)[-20:])
            self.volatility_history.append(recent_vol)
        
        # Refit periodically
        if len(self.returns_history) % 100 == 0:
            self.fit()
    
    def detect_regime(self) -> RegimeState:
        """Detect current regime"""
        if not self.is_fitted:
            self.fit()
        
        if HMM_AVAILABLE and self.model is not None:
            features = self._prepare_features()
            if features is not None and len(features) > 0:
                try:
                    # Get most likely state
                    states = self.model.predict(features)
                    self.current_state = states[-1]
                    
                    # Get state probabilities
                    probs = self.model.predict_proba(features)[-1]
                    
                    # Get transition matrix
                    trans_probs = {
                        self.state_to_regime[i].value: float(self.model.transmat_[self.current_state, i])
                        for i in range(self.n_states)
                    }
                except Exception as e:
                    logger.error(f"HMM prediction failed: {e}")
                    return self._fallback_detection()
            else:
                return self._fallback_detection()
        else:
            return self._fallback_detection()
        
        regime = self.state_to_regime[self.current_state]
        adjustments = self.regime_adjustments[regime]
        
        # Calculate duration
        self.state_history.append(self.current_state)
        duration = 1
        for s in reversed(list(self.state_history)[:-1]):
            if s == self.current_state:
                duration += 1
            else:
                break
        
        return RegimeState(
            regime=regime,
            probability=float(probs[self.current_state]) if 'probs' in dir() else 0.8,
            duration_days=duration,
            transition_probability=trans_probs if 'trans_probs' in dir() else {},
            position_size_multiplier=adjustments['position_multiplier'],
            dc_threshold_multiplier=adjustments['threshold_multiplier'],
            stop_loss_multiplier=adjustments['stop_multiplier'],
        )
    
    def _fallback_detection(self) -> RegimeState:
        """Fallback rule-based regime detection"""
        if len(self.volatility_history) < 20:
            regime = VolatilityRegime.LOW_VOL_RANGING
        else:
            recent_vol = list(self.volatility_history)[-20:]
            avg_vol = np.mean(recent_vol)
            
            # Determine volatility level
            is_high_vol = avg_vol > 0.02  # 2% daily vol threshold
            
            # Determine trend
            if len(self.returns_history) >= 20:
                recent_returns = list(self.returns_history)[-20:]
                trend_strength = abs(sum(recent_returns))
                is_trending = trend_strength > avg_vol * 10
            else:
                is_trending = False
            
            if is_high_vol and is_trending:
                regime = VolatilityRegime.HIGH_VOL_TRENDING
            elif is_high_vol:
                regime = VolatilityRegime.HIGH_VOL_RANGING
            elif is_trending:
                regime = VolatilityRegime.LOW_VOL_TRENDING
            else:
                regime = VolatilityRegime.LOW_VOL_RANGING
        
        adjustments = self.regime_adjustments[regime]
        
        return RegimeState(
            regime=regime,
            probability=0.7,
            duration_days=1,
            transition_probability={},
            position_size_multiplier=adjustments['position_multiplier'],
            dc_threshold_multiplier=adjustments['threshold_multiplier'],
            stop_loss_multiplier=adjustments['stop_multiplier'],
        )


class MLKellyCriterion:
    """
    ML-Enhanced Kelly Criterion for Position Sizing
    
    f* = (p × b - q) / b
    
    Where:
    - p = ML-predicted win probability
    - q = 1 - p
    - b = average win / average loss ratio
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Kelly parameters
        self.kelly_fraction = self.config.get('kelly_fraction', 0.25)  # Use 1/4 Kelly
        self.max_position_pct = self.config.get('max_position_pct', 0.05)  # 5% max
        self.min_confidence = self.config.get('min_confidence', 0.6)
        
        # Historical data for payoff ratio
        self.trade_history: deque = deque(maxlen=500)
        
        # Cached metrics
        self.avg_win = 0.02
        self.avg_loss = 0.01
        self.win_rate = 0.55
    
    def update_history(self, pnl: float, is_win: bool):
        """Update trade history"""
        self.trade_history.append({
            'pnl': pnl,
            'is_win': is_win,
        })
        
        # Update metrics
        self._update_metrics()
    
    def _update_metrics(self):
        """Update win/loss metrics"""
        if len(self.trade_history) < 20:
            return
        
        trades = list(self.trade_history)
        wins = [t['pnl'] for t in trades if t['is_win']]
        losses = [abs(t['pnl']) for t in trades if not t['is_win']]
        
        if wins:
            self.avg_win = np.mean(wins)
        if losses:
            self.avg_loss = np.mean(losses)
        
        self.win_rate = len(wins) / len(trades) if trades else 0.5
    
    def calculate_kelly(self, win_probability: float, confidence: float) -> float:
        """
        Calculate Kelly fraction
        
        Args:
            win_probability: ML-predicted win probability
            confidence: Model confidence
            
        Returns:
            Kelly fraction (0 to 1)
        """
        if confidence < self.min_confidence:
            return 0
        
        # Adjust win probability by confidence
        adjusted_prob = 0.5 + (win_probability - 0.5) * confidence
        
        # Calculate payoff ratio
        if self.avg_loss > 0:
            payoff_ratio = self.avg_win / self.avg_loss
        else:
            payoff_ratio = 2.0  # Default 2:1
        
        # Kelly formula
        p = adjusted_prob
        q = 1 - p
        b = payoff_ratio
        
        if b <= 0:
            return 0
        
        kelly = (p * b - q) / b
        
        # Apply fractional Kelly
        kelly *= self.kelly_fraction
        
        # Ensure non-negative
        kelly = max(0, kelly)
        
        return kelly
    
    def get_position_size(self, capital: float, win_probability: float,
                         confidence: float, regime_multiplier: float = 1.0) -> PositionRecommendation:
        """
        Get recommended position size
        
        Args:
            capital: Available capital
            win_probability: ML-predicted win probability
            confidence: Model confidence
            regime_multiplier: Regime-based adjustment
            
        Returns:
            PositionRecommendation
        """
        kelly = self.calculate_kelly(win_probability, confidence)
        
        # Base size from Kelly
        base_size = kelly * capital
        
        # Apply regime adjustment
        adjusted_size = base_size * regime_multiplier
        
        # Apply max position constraint
        max_size = capital * self.max_position_pct
        final_size = min(adjusted_size, max_size)
        
        # Calculate risk per trade
        risk_per_trade = final_size * self.avg_loss if self.avg_loss > 0 else final_size * 0.02
        
        return PositionRecommendation(
            symbol='',
            base_size=base_size,
            adjusted_size=final_size,
            kelly_fraction=kelly,
            max_allowed=max_size,
            risk_per_trade=risk_per_trade,
            reason=f"Kelly={kelly:.2%}, Regime mult={regime_multiplier:.2f}",
            adjustments={
                'kelly': kelly,
                'regime': regime_multiplier,
                'confidence': confidence,
            },
        )


class CorrelationHedger:
    """
    Correlation-Based Portfolio Hedging
    
    Automatically identifies and recommends hedges based on:
    - Rolling correlations
    - Negative correlation instruments
    - VaR reduction potential
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Correlation parameters
        self.correlation_window = self.config.get('correlation_window', 30)
        self.hedge_threshold = self.config.get('hedge_threshold', -0.5)
        
        # Price history per symbol
        self.price_history: Dict[str, deque] = {}
        
        # Correlation matrix
        self.correlation_matrix: Optional[pd.DataFrame] = None
        
        # Hedge universe
        self.hedge_universe = self.config.get('hedge_universe', [
            'SPY', 'TLT', 'GLD', 'VXX', 'UUP',
        ])
    
    def update_prices(self, symbol: str, price: float):
        """Update price history"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.correlation_window * 2)
        
        self.price_history[symbol].append(price)
    
    def calculate_correlations(self) -> pd.DataFrame:
        """Calculate correlation matrix"""
        # Need at least correlation_window data points
        valid_symbols = [
            s for s, h in self.price_history.items()
            if len(h) >= self.correlation_window
        ]
        
        if len(valid_symbols) < 2:
            return pd.DataFrame()
        
        # Calculate returns
        returns_dict = {}
        for symbol in valid_symbols:
            prices = list(self.price_history[symbol])[-self.correlation_window:]
            returns = np.diff(prices) / prices[:-1]
            returns_dict[symbol] = returns
        
        # Create DataFrame
        returns_df = pd.DataFrame(returns_dict)
        
        # Calculate correlation
        self.correlation_matrix = returns_df.corr()
        
        return self.correlation_matrix
    
    def find_hedge(self, symbol: str, position_value: float) -> Optional[HedgeRecommendation]:
        """
        Find optimal hedge for a position
        
        Args:
            symbol: Symbol to hedge
            position_value: Value of position to hedge
            
        Returns:
            HedgeRecommendation or None
        """
        if self.correlation_matrix is None or self.correlation_matrix.empty:
            self.calculate_correlations()
        
        if self.correlation_matrix is None or symbol not in self.correlation_matrix.columns:
            return None
        
        # Find most negatively correlated instrument
        correlations = self.correlation_matrix[symbol]
        
        best_hedge = None
        best_correlation = 0
        
        for hedge_symbol in self.hedge_universe:
            if hedge_symbol in correlations and hedge_symbol != symbol:
                corr = correlations[hedge_symbol]
                if corr < self.hedge_threshold and corr < best_correlation:
                    best_correlation = corr
                    best_hedge = hedge_symbol
        
        if best_hedge is None:
            return None
        
        # Calculate hedge ratio (beta-adjusted)
        hedge_ratio = abs(best_correlation)
        hedge_size = position_value * hedge_ratio
        
        # Estimate VaR reduction
        var_reduction = (1 - abs(best_correlation)) * 0.3  # Simplified estimate
        
        return HedgeRecommendation(
            primary_symbol=symbol,
            hedge_symbol=best_hedge,
            hedge_ratio=hedge_ratio,
            correlation=best_correlation,
            hedge_size=hedge_size,
            expected_var_reduction=var_reduction,
            reason=f"Correlation: {best_correlation:.2f}, hedge ratio: {hedge_ratio:.2f}",
        )


class TailRiskProtector:
    """
    Tail Risk Protection using Convexity Strategies
    
    Strategies:
    1. Long tail options (OTM puts)
    2. Volatility clustering trades
    3. Crisis alpha positions
    4. Barbell strategy
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Protection parameters
        self.hedge_budget_pct = self.config.get('hedge_budget_pct', 0.01)  # 1% annual
        self.var_threshold = self.config.get('var_threshold', 0.03)  # 3% VaR trigger
        
        # Returns history
        self.returns_history: deque = deque(maxlen=500)
        
        # Current protection level
        self.protection_active = False
        self.protection_positions: List[Dict[str, Any]] = []
    
    def update(self, daily_return: float):
        """Update with daily return"""
        self.returns_history.append(daily_return)
    
    def calculate_tail_metrics(self) -> TailRiskMetrics:
        """Calculate tail risk metrics"""
        if len(self.returns_history) < 50:
            return TailRiskMetrics(
                var_95=0.02,
                var_99=0.03,
                cvar_95=0.025,
                cvar_99=0.04,
                max_drawdown=0.1,
                tail_ratio=1.0,
            )
        
        returns = np.array(list(self.returns_history))
        
        # VaR
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # CVaR (Expected Shortfall)
        cvar_95 = returns[returns <= var_95].mean() if any(returns <= var_95) else var_95
        cvar_99 = returns[returns <= var_99].mean() if any(returns <= var_99) else var_99
        
        # Max Drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = running_max - cumulative
        max_dd = np.max(drawdowns)
        
        # Tail Ratio
        gain_95 = np.percentile(returns, 95)
        loss_5 = abs(np.percentile(returns, 5))
        tail_ratio = gain_95 / loss_5 if loss_5 > 0 else 1.0
        
        return TailRiskMetrics(
            var_95=abs(var_95),
            var_99=abs(var_99),
            cvar_95=abs(cvar_95),
            cvar_99=abs(cvar_99),
            max_drawdown=max_dd,
            tail_ratio=tail_ratio,
        )
    
    def get_protection_recommendation(self, portfolio_value: float,
                                      current_vix: float = 20) -> Dict[str, Any]:
        """
        Get tail risk protection recommendation
        
        Args:
            portfolio_value: Current portfolio value
            current_vix: Current VIX level
            
        Returns:
            Protection recommendation
        """
        metrics = self.calculate_tail_metrics()
        
        # Determine protection level needed
        if metrics.var_99 > self.var_threshold or current_vix > 30:
            protection_level = 'high'
            budget_multiplier = 1.5
        elif metrics.var_95 > self.var_threshold * 0.7 or current_vix > 25:
            protection_level = 'moderate'
            budget_multiplier = 1.0
        else:
            protection_level = 'low'
            budget_multiplier = 0.5
        
        # Calculate hedge budget
        hedge_budget = portfolio_value * self.hedge_budget_pct * budget_multiplier
        
        # Recommend protection positions
        recommendations = []
        
        # 1. OTM Puts (40% of budget)
        recommendations.append({
            'type': 'otm_puts',
            'allocation': hedge_budget * 0.4,
            'description': 'Far OTM puts for crash protection',
            'expected_payoff': '10-50x in crash scenario',
        })
        
        # 2. VIX Calls (30% of budget)
        recommendations.append({
            'type': 'vix_calls',
            'allocation': hedge_budget * 0.3,
            'description': 'VIX calls for volatility spike protection',
            'expected_payoff': '3-10x in vol spike',
        })
        
        # 3. Gold (20% of budget)
        recommendations.append({
            'type': 'gold',
            'allocation': hedge_budget * 0.2,
            'description': 'Gold for crisis alpha',
            'expected_payoff': 'Safe haven appreciation',
        })
        
        # 4. Cash buffer (10% of budget)
        recommendations.append({
            'type': 'cash',
            'allocation': hedge_budget * 0.1,
            'description': 'Cash buffer for opportunities',
            'expected_payoff': 'Dry powder for dips',
        })
        
        return {
            'protection_level': protection_level,
            'total_budget': hedge_budget,
            'metrics': {
                'var_95': metrics.var_95,
                'var_99': metrics.var_99,
                'cvar_95': metrics.cvar_95,
                'max_drawdown': metrics.max_drawdown,
                'tail_ratio': metrics.tail_ratio,
            },
            'recommendations': recommendations,
        }


class AdvancedRiskManager:
    """
    Comprehensive Risk Manager
    
    Integrates all risk management components:
    - HMM Regime Detection
    - ML Kelly Position Sizing
    - Correlation Hedging
    - Tail Risk Protection
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.regime_detector = HMMRegimeDetector(config.get('regime', {}))
        self.kelly = MLKellyCriterion(config.get('kelly', {}))
        self.hedger = CorrelationHedger(config.get('hedger', {}))
        self.tail_protector = TailRiskProtector(config.get('tail', {}))
        
        # Risk limits
        self.max_daily_loss = self.config.get('max_daily_loss', 0.03)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)
        self.max_position_pct = self.config.get('max_position_pct', 0.05)
        self.max_correlation = self.config.get('max_correlation', 0.7)
        
        # Current state
        self.current_equity = 0
        self.peak_equity = 0
        self.daily_pnl = 0
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        # Risk metrics history
        self.risk_history: deque = deque(maxlen=100)
    
    def update_equity(self, equity: float):
        """Update current equity"""
        self.current_equity = equity
        self.peak_equity = max(self.peak_equity, equity)
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl = pnl
        
        # Update components
        daily_return = pnl / self.current_equity if self.current_equity > 0 else 0
        self.regime_detector.update(daily_return)
        self.tail_protector.update(daily_return)
    
    def check_risk_limits(self) -> Dict[str, Any]:
        """
        Check all risk limits
        
        Returns:
            Risk status with any breaches
        """
        breaches = []
        
        # Daily loss limit
        if self.current_equity > 0:
            daily_loss_pct = -self.daily_pnl / self.current_equity
            if daily_loss_pct > self.max_daily_loss:
                breaches.append({
                    'type': 'daily_loss',
                    'limit': self.max_daily_loss,
                    'actual': daily_loss_pct,
                    'severity': 'critical',
                })
        
        # Drawdown limit
        if self.peak_equity > 0:
            drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
            if drawdown > self.max_drawdown:
                breaches.append({
                    'type': 'drawdown',
                    'limit': self.max_drawdown,
                    'actual': drawdown,
                    'severity': 'critical',
                })
        
        # Position concentration
        total_exposure = sum(p.get('value', 0) for p in self.positions.values())
        if self.current_equity > 0:
            exposure_pct = total_exposure / self.current_equity
            if exposure_pct > 1.0:  # Over 100% exposure
                breaches.append({
                    'type': 'exposure',
                    'limit': 1.0,
                    'actual': exposure_pct,
                    'severity': 'warning',
                })
        
        should_trade = len([b for b in breaches if b['severity'] == 'critical']) == 0
        
        return {
            'should_trade': should_trade,
            'breaches': breaches,
            'daily_pnl_pct': self.daily_pnl / self.current_equity if self.current_equity > 0 else 0,
            'current_drawdown': (self.peak_equity - self.current_equity) / self.peak_equity if self.peak_equity > 0 else 0,
        }
    
    def get_position_recommendation(self, symbol: str,
                                   signal: Dict[str, Any]) -> PositionRecommendation:
        """
        Get position sizing recommendation
        
        Args:
            symbol: Trading symbol
            signal: Signal with win_prob and confidence
            
        Returns:
            PositionRecommendation
        """
        # Get regime
        regime = self.regime_detector.detect_regime()
        
        # Get Kelly-based size
        recommendation = self.kelly.get_position_size(
            capital=self.current_equity,
            win_probability=signal.get('win_prob', 0.5),
            confidence=signal.get('confidence', 0.5),
            regime_multiplier=regime.position_size_multiplier,
        )
        
        recommendation.symbol = symbol
        
        # Check risk limits
        risk_status = self.check_risk_limits()
        if not risk_status['should_trade']:
            recommendation.adjusted_size = 0
            recommendation.reason = f"Risk limits breached: {risk_status['breaches']}"
        
        return recommendation
    
    def get_hedge_recommendation(self, symbol: str,
                                position_value: float) -> Optional[HedgeRecommendation]:
        """Get hedge recommendation for position"""
        return self.hedger.find_hedge(symbol, position_value)
    
    def get_tail_protection(self) -> Dict[str, Any]:
        """Get tail risk protection recommendation"""
        return self.tail_protector.get_protection_recommendation(
            self.current_equity
        )
    
    def get_current_regime(self) -> RegimeState:
        """Get current market regime"""
        return self.regime_detector.detect_regime()
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get comprehensive risk status"""
        regime = self.regime_detector.detect_regime()
        tail_metrics = self.tail_protector.calculate_tail_metrics()
        risk_check = self.check_risk_limits()
        
        return {
            'regime': regime.regime.value,
            'regime_probability': regime.probability,
            'position_multiplier': regime.position_size_multiplier,
            'var_95': tail_metrics.var_95,
            'var_99': tail_metrics.var_99,
            'max_drawdown': tail_metrics.max_drawdown,
            'tail_ratio': tail_metrics.tail_ratio,
            'should_trade': risk_check['should_trade'],
            'breaches': risk_check['breaches'],
            'current_drawdown': risk_check['current_drawdown'],
        }
