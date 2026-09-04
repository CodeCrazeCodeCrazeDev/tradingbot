"""
Service Registry Infrastructure

Provides service registration, health monitoring, and dependency management.
"""

import logging
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Type

logger = logging.getLogger(__name__)

class ServiceState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"

class ServicePriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class ServiceHealth:
    def __init__(self, healthy: bool, last_check: Optional[datetime] = None, message: str = "", metrics: Optional[Dict[str, Any]] = None):
        self.healthy = healthy
        self.last_check = last_check or datetime.utcnow()
        self.message = message
        self.metrics = metrics or {}

class ServiceInfo:
    def __init__(self, name: str, instance: Any, priority: ServicePriority = ServicePriority.NORMAL, dependencies: Optional[List[str]] = None):
        self.name = name
        self.instance = instance
        self.priority = priority
        self.dependencies = dependencies or []
        self.state = ServiceState.UNINITIALIZED
        self.health = ServiceHealth(healthy=True)

class BaseService:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._event_bus = None
        self._running = False

    async def initialize(self):
        pass

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False

    def check_health(self) -> ServiceHealth:
        return ServiceHealth(healthy=self._running)

class ServiceRegistry:
    _instance = None

    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}

    @classmethod
    def get_instance(cls) -> "ServiceRegistry":
        if cls._instance is None:
            cls._instance = ServiceRegistry()
        return cls._instance

    def register(self, name: str, service_instance: Any, priority: ServicePriority = ServicePriority.NORMAL, dependencies: Optional[List[str]] = None):
        info = ServiceInfo(name, service_instance, priority, dependencies)
        self._services[name] = info
        logger.info(f"Registered service: {name}")

    def get_service(self, name: str) -> Optional[Any]:
        info = self._services.get(name)
        return info.instance if info else None

    def unregister(self, name: str):
        if name in self._services:
            del self._services[name]

_global_registry = None

def get_service_registry() -> ServiceRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ServiceRegistry.get_instance()
    return _global_registry

def create_service_registry() -> ServiceRegistry:
    return ServiceRegistry()

__all__ = [
    'ServiceState',
    'ServicePriority',
    'ServiceHealth',
    'ServiceInfo',
    'BaseService',
    'ServiceRegistry',
    'get_service_registry',
    'create_service_registry'
]
