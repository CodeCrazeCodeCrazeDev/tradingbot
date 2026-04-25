"""
Advanced Execution Algorithms with Slippage Minimization
Implements smart order routing, TWAP/VWAP with slippage control, and adaptive execution.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order execution types"""
    MARKET = "market"
    LIMIT = "limit"
    TWAP = "twap"  # Time-Weighted Average Price
    VWAP = "vwap"  # Volume-Weighted Average Price
    ICEBERG = "iceberg"  # Hidden size
    ADAPTIVE = "adaptive"  # Adaptive to market conditions


@dataclass
class ExecutionSlice:
    """Single slice of a parent order"""
    size: float
    price: float
    time: datetime
    order_type: OrderType
    filled: bool = False
    actual_price: Optional[float] = None
    slippage_bps: float = 0.0


class SlippageMinimizer:
    """
    Minimizes slippage through intelligent order splitting and timing.
    
    Techniques:
    - Order book imbalance detection
    - Flow toxicity detection (VPIN)
    - Smart order routing
    - Dynamic participation rates
    """
    
    def __init__(self,
                 max_slices: int = 10,
                 min_slice_interval: timedelta = timedelta(seconds=30),
                 toxicity_threshold: float = 0.7):
        """
        Initialize slippage minimizer.
        
        Args:
            max_slices: Maximum number of order slices
            min_slice_interval: Minimum time between slices
            toxicity_threshold: VPIN threshold for toxicity
        """
        self.max_slices = max_slices
        self.min_slice_interval = min_slice_interval
        self.toxicity_threshold = toxicity_threshold
        
        # VPIN tracking (Volume-Synchronized Probability of Informed Trading)
        self.vpin_estimates: List[float] = []
        
    def calculate_optimal_slices(self,
                                total_size: float,
                                time_horizon: timedelta,
                                market_data: Dict) -> List[ExecutionSlice]:
        """
        Calculate optimal order slicing strategy.
        
        Args:
            total_size: Total order size
            time_horizon: Time window for execution
            market_data: Current market data including volume profile
            
        Returns:
            List of execution slices
        """
        # Adjust based on flow toxicity
        vpin = self._estimate_vpin(market_data)
        
        if vpin > self.toxicity_threshold:
            # High toxicity - use more slices, longer intervals
            num_slices = min(self.max_slices, int(total_size / 100) + 5)
            interval = max(self.min_slice_interval, time_horizon / num_slices * 1.5)
        else:
            # Normal conditions - standard slicing
            num_slices = min(self.max_slices, int(total_size / 200) + 3)
            interval = time_horizon / num_slices
        
        # Generate slices
        base_size = total_size / num_slices
        slices = []
        
        for i in range(num_slices):
            # Add slight randomization to slice sizes (±20%)
            size_variation = np.random.uniform(0.8, 1.2)
            slice_size = base_size * size_variation
            
            slice_time = datetime.now() + interval * i
            
            # Choose order type based on conditions
            if vpin > 0.8:
                order_type = OrderType.LIMIT  # Use limits in toxic flow
            elif i == 0 or i == num_slices - 1:
                order_type = OrderType.MARKET  # Market orders at start/end
            else:
                order_type = OrderType.ADAPTIVE
            
            slices.append(ExecutionSlice(
                size=slice_size,
                price=market_data.get('mid_price', 0),
                time=slice_time,
                order_type=order_type
            ))
        
        return slices
    
    def _estimate_vpin(self, market_data: Dict) -> float:
        """
        Estimate VPIN (Volume-Synchronized Probability of Informed Trading).
        
        Higher VPIN indicates more toxic flow (informed traders present).
        """
        # Simplified VPIN estimation
        volume = market_data.get('volume', 0)
        imbalance = market_data.get('volume_imbalance', 0)
        volatility = market_data.get('volatility', 0)
        
        if volume == 0:
            return 0.5
        
        # Estimate based on volume imbalance and volatility
        imbalance_ratio = abs(imbalance) / volume
        vpin = 0.5 + 0.3 * imbalance_ratio + 0.2 * min(volatility * 10, 1.0)
        
        return min(1.0, max(0.0, vpin))
    
    def detect_adverse_selection(self, 
                                order: ExecutionSlice,
                                post_trade_data: Dict) -> bool:
        """
        Detect if order suffered adverse selection.
        
        Returns True if price moved unfavorably after execution.
        """
        if not order.filled or order.actual_price is None:
            return False
        
        # Check mid price movement after execution
        mid_price_before = order.price
        mid_price_after = post_trade_data.get('mid_price', mid_price_before)
        
        # For buy orders, adverse if price went up
        # For sell orders, adverse if price went down
        price_change = (mid_price_after - mid_price_before) / mid_price_before
        
        # Adverse selection if price moved more than 2 bps against us
        return abs(price_change) > 0.0002


class AdaptiveExecutionEngine:
    """
    Execution engine that adapts to real-time market conditions.
    
    Features:
    - Dynamic participation rate adjustment
    - Volatility-based urgency scaling
    - Liquidity-seeking behavior
    - Cost-benchmark optimization
    """
    
    def __init__(self,
                 benchmark: str = 'vwap',  # 'vwap', 'twap', or 'arrival'
                 participation_cap: float = 0.05,
                 urgency_levels: Dict[str, float] = None):
        """
        Initialize adaptive execution engine.
        
        Args:
            benchmark: Target benchmark for execution
            participation_cap: Maximum participation in volume
            urgency_levels: Urgency level multipliers
        """
        self.benchmark = benchmark
        self.participation_cap = participation_cap
        self.urgency_levels = urgency_levels or {
            'low': 0.5,
            'normal': 1.0,
            'high': 2.0,
            'urgent': 4.0
        }
        
        self.execution_history: List[Dict] = []
        self.cost_model = {}
        
    def execute(self,
               symbol: str,
               size: float,
               side: str,
               urgency: str = 'normal',
               market_conditions: Dict = None) -> Dict[str, Any]:
        """
        Execute order with adaptive strategy.
        
        Args:
            symbol: Trading symbol
            size: Order size
            side: 'buy' or 'sell'
            urgency: Urgency level
            market_conditions: Current market state
            
        Returns:
            Execution result with details
        """
        market_conditions = market_conditions or {}
        
        # Determine execution strategy
        strategy = self._select_strategy(size, urgency, market_conditions)
        
        # Calculate target price based on benchmark
        target_price = self._calculate_benchmark(market_conditions)
        
        # Adjust participation rate
        base_participation = self.urgency_levels.get(urgency, 1.0) * self.participation_cap
        adjusted_participation = self._adjust_participation(
            base_participation, market_conditions
        )
        
        # Execute
        result = {
            'symbol': symbol,
            'size': size,
            'side': side,
            'urgency': urgency,
            'strategy': strategy.value,
            'target_price': target_price,
            'participation_rate': adjusted_participation,
            'execution_slices': [],
            'start_time': datetime.now(),
            'status': 'pending'
        }
        
        return result
    
    def _select_strategy(self,
                        size: float,
                        urgency: str,
                        market_conditions: Dict) -> OrderType:
        """Select optimal execution strategy"""
        volatility = market_conditions.get('volatility', 0)
        spread = market_conditions.get('spread', 0)
        
        # High volatility + high urgency = market orders
        if volatility > 0.03 and urgency in ['high', 'urgent']:
            return OrderType.MARKET
        
        # Large size relative to volume = TWAP/VWAP
        daily_volume = market_conditions.get('daily_volume', 1)
        if size / daily_volume > 0.01:  # >1% of daily volume
            return OrderType.VWAP
        
        # Wide spreads = limit orders
        mid_price = market_conditions.get('mid_price', 1)
        if spread / mid_price > 0.001:  # >10 bps spread
            return OrderType.LIMIT
        
        # Default to adaptive
        return OrderType.ADAPTIVE
    
    def _calculate_benchmark(self, market_conditions: Dict) -> float:
        """Calculate target benchmark price"""
        if self.benchmark == 'vwap':
            return market_conditions.get('vwap', market_conditions.get('mid_price', 0))
        elif self.benchmark == 'twap':
            return market_conditions.get('twap', market_conditions.get('mid_price', 0))
        else:  # arrival price
            return market_conditions.get('mid_price', 0)
    
    def _adjust_participation(self,
                            base_rate: float,
                            market_conditions: Dict) -> float:
        """Adjust participation rate based on conditions"""
        volatility = market_conditions.get('volatility', 0)
        
        # Reduce participation in high volatility
        if volatility > 0.03:
            return base_rate * 0.5
        elif volatility > 0.02:
            return base_rate * 0.7
        
        # Increase participation in trending markets with momentum
        trend_strength = market_conditions.get('trend_strength', 0)
        if trend_strength > 0.7:
            return min(base_rate * 1.3, self.participation_cap)
        
        return base_rate
    
    def update_cost_model(self, execution_result: Dict):
        """Update cost model based on execution results"""
        self.execution_history.append(execution_result)
        
        # Keep only recent history
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]
        
        # Calculate average costs by strategy
        strategy_costs = {}
        for result in self.execution_history:
            strategy = result.get('strategy')
            cost = result.get('total_cost', 0)
            
            if strategy not in strategy_costs:
                strategy_costs[strategy] = []
            strategy_costs[strategy].append(cost)
        
        # Update model
        for strategy, costs in strategy_costs.items():
            if costs:
                self.cost_model[strategy] = {
                    'mean_cost': np.mean(costs),
                    'std_cost': np.std(costs),
                    'count': len(costs)
                }
    
    def get_optimal_strategy(self, size: float, urgency: str) -> OrderType:
        """Get optimal strategy based on historical performance"""
        if not self.cost_model:
            return OrderType.ADAPTIVE
        
        # Find strategy with lowest average cost
        best_strategy = None
        best_cost = float('inf')
        
        for strategy, metrics in self.cost_model.items():
            if metrics['count'] > 10:  # Minimum sample size
                if metrics['mean_cost'] < best_cost:
                    best_cost = metrics['mean_cost']
                    best_strategy = strategy
        
        if best_strategy:
            return OrderType(best_strategy)
        
        return OrderType.ADAPTIVE


class DynamicParameterAdjuster:
    """
    Dynamically adjusts execution parameters based on real-time feedback.
    
    Uses reinforcement learning-style updates to optimize:
    - Slice sizes
    - Time intervals
    - Order type selection
    - Participation rates
    """
    
    def __init__(self,
                 learning_rate: float = 0.1,
                 exploration_rate: float = 0.2,
                 performance_window: int = 20):
        """
        Initialize dynamic parameter adjuster.
        
        Args:
            learning_rate: Rate of parameter updates
            exploration_rate: Probability of trying new parameters
            performance_window: Window for performance evaluation
        """
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.performance_window = performance_window
        
        # Current parameters
        self.parameters = {
            'slices': 5,
            'participation_rate': 0.05,
            'limit_order_pct': 0.3,
            'aggression': 0.5
        }
        
        # Performance history
        self.performance_history: List[float] = []
        self.parameter_history: List[Dict] = []
        
    def get_parameters(self, context: Dict = None) -> Dict[str, Any]:
        """
        Get current execution parameters.
        
        May explore new parameters with probability exploration_rate.
        """
        context = context or {}
        
        if np.random.random() < self.exploration_rate:
            # Explore new parameters
            return self._generate_exploratory_parameters()
        else:
            # Use current best parameters, adjusted for context
            return self._adjust_for_context(self.parameters.copy(), context)
    
    def _generate_exploratory_parameters(self) -> Dict[str, Any]:
        """Generate exploratory parameter set"""
        exploratory = self.parameters.copy()
        
        # Random perturbations
        exploratory['slices'] = max(2, min(20, 
            int(exploratory['slices'] * np.random.uniform(0.7, 1.3))))
        exploratory['participation_rate'] = max(0.01, min(0.2,
            exploratory['participation_rate'] * np.random.uniform(0.7, 1.3)))
        exploratory['limit_order_pct'] = max(0.0, min(1.0,
            exploratory['limit_order_pct'] + np.random.uniform(-0.2, 0.2)))
        exploratory['aggression'] = max(0.0, min(1.0,
            exploratory['aggression'] + np.random.uniform(-0.3, 0.3)))
        
        return exploratory
    
    def _adjust_for_context(self, params: Dict, context: Dict) -> Dict:
        """Adjust parameters based on market context"""
        volatility = context.get('volatility', 0)
        spread = context.get('spread', 0)
        
        # High volatility: more slices, less aggression
        if volatility > 0.03:
            params['slices'] = int(params['slices'] * 1.5)
            params['aggression'] = max(0.2, params['aggression'] * 0.7)
        
        # Wide spread: more limit orders
        if spread > 0.001:
            params['limit_order_pct'] = min(0.8, params['limit_order_pct'] * 1.3)
        
        return params
    
    def update(self, performance: float, parameters_used: Dict):
        """
        Update parameters based on execution performance.
        
        Args:
            performance: Performance metric (higher is better)
            parameters_used: Parameters used for this execution
        """
        self.performance_history.append(performance)
        self.parameter_history.append(parameters_used)
        
        # Keep only recent history
        if len(self.performance_history) > self.performance_window:
            self.performance_history.pop(0)
            self.parameter_history.pop(0)
        
        # Update parameters if we have enough history
        if len(self.performance_history) >= self.performance_window // 2:
            self._update_parameters()
    
    def _update_parameters(self):
        """Update parameters based on recent performance"""
        if len(self.performance_history) < 3:
            return
        
        recent_perf = np.mean(self.performance_history[-10:])
        older_perf = np.mean(self.performance_history[:-10]) if len(self.performance_history) > 10 else recent_perf
        
        # If recent performance is better, move toward recent parameters
        if recent_perf > older_perf:
            recent_params = self.parameter_history[-1]
            for key in self.parameters:
                if key in recent_params:
                    # Gradual shift toward better parameters
                    diff = recent_params[key] - self.parameters[key]
                    self.parameters[key] += self.learning_rate * diff
            
            logger.debug(f"Parameters updated toward better config: {self.parameters}")
    
    def get_best_parameters(self) -> Dict[str, Any]:
        """Get best performing parameters from history"""
        if not self.performance_history:
            return self.parameters
        
        # Find best performing parameter set
        best_idx = np.argmax(self.performance_history)
        return self.parameter_history[best_idx]
    
    def reset(self):
        """Reset to default parameters"""
        self.parameters = {
            'slices': 5,
            'participation_rate': 0.05,
            'limit_order_pct': 0.3,
            'aggression': 0.5
        }
        self.performance_history.clear()
        self.parameter_history.clear()
