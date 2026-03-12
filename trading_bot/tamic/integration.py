"""
TAMIC Integration with AlphaAlgo Core

This module implements the integration between TAMIC and AlphaAlgo Core,
allowing TAMIC to be used as a governance layer in the Capital Governance System.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from trading_bot.alphaalgo_core.capital_governance import GovernanceLayer, CapitalGovernanceResult
from .core import TAMIC, TimeHorizon, MarketTimeState, TAMICDecision

logger = logging.getLogger(__name__)


@dataclass
class TAMICGovernanceResult:
    """Result from TAMIC governance layer"""
    is_tradable: bool
    max_exposure: float
    reason: str
    time_horizon: TimeHorizon
    market_time_state: MarketTimeState
    confidence_level: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class TAMICGovernanceLayer(GovernanceLayer):
    """
    TAMIC Governance Layer for AlphaAlgo Core Capital Governance System
    
    Integrates TAMIC as a governance layer in the Capital Governance System,
    providing time-aware market intelligence for trading decisions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize TAMICGovernanceLayer.
        
        Args:
            config: Configuration parameters
        """
        try:
            super().__init__("tamic_governance_layer")
            self.config = config or {}
            self.logger = logging.getLogger("trading_bot.tamic.integration")
        
            # Create TAMIC instance
            from .core import create_tamic
            self.tamic = create_tamic(self.config.get("tamic_config", {}))
        
            # Initialize components if not already done
            self._initialize_components()
        
            self.logger.info("TAMIC Governance Layer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def _initialize_components(self):
        """Initialize TAMIC components"""
        # Check if components are already initialized
        try:
            if not self.tamic.components:
                # Initialize components
                from .horizon_segmentation import HorizonSegmentation
                from .signal_decay import SignalDecay
                from .market_time import MarketTimeEngine
                from .time_risk import TimeBasedRiskManager
                from .institutional_time import InstitutionalTimeEngine
                from .optionality import OptionalityPreservationEngine
                from .confidence_control import ConfidenceHumilityControl
                from .forbidden_behaviors import ForbiddenBehaviorGuard
            
                # Add components
                self.tamic.add_component("horizon_segmentation", HorizonSegmentation())
                self.tamic.add_component("signal_decay", SignalDecay())
                self.tamic.add_component("market_time", MarketTimeEngine())
                self.tamic.add_component("time_risk", TimeBasedRiskManager())
                self.tamic.add_component("institutional_time", InstitutionalTimeEngine())
                self.tamic.add_component("optionality", OptionalityPreservationEngine())
                self.tamic.add_component("confidence_control", ConfidenceHumilityControl())
                self.tamic.add_component("forbidden_behaviors", ForbiddenBehaviorGuard())
        except Exception as e:
            logger.error(f"Error in _initialize_components: {e}")
            raise
    
    def _map_time_horizon(self, strategy_config: Dict[str, Any]) -> TimeHorizon:
        """
        Map strategy configuration to TAMIC time horizon.
        
        Args:
            strategy_config: Strategy configuration
            
        Returns:
            TimeHorizon for TAMIC
        """
        # Get strategy time horizon
        try:
            strategy_horizon = strategy_config.get("time_horizon", "").lower()
        
            # Map to TAMIC time horizon
            if strategy_horizon in ["microstructure", "ultra_short", "tick", "seconds", "minutes"]:
                return TimeHorizon.MICROSTRUCTURE
            elif strategy_horizon in ["intraday", "day", "hours"]:
                return TimeHorizon.INTRADAY
            elif strategy_horizon in ["short_swing", "swing", "days"]:
                return TimeHorizon.SHORT_SWING
            elif strategy_horizon in ["medium", "medium_term", "weeks"]:
                return TimeHorizon.MEDIUM_HORIZON
            else:
                # Default to intraday
                self.logger.warning(f"Unknown strategy horizon '{strategy_horizon}', defaulting to INTRADAY")
                return TimeHorizon.INTRADAY
        except Exception as e:
            logger.error(f"Error in _map_time_horizon: {e}")
            raise
    
    def _prepare_market_data(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare market data for TAMIC.
        
        Args:
            symbol: Market symbol
            market_data: Market data from AlphaAlgo Core
            strategy_config: Strategy configuration
            
        Returns:
            Prepared market data for TAMIC
        """
        # Start with original market data
        try:
            prepared_data = market_data.copy()
        
            # Add strategy-specific data
            prepared_data["strategy_id"] = strategy_config.get("strategy_id", "unknown")
            prepared_data["strategy_type"] = strategy_config.get("strategy_type", "unknown")
            prepared_data["strategy_horizon"] = strategy_config.get("time_horizon", "unknown")
        
            # Add timestamp if not present
            if "timestamp" not in prepared_data:
                prepared_data["timestamp"] = time.time()
        
            # Add symbol if not present
            if "symbol" not in prepared_data:
                prepared_data["symbol"] = symbol
        
            return prepared_data
        except Exception as e:
            logger.error(f"Error in _prepare_market_data: {e}")
            raise
    
    async def process(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        strategy_id: str = None,
        strategy_config: Dict[str, Any] = None
    ) -> TAMICGovernanceResult:
        """
        Process market data and make a governance decision.
        
        Args:
            symbol: Market symbol
            market_data: Market data
            strategy_id: Strategy ID (optional)
            strategy_config: Strategy configuration (optional)
            
        Returns:
            TAMICGovernanceResult with governance decision
        """
        try:
            self.logger.info(f"Processing {symbol} with TAMIC governance layer")
        
            # Use empty dict if strategy_config is None
            strategy_config = strategy_config or {}
        
            # Add strategy_id to strategy_config if provided
            if strategy_id and "strategy_id" not in strategy_config:
                strategy_config["strategy_id"] = strategy_id
        
            # Map strategy configuration to TAMIC time horizon
            horizon = self._map_time_horizon(strategy_config)
        
            # Prepare market data for TAMIC
            prepared_data = self._prepare_market_data(symbol, market_data, strategy_config)
        
            # Evaluate market with TAMIC
            decision = await self.tamic.evaluate_market(
                symbol=symbol,
                horizon=horizon,
                market_data=prepared_data
            )
        
            # Create governance result
            result = TAMICGovernanceResult(
                is_tradable=decision.is_trade_recommended,
                max_exposure=decision.exposure_recommendation,
                reason=decision.no_trade_reason or "TAMIC evaluation",
                time_horizon=decision.time_horizon,
                market_time_state=decision.market_time_state,
                confidence_level=decision.confidence_level,
                metrics=decision.metrics
            )
        
            # Log result
            if result.is_tradable:
                self.logger.info(f"{symbol}: Tradable with {result.max_exposure:.2f} max exposure, "
                                f"confidence {result.confidence_level:.2f}")
            else:
                self.logger.warning(f"{symbol}: Not tradable - {result.reason}")
        
            return result
        except Exception as e:
            logger.error(f"Error in process: {e}")
            raise


class TAMICIntegration:
    """
    TAMIC Integration for AlphaAlgo Core
    
    Provides methods to integrate TAMIC with AlphaAlgo Core.
    """
    
    @staticmethod
    async def integrate_with_capital_governance(
        capital_governance_system,
        config: Dict[str, Any] = None
    ):
        """
        Integrate TAMIC with AlphaAlgo Core Capital Governance System.
        
        Args:
            capital_governance_system: AlphaAlgo Core Capital Governance System
            config: Configuration parameters
            
        Returns:
            TAMICGovernanceLayer instance
        """
        # Create TAMIC governance layer
        try:
            tamic_layer = TAMICGovernanceLayer(config)
        
            # Add to capital governance system
            capital_governance_system.add_layer("tamic_governance_layer", tamic_layer)
        
            logger.info("TAMIC integrated with AlphaAlgo Core Capital Governance System")
        
            return tamic_layer
        except Exception as e:
            logger.error(f"Error in integrate_with_capital_governance: {e}")
            raise


def create_tamic_integration(config: Dict[str, Any] = None) -> TAMICIntegration:
    """
    Create a TAMIC integration instance.
    
    Args:
        config: Configuration parameters
        
    Returns:
        TAMICIntegration instance
    """
    return TAMICIntegration()
