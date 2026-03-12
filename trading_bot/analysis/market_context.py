"""
Market Context Analysis Module

This module provides tools for analyzing market context, including:
- Market phase detection
- Regime classification
- Volatility analysis
- Trend strength measurement
- Intermarket correlations
"""

import numpy as np
import pandas as pd
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import asyncio
from dataclasses import dataclass

import enum

class TrendStrength(enum.Enum):
    """Trend strength classification."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"

class MarketPhase(enum.Enum):
    """Market phase classification."""
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"
from trading_bot.elite_system.regime_detection import MarketRegime
import numpy
import pandas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketContextResult:
    """Market Context Analysis Result"""
    market_phase: MarketPhase = MarketPhase.UNKNOWN
    market_regime: MarketRegime = MarketRegime.UNKNOWN
    volatility: float = 0.0
    trend_strength: float = 0.0
    momentum: float = 0.0
    key_levels: List[float] = None
    support_levels: List[float] = None
    resistance_levels: List[float] = None
    
    def __post_init__(self):
        if self.key_levels is None:
            self.key_levels = []
        if self.support_levels is None:
            self.support_levels = []
        if self.resistance_levels is None:
            self.resistance_levels = []

class MarketContextAnalyzer:
    """Market Context Analysis"""
    
    def __init__(self):
        """Initialize Market Context Analyzer"""
        logger.info("Market Context Analyzer initialized")
    
    async def analyze(self, market_data: pd.DataFrame, timeframe: str = '1H') -> MarketContextResult:
        """
        Analyze market context
        
        Args:
            market_data: OHLCV DataFrame
            timeframe: Timeframe of the data
            
        Returns:
            MarketContextResult object with analysis results
        """
        try:
            # Calculate volatility (ATR as percentage of price)
            atr = self._calculate_atr(market_data, period=14)
            volatility = atr / market_data['close'].iloc[-1]
            
            # Determine market phase
            market_phase = self._determine_market_phase(market_data)
            
            # Determine market regime
            market_regime = self._determine_market_regime(market_data, volatility)
            
            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(market_data)
            
            # Calculate momentum
            momentum = self._calculate_momentum(market_data)
            
            # Identify key levels
            key_levels, support_levels, resistance_levels = self._identify_key_levels(market_data)
            
            # Create result
            result = MarketContextResult(
                market_phase=market_phase,
                market_regime=market_regime,
                volatility=volatility,
                trend_strength=trend_strength,
                momentum=momentum,
                key_levels=key_levels,
                support_levels=support_levels,
                resistance_levels=resistance_levels
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing market context: {e}")
            return MarketContextResult()
    
    def _calculate_atr(self, market_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high = market_data['high']
            low = market_data['low']
            close = market_data['close'].shift(1)
            
            tr1 = high - low
            tr2 = abs(high - close)
            tr3 = abs(low - close)
            
            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            atr = tr.rolling(period).mean().iloc[-1]
            
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return 0.0
    
    def _determine_market_phase(self, market_data: pd.DataFrame) -> MarketPhase:
        """Determine market phase"""
        try:
            # Simple algorithm: use moving averages to determine trend direction
            short_ma = market_data['close'].rolling(20).mean()
            long_ma = market_data['close'].rolling(50).mean()
            
            # Get recent price action
            recent_close = market_data['close'].iloc[-1]
            recent_short_ma = short_ma.iloc[-1]
            recent_long_ma = long_ma.iloc[-1]
            
            # Determine phase based on moving averages
            if recent_short_ma > recent_long_ma and recent_close > recent_short_ma:
                return MarketPhase.ACCUMULATION
            elif recent_short_ma < recent_long_ma and recent_close < recent_short_ma:
                return MarketPhase.DISTRIBUTION
            elif recent_short_ma > recent_long_ma:
                return MarketPhase.MARKUP
            elif recent_short_ma < recent_long_ma:
                return MarketPhase.MARKDOWN
            else:
                return MarketPhase.UNKNOWN
                
        except Exception as e:
            logger.error(f"Error determining market phase: {e}")
            return MarketPhase.UNKNOWN
    
    def _determine_market_regime(self, market_data: pd.DataFrame, volatility: float) -> MarketRegime:
        """Determine market regime"""
        try:
            # Calculate returns
            returns = market_data['close'].pct_change().dropna()
            
            # Calculate trend (using simple moving average direction)
            sma = market_data['close'].rolling(50).mean()
            trend = 1 if sma.iloc[-1] > sma.iloc[-20] else -1 if sma.iloc[-1] < sma.iloc[-20] else 0
            
            # High volatility threshold
            high_vol_threshold = 0.015  # 1.5% ATR/price ratio
            
            # Determine regime
            if trend > 0 and volatility < high_vol_threshold:
                return MarketRegime.TRENDING_BULL
            elif trend < 0 and volatility < high_vol_threshold:
                return MarketRegime.TRENDING_BEAR
            elif trend > 0 and volatility >= high_vol_threshold:
                return MarketRegime.VOLATILE_BULL
            elif trend < 0 and volatility >= high_vol_threshold:
                return MarketRegime.VOLATILE_BEAR
            elif abs(trend) < 0.2 and volatility < high_vol_threshold:
                return MarketRegime.RANGING_LOW_VOL
            elif abs(trend) < 0.2 and volatility >= high_vol_threshold:
                return MarketRegime.RANGING_HIGH_VOL
            else:
                return MarketRegime.UNKNOWN
                
        except Exception as e:
            logger.error(f"Error determining market regime: {e}")
            return MarketRegime.UNKNOWN
    
    def _calculate_trend_strength(self, market_data: pd.DataFrame) -> float:
        """Calculate trend strength"""
        try:
            # Use ADX-like calculation for trend strength
            close = market_data['close']
            high = market_data['high']
            low = market_data['low']
            
            # Calculate +DM and -DM
            plus_dm = high.diff()
            minus_dm = low.diff()
            
            # Replace negative values with 0
            plus_dm = plus_dm.where(plus_dm > 0, 0)
            minus_dm = minus_dm.where(minus_dm < 0, 0).abs()
            
            # Calculate ATR
            atr = self._calculate_atr(market_data)
            
            # Calculate +DI and -DI
            plus_di = 100 * plus_dm.rolling(14).mean() / atr
            minus_di = 100 * minus_dm.rolling(14).mean() / atr
            
            # Calculate DX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            
            # Calculate ADX (trend strength)
            adx = dx.rolling(14).mean().iloc[-1] / 100  # Normalize to 0-1
            
            return min(adx, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.0
    
    def _calculate_momentum(self, market_data: pd.DataFrame) -> float:
        """Calculate momentum"""
        try:
            # Use ROC (Rate of Change) for momentum
            close = market_data['close']
            roc = ((close.iloc[-1] / close.iloc[-20]) - 1) * 100
            
            # Normalize to -1 to 1 range
            normalized_roc = np.tanh(roc / 10)  # tanh squashes to -1 to 1
            
            return normalized_roc
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return 0.0
    
    def _identify_key_levels(self, market_data: pd.DataFrame) -> Tuple[List[float], List[float], List[float]]:
        """Identify key price levels"""
        try:
            # Get high, low, close
            high = market_data['high']
            low = market_data['low']
            close = market_data['close']
            
            # Calculate recent swing highs and lows (simple algorithm)
            window = 5
            swing_highs = []
            swing_lows = []
            
            for i in range(window, len(high) - window):
                # Check for swing high
                if high.iloc[i] == high.iloc[i-window:i+window+1].max():
                    swing_highs.append(high.iloc[i])
                
                # Check for swing low
                if low.iloc[i] == low.iloc[i-window:i+window+1].min():
                    swing_lows.append(low.iloc[i])
            
            # Get recent price
            recent_price = close.iloc[-1]
            
            # Filter levels
            support_levels = [level for level in swing_lows if level < recent_price]
            resistance_levels = [level for level in swing_highs if level > recent_price]
            
            # Combine all levels
            all_levels = sorted(support_levels + resistance_levels)
            
            # Take only the most significant levels (closest to current price)
            support_levels = sorted(support_levels, reverse=True)[:3] if support_levels else []
            resistance_levels = sorted(resistance_levels)[:3] if resistance_levels else []
            key_levels = sorted(support_levels + resistance_levels)
            
            return key_levels, support_levels, resistance_levels
            
        except Exception as e:
            logger.error(f"Error identifying key levels: {e}")
            return [], [], []

# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='1H')
    np.random.seed(42)
    
    market_data = pd.DataFrame({
        'open': np.random.randn(len(dates)).cumsum() + 100,
        'high': np.random.randn(len(dates)).cumsum() + 102,
        'low': np.random.randn(len(dates)).cumsum() + 98,
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Create analyzer
    analyzer = MarketContextAnalyzer()
    
    # Run analysis
    async def test():
        result = await analyzer.analyze(market_data)
        logger.info(f"Market Phase: {result.market_phase}")
        logger.info(f"Market Regime: {result.market_regime}")
        logger.info(f"Volatility: {result.volatility:.2%}")
        logger.info(f"Trend Strength: {result.trend_strength:.2f}")
        logger.info(f"Momentum: {result.momentum:.2f}")
        logger.info(f"Key Levels: {[round(level, 2) for level in result.key_levels]}")
    
    # Run test
    asyncio.run(test())
