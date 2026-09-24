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
import inspect
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
        metadata: Optional[Dict[str, Any]] = None,
        overwrite: bool = False
    ):
        """
        Register a component with the system.
        Enforces no duplicate component IDs and deterministic order.
        Compatible with both legacy SystemRegistry and UCA-2026 signatures.
        """
        # Legacy call shape: register(component) — the first positional arg is
        # the component itself (ServiceRegistry façade / register(service)).
        if not isinstance(name, str):
            component = name
            name = getattr(component, "SERVICE_NAME", None) or type(component).__name__

        # Architectural drift prevention
        if name.endswith("Registry") and name != "UnifiedComponentRegistry":
            raise ValueError(f"Unauthorized registry registration: {name}. Only UnifiedComponentRegistry is allowed.")
        if name.endswith("Orchestrator") and name not in ["AIPOrchestrator", "SimulationOrchestrator"]:
            raise ValueError(f"Unauthorized orchestrator: {name}. All orchestration must route through CognitiveSystemController or authorized Ontologies.")

        if name in self._components:
            if not overwrite:
                raise ValueError(
                    f"Component '{name}' already registered. Duplicate registration "
                    "is forbidden — pass overwrite=True for intentional re-registration."
                )
            logger.warning(f"Component '{name}' already registered. Overwriting.")

        comp = component if component is not None else instance
        deps = dependencies or []

        with self._lock:
            self._components[name] = comp
            self._metadata[name] = {
                "type": component_type,
                "metadata": metadata or {},
            }
            self._dependencies[name] = deps
            self._services[name] = ServiceInfo(
                name=name,
                component_type=component_type,
                instance=comp,
                factory=factory,
                dependencies=deps,
                config=config or {},
            )
            self._legacy_metadata[name] = ComponentMetadata(
                name=name,
                component_type=component_type,
                layer=layer or SystemLayer.INTELLIGENCE_CORE,
                instance=comp,
                factory=factory,
                dependencies=deps,
                config=config or {},
                priority=priority,
                enabled=enabled,
            )
            if comp is not None:
                self._instances[name] = comp
            if name not in self._registration_order:
                self._registration_order.append(name)

        logger.debug(f"Registered {component_type}: {name}")

    def get(self, name: str, default: Any = None) -> Any:
        """
        Retrieve a component by name.
        """
        return self._components.get(name, default)

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

    def validate_dependencies(self) -> Dict[str, List[str]]:
        """Return registered components whose declared dependencies are missing."""
        registered = set(self._components)
        return {
            name: [dependency for dependency in dependencies if dependency not in registered]
            for name, dependencies in self._dependencies.items()
            if any(dependency not in registered for dependency in dependencies)
        }

    def initialization_order(self) -> List[str]:
        """Return deterministic dependency order and fail on missing/cyclic edges."""
        missing = self.validate_dependencies()
        if missing:
            details = "; ".join(
                f"{name}: {', '.join(dependencies)}"
                for name, dependencies in missing.items()
            )
            raise ValueError(f"Unresolved component dependencies: {details}")

        order: List[str] = []
        visiting = set()
        visited = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"Circular component dependency detected at '{name}'")
            visiting.add(name)
            for dependency in self._dependencies.get(name, []):
                visit(dependency)
            visiting.remove(name)
            visited.add(name)
            order.append(name)

        for name in self._registration_order:
            visit(name)
        return order

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

    @classmethod
    def reset(cls):
        """Reset the singleton in place for testing purposes.

        Keeps the same object identity so previously-imported references
        (e.g. module-level ``registry``) stay valid — matching the in-place
        reset contract of ``UnifiedDecisionBus.reset()``.
        """
        with cls._lock:
            inst = cls._instance
            if inst is None:
                return
            # ``self._lock`` is class-level — the same lock guards all
            # mutations, so a single critical section suffices.
            inst._components.clear()
            inst._metadata.clear()
            inst._dependencies.clear()
            inst._services.clear()
            inst._legacy_metadata.clear()
            inst._instances.clear()
            inst._registration_order.clear()
        logger.info("UnifiedComponentRegistry state reset in place")

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
        """Initialize all registered components in deterministic dependency order."""
        logger.info("Initializing all components in registry")
        for name in self.initialization_order():
            meta = self._legacy_metadata[name]
            meta.status = ComponentStatus.INITIALIZING
            service = self._services[name]
            try:
                if service.instance is None and service.factory is not None:
                    service.instance = service.factory()
                    self._components[name] = service.instance
                    self._instances[name] = service.instance
                    meta.instance = service.instance
                component = service.instance
                initialize = getattr(component, "initialize", None)
                if initialize is not None:
                    parameters = inspect.signature(initialize).parameters
                    result = initialize() if not parameters else initialize(service.config)
                    if asyncio.iscoroutine(result):
                        await result
                meta.status = ComponentStatus.READY
                service.state = ServiceState.READY
                service.initialized_at = datetime.utcnow()
                meta.initialized_at = service.initialized_at
            except Exception as exc:
                meta.status = ComponentStatus.ERROR
                service.state = ServiceState.ERROR
                service.last_error = str(exc)
                logger.error("Failed to initialize component %s: %s", name, exc)
                return False
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
