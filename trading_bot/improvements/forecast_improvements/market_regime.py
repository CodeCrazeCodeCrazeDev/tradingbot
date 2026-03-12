"""
Market Regime Detection - Improvement #7 (HIGH PRIORITY)
=========================================================

Full regime classification to adapt strategy to market conditions.

Features:
- Trending vs Ranging detection
- Volatility regime (low/normal/high/extreme)
- Momentum regime
- Liquidity regime
- Correlation regime
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import statistics
import math

logger = logging.getLogger(__name__)


class TrendRegime(Enum):
    """Trend regime types"""
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    WEAK_UPTREND = "weak_uptrend"
    RANGING = "ranging"
    WEAK_DOWNTREND = "weak_downtrend"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"


class VolatilityRegime(Enum):
    """Volatility regime types"""
    EXTREME_LOW = "extreme_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME_HIGH = "extreme_high"


class MomentumRegime(Enum):
    """Momentum regime types"""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class LiquidityRegime(Enum):
    """Liquidity regime types"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    VERY_LOW = "very_low"


class CorrelationRegime(Enum):
    """Correlation regime types"""
    RISK_ON = "risk_on"
    NORMAL = "normal"
    RISK_OFF = "risk_off"
    DECORRELATED = "decorrelated"


@dataclass
class MarketRegimeState:
    """Complete market regime state"""
    symbol: str
    trend: TrendRegime
    volatility: VolatilityRegime
    momentum: MomentumRegime
    liquidity: LiquidityRegime
    correlation: CorrelationRegime
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def is_favorable_for_trend_following(self) -> bool:
        """Check if regime favors trend following"""
        return (
            self.trend in [TrendRegime.STRONG_UPTREND, TrendRegime.UPTREND, 
                          TrendRegime.STRONG_DOWNTREND, TrendRegime.DOWNTREND] and
            self.volatility in [VolatilityRegime.NORMAL, VolatilityRegime.HIGH] and
            self.liquidity in [LiquidityRegime.NORMAL, LiquidityRegime.HIGH, LiquidityRegime.VERY_HIGH]
        )
    
    def is_favorable_for_mean_reversion(self) -> bool:
        """Check if regime favors mean reversion"""
        return (
            self.trend == TrendRegime.RANGING and
            self.volatility in [VolatilityRegime.LOW, VolatilityRegime.NORMAL] and
            self.momentum == MomentumRegime.NEUTRAL
        )
    
    def is_high_risk(self) -> bool:
        """Check if regime is high risk"""
        return (
            self.volatility in [VolatilityRegime.EXTREME_HIGH, VolatilityRegime.EXTREME_LOW] or
            self.liquidity in [LiquidityRegime.LOW, LiquidityRegime.VERY_LOW] or
            self.correlation == CorrelationRegime.RISK_OFF
        )


class TrendRangeClassifier:
    """Classifies market as trending or ranging"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.adx_period = self.config.get('adx_period', 14)
            self.trend_threshold = self.config.get('trend_threshold', 25)
            self.strong_trend_threshold = self.config.get('strong_trend_threshold', 40)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify(
        self,
        highs: List[float],
        lows: List[float],
        closes: List[float]
    ) -> Tuple[TrendRegime, float, Dict[str, Any]]:
        """Classify trend/range regime"""
        try:
            if len(closes) < self.adx_period * 2:
                return TrendRegime.RANGING, 0.5, {'error': 'Insufficient data'}
        
            # Calculate ADX
            adx = self._calculate_adx(highs, lows, closes)
        
            # Calculate directional movement
            plus_di, minus_di = self._calculate_di(highs, lows, closes)
        
            # Calculate trend direction using multiple methods
            sma_20 = sum(closes[-20:]) / 20
            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20
            current_price = closes[-1]
        
            # Determine trend direction
            trend_direction = 0
            if plus_di > minus_di:
                trend_direction = 1
            elif minus_di > plus_di:
                trend_direction = -1
        
            if current_price > sma_20 > sma_50:
                trend_direction += 1
            elif current_price < sma_20 < sma_50:
                trend_direction -= 1
        
            # Classify regime
            if adx >= self.strong_trend_threshold:
                if trend_direction > 0:
                    regime = TrendRegime.STRONG_UPTREND
                elif trend_direction < 0:
                    regime = TrendRegime.STRONG_DOWNTREND
                else:
                    regime = TrendRegime.RANGING
            elif adx >= self.trend_threshold:
                if trend_direction > 0:
                    regime = TrendRegime.UPTREND
                elif trend_direction < 0:
                    regime = TrendRegime.DOWNTREND
                else:
                    regime = TrendRegime.RANGING
            elif adx >= self.trend_threshold * 0.7:
                if trend_direction > 0:
                    regime = TrendRegime.WEAK_UPTREND
                elif trend_direction < 0:
                    regime = TrendRegime.WEAK_DOWNTREND
                else:
                    regime = TrendRegime.RANGING
            else:
                regime = TrendRegime.RANGING
        
            confidence = min(adx / self.strong_trend_threshold, 1.0)
        
            return regime, confidence, {
                'adx': adx,
                'plus_di': plus_di,
                'minus_di': minus_di,
                'trend_direction': trend_direction,
                'sma_20': sma_20,
                'sma_50': sma_50
            }
        except Exception as e:
            logger.error(f"Error in classify: {e}")
            raise
    
    def _calculate_adx(self, highs: List[float], lows: List[float], closes: List[float]) -> float:
        """Calculate ADX"""
        try:
            period = self.adx_period
        
            if len(highs) < period * 2:
                return 0.0
        
            # Calculate True Range and Directional Movement
            tr_values = []
            plus_dm = []
            minus_dm = []
        
            for i in range(1, len(highs)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                tr_values.append(tr)
            
                high_diff = highs[i] - highs[i-1]
                low_diff = lows[i-1] - lows[i]
            
                if high_diff > low_diff and high_diff > 0:
                    plus_dm.append(high_diff)
                else:
                    plus_dm.append(0)
            
                if low_diff > high_diff and low_diff > 0:
                    minus_dm.append(low_diff)
                else:
                    minus_dm.append(0)
        
            # Smooth values
            smoothed_tr = self._wilder_smooth(tr_values, period)
            smoothed_plus_dm = self._wilder_smooth(plus_dm, period)
            smoothed_minus_dm = self._wilder_smooth(minus_dm, period)
        
            if smoothed_tr == 0:
                return 0.0
        
            plus_di = 100 * smoothed_plus_dm / smoothed_tr
            minus_di = 100 * smoothed_minus_dm / smoothed_tr
        
            di_sum = plus_di + minus_di
            if di_sum == 0:
                return 0.0
        
            dx = 100 * abs(plus_di - minus_di) / di_sum
        
            return dx
        except Exception as e:
            logger.error(f"Error in _calculate_adx: {e}")
            raise
    
    def _calculate_di(self, highs: List[float], lows: List[float], closes: List[float]) -> Tuple[float, float]:
        """Calculate +DI and -DI"""
        try:
            period = self.adx_period
        
            if len(highs) < period * 2:
                return 0.0, 0.0
        
            tr_values = []
            plus_dm = []
            minus_dm = []
        
            for i in range(1, len(highs)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                tr_values.append(tr)
            
                high_diff = highs[i] - highs[i-1]
                low_diff = lows[i-1] - lows[i]
            
                if high_diff > low_diff and high_diff > 0:
                    plus_dm.append(high_diff)
                else:
                    plus_dm.append(0)
            
                if low_diff > high_diff and low_diff > 0:
                    minus_dm.append(low_diff)
                else:
                    minus_dm.append(0)
        
            smoothed_tr = self._wilder_smooth(tr_values, period)
            smoothed_plus_dm = self._wilder_smooth(plus_dm, period)
            smoothed_minus_dm = self._wilder_smooth(minus_dm, period)
        
            if smoothed_tr == 0:
                return 0.0, 0.0
        
            plus_di = 100 * smoothed_plus_dm / smoothed_tr
            minus_di = 100 * smoothed_minus_dm / smoothed_tr
        
            return plus_di, minus_di
        except Exception as e:
            logger.error(f"Error in _calculate_di: {e}")
            raise
    
    def _wilder_smooth(self, values: List[float], period: int) -> float:
        """Wilder's smoothing method"""
        try:
            if len(values) < period:
                return sum(values) / len(values) if values else 0
        
            first_sum = sum(values[:period])
            smoothed = first_sum
        
            for i in range(period, len(values)):
                smoothed = smoothed - (smoothed / period) + values[i]
        
            return smoothed / period
        except Exception as e:
            logger.error(f"Error in _wilder_smooth: {e}")
            raise


class VolatilityRegimeDetector:
    """Detects volatility regime"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.atr_period = self.config.get('atr_period', 14)
            self.lookback_period = self.config.get('lookback_period', 100)
            self.volatility_history: Dict[str, deque] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify(
        self,
        symbol: str,
        highs: List[float],
        lows: List[float],
        closes: List[float]
    ) -> Tuple[VolatilityRegime, float, Dict[str, Any]]:
        """Classify volatility regime"""
        try:
            if len(closes) < self.atr_period + 1:
                return VolatilityRegime.NORMAL, 0.5, {'error': 'Insufficient data'}
        
            # Calculate current ATR
            current_atr = self._calculate_atr(highs, lows, closes)
        
            # Normalize by price
            current_price = closes[-1]
            normalized_atr = current_atr / current_price if current_price > 0 else 0
        
            # Update history
            if symbol not in self.volatility_history:
                self.volatility_history[symbol] = deque(maxlen=self.lookback_period)
            self.volatility_history[symbol].append(normalized_atr)
        
            # Calculate percentile
            history = list(self.volatility_history[symbol])
            if len(history) < 20:
                return VolatilityRegime.NORMAL, 0.5, {'atr': current_atr, 'normalized_atr': normalized_atr}
        
            sorted_history = sorted(history)
            percentile = sorted_history.index(min(sorted_history, key=lambda x: abs(x - normalized_atr))) / len(sorted_history)
        
            # Classify based on percentile
            if percentile <= 0.1:
                regime = VolatilityRegime.EXTREME_LOW
            elif percentile <= 0.25:
                regime = VolatilityRegime.LOW
            elif percentile <= 0.75:
                regime = VolatilityRegime.NORMAL
            elif percentile <= 0.9:
                regime = VolatilityRegime.HIGH
            else:
                regime = VolatilityRegime.EXTREME_HIGH
        
            confidence = 1 - abs(percentile - 0.5) * 2  # Higher confidence at extremes
        
            return regime, confidence, {
                'atr': current_atr,
                'normalized_atr': normalized_atr,
                'percentile': percentile,
                'history_length': len(history)
            }
        except Exception as e:
            logger.error(f"Error in classify: {e}")
            raise
    
    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float]) -> float:
        """Calculate ATR"""
        try:
            period = self.atr_period
        
            if len(highs) < period + 1:
                return 0.0
        
            tr_values = []
            for i in range(1, len(highs)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                tr_values.append(tr)
        
            return sum(tr_values[-period:]) / period
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise


class MomentumRegimeDetector:
    """Detects momentum regime"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.rsi_period = self.config.get('rsi_period', 14)
            self.macd_fast = self.config.get('macd_fast', 12)
            self.macd_slow = self.config.get('macd_slow', 26)
            self.macd_signal = self.config.get('macd_signal', 9)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify(self, closes: List[float]) -> Tuple[MomentumRegime, float, Dict[str, Any]]:
        """Classify momentum regime"""
        try:
            if len(closes) < self.macd_slow + self.macd_signal:
                return MomentumRegime.NEUTRAL, 0.5, {'error': 'Insufficient data'}
        
            # Calculate RSI
            rsi = self._calculate_rsi(closes)
        
            # Calculate MACD
            macd, signal, histogram = self._calculate_macd(closes)
        
            # Calculate momentum score
            momentum_score = 0
        
            # RSI contribution
            if rsi > 70:
                momentum_score += 2
            elif rsi > 60:
                momentum_score += 1
            elif rsi < 30:
                momentum_score -= 2
            elif rsi < 40:
                momentum_score -= 1
        
            # MACD contribution
            if macd > signal and histogram > 0:
                momentum_score += 1
                if histogram > abs(macd) * 0.1:  # Strong histogram
                    momentum_score += 1
            elif macd < signal and histogram < 0:
                momentum_score -= 1
                if abs(histogram) > abs(macd) * 0.1:
                    momentum_score -= 1
        
            # Price momentum (rate of change)
            roc_10 = (closes[-1] - closes[-11]) / closes[-11] if len(closes) > 10 else 0
            if roc_10 > 0.02:  # 2% gain
                momentum_score += 1
            elif roc_10 < -0.02:
                momentum_score -= 1
        
            # Classify
            if momentum_score >= 4:
                regime = MomentumRegime.STRONG_BULLISH
            elif momentum_score >= 2:
                regime = MomentumRegime.BULLISH
            elif momentum_score <= -4:
                regime = MomentumRegime.STRONG_BEARISH
            elif momentum_score <= -2:
                regime = MomentumRegime.BEARISH
            else:
                regime = MomentumRegime.NEUTRAL
        
            confidence = min(abs(momentum_score) / 5, 1.0)
        
            return regime, confidence, {
                'rsi': rsi,
                'macd': macd,
                'signal': signal,
                'histogram': histogram,
                'roc_10': roc_10,
                'momentum_score': momentum_score
            }
        except Exception as e:
            logger.error(f"Error in classify: {e}")
            raise
    
    def _calculate_rsi(self, closes: List[float]) -> float:
        """Calculate RSI"""
        try:
            period = self.rsi_period
        
            if len(closes) < period + 1:
                return 50.0
        
            gains = []
            losses = []
        
            for i in range(1, len(closes)):
                change = closes[i] - closes[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
        
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
        
            if avg_loss == 0:
                return 100.0
        
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
            return rsi
        except Exception as e:
            logger.error(f"Error in _calculate_rsi: {e}")
            raise
    
    def _calculate_macd(self, closes: List[float]) -> Tuple[float, float, float]:
        """Calculate MACD"""
        try:
            ema_fast = self._calculate_ema(closes, self.macd_fast)
            ema_slow = self._calculate_ema(closes, self.macd_slow)
        
            macd = ema_fast - ema_slow
        
            # Calculate signal line (EMA of MACD)
            macd_values = []
            for i in range(self.macd_slow, len(closes) + 1):
                fast = self._calculate_ema(closes[:i], self.macd_fast)
                slow = self._calculate_ema(closes[:i], self.macd_slow)
                macd_values.append(fast - slow)
        
            signal = self._calculate_ema(macd_values, self.macd_signal) if len(macd_values) >= self.macd_signal else macd
            histogram = macd - signal
        
            return macd, signal, histogram
        except Exception as e:
            logger.error(f"Error in _calculate_macd: {e}")
            raise
    
    def _calculate_ema(self, data: List[float], period: int) -> float:
        """Calculate EMA"""
        try:
            if len(data) < period:
                return sum(data) / len(data) if data else 0
        
            multiplier = 2 / (period + 1)
            ema = sum(data[:period]) / period
        
            for price in data[period:]:
                ema = (price - ema) * multiplier + ema
        
            return ema
        except Exception as e:
            logger.error(f"Error in _calculate_ema: {e}")
            raise


class LiquidityRegimeDetector:
    """Detects liquidity regime"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.volume_lookback = self.config.get('volume_lookback', 20)
            self.spread_threshold = self.config.get('spread_threshold', 0.001)  # 0.1%
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify(
        self,
        volumes: List[float],
        spreads: List[float] = None,
        bid_ask_depth: Dict[str, float] = None
    ) -> Tuple[LiquidityRegime, float, Dict[str, Any]]:
        """Classify liquidity regime"""
        try:
            if len(volumes) < self.volume_lookback:
                return LiquidityRegime.NORMAL, 0.5, {'error': 'Insufficient data'}
        
            # Calculate volume metrics
            recent_volume = sum(volumes[-5:]) / 5
            avg_volume = sum(volumes[-self.volume_lookback:]) / self.volume_lookback
        
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
            # Calculate spread metrics if available
            spread_score = 0
            if spreads:
                recent_spread = sum(spreads[-5:]) / 5
                avg_spread = sum(spreads[-self.volume_lookback:]) / self.volume_lookback
                spread_ratio = recent_spread / avg_spread if avg_spread > 0 else 1.0
            
                if spread_ratio < 0.8:
                    spread_score = 1  # Tighter spreads = more liquidity
                elif spread_ratio > 1.5:
                    spread_score = -2  # Wider spreads = less liquidity
        
            # Calculate depth score if available
            depth_score = 0
            if bid_ask_depth:
                bid_depth = bid_ask_depth.get('bid_depth', 0)
                ask_depth = bid_ask_depth.get('ask_depth', 0)
                total_depth = bid_depth + ask_depth
            
                # Compare to typical depth (configurable)
                typical_depth = self.config.get('typical_depth', 1000)
                depth_ratio = total_depth / typical_depth if typical_depth > 0 else 1.0
            
                if depth_ratio > 1.5:
                    depth_score = 1
                elif depth_ratio < 0.5:
                    depth_score = -1
        
            # Combine scores
            liquidity_score = 0
        
            if volume_ratio > 1.5:
                liquidity_score += 2
            elif volume_ratio > 1.2:
                liquidity_score += 1
            elif volume_ratio < 0.5:
                liquidity_score -= 2
            elif volume_ratio < 0.8:
                liquidity_score -= 1
        
            liquidity_score += spread_score + depth_score
        
            # Classify
            if liquidity_score >= 3:
                regime = LiquidityRegime.VERY_HIGH
            elif liquidity_score >= 1:
                regime = LiquidityRegime.HIGH
            elif liquidity_score <= -3:
                regime = LiquidityRegime.VERY_LOW
            elif liquidity_score <= -1:
                regime = LiquidityRegime.LOW
            else:
                regime = LiquidityRegime.NORMAL
        
            confidence = min(abs(liquidity_score) / 4, 1.0)
        
            return regime, confidence, {
                'volume_ratio': volume_ratio,
                'recent_volume': recent_volume,
                'avg_volume': avg_volume,
                'liquidity_score': liquidity_score
            }
        except Exception as e:
            logger.error(f"Error in classify: {e}")
            raise


class CorrelationRegimeDetector:
    """Detects correlation regime (risk-on/risk-off)"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.correlation_period = self.config.get('correlation_period', 20)
            self.risk_assets = self.config.get('risk_assets', ['SPY', 'QQQ', 'AUDUSD', 'NZDUSD'])
            self.safe_assets = self.config.get('safe_assets', ['GLD', 'TLT', 'USDJPY', 'USDCHF'])
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify(
        self,
        asset_returns: Dict[str, List[float]]
    ) -> Tuple[CorrelationRegime, float, Dict[str, Any]]:
        """Classify correlation regime"""
        try:
            if not asset_returns:
                return CorrelationRegime.NORMAL, 0.5, {'error': 'No asset returns provided'}
        
            # Calculate correlations between risk assets
            risk_correlations = []
            for i, asset1 in enumerate(self.risk_assets):
                if asset1 not in asset_returns:
                    continue
                for asset2 in self.risk_assets[i+1:]:
                    if asset2 not in asset_returns:
                        continue
                    corr = self._calculate_correlation(
                        asset_returns[asset1],
                        asset_returns[asset2]
                    )
                    if corr is not None:
                        risk_correlations.append(corr)
        
            # Calculate risk-safe correlations
            risk_safe_correlations = []
            for risk_asset in self.risk_assets:
                if risk_asset not in asset_returns:
                    continue
                for safe_asset in self.safe_assets:
                    if safe_asset not in asset_returns:
                        continue
                    corr = self._calculate_correlation(
                        asset_returns[risk_asset],
                        asset_returns[safe_asset]
                    )
                    if corr is not None:
                        risk_safe_correlations.append(corr)
        
            # Analyze correlations
            avg_risk_corr = statistics.mean(risk_correlations) if risk_correlations else 0
            avg_risk_safe_corr = statistics.mean(risk_safe_correlations) if risk_safe_correlations else 0
        
            # Classify regime
            if avg_risk_corr > 0.7 and avg_risk_safe_corr < -0.3:
                regime = CorrelationRegime.RISK_OFF
            elif avg_risk_corr > 0.5 and avg_risk_safe_corr > 0:
                regime = CorrelationRegime.RISK_ON
            elif avg_risk_corr < 0.3:
                regime = CorrelationRegime.DECORRELATED
            else:
                regime = CorrelationRegime.NORMAL
        
            confidence = abs(avg_risk_corr)
        
            return regime, confidence, {
                'avg_risk_correlation': avg_risk_corr,
                'avg_risk_safe_correlation': avg_risk_safe_corr,
                'num_risk_correlations': len(risk_correlations),
                'num_risk_safe_correlations': len(risk_safe_correlations)
            }
        except Exception as e:
            logger.error(f"Error in classify: {e}")
            raise
    
    def _calculate_correlation(self, returns1: List[float], returns2: List[float]) -> Optional[float]:
        """Calculate correlation between two return series"""
        try:
            min_len = min(len(returns1), len(returns2))
        
            if min_len < self.correlation_period:
                return None
        
            r1 = returns1[-self.correlation_period:]
            r2 = returns2[-self.correlation_period:]
        
            mean1 = statistics.mean(r1)
            mean2 = statistics.mean(r2)
        
            numerator = sum((r1[i] - mean1) * (r2[i] - mean2) for i in range(len(r1)))
        
            std1 = statistics.stdev(r1) if len(r1) > 1 else 0
            std2 = statistics.stdev(r2) if len(r2) > 1 else 0
        
            if std1 == 0 or std2 == 0:
                return None
        
            denominator = std1 * std2 * len(r1)
        
            return numerator / denominator if denominator != 0 else None
        except Exception as e:
            logger.error(f"Error in _calculate_correlation: {e}")
            raise


class MarketRegimeDetector:
    """
    Master market regime detection system.
    Combines all regime classifiers.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize components
            self.trend_classifier = TrendRangeClassifier(self.config)
            self.volatility_detector = VolatilityRegimeDetector(self.config)
            self.momentum_detector = MomentumRegimeDetector(self.config)
            self.liquidity_detector = LiquidityRegimeDetector(self.config)
            self.correlation_detector = CorrelationRegimeDetector(self.config)
        
            # Regime history
            self.regime_history: Dict[str, deque] = {}
            self.history_size = self.config.get('history_size', 100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_regime(
        self,
        symbol: str,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        spreads: List[float] = None,
        asset_returns: Dict[str, List[float]] = None
    ) -> MarketRegimeState:
        """Detect complete market regime"""
        # Trend regime
        try:
            trend, trend_conf, trend_details = self.trend_classifier.classify(highs, lows, closes)
        
            # Volatility regime
            vol, vol_conf, vol_details = self.volatility_detector.classify(symbol, highs, lows, closes)
        
            # Momentum regime
            mom, mom_conf, mom_details = self.momentum_detector.classify(closes)
        
            # Liquidity regime
            liq, liq_conf, liq_details = self.liquidity_detector.classify(volumes, spreads)
        
            # Correlation regime
            if asset_returns:
                corr, corr_conf, corr_details = self.correlation_detector.classify(asset_returns)
            else:
                corr, corr_conf, corr_details = CorrelationRegime.NORMAL, 0.5, {}
        
            # Calculate overall confidence
            confidences = [trend_conf, vol_conf, mom_conf, liq_conf, corr_conf]
            overall_confidence = statistics.mean(confidences)
        
            # Create regime state
            state = MarketRegimeState(
                symbol=symbol,
                trend=trend,
                volatility=vol,
                momentum=mom,
                liquidity=liq,
                correlation=corr,
                confidence=overall_confidence,
                details={
                    'trend': trend_details,
                    'volatility': vol_details,
                    'momentum': mom_details,
                    'liquidity': liq_details,
                    'correlation': corr_details
                }
            )
        
            # Update history
            if symbol not in self.regime_history:
                self.regime_history[symbol] = deque(maxlen=self.history_size)
            self.regime_history[symbol].append(state)
        
            logger.info(f"Regime: {symbol} - Trend:{trend.value}, Vol:{vol.value}, Mom:{mom.value}")
            return state
        except Exception as e:
            logger.error(f"Error in detect_regime: {e}")
            raise
    
    def get_regime_summary(self, symbol: str) -> Dict[str, Any]:
        """Get regime summary for symbol"""
        try:
            if symbol not in self.regime_history or not self.regime_history[symbol]:
                return {'error': 'No regime history'}
        
            current = self.regime_history[symbol][-1]
        
            return {
                'symbol': symbol,
                'trend': current.trend.value,
                'volatility': current.volatility.value,
                'momentum': current.momentum.value,
                'liquidity': current.liquidity.value,
                'correlation': current.correlation.value,
                'confidence': current.confidence,
                'favorable_for_trend': current.is_favorable_for_trend_following(),
                'favorable_for_mean_reversion': current.is_favorable_for_mean_reversion(),
                'high_risk': current.is_high_risk(),
                'timestamp': current.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_regime_summary: {e}")
            raise
    
    def get_strategy_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Get strategy recommendation based on regime"""
        try:
            if symbol not in self.regime_history or not self.regime_history[symbol]:
                return {'strategy': 'wait', 'reason': 'No regime data'}
        
            state = self.regime_history[symbol][-1]
        
            if state.is_high_risk():
                return {
                    'strategy': 'reduce_exposure',
                    'reason': 'High risk regime detected',
                    'position_size_multiplier': 0.5
                }
        
            if state.is_favorable_for_trend_following():
                return {
                    'strategy': 'trend_following',
                    'reason': f'Strong {state.trend.value} with {state.volatility.value} volatility',
                    'position_size_multiplier': 1.0
                }
        
            if state.is_favorable_for_mean_reversion():
                return {
                    'strategy': 'mean_reversion',
                    'reason': 'Ranging market with stable volatility',
                    'position_size_multiplier': 0.8
                }
        
            return {
                'strategy': 'cautious',
                'reason': 'Mixed regime signals',
                'position_size_multiplier': 0.7
            }
        except Exception as e:
            logger.error(f"Error in get_strategy_recommendation: {e}")
            raise
    
    def detect_regime_change(self, symbol: str) -> Tuple[bool, str]:
        """Detect if regime has changed"""
        try:
            if symbol not in self.regime_history or len(self.regime_history[symbol]) < 2:
                return False, "Insufficient history"
        
            current = self.regime_history[symbol][-1]
            previous = self.regime_history[symbol][-2]
        
            changes = []
        
            if current.trend != previous.trend:
                changes.append(f"Trend: {previous.trend.value} -> {current.trend.value}")
        
            if current.volatility != previous.volatility:
                changes.append(f"Volatility: {previous.volatility.value} -> {current.volatility.value}")
        
            if current.momentum != previous.momentum:
                changes.append(f"Momentum: {previous.momentum.value} -> {current.momentum.value}")
        
            if changes:
                return True, "; ".join(changes)
        
            return False, "No regime change"
        except Exception as e:
            logger.error(f"Error in detect_regime_change: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get regime detection statistics"""
        try:
            stats = {}
        
            for symbol, history in self.regime_history.items():
                if not history:
                    continue
            
                trend_dist = {}
                vol_dist = {}
            
                for state in history:
                    trend_dist[state.trend.value] = trend_dist.get(state.trend.value, 0) + 1
                    vol_dist[state.volatility.value] = vol_dist.get(state.volatility.value, 0) + 1
            
                stats[symbol] = {
                    'history_length': len(history),
                    'trend_distribution': trend_dist,
                    'volatility_distribution': vol_dist,
                    'avg_confidence': statistics.mean(s.confidence for s in history)
                }
        
            return stats
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise
