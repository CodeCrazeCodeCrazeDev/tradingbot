"""
Lead-Lag Relationship Analysis.

This module implements:
- Cross-asset lead-lag detection
- Granger causality testing
- Correlation lag analysis
- Predictive relationship identification
- Intermarket analysis
- Currency correlation analysis
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of lead-lag relationships."""
    LEADING = "leading"
    LAGGING = "lagging"
    COINCIDENT = "coincident"
    NO_RELATIONSHIP = "no_relationship"


class AssetClass(Enum):
    """Asset classes for intermarket analysis."""
    FOREX = "forex"
    EQUITY = "equity"
    COMMODITY = "commodity"
    BOND = "bond"
    CRYPTO = "crypto"
    INDEX = "index"


@dataclass
class LeadLagResult:
    """Result of lead-lag analysis."""
    leader: str
    lagger: str
    optimal_lag: int  # In periods
    correlation: float
    relationship: RelationshipType
    confidence: float
    p_value: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GrangerResult:
    """Result of Granger causality test."""
    cause: str
    effect: str
    f_statistic: float
    p_value: float
    is_causal: bool
    optimal_lag: int
    confidence: float


@dataclass
class IntermarketSignal:
    """Signal from intermarket analysis."""
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    strength: float
    leading_assets: List[str]
    confirming_assets: List[str]
    diverging_assets: List[str]
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class LeadLagAnalyzer:
    """
    Analyzes lead-lag relationships between assets.
    """
    
    def __init__(
        self,
        max_lag: int = 20,
        min_correlation: float = 0.3,
        significance_level: float = 0.05
    ):
        self.max_lag = max_lag
        self.min_correlation = min_correlation
        self.significance_level = significance_level
        
    def calculate_lagged_correlation(
        self,
        series1: pd.Series,
        series2: pd.Series,
        lag: int
    ) -> float:
        """Calculate correlation with specified lag."""
        if lag > 0:
            # series1 leads series2
            s1 = series1.iloc[:-lag]
            s2 = series2.iloc[lag:]
        elif lag < 0:
            # series2 leads series1
            s1 = series1.iloc[-lag:]
            s2 = series2.iloc[:lag]
        else:
            s1 = series1
            s2 = series2
        
        if len(s1) < 10 or len(s2) < 10:
            return 0.0
        
        return float(s1.corr(s2))
    
    def find_optimal_lag(
        self,
        series1: pd.Series,
        series2: pd.Series
    ) -> Tuple[int, float]:
        """Find the lag that maximizes correlation."""
        best_lag = 0
        best_corr = 0.0
        
        for lag in range(-self.max_lag, self.max_lag + 1):
            corr = self.calculate_lagged_correlation(series1, series2, lag)
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag
        
        return best_lag, best_corr
    
    def analyze_lead_lag(
        self,
        asset1: str,
        series1: pd.Series,
        asset2: str,
        series2: pd.Series
    ) -> LeadLagResult:
        """Analyze lead-lag relationship between two assets."""
        # Calculate returns
        returns1 = series1.pct_change().dropna()
        returns2 = series2.pct_change().dropna()
        
        # Align series
        common_idx = returns1.index.intersection(returns2.index)
        returns1 = returns1.loc[common_idx]
        returns2 = returns2.loc[common_idx]
        
        # Find optimal lag
        optimal_lag, correlation = self.find_optimal_lag(returns1, returns2)
        
        # Determine relationship
        if abs(correlation) < self.min_correlation:
            relationship = RelationshipType.NO_RELATIONSHIP
        elif optimal_lag > 0:
            relationship = RelationshipType.LEADING
            leader, lagger = asset1, asset2
        elif optimal_lag < 0:
            relationship = RelationshipType.LAGGING
            leader, lagger = asset2, asset1
            optimal_lag = abs(optimal_lag)
        else:
            relationship = RelationshipType.COINCIDENT
            leader, lagger = asset1, asset2
        
        # Calculate confidence (based on correlation strength and consistency)
        confidence = min(1.0, abs(correlation) / 0.7)
        
        # Approximate p-value (simplified)
        n = len(returns1)
        t_stat = correlation * np.sqrt(n - 2) / np.sqrt(1 - correlation**2 + 1e-10)
        # Simplified p-value approximation
        p_value = 2 * (1 - min(0.9999, abs(t_stat) / 10))
        
        return LeadLagResult(
            leader=leader if relationship != RelationshipType.NO_RELATIONSHIP else asset1,
            lagger=lagger if relationship != RelationshipType.NO_RELATIONSHIP else asset2,
            optimal_lag=abs(optimal_lag),
            correlation=correlation,
            relationship=relationship,
            confidence=confidence,
            p_value=p_value
        )
    
    def granger_causality_test(
        self,
        cause_series: pd.Series,
        effect_series: pd.Series,
        max_lag: int = 5
    ) -> GrangerResult:
        """
        Perform Granger causality test.
        
        Tests if cause_series Granger-causes effect_series.
        """
        # Prepare data
        cause = cause_series.pct_change().dropna()
        effect = effect_series.pct_change().dropna()
        
        # Align
        common_idx = cause.index.intersection(effect.index)
        cause = cause.loc[common_idx].values
        effect = effect.loc[common_idx].values
        
        n = len(effect)
        
        if n < max_lag + 10:
            return GrangerResult(
                cause="",
                effect="",
                f_statistic=0,
                p_value=1.0,
                is_causal=False,
                optimal_lag=0,
                confidence=0
            )
        
        best_f = 0
        best_lag = 1
        best_p = 1.0
        
        for lag in range(1, max_lag + 1):
            # Restricted model: effect ~ effect_lags
            # Unrestricted model: effect ~ effect_lags + cause_lags
            
            # Build lagged matrices
            y = effect[lag:]
            
            # Effect lags only (restricted)
            X_r = np.column_stack([effect[lag-i-1:-i-1] for i in range(lag)])
            
            # Effect lags + cause lags (unrestricted)
            X_u = np.column_stack([
                *[effect[lag-i-1:-i-1] for i in range(lag)],
                *[cause[lag-i-1:-i-1] for i in range(lag)]
            ])
            
            # Fit models using OLS
            try:
                # Restricted model
                beta_r = np.linalg.lstsq(X_r, y, rcond=None)[0]
                resid_r = y - X_r @ beta_r
                ssr_r = np.sum(resid_r**2)
                
                # Unrestricted model
                beta_u = np.linalg.lstsq(X_u, y, rcond=None)[0]
                resid_u = y - X_u @ beta_u
                ssr_u = np.sum(resid_u**2)
                
                # F-statistic
                df1 = lag
                df2 = len(y) - 2 * lag - 1
                
                if ssr_u > 0 and df2 > 0:
                    f_stat = ((ssr_r - ssr_u) / df1) / (ssr_u / df2)
                    
                    # Approximate p-value
                    p_value = 1 - min(0.9999, f_stat / (f_stat + df2/df1))
                    
                    if f_stat > best_f:
                        best_f = f_stat
                        best_lag = lag
                        best_p = p_value
            except Exception:
                continue
        
        is_causal = best_p < self.significance_level
        confidence = 1 - best_p if is_causal else 0
        
        return GrangerResult(
            cause=cause_series.name if hasattr(cause_series, 'name') else "cause",
            effect=effect_series.name if hasattr(effect_series, 'name') else "effect",
            f_statistic=best_f,
            p_value=best_p,
            is_causal=is_causal,
            optimal_lag=best_lag,
            confidence=confidence
        )


class IntermarketAnalyzer:
    """
    Analyzes intermarket relationships for trading signals.
    """
    
    def __init__(self):
        self.lead_lag = LeadLagAnalyzer()
        
        # Known intermarket relationships
        self.relationships = {
            # Forex relationships
            ('DXY', 'EURUSD'): -0.9,  # Inverse
            ('DXY', 'GBPUSD'): -0.8,
            ('USDJPY', 'US10Y'): 0.7,  # Yield correlation
            
            # Commodity-currency relationships
            ('GOLD', 'DXY'): -0.6,
            ('OIL', 'USDCAD'): -0.5,
            ('GOLD', 'AUDUSD'): 0.6,
            
            # Risk relationships
            ('SPX', 'VIX'): -0.8,
            ('SPX', 'USDJPY'): 0.5,  # Risk-on correlation
            
            # Bond-equity relationships
            ('US10Y', 'SPX'): -0.3,
        }
        
    def analyze_pair(
        self,
        asset1: str,
        data1: pd.Series,
        asset2: str,
        data2: pd.Series
    ) -> Dict[str, Any]:
        """Analyze relationship between two assets."""
        # Lead-lag analysis
        lead_lag = self.lead_lag.analyze_lead_lag(asset1, data1, asset2, data2)
        
        # Granger causality both directions
        granger_1_2 = self.lead_lag.granger_causality_test(data1, data2)
        granger_2_1 = self.lead_lag.granger_causality_test(data2, data1)
        
        # Current correlation
        returns1 = data1.pct_change().dropna()
        returns2 = data2.pct_change().dropna()
        common_idx = returns1.index.intersection(returns2.index)
        current_corr = returns1.loc[common_idx].corr(returns2.loc[common_idx])
        
        # Check for expected relationship
        expected = self.relationships.get((asset1, asset2)) or \
                   self.relationships.get((asset2, asset1))
        
        if expected:
            expected_corr = expected if (asset1, asset2) in self.relationships else -expected
            divergence = current_corr - expected_corr
        else:
            divergence = 0
        
        return {
            'lead_lag': lead_lag,
            'granger_1_causes_2': granger_1_2,
            'granger_2_causes_1': granger_2_1,
            'current_correlation': current_corr,
            'expected_correlation': expected,
            'divergence': divergence,
            'is_diverging': abs(divergence) > 0.3 if expected else False
        }
    
    def get_intermarket_signal(
        self,
        target_asset: str,
        target_data: pd.Series,
        related_assets: Dict[str, pd.Series]
    ) -> IntermarketSignal:
        """Get trading signal based on intermarket analysis."""
        leading = []
        confirming = []
        diverging = []
        
        bullish_score = 0
        bearish_score = 0
        
        for asset, data in related_assets.items():
            analysis = self.analyze_pair(asset, data, target_asset, target_data)
            
            lead_lag = analysis['lead_lag']
            
            # Check if this asset leads the target
            if lead_lag.relationship == RelationshipType.LEADING and \
               lead_lag.leader == asset and lead_lag.confidence > 0.5:
                leading.append(asset)
                
                # Get recent direction of leader
                recent_return = data.pct_change().iloc[-5:].mean()
                
                if lead_lag.correlation > 0:
                    # Positive correlation - same direction
                    if recent_return > 0:
                        bullish_score += lead_lag.confidence
                    else:
                        bearish_score += lead_lag.confidence
                else:
                    # Negative correlation - opposite direction
                    if recent_return > 0:
                        bearish_score += lead_lag.confidence
                    else:
                        bullish_score += lead_lag.confidence
            
            # Check for confirmation
            if abs(analysis['current_correlation']) > 0.5:
                recent_return_related = data.pct_change().iloc[-5:].mean()
                recent_return_target = target_data.pct_change().iloc[-5:].mean()
                
                if (recent_return_related > 0) == (recent_return_target > 0):
                    confirming.append(asset)
                else:
                    diverging.append(asset)
        
        # Determine signal
        total_score = bullish_score + bearish_score
        if total_score > 0:
            if bullish_score > bearish_score * 1.5:
                signal_type = 'bullish'
                strength = bullish_score / total_score
            elif bearish_score > bullish_score * 1.5:
                signal_type = 'bearish'
                strength = bearish_score / total_score
            else:
                signal_type = 'neutral'
                strength = 0.5
        else:
            signal_type = 'neutral'
            strength = 0
        
        # Generate message
        if leading:
            message = f"Leading indicators ({', '.join(leading)}) suggest {signal_type} bias"
        elif confirming:
            message = f"Confirming assets: {', '.join(confirming)}"
        else:
            message = "No clear intermarket signal"
        
        return IntermarketSignal(
            signal_type=signal_type,
            strength=strength,
            leading_assets=leading,
            confirming_assets=confirming,
            diverging_assets=diverging,
            message=message
        )


class SectorAnalyzer:
    """
    Analyzes sector rotations and relationships.
    """
    
    def __init__(self):
        self.sectors = {
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLE': 'Energy',
            'XLV': 'Healthcare',
            'XLI': 'Industrials',
            'XLP': 'Consumer Staples',
            'XLY': 'Consumer Discretionary',
            'XLB': 'Materials',
            'XLU': 'Utilities',
            'XLRE': 'Real Estate'
        }
        
        # Sector relationships in business cycle
        self.cycle_order = [
            'XLF',  # Early cycle
            'XLI',
            'XLB',
            'XLK',  # Mid cycle
            'XLY',
            'XLE',
            'XLV',  # Late cycle
            'XLP',
            'XLU',
            'XLRE'
        ]
        
    def calculate_relative_strength(
        self,
        sector_data: pd.Series,
        benchmark_data: pd.Series,
        period: int = 20
    ) -> float:
        """Calculate relative strength vs benchmark."""
        sector_return = sector_data.pct_change(period).iloc[-1]
        benchmark_return = benchmark_data.pct_change(period).iloc[-1]
        
        return sector_return - benchmark_return
    
    def rank_sectors(
        self,
        sector_data: Dict[str, pd.Series],
        benchmark_data: pd.Series
    ) -> List[Tuple[str, float]]:
        """Rank sectors by relative strength."""
        rankings = []
        
        for symbol, data in sector_data.items():
            rs = self.calculate_relative_strength(data, benchmark_data)
            rankings.append((symbol, rs))
        
        return sorted(rankings, key=lambda x: x[1], reverse=True)
    
    def detect_rotation(
        self,
        sector_data: Dict[str, pd.Series],
        lookback: int = 20
    ) -> Dict[str, Any]:
        """Detect sector rotation patterns."""
        # Calculate momentum for each sector
        momentum = {}
        for symbol, data in sector_data.items():
            returns = data.pct_change()
            recent = returns.iloc[-lookback:].mean()
            prior = returns.iloc[-2*lookback:-lookback].mean()
            momentum[symbol] = {
                'recent': recent,
                'prior': prior,
                'acceleration': recent - prior
            }
        
        # Find leaders and laggards
        by_recent = sorted(momentum.items(), key=lambda x: x[1]['recent'], reverse=True)
        by_acceleration = sorted(momentum.items(), key=lambda x: x[1]['acceleration'], reverse=True)
        
        leaders = [s for s, _ in by_recent[:3]]
        laggards = [s for s, _ in by_recent[-3:]]
        accelerating = [s for s, _ in by_acceleration[:3]]
        decelerating = [s for s, _ in by_acceleration[-3:]]
        
        # Determine cycle phase
        leader_positions = [self.cycle_order.index(s) for s in leaders if s in self.cycle_order]
        if leader_positions:
            avg_position = np.mean(leader_positions)
            if avg_position < 3:
                cycle_phase = 'early'
            elif avg_position < 6:
                cycle_phase = 'mid'
            else:
                cycle_phase = 'late'
        else:
            cycle_phase = 'unknown'
        
        return {
            'leaders': leaders,
            'laggards': laggards,
            'accelerating': accelerating,
            'decelerating': decelerating,
            'cycle_phase': cycle_phase,
            'momentum': momentum
        }
    
    def get_sector_signal(
        self,
        target_sector: str,
        sector_data: Dict[str, pd.Series],
        benchmark_data: pd.Series
    ) -> Dict[str, Any]:
        """Get trading signal for a specific sector."""
        if target_sector not in sector_data:
            return {'signal': 'neutral', 'strength': 0, 'reason': 'Sector not found'}
        
        # Rank sectors
        rankings = self.rank_sectors(sector_data, benchmark_data)
        rank_dict = {s: i+1 for i, (s, _) in enumerate(rankings)}
        
        target_rank = rank_dict.get(target_sector, len(rankings) // 2)
        target_rs = next((rs for s, rs in rankings if s == target_sector), 0)
        
        # Detect rotation
        rotation = self.detect_rotation(sector_data)
        
        # Generate signal
        if target_sector in rotation['leaders'] and target_sector in rotation['accelerating']:
            signal = 'strong_bullish'
            strength = 0.9
        elif target_sector in rotation['leaders']:
            signal = 'bullish'
            strength = 0.7
        elif target_sector in rotation['laggards'] and target_sector in rotation['decelerating']:
            signal = 'strong_bearish'
            strength = 0.9
        elif target_sector in rotation['laggards']:
            signal = 'bearish'
            strength = 0.7
        elif target_sector in rotation['accelerating']:
            signal = 'bullish'
            strength = 0.5
        elif target_sector in rotation['decelerating']:
            signal = 'bearish'
            strength = 0.5
        else:
            signal = 'neutral'
            strength = 0.3
        
        return {
            'signal': signal,
            'strength': strength,
            'rank': target_rank,
            'relative_strength': target_rs,
            'cycle_phase': rotation['cycle_phase'],
            'is_leader': target_sector in rotation['leaders'],
            'is_accelerating': target_sector in rotation['accelerating']
        }


# Convenience functions
def find_leading_asset(
    target: pd.Series,
    candidates: Dict[str, pd.Series]
) -> Optional[LeadLagResult]:
    """Find the best leading indicator for target asset."""
    analyzer = LeadLagAnalyzer()
    
    best_result = None
    best_confidence = 0
    
    for name, data in candidates.items():
        result = analyzer.analyze_lead_lag(name, data, "target", target)
        
        if result.relationship == RelationshipType.LEADING and \
           result.confidence > best_confidence:
            best_result = result
            best_confidence = result.confidence
    
    return best_result


def test_granger_causality(
    cause: pd.Series,
    effect: pd.Series,
    max_lag: int = 5
) -> Dict[str, Any]:
    """Quick Granger causality test."""
    analyzer = LeadLagAnalyzer()
    result = analyzer.granger_causality_test(cause, effect, max_lag)
    
    return {
        'is_causal': result.is_causal,
        'f_statistic': result.f_statistic,
        'p_value': result.p_value,
        'optimal_lag': result.optimal_lag,
        'confidence': result.confidence
    }


def get_correlation_at_lag(
    series1: pd.Series,
    series2: pd.Series,
    lag: int
) -> float:
    """Get correlation at specific lag."""
    analyzer = LeadLagAnalyzer()
    return analyzer.calculate_lagged_correlation(series1, series2, lag)
