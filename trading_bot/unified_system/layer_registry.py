"""
Layer Registry - Central registry for all architecture layers

Manages registration, discovery, and lifecycle of all 11 layers.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime

from .unified_types import LayerStatus, LayerMetrics
from .layer_interfaces import ILayer

logger = logging.getLogger(__name__)


@dataclass
class LayerInfo:
    """Information about a registered layer"""
    layer_id: int
    layer_name: str
    layer_class: Type[ILayer]
    instance: Optional[ILayer] = None
    status: LayerStatus = LayerStatus.UNINITIALIZED
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[int] = field(default_factory=list)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    initialized_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    metrics: Optional[LayerMetrics] = None
    enabled: bool = True
    priority: int = 0


class LayerRegistry:
    """
    Central registry for all architecture layers
    
    Manages the 11-layer architecture:
    - Layer 0: Infrastructure
    - Layer 1: Observability
    - Layer 2: Connectivity
    - Layer 3: Data Foundation
    - Layer 4: Intelligence
    - Layer 5: Signal Generation
    - Layer 6: Risk & Safety
    - Layer 7: Decision Verification
    - Layer 8: Execution
    - Layer 9: Orchestration
    - Layer 10: Governance
    """
    
    # Layer names for reference
    LAYER_NAMES = {
        0: "Infrastructure",
        1: "Observability",
        2: "Connectivity",
        3: "DataFoundation",
        4: "Intelligence",
        5: "SignalGeneration",
        6: "RiskSafety",
        7: "DecisionVerification",
        8: "Execution",
        9: "Orchestration",
        10: "Governance",
    }
    
    def __init__(self):
        self._layers: Dict[int, LayerInfo] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        
    def register(
        self,
        layer_id: int,
        layer_class: Type[ILayer],
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 0,
    ) -> bool:
        """
        Register a layer implementation
        
        Args:
            layer_id: Layer number (0-10)
            layer_class: Class implementing the layer interface
            config: Layer configuration
            enabled: Whether layer is enabled
            priority: Initialization priority within layer
            
        Returns:
            True if registration successful
        """
        if layer_id < 0 or layer_id > 10:
            logger.error(f"Invalid layer ID: {layer_id}. Must be 0-10.")
            return False
        
        layer_name = self.LAYER_NAMES.get(layer_id, f"Layer{layer_id}")
        
        if layer_id in self._layers:
            logger.warning(f"Layer {layer_id} ({layer_name}) already registered, updating")
        
        self._layers[layer_id] = LayerInfo(
            layer_id=layer_id,
            layer_name=layer_name,
            layer_class=layer_class,
            config=config or {},
            enabled=enabled,
            priority=priority,
        )
        
        logger.info(f"Registered layer {layer_id}: {layer_name}")
        return True
    
    def unregister(self, layer_id: int) -> bool:
        """Unregister a layer"""
        if layer_id in self._layers:
            del self._layers[layer_id]
            logger.info(f"Unregistered layer {layer_id}")
            return True
        return False
    
    def get(self, layer_id: int) -> Optional[ILayer]:
        """Get a layer instance"""
        info = self._layers.get(layer_id)
        return info.instance if info else None
    
    def get_info(self, layer_id: int) -> Optional[LayerInfo]:
        """Get layer info"""
        return self._layers.get(layer_id)
    
    def get_all(self) -> Dict[int, ILayer]:
        """Get all layer instances"""
        return {
            layer_id: info.instance
            for layer_id, info in self._layers.items()
            if info.instance is not None
        }
    
    def list_layers(self) -> List[int]:
        """List all registered layer IDs"""
        return sorted(self._layers.keys())
    
    def get_status(self) -> Dict[int, LayerStatus]:
        """Get status of all layers"""
        return {
            layer_id: info.status
            for layer_id, info in self._layers.items()
        }
    
    async def initialize_all(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize all registered layers in order
        
        Args:
            config: Global configuration to merge with layer configs
            
        Returns:
            True if all layers initialized successfully
        """
        async with self._lock:
            logger.info("=" * 60)
            logger.info("INITIALIZING ALL LAYERS")
            logger.info("=" * 60)
            
            # Sort by layer ID (lower layers first)
            sorted_layers = sorted(self._layers.items(), key=lambda x: x[0])
            
            for layer_id, info in sorted_layers:
                if not info.enabled:
                    logger.info(f"Layer {layer_id} ({info.layer_name}) is disabled, skipping")
                    continue
                try:
                
                    logger.info(f"\n[Layer {layer_id}] Initializing {info.layer_name}...")
                    
                    # Create instance
                    instance = info.layer_class()
                    
                    # Merge configs
                    layer_config = {**(config or {}), **info.config}
                    
                    # Initialize
                    success = await instance.initialize(layer_config)
                    
                    if success:
                        info.instance = instance
                        info.status = LayerStatus.READY
                        info.initialized_at = datetime.utcnow()
                        logger.info(f"[Layer {layer_id}] {info.layer_name} initialized successfully")
                    else:
                        info.status = LayerStatus.ERROR
                        logger.error(f"[Layer {layer_id}] {info.layer_name} initialization failed")
                        return False
                        
                except Exception as e:
                    info.status = LayerStatus.ERROR
                    logger.error(f"[Layer {layer_id}] Error initializing {info.layer_name}: {e}")
                    return False
            
            self._initialized = True
            logger.info("\n" + "=" * 60)
            logger.info("ALL LAYERS INITIALIZED SUCCESSFULLY")
            logger.info("=" * 60)
            return True
    
    async def start_all(self) -> bool:
        """Start all initialized layers"""
        async with self._lock:
            logger.info("Starting all layers...")
            
            sorted_layers = sorted(self._layers.items(), key=lambda x: x[0])
            
            for layer_id, info in sorted_layers:
                if not info.enabled or info.instance is None:
                    continue
                try:
                
                    success = await info.instance.start()
                    if success:
                        info.status = LayerStatus.ACTIVE
                        info.started_at = datetime.utcnow()
                        logger.info(f"[Layer {layer_id}] {info.layer_name} started")
                    else:
                        logger.error(f"[Layer {layer_id}] {info.layer_name} failed to start")
                        return False
                except Exception as e:
                    logger.error(f"[Layer {layer_id}] Error starting {info.layer_name}: {e}")
                    return False
            
            return True
    
    async def stop_all(self) -> bool:
        """Stop all layers in reverse order"""
        async with self._lock:
            logger.info("Stopping all layers...")
            
            # Stop in reverse order (higher layers first)
            sorted_layers = sorted(self._layers.items(), key=lambda x: x[0], reverse=True)
            
            for layer_id, info in sorted_layers:
                if info.instance is None:
                    continue
                try:
                
                    await info.instance.stop()
                    info.status = LayerStatus.DISABLED
                    logger.info(f"[Layer {layer_id}] {info.layer_name} stopped")
                except Exception as e:
                    logger.error(f"[Layer {layer_id}] Error stopping {info.layer_name}: {e}")
            
            return True
    
    async def health_check_all(self) -> Dict[int, LayerMetrics]:
        """Perform health check on all layers"""
        results = {}
        
        for layer_id, info in self._layers.items():
            if info.instance is None:
                continue
            try:
            
                metrics = await info.instance.health_check()
                info.metrics = metrics
                results[layer_id] = metrics
            except Exception as e:
                logger.error(f"[Layer {layer_id}] Health check failed: {e}")
                results[layer_id] = LayerMetrics(
                    layer_name=info.layer_name,
                    status=LayerStatus.ERROR,
                )
        
        return results
    
    def is_initialized(self) -> bool:
        """Check if all layers are initialized"""
        return self._initialized
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all layers"""
        return {
            "total_layers": len(self._layers),
            "initialized": self._initialized,
            "layers": {
                layer_id: {
                    "name": info.layer_name,
                    "status": info.status.value,
                    "enabled": info.enabled,
                    "initialized_at": info.initialized_at.isoformat() if info.initialized_at else None,
                }
                for layer_id, info in sorted(self._layers.items())
            }
        }


# Singleton instance
_registry: Optional[LayerRegistry] = None


def get_layer_registry() -> LayerRegistry:
    """Get or create the layer registry singleton"""
    global _registry
    if _registry is None:
        _registry = LayerRegistry()
    return _registry
