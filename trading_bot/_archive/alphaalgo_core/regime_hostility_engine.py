"""
AlphaAlgo Core - Regime Hostility Engine (Layer 3)

Continuously imagines hostile conditions:
- Regime inversion
- Correlation collapse
- Volatility shocks
- Liquidity evaporation
- Signal semantic inversion

If a strategy fails under hostile simulation:
- Label it fragile
- Cap or eliminate exposure permanently
- Do not "fix" the strategy
- Fragility is not repaired — it is punished
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
    RegimeHostilityResult,
    HostileCondition,
    RegimeState,
    RegimeHostilityError
)

logger = logging.getLogger(__name__)


class HostileScenario(Enum):
    """Types of hostile scenarios to simulate"""
    REGIME_INVERSION = "regime_inversion"
    CORRELATION_COLLAPSE = "correlation_collapse"
    VOLATILITY_SHOCK = "volatility_shock"
    LIQUIDITY_EVAPORATION = "liquidity_evaporation"
    SIGNAL_INVERSION = "signal_inversion"


class RegimeHostilityEngine(GovernanceLayer):
    """
    Layer 3 - Regime Hostility Engine
    
    Simulates hostile market conditions to identify fragile strategies.
    Strategies that fail under hostile conditions are labeled as fragile and penalized.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("regime_hostility_engine")
        self.config = config or {}
        
        # Fragility registry - stores permanently identified fragile strategies
        self.fragile_strategies = set()
        
        # Load previously identified fragile strategies if available
        self._load_fragile_strategies()
        
        # Scenario generators for different hostile conditions
        self.scenario_generators = {
            HostileScenario.REGIME_INVERSION: self._generate_regime_inversion,
            HostileScenario.CORRELATION_COLLAPSE: self._generate_correlation_collapse,
            HostileScenario.VOLATILITY_SHOCK: self._generate_volatility_shock,
            HostileScenario.LIQUIDITY_EVAPORATION: self._generate_liquidity_evaporation,
            HostileScenario.SIGNAL_INVERSION: self._generate_signal_inversion
        }
        
        # Scenario evaluators for different hostile conditions
        self.scenario_evaluators = {
            HostileScenario.REGIME_INVERSION: self._evaluate_regime_inversion,
            HostileScenario.CORRELATION_COLLAPSE: self._evaluate_correlation_collapse,
            HostileScenario.VOLATILITY_SHOCK: self._evaluate_volatility_shock,
            HostileScenario.LIQUIDITY_EVAPORATION: self._evaluate_liquidity_evaporation,
            HostileScenario.SIGNAL_INVERSION: self._evaluate_signal_inversion
        }
        
        logger.info("Regime Hostility Engine initialized")
    
    def _load_fragile_strategies(self):
        """Load previously identified fragile strategies"""
        try:
            # Try to load from file
            fragile_path = self.config.get("fragile_strategies_path", "fragile_strategies.json")
            with open(fragile_path, 'r') as f:
                self.fragile_strategies = set(json.load(f))
            logger.info(f"Loaded {len(self.fragile_strategies)} fragile strategies")
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is invalid, start with empty set
            self.fragile_strategies = set()
            logger.info("No existing fragile strategies found, starting fresh")
    
    def _save_fragile_strategies(self):
        """Save identified fragile strategies to persistent storage"""
        try:
            # Save to file
            fragile_path = self.config.get("fragile_strategies_path", "fragile_strategies.json")
            with open(fragile_path, 'w') as f:
                json.dump(list(self.fragile_strategies), f)
            logger.info(f"Saved {len(self.fragile_strategies)} fragile strategies")
        except Exception as e:
            logger.error(f"Error saving fragile strategies: {e}")
    
    def mark_strategy_fragile(self, strategy_id: str, reason: str):
        """
        Mark a strategy as permanently fragile.
        
        This is an irreversible action - fragility is punished, not fixed.
        """
        if strategy_id not in self.fragile_strategies:
            self.fragile_strategies.add(strategy_id)
            logger.warning(f"Strategy {strategy_id} marked as PERMANENTLY FRAGILE: {reason}")
            self._save_fragile_strategies()
    
    async def process(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> RegimeHostilityResult:
        """
        Process a strategy through hostile scenario simulations.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_config: Strategy configuration
            market_data: Current market data
            
        Returns:
            RegimeHostilityResult with fragility determination
        """
        try:
            # Check if strategy is already known to be fragile
            if strategy_id in self.fragile_strategies:
                return RegimeHostilityResult(
                    strategy_id=strategy_id,
                    hostile_conditions=[],
                    state=RegimeState.HOSTILE,
                    is_fragile=True,
                    reason="Strategy previously identified as fragile"
                )
            
            # Generate hostile conditions to test
            hostile_conditions = await self._generate_hostile_conditions(strategy_config, market_data)
            
            # Evaluate strategy against each hostile condition
            failed_conditions = []
            
            for condition in hostile_conditions:
                # Skip conditions that aren't present
                if not condition.is_present:
                    continue
                
                # Evaluate if strategy can survive this condition
                survives = await self._evaluate_strategy_survival(
                    strategy_id, strategy_config, market_data, condition
                )
                
                if not survives:
                    failed_conditions.append(condition)
            
            # Determine overall fragility
            is_fragile = len(failed_conditions) > 0
            
            # If fragile, mark it permanently
            if is_fragile:
                failed_names = [c.name for c in failed_conditions]
                reason = f"Failed under hostile conditions: {', '.join(failed_names)}"
                self.mark_strategy_fragile(strategy_id, reason)
                
                return RegimeHostilityResult(
                    strategy_id=strategy_id,
                    hostile_conditions=hostile_conditions,
                    state=RegimeState.HOSTILE,
                    is_fragile=True,
                    reason=reason
                )
            
            # Determine current regime state
            current_regime = self._determine_current_regime(market_data)
            
            return RegimeHostilityResult(
                strategy_id=strategy_id,
                hostile_conditions=hostile_conditions,
                state=current_regime,
                is_fragile=False,
                reason="Strategy survives all present hostile conditions"
            )
            
        except Exception as e:
            logger.exception(f"Error in regime hostility engine: {e}")
            return RegimeHostilityResult(
                strategy_id=strategy_id,
                hostile_conditions=[],
                state=RegimeState.UNKNOWN,
                is_fragile=True,  # Assume fragile on error (safety first)
                reason=f"Error in hostility evaluation: {str(e)}"
            )
    
    async def _generate_hostile_conditions(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> List[HostileCondition]:
        """
        Generate a list of hostile conditions to test against.
        
        The conditions are tailored to the strategy and current market conditions.
        """
        hostile_conditions = []
        
        # Generate each type of hostile condition
        for scenario in HostileScenario:
            generator = self.scenario_generators.get(scenario)
            if generator:
                condition = await generator(strategy_config, market_data)
                hostile_conditions.append(condition)
        
        return hostile_conditions
    
    async def _evaluate_strategy_survival(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        condition: HostileCondition
    ) -> bool:
        """
        Evaluate if a strategy can survive a specific hostile condition.
        
        Returns True if the strategy survives, False if it fails.
        """
        # Get the appropriate evaluator for this condition
        scenario = next((s for s in HostileScenario if s.value == condition.name), None)
        
        if not scenario:
            logger.warning(f"No evaluator found for condition: {condition.name}")
            return True  # Assume survival if we can't evaluate
        
        evaluator = self.scenario_evaluators.get(scenario)
        if not evaluator:
            logger.warning(f"No evaluator function for scenario: {scenario.value}")
            return True  # Assume survival if we can't evaluate
        
        # Evaluate survival
        return await evaluator(strategy_config, market_data, condition)
    
    def _determine_current_regime(self, market_data: Dict[str, Any]) -> RegimeState:
        """
        Determine the current market regime state.
        """
        # Check if market data includes regime information
        if "regime" in market_data:
            regime_data = market_data["regime"]
            
            # Check for extreme conditions
            if regime_data.get("is_extreme", False):
                return RegimeState.EXTREME
            
            # Check for hostile conditions
            if regime_data.get("is_hostile", False):
                return RegimeState.HOSTILE
            
            # Default to normal
            return RegimeState.NORMAL
        
        # If no regime data, try to infer from volatility
        if "volatility" in market_data:
            vol_data = market_data["volatility"]
            
            # Check if current volatility is much higher than normal
            current_vol = vol_data.get("current", 0)
            normal_vol = vol_data.get("normal", 1)
            
            if normal_vol > 0:
                vol_ratio = current_vol / normal_vol
                
                if vol_ratio > 3.0:
                    return RegimeState.EXTREME
                elif vol_ratio > 1.5:
                    return RegimeState.HOSTILE
        
        # Default to normal if we can't determine
        return RegimeState.NORMAL
    
    # === Hostile scenario generators ===
    
    async def _generate_regime_inversion(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> HostileCondition:
        """
        Generate a regime inversion hostile condition.
        
        This simulates a complete reversal of the current market regime.
        """
        # Determine the strategy's preferred regime
        preferred_regime = None
        if "regime_assumptions" in strategy_config:
            # Find the regime with highest assumption value
            max_value = -1
            for regime, details in strategy_config["regime_assumptions"].items():
                if details.get("value", 0) > max_value:
                    max_value = details.get("value", 0)
                    preferred_regime = regime
        
        # Determine if current regime matches preferred regime
        current_regime = None
        if "regime" in market_data:
            current_regime = market_data["regime"].get("current", None)
        
        # Calculate probability and impact
        probability = 0.3  # Base probability of regime inversion
        impact = 80.0  # Base impact of regime inversion
        
        # Adjust based on strategy and market conditions
        if preferred_regime and current_regime:
            if preferred_regime == current_regime:
                # Strategy is in its preferred regime, inversion would be devastating
                probability = 0.4
                impact = 90.0
            else:
                # Strategy is already not in preferred regime
                probability = 0.2
                impact = 60.0
        
        # Check if there are signs of regime change
        if "regime" in market_data and "transition_probability" in market_data["regime"]:
            transition_prob = market_data["regime"]["transition_probability"]
            probability = max(probability, transition_prob)
        
        # Determine if condition is present
        is_present = probability > 0.25
        
        return HostileCondition(
            name=HostileScenario.REGIME_INVERSION.value,
            description="Complete reversal of current market regime",
            probability=probability,
            impact=impact,
            is_present=is_present
        )
    
    async def _generate_correlation_collapse(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> HostileCondition:
        """
        Generate a correlation collapse hostile condition.
        
        This simulates a breakdown of historical correlations between assets.
        """
        # Determine if strategy relies on correlations
        uses_correlations = False
        correlation_sensitivity = 0.5  # Default sensitivity
        
        if "correlation_assumptions" in strategy_config:
            uses_correlations = True
            correlation_sensitivity = strategy_config["correlation_assumptions"].get("sensitivity", 0.5)
        
        # Calculate probability and impact
        probability = 0.2  # Base probability of correlation collapse
        impact = 70.0  # Base impact of correlation collapse
        
        # Adjust based on strategy sensitivity
        if uses_correlations:
            probability = 0.3
            impact = 70.0 + (correlation_sensitivity * 20.0)
        
        # Check for signs of correlation instability
        if "correlation" in market_data and "stability" in market_data["correlation"]:
            stability = market_data["correlation"]["stability"]
            # Lower stability means higher probability of collapse
            probability = max(probability, 1.0 - stability)
        
        # Determine if condition is present
        is_present = probability > 0.25
        
        return HostileCondition(
            name=HostileScenario.CORRELATION_COLLAPSE.value,
            description="Breakdown of historical correlations between assets",
            probability=probability,
            impact=impact,
            is_present=is_present
        )
    
    async def _generate_volatility_shock(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> HostileCondition:
        """
        Generate a volatility shock hostile condition.
        
        This simulates a sudden, extreme increase in market volatility.
        """
        # Determine strategy's volatility assumptions
        vol_tolerance = 1.0  # Default tolerance (1.0 = normal volatility)
        
        if "volatility_assumptions" in strategy_config:
            vol_tolerance = strategy_config["volatility_assumptions"].get("max_volatility", 1.0)
        
        # Calculate probability and impact
        probability = 0.15  # Base probability of volatility shock
        impact = 75.0  # Base impact of volatility shock
        
        # Adjust based on strategy tolerance
        if vol_tolerance < 1.5:
            # Strategy has low tolerance for volatility
            impact = 90.0
        elif vol_tolerance > 2.5:
            # Strategy has high tolerance for volatility
            impact = 60.0
        
        # Check for signs of volatility instability
        if "volatility" in market_data:
            vol_data = market_data["volatility"]
            
            # Check current vs normal volatility
            current_vol = vol_data.get("current", 0)
            normal_vol = vol_data.get("normal", 1)
            
            if normal_vol > 0:
                vol_ratio = current_vol / normal_vol
                
                # Higher current volatility increases probability of shock
                if vol_ratio > 1.5:
                    probability = 0.3
                
                # Check volatility of volatility (vol-of-vol)
                if "vol_of_vol" in vol_data:
                    vol_of_vol = vol_data["vol_of_vol"]
                    probability = max(probability, min(0.5, vol_of_vol))
        
        # Determine if condition is present
        is_present = probability > 0.2
        
        return HostileCondition(
            name=HostileScenario.VOLATILITY_SHOCK.value,
            description="Sudden, extreme increase in market volatility",
            probability=probability,
            impact=impact,
            is_present=is_present
        )
    
    async def _generate_liquidity_evaporation(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> HostileCondition:
        """
        Generate a liquidity evaporation hostile condition.
        
        This simulates a sudden disappearance of market liquidity.
        """
        # Determine strategy's liquidity requirements
        liquidity_requirement = 0.5  # Default requirement (0.5 = medium liquidity)
        
        if "liquidity_assumptions" in strategy_config:
            liquidity_requirement = strategy_config["liquidity_assumptions"].get("min_liquidity", 0.5)
        
        # Calculate probability and impact
        probability = 0.1  # Base probability of liquidity evaporation
        impact = 80.0  # Base impact of liquidity evaporation
        
        # Adjust based on strategy requirements
        if liquidity_requirement > 0.7:
            # Strategy requires high liquidity
            impact = 95.0
        elif liquidity_requirement < 0.3:
            # Strategy can operate with low liquidity
            impact = 50.0
        
        # Check for signs of liquidity issues
        if "liquidity" in market_data:
            liq_data = market_data["liquidity"]
            
            # Check current vs normal liquidity
            current_liq = liq_data.get("current", 1)
            normal_liq = liq_data.get("normal", 1)
            
            if normal_liq > 0:
                liq_ratio = current_liq / normal_liq
                
                # Lower current liquidity increases probability of evaporation
                if liq_ratio < 0.7:
                    probability = 0.25
                elif liq_ratio < 0.5:
                    probability = 0.4
                
                # Check liquidity stability
                if "stability" in liq_data:
                    stability = liq_data["stability"]
                    probability = max(probability, 1.0 - stability)
        
        # Determine if condition is present
        is_present = probability > 0.15
        
        return HostileCondition(
            name=HostileScenario.LIQUIDITY_EVAPORATION.value,
            description="Sudden disappearance of market liquidity",
            probability=probability,
            impact=impact,
            is_present=is_present
        )
    
    async def _generate_signal_inversion(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> HostileCondition:
        """
        Generate a signal semantic inversion hostile condition.
        
        This simulates a situation where the strategy's signals suddenly mean the opposite.
        """
        # Determine if strategy uses specific signals
        signal_types = []
        signal_robustness = 0.5  # Default robustness
        
        if "signal_assumptions" in strategy_config:
            signal_types = strategy_config["signal_assumptions"].get("types", [])
            signal_robustness = strategy_config["signal_assumptions"].get("robustness", 0.5)
        
        # Calculate probability and impact
        probability = 0.05  # Base probability of signal inversion
        impact = 85.0  # Base impact of signal inversion
        
        # Adjust based on signal robustness
        if signal_robustness < 0.4:
            # Strategy has low signal robustness
            probability = 0.15
            impact = 95.0
        elif signal_robustness > 0.7:
            # Strategy has high signal robustness
            probability = 0.03
            impact = 70.0
        
        # Check for signs of signal instability
        if "signals" in market_data:
            sig_data = market_data["signals"]
            
            # Check signal stability
            if "stability" in sig_data:
                stability = sig_data["stability"]
                probability = max(probability, 0.2 * (1.0 - stability))
            
            # Check for specific signal types
            for signal_type in signal_types:
                if signal_type in sig_data and "inversion_risk" in sig_data[signal_type]:
                    inversion_risk = sig_data[signal_type]["inversion_risk"]
                    probability = max(probability, inversion_risk)
        
        # Determine if condition is present
        is_present = probability > 0.1
        
        return HostileCondition(
            name=HostileScenario.SIGNAL_INVERSION.value,
            description="Strategy signals suddenly mean the opposite",
            probability=probability,
            impact=impact,
            is_present=is_present
        )
    
    # === Hostile scenario evaluators ===
    
    async def _evaluate_regime_inversion(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        condition: HostileCondition
    ) -> bool:
        """
        Evaluate if a strategy can survive a regime inversion.
        
        Returns True if the strategy survives, False if it fails.
        """
        # Check if strategy has explicit regime assumptions
        if "regime_assumptions" in strategy_config:
            regime_assumptions = strategy_config["regime_assumptions"]
            
            # Check if strategy is explicitly designed for multiple regimes
            regime_count = len(regime_assumptions)
            if regime_count > 1:
                # Strategy claims to work in multiple regimes
                # Check if it has specific adaptations for each
                has_adaptations = all("adaptation" in details for _, details in regime_assumptions.items())
                if has_adaptations:
                    # Strategy has specific adaptations for different regimes
                    return True
            
            # Check if strategy has a regime inversion contingency
            if "inversion_contingency" in strategy_config:
                return True
        
        # Check strategy performance in opposite regimes
        if "performance" in strategy_config and "by_regime" in strategy_config["performance"]:
            perf_by_regime = strategy_config["performance"]["by_regime"]
            
            # Get current regime
            current_regime = None
            if "regime" in market_data:
                current_regime = market_data["regime"].get("current", None)
            
            if current_regime and current_regime in perf_by_regime:
                # Check if strategy has positive performance in opposite regime
                opposite_regime = self._get_opposite_regime(current_regime)
                if opposite_regime in perf_by_regime:
                    opposite_perf = perf_by_regime[opposite_regime]
                    if opposite_perf > 0:
                        return True
        
        # Default: assume strategy fails under regime inversion
        # This is the conservative approach - strategies must prove their robustness
        return False
    
    async def _evaluate_correlation_collapse(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        condition: HostileCondition
    ) -> bool:
        """
        Evaluate if a strategy can survive a correlation collapse.
        
        Returns True if the strategy survives, False if it fails.
        """
        # Check if strategy uses correlations
        uses_correlations = False
        
        if "correlation_assumptions" in strategy_config:
            uses_correlations = True
            
            # Check if strategy has correlation collapse protection
            if strategy_config["correlation_assumptions"].get("collapse_protection", False):
                return True
        
        # If strategy doesn't use correlations, it's not affected
        if not uses_correlations:
            return True
        
        # Check if strategy has multi-asset dependencies
        if "assets" in strategy_config and len(strategy_config["assets"]) > 1:
            # Strategy uses multiple assets
            
            # Check if it has a correlation-free mode
            if strategy_config.get("correlation_free_mode", False):
                return True
            
            # Check if it has independent asset evaluation
            if strategy_config.get("independent_asset_evaluation", False):
                return True
            
            # By default, multi-asset strategies are vulnerable to correlation collapse
            return False
        
        # Single-asset strategies are generally not affected by correlation collapse
        return True
    
    async def _evaluate_volatility_shock(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        condition: HostileCondition
    ) -> bool:
        """
        Evaluate if a strategy can survive a volatility shock.
        
        Returns True if the strategy survives, False if it fails.
        """
        # Check volatility assumptions
        if "volatility_assumptions" in strategy_config:
            vol_assumptions = strategy_config["volatility_assumptions"]
            
            # Check max volatility tolerance
            max_vol = vol_assumptions.get("max_volatility", 1.0)
            
            # Volatility shock is typically 3-5x normal volatility
            shock_vol = 4.0
            
            if max_vol >= shock_vol:
                # Strategy can handle the shock level
                return True
            
            # Check if strategy has volatility circuit breakers
            if vol_assumptions.get("circuit_breakers", False):
                return True
            
            # Check if strategy has volatility scaling
            if vol_assumptions.get("volatility_scaling", False):
                return True
        
        # Check if strategy has position sizing based on volatility
        if "position_sizing" in strategy_config:
            pos_sizing = strategy_config["position_sizing"]
            if pos_sizing.get("method", "") == "volatility_based":
                return True
        
        # Check historical performance during volatility spikes
        if "performance" in strategy_config and "during_vol_spikes" in strategy_config["performance"]:
            vol_spike_perf = strategy_config["performance"]["during_vol_spikes"]
            if vol_spike_perf > 0:
                return True
        
        # Default: assume strategy fails under volatility shock
        return False
    
    async def _evaluate_liquidity_evaporation(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        condition: HostileCondition
    ) -> bool:
        """
        Evaluate if a strategy can survive liquidity evaporation.
        
        Returns True if the strategy survives, False if it fails.
        """
        # Check liquidity assumptions
        if "liquidity_assumptions" in strategy_config:
            liq_assumptions = strategy_config["liquidity_assumptions"]
            
            # Check minimum liquidity requirement
            min_liq = liq_assumptions.get("min_liquidity", 0.5)
            
            # Liquidity evaporation typically reduces liquidity to 10-20% of normal
            evaporation_liq = 0.15
            
            if min_liq <= evaporation_liq:
                # Strategy can operate with very low liquidity
                return True
            
            # Check if strategy has liquidity circuit breakers
            if liq_assumptions.get("circuit_breakers", False):
                return True
            
            # Check if strategy has adaptive execution
            if liq_assumptions.get("adaptive_execution", False):
                return True
        
        # Check execution parameters
        if "execution" in strategy_config:
            execution = strategy_config["execution"]
            
            # Check if strategy uses passive orders
            if execution.get("order_type", "") == "passive":
                return True
            
            # Check if strategy has liquidity-aware execution
            if execution.get("liquidity_aware", False):
                return True
            
            # Check if strategy has low urgency
            if execution.get("urgency", "high") == "low":
                return True
        
        # Check position size relative to liquidity
        if "position_sizing" in strategy_config:
            pos_sizing = strategy_config["position_sizing"]
            if pos_sizing.get("liquidity_constrained", False):
                return True
        
        # Default: assume strategy fails under liquidity evaporation
        return False
    
    async def _evaluate_signal_inversion(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        condition: HostileCondition
    ) -> bool:
        """
        Evaluate if a strategy can survive signal semantic inversion.
        
        Returns True if the strategy survives, False if it fails.
        """
        # Check if strategy has signal validation
        if "signal_validation" in strategy_config and strategy_config["signal_validation"]:
            return True
        
        # Check if strategy uses multiple independent signals
        if "signals" in strategy_config:
            signals = strategy_config["signals"]
            
            # Check number of independent signals
            if isinstance(signals, list) and len(signals) >= 3:
                # Strategy uses at least 3 independent signals
                # This provides some protection against single signal inversion
                return True
            
            # Check if strategy has signal consistency checks
            if isinstance(signals, dict) and signals.get("consistency_checks", False):
                return True
        
        # Check if strategy has regime-conditional signal interpretation
        if "regime_conditional_signals" in strategy_config and strategy_config["regime_conditional_signals"]:
            return True
        
        # Check if strategy has signal inversion detection
        if "signal_inversion_detection" in strategy_config and strategy_config["signal_inversion_detection"]:
            return True
        
        # Default: assume strategy fails under signal inversion
        return False
    
    def _get_opposite_regime(self, regime: str) -> str:
        """Get the opposite market regime"""
        regime_opposites = {
            "trending": "ranging",
            "ranging": "trending",
            "bullish": "bearish",
            "bearish": "bullish",
            "high_volatility": "low_volatility",
            "low_volatility": "high_volatility",
            "high_liquidity": "low_liquidity",
            "low_liquidity": "high_liquidity",
            "risk_on": "risk_off",
            "risk_off": "risk_on"
        }
        
        return regime_opposites.get(regime.lower(), "unknown")
