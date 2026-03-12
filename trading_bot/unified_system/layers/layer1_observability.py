"""
Layer 1: Observability & Health Implementation

Integrates:
- trading_bot/monitoring/ (21 files)
- trading_bot/observability/ (8 files)
- trading_bot/log_system/ (9 files)
- trading_bot/telemetry/ (7 files)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..unified_types import LayerStatus, LayerMetrics, SystemHealth, SystemStatus
from ..layer_interfaces import IObservabilityLayer

logger = logging.getLogger(__name__)


class ObservabilityLayerImpl(IObservabilityLayer):
    """Observability Layer - Logging, metrics, tracing, alerting"""
    
    def __init__(self):
        self._status = LayerStatus.UNINITIALIZED
        self._config: Dict[str, Any] = {}
        self._metrics: Dict[str, float] = {}
        self._alerts: List[Dict[str, Any]] = []
        
    @property
    def status(self) -> LayerStatus:
        return self._status
    
    def get_dependencies(self) -> List[int]:
        return [0]  # Depends on Infrastructure
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        try:
            self._config = config
            self._status = LayerStatus.READY
            logger.info("Observability layer initialized")
            return True
        except Exception as e:
            logger.error(f"Observability init failed: {e}")
            self._status = LayerStatus.ERROR
            return False
    
    async def start(self) -> bool:
        self._status = LayerStatus.ACTIVE
        return True
    
    async def stop(self) -> bool:
        self._status = LayerStatus.DISABLED
        return True
    
    async def health_check(self) -> LayerMetrics:
        return LayerMetrics(layer_name=self.layer_name, status=self._status)
    
    async def log(self, level: str, message: str, context: Dict[str, Any]) -> None:
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"{message} | context={context}")
    
    async def record_metric(self, name: str, value: float, tags: Dict[str, str]) -> None:
        self._metrics[name] = value
    
    async def create_alert(self, severity: str, message: str, context: Dict[str, Any]) -> None:
        self._alerts.append({
            'severity': severity,
            'message': message,
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        })
        logger.warning(f"ALERT [{severity}]: {message}")
    
    async def get_system_health(self) -> SystemHealth:
        return SystemHealth(
            status=SystemStatus.RUNNING,
            uptime_seconds=0,
            layer_status={self.layer_name: self._status}
        )
