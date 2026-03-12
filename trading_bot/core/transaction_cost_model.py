"""
Transaction Cost Model - Slippage, fees, and market impact modeling

This module provides comprehensive transaction cost modeling including
slippage estimation, fee calculation, and market impact analysis.
"""

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VenueType(Enum):
    """Venue types with different cost structures"""
    SPOT = 'spot'
    FUTURES = 'futures'
    OPTIONS = 'options'
    CFD = 'cfd'


@dataclass
class TransactionCost:
    """Transaction cost breakdown"""
    slippage_bps: float
    fee_bps: float
    market_impact_bps: float
    total_cost_bps: float
    expected_fill_price: float
    confidence: float = 0.8


class TransactionCostModel:
    """Model for estimating transaction costs"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Fee schedules by venue
            self.fee_schedules = self.config.get('fee_schedules', {
                'default': {'maker': 0.1, 'taker': 0.2},  # bps
            })
        
            # Slippage parameters
            self.slippage_params = self.config.get('slippage_params', {
                'base_slippage_bps': 0.5,
                'volatility_multiplier': 2.0,
                'size_impact_factor': 0.1
            })
        
            # Market impact parameters (Almgren-Chriss model)
            self.impact_params = self.config.get('impact_params', {
                'permanent_impact_coeff': 0.1,
                'temporary_impact_coeff': 0.5,
                'liquidity_factor': 1000000  # ADV in base currency
            })
        
            logger.info("Transaction cost model initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def estimate_cost(self, symbol: str, side: str, size: float, 
                     mid_price: float, spread_bps: float, 
                     volatility: float = 0.01, 
                     venue_id: str = 'default',
                     urgency: float = 0.5) -> TransactionCost:
        """
        Estimate total transaction cost
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            size: Order size in base currency
            mid_price: Current mid price
            spread_bps: Current spread in bps
            volatility: Realized volatility (daily)
            venue_id: Venue identifier
            urgency: Urgency factor (0-1, higher = more aggressive)
            
        Returns:
            TransactionCost object
        """
        # Calculate slippage
        try:
            slippage_bps = self._estimate_slippage(
                spread_bps, volatility, size, urgency
            )
        
            # Calculate fees
            fee_bps = self._calculate_fees(venue_id, urgency)
        
            # Calculate market impact
            impact_bps = self._estimate_market_impact(
                size, mid_price, volatility
            )
        
            # Total cost
            total_cost_bps = slippage_bps + fee_bps + impact_bps
        
            # Expected fill price
            cost_multiplier = 1 + (total_cost_bps / 10000)
            if side.lower() == 'buy':
                expected_fill = mid_price * cost_multiplier
            else:
                expected_fill = mid_price / cost_multiplier
        
            return TransactionCost(
                slippage_bps=slippage_bps,
                fee_bps=fee_bps,
                market_impact_bps=impact_bps,
                total_cost_bps=total_cost_bps,
                expected_fill_price=expected_fill,
                confidence=self._estimate_confidence(volatility, spread_bps)
            )
        except Exception as e:
            logger.error(f"Error in estimate_cost: {e}")
            raise
    
    def _estimate_slippage(self, spread_bps: float, volatility: float, 
                          size: float, urgency: float) -> float:
        """Estimate slippage in bps"""
        try:
            base_slippage = self.slippage_params['base_slippage_bps']
            vol_mult = self.slippage_params['volatility_multiplier']
            size_factor = self.slippage_params['size_impact_factor']
        
            # Base slippage from spread
            spread_slippage = spread_bps * urgency * 0.5
        
            # Volatility component
            vol_slippage = volatility * 10000 * vol_mult * urgency
        
            # Size impact
            size_slippage = size * size_factor * urgency
        
            return base_slippage + spread_slippage + vol_slippage + size_slippage
        except Exception as e:
            logger.error(f"Error in _estimate_slippage: {e}")
            raise
    
    def _calculate_fees(self, venue_id: str, urgency: float) -> float:
        """Calculate trading fees in bps"""
        try:
            schedule = self.fee_schedules.get(venue_id, self.fee_schedules['default'])
        
            # Use maker fee for passive orders, taker for aggressive
            if urgency < 0.3:
                return schedule.get('maker', 0.1)
            else:
                return schedule.get('taker', 0.2)
        except Exception as e:
            logger.error(f"Error in _calculate_fees: {e}")
            raise
    
    def _estimate_market_impact(self, size: float, price: float, 
                                volatility: float) -> float:
        """Estimate market impact using simplified Almgren-Chriss"""
        try:
            perm_coeff = self.impact_params['permanent_impact_coeff']
            temp_coeff = self.impact_params['temporary_impact_coeff']
            liquidity = self.impact_params['liquidity_factor']
        
            # Participation rate
            participation = size * price / liquidity
        
            # Permanent impact
            permanent = perm_coeff * participation * 10000
        
            # Temporary impact (depends on execution speed)
            temporary = temp_coeff * participation * volatility * 10000
        
            return permanent + temporary
        except Exception as e:
            logger.error(f"Error in _estimate_market_impact: {e}")
            raise
    
    def _estimate_confidence(self, volatility: float, spread_bps: float) -> float:
        """Estimate confidence in cost estimate"""
        # Lower confidence in high volatility or wide spreads
        try:
            vol_penalty = min(volatility * 100, 0.3)
            spread_penalty = min(spread_bps / 100, 0.3)
        
            return max(0.4, 1.0 - vol_penalty - spread_penalty)
        except Exception as e:
            logger.error(f"Error in _estimate_confidence: {e}")
            raise
    
    def adjust_size_for_cost(self, target_size: float, max_cost_bps: float,
                            estimated_cost: TransactionCost) -> float:
        """
        Adjust order size to stay within cost budget
        
        Args:
            target_size: Desired order size
            max_cost_bps: Maximum acceptable cost in bps
            estimated_cost: Estimated cost for target size
            
        Returns:
            Adjusted size
        """
        try:
            if estimated_cost.total_cost_bps <= max_cost_bps:
                return target_size
        
            # Scale down size proportionally
            scale_factor = max_cost_bps / estimated_cost.total_cost_bps
            adjusted_size = target_size * scale_factor * 0.9  # 10% safety margin
        
            logger.info(f"Adjusted size from {target_size:.2f} to {adjusted_size:.2f} "
                       f"to meet cost budget ({max_cost_bps:.1f} bps)")
        
            return adjusted_size
        except Exception as e:
            logger.error(f"Error in adjust_size_for_cost: {e}")
            raise
