"""
AlphaAlgo Core - Main Integration Module

Integrates all layers of the capital governance system:
- Layer 0: Market Physics Filter
- Layer 1: Strategy Zoo
- Layer 2: Assumption Decompiler
- Layer 3: Regime Hostility Engine
- Layer 4: Exposure Controller
- Layer 5: Anti-Learning Firewall
- Layer 6: Continuous Validity Monitor

This is the main entry point for the AlphaAlgo Core capital governance system.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from .capital_governance import (
    CapitalGovernanceSystem,
    CapitalGovernanceResult,
    MarketPhysicsResult,
    StrategyZooResult,
    AssumptionDecompilerResult,
    RegimeHostilityResult,
    ExposureControllerResult,
    AntiLearningResult,
    ValidationMonitorResult
)

from .market_physics_filter import MarketPhysicsFilter
from .strategy_zoo import StrategyZoo
from .assumption_decompiler import AssumptionDecompiler
from .regime_hostility_engine import RegimeHostilityEngine
from .exposure_controller import ExposureController
from .anti_learning_firewall import AntiLearningFirewall
from .continuous_validity_monitor import ContinuousValidityMonitor

logger = logging.getLogger(__name__)


class AlphaAlgoCore:
    """
    AlphaAlgo Core - Capital Governance System
    
    A survival-first capital governance system that enforces strict rules
    regarding market tradability, strategy assumptions, adversarial testing,
    exposure control, anti-learning, and continuous validity monitoring.
    
    This system prioritizes survival over performance and operates as a gated
    control system with irreversible barriers.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the AlphaAlgo Core system.
        
        Args:
            config: Configuration dictionary for the system and its layers
        """
        self.config = config or {}
        
        # Create the capital governance system
        self.governance = CapitalGovernanceSystem(self.config)
        
        # Initialize all layers
        self._initialize_layers()
        
        # Strategy registry
        self.strategies = {}
        
        logger.info("AlphaAlgo Core initialized")
    
    def _initialize_layers(self):
        """Initialize all layers of the capital governance system"""
        # Layer 0: Market Physics Filter
        market_physics_config = self.config.get("market_physics_filter", {})
        self.market_physics_filter = MarketPhysicsFilter(market_physics_config)
        self.governance.add_layer("market_physics_filter", self.market_physics_filter)
        
        # Layer 1: Strategy Zoo
        strategy_zoo_config = self.config.get("strategy_zoo", {})
        self.strategy_zoo = StrategyZoo(strategy_zoo_config)
        self.governance.add_layer("strategy_zoo", self.strategy_zoo)
        
        # Layer 2: Assumption Decompiler
        assumption_decompiler_config = self.config.get("assumption_decompiler", {})
        self.assumption_decompiler = AssumptionDecompiler(assumption_decompiler_config)
        self.governance.add_layer("assumption_decompiler", self.assumption_decompiler)
        
        # Layer 3: Regime Hostility Engine
        regime_hostility_config = self.config.get("regime_hostility_engine", {})
        self.regime_hostility_engine = RegimeHostilityEngine(regime_hostility_config)
        self.governance.add_layer("regime_hostility_engine", self.regime_hostility_engine)
        
        # Layer 4: Exposure Controller
        exposure_controller_config = self.config.get("exposure_controller", {})
        self.exposure_controller = ExposureController(exposure_controller_config)
        self.governance.add_layer("exposure_controller", self.exposure_controller)
        
        # Layer 5: Anti-Learning Firewall
        anti_learning_config = self.config.get("anti_learning_firewall", {})
        self.anti_learning_firewall = AntiLearningFirewall(anti_learning_config)
        self.governance.add_layer("anti_learning_firewall", self.anti_learning_firewall)
        
        # Layer 6: Continuous Validity Monitor
        validation_monitor_config = self.config.get("validation_monitor", {})
        self.validation_monitor = ContinuousValidityMonitor(validation_monitor_config)
        self.governance.add_layer("validation_monitor", self.validation_monitor)
    
    def register_strategy(self, strategy_id: str, strategy_config: Dict[str, Any]) -> bool:
        """
        Register a strategy with the AlphaAlgo Core system.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_config: Strategy configuration including assumptions
            
        Returns:
            bool: True if registration was successful
        """
        # Register with Strategy Zoo
        if not self.strategy_zoo.register_strategy(strategy_id, strategy_config):
            logger.warning(f"Failed to register strategy {strategy_id} with Strategy Zoo")
            return False
        
        # Store strategy configuration
        self.strategies[strategy_id] = strategy_config
        logger.info(f"Strategy {strategy_id} registered with AlphaAlgo Core")
        return True
    
    async def evaluate_tradability(
        self,
        strategy_id: str,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> CapitalGovernanceResult:
        """
        Evaluate if a strategy can trade and what exposure is permitted.
        
        This is the main entry point for the capital governance system.
        
        Args:
            strategy_id: Unique identifier for the strategy
            symbol: The market symbol
            market_data: Current market data
            
        Returns:
            CapitalGovernanceResult with tradability determination
        """
        # Check if strategy is registered
        if strategy_id not in self.strategies:
            logger.warning(f"Strategy {strategy_id} not registered with AlphaAlgo Core")
            return CapitalGovernanceResult(
                strategy_id=strategy_id,
                symbol=symbol,
                is_tradable=False,
                max_exposure=0.0,
                reason="Strategy not registered with AlphaAlgo Core"
            )
        
        # Get strategy configuration
        strategy_config = self.strategies[strategy_id]
        
        # Evaluate tradability through the governance system
        result = await self.governance.evaluate_tradability(
            strategy_id=strategy_id,
            symbol=symbol,
            market_data=market_data,
            strategy_config=strategy_config
        )
        
        return result
    
    async def process_market_event(self, event: Dict[str, Any]) -> bool:
        """
        Process a market event through the anti-learning firewall.
        
        Args:
            event: Market event data
            
        Returns:
            bool: True if the event should be included in learning, False if it should be excluded
        """
        return await self.governance.process_market_event(event)
    
    async def update_behavior(
        self,
        strategy_id: str,
        behavior_data: Dict[str, Any]
    ) -> None:
        """
        Update behavior data for continuous validity monitoring.
        
        Args:
            strategy_id: Unique identifier for the strategy
            behavior_data: Dictionary of behavior metrics
        """
        self.validation_monitor.update_behavior_history(strategy_id, behavior_data)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the AlphaAlgo Core system.
        
        Returns:
            Dict with system status information
        """
        return {
            "governance": self.governance.get_status(),
            "registered_strategies": list(self.strategies.keys()),
            "timestamp": time.time()
        }


# Factory function for creating AlphaAlgo Core instances
def create_alphaalgo_core(config_path: Optional[str] = None) -> AlphaAlgoCore:
    """
    Create an AlphaAlgo Core instance with configuration from a file.
    
    Args:
        config_path: Path to configuration file (JSON)
        
    Returns:
        AlphaAlgoCore instance
    """
    config = {}
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.info("Using default configuration")
    
    return AlphaAlgoCore(config)
