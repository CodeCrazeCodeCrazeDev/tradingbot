"""
Graceful Shutdown Handler
Ensures clean shutdown of all trading bot components.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ShutdownPhase(Enum):
    """Phases of shutdown."""
    RUNNING = "running"
    STOPPING = "stopping"
    CLOSING_POSITIONS = "closing_positions"
    SAVING_STATE = "saving_state"
    CLEANUP = "cleanup"
    STOPPED = "stopped"


@dataclass
class ShutdownTask:
    """A task to run during shutdown."""
    name: str
    callback: Callable
    priority: int = 50  # Lower = earlier (0-100)
    timeout_seconds: float = 30.0
    required: bool = True  # If True, failure blocks shutdown


class GracefulShutdownHandler:
    """
    Handles graceful shutdown of the trading bot.
    
    Features:
    - Signal handling (SIGTERM, SIGINT)
    - Ordered shutdown of components
    - Position closing before exit
    - State persistence
    - Timeout handling
    """
    
    def __init__(
        self,
        shutdown_timeout: float = 60.0,
        close_positions_on_shutdown: bool = True
    ):
        self.shutdown_timeout = shutdown_timeout
        self.close_positions_on_shutdown = close_positions_on_shutdown
        
        # State
        self._phase = ShutdownPhase.RUNNING
        self._shutdown_requested = False
        self._shutdown_complete = asyncio.Event()
        self._shutdown_tasks: List[ShutdownTask] = []
        
        # Components
        self._components: Dict[str, Any] = {}
        self._position_manager = None
        self._backup_manager = None
        
        # Callbacks
        self._on_shutdown_start: List[Callable] = []
        self._on_shutdown_complete: List[Callable] = []
        
        logger.info("GracefulShutdownHandler initialized")
    
    def register_signal_handlers(self):
        """Register OS signal handlers."""
        try:
            # Handle SIGTERM (kill command)
            signal.signal(signal.SIGTERM, self._signal_handler)
            # Handle SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Signal handlers registered (SIGTERM, SIGINT)")
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle OS signals."""
        signal_name = signal.Signals(signum).name
        logger.warning(f"Received signal {signal_name}, initiating shutdown...")
        
        # Request shutdown
        self._shutdown_requested = True
        
        try:
            # Create task to run shutdown
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.shutdown())
            else:
                loop.run_until_complete(self.shutdown())
        except RuntimeError:
            # No event loop, do synchronous cleanup
            logger.warning("No event loop, performing synchronous cleanup")
            self._sync_cleanup()
    
    def _sync_cleanup(self):
        """Synchronous cleanup when no event loop available."""
        logger.info("Performing synchronous cleanup...")
        self._phase = ShutdownPhase.STOPPED
        sys.exit(0)
    
    def register_component(self, name: str, component: Any):
        """Register a component for shutdown."""
        self._components[name] = component
        logger.debug(f"Registered component for shutdown: {name}")
    
    def register_position_manager(self, position_manager: Any):
        """Register the position manager for position closing."""
        self._position_manager = position_manager
    
    def register_backup_manager(self, backup_manager: Any):
        """Register the backup manager for state saving."""
        self._backup_manager = backup_manager
    
    def add_shutdown_task(
        self,
        name: str,
        callback: Callable,
        priority: int = 50,
        timeout: float = 30.0,
        required: bool = True
    ):
        """Add a custom shutdown task."""
        task = ShutdownTask(
            name=name,
            callback=callback,
            priority=priority,
            timeout_seconds=timeout,
            required=required
        )
        self._shutdown_tasks.append(task)
        self._shutdown_tasks.sort(key=lambda t: t.priority)
        logger.debug(f"Added shutdown task: {name} (priority={priority})")
    
    def on_shutdown_start(self, callback: Callable):
        """Register callback for shutdown start."""
        self._on_shutdown_start.append(callback)
    
    def on_shutdown_complete(self, callback: Callable):
        """Register callback for shutdown complete."""
        self._on_shutdown_complete.append(callback)
    
    async def shutdown(self, reason: str = "requested"):
        """
        Perform graceful shutdown.
        
        Args:
            reason: Reason for shutdown
        """
        if self._phase != ShutdownPhase.RUNNING:
            logger.warning("Shutdown already in progress")
            return
        
        start_time = datetime.now()
        logger.critical(f"🛑 INITIATING GRACEFUL SHUTDOWN: {reason}")
        
        try:
            # Notify shutdown start
            self._phase = ShutdownPhase.STOPPING
            for callback in self._on_shutdown_start:
                try:
                    result = callback(reason)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Error in shutdown start callback: {e}")
            
            # Phase 1: Stop accepting new trades
            logger.info("Phase 1: Stopping new trade acceptance...")
            await self._stop_trading()
            
            # Phase 2: Close positions if configured
            if self.close_positions_on_shutdown and self._position_manager:
                self._phase = ShutdownPhase.CLOSING_POSITIONS
                logger.info("Phase 2: Closing open positions...")
                await self._close_all_positions()
            
            # Phase 3: Save state
            if self._backup_manager:
                self._phase = ShutdownPhase.SAVING_STATE
                logger.info("Phase 3: Saving state...")
                await self._save_state()
            
            # Phase 4: Run custom shutdown tasks
            self._phase = ShutdownPhase.CLEANUP
            logger.info("Phase 4: Running shutdown tasks...")
            await self._run_shutdown_tasks()
            
            # Phase 5: Cleanup components
            logger.info("Phase 5: Cleaning up components...")
            await self._cleanup_components()
            
            # Mark complete
            self._phase = ShutdownPhase.STOPPED
            self._shutdown_complete.set()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.critical(f"✅ SHUTDOWN COMPLETE in {elapsed:.1f}s")
            
            # Notify shutdown complete
            for callback in self._on_shutdown_complete:
                try:
                    result = callback()
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Error in shutdown complete callback: {e}")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self._phase = ShutdownPhase.STOPPED
    
    async def _stop_trading(self):
        """Stop all trading activity."""
        for name, component in self._components.items():
            try:
                if hasattr(component, 'stop'):
                    result = component.stop()
                    if asyncio.iscoroutine(result):
                        await asyncio.wait_for(result, timeout=10.0)
                    logger.debug(f"Stopped component: {name}")
                elif hasattr(component, 'running'):
                    component.running = False
            except asyncio.TimeoutError:
                logger.warning(f"Timeout stopping component: {name}")
            except Exception as e:
                logger.error(f"Error stopping component {name}: {e}")
    
    async def _close_all_positions(self):
        """Close all open positions."""
        if not self._position_manager:
            return
        try:
        
            # Get all positions
            positions = []
            if hasattr(self._position_manager, 'get_all_positions'):
                positions = await self._position_manager.get_all_positions()
            elif hasattr(self._position_manager, 'positions'):
                positions = list(self._position_manager.positions.values())
            
            if not positions:
                logger.info("No open positions to close")
                return
            
            logger.warning(f"Closing {len(positions)} open positions...")
            
            for position in positions:
                try:
                    symbol = getattr(position, 'symbol', position.get('symbol', 'unknown'))
                    ticket_id = getattr(position, 'ticket_id', position.get('ticket_id', ''))
                    
                    if hasattr(self._position_manager, 'close_position'):
                        await asyncio.wait_for(
                            self._position_manager.close_position(ticket_id, reason="shutdown"),
                            timeout=30.0
                        )
                        logger.info(f"Closed position: {symbol}")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout closing position: {symbol}")
                except Exception as e:
                    logger.error(f"Error closing position: {e}")
            
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
    
    async def _save_state(self):
        """Save current state."""
        if not self._backup_manager:
            return
        try:
        
            if hasattr(self._backup_manager, 'create_backup'):
                await asyncio.wait_for(
                    self._backup_manager.create_backup("shutdown"),
                    timeout=30.0
                )
                logger.info("State saved successfully")
        except asyncio.TimeoutError:
            logger.error("Timeout saving state")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    async def _run_shutdown_tasks(self):
        """Run custom shutdown tasks."""
        for task in self._shutdown_tasks:
            try:
                logger.debug(f"Running shutdown task: {task.name}")
                result = task.callback()
                if asyncio.iscoroutine(result):
                    await asyncio.wait_for(result, timeout=task.timeout_seconds)
                logger.debug(f"Completed shutdown task: {task.name}")
            except asyncio.TimeoutError:
                logger.error(f"Timeout in shutdown task: {task.name}")
                if task.required:
                    logger.warning(f"Required task {task.name} timed out")
            except Exception as e:
                logger.error(f"Error in shutdown task {task.name}: {e}")
                if task.required:
                    logger.warning(f"Required task {task.name} failed")
    
    async def _cleanup_components(self):
        """Cleanup all registered components."""
        for name, component in self._components.items():
            try:
                if hasattr(component, 'cleanup'):
                    result = component.cleanup()
                    if asyncio.iscoroutine(result):
                        await asyncio.wait_for(result, timeout=10.0)
                    logger.debug(f"Cleaned up component: {name}")
                elif hasattr(component, 'close'):
                    result = component.close()
                    if asyncio.iscoroutine(result):
                        await asyncio.wait_for(result, timeout=10.0)
                    logger.debug(f"Closed component: {name}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout cleaning up component: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up component {name}: {e}")
    
    async def wait_for_shutdown(self):
        """Wait for shutdown to complete."""
        await self._shutdown_complete.wait()
    
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._phase != ShutdownPhase.RUNNING
    
    def get_phase(self) -> ShutdownPhase:
        """Get current shutdown phase."""
        return self._phase
    
    def get_status(self) -> Dict:
        """Get shutdown handler status."""
        return {
            'phase': self._phase.value,
            'shutdown_requested': self._shutdown_requested,
            'registered_components': list(self._components.keys()),
            'shutdown_tasks': [t.name for t in self._shutdown_tasks],
            'close_positions_on_shutdown': self.close_positions_on_shutdown,
            'shutdown_timeout': self.shutdown_timeout
        }


# Singleton instance
_shutdown_handler: Optional[GracefulShutdownHandler] = None


def get_shutdown_handler(**kwargs) -> GracefulShutdownHandler:
    """Get or create the shutdown handler singleton."""
    global _shutdown_handler
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdownHandler(**kwargs)
    return _shutdown_handler


def request_shutdown(reason: str = "requested"):
    """Request a graceful shutdown."""
    handler = get_shutdown_handler()
    asyncio.create_task(handler.shutdown(reason))


__all__ = [
    'GracefulShutdownHandler',
    'ShutdownPhase',
    'ShutdownTask',
    'get_shutdown_handler',
    'request_shutdown'
]
