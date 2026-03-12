"""
Advanced Risk Management Module
================================

ML-based risk management with:
- Hidden Markov Model volatility regime detection
- Dynamic position sizing with Kelly Criterion
- Correlation-based portfolio hedging
- Tail risk protection (convexity strategies)
- VaR and CVaR calculations
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

logger = logging.getLogger(__name__)

try:
    from hmmlearn import hmm
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False
    logger.warning("hmmlearn not available. Using simplified regime detection.")

try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class VolatilityRegime(Enum):
    """Volatility regime states"""
    LOW_VOL_TRENDING = "low_vol_trending"
    LOW_VOL_RANGING = "low_vol_ranging"
    HIGH_VOL_TRENDING = "high_vol_trending"
    HIGH_VOL_RANGING = "high_vol_ranging"


class RiskLevel(Enum):
    """Risk level classifications"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    timestamp: datetime
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    cvar_95: float  # Conditional VaR 95%
    cvar_99: float  # Conditional VaR 99%
    max_drawdown: float
    current_drawdown: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    beta: float
    correlation_risk: float
    concentration_risk: float
    liquidity_risk: float
    regime: VolatilityRegime
    risk_level: RiskLevel


@dataclass
class PositionSizeRecommendation:
    """Position sizing recommendation"""
    symbol: str
    base_size: float
    adjusted_size: float
    kelly_fraction: float
    risk_adjustment: float
    regime_adjustment: float
    correlation_adjustment: float
    max_allowed: float
    reason: str


class VolatilityRegimeDetector:
    """
    Hidden Markov Model for volatility regime detection
    
    States:
    - Low Volatility, Trending (Best for DC strategy)
    - Low Volatility, Ranging (Moderate for DC)
    - High Volatility, Trending (Adjust thresholds)
    - High Volatility, Ranging (Reduce position sizes)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.n_states = 4
        
        # Initialize HMM
        if HMM_AVAILABLE:
            self.model = hmm.GaussianHMM(
                n_components=self.n_states,
                covariance_type="full",
                n_iter=100,
                random_state=42
            )
            self.is_fitted = False
        else:
            self.model = None
            self.is_fitted = False
        
        # State mapping
        self.state_mapping = {
            0: VolatilityRegime.LOW_VOL_TRENDING,
            1: VolatilityRegime.LOW_VOL_RANGING,
            2: VolatilityRegime.HIGH_VOL_TRENDING,
            3: VolatilityRegime.HIGH_VOL_RANGING,
        }
        
        # Feature history
        self.feature_history: deque = deque(maxlen=1000)
        
        # Current regime
        self.current_regime = VolatilityRegime.LOW_VOL_RANGING
        self.regime_probabilities: Dict[VolatilityRegime, float] = {}
        
    def extract_features(self, returns: np.ndarray, 
                        lookback: int = 20) -> np.ndarray:
        """Extract features for regime detection"""
        if len(returns) < lookback:
            return np.array([[0, 0, 0]])
        
        # Volatility (realized)
        volatility = np.std(returns[-lookback:]) * np.sqrt(252)
        
        # Trend strength (absolute mean return)
        trend = abs(np.mean(returns[-lookback:])) * 252
        
        # Autocorrelation (trending vs mean-reverting)
        if len(returns) >= lookback + 1:
            autocorr = np.corrcoef(returns[-lookback:-1], returns[-lookback+1:])[0, 1]
        else:
            autocorr = 0
        
        return np.array([[volatility, trend, autocorr]])
    
    def fit(self, returns: np.ndarray):
        """Fit HMM on historical returns"""
        if not HMM_AVAILABLE or self.model is None:
            logger.warning("HMM not available, using rule-based regime detection")
            return
        
        # Extract features for all periods
        features = []
        for i in range(20, len(returns)):
            feat = self.extract_features(returns[:i])
            features.append(feat[0])
        
        if len(features) < 100:
            logger.warning("Not enough data to fit HMM")
            return
        
        X = np.array(features)
        
        try:
            self.model.fit(X)
            self.is_fitted = True
            logger.info("HMM fitted successfully")
        except Exception as e:
            logger.error(f"HMM fitting failed: {e}")
    
    def detect_regime(self, returns: np.ndarray) -> Tuple[VolatilityRegime, Dict[VolatilityRegime, float]]:
        """
        Detect current volatility regime
        
        Args:
            returns: Recent returns array
            
        Returns:
            Tuple of (current regime, probability distribution)
        """
        features = self.extract_features(returns)
        self.feature_history.append(features[0])
        
        if HMM_AVAILABLE and self.is_fitted and self.model is not None:
            try:
                # Predict state
                state = self.model.predict(features)[0]
                
                # Get state probabilities
                log_prob = self.model.score_samples(features)
                probs = np.exp(self.model.predict_proba(features)[0])
                
                self.current_regime = self.state_mapping[state]
                self.regime_probabilities = {
                    self.state_mapping[i]: float(probs[i])
                    for i in range(self.n_states)
                }
                
            except Exception as e:
                logger.error(f"HMM prediction failed: {e}")
                return self._rule_based_detection(features[0])
        else:
            return self._rule_based_detection(features[0])
        
        return self.current_regime, self.regime_probabilities
    
    def _rule_based_detection(self, features: np.ndarray) -> Tuple[VolatilityRegime, Dict[VolatilityRegime, float]]:
        """Fallback rule-based regime detection"""
        volatility, trend, autocorr = features
        
        # Thresholds
        vol_threshold = 0.20  # 20% annualized
        trend_threshold = 0.05  # 5% annualized trend
        
        is_high_vol = volatility > vol_threshold
        is_trending = trend > trend_threshold or abs(autocorr) > 0.3
        
        if is_high_vol:
            if is_trending:
                regime = VolatilityRegime.HIGH_VOL_TRENDING
            else:
                regime = VolatilityRegime.HIGH_VOL_RANGING
        else:
            if is_trending:
                regime = VolatilityRegime.LOW_VOL_TRENDING
            else:
                regime = VolatilityRegime.LOW_VOL_RANGING
        
        self.current_regime = regime
        
        # Simple probability assignment
        self.regime_probabilities = {r: 0.1 for r in VolatilityRegime}
        self.regime_probabilities[regime] = 0.7
        
        return regime, self.regime_probabilities
    
    def get_regime_adjustments(self) -> Dict[str, float]:
        """Get trading adjustments based on current regime"""
        adjustments = {
            VolatilityRegime.LOW_VOL_TRENDING: {
                'position_size': 1.2,
                'dc_threshold': 0.9,
                'stop_loss': 1.0,
            },
            VolatilityRegime.LOW_VOL_RANGING: {
                'position_size': 1.0,
                'dc_threshold': 1.0,
                'stop_loss': 1.0,
            },
            VolatilityRegime.HIGH_VOL_TRENDING: {
                'position_size': 0.8,
                'dc_threshold': 1.3,
                'stop_loss': 0.85,
            },
            VolatilityRegime.HIGH_VOL_RANGING: {
                'position_size': 0.5,
                'dc_threshold': 1.5,
                'stop_loss': 0.75,
            },
        }
        
        return adjustments.get(self.current_regime, adjustments[VolatilityRegime.LOW_VOL_RANGING])


class KellyCriterion:
    """
    Kelly Criterion position sizing with ML enhancement
    
    f* = (p × b - q) / b
    
    Where:
    - p = ML-predicted win probability
    - q = 1 - p
    - b = average win / average loss ratio
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Kelly fraction (safety factor)
        self.kelly_fraction = self.config.get('kelly_fraction', 0.25)  # Quarter Kelly
        
        # Maximum position size
        self.max_position = self.config.get('max_position', 0.05)  # 5% of capital
        
        # Minimum confidence for full sizing
        self.min_confidence = self.config.get('min_confidence', 0.6)
        
        # Historical performance
        self.wins: deque = deque(maxlen=1000)
        self.losses: deque = deque(maxlen=1000)
    
    def calculate_kelly(self, win_prob: float, payoff_ratio: float) -> float:
        """
        Calculate Kelly fraction
        
        Args:
            win_prob: Probability of winning (0-1)
            payoff_ratio: Average win / average loss
            
        Returns:
            Optimal fraction of capital to risk
        """
        if win_prob <= 0 or win_prob >= 1:
            return 0
        
        if payoff_ratio <= 0:
            return 0
        
        q = 1 - win_prob
        kelly = (win_prob * payoff_ratio - q) / payoff_ratio
        
        # Apply safety fraction
        kelly *= self.kelly_fraction
        
        # Ensure non-negative
        return max(0, kelly)
    
    def get_position_size(self, capital: float, win_prob: float,
                         confidence: float, payoff_ratio: float = None) -> float:
        """
        Get recommended position size
        
        Args:
            capital: Total capital
            win_prob: ML-predicted win probability
            confidence: Model confidence (0-1)
            payoff_ratio: Optional override for payoff ratio
            
        Returns:
            Recommended position size in currency units
        """
        # Calculate payoff ratio from history if not provided
        if payoff_ratio is None:
            payoff_ratio = self._calculate_payoff_ratio()
        
        # Calculate base Kelly
        kelly = self.calculate_kelly(win_prob, payoff_ratio)
        
        # Adjust for confidence
        if confidence < self.min_confidence:
            kelly *= confidence / self.min_confidence
        
        # Calculate position size
        position_size = kelly * capital
        
        # Apply maximum
        max_size = capital * self.max_position
        position_size = min(position_size, max_size)
        
        return position_size
    
    def _calculate_payoff_ratio(self) -> float:
        """Calculate payoff ratio from historical trades"""
        if not self.wins or not self.losses:
            return 1.5  # Default assumption
        
        avg_win = np.mean(list(self.wins))
        avg_loss = np.mean(list(self.losses))
        
        if avg_loss == 0:
            return 2.0
        
        return abs(avg_win / avg_loss)
    
    def record_trade(self, pnl: float):
        """Record trade result for payoff ratio calculation"""
        if pnl > 0:
            self.wins.append(pnl)
        elif pnl < 0:
            self.losses.append(abs(pnl))
    
    def get_statistics(self) -> Dict[str, float]:
        """Get Kelly statistics"""
        win_rate = len(self.wins) / (len(self.wins) + len(self.losses)) if self.wins or self.losses else 0.5
        payoff_ratio = self._calculate_payoff_ratio()
        
        return {
            'win_rate': win_rate,
            'payoff_ratio': payoff_ratio,
            'kelly_fraction': self.kelly_fraction,
            'optimal_kelly': self.calculate_kelly(win_rate, payoff_ratio),
            'total_trades': len(self.wins) + len(self.losses),
        }


class DynamicPositionSizer:
    """
    Dynamic position sizing combining multiple factors
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Components
        self.kelly = KellyCriterion(config.get('kelly', {}))
        self.regime_detector = VolatilityRegimeDetector(config.get('regime', {}))
        
        # Risk limits
        self.max_position_pct = self.config.get('max_position_pct', 0.05)
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.20)
        self.max_correlation_exposure = self.config.get('max_correlation_exposure', 0.30)
        
        # Current positions
        self.positions: Dict[str, float] = {}
        self.position_correlations: Dict[Tuple[str, str], float] = {}
    
    def calculate_position_size(self, symbol: str, capital: float,
                               signal: Dict[str, Any],
                               returns: np.ndarray = None) -> PositionSizeRecommendation:
        """
        Calculate optimal position size
        
        Args:
            symbol: Trading symbol
            capital: Total capital
            signal: Trading signal with win_prob, confidence, etc.
            returns: Recent returns for regime detection
            
        Returns:
            PositionSizeRecommendation
        """
        # Extract signal parameters
        win_prob = signal.get('win_prob', 0.5)
        confidence = signal.get('confidence', 0.5)
        
        # Base Kelly sizing
        kelly_size = self.kelly.get_position_size(capital, win_prob, confidence)
        kelly_fraction = kelly_size / capital if capital > 0 else 0
        
        # Regime adjustment
        if returns is not None and len(returns) > 20:
            regime, _ = self.regime_detector.detect_regime(returns)
            regime_adj = self.regime_detector.get_regime_adjustments()
            regime_multiplier = regime_adj['position_size']
        else:
            regime_multiplier = 1.0
        
        # Correlation adjustment
        correlation_adj = self._calculate_correlation_adjustment(symbol)
        
        # Risk adjustment based on current portfolio
        risk_adj = self._calculate_risk_adjustment(symbol, capital)
        
        # Combined adjustment
        adjusted_size = kelly_size * regime_multiplier * correlation_adj * risk_adj
        
        # Apply maximum
        max_allowed = capital * self.max_position_pct
        final_size = min(adjusted_size, max_allowed)
        
        return PositionSizeRecommendation(
            symbol=symbol,
            base_size=kelly_size,
            adjusted_size=final_size,
            kelly_fraction=kelly_fraction,
            risk_adjustment=risk_adj,
            regime_adjustment=regime_multiplier,
            correlation_adjustment=correlation_adj,
            max_allowed=max_allowed,
            reason=self._generate_reason(regime_multiplier, correlation_adj, risk_adj),
        )
    
    def _calculate_correlation_adjustment(self, symbol: str) -> float:
        """Calculate adjustment based on correlation with existing positions"""
        if not self.positions:
            return 1.0
        
        total_correlated_exposure = 0
        
        for existing_symbol, existing_size in self.positions.items():
            if existing_symbol == symbol:
                continue
            
            # Get correlation
            pair = tuple(sorted([symbol, existing_symbol]))
            correlation = self.position_correlations.get(pair, 0)
            
            # Add correlated exposure
            total_correlated_exposure += abs(correlation) * existing_size
        
        # Reduce size if highly correlated
        if total_correlated_exposure > self.max_correlation_exposure:
            return self.max_correlation_exposure / total_correlated_exposure
        
        return 1.0
    
    def _calculate_risk_adjustment(self, symbol: str, capital: float) -> float:
        """Calculate adjustment based on current portfolio risk"""
        total_exposure = sum(abs(size) for size in self.positions.values())
        exposure_ratio = total_exposure / capital if capital > 0 else 0
        
        if exposure_ratio > self.max_portfolio_risk:
            return 0.5  # Reduce new positions
        elif exposure_ratio > self.max_portfolio_risk * 0.8:
            return 0.75
        
        return 1.0
    
    def _generate_reason(self, regime_adj: float, corr_adj: float, risk_adj: float) -> str:
        """Generate explanation for position size"""
        reasons = []
        
        if regime_adj != 1.0:
            reasons.append(f"Regime: {regime_adj:.2f}x")
        if corr_adj != 1.0:
            reasons.append(f"Correlation: {corr_adj:.2f}x")
        if risk_adj != 1.0:
            reasons.append(f"Risk: {risk_adj:.2f}x")
        
        return " | ".join(reasons) if reasons else "Standard sizing"
    
    def update_position(self, symbol: str, size: float):
        """Update position tracking"""
        if size == 0:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = size
    
    def update_correlation(self, symbol1: str, symbol2: str, correlation: float):
        """Update correlation between symbols"""
        pair = tuple(sorted([symbol1, symbol2]))
        self.position_correlations[pair] = correlation


class CorrelationHedger:
    """
    Correlation-based portfolio hedging
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Correlation matrix
        self.correlation_matrix: pd.DataFrame = pd.DataFrame()
        
        # Hedge instruments
        self.hedge_instruments: Dict[str, List[str]] = {
            'EURUSD': ['DXY', 'EURGBP'],
            'GBPUSD': ['DXY', 'EURGBP'],
            'USDJPY': ['DXY', 'NIKKEI'],
            'BTCUSD': ['ETHUSD', 'VIX'],
            'SPY': ['VIX', 'TLT', 'GLD'],
        }
        
        # Hedge thresholds
        self.hedge_correlation_threshold = self.config.get('hedge_threshold', -0.5)
        self.hedge_ratio = self.config.get('hedge_ratio', 0.5)
    
    def update_correlations(self, returns_df: pd.DataFrame):
        """Update correlation matrix from returns"""
        self.correlation_matrix = returns_df.corr()
    
    def get_hedge_recommendation(self, symbol: str, 
                                position_size: float) -> Dict[str, Any]:
        """
        Get hedging recommendation for a position
        
        Args:
            symbol: Symbol of the position
            position_size: Size of the position
            
        Returns:
            Hedge recommendation dictionary
        """
        recommendations = []
        
        # Check available hedge instruments
        hedge_candidates = self.hedge_instruments.get(symbol, [])
        
        for hedge_symbol in hedge_candidates:
            if hedge_symbol in self.correlation_matrix.columns and symbol in self.correlation_matrix.index:
                correlation = self.correlation_matrix.loc[symbol, hedge_symbol]
                
                if correlation < self.hedge_correlation_threshold:
                    # Good hedge candidate
                    hedge_size = abs(position_size * self.hedge_ratio * correlation)
                    
                    recommendations.append({
                        'symbol': hedge_symbol,
                        'size': hedge_size,
                        'correlation': correlation,
                        'hedge_ratio': abs(correlation) * self.hedge_ratio,
                    })
        
        # Sort by correlation (most negative first)
        recommendations.sort(key=lambda x: x['correlation'])
        
        return {
            'main_position': {'symbol': symbol, 'size': position_size},
            'hedges': recommendations[:2],  # Top 2 hedges
            'total_hedge_ratio': sum(h['hedge_ratio'] for h in recommendations[:2]),
        }
    
    def calculate_portfolio_var(self, positions: Dict[str, float],
                               volatilities: Dict[str, float],
                               confidence: float = 0.95) -> float:
        """
        Calculate portfolio VaR using correlation matrix
        
        Args:
            positions: Dictionary of symbol -> position size
            volatilities: Dictionary of symbol -> volatility
            confidence: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            Portfolio VaR
        """
        if not positions or self.correlation_matrix.empty:
            return 0
        
        symbols = list(positions.keys())
        n = len(symbols)
        
        # Build position vector
        position_vector = np.array([positions[s] for s in symbols])
        
        # Build volatility vector
        vol_vector = np.array([volatilities.get(s, 0.2) for s in symbols])
        
        # Build correlation matrix for these symbols
        try:
            corr_matrix = self.correlation_matrix.loc[symbols, symbols].values
        except KeyError:
            corr_matrix = np.eye(n)
        
        # Covariance matrix
        cov_matrix = np.outer(vol_vector, vol_vector) * corr_matrix
        
        # Portfolio variance
        portfolio_variance = position_vector @ cov_matrix @ position_vector
        portfolio_vol = np.sqrt(portfolio_variance)
        
        # VaR
        if SCIPY_AVAILABLE:
            z_score = stats.norm.ppf(confidence)
        else:
            z_score = 1.645 if confidence == 0.95 else 2.326
        
        var = portfolio_vol * z_score
        
        return var


class TailRiskProtector:
    """
    Tail risk protection using convexity strategies
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Hedge budget (% of portfolio per year)
        self.hedge_budget = self.config.get('hedge_budget', 0.01)  # 1%
        
        # Protection levels
        self.protection_levels = {
            'minimal': {'otm_puts': 0.2, 'vix_calls': 0.1, 'gold': 0.1, 'cash': 0.1},
            'moderate': {'otm_puts': 0.4, 'vix_calls': 0.2, 'gold': 0.2, 'cash': 0.2},
            'aggressive': {'otm_puts': 0.5, 'vix_calls': 0.3, 'gold': 0.15, 'cash': 0.05},
        }
        
        # Current protection level
        self.current_level = 'moderate'
        
        # VIX threshold for increasing protection
        self.vix_threshold = self.config.get('vix_threshold', 20)
    
    def get_hedge_allocation(self, portfolio_value: float,
                            current_vix: float = None) -> Dict[str, float]:
        """
        Get hedge allocation based on current conditions
        
        Args:
            portfolio_value: Total portfolio value
            current_vix: Current VIX level
            
        Returns:
            Dictionary of hedge instrument -> allocation
        """
        # Determine protection level
        if current_vix and current_vix > self.vix_threshold * 1.5:
            level = 'aggressive'
        elif current_vix and current_vix > self.vix_threshold:
            level = 'moderate'
        else:
            level = 'minimal'
        
        self.current_level = level
        allocations = self.protection_levels[level]
        
        # Calculate dollar amounts
        budget = portfolio_value * self.hedge_budget
        
        return {
            instrument: budget * weight
            for instrument, weight in allocations.items()
        }
    
    def calculate_tail_risk_metrics(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate tail risk metrics"""
        if len(returns) < 30:
            return {'cvar_95': 0, 'cvar_99': 0, 'tail_ratio': 1}
        
        # Sort returns
        sorted_returns = np.sort(returns)
        
        # CVaR (Expected Shortfall)
        var_95_idx = int(len(returns) * 0.05)
        var_99_idx = int(len(returns) * 0.01)
        
        cvar_95 = np.mean(sorted_returns[:var_95_idx]) if var_95_idx > 0 else sorted_returns[0]
        cvar_99 = np.mean(sorted_returns[:var_99_idx]) if var_99_idx > 0 else sorted_returns[0]
        
        # Tail ratio (95th percentile gain / 5th percentile loss)
        gain_95 = np.percentile(returns, 95)
        loss_5 = np.percentile(returns, 5)
        tail_ratio = abs(gain_95 / loss_5) if loss_5 != 0 else 1
        
        return {
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'tail_ratio': tail_ratio,
            'skewness': float(stats.skew(returns)) if SCIPY_AVAILABLE else 0,
            'kurtosis': float(stats.kurtosis(returns)) if SCIPY_AVAILABLE else 0,
        }


class MLRiskManager:
    """
    Main ML-based risk manager combining all components
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.regime_detector = VolatilityRegimeDetector(config.get('regime', {}))
        self.position_sizer = DynamicPositionSizer(config.get('position_sizer', {}))
        self.correlation_hedger = CorrelationHedger(config.get('hedger', {}))
        self.tail_protector = TailRiskProtector(config.get('tail_risk', {}))
        
        # Risk limits
        self.max_daily_loss = self.config.get('max_daily_loss', 0.03)  # 3%
        self.max_position_risk = self.config.get('max_position_risk', 0.02)  # 2%
        self.max_drawdown = self.config.get('max_drawdown', 0.15)  # 15%
        
        # State tracking
        self.daily_pnl = 0
        self.peak_equity = 0
        self.current_equity = 0
        self.current_drawdown = 0
        
        # Returns history
        self.returns_history: deque = deque(maxlen=252)
    
    def update_equity(self, equity: float):
        """Update equity tracking"""
        self.current_equity = equity
        
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        self.current_drawdown = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl = pnl
        
        # Record return
        if self.current_equity > 0:
            daily_return = pnl / self.current_equity
            self.returns_history.append(daily_return)
    
    def check_risk_limits(self) -> Dict[str, Any]:
        """
        Check if any risk limits are breached
        
        Returns:
            Dictionary with limit status and recommended actions
        """
        breaches = []
        actions = []
        
        # Daily loss limit
        if self.current_equity > 0:
            daily_loss_pct = -self.daily_pnl / self.current_equity
            if daily_loss_pct > self.max_daily_loss:
                breaches.append('daily_loss')
                actions.append('halt_trading')
        
        # Drawdown limit
        if self.current_drawdown > self.max_drawdown:
            breaches.append('max_drawdown')
            actions.append('reduce_positions')
        elif self.current_drawdown > self.max_drawdown * 0.8:
            breaches.append('drawdown_warning')
            actions.append('reduce_new_positions')
        
        return {
            'breaches': breaches,
            'actions': actions,
            'daily_pnl_pct': -self.daily_pnl / self.current_equity if self.current_equity > 0 else 0,
            'current_drawdown': self.current_drawdown,
            'should_trade': len(breaches) == 0 or 'halt_trading' not in actions,
            'position_multiplier': self._get_position_multiplier(breaches),
        }
    
    def _get_position_multiplier(self, breaches: List[str]) -> float:
        """Get position size multiplier based on risk state"""
        if 'max_drawdown' in breaches:
            return 0.25
        elif 'drawdown_warning' in breaches:
            return 0.5
        elif 'daily_loss' in breaches:
            return 0
        return 1.0
    
    def get_comprehensive_risk_metrics(self) -> RiskMetrics:
        """Get comprehensive risk metrics"""
        returns = np.array(list(self.returns_history)) if self.returns_history else np.array([0])
        
        # Detect regime
        regime, _ = self.regime_detector.detect_regime(returns)
        
        # Calculate VaR
        if len(returns) > 20:
            var_95 = np.percentile(returns, 5) * self.current_equity
            var_99 = np.percentile(returns, 1) * self.current_equity
        else:
            var_95 = self.current_equity * 0.02
            var_99 = self.current_equity * 0.03
        
        # Tail risk metrics
        tail_metrics = self.tail_protector.calculate_tail_risk_metrics(returns)
        
        # Sharpe and Sortino
        if len(returns) > 20:
            mean_return = np.mean(returns) * 252
            std_return = np.std(returns) * np.sqrt(252)
            sharpe = mean_return / std_return if std_return > 0 else 0
            
            downside_returns = returns[returns < 0]
            downside_std = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else std_return
            sortino = mean_return / downside_std if downside_std > 0 else 0
        else:
            sharpe = 0
            sortino = 0
        
        # Determine risk level
        if self.current_drawdown > 0.15 or abs(tail_metrics['cvar_99']) > 0.05:
            risk_level = RiskLevel.EXTREME
        elif self.current_drawdown > 0.10 or abs(tail_metrics['cvar_95']) > 0.03:
            risk_level = RiskLevel.HIGH
        elif self.current_drawdown > 0.05:
            risk_level = RiskLevel.MODERATE
        elif self.current_drawdown > 0.02:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MINIMAL
        
        return RiskMetrics(
            timestamp=datetime.now(),
            var_95=var_95,
            var_99=var_99,
            cvar_95=tail_metrics['cvar_95'] * self.current_equity,
            cvar_99=tail_metrics['cvar_99'] * self.current_equity,
            max_drawdown=self.current_drawdown,
            current_drawdown=self.current_drawdown,
            volatility=np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            beta=0,  # Would need market returns
            correlation_risk=0,  # Would need position data
            concentration_risk=0,  # Would need position data
            liquidity_risk=0,  # Would need volume data
            regime=regime,
            risk_level=risk_level,
        )
    
    def get_position_recommendation(self, symbol: str, signal: Dict[str, Any],
                                   capital: float = None) -> PositionSizeRecommendation:
        """Get position size recommendation"""
        if capital is None:
            capital = self.current_equity
        
        returns = np.array(list(self.returns_history)) if self.returns_history else None
        
        # Get base recommendation
        recommendation = self.position_sizer.calculate_position_size(
            symbol, capital, signal, returns
        )
        
        # Apply risk limit multiplier
        risk_check = self.check_risk_limits()
        recommendation.adjusted_size *= risk_check['position_multiplier']
        
        if risk_check['position_multiplier'] < 1:
            recommendation.reason += f" | Risk limit: {risk_check['position_multiplier']:.2f}x"
        
        return recommendation
