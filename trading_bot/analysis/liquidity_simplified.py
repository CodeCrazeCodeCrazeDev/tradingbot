"""
Simplified Liquidity Analysis Module

This module provides a simplified interface to the main liquidity analysis module
for use in the Elite Trading System dashboard.
"""

import numpy as np
import pandas as pd
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import logging

from .liquidity import LiquidityAnalyzer, LiquidityPool, OrderBlock, FairValueGap, TimeFrame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LiquidityAnalysisResult:
    """Simplified liquidity analysis result for dashboard use"""
    key_levels: List[float] = field(default_factory=list)
    imbalance_zones: List[Tuple[float, float]] = field(default_factory=list)
    accumulation_strength: float = 0.0
    distribution_strength: float = 0.0
    buy_liquidity_pools: List[LiquidityPool] = field(default_factory=list)
    sell_liquidity_pools: List[LiquidityPool] = field(default_factory=list)
    order_blocks: List[OrderBlock] = field(default_factory=list)
    fair_value_gaps: List[FairValueGap] = field(default_factory=list)

class LiquidityAnalysis:
    """Simplified liquidity analysis for dashboard use"""
    
    def __init__(self):
        """Initialize liquidity analyzer"""
        self.analyzer = LiquidityAnalyzer()
        logger.info("Liquidity Analysis initialized")
    
    async def analyze(self, market_data: pd.DataFrame, context: Any = None, 
                     timeframe: str = '1H') -> LiquidityAnalysisResult:
        """
        Perform liquidity analysis on market data
        
        Args:
            market_data: OHLCV DataFrame
            context: Optional market context
            timeframe: Timeframe of the data
            
        Returns:
            LiquidityAnalysisResult with analysis results
        """
        try:
            # Convert timeframe string to TimeFrame enum
            tf = self._parse_timeframe(timeframe)
            
            # Find liquidity pools
            buy_pools, sell_pools = self.analyzer.find_equal_highs_lows(market_data, tf)
            
            # Detect order blocks
            order_blocks = self.analyzer.detect_order_blocks(market_data, tf)
            
            # Detect fair value gaps
            fvgs = self.analyzer.detect_fair_value_gaps(market_data, tf)
            
            # Check for mitigation
            self.analyzer.check_order_block_mitigation(market_data, order_blocks)
            self.analyzer.check_fvg_filling(market_data, fvgs)
            
            # Extract key levels
            key_levels = self._extract_key_levels(buy_pools, sell_pools, order_blocks)
            
            # Extract imbalance zones
            imbalance_zones = self._extract_imbalance_zones(fvgs)
            
            # Calculate accumulation/distribution strength
            acc_strength, dist_strength = self._calculate_strength(buy_pools, sell_pools, order_blocks)
            
            # Create result
            result = LiquidityAnalysisResult(
                key_levels=key_levels,
                imbalance_zones=imbalance_zones,
                accumulation_strength=acc_strength,
                distribution_strength=dist_strength,
                buy_liquidity_pools=buy_pools,
                sell_liquidity_pools=sell_pools,
                order_blocks=order_blocks,
                fair_value_gaps=fvgs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in liquidity analysis: {e}")
            return LiquidityAnalysisResult()
    
    def _parse_timeframe(self, timeframe: str) -> TimeFrame:
        """Convert timeframe string to TimeFrame enum"""
        mapping = {
            '1m': TimeFrame.M1,
            '5m': TimeFrame.M5,
            '15m': TimeFrame.M15,
            '30m': TimeFrame.M30,
            '1h': TimeFrame.H1,
            '1H': TimeFrame.H1,
            '4h': TimeFrame.H4,
            '4H': TimeFrame.H4,
            '1d': TimeFrame.D1,
            '1D': TimeFrame.D1,
            'D': TimeFrame.D1,
            'W': TimeFrame.W1,
            '1w': TimeFrame.W1
        }
        return mapping.get(timeframe, TimeFrame.M15)
    
    def _extract_key_levels(self, buy_pools: List[LiquidityPool], 
                          sell_pools: List[LiquidityPool],
                          order_blocks: List[OrderBlock]) -> List[float]:
        """Extract key price levels from liquidity analysis"""
        levels = []
        
        # Add liquidity pool levels
        for pool in buy_pools:
            levels.append(pool.price)
        
        for pool in sell_pools:
            levels.append(pool.price)
        
        # Add order block levels
        for ob in order_blocks:
            levels.append(ob.high)
            levels.append(ob.low)
        
        # Remove duplicates and sort
        levels = sorted(set(levels))
        
        return levels
    
    def _extract_imbalance_zones(self, fvgs: List[FairValueGap]) -> List[Tuple[float, float]]:
        """Extract imbalance zones from fair value gaps"""
        zones = []
        
        for fvg in fvgs:
            if not fvg.filled:
                zones.append((fvg.low, fvg.high))
        
        return zones
    
    def _calculate_strength(self, buy_pools: List[LiquidityPool],
                          sell_pools: List[LiquidityPool],
                          order_blocks: List[OrderBlock]) -> Tuple[float, float]:
        """Calculate accumulation and distribution strength"""
        acc_strength = 0.0
        dist_strength = 0.0
        
        # Calculate from liquidity pools
        for pool in buy_pools:
            if not pool.mitigated:
                acc_strength += pool.strength * 0.2
        
        for pool in sell_pools:
            if not pool.mitigated:
                dist_strength += pool.strength * 0.2
        
        # Calculate from order blocks
        for ob in order_blocks:
            if not ob.mitigated:
                if ob.type.value == "bullish":
                    acc_strength += ob.strength * 0.3
                elif ob.type.value == "bearish":
                    dist_strength += ob.strength * 0.3
        
        # Normalize to 0-1 range
        acc_strength = min(1.0, acc_strength)
        dist_strength = min(1.0, dist_strength)
        
        return acc_strength, dist_strength

# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='1H')
    np.random.seed(42)
    
    market_data = pd.DataFrame({
        'open': np.random.randn(len(dates)).cumsum() + 100,
        'high': np.random.randn(len(dates)).cumsum() + 102,
        'low': np.random.randn(len(dates)).cumsum() + 98,
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Create analyzer
    analyzer = LiquidityAnalysis()
    
    # Run analysis
    async def test():
        result = await analyzer.analyze(market_data)
        logger.info(f"Key Levels: {[round(level, 2) for level in result.key_levels]}")
        logger.info(f"Imbalance Zones: {len(result.imbalance_zones)}")
        logger.info(f"Accumulation Strength: {result.accumulation_strength:.2f}")
        logger.info(f"Distribution Strength: {result.distribution_strength:.2f}")
    
    # Run test
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


    asyncio.run(test())
