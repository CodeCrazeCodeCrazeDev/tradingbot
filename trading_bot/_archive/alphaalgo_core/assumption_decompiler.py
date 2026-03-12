"""
AlphaAlgo Core - Assumption Decompiler (Layer 2)

For every active strategy:
- Extract all hidden assumptions
- Identify which assumptions are currently violated
- Score assumption stress in real time

If assumption stress exceeds tolerance:
- Strategy is invalid for this regime
- Exposure contribution = 0
- No exceptions
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
    AssumptionDecompilerResult,
    StrategyAssumption,
    AssumptionViolationError
)

logger = logging.getLogger(__name__)


class AssumptionCategory(Enum):
    """Categories of hidden assumptions"""
    MARKET_STRUCTURE = "market_structure"
    CORRELATION = "correlation"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    SEASONALITY = "seasonality"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    EXECUTION = "execution"


class AssumptionDecompiler(GovernanceLayer):
    """
    Layer 2 - Assumption Decompiler
    
    Extracts hidden assumptions from strategies and evaluates them against current market conditions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("assumption_decompiler")
        self.config = config or {}
        
        # Default stress tolerance
        self.stress_tolerance = self.config.get("stress_tolerance", 75.0)  # 0-100 scale
        
        # Hidden assumption templates by strategy type
        self.assumption_templates = self._load_assumption_templates()
        
        # Cache of extracted hidden assumptions by strategy
        self.hidden_assumptions_cache = {}
        
        logger.info(f"Assumption Decompiler initialized with stress tolerance: {self.stress_tolerance}")
    
    def _load_assumption_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load assumption templates for different strategy types.
        
        These templates define common hidden assumptions for each strategy type.
        """
        templates = {
            "mean_reversion": [
                {
                    "name": "price_range_bound",
                    "description": "Price remains within historical range",
                    "category": AssumptionCategory.MEAN_REVERSION.value,
                    "threshold": 0.7,  # Minimum probability of range-bound behavior
                    "extraction_function": self._extract_range_bound_assumption
                },
                {
                    "name": "mean_exists",
                    "description": "A stable mean exists for the instrument",
                    "category": AssumptionCategory.MEAN_REVERSION.value,
                    "threshold": 0.6,  # Minimum stability of mean
                    "extraction_function": self._extract_mean_stability_assumption
                },
                {
                    "name": "reversion_speed",
                    "description": "Price reverts to mean within expected timeframe",
                    "category": AssumptionCategory.MEAN_REVERSION.value,
                    "threshold": 0.5,  # Minimum reversion speed ratio
                    "extraction_function": self._extract_reversion_speed_assumption
                }
            ],
            "trend_following": [
                {
                    "name": "trend_persistence",
                    "description": "Trends persist long enough to be profitable",
                    "category": AssumptionCategory.TREND_FOLLOWING.value,
                    "threshold": 0.6,  # Minimum trend persistence
                    "extraction_function": self._extract_trend_persistence_assumption
                },
                {
                    "name": "low_false_breakouts",
                    "description": "Breakouts are genuine, not false",
                    "category": AssumptionCategory.TREND_FOLLOWING.value,
                    "threshold": 0.7,  # Maximum false breakout ratio
                    "extraction_function": self._extract_false_breakout_assumption
                }
            ],
            "volatility": [
                {
                    "name": "vol_clustering",
                    "description": "Volatility exhibits clustering behavior",
                    "category": AssumptionCategory.VOLATILITY.value,
                    "threshold": 0.6,  # Minimum volatility clustering
                    "extraction_function": self._extract_vol_clustering_assumption
                },
                {
                    "name": "vol_mean_reversion",
                    "description": "Volatility reverts to mean",
                    "category": AssumptionCategory.VOLATILITY.value,
                    "threshold": 0.5,  # Minimum vol mean reversion
                    "extraction_function": self._extract_vol_mean_reversion_assumption
                }
            ],
            "momentum": [
                {
                    "name": "momentum_persistence",
                    "description": "Momentum persists over the strategy timeframe",
                    "category": AssumptionCategory.TREND_FOLLOWING.value,
                    "threshold": 0.6,  # Minimum momentum persistence
                    "extraction_function": self._extract_momentum_persistence_assumption
                },
                {
                    "name": "low_momentum_crashes",
                    "description": "Momentum doesn't experience sudden crashes",
                    "category": AssumptionCategory.TREND_FOLLOWING.value,
                    "threshold": 0.7,  # Maximum momentum crash probability
                    "extraction_function": self._extract_momentum_crash_assumption
                }
            ],
            "arbitrage": [
                {
                    "name": "price_convergence",
                    "description": "Price differentials converge within expected timeframe",
                    "category": AssumptionCategory.MARKET_STRUCTURE.value,
                    "threshold": 0.7,  # Minimum convergence probability
                    "extraction_function": self._extract_price_convergence_assumption
                },
                {
                    "name": "execution_speed",
                    "description": "Execution is fast enough to capture arbitrage",
                    "category": AssumptionCategory.EXECUTION.value,
                    "threshold": 0.8,  # Minimum execution speed ratio
                    "extraction_function": self._extract_execution_speed_assumption
                }
            ],
            # Add more strategy types as needed
        }
        
        # Add common assumptions that apply to all strategies
        common_assumptions = [
            {
                "name": "normal_liquidity",
                "description": "Market liquidity is within normal range",
                "category": AssumptionCategory.LIQUIDITY.value,
                "threshold": 0.6,  # Minimum liquidity ratio
                "extraction_function": self._extract_liquidity_assumption
            },
            {
                "name": "stable_correlation",
                "description": "Correlations between assets remain stable",
                "category": AssumptionCategory.CORRELATION.value,
                "threshold": 0.7,  # Minimum correlation stability
                "extraction_function": self._extract_correlation_stability_assumption
            },
            {
                "name": "normal_spread",
                "description": "Bid-ask spreads remain within normal range",
                "category": AssumptionCategory.EXECUTION.value,
                "threshold": 0.7,  # Maximum spread ratio
                "extraction_function": self._extract_spread_assumption
            }
        ]
        
        # Add common assumptions to all strategy types
        for strategy_type in templates:
            templates[strategy_type].extend(common_assumptions)
        
        return templates
    
    async def _extract_hidden_assumptions(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any]
    ) -> List[StrategyAssumption]:
        """
        Extract hidden assumptions from a strategy based on its type and configuration.
        """
        # Check cache first
        if strategy_id in self.hidden_assumptions_cache:
            return self.hidden_assumptions_cache[strategy_id]
        
        hidden_assumptions = []
        
        # Determine strategy type(s)
        strategy_types = strategy_config.get("strategy_types", [])
        if isinstance(strategy_types, str):
            strategy_types = [strategy_types]
        
        if not strategy_types:
            # Try to infer strategy type from other fields
            if "mean_reversion" in strategy_config.get("name", "").lower():
                strategy_types.append("mean_reversion")
            elif "trend" in strategy_config.get("name", "").lower():
                strategy_types.append("trend_following")
            elif "momentum" in strategy_config.get("name", "").lower():
                strategy_types.append("momentum")
            elif "volatility" in strategy_config.get("name", "").lower():
                strategy_types.append("volatility")
            elif "arbitrage" in strategy_config.get("name", "").lower():
                strategy_types.append("arbitrage")
            else:
                # Default to common assumptions only
                strategy_types = ["common"]
        
        # Add common assumptions if not already included
        if "common" not in strategy_types:
            strategy_types.append("common")
        
        # Collect assumptions from all applicable strategy types
        for strategy_type in strategy_types:
            if strategy_type in self.assumption_templates:
                for template in self.assumption_templates[strategy_type]:
                    # Create assumption from template
                    assumption = StrategyAssumption(
                        name=template["name"],
                        description=template["description"],
                        current_value=0.0,  # Will be set during evaluation
                        threshold=template["threshold"],
                        is_valid=True,  # Will be set during evaluation
                        stress_score=0.0  # Will be set during evaluation
                    )
                    hidden_assumptions.append(assumption)
        
        # Cache for future use
        self.hidden_assumptions_cache[strategy_id] = hidden_assumptions
        
        return hidden_assumptions
    
    async def _evaluate_hidden_assumptions(
        self,
        assumptions: List[StrategyAssumption],
        market_data: Dict[str, Any]
    ) -> Tuple[List[StrategyAssumption], List[StrategyAssumption]]:
        """
        Evaluate hidden assumptions against current market data.
        
        Returns:
            Tuple of (all_assumptions, violated_assumptions)
        """
        violated = []
        
        for assumption in assumptions:
            # Get extraction function based on assumption name
            extraction_func = getattr(self, f"_extract_{assumption.name}_value", None)
            
            if extraction_func:
                # Use specific extraction function
                assumption.current_value = await extraction_func(market_data)
            else:
                # Use generic extraction based on category
                category = next((t["category"] for t in sum(self.assumption_templates.values(), []) 
                               if t["name"] == assumption.name), None)
                
                if category:
                    assumption.current_value = await self._extract_generic_value(category, assumption.name, market_data)
                else:
                    # Default to threshold (neutral)
                    assumption.current_value = assumption.threshold
            
            # Determine validity
            assumption.is_valid = assumption.current_value >= assumption.threshold
            
            # Calculate stress score (0-100)
            if assumption.threshold > 0:
                assumption.stress_score = max(0, 100 - (assumption.current_value / assumption.threshold) * 100)
            else:
                assumption.stress_score = 0
            
            # Add to violated list if not valid
            if not assumption.is_valid:
                violated.append(assumption)
        
        return assumptions, violated
    
    async def process(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> AssumptionDecompilerResult:
        """
        Process a strategy to extract and evaluate hidden assumptions.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_config: Strategy configuration
            market_data: Current market data
            
        Returns:
            AssumptionDecompilerResult with validity determination
        """
        try:
            # Extract hidden assumptions
            hidden_assumptions = await self._extract_hidden_assumptions(strategy_id, strategy_config)
            
            if not hidden_assumptions:
                return AssumptionDecompilerResult(
                    strategy_id=strategy_id,
                    hidden_assumptions=[],
                    violated_assumptions=[],
                    assumption_stress=0.0,
                    is_valid=False,
                    reason="No hidden assumptions could be extracted"
                )
            
            # Evaluate hidden assumptions
            evaluated_assumptions, violated_assumptions = await self._evaluate_hidden_assumptions(
                hidden_assumptions, market_data
            )
            
            # Calculate average stress score
            avg_stress = sum(a.stress_score for a in evaluated_assumptions) / len(evaluated_assumptions)
            
            # Check if stress exceeds tolerance
            if avg_stress > self.stress_tolerance:
                return AssumptionDecompilerResult(
                    strategy_id=strategy_id,
                    hidden_assumptions=evaluated_assumptions,
                    violated_assumptions=violated_assumptions,
                    assumption_stress=avg_stress,
                    is_valid=False,
                    reason=f"Assumption stress exceeds tolerance ({avg_stress:.1f}% > {self.stress_tolerance:.1f}%)"
                )
            
            # Check if any assumptions are violated
            if violated_assumptions:
                violated_names = [a.name for a in violated_assumptions]
                return AssumptionDecompilerResult(
                    strategy_id=strategy_id,
                    hidden_assumptions=evaluated_assumptions,
                    violated_assumptions=violated_assumptions,
                    assumption_stress=avg_stress,
                    is_valid=False,
                    reason=f"Violated assumptions: {', '.join(violated_names)}"
                )
            
            # All assumptions valid and stress within tolerance
            return AssumptionDecompilerResult(
                strategy_id=strategy_id,
                hidden_assumptions=evaluated_assumptions,
                violated_assumptions=[],
                assumption_stress=avg_stress,
                is_valid=True,
                reason="All hidden assumptions valid"
            )
            
        except Exception as e:
            logger.exception(f"Error in assumption decompiler: {e}")
            return AssumptionDecompilerResult(
                strategy_id=strategy_id,
                hidden_assumptions=[],
                violated_assumptions=[],
                assumption_stress=100.0,  # Maximum stress on error
                is_valid=False,
                reason=f"Error in assumption evaluation: {str(e)}"
            )
    
    # === Extraction functions for specific assumptions ===
    
    async def _extract_generic_value(self, category: str, name: str, market_data: Dict[str, Any]) -> float:
        """Generic extraction function for when a specific one isn't available"""
        # Try to find the value in market data
        if category in market_data and name in market_data[category]:
            return float(market_data[category][name])
        
        # Try direct lookup
        if name in market_data:
            return float(market_data[name])
        
        # Default to neutral value (0.5)
        return 0.5
    
    async def _extract_range_bound_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract range-bound probability from market data"""
        if "mean_reversion" in market_data and "range_bound_probability" in market_data["mean_reversion"]:
            return float(market_data["mean_reversion"]["range_bound_probability"])
        
        # Simple heuristic based on price vs bollinger bands
        if "technicals" in market_data and "bollinger" in market_data["technicals"]:
            bb = market_data["technicals"]["bollinger"]
            price = market_data.get("price", {}).get("close", 0)
            
            if price and "upper" in bb and "lower" in bb:
                # Check if price is within bands
                upper = bb["upper"]
                lower = bb["lower"]
                
                if lower <= price <= upper:
                    # Calculate how far from edges (1.0 = middle, 0.0 = at band)
                    band_width = upper - lower
                    if band_width > 0:
                        center = (upper + lower) / 2
                        distance_from_center = abs(price - center)
                        position = 1.0 - (distance_from_center / (band_width / 2))
                        return max(0.0, min(1.0, position))
        
        # Default to neutral
        return 0.5
    
    async def _extract_mean_stability_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract mean stability from market data"""
        if "mean_reversion" in market_data and "mean_stability" in market_data["mean_reversion"]:
            return float(market_data["mean_reversion"]["mean_stability"])
        
        # Simple heuristic based on moving average stability
        if "technicals" in market_data and "moving_averages" in market_data["technicals"]:
            mas = market_data["technicals"]["moving_averages"]
            
            if "ma_50" in mas and "ma_200" in mas:
                ma_50 = mas["ma_50"]
                ma_200 = mas["ma_200"]
                
                # Calculate stability as inverse of normalized difference
                if ma_200 > 0:
                    diff = abs(ma_50 - ma_200) / ma_200
                    stability = 1.0 - min(1.0, diff)
                    return stability
        
        # Default to neutral
        return 0.5
    
    async def _extract_reversion_speed_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract reversion speed from market data"""
        if "mean_reversion" in market_data and "reversion_speed" in market_data["mean_reversion"]:
            return float(market_data["mean_reversion"]["reversion_speed"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_trend_persistence_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract trend persistence from market data"""
        if "trend" in market_data and "persistence" in market_data["trend"]:
            return float(market_data["trend"]["persistence"])
        
        # Simple heuristic based on ADX
        if "technicals" in market_data and "adx" in market_data["technicals"]:
            adx = market_data["technicals"]["adx"]
            
            # ADX > 25 indicates strong trend
            # Normalize to 0-1
            return min(1.0, adx / 50.0)
        
        # Default to neutral
        return 0.5
    
    async def _extract_false_breakout_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract false breakout probability from market data"""
        if "trend" in market_data and "false_breakout_ratio" in market_data["trend"]:
            # Invert because lower false breakout ratio is better
            return 1.0 - float(market_data["trend"]["false_breakout_ratio"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_vol_clustering_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract volatility clustering from market data"""
        if "volatility" in market_data and "clustering" in market_data["volatility"]:
            return float(market_data["volatility"]["clustering"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_vol_mean_reversion_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract volatility mean reversion from market data"""
        if "volatility" in market_data and "mean_reversion" in market_data["volatility"]:
            return float(market_data["volatility"]["mean_reversion"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_momentum_persistence_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract momentum persistence from market data"""
        if "momentum" in market_data and "persistence" in market_data["momentum"]:
            return float(market_data["momentum"]["persistence"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_momentum_crash_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract momentum crash probability from market data"""
        if "momentum" in market_data and "crash_probability" in market_data["momentum"]:
            # Invert because lower crash probability is better
            return 1.0 - float(market_data["momentum"]["crash_probability"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_price_convergence_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract price convergence probability from market data"""
        if "arbitrage" in market_data and "convergence_probability" in market_data["arbitrage"]:
            return float(market_data["arbitrage"]["convergence_probability"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_execution_speed_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract execution speed ratio from market data"""
        if "execution" in market_data and "speed_ratio" in market_data["execution"]:
            return float(market_data["execution"]["speed_ratio"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_liquidity_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract liquidity ratio from market data"""
        if "liquidity" in market_data and "ratio" in market_data["liquidity"]:
            return float(market_data["liquidity"]["ratio"])
        
        # Simple heuristic based on volume
        if "volume" in market_data:
            current_volume = market_data["volume"].get("current", 0)
            avg_volume = market_data["volume"].get("average", 0)
            
            if avg_volume > 0:
                return min(1.0, current_volume / avg_volume)
        
        # Default to neutral
        return 0.5
    
    async def _extract_correlation_stability_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract correlation stability from market data"""
        if "correlation" in market_data and "stability" in market_data["correlation"]:
            return float(market_data["correlation"]["stability"])
        
        # Default to neutral
        return 0.5
    
    async def _extract_spread_assumption(self, market_data: Dict[str, Any]) -> float:
        """Extract spread ratio from market data"""
        if "spread" in market_data and "ratio" in market_data["spread"]:
            # Invert because lower spread ratio is better
            spread_ratio = float(market_data["spread"]["ratio"])
            return 1.0 - min(1.0, max(0.0, spread_ratio - 1.0))
        
        # Simple heuristic based on current vs average spread
        if "spread" in market_data:
            current_spread = market_data["spread"].get("current", 0)
            avg_spread = market_data["spread"].get("average", 0)
            
            if avg_spread > 0:
                spread_ratio = current_spread / avg_spread
                # Invert because lower spread ratio is better
                return 1.0 - min(1.0, max(0.0, spread_ratio - 1.0))
        
        # Default to neutral
        return 0.5
