"""
Execution Service - Order Execution System
===========================================

Wraps Execution capabilities as an event-driven service.
Handles order routing, execution, and fill tracking.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority
from trading_bot.core.signal_counterintelligence import (
    CounterintelligenceMode,
    validate_intelligence_metadata,
)

logger = logging.getLogger(__name__)


class ExecutionService(BaseService):
    """
    Execution Service - Order Execution Management
    
    Provides:
    - Smart order routing (SOR)
    - VWAP/TWAP execution
    - Iceberg orders
    - Dark pool access
    - Fill tracking and confirmation
    - Slippage monitoring
    - Market impact models
    """
    
    SERVICE_NAME = "execution"
    SERVICE_TYPE = "execution"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["broker", "risk", "msos"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._task: Optional[asyncio.Task] = None
        self._counterintelligence_mode = self._coerce_counterintelligence_mode(
            self.config.get("counterintelligence_mode", CounterintelligenceMode.HARD_GATE)
        )
        
        # Execution components
        self._smart_router = None
        self._fill_tracker = None
        self._market_impact = None
        self._execution_engine = None
        
        # State
        self._pending_orders: Dict[str, Dict] = {}
        self._executed_orders: List[Dict] = []
        self._execution_stats: Dict[str, Any] = {
            'total_orders': 0,
            'filled_orders': 0,
            'rejected_orders': 0,
            'avg_slippage_bps': 0.0,
        }
        
    async def start(self) -> None:
        """Start Execution service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._execution_loop())
        
        # Subscribe to events
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [
                    EventTypes.TRADE_SIZED,
                    EventTypes.ORDER_CANCEL_REQUEST,
                    EventTypes.BROKER_CONNECTED,
                ],
                self._on_event
            )
        
        logger.info("ExecutionService started")
    
    async def stop(self) -> None:
        """Stop Execution service"""
        self._running = False
        
        # Cancel pending orders
        for order_id in list(self._pending_orders.keys()):
            await self._cancel_order(order_id, "Service shutdown")
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("ExecutionService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components_loaded = sum([
            self._smart_router is not None,
            self._fill_tracker is not None,
            self._market_impact is not None,
            self._execution_engine is not None,
        ])
        return ServiceHealth(
            healthy=self._running and components_loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{components_loaded}/4 Execution components loaded",
            metrics={
                'components_loaded': components_loaded,
                'pending_orders': len(self._pending_orders),
                'execution_stats': self._execution_stats,
            }
        )
    
    async def _load_components(self) -> None:
        """Load Execution components"""
        try:
            from trading_bot.execution import SmartOrderRouter
            self._smart_router = SmartOrderRouter(self.config)
            logger.info("SmartOrderRouter loaded")
        except ImportError as e:
            logger.warning(f"SmartOrderRouter not available: {e}")
        
        try:
            from trading_bot.execution import FillTracker
            self._fill_tracker = FillTracker()
            logger.info("FillTracker loaded")
        except ImportError as e:
            logger.warning(f"FillTracker not available: {e}")
        
        try:
            from trading_bot.execution import MarketImpactModel
            self._market_impact = MarketImpactModel()
            logger.info("MarketImpactModel loaded")
        except ImportError as e:
            logger.warning(f"MarketImpactModel not available: {e}")
        
        try:
            from trading_bot.execution import ExecutionEngine
            self._execution_engine = ExecutionEngine(self.config)
            logger.info("ExecutionEngine loaded")
        except ImportError as e:
            logger.warning(f"ExecutionEngine not available: {e}")
    
    async def _on_event(self, event: Event) -> None:
        """Handle incoming events"""
        if event.event_type == EventTypes.TRADE_SIZED:
            await self._on_trade_sized(event)
        elif event.event_type == EventTypes.ORDER_CANCEL_REQUEST:
            await self._on_cancel_request(event)
        elif event.event_type == EventTypes.BROKER_CONNECTED:
            await self._on_broker_connected(event)
    
    async def _on_trade_sized(self, event: Event) -> None:
        """Execute a sized trade"""
        trade_data = event.payload.get('original_request', {})
        position_size = event.payload.get('position_size', {})
        
        # Create order
        order = await self.create_order(trade_data, position_size)
        
        if order:
            # Submit order
            result = await self.submit_order(order)
            
            if result.get('success'):
                self._execution_stats['total_orders'] += 1
            else:
                self._execution_stats['rejected_orders'] += 1
    
    async def _on_cancel_request(self, event: Event) -> None:
        """Handle order cancellation request"""
        order_id = event.payload.get('order_id')
        reason = event.payload.get('reason', 'User requested')
        
        if order_id:
            await self._cancel_order(order_id, reason)
    
    async def _on_broker_connected(self, event: Event) -> None:
        """Handle broker connection event"""
        logger.info("Broker connected - execution ready")
    
    async def create_order(
        self,
        trade_data: Dict[str, Any],
        position_size: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create an order from trade data and position size"""
        order = {
            'order_id': f"ORD_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            'symbol': trade_data.get('symbol'),
            'side': trade_data.get('side', 'buy'),
            'size': position_size.get('size', 0),
            'order_type': trade_data.get('order_type', 'market'),
            'price': trade_data.get('entry_price'),
            'stop_loss': trade_data.get('stop_loss'),
            'take_profit': trade_data.get('take_profit'),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending',
            'metadata': trade_data.get('metadata', {}),
            'intelligence': trade_data.get('intelligence')
            or trade_data.get('metadata', {}).get('intelligence')
            or position_size.get('intelligence'),
        }
        
        # Validate order
        if not order['symbol'] or order['size'] <= 0:
            logger.warning(f"Invalid order: {order}")
            return None
        
        return order
    
    async def submit_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an order for execution"""
        order_id = order['order_id']
        intelligence_metadata = order.get("intelligence") or order.get("metadata", {}).get("intelligence")
        gate_passed, gate_reasons = validate_intelligence_metadata(
            intelligence_metadata,
            self._counterintelligence_mode,
        )
        if not gate_passed:
            order["status"] = "rejected"
            order["reject_reason"] = "; ".join(gate_reasons)
            self._execution_stats["rejected_orders"] += 1
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type=EventTypes.ORDER_REJECTED,
                    payload=order,
                    source=self.SERVICE_NAME,
                ))
            return {"success": False, "reason": order["reject_reason"], "order": order}
        
        # Add to pending
        self._pending_orders[order_id] = order
        
        # Publish order placed event
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventTypes.ORDER_PLACED,
                payload=order,
                source=self.SERVICE_NAME,
            ))
        
        # Execute via broker (simulated if no broker)
        try:
            if self._execution_engine:
                result = await self._execute_via_engine(order)
            else:
                result = await self._simulate_execution(order)
            
            if result.get('filled'):
                order['status'] = 'filled'
                order['fill_price'] = result.get('fill_price')
                order['fill_time'] = datetime.utcnow().isoformat()
                order['slippage_bps'] = result.get('slippage_bps', 0)
                
                self._executed_orders.append(order)
                del self._pending_orders[order_id]
                
                self._execution_stats['filled_orders'] += 1
                
                # Update average slippage
                total_slippage = sum(o.get('slippage_bps', 0) for o in self._executed_orders)
                self._execution_stats['avg_slippage_bps'] = total_slippage / len(self._executed_orders)
                
                # Publish fill event
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.ORDER_FILLED,
                        payload=order,
                        source=self.SERVICE_NAME,
                    ))
                
                return {'success': True, 'order': order}
            else:
                order['status'] = 'rejected'
                order['reject_reason'] = result.get('reason', 'Unknown')
                
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.ORDER_REJECTED,
                        payload=order,
                        source=self.SERVICE_NAME,
                    ))
                
                return {'success': False, 'reason': result.get('reason')}
                
        except Exception as e:
            logger.error(f"Order execution error: {e}")
            order['status'] = 'error'
            order['error'] = str(e)
            return {'success': False, 'reason': str(e)}
    
    async def _execute_via_engine(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute order via execution engine"""
        try:
            result = await self._execution_engine.execute(order)
            return result
        except Exception as e:
            return {'filled': False, 'reason': str(e)}
    
    async def _simulate_execution(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate order execution (for paper trading)"""
        # Simulate small delay
        await asyncio.sleep(0.1)
        
        # Simulate fill with small slippage
        import random
        slippage_bps = random.uniform(0, 5)
        fill_price = order.get('price', 0)
        
        if fill_price > 0:
            if order['side'] == 'buy':
                fill_price *= (1 + slippage_bps / 10000)
            else:
                fill_price *= (1 - slippage_bps / 10000)
        
        return {
            'filled': True,
            'fill_price': fill_price,
            'slippage_bps': slippage_bps,
        }
    
    async def _cancel_order(self, order_id: str, reason: str) -> bool:
        """Cancel a pending order"""
        if order_id not in self._pending_orders:
            return False
        
        order = self._pending_orders[order_id]
        order['status'] = 'cancelled'
        order['cancel_reason'] = reason
        order['cancelled_at'] = datetime.utcnow().isoformat()
        
        del self._pending_orders[order_id]
        
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventTypes.ORDER_CANCELLED,
                payload=order,
                source=self.SERVICE_NAME,
            ))
        
        logger.info(f"Order {order_id} cancelled: {reason}")
        return True
    
    async def _execution_loop(self) -> None:
        """Main execution monitoring loop"""
        while self._running:
            try:
                # Monitor pending orders
                for order_id, order in list(self._pending_orders.items()):
                    # Check for stale orders
                    created_at = datetime.fromisoformat(order['created_at'])
                    age_seconds = (datetime.utcnow() - created_at).total_seconds()
                    
                    if age_seconds > 300:  # 5 minutes
                        await self._cancel_order(order_id, "Order timeout")
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Execution loop error: {e}")
                await asyncio.sleep(5)
    
    def get_pending_orders(self) -> Dict[str, Dict]:
        """Get all pending orders"""
        return self._pending_orders.copy()
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return self._execution_stats.copy()

    def _coerce_counterintelligence_mode(self, value: Any) -> CounterintelligenceMode:
        if isinstance(value, CounterintelligenceMode):
            return value
        try:
            return CounterintelligenceMode(str(value))
        except ValueError:
            return CounterintelligenceMode.HARD_GATE
