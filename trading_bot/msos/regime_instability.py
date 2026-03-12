"""
AlphaAlgo MSOS - Regime Instability Early Warning System

You do not predict regimes.
You detect regime instability.

Track:
- Volatility-of-volatility
- Correlation dispersion
- Factor dominance shifts
- Entropy spikes

When instability increases:
- Exposure is reduced preemptively
- Capital protection overrides strategy signals

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class RegimeUncertainty(Enum):
    """Regime uncertainty levels"""
    LOW = auto()           # Stable regime, high confidence
    MODERATE = auto()      # Some uncertainty, monitor
    HIGH = auto()          # Significant uncertainty, reduce exposure
    EXTREME = auto()       # Regime transition likely, minimal exposure
    UNKNOWN = auto()       # Cannot determine


class InstabilityType(Enum):
    """Types of regime instability"""
    NONE = auto()
    VOLATILITY_SPIKE = auto()
    CORRELATION_BREAKDOWN = auto()
    FACTOR_SHIFT = auto()
    ENTROPY_EXPLOSION = auto()
    LIQUIDITY_STRESS = auto()
    STRUCTURAL_BREAK = auto()
    MULTIPLE = auto()


@dataclass
class VolatilityOfVolatility:
    """Volatility of volatility metrics"""
    current_vov: float = 0.0
    baseline_vov: float = 0.0
    vov_percentile: float = 0.0
    is_elevated: bool = False
    acceleration: float = 0.0  # Rate of change
    
    def calculate_score(self) -> float:
        """Calculate VoV score (0-1, lower is better)"""
        try:
            if self.baseline_vov <= 0:
                return 0.5
        
            ratio = self.current_vov / self.baseline_vov
            score = min(1.0, ratio / 3)  # 3x baseline = max score
            return score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise


@dataclass
class CorrelationDispersion:
    """Correlation dispersion metrics"""
    current_dispersion: float = 0.0
    baseline_dispersion: float = 0.0
    correlation_breakdown_count: int = 0
    max_correlation_change: float = 0.0
    is_unstable: bool = False
    
    def calculate_score(self) -> float:
        """Calculate dispersion score (0-1, lower is better)"""
        try:
            if self.baseline_dispersion <= 0:
                return 0.5
        
            ratio = self.current_dispersion / self.baseline_dispersion
            score = min(1.0, ratio / 2)  # 2x baseline = max score
            return score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise


@dataclass
class FactorDominance:
    """Factor dominance shift metrics"""
    dominant_factor: str = ""
    factor_concentration: float = 0.0  # How much one factor dominates
    factor_stability: float = 0.0  # How stable factor rankings are
    recent_shifts: int = 0
    is_shifting: bool = False
    
    def calculate_score(self) -> float:
        """Calculate factor shift score (0-1, lower is better)"""
        # High concentration + low stability = bad
        try:
            instability = (1 - self.factor_stability) * self.factor_concentration
            return min(1.0, instability)
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise


@dataclass
class EntropyMetrics:
    """Market entropy metrics"""
    current_entropy: float = 0.0
    baseline_entropy: float = 0.0
    entropy_velocity: float = 0.0  # Rate of change
    is_spiking: bool = False
    
    def calculate_score(self) -> float:
        """Calculate entropy score (0-1, lower is better)"""
        try:
            if self.baseline_entropy <= 0:
                return 0.5
        
            ratio = self.current_entropy / self.baseline_entropy
            velocity_penalty = min(0.5, abs(self.entropy_velocity) * 10)
            score = min(1.0, ratio / 2 + velocity_penalty)
            return score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise


@dataclass
class InstabilityResult:
    """Result from regime instability detection"""
    uncertainty: RegimeUncertainty
    instability_type: InstabilityType
    instability_score: float  # 0-1, higher = more unstable
    exposure_multiplier: float  # 0-1, how much to reduce exposure
    vov: VolatilityOfVolatility
    correlation: CorrelationDispersion
    factor: FactorDominance
    entropy: EntropyMetrics
    early_warnings: List[str]
    reason: str
    recommended_action: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'uncertainty': self.uncertainty.name,
            'instability_type': self.instability_type.name,
            'instability_score': self.instability_score,
            'exposure_multiplier': self.exposure_multiplier,
            'vov_score': self.vov.calculate_score(),
            'correlation_score': self.correlation.calculate_score(),
            'factor_score': self.factor.calculate_score(),
            'entropy_score': self.entropy.calculate_score(),
            'early_warnings': self.early_warnings,
            'reason': self.reason,
            'recommended_action': self.recommended_action,
            'timestamp': self.timestamp
        }


class VolatilityTracker:
    """Tracks volatility and volatility-of-volatility"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._returns: Deque[float] = deque(maxlen=window_size)
            self._volatility: Deque[float] = deque(maxlen=window_size)
            self._vov: Deque[float] = deque(maxlen=window_size)
        
            self.baseline_volatility: Optional[float] = None
            self.baseline_vov: Optional[float] = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, return_value: float) -> VolatilityOfVolatility:
        """Update with new return and calculate VoV"""
        try:
            self._returns.append(return_value)
        
            result = VolatilityOfVolatility()
        
            if len(self._returns) >= 20:
                # Calculate rolling volatility
                recent_returns = list(self._returns)[-20:]
                current_vol = np.std(recent_returns) * np.sqrt(252)  # Annualized
                self._volatility.append(current_vol)
            
                if len(self._volatility) >= 20:
                    # Calculate volatility of volatility
                    recent_vols = list(self._volatility)[-20:]
                    current_vov = np.std(recent_vols)
                    self._vov.append(current_vov)
                
                    result.current_vov = current_vov
                
                    # Establish baseline
                    if self.baseline_vov is None and len(self._vov) >= 50:
                        self.baseline_vov = np.mean(list(self._vov)[:50])
                        self.baseline_volatility = np.mean(list(self._volatility)[:50])
                
                    if self.baseline_vov:
                        result.baseline_vov = self.baseline_vov
                        result.is_elevated = current_vov > self.baseline_vov * 1.5
                    
                        # Calculate percentile
                        sorted_vov = sorted(self._vov)
                        idx = np.searchsorted(sorted_vov, current_vov)
                        result.vov_percentile = idx / len(sorted_vov)
                    
                        # Calculate acceleration
                        if len(self._vov) >= 5:
                            recent = list(self._vov)[-5:]
                            result.acceleration = (recent[-1] - recent[0]) / 5
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class CorrelationTracker:
    """Tracks correlation structure and dispersion"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._asset_returns: Dict[str, Deque[float]] = {}
            self._correlation_matrices: Deque[np.ndarray] = deque(maxlen=window_size)
        
            self.baseline_dispersion: Optional[float] = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, returns: Dict[str, float]) -> CorrelationDispersion:
        """Update with new returns for multiple assets"""
        try:
            result = CorrelationDispersion()
        
            # Store returns
            for asset, ret in returns.items():
                if asset not in self._asset_returns:
                    self._asset_returns[asset] = deque(maxlen=self.window_size)
                self._asset_returns[asset].append(ret)
        
            # Calculate correlation matrix if enough data
            assets = list(self._asset_returns.keys())
            if len(assets) >= 2:
                min_len = min(len(self._asset_returns[a]) for a in assets)
            
                if min_len >= 20:
                    # Build return matrix
                    return_matrix = np.array([
                        list(self._asset_returns[a])[-20:]
                        for a in assets
                    ])
                
                    # Calculate correlation matrix
                    corr_matrix = np.corrcoef(return_matrix)
                    self._correlation_matrices.append(corr_matrix)
                
                    # Calculate dispersion (std of off-diagonal correlations)
                    off_diag = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
                    result.current_dispersion = np.std(off_diag)
                
                    # Establish baseline
                    if self.baseline_dispersion is None and len(self._correlation_matrices) >= 30:
                        dispersions = []
                        for cm in list(self._correlation_matrices)[:30]:
                            od = cm[np.triu_indices_from(cm, k=1)]
                            dispersions.append(np.std(od))
                        self.baseline_dispersion = np.mean(dispersions)
                
                    if self.baseline_dispersion:
                        result.baseline_dispersion = self.baseline_dispersion
                        result.is_unstable = result.current_dispersion > self.baseline_dispersion * 1.5
                    
                        # Count correlation breakdowns
                        if len(self._correlation_matrices) >= 2:
                            prev_matrix = self._correlation_matrices[-2]
                            changes = np.abs(corr_matrix - prev_matrix)
                            result.correlation_breakdown_count = np.sum(changes > 0.3)
                            result.max_correlation_change = np.max(changes)
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class FactorTracker:
    """Tracks factor dominance and shifts"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._factor_exposures: Dict[str, Deque[float]] = {}
            self._dominant_factor_history: Deque[str] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, factor_exposures: Dict[str, float]) -> FactorDominance:
        """Update with new factor exposures"""
        try:
            result = FactorDominance()
        
            if not factor_exposures:
                return result
        
            # Store exposures
            for factor, exposure in factor_exposures.items():
                if factor not in self._factor_exposures:
                    self._factor_exposures[factor] = deque(maxlen=self.window_size)
                self._factor_exposures[factor].append(abs(exposure))
        
            # Find dominant factor
            total_exposure = sum(abs(e) for e in factor_exposures.values())
            if total_exposure > 0:
                dominant = max(factor_exposures.keys(), key=lambda f: abs(factor_exposures[f]))
                result.dominant_factor = dominant
                result.factor_concentration = abs(factor_exposures[dominant]) / total_exposure
            
                self._dominant_factor_history.append(dominant)
            
                # Calculate stability (how often dominant factor changes)
                if len(self._dominant_factor_history) >= 10:
                    recent = list(self._dominant_factor_history)[-10:]
                    changes = sum(1 for i in range(1, len(recent)) if recent[i] != recent[i-1])
                    result.factor_stability = 1 - (changes / len(recent))
                    result.recent_shifts = changes
                    result.is_shifting = changes >= 3
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class EntropyTracker:
    """Tracks market entropy"""
    
    def __init__(self, window_size: int = 100, bins: int = 10):
        try:
            self.window_size = window_size
            self.bins = bins
            self._returns: Deque[float] = deque(maxlen=window_size)
            self._entropy: Deque[float] = deque(maxlen=window_size)
        
            self.baseline_entropy: Optional[float] = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, return_value: float) -> EntropyMetrics:
        """Update with new return and calculate entropy"""
        try:
            self._returns.append(return_value)
        
            result = EntropyMetrics()
        
            if len(self._returns) >= 20:
                # Calculate entropy of return distribution
                returns = np.array(list(self._returns)[-20:])
            
                # Discretize returns
                hist, _ = np.histogram(returns, bins=self.bins, density=True)
                hist = hist[hist > 0]  # Remove zeros
            
                if len(hist) > 0:
                    # Shannon entropy
                    probs = hist / hist.sum()
                    entropy = -np.sum(probs * np.log2(probs + 1e-10))
                    self._entropy.append(entropy)
                
                    result.current_entropy = entropy
                
                    # Establish baseline
                    if self.baseline_entropy is None and len(self._entropy) >= 30:
                        self.baseline_entropy = np.mean(list(self._entropy)[:30])
                
                    if self.baseline_entropy:
                        result.baseline_entropy = self.baseline_entropy
                        result.is_spiking = entropy > self.baseline_entropy * 1.5
                    
                        # Calculate velocity
                        if len(self._entropy) >= 5:
                            recent = list(self._entropy)[-5:]
                            result.entropy_velocity = (recent[-1] - recent[0]) / 5
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class RegimeInstabilityDetector:
    """
    Main Regime Instability Detector
    
    RULES:
    1. Do NOT predict regimes - detect instability
    2. When instability increases → reduce exposure preemptively
    3. Capital protection overrides strategy signals
    4. Act BEFORE regime transition, not after
    """
    
    # Thresholds
    VOV_THRESHOLD = 0.6
    CORRELATION_THRESHOLD = 0.6
    FACTOR_THRESHOLD = 0.5
    ENTROPY_THRESHOLD = 0.6
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.regime")
        
            # Trackers
            self._volatility_tracker = VolatilityTracker()
            self._correlation_tracker = CorrelationTracker()
            self._factor_tracker = FactorTracker()
            self._entropy_tracker = EntropyTracker()
        
            # State
            self._last_result: Optional[InstabilityResult] = None
            self._warning_count: int = 0
        
            self.logger.info("Regime Instability Detector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        market_data: Dict[str, Any]
    ) -> InstabilityResult:
        """
        Update with new market data and detect instability.
        
        Args:
            market_data: Dictionary containing:
                - return: Single asset return
                - returns: Dict of asset returns for correlation
                - factor_exposures: Dict of factor exposures
        """
        # Update all trackers
        try:
            return_value = market_data.get('return', 0.0)
            returns = market_data.get('returns', {})
            factor_exposures = market_data.get('factor_exposures', {})
        
            vov = self._volatility_tracker.update(return_value)
            correlation = self._correlation_tracker.update(returns)
            factor = self._factor_tracker.update(factor_exposures)
            entropy = self._entropy_tracker.update(return_value)
        
            # Calculate scores
            vov_score = vov.calculate_score()
            corr_score = correlation.calculate_score()
            factor_score = factor.calculate_score()
            entropy_score = entropy.calculate_score()
        
            # Overall instability score
            instability_score = (
                vov_score * 0.3 +
                corr_score * 0.25 +
                factor_score * 0.2 +
                entropy_score * 0.25
            )
        
            # Detect early warnings
            early_warnings = []
            instability_types = []
        
            if vov_score > self.VOV_THRESHOLD:
                early_warnings.append(f"Volatility-of-volatility elevated: {vov_score:.2f}")
                instability_types.append(InstabilityType.VOLATILITY_SPIKE)
        
            if corr_score > self.CORRELATION_THRESHOLD:
                early_warnings.append(f"Correlation structure unstable: {corr_score:.2f}")
                instability_types.append(InstabilityType.CORRELATION_BREAKDOWN)
        
            if factor_score > self.FACTOR_THRESHOLD:
                early_warnings.append(f"Factor dominance shifting: {factor_score:.2f}")
                instability_types.append(InstabilityType.FACTOR_SHIFT)
        
            if entropy_score > self.ENTROPY_THRESHOLD:
                early_warnings.append(f"Market entropy spiking: {entropy_score:.2f}")
                instability_types.append(InstabilityType.ENTROPY_EXPLOSION)
        
            # Determine instability type
            if len(instability_types) > 1:
                instability_type = InstabilityType.MULTIPLE
            elif len(instability_types) == 1:
                instability_type = instability_types[0]
            else:
                instability_type = InstabilityType.NONE
        
            # Determine uncertainty level
            if instability_score >= 0.8:
                uncertainty = RegimeUncertainty.EXTREME
                exposure_multiplier = 0.1
            elif instability_score >= 0.6:
                uncertainty = RegimeUncertainty.HIGH
                exposure_multiplier = 0.3
            elif instability_score >= 0.4:
                uncertainty = RegimeUncertainty.MODERATE
                exposure_multiplier = 0.6
            else:
                uncertainty = RegimeUncertainty.LOW
                exposure_multiplier = 1.0
        
            # Get recommendation
            reason, action = self._get_recommendation(uncertainty, instability_type, early_warnings)
        
            # Track warnings
            if early_warnings:
                self._warning_count += 1
            else:
                self._warning_count = max(0, self._warning_count - 1)
        
            result = InstabilityResult(
                uncertainty=uncertainty,
                instability_type=instability_type,
                instability_score=instability_score,
                exposure_multiplier=exposure_multiplier,
                vov=vov,
                correlation=correlation,
                factor=factor,
                entropy=entropy,
                early_warnings=early_warnings,
                reason=reason,
                recommended_action=action
            )
        
            self._last_result = result
        
            if early_warnings:
                self.logger.warning(
                    f"Regime instability detected: {uncertainty.name} | "
                    f"Score: {instability_score:.2f} | "
                    f"Exposure: {exposure_multiplier:.1%}"
                )
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _get_recommendation(
        self,
        uncertainty: RegimeUncertainty,
        instability_type: InstabilityType,
        warnings: List[str]
    ) -> Tuple[str, str]:
        """Get reason and recommended action"""
        try:
            if uncertainty == RegimeUncertainty.EXTREME:
                return (
                    f"EXTREME regime uncertainty: {', '.join(warnings)}",
                    "REDUCE EXPOSURE TO 10%. Capital protection mode."
                )
            elif uncertainty == RegimeUncertainty.HIGH:
                return (
                    f"HIGH regime uncertainty: {', '.join(warnings)}",
                    "Reduce exposure to 30%. Tighten stops."
                )
            elif uncertainty == RegimeUncertainty.MODERATE:
                return (
                    f"Moderate regime uncertainty: {', '.join(warnings)}",
                    "Reduce exposure to 60%. Monitor closely."
                )
            else:
                return (
                    "Regime stable",
                    "Normal operations"
                )
        except Exception as e:
            logger.error(f"Error in _get_recommendation: {e}")
            raise
    
    def get_current_uncertainty(self) -> RegimeUncertainty:
        """Get current regime uncertainty level"""
        try:
            if self._last_result:
                return self._last_result.uncertainty
            return RegimeUncertainty.UNKNOWN
        except Exception as e:
            logger.error(f"Error in get_current_uncertainty: {e}")
            raise
    
    def get_exposure_multiplier(self) -> float:
        """Get current exposure multiplier based on regime"""
        try:
            if self._last_result:
                return self._last_result.exposure_multiplier
            return 0.5  # Conservative default
        except Exception as e:
            logger.error(f"Error in get_exposure_multiplier: {e}")
            raise
    
    def is_regime_stable(self) -> bool:
        """Check if regime is stable enough for normal trading"""
        try:
            if self._last_result:
                return self._last_result.uncertainty in [
                    RegimeUncertainty.LOW,
                    RegimeUncertainty.MODERATE
                ]
            return False
        except Exception as e:
            logger.error(f"Error in is_regime_stable: {e}")
            raise
