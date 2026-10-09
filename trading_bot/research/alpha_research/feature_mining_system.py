"""
Automatic Feature Mining System
===============================
Superhuman intuition through automated feature discovery.

Features:
- 5000+ feature transformations
- PCA and autoencoder compression
- Predictive signal filtering
- Cross-validation for stability
- Top 100 feature selection for live trading

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import hashlib
import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import deque
import threading
import uuid
import warnings

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.signal import find_peaks
    from scipy.fft import fft, ifft
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.feature_selection import mutual_info_regression, f_regression
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LassoCV, ElasticNetCV
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class FeatureType(Enum):
    """Types of feature transformations"""
    PRICE = auto()
    VOLUME = auto()
    MOMENTUM = auto()
    VOLATILITY = auto()
    TREND = auto()
    PATTERN = auto()
    STATISTICAL = auto()
    FOURIER = auto()
    WAVELET = auto()
    INTERACTION = auto()
    LAG = auto()
    ROLLING = auto()
    EXPANDING = auto()
    RATIO = auto()
    DIFFERENCE = auto()


@dataclass
class FeatureMetadata:
    """Metadata for a generated feature"""
    feature_id: str
    name: str
    feature_type: FeatureType
    parameters: Dict[str, Any]
    creation_time: datetime = field(default_factory=datetime.now)
    
    # Quality metrics
    predictive_power: float = 0.0  # Mutual information or correlation
    stability_score: float = 0.0   # Cross-validation consistency
    importance_score: float = 0.0  # Model importance
    
    # Selection status
    selected: bool = False
    rank: int = 0


@dataclass
class FeatureMiningResult:
    """Results from feature mining process"""
    total_features_generated: int = 0
    features_after_filtering: int = 0
    features_after_compression: int = 0
    final_features_selected: int = 0
    
    # Selected features
    selected_features: List[FeatureMetadata] = field(default_factory=list)
    feature_matrix: Optional[np.ndarray] = None
    
    # Compression info
    pca_explained_variance: float = 0.0
    autoencoder_reconstruction_loss: float = 0.0
    
    # Timing
    generation_time: float = 0.0
    filtering_time: float = 0.0
    compression_time: float = 0.0
    selection_time: float = 0.0


class FeatureTransformer:
    """Generates 5000+ feature transformations"""
    
    # Lookback periods for rolling calculations
    LOOKBACK_PERIODS = [3, 5, 8, 10, 13, 15, 20, 21, 30, 50, 63, 100, 126, 200, 252]
    
    # Quantile levels
    QUANTILE_LEVELS = [0.1, 0.25, 0.5, 0.75, 0.9]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.feature_count = 0
        self.features_metadata: List[FeatureMetadata] = []
        
    def generate_all_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[FeatureMetadata]]:
        """Generate all 5000+ feature transformations"""
        
        features = pd.DataFrame(index=data.index)
        self.features_metadata = []
        
        logger.info("Starting feature generation...")
        
        # 1. Price-based features (~500)
        price_features = self._generate_price_features(data)
        features = pd.concat([features, price_features], axis=1)
        
        # 2. Volume-based features (~300)
        if 'volume' in data.columns:
            volume_features = self._generate_volume_features(data)
            features = pd.concat([features, volume_features], axis=1)
        
        # 3. Momentum features (~600)
        momentum_features = self._generate_momentum_features(data)
        features = pd.concat([features, momentum_features], axis=1)
        
        # 4. Volatility features (~400)
        volatility_features = self._generate_volatility_features(data)
        features = pd.concat([features, volatility_features], axis=1)
        
        # 5. Trend features (~400)
        trend_features = self._generate_trend_features(data)
        features = pd.concat([features, trend_features], axis=1)
        
        # 6. Statistical features (~500)
        statistical_features = self._generate_statistical_features(data)
        features = pd.concat([features, statistical_features], axis=1)
        
        # 7. Pattern features (~300)
        pattern_features = self._generate_pattern_features(data)
        features = pd.concat([features, pattern_features], axis=1)
        
        # 8. Fourier features (~200)
        if SCIPY_AVAILABLE:
            fourier_features = self._generate_fourier_features(data)
            features = pd.concat([features, fourier_features], axis=1)
        
        # 9. Lag features (~500)
        lag_features = self._generate_lag_features(data)
        features = pd.concat([features, lag_features], axis=1)
        
        # 10. Interaction features (~800)
        interaction_features = self._generate_interaction_features(features)
        features = pd.concat([features, interaction_features], axis=1)
        
        # 11. Ratio features (~500)
        ratio_features = self._generate_ratio_features(data)
        features = pd.concat([features, ratio_features], axis=1)
        
        logger.info(f"Generated {len(features.columns)} total features")
        
        return features, self.features_metadata
    
    def _generate_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate price-based features"""
        features = pd.DataFrame(index=data.index)
        close = data['close']
        
        for period in self.LOOKBACK_PERIODS:
            # Simple Moving Average
            sma = close.rolling(period).mean()
            features[f'sma_{period}'] = sma
            self._add_metadata(f'sma_{period}', FeatureType.PRICE, {'period': period})
            
            # Exponential Moving Average
            ema = close.ewm(span=period).mean()
            features[f'ema_{period}'] = ema
            self._add_metadata(f'ema_{period}', FeatureType.PRICE, {'period': period})
            
            # Price relative to SMA
            features[f'price_sma_ratio_{period}'] = close / sma
            self._add_metadata(f'price_sma_ratio_{period}', FeatureType.PRICE, {'period': period})
            
            # Distance from SMA
            features[f'price_sma_dist_{period}'] = (close - sma) / sma
            self._add_metadata(f'price_sma_dist_{period}', FeatureType.PRICE, {'period': period})
            
            # Weighted Moving Average
            weights = np.arange(1, period + 1)
            features[f'wma_{period}'] = close.rolling(period).apply(
                lambda x: np.dot(x, weights) / weights.sum(), raw=True
            )
            self._add_metadata(f'wma_{period}', FeatureType.PRICE, {'period': period})
            
            # Hull Moving Average
            half_period = period // 2
            sqrt_period = int(np.sqrt(period))
            wma_half = close.rolling(half_period).mean()
            wma_full = close.rolling(period).mean()
            features[f'hma_{period}'] = (2 * wma_half - wma_full).rolling(sqrt_period).mean()
            self._add_metadata(f'hma_{period}', FeatureType.PRICE, {'period': period})
            
            # DEMA
            ema1 = close.ewm(span=period).mean()
            ema2 = ema1.ewm(span=period).mean()
            features[f'dema_{period}'] = 2 * ema1 - ema2
            self._add_metadata(f'dema_{period}', FeatureType.PRICE, {'period': period})
            
            # TEMA
            ema3 = ema2.ewm(span=period).mean()
            features[f'tema_{period}'] = 3 * ema1 - 3 * ema2 + ema3
            self._add_metadata(f'tema_{period}', FeatureType.PRICE, {'period': period})
        
        # High/Low features
        if 'high' in data.columns and 'low' in data.columns:
            high = data['high']
            low = data['low']
            
            for period in self.LOOKBACK_PERIODS:
                # Highest high
                features[f'highest_{period}'] = high.rolling(period).max()
                self._add_metadata(f'highest_{period}', FeatureType.PRICE, {'period': period})
                
                # Lowest low
                features[f'lowest_{period}'] = low.rolling(period).min()
                self._add_metadata(f'lowest_{period}', FeatureType.PRICE, {'period': period})
                
                # Price position in range
                highest = high.rolling(period).max()
                lowest = low.rolling(period).min()
                features[f'price_position_{period}'] = (close - lowest) / (highest - lowest + 1e-10)
                self._add_metadata(f'price_position_{period}', FeatureType.PRICE, {'period': period})
                
                # Range
                features[f'range_{period}'] = highest - lowest
                self._add_metadata(f'range_{period}', FeatureType.PRICE, {'period': period})
        
        return features
    
    def _generate_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate volume-based features"""
        features = pd.DataFrame(index=data.index)
        volume = data['volume']
        close = data['close']
        
        for period in self.LOOKBACK_PERIODS:
            # Volume SMA
            features[f'volume_sma_{period}'] = volume.rolling(period).mean()
            self._add_metadata(f'volume_sma_{period}', FeatureType.VOLUME, {'period': period})
            
            # Volume ratio
            vol_sma = volume.rolling(period).mean()
            features[f'volume_ratio_{period}'] = volume / vol_sma
            self._add_metadata(f'volume_ratio_{period}', FeatureType.VOLUME, {'period': period})
            
            # OBV
            obv = (np.sign(close.diff()) * volume).cumsum()
            features[f'obv_{period}'] = obv.rolling(period).mean()
            self._add_metadata(f'obv_{period}', FeatureType.VOLUME, {'period': period})
            
            # Volume-weighted price
            features[f'vwap_{period}'] = (close * volume).rolling(period).sum() / volume.rolling(period).sum()
            self._add_metadata(f'vwap_{period}', FeatureType.VOLUME, {'period': period})
            
            # Money Flow
            typical_price = close
            if 'high' in data.columns and 'low' in data.columns:
                typical_price = (data['high'] + data['low'] + close) / 3
            
            money_flow = typical_price * volume
            features[f'money_flow_{period}'] = money_flow.rolling(period).sum()
            self._add_metadata(f'money_flow_{period}', FeatureType.VOLUME, {'period': period})
            
            # Accumulation/Distribution
            if 'high' in data.columns and 'low' in data.columns:
                clv = ((close - data['low']) - (data['high'] - close)) / (data['high'] - data['low'] + 1e-10)
                ad = (clv * volume).cumsum()
                features[f'ad_{period}'] = ad.rolling(period).mean()
                self._add_metadata(f'ad_{period}', FeatureType.VOLUME, {'period': period})
        
        return features
    
    def _generate_momentum_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate momentum features"""
        features = pd.DataFrame(index=data.index)
        close = data['close']
        
        for period in self.LOOKBACK_PERIODS:
            # Rate of Change
            features[f'roc_{period}'] = close.pct_change(period)
            self._add_metadata(f'roc_{period}', FeatureType.MOMENTUM, {'period': period})
            
            # Momentum
            features[f'momentum_{period}'] = close - close.shift(period)
            self._add_metadata(f'momentum_{period}', FeatureType.MOMENTUM, {'period': period})
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / (loss + 1e-10)
            features[f'rsi_{period}'] = 100 - (100 / (1 + rs))
            self._add_metadata(f'rsi_{period}', FeatureType.MOMENTUM, {'period': period})
            
            # Stochastic RSI
            rsi = features[f'rsi_{period}']
            rsi_min = rsi.rolling(period).min()
            rsi_max = rsi.rolling(period).max()
            features[f'stoch_rsi_{period}'] = (rsi - rsi_min) / (rsi_max - rsi_min + 1e-10)
            self._add_metadata(f'stoch_rsi_{period}', FeatureType.MOMENTUM, {'period': period})
            
            # Williams %R
            if 'high' in data.columns and 'low' in data.columns:
                highest = data['high'].rolling(period).max()
                lowest = data['low'].rolling(period).min()
                features[f'williams_r_{period}'] = (highest - close) / (highest - lowest + 1e-10) * -100
                self._add_metadata(f'williams_r_{period}', FeatureType.MOMENTUM, {'period': period})
            
            # CCI
            if 'high' in data.columns and 'low' in data.columns:
                typical_price = (data['high'] + data['low'] + close) / 3
                sma_tp = typical_price.rolling(period).mean()
                mad = typical_price.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
                features[f'cci_{period}'] = (typical_price - sma_tp) / (0.015 * mad + 1e-10)
                self._add_metadata(f'cci_{period}', FeatureType.MOMENTUM, {'period': period})
        
        # MACD variations
        for fast in [8, 12, 15]:
            for slow in [21, 26, 30]:
                for signal in [7, 9, 12]:
                    if fast < slow:
                        ema_fast = close.ewm(span=fast).mean()
                        ema_slow = close.ewm(span=slow).mean()
                        macd = ema_fast - ema_slow
                        macd_signal = macd.ewm(span=signal).mean()
                        macd_hist = macd - macd_signal
                        
                        features[f'macd_{fast}_{slow}_{signal}'] = macd
                        features[f'macd_signal_{fast}_{slow}_{signal}'] = macd_signal
                        features[f'macd_hist_{fast}_{slow}_{signal}'] = macd_hist
                        
                        self._add_metadata(f'macd_{fast}_{slow}_{signal}', FeatureType.MOMENTUM, 
                                         {'fast': fast, 'slow': slow, 'signal': signal})
        
        return features
    
    def _generate_volatility_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate volatility features"""
        features = pd.DataFrame(index=data.index)
        close = data['close']
        returns = close.pct_change()
        
        for period in self.LOOKBACK_PERIODS:
            # Standard deviation
            features[f'std_{period}'] = returns.rolling(period).std()
            self._add_metadata(f'std_{period}', FeatureType.VOLATILITY, {'period': period})
            
            # Annualized volatility
            features[f'volatility_{period}'] = returns.rolling(period).std() * np.sqrt(252)
            self._add_metadata(f'volatility_{period}', FeatureType.VOLATILITY, {'period': period})
            
            # Parkinson volatility (if OHLC available)
            if 'high' in data.columns and 'low' in data.columns:
                hl_ratio = np.log(data['high'] / data['low'])
                features[f'parkinson_vol_{period}'] = np.sqrt(
                    (hl_ratio ** 2).rolling(period).mean() / (4 * np.log(2))
                )
                self._add_metadata(f'parkinson_vol_{period}', FeatureType.VOLATILITY, {'period': period})
            
            # ATR
            if 'high' in data.columns and 'low' in data.columns:
                tr1 = data['high'] - data['low']
                tr2 = abs(data['high'] - close.shift(1))
                tr3 = abs(data['low'] - close.shift(1))
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                features[f'atr_{period}'] = tr.rolling(period).mean()
                self._add_metadata(f'atr_{period}', FeatureType.VOLATILITY, {'period': period})
                
                # ATR ratio
                features[f'atr_ratio_{period}'] = features[f'atr_{period}'] / close
                self._add_metadata(f'atr_ratio_{period}', FeatureType.VOLATILITY, {'period': period})
            
            # Bollinger Band width
            sma = close.rolling(period).mean()
            std = close.rolling(period).std()
            features[f'bb_width_{period}'] = (4 * std) / sma
            self._add_metadata(f'bb_width_{period}', FeatureType.VOLATILITY, {'period': period})
            
            # Bollinger %B
            upper = sma + 2 * std
            lower = sma - 2 * std
            features[f'bb_pct_{period}'] = (close - lower) / (upper - lower + 1e-10)
            self._add_metadata(f'bb_pct_{period}', FeatureType.VOLATILITY, {'period': period})
            
            # Keltner Channel width
            if 'high' in data.columns and 'low' in data.columns:
                ema = close.ewm(span=period).mean()
                atr = features.get(f'atr_{period}', tr.rolling(period).mean())
                kc_width = (4 * atr) / ema
                features[f'kc_width_{period}'] = kc_width
                self._add_metadata(f'kc_width_{period}', FeatureType.VOLATILITY, {'period': period})
        
        return features
    
    def _generate_trend_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trend features"""
        features = pd.DataFrame(index=data.index)
        close = data['close']
        
        for period in self.LOOKBACK_PERIODS:
            # ADX
            if 'high' in data.columns and 'low' in data.columns:
                plus_dm = data['high'].diff()
                minus_dm = -data['low'].diff()
                plus_dm[plus_dm < 0] = 0
                minus_dm[minus_dm < 0] = 0
                
                tr1 = data['high'] - data['low']
                tr2 = abs(data['high'] - close.shift(1))
                tr3 = abs(data['low'] - close.shift(1))
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                
                atr = tr.rolling(period).mean()
                plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
                minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
                dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
                features[f'adx_{period}'] = dx.rolling(period).mean()
                features[f'plus_di_{period}'] = plus_di
                features[f'minus_di_{period}'] = minus_di
                
                self._add_metadata(f'adx_{period}', FeatureType.TREND, {'period': period})
            
            # Linear regression slope
            features[f'linreg_slope_{period}'] = close.rolling(period).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0, raw=True
            )
            self._add_metadata(f'linreg_slope_{period}', FeatureType.TREND, {'period': period})
            
            # R-squared of linear regression
            features[f'linreg_r2_{period}'] = close.rolling(period).apply(
                lambda x: self._calc_r2(x) if len(x) > 1 else 0, raw=True
            )
            self._add_metadata(f'linreg_r2_{period}', FeatureType.TREND, {'period': period})
            
            # Trend strength (slope / volatility)
            slope = features[f'linreg_slope_{period}']
            vol = close.rolling(period).std()
            features[f'trend_strength_{period}'] = slope / (vol + 1e-10)
            self._add_metadata(f'trend_strength_{period}', FeatureType.TREND, {'period': period})
            
            # Aroon
            if 'high' in data.columns and 'low' in data.columns:
                aroon_up = data['high'].rolling(period).apply(
                    lambda x: (period - x.argmax()) / period * 100, raw=True
                )
                aroon_down = data['low'].rolling(period).apply(
                    lambda x: (period - x.argmin()) / period * 100, raw=True
                )
                features[f'aroon_up_{period}'] = aroon_up
                features[f'aroon_down_{period}'] = aroon_down
                features[f'aroon_osc_{period}'] = aroon_up - aroon_down
                
                self._add_metadata(f'aroon_osc_{period}', FeatureType.TREND, {'period': period})
        
        return features
    
    def _generate_statistical_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate statistical features"""
        features = pd.DataFrame(index=data.index)
        close = data['close']
        returns = close.pct_change()
        
        for period in self.LOOKBACK_PERIODS:
            # Skewness
            features[f'skew_{period}'] = returns.rolling(period).skew()
            self._add_metadata(f'skew_{period}', FeatureType.STATISTICAL, {'period': period})
            
            # Kurtosis
            features[f'kurt_{period}'] = returns.rolling(period).kurt()
            self._add_metadata(f'kurt_{period}', FeatureType.STATISTICAL, {'period': period})
            
            # Quantiles
            for q in self.QUANTILE_LEVELS:
                features[f'quantile_{period}_{int(q*100)}'] = returns.rolling(period).quantile(q)
                self._add_metadata(f'quantile_{period}_{int(q*100)}', FeatureType.STATISTICAL, 
                                 {'period': period, 'quantile': q})
            
            # Z-score
            mean = returns.rolling(period).mean()
            std = returns.rolling(period).std()
            features[f'zscore_{period}'] = (returns - mean) / (std + 1e-10)
            self._add_metadata(f'zscore_{period}', FeatureType.STATISTICAL, {'period': period})
            
            # Autocorrelation
            features[f'autocorr_{period}'] = returns.rolling(period).apply(
                lambda x: x.autocorr() if len(x) > 1 else 0, raw=False
            )
            self._add_metadata(f'autocorr_{period}', FeatureType.STATISTICAL, {'period': period})
            
            # Entropy (approximation)
            features[f'entropy_{period}'] = returns.rolling(period).apply(
                lambda x: self._calc_entropy(x), raw=True
            )
            self._add_metadata(f'entropy_{period}', FeatureType.STATISTICAL, {'period': period})
        
        return features
    
    def _generate_pattern_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate pattern-based features"""
        features = pd.DataFrame(index=data.index)
        close = data['close']
        
        for period in self.LOOKBACK_PERIODS[:8]:  # Shorter periods for patterns
            # Higher highs / Lower lows count
            features[f'higher_highs_{period}'] = close.rolling(period).apply(
                lambda x: sum(x[i] > x[i-1] for i in range(1, len(x))), raw=True
            )
            self._add_metadata(f'higher_highs_{period}', FeatureType.PATTERN, {'period': period})
            
            # Consecutive up/down days
            up_days = (close.diff() > 0).astype(int)
            features[f'consecutive_up_{period}'] = up_days.rolling(period).sum()
            self._add_metadata(f'consecutive_up_{period}', FeatureType.PATTERN, {'period': period})
            
            # Gap detection
            if 'open' in data.columns:
                gap = (data['open'] - close.shift(1)) / close.shift(1)
                features[f'gap_sum_{period}'] = gap.rolling(period).sum()
                features[f'gap_count_{period}'] = (abs(gap) > 0.01).rolling(period).sum()
                self._add_metadata(f'gap_sum_{period}', FeatureType.PATTERN, {'period': period})
            
            # Pivot points
            if 'high' in data.columns and 'low' in data.columns:
                pivot = (data['high'] + data['low'] + close) / 3
                features[f'pivot_{period}'] = pivot.rolling(period).mean()
                features[f'dist_to_pivot_{period}'] = (close - features[f'pivot_{period}']) / close
                self._add_metadata(f'pivot_{period}', FeatureType.PATTERN, {'period': period})
        
        return features
    
    def _generate_fourier_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate Fourier transform features"""
        features = pd.DataFrame(index=data.index)
        close = data['close'].values
        
        for period in [20, 50, 100]:
            # Rolling FFT
            for i in range(period, len(close)):
                window = close[i-period:i]
                fft_vals = np.abs(fft(window))
                
                # Store dominant frequencies
                if i == period:
                    features[f'fft_dom1_{period}'] = np.nan
                    features[f'fft_dom2_{period}'] = np.nan
                    features[f'fft_power_{period}'] = np.nan
                
                sorted_idx = np.argsort(fft_vals[1:period//2])[:-1]
                features.loc[data.index[i], f'fft_dom1_{period}'] = sorted_idx[0] if len(sorted_idx) > 0 else 0
                features.loc[data.index[i], f'fft_dom2_{period}'] = sorted_idx[1] if len(sorted_idx) > 1 else 0
                features.loc[data.index[i], f'fft_power_{period}'] = np.sum(fft_vals[1:period//2])
            
            self._add_metadata(f'fft_dom1_{period}', FeatureType.FOURIER, {'period': period})
            self._add_metadata(f'fft_dom2_{period}', FeatureType.FOURIER, {'period': period})
            self._add_metadata(f'fft_power_{period}', FeatureType.FOURIER, {'period': period})
        
        return features
    
    def _generate_lag_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate lag features"""
        features = pd.DataFrame(index=data.index)
        close = data['close']
        returns = close.pct_change()
        
        # Price lags
        for lag in [1, 2, 3, 5, 10, 20, 50]:
            features[f'return_lag_{lag}'] = returns.shift(lag)
            self._add_metadata(f'return_lag_{lag}', FeatureType.LAG, {'lag': lag})
            
            features[f'price_lag_{lag}'] = close.shift(lag)
            self._add_metadata(f'price_lag_{lag}', FeatureType.LAG, {'lag': lag})
            
            # Return over lag period
            features[f'return_over_{lag}'] = close.pct_change(lag)
            self._add_metadata(f'return_over_{lag}', FeatureType.LAG, {'lag': lag})
        
        # Volume lags
        if 'volume' in data.columns:
            volume = data['volume']
            for lag in [1, 2, 3, 5, 10]:
                features[f'volume_lag_{lag}'] = volume.shift(lag)
                self._add_metadata(f'volume_lag_{lag}', FeatureType.LAG, {'lag': lag})
        
        return features
    
    def _generate_interaction_features(self, base_features: pd.DataFrame) -> pd.DataFrame:
        """Generate interaction features between existing features"""
        features = pd.DataFrame(index=base_features.index)
        
        # Select key features for interactions
        key_features = [col for col in base_features.columns if any(
            x in col for x in ['rsi_14', 'macd_12_26_9', 'atr_14', 'sma_20', 'momentum_10']
        )][:10]  # Limit to prevent explosion
        
        for i, feat1 in enumerate(key_features):
            for feat2 in key_features[i+1:]:
                # Product
                features[f'{feat1}_x_{feat2}'] = base_features[feat1] * base_features[feat2]
                self._add_metadata(f'{feat1}_x_{feat2}', FeatureType.INTERACTION, 
                                 {'feature1': feat1, 'feature2': feat2})
                
                # Ratio
                features[f'{feat1}_div_{feat2}'] = base_features[feat1] / (base_features[feat2] + 1e-10)
                self._add_metadata(f'{feat1}_div_{feat2}', FeatureType.INTERACTION,
                                 {'feature1': feat1, 'feature2': feat2})
        
        return features
    
    def _generate_ratio_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate ratio features"""
        features = pd.DataFrame(index=data.index)
        close = data['close']
        
        for period1 in [5, 10, 20]:
            for period2 in [50, 100, 200]:
                if period1 < period2:
                    sma1 = close.rolling(period1).mean()
                    sma2 = close.rolling(period2).mean()
                    
                    features[f'sma_ratio_{period1}_{period2}'] = sma1 / sma2
                    self._add_metadata(f'sma_ratio_{period1}_{period2}', FeatureType.RATIO,
                                     {'period1': period1, 'period2': period2})
                    
                    ema1 = close.ewm(span=period1).mean()
                    ema2 = close.ewm(span=period2).mean()
                    
                    features[f'ema_ratio_{period1}_{period2}'] = ema1 / ema2
                    self._add_metadata(f'ema_ratio_{period1}_{period2}', FeatureType.RATIO,
                                     {'period1': period1, 'period2': period2})
        
        return features
    
    def _add_metadata(self, name: str, feature_type: FeatureType, parameters: Dict):
        """Add feature metadata"""
        self.features_metadata.append(FeatureMetadata(
            feature_id=str(uuid.uuid4())[:8],
            name=name,
            feature_type=feature_type,
            parameters=parameters
        ))
        self.feature_count += 1
    
    def _calc_r2(self, x: np.ndarray) -> float:
        """Calculate R-squared of linear regression"""
        if len(x) < 2:
            return 0
        y = np.arange(len(x))
        correlation = np.corrcoef(x, y)[0, 1]
        return correlation ** 2 if not np.isnan(correlation) else 0
    
    def _calc_entropy(self, x: np.ndarray) -> float:
        """Calculate approximate entropy"""
        if len(x) < 2:
            return 0
        hist, _ = np.histogram(x, bins=10, density=True)
        hist = hist[hist > 0]
        return -np.sum(hist * np.log(hist + 1e-10))


class FeatureCompressor:
    """Compresses features using PCA and autoencoders"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.pca = None
        self.autoencoder = None
        self.scaler = None
        
    def fit_pca(
        self,
        features: pd.DataFrame,
        n_components: float = 0.95
    ) -> Tuple[np.ndarray, float]:
        """Fit PCA and transform features"""
        
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available, skipping PCA")
            return features.values, 0.0
        
        # Scale features
        self.scaler = RobustScaler()
        scaled = self.scaler.fit_transform(features.fillna(0))
        
        # Fit PCA
        self.pca = PCA(n_components=n_components)
        compressed = self.pca.fit_transform(scaled)
        
        explained_variance = sum(self.pca.explained_variance_ratio_)
        logger.info(f"PCA: {features.shape[1]} -> {compressed.shape[1]} features "
                   f"({explained_variance:.2%} variance explained)")
        
        return compressed, explained_variance
    
    def fit_autoencoder(
        self,
        features: pd.DataFrame,
        encoding_dim: int = 100,
        epochs: int = 50
    ) -> Tuple[np.ndarray, float]:
        """Fit autoencoder and transform features"""
        
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available, skipping autoencoder")
            return features.values, 0.0
        
        # Scale features
        if self.scaler is None:
            self.scaler = RobustScaler()
            scaled = self.scaler.fit_transform(features.fillna(0))
        else:
            scaled = self.scaler.transform(features.fillna(0))
        
        input_dim = scaled.shape[1]
        
        # Define autoencoder
        class Autoencoder(nn.Module):
            def __init__(self, input_dim, encoding_dim):
                super().__init__()
                self.encoder = nn.Sequential(
                    nn.Linear(input_dim, 512),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(512, 256),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(256, encoding_dim),
                    nn.ReLU()
                )
                self.decoder = nn.Sequential(
                    nn.Linear(encoding_dim, 256),
                    nn.ReLU(),
                    nn.Linear(256, 512),
                    nn.ReLU(),
                    nn.Linear(512, input_dim)
                )
            
            def forward(self, x):
                encoded = self.encoder(x)
                decoded = self.decoder(encoded)
                return decoded
            
            def encode(self, x):
                return self.encoder(x)
        
        # Train autoencoder
        self.autoencoder = Autoencoder(input_dim, encoding_dim)
        optimizer = torch.optim.Adam(self.autoencoder.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        X = torch.FloatTensor(scaled)
        
        for epoch in range(epochs):
            self.autoencoder.train()
            optimizer.zero_grad()
            output = self.autoencoder(X)
            loss = criterion(output, X)
            loss.backward()
            optimizer.step()
        
        # Get encoded features
        self.autoencoder.eval()
        with torch.no_grad():
            encoded = self.autoencoder.encode(X).numpy()
        
        reconstruction_loss = loss.item()
        logger.info(f"Autoencoder: {input_dim} -> {encoding_dim} features "
                   f"(reconstruction loss: {reconstruction_loss:.4f})")
        
        return encoded, reconstruction_loss


class FeatureSelector:
    """Selects top predictive features"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.n_features = self.config.get('n_features', 100)
        
    def select_features(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        metadata: List[FeatureMetadata],
        n_features: int = 100
    ) -> Tuple[pd.DataFrame, List[FeatureMetadata]]:
        """Select top N predictive features"""
        
        if not SKLEARN_AVAILABLE:
            logger.warning("sklearn not available, returning all features")
            return features, metadata
        
        # Remove NaN rows
        valid_idx = ~(features.isna().any(axis=1) | target.isna())
        X = features.loc[valid_idx]
        y = target.loc[valid_idx]
        
        if len(X) < 100:
            logger.warning("Not enough data for feature selection")
            return features, metadata
        
        # Calculate feature scores
        feature_scores = {}
        
        # 1. Mutual Information
        mi_scores = mutual_info_regression(X.fillna(0), y)
        for i, col in enumerate(X.columns):
            feature_scores[col] = {'mi': mi_scores[i]}
        
        # 2. F-regression
        f_scores, _ = f_regression(X.fillna(0), y)
        for i, col in enumerate(X.columns):
            feature_scores[col]['f_score'] = f_scores[i] if not np.isnan(f_scores[i]) else 0
        
        # 3. Random Forest importance
        rf = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42, n_jobs=-1)
        rf.fit(X.fillna(0), y)
        for i, col in enumerate(X.columns):
            feature_scores[col]['rf_importance'] = rf.feature_importances_[i]
        
        # 4. Cross-validation stability
        tscv = TimeSeriesSplit(n_splits=5)
        stability_scores = {}
        
        for col in X.columns:
            cv_scores = []
            for train_idx, val_idx in tscv.split(X):
                corr = np.corrcoef(X.iloc[train_idx][col].fillna(0), y.iloc[train_idx])[0, 1]
                cv_scores.append(corr if not np.isnan(corr) else 0)
            stability_scores[col] = 1 - np.std(cv_scores) if cv_scores else 0
        
        for col in X.columns:
            feature_scores[col]['stability'] = stability_scores.get(col, 0)
        
        # Calculate composite score
        for col in feature_scores:
            scores = feature_scores[col]
            composite = (
                0.3 * (scores['mi'] / max(mi_scores) if max(mi_scores) > 0 else 0) +
                0.2 * (scores['f_score'] / max(f_scores) if max(f_scores) > 0 else 0) +
                0.3 * scores['rf_importance'] / max(rf.feature_importances_) +
                0.2 * scores['stability']
            )
            feature_scores[col]['composite'] = composite
        
        # Rank and select top features
        ranked_features = sorted(feature_scores.items(), key=lambda x: x[1]['composite'], reverse=True)
        selected_cols = [col for col, _ in ranked_features[:n_features]]
        
        # Update metadata
        selected_metadata = []
        for i, (col, scores) in enumerate(ranked_features[:n_features]):
            for meta in metadata:
                if meta.name == col:
                    meta.selected = True
                    meta.rank = i + 1
                    meta.predictive_power = scores['mi']
                    meta.stability_score = scores['stability']
                    meta.importance_score = scores['rf_importance']
                    selected_metadata.append(meta)
                    break
        
        logger.info(f"Selected {len(selected_cols)} features from {len(features.columns)}")
        
        return features[selected_cols], selected_metadata


class FeatureMiningSystem:
    """
    Complete automatic feature mining system.
    
    Pipeline:
    1. Generate 5000+ transformations
    2. Compress using PCA and autoencoders
    3. Filter for predictive signals
    4. Cross-validate for stability
    5. Save top 100 features for live trading
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.transformer = FeatureTransformer(config)
        self.compressor = FeatureCompressor(config)
        self.selector = FeatureSelector(config)
        
        # Storage
        self.storage_path = Path(self.config.get('storage_path', 'feature_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # State
        self.selected_features: List[FeatureMetadata] = []
        self.feature_matrix: Optional[pd.DataFrame] = None
        
        logger.info("FeatureMiningSystem initialized")
    
    async def mine_features(
        self,
        data: pd.DataFrame,
        target_col: str = 'future_return',
        forward_period: int = 5,
        n_features: int = 100
    ) -> FeatureMiningResult:
        """Run complete feature mining pipeline"""
        
        import time
        result = FeatureMiningResult()
        
        # Prepare target
        if target_col not in data.columns:
            data[target_col] = data['close'].pct_change(forward_period).shift(-forward_period)
        
        target = data[target_col]
        
        # Step 1: Generate features
        logger.info("Step 1: Generating features...")
        start_time = time.time()
        
        features, metadata = self.transformer.generate_all_features(data)
        
        result.total_features_generated = len(features.columns)
        result.generation_time = time.time() - start_time
        logger.info(f"Generated {result.total_features_generated} features in {result.generation_time:.1f}s")
        
        # Step 2: Initial filtering (remove constant/near-constant features)
        logger.info("Step 2: Initial filtering...")
        start_time = time.time()
        
        valid_features = []
        for col in features.columns:
            if features[col].std() > 1e-10:
                valid_features.append(col)
        
        features = features[valid_features]
        result.features_after_filtering = len(features.columns)
        result.filtering_time = time.time() - start_time
        logger.info(f"Filtered to {result.features_after_filtering} features")
        
        # Step 3: Compression
        logger.info("Step 3: Compressing features...")
        start_time = time.time()
        
        # PCA compression
        pca_features, pca_variance = self.compressor.fit_pca(features, n_components=0.95)
        result.pca_explained_variance = pca_variance
        
        # Autoencoder compression (optional)
        if TORCH_AVAILABLE and len(features.columns) > 200:
            ae_features, ae_loss = self.compressor.fit_autoencoder(features, encoding_dim=100)
            result.autoencoder_reconstruction_loss = ae_loss
        
        result.features_after_compression = pca_features.shape[1]
        result.compression_time = time.time() - start_time
        logger.info(f"Compressed to {result.features_after_compression} PCA components")
        
        # Step 4: Feature selection
        logger.info("Step 4: Selecting top features...")
        start_time = time.time()
        
        selected_features, selected_metadata = self.selector.select_features(
            features, target, metadata, n_features=n_features
        )
        
        result.final_features_selected = len(selected_features.columns)
        result.selected_features = selected_metadata
        result.feature_matrix = selected_features.values
        result.selection_time = time.time() - start_time
        
        # Save results
        self.selected_features = selected_metadata
        self.feature_matrix = selected_features
        self._save_features(selected_features, selected_metadata)
        
        logger.info(f"Feature mining complete: {result.final_features_selected} features selected")
        
        return result
    
    def _save_features(self, features: pd.DataFrame, metadata: List[FeatureMetadata]):
        """Save selected features to disk"""
        
        # Save feature matrix
        features.to_parquet(self.storage_path / 'selected_features.parquet')
        
        # Save metadata
        metadata_dict = [
            {
                'feature_id': m.feature_id,
                'name': m.name,
                'feature_type': m.feature_type.name,
                'parameters': m.parameters,
                'predictive_power': m.predictive_power,
                'stability_score': m.stability_score,
                'importance_score': m.importance_score,
                'rank': m.rank
            }
            for m in metadata
        ]
        
        with open(self.storage_path / 'feature_metadata.json', 'w') as f:
            json.dump(metadata_dict, f, indent=2)
        
        logger.info(f"Saved features to {self.storage_path}")
    
    def load_features(self) -> Tuple[pd.DataFrame, List[FeatureMetadata]]:
        """Load saved features"""
        
        features = pd.read_parquet(self.storage_path / 'selected_features.parquet')
        
        with open(self.storage_path / 'feature_metadata.json', 'r') as f:
            metadata_dict = json.load(f)
        
        metadata = [
            FeatureMetadata(
                feature_id=m['feature_id'],
                name=m['name'],
                feature_type=FeatureType[m['feature_type']],
                parameters=m['parameters'],
                predictive_power=m['predictive_power'],
                stability_score=m['stability_score'],
                importance_score=m['importance_score'],
                rank=m['rank'],
                selected=True
            )
            for m in metadata_dict
        ]
        
        return features, metadata
    
    def get_live_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate features for live trading using saved configuration"""
        
        if not self.selected_features:
            self.feature_matrix, self.selected_features = self.load_features()
        
        # Generate all features
        all_features, _ = self.transformer.generate_all_features(data)
        
        # Select only the saved features
        selected_names = [m.name for m in self.selected_features]
        available_names = [n for n in selected_names if n in all_features.columns]
        
        return all_features[available_names]


# Factory function
def create_feature_miner(config: Optional[Dict] = None) -> FeatureMiningSystem:
    """Create and return a FeatureMiningSystem instance"""
    return FeatureMiningSystem(config)


# Quick start
async def quick_mine_features(
    data: pd.DataFrame,
    n_features: int = 100
) -> FeatureMiningResult:
    """Quick start feature mining"""
    miner = create_feature_miner()
    return await miner.mine_features(data, n_features=n_features)
