"""
Tier 1: Market Input & Core Technical Analysis
Processes raw market data to extract technical indicators and patterns
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from scipy import stats

from trading_bot.brain.tier_structure import TierBase, MarketStateVector

# Import indicator modules
from trading_bot.indicators.advanced_technical import (
    HurstExponent, FRAMA, SuperTrend, KAMA, TTMSqueeze, KalmanFilter
)

logger = logging.getLogger(__name__)


class MomentumAnalysis:
    """Momentum indicator analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.rsi_period = self.config.get('rsi_period', 14)
        self.macd_fast = self.config.get('macd_fast', 12)
        self.macd_slow = self.config.get('macd_slow', 26)
        self.macd_signal = self.config.get('macd_signal', 9)
        self.stoch_k = self.config.get('stoch_k', 14)
        self.stoch_d = self.config.get('stoch_d', 3)
        self.adx_period = self.config.get('adx_period', 14)
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD"""
        exp1 = prices.ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = prices.ewm(span=self.macd_slow, adjust=False).mean()
        
        macd = exp1 - exp2
        signal = macd.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd - signal
        
        return {
            'macd': macd,
            'signal': signal,
            'histogram': histogram
        }
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=self.stoch_k).min()
        highest_high = high.rolling(window=self.stoch_k).max()
        
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low + np.finfo(float).eps))
        d = k.rolling(window=self.stoch_d).mean()
        
        return {'k': k, 'd': d}
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Calculate Average Directional Index"""
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.adx_period).mean()
        
        # +DM and -DM
        plus_dm = high.diff()
        minus_dm = low.diff(-1).abs()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        # Smoothed +DM and -DM
        plus_di = 100 * (plus_dm.rolling(window=self.adx_period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=self.adx_period).mean() / atr)
        
        # Directional Movement Index
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + np.finfo(float).eps))
        
        # Average Directional Index
        adx = dx.rolling(window=self.adx_period).mean()
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze momentum indicators"""
        close = df['close']
        high = df['high']
        low = df['low']
        
        # Calculate indicators
        rsi = self.calculate_rsi(close)
        macd_dict = self.calculate_macd(close)
        stoch_dict = self.calculate_stochastic(high, low, close)
        adx_dict = self.calculate_adx(high, low, close)
        
        # Get latest values
        latest_rsi = rsi.iloc[-1]
        latest_macd = macd_dict['macd'].iloc[-1]
        latest_macd_hist = macd_dict['histogram'].iloc[-1]
        latest_stoch_k = stoch_dict['k'].iloc[-1]
        latest_stoch_d = stoch_dict['d'].iloc[-1]
        latest_adx = adx_dict['adx'].iloc[-1]
        latest_plus_di = adx_dict['plus_di'].iloc[-1]
        latest_minus_di = adx_dict['minus_di'].iloc[-1]
        
        # Determine momentum state
        momentum_signal = 0.0
        
        # RSI contribution (-1 to 1)
        if latest_rsi > 70:
            rsi_signal = -1.0  # Overbought
        elif latest_rsi < 30:
            rsi_signal = 1.0   # Oversold
        else:
            rsi_signal = (latest_rsi - 50) / 20  # Scaled between -1 and 1
        
        # MACD contribution (-1 to 1)
        macd_signal = np.sign(latest_macd_hist) * min(abs(latest_macd_hist) / 0.5, 1.0)
        
        # Stochastic contribution (-1 to 1)
        if latest_stoch_k > 80:
            stoch_signal = -1.0  # Overbought
        elif latest_stoch_k < 20:
            stoch_signal = 1.0   # Oversold
        else:
            stoch_signal = (latest_stoch_k - 50) / 30  # Scaled between -1 and 1
        
        # ADX contribution (0 to 1, trend strength)
        adx_strength = min(latest_adx / 50, 1.0)
        
        # Trend direction from +DI and -DI
        trend_direction = 1.0 if latest_plus_di > latest_minus_di else -1.0
        
        # Combine signals
        momentum_signal = (
            0.3 * rsi_signal +
            0.4 * macd_signal +
            0.3 * stoch_signal
        ) * (0.5 + 0.5 * adx_strength)  # Scale by trend strength
        
        return {
            'momentum_signal': momentum_signal,
            'trend_strength': adx_strength,
            'trend_direction': trend_direction,
            'overbought_oversold': rsi_signal,
            'indicators': {
                'rsi': latest_rsi,
                'macd': latest_macd,
                'macd_histogram': latest_macd_hist,
                'stoch_k': latest_stoch_k,
                'stoch_d': latest_stoch_d,
                'adx': latest_adx,
                'plus_di': latest_plus_di,
                'minus_di': latest_minus_di
            }
        }


class VolatilityAnalysis:
    """Volatility indicator analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.atr_period = self.config.get('atr_period', 14)
        self.bb_period = self.config.get('bb_period', 20)
        self.bb_std = self.config.get('bb_std', 2.0)
        self.ttm_squeeze = TTMSqueeze(
            bb_period=self.config.get('ttm_bb_period', 20),
            bb_std=self.config.get('ttm_bb_std', 2.0),
            kc_period=self.config.get('ttm_kc_period', 20),
            kc_mult=self.config.get('ttm_kc_mult', 1.5)
        )
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        return tr.rolling(window=self.atr_period).mean()
    
    def calculate_bollinger_bands(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=self.bb_period).mean()
        std = prices.rolling(window=self.bb_period).std()
        
        upper = middle + (std * self.bb_std)
        lower = middle - (std * self.bb_std)
        
        # Calculate bandwidth
        bandwidth = (upper - lower) / middle
        
        # Calculate %B
        percent_b = (prices - lower) / (upper - lower + np.finfo(float).eps)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        }
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volatility indicators"""
        close = df['close']
        high = df['high']
        low = df['low']
        
        # Calculate indicators
        atr = self.calculate_atr(high, low, close)
        bb = self.calculate_bollinger_bands(close)
        ttm = self.ttm_squeeze.calculate(df)
        
        # Get latest values
        latest_atr = atr.iloc[-1]
        latest_bb_width = bb['bandwidth'].iloc[-1]
        latest_percent_b = bb['percent_b'].iloc[-1]
        latest_squeeze_on = ttm['squeeze_on'].iloc[-1]
        latest_squeeze_momentum = ttm.get('momentum', pd.Series([0])).iloc[-1]
        
        # Normalize ATR
        avg_price = close.mean()
        normalized_atr = latest_atr / avg_price
        
        # Determine volatility state
        if latest_bb_width < bb['bandwidth'].quantile(0.2):
            volatility_state = 'low'
        elif latest_bb_width > bb['bandwidth'].quantile(0.8):
            volatility_state = 'high'
        else:
            volatility_state = 'normal'
        
        # Compression signal from TTM Squeeze
        compression_signal = 1.0 if latest_squeeze_on else 0.0
        
        # Volatility signal (-1 to 1)
        # Negative means contracting volatility, positive means expanding
        volatility_trend = bb['bandwidth'].diff(5).iloc[-1]
        volatility_signal = np.sign(volatility_trend) * min(abs(volatility_trend) / 0.05, 1.0)
        
        return {
            'volatility_state': volatility_state,
            'normalized_atr': normalized_atr,
            'volatility_signal': volatility_signal,
            'compression_signal': compression_signal,
            'indicators': {
                'atr': latest_atr,
                'bb_width': latest_bb_width,
                'percent_b': latest_percent_b,
                'squeeze_on': latest_squeeze_on,
                'squeeze_momentum': latest_squeeze_momentum
            }
        }


class TrendAnalysis:
    """Trend indicator analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.kama = KAMA(
            period=self.config.get('kama_period', 10),
            fast_ema=self.config.get('kama_fast', 2),
            slow_ema=self.config.get('kama_slow', 30)
        )
        self.frama = FRAMA(
            period=self.config.get('frama_period', 16),
            fc=self.config.get('frama_fc', 1),
            sc=self.config.get('frama_sc', 300)
        )
        self.supertrend = SuperTrend(
            period=self.config.get('supertrend_period', 10),
            multiplier=self.config.get('supertrend_mult', 3.0)
        )
        self.kalman = KalmanFilter(
            process_variance=self.config.get('kalman_process_var', 0.01),
            measurement_variance=self.config.get('kalman_meas_var', 0.1)
        )
    
    def calculate_moving_averages(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate various moving averages"""
        sma20 = prices.rolling(window=20).mean()
        sma50 = prices.rolling(window=50).mean()
        sma200 = prices.rolling(window=200).mean()
        
        ema20 = prices.ewm(span=20, adjust=False).mean()
        ema50 = prices.ewm(span=50, adjust=False).mean()
        
        kama = self.kama.calculate(prices)
        frama = self.frama.calculate(prices)
        kalman_trend = self.kalman.calculate(prices)
        
        return {
            'sma20': sma20,
            'sma50': sma50,
            'sma200': sma200,
            'ema20': ema20,
            'ema50': ema50,
            'kama': kama,
            'frama': frama,
            'kalman': kalman_trend
        }
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend indicators"""
        close = df['close']
        
        # Calculate indicators
        mas = self.calculate_moving_averages(close)
        vwap = self.calculate_vwap(df)
        supertrend, direction = self.supertrend.calculate(df)
        
        # Get latest values
        latest_close = close.iloc[-1]
        latest_sma20 = mas['sma20'].iloc[-1]
        latest_sma50 = mas['sma50'].iloc[-1]
        latest_sma200 = mas['sma200'].iloc[-1]
        latest_ema20 = mas['ema20'].iloc[-1]
        latest_ema50 = mas['ema50'].iloc[-1]
        latest_kama = mas['kama'].iloc[-1]
        latest_frama = mas['frama'].iloc[-1]
        latest_kalman = mas['kalman'].iloc[-1]
        latest_vwap = vwap.iloc[-1]
        latest_supertrend = supertrend.iloc[-1]
        latest_direction = direction.iloc[-1]
        
        # Determine trend state
        trend_signals = []
        
        # Price vs SMAs
        trend_signals.append(1 if latest_close > latest_sma20 else -1)
        trend_signals.append(1 if latest_close > latest_sma50 else -1)
        trend_signals.append(1 if latest_close > latest_sma200 else -1)
        
        # SMA alignment
        trend_signals.append(1 if latest_sma20 > latest_sma50 else -1)
        trend_signals.append(1 if latest_sma50 > latest_sma200 else -1)
        
        # Adaptive MAs
        trend_signals.append(1 if latest_close > latest_kama else -1)
        trend_signals.append(1 if latest_close > latest_frama else -1)
        trend_signals.append(1 if latest_close > latest_kalman else -1)
        
        # VWAP
        trend_signals.append(1 if latest_close > latest_vwap else -1)
        
        # SuperTrend
        trend_signals.append(latest_direction)
        
        # Combine signals
        trend_signal = sum(trend_signals) / len(trend_signals)
        
        # Determine trend strength (0 to 1)
        trend_strength = abs(trend_signal)
        
        # Determine trend direction (-1 to 1)
        trend_direction = np.sign(trend_signal)
        
        return {
            'trend_signal': trend_signal,
            'trend_strength': trend_strength,
            'trend_direction': trend_direction,
            'indicators': {
                'sma20': latest_sma20,
                'sma50': latest_sma50,
                'sma200': latest_sma200,
                'ema20': latest_ema20,
                'ema50': latest_ema50,
                'kama': latest_kama,
                'frama': latest_frama,
                'kalman': latest_kalman,
                'vwap': latest_vwap,
                'supertrend': latest_supertrend,
                'supertrend_direction': latest_direction
            }
        }


class FractalAnalysis:
    """Fractal indicator analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.hurst = HurstExponent(lags=self.config.get('hurst_lags', 100))
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze fractal indicators"""
        close = df['close']
        
        # Calculate Hurst exponent
        hurst_value = self.hurst.calculate(close)
        hurst_regime = self.hurst.interpret(hurst_value)
        
        # Determine fractal dimension (1 to 2)
        # Hurst = 1 means smooth trend (dimension = 1)
        # Hurst = 0.5 means random walk (dimension = 1.5)
        # Hurst = 0 means mean-reverting (dimension = 2)
        fractal_dimension = 2 - hurst_value
        
        # Determine market efficiency
        # Higher Hurst = more trending = less efficient
        market_efficiency = 1 - abs(hurst_value - 0.5) * 2
        
        # Determine fractal signal (-1 to 1)
        # Positive for trending, negative for mean-reverting
        fractal_signal = (hurst_value - 0.5) * 2
        
        return {
            'hurst_exponent': hurst_value,
            'hurst_regime': hurst_regime,
            'fractal_dimension': fractal_dimension,
            'market_efficiency': market_efficiency,
            'fractal_signal': fractal_signal
        }


class Tier1TechnicalAnalysis(TierBase):
    """
    Tier 1: Market Input & Core Technical Analysis
    
    Processes raw market data to extract technical indicators and patterns:
    - Momentum indicators (RSI, MACD, Stochastic, ADX)
    - Volatility indicators (ATR, Bollinger Bands, TTM Squeeze)
    - Trend indicators (SMA, EMA, VWAP, KAMA, FRAMA, SuperTrend)
    - Fractal analysis (Hurst Exponent)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 1: Technical Analysis", config)
        self.momentum_analysis = None
        self.volatility_analysis = None
        self.trend_analysis = None
        self.fractal_analysis = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.momentum_analysis = MomentumAnalysis(self.config.get('momentum', {}))
        self.volatility_analysis = VolatilityAnalysis(self.config.get('volatility', {}))
        self.trend_analysis = TrendAnalysis(self.config.get('trend', {}))
        self.fractal_analysis = FractalAnalysis(self.config.get('fractal', {}))
    
    def get_required_columns(self) -> List[str]:
        """Get required columns for this tier"""
        return ['open', 'high', 'low', 'close', 'volume']
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[Any] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> MarketStateVector:
        """
        Process market data and generate technical analysis output
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Not used in Tier 1
            additional_inputs: Additional inputs (not used in Tier 1)
            
        Returns:
            MarketStateVector with technical analysis results
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 1")
            return None
        try:
        
            # Analyze momentum indicators
            momentum_results = self.momentum_analysis.analyze(market_data)
            
            # Analyze volatility indicators
            volatility_results = self.volatility_analysis.analyze(market_data)
            
            # Analyze trend indicators
            trend_results = self.trend_analysis.analyze(market_data)
            
            # Analyze fractal indicators
            fractal_results = self.fractal_analysis.analyze(market_data)
            
            # Combine results into a market state vector
            trend_direction = trend_results['trend_direction']
            trend_strength = trend_results['trend_strength']
            volatility_state = volatility_results['volatility_state']
            momentum = momentum_results['momentum_signal']
            fractal_dimension = fractal_results['fractal_dimension']
            overbought_oversold = momentum_results['overbought_oversold']
            
            # Calculate overall signal (-1.0 to 1.0)
            signal_value = (
                0.4 * trend_direction * trend_strength +
                0.3 * momentum +
                0.2 * fractal_results['fractal_signal'] +
                0.1 * volatility_results['volatility_signal']
            )
            
            # Calculate confidence (0.0 to 1.0)
            # Higher confidence when indicators align
            signal_components = [
                trend_direction,
                np.sign(momentum),
                np.sign(fractal_results['fractal_signal'])
            ]
            
            # Count how many components agree with the overall signal
            agreement = sum(1 for s in signal_components if np.sign(s) == np.sign(signal_value))
            confidence = agreement / len(signal_components)
            
            # Adjust confidence based on trend strength and volatility
            if volatility_state == 'high':
                confidence *= 0.8  # Reduce confidence in high volatility
            
            confidence = min(max(confidence, 0.0), 1.0)  # Ensure in range [0,1]
            
            # Create metadata with all indicator values
            metadata = {
                'momentum': momentum_results['indicators'],
                'volatility': volatility_results['indicators'],
                'trend': trend_results['indicators'],
                'fractal': {
                    'hurst_exponent': fractal_results['hurst_exponent'],
                    'hurst_regime': fractal_results['hurst_regime']
                }
            }
            
            # Create market state vector
            market_state = MarketStateVector(
                timestamp=market_data.index[-1],
                signal_value=signal_value,
                confidence=confidence,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                volatility_state=volatility_state,
                momentum=momentum,
                fractal_dimension=fractal_dimension,
                overbought_oversold=overbought_oversold,
                metadata=metadata
            )
            
            self.last_output = market_state
            return market_state
            
        except Exception as e:
            logger.error(f"Error processing Tier 1: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=250, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(250).cumsum() + 100,
        'high': np.random.randn(250).cumsum() + 102,
        'low': np.random.randn(250).cumsum() + 98,
        'close': np.random.randn(250).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 250)
    }, index=dates)
    
    # Initialize and process
    tier1 = Tier1TechnicalAnalysis()
    tier1.initialize()
    result = tier1.process(df)
    
    # Print results
    logger.info("\n=== Tier 1: Technical Analysis Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Trend Direction: {result.trend_direction:.2f}")
    logger.info(f"Trend Strength: {result.trend_strength:.2f}")
    logger.info(f"Volatility State: {result.volatility_state}")
    logger.info(f"Momentum: {result.momentum:.2f}")
    logger.info(f"Fractal Dimension: {result.fractal_dimension:.2f}")
    logger.info(f"Overbought/Oversold: {result.overbought_oversold:.2f}")
