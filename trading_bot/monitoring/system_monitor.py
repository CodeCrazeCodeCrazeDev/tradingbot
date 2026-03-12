"""
System Monitor - Monitors system resources and performance
"""

import asyncio
import logging
import psutil
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    process_count: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class SystemMonitor:
    """Monitors system resources"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metrics_history: list = []
        self.max_history = 1000
        self._running = False
        
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            self.config.update(config)
        logger.info("SystemMonitor initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        logger.info("SystemMonitor started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        logger.info("SystemMonitor stopped")
        return True
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            net_io = psutil.net_io_counters()
            metrics = SystemMetrics(
                cpu_percent=psutil.cpu_percent(),
                memory_percent=psutil.virtual_memory().percent,
                disk_percent=psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
                network_bytes_sent=net_io.bytes_sent,
                network_bytes_recv=net_io.bytes_recv,
                process_count=len(psutil.pids()),
            )
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history = self.metrics_history[-self.max_history:]
            return metrics
        except Exception as e:
            logger.warning(f"Error collecting metrics: {e}")
            return SystemMetrics()
    
    def get_status(self) -> Dict[str, Any]:
        metrics = self.collect_metrics()
        return {
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'disk_percent': metrics.disk_percent,
            'running': self._running,
        }


_monitor: Optional[SystemMonitor] = None

def get_monitor() -> SystemMonitor:
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_monitor().initialize(config)

async def start() -> bool:
    return await get_monitor().start()

async def stop() -> bool:
    return await get_monitor().stop()
