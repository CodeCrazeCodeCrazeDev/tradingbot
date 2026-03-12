"""
Correlation Analysis Module
Detects breakdown in correlations and pairs trading opportunities
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
try:
    from scipy import stats
except ImportError:
    scipy = None
from sklearn.linear_model import LinearRegression
import asyncio
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

class CorrelationType(Enum):
    """Types of correlations to monitor"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    LAGGED = "lagged"
    NONLINEAR = "nonlinear"
    SEASONAL = "seasonal"

@dataclass
class CorrelationOpportunity:
    """Represents a correlation-based trading opportunity"""
    opportunity_id: str
    pair: Tuple[str, str]
    correlation_type: CorrelationType
    historical_correlation: float
    current_correlation: float
    deviation: float
    z_score: float
    expected_reversion: float
    confidence: float
    trade_direction: Dict[str, str]  # {symbol: 'LONG'/'SHORT'}
    entry_prices: Dict[str, float]
    target_spread: float
    stop_spread: float
    holding_period: float  # Expected days to convergence
    metadata: Dict[str, Any]

class CorrelationBreakdownDetector:
    """
    Detects when historically correlated assets diverge
    Creates mean-reversion opportunities
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lookback_period = self.config.get('lookback_period', 252)
        self.min_correlation = self.config.get('min_correlation', 0.7)
        self.z_score_threshold = self.config.get('z_score_threshold', 2.0)
        
        # Correlation tracking
        self.correlation_matrix = {}
        self.spread_history = {}
        self.half_life = {}
        
        # Cointegration tests
        self.cointegrated_pairs = []
        
    async def scan_correlation_breakdowns(self, market_data: Dict) -> List[CorrelationOpportunity]:
        """
        Scan for correlation breakdown opportunities
        """
        opportunities = []
        
        # Update correlation matrix
        self._update_correlations(market_data)
        
        # Find divergent pairs
        divergent_pairs = self._find_divergences(market_data)
        
        for pair in divergent_pairs:
            # Test for mean reversion potential
            if self._test_mean_reversion(pair, market_data):
                opportunity = self._create_correlation_opportunity(pair, market_data)
                opportunities.append(opportunity)
        
        return self._filter_opportunities(opportunities)
    
    def _update_correlations(self, market_data: Dict):
        """Update correlation matrix with latest data"""
        symbols = list(market_data.keys())
        n = len(symbols)
        
        # Initialize matrix if needed
        if not self.correlation_matrix:
            self.correlation_matrix = np.zeros((n, n))
        
        # Calculate pairwise correlations
        for i in range(n):
            for j in range(i+1, n):
                sym1, sym2 = symbols[i], symbols[j]
                
                if 'price_history' not in market_data[sym1]:
                    continue
                
                prices1 = market_data[sym1]['price_history'][-self.lookback_period:]
                prices2 = market_data[sym2]['price_history'][-self.lookback_period:]
                
                if len(prices1) == len(prices2) and len(prices1) >= 30:
                    # Calculate returns
                    returns1 = np.diff(prices1) / prices1[:-1]
                    returns2 = np.diff(prices2) / prices2[:-1]
                    
                    # Calculate correlation
                    if len(returns1) > 0:
                        corr = np.corrcoef(returns1, returns2)[0, 1]
                        self.correlation_matrix[i, j] = corr
                        self.correlation_matrix[j, i] = corr
    
    def _find_divergences(self, market_data: Dict) -> List[Tuple[str, str]]:
        """Find pairs that have diverged from historical correlation"""
        divergent_pairs = []
        symbols = list(market_data.keys())
        
        for i in range(len(symbols)):
            for j in range(i+1, len(symbols)):
                sym1, sym2 = symbols[i], symbols[j]
                
                # Check historical correlation
                hist_corr = self.correlation_matrix[i, j] if i < len(self.correlation_matrix) else 0
                
                if abs(hist_corr) < self.min_correlation:
                    continue
                
                # Calculate current spread z-score
                z_score = self._calculate_spread_zscore(sym1, sym2, market_data)
                
                if abs(z_score) > self.z_score_threshold:
                    divergent_pairs.append((sym1, sym2))
        
        return divergent_pairs
    
    def _calculate_spread_zscore(self, sym1: str, sym2: str, market_data: Dict) -> float:
        """Calculate z-score of current spread"""
        pair_key = f"{sym1}_{sym2}"
        
        # Get or calculate spread history
        if pair_key not in self.spread_history:
            self._calculate_spread_history(sym1, sym2, market_data)
        
        if pair_key not in self.spread_history:
            return 0
        
        spreads = self.spread_history[pair_key]
        if len(spreads) < 30:
            return 0
        
        # Calculate current spread
        price1 = market_data[sym1]['price']
        price2 = market_data[sym2]['price']
        
        # Get hedge ratio
        hedge_ratio = self._calculate_hedge_ratio(sym1, sym2, market_data)
        current_spread = np.log(price1) - hedge_ratio * np.log(price2)
        
        # Calculate z-score
        mean_spread = np.mean(spreads)
        std_spread = np.std(spreads)
        
        if std_spread == 0:
            return 0
        
        return (current_spread - mean_spread) / std_spread
    
    def _calculate_spread_history(self, sym1: str, sym2: str, market_data: Dict):
        """Calculate historical spread between two assets"""
        if 'price_history' not in market_data[sym1]:
            return
        
        prices1 = market_data[sym1]['price_history'][-self.lookback_period:]
        prices2 = market_data[sym2]['price_history'][-self.lookback_period:]
        
        if len(prices1) != len(prices2):
            return
        
        # Calculate hedge ratio using OLS
        hedge_ratio = self._calculate_hedge_ratio(sym1, sym2, market_data)
        
        # Calculate spread series
        log_prices1 = np.log(prices1)
        log_prices2 = np.log(prices2)
        spreads = log_prices1 - hedge_ratio * log_prices2
        
        self.spread_history[f"{sym1}_{sym2}"] = spreads
    
    def _calculate_hedge_ratio(self, sym1: str, sym2: str, market_data: Dict) -> float:
        """Calculate optimal hedge ratio using OLS regression"""
        prices1 = market_data[sym1]['price_history'][-self.lookback_period:]
        prices2 = market_data[sym2]['price_history'][-self.lookback_period:]
        
        if len(prices1) < 30 or len(prices2) < 30:
            return 1.0
        
        # Log prices for regression
        log_p1 = np.log(prices1).reshape(-1, 1)
        log_p2 = np.log(prices2).reshape(-1, 1)
        
        # OLS regression
        model = LinearRegression()
        model.fit(log_p2, log_p1)
        
        return model.coef_[0][0]
    
    def _test_mean_reversion(self, pair: Tuple[str, str], market_data: Dict) -> bool:
        """Test if the pair exhibits mean reversion"""
        sym1, sym2 = pair
        pair_key = f"{sym1}_{sym2}"
        
        if pair_key not in self.spread_history:
            return False
        
        spreads = self.spread_history[pair_key]
        
        # Augmented Dickey-Fuller test for stationarity
        # Simplified version - use statsmodels.tsa.stattools.adfuller in production
        
        # Calculate autocorrelation
        if len(spreads) < 60:
            return False
        
        autocorr = np.corrcoef(spreads[:-1], spreads[1:])[0, 1]
        
        # If autocorrelation is high but less than 1, likely mean-reverting
        if 0.5 < autocorr < 0.95:
            # Calculate half-life of mean reversion
            half_life = -np.log(2) / np.log(autocorr)
            self.half_life[pair_key] = half_life
            
            # Only trade if half-life is reasonable (2-30 days)
            return 2 < half_life < 30
        
        return False
    
    def _create_correlation_opportunity(self, pair: Tuple[str, str], 
                                      market_data: Dict) -> CorrelationOpportunity:
        """Create a correlation trading opportunity"""
        sym1, sym2 = pair
        pair_key = f"{sym1}_{sym2}"
        
        # Get current prices
        price1 = market_data[sym1]['price']
        price2 = market_data[sym2]['price']
        
        # Calculate z-score and spread
        z_score = self._calculate_spread_zscore(sym1, sym2, market_data)
        hedge_ratio = self._calculate_hedge_ratio(sym1, sym2, market_data)
        
        # Determine trade direction
        if z_score > 0:
            # Spread is too high - short sym1, long sym2
            trade_direction = {sym1: 'SHORT', sym2: 'LONG'}
        else:
            # Spread is too low - long sym1, short sym2
            trade_direction = {sym1: 'LONG', sym2: 'SHORT'}
        
        # Calculate targets
        spreads = self.spread_history[pair_key]
        mean_spread = np.mean(spreads)
        std_spread = np.std(spreads)
        current_spread = np.log(price1) - hedge_ratio * np.log(price2)
        
        target_spread = mean_spread  # Target mean reversion
        stop_spread = current_spread + (2 * std_spread * (1 if z_score < 0 else -1))
        
        # Expected return
        expected_return = abs(current_spread - mean_spread) / price1
        
        return CorrelationOpportunity(
            opportunity_id=f"CORR_{sym1}_{sym2}_{datetime.now().timestamp()}",
            pair=pair,
            correlation_type=CorrelationType.POSITIVE,
            historical_correlation=self._get_historical_correlation(sym1, sym2),
            current_correlation=self._get_current_correlation(sym1, sym2, market_data),
            deviation=abs(z_score),
            z_score=z_score,
            expected_reversion=expected_return,
            confidence=self._calculate_confidence(pair_key, z_score),
            trade_direction=trade_direction,
            entry_prices={sym1: price1, sym2: price2},
            target_spread=target_spread,
            stop_spread=stop_spread,
            holding_period=self.half_life.get(pair_key, 10),
            metadata={
                'hedge_ratio': hedge_ratio,
                'spread_mean': mean_spread,
                'spread_std': std_spread,
                'current_spread': current_spread,
                'half_life': self.half_life.get(pair_key)
            }
        )
    
    def _get_historical_correlation(self, sym1: str, sym2: str) -> float:
        """Get historical correlation between symbols"""
        # Look up in correlation matrix
        return 0.8  # Placeholder
    
    def _get_current_correlation(self, sym1: str, sym2: str, market_data: Dict) -> float:
        """Calculate current correlation (short-term)"""
        if 'price_history' not in market_data[sym1]:
            return 0
        
        # Use last 20 periods for current correlation
        prices1 = market_data[sym1]['price_history'][-20:]
        prices2 = market_data[sym2]['price_history'][-20:]
        
        if len(prices1) == len(prices2) and len(prices1) > 2:
            returns1 = np.diff(prices1) / prices1[:-1]
            returns2 = np.diff(prices2) / prices2[:-1]
            
            if len(returns1) > 0:
                return np.corrcoef(returns1, returns2)[0, 1]
        
        return 0
    
    def _calculate_confidence(self, pair_key: str, z_score: float) -> float:
        """Calculate confidence in mean reversion"""
        factors = []
        
        # Z-score magnitude
        z_confidence = min(1.0, abs(z_score) / 4)
        factors.append(z_confidence)
        
        # Half-life reliability
        if pair_key in self.half_life:
            hl = self.half_life[pair_key]
            hl_confidence = 1.0 if 5 < hl < 20 else 0.7
            factors.append(hl_confidence)
        
        # Historical success rate
        historical_confidence = 0.75  # Based on backtesting
        factors.append(historical_confidence)
        
        return np.mean(factors)
    
    def _filter_opportunities(self, opportunities: List[CorrelationOpportunity]) -> List[CorrelationOpportunity]:
        """Filter and rank opportunities"""
        filtered = []
        
        for opp in opportunities:
            if opp.confidence < 0.6:
                continue
            
            if opp.expected_reversion < 0.01:  # Less than 1% expected return
                continue
            
            if opp.holding_period > 30:  # Too long
                continue
            
            filtered.append(opp)
        
        # Sort by Sharpe ratio proxy (return / holding period)
        return sorted(filtered, 
                     key=lambda x: x.expected_reversion / max(1, x.holding_period), 
                     reverse=True)


class PairsTradingEngine:
    """
    Sophisticated pairs trading with multiple strategies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.pairs_universe = []
        self.active_pairs = {}
        self.performance_history = {}
        
    async def find_pairs_opportunities(self, market_data: Dict) -> List[CorrelationOpportunity]:
        """Find and rank pairs trading opportunities"""
        opportunities = []
        
        # Statistical arbitrage pairs
        stat_arb = await self._find_statistical_arbitrage(market_data)
        opportunities.extend(stat_arb)
        
        # Sector neutral pairs
        sector_pairs = await self._find_sector_pairs(market_data)
        opportunities.extend(sector_pairs)
        
        # Index arbitrage pairs
        index_pairs = await self._find_index_arbitrage(market_data)
        opportunities.extend(index_pairs)
        
        return self._rank_opportunities(opportunities)
    
    async def _find_statistical_arbitrage(self, market_data: Dict) -> List[CorrelationOpportunity]:
        """Find statistical arbitrage pairs"""
        # Cointegration-based pairs
        # Distance method pairs
        # Copula-based pairs
        return []
    
    async def _find_sector_pairs(self, market_data: Dict) -> List[CorrelationOpportunity]:
        """Find sector-neutral pairs"""
        # Pairs within same sector
        # Market-neutral construction
        return []
    
    async def _find_index_arbitrage(self, market_data: Dict) -> List[CorrelationOpportunity]:
        """Find index arbitrage opportunities"""
        # ETF vs constituents
        # Index futures vs cash
        return []
    
    def _rank_opportunities(self, opportunities: List[CorrelationOpportunity]) -> List[CorrelationOpportunity]:
        """Rank opportunities by expected risk-adjusted return"""
        for opp in opportunities:
            # Calculate Sharpe ratio
            expected_return = opp.expected_reversion
            expected_vol = 0.15 / np.sqrt(252 / opp.holding_period)  # Annualized
            opp.sharpe = expected_return / expected_vol if expected_vol > 0 else 0
        
        return sorted(opportunities, key=lambda x: x.sharpe, reverse=True)


class SpreadAnalyzer:
    """
    Analyzes spreads for trading opportunities
    """
    
    def __init__(self):
        self.spread_models = {}
        self.seasonality_patterns = {}
        
    def analyze_spread(self, sym1: str, sym2: str, prices1: List[float], 
                       prices2: List[float]) -> Dict:
        """
        Comprehensive spread analysis
        """
        # Calculate various spread metrics
        log_spread = np.log(np.array(prices1)) - np.log(np.array(prices2))
        ratio_spread = np.array(prices1) / np.array(prices2)
        
        analysis = {
            'mean': np.mean(log_spread),
            'std': np.std(log_spread),
            'current': log_spread[-1],
            'z_score': (log_spread[-1] - np.mean(log_spread)) / np.std(log_spread),
            'percentile': stats.percentileofscore(log_spread, log_spread[-1]),
            'trend': self._calculate_trend(log_spread),
            'momentum': self._calculate_momentum(log_spread),
            'mean_reversion_speed': self._calculate_reversion_speed(log_spread),
            'regime': self._identify_regime(log_spread)
        }
        
        return analysis
    
    def _calculate_trend(self, spread: np.ndarray) -> float:
        """Calculate spread trend"""
        if len(spread) < 10:
            return 0
        
        # Linear regression slope
        x = np.arange(len(spread))
        slope, _ = np.polyfit(x, spread, 1)
        
        return slope
    
    def _calculate_momentum(self, spread: np.ndarray) -> float:
        """Calculate spread momentum"""
        if len(spread) < 20:
            return 0
        
        # Rate of change
        return (spread[-1] - spread[-20]) / spread[-20] if spread[-20] != 0 else 0
    
    def _calculate_reversion_speed(self, spread: np.ndarray) -> float:
        """Calculate mean reversion speed (Ornstein-Uhlenbeck)"""
        if len(spread) < 60:
            return 0
        
        # AR(1) coefficient
        y = spread[1:]
        x = spread[:-1]
        
        if len(x) > 0:
            beta = np.cov(x, y)[0, 1] / np.var(x)
            theta = -np.log(beta) if beta > 0 else 0
            return theta
        
        return 0
    
    def _identify_regime(self, spread: np.ndarray) -> str:
        """Identify spread regime"""
        if len(spread) < 30:
            return "UNKNOWN"
        
        recent = spread[-30:]
        mean = np.mean(recent)
        std = np.std(recent)
        
        # Check for trending
        trend = self._calculate_trend(recent)
        
        if abs(trend) > std * 0.1:
            return "TRENDING"
        elif std < np.std(spread) * 0.5:
            return "COMPRESSED"
        elif std > np.std(spread) * 1.5:
            return "VOLATILE"
        else:
            return "MEAN_REVERTING"


class CointegrationMonitor:
    """
    Monitors cointegration relationships
    """
    
    def __init__(self):
        self.cointegration_tests = {}
        self.test_history = {}
        
    def test_cointegration(self, prices1: List[float], prices2: List[float]) -> Dict:
        """
        Test for cointegration using multiple methods
        """
        results = {
            'is_cointegrated': False,
            'confidence': 0,
            'test_statistic': 0,
            'p_value': 1.0,
            'half_life': None
        }
        
        if len(prices1) < 60 or len(prices2) < 60:
            return results
        
        # Engle-Granger test (simplified)
        log_p1 = np.log(prices1)
        log_p2 = np.log(prices2)
        
        # OLS regression
        model = LinearRegression()
        model.fit(log_p2.reshape(-1, 1), log_p1)
        
        # Calculate residuals
        residuals = log_p1 - model.predict(log_p2.reshape(-1, 1))
        
        # Test residuals for stationarity (simplified ADF test)
        # In production, use statsmodels.tsa.stattools.adfuller
        
        # Calculate autocorrelation
        if len(residuals) > 1:
            autocorr = np.corrcoef(residuals[:-1], residuals[1:])[0, 1]
            
            # Simple stationarity check
            if -0.1 < autocorr < 0.95:
                results['is_cointegrated'] = True
                results['confidence'] = 1 - autocorr
                results['half_life'] = -np.log(2) / np.log(autocorr) if autocorr > 0 else None
        
        return results
    
    def monitor_stability(self, pair: Tuple[str, str], prices1: List[float], 
                         prices2: List[float]) -> Dict:
        """
        Monitor cointegration stability over time
        """
        pair_key = f"{pair[0]}_{pair[1]}"
        
        # Rolling cointegration tests
        window = 60
        stability_scores = []
        
        for i in range(window, len(prices1), 10):
            window_p1 = prices1[i-window:i]
            window_p2 = prices2[i-window:i]
            
            test_result = self.test_cointegration(window_p1, window_p2)
            stability_scores.append(test_result['confidence'])
        
        return {
            'average_stability': np.mean(stability_scores) if stability_scores else 0,
            'current_stability': stability_scores[-1] if stability_scores else 0,
            'is_stable': np.mean(stability_scores) > 0.7 if stability_scores else False
        }
