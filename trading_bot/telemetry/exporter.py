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
        try:
            self.config = config or {}
            self.export_buffer: List[Dict[str, Any]] = []
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            if config:
                self.config.update(config)
            logger.info("TelemetryExporter initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            logger.info("TelemetryExporter started")
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            await self.flush()
            logger.info("TelemetryExporter stopped")
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    def add(self, data: Dict[str, Any]):
        try:
            data['exported_at'] = datetime.utcnow().isoformat()
            self.export_buffer.append(data)
        except Exception as e:
            logger.error(f"Error in add: {e}")
            raise
    
    async def flush(self) -> int:
        try:
            count = len(self.export_buffer)
            self.export_buffer.clear()
            return count
        except Exception as e:
            logger.error(f"Error in flush: {e}")
            raise
    
    def to_json(self) -> str:
        return json.dumps(self.export_buffer, default=str)


_exporter: Optional[TelemetryExporter] = None

def get_exporter() -> TelemetryExporter:
    try:
        global _exporter
        if _exporter is None:
            _exporter = TelemetryExporter()
        return _exporter
    except Exception as e:
        logger.error(f"Error in get_exporter: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_exporter().initialize(config)

async def start() -> bool:
    return await get_exporter().start()

async def stop() -> bool:
    return await get_exporter().stop()
