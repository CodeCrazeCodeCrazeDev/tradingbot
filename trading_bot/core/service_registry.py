"""
Service Registry Shim - UCA 2026 Core Component
===============================================

Provides backward compatibility for consolidated service layers.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseService:
    def __init__(self, config=None):
        self.config = config or {}
        self._event_bus = None
        self._running = False

class ServiceHealth:
    def __init__(self, healthy, last_check=None, message="", metrics=None):
        self.healthy = healthy
        self.last_check = last_check or datetime.utcnow()
        self.message = message
        self.metrics = metrics or {}

class ServicePriority:
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
