"""
Execution Feasibility Engine

Models execution costs, liquidity, and market impact.
Includes order flow analysis, liquidity state modeling, and spread/impact classification.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LiquidityState(Enum):
    """Liquidity state classification"""
    EXCELLENT = "excellent"
    GOOD = "good"
    NORMAL = "normal"
    CONSTRAINED = "constrained"
    POOR = "poor"


class OrderFlowToxicity(Enum):
    """Order flow toxicity level"""
    BENIGN = "benign"
    ELEVATED = "elevated"
    TOXIC = "toxic"
    EXTREME = "extreme"


class SpreadImpactClass(Enum):
    """Spread and market impact classification"""
    FAVORABLE = "favorable"
    NORMAL = "normal"
    ADVERSE = "adverse"
    PROHIBITIVE = "prohibitive"


@dataclass
class OrderFlowMetrics:
    """Order flow analysis metrics"""
    volume_imbalance: float  # -1 (sell pressure) to 1 (buy pressure)
    trade_size_skew: float  # Average trade size direction
    arrival_rate: float  # Orders per second
    cancellation_ratio: float  # Cancellations / submissions
    toxicity_score: float  # 0 to 1
    informed_flow_indicator: float  # Probability of informed trading


@dataclass
class LiquidityMetrics:
    """Liquidity state metrics"""
    bid_ask_spread_bps: float  # Spread in basis points
    depth_at_best: float  # Contracts at best bid/ask
    depth_10bp: float  # Contracts within 10bp
    depth_50bp: float  # Contracts within 50bp
    resiliency: float  # How fast liquidity recovers
    kyle_lambda: float  # Price impact coefficient


@dataclass
class ExecutionEstimate:
    """Detailed execution estimate"""
    expected_slippage_bps: float
    expected_market_impact_bps: float
    expected_fill_time_seconds: float
    fill_probability: float
    partial_fill_probability: float
    cost_adjusted_return: float
    confidence: float


class ExecutionFeasibilityEngine:
    """
    Models execution feasibility with sophisticated market microstructure analysis.
    
    Features:
    - Order flow toxicity analysis
    - Liquidity state modeling
    - Market impact estimation
    - Spread/impact regime classification
    - Cost-adjusted expectancy calculation
    """
    
    def __init__(
        self,
        max_acceptable_slippage_bps: float = 50.0,
        max_acceptable_impact_bps: float = 30.0,
        min_fill_probability: float = 0.8
    ):
        self.max_slippage_bps = max_acceptable_slippage_bps
        self.max_impact_bps = max_acceptable_impact_bps
        self.min_fill_prob = min_fill_probability
        
        # Historical data for impact modeling
        self.impact_history: List[Dict] = []
        self.liquidity_history: Dict[str, List[LiquidityMetrics]] = {}
        
    def assess_execution_feasibility(
        self,
        symbol: str,
        direction: str,
        target_size: float,
        current_price: float,
        order_book: Optional[Dict] = None,
        recent_trades: Optional[List[Dict]] = None,
        time_horizon_seconds: float = 300.0
    ) -> Tuple[bool, ExecutionEstimate, Dict[str, Any]]:
        """
        Assess if execution is feasible for given order.
        
        Returns:
            Tuple of (feasible, estimate, detailed_metrics)
        """
        # Analyze order flow
        flow_metrics = self._analyze_order_flow(recent_trades or [])
        
        # Analyze liquidity
        liquidity = self._analyze_liquidity(order_book or {}, symbol)
        
        # Classify regime
        spread_class = self._classify_spread_impact(liquidity)
        
        # Estimate market impact
        impact = self._estimate_market_impact(
            target_size, current_price, liquidity, flow_metrics, direction
        )
        
        # Estimate slippage
        slippage = self._estimate_slippage(
            target_size, liquidity, flow_metrics, spread_class
        )
        
        # Estimate fill probability
        fill_prob = self._estimate_fill_probability(
            target_size, liquidity, flow_metrics, time_horizon_seconds
        )
        
        # Calculate cost-adjusted return
        cost_adjusted = self._calculate_cost_adjusted_expectancy(
            impact, slippage, flow_metrics.toxicity_score
        )
        
        # Determine feasibility
        feasible = self._check_feasibility(
            slippage, impact, fill_prob, flow_metrics.toxicity_score
        )
        
        estimate = ExecutionEstimate(
            expected_slippage_bps=slippage,
            expected_market_impact_bps=impact,
            expected_fill_time_seconds=self._estimate_fill_time(
                target_size, liquidity, flow_metrics
            ),
            fill_probability=fill_prob,
            partial_fill_probability=1 - fill_prob if fill_prob < 1.0 else 0.0,
            cost_adjusted_return=cost_adjusted,
            confidence=self._calculate_confidence(liquidity, flow_metrics)
        )
        
        metrics = {
            'order_flow': {
                'toxicity': flow_metrics.toxicity_score,
                'imbalance': flow_metrics.volume_imbalance,
                'informed_flow': flow_metrics.informed_flow_indicator,
                'toxicity_class': self._classify_toxicity(flow_metrics.toxicity_score).value
            },
            'liquidity': {
                'spread_bps': liquidity.bid_ask_spread_bps,
                'depth_at_best': liquidity.depth_at_best,
                'depth_50bp': liquidity.depth_50bp,
                'state': self._classify_liquidity(liquidity).value
            },
            'impact': {
                'estimated_bps': impact,
                'kyle_lambda': liquidity.kyle_lambda
            },
            'spread_impact_class': spread_class.value
        }
        
        if not feasible:
            logger.warning(
                f"Execution not feasible for {symbol}: "
                f"slippage={slippage:.1f}bps, impact={impact:.1f}bps, "
                f"fill_prob={fill_prob:.2f}"
            )
            
        return feasible, estimate, metrics
    
    def _analyze_order_flow(self, recent_trades: List[Dict]) -> OrderFlowMetrics:
        """Analyze order flow for toxicity and direction"""
        
        if not recent_trades:
            return OrderFlowMetrics(
                volume_imbalance=0.0,
                trade_size_skew=0.0,
                arrival_rate=0.0,
                cancellation_ratio=0.0,
                toxicity_score=0.0,
                informed_flow_indicator=0.0
            )
            
        # Calculate volume imbalance
        buy_volume = sum(t.get('size', 0) for t in recent_trades if t.get('side') == 'buy')
        sell_volume = sum(t.get('size', 0) for t in recent_trades if t.get('side') == 'sell')
        total_volume = buy_volume + sell_volume
        
        imbalance = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0.0
        
        # Calculate trade size skew
        avg_buy_size = buy_volume / len([t for t in recent_trades if t.get('side') == 'buy']) if buy_volume > 0 else 0
        avg_sell_size = sell_volume / len([t for t in recent_trades if t.get('side') == 'sell']) if sell_volume > 0 else 0
        size_skew = (avg_buy_size - avg_sell_size) / (avg_buy_size + avg_sell_size) if (avg_buy_size + avg_sell_size) > 0 else 0
        
        # Calculate arrival rate
        if len(recent_trades) >= 2:
            time_span = (recent_trades[-1].get('timestamp', datetime.utcnow()) - 
                        recent_trades[0].get('timestamp', datetime.utcnow())).total_seconds()
            arrival_rate = len(recent_trades) / max(time_span, 1.0)
        else:
            arrival_rate = 0.0
            
        # Estimate toxicity (simplified VPIN-like metric)
        # Higher when large trades occur in one direction
        toxicity = abs(imbalance) * (1 + arrival_rate / 10) * 0.5
        
        # Informed flow indicator
        # Based on trade size and timing patterns
        large_trade_threshold = sum(t.get('size', 0) for t in recent_trades) / len(recent_trades) * 2 if recent_trades else 0
        large_trades = [t for t in recent_trades if t.get('size', 0) > large_trade_threshold]
        informed_indicator = len(large_trades) / len(recent_trades) if recent_trades else 0.0
        
        return OrderFlowMetrics(
            volume_imbalance=imbalance,
            trade_size_skew=size_skew,
            arrival_rate=arrival_rate,
            cancellation_ratio=0.3,  # Default assumption
            toxicity_score=min(1.0, toxicity),
            informed_flow_indicator=informed_indicator
        )
    
    def _analyze_liquidity(
        self,
        order_book: Dict,
        symbol: str
    ) -> LiquidityMetrics:
        """Analyze liquidity from order book"""
        
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        
        if not bids or not asks:
            # Use historical average if no order book
            hist = self.liquidity_history.get(symbol, [])
            if hist:
                return hist[-1]
            else:
                return LiquidityMetrics(
                    bid_ask_spread_bps=10.0,
                    depth_at_best=1000.0,
                    depth_10bp=5000.0,
                    depth_50bp=20000.0,
                    resiliency=0.5,
                    kyle_lambda=0.001
                )
                
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0
        
        # Calculate spread in bps
        spread_bps = ((best_ask - best_bid) / mid_price) * 10000 if mid_price > 0 else 0
        
        # Calculate depth at best
        depth_bid = sum(b[1] for b in bids[:1])
        depth_ask = sum(a[1] for a in asks[:1])
        depth_at_best = min(depth_bid, depth_ask)
        
        # Calculate depth within 10bp
        threshold_10bp = mid_price * 0.001
        depth_10bp_bid = sum(b[1] for b in bids if best_bid - b[0] <= threshold_10bp)
        depth_10bp_ask = sum(a[1] for a in asks if a[0] - best_ask <= threshold_10bp)
        depth_10bp = min(depth_10bp_bid, depth_10bp_ask)
        
        # Calculate depth within 50bp
        threshold_50bp = mid_price * 0.005
        depth_50bp_bid = sum(b[1] for b in bids if best_bid - b[0] <= threshold_50bp)
        depth_50bp_ask = sum(a[1] for a in asks if a[0] - best_ask <= threshold_50bp)
        depth_50bp = min(depth_50bp_bid, depth_50bp_ask)
        
        # Estimate Kyle's lambda (simplified)
        kyle_lambda = spread_bps / 10000 / max(depth_at_best, 1)
        
        liquidity = LiquidityMetrics(
            bid_ask_spread_bps=spread_bps,
            depth_at_best=depth_at_best,
            depth_10bp=depth_10bp,
            depth_50bp=depth_50bp,
            resiliency=0.5,  # Would require time-series analysis
            kyle_lambda=kyle_lambda
        )
        
        # Store for history
        if symbol not in self.liquidity_history:
            self.liquidity_history[symbol] = []
        self.liquidity_history[symbol].append(liquidity)
        
        # Keep only recent history
        if len(self.liquidity_history[symbol]) > 100:
            self.liquidity_history[symbol] = self.liquidity_history[symbol][-100:]
            
        return liquidity
    
    def _classify_spread_impact(self, liquidity: LiquidityMetrics) -> SpreadImpactClass:
        """Classify spread and impact conditions"""
        
        spread = liquidity.bid_ask_spread_bps
        depth = liquidity.depth_at_best
        
        if spread < 5 and depth > 10000:
            return SpreadImpactClass.FAVORABLE
        elif spread < 15 and depth > 5000:
            return SpreadImpactClass.NORMAL
        elif spread < 50 and depth > 1000:
            return SpreadImpactClass.ADVERSE
        else:
            return SpreadImpactClass.PROHIBITIVE
    
    def _classify_liquidity(self, liquidity: LiquidityMetrics) -> LiquidityState:
        """Classify overall liquidity state"""
        
        depth_score = min(1.0, liquidity.depth_50bp / 50000)
        spread_score = max(0, 1.0 - liquidity.bid_ask_spread_bps / 50)
        
        overall = (depth_score + spread_score) / 2
        
        if overall > 0.8:
            return LiquidityState.EXCELLENT
        elif overall > 0.6:
            return LiquidityState.GOOD
        elif overall > 0.4:
            return LiquidityState.NORMAL
        elif overall > 0.2:
            return LiquidityState.CONSTRAINED
        else:
            return LiquidityState.POOR
    
    def _classify_toxicity(self, toxicity_score: float) -> OrderFlowToxicity:
        """Classify order flow toxicity"""
        
        if toxicity_score < 0.2:
            return OrderFlowToxicity.BENIGN
        elif toxicity_score < 0.4:
            return OrderFlowToxicity.ELEVATED
        elif toxicity_score < 0.7:
            return OrderFlowToxicity.TOXIC
        else:
            return OrderFlowToxicity.EXTREME
    
    def _estimate_market_impact(
        self,
        size: float,
        price: float,
        liquidity: LiquidityMetrics,
        flow: OrderFlowMetrics,
        direction: str
    ) -> float:
        """Estimate market impact in basis points"""
        
        # Base impact from liquidity
        notional = size * price
        base_impact = (notional / max(liquidity.depth_50bp * price, 1)) * 100  # in bps
        
        # Adjust for flow toxicity
        toxicity_multiplier = 1 + flow.toxicity_score * 0.5
        
        # Adjust for adverse selection
        adverse_multiplier = 1 + flow.informed_flow_indicator * 0.3
        
        impact = base_impact * toxicity_multiplier * adverse_multiplier
        
        return min(impact, 200.0)  # Cap at 200bps
    
    def _estimate_slippage(
        self,
        size: float,
        liquidity: LiquidityMetrics,
        flow: OrderFlowMetrics,
        spread_class: SpreadImpactClass
    ) -> float:
        """Estimate expected slippage in basis points"""
        
        # Base slippage from spread
        base_slippage = liquidity.bid_ask_spread_bps / 2
        
        # Adjust for liquidity depth
        depth_factor = max(0.5, 1 - liquidity.depth_at_best / (size * 10))
        
        # Adjust for flow toxicity
        flow_factor = 1 + flow.toxicity_score * 0.3
        
        slippage = base_slippage * depth_factor * flow_factor
        
        return slippage
    
    def _estimate_fill_probability(
        self,
        size: float,
        liquidity: LiquidityMetrics,
        flow: OrderFlowMetrics,
        time_horizon: float
    ) -> float:
        """Estimate probability of complete fill"""
        
        # Base probability from liquidity
        depth_ratio = liquidity.depth_50bp / size
        base_prob = min(0.99, depth_ratio / (depth_ratio + 1))
        
        # Adjust for order arrival rate
        time_factor = min(1.0, time_horizon / 60)  # Normalize to 1 minute
        
        # Reduce for high toxicity (adverse selection)
        toxicity_penalty = flow.toxicity_score * 0.2
        
        prob = base_prob * time_factor * (1 - toxicity_penalty)
        
        return max(0.0, min(1.0, prob))
    
    def _estimate_fill_time(
        self,
        size: float,
        liquidity: LiquidityMetrics,
        flow: OrderFlowMetrics
    ) -> float:
        """Estimate time to fill in seconds"""
        
        # Base time from order arrival rate
        if flow.arrival_rate > 0:
            base_time = size / (flow.arrival_rate * 10)  # Assuming avg trade size
        else:
            base_time = 30.0  # Default 30 seconds
            
        # Adjust for liquidity
        liquidity_factor = max(0.5, size / max(liquidity.depth_at_best, 1))
        
        return base_time * liquidity_factor
    
    def _calculate_cost_adjusted_expectancy(
        self,
        impact_bps: float,
        slippage_bps: float,
        toxicity: float
    ) -> float:
        """Calculate cost-adjusted expectancy"""
        
        total_costs_bps = impact_bps + slippage_bps
        
        # Add toxicity premium (adverse selection cost)
        toxicity_premium = toxicity * 20  # Up to 20bps
        
        total_costs_pct = (total_costs_bps + toxicity_premium) / 100
        
        # Negative because these are costs
        return -total_costs_pct
    
    def _check_feasibility(
        self,
        slippage: float,
        impact: float,
        fill_prob: float,
        toxicity: float
    ) -> bool:
        """Check if execution parameters are within acceptable bounds"""
        
        if slippage > self.max_slippage_bps:
            return False
        if impact > self.max_impact_bps:
            return False
        if fill_prob < self.min_fill_prob:
            return False
        if toxicity > 0.8:  # Too toxic
            return False
            
        return True
    
    def _calculate_confidence(
        self,
        liquidity: LiquidityMetrics,
        flow: OrderFlowMetrics
    ) -> float:
        """Calculate confidence in execution estimate"""
        
        # Higher confidence with better data
        liquidity_confidence = min(1.0, liquidity.depth_50bp / 100000)
        flow_confidence = 0.7 if flow.arrival_rate > 0 else 0.3
        
        return (liquidity_confidence + flow_confidence) / 2
