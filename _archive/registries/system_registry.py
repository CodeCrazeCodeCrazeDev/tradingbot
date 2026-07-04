"""
System Registry - Component registry and dependency injection
Manages registration, discovery, and lifecycle of all system components
"""
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

from trading_bot.system_interfaces import (
    ISystemComponent,
    ComponentStatus,
    ComponentHealth,
    SystemLayer
)

logger = logging.getLogger(__name__)


@dataclass
class ComponentMetadata:
    """Metadata for a registered component"""
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


class SystemRegistry:
    """
    Central registry for all system components
    Provides dependency injection and lifecycle management
    """
    
    def __init__(self):
        self._components: Dict[str, ComponentMetadata] = {}
        self._instances: Dict[str, ISystemComponent] = {}
        self._initialization_order: List[str] = []
        self._lock = asyncio.Lock()
        
    def register(
        self,
        name: str,
        component_type: str,
        layer: SystemLayer,
        factory: Optional[Callable] = None,
        instance: Optional[ISystemComponent] = None,
        dependencies: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        enabled: bool = True
    ) -> bool:
        """
        Register a component
        
        Args:
            name: Unique component name
            component_type: Type of component (data_provider, signal_generator, etc.)
            layer: Architecture layer
            factory: Factory function to create instance
            instance: Pre-created instance
            dependencies: List of component names this depends on
            config: Component configuration
            priority: Initialization priority (higher = earlier)
            enabled: Whether component is enabled
        """
        if name in self._components:
            logger.warning(f"Component {name} already registered, updating")
        
        metadata = ComponentMetadata(
            name=name,
            component_type=component_type,
            layer=layer,
            instance=instance,
            factory=factory,
            dependencies=dependencies or [],
            config=config or {},
            priority=priority,
            enabled=enabled
        )
        
        self._components[name] = metadata
        
        if instance:
            self._instances[name] = instance
        
        logger.info(f"Registered component: {name} ({component_type}) in layer {layer.name}")
        return True
    
    def unregister(self, name: str) -> bool:
        """Unregister a component"""
        if name in self._components:
            del self._components[name]
            if name in self._instances:
                del self._instances[name]
            logger.info(f"Unregistered component: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[ISystemComponent]:
        """Get a component instance"""
        return self._instances.get(name)
    
    def get_metadata(self, name: str) -> Optional[ComponentMetadata]:
        """Get component metadata"""
        return self._components.get(name)
    
    def get_by_type(self, component_type: str) -> List[ISystemComponent]:
        """Get all components of a specific type"""
        return [
            self._instances[name]
            for name, meta in self._components.items()
            if meta.component_type == component_type and name in self._instances
        ]
    
    def get_by_layer(self, layer: SystemLayer) -> List[ISystemComponent]:
        """Get all components in a specific layer"""
        return [
            self._instances[name]
            for name, meta in self._components.items()
            if meta.layer == layer and name in self._instances
        ]
    
    def list_components(self) -> List[str]:
        """List all registered component names"""
        return list(self._components.keys())
    
    def list_by_type(self, component_type: str) -> List[str]:
        """List component names by type"""
        return [
            name for name, meta in self._components.items()
            if meta.component_type == component_type
        ]
    
    async def initialize_all(self) -> bool:
        """Initialize all registered components in dependency order"""
        async with self._lock:
            # Calculate initialization order based on dependencies and priority
            order = self._calculate_initialization_order()
            
            logger.info(f"Initializing {len(order)} components in order...")
            
            for name in order:
                if not await self._initialize_component(name):
                    logger.error(f"Failed to initialize component: {name}")
                    return False
            
            self._initialization_order = order
            logger.info("All components initialized successfully")
            return True
    
    async def _initialize_component(self, name: str) -> bool:
        """Initialize a single component"""
        metadata = self._components.get(name)
        if not metadata:
            logger.error(f"Component not found: {name}")
            return False
        
        if not metadata.enabled:
            logger.info(f"Skipping disabled component: {name}")
            return True
        
        # Create instance if needed
        if name not in self._instances:
            if metadata.factory:
                try:
                    instance = metadata.factory(metadata.config)
                    self._instances[name] = instance
                    metadata.instance = instance
                except Exception as e:
                    logger.error(f"Failed to create instance for {name}: {e}")
                    return False
            else:
                logger.error(f"No instance or factory for component: {name}")
                return False
        
        # Initialize
        instance = self._instances[name]
        try:
            metadata.status = ComponentStatus.INITIALIZING
            success = await instance.initialize(metadata.config)
            
            if success:
                metadata.status = ComponentStatus.READY
                metadata.initialized_at = datetime.utcnow()
                logger.info(f"Initialized component: {name}")
            else:
                metadata.status = ComponentStatus.ERROR
                logger.error(f"Component initialization returned False: {name}")
                return False
                
        except Exception as e:
            metadata.status = ComponentStatus.ERROR
            logger.error(f"Error initializing component {name}: {e}")
            return False
        
        return True
    
    def _calculate_initialization_order(self) -> List[str]:
        """Calculate initialization order based on dependencies and priority"""
        # Topological sort with priority
        visited = set()
        order = []
        
        def visit(name: str):
            """
            visit function.

    Args:
        name: Description

    Returns:
        Result of operation
            """
            if name in visited:
                return
            
            visited.add(name)
            metadata = self._components.get(name)
            
            if metadata:
                # Visit dependencies first
                for dep in metadata.dependencies:
                    if dep in self._components:
                        visit(dep)
                
                if metadata.enabled:
                    order.append(name)
        
        # Sort by priority (higher priority first)
        sorted_components = sorted(
            self._components.items(),
            key=lambda x: (-x[1].priority, x[1].layer.value)
        )
        
        for name, _ in sorted_components:
            visit(name)
        
        return order
    
    async def start_all(self) -> bool:
        """Start all initialized components"""
        logger.info("Starting all components...")
        
        for name in self._initialization_order:
            metadata = self._components.get(name)
            if not metadata or not metadata.enabled:
                continue
            
            instance = self._instances.get(name)
            if instance:
                try:
                    await instance.start()
                    metadata.status = ComponentStatus.RUNNING
                    logger.info(f"Started component: {name}")
                except Exception as e:
                    logger.error(f"Error starting component {name}: {e}")
                    metadata.status = ComponentStatus.ERROR
                    return False
        
        logger.info("All components started successfully")
        return True
    
    async def stop_all(self) -> bool:
        """Stop all running components in reverse order"""
        logger.info("Stopping all components...")
        
        # Stop in reverse order
        for name in reversed(self._initialization_order):
            metadata = self._components.get(name)
            if not metadata:
                continue
            
            instance = self._instances.get(name)
            if instance:
                try:
                    await instance.stop()
                    metadata.status = ComponentStatus.STOPPED
                    logger.info(f"Stopped component: {name}")
                except Exception as e:
                    logger.error(f"Error stopping component {name}: {e}")
        
        logger.info("All components stopped")
        return True
    
    async def health_check_all(self) -> Dict[str, ComponentHealth]:
        """Run health check on all components"""
        results = {}
        
        for name, instance in self._instances.items():
            try:
                health = await instance.health_check()
                results[name] = health
            except Exception as e:
                results[name] = ComponentHealth(
                    status=ComponentStatus.ERROR,
                    message=f"Health check failed: {e}",
                    metrics={},
                    last_check=datetime.utcnow(),
                    errors=[str(e)],
                    warnings=[]
                )
        
        return results
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of all component statuses"""
        summary = {
            'total': len(self._components),
            'enabled': sum(1 for m in self._components.values() if m.enabled),
            'initialized': sum(1 for m in self._components.values() if m.status != ComponentStatus.UNINITIALIZED),
            'running': sum(1 for m in self._components.values() if m.status == ComponentStatus.RUNNING),
            'error': sum(1 for m in self._components.values() if m.status == ComponentStatus.ERROR),
            'by_layer': {},
            'by_type': {}
        }
        
        for metadata in self._components.values():
            layer_name = metadata.layer.name
            if layer_name not in summary['by_layer']:
                summary['by_layer'][layer_name] = 0
            summary['by_layer'][layer_name] += 1
            
            if metadata.component_type not in summary['by_type']:
                summary['by_type'][metadata.component_type] = 0
            summary['by_type'][metadata.component_type] += 1
        
        return summary


# Global registry instance
_registry_instance: Optional[SystemRegistry] = None


def get_registry() -> SystemRegistry:
    """Get global registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SystemRegistry()
    return _registry_instance


def reset_registry():
    """Reset registry (for testing)"""
    global _registry_instance
    _registry_instance = None


__all__ = [
    'ComponentMetadata',
    'SystemRegistry',
    'get_registry',
    'reset_registry',
]
