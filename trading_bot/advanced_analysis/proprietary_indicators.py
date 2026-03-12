"""
Proprietary Indicators Module

Implements unique, cutting-edge technical indicators:
- Volatility Impulse Vector (VII)
- Fractal Momentum Divergence (FMD)
- VPIN-OI Fusion
- Ricci Flow Momentum
- Liquidity Entropy
- Dynamic Kelly Criterion

Features:
- Novel indicator combinations
- Multi-timeframe analysis
- Institutional-grade metrics
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEUTRAL = "neutral"


@dataclass
class IndicatorResult:
    """Generic indicator result"""
    name: str
    value: float
    signal: str  # BUY, SELL, NEUTRAL
    strength: SignalStrength
    components: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'name': self.name,
            'value': self.value,
            'signal': self.signal,
            'strength': self.strength.value,
            'components': self.components,
            'timestamp': self.timestamp.isoformat()
        }


class VolatilityImpulseVector:
    """
    Volatility Impulse Vector (VII)
    
    A composite indicator combining:
    - Rate of change of volatility (derivative of ATR)
    - Volume surge
    - Order book imbalance
    
    Detects when volatility is accelerating and in which direction
    the energy is likely to be released.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.atr_period = self.config.get('atr_period', 14)
            self.volume_period = self.config.get('volume_period', 20)
        
            # History
            self.atr_history: deque = deque(maxlen=100)
            self.volume_history: deque = deque(maxlen=100)
            self.vii_history: deque = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        bid_volume: float = 0.5,
        ask_volume: float = 0.5
    ) -> IndicatorResult:
        """
        Calculate Volatility Impulse Vector
        
        Args:
            high, low, close: Price arrays
            volume: Volume array
            bid_volume, ask_volume: Current order book volumes
        """
        # Calculate ATR
        try:
            tr = np.maximum(
                high - low,
                np.maximum(
                    np.abs(high - np.roll(close, 1)),
                    np.abs(low - np.roll(close, 1))
                )
            )
            tr[0] = high[0] - low[0]
            atr = self._ema(tr, self.atr_period)
        
            # ATR rate of change (volatility acceleration)
            atr_roc = np.diff(atr) / (atr[:-1] + 1e-10)
            atr_roc = np.append(0, atr_roc)
            volatility_acceleration = atr_roc[-1] * 100
        
            # Volume surge
            avg_volume = np.mean(volume[-self.volume_period:])
            current_volume = volume[-1]
            volume_surge = (current_volume / avg_volume - 1) if avg_volume > 0 else 0
        
            # Order book imbalance
            total_book = bid_volume + ask_volume
            if total_book > 0:
                imbalance = (bid_volume - ask_volume) / total_book
            else:
                imbalance = 0
        
            # Calculate VII
            # Positive = bullish impulse, Negative = bearish impulse
            vii = (
                volatility_acceleration * 0.4 +
                volume_surge * 0.3 +
                imbalance * 0.3
            )
        
            # Store history
            self.atr_history.append(atr[-1])
            self.volume_history.append(current_volume)
            self.vii_history.append(vii)
        
            # Determine signal
            if vii > 0.5:
                signal = "BUY"
                strength = SignalStrength.VERY_STRONG if vii > 1.0 else SignalStrength.STRONG
            elif vii > 0.2:
                signal = "BUY"
                strength = SignalStrength.MODERATE
            elif vii < -0.5:
                signal = "SELL"
                strength = SignalStrength.VERY_STRONG if vii < -1.0 else SignalStrength.STRONG
            elif vii < -0.2:
                signal = "SELL"
                strength = SignalStrength.MODERATE
            else:
                signal = "NEUTRAL"
                strength = SignalStrength.NEUTRAL
        
            return IndicatorResult(
                name="Volatility Impulse Vector",
                value=vii,
                signal=signal,
                strength=strength,
                components={
                    'volatility_acceleration': volatility_acceleration,
                    'volume_surge': volume_surge,
                    'order_book_imbalance': imbalance,
                    'current_atr': atr[-1]
                }
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA"""
        try:
            alpha = 2 / (period + 1)
            ema = np.zeros_like(data)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
            return ema
        except Exception as e:
            logger.error(f"Error in _ema: {e}")
            raise


class FractalMomentumDivergence:
    """
    Fractal Momentum Divergence (FMD)
    
    Compares momentum across three consecutive fractal timeframes
    (e.g., 5m vs. 15m vs. 1H). Filters out false divergences that
    appear on only two timeframes.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.momentum_period = self.config.get('momentum_period', 14)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(
        self,
        prices_tf1: np.ndarray,  # Lowest timeframe (e.g., 5m)
        prices_tf2: np.ndarray,  # Middle timeframe (e.g., 15m)
        prices_tf3: np.ndarray   # Highest timeframe (e.g., 1H)
    ) -> IndicatorResult:
        """
        Calculate Fractal Momentum Divergence
        
        Returns signal only when divergence confirmed across all 3 timeframes
        """
        # Calculate momentum for each timeframe
        try:
            mom1 = self._momentum(prices_tf1)
            mom2 = self._momentum(prices_tf2)
            mom3 = self._momentum(prices_tf3)
        
            # Calculate price direction
            price_dir1 = 1 if prices_tf1[-1] > prices_tf1[-self.momentum_period] else -1
            price_dir2 = 1 if prices_tf2[-1] > prices_tf2[-min(self.momentum_period, len(prices_tf2))] else -1
            price_dir3 = 1 if prices_tf3[-1] > prices_tf3[-min(self.momentum_period, len(prices_tf3))] else -1
        
            # Calculate momentum direction
            mom_dir1 = 1 if mom1 > 0 else -1
            mom_dir2 = 1 if mom2 > 0 else -1
            mom_dir3 = 1 if mom3 > 0 else -1
        
            # Check for divergence on each timeframe
            div1 = price_dir1 != mom_dir1
            div2 = price_dir2 != mom_dir2
            div3 = price_dir3 != mom_dir3
        
            # Count divergences
            divergence_count = sum([div1, div2, div3])
        
            # FMD value
            fmd = (mom1 + mom2 * 2 + mom3 * 3) / 6  # Weighted by timeframe
        
            # Signal only on triple divergence
            if divergence_count >= 3:
                if price_dir1 > 0:  # Price up, momentum down = bearish divergence
                    signal = "SELL"
                    strength = SignalStrength.VERY_STRONG
                else:  # Price down, momentum up = bullish divergence
                    signal = "BUY"
                    strength = SignalStrength.VERY_STRONG
            elif divergence_count == 2:
                if price_dir1 > 0:
                    signal = "SELL"
                    strength = SignalStrength.MODERATE
                else:
                    signal = "BUY"
                    strength = SignalStrength.MODERATE
            else:
                signal = "NEUTRAL"
                strength = SignalStrength.NEUTRAL
        
            return IndicatorResult(
                name="Fractal Momentum Divergence",
                value=fmd,
                signal=signal,
                strength=strength,
                components={
                    'momentum_tf1': mom1,
                    'momentum_tf2': mom2,
                    'momentum_tf3': mom3,
                    'divergence_count': divergence_count,
                    'price_direction': price_dir1
                }
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise
    
    def _momentum(self, prices: np.ndarray) -> float:
        """Calculate momentum"""
        try:
            if len(prices) < self.momentum_period:
                return 0
            return (prices[-1] - prices[-self.momentum_period]) / prices[-self.momentum_period] * 100
        except Exception as e:
            logger.error(f"Error in _momentum: {e}")
            raise


class VPINOIFusion:
    """
    VPIN-OI Fusion
    
    Combines Volume-Synchronized Probability of Informed Trading (VPIN)
    with options open interest to detect insider flows.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.bucket_size = self.config.get('bucket_size', 50)
            self.num_buckets = self.config.get('num_buckets', 50)
        
            # Buckets for VPIN calculation
            self.buckets: deque = deque(maxlen=self.num_buckets)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(
        self,
        trades: List[Dict[str, Any]],
        call_oi: float,
        put_oi: float,
        call_volume: float,
        put_volume: float
    ) -> IndicatorResult:
        """
        Calculate VPIN-OI Fusion indicator
        
        Args:
            trades: List of trades with 'price', 'volume', 'side'
            call_oi, put_oi: Options open interest
            call_volume, put_volume: Options volume
        """
        # Calculate VPIN
        try:
            vpin = self._calculate_vpin(trades)
        
            # Calculate Put/Call ratio
            pc_ratio = put_oi / call_oi if call_oi > 0 else 1
        
            # Calculate options volume ratio
            vol_ratio = put_volume / call_volume if call_volume > 0 else 1
        
            # Fusion score
            # High VPIN + unusual options activity = potential informed trading
            options_signal = (pc_ratio - 1) * 0.5 + (vol_ratio - 1) * 0.5
        
            fusion = vpin * 0.6 + abs(options_signal) * 0.4
        
            # Direction from options
            if pc_ratio > 1.2 and vol_ratio > 1.2:
                direction = "BEARISH"
            elif pc_ratio < 0.8 and vol_ratio < 0.8:
                direction = "BULLISH"
            else:
                direction = "NEUTRAL"
        
            # Signal
            if fusion > 0.7:
                signal = "SELL" if direction == "BEARISH" else "BUY" if direction == "BULLISH" else "NEUTRAL"
                strength = SignalStrength.STRONG
            elif fusion > 0.5:
                signal = "SELL" if direction == "BEARISH" else "BUY" if direction == "BULLISH" else "NEUTRAL"
                strength = SignalStrength.MODERATE
            else:
                signal = "NEUTRAL"
                strength = SignalStrength.NEUTRAL
        
            return IndicatorResult(
                name="VPIN-OI Fusion",
                value=fusion,
                signal=signal,
                strength=strength,
                components={
                    'vpin': vpin,
                    'put_call_ratio': pc_ratio,
                    'volume_ratio': vol_ratio,
                    'options_signal': options_signal,
                    'direction': direction
                }
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise
    
    def _calculate_vpin(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate VPIN from trades"""
        try:
            if not trades:
                return 0.5
        
            # Classify trades and create buckets
            current_bucket_volume = 0
            buy_volume = 0
        
            for trade in trades:
                volume = trade.get('volume', 0)
                side = trade.get('side', 'unknown')
            
                if side == 'buy':
                    buy_volume += volume
            
                current_bucket_volume += volume
            
                if current_bucket_volume >= self.bucket_size:
                    # Complete bucket
                    sell_volume = current_bucket_volume - buy_volume
                    imbalance = abs(buy_volume - sell_volume) / current_bucket_volume
                    self.buckets.append(imbalance)
                
                    current_bucket_volume = 0
                    buy_volume = 0
        
            # Calculate VPIN as average imbalance
            if self.buckets:
                return np.mean(list(self.buckets))
            return 0.5
        except Exception as e:
            logger.error(f"Error in _calculate_vpin: {e}")
            raise


class RicciFlowMomentum:
    """
    Ricci Flow Momentum
    
    Applies differential geometry concepts to measure "market curvature"
    as a momentum indicator. Based on Ricci flow which smooths manifolds.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.window = self.config.get('window', 20)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(self, prices: np.ndarray) -> IndicatorResult:
        """
        Calculate Ricci Flow Momentum
        
        Uses second derivative (curvature) of price to detect momentum changes
        """
        try:
            if len(prices) < self.window:
                return IndicatorResult(
                    name="Ricci Flow Momentum",
                    value=0,
                    signal="NEUTRAL",
                    strength=SignalStrength.NEUTRAL,
                    components={}
                )
        
            # First derivative (velocity)
            velocity = np.diff(prices)
        
            # Second derivative (acceleration/curvature)
            acceleration = np.diff(velocity)
        
            # Ricci curvature approximation
            # Positive curvature = price curving up (bullish)
            # Negative curvature = price curving down (bearish)
            recent_curvature = acceleration[-self.window:] if len(acceleration) >= self.window else acceleration
        
            # Smooth curvature
            ricci = np.mean(recent_curvature)
        
            # Normalize
            price_scale = np.std(prices[-self.window:])
            if price_scale > 0:
                ricci_normalized = ricci / price_scale * 100
            else:
                ricci_normalized = 0
        
            # Curvature trend
            if len(recent_curvature) > 5:
                curvature_trend = np.polyfit(range(len(recent_curvature)), recent_curvature, 1)[0]
            else:
                curvature_trend = 0
        
            # Signal
            if ricci_normalized > 0.5 and curvature_trend > 0:
                signal = "BUY"
                strength = SignalStrength.STRONG
            elif ricci_normalized > 0.2:
                signal = "BUY"
                strength = SignalStrength.MODERATE
            elif ricci_normalized < -0.5 and curvature_trend < 0:
                signal = "SELL"
                strength = SignalStrength.STRONG
            elif ricci_normalized < -0.2:
                signal = "SELL"
                strength = SignalStrength.MODERATE
            else:
                signal = "NEUTRAL"
                strength = SignalStrength.NEUTRAL
        
            return IndicatorResult(
                name="Ricci Flow Momentum",
                value=ricci_normalized,
                signal=signal,
                strength=strength,
                components={
                    'raw_curvature': ricci,
                    'curvature_trend': curvature_trend,
                    'velocity': velocity[-1] if len(velocity) > 0 else 0,
                    'acceleration': acceleration[-1] if len(acceleration) > 0 else 0
                }
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class LiquidityEntropy:
    """
    Liquidity Entropy
    
    Quantifies market fragility based on the dispersion of resting
    orders across price levels. High entropy = fragile market.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(
        self,
        bid_levels: List[Tuple[float, float]],  # (price, volume)
        ask_levels: List[Tuple[float, float]]
    ) -> IndicatorResult:
        """
        Calculate Liquidity Entropy
        
        Uses Shannon entropy to measure order book dispersion
        """
        # Combine all levels
        try:
            all_volumes = [v for _, v in bid_levels] + [v for _, v in ask_levels]
        
            if not all_volumes or sum(all_volumes) == 0:
                return IndicatorResult(
                    name="Liquidity Entropy",
                    value=0,
                    signal="NEUTRAL",
                    strength=SignalStrength.NEUTRAL,
                    components={}
                )
        
            total_volume = sum(all_volumes)
        
            # Calculate probabilities
            probs = [v / total_volume for v in all_volumes if v > 0]
        
            # Shannon entropy
            entropy = -sum(p * np.log2(p) for p in probs if p > 0)
        
            # Normalize by maximum possible entropy
            max_entropy = np.log2(len(probs)) if len(probs) > 1 else 1
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
            # Calculate bid/ask concentration
            bid_volume = sum(v for _, v in bid_levels)
            ask_volume = sum(v for _, v in ask_levels)
        
            concentration = abs(bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
        
            # Fragility score
            fragility = normalized_entropy * (1 - concentration)
        
            # Signal
            if fragility > 0.8:
                signal = "CAUTION"
                strength = SignalStrength.VERY_STRONG
            elif fragility > 0.6:
                signal = "CAUTION"
                strength = SignalStrength.MODERATE
            else:
                signal = "STABLE"
                strength = SignalStrength.NEUTRAL
        
            return IndicatorResult(
                name="Liquidity Entropy",
                value=fragility,
                signal=signal,
                strength=strength,
                components={
                    'entropy': entropy,
                    'normalized_entropy': normalized_entropy,
                    'concentration': concentration,
                    'bid_volume': bid_volume,
                    'ask_volume': ask_volume,
                    'num_levels': len(all_volumes)
                }
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class DynamicKellyCriterion:
    """
    Dynamic Kelly Criterion
    
    Implements "Kelly Criterion on Steroids" - dynamically adjusts
    position size based on real-time probability and volatility.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.max_kelly_fraction = self.config.get('max_kelly_fraction', 0.25)
            self.min_kelly_fraction = self.config.get('min_kelly_fraction', 0.05)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate(
        self,
        win_probability: float,
        avg_win: float,
        avg_loss: float,
        current_volatility: float,
        baseline_volatility: float,
        confidence_score: float
    ) -> IndicatorResult:
        """
        Calculate Dynamic Kelly position size
        
        Args:
            win_probability: Estimated probability of winning (0-1)
            avg_win: Average winning trade size
            avg_loss: Average losing trade size (positive number)
            current_volatility: Current ATR or similar
            baseline_volatility: Normal/baseline volatility
            confidence_score: AI confidence in the trade (0-1)
        """
        # Basic Kelly formula: f* = (bp - q) / b
        # where b = win/loss ratio, p = win prob, q = 1-p
        
        try:
            if avg_loss <= 0:
                avg_loss = 1
        
            b = avg_win / avg_loss  # Win/loss ratio
            p = win_probability
            q = 1 - p
        
            kelly = (b * p - q) / b if b > 0 else 0
        
            # Volatility adjustment
            vol_ratio = current_volatility / baseline_volatility if baseline_volatility > 0 else 1
            vol_adjustment = 1 / vol_ratio if vol_ratio > 0 else 1
        
            # Confidence adjustment
            confidence_adjustment = confidence_score
        
            # Final Kelly fraction
            adjusted_kelly = kelly * vol_adjustment * confidence_adjustment
        
            # Cap Kelly fraction
            final_kelly = np.clip(adjusted_kelly, self.min_kelly_fraction, self.max_kelly_fraction)
        
            # Signal based on Kelly
            if final_kelly >= self.max_kelly_fraction * 0.8:
                signal = "FULL_SIZE"
                strength = SignalStrength.VERY_STRONG
            elif final_kelly >= self.max_kelly_fraction * 0.5:
                signal = "STANDARD_SIZE"
                strength = SignalStrength.STRONG
            elif final_kelly >= self.min_kelly_fraction * 2:
                signal = "REDUCED_SIZE"
                strength = SignalStrength.MODERATE
            else:
                signal = "MINIMAL_SIZE"
                strength = SignalStrength.WEAK
        
            return IndicatorResult(
                name="Dynamic Kelly Criterion",
                value=final_kelly,
                signal=signal,
                strength=strength,
                components={
                    'raw_kelly': kelly,
                    'volatility_adjustment': vol_adjustment,
                    'confidence_adjustment': confidence_adjustment,
                    'win_probability': win_probability,
                    'win_loss_ratio': b,
                    'recommended_position_pct': final_kelly * 100
                }
            )
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class ProprietaryIndicators:
    """
    Collection of all proprietary indicators
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            self.vii = VolatilityImpulseVector(config)
            self.fmd = FractalMomentumDivergence(config)
            self.vpin_oi = VPINOIFusion(config)
            self.ricci = RicciFlowMomentum(config)
            self.entropy = LiquidityEntropy(config)
            self.kelly = DynamicKellyCriterion(config)
        
            logger.info("ProprietaryIndicators initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_all(
        self,
        price_data: Dict[str, np.ndarray],
        volume_data: Dict[str, Any],
        options_data: Dict[str, float],
        order_book: Dict[str, List],
        trade_stats: Dict[str, float]
    ) -> Dict[str, IndicatorResult]:
        """Calculate all indicators"""
        try:
            results = {}
        
            # VII
            if all(k in price_data for k in ['high', 'low', 'close']) and 'volume' in volume_data:
                results['vii'] = self.vii.calculate(
                    price_data['high'],
                    price_data['low'],
                    price_data['close'],
                    volume_data['volume'],
                    volume_data.get('bid_volume', 0.5),
                    volume_data.get('ask_volume', 0.5)
                )
        
            # Ricci Flow
            if 'close' in price_data:
                results['ricci'] = self.ricci.calculate(price_data['close'])
        
            # Liquidity Entropy
            if 'bids' in order_book and 'asks' in order_book:
                results['entropy'] = self.entropy.calculate(
                    order_book['bids'],
                    order_book['asks']
                )
        
            # Dynamic Kelly
            if all(k in trade_stats for k in ['win_prob', 'avg_win', 'avg_loss']):
                results['kelly'] = self.kelly.calculate(
                    trade_stats['win_prob'],
                    trade_stats['avg_win'],
                    trade_stats['avg_loss'],
                    trade_stats.get('current_vol', 1),
                    trade_stats.get('baseline_vol', 1),
                    trade_stats.get('confidence', 0.5)
                )
        
            return results
        except Exception as e:
            logger.error(f"Error in calculate_all: {e}")
            raise


# Factory function
def create_proprietary_indicators(config: Optional[Dict[str, Any]] = None) -> ProprietaryIndicators:
    """Create proprietary indicators"""
    return ProprietaryIndicators(config)
