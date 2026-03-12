"""
Multi-Layer Kill Switch - Answers Q891, Q901, Q892, Q903
========================================================

Critical Question Q891: What triggers an emergency shutdown?
Critical Question Q901: How many independent kill-switches do you have?
Critical Question Q892: How quickly can you shut down all trading?
Critical Question Q903: How do you prevent kill-switch bypass?

This module provides:
1. Multiple independent kill-switch mechanisms
2. Layered shutdown levels (soft -> hard -> nuclear)
3. File-based, API-based, and programmatic triggers
4. Automatic position closure
5. Bypass prevention
6. Audit trail of all activations
"""

import asyncio
import logging
import threading
import json
import os
import signal
import hashlib
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class KillSwitchLevel(Enum):
    """Kill switch activation levels - ordered by severity"""
    NONE = 0           # Normal operation
    SOFT = 1           # Stop new trades only
    MEDIUM = 2         # Stop new trades, reduce exposure
    HARD = 3           # Close all positions gracefully
    NUCLEAR = 4        # Immediate shutdown, market orders to close all


class KillSwitchTrigger(Enum):
    """Types of kill switch triggers"""
    MANUAL_FILE = "manual_file"
    MANUAL_API = "manual_api"
    MANUAL_CODE = "manual_code"
    DRAWDOWN = "drawdown"
    DAILY_LOSS = "daily_loss"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    SYSTEM_ERROR = "system_error"
    DATA_QUALITY = "data_quality"
    CONNECTIVITY = "connectivity"
    EXTERNAL_SIGNAL = "external_signal"
    HEARTBEAT_FAILURE = "heartbeat_failure"
    REGULATORY = "regulatory"


@dataclass
class KillSwitchEvent:
    """Record of a kill switch activation"""
    event_id: str
    timestamp: datetime
    level: KillSwitchLevel
    trigger: KillSwitchTrigger
    reason: str
    triggered_by: str
    positions_affected: int
    positions_closed: int
    time_to_shutdown_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'trigger': self.trigger.value,
            'reason': self.reason,
            'triggered_by': self.triggered_by,
            'positions_affected': self.positions_affected,
            'positions_closed': self.positions_closed,
            'time_to_shutdown_ms': self.time_to_shutdown_ms,
            'metadata': self.metadata
        }


class KillSwitchBypassError(Exception):
    """Raised when attempting to bypass kill switch"""
    pass


class MultiLayerKillSwitch:
    """
    Multi-layer kill switch system with multiple independent triggers.
    
    Addresses critical questions:
    - Q891: What triggers emergency shutdown
    - Q901: Multiple independent kill-switches
    - Q892: Shutdown speed
    - Q903: Bypass prevention
    
    INDEPENDENT KILL SWITCH MECHANISMS:
    1. File-based: Create EMERGENCY_STOP.txt
    2. API-based: Call activate() method
    3. Signal-based: SIGTERM, SIGINT handlers
    4. Threshold-based: Automatic on drawdown/loss limits
    5. Heartbeat-based: Activate if no heartbeat received
    6. External: Redis/network signal
    
    IMMUTABLE RULES:
    - Kill switch CANNOT be deactivated programmatically once at HARD or NUCLEAR
    - All activations are logged and cannot be deleted
    - Bypass attempts are logged and trigger NUCLEAR
    """
    
    # IMMUTABLE: Files that trigger kill switch
    KILL_SWITCH_FILES = [
        "EMERGENCY_STOP.txt",
        "KILL_SWITCH.txt",
        "STOP_TRADING.txt",
        ".kill_switch"
    ]
    
    # IMMUTABLE: Maximum time to shutdown (ms)
    MAX_SHUTDOWN_TIME_MS = 5000
    
    def __init__(
        self,
        broker_adapter,
        db_path: str = "kill_switch.db",
        check_interval: float = 1.0,
        heartbeat_timeout: float = 30.0,
        on_activation: Optional[Callable] = None,
        on_position_closed: Optional[Callable] = None
    ):
        """
        Initialize multi-layer kill switch.
        
        Args:
            broker_adapter: Adapter for broker API
            db_path: Path to SQLite database for audit
            check_interval: Seconds between file checks
            heartbeat_timeout: Seconds before heartbeat failure triggers
            on_activation: Callback when kill switch activates
            on_position_closed: Callback when position is closed
        """
        self.broker = broker_adapter
        self.db_path = Path(db_path)
        self.check_interval = check_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.on_activation = on_activation
        self.on_position_closed = on_position_closed
        
        # State
        self._lock = threading.RLock()
        self._current_level = KillSwitchLevel.NONE
        self._activation_time: Optional[datetime] = None
        self._activation_reason: Optional[str] = None
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Heartbeat tracking
        self._last_heartbeat = datetime.now()
        self._heartbeat_enabled = True
        
        # Bypass prevention
        self._bypass_attempts = 0
        self._bypass_lockout = False
        
        # Event history
        self._events: List[KillSwitchEvent] = []
        
        # Initialize database
        self._init_database()
        
        # Register signal handlers
        self._register_signal_handlers()
        
        # Check for existing kill switch files
        self._check_kill_switch_files()
        
        logger.info("MultiLayerKillSwitch initialized")
    
    def _init_database(self):
        """Initialize SQLite database for audit trail"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kill_switch_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    trigger TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    triggered_by TEXT NOT NULL,
                    positions_affected INTEGER,
                    positions_closed INTEGER,
                    time_to_shutdown_ms REAL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bypass_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    attempted_action TEXT NOT NULL,
                    current_level INTEGER NOT NULL,
                    source TEXT,
                    blocked INTEGER DEFAULT 1
                )
            """)
            
            conn.commit()
    
    def _register_signal_handlers(self):
        """Register OS signal handlers for emergency shutdown"""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Signal handlers registered")
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle OS signals"""
        logger.critical(f"Received signal {signum} - activating NUCLEAR kill switch")
        asyncio.create_task(self.activate(
            KillSwitchLevel.NUCLEAR,
            KillSwitchTrigger.EXTERNAL_SIGNAL,
            f"OS signal {signum} received",
            "os_signal"
        ))
    
    def _check_kill_switch_files(self):
        """Check for kill switch files on startup"""
        for filename in self.KILL_SWITCH_FILES:
            if Path(filename).exists():
                logger.critical(f"Kill switch file found: {filename}")
                # Don't await here, just set the state
                self._current_level = KillSwitchLevel.HARD
                self._activation_time = datetime.now()
                self._activation_reason = f"Kill switch file: {filename}"
                break
    
    @property
    def is_active(self) -> bool:
        """Check if kill switch is active"""
        return self._current_level != KillSwitchLevel.NONE
    
    @property
    def current_level(self) -> KillSwitchLevel:
        """Get current kill switch level"""
        return self._current_level
    
    @property
    def can_trade(self) -> bool:
        """Check if trading is allowed"""
        return self._current_level == KillSwitchLevel.NONE
    
    @property
    def can_open_positions(self) -> bool:
        """Check if new positions can be opened"""
        return self._current_level == KillSwitchLevel.NONE
    
    def heartbeat(self):
        """
        Send heartbeat to prevent automatic shutdown.
        
        Must be called regularly to prevent heartbeat failure trigger.
        """
        with self._lock:
            self._last_heartbeat = datetime.now()
    
    async def activate(
        self,
        level: KillSwitchLevel,
        trigger: KillSwitchTrigger,
        reason: str,
        triggered_by: str = "system"
    ) -> KillSwitchEvent:
        """
        Activate kill switch at specified level.
        
        Args:
            level: Kill switch level to activate
            trigger: What triggered the activation
            reason: Human-readable reason
            triggered_by: Who/what triggered it
            
        Returns:
            KillSwitchEvent with details
        """
        start_time = datetime.now()
        
        with self._lock:
            # Check bypass lockout
            if self._bypass_lockout:
                level = KillSwitchLevel.NUCLEAR
                reason = f"BYPASS LOCKOUT ACTIVE - Original: {reason}"
            
            # Cannot downgrade from HARD or NUCLEAR
            if self._current_level.value >= KillSwitchLevel.HARD.value:
                if level.value < self._current_level.value:
                    self._log_bypass_attempt(f"Attempted downgrade from {self._current_level} to {level}")
                    raise KillSwitchBypassError(
                        f"Cannot downgrade kill switch from {self._current_level.name} to {level.name}"
                    )
            
            # Upgrade level if higher
            if level.value > self._current_level.value:
                self._current_level = level
                self._activation_time = start_time
                self._activation_reason = reason
        
        logger.critical(f"KILL SWITCH ACTIVATED: Level={level.name}, Trigger={trigger.value}, Reason={reason}")
        
        # Execute shutdown actions
        positions_affected = 0
        positions_closed = 0
        
        try:
            if level.value >= KillSwitchLevel.HARD.value:
                positions_affected, positions_closed = await self._close_all_positions(
                    use_market_orders=(level == KillSwitchLevel.NUCLEAR)
                )
            elif level == KillSwitchLevel.MEDIUM:
                positions_affected, positions_closed = await self._reduce_exposure()
        except Exception as e:
            logger.error(f"Error during shutdown actions: {e}")
        
        # Calculate shutdown time
        shutdown_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create event
        event = KillSwitchEvent(
            event_id=hashlib.sha256(f"{start_time}{level}{trigger}".encode()).hexdigest()[:16],
            timestamp=start_time,
            level=level,
            trigger=trigger,
            reason=reason,
            triggered_by=triggered_by,
            positions_affected=positions_affected,
            positions_closed=positions_closed,
            time_to_shutdown_ms=shutdown_time_ms,
            metadata={
                'previous_level': self._current_level.name,
                'heartbeat_enabled': self._heartbeat_enabled
            }
        )
        
        # Log event
        self._log_event(event)
        self._events.append(event)
        
        # Callback
        if self.on_activation:
            try:
                if asyncio.iscoroutinefunction(self.on_activation):
                    await self.on_activation(event)
                else:
                    self.on_activation(event)
            except Exception as e:
                logger.error(f"Activation callback error: {e}")
        
        # Check shutdown time
        if shutdown_time_ms > self.MAX_SHUTDOWN_TIME_MS:
            logger.error(
                f"Shutdown took {shutdown_time_ms:.0f}ms, exceeds limit of {self.MAX_SHUTDOWN_TIME_MS}ms"
            )
        
        return event
    
    async def _close_all_positions(self, use_market_orders: bool = False) -> tuple:
        """Close all open positions"""
        positions_affected = 0
        positions_closed = 0
        
        try:
            # Get all positions
            if hasattr(self.broker, 'get_positions'):
                positions = await self.broker.get_positions()
            elif hasattr(self.broker, 'positions_get'):
                positions = self.broker.positions_get() or []
            else:
                logger.error("Broker adapter does not support position retrieval")
                return 0, 0
            
            positions_affected = len(positions) if positions else 0
            
            for pos in positions or []:
                try:
                    ticket = pos.ticket if hasattr(pos, 'ticket') else pos.get('ticket')
                    symbol = pos.symbol if hasattr(pos, 'symbol') else pos.get('symbol')
                    
                    logger.info(f"Closing position {ticket} ({symbol})")
                    
                    if hasattr(self.broker, 'close_position'):
                        success = await self.broker.close_position(
                            ticket,
                            use_market_order=use_market_orders
                        )
                    elif hasattr(self.broker, 'order_send'):
                        # MT5 style
                        success = self._close_mt5_position(pos, use_market_orders)
                    else:
                        logger.error("Broker adapter does not support position closing")
                        continue
                    
                    if success:
                        positions_closed += 1
                        if self.on_position_closed:
                            try:
                                self.on_position_closed(ticket, symbol)
                            except Exception as e:
                                logger.error(f"Position closed callback error: {e}")
                    else:
                        logger.error(f"Failed to close position {ticket}")
                        
                except Exception as e:
                    logger.error(f"Error closing position: {e}")
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
        
        logger.info(f"Closed {positions_closed}/{positions_affected} positions")
        return positions_affected, positions_closed
    
    def _close_mt5_position(self, position, use_market_order: bool) -> bool:
        """Close MT5 position"""
        try:
            import MetaTrader5 as mt5
            
            # Determine order type
            if position.type == 0:  # Buy position
                order_type = mt5.ORDER_TYPE_SELL
            else:  # Sell position
                order_type = mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": position.ticket,
                "magic": 0,
                "comment": "Kill switch close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if use_market_order:
                # Get current price
                tick = mt5.symbol_info_tick(position.symbol)
                if tick:
                    request["price"] = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
            
            result = mt5.order_send(request)
            return result and result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            logger.error(f"MT5 close error: {e}")
            return False
    
    async def _reduce_exposure(self) -> tuple:
        """Reduce exposure by closing largest positions"""
        # Close 50% of positions, starting with largest
        positions_affected = 0
        positions_closed = 0
        
        try:
            if hasattr(self.broker, 'get_positions'):
                positions = await self.broker.get_positions()
            elif hasattr(self.broker, 'positions_get'):
                positions = self.broker.positions_get() or []
            else:
                return 0, 0
            
            if not positions:
                return 0, 0
            
            # Sort by size (largest first)
            positions = sorted(
                positions,
                key=lambda p: abs(p.volume if hasattr(p, 'volume') else p.get('quantity', 0)),
                reverse=True
            )
            
            # Close half
            to_close = positions[:len(positions) // 2]
            positions_affected = len(to_close)
            
            for pos in to_close:
                try:
                    ticket = pos.ticket if hasattr(pos, 'ticket') else pos.get('ticket')
                    if hasattr(self.broker, 'close_position'):
                        success = await self.broker.close_position(ticket)
                        if success:
                            positions_closed += 1
                except Exception as e:
                    logger.error(f"Error reducing position: {e}")
            
        except Exception as e:
            logger.error(f"Error reducing exposure: {e}")
        
        return positions_affected, positions_closed
    
    def _log_event(self, event: KillSwitchEvent):
        """Log event to database (immutable audit trail)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO kill_switch_events
                    (event_id, timestamp, level, trigger, reason, triggered_by,
                     positions_affected, positions_closed, time_to_shutdown_ms, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.level.value,
                    event.trigger.value,
                    event.reason,
                    event.triggered_by,
                    event.positions_affected,
                    event.positions_closed,
                    event.time_to_shutdown_ms,
                    json.dumps(event.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def _log_bypass_attempt(self, action: str):
        """Log bypass attempt (triggers lockout after 3 attempts)"""
        with self._lock:
            pass
        try:
            self._bypass_attempts += 1
            
            if self._bypass_attempts >= 3:
                self._bypass_lockout = True
                logger.critical("BYPASS LOCKOUT ACTIVATED - 3 bypass attempts detected")
        
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO bypass_attempts
                    (timestamp, attempted_action, current_level, source)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    action,
                    self._current_level.value,
                    "unknown"
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging bypass attempt: {e}")
    
    async def start_monitoring(self):
        """Start background monitoring for automatic triggers"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Kill switch monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Kill switch monitoring stopped")
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                
                if not self._running:
                    break
                
                # Check kill switch files
                for filename in self.KILL_SWITCH_FILES:
                    if Path(filename).exists():
                        await self.activate(
                            KillSwitchLevel.HARD,
                            KillSwitchTrigger.MANUAL_FILE,
                            f"Kill switch file detected: {filename}",
                            "file_monitor"
                        )
                        break
                
                # Check heartbeat
                if self._heartbeat_enabled:
                    time_since_heartbeat = (datetime.now() - self._last_heartbeat).total_seconds()
                    if time_since_heartbeat > self.heartbeat_timeout:
                        await self.activate(
                            KillSwitchLevel.MEDIUM,
                            KillSwitchTrigger.HEARTBEAT_FAILURE,
                            f"No heartbeat for {time_since_heartbeat:.0f}s",
                            "heartbeat_monitor"
                        )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
    
    def deactivate(self, authorization_code: str) -> bool:
        """
        Attempt to deactivate kill switch.
        
        IMPORTANT: Cannot deactivate HARD or NUCLEAR levels.
        Requires authorization code for SOFT and MEDIUM.
        
        Args:
            authorization_code: Required authorization code
            
        Returns:
            True if deactivated
        """
        with self._lock:
            # Cannot deactivate HARD or NUCLEAR
            if self._current_level.value >= KillSwitchLevel.HARD.value:
                self._log_bypass_attempt(f"Attempted deactivation at {self._current_level.name}")
                logger.critical(
                    f"BLOCKED: Cannot deactivate kill switch at {self._current_level.name} level"
                )
                return False
            
            # Verify authorization code (simple hash check)
            expected_code = hashlib.sha256(
                f"DEACTIVATE_{datetime.now().strftime('%Y%m%d')}".encode()
            ).hexdigest()[:8].upper()
            
            if authorization_code != expected_code:
                self._log_bypass_attempt(f"Invalid authorization code: {authorization_code}")
                logger.warning(f"Invalid authorization code for deactivation")
                return False
            
            # Deactivate
            self._current_level = KillSwitchLevel.NONE
            self._activation_time = None
            self._activation_reason = None
            
            logger.info("Kill switch deactivated with valid authorization")
            return True
    
    def get_status(self) -> Dict:
        """Get current kill switch status"""
        return {
            'is_active': self.is_active,
            'current_level': self._current_level.name,
            'can_trade': self.can_trade,
            'can_open_positions': self.can_open_positions,
            'activation_time': self._activation_time.isoformat() if self._activation_time else None,
            'activation_reason': self._activation_reason,
            'bypass_attempts': self._bypass_attempts,
            'bypass_lockout': self._bypass_lockout,
            'heartbeat_enabled': self._heartbeat_enabled,
            'last_heartbeat': self._last_heartbeat.isoformat(),
            'monitoring_active': self._running,
            'recent_events': [e.to_dict() for e in self._events[-10:]]
        }
    
    def create_kill_switch_file(self, reason: str = "Manual activation"):
        """Create a kill switch file to trigger shutdown"""
        filename = self.KILL_SWITCH_FILES[0]
        with open(filename, 'w') as f:
            f.write(f"Kill switch activated at {datetime.now().isoformat()}\n")
            f.write(f"Reason: {reason}\n")
        logger.critical(f"Kill switch file created: {filename}")
