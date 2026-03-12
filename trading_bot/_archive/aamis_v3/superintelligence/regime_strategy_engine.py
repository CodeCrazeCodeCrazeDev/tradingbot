"""
Regime Detection & Auto-Strategy Activation Engine
Automatically detects market regime and activates best strategy
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from collections import deque, defaultdict
from typing import Set
import numpy
import pandas

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING_TIGHT = "ranging_tight"
    RANGING_WIDE = "ranging_wide"
    VOLATILE_CHAOTIC = "volatile_chaotic"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    CRASH = "crash"
    MELT_UP = "melt_up"
    UNKNOWN = "unknown"


class StrategyType(Enum):
    """Strategy types"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    VOLATILITY_TRADING = "volatility_trading"
    MARKET_MAKING = "market_making"
    ARBITRAGE = "arbitrage"
    DEFENSIVE = "defensive"
    AGGRESSIVE_SCALPING = "aggressive_scalping"
    SWING_TRADING = "swing_trading"


@dataclass
class RegimeCharacteristics:
    """Characteristics of a market regime"""
    regime: MarketRegime
    
    # Statistical properties
    volatility: float
    trend_strength: float
    mean_reversion_strength: float
    
    # Market structure
    higher_highs: bool
    higher_lows: bool
    lower_highs: bool
    lower_lows: bool
    
    # Volume
    volume_trend: str  # increasing, decreasing, stable
    volume_spikes: int
    
    # Confidence
    confidence: float  # 0-1
    
    # Duration
    regime_age: int  # bars in this regime
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyPerformance:
    """Performance of a strategy in a regime"""
    strategy: StrategyType
    regime: MarketRegime
    
    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    # Recent performance
    recent_pnl: List[float] = field(default_factory=list)
    
    # Confidence
    confidence: float = 0.0
    
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyActivation:
    """Strategy activation decision"""
    strategy: StrategyType
    regime: MarketRegime
    
    # Activation details
    activation_reason: str
    expected_performance: float
    confidence: float
    
    # Parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Risk management
    max_position_size: float = 1.0
    stop_loss_multiplier: float = 1.0
    
    timestamp: datetime = field(default_factory=datetime.now)


class RegimeDetector:
    """
    Advanced regime detection using multiple indicators
    """
    
    def __init__(self, lookback: int = 100):
        self.lookback = lookback
        self.current_regime = MarketRegime.UNKNOWN
        self.regime_history: List[Tuple[datetime, MarketRegime]] = []
        self.regime_confidence = 0.0
        
        logger.info("Regime Detector initialized")
    
    def detect_regime(self, price_data: pd.Series, volume_data: Optional[pd.Series] = None) -> RegimeCharacteristics:
        """
        Detect current market regime
        """
        
        if len(price_data) < self.lookback:
            return self._create_unknown_regime()
        
        # Calculate indicators
        returns = price_data.pct_change().dropna()
        
        # Volatility
        volatility = returns.std() * np.sqrt(252)
        
        # Trend strength (using linear regression)
        x = np.arange(len(price_data))
        y = price_data.values
        
        # Simple linear regression
        x_mean = x.mean()
        y_mean = y.mean()
        
        numerator = ((x - x_mean) * (y - y_mean)).sum()
        denominator = ((x - x_mean) ** 2).sum()
        
        if denominator != 0:
            slope = numerator / denominator
            trend_strength = abs(slope) / y_mean  # Normalized slope
        else:
            trend_strength = 0.0
        
        # Mean reversion strength (using autocorrelation)
        if len(returns) > 1:
            mean_reversion_strength = abs(returns.autocorr(lag=1))
        else:
            mean_reversion_strength = 0.0
        
        # Market structure
        recent_prices = price_data.tail(20)
        
        highs = []
        lows = []
        
        for i in range(1, len(recent_prices) - 1):
            if recent_prices.iloc[i] > recent_prices.iloc[i-1] and recent_prices.iloc[i] > recent_prices.iloc[i+1]:
                highs.append(recent_prices.iloc[i])
            if recent_prices.iloc[i] < recent_prices.iloc[i-1] and recent_prices.iloc[i] < recent_prices.iloc[i+1]:
                lows.append(recent_prices.iloc[i])
        
        higher_highs = len(highs) >= 2 and highs[-1] > highs[0]
        higher_lows = len(lows) >= 2 and lows[-1] > lows[0]
        lower_highs = len(highs) >= 2 and highs[-1] < highs[0]
        lower_lows = len(lows) >= 2 and lows[-1] < lows[0]
        
        # Volume analysis
        if volume_data is not None and len(volume_data) > 0:
            volume_trend = "increasing" if volume_data.tail(10).mean() > volume_data.tail(30).mean() else "decreasing"
            volume_spikes = (volume_data > volume_data.mean() + 2 * volume_data.std()).sum()
        else:
            volume_trend = "stable"
            volume_spikes = 0
        
        # Determine regime
        regime = self._classify_regime(
            volatility, trend_strength, mean_reversion_strength,
            higher_highs, higher_lows, lower_highs, lower_lows,
            slope if 'slope' in locals() else 0
        )
        
        # Calculate confidence
        confidence = self._calculate_regime_confidence(
            volatility, trend_strength, mean_reversion_strength
        )
        
        # Update regime history
        if regime != self.current_regime:
            self.regime_history.append((datetime.now(), regime))
            self.current_regime = regime
            logger.info(f"Regime changed to: {regime.value}")
        
        # Calculate regime age
        regime_age = 1
        for i in range(len(self.regime_history) - 1, -1, -1):
            if self.regime_history[i][1] == regime:
                regime_age += 1
            else:
                break
        
        return RegimeCharacteristics(
            regime=regime,
            volatility=volatility,
            trend_strength=trend_strength,
            mean_reversion_strength=mean_reversion_strength,
            higher_highs=higher_highs,
            higher_lows=higher_lows,
            lower_highs=lower_highs,
            lower_lows=lower_lows,
            volume_trend=volume_trend,
            volume_spikes=volume_spikes,
            confidence=confidence,
            regime_age=regime_age
        )
    
    def _classify_regime(self, volatility: float, trend_strength: float,
                        mean_reversion: float, higher_highs: bool,
                        higher_lows: bool, lower_highs: bool,
                        lower_lows: bool, slope: float) -> MarketRegime:
        """Classify market regime based on characteristics"""
        
        # Crash detection
        if volatility > 0.5 and slope < -0.01:
            return MarketRegime.CRASH
        
        # Melt-up detection
        if volatility > 0.3 and slope > 0.01 and trend_strength > 0.01:
            return MarketRegime.MELT_UP
        
        # Volatile chaotic
        if volatility > 0.4:
            return MarketRegime.VOLATILE_CHAOTIC
        
        # Trending bull
        if trend_strength > 0.005 and higher_highs and higher_lows and slope > 0:
            return MarketRegime.TRENDING_BULL
        
        # Trending bear
        if trend_strength > 0.005 and lower_highs and lower_lows and slope < 0:
            return MarketRegime.TRENDING_BEAR
        
        # Breakout
        if trend_strength > 0.003 and volatility > 0.2 and slope > 0:
            return MarketRegime.BREAKOUT
        
        # Breakdown
        if trend_strength > 0.003 and volatility > 0.2 and slope < 0:
            return MarketRegime.BREAKDOWN
        
        # Ranging tight
        if trend_strength < 0.002 and volatility < 0.15:
            return MarketRegime.RANGING_TIGHT
        
        # Ranging wide
        if trend_strength < 0.003 and volatility < 0.25:
            return MarketRegime.RANGING_WIDE
        
        # Accumulation (low volatility, no clear trend)
        if volatility < 0.15 and mean_reversion > 0.3:
            return MarketRegime.ACCUMULATION
        
        # Distribution (increasing volatility, weakening trend)
        if volatility > 0.2 and trend_strength < 0.003:
            return MarketRegime.DISTRIBUTION
        
        return MarketRegime.UNKNOWN
    
    def _calculate_regime_confidence(self, volatility: float,
                                    trend_strength: float,
                                    mean_reversion: float) -> float:
        """Calculate confidence in regime classification"""
        
        # Higher confidence when indicators are clear
        confidence = 0.5
        
        # Strong trend increases confidence
        if trend_strength > 0.005:
            confidence += 0.2
        
        # Clear mean reversion increases confidence
        if mean_reversion > 0.4:
            confidence += 0.2
        
        # Stable volatility increases confidence
        if 0.1 < volatility < 0.3:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_unknown_regime(self) -> RegimeCharacteristics:
        """Create unknown regime characteristics"""
        
        return RegimeCharacteristics(
            regime=MarketRegime.UNKNOWN,
            volatility=0.0,
            trend_strength=0.0,
            mean_reversion_strength=0.0,
            higher_highs=False,
            higher_lows=False,
            lower_highs=False,
            lower_lows=False,
            volume_trend="stable",
            volume_spikes=0,
            confidence=0.0,
            regime_age=0
        )


class StrategySelector:
    """
    Selects best strategy for current regime
    """
    
    def __init__(self):
        # Strategy performance by regime
        self.performance_matrix: Dict[Tuple[StrategyType, MarketRegime], StrategyPerformance] = {}
        
        # Initialize default performance
        self._initialize_default_performance()
        
        # Active strategy
        self.active_strategy: Optional[StrategyType] = None
        
        logger.info("Strategy Selector initialized")
    
    def _initialize_default_performance(self):
        """Initialize default strategy-regime performance"""
        
        # Define which strategies work best in which regimes
        regime_strategy_map = {
            MarketRegime.TRENDING_BULL: [
                (StrategyType.TREND_FOLLOWING, 0.8),
                (StrategyType.MOMENTUM, 0.7),
                (StrategyType.BREAKOUT, 0.6)
            ],
            MarketRegime.TRENDING_BEAR: [
                (StrategyType.TREND_FOLLOWING, 0.7),
                (StrategyType.MOMENTUM, 0.6),
                (StrategyType.DEFENSIVE, 0.8)
            ],
            MarketRegime.RANGING_TIGHT: [
                (StrategyType.MEAN_REVERSION, 0.8),
                (StrategyType.MARKET_MAKING, 0.7),
                (StrategyType.AGGRESSIVE_SCALPING, 0.6)
            ],
            MarketRegime.RANGING_WIDE: [
                (StrategyType.MEAN_REVERSION, 0.7),
                (StrategyType.SWING_TRADING, 0.6),
                (StrategyType.VOLATILITY_TRADING, 0.5)
            ],
            MarketRegime.VOLATILE_CHAOTIC: [
                (StrategyType.DEFENSIVE, 0.9),
                (StrategyType.VOLATILITY_TRADING, 0.5)
            ],
            MarketRegime.BREAKOUT: [
                (StrategyType.BREAKOUT, 0.9),
                (StrategyType.MOMENTUM, 0.7)
            ],
            MarketRegime.BREAKDOWN: [
                (StrategyType.DEFENSIVE, 0.8),
                (StrategyType.TREND_FOLLOWING, 0.6)
            ],
            MarketRegime.CRASH: [
                (StrategyType.DEFENSIVE, 1.0)
            ],
            MarketRegime.MELT_UP: [
                (StrategyType.MOMENTUM, 0.8),
                (StrategyType.TREND_FOLLOWING, 0.7)
            ]
        }
        
        # Initialize performance objects
        for regime, strategies in regime_strategy_map.items():
            for strategy, confidence in strategies:
                key = (strategy, regime)
                self.performance_matrix[key] = StrategyPerformance(
                    strategy=strategy,
                    regime=regime,
                    confidence=confidence
                )
    
    def select_strategy(self, regime_chars: RegimeCharacteristics) -> StrategyActivation:
        """
        Select best strategy for current regime
        """
        
        regime = regime_chars.regime
        
        # Find strategies for this regime
        candidates = []
        
        for (strategy, reg), perf in self.performance_matrix.items():
            if reg == regime:
                # Score based on performance and confidence
                score = perf.confidence * regime_chars.confidence
                
                # Boost score if strategy has good recent performance
                if perf.total_trades > 10:
                    score *= (1 + perf.win_rate * 0.5)
                
                candidates.append((score, strategy, perf))
        
        if not candidates:
            # No specific strategy, use defensive
            strategy = StrategyType.DEFENSIVE
            expected_performance = 0.5
            confidence = 0.5
            reason = f"No specific strategy for {regime.value}, using defensive"
        else:
            # Select best strategy
            candidates.sort(key=lambda x: x[0], reverse=True)
            score, strategy, perf = candidates[0]
            
            expected_performance = score
            confidence = perf.confidence
            reason = f"Best strategy for {regime.value} based on historical performance"
        
        # Set parameters based on regime
        parameters = self._get_strategy_parameters(strategy, regime_chars)
        
        # Risk management adjustments
        max_position_size = self._calculate_position_size(regime_chars)
        stop_loss_multiplier = self._calculate_stop_multiplier(regime_chars)
        
        activation = StrategyActivation(
            strategy=strategy,
            regime=regime,
            activation_reason=reason,
            expected_performance=expected_performance,
            confidence=confidence,
            parameters=parameters,
            max_position_size=max_position_size,
            stop_loss_multiplier=stop_loss_multiplier
        )
        
        # Update active strategy
        if self.active_strategy != strategy:
            logger.info(f"Strategy changed: {self.active_strategy} → {strategy.value}")
            self.active_strategy = strategy
        
        return activation
    
    def update_performance(self, strategy: StrategyType, regime: MarketRegime,
                          trade_result: Dict[str, Any]):
        """Update strategy performance based on trade result"""
        
        key = (strategy, regime)
        
        if key not in self.performance_matrix:
            self.performance_matrix[key] = StrategyPerformance(
                strategy=strategy,
                regime=regime
            )
        
        perf = self.performance_matrix[key]
        
        # Update metrics
        perf.total_trades += 1
        
        pnl = trade_result.get('pnl', 0.0)
        perf.recent_pnl.append(pnl)
        
        if len(perf.recent_pnl) > 100:
            perf.recent_pnl.pop(0)
        
        if pnl > 0:
            perf.winning_trades += 1
            perf.avg_win = (perf.avg_win * (perf.winning_trades - 1) + pnl) / perf.winning_trades
        else:
            perf.losing_trades += 1
            perf.avg_loss = (perf.avg_loss * (perf.losing_trades - 1) + abs(pnl)) / perf.losing_trades
        
        # Update win rate
        perf.win_rate = perf.winning_trades / perf.total_trades
        
        # Update profit factor
        if perf.losing_trades > 0 and perf.avg_loss > 0:
            perf.profit_factor = (perf.winning_trades * perf.avg_win) / (perf.losing_trades * perf.avg_loss)
        
        # Update confidence based on recent performance
        if len(perf.recent_pnl) >= 20:
            recent_wins = sum(1 for p in perf.recent_pnl[-20:] if p > 0)
            perf.confidence = recent_wins / 20
        
        perf.last_updated = datetime.now()
        
        logger.info(f"Updated performance for {strategy.value} in {regime.value}: "
                   f"win_rate={perf.win_rate:.2%}, confidence={perf.confidence:.2f}")
    
    def _get_strategy_parameters(self, strategy: StrategyType,
                                 regime_chars: RegimeCharacteristics) -> Dict[str, Any]:
        """Get parameters for strategy based on regime"""
        
        params = {}
        
        if strategy == StrategyType.TREND_FOLLOWING:
            params = {
                'trend_period': 50,
                'entry_threshold': 0.02 * regime_chars.trend_strength,
                'exit_threshold': 0.01
            }
        elif strategy == StrategyType.MEAN_REVERSION:
            params = {
                'lookback': 20,
                'entry_std': 2.0,
                'exit_std': 0.5
            }
        elif strategy == StrategyType.BREAKOUT:
            params = {
                'breakout_period': 20,
                'volume_confirmation': True
            }
        elif strategy == StrategyType.DEFENSIVE:
            params = {
                'max_exposure': 0.3,
                'tight_stops': True
            }
        
        return params
    
    def _calculate_position_size(self, regime_chars: RegimeCharacteristics) -> float:
        """Calculate position size multiplier based on regime"""
        
        # Reduce size in volatile regimes
        if regime_chars.regime in [MarketRegime.VOLATILE_CHAOTIC, MarketRegime.CRASH]:
            return 0.3
        elif regime_chars.regime in [MarketRegime.RANGING_TIGHT, MarketRegime.ACCUMULATION]:
            return 0.8
        elif regime_chars.regime in [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR]:
            return 1.0
        else:
            return 0.6
    
    def _calculate_stop_multiplier(self, regime_chars: RegimeCharacteristics) -> float:
        """Calculate stop loss multiplier based on regime"""
        
        # Tighter stops in ranging, wider in trending
        if regime_chars.regime in [MarketRegime.RANGING_TIGHT, MarketRegime.RANGING_WIDE]:
            return 0.8
        elif regime_chars.regime in [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR]:
            return 1.5
        elif regime_chars.regime in [MarketRegime.VOLATILE_CHAOTIC]:
            return 2.0
        else:
            return 1.0


class RegimeStrategyEngine:
    """
    Complete regime detection and strategy activation engine
    """
    
    def __init__(self):
        self.regime_detector = RegimeDetector()
        self.strategy_selector = StrategySelector()
        
        # History
        self.regime_history: List[RegimeCharacteristics] = []
        self.activation_history: List[StrategyActivation] = []
        
        logger.info("Regime-Strategy Engine initialized")
    
    def analyze_and_activate(self, price_data: pd.Series,
                            volume_data: Optional[pd.Series] = None) -> Tuple[RegimeCharacteristics, StrategyActivation]:
        """
        Analyze regime and activate best strategy
        """
        
        # Detect regime
        regime_chars = self.regime_detector.detect_regime(price_data, volume_data)
        self.regime_history.append(regime_chars)
        
        # Select strategy
        activation = self.strategy_selector.select_strategy(regime_chars)
        self.activation_history.append(activation)
        
        logger.info(f"Regime: {regime_chars.regime.value} (confidence={regime_chars.confidence:.2f}) → "
                   f"Strategy: {activation.strategy.value} (expected={activation.expected_performance:.2f})")
        
        return regime_chars, activation
    
    def update_strategy_performance(self, trade_result: Dict[str, Any]):
        """Update strategy performance"""
        
        if not self.activation_history:
            return
        
        # Get current activation
        current_activation = self.activation_history[-1]
        current_regime = self.regime_history[-1].regime if self.regime_history else MarketRegime.UNKNOWN
        
        self.strategy_selector.update_performance(
            current_activation.strategy,
            current_regime,
            trade_result
        )


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = RegimeStrategyEngine()
    
    print("="*80)
    logger.info("REGIME DETECTION & AUTO-STRATEGY ACTIVATION")
    print("="*80)
    
    # Generate sample price data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
    
    # Trending phase
    trend = np.linspace(100, 120, 200)
    noise = np.random.randn(200) * 2
    prices = trend + noise
    
    price_data = pd.Series(prices, index=dates)
    
    # Analyze
    logger.info("\nAnalyzing market and activating strategy...")
    regime_chars, activation = engine.analyze_and_activate(price_data)
    
    logger.info(f"\nREGIME DETECTED: {regime_chars.regime.value}")
    logger.info(f"  Confidence: {regime_chars.confidence:.2%}")
    logger.info(f"  Volatility: {regime_chars.volatility:.2%}")
    logger.info(f"  Trend Strength: {regime_chars.trend_strength:.4f}")
    logger.info(f"  Regime Age: {regime_chars.regime_age} bars")
    
    logger.info(f"\nSTRATEGY ACTIVATED: {activation.strategy.value}")
    logger.info(f"  Activation Reason: {activation.activation_reason}")
    logger.info(f"  Expected Performance: {activation.expected_performance:.2f}")
    logger.info(f"  Confidence: {activation.confidence:.2%}")
    logger.info(f"  Max Position Size: {activation.max_position_size:.2f}x")
    logger.info(f"  Stop Loss Multiplier: {activation.stop_loss_multiplier:.2f}x")
    
    if activation.parameters:
        logger.info(f"\n  Parameters:")
        for key, value in activation.parameters.items():
            logger.info(f"    {key}: {value}")
    
    print("\n" + "="*80)
    logger.info("REGIME-STRATEGY ENGINE OPERATIONAL")
    print("="*80)
