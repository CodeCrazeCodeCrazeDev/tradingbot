"""
Emergency Controls - One-click emergency operations

Provides emergency controls for critical situations with tested runbooks.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class EmergencyAction(Enum):
    """Emergency action types"""
    FLAT_BOOK = 'flat_book'
    CANCEL_ALL = 'cancel_all'
    HALT_ALL = 'halt_all'
    PAUSE_TRADING = 'pause_trading'
    REDUCE_EXPOSURE = 'reduce_exposure'
    EMERGENCY_HEDGE = 'emergency_hedge'


@dataclass
class EmergencyEvent:
    """Emergency event record"""
    action: EmergencyAction
    trigger: str
    timestamp: datetime
    executed_by: str
    result: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EmergencyControls:
    """Emergency control system with one-click operations"""
    
    def __init__(self, survival_core, config: Optional[Dict[str, Any]] = None):
        self.survival_core = survival_core
        self.config = config or {}
        
        # Emergency event history
        self.emergency_events: List[EmergencyEvent] = []
        
        # Emergency state
        self.emergency_mode = False
        self.last_emergency = None
        
        # Confirmation requirements
        self.require_confirmation = self.config.get('require_confirmation', True)
        
        logger.info("Emergency controls initialized")
    
    async def flat_book(self, reason: str = "Manual emergency", 
                       executed_by: str = "system") -> Dict[str, Any]:
        """
        Emergency: Close all positions immediately
        
        Args:
            reason: Reason for flattening book
            executed_by: Who triggered the action
            
        Returns:
            Result summary
        """
        logger.critical(f"EMERGENCY: Flattening book - {reason}")
        
        try:
            # Get all active positions
            positions = self.survival_core.execution.get_active_positions()
            
            # Close all positions
            closed_positions = []
            failed_positions = []
            
            for position in positions:
                try:
                    order = await self.survival_core.execution.close_position(
                        position.symbol,
                        market_order=True
                    )
                    
                    if order and order.status != 'rejected':
                        closed_positions.append(position.symbol)
                    else:
                        failed_positions.append(position.symbol)
                        
                except Exception as e:
                    logger.error(f"Failed to close {position.symbol}: {e}")
                    failed_positions.append(position.symbol)
            
            # Record event
            event = EmergencyEvent(
                action=EmergencyAction.FLAT_BOOK,
                trigger=reason,
                timestamp=datetime.now(),
                executed_by=executed_by,
                result=f"Closed {len(closed_positions)}/{len(positions)} positions",
                metadata={
                    'closed': closed_positions,
                    'failed': failed_positions
                }
            )
            self.emergency_events.append(event)
            self.last_emergency = datetime.now()
            
            # Pause trading
            await self.survival_core.pause()
            
            # Send notification
            await self.survival_core._send_notification(
                "Emergency: Book Flattened",
                f"All positions closed. Reason: {reason}\n"
                f"Closed: {len(closed_positions)}, Failed: {len(failed_positions)}",
                level="critical"
            )
            
            return {
                'success': True,
                'closed_count': len(closed_positions),
                'failed_count': len(failed_positions),
                'closed_positions': closed_positions,
                'failed_positions': failed_positions
            }
            
        except Exception as e:
            logger.error(f"Error flattening book: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_all_orders(self, reason: str = "Manual emergency",
                               executed_by: str = "system") -> Dict[str, Any]:
        """
        Emergency: Cancel all pending orders
        
        Args:
            reason: Reason for cancellation
            executed_by: Who triggered the action
            
        Returns:
            Result summary
        """
        logger.critical(f"EMERGENCY: Cancelling all orders - {reason}")
        
        try:
            # Get all pending/working orders
            orders = self.survival_core.execution.get_orders(
                status=None  # Get all non-final orders
            )
            
            pending_orders = [
                o for o in orders 
                if o.status.value in ['pending', 'submitted', 'partially_filled']
            ]
            
            # Cancel all
            cancelled = []
            failed = []
            
            for order in pending_orders:
                try:
                    success = await self.survival_core.execution.cancel_order(order.id)
                    if success:
                        cancelled.append(order.id)
                    else:
                        failed.append(order.id)
                except Exception as e:
                    logger.error(f"Failed to cancel {order.id}: {e}")
                    failed.append(order.id)
            
            # Record event
            event = EmergencyEvent(
                action=EmergencyAction.CANCEL_ALL,
                trigger=reason,
                timestamp=datetime.now(),
                executed_by=executed_by,
                result=f"Cancelled {len(cancelled)}/{len(pending_orders)} orders",
                metadata={
                    'cancelled': cancelled,
                    'failed': failed
                }
            )
            self.emergency_events.append(event)
            
            # Send notification
            await self.survival_core._send_notification(
                "Emergency: All Orders Cancelled",
                f"Reason: {reason}\nCancelled: {len(cancelled)}, Failed: {len(failed)}",
                level="critical"
            )
            
            return {
                'success': True,
                'cancelled_count': len(cancelled),
                'failed_count': len(failed),
                'cancelled_orders': cancelled,
                'failed_orders': failed
            }
            
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def halt_all_trading(self, reason: str = "Manual emergency",
                              executed_by: str = "system") -> Dict[str, Any]:
        """
        Emergency: Halt all trading activity
        
        Args:
            reason: Reason for halt
            executed_by: Who triggered the action
            
        Returns:
            Result summary
        """
        logger.critical(f"EMERGENCY: Halting all trading - {reason}")
        
        try:
            # Cancel all orders
            cancel_result = await self.cancel_all_orders(reason, executed_by)
            
            # Pause trading
            await self.survival_core.pause()
            
            # Set emergency mode
            self.emergency_mode = True
            
            # Record event
            event = EmergencyEvent(
                action=EmergencyAction.HALT_ALL,
                trigger=reason,
                timestamp=datetime.now(),
                executed_by=executed_by,
                result="Trading halted",
                metadata={
                    'cancel_result': cancel_result
                }
            )
            self.emergency_events.append(event)
            
            # Send notification
            await self.survival_core._send_notification(
                "Emergency: Trading Halted",
                f"All trading activity stopped. Reason: {reason}",
                level="critical"
            )
            
            return {
                'success': True,
                'emergency_mode': self.emergency_mode,
                'cancel_result': cancel_result
            }
            
        except Exception as e:
            logger.error(f"Error halting trading: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def reduce_exposure(self, target_pct: float = 0.5,
                             reason: str = "Risk reduction",
                             executed_by: str = "system") -> Dict[str, Any]:
        """
        Emergency: Reduce exposure to target percentage
        
        Args:
            target_pct: Target exposure (0.5 = 50% reduction)
            reason: Reason for reduction
            executed_by: Who triggered the action
            
        Returns:
            Result summary
        """
        logger.warning(f"EMERGENCY: Reducing exposure to {target_pct:.0%} - {reason}")
        
        try:
            positions = self.survival_core.execution.get_active_positions()
            
            reduced = []
            failed = []
            
            for position in positions:
                try:
                    # Calculate reduction amount
                    current_qty = abs(position.quantity)
                    target_qty = current_qty * target_pct
                    reduce_qty = current_qty - target_qty
                    
                    if reduce_qty > 0:
                        # Partially close position
                        side = 'sell' if position.quantity > 0 else 'buy'
                        
                        order = await self.survival_core.execution.place_order(
                            symbol=position.symbol,
                            order_type='market',
                            side=side,
                            quantity=reduce_qty,
                            metadata={'purpose': 'emergency_reduction'}
                        )
                        
                        if order:
                            reduced.append({
                                'symbol': position.symbol,
                                'reduced_qty': reduce_qty
                            })
                        else:
                            failed.append(position.symbol)
                            
                except Exception as e:
                    logger.error(f"Failed to reduce {position.symbol}: {e}")
                    failed.append(position.symbol)
            
            # Record event
            event = EmergencyEvent(
                action=EmergencyAction.REDUCE_EXPOSURE,
                trigger=reason,
                timestamp=datetime.now(),
                executed_by=executed_by,
                result=f"Reduced {len(reduced)} positions to {target_pct:.0%}",
                metadata={
                    'target_pct': target_pct,
                    'reduced': reduced,
                    'failed': failed
                }
            )
            self.emergency_events.append(event)
            
            # Send notification
            await self.survival_core._send_notification(
                "Emergency: Exposure Reduced",
                f"Reduced to {target_pct:.0%}. Reason: {reason}\n"
                f"Reduced: {len(reduced)}, Failed: {len(failed)}",
                level="warning"
            )
            
            return {
                'success': True,
                'reduced_count': len(reduced),
                'failed_count': len(failed),
                'reduced_positions': reduced,
                'failed_positions': failed
            }
            
        except Exception as e:
            logger.error(f"Error reducing exposure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_emergency_history(self, limit: int = 10) -> List[EmergencyEvent]:
        """Get recent emergency events"""
        return self.emergency_events[-limit:]
    
    def clear_emergency_mode(self):
        """Clear emergency mode"""
        self.emergency_mode = False
        logger.info("Emergency mode cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get emergency controls status"""
        return {
            'emergency_mode': self.emergency_mode,
            'last_emergency': self.last_emergency.isoformat() if self.last_emergency else None,
            'total_events': len(self.emergency_events),
            'recent_events': [
                {
                    'action': e.action.value,
                    'trigger': e.trigger,
                    'timestamp': e.timestamp.isoformat(),
                    'result': e.result
                }
                for e in self.emergency_events[-5:]
            ]
        }
