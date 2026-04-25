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


# ============================================================================
# ADVANCED LIQUIDITY INTELLIGENCE SYSTEMS
# ============================================================================

@dataclass
class LiquidityVacuumSignal:
    """Signal indicating liquidity vacuum conditions"""
    timestamp: datetime
    symbol: str
    vacuum_probability: float  # 0-1
    thin_book_zones: List[Tuple[float, float]]  # (price, depth) pairs
    estimated_impact_multiplier: float  # Multiplier vs normal conditions
    recommended_action: str


class LiquidityVacuumDetector:
    """
    Liquidity Vacuum Detector
    
    Big moves happen when liquidity disappears.
    
    Detect:
    - Thin order books
    - Widening spreads
    - Low depth zones
    
    Output: liquidity_vacuum_probability
    Trade: movement, not direction
    """
    
    def __init__(self, vacuum_threshold: float = 0.7):
        self.vacuum_threshold = vacuum_threshold
        self.vacuum_history: Dict[str, List[LiquidityVacuumSignal]] = defaultdict(list)
        
    def detect_vacuum(
        self,
        symbol: str,
        order_book: OrderBook,
        recent_trades: List[Dict]
    ) -> LiquidityVacuumSignal:
        """Detect liquidity vacuum conditions."""
        vacuum_score = 0.0
        thin_zones = []
        
        # 1. Order book depth analysis
        total_bid_depth = sum(level.size for level in order_book.bids[:10])
        total_ask_depth = sum(level.size for level in order_book.asks[:10])
        avg_depth = (total_bid_depth + total_ask_depth) / 2
        
        # Compare to historical average
        historical_avg = self._get_historical_avg_depth(symbol)
        if historical_avg > 0:
            depth_ratio = avg_depth / historical_avg
            if depth_ratio < 0.3:
                vacuum_score += 0.5
                thin_zones.append((order_book.mid_price, avg_depth))
            elif depth_ratio < 0.5:
                vacuum_score += 0.3
        
        # 2. Spread analysis
        spread_bps = order_book.spread_bps
        avg_spread = self._get_historical_avg_spread(symbol)
        if avg_spread > 0:
            spread_ratio = spread_bps / avg_spread
            if spread_ratio > 5:
                vacuum_score += 0.3
            elif spread_ratio > 3:
                vacuum_score += 0.2
        
        # 3. Gap detection in order book
        gaps = self._detect_book_gaps(order_book)
        if gaps:
            vacuum_score += min(0.3, len(gaps) * 0.1)
            for gap in gaps:
                thin_zones.append(gap)
        
        # 4. Trade size vs depth ratio
        if recent_trades:
            avg_trade_size = np.mean([t.get('size', 0) for t in recent_trades[-10:]])
            if avg_depth > 0:
                consumption_ratio = avg_trade_size / avg_depth
                if consumption_ratio > 0.1:  # Trade consumes >10% of depth
                    vacuum_score += 0.2
        
        # Determine action
        action = 'normal'
        if vacuum_score > 0.8:
            action = 'halt_large_orders'
        elif vacuum_score > 0.6:
            action = 'reduce_size_significantly'
        elif vacuum_score > 0.4:
            action = 'proceed_with_caution'
        
        signal = LiquidityVacuumSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            vacuum_probability=min(1.0, vacuum_score),
            thin_book_zones=thin_zones,
            estimated_impact_multiplier=1.0 + vacuum_score * 3,  # Up to 4x impact
            recommended_action=action
        )
        
        self.vacuum_history[symbol].append(signal)
        
        if vacuum_score > self.vacuum_threshold:
            logger.warning(f"Liquidity vacuum detected for {symbol}: {vacuum_score:.1%}")
        
        return signal
    
    def _get_historical_avg_depth(self, symbol: str) -> float:
        """Get historical average order book depth."""
        # Placeholder - would fetch from historical data
        return 1000.0
    
    def _get_historical_avg_spread(self, symbol: str) -> float:
        """Get historical average spread."""
        # Placeholder - would fetch from historical data
        return 2.0
    
    def _detect_book_gaps(self, order_book: OrderBook) -> List[Tuple[float, float]]:
        """Detect gaps in order book."""
        gaps = []
        
        # Check bid side
        for i in range(len(order_book.bids) - 1):
            current = order_book.bids[i]
            next_level = order_book.bids[i + 1]
            gap_pct = (current.price - next_level.price) / current.price * 10000
            if gap_pct > 5:  # 5bp gap
                gaps.append((current.price, next_level.price))
        
        # Check ask side
        for i in range(len(order_book.asks) - 1):
            current = order_book.asks[i]
            next_level = order_book.asks[i + 1]
            gap_pct = (next_level.price - current.price) / current.price * 10000
            if gap_pct > 5:
                gaps.append((current.price, next_level.price))
        
        return gaps


@dataclass
class ExecutionStressMetrics:
    """Metrics for execution difficulty assessment"""
    timestamp: datetime
    symbol: str
    stress_score: float  # 0-1
    liquidity_score: float
    volatility_score: float
    spread_score: float
    order_size_score: float
    recommended_size_reduction: float  # 0-1
    expected_slippage_bps: float
    confidence: float


class ExecutionStressIndex:
    """
    Execution Stress Index
    
    Before placing trade:
    Estimate: execution_difficulty_score
    
    Based on:
    - Liquidity
    - Volatility
    - Spread
    - Order size
    
    Reject trades that are too hard to execute.
    """
    
    def __init__(self, max_stress_threshold: float = 0.8):
        self.max_stress_threshold = max_stress_threshold
        self.stress_history: Dict[str, List[ExecutionStressMetrics]] = defaultdict(list)
        
    def calculate_stress(
        self,
        symbol: str,
        order_size: float,
        order_book: OrderBook,
        market_conditions: Dict[str, Any]
    ) -> ExecutionStressMetrics:
        """Calculate execution stress for proposed trade."""
        
        # 1. Liquidity Score (higher = more liquid = less stress)
        bid_depth = sum(level.size for level in order_book.bids[:5])
        ask_depth = sum(level.size for level in order_book.asks[:5])
        avg_depth = (bid_depth + ask_depth) / 2
        
        liquidity_score = min(1.0, avg_depth / (order_size * 10)) if order_size > 0 else 0.5
        
        # 2. Volatility Score (higher = more volatile = more stress)
        volatility = market_conditions.get('realized_volatility_24h', 0.2)
        volatility_score = min(1.0, volatility / 0.5)  # 50% vol = max stress
        
        # 3. Spread Score (higher = wider spread = more stress)
        spread_bps = order_book.spread_bps
        avg_spread = market_conditions.get('average_spread_bps', 2.0)
        spread_score = min(1.0, spread_bps / (avg_spread * 3)) if avg_spread > 0 else 0.5
        
        # 4. Order Size Score (larger relative to market = more stress)
        avg_volume = market_conditions.get('average_daily_volume', order_size * 100)
        size_ratio = order_size / avg_volume if avg_volume > 0 else 0.01
        order_size_score = min(1.0, size_ratio * 100)  # 1% ADV = max stress
        
        # Calculate composite stress score
        # Lower liquidity = higher stress
        # Higher volatility = higher stress
        # Wider spread = higher stress
        # Larger order = higher stress
        stress_score = (
            (1 - liquidity_score) * 0.35 +
            volatility_score * 0.30 +
            spread_score * 0.20 +
            order_size_score * 0.15
        )
        
        # Calculate recommended size reduction
        if stress_score > 0.8:
            reduction = 0.75
        elif stress_score > 0.6:
            reduction = 0.50
        elif stress_score > 0.4:
            reduction = 0.25
        else:
            reduction = 0.0
        
        # Estimate expected slippage
        base_slippage = spread_bps / 2  # Half spread
        impact_slippage = order_size_score * 20  # Up to 20bps for large orders
        vol_adjustment = volatility_score * 10  # Up to 10bps for high vol
        expected_slippage = base_slippage + impact_slippage + vol_adjustment
        
        metrics = ExecutionStressMetrics(
            timestamp=datetime.now(),
            symbol=symbol,
            stress_score=stress_score,
            liquidity_score=liquidity_score,
            volatility_score=volatility_score,
            spread_score=spread_score,
            order_size_score=order_size_score,
            recommended_size_reduction=reduction,
            expected_slippage_bps=expected_slippage,
            confidence=min(1.0, 0.5 + liquidity_score * 0.5)
        )
        
        self.stress_history[symbol].append(metrics)
        
        if stress_score > self.max_stress_threshold:
            logger.warning(f"High execution stress for {symbol}: {stress_score:.1%} - "
                         f"Recommend reducing size by {reduction:.0%}")
        
        return metrics
    
    def should_execute(self, symbol: str, order_size: float) -> Tuple[bool, str, float]:
        """Determine if trade should be executed given stress level."""
        if symbol not in self.stress_history or not self.stress_history[symbol]:
            return True, "No stress data", 1.0
        
        latest = self.stress_history[symbol][-1]
        
        if latest.stress_score > 0.9:
            return False, f"Critical stress level: {latest.stress_score:.1%}", 0.0
        
        if latest.stress_score > self.max_stress_threshold:
            adjusted_size = order_size * (1 - latest.recommended_size_reduction)
            return True, f"High stress - size reduced to {adjusted_size:,.0f}", adjusted_size / order_size
        
        return True, "Stress level acceptable", 1.0


@dataclass
class LiquidityPool:
    """Represents a liquidity pool in the market"""
    price_level: float
    size: float
    pool_type: str  # 'support', 'resistance', 'accumulation', 'distribution'
    confidence: float
    historical_hits: int
    last_tested: datetime


@dataclass
class StopCluster:
    """Represents a cluster of stop orders"""
    price_level: float
    estimated_size: float
    stop_type: str  # 'long_stops', 'short_stops'
    probability: float
    distance_to_current: float  # in price terms


class StructuralLiquidityMap:
    """
    Structural Liquidity Map
    
    Map:
    - Where liquidity pools exist
    - Where stops likely sit
    
    Trade around:
    - Liquidity, not price
    """
    
    def __init__(self):
        self.liquidity_pools: Dict[str, List[LiquidityPool]] = defaultdict(list)
        self.stop_clusters: Dict[str, List[StopCluster]] = defaultdict(list)
        self.price_history: Dict[str, List[Tuple[datetime, float, float]]] = defaultdict(list)
        
    def update_price_history(
        self,
        symbol: str,
        timestamp: datetime,
        high: float,
        low: float,
        close: float,
        volume: float
    ):
        """Update price history for liquidity mapping."""
        self.price_history[symbol].append((timestamp, high, low, close, volume))
        
        # Keep last 1000 bars
        if len(self.price_history[symbol]) > 1000:
            self.price_history[symbol] = self.price_history[symbol][-1000:]
        
        # Update liquidity pools
        self._update_liquidity_pools(symbol)
        
        # Update stop clusters
        self._update_stop_clusters(symbol, close)
    
    def _update_liquidity_pools(self, symbol: str):
        """Identify liquidity pools from price history."""
        if len(self.price_history[symbol]) < 50:
            return
        
        history = self.price_history[symbol]
        pools = []
        
        # Find support/resistance levels
        highs = [h for _, h, _, _, _ in history[-100:]]
        lows = [l for _, _, l, _, _ in history[-100:]]
        
        # Count touches at each level (discretized to 0.1%)
        level_touches = defaultdict(lambda: {'highs': 0, 'lows': 0, 'volume': 0})
        
        for _, h, l, c, v in history[-200:]:
            high_level = round(h / (c * 0.001)) * (c * 0.001)
            low_level = round(l / (c * 0.001)) * (c * 0.001)
            level_touches[high_level]['highs'] += 1
            level_touches[low_level]['lows'] += 1
            level_touches[high_level]['volume'] += v * 0.5
            level_touches[low_level]['volume'] += v * 0.5
        
        # Create pools for levels with multiple touches
        for level, data in level_touches.items():
            if data['highs'] >= 3:
                pools.append(LiquidityPool(
                    price_level=level,
                    size=data['volume'],
                    pool_type='resistance',
                    confidence=min(1.0, data['highs'] / 10),
                    historical_hits=data['highs'],
                    last_tested=history[-1][0]
                ))
            
            if data['lows'] >= 3:
                pools.append(LiquidityPool(
                    price_level=level,
                    size=data['volume'],
                    pool_type='support',
                    confidence=min(1.0, data['lows'] / 10),
                    historical_hits=data['lows'],
                    last_tested=history[-1][0]
                ))
        
        # Sort by confidence and keep top 10
        pools.sort(key=lambda x: x.confidence, reverse=True)
        self.liquidity_pools[symbol] = pools[:10]
    
    def _update_stop_clusters(self, symbol: str, current_price: float):
        """Identify likely stop clusters."""
        if len(self.price_history[symbol]) < 20:
            return
        
        history = self.price_history[symbol]
        recent_lows = [l for _, _, l, _, _ in history[-20:]]
        recent_highs = [h for _, h, _, _, _ in history[-20:]]
        
        clusters = []
        
        # Long stops sit below recent lows
        if recent_lows:
            lowest_low = min(recent_lows)
            # Stops cluster slightly below the low
            stop_level = lowest_low * 0.995
            distance = (current_price - stop_level) / current_price
            
            if distance > 0:
                clusters.append(StopCluster(
                    price_level=stop_level,
                    estimated_size=sum(v for _, _, _, _, v in history[-20:]) * 0.1,
                    stop_type='long_stops',
                    probability=min(1.0, 20 - len(recent_lows) * 0.5),
                    distance_to_current=distance
                ))
        
        # Short stops sit above recent highs
        if recent_highs:
            highest_high = max(recent_highs)
            stop_level = highest_high * 1.005
            distance = (stop_level - current_price) / current_price
            
            if distance > 0:
                clusters.append(StopCluster(
                    price_level=stop_level,
                    estimated_size=sum(v for _, _, _, _, v in history[-20:]) * 0.1,
                    stop_type='short_stops',
                    probability=min(1.0, 20 - len(recent_highs) * 0.5),
                    distance_to_current=distance
                ))
        
        self.stop_clusters[symbol] = clusters
    
    def get_liquidity_map(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Get complete liquidity map for symbol."""
        pools = self.liquidity_pools.get(symbol, [])
        stops = self.stop_clusters.get(symbol, [])
        
        # Find nearest liquidity
        nearest_support = None
        nearest_resistance = None
        
        for pool in pools:
            if pool.pool_type == 'support' and pool.price_level < current_price:
                if nearest_support is None or current_price - pool.price_level < current_price - nearest_support.price_level:
                    nearest_support = pool
            elif pool.pool_type == 'resistance' and pool.price_level > current_price:
                if nearest_resistance is None or pool.price_level - current_price < nearest_resistance.price_level - current_price:
                    nearest_resistance = pool
        
        # Find nearest stop cluster
        nearest_stop = min(stops, key=lambda x: abs(x.distance_to_current)) if stops else None
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'liquidity_pools': [
                {
                    'level': p.price_level,
                    'size': p.size,
                    'type': p.pool_type,
                    'confidence': p.confidence,
                    'hits': p.historical_hits
                } for p in pools
            ],
            'stop_clusters': [
                {
                    'level': s.price_level,
                    'type': s.stop_type,
                    'probability': s.probability,
                    'distance_pct': s.distance_to_current * 100
                } for s in stops
            ],
            'nearest_support': {
                'level': nearest_support.price_level,
                'distance_pct': (current_price - nearest_support.price_level) / current_price * 100
            } if nearest_support else None,
            'nearest_resistance': {
                'level': nearest_resistance.price_level,
                'distance_pct': (nearest_resistance.price_level - current_price) / current_price * 100
            } if nearest_resistance else None,
            'nearest_stop_cluster': {
                'level': nearest_stop.price_level,
                'type': nearest_stop.stop_type,
                'distance_pct': nearest_stop.distance_to_current * 100
            } if nearest_stop else None
        }
    
    def should_trade_toward_liquidity(self, symbol: str, direction: str, current_price: float) -> Tuple[bool, str]:
        """Determine if trading toward liquidity is favorable."""
        map_data = self.get_liquidity_map(symbol, current_price)
        
        if direction == 'buy':
            # Buying - target support levels
            support = map_data.get('nearest_support')
            if support and support['distance_pct'] < 1.0:
                return True, f"Near support at {support['level']:.2f} ({support['distance_pct']:.2f}% below)"
            
            # Check if near short stop cluster (potential stop run)
            stop = map_data.get('nearest_stop_cluster')
            if stop and stop['type'] == 'short_stops' and stop['distance_pct'] < 0.5:
                return True, f"Near short stop cluster - potential for stop run"
        
        else:  # sell
            # Selling - target resistance levels
            resistance = map_data.get('nearest_resistance')
            if resistance and resistance['distance_pct'] < 1.0:
                return True, f"Near resistance at {resistance['level']:.2f} ({resistance['distance_pct']:.2f}% above)"
            
            # Check if near long stop cluster
            stop = map_data.get('nearest_stop_cluster')
            if stop and stop['type'] == 'long_stops' and stop['distance_pct'] < 0.5:
                return True, f"Near long stop cluster - potential for stop run"
        
        return False, "No significant liquidity target nearby"


class InventorySkewRiskManager:
    """
    Inventory Skew Risk Manager
    
    For market makers: Manage inventory imbalance risk.
    
    When inventory gets too long or short:
    - Adjust quotes to skew fills
    - Hedge excess inventory
    - Reduce size until balanced
    """
    
    def __init__(
        self,
        max_inventory_usd: float = 100000,
        target_inventory_usd: float = 0,
        skew_factor: float = 0.1
    ):
        self.max_inventory = max_inventory_usd
        self.target_inventory = target_inventory_usd
        self.skew_factor = skew_factor
        
        self.current_inventory: Dict[str, float] = defaultdict(float)
        self.inventory_history: List[Dict] = []
        
    def update_inventory(self, symbol: str, quantity: float, price: float):
        """Update inventory position."""
        notional = quantity * price
        self.current_inventory[symbol] += notional
        
        # Record history
        self.inventory_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'quantity': quantity,
            'notional': notional,
            'inventory_after': self.current_inventory[symbol]
        })
        
        # Keep last 100
        if len(self.inventory_history) > 100:
            self.inventory_history = self.inventory_history[-100:]
    
    def calculate_skew(self, symbol: str) -> Dict[str, Any]:
        """Calculate quote skew based on inventory position."""
        inventory = self.current_inventory.get(symbol, 0)
        
        # Calculate inventory ratio
        inventory_ratio = inventory / self.max_inventory if self.max_inventory > 0 else 0
        
        # Calculate skew
        # Positive inventory = want to sell = skew bids down
        # Negative inventory = want to buy = skew asks up
        bid_skew = -inventory_ratio * self.skew_factor
        ask_skew = -inventory_ratio * self.skew_factor  # Same direction for both sides
        
        return {
            'symbol': symbol,
            'current_inventory_usd': inventory,
            'inventory_ratio': inventory_ratio,
            'bid_skew_bps': bid_skew * 10000,
            'ask_skew_bps': ask_skew * 10000,
            'skew_direction': 'skew_to_sell' if inventory > 0 else 'skew_to_buy' if inventory < 0 else 'neutral',
            'urgency': self._calculate_hedge_urgency(inventory_ratio)
        }
    
    def _calculate_hedge_urgency(self, inventory_ratio: float) -> str:
        """Calculate urgency to hedge inventory."""
        abs_ratio = abs(inventory_ratio)
        
        if abs_ratio > 0.9:
            return 'CRITICAL'
        elif abs_ratio > 0.7:
            return 'HIGH'
        elif abs_ratio > 0.5:
            return 'MODERATE'
        else:
            return 'LOW'
    
    def get_inventory_risk_report(self) -> Dict[str, Any]:
        """Get comprehensive inventory risk report."""
        if not self.current_inventory:
            return {'status': 'no_positions'}
        
        total_inventory = sum(self.current_inventory.values())
        gross_inventory = sum(abs(inv) for inv in self.current_inventory.values())
        
        # Concentration risk
        if gross_inventory > 0:
            max_single_position = max(abs(inv) for inv in self.current_inventory.values())
            concentration = max_single_position / gross_inventory
        else:
            concentration = 0
        
        return {
            'total_inventory_usd': total_inventory,
            'gross_inventory_usd': gross_inventory,
            'net_inventory_usd': total_inventory,
            'concentration_risk': concentration,
            'utilization': abs(total_inventory) / self.max_inventory,
            'at_limit': abs(total_inventory) >= self.max_inventory * 0.95,
            'positions': dict(self.current_inventory),
            'recommendation': (
                'URGENT: Reduce inventory immediately' if abs(total_inventory) > self.max_inventory * 0.9
                else 'CAUTION: Skew quotes aggressively' if abs(total_inventory) > self.max_inventory * 0.7
                else 'NORMAL: Monitor inventory levels'
            )
        }


class FundingRateArbitrageMonitor:
    """
    Funding Rate Arbitrage Monitor
    
    Monitors funding rates across perpetual futures exchanges.
    
    Opportunities:
    - Long on exchange with negative funding
    - Short on exchange with positive funding
    - Capture funding payments while hedged
    
    Risk: Funding rates can flip quickly.
    """
    
    def __init__(self, min_rate_diff_bps: float = 5.0):
        self.min_rate_diff_bps = min_rate_diff_bps
        self.funding_rates: Dict[str, Dict[str, float]] = {}  # symbol -> exchange -> rate
        self.funding_history: Dict[str, List[Dict]] = defaultdict(list)
        
    def update_funding_rate(
        self,
        symbol: str,
        exchange: str,
        funding_rate_8h: float,  # 8-hour funding rate
        timestamp: Optional[datetime] = None
    ):
        """Update funding rate for symbol/exchange."""
        if symbol not in self.funding_rates:
            self.funding_rates[symbol] = {}
        
        # Convert to daily rate
        daily_rate = funding_rate_8h * 3
        
        self.funding_rates[symbol][exchange] = daily_rate
        
        # Record history
        self.funding_history[symbol].append({
            'timestamp': timestamp or datetime.now(),
            'exchange': exchange,
            'funding_rate_8h': funding_rate_8h,
            'funding_rate_daily': daily_rate
        })
        
        # Keep last 30 days per exchange
        if len(self.funding_history[symbol]) > 90:  # 3 updates/day * 30 days
            self.funding_history[symbol] = self.funding_history[symbol][-90:]
    
    def find_arbitrage_opportunities(self, symbol: str) -> List[Dict[str, Any]]:
        """Find funding rate arbitrage opportunities."""
        rates = self.funding_rates.get(symbol, {})
        
        if len(rates) < 2:
            return []
        
        opportunities = []
        
        # Sort by rate
        sorted_rates = sorted(rates.items(), key=lambda x: x[1])
        
        # Check extremes
        lowest = sorted_rates[0]
        highest = sorted_rates[-1]
        
        rate_diff_bps = (highest[1] - lowest[1]) * 10000
        
        if rate_diff_bps > self.min_rate_diff_bps:
            # Annualized return
            annual_return = (highest[1] - lowest[1]) * 365
            
            opportunities.append({
                'symbol': symbol,
                'long_exchange': lowest[0],  # Lower (or negative) funding
                'short_exchange': highest[0],  # Higher funding
                'long_rate_bps': lowest[1] * 10000,
                'short_rate_bps': highest[1] * 10000,
                'rate_diff_bps': rate_diff_bps,
                'annualized_return_pct': annual_return * 100,
                'strategy': 'long_low_funding_short_high_funding',
                'risk': 'funding_flip_risk'
            })
        
        return opportunities
    
    def analyze_funding_regime(self, symbol: str) -> Dict[str, Any]:
        """Analyze current funding rate regime."""
        history = self.funding_history.get(symbol, [])
        
        if len(history) < 10:
            return {'status': 'insufficient_data'}
        
        recent = history[-30:]
        
        rates = [h['funding_rate_daily'] for h in recent]
        avg_rate = np.mean(rates)
        
        # Calculate trend
        if len(rates) >= 10:
            early_avg = np.mean(rates[:5])
            late_avg = np.mean(rates[-5:])
            trend = 'increasing' if late_avg > early_avg * 1.1 else \
                   'decreasing' if late_avg < early_avg * 0.9 else 'stable'
        else:
            trend = 'unknown'
        
        return {
            'symbol': symbol,
            'current_avg_funding_bps': avg_rate * 10000,
            'funding_trend': trend,
            'funding_regime': (
                'high_positive' if avg_rate > 0.001 else
                'low_positive' if avg_rate > 0 else
                'low_negative' if avg_rate > -0.001 else
                'high_negative'
            ),
            'opportunity_count': len(self.find_arbitrage_opportunities(symbol)),
            'recommendation': (
                'Short perpetuals' if avg_rate > 0.0005 else
                'Long perpetuals' if avg_rate < -0.0005 else
                'Neutral'
            )
        }


class CointegrationBreakdownDetector:
    """
    Cointegration Breakdown Detector
    
    Monitors mean-reverting pairs for cointegration breakdown.
    
    When cointegration breaks:
    - Pairs stop mean-reverting
    - Spread continues drifting
    - Pairs trading becomes toxic
    """
    
    def __init__(self, lookback_window: int = 60):
        self.lookback_window = lookback_window
        self.spread_history: Dict[str, Deque[float]] = {}
        self.cointegration_scores: Dict[str, float] = {}
        
    def update_spread(self, pair_id: str, spread: float, timestamp: Optional[datetime] = None):
        """Update spread for a pair."""
        if pair_id not in self.spread_history:
            self.spread_history[pair_id] = deque(maxlen=self.lookback_window)
        
        self.spread_history[pair_id].append({
            'spread': spread,
            'timestamp': timestamp or datetime.now()
        })
    
    def test_cointegration(self, pair_id: str) -> Dict[str, Any]:
        """
        Test if pair is still cointegrated.
        
        Uses ADF test logic simplified for real-time use.
        """
        history = self.spread_history.get(pair_id, [])
        
        if len(history) < self.lookback_window * 0.5:
            return {'status': 'insufficient_data', 'is_cointegrated': None}
        
        spreads = [h['spread'] for h in history]
        
        # Calculate spread characteristics
        spread_mean = np.mean(spreads)
        spread_std = np.std(spreads)
        
        # Test 1: Mean reversion check
        # Calculate how many times spread crosses the mean
        crossings = sum(
            1 for i in range(1, len(spreads))
            if (spreads[i] - spread_mean) * (spreads[i-1] - spread_mean) < 0
        )
        
        # Healthy cointegration should have regular mean crossings
        expected_crossings = len(spreads) / 10  # Roughly 10% of observations
        mean_reversion_score = min(1.0, crossings / expected_crossings) if expected_crossings > 0 else 0
        
        # Test 2: Spread volatility trend
        if len(spreads) >= 20:
            recent_vol = np.std(spreads[-10:])
            older_vol = np.std(spreads[-20:-10])
            vol_expanding = recent_vol > older_vol * 1.3
        else:
            vol_expanding = False
        
        # Test 3: Deviation persistence
        # How long does spread stay away from mean?
        deviations = [abs(s - spread_mean) / spread_std for s in spreads[-20:]]
        avg_deviation = np.mean(deviations)
        persistent_deviation = avg_deviation > 1.5
        
        # Overall cointegration score
        coint_score = mean_reversion_score * 0.5 + (0.5 if not vol_expanding else 0) + (0.5 if not persistent_deviation else 0)
        coint_score /= 1.5  # Normalize
        
        is_cointegrated = coint_score > 0.6 and not vol_expanding
        
        return {
            'pair_id': pair_id,
            'is_cointegrated': is_cointegrated,
            'cointegration_score': coint_score,
            'mean_reversion_score': mean_reversion_score,
            'volatility_expanding': vol_expanding,
            'persistent_deviation': persistent_deviation,
            'current_spread_zscore': (spreads[-1] - spread_mean) / spread_std if spread_std > 0 else 0,
            'recommendation': (
                'AVOID: Cointegration broken' if not is_cointegrated and coint_score < 0.4
                else 'CAUTION: Monitor closely' if not is_cointegrated
                else 'TRADE: Cointegration healthy'
            )
        }
    
    def get_all_pair_status(self) -> Dict[str, Any]:
        """Get status of all monitored pairs."""
        results = {}
        
        for pair_id in self.spread_history.keys():
            results[pair_id] = self.test_cointegration(pair_id)
        
        cointegrated_count = sum(1 for r in results.values() if r.get('is_cointegrated'))
        total_pairs = len(results)
        
        return {
            'pair_status': results,
            'cointegrated_pairs': cointegrated_count,
            'total_pairs': total_pairs,
            'cointegration_rate': cointegrated_count / total_pairs if total_pairs > 0 else 0,
            'regime': 'favorable' if cointegrated_count / total_pairs > 0.7 else 'challenging' if total_pairs > 0 else 'unknown'
        }
