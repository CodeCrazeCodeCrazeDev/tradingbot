"""
Log Manager - Centralized logging management for the trading system
"""

import logging
import logging.handlers
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LogConfig:
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10_000_000
    backup_count: int = 5
    console_output: bool = True


class LogManager:
    """Centralized log management"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = LogConfig()
        self._configured = False
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            if 'level' in config:
                self.config.level = config['level']
            if 'file_path' in config:
                self.config.file_path = config['file_path']
        
        self._configure_logging()
        logger.info("LogManager initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        logger.info("LogManager started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        logger.info("LogManager stopped")
        return True
    
    def _configure_logging(self):
        if self._configured:
            return
        
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level))
        
        formatter = logging.Formatter(self.config.format)
        
        if self.config.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        if self.config.file_path:
            Path(self.config.file_path).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                self.config.file_path,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        self._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)


_manager: Optional[LogManager] = None

def get_manager() -> LogManager:
    global _manager
    if _manager is None:
        _manager = LogManager()
    return _manager

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_manager().initialize(config)

async def start() -> bool:
    return await get_manager().start()

async def stop() -> bool:
    return await get_manager().stop()
