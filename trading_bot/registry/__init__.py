"""
Module Registry System
Centralized registry for all trading bot modules with dynamic discovery and dependency management.
"""

from .module_registry import ModuleRegistry, ModuleInfo, ModuleCategory
from .service_locator import ServiceLocator
from .dependency_resolver import DependencyResolver

__all__ = [
    'ModuleRegistry',
    'ModuleInfo', 
    'ModuleCategory',
    'ServiceLocator',
    'DependencyResolver'
]

# Global registry instance
_registry = None

def get_registry() -> ModuleRegistry:
    """Get the global module registry instance."""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry

def initialize_registry():
    """Initialize the global registry with all modules."""
    registry = get_registry()
    registry.discover_modules()
    registry.resolve_dependencies()
    return registry
