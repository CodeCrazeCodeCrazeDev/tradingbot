"""
AlphaAlgo Core - Capital Governance System

A market survival and capital governance system focused on preventing capital ruin.
This system operates as a gated control system with irreversible barriers,
prioritizing survival over performance.

The system enforces strict rules regarding market tradability, strategy assumptions,
adversarial testing, exposure control, anti-learning, and continuous validity monitoring.

ABSOLUTE DIRECTIVES (NON-NEGOTIABLE):
- NOT decide what to trade
- ONLY decide what exposure is permitted
- Assume being wrong by default
- Actively try to disprove all strategies
- Prioritize survival over performance
- Reject learning that weakens generalization
- Block trades when uncertainty is unbounded
- Never optimize returns at the expense of constraints
- If a conflict exists between profit and constraint integrity, constraints win automatically
"""

import asyncio
import enum
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class CapitalGovernanceError(Exception):
    """Base exception for all capital governance errors"""
    pass


class ConstraintViolationError(CapitalGovernanceError):
    """Raised when a constraint is violated"""
    pass


class MarketPhysicsError(CapitalGovernanceError):
    """Raised when market physics are violated"""
    pass


class AssumptionViolationError(CapitalGovernanceError):
    """Raised when strategy assumptions are violated"""
    pass


class RegimeHostilityError(CapitalGovernanceError):
    """Raised when regime is hostile to strategy"""
    pass


class ExposureError(CapitalGovernanceError):
    """Raised when exposure constraints are violated"""
    pass


class ValidationError(CapitalGovernanceError):
    """Raised when validation fails"""
    pass


class MarketStructureState(Enum):
    """Market structure state"""
    NORMAL = "normal"
    DEGRADED = "degraded"
    UNDEFINED = "undefined"


class StrategyState(Enum):
    """Strategy state"""
    VALID = "valid"
    INVALID = "invalid"
    FRAGILE = "fragile"
    UNKNOWN = "unknown"


class RegimeState(Enum):
    """Market regime state"""
    NORMAL = "normal"
    HOSTILE = "hostile"
    EXTREME = "extreme"
    UNKNOWN = "unknown"


class ExposureState(Enum):
    """Exposure state"""
    NORMAL = "normal"
    THROTTLED = "throttled"
    DECAYING = "decaying"
    ZERO = "zero"


class ValidationState(Enum):
    """Validation state"""
    VALID = "valid"
    INVALID = "invalid"
    FROZEN = "frozen"
    UNKNOWN = "unknown"


@dataclass
class MarketPhysicsResult:
    """Result from market physics filter"""
    state: MarketStructureState
    is_tradable: bool
    reason: str
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class StrategyAssumption:
    """Strategy assumption"""
    name: str
    description: str
    current_value: float
    threshold: float
    is_valid: bool
    stress_score: float  # 0-100, higher is more stressed


@dataclass
class StrategyZooResult:
    """Result from strategy zoo"""
    strategy_id: str
    state: StrategyState
    assumptions: List[StrategyAssumption]
    is_valid: bool
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class AssumptionDecompilerResult:
    """Result from assumption decompiler"""
    strategy_id: str
    hidden_assumptions: List[StrategyAssumption]
    violated_assumptions: List[StrategyAssumption]
    assumption_stress: float  # 0-100, higher is more stressed
    is_valid: bool
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class HostileCondition:
    """Hostile market condition"""
    name: str
    description: str
    probability: float  # 0-1
    impact: float  # 0-100, higher is more severe
    is_present: bool


@dataclass
class RegimeHostilityResult:
    """Result from regime hostility engine"""
    strategy_id: str
    hostile_conditions: List[HostileCondition]
    state: RegimeState
    is_fragile: bool
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExposureControllerResult:
    """Result from exposure controller"""
    strategy_id: str
    max_exposure: float  # 0-1
    state: ExposureState
    reason: str
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class AntiLearningResult:
    """Result from anti-learning firewall"""
    event_id: str
    is_extreme_event: bool
    should_exclude: bool
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ValidationMonitorResult:
    """Result from validation monitor"""
    strategy_id: str
    state: ValidationState
    deviation: float  # 0-100, higher is more deviated
    is_valid: bool
    reason: str
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class CapitalGovernanceResult:
    """Final result from capital governance system"""
    strategy_id: str
    symbol: str
    is_tradable: bool
    max_exposure: float  # 0-1
    reason: str
    market_physics: Optional[MarketPhysicsResult] = None
    strategy_zoo: Optional[StrategyZooResult] = None
    assumption_decompiler: Optional[AssumptionDecompilerResult] = None
    regime_hostility: Optional[RegimeHostilityResult] = None
    exposure_controller: Optional[ExposureControllerResult] = None
    validation_monitor: Optional[ValidationMonitorResult] = None
    timestamp: float = field(default_factory=time.time)


class GovernanceLayer(ABC):
    """Base class for all governance layers"""
    
    def __init__(self, name: str):
        try:
            self.name = name
            self.logger = logging.getLogger(f"alphaalgo.core.governance.{name}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Process data through this layer"""
        pass
    
    def log_decision(self, decision: Any, reason: str, level: str = "info"):
        """Log a decision made by this layer"""
        try:
            log_method = getattr(self.logger, level)
            log_method(f"[{self.name}] {reason}")
        except Exception as e:
            logger.error(f"Error in log_decision: {e}")
            raise


class CapitalGovernanceSystem:
    """
    AlphaAlgo Core Capital Governance System
    
    A gated control system with irreversible barriers that prioritizes survival over performance.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("alphaalgo.core.capital_governance")
        
            # Initialize layers
            self.layers = {}
        
            self.logger.info("Capital Governance System initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_layer(self, layer_id: str, layer: GovernanceLayer):
        """Add a governance layer"""
        try:
            self.layers[layer_id] = layer
            self.logger.info(f"Added governance layer: {layer_id}")
        except Exception as e:
            logger.error(f"Error in add_layer: {e}")
            raise
    
    async def evaluate_tradability(
        self,
        strategy_id: str,
        symbol: str,
        market_data: Dict[str, Any],
        strategy_config: Dict[str, Any]
    ) -> CapitalGovernanceResult:
        """
        Evaluate if a strategy can trade and what exposure is permitted.
        
        This is the main entry point for the capital governance system.
        """
        try:
            self.logger.info(f"Evaluating tradability for {strategy_id} on {symbol}")
        
            result = CapitalGovernanceResult(
                strategy_id=strategy_id,
                symbol=symbol,
                is_tradable=True,  # Default to True, layers will gate this
                max_exposure=0.0,  # Default to 0, will be set by exposure controller
                reason="Evaluation in progress"
            )
        
            # Layer 0: Market Physics Filter
            if "market_physics_filter" in self.layers:
                market_physics = await self.layers["market_physics_filter"].process(
                    symbol=symbol,
                    market_data=market_data
                )
                result.market_physics = market_physics
            
                if not market_physics.is_tradable:
                    result.is_tradable = False
                    result.max_exposure = 0.0
                    result.reason = f"Market physics filter: {market_physics.reason}"
                    return result
        
            # Layer 1: Strategy Zoo
            if "strategy_zoo" in self.layers:
                strategy_zoo = await self.layers["strategy_zoo"].process(
                    strategy_id=strategy_id,
                    strategy_config=strategy_config,
                    market_data=market_data
                )
                result.strategy_zoo = strategy_zoo
            
                if not strategy_zoo.is_valid:
                    result.is_tradable = False
                    result.max_exposure = 0.0
                    result.reason = f"Strategy zoo: {strategy_zoo.reason}"
                    return result
        
            # Layer 2: Assumption Decompiler
            if "assumption_decompiler" in self.layers:
                assumption_decompiler = await self.layers["assumption_decompiler"].process(
                    strategy_id=strategy_id,
                    strategy_config=strategy_config,
                    market_data=market_data
                )
                result.assumption_decompiler = assumption_decompiler
            
                if not assumption_decompiler.is_valid:
                    result.is_tradable = False
                    result.max_exposure = 0.0
                    result.reason = f"Assumption decompiler: {assumption_decompiler.reason}"
                    return result
        
            # Layer 3: Regime Hostility Engine
            if "regime_hostility_engine" in self.layers:
                regime_hostility = await self.layers["regime_hostility_engine"].process(
                    strategy_id=strategy_id,
                    strategy_config=strategy_config,
                    market_data=market_data
                )
                result.regime_hostility = regime_hostility
            
                if regime_hostility.is_fragile:
                    result.is_tradable = False
                    result.max_exposure = 0.0
                    result.reason = f"Regime hostility engine: {regime_hostility.reason}"
                    return result
        
            # Layer 4: Exposure Controller
            if "exposure_controller" in self.layers:
                exposure_controller = await self.layers["exposure_controller"].process(
                    strategy_id=strategy_id,
                    strategy_config=strategy_config,
                    market_data=market_data
                )
                result.exposure_controller = exposure_controller
                result.max_exposure = exposure_controller.max_exposure
            
                if exposure_controller.max_exposure <= 0:
                    result.is_tradable = False
                    result.reason = f"Exposure controller: {exposure_controller.reason}"
                    return result
        
            # Layer 6: Continuous Validity Monitor
            if "validation_monitor" in self.layers:
                validation_monitor = await self.layers["validation_monitor"].process(
                    strategy_id=strategy_id,
                    strategy_config=strategy_config,
                    market_data=market_data
                )
                result.validation_monitor = validation_monitor
            
                if not validation_monitor.is_valid:
                    result.is_tradable = False
                    result.max_exposure = 0.0
                    result.reason = f"Validation monitor: {validation_monitor.reason}"
                    return result
        
            # If we made it here, the strategy is tradable with the exposure set by the controller
            result.reason = "All governance checks passed"
            return result
        except Exception as e:
            logger.error(f"Error in evaluate_tradability: {e}")
            raise
    
    async def process_market_event(self, event: Dict[str, Any]) -> bool:
        """
        Process a market event through the anti-learning firewall.
        
        Returns True if the event should be included in learning, False if it should be excluded.
        """
        try:
            if "anti_learning_firewall" in self.layers:
                result = await self.layers["anti_learning_firewall"].process(event)
                return not result.should_exclude
        
            # Default to including the event if no anti-learning firewall
            return True
        except Exception as e:
            logger.error(f"Error in process_market_event: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the capital governance system"""
        return {
            "layers": list(self.layers.keys()),
            "timestamp": datetime.now().isoformat()
        }
