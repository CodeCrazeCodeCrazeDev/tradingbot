"""Fear and Greed Index Module.

Implements comprehensive market psychology quantification including:
- Fear and Greed Index calculation (0-100)
- Multiple sentiment indicators aggregation
- Regime-specific calibration
- Contrarian signal detection
- Historical percentile analysis
- Sentiment momentum tracking
- Extreme sentiment alerts
- Multi-timeframe sentiment analysis

This module enables market psychology quantification for
identifying potential reversal points and sentiment extremes.
"""


from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from enum import Enum
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class SentimentLevel(enum.Enum):
    """Sentiment classification levels."""
    EXTREME_FEAR = "extreme_fear"  # 0-20
    FEAR = "fear"  # 21-40
    NEUTRAL = "neutral"  # 41-60
    GREED = "greed"  # 61-80
    EXTREME_GREED = "extreme_greed"  # 81-100


class SentimentSignal(enum.Enum):
    """Trading signals from sentiment."""
    STRONG_BUY = "strong_buy"  # Extreme fear = contrarian buy
    BUY = "buy"  # Fear = potential buy
    NEUTRAL = "neutral"  # No signal
    SELL = "sell"  # Greed = potential sell
    STRONG_SELL = "strong_sell"  # Extreme greed = contrarian sell


class IndicatorType(enum.Enum):
    """Types of sentiment indicators."""
    VOLATILITY = "volatility"  # VIX, ATR
    MOMENTUM = "momentum"  # RSI, price momentum
    VOLUME = "volume"  # Volume trends
    BREADTH = "breadth"  # Advance/decline
    OPTIONS = "options"  # Put/call ratio
    SAFE_HAVEN = "safe_haven"  # Gold, bonds demand
    JUNK_BOND = "junk_bond"  # Credit spreads
    SOCIAL = "social"  # Social media sentiment


@dataclass
class SentimentIndicator:
    """Individual sentiment indicator."""
    name: str
    indicator_type: IndicatorType
    raw_value: float
    normalized_value: float  # 0-100 scale
    weight: float  # Weight in overall index
    signal: SentimentSignal
    description: str


@dataclass
class FearGreedReading:
    """Complete Fear and Greed Index reading."""
    timestamp: datetime
    index_value: float  # 0-100
    level: SentimentLevel
    signal: SentimentSignal
    indicators: List[SentimentIndicator]
    momentum: float  # Change from previous reading
    percentile: float  # Historical percentile
    regime: str  # Current market regime
    confidence: float  # Confidence in reading


@dataclass
class SentimentExtreme:
    """Detected sentiment extreme."""
    timestamp: datetime
    extreme_type: str  # 'fear' or 'greed'
    index_value: float
    duration_hours: int
    historical_percentile: float
    contrarian_signal: SentimentSignal
    expected_reversal_probability: float


@dataclass
class SentimentDivergence:
    """Divergence between price and sentiment."""
    timestamp: datetime
    divergence_type: str  # 'bullish' or 'bearish'
    price_direction: str
    sentiment_direction: str
    strength: float  # 0-100
    periods: int


class FearGreedCalculator:
    """Fear and Greed Index Calculator.
    
    Aggregates multiple sentiment indicators into a single
    0-100 index for market psychology quantification.
    """
    
    # Default indicator weights
    DEFAULT_WEIGHTS = {
        IndicatorType.VOLATILITY: 0.20,
        IndicatorType.MOMENTUM: 0.20,
        IndicatorType.VOLUME: 0.10,
        IndicatorType.BREADTH: 0.15,
        IndicatorType.OPTIONS: 0.15,
        IndicatorType.SAFE_HAVEN: 0.10,
        IndicatorType.JUNK_BOND: 0.05,
        IndicatorType.SOCIAL: 0.05,
    }
    
    def __init__(
        self,
        lookback_period: int = 20,
        extreme_threshold: float = 20.0,
        weights: Optional[Dict[IndicatorType, float]] = None
    ):
        """Initialize Fear and Greed Calculator.
        
        Args:
            lookback_period: Period for normalization
            extreme_threshold: Threshold for extreme readings
            weights: Custom indicator weights
        """
        try:
            self.lookback_period = lookback_period
            self.extreme_threshold = extreme_threshold
            self.weights = weights or self.DEFAULT_WEIGHTS
        
            # Historical readings
            self._history: List[FearGreedReading] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_index(
        self,
        market_data: pd.DataFrame,
        vix: Optional[float] = None,
        put_call_ratio: Optional[float] = None,
        advance_decline: Optional[float] = None,
        social_sentiment: Optional[float] = None,
        safe_haven_demand: Optional[float] = None,
        credit_spread: Optional[float] = None
    ) -> FearGreedReading:
        """Calculate Fear and Greed Index.
        
        Args:
            market_data: DataFrame with OHLCV data
            vix: VIX value (optional)
            put_call_ratio: Put/Call ratio (optional)
            advance_decline: Advance/Decline ratio (optional)
            social_sentiment: Social media sentiment -100 to +100 (optional)
            safe_haven_demand: Safe haven demand indicator (optional)
            credit_spread: Credit spread indicator (optional)
            
        Returns:
            FearGreedReading with complete analysis
        """
        try:
            indicators = []
        
            # 1. Volatility Indicator
            vol_indicator = self._calculate_volatility_indicator(market_data, vix)
            indicators.append(vol_indicator)
        
            # 2. Momentum Indicator
            mom_indicator = self._calculate_momentum_indicator(market_data)
            indicators.append(mom_indicator)
        
            # 3. Volume Indicator
            vol_trend = self._calculate_volume_indicator(market_data)
            indicators.append(vol_trend)
        
            # 4. Market Breadth Indicator
            breadth = self._calculate_breadth_indicator(market_data, advance_decline)
            indicators.append(breadth)
        
            # 5. Options Indicator
            options = self._calculate_options_indicator(put_call_ratio)
            indicators.append(options)
        
            # 6. Safe Haven Indicator
            safe_haven = self._calculate_safe_haven_indicator(safe_haven_demand)
            indicators.append(safe_haven)
        
            # 7. Junk Bond Indicator
            junk = self._calculate_junk_bond_indicator(credit_spread)
            indicators.append(junk)
        
            # 8. Social Sentiment Indicator
            social = self._calculate_social_indicator(social_sentiment)
            indicators.append(social)
        
            # Calculate weighted average
            total_weight = sum(ind.weight for ind in indicators)
            index_value = sum(ind.normalized_value * ind.weight for ind in indicators) / total_weight
        
            # Determine level
            level = self._get_sentiment_level(index_value)
        
            # Determine signal (contrarian)
            signal = self._get_contrarian_signal(index_value)
        
            # Calculate momentum
            momentum = 0
            if self._history:
                momentum = index_value - self._history[-1].index_value
            
            # Calculate percentile
            percentile = self._calculate_percentile(index_value)
        
            # Determine regime
            regime = self._determine_regime(market_data)
        
            # Calculate confidence
            confidence = self._calculate_confidence(indicators)
        
            reading = FearGreedReading(
                timestamp=datetime.now(),
                index_value=index_value,
                level=level,
                signal=signal,
                indicators=indicators,
                momentum=momentum,
                percentile=percentile,
                regime=regime,
                confidence=confidence
            )
        
            self._history.append(reading)
        
            return reading
        except Exception as e:
            logger.error(f"Error in calculate_index: {e}")
            raise
        
    def _calculate_volatility_indicator(
        self,
        df: pd.DataFrame,
        vix: Optional[float]
    ) -> SentimentIndicator:
        """Calculate volatility-based sentiment."""
        try:
            if vix is not None:
                # VIX: High = Fear, Low = Greed
                # Typical range: 10-40
                normalized = 100 - min(100, max(0, (vix - 10) / 30 * 100))
            else:
                # Use ATR-based volatility
                if len(df) < self.lookback_period:
                    normalized = 50
                else:
                    atr = self._calculate_atr(df, self.lookback_period)
                    avg_price = df['close'].mean()
                    atr_pct = (atr / avg_price) * 100
                
                    # ATR%: High = Fear, Low = Greed
                    # Typical range: 0.5% - 3%
                    normalized = 100 - min(100, max(0, (atr_pct - 0.5) / 2.5 * 100))
                
            signal = self._value_to_signal(normalized)
        
            return SentimentIndicator(
                name="Volatility",
                indicator_type=IndicatorType.VOLATILITY,
                raw_value=vix if vix else atr_pct,
                normalized_value=normalized,
                weight=self.weights[IndicatorType.VOLATILITY],
                signal=signal,
                description="High volatility = Fear, Low volatility = Greed"
            )
        except Exception as e:
            logger.error(f"Error in _calculate_volatility_indicator: {e}")
            raise
        
    def _calculate_momentum_indicator(
        self,
        df: pd.DataFrame
    ) -> SentimentIndicator:
        """Calculate momentum-based sentiment."""
        try:
            if len(df) < self.lookback_period:
                return SentimentIndicator(
                    name="Momentum",
                    indicator_type=IndicatorType.MOMENTUM,
                    raw_value=50,
                    normalized_value=50,
                    weight=self.weights[IndicatorType.MOMENTUM],
                    signal=SentimentSignal.NEUTRAL,
                    description="Insufficient data"
                )
            
            # RSI
            rsi = self._calculate_rsi(df, 14)
        
            # Price momentum (% change over lookback)
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-self.lookback_period]) / df['close'].iloc[-self.lookback_period] * 100
        
            # Combine RSI and price momentum
            # RSI > 70 = Greed, RSI < 30 = Fear
            rsi_normalized = rsi  # Already 0-100
        
            # Price momentum: +10% = Greed (100), -10% = Fear (0)
            mom_normalized = min(100, max(0, (price_change + 10) / 20 * 100))
        
            normalized = (rsi_normalized + mom_normalized) / 2
            signal = self._value_to_signal(normalized)
        
            return SentimentIndicator(
                name="Momentum",
                indicator_type=IndicatorType.MOMENTUM,
                raw_value=rsi,
                normalized_value=normalized,
                weight=self.weights[IndicatorType.MOMENTUM],
                signal=signal,
                description=f"RSI: {rsi:.1f}, Price Change: {price_change:.1f}%"
            )
        except Exception as e:
            logger.error(f"Error in _calculate_momentum_indicator: {e}")
            raise
        
    def _calculate_volume_indicator(
        self,
        df: pd.DataFrame
    ) -> SentimentIndicator:
        """Calculate volume-based sentiment."""
        try:
            if len(df) < self.lookback_period or 'volume' not in df.columns:
                return SentimentIndicator(
                    name="Volume",
                    indicator_type=IndicatorType.VOLUME,
                    raw_value=50,
                    normalized_value=50,
                    weight=self.weights[IndicatorType.VOLUME],
                    signal=SentimentSignal.NEUTRAL,
                    description="Insufficient data"
                )
            
            # Volume trend
            recent_vol = df['volume'].iloc[-5:].mean()
            avg_vol = df['volume'].iloc[-self.lookback_period:].mean()
        
            vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
            # High volume on up days = Greed
            # High volume on down days = Fear
            recent_return = df['close'].iloc[-1] - df['close'].iloc[-5]
        
            if recent_return > 0:
                # Up move with high volume = Greed
                normalized = min(100, 50 + (vol_ratio - 1) * 50)
            else:
                # Down move with high volume = Fear
                normalized = max(0, 50 - (vol_ratio - 1) * 50)
            
            signal = self._value_to_signal(normalized)
        
            return SentimentIndicator(
                name="Volume",
                indicator_type=IndicatorType.VOLUME,
                raw_value=vol_ratio,
                normalized_value=normalized,
                weight=self.weights[IndicatorType.VOLUME],
                signal=signal,
                description=f"Volume ratio: {vol_ratio:.2f}x average"
            )
        except Exception as e:
            logger.error(f"Error in _calculate_volume_indicator: {e}")
            raise
        
    def _calculate_breadth_indicator(
        self,
        df: pd.DataFrame,
        advance_decline: Optional[float]
    ) -> SentimentIndicator:
        """Calculate market breadth sentiment."""
        try:
            if advance_decline is not None:
                # A/D ratio: > 1 = Greed, < 1 = Fear
                # Typical range: 0.5 - 2.0
                normalized = min(100, max(0, (advance_decline - 0.5) / 1.5 * 100))
            else:
                # Use price-based proxy
                if len(df) < self.lookback_period:
                    normalized = 50
                else:
                    # % of days with positive close
                    positive_days = sum(1 for i in range(1, min(self.lookback_period, len(df))) 
                                       if df['close'].iloc[-i] > df['close'].iloc[-i-1])
                    normalized = (positive_days / (self.lookback_period - 1)) * 100
                
            signal = self._value_to_signal(normalized)
        
            return SentimentIndicator(
                name="Market Breadth",
                indicator_type=IndicatorType.BREADTH,
                raw_value=advance_decline if advance_decline else normalized / 100,
                normalized_value=normalized,
                weight=self.weights[IndicatorType.BREADTH],
                signal=signal,
                description="Advance/Decline ratio indicator"
            )
        except Exception as e:
            logger.error(f"Error in _calculate_breadth_indicator: {e}")
            raise
        
    def _calculate_options_indicator(
        self,
        put_call_ratio: Optional[float]
    ) -> SentimentIndicator:
        """Calculate options-based sentiment."""
        try:
            if put_call_ratio is None:
                return SentimentIndicator(
                    name="Options",
                    indicator_type=IndicatorType.OPTIONS,
                    raw_value=1.0,
                    normalized_value=50,
                    weight=self.weights[IndicatorType.OPTIONS],
                    signal=SentimentSignal.NEUTRAL,
                    description="No options data available"
                )
            
            # P/C ratio: High = Fear (contrarian bullish), Low = Greed (contrarian bearish)
            # Typical range: 0.7 - 1.3
            # Inverted: High P/C = Fear = Low index value
            normalized = 100 - min(100, max(0, (put_call_ratio - 0.7) / 0.6 * 100))
        
            signal = self._value_to_signal(normalized)
        
            return SentimentIndicator(
                name="Options (P/C Ratio)",
                indicator_type=IndicatorType.OPTIONS,
                raw_value=put_call_ratio,
                normalized_value=normalized,
                weight=self.weights[IndicatorType.OPTIONS],
                signal=signal,
                description=f"Put/Call ratio: {put_call_ratio:.2f}"
            )
        except Exception as e:
            logger.error(f"Error in _calculate_options_indicator: {e}")
            raise
        
    def _calculate_safe_haven_indicator(
        self,
        safe_haven_demand: Optional[float]
    ) -> SentimentIndicator:
        """Calculate safe haven demand sentiment."""
        try:
            if safe_haven_demand is None:
                return SentimentIndicator(
                    name="Safe Haven",
                    indicator_type=IndicatorType.SAFE_HAVEN,
                    raw_value=0,
                    normalized_value=50,
                    weight=self.weights[IndicatorType.SAFE_HAVEN],
                    signal=SentimentSignal.NEUTRAL,
                    description="No safe haven data available"
                )
            
            # High safe haven demand = Fear
            # Scale: -100 to +100 (positive = high demand)
            normalized = 50 - (safe_haven_demand / 2)
            normalized = min(100, max(0, normalized))
        
            signal = self._value_to_signal(normalized)
        
            return SentimentIndicator(
                name="Safe Haven Demand",
                indicator_type=IndicatorType.SAFE_HAVEN,
                raw_value=safe_haven_demand,
                normalized_value=normalized,
                weight=self.weights[IndicatorType.SAFE_HAVEN],
                signal=signal,
                description="Gold/Bond demand indicator"
            )
        except Exception as e:
            logger.error(f"Error in _calculate_safe_haven_indicator: {e}")
            raise
        
    def _calculate_junk_bond_indicator(
        self,
        credit_spread: Optional[float]
    ) -> SentimentIndicator:
        """Calculate junk bond spread sentiment."""
        try:
            if credit_spread is None:
                return SentimentIndicator(
                    name="Junk Bond Spread",
                    indicator_type=IndicatorType.JUNK_BOND,
                    raw_value=0,
                    normalized_value=50,
                    weight=self.weights[IndicatorType.JUNK_BOND],
                    signal=SentimentSignal.NEUTRAL,
                    description="No credit spread data available"
                )
            
            # High spread = Fear, Low spread = Greed
            # Typical range: 3% - 8%
            normalized = 100 - min(100, max(0, (credit_spread - 3) / 5 * 100))
        
            signal = self._value_to_signal(normalized)
        
            return SentimentIndicator(
                name="Junk Bond Spread",
                indicator_type=IndicatorType.JUNK_BOND,
                raw_value=credit_spread,
                normalized_value=normalized,
                weight=self.weights[IndicatorType.JUNK_BOND],
                signal=signal,
                description=f"Credit spread: {credit_spread:.2f}%"
            )
        except Exception as e:
            logger.error(f"Error in _calculate_junk_bond_indicator: {e}")
            raise
        
    def _calculate_social_indicator(
        self,
        social_sentiment: Optional[float]
    ) -> SentimentIndicator:
        """Calculate social media sentiment."""
        try:
            if social_sentiment is None:
                return SentimentIndicator(
                    name="Social Sentiment",
                    indicator_type=IndicatorType.SOCIAL,
                    raw_value=0,
                    normalized_value=50,
                    weight=self.weights[IndicatorType.SOCIAL],
                    signal=SentimentSignal.NEUTRAL,
                    description="No social data available"
                )
            
            # Social sentiment: -100 to +100
            normalized = (social_sentiment + 100) / 2
            normalized = min(100, max(0, normalized))
        
            signal = self._value_to_signal(normalized)
        
            return SentimentIndicator(
                name="Social Sentiment",
                indicator_type=IndicatorType.SOCIAL,
                raw_value=social_sentiment,
                normalized_value=normalized,
                weight=self.weights[IndicatorType.SOCIAL],
                signal=signal,
                description=f"Social sentiment: {social_sentiment:.1f}"
            )
        except Exception as e:
            logger.error(f"Error in _calculate_social_indicator: {e}")
            raise
        
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> float:
        """Calculate Average True Range."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
        
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
        
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean().iloc[-1]
        
            return float(atr) if not pd.isna(atr) else 0
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise
        
    def _calculate_rsi(self, df: pd.DataFrame, period: int) -> float:
        """Calculate RSI."""
        try:
            delta = df['close'].diff()
        
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
        
            avg_gain = gain.rolling(period).mean()
            avg_loss = loss.rolling(period).mean()
        
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
        except Exception as e:
            logger.error(f"Error in _calculate_rsi: {e}")
            raise
        
    def _get_sentiment_level(self, value: float) -> SentimentLevel:
        """Convert index value to sentiment level."""
        try:
            if value <= 20:
                return SentimentLevel.EXTREME_FEAR
            elif value <= 40:
                return SentimentLevel.FEAR
            elif value <= 60:
                return SentimentLevel.NEUTRAL
            elif value <= 80:
                return SentimentLevel.GREED
            else:
                return SentimentLevel.EXTREME_GREED
        except Exception as e:
            logger.error(f"Error in _get_sentiment_level: {e}")
            raise
            
    def _get_contrarian_signal(self, value: float) -> SentimentSignal:
        """Get contrarian trading signal."""
        try:
            if value <= 20:
                return SentimentSignal.STRONG_BUY
            elif value <= 35:
                return SentimentSignal.BUY
            elif value <= 65:
                return SentimentSignal.NEUTRAL
            elif value <= 80:
                return SentimentSignal.SELL
            else:
                return SentimentSignal.STRONG_SELL
        except Exception as e:
            logger.error(f"Error in _get_contrarian_signal: {e}")
            raise
            
    def _value_to_signal(self, value: float) -> SentimentSignal:
        """Convert normalized value to signal."""
        return self._get_contrarian_signal(value)
        
    def _calculate_percentile(self, value: float) -> float:
        """Calculate historical percentile."""
        try:
            if not self._history:
                return 50.0
            
            historical_values = [r.index_value for r in self._history]
            below = sum(1 for v in historical_values if v < value)
        
            return (below / len(historical_values)) * 100
        except Exception as e:
            logger.error(f"Error in _calculate_percentile: {e}")
            raise
        
    def _determine_regime(self, df: pd.DataFrame) -> str:
        """Determine current market regime."""
        try:
            if len(df) < 50:
                return "unknown"
            
            # Simple regime detection
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(50).mean().iloc[-1]
            current = df['close'].iloc[-1]
        
            if current > sma_20 > sma_50:
                return "bullish"
            elif current < sma_20 < sma_50:
                return "bearish"
            else:
                return "ranging"
        except Exception as e:
            logger.error(f"Error in _determine_regime: {e}")
            raise
            
    def _calculate_confidence(self, indicators: List[SentimentIndicator]) -> float:
        """Calculate confidence in reading."""
        # Confidence based on indicator agreement
        try:
            signals = [ind.signal for ind in indicators]
        
            bullish = sum(1 for s in signals if s in [SentimentSignal.BUY, SentimentSignal.STRONG_BUY])
            bearish = sum(1 for s in signals if s in [SentimentSignal.SELL, SentimentSignal.STRONG_SELL])
        
            agreement = max(bullish, bearish) / len(signals)
        
            return agreement * 100
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
        
    def detect_extremes(
        self,
        lookback_hours: int = 168  # 1 week
    ) -> List[SentimentExtreme]:
        """Detect sentiment extremes in history.
        
        Args:
            lookback_hours: Hours to look back
            
        Returns:
            List of detected extremes
        """
        try:
            extremes = []
        
            if len(self._history) < 10:
                return extremes
            
            cutoff = datetime.now() - timedelta(hours=lookback_hours)
            recent = [r for r in self._history if r.timestamp >= cutoff]
        
            # Find extreme fear periods
            fear_periods = []
            current_fear_start = None
        
            for reading in recent:
                if reading.level == SentimentLevel.EXTREME_FEAR:
                    if current_fear_start is None:
                        current_fear_start = reading
                else:
                    if current_fear_start is not None:
                        duration = (reading.timestamp - current_fear_start.timestamp).total_seconds() / 3600
                        fear_periods.append((current_fear_start, duration))
                        current_fear_start = None
                    
            for start, duration in fear_periods:
                extremes.append(SentimentExtreme(
                    timestamp=start.timestamp,
                    extreme_type='fear',
                    index_value=start.index_value,
                    duration_hours=int(duration),
                    historical_percentile=start.percentile,
                    contrarian_signal=SentimentSignal.STRONG_BUY,
                    expected_reversal_probability=min(90, 50 + (20 - start.index_value) * 2)
                ))
            
            # Find extreme greed periods
            greed_periods = []
            current_greed_start = None
        
            for reading in recent:
                if reading.level == SentimentLevel.EXTREME_GREED:
                    if current_greed_start is None:
                        current_greed_start = reading
                else:
                    if current_greed_start is not None:
                        duration = (reading.timestamp - current_greed_start.timestamp).total_seconds() / 3600
                        greed_periods.append((current_greed_start, duration))
                        current_greed_start = None
                    
            for start, duration in greed_periods:
                extremes.append(SentimentExtreme(
                    timestamp=start.timestamp,
                    extreme_type='greed',
                    index_value=start.index_value,
                    duration_hours=int(duration),
                    historical_percentile=start.percentile,
                    contrarian_signal=SentimentSignal.STRONG_SELL,
                    expected_reversal_probability=min(90, 50 + (start.index_value - 80) * 2)
                ))
            
            return extremes
        except Exception as e:
            logger.error(f"Error in detect_extremes: {e}")
            raise
        
    def detect_divergence(
        self,
        price_data: pd.DataFrame,
        periods: int = 10
    ) -> Optional[SentimentDivergence]:
        """Detect divergence between price and sentiment.
        
        Args:
            price_data: Price DataFrame
            periods: Periods to analyze
            
        Returns:
            SentimentDivergence if found
        """
        try:
            if len(self._history) < periods or len(price_data) < periods:
                return None
            
            # Get sentiment trend
            recent_readings = self._history[-periods:]
            sentiment_start = recent_readings[0].index_value
            sentiment_end = recent_readings[-1].index_value
            sentiment_change = sentiment_end - sentiment_start
        
            # Get price trend
            price_start = price_data['close'].iloc[-periods]
            price_end = price_data['close'].iloc[-1]
            price_change = (price_end - price_start) / price_start * 100
        
            # Detect divergence
            # Bullish divergence: Price down, sentiment up
            # Bearish divergence: Price up, sentiment down
        
            if price_change < -2 and sentiment_change > 10:
                return SentimentDivergence(
                    timestamp=datetime.now(),
                    divergence_type='bullish',
                    price_direction='down',
                    sentiment_direction='up',
                    strength=min(100, abs(price_change) + abs(sentiment_change)),
                    periods=periods
                )
            elif price_change > 2 and sentiment_change < -10:
                return SentimentDivergence(
                    timestamp=datetime.now(),
                    divergence_type='bearish',
                    price_direction='up',
                    sentiment_direction='down',
                    strength=min(100, abs(price_change) + abs(sentiment_change)),
                    periods=periods
                )
            
            return None
        except Exception as e:
            logger.error(f"Error in detect_divergence: {e}")
            raise
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current sentiment state."""
        try:
            if not self._history:
                return {'status': 'no_data'}
            
            current = self._history[-1]
        
            return {
                'current_index': current.index_value,
                'level': current.level.value,
                'signal': current.signal.value,
                'momentum': current.momentum,
                'percentile': current.percentile,
                'regime': current.regime,
                'confidence': current.confidence,
                'indicators': {
                    ind.name: {
                        'value': ind.normalized_value,
                        'signal': ind.signal.value
                    }
                    for ind in current.indicators
                },
                'history_length': len(self._history)
            }
        except Exception as e:
            logger.error(f"Error in get_summary: {e}")
            raise


# Convenience functions
def calculate_fear_greed(
    market_data: pd.DataFrame,
    vix: Optional[float] = None,
    put_call_ratio: Optional[float] = None
) -> float:
    """Quick function to calculate Fear and Greed Index."""
    try:
        calculator = FearGreedCalculator()
        reading = calculator.calculate_index(market_data, vix=vix, put_call_ratio=put_call_ratio)
        return reading.index_value
    except Exception as e:
        logger.error(f"Error in calculate_fear_greed: {e}")
        raise


def get_sentiment_signal(index_value: float) -> str:
    """Quick function to get trading signal from index value."""
    try:
        if index_value <= 20:
            return "STRONG_BUY"
        elif index_value <= 35:
            return "BUY"
        elif index_value <= 65:
            return "NEUTRAL"
        elif index_value <= 80:
            return "SELL"
        else:
            return "STRONG_SELL"
    except Exception as e:
        logger.error(f"Error in get_sentiment_signal: {e}")
        raise
