"""
Service Locator - Centralized service access point for all trading bot modules.
"""

import logging
from typing import Dict, Any, Optional, TypeVar, Type, Callable
from contextlib import contextmanager
import threading
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class ServiceInfo:
    """Information about a registered service."""
    name: str
    service: Any
    factory: Optional[Callable] = None
    singleton: bool = True
    created_at: datetime = None
    dependencies: list = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []

class ServiceLocator:
    """
    Centralized service locator with dependency injection support.
    
    Provides:
    - Service registration and retrieval
    - Lazy initialization via factories
    - Singleton and prototype service patterns
    - Thread-safe operations
    - Service lifecycle management
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._services: Dict[str, ServiceInfo] = {}
            self._factories: Dict[str, Callable] = {}
            self._singletons: Dict[str, Any] = {}
            self._lock = threading.RLock()
            self._initialized = True
            logger.info("ServiceLocator initialized")
    
    def register(self, 
                 name: str, 
                 service: Any = None, 
                 factory: Callable = None,
                 singleton: bool = True,
                 dependencies: list = None) -> None:
        """
        Register a service.
        
        Args:
            name: Service name
            service: Service instance (if not using factory)
            factory: Factory function to create service
            singleton: Whether service should be singleton
            dependencies: List of service dependencies
        """
        with self._lock:
            if service is None and factory is None:
                raise ValueError("Either service or factory must be provided")
            
            if name in self._services:
                logger.warning(f"Service {name} already registered, overwriting")
            
            service_info = ServiceInfo(
                name=name,
                service=service,
                factory=factory,
                singleton=singleton,
                dependencies=dependencies or []
            )
            
            self._services[name] = service_info
            
            # If it's a singleton and service is provided, store it
            if singleton and service is not None:
                self._singletons[name] = service
            
            logger.debug(f"Registered service: {name} (singleton={singleton})")
    
    def get(self, name: str, default: Any = None) -> Any:
        """
        Get a service by name.
        
        Args:
            name: Service name
            default: Default value if service not found
            
        Returns:
            Service instance or default
        """
        with self._lock:
            if name not in self._services:
                logger.warning(f"Service {name} not registered")
                return default
            
            service_info = self._services[name]
            
            # Return singleton if already created
            if service_info.singleton and name in self._singletons:
                return self._singletons[name]
            
            # Create service if needed
            if service_info.service is None:
                if service_info.factory is None:
                    logger.error(f"Service {name} has no instance or factory")
                    return default
                
                try:
                    # Ensure dependencies are available
                    for dep in service_info.dependencies:
                        if not self.is_registered(dep):
                            logger.error(f"Dependency {dep} not found for service {name}")
                            return default
                    
                    # Create service
                    if service_info.dependencies:
                        # Inject dependencies
                        deps = {dep: self.get(dep) for dep in service_info.dependencies}
                        service = service_info.factory(**deps)
                    else:
                        service = service_info.factory()
                    
                    service_info.service = service
                    
                    # Store singleton
                    if service_info.singleton:
                        self._singletons[name] = service
                    
                    logger.debug(f"Created service: {name}")
                    
                except Exception as e:
                    logger.error(f"Failed to create service {name}: {e}")
                    return default
            
            return service_info.service
    
    def get_typed(self, service_type: Type[T], name: Optional[str] = None) -> Optional[T]:
        """
        Get a service with type hinting.
        
        Args:
            service_type: Expected service type
            name: Service name (defaults to type name)
            
        Returns:
            Service instance of specified type
        """
        service_name = name or service_type.__name__
        service = self.get(service_name)
        
        if service is not None and not isinstance(service, service_type):
            logger.warning(f"Service {service_name} is not of type {service_type}")
            return None
        
        return service
    
    def is_registered(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services
    
    def unregister(self, name: str) -> bool:
        """Unregister a service."""
        with self._lock:
            if name in self._services:
                del self._services[name]
                if name in self._singletons:
                    del self._singletons[name]
                logger.debug(f"Unregistered service: {name}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()
            logger.info("All services cleared")
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all registered services with their info."""
        with self._lock:
            result = {}
            for name, info in self._services.items():
                result[name] = {
                    'singleton': info.singleton,
                    'created': info.created_at.isoformat(),
                    'dependencies': info.dependencies,
                    'initialized': info.service is not None,
                    'has_factory': info.factory is not None
                }
            return result
    
    @contextmanager
    def temporary_service(self, name: str, service: Any):
        """
        Context manager for temporarily overriding a service.
        
        Args:
            name: Service name
            service: Temporary service instance
        """
        # Store original
        original = None
        was_registered = name in self._services
        
        if was_registered:
            original_info = self._services[name]
            original = original_info.service
        
        try:
            # Register temporary service
            self.register(name, service, singleton=True)
            yield service
        finally:
            # Restore original
            with self._lock:
                if was_registered:
                    self._services[name] = original_info
                    if original_info.singleton and original is not None:
                        self._singletons[name] = original
                else:
                    self.unregister(name)
    
    def create_scope(self) -> 'ServiceScope':
        """Create a new service scope for isolated operations."""
        return ServiceScope(self)
    
    def validate_dependencies(self) -> Dict[str, list]:
        """
        Validate all service dependencies.
        
        Returns:
            Dictionary mapping service names to missing dependencies
        """
        missing_deps = {}
        
        for name, info in self._services.items():
            missing = []
            for dep in info.dependencies:
                if not self.is_registered(dep):
                    missing.append(dep)
            
            if missing:
                missing_deps[name] = missing
        
        return missing_deps
    
    def get_dependency_graph(self) -> Dict[str, list]:
        """Get the dependency graph of all services."""
        graph = {}
        for name, info in self._services.items():
            graph[name] = info.dependencies.copy()
        return graph

class ServiceScope:
    """
    Service scope for isolated service operations.
    
    Allows creating temporary contexts where services can be overridden
    without affecting the global service locator.
    """
    
    def __init__(self, parent: ServiceLocator):
        self.parent = parent
        self.overrides: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def register(self, name: str, service: Any) -> None:
        """Register a service override in this scope."""
        with self._lock:
            self.overrides[name] = service
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get a service, checking scope overrides first."""
        with self._lock:
            if name in self.overrides:
                return self.overrides[name]
            return self.parent.get(name, default)
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, cleaning up overrides."""
        with self._lock:
            self.overrides.clear()

# Global service locator instance
_service_locator = ServiceLocator()

def get_service_locator() -> ServiceLocator:
    """Get the global service locator instance."""
    return _service_locator

def register_service(name: str, 
                    service: Any = None, 
                    factory: Callable = None,
                    singleton: bool = True,
                    dependencies: list = None) -> None:
    """Register a service with the global locator."""
    _service_locator.register(
        name=name,
        service=service,
        factory=factory,
        singleton=singleton,
        dependencies=dependencies
    )

def get_service(name: str, default: Any = None) -> Any:
    """Get a service from the global locator."""
    return _service_locator.get(name, default)

def get_service_typed(service_type: Type[T], name: Optional[str] = None) -> Optional[T]:
    """Get a typed service from the global locator."""
    return _service_locator.get_typed(service_type, name)
