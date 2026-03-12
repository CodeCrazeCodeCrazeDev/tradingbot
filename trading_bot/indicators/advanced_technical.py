"""
Advanced Technical Indicators
Includes: Hurst Exponent, FRAMA, SuperTrend, KAMA, TTM Squeeze, Kalman Filter
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
try:
    from scipy import stats
except ImportError:
    scipy = None
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class HurstExponent:
    """
    Hurst Exponent - Detects market fractal dimension.
    H < 0.5: Mean-reverting
    H = 0.5: Random walk
    H > 0.5: Trending
    """
    
    def __init__(self, lags: int = 100):
        self.lags = lags
    
    def calculate(self, prices: pd.Series) -> float:
        """Calculate Hurst Exponent using R/S analysis."""
        lags_range = range(2, self.lags)
        tau = []
        
        for lag in lags_range:
            # Calculate standard deviation
            std = np.std(prices.diff().dropna())
            
            if std == 0:
                continue
                
            # Calculate range
            ts = prices.diff().dropna()
            rs = []
            
            for i in range(0, len(ts), lag):
                chunk = ts.iloc[i:i+lag]
                if len(chunk) < lag:
                    continue
                    
                mean_chunk = chunk.mean()
                deviations = chunk - mean_chunk
                cumulative_dev = deviations.cumsum()
                
                R = cumulative_dev.max() - cumulative_dev.min()
                S = chunk.std()
                
                if S != 0:
                    rs.append(R / S)
            
            if rs:
                tau.append(np.mean(rs))
        
        if len(tau) < 2:
            return 0.5  # Default to random walk
        
        # Linear regression to find Hurst exponent
        lags_log = np.log(list(lags_range)[:len(tau)])
        tau_log = np.log(tau)
        
        slope, _ = np.polyfit(lags_log, tau_log, 1)
        return slope
    
    def interpret(self, hurst: float) -> str:
        """Interpret Hurst exponent value."""
        if hurst < 0.4:
            return "STRONG_MEAN_REVERTING"
        elif hurst < 0.5:
            return "MEAN_REVERTING"
        elif hurst < 0.6:
            return "RANDOM_WALK"
        elif hurst < 0.7:
            return "TRENDING"
        else:
            return "STRONG_TRENDING"


class FRAMA:
    """
    Fractal Adaptive Moving Average
    Adjusts smoothing based on fractal dimension (volatility)
    """
    
    def __init__(self, period: int = 16, fc: int = 1, sc: int = 300):
        self.period = period
        self.fc = fc  # Fast constant
        self.sc = sc  # Slow constant
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        """Calculate FRAMA."""
        frama = pd.Series(index=prices.index, dtype=float)
        frama.iloc[0] = prices.iloc[0]
        
        for i in range(self.period, len(prices)):
            # Split period in half
            n = self.period // 2
            
            # Calculate highs and lows for each half
            high1 = prices.iloc[i-self.period:i-n].max()
            low1 = prices.iloc[i-self.period:i-n].min()
            high2 = prices.iloc[i-n:i].max()
            low2 = prices.iloc[i-n:i].min()
            high_total = prices.iloc[i-self.period:i].max()
            low_total = prices.iloc[i-self.period:i].min()
            
            # Calculate fractal dimension
            n1 = (high1 - low1) / n
            n2 = (high2 - low2) / n
            n3 = (high_total - low_total) / self.period
            
            if n1 + n2 > 0:
                dimen = (np.log(n1 + n2) - np.log(n3)) / np.log(2)
            else:
                dimen = 0
            
            # Calculate alpha
            alpha = np.exp(-4.6 * (dimen - 1))
            alpha = max(self.fc / self.sc, min(alpha, 1))
            
            # Calculate FRAMA
            frama.iloc[i] = alpha * prices.iloc[i] + (1 - alpha) * frama.iloc[i-1]
        
        return frama


class SuperTrend:
    """
    SuperTrend Indicator
    Combines ATR and price action for trend detection
    """
    
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        self.period = period
        self.multiplier = multiplier
    
    def calculate(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate SuperTrend.
        Returns: (supertrend, direction)
        direction: 1 = uptrend, -1 = downtrend
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate ATR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.period).mean()
        
        # Calculate basic bands
        hl_avg = (high + low) / 2
        upper_band = hl_avg + (self.multiplier * atr)
        lower_band = hl_avg - (self.multiplier * atr)
        
        # Initialize
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        
        supertrend.iloc[0] = lower_band.iloc[0]
        direction.iloc[0] = 1
        
        for i in range(1, len(df)):
            # Update bands
            if close.iloc[i] > supertrend.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            elif close.iloc[i] < supertrend.iloc[i-1]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]
        
        return supertrend, direction


class KAMA:
    """
    Kaufman Adaptive Moving Average
    Reacts faster in strong trends, slower in noise
    """
    
    def __init__(self, period: int = 10, fast_ema: int = 2, slow_ema: int = 30):
        self.period = period
        self.fast_sc = 2 / (fast_ema + 1)
        self.slow_sc = 2 / (slow_ema + 1)
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        """Calculate KAMA."""
        # Calculate Efficiency Ratio
        change = abs(prices - prices.shift(self.period))
        volatility = prices.diff().abs().rolling(window=self.period).sum()
        
        er = change / volatility
        er = er.fillna(0)
        
        # Calculate Smoothing Constant
        sc = (er * (self.fast_sc - self.slow_sc) + self.slow_sc) ** 2
        
        # Calculate KAMA
        kama = pd.Series(index=prices.index, dtype=float)
        kama.iloc[self.period] = prices.iloc[self.period]
        
        for i in range(self.period + 1, len(prices)):
            kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (prices.iloc[i] - kama.iloc[i-1])
        
        return kama


class TTMSqueeze:
    """
    TTM Squeeze Indicator
    Combines Bollinger Bands + Keltner Channels
    Detects volatility compression before breakout
    """
    
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0,
                 kc_period: int = 20, kc_mult: float = 1.5):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.kc_period = kc_period
        self.kc_mult = kc_mult
    
    def calculate(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate TTM Squeeze.
        Returns: squeeze_on, momentum, histogram
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Bollinger Bands
        bb_middle = close.rolling(window=self.bb_period).mean()
        bb_std = close.rolling(window=self.bb_period).std()
        bb_upper = bb_middle + (bb_std * self.bb_std)
        bb_lower = bb_middle - (bb_std * self.bb_std)
        
        # Keltner Channels
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.kc_period).mean()
        
        kc_middle = close.rolling(window=self.kc_period).mean()
        kc_upper = kc_middle + (atr * self.kc_mult)
        kc_lower = kc_middle - (atr * self.kc_mult)
        
        # Squeeze detection (BB inside KC)
        squeeze_on = (bb_lower > kc_lower) & (bb_upper < kc_upper)
        
        # Momentum calculation
        highest = high.rolling(window=self.kc_period).max()
        lowest = low.rolling(window=self.kc_period).min()
        avg_hl = (highest + lowest) / 2
        avg_close = (close + close.rolling(window=self.kc_period).mean()) / 2
        
        momentum = close - avg_hl
        
        return {
            'squeeze_on': squeeze_on.astype(int),
            'momentum': momentum,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'kc_upper': kc_upper,
            'kc_lower': kc_lower
        }


class KalmanFilter:
    """
    Kalman Filter Adaptive Trendline
    Dynamic trend smoothing with noise reduction
    """
    
    def __init__(self, process_variance: float = 0.01, 
                 measurement_variance: float = 0.1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        """Apply Kalman filter to price series."""
        n = len(prices)
        
        # Initialize
        filtered = np.zeros(n)
        prediction_error = np.zeros(n)
        estimate_error = np.zeros(n)
        
        # Initial values
        filtered[0] = prices.iloc[0]
        estimate_error[0] = 1.0
        
        for i in range(1, n):
            # Prediction
            predicted_state = filtered[i-1]
            predicted_error = estimate_error[i-1] + self.process_variance
            
            # Update
            kalman_gain = predicted_error / (predicted_error + self.measurement_variance)
            filtered[i] = predicted_state + kalman_gain * (prices.iloc[i] - predicted_state)
            estimate_error[i] = (1 - kalman_gain) * predicted_error
            prediction_error[i] = prices.iloc[i] - predicted_state
        
        return pd.Series(filtered, index=prices.index)


class AdvancedTechnicalIndicators:
    """Unified interface for all advanced technical indicators."""
    
    def __init__(self):
        self.hurst = HurstExponent()
        self.frama = FRAMA()
        self.supertrend = SuperTrend()
        self.kama = KAMA()
        self.ttm_squeeze = TTMSqueeze()
        self.kalman = KalmanFilter()
        
        logger.info("✅ Advanced Technical Indicators initialized")
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all advanced indicators."""
        result = df.copy()
        
        try:
            # Hurst Exponent
            hurst_value = self.hurst.calculate(df['close'])
            result['hurst_exponent'] = hurst_value
            result['hurst_regime'] = self.hurst.interpret(hurst_value)
            
            # FRAMA
            result['frama'] = self.frama.calculate(df['close'])
            
            # SuperTrend
            supertrend, direction = self.supertrend.calculate(df)
            result['supertrend'] = supertrend
            result['supertrend_direction'] = direction
            
            # KAMA
            result['kama'] = self.kama.calculate(df['close'])
            
            # TTM Squeeze
            squeeze = self.ttm_squeeze.calculate(df)
            for key, value in squeeze.items():
                result[f'ttm_{key}'] = value
            
            # Kalman Filter
            result['kalman_trend'] = self.kalman.calculate(df['close'])
            
            logger.info("✅ All advanced indicators calculated")
            
        except Exception as e:
            logger.error(f"❌ Error calculating advanced indicators: {e}")
        
        return result


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=500, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(500).cumsum() + 100,
        'high': np.random.randn(500).cumsum() + 102,
        'low': np.random.randn(500).cumsum() + 98,
        'close': np.random.randn(500).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)
    
    # Calculate indicators
    indicators = AdvancedTechnicalIndicators()
    result = indicators.calculate_all(df)
    
    logger.info("\n=== Advanced Technical Indicators ===")
    logger.info(f"Hurst Exponent: {result['hurst_exponent'].iloc[-1]:.4f}")
    logger.info(f"Regime: {result['hurst_regime'].iloc[-1]}")
    logger.info(f"FRAMA: {result['frama'].iloc[-1]:.2f}")
    logger.info(f"SuperTrend: {result['supertrend'].iloc[-1]:.2f}")
    logger.info(f"Direction: {'UP' if result['supertrend_direction'].iloc[-1] == 1 else 'DOWN'}")
    logger.info(f"KAMA: {result['kama'].iloc[-1]:.2f}")
    logger.info(f"TTM Squeeze: {'ON' if result['ttm_squeeze_on'].iloc[-1] else 'OFF'}")
    logger.info(f"Kalman Trend: {result['kalman_trend'].iloc[-1]:.2f}")
