"""
Market Making Strategy Module
Provides liquidity and captures bid-ask spreads
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import deque
import asyncio
import numpy
import pandas

logger = logging.getLogger(__name__)

class MakingStrategy(Enum):
    """Types of market making strategies"""
    PURE_SPREAD = "pure_spread"
    INVENTORY_BASED = "inventory_based"
    INFORMED = "informed"
    ADAPTIVE = "adaptive"
    HIGH_FREQUENCY = "high_frequency"

@dataclass
class MakingOpportunity:
    """Represents a market making opportunity"""
    opportunity_id: str
    symbol: str
    strategy_type: MakingStrategy
    bid_price: float
    ask_price: float
    spread: float
    expected_profit: float
    inventory_risk: float
    competition_level: float
    optimal_quotes: Dict[str, float]
    position_limits: Dict[str, float]
    execution_probability: float
    metadata: Dict[str, Any]

class MarketMakerStrategy:
    """
    Advanced market making with inventory management and risk control
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_spread = self.config.get('min_spread', 0.001)
            self.max_inventory = self.config.get('max_inventory', 100000)
            self.risk_aversion = self.config.get('risk_aversion', 0.5)
        
            # Inventory tracking
            self.inventory = {}
            self.inventory_history = {}
        
            # Market microstructure
            self.order_flow = {}
            self.quote_history = {}
            self.execution_stats = {}
        
            # Optimal quoting models
            self.avellaneda_stoikov_params = {}
            self.glosten_milgrom_params = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    async def find_making_opportunities(self, market_data: Dict) -> List[MakingOpportunity]:
        """
        Find profitable market making opportunities
        """
        try:
            opportunities = []
        
            for symbol, data in market_data.items():
                # Check if suitable for market making
                if not self._is_suitable_for_making(symbol, data):
                    continue
            
                # Calculate optimal quotes
                optimal_quotes = self._calculate_optimal_quotes(symbol, data)
            
                # Assess profitability
                profit_potential = self._estimate_profit(symbol, optimal_quotes, data)
            
                if profit_potential > self.min_spread * data['price']:
                    opportunity = self._create_making_opportunity(symbol, optimal_quotes, data)
                    opportunities.append(opportunity)
        
            return self._filter_opportunities(opportunities)
        except Exception as e:
            logger.error(f"Error in find_making_opportunities: {e}")
            raise
    
    def _is_suitable_for_making(self, symbol: str, data: Dict) -> bool:
        """Check if asset is suitable for market making"""
        # Check liquidity
        try:
            if data.get('volume', 0) < 100000:
                return False
        
            # Check spread
            current_spread = data.get('ask', 0) - data.get('bid', 0)
            if current_spread < self.min_spread * data['price']:
                return False
        
            # Check volatility (not too high)
            if data.get('volatility', 0) > 0.5:
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in _is_suitable_for_making: {e}")
            raise
    
    def _calculate_optimal_quotes(self, symbol: str, data: Dict) -> Dict[str, float]:
        """
        Calculate optimal bid/ask quotes using Avellaneda-Stoikov model
        """
        try:
            mid_price = (data['bid'] + data['ask']) / 2
        
            # Get or initialize parameters
            if symbol not in self.avellaneda_stoikov_params:
                self._calibrate_as_model(symbol, data)
        
            params = self.avellaneda_stoikov_params.get(symbol, {})
        
            # Current inventory
            current_inv = self.inventory.get(symbol, 0)
        
            # Reservation price (adjusted for inventory)
            sigma = data.get('volatility', 0.01)
            gamma = self.risk_aversion
            T = 1.0  # Time horizon
            q = current_inv / self.max_inventory if self.max_inventory > 0 else 0
        
            reservation_price = mid_price - q * gamma * sigma**2 * T
        
            # Optimal spread
            kappa = params.get('kappa', 1.5)  # Order arrival rate
            optimal_spread = gamma * sigma**2 * T + (2/gamma) * np.log(1 + gamma/kappa)
        
            # Calculate quotes
            half_spread = optimal_spread / 2
        
            optimal_quotes = {
                'bid': reservation_price - half_spread,
                'ask': reservation_price + half_spread,
                'mid': reservation_price,
                'spread': optimal_spread
            }
        
            # Adjust for tick size
            tick_size = data.get('tick_size', 0.01)
            optimal_quotes['bid'] = np.floor(optimal_quotes['bid'] / tick_size) * tick_size
            optimal_quotes['ask'] = np.ceil(optimal_quotes['ask'] / tick_size) * tick_size
        
            return optimal_quotes
        except Exception as e:
            logger.error(f"Error in _calculate_optimal_quotes: {e}")
            raise
    
    def _calibrate_as_model(self, symbol: str, data: Dict):
        """Calibrate Avellaneda-Stoikov model parameters"""
        # Estimate order arrival rate (kappa)
        try:
            volume = data.get('volume', 100000)
            avg_trade_size = data.get('avg_trade_size', 100)
        
            kappa = volume / avg_trade_size / 3600  # Per second
        
            # Estimate price impact (lambda)
            lambda_param = 0.1 / volume  # Simplified
        
            self.avellaneda_stoikov_params[symbol] = {
                'kappa': kappa,
                'lambda': lambda_param,
                'calibrated_at': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error in _calibrate_as_model: {e}")
            raise
    
    def _estimate_profit(self, symbol: str, quotes: Dict, data: Dict) -> float:
        """Estimate expected profit from market making"""
        try:
            spread = quotes['spread']
        
            # Estimate fill probability
            fill_prob = self._estimate_fill_probability(symbol, quotes, data)
        
            # Expected number of round trips per hour
            volume = data.get('volume', 100000)
            market_share = 0.01  # Assume 1% market share
            round_trips = volume * market_share / 2 / 24  # Per hour
        
            # Expected profit per round trip
            profit_per_trip = spread * data['price'] - self._estimate_costs(data)
        
            # Total expected profit
            expected_profit = round_trips * profit_per_trip * fill_prob
        
            return expected_profit
        except Exception as e:
            logger.error(f"Error in _estimate_profit: {e}")
            raise
    
    def _estimate_fill_probability(self, symbol: str, quotes: Dict, data: Dict) -> float:
        """Estimate probability of fills at quoted prices"""
        # Distance from mid
        try:
            mid = (data['bid'] + data['ask']) / 2
            bid_distance = abs(quotes['bid'] - mid) / mid
            ask_distance = abs(quotes['ask'] - mid) / mid
        
            # Exponential decay based on distance
            bid_fill = np.exp(-bid_distance * 100)
            ask_fill = np.exp(-ask_distance * 100)
        
            # Average fill probability
            return (bid_fill + ask_fill) / 2
        except Exception as e:
            logger.error(f"Error in _estimate_fill_probability: {e}")
            raise
    
    def _estimate_costs(self, data: Dict) -> float:
        """Estimate costs (fees, slippage, etc.)"""
        try:
            price = data['price']
        
            # Trading fees
            fees = price * 0.0002  # 2 bps
        
            # Adverse selection cost
            adverse_selection = price * 0.0001
        
            # Inventory holding cost
            holding_cost = price * 0.00005
        
            return fees + adverse_selection + holding_cost
        except Exception as e:
            logger.error(f"Error in _estimate_costs: {e}")
            raise
    
    def _create_making_opportunity(self, symbol: str, quotes: Dict, data: Dict) -> MakingOpportunity:
        """Create market making opportunity"""
        return MakingOpportunity(
            opportunity_id=f"MM_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            strategy_type=MakingStrategy.ADAPTIVE,
            bid_price=quotes['bid'],
            ask_price=quotes['ask'],
            spread=quotes['spread'],
            expected_profit=self._estimate_profit(symbol, quotes, data),
            inventory_risk=self._calculate_inventory_risk(symbol),
            competition_level=self._assess_competition(symbol, data),
            optimal_quotes=quotes,
            position_limits=self._calculate_position_limits(symbol, data),
            execution_probability=self._estimate_fill_probability(symbol, quotes, data),
            metadata={
                'volatility': data.get('volatility', 0),
                'volume': data.get('volume', 0),
                'current_inventory': self.inventory.get(symbol, 0),
                'risk_aversion': self.risk_aversion
            }
        )
    
    def _calculate_inventory_risk(self, symbol: str) -> float:
        """Calculate inventory risk score"""
        try:
            current_inv = abs(self.inventory.get(symbol, 0))
        
            if self.max_inventory == 0:
                return 0
        
            # Risk increases non-linearly with inventory
            inv_ratio = current_inv / self.max_inventory
            risk = inv_ratio ** 2
        
            return min(1.0, risk)
        except Exception as e:
            logger.error(f"Error in _calculate_inventory_risk: {e}")
            raise
    
    def _assess_competition(self, symbol: str, data: Dict) -> float:
        """Assess level of competition from other market makers"""
        # Tightness of spread indicates competition
        try:
            spread = data.get('ask', 0) - data.get('bid', 0)
            price = data['price']
        
            if price == 0:
                return 0.5
        
            spread_bps = (spread / price) * 10000
        
            if spread_bps < 5:
                return 0.9  # Very high competition
            elif spread_bps < 10:
                return 0.7
            elif spread_bps < 20:
                return 0.5
            else:
                return 0.3  # Low competition
        except Exception as e:
            logger.error(f"Error in _assess_competition: {e}")
            raise
    
    def _calculate_position_limits(self, symbol: str, data: Dict) -> Dict[str, float]:
        """Calculate position limits for risk management"""
        try:
            price = data['price']
            volatility = data.get('volatility', 0.01)
            volume = data.get('volume', 100000)
        
            # Base limit on volume
            volume_limit = volume * 0.01  # 1% of daily volume
        
            # Adjust for volatility
            vol_adjustment = 1 / (1 + volatility * 10)
        
            # Dollar limits
            max_position = min(
                self.max_inventory,
                volume_limit * vol_adjustment
            )
        
            return {
                'max_long': max_position,
                'max_short': max_position,
                'max_order_size': max_position * 0.1,
                'max_dollar_exposure': max_position * price
            }
        except Exception as e:
            logger.error(f"Error in _calculate_position_limits: {e}")
            raise
    
    def _filter_opportunities(self, opportunities: List[MakingOpportunity]) -> List[MakingOpportunity]:
        """Filter and rank market making opportunities"""
        try:
            filtered = []
        
            for opp in opportunities:
                # Filter by minimum profit
                if opp.expected_profit < 10:  # $10 minimum
                    continue
            
                # Filter by inventory risk
                if opp.inventory_risk > 0.8:
                    continue
            
                # Filter by execution probability
                if opp.execution_probability < 0.3:
                    continue
            
                filtered.append(opp)
        
            # Sort by risk-adjusted profit
            return sorted(filtered, 
                         key=lambda x: x.expected_profit * (1 - x.inventory_risk), 
                         reverse=True)
        except Exception as e:
            logger.error(f"Error in _filter_opportunities: {e}")
            raise


class SpreadCapture:
    """
    Captures bid-ask spreads with advanced execution
    """
    
    def __init__(self):
        try:
            self.spread_targets = {}
            self.execution_algos = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_spread_capture(self, order_book: Dict) -> Dict:
        """Calculate potential spread capture"""
        try:
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
        
            if not bids or not asks:
                return {}
        
            # Best bid-ask spread
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            spread = best_ask - best_bid
        
            # Calculate weighted mid-price
            bid_volume = sum(b[1] for b in bids[:5])
            ask_volume = sum(a[1] for a in asks[:5])
        
            if bid_volume + ask_volume > 0:
                weighted_mid = (best_bid * ask_volume + best_ask * bid_volume) / (bid_volume + ask_volume)
            else:
                weighted_mid = (best_bid + best_ask) / 2
        
            return {
                'spread': spread,
                'mid_price': weighted_mid,
                'capture_potential': spread * 0.4,  # Assume 40% capture
                'bid_depth': bid_volume,
                'ask_depth': ask_volume
            }
        except Exception as e:
            logger.error(f"Error in calculate_spread_capture: {e}")
            raise


class LiquidityProvider:
    """
    Provides liquidity with sophisticated models
    """
    
    def __init__(self):
        try:
            self.liquidity_models = {}
            self.provision_strategies = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def optimize_liquidity_provision(self, symbol: str, market_data: Dict) -> Dict:
        """
        Optimize liquidity provision strategy
        """
        # Glosten-Milgrom model for informed trading
        try:
            informed_prob = self._estimate_informed_trading(market_data)
        
            # Kyle model for price impact
            price_impact = self._estimate_price_impact(market_data)
        
            # Optimal provision strategy
            strategy = {
                'quote_size': self._optimal_quote_size(market_data, informed_prob),
                'quote_frequency': self._optimal_quote_frequency(market_data),
                'spread_adjustment': self._spread_adjustment(informed_prob, price_impact),
                'passive_aggressive_ratio': self._passive_aggressive_mix(market_data)
            }
        
            return strategy
        except Exception as e:
            logger.error(f"Error in optimize_liquidity_provision: {e}")
            raise
    
    def _estimate_informed_trading(self, market_data: Dict) -> float:
        """Estimate probability of informed trading (PIN)"""
        # Simplified PIN model
        try:
            trades = market_data.get('trades', [])
        
            if not trades:
                return 0.1  # Default
        
            # Analyze trade imbalance
            buys = sum(1 for t in trades if t.get('side') == 'buy')
            sells = len(trades) - buys
        
            imbalance = abs(buys - sells) / len(trades) if len(trades) > 0 else 0
        
            # Higher imbalance suggests informed trading
            return min(0.5, imbalance)
        except Exception as e:
            logger.error(f"Error in _estimate_informed_trading: {e}")
            raise
    
    def _estimate_price_impact(self, market_data: Dict) -> float:
        """Estimate price impact using Kyle's lambda"""
        try:
            volume = market_data.get('volume', 100000)
            volatility = market_data.get('volatility', 0.01)
        
            # Kyle's lambda (simplified)
            lambda_kyle = volatility / np.sqrt(volume)
        
            return lambda_kyle
        except Exception as e:
            logger.error(f"Error in _estimate_price_impact: {e}")
            raise
    
    def _optimal_quote_size(self, market_data: Dict, informed_prob: float) -> float:
        """Calculate optimal quote size"""
        try:
            avg_trade_size = market_data.get('avg_trade_size', 100)
        
            # Reduce size when informed trading is likely
            size_adjustment = 1 - informed_prob
        
            return avg_trade_size * size_adjustment
        except Exception as e:
            logger.error(f"Error in _optimal_quote_size: {e}")
            raise
    
    def _optimal_quote_frequency(self, market_data: Dict) -> float:
        """Calculate optimal quoting frequency"""
        try:
            volatility = market_data.get('volatility', 0.01)
        
            # Higher volatility requires more frequent updates
            base_frequency = 1.0  # Per second
            vol_adjustment = 1 + volatility * 10
        
            return base_frequency * vol_adjustment
        except Exception as e:
            logger.error(f"Error in _optimal_quote_frequency: {e}")
            raise
    
    def _spread_adjustment(self, informed_prob: float, price_impact: float) -> float:
        """Adjust spread based on market conditions"""
        # Wider spread for informed trading
        try:
            informed_adjustment = 1 + informed_prob
        
            # Wider spread for high price impact
            impact_adjustment = 1 + price_impact * 100
        
            return informed_adjustment * impact_adjustment
        except Exception as e:
            logger.error(f"Error in _spread_adjustment: {e}")
            raise
    
    def _passive_aggressive_mix(self, market_data: Dict) -> float:
        """Determine mix of passive vs aggressive orders"""
        try:
            spread = market_data.get('spread', 0.01)
            volatility = market_data.get('volatility', 0.01)
        
            # More aggressive in tight spreads
            if spread < 0.001:
                return 0.7  # 70% aggressive
            # More passive in volatile markets
            elif volatility > 0.03:
                return 0.3  # 30% aggressive
            else:
                return 0.5  # Balanced
        except Exception as e:
            logger.error(f"Error in _passive_aggressive_mix: {e}")
            raise


class OrderBookImbalance:
    """
    Detects and trades order book imbalances
    """
    
    def __init__(self):
        try:
            self.imbalance_threshold = 0.6
            self.imbalance_history = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def detect_imbalances(self, order_book: Dict) -> Dict:
        """
        Detect order book imbalances that predict price movement
        """
        try:
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
        
            if not bids or not asks:
                return {}
        
            # Calculate volume imbalance at different levels
            imbalances = {}
        
            for level in [1, 5, 10]:
                bid_volume = sum(b[1] for b in bids[:level])
                ask_volume = sum(a[1] for a in asks[:level])
            
                total_volume = bid_volume + ask_volume
                if total_volume > 0:
                    imbalance = (bid_volume - ask_volume) / total_volume
                    imbalances[f'level_{level}'] = imbalance
        
            # Calculate pressure metrics
            bid_pressure = self._calculate_pressure(bids)
            ask_pressure = self._calculate_pressure(asks)
        
            # Predict direction
            net_pressure = bid_pressure - ask_pressure
            predicted_direction = 'BUY' if net_pressure > self.imbalance_threshold else \
                                'SELL' if net_pressure < -self.imbalance_threshold else 'NEUTRAL'
        
            return {
                'imbalances': imbalances,
                'bid_pressure': bid_pressure,
                'ask_pressure': ask_pressure,
                'net_pressure': net_pressure,
                'predicted_direction': predicted_direction,
                'confidence': abs(net_pressure)
            }
        except Exception as e:
            logger.error(f"Error in detect_imbalances: {e}")
            raise
    
    def _calculate_pressure(self, orders: List) -> float:
        """Calculate order book pressure"""
        try:
            if not orders:
                return 0
        
            # Weight by price proximity
            best_price = orders[0][0]
            weighted_volume = 0
            total_weight = 0
        
            for price, volume in orders[:20]:
                # Exponential decay weight
                distance = abs(price - best_price) / best_price
                weight = np.exp(-distance * 100)
            
                weighted_volume += volume * weight
                total_weight += weight
        
            if total_weight > 0:
                return weighted_volume / total_weight
        
            return 0
        except Exception as e:
            logger.error(f"Error in _calculate_pressure: {e}")
            raise
