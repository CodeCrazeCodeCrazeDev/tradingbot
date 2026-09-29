"""
Service Locator - shared service discovery for orchestration managers.

Provides the singleton ``ServiceLocator`` that
``trading_bot.orchestration.service_managers`` uses to publish and resolve
services across manager categories.

Supports three registration styles:

* ``register(name, service)``            - eager instance
* ``register(name, factory=fn)``         - lazy, called on first ``get``
* ``register(name, factory=fn, dependencies=[...])``
    - lazy; on first ``get`` each dependency is resolved via the locator and
      passed to the factory as keyword arguments.
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceLocator:
    """Simple thread-safe service registry (name -> service instance/factory)."""

    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[..., Any]] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._lock = threading.RLock()

    def register(
        self,
        name: str,
        service: Any = None,
        factory: Optional[Callable[..., Any]] = None,
        singleton: bool = True,
        dependencies: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Register a service instance or a lazy factory under ``name``."""
        with self._lock:
            if factory is not None:
                self._factories[name] = factory
                if dependencies:
                    self._dependencies[name] = list(dependencies)
            else:
                self._services[name] = service
                if singleton:
                    self._singletons[name] = service
        logger.debug(f"ServiceLocator: registered '{name}' (factory={factory is not None}, singleton={singleton})")

    def get(self, name: str, default: Any = None) -> Any:
        """
        Resolve a service by name. Factory-registered services are
        instantiated on first access (with their dependencies injected as
        keyword arguments) and then cached.
        """
        with self._lock:
            if name in self._services:
                return self._services[name]
            if name in self._factories:
                deps = {
                    dep_name: self.get(dep_name)
                    for dep_name in self._dependencies.get(name, [])
                }
                instance = self._factories[name](**deps) if deps else self._factories[name]()
                self._services[name] = instance
                self._singletons[name] = instance
                return instance
            return default

    def get_singleton(self, name: str, default: Any = None) -> Any:
        with self._lock:
            if name in self._singletons:
                return self._singletons[name]
            return self.get(name, default)

    def unregister(self, name: str) -> bool:
        with self._lock:
            existed = name in self._services or name in self._factories
            self._services.pop(name, None)
            self._singletons.pop(name, None)
            self._factories.pop(name, None)
            self._dependencies.pop(name, None)
            return existed

    def list_services(self) -> List[str]:
        with self._lock:
            return list(set(self._services) | set(self._factories))

    def clear(self) -> None:
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._factories.clear()
            self._dependencies.clear()


_service_locator: Optional[ServiceLocator] = None
_service_locator_lock = threading.Lock()


def get_service_locator() -> ServiceLocator:
    """Return the process-wide ServiceLocator singleton."""
    global _service_locator
    if _service_locator is None:
        with _service_locator_lock:
            if _service_locator is None:
                _service_locator = ServiceLocator()
    return _service_locator
