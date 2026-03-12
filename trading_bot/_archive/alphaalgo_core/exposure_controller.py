"""
AlphaAlgo Core - Exposure Controller (Layer 4)

The only real brain of the system. Does NOT allocate capital by confidence.

Allocates exposure based on:
- Worst-case drawdown under hostile regimes
- Loss convexity
- Recovery half-life
- Error autocorrelation
- Regime persistence probability
- Entropy stability

If loss convexity is asymmetric: Exposure is throttled automatically.
If recovery is slow: Exposure decays aggressively.
If uncertainty spikes: Exposure → 0.
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
    ExposureControllerResult,
    ExposureState,
    ExposureError
)

logger = logging.getLogger(__name__)


class ExposureController(GovernanceLayer):
    """
    Layer 4 - Exposure Controller
    
    Controls the maximum allowable exposure for each strategy based on risk metrics.
    This is the only component that can set exposure levels.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("exposure_controller")
        self.config = config or {}
        
        # Default risk parameters
        self.risk_params = {
            "max_portfolio_exposure": self.config.get("max_portfolio_exposure", 1.0),
            "max_strategy_exposure": self.config.get("max_strategy_exposure", 0.5),
            "max_drawdown_tolerance": self.config.get("max_drawdown_tolerance", 0.15),  # 15% max drawdown
            "recovery_threshold": self.config.get("recovery_threshold", 2.0),  # Recovery should take < 2x drawdown time
            "uncertainty_threshold": self.config.get("uncertainty_threshold", 0.7),  # Uncertainty > 0.7 reduces exposure
            "convexity_threshold": self.config.get("convexity_threshold", 1.5),  # Loss convexity > 1.5 reduces exposure
            "autocorrelation_threshold": self.config.get("autocorrelation_threshold", 0.3),  # Error autocorr > 0.3 reduces exposure
        }
        
        # Strategy exposure history
        self.exposure_history = {}
        
        # Strategy risk metrics history
        self.risk_metrics_history = {}
        
        logger.info(f"Exposure Controller initialized with risk parameters: {self.risk_params}")
    
    async def process(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> ExposureControllerResult:
        """
        Process a strategy to determine its maximum allowable exposure.
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_config: Strategy configuration
            market_data: Current market data
            
        Returns:
            ExposureControllerResult with exposure determination
        """
        try:
            # Calculate risk metrics
            risk_metrics = await self._calculate_risk_metrics(strategy_id, strategy_config, market_data)
            
            # Store risk metrics history
            if strategy_id not in self.risk_metrics_history:
                self.risk_metrics_history[strategy_id] = []
            self.risk_metrics_history[strategy_id].append(risk_metrics)
            
            # Limit history size
            max_history = 100
            if len(self.risk_metrics_history[strategy_id]) > max_history:
                self.risk_metrics_history[strategy_id] = self.risk_metrics_history[strategy_id][-max_history:]
            
            # Determine exposure state
            exposure_state, reason = self._determine_exposure_state(strategy_id, risk_metrics)
            
            # Calculate maximum exposure
            max_exposure = self._calculate_max_exposure(strategy_id, risk_metrics, exposure_state)
            
            # Store exposure history
            if strategy_id not in self.exposure_history:
                self.exposure_history[strategy_id] = []
            self.exposure_history[strategy_id].append(max_exposure)
            
            # Limit history size
            if len(self.exposure_history[strategy_id]) > max_history:
                self.exposure_history[strategy_id] = self.exposure_history[strategy_id][-max_history:]
            
            # Create result
            result = ExposureControllerResult(
                strategy_id=strategy_id,
                max_exposure=max_exposure,
                state=exposure_state,
                reason=reason,
                metrics=risk_metrics
            )
            
            # Log decision
            level = "info" if max_exposure > 0 else "warning"
            self.log_decision(max_exposure, reason, level)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in exposure controller: {e}")
            return ExposureControllerResult(
                strategy_id=strategy_id,
                max_exposure=0.0,  # Zero exposure on error (safety first)
                state=ExposureState.ZERO,
                reason=f"Error in exposure calculation: {str(e)}",
                metrics={}
            )
    
    async def _calculate_risk_metrics(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate risk metrics for a strategy.
        
        Returns a dictionary of risk metrics.
        """
        metrics = {}
        
        # 1. Worst-case drawdown under hostile regimes
        metrics["worst_case_drawdown"] = await self._calculate_worst_case_drawdown(
            strategy_id, strategy_config, market_data
        )
        
        # 2. Loss convexity
        metrics["loss_convexity"] = await self._calculate_loss_convexity(
            strategy_id, strategy_config, market_data
        )
        
        # 3. Recovery half-life
        metrics["recovery_half_life"] = await self._calculate_recovery_half_life(
            strategy_id, strategy_config, market_data
        )
        
        # 4. Error autocorrelation
        metrics["error_autocorrelation"] = await self._calculate_error_autocorrelation(
            strategy_id, strategy_config, market_data
        )
        
        # 5. Regime persistence probability
        metrics["regime_persistence"] = await self._calculate_regime_persistence(
            strategy_id, strategy_config, market_data
        )
        
        # 6. Entropy stability
        metrics["entropy_stability"] = await self._calculate_entropy_stability(
            strategy_id, strategy_config, market_data
        )
        
        # 7. Uncertainty
        metrics["uncertainty"] = await self._calculate_uncertainty(
            strategy_id, strategy_config, market_data
        )
        
        return metrics
    
    def _determine_exposure_state(
        self,
        strategy_id: str,
        risk_metrics: Dict[str, float]
    ) -> Tuple[ExposureState, str]:
        """
        Determine the exposure state based on risk metrics.
        
        Returns a tuple of (state, reason).
        """
        # Check for uncertainty spike
        if risk_metrics["uncertainty"] > self.risk_params["uncertainty_threshold"]:
            return ExposureState.ZERO, f"Uncertainty spike ({risk_metrics['uncertainty']:.2f} > {self.risk_params['uncertainty_threshold']:.2f})"
        
        # Check for asymmetric loss convexity
        if risk_metrics["loss_convexity"] > self.risk_params["convexity_threshold"]:
            return ExposureState.THROTTLED, f"Asymmetric loss convexity ({risk_metrics['loss_convexity']:.2f} > {self.risk_params['convexity_threshold']:.2f})"
        
        # Check for slow recovery
        if risk_metrics["recovery_half_life"] > self.risk_params["recovery_threshold"]:
            return ExposureState.DECAYING, f"Slow recovery ({risk_metrics['recovery_half_life']:.2f} > {self.risk_params['recovery_threshold']:.2f})"
        
        # Check for high error autocorrelation
        if risk_metrics["error_autocorrelation"] > self.risk_params["autocorrelation_threshold"]:
            return ExposureState.THROTTLED, f"High error autocorrelation ({risk_metrics['error_autocorrelation']:.2f} > {self.risk_params['autocorrelation_threshold']:.2f})"
        
        # Default to normal state
        return ExposureState.NORMAL, "Normal exposure conditions"
    
    def _calculate_max_exposure(
        self,
        strategy_id: str,
        risk_metrics: Dict[str, float],
        exposure_state: ExposureState
    ) -> float:
        """
        Calculate the maximum allowable exposure based on risk metrics and state.
        
        Returns a float between 0 and 1.
        """
        # Start with the maximum strategy exposure
        max_exposure = self.risk_params["max_strategy_exposure"]
        
        # Adjust based on worst-case drawdown
        drawdown_factor = 1.0 - (risk_metrics["worst_case_drawdown"] / self.risk_params["max_drawdown_tolerance"])
        drawdown_factor = max(0.0, min(1.0, drawdown_factor))
        max_exposure *= drawdown_factor
        
        # Adjust based on exposure state
        if exposure_state == ExposureState.ZERO:
            return 0.0
        elif exposure_state == ExposureState.THROTTLED:
            # Reduce exposure by 50-80% depending on metrics
            throttle_factor = 0.5 - (0.3 * (risk_metrics["uncertainty"] / self.risk_params["uncertainty_threshold"]))
            throttle_factor = max(0.2, min(0.5, throttle_factor))
            max_exposure *= throttle_factor
        elif exposure_state == ExposureState.DECAYING:
            # Apply exponential decay based on history
            if strategy_id in self.exposure_history and len(self.exposure_history[strategy_id]) > 0:
                previous_exposure = self.exposure_history[strategy_id][-1]
                decay_factor = 0.9  # 10% decay per period
                max_exposure = min(max_exposure, previous_exposure * decay_factor)
        
        # Ensure exposure is within bounds
        max_exposure = max(0.0, min(self.risk_params["max_strategy_exposure"], max_exposure))
        
        return max_exposure
    
    # === Risk metric calculation methods ===
    
    async def _calculate_worst_case_drawdown(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> float:
        """
        Calculate the worst-case drawdown under hostile regimes.
        
        Returns a float representing the expected worst-case drawdown.
        """
        # Check if strategy has historical drawdown data
        if "performance" in strategy_config and "max_drawdown" in strategy_config["performance"]:
            historical_dd = strategy_config["performance"]["max_drawdown"]
            
            # Check if strategy has worst-case drawdown data
            if "worst_case_drawdown" in strategy_config["performance"]:
                return strategy_config["performance"]["worst_case_drawdown"]
            
            # Apply a safety multiplier to historical drawdown
            safety_multiplier = 1.5
            return historical_dd * safety_multiplier
        
        # Check if market data includes risk metrics
        if "risk" in market_data and "expected_drawdown" in market_data["risk"]:
            return market_data["risk"]["expected_drawdown"]
        
        # Default to a conservative estimate
        return 0.2  # Assume 20% worst-case drawdown
    
    async def _calculate_loss_convexity(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> float:
        """
        Calculate the loss convexity (asymmetry of losses vs gains).
        
        Returns a float where 1.0 is symmetric, >1.0 is convex (losses larger than gains).
        """
        # Check if strategy has loss convexity data
        if "performance" in strategy_config and "loss_convexity" in strategy_config["performance"]:
            return strategy_config["performance"]["loss_convexity"]
        
        # Check if market data includes risk metrics
        if "risk" in market_data and "loss_convexity" in market_data["risk"]:
            return market_data["risk"]["loss_convexity"]
        
        # Check if we have return distribution data
        if "returns" in market_data:
            returns = market_data["returns"]
            
            if isinstance(returns, list) and len(returns) > 0:
                # Calculate loss convexity from return distribution
                returns_array = np.array(returns)
                gains = returns_array[returns_array > 0]
                losses = returns_array[returns_array < 0]
                
                if len(gains) > 0 and len(losses) > 0:
                    avg_gain = np.mean(gains)
                    avg_loss = abs(np.mean(losses))
                    
                    if avg_gain > 0:
                        return avg_loss / avg_gain
        
        # Default to slightly convex
        return 1.2
    
    async def _calculate_recovery_half_life(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> float:
        """
        Calculate the recovery half-life (how long it takes to recover from drawdowns).
        
        Returns a float representing the ratio of recovery time to drawdown time.
        """
        # Check if strategy has recovery data
        if "performance" in strategy_config and "recovery_ratio" in strategy_config["performance"]:
            return strategy_config["performance"]["recovery_ratio"]
        
        # Check if market data includes risk metrics
        if "risk" in market_data and "recovery_half_life" in market_data["risk"]:
            return market_data["risk"]["recovery_half_life"]
        
        # Default to moderate recovery time
        return 1.5
    
    async def _calculate_error_autocorrelation(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> float:
        """
        Calculate the error autocorrelation (tendency for errors to cluster).
        
        Returns a float between 0 and 1, where higher values indicate stronger autocorrelation.
        """
        # Check if strategy has error autocorrelation data
        if "performance" in strategy_config and "error_autocorrelation" in strategy_config["performance"]:
            return strategy_config["performance"]["error_autocorrelation"]
        
        # Check if market data includes risk metrics
        if "risk" in market_data and "error_autocorrelation" in market_data["risk"]:
            return market_data["risk"]["error_autocorrelation"]
        
        # Check if we have error history
        if "errors" in market_data and isinstance(market_data["errors"], list) and len(market_data["errors"]) > 1:
            errors = np.array(market_data["errors"])
            
            # Calculate lag-1 autocorrelation
            n = len(errors)
            if n > 1:
                lag_1_autocorr = np.corrcoef(errors[:-1], errors[1:])[0, 1]
                return abs(lag_1_autocorr)
        
        # Default to moderate autocorrelation
        return 0.2
    
    async def _calculate_regime_persistence(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> float:
        """
        Calculate the regime persistence probability.
        
        Returns a float between 0 and 1, where higher values indicate more stable regimes.
        """
        # Check if market data includes regime information
        if "regime" in market_data and "persistence" in market_data["regime"]:
            return market_data["regime"]["persistence"]
        
        # Default to moderate persistence
        return 0.7
    
    async def _calculate_entropy_stability(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> float:
        """
        Calculate the entropy stability (consistency of market randomness).
        
        Returns a float between 0 and 1, where higher values indicate more stable entropy.
        """
        # Check if market data includes entropy information
        if "entropy" in market_data and "stability" in market_data["entropy"]:
            return market_data["entropy"]["stability"]
        
        # Default to moderate stability
        return 0.6
    
    async def _calculate_uncertainty(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> float:
        """
        Calculate the overall uncertainty level.
        
        Returns a float between 0 and 1, where higher values indicate more uncertainty.
        """
        # Start with a base uncertainty
        uncertainty = 0.3
        
        # Factors that increase uncertainty
        uncertainty_factors = []
        
        # Check if market data includes volatility information
        if "volatility" in market_data:
            vol_data = market_data["volatility"]
            
            # Volatility ratio (current / normal)
            if "current" in vol_data and "normal" in vol_data and vol_data["normal"] > 0:
                vol_ratio = vol_data["current"] / vol_data["normal"]
                uncertainty_factors.append(min(1.0, (vol_ratio - 1.0) / 3.0))
            
            # Volatility of volatility
            if "vol_of_vol" in vol_data:
                uncertainty_factors.append(min(1.0, vol_data["vol_of_vol"]))
        
        # Check if market data includes liquidity information
        if "liquidity" in market_data:
            liq_data = market_data["liquidity"]
            
            # Liquidity ratio (normal / current) - inverted because lower liquidity = higher uncertainty
            if "current" in liq_data and "normal" in liq_data and liq_data["current"] > 0:
                liq_ratio = liq_data["normal"] / liq_data["current"]
                uncertainty_factors.append(min(1.0, (liq_ratio - 1.0) / 2.0))
        
        # Check if market data includes regime information
        if "regime" in market_data:
            regime_data = market_data["regime"]
            
            # Regime transition probability
            if "transition_probability" in regime_data:
                uncertainty_factors.append(regime_data["transition_probability"])
        
        # Check if market data includes correlation information
        if "correlation" in market_data:
            corr_data = market_data["correlation"]
            
            # Correlation stability (inverted because lower stability = higher uncertainty)
            if "stability" in corr_data:
                uncertainty_factors.append(1.0 - corr_data["stability"])
        
        # Combine uncertainty factors
        if uncertainty_factors:
            # Use a weighted average
            combined_factor = sum(uncertainty_factors) / len(uncertainty_factors)
            
            # Apply a non-linear transformation to make high uncertainty more impactful
            uncertainty = 0.3 + (0.7 * combined_factor * combined_factor)
        
        return min(1.0, uncertainty)
