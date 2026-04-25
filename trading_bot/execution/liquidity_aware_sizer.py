"""
Liquidity-Aware Position Sizer
Implements position sizing based on market liquidity and order book depth.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class OrderBookLevel:
    """Single level in order book"""
    price: float
    size: float
    side: str  # 'bid' or 'ask'


@dataclass
class MarketDepth:
    """Market depth information"""
    symbol: str
    timestamp: datetime
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    spread: float
    mid_price: float
    
    def get_liquidity_at_price(self, price: float, side: str) -> float:
        """Get available liquidity at specific price level"""
        levels = self.bids if side == 'buy' else self.asks
        
        total_liquidity = 0.0
        for level in levels:
            if side == 'buy' and level.price >= price:
                total_liquidity += level.size
            elif side == 'sell' and level.price <= price:
                total_liquidity += level.size
        
        return total_liquidity
    
    def get_average_price_for_size(self, size: float, side: str) -> Tuple[float, float]:
        """
        Calculate average execution price for given size.
        
        Returns:
            Tuple of (avg_price, slippage_bps)
        """
        levels = self.bids if side == 'sell' else self.asks
        
        remaining_size = size
        total_cost = 0.0
        filled_size = 0.0
        
        for level in levels:
            if remaining_size <= 0:
                break
            
            fill_size = min(remaining_size, level.size)
            total_cost += fill_size * level.price
            filled_size += fill_size
            remaining_size -= fill_size
        
        if filled_size == 0:
            return self.mid_price, float('inf')
        
        avg_price = total_cost / filled_size
        
        # Calculate slippage from mid
        if side == 'buy':
            slippage_bps = (avg_price - self.mid_price) / self.mid_price * 10000
        else:
            slippage_bps = (self.mid_price - avg_price) / self.mid_price * 10000
        
        return avg_price, slippage_bps


@dataclass
class ImpactModel:
    """Market impact model parameters"""
    temporary_impact_coeff: float = 0.1  # Temporary impact coefficient
    permanent_impact_coeff: float = 0.02  # Permanent impact coefficient
    decay_factor: float = 0.5  # Impact decay over time
    
    def estimate_impact(self, order_size: float, daily_volume: float, volatility: float) -> Dict[str, float]:
        """
        Estimate market impact of an order.
        
        Based on square-root model: impact = coeff * sigma * sqrt(order_size / volume)
        """
        participation_rate = order_size / daily_volume if daily_volume > 0 else 1.0
        
        # Square root impact model
        base_impact = volatility * np.sqrt(participation_rate)
        
        temporary_impact = self.temporary_impact_coeff * base_impact
        permanent_impact = self.permanent_impact_coeff * base_impact
        
        return {
            'temporary': temporary_impact,
            'permanent': permanent_impact,
            'total': temporary_impact + permanent_impact,
            'participation_rate': participation_rate
        }


class LiquidityAwareSizer:
    """
    Position sizer that considers market liquidity.
    
    Adjusts position sizes based on:
    - Order book depth
    - Market impact estimates
    - Maximum participation rates
    - Liquidity constraints
    """
    
    def __init__(self,
                 max_participation_rate: float = 0.05,  # Max 5% of daily volume
                 max_impact_bps: float = 10.0,  # Max 10 bps market impact
                 min_liquidity_ratio: float = 2.0,  # Need 2x position size in liquidity
                 impact_model: Optional[ImpactModel] = None):
        """
        Initialize liquidity-aware sizer.
        
        Args:
            max_participation_rate: Maximum participation in daily volume
            max_impact_bps: Maximum acceptable market impact in basis points
            min_liquidity_ratio: Minimum liquidity to position size ratio
            impact_model: Market impact model
        """
        self.max_participation_rate = max_participation_rate
        self.max_impact_bps = max_impact_bps
        self.min_liquidity_ratio = min_liquidity_ratio
        self.impact_model = impact_model or ImpactModel()
        
        # Tracking
        self.sizing_history: List[Dict] = []
        
        logger.info(f"LiquidityAwareSizer initialized: max_participation={max_participation_rate:.1%}")
    
    def calculate_position_size(self,
                             target_size: float,
                             symbol: str,
                             market_depth: MarketDepth,
                             daily_volume: float,
                             volatility: float,
                             side: str) -> Dict[str, Any]:
        """
        Calculate optimal position size considering liquidity.
        
        Args:
            target_size: Desired position size
            symbol: Trading symbol
            market_depth: Current market depth
            daily_volume: Daily trading volume
            volatility: Current volatility
            side: 'buy' or 'sell'
            
        Returns:
            Dictionary with sizing decision and rationale
        """
        constraints = []
        
        # 1. Check participation rate constraint
        max_size_participation = daily_volume * self.max_participation_rate
        
        if target_size > max_size_participation:
            constraints.append({
                'type': 'participation_rate',
                'limit': max_size_participation,
                'actual': target_size,
                'binding': True
            })
        
        # 2. Check market impact constraint
        impact = self.impact_model.estimate_impact(target_size, daily_volume, volatility)
        impact_bps = impact['total'] * 10000
        
        if impact_bps > self.max_impact_bps:
            # Scale down to meet impact constraint
            scale_factor = self.max_impact_bps / impact_bps
            max_size_impact = target_size * scale_factor
            
            constraints.append({
                'type': 'market_impact',
                'limit': max_size_impact,
                'actual': target_size,
                'impact_bps': impact_bps,
                'binding': True
            })
        else:
            max_size_impact = target_size
        
        # 3. Check liquidity depth constraint
        available_liquidity = market_depth.get_liquidity_at_price(
            market_depth.mid_price * 0.995 if side == 'buy' else market_depth.mid_price * 1.005,
            side
        )
        
        max_size_liquidity = available_liquidity / self.min_liquidity_ratio
        
        if target_size > max_size_liquidity:
            constraints.append({
                'type': 'liquidity_depth',
                'limit': max_size_liquidity,
                'actual': target_size,
                'available_liquidity': available_liquidity,
                'binding': True
            })
        
        # 4. Check order book slippage
        avg_price, slippage_bps = market_depth.get_average_price_for_size(target_size, side)
        
        if slippage_bps > self.max_impact_bps:
            # Find size that meets slippage constraint through binary search
            max_size_slippage = self._find_size_for_slippage(
                market_depth, side, self.max_impact_bps
            )
            
            constraints.append({
                'type': 'orderbook_slippage',
                'limit': max_size_slippage,
                'actual': target_size,
                'slippage_bps': slippage_bps,
                'binding': True
            })
        else:
            max_size_slippage = target_size
        
        # Determine final size (minimum of all constraints)
        final_size = min(
            target_size,
            max_size_participation,
            max_size_impact,
            max_size_liquidity,
            max_size_slippage
        )
        
        # Calculate actual impact with final size
        final_impact = self.impact_model.estimate_impact(final_size, daily_volume, volatility)
        final_slippage = market_depth.get_average_price_for_size(final_size, side)[1]
        
        # Record decision
        decision = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'target_size': target_size,
            'final_size': final_size,
            'constraints': constraints,
            'impact': {
                'temporary': final_impact['temporary'],
                'permanent': final_impact['permanent'],
                'participation_rate': final_impact['participation_rate']
            },
            'slippage_bps': final_slippage,
            'size_reduction': (target_size - final_size) / target_size if target_size > 0 else 0
        }
        
        self.sizing_history.append(decision)
        
        return decision
    
    def _find_size_for_slippage(self,
                               market_depth: MarketDepth,
                               side: str,
                               target_slippage: float,
                               tolerance: float = 0.5) -> float:
        """Find position size that results in target slippage using binary search"""
        low = 0.0
        high = market_depth.get_liquidity_at_price(
            market_depth.mid_price * 0.9 if side == 'buy' else market_depth.mid_price * 1.1,
            side
        )
        
        best_size = low
        
        for _ in range(20):  # Max iterations
            mid = (low + high) / 2.0
            _, slippage = market_depth.get_average_price_for_size(mid, side)
            
            if abs(slippage - target_slippage) < tolerance:
                return mid
            
            if slippage < target_slippage:
                best_size = mid
                low = mid
            else:
                high = mid
        
        return best_size
    
    def get_liquidity_statistics(self) -> Dict[str, Any]:
        """Get statistics about liquidity-based sizing"""
        if not self.sizing_history:
            return {}
        
        recent = self.sizing_history[-100:]  # Last 100 decisions
        
        constrained_count = sum(
            1 for d in recent if d['constraints']
        )
        
        avg_reduction = np.mean([
            d['size_reduction'] for d in recent
        ]) if recent else 0.0
        
        avg_slippage = np.mean([
            d['slippage_bps'] for d in recent
        ]) if recent else 0.0
        
        return {
            'total_decisions': len(self.sizing_history),
            'constrained_decisions': constrained_count,
            'constrained_rate': constrained_count / len(recent) if recent else 0,
            'avg_size_reduction': avg_reduction,
            'avg_slippage_bps': avg_slippage,
            'constraint_types': self._count_constraint_types(recent)
        }
    
    def _count_constraint_types(self, decisions: List[Dict]) -> Dict[str, int]:
        """Count frequency of each constraint type"""
        counts = {}
        
        for decision in decisions:
            for constraint in decision.get('constraints', []):
                c_type = constraint['type']
                counts[c_type] = counts.get(c_type, 0) + 1
        
        return counts


class ExecutionTimingOptimizer:
    """
    Optimizes execution timing based on market conditions.
    
    Considers:
    - Volatility forecasts
    - Volume patterns
    - Market impact timing
    - Execution windows
    """
    
    def __init__(self,
                 volatility_lookback: int = 20,
                 volume_profile_period: str = '1D',
                 optimal_volatility_range: Tuple[float, float] = (0.01, 0.03)):
        """
        Initialize execution timing optimizer.
        
        Args:
            volatility_lookback: Period for volatility calculation
            volume_profile_period: Period for volume pattern analysis
            optimal_volatility_range: Target volatility range for execution
        """
        self.volatility_lookback = volatility_lookback
        self.volume_profile_period = volume_profile_period
        self.optimal_volatility_range = optimal_volatility_range
        
        # Volume profiles (hour of day -> avg volume)
        self.volume_profiles: Dict[str, Dict[int, float]] = {}
        
        logger.info("ExecutionTimingOptimizer initialized")
    
    def forecast_volatility(self, returns: np.ndarray) -> float:
        """Simple volatility forecast based on recent data"""
        if len(returns) < self.volatility_lookback:
            return 0.0
        
        recent = returns[-self.volatility_lookback:]
        return np.std(recent) * np.sqrt(252)  # Annualized
    
    def is_optimal_execution_time(self,
                                 current_volatility: float,
                                 current_hour: int,
                                 symbol: str) -> Tuple[bool, float]:
        """
        Determine if current time is optimal for execution.
        
        Returns:
            Tuple of (is_optimal, score)
        """
        # Check volatility
        vol_min, vol_max = self.optimal_volatility_range
        vol_score = 1.0
        
        if current_volatility < vol_min:
            vol_score = 0.5  # Too calm, might lack liquidity
        elif current_volatility > vol_max:
            vol_score = 0.3  # Too volatile
        
        # Check volume profile
        volume_score = self._get_volume_score(current_hour, symbol)
        
        # Combined score
        total_score = (vol_score + volume_score) / 2.0
        is_optimal = total_score > 0.7
        
        return is_optimal, total_score
    
    def _get_volume_score(self, hour: int, symbol: str) -> float:
        """Get volume score for given hour (0-1, higher = better)"""
        if symbol not in self.volume_profiles:
            # Default: higher volume during market open/close
            if hour in [9, 10, 15, 16]:  # Market open/close hours
                return 1.0
            elif hour in [11, 12, 13, 14]:  # Mid-day
                return 0.7
            else:
                return 0.3
        
        profile = self.volume_profiles[symbol]
        hour_volume = profile.get(hour, np.mean(list(profile.values())))
        max_volume = max(profile.values()) if profile else 1.0
        
        return hour_volume / max_volume if max_volume > 0 else 0.5
    
    def update_volume_profile(self, symbol: str, trades: List[Dict]):
        """Update volume profile based on trade history"""
        hourly_volumes = {}
        
        for trade in trades:
            hour = trade['timestamp'].hour
            hourly_volumes[hour] = hourly_volumes.get(hour, 0) + trade['volume']
        
        # Normalize
        total = sum(hourly_volumes.values())
        if total > 0:
            hourly_volumes = {h: v/total for h, v in hourly_volumes.items()}
        
        self.volume_profiles[symbol] = hourly_volumes
    
    def calculate_optimal_execution_window(self,
                                         order_size: float,
                                         urgency: str = 'normal') -> timedelta:
        """
        Calculate optimal time window for execution.
        
        Args:
            order_size: Size of order to execute
            urgency: 'high', 'normal', or 'low'
            
        Returns:
            Recommended execution window
        """
        urgency_multipliers = {
            'high': 0.5,
            'normal': 1.0,
            'low': 2.0
        }
        
        multiplier = urgency_multipliers.get(urgency, 1.0)
        
        # Base window: larger orders need more time
        if order_size < 1000:
            base_window = timedelta(minutes=5)
        elif order_size < 10000:
            base_window = timedelta(minutes=15)
        elif order_size < 100000:
            base_window = timedelta(hours=1)
        else:
            base_window = timedelta(hours=4)
        
        return base_window * multiplier
    
    def recommend_execution_schedule(self,
                                   order_size: float,
                                   symbol: str,
                                  current_volatility: float,
                                   current_time: datetime) -> Dict[str, Any]:
        """
        Recommend execution schedule for an order.
        
        Returns:
            Dictionary with execution recommendations
        """
        # Check if now is good
        is_optimal, score = self.is_optimal_execution_time(
            current_volatility, current_time.hour, symbol
        )
        
        # Calculate window
        window = self.calculate_optimal_execution_window(order_size)
        
        recommendation = {
            'execute_now': is_optimal,
            'score': score,
            'recommended_window': window,
            'end_time': current_time + window,
            'rationale': []
        }
        
        if is_optimal:
            recommendation['rationale'].append('Current conditions are favorable')
        else:
            # Provide specific guidance
            vol_min, vol_max = self.optimal_volatility_range
            if current_volatility > vol_max:
                recommendation['rationale'].append(f'Volatility too high ({current_volatility:.2%}), wait for calmer conditions')
            elif current_volatility < vol_min:
                recommendation['rationale'].append(f'Volatility very low, may indicate low liquidity')
            
            volume_score = self._get_volume_score(current_time.hour, symbol)
            if volume_score < 0.5:
                recommendation['rationale'].append('Low volume period, consider waiting for higher volume')
        
        return recommendation
