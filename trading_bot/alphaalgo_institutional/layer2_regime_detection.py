"""
AlphaAlgo Institutional - Layer 2: Regime Detection
====================================================

The Regime Detection Layer is responsible for:
- Detecting volatility regimes
- Identifying correlation regimes
- Assessing liquidity regimes
- Determining trend vs mean-reversion states
- Detecting crisis vs normal transitions
- Monitoring policy regime shifts

This layer operates as the REGIME INTELLIGENCE UNIT.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from collections import deque

from .core_types import (
    VolatilityRegime, CorrelationRegime, LiquidityRegime, TrendRegime,
    MarketRegime, RegimeState, CommitteeType, CommitteeVote, CommitteeDecision,
    RiskLevel, SystemConstants
)

logger = logging.getLogger(__name__)


# =============================================================================
# REGIME DETECTION MODELS
# =============================================================================

@dataclass
class RegimeTransition:
    """Record of a regime transition."""
    from_regime: MarketRegime
    to_regime: MarketRegime
    transition_time: datetime
    confidence: float
    trigger: str
    duration_in_previous: timedelta = None


@dataclass
class RegimeProbabilities:
    """Probability distribution over regimes."""
    regime_probs: Dict[MarketRegime, float]
    most_likely: MarketRegime
    entropy: float  # Higher = more uncertainty
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def get_confidence(self) -> float:
        """Get confidence in most likely regime."""
        return self.regime_probs.get(self.most_likely, 0.0)


# =============================================================================
# HIDDEN MARKOV MODEL FOR REGIME DETECTION
# =============================================================================

class HiddenMarkovRegimeDetector:
    """
    Hidden Markov Model for regime detection.
    
    Uses:
    - Volatility observations
    - Return observations
    - Volume observations
    
    To infer hidden regime states.
    """
    
    def __init__(self, n_regimes: int = 4):
        try:
            self.n_regimes = n_regimes
        
            # Regime mapping
            self.regime_map = {
                0: MarketRegime.CALM,
                1: MarketRegime.NORMAL,
                2: MarketRegime.VOLATILE,
                3: MarketRegime.CRISIS
            }
        
            # Transition matrix (initialized with reasonable priors)
            self.transition_matrix = np.array([
                [0.90, 0.08, 0.02, 0.00],  # From CALM
                [0.05, 0.85, 0.08, 0.02],  # From NORMAL
                [0.02, 0.10, 0.80, 0.08],  # From VOLATILE
                [0.01, 0.05, 0.14, 0.80],  # From CRISIS
            ])
        
            # Emission parameters (mean, std) for each regime
            self.emission_params = {
                0: {'vol_mean': 0.10, 'vol_std': 0.02, 'ret_mean': 0.0005, 'ret_std': 0.005},
                1: {'vol_mean': 0.15, 'vol_std': 0.03, 'ret_mean': 0.0003, 'ret_std': 0.010},
                2: {'vol_mean': 0.25, 'vol_std': 0.05, 'ret_mean': 0.0000, 'ret_std': 0.020},
                3: {'vol_mean': 0.50, 'vol_std': 0.10, 'ret_mean': -0.002, 'ret_std': 0.040},
            }
        
            # State tracking
            self.current_state_probs = np.array([0.1, 0.7, 0.15, 0.05])
            self.state_history: List[int] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def update(self, volatility: float, returns: float) -> RegimeProbabilities:
        """
        Update regime probabilities given new observations.
        
        Uses forward algorithm for filtering.
        """
        # Compute emission probabilities
        try:
            emission_probs = np.zeros(self.n_regimes)
            for state in range(self.n_regimes):
                params = self.emission_params[state]
            
                # Volatility likelihood
                vol_prob = self._gaussian_pdf(volatility, params['vol_mean'], params['vol_std'])
            
                # Return likelihood
                ret_prob = self._gaussian_pdf(returns, params['ret_mean'], params['ret_std'])
            
                emission_probs[state] = vol_prob * ret_prob
        
            # Forward step: predict then update
            predicted_probs = self.transition_matrix.T @ self.current_state_probs
            updated_probs = predicted_probs * emission_probs
        
            # Normalize
            if updated_probs.sum() > 0:
                updated_probs /= updated_probs.sum()
            else:
                updated_probs = self.current_state_probs
        
            self.current_state_probs = updated_probs
        
            # Track state
            most_likely_state = int(np.argmax(updated_probs))
            self.state_history.append(most_likely_state)
        
            # Compute entropy
            entropy = -np.sum(updated_probs * np.log(updated_probs + 1e-10))
        
            # Create regime probabilities
            regime_probs = {
                self.regime_map[i]: float(updated_probs[i])
                for i in range(self.n_regimes)
            }
        
            return RegimeProbabilities(
                regime_probs=regime_probs,
                most_likely=self.regime_map[most_likely_state],
                entropy=float(entropy)
            )
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _gaussian_pdf(self, x: float, mean: float, std: float) -> float:
        """Compute Gaussian PDF."""
        return np.exp(-0.5 * ((x - mean) / std) ** 2) / (std * np.sqrt(2 * np.pi))
    
    def get_transition_probability(self, from_regime: MarketRegime, to_regime: MarketRegime) -> float:
        """Get transition probability between regimes."""
        try:
            from_idx = list(self.regime_map.values()).index(from_regime)
            to_idx = list(self.regime_map.values()).index(to_regime)
            return float(self.transition_matrix[from_idx, to_idx])
        except Exception as e:
            logger.error(f"Error in get_transition_probability: {e}")
            raise


# =============================================================================
# BAYESIAN CHANGE POINT DETECTOR
# =============================================================================

class BayesianChangePointDetector:
    """
    Bayesian online change point detection.
    
    Detects structural breaks in:
    - Volatility
    - Correlation
    - Mean returns
    """
    
    def __init__(self, hazard_rate: float = 0.01):
        try:
            self.hazard_rate = hazard_rate  # Prior probability of change point
        
            # Run length distribution
            self.run_length_probs: List[float] = [1.0]
            self.max_run_length = 500
        
            # Sufficient statistics for Gaussian model
            self.sum_x: List[float] = [0.0]
            self.sum_x2: List[float] = [0.0]
            self.n: List[int] = [0]
        
            # Prior parameters
            self.prior_mean = 0.0
            self.prior_var = 1.0
        
            # Change point history
            self.change_points: List[Tuple[int, float, datetime]] = []
            self.observation_count = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def update(self, observation: float) -> Tuple[bool, float]:
        """
        Update with new observation.
        
        Returns:
            Tuple of (change_point_detected, change_probability)
        """
        try:
            self.observation_count += 1
        
            # Compute predictive probabilities for each run length
            predictive_probs = []
            for r in range(len(self.run_length_probs)):
                if self.n[r] == 0:
                    # Use prior
                    pred_mean = self.prior_mean
                    pred_var = self.prior_var
                else:
                    # Posterior predictive
                    post_mean = self.sum_x[r] / self.n[r]
                    post_var = max(0.01, self.sum_x2[r] / self.n[r] - post_mean ** 2)
                    pred_mean = post_mean
                    pred_var = post_var + self.prior_var / (self.n[r] + 1)
            
                pred_prob = self._gaussian_pdf(observation, pred_mean, np.sqrt(pred_var))
                predictive_probs.append(pred_prob)
        
            # Growth probabilities (no change point)
            growth_probs = [
                self.run_length_probs[r] * predictive_probs[r] * (1 - self.hazard_rate)
                for r in range(len(self.run_length_probs))
            ]
        
            # Change point probability
            cp_prob = sum(
                self.run_length_probs[r] * predictive_probs[r] * self.hazard_rate
                for r in range(len(self.run_length_probs))
            )
        
            # New run length distribution
            new_run_length_probs = [cp_prob] + growth_probs
        
            # Normalize
            total = sum(new_run_length_probs)
            if total > 0:
                new_run_length_probs = [p / total for p in new_run_length_probs]
        
            # Truncate to max run length
            if len(new_run_length_probs) > self.max_run_length:
                new_run_length_probs = new_run_length_probs[:self.max_run_length]
        
            self.run_length_probs = new_run_length_probs
        
            # Update sufficient statistics
            new_sum_x = [0.0] + [self.sum_x[r] + observation for r in range(len(self.sum_x))]
            new_sum_x2 = [0.0] + [self.sum_x2[r] + observation ** 2 for r in range(len(self.sum_x2))]
            new_n = [0] + [self.n[r] + 1 for r in range(len(self.n))]
        
            # Truncate
            self.sum_x = new_sum_x[:self.max_run_length]
            self.sum_x2 = new_sum_x2[:self.max_run_length]
            self.n = new_n[:self.max_run_length]
        
            # Detect change point
            change_detected = cp_prob > 0.5
        
            if change_detected:
                self.change_points.append((self.observation_count, cp_prob, datetime.utcnow()))
        
            return change_detected, cp_prob
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _gaussian_pdf(self, x: float, mean: float, std: float) -> float:
        """Compute Gaussian PDF."""
        return np.exp(-0.5 * ((x - mean) / std) ** 2) / (std * np.sqrt(2 * np.pi))
    
    def get_recent_change_points(self, n: int = 5) -> List[Tuple[int, float, datetime]]:
        """Get most recent change points."""
        return self.change_points[-n:]


# =============================================================================
# VOLATILITY REGIME DETECTOR
# =============================================================================

class VolatilityRegimeDetector:
    """Detects volatility regime from price data."""
    
    def __init__(self, lookback: int = 60):
        try:
            self.lookback = lookback
            self.volatility_history = deque(maxlen=lookback * 5)
        
            # Regime thresholds (annualized volatility)
            self.thresholds = {
                VolatilityRegime.ULTRA_LOW: 0.08,
                VolatilityRegime.LOW: 0.12,
                VolatilityRegime.NORMAL: 0.18,
                VolatilityRegime.ELEVATED: 0.25,
                VolatilityRegime.HIGH: 0.35,
                VolatilityRegime.EXTREME: 0.50,
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, returns: float) -> Tuple[VolatilityRegime, float]:
        """
        Update with new return and detect regime.
        
        Returns:
            Tuple of (regime, current_volatility)
        """
        try:
            self.volatility_history.append(returns)
        
            if len(self.volatility_history) < self.lookback:
                return VolatilityRegime.NORMAL, 0.15
        
            # Compute realized volatility (annualized)
            recent_returns = list(self.volatility_history)[-self.lookback:]
            realized_vol = np.std(recent_returns) * np.sqrt(252)
        
            # Determine regime
            regime = VolatilityRegime.CRISIS
            for vol_regime, threshold in sorted(self.thresholds.items(), key=lambda x: x[1]):
                if realized_vol <= threshold:
                    regime = vol_regime
                    break
        
            return regime, float(realized_vol)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def get_volatility_percentile(self) -> float:
        """Get current volatility percentile vs history."""
        try:
            if len(self.volatility_history) < self.lookback * 2:
                return 0.5
        
            recent_vol = np.std(list(self.volatility_history)[-self.lookback:])
            all_vols = [
                np.std(list(self.volatility_history)[i:i+self.lookback])
                for i in range(0, len(self.volatility_history) - self.lookback, 5)
            ]
        
            if not all_vols:
                return 0.5
        
            percentile = sum(1 for v in all_vols if v <= recent_vol) / len(all_vols)
            return percentile
        except Exception as e:
            logger.error(f"Error in get_volatility_percentile: {e}")
            raise


# =============================================================================
# CORRELATION REGIME DETECTOR
# =============================================================================

class CorrelationRegimeDetector:
    """Detects correlation regime across assets."""
    
    def __init__(self, lookback: int = 60):
        try:
            self.lookback = lookback
            self.returns_history: Dict[str, deque] = {}
        
            # Regime thresholds (average pairwise correlation)
            self.thresholds = {
                CorrelationRegime.DECORRELATED: 0.15,
                CorrelationRegime.NORMAL: 0.35,
                CorrelationRegime.ELEVATED: 0.55,
                CorrelationRegime.RISK_ON: 0.70,
                CorrelationRegime.RISK_OFF: 0.80,
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, asset_returns: Dict[str, float]) -> Tuple[CorrelationRegime, float]:
        """
        Update with new returns and detect regime.
        
        Args:
            asset_returns: Dict mapping asset names to returns
            
        Returns:
            Tuple of (regime, average_correlation)
        """
        # Update history
        try:
            for asset, ret in asset_returns.items():
                if asset not in self.returns_history:
                    self.returns_history[asset] = deque(maxlen=self.lookback * 5)
                self.returns_history[asset].append(ret)
        
            # Need at least 2 assets and sufficient history
            if len(self.returns_history) < 2:
                return CorrelationRegime.NORMAL, 0.3
        
            # Check if we have enough data
            min_len = min(len(h) for h in self.returns_history.values())
            if min_len < self.lookback:
                return CorrelationRegime.NORMAL, 0.3
        
            # Compute correlation matrix
            assets = list(self.returns_history.keys())
            n_assets = len(assets)
        
            correlations = []
            for i in range(n_assets):
                for j in range(i + 1, n_assets):
                    ret_i = list(self.returns_history[assets[i]])[-self.lookback:]
                    ret_j = list(self.returns_history[assets[j]])[-self.lookback:]
                
                    corr = np.corrcoef(ret_i, ret_j)[0, 1]
                    if not np.isnan(corr):
                        correlations.append(abs(corr))
        
            if not correlations:
                return CorrelationRegime.NORMAL, 0.3
        
            avg_corr = np.mean(correlations)
        
            # Determine regime
            regime = CorrelationRegime.CRISIS_CORRELATION
            for corr_regime, threshold in sorted(self.thresholds.items(), key=lambda x: x[1]):
                if avg_corr <= threshold:
                    regime = corr_regime
                    break
        
            return regime, float(avg_corr)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


# =============================================================================
# LIQUIDITY REGIME DETECTOR
# =============================================================================

class LiquidityRegimeDetector:
    """Detects liquidity regime from market data."""
    
    def __init__(self, lookback: int = 60):
        try:
            self.lookback = lookback
            self.spread_history = deque(maxlen=lookback * 5)
            self.volume_history = deque(maxlen=lookback * 5)
        
            # Regime thresholds
            self.spread_thresholds = {
                LiquidityRegime.ABUNDANT: 0.5,
                LiquidityRegime.NORMAL: 1.0,
                LiquidityRegime.THIN: 2.0,
                LiquidityRegime.STRESSED: 5.0,
                LiquidityRegime.CRISIS: 10.0,
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, spread_bps: float, volume: float) -> Tuple[LiquidityRegime, Dict[str, float]]:
        """
        Update with new data and detect regime.
        
        Returns:
            Tuple of (regime, metrics_dict)
        """
        try:
            self.spread_history.append(spread_bps)
            self.volume_history.append(volume)
        
            if len(self.spread_history) < self.lookback:
                return LiquidityRegime.NORMAL, {'spread': spread_bps, 'volume_ratio': 1.0}
        
            # Compute metrics
            recent_spread = np.mean(list(self.spread_history)[-self.lookback:])
            historical_spread = np.mean(list(self.spread_history))
        
            recent_volume = np.mean(list(self.volume_history)[-self.lookback:])
            historical_volume = np.mean(list(self.volume_history))
        
            volume_ratio = recent_volume / max(historical_volume, 1)
            spread_ratio = recent_spread / max(historical_spread, 0.1)
        
            # Determine regime based on spread
            regime = LiquidityRegime.FROZEN
            for liq_regime, threshold in sorted(self.spread_thresholds.items(), key=lambda x: x[1]):
                if recent_spread <= threshold:
                    regime = liq_regime
                    break
        
            # Adjust for volume
            if volume_ratio < 0.5 and regime.value in ['abundant', 'normal']:
                regime = LiquidityRegime.THIN
        
            metrics = {
                'spread': float(recent_spread),
                'volume_ratio': float(volume_ratio),
                'spread_ratio': float(spread_ratio)
            }
        
            return regime, metrics
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


# =============================================================================
# TREND REGIME DETECTOR
# =============================================================================

class TrendRegimeDetector:
    """Detects trend vs mean-reversion regime."""
    
    def __init__(self, lookback: int = 60):
        try:
            self.lookback = lookback
            self.price_history = deque(maxlen=lookback * 5)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def update(self, price: float) -> Tuple[TrendRegime, Dict[str, float]]:
        """
        Update with new price and detect regime.
        
        Uses:
        - Hurst exponent estimation
        - Variance ratio test
        - ADX-like trend strength
        """
        try:
            self.price_history.append(price)
        
            if len(self.price_history) < self.lookback * 2:
                return TrendRegime.RANGING, {'hurst': 0.5, 'trend_strength': 0.0}
        
            prices = np.array(list(self.price_history)[-self.lookback * 2:])
            returns = np.diff(np.log(prices))
        
            # Estimate Hurst exponent using R/S analysis
            hurst = self._estimate_hurst(returns)
        
            # Compute variance ratio
            var_ratio = self._variance_ratio(returns)
        
            # Compute trend strength
            trend_strength = self._trend_strength(prices)
        
            # Determine regime
            if hurst > 0.6 and trend_strength > 0.5:
                regime = TrendRegime.STRONG_TREND
            elif hurst > 0.55:
                regime = TrendRegime.WEAK_TREND
            elif hurst < 0.4:
                regime = TrendRegime.MEAN_REVERTING
            elif var_ratio < 0.8 or var_ratio > 1.2:
                regime = TrendRegime.CHOPPY
            else:
                regime = TrendRegime.RANGING
        
            metrics = {
                'hurst': float(hurst),
                'variance_ratio': float(var_ratio),
                'trend_strength': float(trend_strength)
            }
        
            return regime, metrics
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _estimate_hurst(self, returns: np.ndarray) -> float:
        """Estimate Hurst exponent using R/S analysis."""
        try:
            n = len(returns)
            if n < 20:
                return 0.5
        
            # Simplified R/S calculation
            max_k = min(n // 4, 50)
            if max_k < 4:
                return 0.5
        
            rs_values = []
            k_values = []
        
            for k in range(4, max_k):
                # Divide into k subseries
                subseries_len = n // k
                rs_list = []
            
                for i in range(k):
                    start = i * subseries_len
                    end = start + subseries_len
                    subseries = returns[start:end]
                
                    if len(subseries) < 2:
                        continue
                
                    # Compute R/S
                    mean_adj = subseries - np.mean(subseries)
                    cumsum = np.cumsum(mean_adj)
                    r = np.max(cumsum) - np.min(cumsum)
                    s = np.std(subseries)
                
                    if s > 0:
                        rs_list.append(r / s)
            
                if rs_list:
                    rs_values.append(np.mean(rs_list))
                    k_values.append(subseries_len)
        
            if len(rs_values) < 3:
                return 0.5
        
            # Linear regression in log space
            log_k = np.log(k_values)
            log_rs = np.log(rs_values)
        
            slope, _ = np.polyfit(log_k, log_rs, 1)
        
            return float(np.clip(slope, 0, 1))
        except Exception as e:
            logger.error(f"Error in _estimate_hurst: {e}")
            raise
    
    def _variance_ratio(self, returns: np.ndarray, q: int = 5) -> float:
        """Compute variance ratio test statistic."""
        try:
            n = len(returns)
            if n < q * 2:
                return 1.0
        
            var_1 = np.var(returns)
        
            # q-period returns
            q_returns = np.array([
                sum(returns[i:i+q])
                for i in range(0, n - q + 1, q)
            ])
            var_q = np.var(q_returns)
        
            if var_1 == 0:
                return 1.0
        
            return float(var_q / (q * var_1))
        except Exception as e:
            logger.error(f"Error in _variance_ratio: {e}")
            raise
    
    def _trend_strength(self, prices: np.ndarray) -> float:
        """Compute trend strength (0-1)."""
        try:
            n = len(prices)
            if n < 10:
                return 0.0
        
            # Linear regression
            x = np.arange(n)
            slope, intercept = np.polyfit(x, prices, 1)
        
            # R-squared
            predicted = slope * x + intercept
            ss_res = np.sum((prices - predicted) ** 2)
            ss_tot = np.sum((prices - np.mean(prices)) ** 2)
        
            if ss_tot == 0:
                return 0.0
        
            r_squared = 1 - ss_res / ss_tot
        
            return float(np.clip(r_squared, 0, 1))
        except Exception as e:
            logger.error(f"Error in _trend_strength: {e}")
            raise


# =============================================================================
# REGIME INTELLIGENCE UNIT
# =============================================================================

class RegimeIntelligenceUnit:
    """
    Internal unit responsible for regime detection.
    
    Detects:
    - Volatility regimes
    - Correlation regimes
    - Liquidity regimes
    - Trend vs mean-reversion dominance
    - Crisis vs normal states
    
    Uses:
    - HMM
    - Bayesian change point detection
    - Factor dynamics
    - Volatility term structure
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.committee_type = CommitteeType.REGIME_INTELLIGENCE
        
            # Initialize detectors
            self.hmm_detector = HiddenMarkovRegimeDetector(
                n_regimes=self.config.get('n_regimes', 4)
            )
            self.change_point_detector = BayesianChangePointDetector(
                hazard_rate=self.config.get('hazard_rate', 0.01)
            )
            self.volatility_detector = VolatilityRegimeDetector(
                lookback=self.config.get('vol_lookback', 60)
            )
            self.correlation_detector = CorrelationRegimeDetector(
                lookback=self.config.get('corr_lookback', 60)
            )
            self.liquidity_detector = LiquidityRegimeDetector(
                lookback=self.config.get('liq_lookback', 60)
            )
            self.trend_detector = TrendRegimeDetector(
                lookback=self.config.get('trend_lookback', 60)
            )
        
            # State tracking
            self.current_regime: Optional[RegimeState] = None
            self.regime_history: List[RegimeState] = []
            self.transition_history: List[RegimeTransition] = []
        
            logger.info("RegimeIntelligenceUnit initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, 
               returns: float,
               price: float,
               spread_bps: float = 1.0,
               volume: float = 1e6,
               asset_returns: Dict[str, float] = None) -> RegimeState:
        """
        Update all regime detectors with new data.
        
        Returns:
            Current RegimeState
        """
        # Update HMM
        try:
            volatility = abs(returns) * np.sqrt(252)
            hmm_probs = self.hmm_detector.update(volatility, returns)
        
            # Update change point detector
            change_detected, change_prob = self.change_point_detector.update(returns)
        
            # Update individual regime detectors
            vol_regime, vol_value = self.volatility_detector.update(returns)
        
            if asset_returns:
                corr_regime, corr_value = self.correlation_detector.update(asset_returns)
            else:
                corr_regime = CorrelationRegime.NORMAL
                corr_value = 0.3
        
            liq_regime, liq_metrics = self.liquidity_detector.update(spread_bps, volume)
            trend_regime, trend_metrics = self.trend_detector.update(price)
        
            # Determine overall regime
            overall_regime = self._determine_overall_regime(
                hmm_probs, vol_regime, corr_regime, liq_regime, trend_regime
            )
        
            # Compute confidence
            confidence = self._compute_confidence(
                hmm_probs, vol_regime, corr_regime, liq_regime
            )
        
            # Compute transition probability
            if self.current_regime:
                transition_prob = self.hmm_detector.get_transition_probability(
                    self.current_regime.overall, overall_regime
                )
            else:
                transition_prob = 0.0
        
            # Create new regime state
            new_regime = RegimeState(
                volatility=vol_regime,
                correlation=corr_regime,
                liquidity=liq_regime,
                trend=trend_regime,
                overall=overall_regime,
                confidence=confidence,
                transition_probability=transition_prob
            )
        
            # Track transitions
            if self.current_regime and self.current_regime.overall != overall_regime:
                transition = RegimeTransition(
                    from_regime=self.current_regime.overall,
                    to_regime=overall_regime,
                    transition_time=datetime.utcnow(),
                    confidence=confidence,
                    trigger=self._identify_trigger(vol_regime, corr_regime, liq_regime)
                )
                self.transition_history.append(transition)
                logger.info(f"Regime transition: {transition.from_regime.value} -> {transition.to_regime.value}")
        
            # Update state
            self.current_regime = new_regime
            self.regime_history.append(new_regime)
        
            return new_regime
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _determine_overall_regime(self,
                                   hmm_probs: RegimeProbabilities,
                                   vol_regime: VolatilityRegime,
                                   corr_regime: CorrelationRegime,
                                   liq_regime: LiquidityRegime,
                                   trend_regime: TrendRegime) -> MarketRegime:
        """Determine overall market regime from components."""
        # Crisis detection takes priority
        try:
            if vol_regime in [VolatilityRegime.EXTREME, VolatilityRegime.CRISIS]:
                return MarketRegime.CRISIS
            if liq_regime in [LiquidityRegime.CRISIS, LiquidityRegime.FROZEN]:
                return MarketRegime.CRISIS
            if corr_regime == CorrelationRegime.CRISIS_CORRELATION:
                return MarketRegime.CRISIS
        
            # Volatile regime
            if vol_regime in [VolatilityRegime.HIGH, VolatilityRegime.ELEVATED]:
                return MarketRegime.VOLATILE
        
            # Trending regime
            if trend_regime in [TrendRegime.STRONG_TREND, TrendRegime.WEAK_TREND]:
                return MarketRegime.TRENDING
        
            # Calm regime
            if vol_regime in [VolatilityRegime.ULTRA_LOW, VolatilityRegime.LOW]:
                if liq_regime in [LiquidityRegime.ABUNDANT, LiquidityRegime.NORMAL]:
                    return MarketRegime.CALM
        
            # Use HMM as tiebreaker
            return hmm_probs.most_likely
        except Exception as e:
            logger.error(f"Error in _determine_overall_regime: {e}")
            raise
    
    def _compute_confidence(self,
                            hmm_probs: RegimeProbabilities,
                            vol_regime: VolatilityRegime,
                            corr_regime: CorrelationRegime,
                            liq_regime: LiquidityRegime) -> float:
        """Compute confidence in regime detection."""
        # Base confidence from HMM
        try:
            base_confidence = hmm_probs.get_confidence()
        
            # Adjust for entropy (lower entropy = higher confidence)
            entropy_factor = max(0.5, 1 - hmm_probs.entropy / 2)
        
            # Adjust for regime clarity
            clarity_bonus = 0.0
            if vol_regime in [VolatilityRegime.ULTRA_LOW, VolatilityRegime.CRISIS]:
                clarity_bonus += 0.1  # Extreme regimes are clearer
            if liq_regime in [LiquidityRegime.ABUNDANT, LiquidityRegime.FROZEN]:
                clarity_bonus += 0.1
        
            confidence = base_confidence * entropy_factor + clarity_bonus
            return float(np.clip(confidence, 0, 1))
        except Exception as e:
            logger.error(f"Error in _compute_confidence: {e}")
            raise
    
    def _identify_trigger(self,
                          vol_regime: VolatilityRegime,
                          corr_regime: CorrelationRegime,
                          liq_regime: LiquidityRegime) -> str:
        """Identify what triggered a regime change."""
        try:
            triggers = []
        
            if vol_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME, VolatilityRegime.CRISIS]:
                triggers.append("volatility_spike")
        
            if corr_regime in [CorrelationRegime.RISK_OFF, CorrelationRegime.CRISIS_CORRELATION]:
                triggers.append("correlation_breakdown")
        
            if liq_regime in [LiquidityRegime.STRESSED, LiquidityRegime.CRISIS, LiquidityRegime.FROZEN]:
                triggers.append("liquidity_stress")
        
            return ", ".join(triggers) if triggers else "gradual_shift"
        except Exception as e:
            logger.error(f"Error in _identify_trigger: {e}")
            raise
    
    def vote(self, proposed_action: str) -> CommitteeVote:
        """
        Cast a vote on a proposed action based on current regime.
        
        Args:
            proposed_action: Description of proposed action
            
        Returns:
            CommitteeVote
        """
        try:
            if self.current_regime is None:
                return CommitteeVote(
                    committee=self.committee_type,
                    decision=CommitteeDecision.DEFER,
                    confidence=0.0,
                    rationale="No regime data available"
                )
        
            # Determine decision based on regime
            if self.current_regime.overall == MarketRegime.CRISIS:
                decision = CommitteeDecision.REJECT
                rationale = "Crisis regime detected - no new positions"
            elif self.current_regime.overall == MarketRegime.VOLATILE:
                decision = CommitteeDecision.CONDITIONAL
                rationale = "Volatile regime - reduced position sizes recommended"
            elif self.current_regime.confidence < 0.5:
                decision = CommitteeDecision.DEFER
                rationale = f"Low regime confidence ({self.current_regime.confidence:.2f})"
            else:
                decision = CommitteeDecision.APPROVE
                rationale = f"Regime: {self.current_regime.overall.value} (confidence: {self.current_regime.confidence:.2f})"
        
            conditions = []
            if self.current_regime.transition_probability > 0.3:
                conditions.append("Monitor for regime transition")
            if self.current_regime.volatility in [VolatilityRegime.ELEVATED, VolatilityRegime.HIGH]:
                conditions.append("Reduce position sizes by 50%")
        
            return CommitteeVote(
                committee=self.committee_type,
                decision=decision,
                confidence=self.current_regime.confidence,
                rationale=rationale,
                conditions=conditions
            )
        except Exception as e:
            logger.error(f"Error in vote: {e}")
            raise
    
    def get_regime_summary(self) -> Dict[str, Any]:
        """Get summary of current regime state."""
        try:
            if self.current_regime is None:
                return {'status': 'no_data'}
        
            return {
                'overall': self.current_regime.overall.value,
                'volatility': self.current_regime.volatility.value,
                'correlation': self.current_regime.correlation.value,
                'liquidity': self.current_regime.liquidity.value,
                'trend': self.current_regime.trend.value,
                'confidence': self.current_regime.confidence,
                'transition_probability': self.current_regime.transition_probability,
                'recent_transitions': len([
                    t for t in self.transition_history
                    if (datetime.utcnow() - t.transition_time).days < 30
                ])
            }
        except Exception as e:
            logger.error(f"Error in get_regime_summary: {e}")
            raise


# =============================================================================
# REGIME DETECTION LAYER
# =============================================================================

class RegimeDetectionLayer:
    """
    Layer 2: Regime Detection Layer
    
    Responsible for:
    - Multi-dimensional regime detection
    - Regime transition monitoring
    - Regime-conditioned decision support
    - Historical regime analysis
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.intelligence_unit = RegimeIntelligenceUnit(self.config)
            self.regime_unit = self.intelligence_unit  # Alias for backward compatibility
        
            # Layer state
            self.is_initialized = False
            self.last_update: Optional[datetime] = None
            self.update_count = 0
        
            logger.info("RegimeDetectionLayer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self,
               returns: float,
               price: float,
               spread_bps: float = 1.0,
               volume: float = 1e6,
               asset_returns: Dict[str, float] = None) -> RegimeState:
        """
        Update regime detection with new market data.
        
        Returns:
            Current RegimeState
        """
        try:
            regime = self.intelligence_unit.update(
                returns=returns,
                price=price,
                spread_bps=spread_bps,
                volume=volume,
                asset_returns=asset_returns
            )
        
            self.is_initialized = True
            self.last_update = datetime.utcnow()
            self.update_count += 1
        
            return regime
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def get_current_regime(self) -> Optional[RegimeState]:
        """Get current regime state."""
        return self.intelligence_unit.current_regime
    
    def get_regime_vote(self, proposed_action: str) -> CommitteeVote:
        """Get regime-based vote on proposed action."""
        return self.intelligence_unit.vote(proposed_action)
    
    def is_crisis_regime(self) -> bool:
        """Check if currently in crisis regime."""
        try:
            if self.intelligence_unit.current_regime is None:
                return False
            return self.intelligence_unit.current_regime.overall == MarketRegime.CRISIS
        except Exception as e:
            logger.error(f"Error in is_crisis_regime: {e}")
            raise
    
    def should_reduce_exposure(self) -> Tuple[bool, float]:
        """
        Check if exposure should be reduced based on regime.
        
        Returns:
            Tuple of (should_reduce, reduction_factor)
        """
        try:
            if self.intelligence_unit.current_regime is None:
                return False, 1.0
        
            regime = self.intelligence_unit.current_regime
        
            if regime.overall == MarketRegime.CRISIS:
                return True, 0.1  # Reduce to 10%
            elif regime.overall == MarketRegime.VOLATILE:
                return True, 0.5  # Reduce to 50%
            elif regime.volatility in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                return True, 0.5
            elif regime.liquidity in [LiquidityRegime.STRESSED, LiquidityRegime.CRISIS]:
                return True, 0.3
        
            return False, 1.0
        except Exception as e:
            logger.error(f"Error in should_reduce_exposure: {e}")
            raise
    
    def get_layer_state(self) -> Dict[str, Any]:
        """Get current layer state."""
        return {
            'is_initialized': self.is_initialized,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_count': self.update_count,
            'regime_summary': self.intelligence_unit.get_regime_summary(),
            'recent_transitions': [
                {
                    'from': t.from_regime.value,
                    'to': t.to_regime.value,
                    'time': t.transition_time.isoformat(),
                    'trigger': t.trigger
                }
                for t in self.intelligence_unit.transition_history[-5:]
            ]
        }
