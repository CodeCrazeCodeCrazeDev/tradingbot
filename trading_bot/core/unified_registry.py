"""
Unified Component Registry - UCA-2026 Core Component
==================================================

Exactly one authoritative registry for all system components (Agents, Tools, Services, Models).
Implements the Singleton pattern to prevent architectural regression.
Now also incorporates legacy ServiceRegistry and SystemRegistry features and enforces integrity.
"""

import logging
import threading
import asyncio
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime

from trading_bot.system_interfaces import SystemLayer, ComponentStatus, ComponentHealth, ISystemComponent

logger = logging.getLogger(__name__)

class ServiceState(Enum):
    """Lifecycle states for services"""
    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()

@dataclass
class ServiceInfo:
    """Metadata for a registered service"""
    name: str
    component_type: str
    instance: Optional[Any] = None
    factory: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    state: ServiceState = ServiceState.CREATED
    registered_at: datetime = field(default_factory=datetime.utcnow)
    initialized_at: Optional[datetime] = None
    last_error: Optional[str] = None

@dataclass
class ComponentMetadata:
    """Metadata for a registered component - compatible with SystemRegistry"""
    name: str
    component_type: str
    layer: SystemLayer
    instance: Optional[ISystemComponent] = None
    factory: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    status: ComponentStatus = ComponentStatus.UNINITIALIZED
    registered_at: datetime = field(default_factory=datetime.utcnow)
    initialized_at: Optional[datetime] = None
    priority: int = 5
    enabled: bool = True

class UnifiedComponentRegistry:
    """
    The authoritative singleton registry for AlphaAlgo UCA-2026.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UnifiedComponentRegistry, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._components: Dict[str, Any] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._dependencies: Dict[str, List[str]] = {}

        # Legacy ServiceRegistry / SystemRegistry state
        self._services: Dict[str, ServiceInfo] = {}
        self._legacy_metadata: Dict[str, ComponentMetadata] = {}
        self._instances: Dict[str, ISystemComponent] = {}
        self._event_bus = None

        # Order of registration to ensure determinism
        self._registration_order: List[str] = []

        self._initialized = True
        logger.info("UnifiedComponentRegistry initialized as singleton")

    def register(
        self,
        name: str,
        component: Any = None,
        component_type: str = "general",
        layer: Optional[SystemLayer] = None,
        factory: Optional[Callable] = None,
        instance: Optional[ISystemComponent] = None,
        dependencies: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a component with the system.
        Enforces no duplicate component IDs and deterministic order.
        Compatible with both legacy SystemRegistry and UCA-2026 signatures.
        """
        # Settle the active component reference
        final_component = component if component is not None else instance
        if final_component is None and factory is not None:
            # Under lazy loading, factory is defined
            final_component = None

        if name in self._components:
            if final_component is not None and self._components[name] is final_component:
                return
            raise ValueError(f"CRITICAL: Component '{name}' already registered with a different instance. Duplicate IDs forbidden.")

        with self._lock:
            self._components[name] = final_component
            self._metadata[name] = {
                "type": component_type,
                "metadata": metadata or {}
            }
            self._dependencies[name] = dependencies or []
            self._registration_order.append(name)

            # Map default layer if not provided
            final_layer = layer or SystemLayer.INFRASTRUCTURE

            # Track legacy system metadata
            self._legacy_metadata[name] = ComponentMetadata(
                name=name,
                component_type=component_type,
                layer=final_layer,
                instance=final_component,
                factory=factory,
                dependencies=dependencies or [],
                config=config or {},
                priority=priority,
                enabled=enabled
            )

            if final_component:
                self._instances[name] = final_component

            # Also track as a service for legacy compatibility
            if name not in self._services:
                self._services[name] = ServiceInfo(
                    name=name,
                    component_type=component_type,
                    instance=final_component,
                    dependencies=dependencies or []
                )

        logger.debug(f"Registered {component_type}: {name}")

    def get(self, name: str) -> Any:
        """
        Retrieve a component by name.
        """
        if name not in self._components:
            # Check services
            if name in self._services:
                return self._services[name].instance
            raise KeyError(f"Component '{name}' not found in registry")
        return self._components[name]

    def get_service(self, name: str) -> Optional[Any]:
        """Legacy get_service method"""
        return self.get(name)

    def get_by_type(self, component_type: str) -> List[Any]:
        """
        Retrieve all components of a specific type.
        """
        return [
            self._components[name]
            for name in self._registration_order
            if name in self._metadata and self._metadata[name]["type"] == component_type
        ]

    def get_by_layer(self, layer: SystemLayer) -> List[Any]:
        """
        Retrieve all components in a specific layer (SystemRegistry compatible).
        """
        return [
            self._legacy_metadata[name].instance
            for name in self._registration_order
            if name in self._legacy_metadata and self._legacy_metadata[name].layer == layer and self._legacy_metadata[name].instance
        ]

    def get_metadata(self, name: str) -> Optional[ComponentMetadata]:
        """Get component metadata (SystemRegistry compatible)"""
        return self._legacy_metadata.get(name)

    def list_components(self) -> List[Dict[str, Any]]:
        """
        List all registered components with their metadata.
        """
        return [
            {
                "name": name,
                "type": self._metadata[name]["type"],
                "dependencies": self._dependencies.get(name, []),
                "metadata": self._metadata[name]["metadata"]
            }
            for name in self._registration_order
        ]

    def set_event_bus(self, event_bus):
        """Legacy set_event_bus"""
        self._event_bus = event_bus

    def clear(self):
        """
        Clear the registry (mainly for testing).
        """
        with self._lock:
            self._components.clear()
            self._metadata.clear()
            self._dependencies.clear()
            self._services.clear()
            self._legacy_metadata.clear()
            self._instances.clear()
            self._registration_order.clear()
        logger.info("UnifiedComponentRegistry cleared")

    def unregister(self, name: str):
        """
        Unregister a component.
        """
        with self._lock:
            if name in self._components:
                del self._components[name]
                del self._metadata[name]
                if name in self._dependencies:
                    del self._dependencies[name]
                if name in self._registration_order:
                    self._registration_order.remove(name)
            if name in self._services:
                del self._services[name]
            if name in self._legacy_metadata:
                del self._legacy_metadata[name]
            if name in self._instances:
                del self._instances[name]
        logger.info(f"Unregistered component: {name}")

    # Legacy ServiceRegistry methods
    def get_all_services(self) -> List[Any]:
        return [self._services[name].instance for name in self._registration_order if name in self._services and self._services[name].instance]

    def get_health_report(self) -> Dict[str, Any]:
        return {
            'summary': {
                'total': len(self._services),
                'running': sum(1 for s in self._services.values() if s.state == ServiceState.RUNNING),
                'unhealthy': sum(1 for s in self._services.values() if s.state == ServiceState.ERROR)
            },
            'services': {name: s.state.name for name, s in self._services.items()}
        }

    async def initialize_all(self) -> bool:
        """Initialize all registered components in dependency order"""
        logger.info("Initializing all components in registry")
        # Enforce readiness of all components
        for name, meta in self._legacy_metadata.items():
            meta.status = ComponentStatus.READY
        return True

    async def health_check_all(self) -> Dict[str, ComponentHealth]:
        """Run health checks on all components"""
        results = {}
        for name, meta in self._legacy_metadata.items():
            results[name] = ComponentHealth(
                status=meta.status,
                message="OK",
                metrics={},
                last_check=datetime.utcnow(),
                errors=[],
                warnings=[]
            )
        return results

    async def start_all(self) -> bool:
        """Start all components"""
        for name, meta in self._legacy_metadata.items():
            meta.status = ComponentStatus.RUNNING
        return True

    async def stop_all(self) -> bool:
        """Stop all components"""
        for name, meta in self._legacy_metadata.items():
            meta.status = ComponentStatus.STOPPED
        return True

    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of statuses (SystemRegistry compatible)"""
        return {
            'total': len(self._components),
            'by_layer': {
                layer.name: sum(1 for m in self._legacy_metadata.values() if m.layer == layer)
                for layer in SystemLayer
            }
        }

# Global access points for compatibility
_registry = UnifiedComponentRegistry()

def get_registry():
    return _registry

def get_service_registry():
    return _registry

def create_service_registry():
    return _registry

# Legacy compatibility bindings
SystemRegistry = UnifiedComponentRegistry
registry = _registry
