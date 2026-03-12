"""
Optionality Preservation System for TAMIC

This module implements optionality preservation focusing on:
1. Irreversibility costs - Avoiding trades that limit future options
2. Liquidity value - Preserving capital for future opportunities
3. Opportunity cost tracking - Measuring the cost of committing capital
4. Position sizing with optionality - Keeping dry powder for better setups
5. Scenario planning - Maintaining flexibility across possible futures

The primary goal is to avoid overcommitment and preserve future trading options.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from .core import TimeHorizon, MarketTimeState

logger = logging.getLogger(__name__)


class OptionalityValue(Enum):
    """Value of preserving optionality"""
    LOW = "low"  # Low value in preserving optionality
    MEDIUM = "medium"  # Medium value in preserving optionality
    HIGH = "high"  # High value in preserving optionality
    CRITICAL = "critical"  # Critical value in preserving optionality


class IrreversibilityLevel(Enum):
    """Level of trade irreversibility"""
    EASILY_REVERSIBLE = "easily_reversible"  # Can exit with minimal cost
    MODERATELY_REVERSIBLE = "moderately_reversible"  # Can exit with some cost
    DIFFICULT_TO_REVERSE = "difficult_to_reverse"  # Difficult to exit
    PRACTICALLY_IRREVERSIBLE = "practically_irreversible"  # Nearly impossible to exit


class OpportunityState(Enum):
    """State of opportunity landscape"""
    SCARCE = "scarce"  # Few opportunities available
    NORMAL = "normal"  # Normal number of opportunities
    ABUNDANT = "abundant"  # Many opportunities available
    EXCEPTIONAL = "exceptional"  # Exceptional opportunities available


@dataclass
class OptionalityMetrics:
    """Metrics related to optionality analysis"""
    liquidity_value: float = 0.0  # Value of maintaining liquidity (0-1)
    irreversibility_cost: float = 0.0  # Cost of irreversibility (0-1)
    opportunity_cost: float = 0.0  # Opportunity cost (0-1)
    dry_powder_value: float = 0.0  # Value of keeping dry powder (0-1)
    scenario_flexibility: float = 0.0  # Flexibility across scenarios (0-1)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptionalityResult:
    """Result from optionality analysis"""
    optionality_value: float  # Overall value of preserving optionality (0-1)
    irreversibility_level: IrreversibilityLevel  # Level of trade irreversibility
    opportunity_state: OpportunityState  # State of opportunity landscape
    recommended_max_allocation: float  # Recommended maximum allocation (0-1)
    metrics: OptionalityMetrics  # Detailed optionality metrics
    timestamp: float = field(default_factory=time.time)


class OptionalityPreservationEngine:
    """
    Engine for preserving optionality in trading decisions.
    
    Focuses on avoiding overcommitment and preserving future trading options.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize OptionalityPreservationEngine.
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger("trading_bot.tamic.optionality")
        
        # Optionality value thresholds
        self.optionality_thresholds = self.config.get("optionality_thresholds", {
            OptionalityValue.LOW: 0.2,
            OptionalityValue.MEDIUM: 0.5,
            OptionalityValue.HIGH: 0.7,
            OptionalityValue.CRITICAL: 0.9,
        })
        
        # Irreversibility thresholds
        self.irreversibility_thresholds = self.config.get("irreversibility_thresholds", {
            IrreversibilityLevel.EASILY_REVERSIBLE: 0.2,
            IrreversibilityLevel.MODERATELY_REVERSIBLE: 0.4,
            IrreversibilityLevel.DIFFICULT_TO_REVERSE: 0.7,
            IrreversibilityLevel.PRACTICALLY_IRREVERSIBLE: 0.9,
        })
        
        # Opportunity state thresholds
        self.opportunity_thresholds = self.config.get("opportunity_thresholds", {
            OpportunityState.SCARCE: 0.3,
            OpportunityState.NORMAL: 0.5,
            OpportunityState.ABUNDANT: 0.7,
            OpportunityState.EXCEPTIONAL: 0.9,
        })
        
        # Allocation multipliers based on optionality value
        self.allocation_multipliers = self.config.get("allocation_multipliers", {
            OptionalityValue.LOW: 1.0,
            OptionalityValue.MEDIUM: 0.8,
            OptionalityValue.HIGH: 0.6,
            OptionalityValue.CRITICAL: 0.4,
        })
        
        # Liquidity value multiplier
        self.liquidity_value_multiplier = self.config.get("liquidity_value_multiplier", 0.05)
        
        # Irreversibility penalty
        self.irreversibility_penalty = self.config.get("irreversibility_penalty", 0.2)
        
        # Opportunity cost tracking
        self.opportunity_history = {}  # Symbol -> history
    
    def _evaluate_liquidity_value(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> float:
        """
        Evaluate the value of maintaining liquidity.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            Liquidity value (0-1)
        """
        # This would typically be a more sophisticated analysis
        # For now, we'll use a simple approach based on volatility and spread
        
        # Default value - moderate importance of liquidity
        liquidity_value = 0.5
        
        # If we have volatility data, adjust based on volatility
        if "volatility" in market_data:
            volatility = market_data["volatility"]
            if isinstance(volatility, (int, float)):
                # Higher volatility = higher value of liquidity
                if volatility > 0.03:  # 3% daily volatility
                    liquidity_value += 0.3
                elif volatility > 0.02:  # 2% daily volatility
                    liquidity_value += 0.2
                elif volatility > 0.01:  # 1% daily volatility
                    liquidity_value += 0.1
        
        # If we have spread data, adjust based on spread
        if "spread" in market_data:
            spread = market_data["spread"]
            if isinstance(spread, (int, float)):
                # Higher spread = higher value of liquidity
                if spread > 0.005:  # 0.5% spread
                    liquidity_value += 0.2
                elif spread > 0.002:  # 0.2% spread
                    liquidity_value += 0.1
                elif spread > 0.001:  # 0.1% spread
                    liquidity_value += 0.05
        
        # If we have volume data, adjust based on volume
        if "volume" in market_data:
            volume = market_data["volume"]
            if isinstance(volume, (list, np.ndarray, pd.Series)):
                # Convert to numpy array if needed
                if isinstance(volume, list):
                    volume = np.array(volume)
                elif isinstance(volume, pd.Series):
                    volume = volume.values
                
                # Calculate average volume
                avg_volume = np.mean(volume)
                
                # Check recent volume
                recent_volume = volume[-5:]  # Last 5 periods
                recent_avg = np.mean(recent_volume)
                
                # Lower recent volume = higher value of liquidity
                if recent_avg < avg_volume * 0.7:
                    liquidity_value += 0.2
                elif recent_avg < avg_volume * 0.9:
                    liquidity_value += 0.1
        
        # Cap at 1.0
        return min(1.0, liquidity_value)
    
    def _evaluate_irreversibility(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Tuple[IrreversibilityLevel, float]:
        """
        Evaluate the irreversibility of a trade.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            Tuple of (irreversibility_level, irreversibility_cost)
        """
        # This would typically be a more sophisticated analysis
        # For now, we'll use a simple approach based on liquidity and volatility
        
        # Default level - moderately reversible
        irreversibility_level = IrreversibilityLevel.MODERATELY_REVERSIBLE
        irreversibility_cost = 0.4  # Default cost
        
        # If we have liquidity data, adjust based on liquidity
        if "liquidity" in market_data:
            liquidity = market_data["liquidity"]
            if isinstance(liquidity, (int, float)):
                # Lower liquidity = higher irreversibility
                if liquidity < 0.3:  # Very low liquidity
                    irreversibility_level = IrreversibilityLevel.PRACTICALLY_IRREVERSIBLE
                    irreversibility_cost = 0.9
                elif liquidity < 0.5:  # Low liquidity
                    irreversibility_level = IrreversibilityLevel.DIFFICULT_TO_REVERSE
                    irreversibility_cost = 0.7
                elif liquidity > 0.8:  # High liquidity
                    irreversibility_level = IrreversibilityLevel.EASILY_REVERSIBLE
                    irreversibility_cost = 0.2
        
        # If we have volatility data, adjust based on volatility
        if "volatility" in market_data:
            volatility = market_data["volatility"]
            if isinstance(volatility, (int, float)):
                # Higher volatility = higher irreversibility
                if volatility > 0.03:  # 3% daily volatility
                    irreversibility_cost += 0.2
                    # Upgrade irreversibility level if not already at max
                    if irreversibility_level != IrreversibilityLevel.PRACTICALLY_IRREVERSIBLE:
                        if irreversibility_level == IrreversibilityLevel.DIFFICULT_TO_REVERSE:
                            irreversibility_level = IrreversibilityLevel.PRACTICALLY_IRREVERSIBLE
                        elif irreversibility_level == IrreversibilityLevel.MODERATELY_REVERSIBLE:
                            irreversibility_level = IrreversibilityLevel.DIFFICULT_TO_REVERSE
                        elif irreversibility_level == IrreversibilityLevel.EASILY_REVERSIBLE:
                            irreversibility_level = IrreversibilityLevel.MODERATELY_REVERSIBLE
        
        # If we have spread data, adjust based on spread
        if "spread" in market_data:
            spread = market_data["spread"]
            if isinstance(spread, (int, float)):
                # Higher spread = higher irreversibility
                if spread > 0.005:  # 0.5% spread
                    irreversibility_cost += 0.15
                elif spread > 0.002:  # 0.2% spread
                    irreversibility_cost += 0.1
        
        # Cap at 1.0
        irreversibility_cost = min(1.0, irreversibility_cost)
        
        return irreversibility_level, irreversibility_cost
    
    def _evaluate_opportunity_landscape(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any]
    ) -> Tuple[OpportunityState, float]:
        """
        Evaluate the opportunity landscape.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            
        Returns:
            Tuple of (opportunity_state, opportunity_cost)
        """
        # This would typically be a more sophisticated analysis
        # For now, we'll use a simple approach based on volatility and market regime
        
        # Default state - normal opportunities
        opportunity_state = OpportunityState.NORMAL
        opportunity_cost = 0.5  # Default cost
        
        # If we have volatility data, adjust based on volatility
        if "volatility" in market_data:
            volatility = market_data["volatility"]
            if isinstance(volatility, (int, float)):
                # Higher volatility = more opportunities
                if volatility > 0.03:  # 3% daily volatility
                    opportunity_state = OpportunityState.ABUNDANT
                    opportunity_cost = 0.7
                elif volatility > 0.02:  # 2% daily volatility
                    opportunity_state = OpportunityState.NORMAL
                    opportunity_cost = 0.5
                elif volatility < 0.01:  # 1% daily volatility
                    opportunity_state = OpportunityState.SCARCE
                    opportunity_cost = 0.3
        
        # If we have market regime data, adjust based on regime
        if "market_regime" in market_data:
            regime = market_data["market_regime"]
            if isinstance(regime, str):
                # Different regimes have different opportunity landscapes
                if regime.lower() in ["trending", "strong_trend"]:
                    # Trending markets have more directional opportunities
                    if opportunity_state != OpportunityState.EXCEPTIONAL:
                        opportunity_state = OpportunityState.ABUNDANT
                        opportunity_cost = 0.7
                elif regime.lower() in ["volatile", "high_volatility"]:
                    # Volatile markets have more opportunities
                    opportunity_state = OpportunityState.EXCEPTIONAL
                    opportunity_cost = 0.9
                elif regime.lower() in ["ranging", "sideways"]:
                    # Ranging markets have fewer directional opportunities
                    if opportunity_state != OpportunityState.SCARCE:
                        opportunity_state = OpportunityState.NORMAL
                        opportunity_cost = 0.5
                elif regime.lower() in ["low_volatility", "quiet"]:
                    # Low volatility markets have fewer opportunities
                    opportunity_state = OpportunityState.SCARCE
                    opportunity_cost = 0.3
        
        # Adjust based on time horizon
        if horizon == TimeHorizon.MICROSTRUCTURE:
            # Microstructure typically has more opportunities
            if opportunity_state != OpportunityState.EXCEPTIONAL:
                opportunity_state = OpportunityState.ABUNDANT
                opportunity_cost = 0.7
        elif horizon == TimeHorizon.MEDIUM_HORIZON:
            # Medium horizon typically has fewer opportunities
            if opportunity_state != OpportunityState.SCARCE:
                opportunity_state = OpportunityState.NORMAL
                opportunity_cost = 0.5
        
        return opportunity_state, opportunity_cost
    
    def _calculate_dry_powder_value(
        self,
        opportunity_state: OpportunityState,
        irreversibility_level: IrreversibilityLevel
    ) -> float:
        """
        Calculate the value of keeping dry powder.
        
        Args:
            opportunity_state: State of opportunity landscape
            irreversibility_level: Level of trade irreversibility
            
        Returns:
            Dry powder value (0-1)
        """
        # Base value based on opportunity state
        if opportunity_state == OpportunityState.EXCEPTIONAL:
            base_value = 0.2  # Low value in keeping dry powder when opportunities are exceptional
        elif opportunity_state == OpportunityState.ABUNDANT:
            base_value = 0.4  # Moderate value in keeping dry powder when opportunities are abundant
        elif opportunity_state == OpportunityState.NORMAL:
            base_value = 0.6  # Higher value in keeping dry powder when opportunities are normal
        else:  # SCARCE
            base_value = 0.8  # High value in keeping dry powder when opportunities are scarce
        
        # Adjust based on irreversibility
        if irreversibility_level == IrreversibilityLevel.PRACTICALLY_IRREVERSIBLE:
            base_value += 0.2  # Higher value in keeping dry powder when trades are irreversible
        elif irreversibility_level == IrreversibilityLevel.DIFFICULT_TO_REVERSE:
            base_value += 0.1  # Moderate increase when trades are difficult to reverse
        
        # Cap at 1.0
        return min(1.0, base_value)
    
    def _evaluate_scenario_flexibility(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        irreversibility_level: IrreversibilityLevel
    ) -> float:
        """
        Evaluate flexibility across possible future scenarios.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            irreversibility_level: Level of trade irreversibility
            
        Returns:
            Scenario flexibility (0-1)
        """
        # This would typically be a more sophisticated analysis
        # For now, we'll use a simple approach based on irreversibility and volatility
        
        # Base flexibility based on irreversibility
        if irreversibility_level == IrreversibilityLevel.PRACTICALLY_IRREVERSIBLE:
            base_flexibility = 0.2  # Low flexibility when trades are irreversible
        elif irreversibility_level == IrreversibilityLevel.DIFFICULT_TO_REVERSE:
            base_flexibility = 0.4  # Moderate flexibility when trades are difficult to reverse
        elif irreversibility_level == IrreversibilityLevel.MODERATELY_REVERSIBLE:
            base_flexibility = 0.6  # Higher flexibility when trades are moderately reversible
        else:  # EASILY_REVERSIBLE
            base_flexibility = 0.8  # High flexibility when trades are easily reversible
        
        # If we have volatility data, adjust based on volatility
        if "volatility" in market_data:
            volatility = market_data["volatility"]
            if isinstance(volatility, (int, float)):
                # Higher volatility = lower flexibility
                if volatility > 0.03:  # 3% daily volatility
                    base_flexibility -= 0.2
                elif volatility > 0.02:  # 2% daily volatility
                    base_flexibility -= 0.1
        
        # If we have correlation data, adjust based on correlation
        if "correlation" in market_data:
            correlation = market_data["correlation"]
            if isinstance(correlation, (int, float)):
                # Higher correlation = lower flexibility
                if abs(correlation) > 0.8:  # High correlation
                    base_flexibility -= 0.2
                elif abs(correlation) > 0.6:  # Moderate correlation
                    base_flexibility -= 0.1
        
        # Cap between 0 and 1
        return max(0.0, min(1.0, base_flexibility))
    
    def _calculate_optionality_value(self, metrics: OptionalityMetrics) -> float:
        """
        Calculate overall optionality value from metrics.
        
        Args:
            metrics: Optionality metrics
            
        Returns:
            Overall optionality value (0-1)
        """
        # Weighted average of metrics
        weights = {
            "liquidity_value": 0.2,
            "irreversibility_cost": 0.25,
            "opportunity_cost": 0.2,
            "dry_powder_value": 0.2,
            "scenario_flexibility": 0.15,
        }
        
        optionality_value = (
            metrics.liquidity_value * weights["liquidity_value"] +
            metrics.irreversibility_cost * weights["irreversibility_cost"] +
            metrics.opportunity_cost * weights["opportunity_cost"] +
            metrics.dry_powder_value * weights["dry_powder_value"] +
            metrics.scenario_flexibility * weights["scenario_flexibility"]
        )
        
        return optionality_value
    
    def _get_optionality_value_category(self, value: float) -> OptionalityValue:
        """
        Get optionality value category based on value.
        
        Args:
            value: Optionality value (0-1)
            
        Returns:
            OptionalityValue category
        """
        if value >= self.optionality_thresholds[OptionalityValue.CRITICAL]:
            return OptionalityValue.CRITICAL
        elif value >= self.optionality_thresholds[OptionalityValue.HIGH]:
            return OptionalityValue.HIGH
        elif value >= self.optionality_thresholds[OptionalityValue.MEDIUM]:
            return OptionalityValue.MEDIUM
        else:
            return OptionalityValue.LOW
    
    def _calculate_recommended_allocation(
        self,
        optionality_value: float,
        opportunity_state: OpportunityState
    ) -> float:
        """
        Calculate recommended maximum allocation based on optionality value.
        
        Args:
            optionality_value: Optionality value (0-1)
            opportunity_state: State of opportunity landscape
            
        Returns:
            Recommended maximum allocation (0-1)
        """
        # Get optionality value category
        optionality_category = self._get_optionality_value_category(optionality_value)
        
        # Base allocation from optionality category
        base_allocation = self.allocation_multipliers[optionality_category]
        
        # Adjust based on opportunity state
        if opportunity_state == OpportunityState.EXCEPTIONAL:
            # Exceptional opportunities warrant higher allocation
            base_allocation = min(1.0, base_allocation * 1.5)
        elif opportunity_state == OpportunityState.ABUNDANT:
            # Abundant opportunities warrant slightly higher allocation
            base_allocation = min(1.0, base_allocation * 1.2)
        elif opportunity_state == OpportunityState.SCARCE:
            # Scarce opportunities warrant lower allocation
            base_allocation = base_allocation * 0.8
        
        return base_allocation
    
    async def evaluate_optionality(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any]
    ) -> OptionalityResult:
        """
        Evaluate optionality preservation for a symbol and horizon.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            
        Returns:
            OptionalityResult with optionality analysis
        """
        self.logger.info(f"Evaluating optionality for {symbol} on {horizon.value} horizon")
        
        # 1. Evaluate liquidity value
        liquidity_value = self._evaluate_liquidity_value(symbol, market_data)
        
        # 2. Evaluate irreversibility
        irreversibility_level, irreversibility_cost = self._evaluate_irreversibility(symbol, market_data)
        
        # 3. Evaluate opportunity landscape
        opportunity_state, opportunity_cost = self._evaluate_opportunity_landscape(symbol, horizon, market_data)
        
        # 4. Calculate dry powder value
        dry_powder_value = self._calculate_dry_powder_value(opportunity_state, irreversibility_level)
        
        # 5. Evaluate scenario flexibility
        scenario_flexibility = self._evaluate_scenario_flexibility(symbol, market_data, irreversibility_level)
        
        # Create metrics object
        metrics = OptionalityMetrics(
            liquidity_value=liquidity_value,
            irreversibility_cost=irreversibility_cost,
            opportunity_cost=opportunity_cost,
            dry_powder_value=dry_powder_value,
            scenario_flexibility=scenario_flexibility,
            metrics={
                "liquidity_value": liquidity_value,
                "irreversibility_cost": irreversibility_cost,
                "irreversibility_level": irreversibility_level.value,
                "opportunity_cost": opportunity_cost,
                "opportunity_state": opportunity_state.value,
                "dry_powder_value": dry_powder_value,
                "scenario_flexibility": scenario_flexibility,
            }
        )
        
        # Calculate overall optionality value
        optionality_value = self._calculate_optionality_value(metrics)
        
        # Calculate recommended allocation
        recommended_max_allocation = self._calculate_recommended_allocation(
            optionality_value, opportunity_state
        )
        
        # Log results
        self.logger.info(f"{symbol} {horizon.value}: Optionality value {optionality_value:.2f}, "
                        f"Irreversibility {irreversibility_level.value}, "
                        f"Opportunity state {opportunity_state.value}")
        
        # Create result
        result = OptionalityResult(
            optionality_value=optionality_value,
            irreversibility_level=irreversibility_level,
            opportunity_state=opportunity_state,
            recommended_max_allocation=recommended_max_allocation,
            metrics=metrics
        )
        
        return result
