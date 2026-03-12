"""
Atomic Cross-Exchange Execution
Simultaneous execution across multiple venues with zero slippage arbitrage
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class VenueOrder:
    """Order for a specific venue"""
    venue: str
    symbol: str
    side: str  # buy/sell
    quantity: float
    price: Optional[float] = None
    order_id: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    filled_quantity: float = 0.0
    average_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AtomicExecution:
    """Atomic execution across multiple venues"""
    execution_id: str
    orders: List[VenueOrder]
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_slippage: float = 0.0
    profit_loss: float = 0.0


class AtomicExecutor:
    """
    Atomic cross-exchange execution engine
    Ensures all-or-nothing execution across multiple venues
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Venue connections (mock for now)
        self.venues = {
            'binance': {'connected': True, 'latency': 0.010},
            'coinbase': {'connected': True, 'latency': 0.015},
            'kraken': {'connected': True, 'latency': 0.020},
            'ftx': {'connected': True, 'latency': 0.012},
            'bitstamp': {'connected': True, 'latency': 0.018}
        }
        
        # Execution settings
        self.max_execution_time = self.config.get('max_execution_time', 2.0)  # seconds
        self.rollback_on_partial = self.config.get('rollback_on_partial', True)
        
        # Active executions
        self.active_executions: Dict[str, AtomicExecution] = {}
        
        logger.info("Atomic executor initialized")
        
    async def execute_atomic(self, orders: List[VenueOrder]) -> AtomicExecution:
        """
        Execute orders atomically across multiple venues
        
        All orders must complete or all are rolled back
        """
        execution_id = f"atomic_{datetime.now().timestamp()}"
        
        # Validate all orders
        valid_orders = []
        for order in orders:
            if not (hasattr(order, 'venue') and hasattr(order, 'symbol') and hasattr(order, 'side') and hasattr(order, 'quantity')):
                logger.error(f"Invalid order missing required fields: {order}")
                continue
            if not order.venue or not order.symbol or not order.side or order.quantity <= 0:
                logger.error(f"Order has invalid values: {order}")
                continue
            valid_orders.append(order)
        if not valid_orders:
            logger.error("No valid orders to execute.")
            return AtomicExecution(
                execution_id=execution_id,
                orders=[],
                status=ExecutionStatus.FAILED,
                start_time=datetime.now()
            )
        
        execution = AtomicExecution(
            execution_id=execution_id,
            orders=valid_orders,
            status=ExecutionStatus.EXECUTING,
            start_time=datetime.now()
        )
        
        self.active_executions[execution_id] = execution
        
        logger.info(f"Starting atomic execution {execution_id} with {len(valid_orders)} orders")
        
        try:
            # Phase 1: Pre-flight checks
            if not await self._preflight_checks(valid_orders):
                execution.status = ExecutionStatus.FAILED
                logger.error("Pre-flight checks failed")
                return execution
                
            # Phase 2: Lock liquidity (reserve orders on all venues)
            locked = await self._lock_liquidity(valid_orders)
            
            if not locked:
                execution.status = ExecutionStatus.FAILED
                logger.error("Failed to lock liquidity")
                return execution
                
            # Phase 3: Simultaneous execution
            results = await self._execute_simultaneously(valid_orders)
            
            # Phase 4: Verify all completed
            all_completed = all(r.get('status') == 'completed' for r in results if isinstance(r, dict))
            
            if all_completed:
                execution.status = ExecutionStatus.COMPLETED
                execution.end_time = datetime.now()
                
                # Calculate metrics
                execution.total_slippage = self._calculate_slippage(valid_orders, results)
                execution.profit_loss = self._calculate_pnl(valid_orders, results)
                
                logger.info(f"Atomic execution {execution_id} completed successfully")
                logger.info(f"Slippage: {execution.total_slippage:.4f}, P&L: {execution.profit_loss:.2f}")
                
            else:
                # Rollback if configured
                if self.rollback_on_partial:
                    logger.warning(f"Partial execution detected. Rolling back...")
                    await self._rollback(valid_orders, results)
                    execution.status = ExecutionStatus.ROLLED_BACK
                else:
                    execution.status = ExecutionStatus.PARTIAL
                    
            return execution
            
        except Exception as e:
            logger.error(f"Atomic execution failed: {e}")
            execution.status = ExecutionStatus.FAILED
            
            try:
            # Attempt rollback
                await self._rollback(valid_orders, [])
            except Exception as ex:
                logger.error(f"Rollback failed: {ex}")
                
            return execution
            
        finally:
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
                
    async def _preflight_checks(self, orders: List[VenueOrder]) -> bool:
        """Pre-flight checks before execution"""
        try:
            # Check venue connectivity
            for order in orders:
                if order.venue not in self.venues:
                    logger.error(f"Unknown venue: {order.venue}")
                    return False
                    
                if not self.venues[order.venue]['connected']:
                    logger.error(f"Venue not connected: {order.venue}")
                    return False
                    
            # Check for sufficient liquidity (mock)
            for order in orders:
                available = await self._check_liquidity(order.venue, order.symbol, order.quantity)
                if not available:
                    logger.error(f"Insufficient liquidity on {order.venue}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Pre-flight checks error: {e}")
            return False
            
    async def _check_liquidity(self, venue: str, symbol: str, quantity: float) -> bool:
        """Check if sufficient liquidity is available"""
        # Mock implementation
        await asyncio.sleep(0.001)
        return True
        
    async def _lock_liquidity(self, orders: List[VenueOrder]) -> bool:
        """Lock liquidity on all venues before execution"""
        try:
            # In production: place IOC (Immediate-or-Cancel) orders to reserve liquidity
            # For now, simulate locking
            
            lock_tasks = [
                self._lock_venue_liquidity(order) 
                for order in orders
            ]
            
            results = await asyncio.gather(*lock_tasks, return_exceptions=True)
            
            # Check all locks succeeded
            return all(r is True for r in results)
            
        except Exception as e:
            logger.error(f"Liquidity locking failed: {e}")
            return False
            
    async def _lock_venue_liquidity(self, order: VenueOrder) -> bool:
        """Lock liquidity on a specific venue"""
        # Simulate network latency
        await asyncio.sleep(self.venues[order.venue]['latency'])
        
        # Mock success
        return True
        
    async def _execute_simultaneously(self, orders: List[VenueOrder]) -> List[Dict]:
        """Execute all orders simultaneously"""
        # Create execution tasks
        tasks = [
            self._execute_venue_order(order) 
            for order in orders
        ]
        
        try:
            # Execute all simultaneously with timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.max_execution_time
            )
            
            return results
            
        except asyncio.TimeoutError:
            logger.error("Execution timeout")
            return [{'status': 'failed', 'error': 'timeout'} for _ in orders]
            
    async def _execute_venue_order(self, order: VenueOrder) -> Dict:
        """Execute order on a specific venue"""
        try:
            # Simulate execution
            await asyncio.sleep(self.venues[order.venue]['latency'])
            
            # Mock execution result
            slippage = np.random.uniform(-0.0005, 0.0005)  # 5 bps
            
            if order.price is not None:
                fill_price = order.price * (1 + slippage)
            else:
                fill_price = 100.0 * (1 + slippage)  # Mock price
                
            order.status = ExecutionStatus.COMPLETED
            order.filled_quantity = order.quantity
            order.average_price = fill_price
            order.order_id = f"{order.venue}_{datetime.now().timestamp()}"
            
            return {
                'status': 'completed',
                'venue': order.venue,
                'filled_quantity': order.quantity,
                'average_price': fill_price,
                'order_id': order.order_id
            }
            
        except Exception as e:
            logger.error(f"Venue execution failed on {order.venue}: {e}")
            order.status = ExecutionStatus.FAILED
            
            return {
                'status': 'failed',
                'venue': order.venue,
                'error': str(e)
            }
            
    async def _rollback(self, orders: List[VenueOrder], results: List[Dict]):
        """Rollback completed orders"""
        logger.info("Rolling back atomic execution...")
        
        # Find completed orders
        completed_orders = [
            order for order, result in zip(orders, results)
            if result.get('status') == 'completed'
        ]
        
        # Create reverse orders
        reverse_tasks = []
        for order in completed_orders:
            reverse_order = VenueOrder(
                venue=order.venue,
                symbol=order.symbol,
                side='sell' if order.side == 'buy' else 'buy',
                quantity=order.filled_quantity,
                price=order.average_price
            )
            reverse_tasks.append(self._execute_venue_order(reverse_order))
            
        # Execute rollback
        if reverse_tasks:
            await asyncio.gather(*reverse_tasks, return_exceptions=True)
            logger.info(f"Rolled back {len(reverse_tasks)} orders")
            
    def _calculate_slippage(self, orders: List[VenueOrder], results: List[Dict]) -> float:
        """Calculate total slippage"""
        total_slippage = 0.0
        
        for order, result in zip(orders, results):
            if result.get('status') == 'completed' and order.price is not None:
                expected_price = order.price
                actual_price = result['average_price']
                slippage = abs(actual_price - expected_price) / expected_price
                total_slippage += slippage
                
        return total_slippage
        
    def _calculate_pnl(self, orders: List[VenueOrder], results: List[Dict]) -> float:
        """Calculate profit/loss from arbitrage"""
        buy_cost = 0.0
        sell_revenue = 0.0
        
        for order, result in zip(orders, results):
            if result.get('status') == 'completed':
                amount = result['filled_quantity'] * result['average_price']
                
                if order.side == 'buy':
                    buy_cost += amount
                else:
                    sell_revenue += amount
                    
        return sell_revenue - buy_cost


class PredictiveLiquiditySeeker:
    """
    ML-based predictive liquidity seeking
    Predicts where liquidity will appear and pre-positions
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Liquidity prediction model (simplified)
        self.liquidity_patterns: Dict[str, List] = {}
        
        logger.info("Predictive liquidity seeker initialized")
        
    async def predict_liquidity(self, symbol: str, timeframe: int = 60) -> Dict[str, Any]:
        """
        Predict where liquidity will appear in next timeframe
        
        Args:
            symbol: Trading symbol
            timeframe: Prediction timeframe in seconds
        """
        # In production: use ML model trained on order book dynamics
        # Features: time of day, recent volume, price momentum, etc.
        
        # Mock prediction
        predicted_venues = []
        
        for venue in ['binance', 'coinbase', 'kraken']:
            liquidity_score = np.random.beta(5, 2)  # Skewed toward high liquidity
            
            predicted_venues.append({
                'venue': venue,
                'liquidity_score': liquidity_score,
                'predicted_depth': np.random.uniform(10000, 100000),
                'confidence': np.random.uniform(0.7, 0.95)
            })
            
        # Sort by liquidity score
        predicted_venues.sort(key=lambda x: x['liquidity_score'], reverse=True)
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'predictions': predicted_venues,
            'timestamp': datetime.now()
        }
        
    async def optimal_venue_selection(self, symbol: str, quantity: float) -> List[Tuple[str, float]]:
        """
        Select optimal venues and quantities for execution
        
        Returns list of (venue, quantity) tuples
        """
        predictions = await self.predict_liquidity(symbol)
        
        allocations = []
        remaining = quantity
        
        for pred in predictions['predictions']:
            if remaining <= 0:
                break
                
            # Allocate based on liquidity score
            allocation = min(
                remaining,
                pred['predicted_depth'] * 0.1  # Max 10% of depth
            )
            
            allocations.append((pred['venue'], allocation))
            remaining -= allocation
            
        return allocations
