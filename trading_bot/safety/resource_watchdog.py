"""
Resource Watchdog

Monitors system resources (CPU, memory) and takes action to prevent crashes.
"""

import time
import logging
from dataclasses import dataclass
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

from .latency_circuit_breaker import TradingMode
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class ResourceStatus:
    """Current resource status."""
    cpu_percent: float
    memory_percent: float
    mode: TradingMode
    should_reduce_positions: bool
    should_stop_scanning: bool
    message: str = ""
    
    @property
    def is_healthy(self) -> bool:
        """Check if resources are healthy."""
        return self.mode == TradingMode.NORMAL and not self.should_reduce_positions


class ResourceWatchdog:
    """
    Monitors system resources and adjusts trading behavior.
    
    Actions:
    - High CPU (>80% for 60s): Stop scanners, increase buffers
    - High memory (>85%): Close 50% of positions
    - Critical resources: Pause trading
    """
    
    def __init__(
        self,
        cpu_threshold_pct: float = 80.0,
        memory_threshold_pct: float = 85.0,
        cpu_duration_seconds: int = 60
    ):
        """
        Initialize resource watchdog.
        
        Args:
            cpu_threshold_pct: CPU percentage threshold
            memory_threshold_pct: Memory percentage threshold
            cpu_duration_seconds: How long CPU must be high before action
        """
        if psutil is None:
            logger.warning("psutil not installed, resource monitoring disabled")
        
        self.cpu_threshold = cpu_threshold_pct
        self.memory_threshold = memory_threshold_pct
        self.cpu_duration = cpu_duration_seconds
        self.high_cpu_start: Optional[float] = None
        
        logger.info(f"Resource Watchdog initialized:")
        logger.info(f"  CPU threshold: {cpu_threshold_pct}%")
        logger.info(f"  Memory threshold: {memory_threshold_pct}%")
        logger.info(f"  CPU duration: {cpu_duration_seconds}s")
    
    def check_resources(self) -> ResourceStatus:
        """
        Check system resources and determine actions.
        
        Returns:
            ResourceStatus with current state and recommended actions
        """
        if psutil is None:
            return ResourceStatus(
                cpu_percent=0.0,
                memory_percent=0.0,
                mode=TradingMode.NORMAL,
                should_reduce_positions=False,
                should_stop_scanning=False,
                message="psutil not available"
            )
        
        # Get current resource usage
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        
        # Track high CPU duration
        if cpu > self.cpu_threshold:
            if self.high_cpu_start is None:
                self.high_cpu_start = time.time()
                logger.warning(f"High CPU detected: {cpu:.1f}%")
            cpu_duration = time.time() - self.high_cpu_start
        else:
            self.high_cpu_start = None
            cpu_duration = 0
        
        # Determine actions
        should_reduce = memory > self.memory_threshold
        should_stop_scanning = cpu_duration > self.cpu_duration
        
        # Determine mode
        if should_reduce and should_stop_scanning:
            mode = TradingMode.PAUSED
            message = f"Critical resources: CPU {cpu:.1f}%, Memory {memory:.1f}%"
        elif should_reduce or should_stop_scanning:
            mode = TradingMode.CONSERVATIVE
            if should_reduce:
                message = f"High memory: {memory:.1f}%"
            else:
                message = f"High CPU for {cpu_duration:.0f}s: {cpu:.1f}%"
        else:
            mode = TradingMode.NORMAL
            message = "Resources OK"
        
        # Log warnings
        if should_reduce:
            logger.warning(f"Memory usage high: {memory:.1f}% (threshold: {self.memory_threshold}%)")
        
        if should_stop_scanning:
            logger.warning(
                f"CPU usage high for {cpu_duration:.0f}s: {cpu:.1f}% "
                f"(threshold: {self.cpu_threshold}%)"
            )
        
        return ResourceStatus(
            cpu_percent=cpu,
            memory_percent=memory,
            mode=mode,
            should_reduce_positions=should_reduce,
            should_stop_scanning=should_stop_scanning,
            message=message
        )
    
    def get_recommended_actions(self, status: ResourceStatus) -> list:
        """
        Get list of recommended actions based on resource status.
        
        Args:
            status: Current resource status
        
        Returns:
            List of action strings
        """
        actions = []
        
        if status.should_stop_scanning:
            actions.append("Stop opportunity scanners")
            actions.append("Increase validator buffers")
            actions.append("Reduce processing frequency")
        
        if status.should_reduce_positions:
            actions.append("Close 50% of open positions")
            actions.append("Pause new entries")
            actions.append("Clear caches")
        
        if status.mode == TradingMode.PAUSED:
            actions.append("Pause all trading")
            actions.append("Alert administrator")
        
        return actions
