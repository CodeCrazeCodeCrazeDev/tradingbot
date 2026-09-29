"""
Cross-Asset Divergence Detection
=================================

Algorithms for detecting when correlated assets start diverging,
often a leading indicator of market stress or opportunity.

Methods:
- Cointegration tests
- Correlation breakdown detection
- Spread monitoring
- Lead-lag relationship changes
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


class DivergenceType(Enum):
    """Types of cross-asset divergence."""
    COINTEGRATION_BREAK = "cointegration_break"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    SPREAD_EXPLOSION = "spread_explosion"
    LEAD_LAG_CHANGE = "lead_lag_change"


@dataclass
class DivergenceResult:
    """Detected divergence between assets."""
    asset_pair: Tuple[str, str]
    divergence_type: DivergenceType
    start_idx: int
    confidence: float
    spread_value: float
    historical_spread_mean: float
    historical_spread_std: float
    statistics: dict


class CrossAssetDivergenceDetector:
    """
    Detects when correlated assets start diverging from historical relationships.
    
    Useful for identifying:
    - Pairs trading opportunities
    - Market stress (correlation breakdown)
    - Sector rotation signals
    - Arbitrage opportunities
    """
    
    def __init__(self, lookback_window: int = 60, 
                 correlation_threshold: float = 0.5,
                 z_score_threshold: float = 2.0):
        """
        Initialize detector.
        
        Args:
            lookback_window: Window for relationship estimation
            correlation_threshold: Minimum correlation to consider
            z_score_threshold: Z-score threshold for divergence
        """
        self.lookback_window = lookback_window
        self.correlation_threshold = correlation_threshold
        self.z_score_threshold = z_score_threshold
    
    def detect_spread_divergence(self, 
                                 asset1_prices: List[float],
                                 asset2_prices: List[float],
                                 asset1_name: str = "Asset1",
                                 asset2_name: str = "Asset2") -> List[DivergenceResult]:
        """
        Detect spread-based divergence between two assets.
        
        Args:
            asset1_prices: Price series for asset 1
            asset2_prices: Price series for asset 2
            asset1_name: Name of asset 1
            asset2_name: Name of asset 2
            
        Returns:
            List of detected divergences
        """
        if len(asset1_prices) < self.lookback_window * 2 or len(asset2_prices) < self.lookback_window * 2:
            return []
        
        divergences = []
        
        # Calculate spread (log prices)
        spread = [np.log(p1) - np.log(p2) for p1, p2 in zip(asset1_prices, asset2_prices)]
        
        # Rolling window analysis
        for i in range(self.lookback_window * 2, len(spread)):
            historical_spread = spread[i-self.lookback_window*2:i-self.lookback_window]
            recent_spread = spread[i-self.lookback_window:i]
            current_spread = spread[i]
            
            mean_hist = np.mean(historical_spread)
            std_hist = np.std(historical_spread)
            mean_recent = np.mean(recent_spread)
            
            if std_hist == 0:
                continue
            
            # Z-score of current spread vs historical
            z_score = abs((current_spread - mean_hist) / std_hist)
            
            # Check for spread explosion (mean shift)
            mean_shift_z = abs((mean_recent - mean_hist) / std_hist)
            
            if z_score > self.z_score_threshold or mean_shift_z > self.z_score_threshold:
                confidence = min(1.0, max(z_score, mean_shift_z) / 4.0)
                
                divergence_type = (
                    DivergenceType.SPREAD_EXPLOSION if z_score > self.z_score_threshold
                    else DivergenceType.COINTEGRATION_BREAK
                )
                
                divergences.append(DivergenceResult(
                    asset_pair=(asset1_name, asset2_name),
                    divergence_type=divergence_type,
                    start_idx=i - self.lookback_window,
                    confidence=confidence,
                    spread_value=current_spread,
                    historical_spread_mean=mean_hist,
                    historical_spread_std=std_hist,
                    statistics={
                        'z_score': z_score,
                        'mean_shift_z': mean_shift_z,
                        'current_spread': current_spread,
                        'mean_recent': mean_recent,
                    }
                ))
        
        return divergences
    
    def detect_correlation_breakdown(self,
                                    asset1_returns: List[float],
                                    asset2_returns: List[float],
                                    asset1_name: str = "Asset1",
                                    asset2_name: str = "Asset2") -> Optional[DivergenceResult]:
        """
        Detect correlation breakdown between two assets.
        
        Returns:
            DivergenceResult if correlation breakdown detected, None otherwise
        """
        if len(asset1_returns) < self.lookback_window * 2:
            return None
        
        # Calculate historical and recent correlation
        historical_corr = np.corrcoef(
            asset1_returns[:self.lookback_window],
            asset2_returns[:self.lookback_window]
        )[0, 1]
        
        recent_corr = np.corrcoef(
            asset1_returns[-self.lookback_window:],
            asset2_returns[-self.lookback_window:]
        )[0, 1]
        
        # Check for significant change
        if np.isnan(historical_corr) or np.isnan(recent_corr):
            return None
        
        # Detect breakdown: correlation dropped significantly
        if historical_corr > self.correlation_threshold and recent_corr < 0.3:
            confidence = min(1.0, (historical_corr - recent_corr) / historical_corr)
            
            return DivergenceResult(
                asset_pair=(asset1_name, asset2_name),
                divergence_type=DivergenceType.CORRELATION_BREAKDOWN,
                start_idx=len(asset1_returns) - self.lookback_window,
                confidence=confidence,
                spread_value=0,
                historical_spread_mean=historical_corr,
                historical_spread_std=0,
                statistics={
                    'historical_correlation': historical_corr,
                    'recent_correlation': recent_corr,
                    'correlation_change': historical_corr - recent_corr,
                }
            )
        
        return None
    
    def find_cointegrated_pairs(self, 
                                price_data: Dict[str, List[float]]) -> List[Tuple[str, str, float]]:
        """
        Find cointegrated pairs from a universe of assets.
        
        Args:
            price_data: Dictionary of asset_name -> price series
            
        Returns:
            List of (asset1, asset2, confidence) tuples
        """
        cointegrated = []
        assets = list(price_data.keys())
        
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                asset1, asset2 = assets[i], assets[j]
                prices1 = price_data[asset1]
                prices2 = price_data[asset2]
                
                if len(prices1) < self.lookback_window or len(prices2) < self.lookback_window:
                    continue
                
                # Simple cointegration test using correlation of returns and spread stationarity
                returns1 = np.diff(prices1) / prices1[:-1]
                returns2 = np.diff(prices2) / prices2[:-1]
                
                if len(returns1) < 10 or len(returns2) < 10:
                    continue
                
                correlation = np.corrcoef(returns1[-self.lookback_window:], 
                                         returns2[-self.lookback_window:])[0, 1]
                
                if correlation > 0.7:  # High correlation threshold
                    # Check spread stationarity (simplified)
                    spread = [np.log(p1) - np.log(p2) 
                             for p1, p2 in zip(prices1[-self.lookback_window:], 
                                              prices2[-self.lookback_window:])]
                    
                    # Simple stationarity test: check if spread reverts to mean
                    spread_mean = np.mean(spread)
                    spread_std = np.std(spread)
                    
                    if spread_std > 0:
                        # Count mean crossings as proxy for stationarity
                        crossings = sum(1 for k in range(1, len(spread)) 
                                      if (spread[k-1] - spread_mean) * (spread[k] - spread_mean) < 0)
                        
                        stationarity_score = crossings / len(spread)
                        
                        if stationarity_score > 0.1:  # Reasonable mean reversion
                            cointegrated.append((asset1, asset2, correlation * stationarity_score))
        
        # Sort by confidence
        cointegrated.sort(key=lambda x: x[2], reverse=True)
        return cointegrated
    
    def calculate_rolling_correlation(self,
                                    returns1: List[float],
                                    returns2: List[float],
                                    window: Optional[int] = None) -> List[float]:
        """
        Calculate rolling correlation between two return series.
        
        Returns:
            List of correlation values
        """
        window = window or self.lookback_window
        correlations = []
        
        for i in range(window, len(returns1)):
            corr = np.corrcoef(returns1[i-window:i], returns2[i-window:i])[0, 1]
            correlations.append(corr if not np.isnan(corr) else 0)
        
        return correlations
