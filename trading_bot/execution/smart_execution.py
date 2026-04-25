"""Smart Order Execution Algorithms Module

This module implements advanced order execution algorithms including:
- VWAP (Volume-Weighted Average Price)
- TWAP (Time-Weighted Average Price)
- Iceberg Orders
- Smart Order Routing (SOR)
"""

import logging
logger = logging.getLogger(__name__)
import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import time
import threading
import queue
from loguru import logger
import numpy
import pandas


class ExecutionAlgorithm(Enum):
    """Types of execution algorithms."""
    VWAP = auto()
    TWAP = auto()
    ICEBERG = auto()
    SMART_ORDER_ROUTING = auto()
    IMPLEMENTATION_SHORTFALL = auto()
    ADAPTIVE = auto()
    SNIPER = auto()


class OrderSide(Enum):
    """Order side (buy or sell)."""
    BUY = auto()
    SELL = auto()


class OrderStatus(Enum):
    """Status of an order."""
    PENDING = auto()
    ACTIVE = auto()
    PARTIALLY_FILLED = auto()
    FILLED = auto()
    CANCELLED = auto()
    REJECTED = auto()


@dataclass
class OrderSlice:
    """A slice of a parent order."""
    id: str
    parent_id: str
    quantity: float
    price: Optional[float]
    timestamp: datetime
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    venue: Optional[str] = None


@dataclass
class ExecutionReport:
    """Report on execution performance."""
    algorithm: ExecutionAlgorithm
    symbol: str
    side: OrderSide
    total_quantity: float
    filled_quantity: float
    average_price: float
    benchmark_price: float
    slippage: float
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    num_slices: int
    slices: List[OrderSlice]
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class SmartExecutionEngine:
    """Engine for smart order execution algorithms."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the smart execution engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.execution_queue = queue.Queue()
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        self.execution_thread = None
        self.running = False
        
        # Initialize algorithm handlers
        self.algorithms = {
            ExecutionAlgorithm.VWAP: VWAPExecutor(self.config.get('vwap_config', {})),
            ExecutionAlgorithm.TWAP: TWAPExecutor(self.config.get('twap_config', {})),
            ExecutionAlgorithm.ICEBERG: IcebergExecutor(self.config.get('iceberg_config', {})),
            ExecutionAlgorithm.SMART_ORDER_ROUTING: SORExecutor(self.config.get('sor_config', {})),
            ExecutionAlgorithm.IMPLEMENTATION_SHORTFALL: ISExecutor(self.config.get('is_config', {})),
            ExecutionAlgorithm.ADAPTIVE: AdaptiveExecutor(self.config.get('adaptive_config', {})),
            ExecutionAlgorithm.SNIPER: SniperExecutor(self.config.get('sniper_config', {})),
        }
        
        logger.info("SmartExecutionEngine initialized")
    
    def start(self):
        """Start the execution engine."""
        if self.execution_thread is not None and self.execution_thread.is_alive():
            logger.warning("Execution engine already running")
            return
        
        self.running = True
        self.execution_thread = threading.Thread(
            target=self._execution_loop,
            daemon=True,
            name="ExecutionThread"
        )
        self.execution_thread.start()
        logger.info("Execution engine started")
    
    def stop(self):
        """Stop the execution engine."""
        self.running = False
        if self.execution_thread is not None:
            self.execution_thread.join(timeout=5.0)
            logger.info("Execution engine stopped")
    
    def _execution_loop(self):
        """Main execution loop."""
        while self.running:
            try:
                try:
                    # Get next order from queue (non-blocking)
                    order = self.execution_queue.get(block=True, timeout=1.0)
                    self._process_order(order)
                    self.execution_queue.task_done()
                except queue.Empty:
                    continue
                
                # Process active orders
                self._process_active_orders()
                
                # Sleep briefly
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                time.sleep(1.0)
    
    def _process_order(self, order: Dict[str, Any]):
        """Process a new order."""
        try:
            order_id = order.get('id')
            algorithm = order.get('algorithm')
            
            if algorithm not in self.algorithms:
                logger.error(f"Unknown algorithm: {algorithm}")
                return
            
            # Add to active orders
            self.active_orders[order_id] = order
            
            # Initialize execution
            executor = self.algorithms[algorithm]
            executor.initialize(order)
            
            logger.info(f"Started execution of order {order_id} using {algorithm.name}")
            
        except Exception as e:
            logger.error(f"Error processing order: {e}")
    
    def _process_active_orders(self):
        """Process all active orders."""
        for order_id, order in list(self.active_orders.items()):
            try:
                algorithm = order.get('algorithm')
                executor = self.algorithms[algorithm]
                
                # Check if order is complete
                if executor.is_complete(order):
                    # Generate execution report
                    report = executor.generate_report(order)
                    
                    # Remove from active orders
                    del self.active_orders[order_id]
                    
                    # Call completion callback if provided
                    callback = order.get('completion_callback')
                    if callback is not None:
                        callback(report)
                    
                    logger.info(f"Completed execution of order {order_id}")
                    continue
                
                # Execute next slice if needed
                executor.execute_next_slice(order)
                
            except Exception as e:
                logger.error(f"Error processing active order {order_id}: {e}")
    
    def execute_order(self, symbol: str, side: OrderSide, quantity: float, 
                    algorithm: ExecutionAlgorithm, 
                    params: Optional[Dict[str, Any]] = None,
                    callback: Optional[Callable[[ExecutionReport], None]] = None) -> str:
        """Execute an order using the specified algorithm.
        
        Args:
            symbol: Symbol to trade
            side: Order side (buy or sell)
            quantity: Quantity to trade
            algorithm: Execution algorithm to use
            params: Additional parameters for the algorithm
            callback: Callback function to call when execution is complete
            
        Returns:
            Order ID
        """
        # Generate order ID
        order_id = f"order_{int(time.time() * 1000)}_{hash(symbol) % 10000}"
        
        # Create order
        order = {
            'id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'algorithm': algorithm,
            'params': params or {},
            'status': OrderStatus.PENDING,
            'creation_time': datetime.now(),
            'last_update_time': datetime.now(),
            'filled_quantity': 0.0,
            'average_price': 0.0,
            'slices': [],
            'completion_callback': callback
        }
        
        # Add to execution queue
        self.execution_queue.put(order)
        
        logger.info(f"Queued order {order_id} for execution using {algorithm.name}")
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if order was cancelled, False otherwise
        """
        if order_id not in self.active_orders:
            logger.warning(f"Order {order_id} not found")
            return False
        
        order = self.active_orders[order_id]
        algorithm = order.get('algorithm')
        executor = self.algorithms[algorithm]
        
        # Cancel order
        success = executor.cancel(order)
        
        if success:
            # Update status
            order['status'] = OrderStatus.CANCELLED
            order['last_update_time'] = datetime.now()
            
            # Generate report
            report = executor.generate_report(order)
            
            # Call completion callback if provided
            callback = order.get('completion_callback')
            if callback is not None:
                callback(report)
            
            # Remove from active orders
            del self.active_orders[order_id]
            
            logger.info(f"Cancelled order {order_id}")
        
        return success
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an order.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Order status dictionary, or None if order not found
        """
        if order_id not in self.active_orders:
            return None
        
        order = self.active_orders[order_id]
        return {
            'id': order['id'],
            'symbol': order['symbol'],
            'side': order['side'],
            'quantity': order['quantity'],
            'algorithm': order['algorithm'],
            'status': order['status'],
            'filled_quantity': order['filled_quantity'],
            'average_price': order['average_price'],
            'creation_time': order['creation_time'],
            'last_update_time': order['last_update_time'],
            'num_slices': len(order['slices'])
        }


class BaseExecutor:
    """Base class for execution algorithms."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the executor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
    
    def initialize(self, order: Dict[str, Any]):
        """Initialize execution for an order.
        
        Args:
            order: Order dictionary
        """
        logger.info(f"Initializing execution for order {order.get('order_id', 'unknown')}")
        order['execution_state'] = {'initialized': True, 'slices': []}
        return order
    
    def execute_next_slice(self, order: Dict[str, Any]):
        """Execute the next slice of an order.
        
        Args:
            order: Order dictionary
        """
        logger.info(f"Executing next slice for order {order.get('order_id', 'unknown')}")
        # Default implementation: execute entire order at once
        remaining = order['quantity'] - order.get('filled_quantity', 0)
        if remaining > 0:
            order['filled_quantity'] = order.get('filled_quantity', 0) + remaining
            order['status'] = OrderStatus.FILLED
        return order
    
    def is_complete(self, order: Dict[str, Any]) -> bool:
        """Check if an order is complete.
        
        Args:
            order: Order dictionary
            
        Returns:
            True if order is complete, False otherwise
        """
        return order['filled_quantity'] >= order['quantity'] or order['status'] in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]
    
    def cancel(self, order: Dict[str, Any]) -> bool:
        """Cancel an order.
        
        Args:
            order: Order dictionary
            
        Returns:
            True if order was cancelled, False otherwise
        """
        # Cancel any pending slices
        for slice in order['slices']:
            if slice['status'] == OrderStatus.PENDING:
                slice['status'] = OrderStatus.CANCELLED
        
        return True
    
    def generate_report(self, order: Dict[str, Any]) -> ExecutionReport:
        """Generate an execution report.
        
        Args:
            order: Order dictionary
            
        Returns:
            Execution report
        """
        # Calculate metrics
        start_time = order['creation_time']
        end_time = order['last_update_time']
        duration_seconds = (end_time - start_time).total_seconds()
        
        # Create slice objects
        slices = [
            OrderSlice(
                id=slice['id'],
                parent_id=order['id'],
                quantity=slice['quantity'],
                price=slice.get('price'),
                timestamp=slice['timestamp'],
                status=slice['status'],
                filled_quantity=slice.get('filled_quantity', 0.0),
                average_fill_price=slice.get('average_fill_price', 0.0),
                venue=slice.get('venue')
            )
            for slice in order['slices']
        ]
        
        # Get benchmark price (implementation-specific)
        benchmark_price = self._get_benchmark_price(order)
        
        # Calculate slippage
        slippage = 0.0
        if benchmark_price > 0 and order['average_price'] > 0:
            if order['side'] == OrderSide.BUY:
                slippage = (order['average_price'] - benchmark_price) / benchmark_price
            else:
                slippage = (benchmark_price - order['average_price']) / benchmark_price
        
        # Create report
        return ExecutionReport(
            algorithm=order['algorithm'],
            symbol=order['symbol'],
            side=order['side'],
            total_quantity=order['quantity'],
            filled_quantity=order['filled_quantity'],
            average_price=order['average_price'],
            benchmark_price=benchmark_price,
            slippage=slippage,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            num_slices=len(order['slices']),
            slices=slices,
            performance_metrics=self._calculate_performance_metrics(order)
        )
    
    def _get_benchmark_price(self, order: Dict[str, Any]) -> float:
        """Get the benchmark price for an order.
        
        Args:
            order: Order dictionary
            
        Returns:
            Benchmark price
        """
        # Default implementation uses the first slice price
        if order['slices']:
            return order['slices'][0].get('price', 0.0)
        return 0.0
    
    def _calculate_performance_metrics(self, order: Dict[str, Any]) -> Dict[str, float]:
        """Calculate performance metrics for an order.
        
        Args:
            order: Order dictionary
            
        Returns:
            Dictionary of performance metrics
        """
        # Default implementation with basic metrics
        return {
            'fill_rate': order['filled_quantity'] / order['quantity'] if order['quantity'] > 0 else 0.0,
            'execution_time': (order['last_update_time'] - order['creation_time']).total_seconds()
        }


class VWAPExecutor(BaseExecutor):
    """Volume-Weighted Average Price execution algorithm."""
    
    def initialize(self, order: Dict[str, Any]):
        """Initialize VWAP execution.
        
        Args:
            order: Order dictionary
        """
        params = order.get('params', {})
        
        # Get parameters
        start_time = params.get('start_time', datetime.now())
        end_time = params.get('end_time', start_time + timedelta(hours=1))
        num_slices = params.get('num_slices', 10)
        
        # Get volume profile (in a real implementation, this would use historical data)
        volume_profile = self._get_volume_profile(order['symbol'], start_time, end_time, num_slices)
        
        # Calculate slice sizes based on volume profile
        total_quantity = order['quantity']
        slices = []
        
        for i, volume_pct in enumerate(volume_profile):
            slice_time = start_time + (end_time - start_time) * (i / num_slices)
            
            slice_quantity = total_quantity * volume_pct
            
            slice_id = f"{order['id']}_slice_{i}"
            
            slices.append({
                'id': slice_id,
                'quantity': slice_quantity,
                'timestamp': slice_time,
                'status': OrderStatus.PENDING,
                'filled_quantity': 0.0,
                'average_fill_price': 0.0
            })
        
        # Update order
        order['slices'] = slices
        order['status'] = OrderStatus.ACTIVE
        order['start_time'] = start_time
        order['end_time'] = end_time
        order['last_update_time'] = datetime.now()
    
    def execute_next_slice(self, order: Dict[str, Any]):
        """Execute the next slice of a VWAP order.
        
        Args:
            order: Order dictionary
        """
        # Find next pending slice that's due
        now = datetime.now()
        
        for slice in order['slices']:
            if slice['status'] == OrderStatus.PENDING and slice['timestamp'] <= now:
                # In a real implementation, this would submit the order to the market
                # For simulation, we'll just mark it as filled
                
                # Simulate execution price (in a real implementation, this would be the actual fill price)
                current_price = self._get_current_price(order['symbol'])
                
                # Update slice
                slice['status'] = OrderStatus.FILLED
                slice['filled_quantity'] = slice['quantity']
                slice['average_fill_price'] = current_price
                
                # Update order
                order['filled_quantity'] += slice['quantity']
                
                # Update average price
                if order['filled_quantity'] > 0:
                    order['average_price'] = (
                        (order['average_price'] * (order['filled_quantity'] - slice['quantity'])) +
                        (slice['average_fill_price'] * slice['quantity'])
                    ) / order['filled_quantity']
                
                order['last_update_time'] = now
                
                # Check if order is complete
                if order['filled_quantity'] >= order['quantity']:
                    order['status'] = OrderStatus.FILLED
                
                logger.info(f"Executed VWAP slice {slice['id']} for order {order['id']}: "
                           f"{slice['quantity']} @ {slice['average_fill_price']}")
                
                # Only execute one slice per call
                break
    
    def _get_volume_profile(self, symbol: str, start_time: datetime, end_time: datetime, num_slices: int) -> List[float]:
        """Get the volume profile for a symbol.
        
        In a real implementation, this would use historical volume data.
        
        Args:
            symbol: Symbol to get volume profile for
            start_time: Start time
            end_time: End time
            num_slices: Number of slices
            
        Returns:
            List of volume percentages for each slice
        """
        # For simulation, we'll use a typical U-shaped volume profile
        x = np.linspace(0, 1, num_slices)
        volume_profile = 1 - 0.5 * np.sin(np.pi * x)
        
        # Normalize
        volume_profile = volume_profile / np.sum(volume_profile)
        
        return volume_profile.tolist()
    
    def _get_current_price(self, symbol: str) -> float:
        """Get the current price for a symbol.
        
        In a real implementation, this would get the actual market price.
        
        Args:
            symbol: Symbol to get price for
            
        Returns:
            Current price
        """
        # For simulation, we'll use a random price
        # In a real implementation, this would get the actual market price
        base_price = 100.0
        return base_price * (1 + np.random.normal(0, 0.001))
    
    def _get_benchmark_price(self, order: Dict[str, Any]) -> float:
        """Get the VWAP benchmark price.
        
        Args:
            order: Order dictionary
            
        Returns:
            VWAP benchmark price
        """
        # In a real implementation, this would calculate the actual VWAP
        # For simulation, we'll use the average of all slice prices
        if not order['slices']:
            return 0.0
        
        prices = [slice.get('average_fill_price', 0.0) for slice in order['slices'] 
                 if slice['status'] == OrderStatus.FILLED]
        
        if not prices:
            return 0.0
        
        return sum(prices) / len(prices)


class TWAPExecutor(BaseExecutor):
    """Time-Weighted Average Price execution algorithm."""
    
    def initialize(self, order: Dict[str, Any]):
        """Initialize TWAP execution.
        
        Args:
            order: Order dictionary
        """
        params = order.get('params', {})
        
        # Get parameters
        start_time = params.get('start_time', datetime.now())
        end_time = params.get('end_time', start_time + timedelta(hours=1))
        num_slices = params.get('num_slices', 10)
        
        # Calculate time intervals
        interval = (end_time - start_time) / num_slices
        
        # Calculate slice sizes (equal for TWAP)
        total_quantity = order['quantity']
        slice_quantity = total_quantity / num_slices
        
        slices = []
        
        for i in range(num_slices):
            slice_time = start_time + interval * i
            
            slice_id = f"{order['id']}_slice_{i}"
            
            slices.append({
                'id': slice_id,
                'quantity': slice_quantity,
                'timestamp': slice_time,
                'status': OrderStatus.PENDING,
                'filled_quantity': 0.0,
                'average_fill_price': 0.0
            })
        
        # Update order
        order['slices'] = slices
        order['status'] = OrderStatus.ACTIVE
        order['start_time'] = start_time
        order['end_time'] = end_time
        order['last_update_time'] = datetime.now()
    
    def execute_next_slice(self, order: Dict[str, Any]):
        """Execute the next slice of a TWAP order.
        
        Args:
            order: Order dictionary
        """
        # Find next pending slice that's due
        now = datetime.now()
        
        for slice in order['slices']:
            if slice['status'] == OrderStatus.PENDING and slice['timestamp'] <= now:
                # In a real implementation, this would submit the order to the market
                # For simulation, we'll just mark it as filled
                
                # Simulate execution price (in a real implementation, this would be the actual fill price)
                current_price = self._get_current_price(order['symbol'])
                
                # Update slice
                slice['status'] = OrderStatus.FILLED
                slice['filled_quantity'] = slice['quantity']
                slice['average_fill_price'] = current_price
                
                # Update order
                order['filled_quantity'] += slice['quantity']
                
                # Update average price
                if order['filled_quantity'] > 0:
                    order['average_price'] = (
                        (order['average_price'] * (order['filled_quantity'] - slice['quantity'])) +
                        (slice['average_fill_price'] * slice['quantity'])
                    ) / order['filled_quantity']
                
                order['last_update_time'] = now
                
                # Check if order is complete
                if order['filled_quantity'] >= order['quantity']:
                    order['status'] = OrderStatus.FILLED
                
                logger.info(f"Executed TWAP slice {slice['id']} for order {order['id']}: "
                           f"{slice['quantity']} @ {slice['average_fill_price']}")
                
                # Only execute one slice per call
                break
    
    def _get_current_price(self, symbol: str) -> float:
        """Get the current price for a symbol.
        
        In a real implementation, this would get the actual market price.
        
        Args:
            symbol: Symbol to get price for
            
        Returns:
            Current price
        """
        # For simulation, we'll use a random price
        # In a real implementation, this would get the actual market price
        base_price = 100.0
        return base_price * (1 + np.random.normal(0, 0.001))


class IcebergExecutor(BaseExecutor):
    """Iceberg order execution algorithm."""
    
    def initialize(self, order: Dict[str, Any]):
        """Initialize iceberg execution.
        
        Args:
            order: Order dictionary
        """
        params = order.get('params', {})
        
        # Get parameters
        display_size = params.get('display_size', order['quantity'] * 0.1)
        max_slices = params.get('max_slices', 100)
        
        # Calculate number of slices
        total_quantity = order['quantity']
        num_slices = min(max_slices, int(np.ceil(total_quantity / display_size)))
        
        # Create slices
        slices = []
        remaining_quantity = total_quantity
        
        for i in range(num_slices):
            slice_quantity = min(display_size, remaining_quantity)
            remaining_quantity -= slice_quantity
            
            slice_id = f"{order['id']}_slice_{i}"
            
            slices.append({
                'id': slice_id,
                'quantity': slice_quantity,
                'timestamp': datetime.now() if i == 0 else None,  # Only first slice is active initially
                'status': OrderStatus.PENDING if i == 0 else OrderStatus.PENDING,
                'filled_quantity': 0.0,
                'average_fill_price': 0.0
            })
        
        # Update order
        order['slices'] = slices
        order['status'] = OrderStatus.ACTIVE
        order['last_update_time'] = datetime.now()
    
    def execute_next_slice(self, order: Dict[str, Any]):
        """Execute the next slice of an iceberg order.
        
        Args:
            order: Order dictionary
        """
        # Find active slice
        active_slice = None
        next_slice_index = None
        
        for i, slice in enumerate(order['slices']):
            if slice['status'] == OrderStatus.PENDING and slice['timestamp'] is not None:
                active_slice = slice
                next_slice_index = i + 1
                break
        
        if active_slice is None:
            return
        
        # In a real implementation, this would check if the slice has been filled
        # For simulation, we'll just mark it as filled with some probability
        
        if np.random.random() < 0.2:  # 20% chance of fill per call
            # Simulate execution price
            current_price = self._get_current_price(order['symbol'])
            
            # Update slice
            active_slice['status'] = OrderStatus.FILLED
            active_slice['filled_quantity'] = active_slice['quantity']
            active_slice['average_fill_price'] = current_price
            
            # Update order
            order['filled_quantity'] += active_slice['quantity']
            
            # Update average price
            if order['filled_quantity'] > 0:
                order['average_price'] = (
                    (order['average_price'] * (order['filled_quantity'] - active_slice['quantity'])) +
                    (active_slice['average_fill_price'] * active_slice['quantity'])
                ) / order['filled_quantity']
            
            order['last_update_time'] = datetime.now()
            
            # Activate next slice if available
            if next_slice_index is not None and next_slice_index < len(order['slices']):
                order['slices'][next_slice_index]['timestamp'] = datetime.now()
            
            # Check if order is complete
            if order['filled_quantity'] >= order['quantity']:
                order['status'] = OrderStatus.FILLED
            
            logger.info(f"Executed iceberg slice {active_slice['id']} for order {order['id']}: "
                       f"{active_slice['quantity']} @ {active_slice['average_fill_price']}")
    
    def _get_current_price(self, symbol: str) -> float:
        """Get the current price for a symbol."""
        base_price = 100.0
        return base_price * (1 + np.random.normal(0, 0.001))


# Placeholder implementations for other executors
class SORExecutor(BaseExecutor):
    """Smart Order Routing execution algorithm."""
    
    def initialize(self, order: Dict[str, Any]):
        """Initialize SOR execution."""
        # Placeholder implementation
        order['status'] = OrderStatus.ACTIVE
        order['last_update_time'] = datetime.now()
    
    def execute_next_slice(self, order: Dict[str, Any]):
        """Execute the next slice of a SOR order."""
        # Placeholder implementation
        pass


class ISExecutor(BaseExecutor):
    """Implementation Shortfall execution algorithm."""
    
    def initialize(self, order: Dict[str, Any]):
        """Initialize IS execution."""
        # Placeholder implementation
        order['status'] = OrderStatus.ACTIVE
        order['last_update_time'] = datetime.now()
    
    def execute_next_slice(self, order: Dict[str, Any]):
        """Execute the next slice of an IS order."""
        # Placeholder implementation
        pass


class AdaptiveExecutor(BaseExecutor):
    """Adaptive execution algorithm."""
    
    def initialize(self, order: Dict[str, Any]):
        """Initialize adaptive execution."""
        # Placeholder implementation
        order['status'] = OrderStatus.ACTIVE
        order['last_update_time'] = datetime.now()
    
    def execute_next_slice(self, order: Dict[str, Any]):
        """Execute the next slice of an adaptive order."""
        # Placeholder implementation
        pass


class SniperExecutor(BaseExecutor):
    """Sniper execution algorithm."""
    
    def initialize(self, order: Dict[str, Any]):
        """Initialize sniper execution."""
        # Placeholder implementation
        order['status'] = OrderStatus.ACTIVE
        order['last_update_time'] = datetime.now()
    
    def execute_next_slice(self, order: Dict[str, Any]):
        """Execute the next slice of a sniper order."""
        # Placeholder implementation
        pass


@dataclass
class KillSwitchPrediction:
    """Prediction of trade failure probability"""
    trade_id: str
    timestamp: datetime
    failure_probability: float  # 0-1
    confidence: float
    leading_indicators: List[str]
    recommended_action: str  # 'hold', 'reduce', 'exit_now'
    estimated_loss_if_fail: float
    time_to_decision: int  # seconds


class TradeKillSwitchPredictor:
    """
    Trade Kill Switch Predictor
    
    Predict: "This trade will fail BEFORE it fails"
    
    Uses:
    - Early exit
    - Capital preservation
    - Drawdown compression
    
    Inputs:
    - Microstructure deterioration
    - Order flow reversal
    - Spread widening
    - Failed continuation patterns
    """
    
    def __init__(self, warning_threshold: float = 0.6, kill_threshold: float = 0.8):
        self.warning_threshold = warning_threshold
        self.kill_threshold = kill_threshold
        
        # Historical predictions for calibration
        self.prediction_history: List[KillSwitchPrediction] = []
        self.outcome_history: Dict[str, Dict] = {}
        
        # Calibration tracking
        self.calibration_stats = {
            'true_positives': 0,
            'false_positives': 0,
            'true_negatives': 0,
            'false_negatives': 0
        }
    
    def predict_failure(
        self,
        trade: Dict[str, Any],
        microstructure: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> KillSwitchPrediction:
        """
        Predict probability that trade will fail.
        
        Args:
            trade: Current trade details
            microstructure: Real-time microstructure data
            market_context: Market context
            
        Returns:
            KillSwitchPrediction with failure probability
        """
        failure_signals = {}
        leading_indicators = []
        
        # 1. Microstructure Deterioration
        micro_deterioration = self._detect_microstructure_deterioration(microstructure, trade)
        failure_signals['microstructure'] = micro_deterioration
        if micro_deterioration > 0.6:
            leading_indicators.append("Order book depth deterioration")
        
        # 2. Order Flow Reversal
        flow_reversal = self._detect_order_flow_reversal(microstructure, trade)
        failure_signals['flow_reversal'] = flow_reversal
        if flow_reversal > 0.6:
            leading_indicators.append("Order flow reversal detected")
        
        # 3. Spread Widening
        spread_widening = self._detect_spread_widening(microstructure, trade)
        failure_signals['spread'] = spread_widening
        if spread_widening > 0.6:
            leading_indicators.append("Bid-ask spread widening")
        
        # 4. Failed Continuation Pattern
        failed_continuation = self._detect_failed_continuation(market_context, trade)
        failure_signals['continuation'] = failed_continuation
        if failed_continuation > 0.6:
            leading_indicators.append("Failed continuation pattern")
        
        # 5. Momentum Divergence
        momentum_divergence = self._detect_momentum_divergence(market_context, trade)
        failure_signals['momentum'] = momentum_divergence
        if momentum_divergence > 0.6:
            leading_indicators.append("Price-momentum divergence")
        
        # 6. Volume Profile Shift
        volume_shift = self._detect_volume_profile_shift(microstructure, trade)
        failure_signals['volume'] = volume_shift
        if volume_shift > 0.6:
            leading_indicators.append("Volume profile shift")
        
        # Calculate composite failure probability
        failure_prob = self._calculate_failure_probability(failure_signals)
        
        # Determine recommended action
        action = self._determine_action(failure_prob, failure_signals)
        
        # Estimate loss if trade fails
        est_loss = self._estimate_loss_if_fail(trade, failure_signals)
        
        prediction = KillSwitchPrediction(
            trade_id=trade.get('id', 'unknown'),
            timestamp=datetime.now(),
            failure_probability=failure_prob,
            confidence=self._calculate_confidence(failure_signals),
            leading_indicators=leading_indicators,
            recommended_action=action,
            estimated_loss_if_fail=est_loss,
            time_to_decision=self._estimate_decision_time(failure_signals)
        )
        
        self.prediction_history.append(prediction)
        
        if failure_prob > self.kill_threshold:
            logger.critical(f"KILL SWITCH TRIGGERED for trade {prediction.trade_id}: "
                          f"{failure_prob:.1%} failure probability")
        elif failure_prob > self.warning_threshold:
            logger.warning(f"Kill switch warning for trade {prediction.trade_id}: "
                         f"{failure_prob:.1%} failure probability")
        
        return prediction
    
    def _detect_microstructure_deterioration(
        self, microstructure: Dict, trade: Dict
    ) -> float:
        """Detect deterioration in microstructure conditions."""
        score = 0.0
        
        # Order book depth reduction
        current_depth = microstructure.get('bid_depth', 0) + microstructure.get('ask_depth', 0)
        entry_depth = trade.get('entry_order_book_depth', current_depth)
        
        if entry_depth > 0:
            depth_ratio = current_depth / entry_depth
            if depth_ratio < 0.5:
                score += 0.4
            elif depth_ratio < 0.7:
                score += 0.2
        
        # Increase in large orders against position
        large_orders_against = microstructure.get('large_orders_against', 0)
        if large_orders_against > 3:
            score += min(0.3, large_orders_against * 0.1)
        
        # VWAP deviation (price moving against position)
        vwap = microstructure.get('vwap', 0)
        current_price = microstructure.get('last_price', 0)
        entry_price = trade.get('entry_price', current_price)
        
        if trade.get('direction') == 'buy':
            if current_price < vwap * 0.998:  # Below VWAP
                score += 0.3
        else:  # sell
            if current_price > vwap * 1.002:  # Above VWAP
                score += 0.3
        
        return min(1.0, score)
    
    def _detect_order_flow_reversal(self, microstructure: Dict, trade: Dict) -> float:
        """Detect reversal in order flow direction."""
        score = 0.0
        
        # Delta change (aggressive buy vs sell volume)
        current_delta = microstructure.get('delta', 0)
        entry_delta = trade.get('entry_delta', 0)
        
        if trade.get('direction') == 'buy':
            # We bought, want positive delta (buying pressure)
            if current_delta < 0 and entry_delta > 0:
                score += 0.5  # Complete reversal
            elif current_delta < entry_delta * 0.5:
                score += 0.3
        else:  # sell
            # We sold, want negative delta (selling pressure)
            if current_delta > 0 and entry_delta < 0:
                score += 0.5
            elif current_delta > entry_delta * 0.5:
                score += 0.3
        
        # Trade imbalance shift
        imbalance = microstructure.get('trade_imbalance', 0)
        if trade.get('direction') == 'buy' and imbalance < -0.3:
            score += 0.3
        elif trade.get('direction') == 'sell' and imbalance > 0.3:
            score += 0.3
        
        return min(1.0, score)
    
    def _detect_spread_widening(self, microstructure: Dict, trade: Dict) -> float:
        """Detect adverse spread widening."""
        current_spread = microstructure.get('spread', 0)
        entry_spread = trade.get('entry_spread', current_spread)
        avg_spread = microstructure.get('avg_spread', entry_spread)
        
        if entry_spread > 0:
            spread_ratio = current_spread / entry_spread
            if spread_ratio > 3.0:
                return 0.8
            elif spread_ratio > 2.0:
                return 0.5
            elif spread_ratio > 1.5:
                return 0.3
        
        # Compare to average
        if avg_spread > 0 and current_spread > avg_spread * 2:
            return 0.4
        
        return 0.0
    
    def _detect_failed_continuation(self, market_context: Dict, trade: Dict) -> float:
        """Detect failed continuation pattern."""
        score = 0.0
        
        # Time since entry
        time_since_entry = market_context.get('minutes_since_entry', 0)
        
        # Expected move not materializing
        current_pnl = trade.get('unrealized_pnl', 0)
        expected_pnl = trade.get('expected_pnl', 0)
        
        if time_since_entry > 5 and current_pnl < expected_pnl * 0.2:
            score += 0.4
        
        if time_since_entry > 15 and current_pnl < 0:
            score += 0.3
        
        # Price action (lower highs for longs, higher lows for shorts)
        highs = market_context.get('recent_highs', [])
        lows = market_context.get('recent_lows', [])
        
        if trade.get('direction') == 'buy' and len(highs) >= 3:
            # Lower highs = failed uptrend
            if highs[-1] < highs[-2] < highs[-3]:
                score += 0.4
        elif trade.get('direction') == 'sell' and len(lows) >= 3:
            # Higher lows = failed downtrend
            if lows[-1] > lows[-2] > lows[-3]:
                score += 0.4
        
        return min(1.0, score)
    
    def _detect_momentum_divergence(self, market_context: Dict, trade: Dict) -> float:
        """Detect divergence between price and momentum."""
        price_trend = market_context.get('price_trend', 0)
        momentum = market_context.get('momentum', 0)
        
        # Bullish divergence: lower price, higher momentum (for longs)
        # Bearish divergence: higher price, lower momentum (for shorts)
        
        if trade.get('direction') == 'buy':
            if price_trend < -0.1 and momentum > 0.1:
                return 0.6  # Bullish divergence (good for longs)
            elif price_trend < 0 and momentum < 0:
                return 0.3  # Confirming downtrend
        else:  # sell
            if price_trend > 0.1 and momentum < -0.1:
                return 0.6  # Bearish divergence (good for shorts)
            elif price_trend > 0 and momentum > 0:
                return 0.3  # Confirming uptrend
        
        return 0.0
    
    def _detect_volume_profile_shift(self, microstructure: Dict, trade: Dict) -> float:
        """Detect shift in volume profile."""
        current_volume = microstructure.get('volume', 0)
        avg_volume = microstructure.get('avg_volume', current_volume)
        
        if avg_volume > 0:
            volume_ratio = current_volume / avg_volume
            
            # Low volume on supposed breakout = likely failure
            if volume_ratio < 0.5:
                return 0.4
            
            # Declining volume after entry
            volume_trend = microstructure.get('volume_trend', 0)
            if volume_trend < -0.3:
                return 0.3
        
        return 0.0
    
    def _calculate_failure_probability(self, signals: Dict[str, float]) -> float:
        """Calculate composite failure probability."""
        if not signals:
            return 0.0
        
        weights = {
            'microstructure': 0.25,
            'flow_reversal': 0.25,
            'spread': 0.15,
            'continuation': 0.15,
            'momentum': 0.10,
            'volume': 0.10
        }
        
        weighted_sum = sum(
            signals.get(k, 0) * v for k, v in weights.items()
        )
        
        # Boost if multiple signals present
        high_signals = sum(1 for v in signals.values() if v > 0.5)
        if high_signals >= 4:
            weighted_sum *= 1.2
        
        return min(1.0, weighted_sum)
    
    def _determine_action(self, failure_prob: float, signals: Dict) -> str:
        """Determine recommended action based on failure probability."""
        if failure_prob > self.kill_threshold:
            return 'exit_now'
        elif failure_prob > self.warning_threshold:
            return 'reduce'
        elif failure_prob > 0.4:
            return 'hold_caution'
        else:
            return 'hold'
    
    def _calculate_confidence(self, signals: Dict) -> float:
        """Calculate confidence in prediction."""
        # Higher confidence with more signals
        num_signals = len([v for v in signals.values() if v > 0.3])
        return min(1.0, 0.5 + num_signals * 0.1)
    
    def _estimate_loss_if_fail(self, trade: Dict, signals: Dict) -> float:
        """Estimate potential loss if trade fails."""
        position_size = trade.get('position_size', 0)
        entry_price = trade.get('entry_price', 0)
        stop_price = trade.get('stop_price', entry_price * 0.98)
        
        if position_size > 0 and entry_price > 0:
            potential_loss = abs(position_size * (stop_price - entry_price))
            
            # Adjust based on failure signal strength
            max_signal = max(signals.values()) if signals else 0
            return potential_loss * (0.5 + max_signal * 0.5)
        
        return 0.0
    
    def _estimate_decision_time(self, signals: Dict) -> int:
        """Estimate seconds until decision must be made."""
        max_signal = max(signals.values()) if signals else 0
        
        if max_signal > 0.8:
            return 10
        elif max_signal > 0.6:
            return 60
        elif max_signal > 0.4:
            return 300
        else:
            return 900
    
    def record_outcome(self, trade_id: str, actual_outcome: Dict):
        """Record actual outcome for calibration."""
        self.outcome_history[trade_id] = actual_outcome
        
        # Find corresponding prediction
        prediction = None
        for p in reversed(self.prediction_history):
            if p.trade_id == trade_id:
                prediction = p
                break
        
        if prediction:
            # Update calibration stats
            predicted_fail = prediction.failure_probability > self.warning_threshold
            actual_fail = actual_outcome.get('pnl', 0) < 0
            
            if predicted_fail and actual_fail:
                self.calibration_stats['true_positives'] += 1
            elif predicted_fail and not actual_fail:
                self.calibration_stats['false_positives'] += 1
            elif not predicted_fail and not actual_fail:
                self.calibration_stats['true_negatives'] += 1
            else:
                self.calibration_stats['false_negatives'] += 1
    
    def get_calibration_report(self) -> Dict[str, Any]:
        """Get calibration statistics."""
        stats = self.calibration_stats
        total = sum(stats.values())
        
        if total == 0:
            return {'error': 'No data for calibration'}
        
        precision = stats['true_positives'] / (stats['true_positives'] + stats['false_positives']) \
            if (stats['true_positives'] + stats['false_positives']) > 0 else 0
        
        recall = stats['true_positives'] / (stats['true_positives'] + stats['false_negatives']) \
            if (stats['true_positives'] + stats['false_negatives']) > 0 else 0
        
        return {
            'total_predictions': total,
            'precision': precision,
            'recall': recall,
            'f1_score': 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0,
            'calibration_stats': stats,
            'current_kill_threshold': self.kill_threshold,
            'recommended_threshold': self._recommend_threshold()
        }
    
    def _recommend_threshold(self) -> float:
        """Recommend optimal kill threshold based on calibration."""
        # Simple heuristic: if too many false positives, raise threshold
        stats = self.calibration_stats
        fp_rate = stats['false_positives'] / (stats['false_positives'] + stats['true_negatives']) \
            if (stats['false_positives'] + stats['true_negatives']) > 0 else 0
        
        if fp_rate > 0.3:
            return min(0.9, self.kill_threshold + 0.1)
        elif fp_rate < 0.1:
            return max(0.5, self.kill_threshold - 0.05)
        
        return self.kill_threshold


class ExecutionAlphaExtractor:
    """
    Execution Alpha Extractor
    
    Most people ignore this.
    
    Idea: Separate signal alpha vs execution alpha
    
    You can make money even with average signals if execution is superior.
    
    Focus:
    - order timing
    - liquidity routing
    - impact minimization
    """
    
    def __init__(self):
        self.execution_history: List[Dict] = []
        self.alpha_decomposition: Dict[str, float] = {}
        
    def record_execution(
        self,
        signal_alpha: float,
        expected_price: float,
        actual_price: float,
        signal_return: float,
        execution_cost: float,
        timing_score: float,
        timestamp: Optional[datetime] = None
    ):
        """Record execution performance for alpha decomposition."""
        execution_return = signal_return - execution_cost
        
        self.execution_history.append({
            'signal_alpha': signal_alpha,
            'expected_price': expected_price,
            'actual_price': actual_price,
            'signal_return': signal_return,
            'execution_cost': execution_cost,
            'execution_return': execution_return,
            'timing_score': timing_score,
            'timestamp': timestamp or datetime.now()
        })
        
        # Keep last 200 executions
        if len(self.execution_history) > 200:
            self.execution_history = self.execution_history[-200:]
    
    def decompose_alpha(self) -> Dict[str, Any]:
        """
        Decompose total alpha into signal alpha and execution alpha.
        
        Returns:
            Alpha decomposition with execution contribution
        """
        if len(self.execution_history) < 20:
            return {'status': 'insufficient_data'}
        
        recent = self.execution_history[-50:]
        
        # Calculate components
        total_returns = [e['signal_return'] for e in recent]
        execution_costs = [e['execution_cost'] for e in recent]
        timing_scores = [e['timing_score'] for e in recent]
        
        avg_total_return = np.mean(total_returns)
        avg_execution_cost = np.mean(execution_costs)
        avg_timing_score = np.mean(timing_scores)
        
        # Estimate signal alpha (what you would get with perfect execution)
        # Total return = signal_return - execution_cost
        # So signal_alpha ≈ total_return + execution_cost
        signal_alpha_estimate = avg_total_return + avg_execution_cost
        
        # Execution alpha is negative of execution costs (saved money)
        execution_alpha = -avg_execution_cost
        
        # Timing contribution (correlation between timing score and return)
        timing_contribution = np.corrcoef(timing_scores, total_returns)[0, 1] if len(timing_scores) > 10 else 0
        
        # Calculate execution efficiency
        execution_efficiency = 1.0 - (avg_execution_cost / max(abs(signal_alpha_estimate), 0.001))
        
        return {
            'total_alpha': avg_total_return,
            'signal_alpha_estimate': signal_alpha_estimate,
            'execution_alpha': execution_alpha,
            'execution_cost_bps': avg_execution_cost * 10000,  # Convert to bps
            'timing_contribution': timing_contribution,
            'execution_efficiency': execution_efficiency,
            'signal_to_execution_ratio': abs(signal_alpha_estimate / execution_alpha) if execution_alpha != 0 else float('inf'),
            'execution_quality_grade': self._grade_execution(execution_efficiency),
            'recommendation': self._get_execution_recommendation(execution_efficiency, timing_contribution)
        }
    
    def _grade_execution(self, efficiency: float) -> str:
        """Grade execution quality."""
        if efficiency > 0.95:
            return 'A+'
        elif efficiency > 0.90:
            return 'A'
        elif efficiency > 0.80:
            return 'B'
        elif efficiency > 0.70:
            return 'C'
        else:
            return 'D'
    
    def _get_execution_recommendation(self, efficiency: float, timing: float) -> str:
        """Get recommendation based on execution quality."""
        if efficiency < 0.70:
            return 'URGENT: Execution costs destroying alpha. Review routing and timing.'
        elif efficiency < 0.85:
            return 'Execution improvement needed. Consider better liquidity access.'
        elif timing < 0.3:
            return 'Good cost control but timing could improve. Analyze entry windows.'
        else:
            return 'Excellent execution. Maintain current approach.'
    
    def get_execution_optimization_suggestions(self) -> List[str]:
        """Get specific suggestions for execution improvement."""
        if len(self.execution_history) < 30:
            return ['Collect more execution data for optimization suggestions']
        
        suggestions = []
        
        recent = self.execution_history[-30:]
        avg_cost = np.mean([e['execution_cost'] for e in recent])
        avg_timing = np.mean([e['timing_score'] for e in recent])
        
        if avg_cost > 0.001:  # > 10 bps
            suggestions.append("High execution costs detected. Review broker routing.")
            suggestions.append("Consider iceberg orders for larger positions.")
        
        if avg_timing < 0.6:
            suggestions.append("Timing score below optimal. Analyze microstructure patterns.")
            suggestions.append("Consider VWAP/TWAP for less time-sensitive entries.")
        
        # Analyze price drift
        price_drifts = [(e['actual_price'] - e['expected_price']) / e['expected_price'] 
                       for e in recent]
        avg_drift = np.mean(price_drifts)
        
        if avg_drift > 0.0002:  # > 2 bps adverse drift
            suggestions.append(f"Adverse selection detected ({avg_drift*10000:.1f} bps). Improve signal latency.")
        
        return suggestions if suggestions else ['Execution performing well. Monitor for changes.']


class ExecutionTimingOptimizer:
    """
    Execution Timing Optimizer
    
    Not just entry/exit price.
    
    Optimize:
    - when to enter relative to microstructure
    - delay vs urgency
    """
    
    def __init__(self):
        self.timing_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self.optimal_windows: Dict[str, Dict] = {}
        
    def record_timing(
        self,
        symbol: str,
        entry_time: datetime,
        microstructure_state: Dict[str, Any],
        execution_quality: float,
        slippage_bps: float
    ):
        """Record execution timing data."""
        hour = entry_time.hour
        minute = entry_time.minute
        
        self.timing_patterns[symbol].append({
            'hour': hour,
            'minute': minute,
            'time_bucket': f"{hour:02d}:{(minute // 15) * 15:02d}",
            'spread_bps': microstructure_state.get('spread_bps', 0),
            'volume_imbalance': microstructure_state.get('volume_imbalance', 0),
            'order_book_depth': microstructure_state.get('depth', 0),
            'execution_quality': execution_quality,
            'slippage_bps': slippage_bps
        })
        
        # Keep last 100 per symbol
        if len(self.timing_patterns[symbol]) > 100:
            self.timing_patterns[symbol] = self.timing_patterns[symbol][-100:]
    
    def analyze_optimal_timing(self, symbol: str) -> Dict[str, Any]:
        """Analyze optimal execution timing for symbol."""
        patterns = self.timing_patterns.get(symbol, [])
        
        if len(patterns) < 20:
            return {'status': 'insufficient_data', 'symbol': symbol}
        
        # Group by time bucket
        bucket_performance = defaultdict(lambda: {'count': 0, 'avg_slippage': 0, 'avg_quality': 0})
        
        for p in patterns:
            bucket = p['time_bucket']
            bucket_performance[bucket]['count'] += 1
            bucket_performance[bucket]['avg_slippage'] += p['slippage_bps']
            bucket_performance[bucket]['avg_quality'] += p['execution_quality']
        
        # Calculate averages
        for bucket in bucket_performance:
            count = bucket_performance[bucket]['count']
            bucket_performance[bucket]['avg_slippage'] /= count
            bucket_performance[bucket]['avg_quality'] /= count
        
        # Find best windows
        sorted_by_quality = sorted(
            bucket_performance.items(),
            key=lambda x: x[1]['avg_quality'],
            reverse=True
        )
        
        best_windows = [
            {'time': bucket, 'quality': stats['avg_quality'], 'slippage': stats['avg_slippage']}
            for bucket, stats in sorted_by_quality[:3]
        ]
        
        worst_windows = [
            {'time': bucket, 'quality': stats['avg_quality'], 'slippage': stats['avg_slippage']}
            for bucket, stats in sorted_by_quality[-3:]
        ]
        
        return {
            'symbol': symbol,
            'best_execution_windows': best_windows,
            'avoid_windows': worst_windows,
            'recommendation': f"Trade during {best_windows[0]['time']}" if best_windows else "No clear pattern",
            'sample_size': len(patterns)
        }
    
    def get_timing_recommendation(
        self,
        symbol: str,
        current_time: datetime,
        urgency: str = 'normal'
    ) -> Dict[str, Any]:
        """Get timing recommendation for current conditions."""
        optimal = self.analyze_optimal_timing(symbol)
        
        current_bucket = f"{current_time.hour:02d}:{(current_time.minute // 15) * 15:02d}"
        
        best_windows = optimal.get('best_execution_windows', [])
        is_optimal_time = any(w['time'] == current_bucket for w in best_windows)
        
        if is_optimal_time:
            return {
                'recommendation': 'EXECUTE_NOW',
                'reason': f'Current time {current_bucket} is in optimal window',
                'urgency': 'high' if urgency == 'high' else 'normal'
            }
        
        # Check if we should delay
        if urgency == 'low':
            if best_windows:
                next_window = best_windows[0]['time']
                return {
                    'recommendation': 'DELAY',
                    'reason': f'Current time suboptimal. Wait for {next_window}',
                    'target_time': next_window,
                    'urgency': 'low'
                }
        
        return {
            'recommendation': 'EXECUTE_WITH_CAUTION',
            'reason': f'Timing not optimal but urgency {urgency} requires execution',
            'urgency': urgency
        }


class DecisionLatencyOptimizer:
    """
    Decision Latency Optimizer
    
    Speed matters.
    
    Measure:
    - time from signal -> execution
    - performance degradation due to delay
    
    Optimize:
    - faster pipelines
    - prioritization of high-impact decisions
    """
    
    def __init__(self):
        self.latency_measurements: List[Dict] = []
        self.impact_analysis: Dict[str, List[float]] = defaultdict(list)
        
    def record_latency(
        self,
        signal_timestamp: datetime,
        decision_timestamp: datetime,
        execution_timestamp: datetime,
        signal_strength: float,
        symbol: str,
        price_at_signal: float,
        price_at_execution: float,
        expected_return: float,
        actual_return: float
    ):
        """Record latency and its impact."""
        decision_latency = (decision_timestamp - signal_timestamp).total_seconds()
        execution_latency = (execution_timestamp - decision_timestamp).total_seconds()
        total_latency = (execution_timestamp - signal_timestamp).total_seconds()
        
        # Calculate slippage due to latency
        latency_slippage = (price_at_execution - price_at_signal) / price_at_signal
        
        # Calculate return degradation
        return_degradation = expected_return - actual_return
        
        measurement = {
            'decision_latency_ms': decision_latency * 1000,
            'execution_latency_ms': execution_latency * 1000,
            'total_latency_ms': total_latency * 1000,
            'signal_strength': signal_strength,
            'symbol': symbol,
            'latency_slippage_bps': latency_slippage * 10000,
            'return_degradation': return_degradation,
            'timestamp': execution_timestamp
        }
        
        self.latency_measurements.append(measurement)
        
        # Keep last 100 measurements
        if len(self.latency_measurements) > 100:
            self.latency_measurements = self.latency_measurements[-100:]
    
    def analyze_latency_impact(self) -> Dict[str, Any]:
        """Analyze the impact of latency on performance."""
        if len(self.latency_measurements) < 20:
            return {'status': 'insufficient_data'}
        
        recent = self.latency_measurements[-50:]
        
        # Calculate statistics
        latencies = [m['total_latency_ms'] for m in recent]
        slippages = [m['latency_slippage_bps'] for m in recent]
        degradations = [m['return_degradation'] for m in recent]
        
        # Correlation between latency and degradation
        correlation = np.corrcoef(latencies, degradations)[0, 1] if len(latencies) > 10 else 0
        
        # Cost of latency
        avg_latency_ms = np.mean(latencies)
        avg_slippage_bps = np.mean(slippages)
        avg_degradation = np.mean(degradations)
        
        # Calculate cost per millisecond
        cost_per_ms = avg_degradation / avg_latency_ms if avg_latency_ms > 0 else 0
        
        return {
            'avg_latency_ms': avg_latency_ms,
            'avg_slippage_bps': avg_slippage_bps,
            'avg_return_degradation': avg_degradation,
            'latency_correlation': correlation,
            'cost_per_ms': cost_per_ms,
            'annual_cost_estimate': self._estimate_annual_latency_cost(cost_per_ms),
            'urgency': 'HIGH' if correlation > 0.5 and cost_per_ms > 0.0001 else 'MEDIUM' if correlation > 0.3 else 'LOW'
        }
    
    def _estimate_annual_latency_cost(self, cost_per_ms: float) -> float:
        """Estimate annual cost of latency."""
        # Assume 100 trades/day, 250 trading days
        trades_per_year = 100 * 250
        avg_latency_ms = 100  # Assume 100ms average
        
        return cost_per_ms * avg_latency_ms * trades_per_year
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get recommendations for latency optimization."""
        analysis = self.analyze_latency_impact()
        
        if analysis.get('status') == 'insufficient_data':
            return ['Collect more latency data for optimization recommendations']
        
        recommendations = []
        
        avg_latency = analysis.get('avg_latency_ms', 0)
        correlation = analysis.get('latency_correlation', 0)
        cost_per_ms = analysis.get('cost_per_ms', 0)
        
        if avg_latency > 500:
            recommendations.append(f"High latency detected ({avg_latency:.0f}ms). Review pipeline bottlenecks.")
        
        if correlation > 0.5:
            recommendations.append(f"Strong latency-performance correlation ({correlation:.2f}). Prioritize speed optimization.")
            recommendations.append(f"Each ms costs {cost_per_ms*10000:.2f} bps. ROI on latency reduction is clear.")
        
        if analysis.get('annual_cost_estimate', 0) > 0.05:  # > 5% annual
            recommendations.append("Latency costs exceed 5% annually. Consider infrastructure upgrades.")
        
        return recommendations if recommendations else ['Latency impact minimal. Current performance acceptable.']


class MarketImpactEstimator:
    """
    Market Impact Estimator
    
    Estimates price impact of trades before execution.
    
    Uses:
    - Square-root law for impact estimation
    - Order book depth analysis
    - Historical impact regression
    
    Formula: Impact = k * sigma * sqrt(order_size / avg_daily_volume)
    """
    
    def __init__(self, impact_coefficient: float = 1.0):
        self.impact_coefficient = impact_coefficient
        self.impact_history: List[Dict] = []
        
    def estimate_impact(
        self,
        order_size: float,
        avg_daily_volume: float,
        volatility: float,
        order_book_depth: Optional[float] = None,
        spread_bps: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Estimate market impact for a proposed trade.
        
        Args:
            order_size: Size of the order
            avg_daily_volume: Average daily trading volume
            volatility: Daily volatility (standard deviation)
            order_book_depth: Depth at best bid/ask
            spread_bps: Current spread in basis points
            
        Returns:
            Impact estimate in various units
        """
        if avg_daily_volume <= 0:
            return {'temporary_impact': 0, 'permanent_impact': 0, 'total_impact': 0}
        
        # Participation rate
        participation = order_size / avg_daily_volume
        
        # Square-root impact model
        temp_impact = self.impact_coefficient * volatility * np.sqrt(participation)
        
        # Permanent impact (typically 10-20% of temporary)
        perm_impact = temp_impact * 0.15
        
        # Total impact
        total_impact = temp_impact + perm_impact
        
        # Adjust for order book depth if available
        if order_book_depth and order_book_depth > 0:
            depth_ratio = order_size / order_book_depth
            if depth_ratio > 0.5:
                # Deep in the book - higher impact
                total_impact *= (1 + depth_ratio * 0.5)
        
        # Adjust for spread if available
        if spread_bps:
            spread_factor = spread_bps / 10  # Normalize to 10 bps
            total_impact *= (1 + spread_factor * 0.1)
        
        return {
            'temporary_impact_bps': temp_impact * 10000,
            'permanent_impact_bps': perm_impact * 10000,
            'total_impact_bps': total_impact * 10000,
            'temporary_impact_pct': temp_impact,
            'permanent_impact_pct': perm_impact,
            'total_impact_pct': total_impact,
            'participation_rate': participation,
            'order_size': order_size,
            'recommendation': self._get_impact_recommendation(total_impact, participation)
        }
    
    def _get_impact_recommendation(self, total_impact: float, participation: float) -> str:
        """Get recommendation based on impact estimate."""
        if total_impact > 0.01 or participation > 0.3:  # > 1% impact or > 30% ADV
            return 'HIGH_IMPACT: Split order or reduce size significantly'
        elif total_impact > 0.005 or participation > 0.15:  # > 50 bps or > 15% ADV
            return 'MODERATE_IMPACT: Consider order splitting'
        else:
            return 'LOW_IMPACT: Safe to execute'
    
    def record_actual_impact(
        self,
        pre_trade_price: float,
        execution_price: float,
        post_trade_price: float,
        order_size: float,
        predicted_impact: float
    ):
        """Record actual impact for model calibration."""
        # Calculate realized impact
        temp_impact = abs(execution_price - pre_trade_price) / pre_trade_price
        perm_impact = abs(post_trade_price - pre_trade_price) / pre_trade_price
        
        self.impact_history.append({
            'timestamp': datetime.now(),
            'predicted': predicted_impact,
            'actual_temp': temp_impact,
            'actual_perm': perm_impact,
            'order_size': order_size,
            'prediction_error': temp_impact - predicted_impact
        })
        
        # Keep last 50
        if len(self.impact_history) > 50:
            self.impact_history = self.impact_history[-50:]
    
    def calibrate_model(self) -> Dict[str, Any]:
        """Calibrate impact model based on historical predictions."""
        if len(self.impact_history) < 10:
            return {'status': 'insufficient_data'}
        
        recent = self.impact_history[-20:]
        
        errors = [h['prediction_error'] for h in recent]
        predictions = [h['predicted'] for h in recent]
        actuals = [h['actual_temp'] for h in recent]
        
        mae = np.mean(np.abs(errors))
        bias = np.mean(errors)  # Positive = under-predicting
        
        # Correlation between predicted and actual
        correlation = np.corrcoef(predictions, actuals)[0, 1] if len(predictions) > 1 else 0
        
        # Adjust coefficient if systematic bias
        if abs(bias) > mae * 0.5:
            adjustment = 1 + (bias / np.mean(predictions)) if np.mean(predictions) > 0 else 1
            self.impact_coefficient *= adjustment
        
        return {
            'prediction_mae': mae,
            'prediction_bias': bias,
            'prediction_correlation': correlation,
            'model_quality': 'GOOD' if correlation > 0.7 else 'FAIR' if correlation > 0.4 else 'POOR',
            'coefficient_adjusted': abs(bias) > mae * 0.5,
            'current_coefficient': self.impact_coefficient
        }


class OrderFlowToxicityDetector:
    """
    Order Flow Toxicity Detector (VPIN - Volume Synchronized Probability of Informed Trading)
    
    Detects when order flow becomes "toxic" - i.e., when informed traders are active.
    
    High toxicity means:
    - Adverse selection risk is elevated
    - You are more likely to trade against informed flow
    - Consider widening spreads or reducing participation
    """
    
    def __init__(self, window_size: int = 50, buckets: int = 50):
        self.window_size = window_size  # Number of volume buckets
        self.buckets = buckets
        self.volume_buckets: Deque[Dict] = deque(maxlen=buckets)
        self.bulk_volume_delta: float = 0.0
        
    def process_trade(
        self,
        price: float,
        volume: float,
        bid: float,
        ask: float,
        timestamp: Optional[datetime] = None
    ):
        """Process a trade to update toxicity metrics."""
        # Calculate buy/sell classification
        if ask - bid > 0:
            buy_prob = (price - bid) / (ask - bid)
        else:
            buy_prob = 0.5
        
        # Volume classification (buy volume - sell volume)
        buy_volume = volume * buy_prob
        sell_volume = volume * (1 - buy_prob)
        volume_delta = buy_volume - sell_volume
        
        # Add to current bucket
        current_bucket_volume = sum(b['volume'] for b in self.volume_buckets) if self.volume_buckets else 0
        
        if current_bucket_volume < self.window_size or not self.volume_buckets:
            # Add to current or new bucket
            self.volume_buckets.append({
                'volume': volume,
                'volume_delta': volume_delta,
                'price': price,
                'timestamp': timestamp or datetime.now()
            })
        
        # Calculate BVC (Bulk Volume Classification)
        if len(self.volume_buckets) > 0:
            total_volume = sum(b['volume'] for b in self.volume_buckets)
            total_delta = sum(b['volume_delta'] for b in self.volume_buckets)
            
            if total_volume > 0:
                self.bulk_volume_delta = total_delta / total_volume
    
    def calculate_vpin(self) -> Dict[str, Any]:
        """Calculate Volume-Synchronized Probability of Informed Trading."""
        if len(self.volume_buckets) < self.buckets * 0.5:
            return {'status': 'insufficient_data', 'vpin': 0.5}
        
        # VPIN = average absolute BVC over buckets
        abs_deltas = [abs(b['volume_delta']) / b['volume'] if b['volume'] > 0 else 0 
                     for b in self.volume_buckets]
        
        vpin = np.mean(abs_deltas) if abs_deltas else 0.5
        
        # Calculate rolling statistics
        recent_deltas = abs_deltas[-10:] if len(abs_deltas) >= 10 else abs_deltas
        vpin_volatility = np.std(recent_deltas) if len(recent_deltas) > 1 else 0
        
        return {
            'vpin': vpin,
            'vpin_volatility': vpin_volatility,
            'toxicity_level': self._classify_toxicity(vpin),
            'confidence': min(1.0, len(self.volume_buckets) / self.buckets),
            'recommendation': self._get_toxicity_recommendation(vpin, vpin_volatility)
        }
    
    def _classify_toxicity(self, vpin: float) -> str:
        """Classify toxicity level."""
        if vpin > 0.7:
            return 'EXTREME'
        elif vpin > 0.6:
            return 'HIGH'
        elif vpin > 0.5:
            return 'ELEVATED'
        elif vpin > 0.4:
            return 'MODERATE'
        else:
            return 'LOW'
    
    def _get_toxicity_recommendation(self, vpin: float, volatility: float) -> str:
        """Get trading recommendation based on toxicity."""
        if vpin > 0.7:
            return 'AVOID: Extreme informed trading detected. Stay out.'
        elif vpin > 0.6:
            return 'CAUTION: High toxicity. Reduce size by 50% and widen stops.'
        elif vpin > 0.5 and volatility > 0.1:
            return 'MODERATE: Elevated toxicity with volatility. Tighten risk.'
        elif vpin < 0.3:
            return 'FAVORABLE: Low toxicity environment. Normal trading.'
        else:
            return 'NEUTRAL: Monitor for changes.'
    
    def get_flow_toxicity_score(self) -> float:
        """Get current toxicity score (0-1)."""
        vpin_data = self.calculate_vpin()
        return vpin_data.get('vpin', 0.5)


class CrossExchangeLiquidityRouter:
    """
    Cross-Exchange Liquidity Router
    
    Routes orders across multiple exchanges to:
    - Minimize market impact
    - Optimize fill rates
    - Reduce slippage
    - Access best liquidity
    """
    
    def __init__(self):
        self.exchange_liquidity: Dict[str, Dict[str, Any]] = {}
        self.routing_history: List[Dict] = []
        
    def update_exchange_liquidity(
        self,
        exchange: str,
        symbol: str,
        bid_depth: float,
        ask_depth: float,
        spread_bps: float,
        fees_bps: float,
        latency_ms: float
    ):
        """Update liquidity info for an exchange."""
        key = f"{exchange}_{symbol}"
        
        # Calculate liquidity score
        total_depth = bid_depth + ask_depth
        spread_penalty = spread_bps / 10  # Normalize
        fee_penalty = fees_bps / 10
        latency_penalty = latency_ms / 100
        
        # Higher score = better
        liquidity_score = (
            total_depth / 1000000 * 0.4 -  # Depth contribution
            spread_penalty * 0.2 -
            fee_penalty * 0.2 -
            latency_penalty * 0.2
        )
        
        self.exchange_liquidity[key] = {
            'exchange': exchange,
            'symbol': symbol,
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'total_depth': total_depth,
            'spread_bps': spread_bps,
            'fees_bps': fees_bps,
            'latency_ms': latency_ms,
            'liquidity_score': liquidity_score,
            'updated_at': datetime.now()
        }
    
    def route_order(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        total_size: float,
        urgency: str = 'normal'  # 'low', 'normal', 'high'
    ) -> Dict[str, Any]:
        """
        Determine optimal routing across exchanges.
        
        Returns:
            Routing plan with exchange allocations
        """
        # Get all exchanges for this symbol
        exchanges = [
            data for key, data in self.exchange_liquidity.items()
            if data['symbol'] == symbol and (datetime.now() - data['updated_at']).seconds < 60
        ]
        
        if not exchanges:
            return {'status': 'no_liquidity_data', 'routing': []}
        
        # Sort by liquidity score
        exchanges.sort(key=lambda x: x['liquidity_score'], reverse=True)
        
        routing_plan = []
        remaining_size = total_size
        
        for ex in exchanges:
            if remaining_size <= 0:
                break
            
            # Determine how much to send to this exchange
            if urgency == 'high':
                # Split aggressively across top exchanges
                allocation_pct = 0.5 if ex == exchanges[0] else 0.25
            elif urgency == 'low':
                # Send to best exchange only
                allocation_pct = 1.0 if ex == exchanges[0] else 0
            else:
                # Normal: proportional to liquidity
                total_top_depth = sum(e['total_depth'] for e in exchanges[:3])
                if total_top_depth > 0:
                    allocation_pct = ex['total_depth'] / total_top_depth
                else:
                    allocation_pct = 1.0 / len(exchanges)
            
            allocation_size = min(remaining_size, total_size * allocation_pct)
            
            if allocation_size > 0:
                routing_plan.append({
                    'exchange': ex['exchange'],
                    'size': allocation_size,
                    'expected_slippage_bps': ex['spread_bps'] + ex['fees_bps'],
                    'expected_latency_ms': ex['latency_ms']
                })
                remaining_size -= allocation_size
        
        # Record routing decision
        self.routing_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': side,
            'total_size': total_size,
            'urgency': urgency,
            'routing_plan': routing_plan,
            'exchanges_used': len(routing_plan)
        })
        
        # Keep last 50
        if len(self.routing_history) > 50:
            self.routing_history = self.routing_history[-50:]
        
        return {
            'symbol': symbol,
            'side': side,
            'total_size': total_size,
            'routing_plan': routing_plan,
            'expected_total_slippage': sum(r['size'] * r['expected_slippage_bps'] for r in routing_plan) / total_size if total_size > 0 else 0,
            'exchanges_used': len(routing_plan),
            'fill_confidence': 'HIGH' if len(routing_plan) >= 2 else 'MEDIUM'
        }
    
    def get_routing_performance(self) -> Dict[str, Any]:
        """Analyze historical routing performance."""
        if len(self.routing_history) < 10:
            return {'status': 'insufficient_data'}
        
        recent = self.routing_history[-20:]
        
        avg_exchanges = np.mean([r['exchanges_used'] for r in recent])
        
        return {
            'avg_exchanges_per_order': avg_exchanges,
            'routing_diversity': len(set(
                ex['exchange'] 
                for r in recent 
                for ex in r['routing_plan']
            )),
            'recommendation': 'Good routing diversity' if avg_exchanges > 1.5 else 'Consider using more exchanges'
        }
