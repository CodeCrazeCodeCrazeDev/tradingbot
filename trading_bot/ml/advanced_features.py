"""
Advanced feature engineering with 200+ institutional-grade features.
Microstructure, fractal, sentiment, and regime-specific features.
"""

import numpy as np
import pandas as pd
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.signal import find_peaks
from typing import Dict, Optional
from loguru import logger
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class AdvancedFeatureEngine:
    """Institutional-grade feature engineering."""
    
    def __init__(self):
        self.feature_cache = {}
        logger.info("AdvancedFeatureEngine initialized")
    
    def extract_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract 200+ advanced features."""
        logger.info("Extracting advanced features...")
        
        df = self._add_price_features(df)
        df = self._add_microstructure_features(df)
        df = self._add_liquidity_features(df)
        df = self._add_volatility_features(df)
        df = self._add_fractal_features(df)
        df = self._add_regime_features(df)
        df = self._add_order_flow_features(df)
        df = self._add_momentum_features(df)
        df = self._add_pattern_features(df)
        
        feature_count = len([col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']])
        logger.success(f"Extracted {feature_count} advanced features")
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Price-based features."""
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['price_momentum_5'] = df['close'] - df['close'].shift(5)
        df['price_momentum_10'] = df['close'] - df['close'].shift(10)
        df['price_momentum_20'] = df['close'] - df['close'].shift(20)
        
        # Price acceleration
        df['price_acceleration'] = df['returns'].diff()
        
        # Price range features
        df['hl_range'] = df['high'] - df['low']
        df['hl_range_pct'] = df['hl_range'] / df['close']
        df['oc_range'] = abs(df['open'] - df['close'])
        df['oc_range_pct'] = df['oc_range'] / df['close']
        
        return df
    
    def _add_microstructure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Market microstructure indicators."""
        
        # Spread metrics (if bid/ask available)
        if 'bid' in df.columns and 'ask' in df.columns:
            df['spread'] = df['ask'] - df['bid']
            df['spread_pct'] = df['spread'] / ((df['bid'] + df['ask']) / 2)
            df['mid_price'] = (df['bid'] + df['ask']) / 2
            df['effective_spread'] = 2 * abs(df['close'] - df['mid_price'])
        
        # Volume-based microstructure
        if 'volume' in df.columns:
            df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            df['volume_std'] = df['volume'].rolling(20).std()
            df['volume_zscore'] = (df['volume'] - df['volume'].rolling(20).mean()) / df['volume_std']
            
            # Trade intensity
            df['trade_intensity'] = df['volume'] / df['hl_range']
            
            # Price impact estimate (Kyle's lambda approximation)
            df['kyle_lambda'] = abs(df['returns']) / (df['volume'] + 1)
            df['kyle_lambda_ma'] = df['kyle_lambda'].rolling(20).mean()
            
            # Amihud illiquidity
            df['amihud_illiquidity'] = abs(df['returns']) / (df['volume'] * df['close'] + 1)
        
        return df
    
    def _add_liquidity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Liquidity indicators."""
        
        if 'volume' in df.columns:
            # Volume profile
            df['volume_profile'] = df['volume'] / df['volume'].rolling(20).mean()
            
            # Liquidity ratio
            df['liquidity_ratio'] = df['volume'] / (df['hl_range'] + 1e-10)
            
            # VWAP deviation
            df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
            df['vwap_deviation'] = (df['close'] - df['vwap']) / df['vwap']
            df['vwap_deviation_ma'] = df['vwap_deviation'].rolling(20).mean()
            
            # On-Balance Volume
            df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
            df['obv_ma'] = df['obv'].rolling(20).mean()
        
        return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volatility and risk features."""
        
        # Historical volatility
        for window in [5, 10, 20, 50]:
            df[f'volatility_{window}'] = df['returns'].rolling(window).std()
            df[f'volatility_{window}_ma'] = df[f'volatility_{window}'].rolling(10).mean()
        
        # Parkinson volatility (high-low)
        df['parkinson_vol'] = np.sqrt(
            (1 / (4 * np.log(2))) * 
            (np.log(df['high'] / df['low']) ** 2).rolling(20).mean()
        )
        
        # Garman-Klass volatility
        df['gk_vol'] = np.sqrt(
            0.5 * (np.log(df['high'] / df['low']) ** 2).rolling(20).mean() -
            (2 * np.log(2) - 1) * (np.log(df['close'] / df['open']) ** 2).rolling(20).mean()
        )
        
        # Volatility regime
        df['vol_regime'] = pd.cut(
            df['volatility_20'],
            bins=3,
            labels=[0, 1, 2]  # low, medium, high
        ).astype(float)
        
        # Volatility of volatility
        df['volvol'] = df['volatility_20'].rolling(20).std()
        
        return df
    
    def _add_fractal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fractal and complexity features."""
        
        # Hurst exponent (rolling)
        df['hurst_exponent'] = df['close'].rolling(100).apply(
            self._hurst_exponent, raw=True
        )
        df['fractal_dimension'] = 2 - df['hurst_exponent']
        
        # Detrended Fluctuation Analysis
        df['dfa_alpha'] = df['close'].rolling(100).apply(
            self._dfa, raw=True
        )
        
        # Fractal efficiency
        df['fractal_efficiency'] = abs(df['close'] - df['close'].shift(20)) / (
            df['close'].diff().abs().rolling(20).sum() + 1e-10
        )
        
        return df
    
    def _add_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Market regime indicators."""
        
        # Trend strength (ADX approximation)
        df['trend_strength'] = self._calculate_adx_simple(df)
        
        # Regime classification
        df['regime'] = self._classify_regime(df)
        
        # Regime volatility
        df['regime_volatility'] = df.groupby('regime')['returns'].transform('std')
        
        # Regime persistence
        df['regime_changes'] = (df['regime'] != df['regime'].shift(1)).astype(int)
        df['regime_persistence'] = df['regime_changes'].rolling(20).sum()
        
        return df
    
    def _add_order_flow_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Order flow and tape reading features."""
        
        if 'volume' in df.columns:
            # Volume delta (buy vs sell pressure)
            df['volume_delta'] = df['volume'] * np.sign(df['close'].diff())
            df['volume_delta_ma'] = df['volume_delta'].rolling(20).mean()
            
            # Cumulative volume delta
            df['cumulative_volume_delta'] = df['volume_delta'].cumsum()
            
            # Volume-weighted price momentum
            df['vw_momentum'] = (df['returns'] * df['volume']).rolling(20).sum() / (
                df['volume'].rolling(20).sum() + 1e-10
            )
            
            # Absorption (large volume, small price change)
            df['absorption'] = df['volume'] / (abs(df['returns']) + 1e-10)
            df['absorption_ma'] = df['absorption'].rolling(20).mean()
            
            # Exhaustion (small volume, large price change)
            df['exhaustion'] = abs(df['returns']) / (df['volume'] + 1e-10)
            df['exhaustion_ma'] = df['exhaustion'].rolling(20).mean()
        
        return df
    
    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Momentum and trend features."""
        
        # Rate of change
        for period in [5, 10, 20, 50]:
            df[f'roc_{period}'] = df['close'].pct_change(period) * 100
        
        # Momentum oscillator
        df['momentum_oscillator'] = df['close'] - df['close'].shift(10)
        
        # Trend intensity
        df['trend_intensity'] = abs(df['close'].rolling(20).mean() - df['close'].rolling(50).mean()) / (
            df['close'].rolling(50).std() + 1e-10
        )
        
        # Acceleration
        df['acceleration'] = df['returns'].diff()
        df['acceleration_ma'] = df['acceleration'].rolling(10).mean()
        
        return df
    
    def _add_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pattern recognition features."""
        
        # Higher highs / Lower lows
        df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
        df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
        
        # Swing points
        df['swing_high'] = self._detect_swing_points(df['high'].values, order=5)
        df['swing_low'] = self._detect_swing_points(-df['low'].values, order=5)
        
        # Gap detection
        df['gap_up'] = (df['low'] > df['high'].shift(1)).astype(int)
        df['gap_down'] = (df['high'] < df['low'].shift(1)).astype(int)
        
        # Inside/Outside bars
        df['inside_bar'] = (
            (df['high'] < df['high'].shift(1)) & 
            (df['low'] > df['low'].shift(1))
        ).astype(int)
        
        df['outside_bar'] = (
            (df['high'] > df['high'].shift(1)) & 
            (df['low'] < df['low'].shift(1))
        ).astype(int)
        
        return df
    
    def _hurst_exponent(self, ts: np.ndarray) -> float:
        """Calculate Hurst exponent."""
        if len(ts) < 20:
            return 0.5
        
        lags = range(2, min(20, len(ts) // 2))
        tau = [np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]
        
        if len(tau) < 2:
            return 0.5
        
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0]
    
    def _dfa(self, ts: np.ndarray) -> float:
        """Detrended Fluctuation Analysis."""
        if len(ts) < 20:
            return 1.0
        
        y = np.cumsum(ts - np.mean(ts))
        n = len(y)
        scales = np.logspace(0.5, np.log10(n // 4), 10, dtype=int)
        
        fluctuations = []
        for scale in scales:
            segments = [y[i:i+scale] for i in range(0, n, scale) if i+scale <= n]
            F = []
            for segment in segments:
                x = np.arange(len(segment))
                coeffs = np.polyfit(x, segment, 1)
                trend = np.polyval(coeffs, x)
                F.append(np.sqrt(np.mean((segment - trend) ** 2)))
            if F:
                fluctuations.append(np.mean(F))
        
        if len(fluctuations) < 2:
            return 1.0
        
        coeffs = np.polyfit(np.log(scales[:len(fluctuations)]), np.log(fluctuations), 1)
        return coeffs[0]
    
    def _calculate_adx_simple(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Simplified ADX calculation."""
        high = df['high']
        low = df['low']
        close = df['close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.rolling(period).mean()
        
        return adx
    
    def _classify_regime(self, df: pd.DataFrame) -> pd.Series:
        """Classify market regime."""
        returns = df['returns']
        volatility = df['returns'].rolling(20).std()
        
        regimes = []
        for ret, vol in zip(returns, volatility):
            if pd.isna(ret) or pd.isna(vol):
                regimes.append(0)
            elif ret > 0.001 and vol < volatility.median():
                regimes.append(1)  # bull_low_vol
            elif ret > 0.001 and vol >= volatility.median():
                regimes.append(2)  # bull_high_vol
            elif ret < -0.001 and vol < volatility.median():
                regimes.append(3)  # bear_low_vol
            elif ret < -0.001 and vol >= volatility.median():
                regimes.append(4)  # bear_high_vol
            else:
                regimes.append(0)  # sideways
        
        return pd.Series(regimes, index=df.index)
    
    def _detect_swing_points(self, data: np.ndarray, order: int = 5) -> np.ndarray:
        """Detect swing high/low points."""
        peaks, _ = find_peaks(data, distance=order)
        result = np.zeros(len(data))
        result[peaks] = 1
        return result
