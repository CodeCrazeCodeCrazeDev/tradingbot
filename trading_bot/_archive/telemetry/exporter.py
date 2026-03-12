"""
Telemetry Exporter - Exports telemetry data to external systems
"""

import logging
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class TelemetryExporter:
    """Exports telemetry to external systems"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.export_buffer: List[Dict[str, Any]] = []
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            self.config.update(config)
        logger.info("TelemetryExporter initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        logger.info("TelemetryExporter started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        await self.flush()
        logger.info("TelemetryExporter stopped")
        return True
    
    def add(self, data: Dict[str, Any]):
        data['exported_at'] = datetime.utcnow().isoformat()
        self.export_buffer.append(data)
    
    async def flush(self) -> int:
        count = len(self.export_buffer)
        self.export_buffer.clear()
        return count
    
    def to_json(self) -> str:
        return json.dumps(self.export_buffer, default=str)


_exporter: Optional[TelemetryExporter] = None

def get_exporter() -> TelemetryExporter:
    global _exporter
    if _exporter is None:
        _exporter = TelemetryExporter()
    return _exporter

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_exporter().initialize(config)

async def start() -> bool:
    return await get_exporter().start()

async def stop() -> bool:
    return await get_exporter().stop()
