"""
Elite Regime Detection and Volatility Analysis Module
"""
from enum import Enum
from typing import Dict, Optional
import logging
import numpy as np
import pandas as pd
import numpy
import pandas

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    MEAN_REVERTING = "mean_reverting"
    VOLATILE_SIDEWAYS = "volatile_sideways"
    QUIET_RANGE = "quiet_range"
    UNKNOWN = "unknown"


class EliteRegimeDetector:
    """
    Core regime classification with volatility analysis and simple EWMA forecast.
    Expects market_data DataFrame with columns: ['open','high','low','close','volume']
    """
    def __init__(
        self,
        fast_ma: int = 20,
        slow_ma: int = 50,
        vol_window: int = 20,
        ewma_lambda: float = 0.94,
        lookback: int = 250,
        trend_gap_threshold: float = 0.002,
        bb_width_thresholds: tuple = (0.01, 0.03),  # (quiet, wide)
    ) -> None:
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.vol_window = vol_window
        self.ewma_lambda = ewma_lambda
        self.lookback = lookback
        self.trend_gap_threshold = trend_gap_threshold
        self.bb_width_thresholds = bb_width_thresholds

    def analyze(self, market_data: pd.DataFrame) -> Dict:
        if market_data is None or len(market_data) < max(self.slow_ma, self.vol_window, 60):
            return {"regime": MarketRegime.UNKNOWN.value, "reason": "insufficient_data"}

        df = market_data.copy()
        df = df.dropna().tail(self.lookback)

        # Basic features
        df['ret'] = df['close'].pct_change()
        df['ma_fast'] = df['close'].rolling(self.fast_ma).mean()
        df['ma_slow'] = df['close'].rolling(self.slow_ma).mean()
        df['std'] = df['ret'].rolling(self.vol_window).std()
        df['bb_width'] = (df['std'] / df['ma_slow']).replace([np.inf, -np.inf], np.nan)

        # ATR for robustness
        df['tr1'] = (df['high'] - df['low']).abs()
        df['tr2'] = (df['high'] - df['close'].shift()).abs()
        df['tr3'] = (df['low'] - df['close'].shift()).abs()
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr'] = df['tr'].rolling(14).mean()

        latest = df.iloc[-1]
        close = df['close']

        # Trend metrics
        ma_gap = (latest['ma_fast'] - latest['ma_slow']) / latest['close']
        trend_slope = (df['ma_fast'].diff().tail(5).mean() or 0) / (latest['close'] or 1)

        # Hurst exponent (simplified)
        hurst = self._hurst_exponent(close.dropna().values[-200:])

        # Realized volatility and percentile
        realized_vol = df['std'].iloc[-1]
        vol_hist = df['std'].dropna()
        vol_percentile = float((vol_hist <= realized_vol).mean()) if len(vol_hist) > 0 else 0.5

        # Bollinger bandwidth
        bb_width = float(df['bb_width'].iloc[-1]) if not np.isnan(df['bb_width'].iloc[-1]) else 0.0

        # EWMA volatility forecast
        ewma_vol = self._ewma_vol(df['ret'].dropna().values)

        # Regime rules
        regime = MarketRegime.UNKNOWN
        reason = []

        # Trending if MA gap is large and Hurst > 0.55
        if abs(ma_gap) > self.trend_gap_threshold and hurst is not None and hurst > 0.55:
            if latest['ma_fast'] > latest['ma_slow'] and trend_slope > 0:
                regime = MarketRegime.TRENDING_BULL
                reason.append('ma_gap_large + hurst_trend + slope_up')
            elif latest['ma_fast'] < latest['ma_slow'] and trend_slope < 0:
                regime = MarketRegime.TRENDING_BEAR
                reason.append('ma_gap_large + hurst_trend + slope_down')

        # Mean-reverting if Hurst < 0.45 and not trending
        if regime == MarketRegime.UNKNOWN and hurst is not None and hurst < 0.45:
            regime = MarketRegime.MEAN_REVERTING
            reason.append('hurst_mean_reverting')

        # Volatile sideways if high vol percentile and wide bands without clear MA dominance
        quiet_th, wide_th = self.bb_width_thresholds
        if regime == MarketRegime.UNKNOWN and vol_percentile > 0.8 and bb_width > wide_th and abs(ma_gap) <= self.trend_gap_threshold:
            regime = MarketRegime.VOLATILE_SIDEWAYS
            reason.append('high_vol_percentile + wide_bands + small_ma_gap')

        # Quiet range if low vol percentile and narrow bands
        if regime == MarketRegime.UNKNOWN and vol_percentile < 0.2 and bb_width < quiet_th:
            regime = MarketRegime.QUIET_RANGE
            reason.append('low_vol_percentile + narrow_bands')

        # Fallback based on sign of recent return if still unknown
        if regime == MarketRegime.UNKNOWN:
            recent_ret = df['ret'].tail(20).mean()
            if recent_ret > 0:
                regime = MarketRegime.TRENDING_BULL if abs(ma_gap) > self.trend_gap_threshold/2 else MarketRegime.QUIET_RANGE
            elif recent_ret < 0:
                regime = MarketRegime.TRENDING_BEAR if abs(ma_gap) > self.trend_gap_threshold/2 else MarketRegime.QUIET_RANGE
            reason.append('fallback_recent_returns')

        adaptive = self.get_adaptive_parameters(regime, realized_vol, vol_percentile)

        return {
            'regime': regime.value,
            'reason': ",".join(reason) if reason else 'rule_default',
            'metrics': {
                'ma_gap': float(ma_gap),
                'trend_slope': float(trend_slope),
                'hurst': None if hurst is None else float(hurst),
                'realized_vol': float(realized_vol) if not np.isnan(realized_vol) else None,
                'vol_percentile': float(vol_percentile),
                'bb_width': float(bb_width),
                'atr': float(latest['atr']) if not np.isnan(latest['atr']) else None,
                'ewma_vol': float(ewma_vol) if ewma_vol is not None else None,
            },
            'adaptive': adaptive,
        }

    def _ewma_vol(self, returns: np.ndarray) -> Optional[float]:
        if returns.size == 0:
            return None
        lam = self.ewma_lambda
        var = returns[0] ** 2
        for r in returns[1:]:
            var = lam * var + (1 - lam) * (r ** 2)
        return float(np.sqrt(var))

    def _hurst_exponent(self, ts: np.ndarray) -> Optional[float]:
        try:
            if ts.size < 100:
                return None
            lags = np.arange(2, min(100, ts.size // 2))
            if lags.size < 5:
                return None
            tau = np.array([np.sqrt(np.std(ts[lag:] - ts[:-lag])) for lag in lags])
            tau = tau[(tau > 0) & np.isfinite(tau)]
            lags = lags[:tau.size]
            if tau.size < 5:
                return None
            log_lags = np.log(lags)
            log_tau = np.log(tau)
            slope = np.polyfit(log_lags, log_tau, 1)[0]
            H = slope
            return float(H)
        except Exception as e:
            logger.warning(f"Hurst exponent calculation failed: {e}")
            return None

    def get_adaptive_parameters(self, regime: MarketRegime, realized_vol: float, vol_percentile: float) -> Dict:
        # Base defaults
        params = {
            'position_size_factor': 1.0,
            'stop_atr_mult': 1.5,
            'take_profit_r_multiple': 2.0,
            'strategy_bias': 'balanced',
        }
        if regime == MarketRegime.TRENDING_BULL or regime == MarketRegime.TRENDING_BEAR:
            params.update({
                'position_size_factor': max(0.6, 1.2 - vol_percentile * 0.6),
                'stop_atr_mult': 1.8,
                'take_profit_r_multiple': 2.5,
                'strategy_bias': 'breakout-trend-follow',
            })
        elif regime == MarketRegime.MEAN_REVERTING:
            params.update({
                'position_size_factor': max(0.5, 1.0 - vol_percentile * 0.5),
                'stop_atr_mult': 1.2,
                'take_profit_r_multiple': 1.5,
                'strategy_bias': 'mean-reversion',
            })
        elif regime == MarketRegime.VOLATILE_SIDEWAYS:
            params.update({
                'position_size_factor': 0.5,
                'stop_atr_mult': 2.2,
                'take_profit_r_multiple': 1.2,
                'strategy_bias': 'range-breakout-scalp',
            })
        elif regime == MarketRegime.QUIET_RANGE:
            params.update({
                'position_size_factor': 1.1,
                'stop_atr_mult': 1.0,
                'take_profit_r_multiple': 1.2,
                'strategy_bias': 'range-fade',
            })
        return params

    @staticmethod
    def correlation_regime(corr_matrix: np.ndarray, high_thresh: float = 0.6, low_thresh: float = 0.2) -> str:
        if corr_matrix.ndim != 2 or corr_matrix.shape[0] != corr_matrix.shape[1]:
            return 'invalid'
        n = corr_matrix.shape[0]
        mask = ~np.eye(n, dtype=bool)
        mean_offdiag = float(np.mean(corr_matrix[mask]))
        if mean_offdiag >= high_thresh:
            return 'high_correlation'
        if mean_offdiag <= low_thresh:
            return 'low_correlation'
        return 'normal_correlation'
