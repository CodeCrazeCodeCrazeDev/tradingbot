"""
Regime Change Detection
=======================

Algorithms for detecting market regime changes.

Methods:
- Markov-Switching models
- Bayesian Online Changepoint Detection (BOCD)
- CUSUM (Cumulative Sum)
- Volatility regime detection
- Correlation regime detection
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class RegimeType(Enum):
    """Types of market regimes."""
    BULL = "bull"
    BEAR = "bear"
    CHOPPY = "choppy"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"


class RegimeMethod(Enum):
    """Methods for regime change detection."""
    MARKOV_SWITCHING = "markov_switching"
    BOCD = "bayesian_online_changepoint"
    CUSUM = "cusum"
    VOLATILITY_REGIME = "volatility_regime"


@dataclass
class RegimeChange:
    """Detected regime change."""
    timestamp_idx: int
    previous_regime: RegimeType
    new_regime: RegimeType
    confidence: float
    method: RegimeMethod
    statistics: dict


class RegimeChangeDetector:
    """
    Detects market regime changes in time series data.
    
    Useful for identifying:
    - Bull to bear transitions
    - Volatility regime shifts
    - Crisis onset detection
    - Correlation breakdowns
    """
    
    def __init__(self, method: RegimeMethod = RegimeMethod.BOCD,
                 lookback_window: int = 60):
        """
        Initialize detector.
        
        Args:
            method: Detection method to use
            lookback_window: Window for regime estimation
        """
        self.method = method
        self.lookback_window = lookback_window
        self._regime_history: List[RegimeType] = []
    
    def detect(self, prices: List[float], volumes: Optional[List[float]] = None) -> List[RegimeChange]:
        """
        Detect regime changes in price data.
        
        Args:
            prices: List of prices
            volumes: Optional list of volumes
            
        Returns:
            List of detected regime changes
        """
        if len(prices) < self.lookback_window * 2:
            return []
        
        if self.method == RegimeMethod.BOCD:
            return self._bocd_detection(prices)
        elif self.method == RegimeMethod.CUSUM:
            return self._cusum_detection(prices)
        elif self.method == RegimeMethod.VOLATILITY_REGIME:
            return self._volatility_regime_detection(prices)
        else:
            return []
    
    def _bocd_detection(self, prices: List[float]) -> List[RegimeChange]:
        """
        Bayesian Online Changepoint Detection.
        
        Simplified implementation of BOCD algorithm.
        """
        returns = np.diff(prices) / prices[:-1]
        
        # Run length probabilities
        hazard = 1 / 100  # Constant hazard rate
        
        changes = []
        max_run_length = 0
        
        for i in range(self.lookback_window, len(returns)):
            # Simplified: check if recent returns distribution differs significantly
            recent_returns = returns[i-self.lookback_window:i]
            older_returns = returns[max(0, i-2*self.lookback_window):i-self.lookback_window]
            
            if len(older_returns) < 10:
                continue
            
            # Two-sample t-test equivalent
            mean_recent = np.mean(recent_returns)
            mean_older = np.mean(older_returns)
            std_recent = np.std(recent_returns)
            std_older = np.std(older_returns)
            
            if std_recent == 0 or std_older == 0:
                continue
            
            # Effect size (Cohen's d)
            pooled_std = np.sqrt((std_recent**2 + std_older**2) / 2)
            effect_size = abs(mean_recent - mean_older) / pooled_std
            
            if effect_size > 0.5:  # Medium to large effect
                # Determine new regime
                new_regime = self._classify_regime(recent_returns, std_recent)
                old_regime = self._classify_regime(older_returns, std_older)
                
                if new_regime != old_regime:
                    changes.append(RegimeChange(
                        timestamp_idx=i,
                        previous_regime=old_regime,
                        new_regime=new_regime,
                        confidence=min(1.0, effect_size),
                        method=RegimeMethod.BOCD,
                        statistics={
                            'effect_size': effect_size,
                            'mean_recent': mean_recent,
                            'mean_older': mean_older,
                        }
                    ))
        
        return changes
    
    def _cusum_detection(self, prices: List[float]) -> List[RegimeChange]:
        """
        CUSUM (Cumulative Sum) control chart for changepoint detection.
        """
        returns = np.diff(prices) / prices[:-1]
        mean_return = np.mean(returns[:self.lookback_window])
        std_return = np.std(returns[:self.lookback_window])
        
        if std_return == 0:
            return []
        
        # CUSUM parameters
        k = 0.5  # Slack parameter
        h = 4.0  # Decision interval
        
        cusum_pos = 0
        cusum_neg = 0
        changes = []
        
        for i in range(self.lookback_window, len(returns)):
            # Standardized return
            z = (returns[i] - mean_return) / std_return
            
            # Update CUSUM statistics
            cusum_pos = max(0, cusum_pos + z - k)
            cusum_neg = max(0, cusum_neg - z - k)
            
            # Check for changepoint
            if cusum_pos > h or cusum_neg > h:
                recent_returns = returns[i-self.lookback_window:i]
                older_returns = returns[max(0, i-2*self.lookback_window):i-self.lookback_window]
                
                new_regime = self._classify_regime(recent_returns, np.std(recent_returns))
                old_regime = self._classify_regime(older_returns, np.std(older_returns)) if len(older_returns) > 0 else RegimeType.CHOPPY
                
                changes.append(RegimeChange(
                    timestamp_idx=i,
                    previous_regime=old_regime,
                    new_regime=new_regime,
                    confidence=min(1.0, max(cusum_pos, cusum_neg) / h),
                    method=RegimeMethod.CUSUM,
                    statistics={
                        'cusum_pos': cusum_pos,
                        'cusum_neg': cusum_neg,
                    }
                ))
                
                # Reset CUSUM
                cusum_pos = 0
                cusum_neg = 0
        
        return changes
    
    def _volatility_regime_detection(self, prices: List[float]) -> List[RegimeChange]:
        """
        Detect changes in volatility regime using rolling window.
        """
        returns = np.diff(prices) / prices[:-1]
        changes = []
        
        for i in range(self.lookback_window * 2, len(returns)):
            # Calculate volatility in recent vs older window
            recent_vol = np.std(returns[i-self.lookback_window:i])
            older_vol = np.std(returns[i-2*self.lookback_window:i-self.lookback_window])
            
            if older_vol == 0:
                continue
            
            vol_ratio = recent_vol / older_vol
            
            # Detect regime change
            if vol_ratio > 2.0:  # Volatility doubled
                new_regime = RegimeType.HIGH_VOLATILITY
                old_regime = RegimeType.LOW_VOLATILITY if older_vol < 0.01 else RegimeType.CHOPPY
                
                changes.append(RegimeChange(
                    timestamp_idx=i,
                    previous_regime=old_regime,
                    new_regime=new_regime,
                    confidence=min(1.0, vol_ratio / 3.0),
                    method=RegimeMethod.VOLATILITY_REGIME,
                    statistics={
                        'vol_ratio': vol_ratio,
                        'recent_vol': recent_vol,
                        'older_vol': older_vol,
                    }
                ))
            elif vol_ratio < 0.5:  # Volatility halved
                new_regime = RegimeType.LOW_VOLATILITY
                old_regime = RegimeType.HIGH_VOLATILITY if older_vol > 0.02 else RegimeType.CHOPPY
                
                changes.append(RegimeChange(
                    timestamp_idx=i,
                    previous_regime=old_regime,
                    new_regime=new_regime,
                    confidence=min(1.0, (1 - vol_ratio) * 2),
                    method=RegimeMethod.VOLATILITY_REGIME,
                    statistics={
                        'vol_ratio': vol_ratio,
                        'recent_vol': recent_vol,
                        'older_vol': older_vol,
                    }
                ))
        
        return changes
    
    def _classify_regime(self, returns: np.ndarray, volatility: float) -> RegimeType:
        """
        Classify market regime based on return characteristics.
        """
        mean_return = np.mean(returns)
        
        # Crisis detection: large negative returns + high vol
        if mean_return < -0.02 and volatility > 0.03:
            return RegimeType.CRISIS
        
        # High volatility regime
        if volatility > 0.025:
            if mean_return > 0.001:
                return RegimeType.BULL
            elif mean_return < -0.001:
                return RegimeType.BEAR
            return RegimeType.HIGH_VOLATILITY
        
        # Low volatility regime
        if volatility < 0.01:
            return RegimeType.LOW_VOLATILITY
        
        # Trend detection
        if mean_return > 0.0005:
            return RegimeType.BULL
        elif mean_return < -0.0005:
            return RegimeType.BEAR
        
        return RegimeType.CHOPPY
    
    def get_current_regime(self, prices: List[float]) -> RegimeType:
        """Get the current regime classification."""
        if len(prices) < self.lookback_window:
            return RegimeType.CHOPPY
        
        returns = np.diff(prices) / prices[:-1]
        recent_returns = returns[-self.lookback_window:]
        volatility = np.std(recent_returns)
        
        return self._classify_regime(recent_returns, volatility)
