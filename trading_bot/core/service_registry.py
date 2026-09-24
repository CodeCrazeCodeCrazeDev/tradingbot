"""
Core Service Registry

Provides backward compatibility for consolidated service layers.

CANONICAL REGISTRY: ``trading_bot.core.unified_registry.UnifiedComponentRegistry``
is the single authoritative registry. ``ServiceRegistry`` below is an alias
for it — instantiating it returns the shared singleton, so every lookup
lands in one registry (per ARCHITECTURE_GAP_MATRIX / CANONICAL_COMPONENTS).
"""

import logging
from datetime import datetime
from typing import Any

from .unified_registry import (
    ServiceState,
    ServiceInfo,
    UnifiedComponentRegistry,
    get_registry,
    get_service_registry,
    create_service_registry,
)

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


# Single-registry enforcement: ServiceRegistry() returns the canonical
# UnifiedComponentRegistry singleton rather than a parallel dict.
ServiceRegistry = UnifiedComponentRegistry

__all__ = [
    'BaseService',
    'ServiceHealth',
    'ServicePriority',
    'ServiceState',
    'ServiceInfo',
    'ServiceRegistry',
    'UnifiedComponentRegistry',
    'get_registry',
    'get_service_registry',
    'create_service_registry',
]
