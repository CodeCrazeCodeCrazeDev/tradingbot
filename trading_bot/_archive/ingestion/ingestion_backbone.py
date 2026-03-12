"""
Ingestion Backbone - Core data ingestion pipeline
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class DataSource(Enum):
    YAHOO = "yahoo"
    COINGECKO = "coingecko"
    FRED = "fred"
    BINANCE = "binance"
    ALPACA = "alpaca"


@dataclass
class IngestionTask:
    source: DataSource
    symbol: str
    interval: str
    last_run: Optional[datetime] = None
    status: str = "pending"


class IngestionBackbone:
    """Core data ingestion pipeline"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.tasks: Dict[str, IngestionTask] = {}
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            self.config.update(config)
        logger.info("IngestionBackbone initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        logger.info("IngestionBackbone started")
        return True
    
    async def stop(self) -> bool:
        self._running = False
        logger.info("IngestionBackbone stopped")
        return True
    
    def add_task(self, task_id: str, source: DataSource, symbol: str, interval: str):
        self.tasks[task_id] = IngestionTask(source=source, symbol=symbol, interval=interval)
    
    def remove_task(self, task_id: str):
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    async def run_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        task.status = "running"
        task.last_run = datetime.utcnow()
        task.status = "completed"
        return True


_backbone: Optional[IngestionBackbone] = None

def get_backbone() -> IngestionBackbone:
    global _backbone
    if _backbone is None:
        _backbone = IngestionBackbone()
    return _backbone

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_backbone().initialize(config)

async def start() -> bool:
    return await get_backbone().start()

async def stop() -> bool:
    return await get_backbone().stop()
