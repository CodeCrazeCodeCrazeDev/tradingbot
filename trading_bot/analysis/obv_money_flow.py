"""
OBV (On Balance Volume) and Money Flow Index Analysis.

This module implements:
- On Balance Volume (OBV) calculation and analysis
- Money Flow Index (MFI) calculation
- Chaikin Money Flow (CMF)
- Volume-Price Trend (VPT)
- Accumulation/Distribution Line
- Force Index
- Ease of Movement
- Volume Weighted indicators
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class VolumeSignal(Enum):
    """Volume-based trading signals."""
    STRONG_ACCUMULATION = "strong_accumulation"
    ACCUMULATION = "accumulation"
    NEUTRAL = "neutral"
    DISTRIBUTION = "distribution"
    STRONG_DISTRIBUTION = "strong_distribution"


class DivergenceType(Enum):
    """Types of price-volume divergence."""
    BULLISH_REGULAR = "bullish_regular"
    BULLISH_HIDDEN = "bullish_hidden"
    BEARISH_REGULAR = "bearish_regular"
    BEARISH_HIDDEN = "bearish_hidden"
    NONE = "none"


class TrendConfirmation(Enum):
    """Volume trend confirmation status."""
    CONFIRMED = "confirmed"
    DIVERGING = "diverging"
    WEAK = "weak"
    NEUTRAL = "neutral"


@dataclass
class OBVReading:
    """On Balance Volume reading."""
    value: float
    change: float
    signal: VolumeSignal
    trend: str  # 'up', 'down', 'flat'
    divergence: DivergenceType
    breakout_potential: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MFIReading:
    """Money Flow Index reading."""
    value: float
    signal: VolumeSignal
    is_overbought: bool
    is_oversold: bool
    divergence: DivergenceType
    money_flow_ratio: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MoneyFlowAnalysis:
    """Complete money flow analysis."""
    obv: OBVReading
    mfi: MFIReading
    cmf: float
    vpt: float
    ad_line: float
    force_index: float
    eom: float
    overall_signal: VolumeSignal
    trend_confirmation: TrendConfirmation
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VolumeBreakout:
    """Volume breakout detection."""
    is_breakout: bool
    direction: str  # 'up', 'down'
    volume_ratio: float
    price_change: float
    confirmation_strength: float
    timestamp: datetime = field(default_factory=datetime.now)


class OBVCalculator:
    """
    On Balance Volume Calculator.
    
    OBV measures buying and selling pressure as a cumulative indicator,
    adding volume on up days and subtracting on down days.
    """
    
    def __init__(self, smoothing_period: int = 20):
        try:
            self.smoothing_period = smoothing_period
            self.obv_history: List[float] = []
            self.price_history: List[float] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On Balance Volume."""
        try:
            close = df['close'].values
            volume = df['volume'].values
        
            obv = np.zeros(len(close))
            obv[0] = volume[0]
        
            for i in range(1, len(close)):
                if close[i] > close[i-1]:
                    obv[i] = obv[i-1] + volume[i]
                elif close[i] < close[i-1]:
                    obv[i] = obv[i-1] - volume[i]
                else:
                    obv[i] = obv[i-1]
        
            return pd.Series(obv, index=df.index)
        except Exception as e:
            logger.error(f"Error in calculate_obv: {e}")
            raise
    
    def calculate_obv_ema(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate OBV with EMA smoothing."""
        try:
            obv = self.calculate_obv(df)
            return obv.ewm(span=period, adjust=False).mean()
        except Exception as e:
            logger.error(f"Error in calculate_obv_ema: {e}")
            raise
    
    def detect_obv_divergence(
        self,
        df: pd.DataFrame,
        lookback: int = 20
    ) -> DivergenceType:
        """Detect divergence between price and OBV."""
        try:
            if len(df) < lookback:
                return DivergenceType.NONE
        
            obv = self.calculate_obv(df)
            close = df['close']
        
            recent_close = close.iloc[-lookback:]
            recent_obv = obv.iloc[-lookback:]
        
            # Find swing points
            price_higher_high = recent_close.iloc[-1] > recent_close.iloc[0]
            price_lower_low = recent_close.iloc[-1] < recent_close.iloc[0]
            obv_higher_high = recent_obv.iloc[-1] > recent_obv.iloc[0]
            obv_lower_low = recent_obv.iloc[-1] < recent_obv.iloc[0]
        
            # Regular bullish: price lower low, OBV higher low
            if price_lower_low and not obv_lower_low:
                return DivergenceType.BULLISH_REGULAR
        
            # Regular bearish: price higher high, OBV lower high
            if price_higher_high and not obv_higher_high:
                return DivergenceType.BEARISH_REGULAR
        
            # Hidden bullish: price higher low, OBV lower low
            if not price_lower_low and obv_lower_low:
                return DivergenceType.BULLISH_HIDDEN
        
            # Hidden bearish: price lower high, OBV higher high
            if not price_higher_high and obv_higher_high:
                return DivergenceType.BEARISH_HIDDEN
        
            return DivergenceType.NONE
        except Exception as e:
            logger.error(f"Error in detect_obv_divergence: {e}")
            raise
    
    def get_obv_signal(self, df: pd.DataFrame) -> OBVReading:
        """Get complete OBV analysis."""
        try:
            obv = self.calculate_obv(df)
            obv_ema = self.calculate_obv_ema(df, self.smoothing_period)
        
            current_obv = obv.iloc[-1]
            prev_obv = obv.iloc[-2] if len(obv) > 1 else current_obv
            obv_change = current_obv - prev_obv
        
            # Determine trend
            if current_obv > obv_ema.iloc[-1]:
                trend = 'up'
            elif current_obv < obv_ema.iloc[-1]:
                trend = 'down'
            else:
                trend = 'flat'
        
            # Determine signal strength
            obv_std = obv.std()
            if obv_std > 0:
                z_score = (current_obv - obv.mean()) / obv_std
            else:
                z_score = 0
        
            if z_score > 2:
                signal = VolumeSignal.STRONG_ACCUMULATION
            elif z_score > 1:
                signal = VolumeSignal.ACCUMULATION
            elif z_score < -2:
                signal = VolumeSignal.STRONG_DISTRIBUTION
            elif z_score < -1:
                signal = VolumeSignal.DISTRIBUTION
            else:
                signal = VolumeSignal.NEUTRAL
        
            # Detect divergence
            divergence = self.detect_obv_divergence(df)
        
            # Calculate breakout potential
            obv_range = obv.max() - obv.min()
            if obv_range > 0:
                breakout_potential = abs(current_obv - obv.mean()) / obv_range
            else:
                breakout_potential = 0
        
            return OBVReading(
                value=current_obv,
                change=obv_change,
                signal=signal,
                trend=trend,
                divergence=divergence,
                breakout_potential=min(1.0, breakout_potential)
            )
        except Exception as e:
            logger.error(f"Error in get_obv_signal: {e}")
            raise


class MFICalculator:
    """
    Money Flow Index Calculator.
    
    MFI is a volume-weighted RSI that measures buying and selling pressure.
    """
    
    def __init__(self, period: int = 14):
        try:
            self.period = period
            self.overbought_level = 80
            self.oversold_level = 20
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_typical_price(self, df: pd.DataFrame) -> pd.Series:
        """Calculate typical price (HLC average)."""
        return (df['high'] + df['low'] + df['close']) / 3
    
    def calculate_raw_money_flow(self, df: pd.DataFrame) -> pd.Series:
        """Calculate raw money flow."""
        try:
            typical_price = self.calculate_typical_price(df)
            return typical_price * df['volume']
        except Exception as e:
            logger.error(f"Error in calculate_raw_money_flow: {e}")
            raise
    
    def calculate_mfi(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Money Flow Index."""
        try:
            typical_price = self.calculate_typical_price(df)
            raw_money_flow = self.calculate_raw_money_flow(df)
        
            # Determine positive and negative money flow
            price_change = typical_price.diff()
        
            positive_flow = pd.Series(0.0, index=df.index)
            negative_flow = pd.Series(0.0, index=df.index)
        
            positive_flow[price_change > 0] = raw_money_flow[price_change > 0]
            negative_flow[price_change < 0] = raw_money_flow[price_change < 0]
        
            # Calculate money flow ratio
            positive_sum = positive_flow.rolling(window=self.period).sum()
            negative_sum = negative_flow.rolling(window=self.period).sum()
        
            money_flow_ratio = positive_sum / (negative_sum + 1e-10)
        
            # Calculate MFI
            mfi = 100 - (100 / (1 + money_flow_ratio))
        
            return mfi
        except Exception as e:
            logger.error(f"Error in calculate_mfi: {e}")
            raise
    
    def detect_mfi_divergence(
        self,
        df: pd.DataFrame,
        lookback: int = 20
    ) -> DivergenceType:
        """Detect divergence between price and MFI."""
        try:
            if len(df) < lookback:
                return DivergenceType.NONE
        
            mfi = self.calculate_mfi(df)
            close = df['close']
        
            recent_close = close.iloc[-lookback:]
            recent_mfi = mfi.iloc[-lookback:]
        
            price_trend = recent_close.iloc[-1] - recent_close.iloc[0]
            mfi_trend = recent_mfi.iloc[-1] - recent_mfi.iloc[0]
        
            # Regular bullish: price down, MFI up
            if price_trend < 0 and mfi_trend > 0:
                return DivergenceType.BULLISH_REGULAR
        
            # Regular bearish: price up, MFI down
            if price_trend > 0 and mfi_trend < 0:
                return DivergenceType.BEARISH_REGULAR
        
            return DivergenceType.NONE
        except Exception as e:
            logger.error(f"Error in detect_mfi_divergence: {e}")
            raise
    
    def get_mfi_signal(self, df: pd.DataFrame) -> MFIReading:
        """Get complete MFI analysis."""
        try:
            mfi = self.calculate_mfi(df)
            current_mfi = mfi.iloc[-1]
        
            # Determine signal
            if current_mfi >= self.overbought_level:
                signal = VolumeSignal.STRONG_DISTRIBUTION
            elif current_mfi >= 60:
                signal = VolumeSignal.ACCUMULATION
            elif current_mfi <= self.oversold_level:
                signal = VolumeSignal.STRONG_ACCUMULATION
            elif current_mfi <= 40:
                signal = VolumeSignal.DISTRIBUTION
            else:
                signal = VolumeSignal.NEUTRAL
        
            # Calculate money flow ratio
            typical_price = self.calculate_typical_price(df)
            raw_money_flow = self.calculate_raw_money_flow(df)
            price_change = typical_price.diff()
        
            positive_flow = raw_money_flow[price_change > 0].iloc[-self.period:].sum()
            negative_flow = raw_money_flow[price_change < 0].iloc[-self.period:].sum()
            money_flow_ratio = positive_flow / (negative_flow + 1e-10)
        
            # Detect divergence
            divergence = self.detect_mfi_divergence(df)
        
            return MFIReading(
                value=current_mfi,
                signal=signal,
                is_overbought=current_mfi >= self.overbought_level,
                is_oversold=current_mfi <= self.oversold_level,
                divergence=divergence,
                money_flow_ratio=money_flow_ratio
            )
        except Exception as e:
            logger.error(f"Error in get_mfi_signal: {e}")
            raise


class MoneyFlowAnalyzer:
    """
    Comprehensive Money Flow Analysis.
    
    Combines multiple volume-based indicators for complete analysis.
    """
    
    def __init__(
        self,
        obv_smoothing: int = 20,
        mfi_period: int = 14,
        cmf_period: int = 20,
        force_period: int = 13
    ):
        try:
            self.obv_calculator = OBVCalculator(obv_smoothing)
            self.mfi_calculator = MFICalculator(mfi_period)
            self.cmf_period = cmf_period
            self.force_period = force_period
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_chaikin_money_flow(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Chaikin Money Flow."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            volume = df['volume']
        
            # Money Flow Multiplier
            mfm = ((close - low) - (high - close)) / (high - low + 1e-10)
        
            # Money Flow Volume
            mfv = mfm * volume
        
            # CMF
            cmf = mfv.rolling(window=self.cmf_period).sum() / \
                  volume.rolling(window=self.cmf_period).sum()
        
            return cmf
        except Exception as e:
            logger.error(f"Error in calculate_chaikin_money_flow: {e}")
            raise
    
    def calculate_volume_price_trend(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Price Trend."""
        try:
            close = df['close']
            volume = df['volume']
        
            price_change_pct = close.pct_change()
            vpt = (price_change_pct * volume).cumsum()
        
            return vpt
        except Exception as e:
            logger.error(f"Error in calculate_volume_price_trend: {e}")
            raise
    
    def calculate_accumulation_distribution(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Accumulation/Distribution Line."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            volume = df['volume']
        
            # Money Flow Multiplier
            mfm = ((close - low) - (high - close)) / (high - low + 1e-10)
        
            # A/D Line
            ad = (mfm * volume).cumsum()
        
            return ad
        except Exception as e:
            logger.error(f"Error in calculate_accumulation_distribution: {e}")
            raise
    
    def calculate_force_index(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Force Index."""
        try:
            close = df['close']
            volume = df['volume']
        
            # Raw Force Index
            force = close.diff() * volume
        
            # Smoothed Force Index
            force_ema = force.ewm(span=self.force_period, adjust=False).mean()
        
            return force_ema
        except Exception as e:
            logger.error(f"Error in calculate_force_index: {e}")
            raise
    
    def calculate_ease_of_movement(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Ease of Movement."""
        try:
            high = df['high']
            low = df['low']
            volume = df['volume']
        
            # Distance moved
            dm = ((high + low) / 2) - ((high.shift(1) + low.shift(1)) / 2)
        
            # Box ratio
            br = (volume / 1e8) / (high - low + 1e-10)
        
            # EMV
            emv = dm / (br + 1e-10)
        
            # Smoothed EMV
            emv_sma = emv.rolling(window=14).mean()
        
            return emv_sma
        except Exception as e:
            logger.error(f"Error in calculate_ease_of_movement: {e}")
            raise
    
    def detect_volume_breakout(
        self,
        df: pd.DataFrame,
        volume_threshold: float = 2.0,
        price_threshold: float = 0.02
    ) -> VolumeBreakout:
        """Detect volume breakout conditions."""
        try:
            volume = df['volume']
            close = df['close']
        
            # Calculate average volume
            avg_volume = volume.rolling(window=20).mean()
            current_volume = volume.iloc[-1]
            volume_ratio = current_volume / (avg_volume.iloc[-1] + 1e-10)
        
            # Calculate price change
            price_change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]
        
            # Determine if breakout
            is_breakout = volume_ratio >= volume_threshold and abs(price_change) >= price_threshold
        
            # Determine direction
            direction = 'up' if price_change > 0 else 'down'
        
            # Calculate confirmation strength
            confirmation_strength = min(1.0, (volume_ratio / volume_threshold) * 
                                       (abs(price_change) / price_threshold) / 2)
        
            return VolumeBreakout(
                is_breakout=is_breakout,
                direction=direction,
                volume_ratio=volume_ratio,
                price_change=price_change,
                confirmation_strength=confirmation_strength
            )
        except Exception as e:
            logger.error(f"Error in detect_volume_breakout: {e}")
            raise
    
    def get_trend_confirmation(
        self,
        df: pd.DataFrame,
        price_trend: str
    ) -> TrendConfirmation:
        """Check if volume confirms price trend."""
        try:
            obv = self.obv_calculator.calculate_obv(df)
            obv_trend = 'up' if obv.iloc[-1] > obv.iloc[-5] else 'down'
        
            cmf = self.calculate_chaikin_money_flow(df)
            cmf_signal = 'up' if cmf.iloc[-1] > 0 else 'down'
        
            ad = self.calculate_accumulation_distribution(df)
            ad_trend = 'up' if ad.iloc[-1] > ad.iloc[-5] else 'down'
        
            # Count confirmations
            confirmations = sum([
                obv_trend == price_trend,
                cmf_signal == price_trend,
                ad_trend == price_trend
            ])
        
            if confirmations >= 3:
                return TrendConfirmation.CONFIRMED
            elif confirmations >= 2:
                return TrendConfirmation.WEAK
            elif confirmations == 0:
                return TrendConfirmation.DIVERGING
            else:
                return TrendConfirmation.NEUTRAL
        except Exception as e:
            logger.error(f"Error in get_trend_confirmation: {e}")
            raise
    
    def analyze(self, df: pd.DataFrame) -> MoneyFlowAnalysis:
        """Perform complete money flow analysis."""
        # Get individual indicators
        try:
            obv_reading = self.obv_calculator.get_obv_signal(df)
            mfi_reading = self.mfi_calculator.get_mfi_signal(df)
        
            cmf = self.calculate_chaikin_money_flow(df)
            vpt = self.calculate_volume_price_trend(df)
            ad = self.calculate_accumulation_distribution(df)
            force = self.calculate_force_index(df)
            eom = self.calculate_ease_of_movement(df)
        
            # Determine overall signal
            signals = [obv_reading.signal, mfi_reading.signal]
        
            # Add CMF signal
            if cmf.iloc[-1] > 0.1:
                signals.append(VolumeSignal.ACCUMULATION)
            elif cmf.iloc[-1] < -0.1:
                signals.append(VolumeSignal.DISTRIBUTION)
            else:
                signals.append(VolumeSignal.NEUTRAL)
        
            # Count signal types
            accumulation_count = sum(1 for s in signals if s in 
                                     [VolumeSignal.ACCUMULATION, VolumeSignal.STRONG_ACCUMULATION])
            distribution_count = sum(1 for s in signals if s in 
                                    [VolumeSignal.DISTRIBUTION, VolumeSignal.STRONG_DISTRIBUTION])
        
            if accumulation_count > distribution_count:
                if accumulation_count >= 2:
                    overall_signal = VolumeSignal.STRONG_ACCUMULATION
                else:
                    overall_signal = VolumeSignal.ACCUMULATION
            elif distribution_count > accumulation_count:
                if distribution_count >= 2:
                    overall_signal = VolumeSignal.STRONG_DISTRIBUTION
                else:
                    overall_signal = VolumeSignal.DISTRIBUTION
            else:
                overall_signal = VolumeSignal.NEUTRAL
        
            # Determine price trend
            close = df['close']
            price_trend = 'up' if close.iloc[-1] > close.iloc[-5] else 'down'
        
            # Get trend confirmation
            trend_confirmation = self.get_trend_confirmation(df, price_trend)
        
            # Calculate confidence
            confidence = (accumulation_count + distribution_count) / len(signals)
            if trend_confirmation == TrendConfirmation.CONFIRMED:
                confidence = min(1.0, confidence + 0.2)
            elif trend_confirmation == TrendConfirmation.DIVERGING:
                confidence = max(0.0, confidence - 0.2)
        
            return MoneyFlowAnalysis(
                obv=obv_reading,
                mfi=mfi_reading,
                cmf=float(cmf.iloc[-1]),
                vpt=float(vpt.iloc[-1]),
                ad_line=float(ad.iloc[-1]),
                force_index=float(force.iloc[-1]),
                eom=float(eom.iloc[-1]) if not np.isnan(eom.iloc[-1]) else 0.0,
                overall_signal=overall_signal,
                trend_confirmation=trend_confirmation,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def get_trading_signal(
        self,
        df: pd.DataFrame,
        min_confidence: float = 0.6
    ) -> Dict[str, Any]:
        """Get actionable trading signal from money flow analysis."""
        try:
            analysis = self.analyze(df)
        
            signal = {
                'action': 'hold',
                'strength': 0.0,
                'confidence': analysis.confidence,
                'reasons': []
            }
        
            if analysis.confidence < min_confidence:
                signal['reasons'].append('Low confidence')
                return signal
        
            # Determine action
            if analysis.overall_signal in [VolumeSignal.STRONG_ACCUMULATION, VolumeSignal.ACCUMULATION]:
                signal['action'] = 'buy'
                signal['strength'] = 0.8 if analysis.overall_signal == VolumeSignal.STRONG_ACCUMULATION else 0.6
                signal['reasons'].append(f'Money flow indicates {analysis.overall_signal.value}')
            
            elif analysis.overall_signal in [VolumeSignal.STRONG_DISTRIBUTION, VolumeSignal.DISTRIBUTION]:
                signal['action'] = 'sell'
                signal['strength'] = 0.8 if analysis.overall_signal == VolumeSignal.STRONG_DISTRIBUTION else 0.6
                signal['reasons'].append(f'Money flow indicates {analysis.overall_signal.value}')
        
            # Add divergence information
            if analysis.obv.divergence != DivergenceType.NONE:
                signal['reasons'].append(f'OBV divergence: {analysis.obv.divergence.value}')
            
            if analysis.mfi.divergence != DivergenceType.NONE:
                signal['reasons'].append(f'MFI divergence: {analysis.mfi.divergence.value}')
        
            # Add trend confirmation
            signal['reasons'].append(f'Trend confirmation: {analysis.trend_confirmation.value}')
        
            return signal
        except Exception as e:
            logger.error(f"Error in get_trading_signal: {e}")
            raise


# Convenience functions
def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """Quick OBV calculation."""
    try:
        calculator = OBVCalculator()
        return calculator.calculate_obv(df)
    except Exception as e:
        logger.error(f"Error in calculate_obv: {e}")
        raise


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Quick MFI calculation."""
    try:
        calculator = MFICalculator(period)
        return calculator.calculate_mfi(df)
    except Exception as e:
        logger.error(f"Error in calculate_mfi: {e}")
        raise


def get_money_flow_signal(df: pd.DataFrame) -> Dict[str, Any]:
    """Get quick money flow trading signal."""
    try:
        analyzer = MoneyFlowAnalyzer()
        return analyzer.get_trading_signal(df)
    except Exception as e:
        logger.error(f"Error in get_money_flow_signal: {e}")
        raise


def detect_volume_divergence(df: pd.DataFrame) -> Dict[str, DivergenceType]:
    """Detect volume divergences."""
    try:
        obv_calc = OBVCalculator()
        mfi_calc = MFICalculator()
    
        return {
            'obv_divergence': obv_calc.detect_obv_divergence(df),
            'mfi_divergence': mfi_calc.detect_mfi_divergence(df)
        }
    except Exception as e:
        logger.error(f"Error in detect_volume_divergence: {e}")
        raise
