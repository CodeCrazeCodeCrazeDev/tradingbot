"""
Auto Scaling Module - Dynamic resource scaling for the trading system
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ScalingDirection(Enum):
    UP = "up"
    DOWN = "down"
    NONE = "none"


@dataclass
class ScalingMetrics:
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    request_rate: float = 0.0
    latency_ms: float = 0.0
    queue_depth: int = 0
    active_connections: int = 0


@dataclass
class ScalingPolicy:
    min_instances: int = 1
    max_instances: int = 10
    target_cpu: float = 70.0
    target_memory: float = 80.0
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 30.0
    cooldown_seconds: int = 300


class AutoScaler:
    """Automatic scaling manager for trading system resources"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.policy = ScalingPolicy()
        self.current_instances = 1
        self.metrics = ScalingMetrics()
        self.last_scale_time: Optional[datetime] = None
        self._running = False
        
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the auto scaler"""
        if config:
            self.config.update(config)
        logger.info("AutoScaler initialized")
        return True
    
    async def start(self) -> bool:
        """Start the auto scaler"""
        self._running = True
        logger.info("AutoScaler started")
        return True
    
    async def stop(self) -> bool:
        """Stop the auto scaler"""
        self._running = False
        logger.info("AutoScaler stopped")
        return True
    
    def update_metrics(self, metrics: ScalingMetrics):
        """Update current metrics"""
        self.metrics = metrics
    
    def evaluate_scaling(self) -> ScalingDirection:
        """Evaluate if scaling is needed"""
        if self.metrics.cpu_usage > self.policy.scale_up_threshold:
            return ScalingDirection.UP
        elif self.metrics.cpu_usage < self.policy.scale_down_threshold:
            return ScalingDirection.DOWN
        return ScalingDirection.NONE
    
    async def scale(self, direction: ScalingDirection) -> bool:
        """Execute scaling action"""
        if direction == ScalingDirection.UP:
            if self.current_instances < self.policy.max_instances:
                self.current_instances += 1
                self.last_scale_time = datetime.utcnow()
                logger.info(f"Scaled up to {self.current_instances} instances")
                return True
        elif direction == ScalingDirection.DOWN:
            if self.current_instances > self.policy.min_instances:
                self.current_instances -= 1
                self.last_scale_time = datetime.utcnow()
                logger.info(f"Scaled down to {self.current_instances} instances")
                return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scaling status"""
        return {
            'current_instances': self.current_instances,
            'metrics': {
                'cpu_usage': self.metrics.cpu_usage,
                'memory_usage': self.metrics.memory_usage,
            },
            'last_scale_time': self.last_scale_time.isoformat() if self.last_scale_time else None,
            'running': self._running,
        }


# Module-level instance
_auto_scaler: Optional[AutoScaler] = None


def get_auto_scaler() -> AutoScaler:
    """Get or create the auto scaler instance"""
    global _auto_scaler
    if _auto_scaler is None:
        _auto_scaler = AutoScaler()
    return _auto_scaler


async def initialize(config: Dict[str, Any] = None) -> bool:
    """Initialize the module"""
    return await get_auto_scaler().initialize(config)


async def start() -> bool:
    """Start the module"""
    return await get_auto_scaler().start()


async def stop() -> bool:
    """Stop the module"""
    return await get_auto_scaler().stop()
