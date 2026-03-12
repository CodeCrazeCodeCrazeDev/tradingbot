"""
Service Managers - Manage groups of related services within each category.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import traceback

from ..registry import ModuleRegistry, ModuleCategory, get_registry
from ..registry.service_locator import ServiceLocator, get_service_locator
from .event_bus import EventBus, get_event_bus, Event, EventPriority

logger = logging.getLogger(__name__)

@dataclass
class ServiceStatus:
    """Status of a service."""
    name: str
    initialized: bool = False
    healthy: bool = True
    last_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    last_error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

class ServiceManager(ABC):
    """
    Base class for all service managers.
    
    Service managers are responsible for:
    - Initializing services in their category
    - Monitoring service health
    - Coordinating service interactions
    - Handling service failures
    """
    
    def __init__(self, 
                 category: ModuleCategory,
                 name: str = None):
        self.category = category
        self.name = name or f"{category.value}_manager"
        self.registry: ModuleRegistry = get_registry()
        self.service_locator: ServiceLocator = get_service_locator()
        self.event_bus: EventBus = get_event_bus()
        
        self.services: Dict[str, Any] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.initialized = False
        
        # Configuration
        self.auto_retry = True
        self.max_retries = 3
        self.retry_delay = 5.0
        self.health_check_interval = 60.0
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """Initialize all services in this category."""
        logger.info(f"Initializing {self.name}...")
        
        try:
            # Get modules for this category
            modules = self.registry.get_modules_by_category(self.category)
            
            # Sort by priority
            modules.sort(key=lambda m: m.priority, reverse=True)
            
            # Initialize each module
            for module_info in modules:
                if not module_info.enabled:
                    logger.info(f"Skipping disabled module: {module_info.name}")
                    continue
                
                success = await self._initialize_service(module_info)
                if not success and not self._is_optional(module_info.name):
                    logger.error(f"Failed to initialize required service: {module_info.name}")
                    return False
            
            # Start health monitoring
            self._start_health_monitoring()
            
            self.initialized = True
            logger.info(f"{self.name} initialized successfully")
            
            # Publish initialization event
            await self.event_bus.publish(Event(
                type="service_manager_initialized",
                data={
                    'manager': self.name,
                    'category': self.category.value,
                    'services': list(self.services.keys())
                },
                source=self.name,
                priority=EventPriority.HIGH
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            traceback.print_exc()
            return False
    
    async def _initialize_service(self, module_info) -> bool:
        """Initialize a single service."""
        service_name = module_info.name
        
        try:
            # Check if already initialized
            if service_name in self.services:
                logger.debug(f"Service {service_name} already initialized")
                return True
            
            # Initialize dependencies first
            for dep in module_info.dependencies:
                if not await self._ensure_dependency(dep):
                    logger.error(f"Failed to initialize dependency {dep} for {service_name}")
                    return False
            
            # Initialize the module
            if self.registry.initialize_module(service_name):
                # Get the main service instance
                service = self._get_service_instance(module_info)
                
                if service:
                    self.services[service_name] = service
                    self.service_status[service_name] = ServiceStatus(name=service_name, initialized=True)
                    
                    # Register with service locator
                    self.service_locator.register(
                        name=service_name,
                        service=service,
                        singleton=True
                    )
                    
                    logger.info(f"Initialized service: {service_name}")
                    
                    # Publish service initialization event
                    await self.event_bus.publish(Event(
                        type="service_initialized",
                        data={
                            'service': service_name,
                            'category': self.category.value,
                            'class': module_info.class_name
                        },
                        source=self.name
                    ))
                    
                    return True
                else:
                    logger.warning(f"No service instance found for {service_name}")
                    return False
            else:
                logger.error(f"Registry failed to initialize {service_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize service {service_name}: {e}")
            self._record_error(service_name, str(e))
            return False
    
    def _get_service_instance(self, module_info) -> Optional[Any]:
        """Get the main service instance from a module."""
        if not module_info.module:
            return None
        
        # Try to get the main class
        if module_info.class_name:
            service_class = getattr(module_info.module, module_info.class_name, None)
            if service_class:
                try:
                    # Try to get existing instance
                    if hasattr(service_class, 'get_instance'):
                        return service_class.get_instance()
                    # Create new instance
                    return service_class()
                except Exception as e:
                    logger.error(f"Failed to create instance of {module_info.class_name}: {e}")
        
        # Fall back to module itself
        return module_info.module
    
    async def _ensure_dependency(self, dependency: str) -> bool:
        """Ensure a dependency is available."""
        # Check if it's in the same category
        dep_module = self.registry.get_module(dependency)
        if dep_module and dep_module.category == self.category:
            if dependency not in self.services:
                return await self._initialize_service(dep_module)
            return True
        
        # Check other categories through service locator
        service = self.service_locator.get(dependency)
        return service is not None
    
    def _is_optional(self, service_name: str) -> bool:
        """Check if a service is optional."""
        # Override in subclasses
        return False
    
    def _record_error(self, service_name: str, error: str) -> None:
        """Record an error for a service."""
        if service_name not in self.service_status:
            self.service_status[service_name] = ServiceStatus(name=service_name)
        
        status = self.service_status[service_name]
        status.error_count += 1
        status.last_error = error
        status.healthy = False
        status.last_check = datetime.now()
    
    def _start_health_monitoring(self) -> None:
        """Start background health monitoring."""
        if self.health_check_interval > 0:
            self._health_check_task = asyncio.create_task(self._health_monitor_loop())
    
    async def _health_monitor_loop(self) -> None:
        """Background health monitoring loop."""
        while True:
            try:
                await self._check_all_health()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error in {self.name}: {e}")
                await asyncio.sleep(10)
    
    async def _check_all_health(self) -> None:
        """Check health of all services."""
        for service_name, service in self.services.items():
            try:
                healthy = await self._check_service_health(service_name, service)
                
                if service_name in self.service_status:
                    status = self.service_status[service_name]
                    status.healthy = healthy
                    status.last_check = datetime.now()
                    
                    if not healthy:
                        await self._handle_unhealthy_service(service_name, service)
                        
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                self._record_error(service_name, str(e))
    
    async def _check_service_health(self, service_name: str, service: Any) -> bool:
        """Check health of a specific service."""
        # Try to call health check method
        if hasattr(service, 'health_check'):
            if asyncio.iscoroutinefunction(service.health_check):
                return await service.health_check()
            else:
                return service.health_check()
        
        # Try to check if service is callable/usable
        try:
            if hasattr(service, 'is_healthy'):
                return service.is_healthy()
            elif hasattr(service, 'status'):
                return service.status == 'running'
            else:
                # Default to healthy if no check method
                return True
        except Exception:
            return False
    
    async def _handle_unhealthy_service(self, service_name: str, service: Any) -> None:
        """Handle an unhealthy service."""
        logger.warning(f"Service {service_name} is unhealthy")
        
        # Publish unhealthy service event
        await self.event_bus.publish(Event(
            type="service_unhealthy",
            data={
                'service': service_name,
                'manager': self.name,
                'error': self.service_status[service_name].last_error
            },
            source=self.name,
            priority=EventPriority.HIGH
        ))
        
        # Try to recover if auto-retry is enabled
        if self.auto_retry:
            status = self.service_status[service_name]
            if status.error_count <= self.max_retries:
                logger.info(f"Attempting to recover service {service_name}")
                await asyncio.sleep(self.retry_delay)
                await self._recover_service(service_name, service)
    
    async def _recover_service(self, service_name: str, service: Any) -> None:
        """Attempt to recover a service."""
        try:
            # Try to reinitialize
            module_info = self.registry.get_module(service_name)
            if module_info:
                await self._initialize_service(module_info)
                logger.info(f"Successfully recovered service {service_name}")
        except Exception as e:
            logger.error(f"Failed to recover service {service_name}: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown all services."""
        logger.info(f"Shutting down {self.name}...")
        
        # Stop health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown services in reverse order
        for service_name in reversed(list(self.services.keys())):
            await self._shutdown_service(service_name)
        
        self.services.clear()
        self.service_status.clear()
        self.initialized = False
        
        logger.info(f"{self.name} shutdown complete")
    
    async def _shutdown_service(self, service_name: str) -> None:
        """Shutdown a specific service."""
        try:
            service = self.services.get(service_name)
            if service and hasattr(service, 'shutdown'):
                if asyncio.iscoroutinefunction(service.shutdown):
                    await service.shutdown()
                else:
                    service.shutdown()
                logger.debug(f"Shutdown service: {service_name}")
        except Exception as e:
            logger.error(f"Error shutting down service {service_name}: {e}")
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name."""
        return self.services.get(name)
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status."""
        return {
            'name': self.name,
            'category': self.category.value,
            'initialized': self.initialized,
            'service_count': len(self.services),
            'healthy_services': sum(1 for s in self.service_status.values() if s.healthy),
            'services': {
                name: {
                    'initialized': status.initialized,
                    'healthy': status.healthy,
                    'error_count': status.error_count,
                    'last_error': status.last_error,
                    'last_check': status.last_check.isoformat() if status.last_check else None
                }
                for name, status in self.service_status.items()
            }
        }

class DataServiceManager(ServiceManager):
    """Manager for data and connectivity services."""
    
    def __init__(self):
        super().__init__(ModuleCategory.DATA_CONNECTIVITY, "data_service_manager")
        self.optional_services = {
            'blockchain', 'crypto', 'alternative_data'
        }
    
    def _is_optional(self, service_name: str) -> bool:
        return service_name in self.optional_services

class AnalysisServiceManager(ServiceManager):
    """Manager for analysis and intelligence services."""
    
    def __init__(self):
        super().__init__(ModuleCategory.ANALYSIS_INTELLIGENCE, "analysis_service_manager")
        self.optional_services = {
            'quantum', 'deepchart', 'perplexity_trading'
        }
    
    def _is_optional(self, service_name: str) -> bool:
        return service_name in self.optional_services

class TradingServiceManager(ServiceManager):
    """Manager for trading and execution services."""
    
    def __init__(self):
        super().__init__(ModuleCategory.TRADING_EXECUTION, "trading_service_manager")
        self.optional_services = {
            'hft', 'market_making', 'arbitrage'
        }
    
    def _is_optional(self, service_name: str) -> bool:
        return service_name in self.optional_services

class RiskServiceManager(ServiceManager):
    """Manager for risk and safety services."""
    
    def __init__(self):
        super().__init__(ModuleCategory.RISK_SAFETY, "risk_service_manager")
        # Risk services are generally not optional
        self.optional_services = set()
    
    def _is_optional(self, service_name: str) -> bool:
        return service_name in self.optional_services

class OptimizationServiceManager(ServiceManager):
    """Manager for optimization and evolution services."""
    
    def __init__(self):
        super().__init__(ModuleCategory.OPTIMIZATION_EVOLUTION, "optimization_service_manager")
        self.optional_services = {
            'eternal_evolution', 'self_assembly_ai', 'sentient_core'
        }
    
    def _is_optional(self, service_name: str) -> bool:
        return service_name in self.optional_services

class OrchestrationServiceManager(ServiceManager):
    """Manager for orchestration and management services."""
    
    def __init__(self):
        super().__init__(ModuleCategory.ORCHESTRATION_MANAGEMENT, "orchestration_service_manager")
        self.optional_services = {
            'notifications', 'mobile', 'voice_assistant'
        }
    
    def _is_optional(self, service_name: str) -> bool:
        return service_name in self.optional_services

class SpecializedSystemServiceManager(ServiceManager):
    """Manager for specialized trading systems."""
    
    def __init__(self):
        super().__init__(ModuleCategory.SPECIALIZED_SYSTEMS, "specialized_systems_manager")
        self.optional_services = {
            'apex_fi', 'mosefs', 'neuros_evolution', 'neuros_fi',
            'hivemind', 'hedge_fund', 'msos'
        }
    
    def _is_optional(self, service_name: str) -> bool:
        return service_name in self.optional_services

class InfrastructureServiceManager(ServiceManager):
    """Manager for infrastructure services."""
    
    def __init__(self):
        super().__init__(ModuleCategory.INFRASTRUCTURE, "infrastructure_service_manager")
        self.optional_services = {
            'mobile_app', 'web', 'deployment', 'devops'
        }
    
    def _is_optional(self, service_name: str) -> bool:
        return service_name in self.optional_services
