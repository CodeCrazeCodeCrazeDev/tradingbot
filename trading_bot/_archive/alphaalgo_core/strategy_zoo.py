"""
AlphaAlgo Core - Strategy Zoo (Layer 1)

Strategies are:
- Narrow
- Simple
- Assumption-bound
- Non-adaptive
- Replaceable

Each strategy must explicitly declare:
- Regime assumptions
- Volatility assumptions
- Liquidity assumptions
- Failure conditions
- Latency sensitivity

If assumptions cannot be extracted → strategy is invalid.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .capital_governance import (
    GovernanceLayer,
    StrategyZooResult,
    StrategyState,
    StrategyAssumption
)

logger = logging.getLogger(__name__)


class StrategyRequirement(Enum):
    """Required strategy declarations"""
    REGIME_ASSUMPTIONS = "regime_assumptions"
    VOLATILITY_ASSUMPTIONS = "volatility_assumptions"
    LIQUIDITY_ASSUMPTIONS = "liquidity_assumptions"
    FAILURE_CONDITIONS = "failure_conditions"
    LATENCY_SENSITIVITY = "latency_sensitivity"


class StrategyZoo(GovernanceLayer):
    """
    Layer 1 - Strategy Zoo
    
    Manages strategies and ensures they are properly defined with explicit assumptions.
    Strategies are treated as disposable by design.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("strategy_zoo")
        self.config = config or {}
        
        # Strategy registry
        self.strategies = {}
        
        # Required declarations
        self.required_declarations = {req.value for req in StrategyRequirement}
        
        logger.info("Strategy Zoo initialized")
    
    def register_strategy(self, strategy_id: str, strategy_config: Dict[str, Any]) -> bool:
        """
        Register a strategy with the zoo.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_config: Strategy configuration including assumptions
            
        Returns:
            bool: True if registration was successful
        """
        # Validate strategy has all required declarations
        missing = self._validate_strategy_declarations(strategy_config)
        
        if missing:
            logger.warning(f"Strategy {strategy_id} missing required declarations: {missing}")
            return False
        
        # Store strategy
        self.strategies[strategy_id] = strategy_config
        logger.info(f"Strategy {strategy_id} registered with Zoo")
        return True
    
    def _validate_strategy_declarations(self, strategy_config: Dict[str, Any]) -> Set[str]:
        """
        Validate that a strategy has all required declarations.
        
        Returns:
            Set of missing declarations
        """
        missing = set()
        
        for req in self.required_declarations:
            if req not in strategy_config:
                missing.add(req)
            elif not strategy_config[req]:
                missing.add(req)  # Empty declarations are not valid
        
        return missing
    
    def _extract_assumptions(self, strategy_config: Dict[str, Any]) -> List[StrategyAssumption]:
        """
        Extract explicit assumptions from strategy configuration.
        """
        assumptions = []
        
        # Process regime assumptions
        if "regime_assumptions" in strategy_config:
            for name, details in strategy_config["regime_assumptions"].items():
                assumptions.append(
                    StrategyAssumption(
                        name=f"regime_{name}",
                        description=details.get("description", ""),
                        current_value=0.0,  # Will be set during evaluation
                        threshold=details.get("threshold", 0.5),
                        is_valid=True,  # Will be set during evaluation
                        stress_score=0.0  # Will be set during evaluation
                    )
                )
        
        # Process volatility assumptions
        if "volatility_assumptions" in strategy_config:
            for name, details in strategy_config["volatility_assumptions"].items():
                assumptions.append(
                    StrategyAssumption(
                        name=f"volatility_{name}",
                        description=details.get("description", ""),
                        current_value=0.0,  # Will be set during evaluation
                        threshold=details.get("threshold", 0.5),
                        is_valid=True,  # Will be set during evaluation
                        stress_score=0.0  # Will be set during evaluation
                    )
                )
        
        # Process liquidity assumptions
        if "liquidity_assumptions" in strategy_config:
            for name, details in strategy_config["liquidity_assumptions"].items():
                assumptions.append(
                    StrategyAssumption(
                        name=f"liquidity_{name}",
                        description=details.get("description", ""),
                        current_value=0.0,  # Will be set during evaluation
                        threshold=details.get("threshold", 0.5),
                        is_valid=True,  # Will be set during evaluation
                        stress_score=0.0  # Will be set during evaluation
                    )
                )
        
        # Process failure conditions
        if "failure_conditions" in strategy_config:
            for name, details in strategy_config["failure_conditions"].items():
                assumptions.append(
                    StrategyAssumption(
                        name=f"failure_{name}",
                        description=details.get("description", ""),
                        current_value=0.0,  # Will be set during evaluation
                        threshold=details.get("threshold", 0.5),
                        is_valid=True,  # Will be set during evaluation
                        stress_score=0.0  # Will be set during evaluation
                    )
                )
        
        # Process latency sensitivity
        if "latency_sensitivity" in strategy_config:
            assumptions.append(
                StrategyAssumption(
                    name="latency_sensitivity",
                    description="Maximum acceptable latency",
                    current_value=0.0,  # Will be set during evaluation
                    threshold=strategy_config["latency_sensitivity"].get("max_ms", 1000),
                    is_valid=True,  # Will be set during evaluation
                    stress_score=0.0  # Will be set during evaluation
                )
            )
        
        return assumptions
    
    async def _evaluate_assumptions(
        self,
        assumptions: List[StrategyAssumption],
        market_data: Dict[str, Any]
    ) -> List[StrategyAssumption]:
        """
        Evaluate assumptions against current market data.
        
        Updates the current_value, is_valid, and stress_score fields of each assumption.
        """
        # Extract market metrics
        market_metrics = self._extract_market_metrics(market_data)
        
        # Update each assumption
        for assumption in assumptions:
            # Get the base name (without prefix)
            if "_" in assumption.name:
                prefix, base_name = assumption.name.split("_", 1)
            else:
                prefix, base_name = "", assumption.name
            
            # Set current value based on market metrics
            if assumption.name in market_metrics:
                assumption.current_value = market_metrics[assumption.name]
            elif base_name in market_metrics:
                assumption.current_value = market_metrics[base_name]
            else:
                # Default to neutral if metric not found
                assumption.current_value = assumption.threshold
            
            # Determine validity based on threshold comparison
            if prefix == "failure":
                # For failure conditions, valid means below threshold
                assumption.is_valid = assumption.current_value < assumption.threshold
            else:
                # For other assumptions, valid means above threshold
                assumption.is_valid = assumption.current_value >= assumption.threshold
            
            # Calculate stress score (0-100)
            if prefix == "failure":
                # For failure conditions, stress increases as we approach threshold
                if assumption.threshold > 0:
                    assumption.stress_score = min(100, (assumption.current_value / assumption.threshold) * 100)
                else:
                    assumption.stress_score = 0
            else:
                # For other assumptions, stress increases as we move away from threshold
                if assumption.threshold > 0:
                    assumption.stress_score = max(0, 100 - (assumption.current_value / assumption.threshold) * 100)
                else:
                    assumption.stress_score = 100
        
        return assumptions
    
    def _extract_market_metrics(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract relevant metrics from market data for assumption evaluation.
        """
        metrics = {}
        
        # Extract regime metrics
        if "regime" in market_data:
            regime_data = market_data["regime"]
            for key, value in regime_data.items():
                metrics[f"regime_{key}"] = float(value)
        
        # Extract volatility metrics
        if "volatility" in market_data:
            vol_data = market_data["volatility"]
            for key, value in vol_data.items():
                metrics[f"volatility_{key}"] = float(value)
        
        # Extract liquidity metrics
        if "liquidity" in market_data:
            liq_data = market_data["liquidity"]
            for key, value in liq_data.items():
                metrics[f"liquidity_{key}"] = float(value)
        
        # Extract failure condition metrics
        if "risk" in market_data:
            risk_data = market_data["risk"]
            for key, value in risk_data.items():
                metrics[f"failure_{key}"] = float(value)
        
        # Extract latency metrics
        if "latency" in market_data:
            metrics["latency_sensitivity"] = float(market_data["latency"].get("current_ms", 0))
        
        return metrics
    
    async def process(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> StrategyZooResult:
        """
        Process a strategy to determine if it's valid based on its declared assumptions.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_config: Strategy configuration including assumptions
            market_data: Current market data
            
        Returns:
            StrategyZooResult with validity determination
        """
        try:
            # Check if strategy is registered
            if strategy_id not in self.strategies:
                # Try to register it
                if not self.register_strategy(strategy_id, strategy_config):
                    return StrategyZooResult(
                        strategy_id=strategy_id,
                        state=StrategyState.INVALID,
                        assumptions=[],
                        is_valid=False,
                        reason="Strategy missing required declarations"
                    )
            
            # Extract explicit assumptions
            assumptions = self._extract_assumptions(strategy_config)
            
            if not assumptions:
                return StrategyZooResult(
                    strategy_id=strategy_id,
                    state=StrategyState.INVALID,
                    assumptions=[],
                    is_valid=False,
                    reason="No assumptions could be extracted"
                )
            
            # Evaluate assumptions against current market data
            evaluated_assumptions = await self._evaluate_assumptions(assumptions, market_data)
            
            # Check if any assumptions are invalid
            invalid_assumptions = [a for a in evaluated_assumptions if not a.is_valid]
            
            if invalid_assumptions:
                invalid_names = [a.name for a in invalid_assumptions]
                return StrategyZooResult(
                    strategy_id=strategy_id,
                    state=StrategyState.INVALID,
                    assumptions=evaluated_assumptions,
                    is_valid=False,
                    reason=f"Invalid assumptions: {', '.join(invalid_names)}"
                )
            
            # Calculate average stress score
            avg_stress = sum(a.stress_score for a in evaluated_assumptions) / len(evaluated_assumptions)
            
            # Strategy is valid but may be stressed
            state = StrategyState.VALID
            reason = "All assumptions valid"
            
            if avg_stress > 70:
                reason = f"Strategy valid but highly stressed ({avg_stress:.1f}%)"
            
            return StrategyZooResult(
                strategy_id=strategy_id,
                state=state,
                assumptions=evaluated_assumptions,
                is_valid=True,
                reason=reason
            )
            
        except Exception as e:
            logger.exception(f"Error in strategy zoo: {e}")
            return StrategyZooResult(
                strategy_id=strategy_id,
                state=StrategyState.UNKNOWN,
                assumptions=[],
                is_valid=False,
                reason=f"Error in strategy evaluation: {str(e)}"
            )
