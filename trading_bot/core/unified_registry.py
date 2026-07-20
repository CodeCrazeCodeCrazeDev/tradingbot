"""
Unified Component Registry - UCA-2026 Core Component
==================================================

Exactly one authoritative registry for all system components (Agents, Tools, Services, Models).
Implements the Singleton pattern to prevent architectural regression.
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)

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
        self._initialized = True
        logger.info("UnifiedComponentRegistry initialized as singleton")

    def register(
        self,
        name: str,
        component: Any,
        component_type: str,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a component with the system.
        """
        # Architectural drift prevention
        if name.endswith("Registry") and name != "UnifiedComponentRegistry":
            raise ValueError(f"Unauthorized registry registration: {name}. Only UnifiedComponentRegistry is allowed.")
        if name.endswith("Orchestrator") and name not in ["AIPOrchestrator", "SimulationOrchestrator"]:
            raise ValueError(f"Unauthorized orchestrator: {name}. All orchestration must route through CognitiveSystemController or authorized Ontologies.")

        if name in self._components:
            logger.warning(f"Component '{name}' already registered. Overwriting.")

        self._components[name] = component
        self._metadata[name] = {
            "type": component_type,
            "metadata": metadata or {}
        }
        self._dependencies[name] = dependencies or []
        logger.debug(f"Registered {component_type}: {name}")

    def get(self, name: str) -> Any:
        """
        Retrieve a component by name.
        """
        if name not in self._components:
            raise KeyError(f"Component '{name}' not found in registry")
        return self._components[name]

    def get_by_type(self, component_type: str) -> List[Any]:
        """
        Retrieve all components of a specific type.
        """
        return [
            self._components[name]
            for name, meta in self._metadata.items()
            if meta["type"] == component_type
        ]

    def list_components(self) -> List[Dict[str, Any]]:
        """
        List all registered components with their metadata.
        """
        return [
            {
                "name": name,
                "type": meta["type"],
                "dependencies": self._dependencies.get(name, []),
                "metadata": meta["metadata"]
            }
            for name, meta in self._metadata.items()
        ]

    def clear(self):
        """
        Clear the registry (mainly for testing).
        """
        self._components.clear()
        self._metadata.clear()
        self._dependencies.clear()
        logger.info("UnifiedComponentRegistry cleared")

    def unregister(self, name: str):
        """
        Unregister a component.
        """
        if name in self._components:
            del self._components[name]
            del self._metadata[name]
            if name in self._dependencies:
                del self._dependencies[name]
            logger.info(f"Unregistered component: {name}")

# Global access point
registry = UnifiedComponentRegistry()
