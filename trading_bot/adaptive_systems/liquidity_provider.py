"""
Advanced Liquidity Provision System
Provides intelligent liquidity across multiple venues with dynamic adjustments
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy.optimize import minimize
import numpy
import pandas

logger = logging.getLogger(__name__)

@dataclass
class LiquidityParameters:
    """Parameters for liquidity provision"""
    max_position: float  # Maximum position size
    max_risk: float  # Maximum risk exposure
    min_spread: float  # Minimum spread to quote
    max_spread: float  # Maximum spread to quote
    tick_size: float  # Minimum price increment
    lot_size: float  # Minimum quantity increment
    risk_limit: float  # Maximum risk exposure
    capital: float  # Available capital
    target_utilization: float  # Target capital utilization
    rebalance_threshold: float  # Position rebalance threshold

@dataclass
class LiquidityQuote:
    """Liquidity quote for a venue"""
    venue: str
    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: datetime
    spread: float
    mid_price: float
    expected_edge: float
    risk_metrics: Dict

class LiquidityProvider:
    """
    Advanced liquidity provision system with cross-venue optimization
    """
    
    def __init__(self, params: LiquidityParameters):
        self.params = params
        
        # Position tracking
        self.positions = {}  # venue -> symbol -> position
        self.total_exposure = 0
        self.capital_utilized = 0
        
        # Risk tracking
        self.position_risks = {}
        self.total_risk = 0
        self.var_99 = 0
        
        # Performance tracking
        self.quotes = {}  # venue -> symbol -> quote
        self.trades = []
        self.metrics = {}
        
        # Market state
        self.venue_stats = {}
        self.symbol_stats = {}
        
        logger.info("Liquidity Provider initialized")
    
    def optimize_liquidity(self, market_data: Dict) -> Dict[str, List[LiquidityQuote]]:
        """
        Optimize liquidity provision across venues
        """
        quotes_by_venue = {}
        
        # Get available venues and symbols
        venues = market_data.keys()
        
        for venue in venues:
            venue_data = market_data[venue]
            venue_quotes = []
            
            # Update venue statistics
            self._update_venue_stats(venue, venue_data)
            
            for symbol, symbol_data in venue_data.items():
                # Update symbol statistics
                self._update_symbol_stats(symbol, symbol_data)
                
                # Generate optimal quotes
                quote = self._generate_optimal_quote(venue, symbol, symbol_data)
                
                if quote:
                    venue_quotes.append(quote)
                    self.quotes[venue] = self.quotes.get(venue, {})
                    self.quotes[venue][symbol] = quote
            
            quotes_by_venue[venue] = venue_quotes
        
        # Cross-venue position optimization
        self._optimize_cross_venue_positions()
        
        return quotes_by_venue
    
    def _generate_optimal_quote(self, venue: str, symbol: str, 
                              market_data: Dict) -> Optional[LiquidityQuote]:
        """
        Generate optimal quotes for a symbol on a venue
        """
        try:
            # Extract market data
            mid_price = market_data.get('mid_price', 0)
            market_spread = market_data.get('spread', self.params.min_spread)
            volume = market_data.get('volume', 0)
            volatility = market_data.get('volatility', 0)
            
            if mid_price == 0:
                return None
            
            # Calculate optimal spread
            spread = self._calculate_optimal_spread(
                market_spread,
                volatility,
                volume,
                venue,
                symbol
            )
            
            # Calculate position adjustments
            position = self.positions.get(venue, {}).get(symbol, 0)
            position_adjustment = self._calculate_position_adjustment(position)
            
            # Calculate quote sizes
            bid_size, ask_size = self._calculate_quote_sizes(
                venue,
                symbol,
                spread,
                position
            )
            
            # Calculate final prices
            half_spread = spread / 2
            bid_price = self._round_price(mid_price - half_spread + position_adjustment)
            ask_price = self._round_price(mid_price + half_spread + position_adjustment)
            
            # Calculate expected edge
            expected_edge = self._calculate_expected_edge(
                spread,
                market_spread,
                volume,
                volatility
            )
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(
                venue,
                symbol,
                bid_size,
                ask_size,
                mid_price
            )
            
            return LiquidityQuote(
                venue=venue,
                symbol=symbol,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_size=bid_size,
                ask_size=ask_size,
                timestamp=datetime.now(),
                spread=spread,
                mid_price=mid_price,
                expected_edge=expected_edge,
                risk_metrics=risk_metrics
            )
            
        except Exception as e:
            logger.error(f"Error generating quote for {symbol} on {venue}: {e}")
            return None
    
    def _calculate_optimal_spread(self, market_spread: float, volatility: float,
                                volume: float, venue: str, symbol: str) -> float:
        """
        Calculate optimal spread based on market conditions
        """
        # Base spread from market
        base_spread = market_spread * 1.1  # Start slightly wider
        
        # Volatility component
        vol_spread = volatility * np.sqrt(252) * 0.1
        
        # Volume component (tighter spreads for higher volume)
        volume_factor = max(0.5, min(1.0, 1000 / volume)) if volume > 0 else 1.0
        
        # Position component
        position = self.positions.get(venue, {}).get(symbol, 0)
        position_factor = 1 + abs(position / self.params.max_position) * 0.5
        
        # Risk component
        risk_factor = 1 + self.total_risk / self.params.risk_limit * 0.5
        
        # Combine components
        spread = (base_spread + vol_spread) * volume_factor * position_factor * risk_factor
        
        # Apply constraints
        spread = max(self.params.min_spread, min(spread, self.params.max_spread))
        
        return self._round_price(spread)
    
    def _calculate_position_adjustment(self, position: float) -> float:
        """
        Calculate price adjustment based on position
        """
        # Linear adjustment based on position utilization
        position_util = position / self.params.max_position
        base_adjustment = position_util * self.params.min_spread
        
        # Risk-based scaling
        risk_scale = 1 + (self.total_risk / self.params.risk_limit) * 0.5
        
        # Capital utilization impact
        capital_scale = 1 + (self.capital_utilized / self.params.capital) * 0.3
        
        return base_adjustment * risk_scale * capital_scale
    
    def _calculate_quote_sizes(self, venue: str, symbol: str, 
                             spread: float, position: float) -> Tuple[float, float]:
        """
        Calculate optimal quote sizes
        """
        # Base size calculation
        base_size = self.params.lot_size * 5
        
        # Available risk capacity
        risk_capacity = max(0, self.params.risk_limit - self.total_risk)
        risk_factor = risk_capacity / self.params.risk_limit
        
        # Position utilization
        position_util = abs(position) / self.params.max_position
        position_factor = 1 - position_util
        
        # Spread impact
        spread_factor = min(1.0, self.params.min_spread / spread)
        
        # Calculate asymmetric sizes based on position
        if position > 0:
            # Long position - larger ask size
            ask_size = base_size * (1 + position_util)
            bid_size = base_size * position_factor
        else:
            # Short position - larger bid size
            bid_size = base_size * (1 + abs(position_util))
            ask_size = base_size * position_factor
        
        # Apply factors
        bid_size *= risk_factor * spread_factor
        ask_size *= risk_factor * spread_factor
        
        # Round to lot size
        bid_size = self._round_size(bid_size)
        ask_size = self._round_size(ask_size)
        
        return bid_size, ask_size
    
    def _calculate_expected_edge(self, quote_spread: float, market_spread: float,
                               volume: float, volatility: float) -> float:
        """
        Calculate expected edge (profit) for quotes
        """
        # Spread capture
        spread_edge = (quote_spread - market_spread) / 2
        
        # Volume-based probability of execution
        exec_prob = max(0.1, min(0.8, 1000 / volume)) if volume > 0 else 0.1
        
        # Volatility impact
        vol_cost = volatility * np.sqrt(252) * 0.05
        
        # Net expected edge
        return spread_edge * exec_prob - vol_cost
    
    def _calculate_risk_metrics(self, venue: str, symbol: str,
                              bid_size: float, ask_size: float,
                              mid_price: float) -> Dict:
        """
        Calculate risk metrics for quotes
        """
        # Current position risk
        position = self.positions.get(venue, {}).get(symbol, 0)
        position_value = position * mid_price
        
        # New position scenarios
        max_long = position + bid_size
        max_short = position - ask_size
        
        # Value at Risk
        daily_vol = self.symbol_stats.get(symbol, {}).get('volatility', 0.02)
        var_99 = abs(position_value) * daily_vol * 2.33  # 99% VaR
        
        # Stress test
        stress_loss = abs(position_value) * 0.1  # 10% adverse move
        
        return {
            'position_value': position_value,
            'max_long_value': max_long * mid_price,
            'max_short_value': max_short * mid_price,
            'var_99': var_99,
            'stress_loss': stress_loss,
            'capital_utilization': abs(position_value) / self.params.capital
        }
    
    def _optimize_cross_venue_positions(self):
        """
        Optimize positions across venues
        """
        # Aggregate positions by symbol
        symbol_positions = {}
        for venue_pos in self.positions.values():
            for symbol, pos in venue_pos.items():
                symbol_positions[symbol] = symbol_positions.get(symbol, 0) + pos
        
        # Check for rebalancing needs
        for symbol, total_pos in symbol_positions.items():
            if abs(total_pos) > self.params.max_position * self.params.rebalance_threshold:
                self._trigger_rebalancing(symbol, total_pos)
    
    def _trigger_rebalancing(self, symbol: str, total_position: float):
        """
        Trigger position rebalancing across venues
        """
        logger.info(f"Triggering rebalancing for {symbol} - Position: {total_position}")
        
        # Calculate target position by venue
        venues = [v for v in self.quotes.keys() if symbol in self.quotes[v]]
        if not venues:
            return
        
        # Simple equal distribution for now
        target_per_venue = total_position / len(venues)
        
        for venue in venues:
            current_pos = self.positions.get(venue, {}).get(symbol, 0)
            delta = target_per_venue - current_pos
            
            if abs(delta) > self.params.lot_size:
                logger.info(f"Venue {venue} needs adjustment of {delta}")
                # Actual rebalancing would be implemented by the execution engine
    
    def update_position(self, venue: str, trade: Dict):
        """
        Update position after trade execution
        """
        symbol = trade.get('symbol')
        size = trade.get('size', 0)
        price = trade.get('price', 0)
        side = trade.get('side', 'buy')
        
        # Initialize venue if needed
        if venue not in self.positions:
            self.positions[venue] = {}
        
        # Update position
        old_pos = self.positions[venue].get(symbol, 0)
        if side == 'buy':
            self.positions[venue][symbol] = old_pos + size
        else:
            self.positions[venue][symbol] = old_pos - size
        
        # Update metrics
        self._update_metrics(venue, symbol, trade)
        
        # Record trade
        self.trades.append({
            'venue': venue,
            'symbol': symbol,
            'price': price,
            'size': size,
            'side': side,
            'timestamp': datetime.now()
        })
        
        logger.info(f"Position updated - {venue} {symbol}: {self.positions[venue][symbol]}")
    
    def _update_metrics(self, venue: str, symbol: str, trade: Dict):
        """
        Update trading metrics
        """
        if venue not in self.metrics:
            self.metrics[venue] = {}
        
        if symbol not in self.metrics[venue]:
            self.metrics[venue][symbol] = {
                'volume': 0,
                'value': 0,
                'trades': 0,
                'fees': 0
            }
        
        metrics = self.metrics[venue][symbol]
        metrics['volume'] += trade.get('size', 0)
        metrics['value'] += trade.get('size', 0) * trade.get('price', 0)
        metrics['trades'] += 1
        metrics['fees'] += trade.get('fees', 0)
    
    def _update_venue_stats(self, venue: str, venue_data: Dict):
        """
        Update venue statistics
        """
        if venue not in self.venue_stats:
            self.venue_stats[venue] = {
                'volume': 0,
                'trades': 0,
                'active_symbols': 0
            }
        
        stats = self.venue_stats[venue]
        stats['active_symbols'] = len(venue_data)
        
        # Aggregate volume and trades
        total_volume = 0
        total_trades = 0
        for symbol_data in venue_data.values():
            total_volume += symbol_data.get('volume', 0)
            total_trades += symbol_data.get('trade_count', 0)
        
        stats['volume'] = total_volume
        stats['trades'] = total_trades
    
    def _update_symbol_stats(self, symbol: str, symbol_data: Dict):
        """
        Update symbol statistics
        """
        if symbol not in self.symbol_stats:
            self.symbol_stats[symbol] = {
                'volatility': 0,
                'avg_spread': 0,
                'avg_volume': 0
            }
        
        stats = self.symbol_stats[symbol]
        
        # Exponential moving average updates
        alpha = 0.1  # Smoothing factor
        
        stats['volatility'] = (alpha * symbol_data.get('volatility', stats['volatility']) +
                             (1 - alpha) * stats['volatility'])
        
        stats['avg_spread'] = (alpha * symbol_data.get('spread', stats['avg_spread']) +
                             (1 - alpha) * stats['avg_spread'])
        
        stats['avg_volume'] = (alpha * symbol_data.get('volume', stats['avg_volume']) +
                             (1 - alpha) * stats['avg_volume'])
    
    def _round_price(self, price: float) -> float:
        """Round price to nearest tick size"""
        return round(price / self.params.tick_size) * self.params.tick_size
    
    def _round_size(self, size: float) -> float:
        """Round size to nearest lot size"""
        return round(size / self.params.lot_size) * self.params.lot_size
    
    def get_liquidity_stats(self) -> Dict:
        """
        Get current liquidity provision statistics
        """
        total_volume = sum(m['volume'] for v in self.metrics.values() 
                         for m in v.values())
        total_value = sum(m['value'] for v in self.metrics.values() 
                         for m in v.values())
        total_trades = sum(m['trades'] for v in self.metrics.values() 
                         for m in v.values())
        total_fees = sum(m['fees'] for v in self.metrics.values() 
                        for m in v.values())
        
        return {
            'positions': self.positions,
            'total_exposure': self.total_exposure,
            'capital_utilized': self.capital_utilized,
            'risk_metrics': {
                'total_risk': self.total_risk,
                'var_99': self.var_99,
                'risk_utilization': self.total_risk / self.params.risk_limit
            },
            'trading_metrics': {
                'total_volume': total_volume,
                'total_value': total_value,
                'total_trades': total_trades,
                'total_fees': total_fees
            },
            'venue_metrics': self.venue_stats,
            'symbol_metrics': self.symbol_stats
        }
