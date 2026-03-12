"""
Skill #2: Hurst Exponent Calculator
===================================

Measures market persistence/mean-reversion tendency using the Hurst exponent.
H < 0.5: Mean-reverting (anti-persistent)
H = 0.5: Random walk
H > 0.5: Trending (persistent)
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketCharacter(Enum):
    """Market character based on Hurst exponent."""
    STRONGLY_MEAN_REVERTING = "strongly_mean_reverting"  # H < 0.3
    MEAN_REVERTING = "mean_reverting"  # 0.3 <= H < 0.45
    RANDOM_WALK = "random_walk"  # 0.45 <= H <= 0.55
    TRENDING = "trending"  # 0.55 < H <= 0.7
    STRONGLY_TRENDING = "strongly_trending"  # H > 0.7


@dataclass
class HurstResult:
    """Result of Hurst exponent calculation."""
    hurst_exponent: float
    market_character: MarketCharacter
    confidence: float
    r_squared: float
    interpretation: str
    recommended_strategy: str
    half_life: Optional[float]  # For mean-reverting series
    sample_size: int
    method: str


@dataclass
class RollingHurst:
    """Rolling Hurst exponent over time."""
    timestamps: List[datetime]
    values: List[float]
    characters: List[MarketCharacter]
    regime_changes: List[Tuple[datetime, MarketCharacter, MarketCharacter]]


class HurstExponentCalculator:
    """
    Advanced Hurst Exponent Calculator.
    
    Implements multiple methods:
    - Rescaled Range (R/S) Analysis
    - Detrended Fluctuation Analysis (DFA)
    - Variance Ratio Test
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_window = self.config.get('min_window', 20)
        self.max_window = self.config.get('max_window', 100)
        self.rolling_window = self.config.get('rolling_window', 50)
        self.history: List[HurstResult] = []
        
        logger.info("HurstExponentCalculator initialized")
    
    def calculate(
        self,
        prices: np.ndarray,
        method: str = 'rs',
        timestamps: Optional[List[datetime]] = None
    ) -> HurstResult:
        """
        Calculate Hurst exponent.
        
        Args:
            prices: Array of prices
            method: 'rs' (Rescaled Range), 'dfa' (DFA), or 'variance_ratio'
            timestamps: Optional timestamps for the data
            
        Returns:
            HurstResult with analysis
        """
        if len(prices) < self.min_window:
            return HurstResult(
                hurst_exponent=0.5,
                market_character=MarketCharacter.RANDOM_WALK,
                confidence=0.0,
                r_squared=0.0,
                interpretation="Insufficient data",
                recommended_strategy="Wait for more data",
                half_life=None,
                sample_size=len(prices),
                method=method
            )
        
        # Calculate returns
        returns = np.diff(np.log(prices))
        
        if method == 'rs':
            hurst, r_squared = self._rescaled_range(returns)
        elif method == 'dfa':
            hurst, r_squared = self._dfa(returns)
        elif method == 'variance_ratio':
            hurst, r_squared = self._variance_ratio(returns)
        else:
            hurst, r_squared = self._rescaled_range(returns)
        
        # Determine market character
        market_character = self._classify_market(hurst)
        
        # Calculate confidence
        confidence = self._calculate_confidence(r_squared, len(prices))
        
        # Get interpretation
        interpretation = self._get_interpretation(hurst, market_character)
        
        # Get recommended strategy
        recommended_strategy = self._get_strategy(market_character)
        
        # Calculate half-life for mean-reverting series
        half_life = None
        if hurst < 0.5:
            half_life = self._calculate_half_life(prices)
        
        result = HurstResult(
            hurst_exponent=hurst,
            market_character=market_character,
            confidence=confidence,
            r_squared=r_squared,
            interpretation=interpretation,
            recommended_strategy=recommended_strategy,
            half_life=half_life,
            sample_size=len(prices),
            method=method
        )
        
        self.history.append(result)
        
        return result
    
    def _rescaled_range(self, returns: np.ndarray) -> Tuple[float, float]:
        """
        Calculate Hurst exponent using Rescaled Range (R/S) analysis.
        
        The R/S statistic scales as n^H where H is the Hurst exponent.
        """
        n = len(returns)
        
        # Define window sizes
        max_k = min(n // 2, self.max_window)
        min_k = max(self.min_window, 10)
        
        if max_k <= min_k:
            return 0.5, 0.0
        
        # Generate window sizes (powers of 2 work well)
        window_sizes = []
        k = min_k
        while k <= max_k:
            window_sizes.append(k)
            k = int(k * 1.5)
        
        if len(window_sizes) < 3:
            window_sizes = list(range(min_k, max_k + 1, max(1, (max_k - min_k) // 5)))
        
        rs_values = []
        
        for window_size in window_sizes:
            rs_list = []
            
            # Calculate R/S for each window
            for start in range(0, n - window_size + 1, window_size):
                window = returns[start:start + window_size]
                
                # Mean-adjusted cumulative sum
                mean = np.mean(window)
                cumsum = np.cumsum(window - mean)
                
                # Range
                R = np.max(cumsum) - np.min(cumsum)
                
                # Standard deviation
                S = np.std(window, ddof=1)
                
                if S > 0:
                    rs_list.append(R / S)
            
            if rs_list:
                rs_values.append((np.log(window_size), np.log(np.mean(rs_list))))
        
        if len(rs_values) < 2:
            return 0.5, 0.0
        
        # Linear regression to find Hurst exponent
        x = np.array([v[0] for v in rs_values])
        y = np.array([v[1] for v in rs_values])
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))
        
        # Clamp Hurst to valid range
        hurst = max(0.0, min(1.0, slope))
        
        return hurst, max(0, r_squared)
    
    def _dfa(self, returns: np.ndarray) -> Tuple[float, float]:
        """
        Calculate Hurst exponent using Detrended Fluctuation Analysis.
        
        DFA is more robust to non-stationarities than R/S analysis.
        """
        n = len(returns)
        
        # Integrate the series
        y = np.cumsum(returns - np.mean(returns))
        
        # Define window sizes
        min_window = max(4, self.min_window // 2)
        max_window = min(n // 4, self.max_window)
        
        if max_window <= min_window:
            return 0.5, 0.0
        
        window_sizes = []
        s = min_window
        while s <= max_window:
            window_sizes.append(int(s))
            s *= 1.5
        
        fluctuations = []
        
        for window_size in window_sizes:
            # Divide into windows
            n_windows = n // window_size
            
            if n_windows < 1:
                continue
            
            f2 = []
            
            for i in range(n_windows):
                start = i * window_size
                end = start + window_size
                segment = y[start:end]
                
                # Fit linear trend
                x = np.arange(window_size)
                coeffs = np.polyfit(x, segment, 1)
                trend = np.polyval(coeffs, x)
                
                # Calculate fluctuation
                f2.append(np.mean((segment - trend) ** 2))
            
            if f2:
                fluctuations.append((np.log(window_size), np.log(np.sqrt(np.mean(f2)))))
        
        if len(fluctuations) < 2:
            return 0.5, 0.0
        
        # Linear regression
        x = np.array([f[0] for f in fluctuations])
        y = np.array([f[1] for f in fluctuations])
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))
        
        hurst = max(0.0, min(1.0, slope))
        
        return hurst, max(0, r_squared)
    
    def _variance_ratio(self, returns: np.ndarray) -> Tuple[float, float]:
        """
        Calculate Hurst exponent using Variance Ratio test.
        
        For a random walk, Var(k-period returns) = k * Var(1-period returns)
        """
        n = len(returns)
        
        # Calculate variance at different lags
        lags = [2, 4, 8, 16, 32]
        lags = [l for l in lags if l < n // 2]
        
        if len(lags) < 2:
            return 0.5, 0.0
        
        var_1 = np.var(returns, ddof=1)
        
        if var_1 == 0:
            return 0.5, 0.0
        
        log_ratios = []
        
        for k in lags:
            # Calculate k-period returns
            k_returns = np.array([
                np.sum(returns[i:i + k])
                for i in range(0, n - k + 1, k)
            ])
            
            if len(k_returns) < 2:
                continue
            
            var_k = np.var(k_returns, ddof=1)
            
            # Variance ratio
            vr = var_k / (k * var_1)
            
            # For Hurst: VR(k) ~ k^(2H-1)
            # log(VR) ~ (2H-1) * log(k)
            if vr > 0:
                log_ratios.append((np.log(k), np.log(vr)))
        
        if len(log_ratios) < 2:
            return 0.5, 0.0
        
        x = np.array([lr[0] for lr in log_ratios])
        y = np.array([lr[1] for lr in log_ratios])
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Hurst = (slope + 1) / 2
        hurst = (slope + 1) / 2
        hurst = max(0.0, min(1.0, hurst))
        
        # R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))
        
        return hurst, max(0, r_squared)
    
    def _classify_market(self, hurst: float) -> MarketCharacter:
        """Classify market character based on Hurst exponent."""
        if hurst < 0.3:
            return MarketCharacter.STRONGLY_MEAN_REVERTING
        elif hurst < 0.45:
            return MarketCharacter.MEAN_REVERTING
        elif hurst <= 0.55:
            return MarketCharacter.RANDOM_WALK
        elif hurst <= 0.7:
            return MarketCharacter.TRENDING
        else:
            return MarketCharacter.STRONGLY_TRENDING
    
    def _calculate_confidence(self, r_squared: float, sample_size: int) -> float:
        """Calculate confidence in the Hurst estimate."""
        # Base confidence from R-squared
        confidence = r_squared * 0.7
        
        # Adjust for sample size
        if sample_size >= 500:
            confidence += 0.3
        elif sample_size >= 200:
            confidence += 0.2
        elif sample_size >= 100:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _get_interpretation(self, hurst: float, character: MarketCharacter) -> str:
        """Get human-readable interpretation."""
        interpretations = {
            MarketCharacter.STRONGLY_MEAN_REVERTING: (
                f"H={hurst:.3f}: Strongly mean-reverting. Price tends to reverse "
                "quickly. Excellent for mean-reversion strategies."
            ),
            MarketCharacter.MEAN_REVERTING: (
                f"H={hurst:.3f}: Mean-reverting tendency. Price shows some "
                "tendency to return to mean. Consider range-trading."
            ),
            MarketCharacter.RANDOM_WALK: (
                f"H={hurst:.3f}: Random walk behavior. No predictable pattern. "
                "Technical analysis may be less effective."
            ),
            MarketCharacter.TRENDING: (
                f"H={hurst:.3f}: Trending behavior. Price tends to continue "
                "in the same direction. Trend-following recommended."
            ),
            MarketCharacter.STRONGLY_TRENDING: (
                f"H={hurst:.3f}: Strongly trending. High persistence. "
                "Strong trend-following with momentum strategies."
            ),
        }
        return interpretations.get(character, f"H={hurst:.3f}")
    
    def _get_strategy(self, character: MarketCharacter) -> str:
        """Get recommended strategy based on market character."""
        strategies = {
            MarketCharacter.STRONGLY_MEAN_REVERTING: (
                "Mean-reversion: Buy oversold, sell overbought. "
                "Use Bollinger Bands, RSI extremes. Tight stops."
            ),
            MarketCharacter.MEAN_REVERTING: (
                "Range trading: Trade between support/resistance. "
                "Fade moves to range extremes. Medium stops."
            ),
            MarketCharacter.RANDOM_WALK: (
                "Reduce position size. Use wider stops. "
                "Consider fundamental analysis or wait for regime change."
            ),
            MarketCharacter.TRENDING: (
                "Trend following: Buy breakouts, add on pullbacks. "
                "Use moving averages, trailing stops."
            ),
            MarketCharacter.STRONGLY_TRENDING: (
                "Aggressive trend following: Pyramid positions. "
                "Wide trailing stops. Hold for extended moves."
            ),
        }
        return strategies.get(character, "No specific strategy")
    
    def _calculate_half_life(self, prices: np.ndarray) -> Optional[float]:
        """
        Calculate mean-reversion half-life using Ornstein-Uhlenbeck process.
        
        Half-life = -ln(2) / ln(theta) where theta is the mean-reversion speed.
        """
        try:
            # Log prices for better stationarity
            log_prices = np.log(prices)
            
            # Lag-1 regression: y_t = a + b * y_{t-1} + e
            y = log_prices[1:]
            x = log_prices[:-1]
            
            # Add constant
            X = np.column_stack([np.ones(len(x)), x])
            
            # OLS
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
            theta = coeffs[1]
            
            if theta <= 0 or theta >= 1:
                return None
            
            half_life = -np.log(2) / np.log(theta)
            
            # Sanity check
            if half_life < 1 or half_life > len(prices):
                return None
            
            return half_life
            
        except Exception:
            return None
    
    def calculate_rolling(
        self,
        prices: np.ndarray,
        timestamps: List[datetime],
        window: Optional[int] = None,
        method: str = 'rs'
    ) -> RollingHurst:
        """
        Calculate rolling Hurst exponent.
        
        Args:
            prices: Array of prices
            timestamps: List of timestamps
            window: Rolling window size
            method: Calculation method
            
        Returns:
            RollingHurst with time series of Hurst values
        """
        window = window or self.rolling_window
        
        if len(prices) < window + 10:
            return RollingHurst(
                timestamps=[],
                values=[],
                characters=[],
                regime_changes=[]
            )
        
        result_timestamps = []
        result_values = []
        result_characters = []
        regime_changes = []
        
        prev_character = None
        
        for i in range(window, len(prices)):
            window_prices = prices[i - window:i]
            
            result = self.calculate(window_prices, method=method)
            
            result_timestamps.append(timestamps[i])
            result_values.append(result.hurst_exponent)
            result_characters.append(result.market_character)
            
            # Detect regime changes
            if prev_character is not None and result.market_character != prev_character:
                regime_changes.append((
                    timestamps[i],
                    prev_character,
                    result.market_character
                ))
            
            prev_character = result.market_character
        
        return RollingHurst(
            timestamps=result_timestamps,
            values=result_values,
            characters=result_characters,
            regime_changes=regime_changes
        )
    
    def compare_methods(self, prices: np.ndarray) -> Dict[str, HurstResult]:
        """Compare Hurst estimates from different methods."""
        results = {}
        
        for method in ['rs', 'dfa', 'variance_ratio']:
            results[method] = self.calculate(prices, method=method)
        
        return results
    
    def get_consensus(self, prices: np.ndarray) -> HurstResult:
        """Get consensus Hurst estimate from all methods."""
        results = self.compare_methods(prices)
        
        # Weight by R-squared
        total_weight = 0
        weighted_hurst = 0
        
        for method, result in results.items():
            weight = result.r_squared
            weighted_hurst += result.hurst_exponent * weight
            total_weight += weight
        
        if total_weight > 0:
            consensus_hurst = weighted_hurst / total_weight
        else:
            consensus_hurst = 0.5
        
        # Create consensus result
        character = self._classify_market(consensus_hurst)
        avg_r_squared = np.mean([r.r_squared for r in results.values()])
        
        return HurstResult(
            hurst_exponent=consensus_hurst,
            market_character=character,
            confidence=self._calculate_confidence(avg_r_squared, len(prices)),
            r_squared=avg_r_squared,
            interpretation=self._get_interpretation(consensus_hurst, character),
            recommended_strategy=self._get_strategy(character),
            half_life=results['rs'].half_life,
            sample_size=len(prices),
            method='consensus'
        )
