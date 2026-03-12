"""
Structured Logger - JSON-formatted structured logging
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    timestamp: str
    level: str
    message: str
    logger_name: str
    extra: Dict[str, Any] = None
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


class StructuredLogger:
    """JSON-formatted structured logging"""
    
    def __init__(self, name: str = "trading_bot"):
        self.name = name
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        logger.info("StructuredLogger initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        return True
    
    async def stop(self) -> bool:
        self._running = False
        return True
    
    def _create_entry(self, level: str, message: str, **kwargs) -> LogEntry:
        return LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            message=message,
            logger_name=self.name,
            extra=kwargs if kwargs else None
        )
    
    def info(self, message: str, **kwargs):
        entry = self._create_entry("INFO", message, **kwargs)
        logger.info(entry.to_json())
    
    def warning(self, message: str, **kwargs):
        entry = self._create_entry("WARNING", message, **kwargs)
        logger.warning(entry.to_json())
    
    def error(self, message: str, **kwargs):
        entry = self._create_entry("ERROR", message, **kwargs)
        logger.error(entry.to_json())
    
    def debug(self, message: str, **kwargs):
        entry = self._create_entry("DEBUG", message, **kwargs)
        logger.debug(entry.to_json())


_logger: Optional[StructuredLogger] = None

def get_logger(name: str = "trading_bot") -> StructuredLogger:
    global _logger
    if _logger is None:
        _logger = StructuredLogger(name)
    return _logger

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_logger().initialize(config)

async def start() -> bool:
    return await get_logger().start()

async def stop() -> bool:
    return await get_logger().stop()
