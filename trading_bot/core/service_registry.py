"""
Core Service Registry

Provides service registration, health tracking, and backward compatibility.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ServicePriority:
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class ServiceHealth:
    def __init__(self, healthy=True, last_check=None, message="", metrics=None):
        self.healthy = healthy
        self.last_check = last_check or datetime.utcnow()
        self.message = message
        self.metrics = metrics or {}

class BaseService:
    def __init__(self, config=None):
        self.config = config or {}
        self._event_bus = None
        self._running = False

try:
    from trading_bot._archive.legacy_core.service_registry import (
        ServiceState,
        ServiceInfo,
        ServiceRegistry,
        get_service_registry,
        create_service_registry
    )
except ImportError:
    class ServiceState:
        STOPPED = "stopped"
        RUNNING = "running"
        FAILED = "failed"

    class ServiceInfo:
        def __init__(self, name, service_type=None):
            self.name = name
            self.service_type = service_type

    class ServiceRegistry:
        def __init__(self):
            self._services = {}

        def register(self, name, service):
            self._services[name] = service

        def get(self, name):
            return self._services.get(name)

    _global_registry = ServiceRegistry()

    def get_service_registry():
        return _global_registry

    def create_service_registry():
        return ServiceRegistry()

__all__ = [
    'BaseService',
    'ServiceHealth',
    'ServicePriority',
    'ServiceState',
    'ServiceInfo',
    'ServiceRegistry',
    'get_service_registry',
    'create_service_registry',
]
