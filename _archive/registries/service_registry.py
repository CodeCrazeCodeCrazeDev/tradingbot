"""
Service Registry - Service Discovery and Management
====================================================

Central registry for all trading bot services:
- Service registration and discovery
- Health monitoring
- Dependency injection
- Lifecycle management
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
from uuid import uuid4

logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """Service lifecycle states"""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServicePriority(Enum):
    """Service startup priority"""
    CRITICAL = 0      # Core infrastructure
    HIGH = 1          # Essential services
    NORMAL = 2        # Standard services
    LOW = 3           # Optional services
    BACKGROUND = 4    # Background tasks


@dataclass
class ServiceHealth:
    """Service health status"""
    healthy: bool
    last_check: datetime
    message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceInfo:
    """Service metadata"""
    service_id: str
    name: str
    service_type: str
    priority: ServicePriority
    state: ServiceState = ServiceState.REGISTERED
    health: Optional[ServiceHealth] = None
    dependencies: List[str] = field(default_factory=list)
    instance: Any = None
    started_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseService(ABC):
    """Base class for all services"""
    
    SERVICE_NAME: str = "base_service"
    SERVICE_TYPE: str = "generic"
    PRIORITY: ServicePriority = ServicePriority.NORMAL
    DEPENDENCIES: List[str] = []
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.service_id = str(uuid4())
        self._running = False
        self._event_bus = None
        self._registry = None
        
    @abstractmethod
    async def start(self) -> None:
        """Start the service"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the service"""
        pass
    
    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        pass
    
    def set_event_bus(self, event_bus) -> None:
        """Set event bus reference"""
        self._event_bus = event_bus
    
    def set_registry(self, registry) -> None:
        """Set registry reference"""
        self._registry = registry
    
    def get_dependency(self, service_name: str) -> Optional[Any]:
        """Get a dependency service"""
        if self._registry:
            return self._registry.get_service(service_name)
        return None


class ServiceRegistry:
    """
    Central Service Registry
    
    Manages service lifecycle, discovery, and health monitoring.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._services: Dict[str, ServiceInfo] = {}
        self._service_types: Dict[str, List[str]] = {}
        self._event_bus = None
        self._health_check_interval = self.config.get('health_check_interval', 30)
        self._health_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info("ServiceRegistry initialized")
    
    def set_event_bus(self, event_bus) -> None:
        """Set event bus for service communication"""
        self._event_bus = event_bus
    
    def register(
        self,
        service: BaseService,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Register a service"""
        service_info = ServiceInfo(
            service_id=service.service_id,
            name=service.SERVICE_NAME,
            service_type=service.SERVICE_TYPE,
            priority=service.PRIORITY,
            dependencies=dependencies or service.DEPENDENCIES,
            instance=service,
        )
        
        self._services[service.SERVICE_NAME] = service_info
        
        # Track by type
        if service.SERVICE_TYPE not in self._service_types:
            self._service_types[service.SERVICE_TYPE] = []
        self._service_types[service.SERVICE_TYPE].append(service.SERVICE_NAME)
        
        # Inject dependencies
        service.set_registry(self)
        if self._event_bus:
            service.set_event_bus(self._event_bus)
        
        logger.info(f"Service registered: {service.SERVICE_NAME}")
        return service.service_id
    
    def unregister(self, service_name: str) -> bool:
        """Unregister a service"""
        if service_name not in self._services:
            return False
        
        service_info = self._services.pop(service_name)
        
        # Remove from type tracking
        if service_info.service_type in self._service_types:
            self._service_types[service_info.service_type].remove(service_name)
        
        logger.info(f"Service unregistered: {service_name}")
        return True
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service instance by name"""
        service_info = self._services.get(service_name)
        if service_info and service_info.state == ServiceState.RUNNING:
            return service_info.instance
        return None
    
    def get_services_by_type(self, service_type: str) -> List[Any]:
        """Get all services of a specific type"""
        service_names = self._service_types.get(service_type, [])
        return [
            self._services[name].instance
            for name in service_names
            if self._services[name].state == ServiceState.RUNNING
        ]
    
    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Get all registered services"""
        return self._services.copy()
    
    async def start_all(self) -> Dict[str, bool]:
        """Start all services in priority order"""
        results = {}
        
        # Sort by priority
        sorted_services = sorted(
            self._services.values(),
            key=lambda s: s.priority.value
        )
        
        for service_info in sorted_services:
            # Check dependencies
            deps_ready = all(
                self._services.get(dep, ServiceInfo(
                    service_id="", name="", service_type="",
                    priority=ServicePriority.NORMAL
                )).state == ServiceState.RUNNING
                for dep in service_info.dependencies
            )
            
            if not deps_ready:
                logger.warning(
                    f"Service {service_info.name} dependencies not ready"
                )
                results[service_info.name] = False
                continue
            
            try:
                service_info.state = ServiceState.INITIALIZING
                await service_info.instance.start()
                service_info.state = ServiceState.RUNNING
                service_info.started_at = datetime.utcnow()
                results[service_info.name] = True
                logger.info(f"Service started: {service_info.name}")
            except Exception as e:
                service_info.state = ServiceState.ERROR
                results[service_info.name] = False
                logger.error(f"Failed to start {service_info.name}: {e}")
        
        # Start health monitoring
        self._health_task = asyncio.create_task(self._health_monitor())
        
        return results
    
    async def stop_all(self) -> Dict[str, bool]:
        """Stop all services in reverse priority order"""
        results = {}
        
        # Stop health monitoring
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        
        # Sort by priority (reverse)
        sorted_services = sorted(
            self._services.values(),
            key=lambda s: -s.priority.value
        )
        
        for service_info in sorted_services:
            if service_info.state != ServiceState.RUNNING:
                continue
            
            try:
                service_info.state = ServiceState.STOPPING
                await service_info.instance.stop()
                service_info.state = ServiceState.STOPPED
                results[service_info.name] = True
                logger.info(f"Service stopped: {service_info.name}")
            except Exception as e:
                service_info.state = ServiceState.ERROR
                results[service_info.name] = False
                logger.error(f"Failed to stop {service_info.name}: {e}")
        
        return results
    
    async def _health_monitor(self) -> None:
        """Monitor service health"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                
                for service_info in self._services.values():
                    if service_info.state != ServiceState.RUNNING:
                        continue
                    
                    try:
                        health = await service_info.instance.health_check()
                        service_info.health = health
                        
                        if not health.healthy:
                            logger.warning(
                                f"Service unhealthy: {service_info.name} - {health.message}"
                            )
                    except Exception as e:
                        service_info.health = ServiceHealth(
                            healthy=False,
                            last_check=datetime.utcnow(),
                            message=str(e)
                        )
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get health report for all services"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'services': {},
            'summary': {
                'total': len(self._services),
                'running': 0,
                'healthy': 0,
                'unhealthy': 0,
            }
        }
        
        for name, info in self._services.items():
            report['services'][name] = {
                'state': info.state.value,
                'type': info.service_type,
                'priority': info.priority.name,
                'started_at': info.started_at.isoformat() if info.started_at else None,
                'health': {
                    'healthy': info.health.healthy if info.health else None,
                    'message': info.health.message if info.health else None,
                    'last_check': info.health.last_check.isoformat() if info.health else None,
                } if info.health else None
            }
            
            if info.state == ServiceState.RUNNING:
                report['summary']['running'] += 1
                if info.health and info.health.healthy:
                    report['summary']['healthy'] += 1
                elif info.health:
                    report['summary']['unhealthy'] += 1
        
        return report


# Singleton instance
_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get singleton registry instance"""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry


def create_service_registry(config: Optional[Dict] = None) -> ServiceRegistry:
    """Factory function to create ServiceRegistry instance"""
    return ServiceRegistry(config)
