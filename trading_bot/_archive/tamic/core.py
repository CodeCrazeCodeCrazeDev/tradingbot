"""
TAMIC Core - Time-Aware Market Intelligence Core

The primary module for the TAMIC system that integrates all time-aware components
and provides the main interface for trading decisions.
"""

import asyncio
import enum
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TimeHorizon(Enum):
    """
    Strictly separated time horizons for TAMIC.
    Each horizon has independent confidence, risk, and decay logic.
    """
    MICROSTRUCTURE = "microstructure"  # seconds-minutes
    INTRADAY = "intraday"  # minutes-hours
    SHORT_SWING = "short_swing"  # hours-days
    MEDIUM_HORIZON = "medium_horizon"  # days-weeks


class MarketTimeState(Enum):
    """
    Market time states representing the pace of market time relative to clock time.
    """
    NORMAL = "normal"  # Market time flows normally
    ACCELERATED = "accelerated"  # Market time is accelerated (high volatility, low liquidity)
    EXTREME = "extreme"  # Market time is extremely accelerated (crisis, panic)


class SignalHalfLife(Enum):
    """
    Signal half-life categories for decay tracking.
    """
    VERY_SHORT = "very_short"  # <1 hour
    SHORT = "short"  # 1-4 hours
    MEDIUM = "medium"  # 4-24 hours
    LONG = "long"  # 1-3 days
    VERY_LONG = "very_long"  # >3 days


@dataclass
class TAMICConfig:
    """Configuration for TAMIC"""
    # Horizon segmentation settings
    horizon_isolation_strict: bool = True  # Strict separation between time horizons
    
    # Signal half-life settings
    signal_expiration_strict: bool = True  # Expired signals are treated as false information
    signal_half_life_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "trending": 1.2,  # Signals last longer in trending regimes
        "ranging": 0.8,  # Signals decay faster in ranging regimes
        "volatile": 0.5,  # Signals decay much faster in volatile regimes
    })
    
    # Market time settings
    market_time_acceleration_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "volatility_expansion": 2.0,  # Volatility expansion threshold
        "liquidity_withdrawal": 0.5,  # Liquidity withdrawal threshold (ratio to normal)
        "correlation_instability": 0.7,  # Correlation instability threshold
    })
    
    # Time-based risk settings
    drawdown_speed_weights: Dict[str, float] = field(default_factory=lambda: {
        "fast": 2.0,  # Fast drawdowns are weighted more heavily
        "medium": 1.0,
        "slow": 0.5,
    })
    recovery_duration_penalty: float = 0.1  # Penalty per day of recovery
    
    # Institutional time settings
    month_end_window: int = 3  # Days before month-end to consider flows
    quarter_end_window: int = 5  # Days before quarter-end to consider flows
    
    # Optionality preservation settings
    irreversibility_penalty: float = 0.2  # Penalty for irreversible trades
    liquidity_value_multiplier: float = 0.05  # Value of maintaining liquidity
    
    # Confidence and humility settings
    overconfidence_penalty: float = 0.3  # Penalty for overconfidence
    win_streak_confidence_reduction: float = 0.05  # Reduce confidence after win streaks
    
    # Forbidden behavior settings
    forbidden_behavior_penalties: Dict[str, float] = field(default_factory=lambda: {
        "chase_recent_performance": 0.9,  # Penalty for chasing recent performance
        "mix_time_horizons": 0.8,  # Penalty for mixing time horizons
        "reuse_expired_signals": 0.9,  # Penalty for reusing expired signals
        "retrain_during_drawdowns": 0.7,  # Penalty for retraining during drawdowns
        "increase_leverage_after_losses": 0.9,  # Penalty for increasing leverage after losses
        "narrative_explanations": 0.6,  # Penalty for narrative explanations
        "assume_stationarity": 0.7,  # Penalty for assuming stationarity
    })


@dataclass
class TAMICDecision:
    """
    Decision output from TAMIC with required fields.
    """
    time_horizon: TimeHorizon
    signal_half_life: SignalHalfLife
    market_time_state: MarketTimeState
    confidence_level: float  # 0-1
    no_trade_reason: Optional[str] = None
    worst_case_scenario: str = ""
    is_trade_recommended: bool = False
    exposure_recommendation: float = 0.0  # 0-1
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class TAMIC:
    """
    Time-Aware Market Intelligence Core
    
    A conservative, time-aware market intelligence system operating under real-world
    trading constraints. Prioritizes long-term survival and capital compounding over
    prediction accuracy or trade frequency.
    """
    
    def __init__(self, config: TAMICConfig = None):
        """
        Initialize TAMIC with configuration.
        
        Args:
            config: Configuration for TAMIC
        """
        self.config = config or TAMICConfig()
        self.logger = logging.getLogger("trading_bot.tamic")
        
        # Initialize components
        self.components = {}
        
        self.logger.info("TAMIC initialized with configuration")
    
    def add_component(self, component_id: str, component: Any):
        """Add a TAMIC component"""
        self.components[component_id] = component
        self.logger.info(f"Added TAMIC component: {component_id}")
    
    async def evaluate_market(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
    ) -> TAMICDecision:
        """
        Evaluate market conditions and make a trading decision.
        This is the main entry point for TAMIC.
        
        Args:
            symbol: The market symbol
            horizon: The time horizon to evaluate
            market_data: Dictionary containing market data
            
        Returns:
            TAMICDecision with trading recommendation
        """
        self.logger.info(f"Evaluating {symbol} on {horizon.value} horizon")
        
        # Initialize decision with default values
        decision = TAMICDecision(
            time_horizon=horizon,
            signal_half_life=SignalHalfLife.MEDIUM,
            market_time_state=MarketTimeState.NORMAL,
            confidence_level=0.0,
            is_trade_recommended=False,
        )
        
        # 1. Horizon Segmentation - ensure we're only using data for this horizon
        if "horizon_segmentation" in self.components:
            horizon_data = await self.components["horizon_segmentation"].get_horizon_data(
                symbol=symbol,
                horizon=horizon,
                market_data=market_data
            )
            
            if not horizon_data:
                decision.no_trade_reason = f"Insufficient data for {horizon.value} horizon"
                return decision
        else:
            horizon_data = market_data
        
        # 2. Market Time State
        if "market_time" in self.components:
            market_time_result = await self.components["market_time"].evaluate_market_time(
                symbol=symbol,
                market_data=horizon_data
            )
            decision.market_time_state = market_time_result.state
            
            # If market time is accelerated, reduce confidence
            if decision.market_time_state == MarketTimeState.ACCELERATED:
                self.logger.warning(f"Market time accelerated for {symbol}")
                decision.confidence_level *= 0.7
            elif decision.market_time_state == MarketTimeState.EXTREME:
                self.logger.warning(f"Market time extremely accelerated for {symbol}")
                decision.confidence_level *= 0.3
        
        # 3. Signal Analysis and Half-Life
        if "signal_decay" in self.components:
            signal_result = await self.components["signal_decay"].analyze_signals(
                symbol=symbol,
                horizon=horizon,
                market_data=horizon_data
            )
            decision.signal_half_life = signal_result.half_life
            
            # Check if signals are expired
            if signal_result.is_expired and self.config.signal_expiration_strict:
                decision.no_trade_reason = "Signal expired"
                decision.is_trade_recommended = False
                return decision
                
            # Update confidence based on signal strength
            decision.confidence_level = signal_result.confidence
        
        # 4. Time-Based Risk Management
        if "time_risk" in self.components:
            risk_result = await self.components["time_risk"].evaluate_risk(
                symbol=symbol,
                horizon=horizon,
                market_data=horizon_data
            )
            decision.risk_assessment = risk_result.risk_assessment
            
            # Adjust exposure based on risk
            max_exposure = risk_result.max_exposure
            decision.exposure_recommendation = min(decision.exposure_recommendation or 1.0, max_exposure)
            
            # If risk is too high, don't trade
            if max_exposure <= 0:
                decision.no_trade_reason = "Time-based risk too high"
                decision.is_trade_recommended = False
                return decision
        
        # 5. Institutional Time Awareness
        if "institutional_time" in self.components:
            inst_result = await self.components["institutional_time"].check_institutional_flows(
                symbol=symbol,
                market_data=horizon_data
            )
            
            # Add institutional time metrics
            decision.metrics.update(inst_result.metrics)
            
            # If there are forced flows, adjust confidence
            if inst_result.has_forced_flows:
                self.logger.info(f"Institutional flows detected for {symbol}")
                decision.confidence_level *= inst_result.confidence_multiplier
        
        # 6. Optionality Preservation
        if "optionality" in self.components:
            opt_result = await self.components["optionality"].evaluate_optionality(
                symbol=symbol,
                horizon=horizon,
                market_data=horizon_data
            )
            
            # If optionality value is high, reduce exposure
            if opt_result.optionality_value > 0.7:
                self.logger.info(f"High optionality value for {symbol}, reducing exposure")
                decision.exposure_recommendation *= (1 - opt_result.optionality_value * 0.5)
        
        # 7. Confidence and Humility Controls
        if "confidence_control" in self.components:
            conf_result = await self.components["confidence_control"].calibrate_confidence(
                symbol=symbol,
                horizon=horizon,
                raw_confidence=decision.confidence_level,
                market_data=horizon_data
            )
            
            # Update calibrated confidence
            decision.confidence_level = conf_result.calibrated_confidence
            
            # If confidence is too low, don't trade
            if decision.confidence_level < 0.4:
                decision.no_trade_reason = "Insufficient confidence"
                decision.is_trade_recommended = False
                return decision
        
        # 8. Forbidden Behavior Guard
        if "forbidden_behaviors" in self.components:
            forbidden_result = await self.components["forbidden_behaviors"].check_behaviors(
                symbol=symbol,
                horizon=horizon,
                market_data=horizon_data,
                decision=decision
            )
            
            # If forbidden behaviors detected, don't trade
            if forbidden_result.has_forbidden_behaviors:
                decision.no_trade_reason = f"Forbidden behavior: {forbidden_result.behavior_type}"
                decision.is_trade_recommended = False
                return decision
        
        # Final decision
        if decision.confidence_level >= 0.5 and not decision.no_trade_reason:
            decision.is_trade_recommended = True
            decision.worst_case_scenario = self._generate_worst_case_scenario(symbol, horizon, decision)
        else:
            decision.is_trade_recommended = False
            if not decision.no_trade_reason:
                decision.no_trade_reason = "Insufficient conviction"
        
        return decision
    
    def _generate_worst_case_scenario(self, symbol: str, horizon: TimeHorizon, decision: TAMICDecision) -> str:
        """Generate worst-case failure scenario based on the decision context"""
        market_time = decision.market_time_state.value
        
        scenarios = {
            TimeHorizon.MICROSTRUCTURE: f"Sudden liquidity vacuum causing slippage, market time acceleration beyond model capacity",
            TimeHorizon.INTRADAY: f"News event during {market_time} market time causing gap against position",
            TimeHorizon.SHORT_SWING: f"Overnight gap against position due to unforeseen catalyst",
            TimeHorizon.MEDIUM_HORIZON: f"Regime change invalidating assumptions, correlation breakdown"
        }
        
        return scenarios.get(horizon, "Unknown failure mode")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of TAMIC"""
        return {
            "components": list(self.components.keys()),
            "timestamp": datetime.now().isoformat()
        }


def create_tamic(config: Dict[str, Any] = None) -> TAMIC:
    """
    Create a TAMIC instance with the specified configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured TAMIC instance
    """
    tamic_config = TAMICConfig()
    
    if config:
        # Update config with provided values
        for key, value in config.items():
            if hasattr(tamic_config, key):
                setattr(tamic_config, key, value)
    
    return TAMIC(tamic_config)


async def quick_start(config: Dict[str, Any] = None) -> TAMIC:
    """
    Quick start function to create and initialize TAMIC with all components.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Fully initialized TAMIC instance
    """
    from .horizon_segmentation import HorizonSegmentation
    from .signal_decay import SignalDecay
    from .market_time import MarketTimeEngine
    from .time_risk import TimeBasedRiskManager
    from .institutional_time import InstitutionalTimeEngine
    from .optionality import OptionalityPreservationEngine
    from .confidence_control import ConfidenceHumilityControl
    from .forbidden_behaviors import ForbiddenBehaviorGuard
    
    # Create TAMIC instance
    tamic = create_tamic(config)
    
    # Add components
    tamic.add_component("horizon_segmentation", HorizonSegmentation())
    tamic.add_component("signal_decay", SignalDecay())
    tamic.add_component("market_time", MarketTimeEngine())
    tamic.add_component("time_risk", TimeBasedRiskManager())
    tamic.add_component("institutional_time", InstitutionalTimeEngine())
    tamic.add_component("optionality", OptionalityPreservationEngine())
    tamic.add_component("confidence_control", ConfidenceHumilityControl())
    tamic.add_component("forbidden_behaviors", ForbiddenBehaviorGuard())
    
    return tamic
