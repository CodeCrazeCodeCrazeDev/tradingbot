"""
Real-Time Execution Engine with Smart Order Routing
Ensures optimal order execution across multiple venues
"""

import asyncio
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import deque
import heapq
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    ICEBERG = "iceberg"
    TRAILING_STOP = "trailing_stop"
    PEG = "peg"
    HIDDEN = "hidden"

class ExecutionAlgorithm(Enum):
    """Execution algorithms"""
    TWAP = "twap"  # Time-Weighted Average Price
    VWAP = "vwap"  # Volume-Weighted Average Price
    POV = "pov"    # Percentage of Volume
    IS = "is"      # Implementation Shortfall
    ADAPTIVE = "adaptive"
    SNIPER = "sniper"
    GUERRILLA = "guerrilla"
    LIQUIDITY_SEEKING = "liquidity_seeking"

@dataclass
class ExecutionResult:
    """Result of order execution"""
    order_id: str
    success: bool
    executed_price: float
    executed_quantity: float
    slippage: float
    execution_time: float
    fees: float
    venue: str
    metadata: Dict[str, Any]


@dataclass
class TradingDecision:
    """Trading decision to be executed"""
    decision_id: str
    symbol: str
    direction: str  # 'buy' or 'sell'
    quantity: float
    price: Optional[float] = None
    order_type: str = 'market'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionEngine:
    async def execute_order(self, order: dict) -> dict:
        """Public API for order execution, routes to execute() for compatibility."""
        # If the main 'execute' expects a decision, wrap order as needed or adapt as appropriate
        # For now, we assume 'order' is compatible with execute()
        return await self.execute(order)

    """
    High-performance execution engine with smart order routing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Execution parameters
        self.max_slippage = self.config.get('max_slippage', 0.002)
        self.urgency_threshold = self.config.get('urgency_threshold', 0.7)
        self.chunk_size = self.config.get('chunk_size', 1000)
        
        # Connected venues
        self.venues = {}
        self.venue_latencies = {}
        self.venue_fees = {}
        self.venue_liquidity = {}
        
        # Order tracking
        self.active_orders = {}
        self.order_history = deque(maxlen=10000)
        self.execution_stats = {}
        
        # Smart routing
        self.router = SmartOrderRouter()
        
        # Execution algorithms
        self.algorithms = {
            ExecutionAlgorithm.TWAP: self._execute_twap,
            ExecutionAlgorithm.VWAP: self._execute_vwap,
            ExecutionAlgorithm.POV: self._execute_pov,
            ExecutionAlgorithm.IS: self._execute_is,
            ExecutionAlgorithm.ADAPTIVE: self._execute_adaptive,
            ExecutionAlgorithm.SNIPER: self._execute_sniper,
            ExecutionAlgorithm.GUERRILLA: self._execute_guerrilla,
            ExecutionAlgorithm.LIQUIDITY_SEEKING: self._execute_liquidity_seeking
        }
        
        logger.info("Execution Engine initialized")
    
    async def execute(self, decision: 'TradingDecision') -> ExecutionResult:
        """
        Execute a trading decision using optimal strategy
        """
        logger.info(f"Executing decision {decision.decision_id}")
        
        # Extract execution parameters
        params = self._prepare_execution_params(decision)
        
        # Select execution algorithm
        algorithm = self._select_algorithm(params)
        
        # Route order to best venue(s)
        routing_plan = await self.router.route(params, self.venues)
        
        # Execute using selected algorithm
        if algorithm in self.algorithms:
            result = await self.algorithms[algorithm](params, routing_plan)
        else:
            result = await self._execute_default(params, routing_plan)
        
        # Track execution
        self._track_execution(decision, result)
        
        return result
    
    def _prepare_execution_params(self, decision: 'TradingDecision') -> Dict:
        """
        Prepare execution parameters from trading decision
        """
        plan = decision.execution_plan
        
        params = {
            'decision_id': decision.decision_id,
            'symbols': decision.symbols,
            'action': decision.action,
            'quantity': self._calculate_quantity(decision),
            'urgency': plan.get('urgency', 0.5),
            'entry_method': plan.get('entry_method', 'ADAPTIVE'),
            'entry_price': plan.get('entry_price'),
            'slippage_limit': plan.get('slippage_limit', self.max_slippage),
            'time_limit': plan.get('time_limit', 60),
            'algo_preference': plan.get('execution_algo')
        }
        
        return params
    
    def _calculate_quantity(self, decision: 'TradingDecision') -> float:
        """
        Calculate order quantity from allocation
        """
        total_allocation = sum(decision.allocation.values())
        
        # Get current price (simplified)
        price = 100  # Would fetch actual price
        
        quantity = total_allocation / price
        
        return quantity
    
    def _select_algorithm(self, params: Dict) -> ExecutionAlgorithm:
        """
        Select optimal execution algorithm based on parameters
        """
        urgency = params['urgency']
        quantity = params['quantity']
        
        # High urgency - use aggressive algorithms
        if urgency > self.urgency_threshold:
            if quantity < self.chunk_size:
                return ExecutionAlgorithm.SNIPER
            else:
                return ExecutionAlgorithm.GUERRILLA
        
        # Large orders - use patient algorithms
        if quantity > self.chunk_size * 10:
            return ExecutionAlgorithm.VWAP
        
        # Medium orders - adaptive
        if quantity > self.chunk_size:
            return ExecutionAlgorithm.ADAPTIVE
        
        # Small orders - liquidity seeking
        return ExecutionAlgorithm.LIQUIDITY_SEEKING
    
    async def _execute_twap(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Time-Weighted Average Price execution
        """
        total_quantity = params['quantity']
        time_limit = params['time_limit']
        
        # Split into time slices
        num_slices = min(20, int(time_limit / 3))  # Execute every 3 seconds
        slice_size = total_quantity / num_slices
        
        executed_quantity = 0
        total_cost = 0
        
        for i in range(num_slices):
            # Execute slice
            slice_result = await self._execute_slice(
                params['symbols'][0],
                slice_size,
                params['action'],
                routing_plan
            )
            
            executed_quantity += slice_result['quantity']
            total_cost += slice_result['cost']
            
            # Wait for next slice
            if i < num_slices - 1:
                await asyncio.sleep(time_limit / num_slices)
        
        avg_price = total_cost / executed_quantity if executed_quantity > 0 else 0
        
        return ExecutionResult(
            order_id=f"TWAP_{params['decision_id']}",
            success=executed_quantity > 0,
            executed_price=avg_price,
            executed_quantity=executed_quantity,
            slippage=self._calculate_slippage(params.get('entry_price'), avg_price),
            execution_time=time_limit,
            fees=total_cost * 0.001,  # 0.1% fees
            venue='multiple',
            metadata={'algorithm': 'TWAP', 'slices': num_slices}
        )
    
    async def _execute_vwap(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Volume-Weighted Average Price execution
        """
        # Get volume profile
        volume_profile = await self._get_volume_profile(params['symbols'][0])
        
        total_quantity = params['quantity']
        executed_quantity = 0
        total_cost = 0
        
        # Execute according to volume distribution
        for time_bin, volume_pct in volume_profile.items():
            bin_quantity = total_quantity * volume_pct
            
            # Execute this portion
            result = await self._execute_slice(
                params['symbols'][0],
                bin_quantity,
                params['action'],
                routing_plan
            )
            
            executed_quantity += result['quantity']
            total_cost += result['cost']
        
        avg_price = total_cost / executed_quantity if executed_quantity > 0 else 0
        
        return ExecutionResult(
            order_id=f"VWAP_{params['decision_id']}",
            success=executed_quantity > 0,
            executed_price=avg_price,
            executed_quantity=executed_quantity,
            slippage=self._calculate_slippage(params.get('entry_price'), avg_price),
            execution_time=params['time_limit'],
            fees=total_cost * 0.001,
            venue='multiple',
            metadata={'algorithm': 'VWAP'}
        )
    
    async def _execute_pov(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Percentage of Volume execution
        """
        target_pov = 0.1  # Target 10% of market volume
        
        total_quantity = params['quantity']
        executed_quantity = 0
        total_cost = 0
        
        start_time = datetime.now()
        
        while executed_quantity < total_quantity:
            # Get current market volume
            market_volume = await self._get_market_volume(params['symbols'][0])
            
            # Calculate our slice size
            our_slice = market_volume * target_pov
            remaining = total_quantity - executed_quantity
            slice_size = min(our_slice, remaining)
            
            # Execute slice
            result = await self._execute_slice(
                params['symbols'][0],
                slice_size,
                params['action'],
                routing_plan
            )
            
            executed_quantity += result['quantity']
            total_cost += result['cost']
            
            # Check time limit
            if (datetime.now() - start_time).seconds > params['time_limit']:
                break
            
            await asyncio.sleep(1)
        
        avg_price = total_cost / executed_quantity if executed_quantity > 0 else 0
        
        return ExecutionResult(
            order_id=f"POV_{params['decision_id']}",
            success=executed_quantity > 0,
            executed_price=avg_price,
            executed_quantity=executed_quantity,
            slippage=self._calculate_slippage(params.get('entry_price'), avg_price),
            execution_time=(datetime.now() - start_time).seconds,
            fees=total_cost * 0.001,
            venue='multiple',
            metadata={'algorithm': 'POV', 'target_pov': target_pov}
        )
    
    async def _execute_is(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Implementation Shortfall minimization
        """
        # Minimize difference between decision price and execution price
        # Uses predictive model to optimize execution trajectory
        
        total_quantity = params['quantity']
        urgency = params['urgency']
        
        # Calculate optimal trajectory
        trajectory = self._calculate_optimal_trajectory(
            total_quantity, 
            params['time_limit'],
            urgency
        )
        
        executed_quantity = 0
        total_cost = 0
        
        for step in trajectory:
            result = await self._execute_slice(
                params['symbols'][0],
                step['quantity'],
                params['action'],
                routing_plan
            )
            
            executed_quantity += result['quantity']
            total_cost += result['cost']
            
            await asyncio.sleep(step['wait_time'])
        
        avg_price = total_cost / executed_quantity if executed_quantity > 0 else 0
        
        return ExecutionResult(
            order_id=f"IS_{params['decision_id']}",
            success=executed_quantity > 0,
            executed_price=avg_price,
            executed_quantity=executed_quantity,
            slippage=self._calculate_slippage(params.get('entry_price'), avg_price),
            execution_time=params['time_limit'],
            fees=total_cost * 0.001,
            venue='multiple',
            metadata={'algorithm': 'IS'}
        )
    
    async def _execute_adaptive(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Adaptive execution that adjusts to market conditions
        """
        total_quantity = params['quantity']
        executed_quantity = 0
        total_cost = 0
        
        while executed_quantity < total_quantity:
            # Assess current market conditions
            conditions = await self._assess_market_conditions(params['symbols'][0])
            
            # Adapt slice size and timing
            if conditions['liquidity'] == 'high' and conditions['volatility'] == 'low':
                slice_size = min(total_quantity * 0.2, total_quantity - executed_quantity)
                wait_time = 1
            elif conditions['liquidity'] == 'low' or conditions['volatility'] == 'high':
                slice_size = min(total_quantity * 0.05, total_quantity - executed_quantity)
                wait_time = 5
            else:
                slice_size = min(total_quantity * 0.1, total_quantity - executed_quantity)
                wait_time = 3
            
            # Execute adapted slice
            result = await self._execute_slice(
                params['symbols'][0],
                slice_size,
                params['action'],
                routing_plan
            )
            
            executed_quantity += result['quantity']
            total_cost += result['cost']
            
            await asyncio.sleep(wait_time)
        
        avg_price = total_cost / executed_quantity if executed_quantity > 0 else 0
        
        return ExecutionResult(
            order_id=f"ADAPTIVE_{params['decision_id']}",
            success=executed_quantity > 0,
            executed_price=avg_price,
            executed_quantity=executed_quantity,
            slippage=self._calculate_slippage(params.get('entry_price'), avg_price),
            execution_time=params['time_limit'],
            fees=total_cost * 0.001,
            venue='multiple',
            metadata={'algorithm': 'ADAPTIVE'}
        )
    
    async def _execute_sniper(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Sniper execution for small, urgent orders
        """
        # Single shot execution at best available price
        symbol = params['symbols'][0]
        quantity = params['quantity']
        
        # Find best price across venues
        best_venue, best_price = await self._find_best_price(symbol, params['action'])
        
        # Execute immediately
        result = await self._send_order(
            venue=best_venue,
            symbol=symbol,
            order_type=OrderType.MARKET,
            quantity=quantity,
            action=params['action']
        )
        
        return ExecutionResult(
            order_id=f"SNIPER_{params['decision_id']}",
            success=result['success'],
            executed_price=result['price'],
            executed_quantity=result['quantity'],
            slippage=self._calculate_slippage(params.get('entry_price'), result['price']),
            execution_time=result['latency'],
            fees=result['fees'],
            venue=best_venue,
            metadata={'algorithm': 'SNIPER'}
        )
    
    async def _execute_guerrilla(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Guerrilla execution - aggressive but smart
        """
        total_quantity = params['quantity']
        
        # Break into random-sized chunks to avoid detection
        chunks = self._create_guerrilla_chunks(total_quantity)
        
        executed_quantity = 0
        total_cost = 0
        
        for chunk in chunks:
            # Random venue selection
            venue = self._select_random_venue(routing_plan)
            
            # Execute with randomized timing
            result = await self._send_order(
                venue=venue,
                symbol=params['symbols'][0],
                order_type=OrderType.MARKET,
                quantity=chunk,
                action=params['action']
            )
            
            executed_quantity += result['quantity']
            total_cost += result['cost']
            
            # Random delay
            await asyncio.sleep(np.random.uniform(0.1, 1))
        
        avg_price = total_cost / executed_quantity if executed_quantity > 0 else 0
        
        return ExecutionResult(
            order_id=f"GUERRILLA_{params['decision_id']}",
            success=executed_quantity > 0,
            executed_price=avg_price,
            executed_quantity=executed_quantity,
            slippage=self._calculate_slippage(params.get('entry_price'), avg_price),
            execution_time=10,
            fees=total_cost * 0.001,
            venue='multiple',
            metadata={'algorithm': 'GUERRILLA', 'chunks': len(chunks)}
        )
    
    async def _execute_liquidity_seeking(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Liquidity seeking execution
        """
        symbol = params['symbols'][0]
        total_quantity = params['quantity']
        
        # Find venues with best liquidity
        liquidity_map = await self._map_liquidity(symbol)
        
        executed_quantity = 0
        total_cost = 0
        
        # Execute at venues with liquidity
        for venue, available_liquidity in liquidity_map.items():
            if executed_quantity >= total_quantity:
                break
            
            exec_quantity = min(available_liquidity, total_quantity - executed_quantity)
            
            result = await self._send_order(
                venue=venue,
                symbol=symbol,
                order_type=OrderType.LIMIT,
                quantity=exec_quantity,
                action=params['action'],
                limit_price=params.get('entry_price')
            )
            
            executed_quantity += result['quantity']
            total_cost += result['cost']
        
        avg_price = total_cost / executed_quantity if executed_quantity > 0 else 0
        
        return ExecutionResult(
            order_id=f"LIQ_SEEK_{params['decision_id']}",
            success=executed_quantity > 0,
            executed_price=avg_price,
            executed_quantity=executed_quantity,
            slippage=self._calculate_slippage(params.get('entry_price'), avg_price),
            execution_time=5,
            fees=total_cost * 0.001,
            venue='multiple',
            metadata={'algorithm': 'LIQUIDITY_SEEKING'}
        )
    
    async def _execute_default(self, params: Dict, routing_plan: Dict) -> ExecutionResult:
        """
        Default execution when no specific algorithm is selected
        """
        return await self._execute_adaptive(params, routing_plan)
    
    async def _execute_slice(self, symbol: str, quantity: float, 
                            action: str, routing_plan: Dict) -> Dict:
        """
        Execute a single slice of an order
        """
        # Simplified execution
        price = 100 + np.random.normal(0, 0.1)  # Simulated price
        
        return {
            'quantity': quantity,
            'cost': quantity * price,
            'price': price
        }
    
    async def _get_volume_profile(self, symbol: str) -> Dict:
        """
        Get intraday volume profile
        """
        # Simulated volume profile
        profile = {}
        for hour in range(24):
            if 9 <= hour <= 16:  # Market hours
                profile[hour] = 0.1  # 10% per hour during market
            else:
                profile[hour] = 0.01  # 1% per hour after hours
        
        return profile
    
    async def _get_market_volume(self, symbol: str) -> float:
        """
        Get current market volume
        """
        # Simulated
        return np.random.uniform(10000, 100000)
    
    def _calculate_optimal_trajectory(self, quantity: float, time_limit: float, 
                                     urgency: float) -> List[Dict]:
        """
        Calculate optimal execution trajectory
        """
        # Simple trajectory based on urgency
        if urgency > 0.8:
            # Front-loaded
            return [
                {'quantity': quantity * 0.6, 'wait_time': 1},
                {'quantity': quantity * 0.3, 'wait_time': 2},
                {'quantity': quantity * 0.1, 'wait_time': 1}
            ]
        else:
            # Even distribution
            steps = 5
            return [
                {'quantity': quantity / steps, 'wait_time': time_limit / steps}
                for _ in range(steps)
            ]
    
    async def _assess_market_conditions(self, symbol: str) -> Dict:
        """
        Assess current market conditions
        """
        # Simulated assessment
        return {
            'liquidity': np.random.choice(['high', 'medium', 'low']),
            'volatility': np.random.choice(['high', 'medium', 'low']),
            'trend': np.random.choice(['up', 'down', 'sideways'])
        }
    
    async def _find_best_price(self, symbol: str, action: str) -> Tuple[str, float]:
        """
        Find best price across venues
        """
        best_venue = 'exchange1'
        best_price = 100 + np.random.normal(0, 0.1)
        
        return best_venue, best_price
    
    async def _send_order(self, venue: str, symbol: str, order_type: OrderType,
                         quantity: float, action: str, limit_price: Optional[float] = None) -> Dict:
        """
        Send order to specific venue
        """
        # Simulated order execution
        executed_price = 100 + np.random.normal(0, 0.1)
        
        return {
            'success': True,
            'price': executed_price,
            'quantity': quantity,
            'cost': quantity * executed_price,
            'latency': np.random.uniform(0.001, 0.01),
            'fees': quantity * executed_price * 0.001
        }
    
    def _create_guerrilla_chunks(self, total_quantity: float) -> List[float]:
        """
        Create random-sized chunks for guerrilla execution
        """
        chunks = []
        remaining = total_quantity
        min_chunk = total_quantity * 0.01  # Minimum 1% of total
        
        while remaining > min_chunk:
            # Random chunk size (10% to 30% of remaining)
            chunk = remaining * np.random.uniform(0.1, 0.3)
            chunk = max(min_chunk, min(chunk, remaining))
            chunks.append(chunk)
            remaining -= chunk
        
        # Add any remaining amount to last chunk
        if remaining > 0:
            if chunks:
                chunks[-1] += remaining
            else:
                chunks.append(remaining)
        
        return chunks
    
    def _select_random_venue(self, routing_plan: Dict) -> str:
        """
        Select random venue from routing plan
        """
        venues = list(routing_plan.keys()) if routing_plan else ['default']
        return np.random.choice(venues)
    
    async def _map_liquidity(self, symbol: str) -> Dict[str, float]:
        """
        Map available liquidity across venues
        """
        # Simulated liquidity map
        return {
            'exchange1': np.random.uniform(1000, 10000),
            'exchange2': np.random.uniform(1000, 10000),
            'darkpool1': np.random.uniform(5000, 20000)
        }
    
    def _calculate_slippage(self, expected_price: Optional[float], 
                           executed_price: float) -> float:
        """
        Calculate slippage from expected price
        """
        if not expected_price:
            return 0
        
        return abs(executed_price - expected_price) / expected_price
    
    def _track_execution(self, decision: 'TradingDecision', result: ExecutionResult):
        """
        Track execution for analysis
        """
        self.order_history.append({
            'decision_id': decision.decision_id,
            'timestamp': datetime.now(),
            'result': result,
            'symbols': decision.symbols
        })
        
        # Update statistics
        self._update_execution_stats(result)
    
    def _update_execution_stats(self, result: ExecutionResult):
        """
        Update execution statistics
        """
        algo = result.metadata.get('algorithm', 'unknown')
        
        if algo not in self.execution_stats:
            self.execution_stats[algo] = {
                'count': 0,
                'total_slippage': 0,
                'success_rate': 0,
                'avg_execution_time': 0
            }
        
        stats = self.execution_stats[algo]
        stats['count'] += 1
        stats['total_slippage'] += result.slippage
        stats['success_rate'] = (stats['success_rate'] * (stats['count'] - 1) + 
                                 (1 if result.success else 0)) / stats['count']
        stats['avg_execution_time'] = (stats['avg_execution_time'] * (stats['count'] - 1) + 
                                       result.execution_time) / stats['count']


class SmartOrderRouter:
    """
    Smart order routing to find best execution venues
    """
    
    def __init__(self):
        self.routing_cache = {}
        self.venue_scores = {}
        
    async def route(self, params: Dict, venues: Dict) -> Dict:
        """
        Determine optimal routing for order
        """
        symbol = params['symbols'][0]
        quantity = params['quantity']
        
        # Score each venue
        venue_scores = await self._score_venues(symbol, quantity, venues)
        
        # Create routing plan
        routing_plan = self._create_routing_plan(venue_scores, quantity)
        
        return routing_plan
    
    async def _score_venues(self, symbol: str, quantity: float, 
                           venues: Dict) -> Dict[str, float]:
        """
        Score venues based on multiple factors
        """
        scores = {}
        
        for venue_name, venue_info in venues.items():
            # Factors: fees, latency, liquidity, fill rate
            fee_score = 1 - venue_info.get('fee_rate', 0.001) * 100
            latency_score = 1 - venue_info.get('latency', 10) / 100
            liquidity_score = min(1, venue_info.get('liquidity', 10000) / quantity)
            fill_score = venue_info.get('fill_rate', 0.95)
            
            # Weighted score
            total_score = (
                fee_score * 0.2 +
                latency_score * 0.2 +
                liquidity_score * 0.4 +
                fill_score * 0.2
            )
            
            scores[venue_name] = total_score
        
        return scores
    
    def _create_routing_plan(self, venue_scores: Dict[str, float], 
                            quantity: float) -> Dict:
        """
        Create routing plan based on venue scores
        """
        # Sort venues by score
        sorted_venues = sorted(venue_scores.items(), key=lambda x: x[1], reverse=True)
        
        routing_plan = {}
        remaining = quantity
        
        for venue, score in sorted_venues:
            if remaining <= 0:
                break
            
            # Allocate proportionally to score
            allocation = min(remaining, quantity * score)
            routing_plan[venue] = {
                'quantity': allocation,
                'priority': len(routing_plan) + 1,
                'score': score
            }
            
            remaining -= allocation
        
        return routing_plan
