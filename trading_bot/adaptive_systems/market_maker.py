"""
Advanced Market Making System with Adaptive Quoting
Based on Avellaneda-Stoikov model with dynamic adjustments
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy.stats import norm
import numpy
import pandas

logger = logging.getLogger(__name__)

@dataclass
class MarketMakingParameters:
    """Parameters for market making strategy"""
    gamma: float  # Risk aversion parameter
    k: float  # Order fill intensity parameter
    sigma: float  # Volatility estimate
    T: float  # Time horizon in seconds
    inventory_limit: int  # Maximum allowed inventory
    position_fade_time: float  # Time to reduce position (seconds)
    min_spread: float  # Minimum spread to quote
    max_spread: float  # Maximum spread to quote
    tick_size: float  # Minimum price increment
    lot_size: float  # Minimum quantity increment
    risk_limit: float  # Maximum risk exposure

@dataclass
class QuoteUpdate:
    """Market making quote update"""
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: datetime
    spread: float
    mid_price: float
    inventory_skew: float
    expected_pnl: float
    risk_metrics: Dict

class AdaptiveMarketMaker:
    """
    Advanced market making system with dynamic quote adjustment
    """
    
    def __init__(self, params: MarketMakingParameters):
        try:
            self.params = params
        
            # State variables
            self.inventory = 0
            self.position_value = 0
            self.last_mid_price = 0
            self.realized_pnl = 0
            self.unrealized_pnl = 0
        
            # Market state
            self.volatility_estimate = params.sigma
            self.spread_estimate = 0
            self.market_impact_estimate = 0
        
            # Performance tracking
            self.quote_history = []
            self.trade_history = []
            self.inventory_history = []
        
            # Risk metrics
            self.var_99 = 0
            self.expected_shortfall = 0
            self.inventory_cost = 0
        
            logger.info("Adaptive Market Maker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate_quotes(self, market_data: Dict) -> QuoteUpdate:
        """
        Generate optimal quotes using Avellaneda-Stoikov framework
        """
        # Extract market data
        try:
            mid_price = market_data.get('mid_price', self.last_mid_price)
            market_spread = market_data.get('spread', self.params.min_spread)
            market_vol = market_data.get('volatility', self.volatility_estimate)
        
            # Update state
            self.last_mid_price = mid_price
            self.volatility_estimate = self._update_volatility(market_vol)
        
            # Calculate optimal spread and skew
            base_spread = self._calculate_optimal_spread(market_spread)
            inventory_skew = self._calculate_inventory_skew()
        
            # Apply constraints
            spread = max(self.params.min_spread, min(base_spread, self.params.max_spread))
        
            # Calculate quote prices
            half_spread = spread / 2
            bid_price = self._round_price(mid_price - half_spread + inventory_skew)
            ask_price = self._round_price(mid_price + half_spread + inventory_skew)
        
            # Calculate quote sizes
            bid_size, ask_size = self._calculate_quote_sizes(spread)
        
            # Risk metrics
            risk_metrics = self._calculate_risk_metrics(mid_price)
        
            # Expected PnL
            expected_pnl = self._calculate_expected_pnl(bid_price, ask_price, bid_size, ask_size)
        
            quote = QuoteUpdate(
                bid_price=bid_price,
                ask_price=ask_price,
                bid_size=bid_size,
                ask_size=ask_size,
                timestamp=datetime.now(),
                spread=spread,
                mid_price=mid_price,
                inventory_skew=inventory_skew,
                expected_pnl=expected_pnl,
                risk_metrics=risk_metrics
            )
        
            self.quote_history.append(quote)
            return quote
        except Exception as e:
            logger.error(f"Error in generate_quotes: {e}")
            raise
    
    def update_position(self, trade: Dict):
        """
        Update position after trade execution
        """
        try:
            size = trade.get('size', 0)
            price = trade.get('price', self.last_mid_price)
            side = trade.get('side', 'buy')
        
            # Update inventory
            old_inventory = self.inventory
            if side == 'buy':
                self.inventory += size
            else:
                self.inventory -= size
        
            # Update PnL
            trade_pnl = self._calculate_trade_pnl(price, size, side)
            self.realized_pnl += trade_pnl
        
            # Update position value
            self.position_value = self.inventory * self.last_mid_price
        
            # Record trade
            self.trade_history.append({
                'timestamp': datetime.now(),
                'price': price,
                'size': size,
                'side': side,
                'inventory_before': old_inventory,
                'inventory_after': self.inventory,
                'pnl': trade_pnl
            })
        
            # Record inventory
            self.inventory_history.append({
                'timestamp': datetime.now(),
                'inventory': self.inventory,
                'position_value': self.position_value
            })
        
            logger.info(f"Position updated - Inventory: {self.inventory}, PnL: {self.realized_pnl:.2f}")
        except Exception as e:
            logger.error(f"Error in update_position: {e}")
            raise
    
    def _calculate_optimal_spread(self, market_spread: float) -> float:
        """
        Calculate optimal spread using Avellaneda-Stoikov formula
        """
        # Base spread from A-S model
        try:
            gamma = self.params.gamma
            sigma = self.volatility_estimate
            T = self.params.T
            k = self.params.k
        
            optimal_spread = (gamma * sigma**2 * T + 2/gamma * np.log(1 + gamma/k))
        
            # Adjust for market conditions
            market_adjustment = market_spread * 0.5  # Start at half market spread
            volatility_adjustment = sigma * np.sqrt(T) * 0.1
        
            # Combine components
            spread = optimal_spread + market_adjustment + volatility_adjustment
        
            return spread
        except Exception as e:
            logger.error(f"Error in _calculate_optimal_spread: {e}")
            raise
    
    def _calculate_inventory_skew(self) -> float:
        """
        Calculate price skew based on inventory position
        """
        # Basic inventory skew
        try:
            inventory_ratio = self.inventory / self.params.inventory_limit
            base_skew = -self.volatility_estimate * inventory_ratio
        
            # Time decay factor
            time_factor = np.exp(-self.params.T / self.params.position_fade_time)
        
            # Risk adjustment
            risk_factor = 1 + abs(inventory_ratio) * 0.5
        
            return base_skew * time_factor * risk_factor
        except Exception as e:
            logger.error(f"Error in _calculate_inventory_skew: {e}")
            raise
    
    def _calculate_quote_sizes(self, spread: float) -> Tuple[float, float]:
        """
        Calculate optimal quote sizes
        """
        try:
            base_size = self.params.lot_size * 10
        
            # Adjust for inventory
            inventory_ratio = self.inventory / self.params.inventory_limit
            inventory_factor = 1 - abs(inventory_ratio)
        
            # Adjust for spread
            spread_factor = min(1.0, self.params.min_spread / spread)
        
            # Calculate asymmetric sizes based on inventory
            if self.inventory > 0:
                # Long inventory - larger ask size
                ask_size = base_size * (1 + abs(inventory_ratio))
                bid_size = base_size * inventory_factor
            else:
                # Short inventory - larger bid size
                bid_size = base_size * (1 + abs(inventory_ratio))
                ask_size = base_size * inventory_factor
        
            # Apply spread factor
            bid_size *= spread_factor
            ask_size *= spread_factor
        
            # Round to lot size
            bid_size = self._round_size(bid_size)
            ask_size = self._round_size(ask_size)
        
            return bid_size, ask_size
        except Exception as e:
            logger.error(f"Error in _calculate_quote_sizes: {e}")
            raise
    
    def _calculate_risk_metrics(self, mid_price: float) -> Dict:
        """
        Calculate risk metrics for current position
        """
        try:
            position_value = self.inventory * mid_price
        
            # Value at Risk (99%)
            daily_vol = self.volatility_estimate * np.sqrt(252)
            self.var_99 = abs(position_value) * daily_vol * norm.ppf(0.99)
        
            # Expected Shortfall
            self.expected_shortfall = self.var_99 * 1.3  # Approximate ES
        
            # Inventory holding cost
            self.inventory_cost = abs(self.inventory) * self.volatility_estimate * mid_price * 0.1
        
            return {
                'var_99': self.var_99,
                'expected_shortfall': self.expected_shortfall,
                'inventory_cost': self.inventory_cost,
                'position_value': position_value,
                'utilization': abs(self.inventory) / self.params.inventory_limit
            }
        except Exception as e:
            logger.error(f"Error in _calculate_risk_metrics: {e}")
            raise
    
    def _calculate_expected_pnl(self, bid_price: float, ask_price: float,
                              bid_size: float, ask_size: float) -> float:
        """
        Calculate expected PnL for quotes
        """
        try:
            spread_pnl = (ask_price - bid_price) * min(bid_size, ask_size)
            inventory_cost = self.inventory_cost
            expected_fill_rate = 0.3  # Assumed fill rate
        
            return spread_pnl * expected_fill_rate - inventory_cost
        except Exception as e:
            logger.error(f"Error in _calculate_expected_pnl: {e}")
            raise
    
    def _calculate_trade_pnl(self, price: float, size: float, side: str) -> float:
        """
        Calculate PnL for a single trade
        """
        try:
            if side == 'buy':
                return -price * size  # Negative for buys
            else:
                return price * size  # Positive for sells
        except Exception as e:
            logger.error(f"Error in _calculate_trade_pnl: {e}")
            raise
    
    def _update_volatility(self, market_vol: float) -> float:
        """
        Update volatility estimate with exponential smoothing
        """
        try:
            alpha = 0.1  # Smoothing factor
            return alpha * market_vol + (1 - alpha) * self.volatility_estimate
        except Exception as e:
            logger.error(f"Error in _update_volatility: {e}")
            raise
    
    def _round_price(self, price: float) -> float:
        """Round price to nearest tick size"""
        return round(price / self.params.tick_size) * self.params.tick_size
    
    def _round_size(self, size: float) -> float:
        """Round size to nearest lot size"""
        return round(size / self.params.lot_size) * self.params.lot_size
    
    def get_market_making_stats(self) -> Dict:
        """
        Get current market making statistics
        """
        return {
            'inventory': self.inventory,
            'position_value': self.position_value,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'total_pnl': self.realized_pnl + self.unrealized_pnl,
            'risk_metrics': {
                'var_99': self.var_99,
                'expected_shortfall': self.expected_shortfall,
                'inventory_cost': self.inventory_cost
            },
            'quotes': {
                'last_spread': self.quote_history[-1].spread if self.quote_history else None,
                'last_skew': self.quote_history[-1].inventory_skew if self.quote_history else None
            },
            'market_state': {
                'volatility': self.volatility_estimate,
                'last_mid': self.last_mid_price
            }
        }
    
    def reset_position(self):
        """
        Reset position and metrics
        """
        try:
            self.inventory = 0
            self.position_value = 0
            self.realized_pnl = 0
            self.unrealized_pnl = 0
            self.quote_history = []
            self.trade_history = []
            self.inventory_history = []
            logger.info("Market maker position reset")
        except Exception as e:
            logger.error(f"Error in reset_position: {e}")
            raise
