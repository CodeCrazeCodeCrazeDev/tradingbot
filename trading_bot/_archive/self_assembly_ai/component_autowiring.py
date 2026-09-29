"""
Component Auto-Wiring System
=============================

Automatic discovery, dependency resolution, and wiring of
system components without manual configuration:
- Component scanning and registration
- Dependency injection
- Interface matching
- Hot-swapping capabilities
- Lazy loading
- Circular dependency detection
- Auto-configuration

The system can wire itself together like a self-assembling machine.
"""

import asyncio
import importlib
import inspect
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Generic
import hashlib

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ComponentScope(Enum):
    """Scope of component lifecycle"""
    SINGLETON = "singleton"     # One instance for entire application
    PROTOTYPE = "prototype"     # New instance each time
    REQUEST = "request"         # One instance per request
    SESSION = "session"         # One instance per session


class WiringMode(Enum):
    """How components are wired"""
    CONSTRUCTOR = "constructor"  # Inject via constructor
    SETTER = "setter"           # Inject via setter methods
    FIELD = "field"             # Inject directly to fields
    LAZY = "lazy"               # Inject lazily on first access


class ComponentState(Enum):
    """State of a component"""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    DISPOSED = "disposed"


@dataclass
class ComponentMetadata:
    """Metadata about a component"""
    component_id: str
    component_type: Type
    interfaces: List[Type]
    scope: ComponentScope
    wiring_mode: WiringMode
    dependencies: List[str]
    provides: List[str]
    priority: int = 0
    lazy: bool = False
    auto_start: bool = True
    tags: Set[str] = field(default_factory=set)
    
    # Runtime info
    state: ComponentState = ComponentState.REGISTERED
    instance: Optional[Any] = None
    created_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class DependencyDescriptor:
    """Describes a dependency"""
    name: str
    required_type: Type
    optional: bool = False
    default: Any = None
    qualifier: Optional[str] = None


class ComponentInterface(ABC):
    """Base interface for auto-wirable components"""
    
    @abstractmethod
    def get_component_id(self) -> str:
        """Get unique component ID"""
        pass
    
    def on_wire(self) -> None:
        """Called when component is wired"""
        pass
    
    def on_start(self) -> None:
        """Called when component starts"""
        pass
    
    def on_stop(self) -> None:
        """Called when component stops"""
        pass
    
    def health_check(self) -> bool:
        """Check component health"""
        return True


class ComponentRegistry:
    """
    Registry of all discoverable components
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentMetadata] = {}
        self.by_type: Dict[Type, List[str]] = {}
        self.by_interface: Dict[Type, List[str]] = {}
        self.by_tag: Dict[str, List[str]] = {}
    
    def register(self, metadata: ComponentMetadata) -> None:
        """Register a component"""
        self.components[metadata.component_id] = metadata
        
        # Index by type
        if metadata.component_type not in self.by_type:
            self.by_type[metadata.component_type] = []
        self.by_type[metadata.component_type].append(metadata.component_id)
        
        # Index by interfaces
        for interface in metadata.interfaces:
            if interface not in self.by_interface:
                self.by_interface[interface] = []
            self.by_interface[interface].append(metadata.component_id)
        
        # Index by tags
        for tag in metadata.tags:
            if tag not in self.by_tag:
                self.by_tag[tag] = []
            self.by_tag[tag].append(metadata.component_id)
        
        logger.debug(f"Registered component: {metadata.component_id}")
    
    def unregister(self, component_id: str) -> None:
        """Unregister a component"""
        if component_id not in self.components:
            return
        
        metadata = self.components[component_id]
        
        # Remove from indices
        if metadata.component_type in self.by_type:
            self.by_type[metadata.component_type].remove(component_id)
        
        for interface in metadata.interfaces:
            if interface in self.by_interface:
                self.by_interface[interface].remove(component_id)
        
        for tag in metadata.tags:
            if tag in self.by_tag:
                self.by_tag[tag].remove(component_id)
        
        del self.components[component_id]
    
    def get(self, component_id: str) -> Optional[ComponentMetadata]:
        """Get component by ID"""
        return self.components.get(component_id)
    
    def find_by_type(self, component_type: Type) -> List[ComponentMetadata]:
        """Find components by type"""
        ids = self.by_type.get(component_type, [])
        return [self.components[cid] for cid in ids]
    
    def find_by_interface(self, interface: Type) -> List[ComponentMetadata]:
        """Find components implementing interface"""
        ids = self.by_interface.get(interface, [])
        return [self.components[cid] for cid in ids]
    
    def find_by_tag(self, tag: str) -> List[ComponentMetadata]:
        """Find components by tag"""
        ids = self.by_tag.get(tag, [])
        return [self.components[cid] for cid in ids]
    
    def get_all(self) -> List[ComponentMetadata]:
        """Get all components"""
        return list(self.components.values())


class DependencyResolver:
    """
    Resolves component dependencies and detects cycles
    """
    
    def __init__(self, registry: ComponentRegistry):
        self.registry = registry
    
    def resolve_order(self) -> List[str]:
        """Resolve initialization order using topological sort"""
        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        in_degree: Dict[str, int] = {}
        
        for component_id, metadata in self.registry.components.items():
            if component_id not in graph:
                graph[component_id] = set()
                in_degree[component_id] = 0
            
            for dep in metadata.dependencies:
                if dep not in graph:
                    graph[dep] = set()
                    in_degree[dep] = 0
                
                graph[dep].add(component_id)
                in_degree[component_id] = in_degree.get(component_id, 0) + 1
        
        # Topological sort (Kahn's algorithm)
        queue = [cid for cid, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph.get(current, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(self.registry.components):
            cycle = self._find_cycle(graph)
            raise ValueError(f"Circular dependency detected: {' -> '.join(cycle)}")
        
        return result
    
    def _find_cycle(self, graph: Dict[str, Set[str]]) -> List[str]:
        """Find a cycle in the dependency graph"""
        visited = set()
        path = []
        
        def dfs(node: str) -> Optional[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, set()):
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            
            path.pop()
            return None
        
        for node in graph:
            cycle = dfs(node)
            if cycle:
                return cycle
        
        return []
    
    def get_dependencies(self, component_id: str) -> List[ComponentMetadata]:
        """Get all dependencies of a component"""
        metadata = self.registry.get(component_id)
        if not metadata:
            return []
        
        deps = []
        for dep_id in metadata.dependencies:
            dep_metadata = self.registry.get(dep_id)
            if dep_metadata:
                deps.append(dep_metadata)
        
        return deps
    
    def get_dependents(self, component_id: str) -> List[ComponentMetadata]:
        """Get all components that depend on this one"""
        dependents = []
        for cid, metadata in self.registry.components.items():
            if component_id in metadata.dependencies:
                dependents.append(metadata)
        return dependents


class ComponentScanner:
    """
    Scans directories for components to auto-register
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.scanned_modules: Set[str] = set()
    
    def scan(self, package_name: str = "trading_bot") -> List[ComponentMetadata]:
        """Scan package for components"""
        discovered = []
        
        package_path = self.base_path / package_name.replace('.', os.sep)
        if not package_path.exists():
            logger.warning(f"Package path not found: {package_path}")
            return discovered
        
        for py_file in package_path.rglob("*.py"):
            if py_file.name.startswith('_'):
                continue
            
            # Convert path to module name
            relative_path = py_file.relative_to(self.base_path)
            module_name = str(relative_path).replace(os.sep, '.').replace('.py', '')
            
            if module_name in self.scanned_modules:
                continue
            
            try:
                components = self._scan_module(module_name)
                discovered.extend(components)
                self.scanned_modules.add(module_name)
            except Exception as e:
                logger.debug(f"Could not scan module {module_name}: {e}")
        
        logger.info(f"Discovered {len(discovered)} components")
        return discovered
    
    def _scan_module(self, module_name: str) -> List[ComponentMetadata]:
        """Scan a single module for components"""
        components = []
        
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return components
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a component (has specific markers)
            if self._is_component(obj):
                metadata = self._extract_metadata(obj, module_name)
                if metadata:
                    components.append(metadata)
        
        return components
    
    def _is_component(self, cls: Type) -> bool:
        """Check if class is a component"""
        # Check for ComponentInterface
        if issubclass(cls, ComponentInterface) and cls != ComponentInterface:
            return True
        
        # Check for component marker attributes
        if hasattr(cls, '__component__') and cls.__component__:
            return True
        
        # Check for specific naming patterns
        component_suffixes = ['Strategy', 'Manager', 'Engine', 'Service', 'Handler', 'Processor']
        for suffix in component_suffixes:
            if cls.__name__.endswith(suffix):
                return True
        
        return False
    
    def _extract_metadata(self, cls: Type, module_name: str) -> Optional[ComponentMetadata]:
        """Extract component metadata from class"""
        try:
            # Get component ID
            component_id = getattr(cls, '__component_id__', None)
            if not component_id:
                component_id = f"{module_name}.{cls.__name__}"
            
            # Get interfaces
            interfaces = [base for base in cls.__mro__ if base not in (object, cls)]
            
            # Get dependencies from constructor
            dependencies = []
            if hasattr(cls, '__init__'):
                sig = inspect.signature(cls.__init__)
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    if param.annotation != inspect.Parameter.empty:
                        # This is a typed dependency
                        dep_type_name = param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)
                        dependencies.append(dep_type_name)
            
            # Get scope
            scope = getattr(cls, '__scope__', ComponentScope.SINGLETON)
            
            # Get tags
            tags = set(getattr(cls, '__tags__', []))
            
            return ComponentMetadata(
                component_id=component_id,
                component_type=cls,
                interfaces=interfaces,
                scope=scope,
                wiring_mode=WiringMode.CONSTRUCTOR,
                dependencies=dependencies,
                provides=[cls.__name__],
                tags=tags,
            )
        except Exception as e:
            logger.debug(f"Could not extract metadata from {cls}: {e}")
            return None


class AutoWiringContainer:
    """
    Dependency Injection Container with Auto-Wiring
    
    Manages component lifecycle and dependency injection.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.registry = ComponentRegistry()
        self.resolver = DependencyResolver(self.registry)
        self.scanner = ComponentScanner(self.config.get('base_path', '.'))
        
        # Instance cache for singletons
        self.instances: Dict[str, Any] = {}
        
        # Initialization state
        self.initialized = False
        self.initialization_order: List[str] = []
        
        logger.info("AutoWiringContainer initialized")
    
    def register(
        self,
        component_type: Type,
        component_id: Optional[str] = None,
        scope: ComponentScope = ComponentScope.SINGLETON,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """Manually register a component"""
        if not component_id:
            component_id = f"{component_type.__module__}.{component_type.__name__}"
        
        metadata = ComponentMetadata(
            component_id=component_id,
            component_type=component_type,
            interfaces=[],
            scope=scope,
            wiring_mode=WiringMode.CONSTRUCTOR,
            dependencies=[],
            provides=[component_type.__name__],
            tags=tags or set(),
        )
        
        self.registry.register(metadata)
    
    def register_instance(self, component_id: str, instance: Any) -> None:
        """Register an existing instance"""
        metadata = ComponentMetadata(
            component_id=component_id,
            component_type=type(instance),
            interfaces=[],
            scope=ComponentScope.SINGLETON,
            wiring_mode=WiringMode.CONSTRUCTOR,
            dependencies=[],
            provides=[type(instance).__name__],
            state=ComponentState.READY,
            instance=instance,
            created_at=datetime.utcnow(),
        )
        
        self.registry.register(metadata)
        self.instances[component_id] = instance
    
    def scan_and_register(self, package_name: str = "trading_bot") -> int:
        """Scan package and register discovered components"""
        discovered = self.scanner.scan(package_name)
        
        for metadata in discovered:
            self.registry.register(metadata)
        
        return len(discovered)
    
    async def initialize(self) -> None:
        """Initialize all components in dependency order"""
        if self.initialized:
            return
        
        try:
            # Resolve initialization order
            self.initialization_order = self.resolver.resolve_order()
            
            # Initialize in order
            for component_id in self.initialization_order:
                metadata = self.registry.get(component_id)
                if metadata and metadata.auto_start:
                    await self._initialize_component(metadata)
            
            self.initialized = True
            logger.info(f"Initialized {len(self.initialization_order)} components")
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise
    
    async def _initialize_component(self, metadata: ComponentMetadata) -> Any:
        """Initialize a single component"""
        if metadata.state == ComponentState.READY:
            return metadata.instance
        
        if metadata.component_id in self.instances:
            return self.instances[metadata.component_id]
        
        metadata.state = ComponentState.INITIALIZING
        
        try:
            # Resolve dependencies
            deps = {}
            for dep_id in metadata.dependencies:
                dep_metadata = self.registry.get(dep_id)
                if dep_metadata:
                    dep_instance = await self._initialize_component(dep_metadata)
                    deps[dep_id] = dep_instance
            
            # Create instance
            instance = self._create_instance(metadata, deps)
            
            # Call lifecycle hooks
            if hasattr(instance, 'on_wire'):
                instance.on_wire()
            
            if hasattr(instance, 'on_start'):
                result = instance.on_start()
                if asyncio.iscoroutine(result):
                    await result
            
            # Store instance
            if metadata.scope == ComponentScope.SINGLETON:
                self.instances[metadata.component_id] = instance
            
            metadata.instance = instance
            metadata.state = ComponentState.READY
            metadata.created_at = datetime.utcnow()
            
            logger.debug(f"Initialized component: {metadata.component_id}")
            return instance
            
        except Exception as e:
            metadata.state = ComponentState.FAILED
            metadata.error = str(e)
            logger.error(f"Failed to initialize {metadata.component_id}: {e}")
            raise
    
    def _create_instance(self, metadata: ComponentMetadata, deps: Dict[str, Any]) -> Any:
        """Create component instance with dependencies"""
        cls = metadata.component_type
        
        # Get constructor signature
        sig = inspect.signature(cls.__init__)
        kwargs = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Try to find matching dependency
            for dep_id, dep_instance in deps.items():
                if dep_id.endswith(param_name) or param_name in dep_id.lower():
                    kwargs[param_name] = dep_instance
                    break
            
            # Use default if available
            if param_name not in kwargs and param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
        
        return cls(**kwargs)
    
    def get(self, component_id: str) -> Optional[Any]:
        """Get component instance by ID"""
        if component_id in self.instances:
            return self.instances[component_id]
        
        metadata = self.registry.get(component_id)
        if metadata and metadata.instance:
            return metadata.instance
        
        return None
    
    def get_by_type(self, component_type: Type[T]) -> Optional[T]:
        """Get component instance by type"""
        components = self.registry.find_by_type(component_type)
        if components and components[0].instance:
            return components[0].instance
        return None
    
    def get_all_by_interface(self, interface: Type[T]) -> List[T]:
        """Get all components implementing interface"""
        components = self.registry.find_by_interface(interface)
        return [c.instance for c in components if c.instance]
    
    def get_all_by_tag(self, tag: str) -> List[Any]:
        """Get all components with tag"""
        components = self.registry.find_by_tag(tag)
        return [c.instance for c in components if c.instance]
    
    async def shutdown(self) -> None:
        """Shutdown all components in reverse order"""
        for component_id in reversed(self.initialization_order):
            metadata = self.registry.get(component_id)
            if metadata and metadata.instance:
                try:
                    if hasattr(metadata.instance, 'on_stop'):
                        result = metadata.instance.on_stop()
                        if asyncio.iscoroutine(result):
                            await result
                    
                    metadata.state = ComponentState.DISPOSED
                except Exception as e:
                    logger.error(f"Error stopping {component_id}: {e}")
        
        self.instances.clear()
        self.initialized = False
        logger.info("Container shutdown complete")
    
    async def hot_swap(self, component_id: str, new_type: Type) -> bool:
        """Hot-swap a component with a new implementation"""
        old_metadata = self.registry.get(component_id)
        if not old_metadata:
            return False
        
        try:
            # Stop old instance
            if old_metadata.instance and hasattr(old_metadata.instance, 'on_stop'):
                result = old_metadata.instance.on_stop()
                if asyncio.iscoroutine(result):
                    await result
            
            # Create new metadata
            new_metadata = ComponentMetadata(
                component_id=component_id,
                component_type=new_type,
                interfaces=old_metadata.interfaces,
                scope=old_metadata.scope,
                wiring_mode=old_metadata.wiring_mode,
                dependencies=old_metadata.dependencies,
                provides=old_metadata.provides,
                tags=old_metadata.tags,
            )
            
            # Replace in registry
            self.registry.unregister(component_id)
            self.registry.register(new_metadata)
            
            # Initialize new instance
            if component_id in self.instances:
                del self.instances[component_id]
            
            await self._initialize_component(new_metadata)
            
            logger.info(f"Hot-swapped component: {component_id}")
            return True
            
        except Exception as e:
            logger.error(f"Hot-swap failed for {component_id}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get container status"""
        components_by_state = {}
        for state in ComponentState:
            components_by_state[state.value] = len([
                c for c in self.registry.get_all() if c.state == state
            ])
        
        return {
            'initialized': self.initialized,
            'total_components': len(self.registry.components),
            'instances': len(self.instances),
            'components_by_state': components_by_state,
            'initialization_order': self.initialization_order[:10],  # First 10
        }


# Decorators for component marking
def component(
    component_id: Optional[str] = None,
    scope: ComponentScope = ComponentScope.SINGLETON,
    tags: Optional[List[str]] = None,
):
    """Decorator to mark a class as a component"""
    def decorator(cls):
        cls.__component__ = True
        cls.__component_id__ = component_id
        cls.__scope__ = scope
        cls.__tags__ = tags or []
        return cls
    return decorator


def autowired(func):
    """Decorator to mark a method for autowiring"""
    func.__autowired__ = True
    return func


# Factory function
def create_autowiring_container(
    base_path: str = ".",
    auto_scan: bool = True,
    config: Optional[Dict[str, Any]] = None
) -> AutoWiringContainer:
    """Create and optionally initialize autowiring container"""
    config = config or {}
    config['base_path'] = base_path
    
    container = AutoWiringContainer(config)
    
    if auto_scan:
        container.scan_and_register()
    
    return container
