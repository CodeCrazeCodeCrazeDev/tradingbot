"""
AlphaAlgo Manual Override - Human Control

This module provides manual override capabilities for humans.
Humans can ALWAYS override the bot's decisions.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import logging
import asyncio

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


class OverrideAction(Enum):
    """Types of override actions"""
    PAUSE_TRADING = "pause_trading"
    RESUME_TRADING = "resume_trading"
    CLOSE_ALL_POSITIONS = "close_all_positions"
    CLOSE_POSITION = "close_position"
    CANCEL_ALL_ORDERS = "cancel_all_orders"
    CANCEL_ORDER = "cancel_order"
    FORCE_SIGNAL = "force_signal"
    BLOCK_SIGNAL = "block_signal"
    CHANGE_MODE = "change_mode"
    EMERGENCY_STOP = "emergency_stop"
    RESTART_SYSTEM = "restart_system"


@dataclass
class OverrideResult:
    """Result of an override action"""
    success: bool
    action: OverrideAction
    user: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'action': self.action.value,
            'user': self.user,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'error': self.error,
        }


class EmergencyStop:
    """
    Emergency stop mechanism.
    
    When triggered:
    1. Immediately stops all trading
    2. Cancels all pending orders
    3. Optionally closes all positions
    4. Sends emergency alerts
    5. Logs the event
    """
    
    def __init__(self):
        self._triggered = False
        self._trigger_time: Optional[datetime] = None
        self._trigger_reason: Optional[str] = None
        self._triggered_by: Optional[str] = None
        self._callbacks: List[Callable] = []
    
    @property
    def is_triggered(self) -> bool:
        return self._triggered
    
    @property
    def trigger_reason(self) -> Optional[str]:
        return self._trigger_reason
    
    def add_callback(self, callback: Callable) -> None:
        """Add callback to be called on emergency stop"""
        self._callbacks.append(callback)
    
    async def trigger(self, reason: str, user: str) -> bool:
        """
        Trigger emergency stop.
        
        This IMMEDIATELY stops all trading activity.
        """
        if self._triggered:
            logger.warning("Emergency stop already triggered")
            return False
        
        self._triggered = True
        self._trigger_time = datetime.now()
        self._trigger_reason = reason
        self._triggered_by = user
        
        logger.critical(f"EMERGENCY STOP TRIGGERED by {user}: {reason}")
        
        # Execute callbacks
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reason, user)
                else:
                    callback(reason, user)
            except Exception as e:
                logger.error(f"Emergency stop callback failed: {e}")
        
        return True
    
    def reset(self, user: str) -> bool:
        """
        Reset emergency stop.
        
        This allows trading to resume.
        """
        if not self._triggered:
            return False
        
        logger.warning(f"Emergency stop reset by {user}")
        
        self._triggered = False
        self._trigger_time = None
        self._trigger_reason = None
        self._triggered_by = None
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'triggered': self._triggered,
            'trigger_time': self._trigger_time.isoformat() if self._trigger_time else None,
            'trigger_reason': self._trigger_reason,
            'triggered_by': self._triggered_by,
        }


class ManualOverride:
    """
    Manual override system for human control.
    
    This system allows humans to:
    1. Pause/resume trading
    2. Close positions
    3. Cancel orders
    4. Force or block signals
    5. Change trading mode
    6. Trigger emergency stop
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Emergency stop
        self.emergency_stop = EmergencyStop()
        
        # Override handlers
        self._handlers: Dict[OverrideAction, Callable] = {}
        
        # Override history
        self._history: List[OverrideResult] = []
        self._max_history = 1000
        
        # Current state
        self._trading_paused = False
        self._blocked_signals: List[str] = []
        self._forced_signals: List[Dict[str, Any]] = []
        
        logger.info("ManualOverride initialized")
    
    def register_handler(self, action: OverrideAction, handler: Callable) -> None:
        """Register a handler for an override action"""
        self._handlers[action] = handler
        logger.info(f"Registered handler for {action.value}")
    
    async def execute(
        self,
        action: OverrideAction,
        user: str,
        params: Optional[Dict[str, Any]] = None
    ) -> OverrideResult:
        """
        Execute a manual override action.
        
        Args:
            action: The override action to execute
            user: The user executing the override
            params: Additional parameters
        
        Returns:
            OverrideResult with outcome
        """
        params = params or {}
        
        logger.info(f"Manual override: {action.value} by {user}")
        
        try:
            # Handle built-in actions
            if action == OverrideAction.EMERGENCY_STOP:
                reason = params.get('reason', 'Manual emergency stop')
                await self.emergency_stop.trigger(reason, user)
                result = OverrideResult(
                    success=True,
                    action=action,
                    user=user,
                    timestamp=datetime.now(),
                    details={'reason': reason},
                )
            
            elif action == OverrideAction.PAUSE_TRADING:
                self._trading_paused = True
                result = OverrideResult(
                    success=True,
                    action=action,
                    user=user,
                    timestamp=datetime.now(),
                    details={'trading_paused': True},
                )
            
            elif action == OverrideAction.RESUME_TRADING:
                if self.emergency_stop.is_triggered:
                    result = OverrideResult(
                        success=False,
                        action=action,
                        user=user,
                        timestamp=datetime.now(),
                        error="Cannot resume: Emergency stop is active",
                    )
                else:
                    self._trading_paused = False
                    result = OverrideResult(
                        success=True,
                        action=action,
                        user=user,
                        timestamp=datetime.now(),
                        details={'trading_paused': False},
                    )
            
            elif action == OverrideAction.BLOCK_SIGNAL:
                signal_id = params.get('signal_id')
                if signal_id:
                    self._blocked_signals.append(signal_id)
                    result = OverrideResult(
                        success=True,
                        action=action,
                        user=user,
                        timestamp=datetime.now(),
                        details={'blocked_signal': signal_id},
                    )
                else:
                    result = OverrideResult(
                        success=False,
                        action=action,
                        user=user,
                        timestamp=datetime.now(),
                        error="No signal_id provided",
                    )
            
            elif action == OverrideAction.FORCE_SIGNAL:
                signal = params.get('signal')
                if signal:
                    self._forced_signals.append(signal)
                    result = OverrideResult(
                        success=True,
                        action=action,
                        user=user,
                        timestamp=datetime.now(),
                        details={'forced_signal': signal},
                    )
                else:
                    result = OverrideResult(
                        success=False,
                        action=action,
                        user=user,
                        timestamp=datetime.now(),
                        error="No signal provided",
                    )
            
            # Use registered handler for other actions
            elif action in self._handlers:
                handler = self._handlers[action]
                if asyncio.iscoroutinefunction(handler):
                    handler_result = await handler(params)
                else:
                    handler_result = handler(params)
                
                result = OverrideResult(
                    success=True,
                    action=action,
                    user=user,
                    timestamp=datetime.now(),
                    details=handler_result if isinstance(handler_result, dict) else {},
                )
            
            else:
                result = OverrideResult(
                    success=False,
                    action=action,
                    user=user,
                    timestamp=datetime.now(),
                    error=f"No handler for action: {action.value}",
                )
        
        except Exception as e:
            logger.error(f"Override failed: {e}")
            result = OverrideResult(
                success=False,
                action=action,
                user=user,
                timestamp=datetime.now(),
                error=str(e),
            )
        
        # Store in history
        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        return result
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed"""
        if self.emergency_stop.is_triggered:
            return False
        if self._trading_paused:
            return False
        return True
    
    def is_signal_blocked(self, signal_id: str) -> bool:
        """Check if a signal is blocked"""
        return signal_id in self._blocked_signals
    
    def get_forced_signals(self) -> List[Dict[str, Any]]:
        """Get and clear forced signals"""
        signals = self._forced_signals.copy()
        self._forced_signals.clear()
        return signals
    
    def get_status(self) -> Dict[str, Any]:
        """Get current override status"""
        return {
            'trading_paused': self._trading_paused,
            'emergency_stop': self.emergency_stop.get_status(),
            'blocked_signals_count': len(self._blocked_signals),
            'forced_signals_count': len(self._forced_signals),
            'trading_allowed': self.is_trading_allowed(),
        }
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get override history"""
        return [r.to_dict() for r in self._history[-limit:]]


# =============================================================================
# SINGLETON
# =============================================================================

_override_instance: Optional[ManualOverride] = None


def get_manual_override(config: Optional[Dict[str, Any]] = None) -> ManualOverride:
    """Get the singleton manual override"""
    global _override_instance
    if _override_instance is None:
        _override_instance = ManualOverride(config)
    return _override_instance


async def emergency_stop(reason: str, user: str) -> bool:
    """Trigger emergency stop"""
    override = get_manual_override()
    return await override.emergency_stop.trigger(reason, user)


def is_trading_allowed() -> bool:
    """Check if trading is allowed"""
    override = get_manual_override()
    return override.is_trading_allowed()


async def pause_trading(user: str) -> OverrideResult:
    """Pause trading"""
    override = get_manual_override()
    return await override.execute(OverrideAction.PAUSE_TRADING, user)


async def resume_trading(user: str) -> OverrideResult:
    """Resume trading"""
    override = get_manual_override()
    return await override.execute(OverrideAction.RESUME_TRADING, user)
