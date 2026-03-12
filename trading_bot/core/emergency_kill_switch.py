"""
Emergency Kill Switch - Core Module
====================================

Central emergency kill switch that integrates with all trading components.
Provides immediate shutdown capability with multiple trigger mechanisms.

This module re-exports and extends the safety module's kill switch
to ensure it's available from trading_bot.core.
"""

import logging
import asyncio
import threading
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)


class EmergencyLevel(Enum):
    """Emergency severity levels"""
    NONE = auto()           # No emergency
    CAUTION = auto()        # Minor issue - monitor closely
    WARNING = auto()        # Significant issue - reduce activity
    CRITICAL = auto()       # Major issue - stop new trades
    EMERGENCY = auto()      # Emergency - close all positions immediately


@dataclass
class EmergencyEvent:
    """Record of an emergency event"""
    timestamp: datetime
    level: EmergencyLevel
    trigger: str
    reason: str
    positions_closed: int
    time_to_stop_ms: float
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "trigger": self.trigger,
            "reason": self.reason,
            "positions_closed": self.positions_closed,
            "time_to_stop_ms": self.time_to_stop_ms
        }


class EmergencyKillSwitch:
    """
    Emergency kill switch for immediate trading shutdown.
    
    Features:
    - Multiple trigger mechanisms (file, API, signal, threshold)
    - Immediate position closure
    - Cannot be bypassed once activated at EMERGENCY level
    - Full audit trail
    - Integration with broker adapters
    
    IMMUTABLE RULES:
    - EMERGENCY level cannot be deactivated programmatically
    - All activations are logged permanently
    - Human intervention required to resume after EMERGENCY
    """
    
    # Kill switch trigger files
    KILL_FILES = [
        "EMERGENCY_STOP.txt",
        "KILL_SWITCH.txt", 
        "STOP_TRADING.txt",
        ".kill_switch"
    ]
    
    def __init__(
        self,
        broker_adapter=None,
        max_drawdown: float = 0.15,
        max_daily_loss: float = 0.05,
        max_consecutive_losses: int = 5,
        on_activate: Optional[Callable] = None,
        on_deactivate: Optional[Callable] = None
    ):
        """
        Initialize emergency kill switch.
        
        Args:
            broker_adapter: Broker adapter for position management
            max_drawdown: Maximum drawdown before emergency (default 15%)
            max_daily_loss: Maximum daily loss before emergency (default 5%)
            max_consecutive_losses: Max consecutive losses before warning
            on_activate: Callback when kill switch activates
            on_deactivate: Callback when kill switch deactivates
        """
        self._lock = threading.RLock()
        self.broker = broker_adapter
        self.max_drawdown = max_drawdown
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.on_activate = on_activate
        self.on_deactivate = on_deactivate
        
        # State
        self._level = EmergencyLevel.NONE
        self._activated = False
        self._activation_time: Optional[datetime] = None
        self._activation_reason: Optional[str] = None
        
        # Tracking
        self._consecutive_losses = 0
        self._peak_equity: Optional[float] = None
        self._daily_start_equity: Optional[float] = None
        self._last_reset_date: Optional[str] = None
        
        # Event history
        self._events: List[EmergencyEvent] = []
        
        # Check for existing kill files
        self._check_kill_files()
        
        logger.info("EmergencyKillSwitch initialized")
    
    @property
    def is_active(self) -> bool:
        """Check if kill switch is active"""
        return self._activated or self._level.value >= EmergencyLevel.CRITICAL.value
    
    @property
    def level(self) -> EmergencyLevel:
        """Get current emergency level"""
        return self._level
    
    @property
    def can_trade(self) -> bool:
        """Check if trading is allowed"""
        return not self.is_active and self._level.value < EmergencyLevel.CRITICAL.value
    
    @property
    def can_open_positions(self) -> bool:
        """Check if new positions can be opened"""
        return self._level.value < EmergencyLevel.WARNING.value
    
    def _check_kill_files(self):
        """Check for kill switch files on startup"""
        for filename in self.KILL_FILES:
            if Path(filename).exists():
                logger.critical(f"Kill switch file found: {filename}")
                self._level = EmergencyLevel.EMERGENCY
                self._activated = True
                self._activation_time = datetime.utcnow()
                self._activation_reason = f"Kill switch file: {filename}"
                break
    
    def activate(
        self,
        level: EmergencyLevel = EmergencyLevel.EMERGENCY,
        reason: str = "Manual activation",
        close_positions: bool = True
    ) -> EmergencyEvent:
        """
        Activate the kill switch.
        
        Args:
            level: Emergency level
            reason: Reason for activation
            close_positions: Whether to close all positions
            
        Returns:
            EmergencyEvent with details
        """
        start_time = datetime.utcnow()
        
        with self._lock:
            # Cannot downgrade from EMERGENCY
            if self._level == EmergencyLevel.EMERGENCY and level.value < EmergencyLevel.EMERGENCY.value:
                logger.warning("Cannot downgrade from EMERGENCY level")
                level = EmergencyLevel.EMERGENCY
            
            self._level = level
            
            if level.value >= EmergencyLevel.CRITICAL.value:
                self._activated = True
                self._activation_time = start_time
                self._activation_reason = reason
        
        logger.critical(f"KILL SWITCH ACTIVATED: Level={level.name}, Reason={reason}")
        
        # Close positions if requested
        positions_closed = 0
        if close_positions and level.value >= EmergencyLevel.CRITICAL.value:
            positions_closed = self._close_all_positions()
        
        # Calculate time
        time_to_stop = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create event
        event = EmergencyEvent(
            timestamp=start_time,
            level=level,
            trigger="api",
            reason=reason,
            positions_closed=positions_closed,
            time_to_stop_ms=time_to_stop
        )
        self._events.append(event)
        
        # Callback
        if self.on_activate:
            try:
                self.on_activate(event)
            except Exception as e:
                logger.error(f"Activation callback error: {e}")
        
        # Create kill switch file
        if level == EmergencyLevel.EMERGENCY:
            self._create_kill_file(reason)
        
        return event
    
    def _close_all_positions(self) -> int:
        """Close all open positions"""
        if not self.broker:
            logger.warning("No broker adapter - cannot close positions")
            return 0
        
        positions_closed = 0
        
        try:
            # Get positions
            if hasattr(self.broker, 'get_positions'):
                positions = self.broker.get_positions()
            elif hasattr(self.broker, 'positions_get'):
                positions = self.broker.positions_get() or []
            else:
                logger.error("Broker does not support position retrieval")
                return 0
            
            # Close each position
            for pos in positions or []:
                try:
                    ticket = pos.ticket if hasattr(pos, 'ticket') else pos.get('ticket')
                    
                    if hasattr(self.broker, 'close_position'):
                        success = self.broker.close_position(ticket)
                    elif hasattr(self.broker, 'close_all_positions'):
                        success = self.broker.close_all_positions()
                        positions_closed = len(positions) if success else 0
                        break
                    else:
                        logger.error("Broker does not support position closing")
                        break
                    
                    if success:
                        positions_closed += 1
                        logger.info(f"Closed position {ticket}")
                        
                except Exception as e:
                    logger.error(f"Error closing position: {e}")
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
        
        logger.info(f"Closed {positions_closed} positions")
        return positions_closed
    
    def _create_kill_file(self, reason: str):
        """Create kill switch file"""
        try:
            with open(self.KILL_FILES[0], 'w') as f:
                f.write(f"Kill switch activated at {datetime.utcnow().isoformat()}\n")
                f.write(f"Reason: {reason}\n")
                f.write("Delete this file and restart to resume trading.\n")
            logger.info(f"Created kill switch file: {self.KILL_FILES[0]}")
        except Exception as e:
            logger.error(f"Failed to create kill file: {e}")
    
    def deactivate(self, authorization_code: str = None) -> bool:
        """
        Deactivate the kill switch.
        
        IMPORTANT: Cannot deactivate EMERGENCY level programmatically.
        Must delete kill switch file and restart.
        
        Args:
            authorization_code: Required for CRITICAL level
            
        Returns:
            True if deactivated
        """
        with self._lock:
            if self._level == EmergencyLevel.EMERGENCY:
                logger.critical("Cannot deactivate EMERGENCY level programmatically")
                logger.critical("Delete EMERGENCY_STOP.txt and restart to resume trading")
                return False
            
            if self._level == EmergencyLevel.CRITICAL:
                # Require authorization for CRITICAL
                if not authorization_code:
                    logger.warning("Authorization code required to deactivate CRITICAL")
                    return False
            
            old_level = self._level
            self._level = EmergencyLevel.NONE
            self._activated = False
            self._activation_time = None
            self._activation_reason = None
            
            logger.info(f"Kill switch deactivated from {old_level.name}")
            
            if self.on_deactivate:
                try:
                    self.on_deactivate()
                except Exception as e:
                    logger.error(f"Deactivation callback error: {e}")
            
            return True
    
    def check_thresholds(
        self,
        current_equity: float,
        last_trade_pnl: Optional[float] = None
    ) -> EmergencyLevel:
        """
        Check thresholds and update emergency level.
        
        Args:
            current_equity: Current account equity
            last_trade_pnl: PnL of last trade (if any)
            
        Returns:
            Current emergency level
        """
        with self._lock:
            # Reset daily tracking at start of new day
            current_date = datetime.utcnow().strftime("%Y-%m-%d")
            if self._last_reset_date != current_date:
                self._daily_start_equity = current_equity
                self._last_reset_date = current_date
            
            # Initialize tracking
            if self._daily_start_equity is None:
                self._daily_start_equity = current_equity
            if self._peak_equity is None or current_equity > self._peak_equity:
                self._peak_equity = current_equity
            
            # Track consecutive losses
            if last_trade_pnl is not None:
                if last_trade_pnl < 0:
                    self._consecutive_losses += 1
                else:
                    self._consecutive_losses = 0
            
            # Calculate metrics
            drawdown = (self._peak_equity - current_equity) / self._peak_equity if self._peak_equity > 0 else 0
            daily_loss = (self._daily_start_equity - current_equity) / self._daily_start_equity if self._daily_start_equity > 0 else 0
            
            # Determine level based on thresholds
            new_level = EmergencyLevel.NONE
            
            if drawdown > self.max_drawdown or daily_loss > self.max_daily_loss:
                new_level = EmergencyLevel.EMERGENCY
                reason = f"Drawdown: {drawdown:.1%}, Daily loss: {daily_loss:.1%}"
                self.activate(new_level, reason)
            elif drawdown > self.max_drawdown * 0.8 or daily_loss > self.max_daily_loss * 0.8:
                new_level = EmergencyLevel.CRITICAL
            elif drawdown > self.max_drawdown * 0.6 or daily_loss > self.max_daily_loss * 0.6:
                new_level = EmergencyLevel.WARNING
            elif self._consecutive_losses >= self.max_consecutive_losses:
                new_level = EmergencyLevel.CAUTION
            
            # Only upgrade level, never downgrade automatically
            if new_level.value > self._level.value:
                self._level = new_level
                logger.warning(f"Emergency level raised to {new_level.name}")
            
            return self._level
    
    def reset(self):
        """Reset tracking (use with caution)"""
        with self._lock:
            self._consecutive_losses = 0
            self._peak_equity = None
            self._daily_start_equity = None
            logger.info("Kill switch tracking reset")
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            "is_active": self.is_active,
            "level": self._level.name,
            "can_trade": self.can_trade,
            "can_open_positions": self.can_open_positions,
            "activated": self._activated,
            "activation_time": self._activation_time.isoformat() if self._activation_time else None,
            "activation_reason": self._activation_reason,
            "consecutive_losses": self._consecutive_losses,
            "peak_equity": self._peak_equity,
            "daily_start_equity": self._daily_start_equity,
            "recent_events": [e.to_dict() for e in self._events[-10:]]
        }
    
    def stop(self):
        """Alias for activate with EMERGENCY level"""
        return self.activate(EmergencyLevel.EMERGENCY, "Emergency stop called")
    
    def shutdown(self):
        """Alias for activate with EMERGENCY level"""
        return self.activate(EmergencyLevel.EMERGENCY, "Shutdown called")
    
    def kill(self):
        """Alias for activate with EMERGENCY level"""
        return self.activate(EmergencyLevel.EMERGENCY, "Kill called")


# Global instance
_global_kill_switch: Optional[EmergencyKillSwitch] = None


def get_kill_switch() -> EmergencyKillSwitch:
    """Get global kill switch instance"""
    global _global_kill_switch
    if _global_kill_switch is None:
        _global_kill_switch = EmergencyKillSwitch()
    return _global_kill_switch


def emergency_stop(reason: str = "Emergency stop"):
    """Trigger emergency stop"""
    return get_kill_switch().activate(EmergencyLevel.EMERGENCY, reason)


def can_trade() -> bool:
    """Check if trading is allowed"""
    return get_kill_switch().can_trade
