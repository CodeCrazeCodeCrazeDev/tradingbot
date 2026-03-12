"""
Real-Time Liquidity Analysis & Slippage Modeling System
Institutional-Grade Execution Intelligence

This module provides comprehensive liquidity analysis:
- Real-time order book depth analysis
- Market impact modeling (Almgren-Chriss)
- Slippage prediction and tracking
- Adaptive position sizing based on liquidity
- Optimal execution scheduling (TWAP, VWAP, Implementation Shortfall)
- Liquidity regime detection
- Historical slippage analysis

Market Maker + Professional Trader + Risk Manager Perspective
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque
import warnings
from typing import Set
import numpy
import pandas

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class LiquidityRegime(Enum):
    """Liquidity environment classification"""
    VERY_HIGH = "VERY_HIGH"  # Excellent liquidity, minimal impact
    HIGH = "HIGH"  # Good liquidity
    NORMAL = "NORMAL"  # Average liquidity
    LOW = "LOW"  # Reduced liquidity
    VERY_LOW = "VERY_LOW"  # Poor liquidity, high impact
    CRISIS = "CRISIS"  # Liquidity crisis


class ExecutionAlgorithm(Enum):
    """Execution algorithm types"""
    MARKET = "MARKET"  # Immediate execution
    TWAP = "TWAP"  # Time-Weighted Average Price
    VWAP = "VWAP"  # Volume-Weighted Average Price
    IS = "IS"  # Implementation Shortfall
    POV = "POV"  # Percentage of Volume
    ICEBERG = "ICEBERG"  # Hidden order
    ADAPTIVE = "ADAPTIVE"  # ML-based adaptive


@dataclass
class OrderBookLevel:
    """Single order book level"""
    price: float
    size: float
    num_orders: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'price': self.price,
            'size': self.size,
            'num_orders': self.num_orders
        }


@dataclass
class OrderBook:
    """Order book snapshot"""
    symbol: str
    timestamp: datetime
    bids: List[OrderBookLevel]  # Sorted by price descending
    asks: List[OrderBookLevel]  # Sorted by price ascending
    
    @property
    def mid_price(self) -> float:
        try:
            if self.bids and self.asks:
                return (self.bids[0].price + self.asks[0].price) / 2
            return 0.0
        except Exception as e:
            logger.error(f"Error in mid_price: {e}")
            raise
    
    @property
    def spread(self) -> float:
        try:
            if self.bids and self.asks:
                return self.asks[0].price - self.bids[0].price
            return 0.0
        except Exception as e:
            logger.error(f"Error in spread: {e}")
            raise
    
    @property
    def spread_bps(self) -> float:
        try:
            if self.mid_price > 0:
                return (self.spread / self.mid_price) * 10000
            return 0.0
        except Exception as e:
            logger.error(f"Error in spread_bps: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'mid_price': self.mid_price,
            'spread': self.spread,
            'spread_bps': round(self.spread_bps, 2),
            'bid_depth': sum(b.size for b in self.bids),
            'ask_depth': sum(a.size for a in self.asks)
        }


@dataclass
class LiquidityMetrics:
    """Comprehensive liquidity metrics"""
    timestamp: datetime
    symbol: str
    regime: LiquidityRegime
    
    # Spread metrics
    bid_ask_spread: float  # Absolute spread
    spread_bps: float  # Spread in basis points
    effective_spread: float  # Realized spread
    
    # Depth metrics
    bid_depth_10bps: float  # Bid depth within 10bps
    ask_depth_10bps: float  # Ask depth within 10bps
    total_depth: float  # Total visible depth
    depth_imbalance: float  # (bid - ask) / (bid + ask)
    
    # Impact metrics
    kyle_lambda: float  # Price impact coefficient
    amihud_illiquidity: float  # Amihud illiquidity ratio
    market_impact_1pct: float  # Impact of 1% ADV order
    
    # Volume metrics
    adv: float  # Average daily volume
    current_volume: float  # Current session volume
    volume_ratio: float  # Current / ADV
    
    # Quality score (0-100)
    liquidity_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'regime': self.regime.value,
            'spread_bps': round(self.spread_bps, 2),
            'bid_depth_10bps': round(self.bid_depth_10bps, 2),
            'ask_depth_10bps': round(self.ask_depth_10bps, 2),
            'depth_imbalance': round(self.depth_imbalance, 4),
            'kyle_lambda': round(self.kyle_lambda, 6),
            'market_impact_1pct': round(self.market_impact_1pct, 4),
            'liquidity_score': round(self.liquidity_score, 1)
        }


@dataclass
class SlippageEstimate:
    """Slippage estimation for an order"""
    symbol: str
    side: str  # BUY or SELL
    order_size: float
    order_value: float
    
    # Slippage components
    spread_cost: float  # Half spread cost
    market_impact: float  # Permanent + temporary impact
    timing_risk: float  # Volatility-based timing risk
    
    # Total estimates
    total_slippage_bps: float  # Total in basis points
    total_slippage_dollars: float  # Total in dollars
    
    # Confidence interval
    slippage_low: float  # 25th percentile
    slippage_high: float  # 75th percentile
    
    # Recommendation
    recommended_algo: ExecutionAlgorithm
    recommended_duration: int  # Minutes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'side': self.side,
            'order_size': self.order_size,
            'order_value': round(self.order_value, 2),
            'spread_cost_bps': round(self.spread_cost * 10000, 2),
            'market_impact_bps': round(self.market_impact * 10000, 2),
            'timing_risk_bps': round(self.timing_risk * 10000, 2),
            'total_slippage_bps': round(self.total_slippage_bps, 2),
            'total_slippage_dollars': round(self.total_slippage_dollars, 2),
            'slippage_range': f"{round(self.slippage_low, 2)} - {round(self.slippage_high, 2)} bps",
            'recommended_algo': self.recommended_algo.value,
            'recommended_duration_min': self.recommended_duration
        }


@dataclass
class ExecutionPlan:
    """Optimal execution plan"""
    symbol: str
    total_size: float
    side: str
    algorithm: ExecutionAlgorithm
    
    # Schedule
    num_slices: int
    slice_size: float
    interval_seconds: int
    total_duration_minutes: int
    
    # Expected costs
    expected_slippage_bps: float
    expected_market_impact_bps: float
    expected_timing_risk_bps: float
    total_expected_cost_bps: float
    
    # Constraints
    max_participation_rate: float  # Max % of volume
    urgency: str  # LOW, MEDIUM, HIGH
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'total_size': self.total_size,
            'side': self.side,
            'algorithm': self.algorithm.value,
            'num_slices': self.num_slices,
            'slice_size': self.slice_size,
            'interval_seconds': self.interval_seconds,
            'total_duration_minutes': self.total_duration_minutes,
            'expected_slippage_bps': round(self.expected_slippage_bps, 2),
            'total_expected_cost_bps': round(self.total_expected_cost_bps, 2),
            'max_participation_rate': round(self.max_participation_rate, 2),
            'urgency': self.urgency
        }


@dataclass
class SlippageRecord:
    """Historical slippage record"""
    timestamp: datetime
    symbol: str
    side: str
    order_size: float
    expected_price: float
    executed_price: float
    slippage_bps: float
    market_conditions: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'side': self.side,
            'order_size': self.order_size,
            'expected_price': self.expected_price,
            'executed_price': self.executed_price,
            'slippage_bps': round(self.slippage_bps, 2)
        }


class LiquidityAnalyzer:
    """
    Real-Time Liquidity Analysis System
    
    Provides comprehensive liquidity intelligence for optimal execution:
    
    1. Order Book Analysis
       - Real-time depth analysis
       - Spread monitoring
       - Imbalance detection
    
    2. Market Impact Modeling
       - Almgren-Chriss model
       - Kyle's lambda estimation
       - Temporary vs permanent impact
    
    3. Slippage Prediction
       - Pre-trade cost estimation
       - Historical slippage analysis
       - Confidence intervals
    
    4. Execution Optimization
       - TWAP/VWAP scheduling
       - Implementation shortfall minimization
       - Adaptive execution
    
    5. Liquidity Regime Detection
       - Real-time regime classification
       - Regime-based execution adjustment
    
    Key Metrics:
    - Spread: Cost of crossing bid-ask
    - Depth: Available liquidity at price levels
    - Impact: Price movement from order
    - Timing Risk: Volatility during execution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize liquidity analyzer
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
        
            # Model parameters
            self.volatility_window = self.config.get('volatility_window', 20)
            self.impact_decay = self.config.get('impact_decay', 0.5)  # Temporary impact decay
            self.risk_aversion = self.config.get('risk_aversion', 1e-6)  # Almgren-Chriss
        
            # Thresholds
            self.spread_thresholds = self.config.get('spread_thresholds', {
                'very_high': 5,  # bps
                'high': 10,
                'normal': 20,
                'low': 50
            })
        
            # State tracking
            self.order_books: Dict[str, OrderBook] = {}
            self.liquidity_history: Dict[str, deque] = {}
            self.slippage_history: deque = deque(maxlen=1000)
        
            # Market data
            self.adv: Dict[str, float] = {}  # Average daily volume
            self.volatility: Dict[str, float] = {}  # Annualized volatility
            self.price_history: Dict[str, deque] = {}
        
            # Statistics
            self.analyses_performed = 0
            self.orders_analyzed = 0
        
            logger.info("LiquidityAnalyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_order_book(self, order_book: OrderBook):
        """
        Update order book for a symbol
        
        Args:
            order_book: Current order book snapshot
        """
        try:
            self.order_books[order_book.symbol] = order_book
        
            # Update price history
            if order_book.symbol not in self.price_history:
                self.price_history[order_book.symbol] = deque(maxlen=1000)
        
            self.price_history[order_book.symbol].append({
                'timestamp': order_book.timestamp,
                'mid_price': order_book.mid_price,
                'spread': order_book.spread
            })
        except Exception as e:
            logger.error(f"Error in update_order_book: {e}")
            raise
    
    def set_market_data(self,
                       symbol: str,
                       adv: float,
                       volatility: float):
        """
        Set market data for a symbol
        
        Args:
            symbol: Asset symbol
            adv: Average daily volume
            volatility: Annualized volatility
        """
        try:
            self.adv[symbol] = adv
            self.volatility[symbol] = volatility
        except Exception as e:
            logger.error(f"Error in set_market_data: {e}")
            raise
    
    def analyze_liquidity(self, symbol: str) -> LiquidityMetrics:
        """
        Analyze current liquidity for a symbol
        
        Args:
            symbol: Asset symbol
            
        Returns:
            LiquidityMetrics with comprehensive analysis
        """
        try:
            self.analyses_performed += 1
        
            order_book = self.order_books.get(symbol)
        
            if not order_book:
                # Return default metrics if no order book
                return self._default_liquidity_metrics(symbol)
        
            # Calculate spread metrics
            spread_bps = order_book.spread_bps
            effective_spread = order_book.spread / 2  # Approximate
        
            # Calculate depth metrics
            mid_price = order_book.mid_price
            threshold_10bps = mid_price * 0.001  # 10 bps
        
            bid_depth_10bps = sum(
                b.size for b in order_book.bids
                if mid_price - b.price <= threshold_10bps
            )
            ask_depth_10bps = sum(
                a.size for a in order_book.asks
                if a.price - mid_price <= threshold_10bps
            )
        
            total_depth = sum(b.size for b in order_book.bids) + sum(a.size for a in order_book.asks)
        
            # Depth imbalance
            if total_depth > 0:
                bid_total = sum(b.size for b in order_book.bids)
                ask_total = sum(a.size for a in order_book.asks)
                depth_imbalance = (bid_total - ask_total) / total_depth
            else:
                depth_imbalance = 0.0
        
            # Calculate impact metrics
            adv = self.adv.get(symbol, 1000000)  # Default 1M
            volatility = self.volatility.get(symbol, 0.20)  # Default 20%
        
            # Kyle's lambda (price impact coefficient)
            # Estimated from spread and depth
            kyle_lambda = self._estimate_kyle_lambda(order_book, adv, volatility)
        
            # Amihud illiquidity
            amihud = self._calculate_amihud(symbol)
        
            # Market impact for 1% ADV order
            order_size_1pct = adv * 0.01
            impact_1pct = self._estimate_market_impact(
                order_size_1pct, adv, volatility, kyle_lambda
            )
        
            # Volume metrics
            current_volume = self._get_current_volume(symbol)
            volume_ratio = current_volume / adv if adv > 0 else 0
        
            # Calculate liquidity score (0-100)
            liquidity_score = self._calculate_liquidity_score(
                spread_bps, bid_depth_10bps + ask_depth_10bps, impact_1pct, adv
            )
        
            # Determine regime
            regime = self._classify_liquidity_regime(liquidity_score, spread_bps)
        
            metrics = LiquidityMetrics(
                timestamp=datetime.now(),
                symbol=symbol,
                regime=regime,
                bid_ask_spread=order_book.spread,
                spread_bps=spread_bps,
                effective_spread=effective_spread,
                bid_depth_10bps=bid_depth_10bps,
                ask_depth_10bps=ask_depth_10bps,
                total_depth=total_depth,
                depth_imbalance=depth_imbalance,
                kyle_lambda=kyle_lambda,
                amihud_illiquidity=amihud,
                market_impact_1pct=impact_1pct,
                adv=adv,
                current_volume=current_volume,
                volume_ratio=volume_ratio,
                liquidity_score=liquidity_score
            )
        
            # Store in history
            if symbol not in self.liquidity_history:
                self.liquidity_history[symbol] = deque(maxlen=100)
            self.liquidity_history[symbol].append(metrics)
        
            return metrics
        except Exception as e:
            logger.error(f"Error in analyze_liquidity: {e}")
            raise
    
    def estimate_slippage(self,
                         symbol: str,
                         side: str,
                         order_size: float,
                         price: Optional[float] = None) -> SlippageEstimate:
        """
        Estimate slippage for a potential order
        
        Args:
            symbol: Asset symbol
            side: BUY or SELL
            order_size: Order size in shares/units
            price: Reference price (uses mid if not provided)
            
        Returns:
            SlippageEstimate with cost breakdown
        """
        try:
            self.orders_analyzed += 1
        
            order_book = self.order_books.get(symbol)
        
            if price is None:
                price = order_book.mid_price if order_book else 100.0
        
            order_value = order_size * price
        
            # Get market data
            adv = self.adv.get(symbol, 1000000)
            volatility = self.volatility.get(symbol, 0.20)
        
            # 1. Spread cost (half spread for crossing)
            if order_book:
                spread_cost = (order_book.spread / 2) / price
            else:
                spread_cost = 0.0005  # Default 5 bps
        
            # 2. Market impact (Almgren-Chriss model)
            participation_rate = order_size / adv if adv > 0 else 0.01
        
            # Temporary impact (decays)
            temp_impact = self._calculate_temporary_impact(
                order_size, adv, volatility, participation_rate
            )
        
            # Permanent impact
            perm_impact = self._calculate_permanent_impact(
                order_size, adv, volatility
            )
        
            market_impact = temp_impact + perm_impact
        
            # 3. Timing risk (volatility during execution)
            # Assume 30-minute execution window
            execution_time = 0.5 / 6.5  # 30 min / 6.5 hours
            timing_risk = volatility * np.sqrt(execution_time) * 0.5
        
            # Total slippage
            total_slippage = spread_cost + market_impact + timing_risk
            total_slippage_bps = total_slippage * 10000
            total_slippage_dollars = total_slippage * order_value
        
            # Confidence interval (based on historical variance)
            slippage_std = total_slippage * 0.3  # 30% standard deviation
            slippage_low = (total_slippage - slippage_std) * 10000
            slippage_high = (total_slippage + slippage_std) * 10000
        
            # Recommend execution algorithm
            recommended_algo, recommended_duration = self._recommend_execution(
                order_size, adv, volatility, participation_rate
            )
        
            return SlippageEstimate(
                symbol=symbol,
                side=side,
                order_size=order_size,
                order_value=order_value,
                spread_cost=spread_cost,
                market_impact=market_impact,
                timing_risk=timing_risk,
                total_slippage_bps=total_slippage_bps,
                total_slippage_dollars=total_slippage_dollars,
                slippage_low=slippage_low,
                slippage_high=slippage_high,
                recommended_algo=recommended_algo,
                recommended_duration=recommended_duration
            )
        except Exception as e:
            logger.error(f"Error in estimate_slippage: {e}")
            raise
    
    def create_execution_plan(self,
                             symbol: str,
                             side: str,
                             total_size: float,
                             urgency: str = "MEDIUM") -> ExecutionPlan:
        """
        Create optimal execution plan
        
        Args:
            symbol: Asset symbol
            side: BUY or SELL
            total_size: Total order size
            urgency: LOW, MEDIUM, HIGH
            
        Returns:
            ExecutionPlan with schedule and expected costs
        """
        # Get market data
        try:
            adv = self.adv.get(symbol, 1000000)
            volatility = self.volatility.get(symbol, 0.20)
        
            # Participation rate based on urgency
            urgency_rates = {
                'LOW': 0.05,  # 5% of volume
                'MEDIUM': 0.10,  # 10% of volume
                'HIGH': 0.20  # 20% of volume
            }
            max_participation = urgency_rates.get(urgency, 0.10)
        
            # Calculate execution duration
            # Duration = order_size / (adv * participation_rate * trading_hours)
            trading_minutes = 6.5 * 60  # 6.5 hours
            volume_per_minute = adv / trading_minutes
        
            duration_minutes = int(total_size / (volume_per_minute * max_participation))
            duration_minutes = max(5, min(duration_minutes, trading_minutes))  # 5 min to full day
        
            # Number of slices (one every 1-5 minutes based on duration)
            if duration_minutes <= 30:
                interval_seconds = 60  # 1 minute
            elif duration_minutes <= 120:
                interval_seconds = 180  # 3 minutes
            else:
                interval_seconds = 300  # 5 minutes
        
            num_slices = max(1, duration_minutes * 60 // interval_seconds)
            slice_size = total_size / num_slices
        
            # Choose algorithm
            if urgency == 'HIGH':
                algorithm = ExecutionAlgorithm.IS  # Implementation Shortfall
            elif total_size / adv > 0.05:
                algorithm = ExecutionAlgorithm.VWAP  # Large order
            else:
                algorithm = ExecutionAlgorithm.TWAP  # Standard
        
            # Calculate expected costs
            slippage_estimate = self.estimate_slippage(symbol, side, total_size)
        
            return ExecutionPlan(
                symbol=symbol,
                total_size=total_size,
                side=side,
                algorithm=algorithm,
                num_slices=num_slices,
                slice_size=slice_size,
                interval_seconds=interval_seconds,
                total_duration_minutes=duration_minutes,
                expected_slippage_bps=slippage_estimate.total_slippage_bps,
                expected_market_impact_bps=slippage_estimate.market_impact * 10000,
                expected_timing_risk_bps=slippage_estimate.timing_risk * 10000,
                total_expected_cost_bps=slippage_estimate.total_slippage_bps,
                max_participation_rate=max_participation,
                urgency=urgency
            )
        except Exception as e:
            logger.error(f"Error in create_execution_plan: {e}")
            raise
    
    def record_slippage(self,
                       symbol: str,
                       side: str,
                       order_size: float,
                       expected_price: float,
                       executed_price: float):
        """
        Record actual slippage for analysis
        
        Args:
            symbol: Asset symbol
            side: BUY or SELL
            order_size: Order size
            expected_price: Expected execution price
            executed_price: Actual execution price
        """
        # Calculate slippage
        try:
            if side == 'BUY':
                slippage = (executed_price - expected_price) / expected_price
            else:
                slippage = (expected_price - executed_price) / expected_price
        
            slippage_bps = slippage * 10000
        
            # Get current market conditions
            liquidity = self.analyze_liquidity(symbol)
        
            record = SlippageRecord(
                timestamp=datetime.now(),
                symbol=symbol,
                side=side,
                order_size=order_size,
                expected_price=expected_price,
                executed_price=executed_price,
                slippage_bps=slippage_bps,
                market_conditions={
                    'spread_bps': liquidity.spread_bps,
                    'regime': liquidity.regime.value,
                    'liquidity_score': liquidity.liquidity_score
                }
            )
        
            self.slippage_history.append(record)
        
            logger.info(f"Slippage recorded: {symbol} {side} {slippage_bps:.2f} bps")
        except Exception as e:
            logger.error(f"Error in record_slippage: {e}")
            raise
    
    def get_adaptive_position_size(self,
                                  symbol: str,
                                  target_size: float,
                                  max_impact_bps: float = 10.0) -> float:
        """
        Get liquidity-adjusted position size
        
        Args:
            symbol: Asset symbol
            target_size: Desired position size
            max_impact_bps: Maximum acceptable market impact in bps
            
        Returns:
            Adjusted position size
        """
        # Estimate slippage for target size
        try:
            estimate = self.estimate_slippage(symbol, 'BUY', target_size)
        
            if estimate.market_impact * 10000 <= max_impact_bps:
                return target_size
        
            # Binary search for optimal size
            low, high = 0, target_size
        
            for _ in range(10):  # Max 10 iterations
                mid = (low + high) / 2
                est = self.estimate_slippage(symbol, 'BUY', mid)
            
                if est.market_impact * 10000 <= max_impact_bps:
                    low = mid
                else:
                    high = mid
        
            adjusted_size = low
        
            logger.info(f"Position size adjusted: {target_size:.0f} -> {adjusted_size:.0f} "
                       f"(max impact: {max_impact_bps} bps)")
        
            return adjusted_size
        except Exception as e:
            logger.error(f"Error in get_adaptive_position_size: {e}")
            raise
    
    def _estimate_kyle_lambda(self,
                             order_book: OrderBook,
                             adv: float,
                             volatility: float) -> float:
        """Estimate Kyle's lambda (price impact coefficient)"""
        # Lambda = volatility / sqrt(ADV)
        # Adjusted for spread
        try:
            base_lambda = volatility / np.sqrt(adv) if adv > 0 else 0.001
        
            # Adjust for spread (wider spread = higher impact)
            spread_adjustment = 1 + order_book.spread_bps / 100
        
            return base_lambda * spread_adjustment
        except Exception as e:
            logger.error(f"Error in _estimate_kyle_lambda: {e}")
            raise
    
    def _calculate_amihud(self, symbol: str) -> float:
        """Calculate Amihud illiquidity ratio"""
        try:
            if symbol not in self.price_history:
                return 0.0
        
            history = list(self.price_history[symbol])
            if len(history) < 2:
                return 0.0
        
            # Amihud = |return| / volume
            returns = []
            for i in range(1, len(history)):
                if history[i-1]['mid_price'] > 0:
                    ret = abs(history[i]['mid_price'] - history[i-1]['mid_price']) / history[i-1]['mid_price']
                    returns.append(ret)
        
            if not returns:
                return 0.0
        
            adv = self.adv.get(symbol, 1000000)
            return np.mean(returns) / adv * 1e6  # Scale for readability
        except Exception as e:
            logger.error(f"Error in _calculate_amihud: {e}")
            raise
    
    def _estimate_market_impact(self,
                               order_size: float,
                               adv: float,
                               volatility: float,
                               kyle_lambda: float) -> float:
        """Estimate total market impact"""
        # Square root model: impact = lambda * sqrt(order_size / ADV)
        try:
            participation = order_size / adv if adv > 0 else 0.01
            impact = kyle_lambda * np.sqrt(participation) * volatility
        
            return impact
        except Exception as e:
            logger.error(f"Error in _estimate_market_impact: {e}")
            raise
    
    def _calculate_temporary_impact(self,
                                   order_size: float,
                                   adv: float,
                                   volatility: float,
                                   participation_rate: float) -> float:
        """Calculate temporary market impact"""
        # Temporary impact decays after execution
        # Model: temp_impact = eta * (order_rate / ADV_rate)^gamma
        try:
            eta = 0.1 * volatility  # Impact coefficient
            gamma = 0.5  # Impact exponent
        
            temp_impact = eta * (participation_rate ** gamma)
        
            return temp_impact * self.impact_decay  # Apply decay
        except Exception as e:
            logger.error(f"Error in _calculate_temporary_impact: {e}")
            raise
    
    def _calculate_permanent_impact(self,
                                   order_size: float,
                                   adv: float,
                                   volatility: float) -> float:
        """Calculate permanent market impact"""
        # Permanent impact persists after execution
        # Model: perm_impact = gamma * sigma * (order_size / ADV)
        try:
            gamma = 0.1  # Permanent impact coefficient
            participation = order_size / adv if adv > 0 else 0.01
        
            perm_impact = gamma * volatility * np.sqrt(participation)
        
            return perm_impact
        except Exception as e:
            logger.error(f"Error in _calculate_permanent_impact: {e}")
            raise
    
    def _get_current_volume(self, symbol: str) -> float:
        """Get current session volume (placeholder)"""
        # In production, this would come from market data feed
        try:
            adv = self.adv.get(symbol, 1000000)
        
            # Assume we're mid-session
            return adv * 0.5
        except Exception as e:
            logger.error(f"Error in _get_current_volume: {e}")
            raise
    
    def _calculate_liquidity_score(self,
                                  spread_bps: float,
                                  depth: float,
                                  impact_1pct: float,
                                  adv: float) -> float:
        """Calculate composite liquidity score (0-100)"""
        try:
            score = 100
        
            # Spread penalty
            if spread_bps > 50:
                score -= 30
            elif spread_bps > 20:
                score -= 20
            elif spread_bps > 10:
                score -= 10
            elif spread_bps > 5:
                score -= 5
        
            # Depth bonus/penalty
            depth_ratio = depth / (adv * 0.01) if adv > 0 else 0
            if depth_ratio < 0.1:
                score -= 20
            elif depth_ratio < 0.5:
                score -= 10
            elif depth_ratio > 2:
                score += 10
        
            # Impact penalty
            if impact_1pct > 0.01:  # > 100 bps
                score -= 30
            elif impact_1pct > 0.005:  # > 50 bps
                score -= 20
            elif impact_1pct > 0.002:  # > 20 bps
                score -= 10
        
            return max(0, min(100, score))
        except Exception as e:
            logger.error(f"Error in _calculate_liquidity_score: {e}")
            raise
    
    def _classify_liquidity_regime(self,
                                  score: float,
                                  spread_bps: float) -> LiquidityRegime:
        """Classify liquidity regime"""
        try:
            if score >= 90 and spread_bps < 5:
                return LiquidityRegime.VERY_HIGH
            elif score >= 75:
                return LiquidityRegime.HIGH
            elif score >= 50:
                return LiquidityRegime.NORMAL
            elif score >= 25:
                return LiquidityRegime.LOW
            elif score >= 10:
                return LiquidityRegime.VERY_LOW
            else:
                return LiquidityRegime.CRISIS
        except Exception as e:
            logger.error(f"Error in _classify_liquidity_regime: {e}")
            raise
    
    def _recommend_execution(self,
                            order_size: float,
                            adv: float,
                            volatility: float,
                            participation_rate: float) -> Tuple[ExecutionAlgorithm, int]:
        """Recommend execution algorithm and duration"""
        # Small orders: market
        try:
            if participation_rate < 0.001:
                return ExecutionAlgorithm.MARKET, 0
        
            # Medium orders: TWAP
            if participation_rate < 0.01:
                duration = int(participation_rate * 100 * 60)  # Scale to minutes
                return ExecutionAlgorithm.TWAP, max(5, duration)
        
            # Large orders: VWAP or IS
            if participation_rate < 0.05:
                duration = int(participation_rate * 20 * 60)
                return ExecutionAlgorithm.VWAP, max(30, duration)
        
            # Very large orders: Implementation Shortfall
            duration = int(participation_rate * 10 * 60)
            return ExecutionAlgorithm.IS, max(60, min(duration, 390))
        except Exception as e:
            logger.error(f"Error in _recommend_execution: {e}")
            raise
    
    def _default_liquidity_metrics(self, symbol: str) -> LiquidityMetrics:
        """Return default metrics when no data available"""
        return LiquidityMetrics(
            timestamp=datetime.now(),
            symbol=symbol,
            regime=LiquidityRegime.NORMAL,
            bid_ask_spread=0.01,
            spread_bps=10.0,
            effective_spread=0.005,
            bid_depth_10bps=10000,
            ask_depth_10bps=10000,
            total_depth=20000,
            depth_imbalance=0.0,
            kyle_lambda=0.0001,
            amihud_illiquidity=0.0,
            market_impact_1pct=0.002,
            adv=self.adv.get(symbol, 1000000),
            current_volume=500000,
            volume_ratio=0.5,
            liquidity_score=70.0
        )
    
    def get_slippage_statistics(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get historical slippage statistics"""
        try:
            records = [r for r in self.slippage_history if symbol is None or r.symbol == symbol]
        
            if not records:
                return {'message': 'No slippage records available'}
        
            slippages = [r.slippage_bps for r in records]
        
            return {
                'count': len(records),
                'mean_slippage_bps': round(np.mean(slippages), 2),
                'median_slippage_bps': round(np.median(slippages), 2),
                'std_slippage_bps': round(np.std(slippages), 2),
                'min_slippage_bps': round(min(slippages), 2),
                'max_slippage_bps': round(max(slippages), 2),
                'percentile_95': round(np.percentile(slippages, 95), 2)
            }
        except Exception as e:
            logger.error(f"Error in get_slippage_statistics: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            'analyses_performed': self.analyses_performed,
            'orders_analyzed': self.orders_analyzed,
            'symbols_tracked': len(self.order_books),
            'slippage_records': len(self.slippage_history)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create analyzer
    analyzer = LiquidityAnalyzer()
    
    # Set market data
    analyzer.set_market_data('AAPL', adv=50000000, volatility=0.25)
    analyzer.set_market_data('TSLA', adv=100000000, volatility=0.50)
    
    # Create sample order book
    order_book = OrderBook(
        symbol='AAPL',
        timestamp=datetime.now(),
        bids=[
            OrderBookLevel(price=175.00, size=1000),
            OrderBookLevel(price=174.99, size=2000),
            OrderBookLevel(price=174.98, size=3000),
            OrderBookLevel(price=174.95, size=5000),
            OrderBookLevel(price=174.90, size=10000)
        ],
        asks=[
            OrderBookLevel(price=175.01, size=1000),
            OrderBookLevel(price=175.02, size=2000),
            OrderBookLevel(price=175.03, size=3000),
            OrderBookLevel(price=175.05, size=5000),
            OrderBookLevel(price=175.10, size=10000)
        ]
    )
    
    analyzer.update_order_book(order_book)
    
    # Analyze liquidity
    logger.info("\n=== Liquidity Analysis ===")
    metrics = analyzer.analyze_liquidity('AAPL')
    logger.info(f"Symbol: {metrics.symbol}")
    logger.info(f"Regime: {metrics.regime.value}")
    logger.info(f"Spread: {metrics.spread_bps:.2f} bps")
    logger.info(f"Liquidity Score: {metrics.liquidity_score:.1f}/100")
    logger.info(f"Depth Imbalance: {metrics.depth_imbalance:.2%}")
    
    # Estimate slippage for different order sizes
    logger.info("\n=== Slippage Estimates ===")
    for size in [10000, 100000, 500000, 1000000]:
        estimate = analyzer.estimate_slippage('AAPL', 'BUY', size)
        logger.info(f"\nOrder Size: {size:,} shares (${estimate.order_value:,.0f})")
        logger.info(f"  Spread Cost: {estimate.spread_cost * 10000:.2f} bps")
        logger.info(f"  Market Impact: {estimate.market_impact * 10000:.2f} bps")
        logger.info(f"  Timing Risk: {estimate.timing_risk * 10000:.2f} bps")
        logger.info(f"  Total Slippage: {estimate.total_slippage_bps:.2f} bps (${estimate.total_slippage_dollars:.2f})")
        logger.info(f"  Recommended: {estimate.recommended_algo.value} over {estimate.recommended_duration} min")
    
    # Create execution plan
    logger.info("\n=== Execution Plan ===")
    plan = analyzer.create_execution_plan('AAPL', 'BUY', 500000, urgency='MEDIUM')
    logger.info(f"Algorithm: {plan.algorithm.value}")
    logger.info(f"Total Size: {plan.total_size:,}")
    logger.info(f"Slices: {plan.num_slices} x {plan.slice_size:,.0f}")
    logger.info(f"Duration: {plan.total_duration_minutes} minutes")
    logger.info(f"Expected Cost: {plan.total_expected_cost_bps:.2f} bps")
    
    # Adaptive position sizing
    logger.info("\n=== Adaptive Position Sizing ===")
    target = 1000000
    adjusted = analyzer.get_adaptive_position_size('AAPL', target, max_impact_bps=10)
    logger.info(f"Target: {target:,} -> Adjusted: {adjusted:,.0f}")
