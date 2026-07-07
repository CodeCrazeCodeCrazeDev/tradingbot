"""
UCA-2026 Core Integration & Main Service Registry
================================================

Synthesizes all core components into the Unified Registry.
"""

import logging
from typing import Any, Dict

from .unified_registry import registry
from .unified_event_bus import decision_bus
from .immutable_shield import shield
from .hms.memory import HierarchicalMemorySystem
from .csc.controller import CognitiveSystemController
from ..world_model.v3_core import WorldModelV3
from ..world_model.imagination import FutureSimulator, PlanningEngine
from ..world_model.causal_model import StructuralCausalModel

logger = logging.getLogger(__name__)

def initialize_uca_system(config: Dict[str, Any]):
    """
    Authoritative system instantiation and registration.
    """
    logger.info("UCA: Initializing Unified Intelligence System")

    # 1. Memory & State
    hms = HierarchicalMemorySystem()
    registry.register("hms", hms, "Core")

    # 2. Intelligence Modules
    # Note: asset_dims should come from config
    asset_dims = config.get("asset_dims", {"FX": 64})
    world_model = WorldModelV3(asset_dims=asset_dims)
    registry.register("world_model", world_model, "Intelligence")
    
    causal_engine = StructuralCausalModel()
    registry.register("causal_engine", causal_engine, "Intelligence")

    # 3. Simulation & Planning
    simulator = FutureSimulator(world_model)
    registry.register("simulator", simulator, "Intelligence")
    
    planner = PlanningEngine(simulator, causal_engine)
    registry.register("planner", planner, "Intelligence")

    # 4. Cognitive Controller
    csc = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)
    registry.register("csc", csc, "Controller")

    # 5. Infrastructure
    registry.register("decision_bus", decision_bus, "Infrastructure")
    registry.register("shield", shield, "Governance")

    logger.info("UCA: All components successfully integrated into Unified Registry")
    return csc
