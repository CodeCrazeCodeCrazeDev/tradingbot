"""
AAMIS v3.0 - Advanced Execution System

This module implements:
1. Execution Edge - HFT-level execution
2. Adverse Selection Modeling
3. Time-Priority Execution
4. Opportunistic Liquidity Sniping
5. News-Event Order Throttling
6. Smart Routing
7. Spread-Aware Order Decisions
8. Hidden Liquidity Detection
9. Optimize Execution Like HFT Desk
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import random
from collections import deque

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Execution strategies"""
    AGGRESSIVE = "AGGRESSIVE"  # Market orders, immediate
    PASSIVE = "PASSIVE"  # Limit orders, patient
    OPPORTUNISTIC = "OPPORTUNISTIC"  # Wait for liquidity
    STEALTH = "STEALTH"  # Hide intentions
    SMART_ROUTED = "SMART_ROUTED"  # Multi-venue
    TIME_PRIORITY = "TIME_PRIORITY"  # Queue position
    LIQUIDITY_SEEKING = "LIQUIDITY_SEEKING"  # Find hidden liquidity


class VenueType(Enum):
    """Trading venue types"""
    LIT_EXCHANGE = "LIT_EXCHANGE"  # Public exchange
    DARK_POOL = "DARK_POOL"  # Hidden liquidity
    ECN = "ECN"  # Electronic communication network
    MARKET_MAKER = "MARKET_MAKER"  # Direct to MM
    CROSSING_NETWORK = "CROSSING_NETWORK"  # Periodic auctions


@dataclass
class ExecutionMetrics:
    """Execution performance metrics"""
    arrival_price: float
    execution_price: float
    slippage: float  # Basis points
    market_impact: float  # Basis points
    timing_cost: float  # Basis points
    opportunity_cost: float  # Basis points
    total_cost: float  # Basis points
    fill_rate: float  # 0-1
    execution_time: float  # seconds
    adverse_selection: float  # Post-trade price movement


@dataclass
class VenueQuality:
    """Quality metrics for a venue"""
    venue_id: str
    venue_type: VenueType
    avg_spread: float
    fill_probability: float
    avg_fill_time: float  # seconds
    hidden_liquidity_score: float  # 0-1
    adverse_selection_rate: float  # 0-1
    latency: float  # milliseconds
    cost_score: float  # Lower is better


@dataclass
class LiquiditySnapshot:
    """Snapshot of market liquidity"""
    timestamp: datetime
    visible_bid_liquidity: float
    visible_ask_liquidity: float
    estimated_hidden_liquidity: float
    spread: float
    depth_imbalance: float  # -1 to 1
    liquidity_score: float  # 0-1


class HFTExecutionEngine:
    """
    HFT-Level Execution Engine
    Ultra-low latency, smart routing, liquidity detection
    """
    
    def __init__(self):
        self.execution_history: List[Dict] = []
        self.venue_quality: Dict[str, VenueQuality] = self._initialize_venues()
        self.latency_target_ms = 1.0  # 1ms target
        
    def _initialize_venues(self) -> Dict[str, VenueQuality]:
        """Initialize venue quality metrics"""
        venues = {}
        
        # Lit exchanges
        for i, name in enumerate(['NYSE', 'NASDAQ', 'BATS']):
            venues[name] = VenueQuality(
                venue_id=name,
                venue_type=VenueType.LIT_EXCHANGE,
                avg_spread=0.0001,
                fill_probability=0.9,
                avg_fill_time=0.5,
                hidden_liquidity_score=0.2,
                adverse_selection_rate=0.3,
                latency=0.5 + i * 0.1,
                cost_score=1.0
            )
        
        # Dark pools
        for i, name in enumerate(['DARK_A', 'DARK_B']):
            venues[name] = VenueQuality(
                venue_id=name,
                venue_type=VenueType.DARK_POOL,
                avg_spread=0.0,  # No spread in dark pools
                fill_probability=0.6,
                avg_fill_time=2.0,
                hidden_liquidity_score=0.8,
                adverse_selection_rate=0.1,
                latency=1.0 + i * 0.2,
                cost_score=0.5
            )
        
        return venues
    
    def execute_order(self, order: Dict, market_data: Dict, strategy: ExecutionStrategy) -> Dict:
        """Execute order with HFT-level optimization"""
        start_time = datetime.now()
        arrival_price = market_data.get('price', 1.0)
        
        logger.info(f"⚡ HFT Execution: {order['size']} @ {arrival_price:.5f} ({strategy.value})")
        
        # Select execution method
        if strategy == ExecutionStrategy.SMART_ROUTED:
            result = self._smart_route_execution(order, market_data)
        elif strategy == ExecutionStrategy.LIQUIDITY_SEEKING:
            result = self._liquidity_seeking_execution(order, market_data)
        elif strategy == ExecutionStrategy.TIME_PRIORITY:
            result = self._time_priority_execution(order, market_data)
        elif strategy == ExecutionStrategy.OPPORTUNISTIC:
            result = self._opportunistic_execution(order, market_data)
        else:
            result = self._aggressive_execution(order, market_data)
        
        # Calculate metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        metrics = self._calculate_execution_metrics(
            arrival_price=arrival_price,
            execution_price=result['avg_price'],
            size=order['size'],
            execution_time=execution_time,
            market_data=market_data
        )
        
        result['metrics'] = metrics
        result['execution_time'] = execution_time
        
        self.execution_history.append(result)
        
        logger.info(f"⚡ Executed in {execution_time*1000:.2f}ms, Slippage: {metrics.slippage:.2f}bps")
        
        return result
    
    def _smart_route_execution(self, order: Dict, market_data: Dict) -> Dict:
        """Smart order routing across multiple venues"""
        # Rank venues by quality
        ranked_venues = self._rank_venues(order, market_data)
        
        fills = []
        remaining_size = order['size']
        
        for venue_id, quality in ranked_venues[:3]:  # Top 3 venues
            if remaining_size <= 0:
                break
            
            # Allocate portion to this venue
            venue_size = min(remaining_size, order['size'] * 0.4)  # Max 40% per venue
            
            fill = {
                'venue': venue_id,
                'size': venue_size,
                'price': market_data.get('price', 1.0) * (1 + random.gauss(0, 0.0001)),
                'timestamp': datetime.now(),
                'latency_ms': quality.latency
            }
            
            fills.append(fill)
            remaining_size -= venue_size
        
        # Calculate average price
        total_value = sum(f['size'] * f['price'] for f in fills)
        total_size = sum(f['size'] for f in fills)
        avg_price = total_value / total_size if total_size > 0 else market_data.get('price', 1.0)
        
        return {
            'strategy': 'SMART_ROUTED',
            'fills': fills,
            'avg_price': avg_price,
            'total_filled': total_size,
            'fill_rate': total_size / order['size']
        }
    
    def _liquidity_seeking_execution(self, order: Dict, market_data: Dict) -> Dict:
        """Seek hidden liquidity"""
        # Check for hidden liquidity
        liquidity = self._detect_hidden_liquidity(market_data)
        
        fills = []
        
        if liquidity.estimated_hidden_liquidity > order['size'] * 0.5:
            # Enough hidden liquidity, use dark pools
            logger.info(f"💧 Hidden liquidity detected: {liquidity.estimated_hidden_liquidity:.0f}")
            
            dark_venues = [v for v in self.venue_quality.values() if v.venue_type == VenueType.DARK_POOL]
            
            for venue in dark_venues:
                fill = {
                    'venue': venue.venue_id,
                    'size': order['size'] / len(dark_venues),
                    'price': market_data.get('price', 1.0),  # Mid-price in dark pools
                    'timestamp': datetime.now(),
                    'hidden': True
                }
                fills.append(fill)
        else:
            # Not enough hidden liquidity, use lit venues
            fills = self._aggressive_execution(order, market_data)['fills']
        
        total_size = sum(f['size'] for f in fills)
        total_value = sum(f['size'] * f['price'] for f in fills)
        avg_price = total_value / total_size if total_size > 0 else market_data.get('price', 1.0)
        
        return {
            'strategy': 'LIQUIDITY_SEEKING',
            'fills': fills,
            'avg_price': avg_price,
            'total_filled': total_size,
            'fill_rate': total_size / order['size']
        }
    
    def _time_priority_execution(self, order: Dict, market_data: Dict) -> Dict:
        """Optimize for queue position (time priority)"""
        # Post limit order at best bid/ask to get in queue
        side = order.get('side', 'BUY')
        
        if side == 'BUY':
            limit_price = market_data.get('bid', 1.0)
        else:
            limit_price = market_data.get('ask', 1.0)
        
        # Simulate queue position
        queue_position = random.randint(1, 100)
        estimated_fill_time = queue_position * 0.1  # seconds
        
        fill = {
            'venue': 'PRIMARY',
            'size': order['size'],
            'price': limit_price,
            'timestamp': datetime.now() + timedelta(seconds=estimated_fill_time),
            'queue_position': queue_position,
            'limit_order': True
        }
        
        return {
            'strategy': 'TIME_PRIORITY',
            'fills': [fill],
            'avg_price': limit_price,
            'total_filled': order['size'],
            'fill_rate': 1.0,
            'estimated_fill_time': estimated_fill_time
        }
    
    def _opportunistic_execution(self, order: Dict, market_data: Dict) -> Dict:
        """Wait for opportunistic liquidity"""
        # Wait for favorable conditions
        # Simplified: check spread
        spread = market_data.get('ask', 1.0) - market_data.get('bid', 1.0)
        avg_spread = 0.0001
        
        if spread < avg_spread * 0.8:  # Tight spread
            logger.info(f"✨ Opportunistic: Tight spread detected ({spread:.5f})")
            return self._aggressive_execution(order, market_data)
        else:
            # Wait for better spread (simplified: use mid-price)
            mid_price = (market_data.get('bid', 1.0) + market_data.get('ask', 1.0)) / 2
            
            fill = {
                'venue': 'PRIMARY',
                'size': order['size'],
                'price': mid_price,
                'timestamp': datetime.now() + timedelta(seconds=5),  # Wait 5 seconds
                'opportunistic': True
            }
            
            return {
                'strategy': 'OPPORTUNISTIC',
                'fills': [fill],
                'avg_price': mid_price,
                'total_filled': order['size'],
                'fill_rate': 1.0
            }
    
    def _aggressive_execution(self, order: Dict, market_data: Dict) -> Dict:
        """Aggressive market order execution"""
        side = order.get('side', 'BUY')
        
        if side == 'BUY':
            price = market_data.get('ask', 1.0)
        else:
            price = market_data.get('bid', 1.0)
        
        fill = {
            'venue': 'PRIMARY',
            'size': order['size'],
            'price': price,
            'timestamp': datetime.now(),
            'market_order': True
        }
        
        return {
            'strategy': 'AGGRESSIVE',
            'fills': [fill],
            'avg_price': price,
            'total_filled': order['size'],
            'fill_rate': 1.0
        }
    
    def _rank_venues(self, order: Dict, market_data: Dict) -> List[Tuple[str, VenueQuality]]:
        """Rank venues by quality for this order"""
        scores = []
        
        for venue_id, quality in self.venue_quality.items():
            # Calculate composite score
            score = 0.0
            
            # Lower latency is better
            score += (1.0 - quality.latency / 10.0) * 0.3
            
            # Higher fill probability is better
            score += quality.fill_probability * 0.3
            
            # Lower cost is better
            score += (1.0 - quality.cost_score / 5.0) * 0.2
            
            # Lower adverse selection is better
            score += (1.0 - quality.adverse_selection_rate) * 0.2
            
            scores.append((venue_id, quality, score))
        
        # Sort by score (descending)
        return [(v_id, qual) for v_id, qual, score in sorted(scores, key=lambda x: x[2], reverse=True)]
    
    def _detect_hidden_liquidity(self, market_data: Dict) -> LiquiditySnapshot:
        """Detect hidden liquidity in the market"""
        # Analyze order book and trade flow
        visible_bid = market_data.get('bid_size', 1000)
        visible_ask = market_data.get('ask_size', 1000)
        
        # Estimate hidden liquidity from patterns
        # Simplified: assume 30-50% hidden liquidity
        hidden_multiplier = random.uniform(0.3, 0.5)
        estimated_hidden = (visible_bid + visible_ask) * hidden_multiplier
        
        spread = market_data.get('ask', 1.0) - market_data.get('bid', 1.0)
        
        # Calculate depth imbalance
        total_depth = visible_bid + visible_ask
        imbalance = (visible_bid - visible_ask) / total_depth if total_depth > 0 else 0
        
        # Liquidity score
        liquidity_score = min(1.0, (visible_bid + visible_ask + estimated_hidden) / 10000)
        
        return LiquiditySnapshot(
            timestamp=datetime.now(),
            visible_bid_liquidity=visible_bid,
            visible_ask_liquidity=visible_ask,
            estimated_hidden_liquidity=estimated_hidden,
            spread=spread,
            depth_imbalance=imbalance,
            liquidity_score=liquidity_score
        )
    
    def _calculate_execution_metrics(self, arrival_price: float, execution_price: float, 
                                     size: float, execution_time: float, market_data: Dict) -> ExecutionMetrics:
        """Calculate comprehensive execution metrics"""
        # Slippage (basis points)
        slippage = abs(execution_price - arrival_price) / arrival_price * 10000
        
        # Market impact (simplified)
        avg_daily_volume = market_data.get('avg_daily_volume', 1000000)
        market_impact = (size / avg_daily_volume) * 100  # bps
        
        # Timing cost
        timing_cost = execution_time * 0.1  # 0.1 bps per second
        
        # Opportunity cost (if we waited)
        opportunity_cost = max(0, slippage - timing_cost)
        
        # Total cost
        total_cost = slippage + market_impact + timing_cost
        
        # Fill rate
        fill_rate = 1.0  # Simplified
        
        # Adverse selection (post-trade price movement)
        # Simplified: random for now
        adverse_selection = random.gauss(0, 0.5)  # bps
        
        return ExecutionMetrics(
            arrival_price=arrival_price,
            execution_price=execution_price,
            slippage=slippage,
            market_impact=market_impact,
            timing_cost=timing_cost,
            opportunity_cost=opportunity_cost,
            total_cost=total_cost,
            fill_rate=fill_rate,
            execution_time=execution_time,
            adverse_selection=adverse_selection
        )


class AdverseSelectionModeler:
    """
    Models adverse selection risk
    Predicts post-trade price movement
    """
    
    def __init__(self):
        self.adverse_selection_history: List[Dict] = []
        
    def predict_adverse_selection(self, order: Dict, market_data: Dict) -> float:
        """Predict adverse selection for this order"""
        # Factors that increase adverse selection:
        # 1. Large order size relative to liquidity
        # 2. Wide spread
        # 3. High volatility
        # 4. News events
        
        score = 0.0
        
        # Order size impact
        order_size = order.get('size', 0)
        avg_size = market_data.get('avg_order_size', 1000)
        if order_size > avg_size * 2:
            score += 0.3
        
        # Spread impact
        spread = market_data.get('spread', 0.0001)
        avg_spread = 0.0001
        if spread > avg_spread * 1.5:
            score += 0.2
        
        # Volatility impact
        volatility = market_data.get('volatility', 0.01)
        if volatility > 0.02:
            score += 0.3
        
        # News impact
        if market_data.get('news_event', False):
            score += 0.2
        
        return min(1.0, score)
    
    def record_adverse_selection(self, order: Dict, pre_trade_price: float, post_trade_price: float):
        """Record actual adverse selection"""
        adverse_selection = (post_trade_price - pre_trade_price) / pre_trade_price * 10000  # bps
        
        record = {
            'timestamp': datetime.now(),
            'order_size': order.get('size', 0),
            'adverse_selection_bps': adverse_selection,
            'order': order
        }
        
        self.adverse_selection_history.append(record)
        
        if abs(adverse_selection) > 5:  # >5 bps
            logger.warning(f"⚠️ High adverse selection: {adverse_selection:.2f}bps")


class NewsEventThrottler:
    """
    Throttles orders during news events
    Prevents trading during high-risk periods
    """
    
    def __init__(self):
        self.news_events: List[Dict] = []
        self.throttle_duration = 60  # seconds
        
    def check_news_event(self, market_data: Dict) -> Dict:
        """Check if there's a news event"""
        is_news_event = market_data.get('news_event', False)
        
        if is_news_event:
            event = {
                'timestamp': datetime.now(),
                'event_type': market_data.get('event_type', 'UNKNOWN'),
                'severity': market_data.get('event_severity', 0.5)
            }
            self.news_events.append(event)
            
            logger.warning(f"📰 News Event Detected: {event['event_type']}")
            
            return {
                'should_throttle': True,
                'throttle_duration': self.throttle_duration * event['severity'],
                'reason': f"News event: {event['event_type']}"
            }
        
        # Check recent news events
        recent_events = [e for e in self.news_events 
                        if (datetime.now() - e['timestamp']).total_seconds() < self.throttle_duration]
        
        if recent_events:
            return {
                'should_throttle': True,
                'throttle_duration': self.throttle_duration,
                'reason': 'Recent news event'
            }
        
        return {
            'should_throttle': False,
            'throttle_duration': 0,
            'reason': 'No news events'
        }


class SpreadAwareExecutor:
    """
    Makes execution decisions based on spread conditions
    Waits for favorable spreads
    """
    
    def __init__(self):
        self.spread_history: deque = deque(maxlen=1000)
        self.avg_spread = 0.0001
        
    def analyze_spread(self, market_data: Dict) -> Dict:
        """Analyze current spread conditions"""
        current_spread = market_data.get('ask', 1.0) - market_data.get('bid', 1.0)
        self.spread_history.append(current_spread)
        
        # Update average spread
        if self.spread_history:
            self.avg_spread = np.mean(self.spread_history)
        
        # Calculate spread percentile
        if len(self.spread_history) > 10:
            percentile = np.percentile(self.spread_history, 50)
            spread_ratio = current_spread / percentile if percentile > 0 else 1.0
        else:
            spread_ratio = 1.0
        
        # Determine execution recommendation
        if spread_ratio < 0.8:  # Tight spread
            recommendation = 'EXECUTE_NOW'
            reason = 'Favorable spread conditions'
        elif spread_ratio > 1.5:  # Wide spread
            recommendation = 'WAIT'
            reason = 'Spread too wide, wait for better conditions'
        else:
            recommendation = 'NEUTRAL'
            reason = 'Normal spread conditions'
        
        return {
            'current_spread': current_spread,
            'avg_spread': self.avg_spread,
            'spread_ratio': spread_ratio,
            'recommendation': recommendation,
            'reason': reason
        }


class AdvancedExecutionSystem:
    """
    Complete Advanced Execution System
    Combines all execution optimization techniques
    """
    
    def __init__(self):
        self.hft_engine = HFTExecutionEngine()
        self.adverse_selection_modeler = AdverseSelectionModeler()
        self.news_throttler = NewsEventThrottler()
        self.spread_executor = SpreadAwareExecutor()
        self.execution_sessions: List[Dict] = []
        
    def execute_with_optimization(self, order: Dict, market_data: Dict) -> Dict:
        """Execute order with full optimization"""
        session_id = f"EXEC_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        logger.info(f"🚀 Execution session started: {session_id}")
        
        session = {
            'session_id': session_id,
            'start_time': datetime.now(),
            'order': order,
            'market_data': market_data
        }
        
        # 1. Check for news events
        news_check = self.news_throttler.check_news_event(market_data)
        session['news_check'] = news_check
        
        if news_check['should_throttle']:
            logger.warning(f"⏸️ Execution throttled: {news_check['reason']}")
            session['status'] = 'THROTTLED'
            session['end_time'] = datetime.now()
            self.execution_sessions.append(session)
            return session
        
        # 2. Analyze spread conditions
        spread_analysis = self.spread_executor.analyze_spread(market_data)
        session['spread_analysis'] = spread_analysis
        
        # 3. Predict adverse selection
        adverse_selection_risk = self.adverse_selection_modeler.predict_adverse_selection(order, market_data)
        session['adverse_selection_risk'] = adverse_selection_risk
        
        # 4. Select execution strategy
        if adverse_selection_risk > 0.7:
            strategy = ExecutionStrategy.STEALTH
        elif spread_analysis['recommendation'] == 'WAIT':
            strategy = ExecutionStrategy.OPPORTUNISTIC
        elif order.get('size', 0) > 1000000:  # Large order
            strategy = ExecutionStrategy.SMART_ROUTED
        else:
            strategy = ExecutionStrategy.AGGRESSIVE
        
        session['strategy'] = strategy.value
        
        # 5. Execute with HFT engine
        execution_result = self.hft_engine.execute_order(order, market_data, strategy)
        session['execution_result'] = execution_result
        
        # 6. Record adverse selection (simulated post-trade price)
        post_trade_price = execution_result['avg_price'] * (1 + random.gauss(0, 0.0005))
        self.adverse_selection_modeler.record_adverse_selection(
            order, 
            market_data.get('price', 1.0),
            post_trade_price
        )
        
        session['status'] = 'COMPLETED'
        session['end_time'] = datetime.now()
        session['duration'] = (session['end_time'] - session['start_time']).total_seconds()
        
        self.execution_sessions.append(session)
        
        logger.info(f"🚀 Execution completed: {session_id}")
        logger.info(f"   Strategy: {strategy.value}")
        logger.info(f"   Total Cost: {execution_result['metrics'].total_cost:.2f}bps")
        
        return session
    
    def get_execution_report(self) -> Dict:
        """Get comprehensive execution report"""
        if not self.execution_sessions:
            return {'error': 'No executions yet'}
        
        completed_sessions = [s for s in self.execution_sessions if s['status'] == 'COMPLETED']
        
        if not completed_sessions:
            return {'error': 'No completed executions'}
        
        # Calculate statistics
        total_costs = [s['execution_result']['metrics'].total_cost for s in completed_sessions]
        slippages = [s['execution_result']['metrics'].slippage for s in completed_sessions]
        execution_times = [s['execution_result']['execution_time'] for s in completed_sessions]
        
        return {
            'total_executions': len(self.execution_sessions),
            'completed_executions': len(completed_sessions),
            'throttled_executions': len([s for s in self.execution_sessions if s['status'] == 'THROTTLED']),
            'avg_total_cost_bps': np.mean(total_costs),
            'avg_slippage_bps': np.mean(slippages),
            'avg_execution_time_ms': np.mean(execution_times) * 1000,
            'best_execution_cost_bps': min(total_costs),
            'worst_execution_cost_bps': max(total_costs),
            'strategies_used': self._count_strategies()
        }
    
    def _count_strategies(self) -> Dict[str, int]:
        """Count usage of each strategy"""
        from collections import defaultdict
        counts = defaultdict(int)
        
        for session in self.execution_sessions:
            if session['status'] == 'COMPLETED':
                strategy = session.get('strategy', 'UNKNOWN')
                counts[strategy] += 1
        
        return dict(counts)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create advanced execution system
    exec_system = AdvancedExecutionSystem()
    
    # Simulate orders
    orders = [
        {'size': 500000, 'side': 'BUY'},
        {'size': 2000000, 'side': 'BUY'},  # Large order
        {'size': 100000, 'side': 'SELL'},
    ]
    
    market_data = {
        'price': 1.1000,
        'bid': 1.0999,
        'ask': 1.1001,
        'spread': 0.0002,
        'bid_size': 1000,
        'ask_size': 1000,
        'volatility': 0.015,
        'avg_daily_volume': 10000000,
        'avg_order_size': 500000,
        'news_event': False
    }
    
    for order in orders:
        session = exec_system.execute_with_optimization(order, market_data)
        logger.info(f"\nOrder: {order['size']} {order['side']}")
        if session['status'] == 'COMPLETED':
            metrics = session['execution_result']['metrics']
            logger.info(f"  Total Cost: {metrics.total_cost:.2f}bps")
            logger.info(f"  Slippage: {metrics.slippage:.2f}bps")
            logger.info(f"  Execution Time: {session['execution_result']['execution_time']*1000:.2f}ms")
    
    # Get execution report
    report = exec_system.get_execution_report()
    print("\n" + "="*80)
    logger.info("EXECUTION PERFORMANCE REPORT")
    print("="*80)
    logger.info(f"Total Executions: {report['total_executions']}")
    logger.info(f"Avg Total Cost: {report['avg_total_cost_bps']:.2f}bps")
    logger.info(f"Avg Slippage: {report['avg_slippage_bps']:.2f}bps")
    logger.info(f"Avg Execution Time: {report['avg_execution_time_ms']:.2f}ms")
    logger.info("\nStrategies Used:")
    for strategy, count in report['strategies_used'].items():
        logger.info(f"  {strategy}: {count}")
    print("="*80)
