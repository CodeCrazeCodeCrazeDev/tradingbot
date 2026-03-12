"""
Execution Realism Gate - The Bridge Between Backtest Fantasy and Live Reality

This gate ensures that all trading decisions account for real-world execution:
1. Slippage - You won't get the price you see
2. Latency - By the time you act, the market moved
3. Partial fills - You might not get your full size
4. Market impact - Your order moves the market
5. Spread costs - Bid/ask spread eats into profits

THE PROBLEM:
- Backtest assumes instant execution at mid-price
- Reality: 50ms latency, 2 pip slippage, partial fills
- Backtest: +20% returns
- Reality: -5% after execution costs

RULE: "If it doesn't work with realistic execution, it doesn't work."

Author: AlphaAlgo Reality Check System
"""

import logging
import statistics
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class ExecutionQuality(Enum):
    """Quality of execution conditions"""
    EXCELLENT = "excellent"  # Low spread, high liquidity
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"  # Block trading


@dataclass
class ExecutionAssumptions:
    """Realistic execution assumptions"""
    # Slippage (in basis points)
    expected_slippage_bps: float = 5.0  # 0.05%
    max_slippage_bps: float = 20.0  # 0.20%
    
    # Latency (milliseconds)
    expected_latency_ms: float = 50.0
    max_latency_ms: float = 500.0
    
    # Fill rates
    expected_fill_rate: float = 0.95  # 95% filled
    min_acceptable_fill_rate: float = 0.80
    
    # Spread (basis points)
    expected_spread_bps: float = 2.0
    max_spread_bps: float = 10.0
    
    # Market impact (basis points per $1M)
    market_impact_per_million: float = 5.0
    
    # Commission (per trade)
    commission_per_trade: float = 2.0
    
    # Minimum edge required after costs
    min_edge_after_costs_bps: float = 10.0


@dataclass
class RealismAdjustment:
    """Adjustments to apply for realistic execution"""
    # Adjusted metrics
    adjusted_return: float
    adjusted_sharpe: float
    adjusted_win_rate: float
    
    # Cost breakdown
    slippage_cost: float
    spread_cost: float
    commission_cost: float
    market_impact_cost: float
    latency_cost: float
    total_cost: float
    
    # Original vs adjusted
    return_haircut: float  # How much return was reduced
    
    # Execution quality
    quality: ExecutionQuality
    is_viable: bool
    
    # Warnings
    warnings: List[str] = field(default_factory=list)


class ExecutionRealismGate:
    """
    HARD GATE: Execution Realism
    
    This gate BLOCKS any trade or strategy that doesn't account for
    realistic execution costs and conditions.
    
    Adjustments applied:
    1. Slippage - Based on volatility and order size
    2. Spread costs - Actual bid/ask spread
    3. Market impact - Based on order size vs ADV
    4. Latency - Price movement during execution
    5. Partial fills - Reduced position sizes
    6. Commissions - Fixed and variable costs
    
    A trade must:
    - Have positive expected return AFTER all costs
    - Meet minimum edge threshold
    - Have acceptable execution conditions
    """
    
    def __init__(self, assumptions: Optional[ExecutionAssumptions] = None):
        try:
            self.assumptions = assumptions or ExecutionAssumptions()
        
            # Historical execution data
            self.execution_history: Dict[str, deque] = {}
            self.slippage_history: deque = deque(maxlen=1000)
            self.fill_rate_history: deque = deque(maxlen=1000)
        
            # Statistics
            self.trades_analyzed = 0
            self.trades_blocked = 0
            self.total_cost_saved = 0.0
        
            logger.info("ExecutionRealismGate initialized - NO FANTASY EXECUTION SHALL PASS")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_trade(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        size: float,  # Position size in units
        price: float,  # Target price
        expected_return: float,  # Expected return in %
        volatility: float,  # Current volatility
        spread: float,  # Current bid/ask spread
        avg_daily_volume: float,  # Average daily volume
        latency_ms: float = None,  # Current latency
    ) -> RealismAdjustment:
        """
        Analyze a trade for realistic execution.
        
        Returns adjusted metrics accounting for all execution costs.
        """
        try:
            self.trades_analyzed += 1
            warnings = []
        
            # 1. Calculate slippage cost
            slippage_bps = self._estimate_slippage(volatility, size, avg_daily_volume)
            slippage_cost = slippage_bps / 10000  # Convert to decimal
        
            if slippage_bps > self.assumptions.max_slippage_bps:
                warnings.append(f"High slippage expected: {slippage_bps:.1f} bps")
        
            # 2. Calculate spread cost
            spread_bps = (spread / price) * 10000 if price > 0 else self.assumptions.expected_spread_bps
            spread_cost = spread_bps / 10000 / 2  # Half spread per side
        
            if spread_bps > self.assumptions.max_spread_bps:
                warnings.append(f"Wide spread: {spread_bps:.1f} bps")
        
            # 3. Calculate market impact
            trade_value = size * price
            impact_bps = self._estimate_market_impact(trade_value, avg_daily_volume, volatility)
            market_impact_cost = impact_bps / 10000
        
            if impact_bps > 10:
                warnings.append(f"Significant market impact: {impact_bps:.1f} bps")
        
            # 4. Calculate latency cost
            actual_latency = latency_ms or self.assumptions.expected_latency_ms
            latency_cost = self._estimate_latency_cost(actual_latency, volatility)
        
            if actual_latency > self.assumptions.max_latency_ms:
                warnings.append(f"High latency: {actual_latency:.0f}ms")
        
            # 5. Calculate commission cost
            commission_cost = self.assumptions.commission_per_trade / trade_value if trade_value > 0 else 0
        
            # 6. Total cost
            total_cost = slippage_cost + spread_cost + market_impact_cost + latency_cost + commission_cost
        
            # 7. Adjust returns
            adjusted_return = expected_return - (total_cost * 100)  # Convert to percentage
            return_haircut = total_cost * 100
        
            # 8. Adjust Sharpe (rough estimate)
            # Assume costs add to volatility
            cost_vol_addition = total_cost * math.sqrt(252)  # Annualized
            original_sharpe = expected_return / (volatility * 100) if volatility > 0 else 0
            adjusted_sharpe = adjusted_return / ((volatility * 100) + cost_vol_addition) if volatility > 0 else 0
        
            # 9. Adjust win rate (costs turn some winners into losers)
            # Assume normal distribution of returns
            original_win_rate = 0.5 + expected_return / (volatility * 100 * 2) if volatility > 0 else 0.5
            adjusted_win_rate = 0.5 + adjusted_return / (volatility * 100 * 2) if volatility > 0 else 0.5
            adjusted_win_rate = max(0, min(1, adjusted_win_rate))
        
            # 10. Determine execution quality
            quality = self._assess_quality(
                slippage_bps, spread_bps, impact_bps, actual_latency
            )
        
            # 11. Determine viability
            edge_after_costs = expected_return - return_haircut
            is_viable = (
                edge_after_costs >= self.assumptions.min_edge_after_costs_bps / 100 and
                quality != ExecutionQuality.UNACCEPTABLE and
                adjusted_return > 0
            )
        
            if not is_viable:
                self.trades_blocked += 1
                self.total_cost_saved += total_cost * trade_value
            
                if edge_after_costs < 0:
                    warnings.append(f"Negative edge after costs: {edge_after_costs:.2f}%")
                elif edge_after_costs < self.assumptions.min_edge_after_costs_bps / 100:
                    warnings.append(f"Insufficient edge: {edge_after_costs:.2f}% < {self.assumptions.min_edge_after_costs_bps/100:.2f}%")
        
            result = RealismAdjustment(
                adjusted_return=adjusted_return,
                adjusted_sharpe=adjusted_sharpe,
                adjusted_win_rate=adjusted_win_rate,
                slippage_cost=slippage_cost,
                spread_cost=spread_cost,
                commission_cost=commission_cost,
                market_impact_cost=market_impact_cost,
                latency_cost=latency_cost,
                total_cost=total_cost,
                return_haircut=return_haircut,
                quality=quality,
                is_viable=is_viable,
                warnings=warnings
            )
        
            if not is_viable:
                logger.warning(
                    f"EXECUTION REALISM GATE BLOCKED {symbol}: "
                    f"Expected={expected_return:.2f}%, After costs={adjusted_return:.2f}%, "
                    f"Total cost={total_cost*100:.2f}%"
                )
        
            return result
        except Exception as e:
            logger.error(f"Error in analyze_trade: {e}")
            raise
    
    def _estimate_slippage(
        self,
        volatility: float,
        size: float,
        avg_daily_volume: float
    ) -> float:
        """Estimate slippage in basis points"""
        # Base slippage from volatility
        try:
            vol_slippage = volatility * 100 * 0.1  # 10% of daily vol
        
            # Size-based slippage
            if avg_daily_volume > 0:
                participation_rate = size / avg_daily_volume
                size_slippage = participation_rate * 50  # 50 bps per 1% of ADV
            else:
                size_slippage = self.assumptions.expected_slippage_bps
        
            # Use historical if available
            if self.slippage_history:
                historical_avg = statistics.mean(self.slippage_history)
                return (vol_slippage + size_slippage + historical_avg) / 3
        
            return max(vol_slippage, size_slippage, self.assumptions.expected_slippage_bps)
        except Exception as e:
            logger.error(f"Error in _estimate_slippage: {e}")
            raise
    
    def _estimate_market_impact(
        self,
        trade_value: float,
        avg_daily_volume: float,
        volatility: float
    ) -> float:
        """Estimate market impact in basis points using square-root model"""
        try:
            if avg_daily_volume <= 0:
                return self.assumptions.market_impact_per_million
        
            # Square-root market impact model
            # Impact = sigma * sqrt(Q/V) where Q=order size, V=daily volume
            participation = trade_value / (avg_daily_volume * 100)  # Assuming $100 avg price
        
            if participation <= 0:
                return 0
        
            impact = volatility * 100 * math.sqrt(participation) * 10  # Scale factor
        
            return min(impact, 50)  # Cap at 50 bps
        except Exception as e:
            logger.error(f"Error in _estimate_market_impact: {e}")
            raise
    
    def _estimate_latency_cost(self, latency_ms: float, volatility: float) -> float:
        """Estimate cost of latency in decimal"""
        # Price can move during latency
        # Assume price moves at rate proportional to volatility
        
        # Daily vol to per-millisecond vol
        try:
            ms_per_day = 6.5 * 60 * 60 * 1000  # Trading hours in ms
            vol_per_ms = volatility / math.sqrt(ms_per_day)
        
            # Expected adverse move during latency
            expected_move = vol_per_ms * math.sqrt(latency_ms)
        
            return expected_move
        except Exception as e:
            logger.error(f"Error in _estimate_latency_cost: {e}")
            raise
    
    def _assess_quality(
        self,
        slippage_bps: float,
        spread_bps: float,
        impact_bps: float,
        latency_ms: float
    ) -> ExecutionQuality:
        """Assess overall execution quality"""
        try:
            score = 100
        
            # Slippage penalty
            if slippage_bps > self.assumptions.max_slippage_bps:
                score -= 30
            elif slippage_bps > self.assumptions.expected_slippage_bps:
                score -= 10
        
            # Spread penalty
            if spread_bps > self.assumptions.max_spread_bps:
                score -= 30
            elif spread_bps > self.assumptions.expected_spread_bps:
                score -= 10
        
            # Impact penalty
            if impact_bps > 20:
                score -= 20
            elif impact_bps > 10:
                score -= 10
        
            # Latency penalty
            if latency_ms > self.assumptions.max_latency_ms:
                score -= 20
            elif latency_ms > self.assumptions.expected_latency_ms:
                score -= 5
        
            if score >= 90:
                return ExecutionQuality.EXCELLENT
            elif score >= 70:
                return ExecutionQuality.GOOD
            elif score >= 50:
                return ExecutionQuality.FAIR
            elif score >= 30:
                return ExecutionQuality.POOR
            else:
                return ExecutionQuality.UNACCEPTABLE
        except Exception as e:
            logger.error(f"Error in _assess_quality: {e}")
            raise
    
    def record_execution(
        self,
        symbol: str,
        expected_price: float,
        actual_price: float,
        expected_size: float,
        filled_size: float,
        latency_ms: float
    ):
        """Record actual execution for calibration"""
        # Calculate actual slippage
        try:
            if expected_price > 0:
                actual_slippage_bps = abs(actual_price - expected_price) / expected_price * 10000
                self.slippage_history.append(actual_slippage_bps)
        
            # Calculate fill rate
            if expected_size > 0:
                fill_rate = filled_size / expected_size
                self.fill_rate_history.append(fill_rate)
        
            # Update symbol-specific history
            if symbol not in self.execution_history:
                self.execution_history[symbol] = deque(maxlen=100)
        
            self.execution_history[symbol].append({
                'timestamp': datetime.utcnow(),
                'slippage_bps': actual_slippage_bps if expected_price > 0 else 0,
                'fill_rate': fill_rate if expected_size > 0 else 1.0,
                'latency_ms': latency_ms
            })
        except Exception as e:
            logger.error(f"Error in record_execution: {e}")
            raise
    
    def get_symbol_stats(self, symbol: str) -> Dict[str, float]:
        """Get execution statistics for a symbol"""
        try:
            if symbol not in self.execution_history:
                return {
                    'avg_slippage_bps': self.assumptions.expected_slippage_bps,
                    'avg_fill_rate': self.assumptions.expected_fill_rate,
                    'avg_latency_ms': self.assumptions.expected_latency_ms
                }
        
            history = list(self.execution_history[symbol])
        
            return {
                'avg_slippage_bps': statistics.mean(h['slippage_bps'] for h in history),
                'avg_fill_rate': statistics.mean(h['fill_rate'] for h in history),
                'avg_latency_ms': statistics.mean(h['latency_ms'] for h in history),
                'sample_size': len(history)
            }
        except Exception as e:
            logger.error(f"Error in get_symbol_stats: {e}")
            raise
    
    def adjust_backtest_results(
        self,
        backtest_returns: float,
        backtest_sharpe: float,
        num_trades: int,
        avg_trade_size: float,
        avg_holding_period_days: float,
        volatility: float
    ) -> Dict[str, float]:
        """
        Adjust backtest results for realistic execution.
        
        This is the key function that prevents backtest delusion.
        """
        # Estimate round-trip costs per trade
        try:
            slippage_per_trade = self.assumptions.expected_slippage_bps / 10000 * 2  # Both sides
            spread_per_trade = self.assumptions.expected_spread_bps / 10000  # Full spread
            commission_per_trade = self.assumptions.commission_per_trade / (avg_trade_size * 100)  # Assuming $100 price
        
            total_cost_per_trade = slippage_per_trade + spread_per_trade + commission_per_trade
        
            # Total cost impact
            total_trades_cost = total_cost_per_trade * num_trades
        
            # Adjust returns
            adjusted_returns = backtest_returns - (total_trades_cost * 100)
        
            # Adjust Sharpe
            # Costs add to volatility and reduce returns
            cost_drag = total_trades_cost / (num_trades * avg_holding_period_days / 252) if num_trades > 0 else 0
            adjusted_sharpe = backtest_sharpe * (adjusted_returns / backtest_returns) if backtest_returns > 0 else 0
        
            # Reality factor (how much to discount backtest)
            reality_factor = adjusted_returns / backtest_returns if backtest_returns > 0 else 0
        
            return {
                'original_returns': backtest_returns,
                'adjusted_returns': adjusted_returns,
                'original_sharpe': backtest_sharpe,
                'adjusted_sharpe': adjusted_sharpe,
                'total_cost_pct': total_trades_cost * 100,
                'cost_per_trade_pct': total_cost_per_trade * 100,
                'reality_factor': reality_factor,
                'is_still_profitable': adjusted_returns > 0
            }
        except Exception as e:
            logger.error(f"Error in adjust_backtest_results: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics"""
        return {
            'trades_analyzed': self.trades_analyzed,
            'trades_blocked': self.trades_blocked,
            'block_rate': self.trades_blocked / max(self.trades_analyzed, 1),
            'total_cost_saved': self.total_cost_saved,
            'avg_slippage_bps': statistics.mean(self.slippage_history) if self.slippage_history else self.assumptions.expected_slippage_bps,
            'avg_fill_rate': statistics.mean(self.fill_rate_history) if self.fill_rate_history else self.assumptions.expected_fill_rate
        }
