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
        try:
            self.config = config or {}
            self.tasks: Dict[str, IngestionTask] = {}
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            if config:
                self.config.update(config)
            logger.info("IngestionBackbone initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            logger.info("IngestionBackbone started")
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            logger.info("IngestionBackbone stopped")
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    def add_task(self, task_id: str, source: DataSource, symbol: str, interval: str):
        try:
            self.tasks[task_id] = IngestionTask(source=source, symbol=symbol, interval=interval)
        except Exception as e:
            logger.error(f"Error in add_task: {e}")
            raise
    
    def remove_task(self, task_id: str):
        try:
            if task_id in self.tasks:
                del self.tasks[task_id]
        except Exception as e:
            logger.error(f"Error in remove_task: {e}")
            raise
    
    async def run_task(self, task_id: str) -> bool:
        try:
            if task_id not in self.tasks:
                return False
            task = self.tasks[task_id]
            task.status = "running"
            task.last_run = datetime.utcnow()
            task.status = "completed"
            return True
        except Exception as e:
            logger.error(f"Error in run_task: {e}")
            raise


_backbone: Optional[IngestionBackbone] = None

def get_backbone() -> IngestionBackbone:
    try:
        global _backbone
        if _backbone is None:
            _backbone = IngestionBackbone()
        return _backbone
    except Exception as e:
        logger.error(f"Error in get_backbone: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_backbone().initialize(config)

async def start() -> bool:
    return await get_backbone().start()

async def stop() -> bool:
    return await get_backbone().stop()
