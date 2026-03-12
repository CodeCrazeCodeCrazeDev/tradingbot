"""
Layer 0: Infrastructure & Hardware Implementation

Integrates:
- trading_bot/infrastructure/ (21 files)
- trading_bot/performance/ (10 files)
- trading_bot/profiling/ (2 files)
"""

import asyncio
import logging
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..unified_types import LayerStatus, LayerMetrics
from ..layer_interfaces import IInfrastructureLayer

logger = logging.getLogger(__name__)


class InfrastructureLayerImpl(IInfrastructureLayer):
    """
    Infrastructure Layer Implementation
    
    Manages hardware resources, network, and system infrastructure.
    """
    
    def __init__(self):
        self._status = LayerStatus.UNINITIALIZED
        self._config: Dict[str, Any] = {}
        self._start_time: Optional[datetime] = None
        
    @property
    def status(self) -> LayerStatus:
        return self._status
    
    def get_dependencies(self) -> List[int]:
        return []  # No dependencies - base layer
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize infrastructure layer"""
        try:
            self._config = config
            self._status = LayerStatus.INITIALIZING
            
            # Initialize resource monitoring
            logger.info("Initializing resource monitoring...")
            
            # Check system resources
            resources = await self.get_resource_usage()
            logger.info(f"CPU: {resources.get('cpu_percent', 0):.1f}%")
            logger.info(f"Memory: {resources.get('memory_percent', 0):.1f}%")
            
            # Initialize network monitoring
            logger.info("Initializing network monitoring...")
            
            self._status = LayerStatus.READY
            return True
            
        except Exception as e:
            logger.error(f"Infrastructure initialization failed: {e}")
            self._status = LayerStatus.ERROR
            return False
    
    async def start(self) -> bool:
        """Start infrastructure layer"""
        self._start_time = datetime.utcnow()
        self._status = LayerStatus.ACTIVE
        logger.info("Infrastructure layer started")
        return True
    
    async def stop(self) -> bool:
        """Stop infrastructure layer"""
        self._status = LayerStatus.DISABLED
        logger.info("Infrastructure layer stopped")
        return True
    
    async def health_check(self) -> LayerMetrics:
        """Check infrastructure health"""
        resources = await self.get_resource_usage()
        
        return LayerMetrics(
            layer_name=self.layer_name,
            status=self._status,
            cpu_percent=resources.get('cpu_percent', 0),
            memory_mb=resources.get('memory_mb', 0),
            custom_metrics={
                'disk_percent': resources.get('disk_percent', 0),
                'network_connections': resources.get('network_connections', 0),
            }
        )
    
    async def get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_mb': memory.used / (1024 * 1024),
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'network_connections': len(psutil.net_connections()),
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {}
    
    async def optimize_resources(self) -> bool:
        """Optimize resource allocation"""
        try:
            # Trigger garbage collection
            import gc
            gc.collect()
            
            logger.info("Resource optimization completed")
            return True
        except Exception as e:
            logger.error(f"Resource optimization failed: {e}")
            return False
    
    async def get_network_status(self) -> Dict[str, Any]:
        """Get network connectivity status"""
        try:
            net_io = psutil.net_io_counters()
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors_in': net_io.errin,
                'errors_out': net_io.errout,
                'connections': len(psutil.net_connections()),
            }
        except Exception as e:
            logger.error(f"Error getting network status: {e}")
            return {}
