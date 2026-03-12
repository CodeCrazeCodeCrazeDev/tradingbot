"""
Forbidden Behaviors Guard for TAMIC

This module implements safeguards against forbidden trading behaviors focusing on:
1. Chasing recent performance - Avoiding recency bias and performance chasing
2. Mixing time horizons - Enforcing strict separation between time horizons
3. Reusing expired signals - Preventing the use of stale information
4. Retraining during drawdowns - Avoiding overfitting to drawdown periods
5. Increasing leverage after losses - Preventing revenge trading and martingale
6. Narrative explanations - Avoiding narrative fallacy in trading decisions
7. Assuming stationarity - Preventing assumption of unchanging market dynamics

The primary goal is to prevent common cognitive biases and behavioral mistakes
that lead to poor trading decisions.
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

from .core import TimeHorizon, MarketTimeState, TAMICDecision

logger = logging.getLogger(__name__)


class ForbiddenBehaviorType(Enum):
    """Types of forbidden behaviors"""
    CHASE_RECENT_PERFORMANCE = "chase_recent_performance"
    MIX_TIME_HORIZONS = "mix_time_horizons"
    REUSE_EXPIRED_SIGNALS = "reuse_expired_signals"
    RETRAIN_DURING_DRAWDOWNS = "retrain_during_drawdowns"
    INCREASE_LEVERAGE_AFTER_LOSSES = "increase_leverage_after_losses"
    NARRATIVE_EXPLANATIONS = "narrative_explanations"
    ASSUME_STATIONARITY = "assume_stationarity"


@dataclass
class ForbiddenBehaviorResult:
    """Result from forbidden behavior check"""
    has_forbidden_behaviors: bool
    behavior_type: Optional[ForbiddenBehaviorType] = None
    behavior_score: float = 0.0  # 0-1, higher is more severe
    explanation: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ForbiddenBehaviorGuard:
    """
    Guard against forbidden trading behaviors.
    
    Prevents common cognitive biases and behavioral mistakes that lead to
    poor trading decisions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize ForbiddenBehaviorGuard.
        
        Args:
            config: Configuration parameters
        """
        try:
            self.config = config or {}
            self.logger = logging.getLogger("trading_bot.tamic.forbidden_behaviors")
        
            # Behavior history
            self.behavior_history = {}  # Symbol -> {horizon -> history}
        
            # Behavior thresholds
            self.behavior_thresholds = self.config.get("behavior_thresholds", {
                ForbiddenBehaviorType.CHASE_RECENT_PERFORMANCE: 0.7,
                ForbiddenBehaviorType.MIX_TIME_HORIZONS: 0.8,
                ForbiddenBehaviorType.REUSE_EXPIRED_SIGNALS: 0.9,
                ForbiddenBehaviorType.RETRAIN_DURING_DRAWDOWNS: 0.7,
                ForbiddenBehaviorType.INCREASE_LEVERAGE_AFTER_LOSSES: 0.9,
                ForbiddenBehaviorType.NARRATIVE_EXPLANATIONS: 0.6,
                ForbiddenBehaviorType.ASSUME_STATIONARITY: 0.7,
            })
        
            # Behavior penalties
            self.behavior_penalties = self.config.get("behavior_penalties", {
                ForbiddenBehaviorType.CHASE_RECENT_PERFORMANCE: 0.9,
                ForbiddenBehaviorType.MIX_TIME_HORIZONS: 0.8,
                ForbiddenBehaviorType.REUSE_EXPIRED_SIGNALS: 0.9,
                ForbiddenBehaviorType.RETRAIN_DURING_DRAWDOWNS: 0.7,
                ForbiddenBehaviorType.INCREASE_LEVERAGE_AFTER_LOSSES: 0.9,
                ForbiddenBehaviorType.NARRATIVE_EXPLANATIONS: 0.6,
                ForbiddenBehaviorType.ASSUME_STATIONARITY: 0.7,
            })
        
            # Signal expiration settings
            self.signal_expiration_hours = self.config.get("signal_expiration_hours", {
                TimeHorizon.MICROSTRUCTURE: 0.5,  # 30 minutes
                TimeHorizon.INTRADAY: 4,  # 4 hours
                TimeHorizon.SHORT_SWING: 24,  # 1 day
                TimeHorizon.MEDIUM_HORIZON: 72,  # 3 days
            })
        
            # Drawdown threshold for retraining detection
            self.drawdown_threshold = self.config.get("drawdown_threshold", 0.1)  # 10% drawdown
        
            # Initialize behavior history
            self._initialize_behavior_history()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_behavior_history(self):
        """Initialize behavior history"""
        try:
            self.behavior_history = {}
        except Exception as e:
            logger.error(f"Error in _initialize_behavior_history: {e}")
            raise
    
    def _initialize_symbol_history(self, symbol: str, horizon: TimeHorizon):
        """Initialize history for a symbol and horizon"""
        try:
            if symbol not in self.behavior_history:
                self.behavior_history[symbol] = {}
        
            if horizon not in self.behavior_history[symbol]:
                self.behavior_history[symbol][horizon] = {
                    "signals": [],  # List of signals with timestamps
                    "trades": [],  # List of trades with timestamps
                    "performance": [],  # List of performance metrics
                    "drawdowns": [],  # List of drawdowns
                    "leverage": [],  # List of leverage values
                    "retraining_events": [],  # List of retraining events
                }
        except Exception as e:
            logger.error(f"Error in _initialize_symbol_history: {e}")
            raise
    
    def _check_performance_chasing(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        decision: TAMICDecision
    ) -> Tuple[bool, float, str]:
        """
        Check for performance chasing behavior.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            decision: TAMIC decision
            
        Returns:
            Tuple of (is_chasing, chasing_score, explanation)
        """
        # This would typically be a more sophisticated analysis
        # For now, we'll use a simple approach based on recent performance
        
        # Default values
        try:
            is_chasing = False
            chasing_score = 0.0
            explanation = ""
        
            # Check if we have recent performance data
            if "recent_performance" in market_data:
                recent_performance = market_data["recent_performance"]
                if isinstance(recent_performance, (int, float)):
                    # Check if recent performance is exceptionally good
                    if recent_performance > 0.1:  # 10% recent return
                        # Check if confidence is high
                        if decision.confidence_level > 0.8:
                            is_chasing = True
                            chasing_score = min(1.0, recent_performance * 5)  # Scale up for scoring
                            explanation = (f"High confidence ({decision.confidence_level:.2f}) after "
                                          f"exceptional recent performance ({recent_performance:.2%})")
        
            # Check if we have price data
            if not is_chasing and "close" in market_data:
                close = market_data["close"]
                if isinstance(close, (list, np.ndarray, pd.Series)):
                    # Convert to numpy array if needed
                    if isinstance(close, list):
                        close = np.array(close)
                    elif isinstance(close, pd.Series):
                        close = close.values
                
                    # Check if we have enough data
                    if len(close) >= 10:
                        # Calculate recent return
                        recent_return = close[-1] / close[-10] - 1
                    
                        # Check if recent return is exceptionally good
                        if recent_return > 0.05:  # 5% recent return
                            # Check if confidence is high
                            if decision.confidence_level > 0.8:
                                is_chasing = True
                                chasing_score = min(1.0, recent_return * 10)  # Scale up for scoring
                                explanation = (f"High confidence ({decision.confidence_level:.2f}) after "
                                              f"strong recent price movement ({recent_return:.2%})")
        
            return is_chasing, chasing_score, explanation
        except Exception as e:
            logger.error(f"Error in _check_performance_chasing: {e}")
            raise
    
    def _check_time_horizon_mixing(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        decision: TAMICDecision
    ) -> Tuple[bool, float, str]:
        """
        Check for time horizon mixing behavior.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            decision: TAMIC decision
            
        Returns:
            Tuple of (is_mixing, mixing_score, explanation)
        """
        # Default values
        try:
            is_mixing = False
            mixing_score = 0.0
            explanation = ""
        
            # Check if market data contains data from multiple horizons
            horizons_in_data = set()
        
            for key in market_data:
                # Check for horizon-specific keys
                for h in TimeHorizon:
                    if h.value in key:
                        horizons_in_data.add(h)
        
            # If we have data from multiple horizons, check if they're being mixed
            if len(horizons_in_data) > 1 and horizon in horizons_in_data:
                # Check if decision is using data from multiple horizons
                if decision.time_horizon != horizon:
                    is_mixing = True
                    mixing_score = 0.8
                    explanation = (f"Decision uses {decision.time_horizon.value} horizon but "
                                  f"analysis is for {horizon.value} horizon")
            
                # Check if multiple horizons are referenced in metrics
                if hasattr(decision, "metrics") and isinstance(decision.metrics, dict):
                    referenced_horizons = set()
                
                    for key in decision.metrics:
                        for h in TimeHorizon:
                            if h.value in key:
                                referenced_horizons.add(h)
                
                    if len(referenced_horizons) > 1:
                        is_mixing = True
                        mixing_score = 0.9
                        explanation = (f"Decision metrics reference multiple horizons: "
                                      f"{', '.join(h.value for h in referenced_horizons)}")
        
            return is_mixing, mixing_score, explanation
        except Exception as e:
            logger.error(f"Error in _check_time_horizon_mixing: {e}")
            raise
    
    def _check_expired_signals(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        decision: TAMICDecision
    ) -> Tuple[bool, float, str]:
        """
        Check for reuse of expired signals.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            decision: TAMIC decision
            
        Returns:
            Tuple of (is_expired, expiry_score, explanation)
        """
        # Default values
        try:
            is_expired = False
            expiry_score = 0.0
            explanation = ""
        
            # Check if we have signal timestamp
            if "signal_timestamp" in market_data:
                signal_timestamp = market_data["signal_timestamp"]
                if isinstance(signal_timestamp, (int, float)):
                    # Convert to datetime if needed
                    if isinstance(signal_timestamp, int) or isinstance(signal_timestamp, float):
                        signal_timestamp = datetime.fromtimestamp(signal_timestamp)
                
                    # Get current time
                    current_time = datetime.now()
                
                    # Calculate age in hours
                    age_hours = (current_time - signal_timestamp).total_seconds() / 3600
                
                    # Get expiration threshold for this horizon
                    expiration_hours = self.signal_expiration_hours.get(horizon, 24)
                
                    # Check if signal is expired
                    if age_hours > expiration_hours:
                        is_expired = True
                        expiry_score = min(1.0, age_hours / expiration_hours)
                        explanation = (f"Signal is {age_hours:.1f} hours old, "
                                      f"exceeding {expiration_hours} hour limit for {horizon.value}")
        
            return is_expired, expiry_score, explanation
        except Exception as e:
            logger.error(f"Error in _check_expired_signals: {e}")
            raise
    
    def _check_drawdown_retraining(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        decision: TAMICDecision
    ) -> Tuple[bool, float, str]:
        """
        Check for retraining during drawdowns.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            decision: TAMIC decision
            
        Returns:
            Tuple of (is_retraining, retraining_score, explanation)
        """
        # Default values
        try:
            is_retraining = False
            retraining_score = 0.0
            explanation = ""
        
            # Check if we're in a drawdown
            in_drawdown = False
            drawdown = 0.0
        
            if "drawdown" in market_data:
                drawdown = market_data["drawdown"]
                if isinstance(drawdown, (int, float)):
                    in_drawdown = drawdown > self.drawdown_threshold
        
            # Check if we're retraining
            is_retraining_event = False
        
            if "is_retraining" in market_data:
                is_retraining_event = bool(market_data["is_retraining"])
        
            # If we're in a drawdown and retraining, flag it
            if in_drawdown and is_retraining_event:
                is_retraining = True
                retraining_score = min(1.0, drawdown * 5)  # Scale up for scoring
                explanation = (f"Retraining during {drawdown:.2%} drawdown, "
                              f"exceeding {self.drawdown_threshold:.2%} threshold")
        
            return is_retraining, retraining_score, explanation
        except Exception as e:
            logger.error(f"Error in _check_drawdown_retraining: {e}")
            raise
    
    def _check_leverage_increase_after_losses(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        decision: TAMICDecision
    ) -> Tuple[bool, float, str]:
        """
        Check for increasing leverage after losses.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            decision: TAMIC decision
            
        Returns:
            Tuple of (is_increasing, increase_score, explanation)
        """
        # Default values
        try:
            is_increasing = False
            increase_score = 0.0
            explanation = ""
        
            # Check if we have recent losses
            recent_losses = False
            loss_streak = 0
        
            if "loss_streak" in market_data:
                loss_streak = market_data["loss_streak"]
                if isinstance(loss_streak, int):
                    recent_losses = loss_streak >= 2
        
            # Check if we're increasing leverage
            leverage_increase = 0.0
        
            if "previous_leverage" in market_data and "current_leverage" in market_data:
                previous_leverage = market_data["previous_leverage"]
                current_leverage = market_data["current_leverage"]
            
                if isinstance(previous_leverage, (int, float)) and isinstance(current_leverage, (int, float)):
                    leverage_increase = current_leverage - previous_leverage
        
            # If we have recent losses and increasing leverage, flag it
            if recent_losses and leverage_increase > 0:
                is_increasing = True
                increase_score = min(1.0, leverage_increase + loss_streak * 0.1)
                explanation = (f"Increasing leverage by {leverage_increase:.2f}x after "
                              f"{loss_streak} consecutive losses")
        
            return is_increasing, increase_score, explanation
        except Exception as e:
            logger.error(f"Error in _check_leverage_increase_after_losses: {e}")
            raise
    
    def _check_narrative_explanations(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        decision: TAMICDecision
    ) -> Tuple[bool, float, str]:
        """
        Check for narrative explanations.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            decision: TAMIC decision
            
        Returns:
            Tuple of (has_narrative, narrative_score, explanation)
        """
        # This would typically be a more sophisticated analysis
        # For now, we'll use a simple approach based on decision explanation
        
        # Default values
        try:
            has_narrative = False
            narrative_score = 0.0
            explanation = ""
        
            # Check if decision has a narrative explanation
            if hasattr(decision, "explanation") and isinstance(decision.explanation, str):
                # Check for narrative keywords
                narrative_keywords = [
                    "because", "story", "narrative", "expect", "believe", "feel",
                    "think", "should", "could", "would", "might", "may", "opinion"
                ]
            
                # Count narrative keywords
                keyword_count = sum(1 for keyword in narrative_keywords if keyword in decision.explanation.lower())
            
                # If we have multiple narrative keywords, flag it
                if keyword_count >= 3:
                    has_narrative = True
                    narrative_score = min(1.0, keyword_count * 0.1)
                    explanation = (f"Decision explanation contains {keyword_count} narrative keywords")
        
            return has_narrative, narrative_score, explanation
        except Exception as e:
            logger.error(f"Error in _check_narrative_explanations: {e}")
            raise
    
    def _check_stationarity_assumption(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        decision: TAMICDecision
    ) -> Tuple[bool, float, str]:
        """
        Check for assumption of stationarity.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            decision: TAMIC decision
            
        Returns:
            Tuple of (assumes_stationarity, stationarity_score, explanation)
        """
        # This would typically be a more sophisticated analysis
        # For now, we'll use a simple approach based on market regime
        
        # Default values
        try:
            assumes_stationarity = False
            stationarity_score = 0.0
            explanation = ""
        
            # Check if we have regime change information
            regime_changed = False
        
            if "regime_changed" in market_data:
                regime_changed = bool(market_data["regime_changed"])
        
            # Check if we have volatility change information
            volatility_increased = False
        
            if "volatility_change" in market_data:
                volatility_change = market_data["volatility_change"]
                if isinstance(volatility_change, (int, float)):
                    volatility_increased = volatility_change > 0.3  # 30% increase in volatility
        
            # If regime changed or volatility increased, check if decision assumes stationarity
            if regime_changed or volatility_increased:
                # Check if confidence is too high given the changes
                if decision.confidence_level > 0.7:
                    assumes_stationarity = True
                    stationarity_score = 0.7
                
                    if regime_changed and volatility_increased:
                        explanation = (f"High confidence ({decision.confidence_level:.2f}) despite "
                                      f"regime change and volatility increase")
                    elif regime_changed:
                        explanation = (f"High confidence ({decision.confidence_level:.2f}) despite "
                                      f"regime change")
                    else:
                        explanation = (f"High confidence ({decision.confidence_level:.2f}) despite "
                                      f"volatility increase")
        
            return assumes_stationarity, stationarity_score, explanation
        except Exception as e:
            logger.error(f"Error in _check_stationarity_assumption: {e}")
            raise
    
    async def check_behaviors(
        self,
        symbol: str,
        horizon: TimeHorizon,
        market_data: Dict[str, Any],
        decision: TAMICDecision
    ) -> ForbiddenBehaviorResult:
        """
        Check for forbidden behaviors.
        
        Args:
            symbol: Market symbol
            horizon: Time horizon
            market_data: Market data dictionary
            decision: TAMIC decision
            
        Returns:
            ForbiddenBehaviorResult with behavior analysis
        """
        try:
            self.logger.info(f"Checking forbidden behaviors for {symbol} on {horizon.value} horizon")
        
            # Initialize symbol history if needed
            self._initialize_symbol_history(symbol, horizon)
        
            # Check each forbidden behavior
        
            # 1. Performance chasing
            is_chasing, chasing_score, chasing_explanation = self._check_performance_chasing(
                symbol, horizon, market_data, decision
            )
        
            if is_chasing and chasing_score >= self.behavior_thresholds[ForbiddenBehaviorType.CHASE_RECENT_PERFORMANCE]:
                self.logger.warning(f"{symbol} {horizon.value}: Performance chasing detected - {chasing_explanation}")
                return ForbiddenBehaviorResult(
                    has_forbidden_behaviors=True,
                    behavior_type=ForbiddenBehaviorType.CHASE_RECENT_PERFORMANCE,
                    behavior_score=chasing_score,
                    explanation=chasing_explanation,
                    metrics={
                        "behavior_type": ForbiddenBehaviorType.CHASE_RECENT_PERFORMANCE.value,
                        "behavior_score": chasing_score,
                    }
                )
        
            # 2. Time horizon mixing
            is_mixing, mixing_score, mixing_explanation = self._check_time_horizon_mixing(
                symbol, horizon, market_data, decision
            )
        
            if is_mixing and mixing_score >= self.behavior_thresholds[ForbiddenBehaviorType.MIX_TIME_HORIZONS]:
                self.logger.warning(f"{symbol} {horizon.value}: Time horizon mixing detected - {mixing_explanation}")
                return ForbiddenBehaviorResult(
                    has_forbidden_behaviors=True,
                    behavior_type=ForbiddenBehaviorType.MIX_TIME_HORIZONS,
                    behavior_score=mixing_score,
                    explanation=mixing_explanation,
                    metrics={
                        "behavior_type": ForbiddenBehaviorType.MIX_TIME_HORIZONS.value,
                        "behavior_score": mixing_score,
                    }
                )
        
            # 3. Expired signals
            is_expired, expiry_score, expiry_explanation = self._check_expired_signals(
                symbol, horizon, market_data, decision
            )
        
            if is_expired and expiry_score >= self.behavior_thresholds[ForbiddenBehaviorType.REUSE_EXPIRED_SIGNALS]:
                self.logger.warning(f"{symbol} {horizon.value}: Expired signal detected - {expiry_explanation}")
                return ForbiddenBehaviorResult(
                    has_forbidden_behaviors=True,
                    behavior_type=ForbiddenBehaviorType.REUSE_EXPIRED_SIGNALS,
                    behavior_score=expiry_score,
                    explanation=expiry_explanation,
                    metrics={
                        "behavior_type": ForbiddenBehaviorType.REUSE_EXPIRED_SIGNALS.value,
                        "behavior_score": expiry_score,
                    }
                )
        
            # 4. Retraining during drawdowns
            is_retraining, retraining_score, retraining_explanation = self._check_drawdown_retraining(
                symbol, horizon, market_data, decision
            )
        
            if is_retraining and retraining_score >= self.behavior_thresholds[ForbiddenBehaviorType.RETRAIN_DURING_DRAWDOWNS]:
                self.logger.warning(f"{symbol} {horizon.value}: Drawdown retraining detected - {retraining_explanation}")
                return ForbiddenBehaviorResult(
                    has_forbidden_behaviors=True,
                    behavior_type=ForbiddenBehaviorType.RETRAIN_DURING_DRAWDOWNS,
                    behavior_score=retraining_score,
                    explanation=retraining_explanation,
                    metrics={
                        "behavior_type": ForbiddenBehaviorType.RETRAIN_DURING_DRAWDOWNS.value,
                        "behavior_score": retraining_score,
                    }
                )
        
            # 5. Increasing leverage after losses
            is_increasing, increase_score, increase_explanation = self._check_leverage_increase_after_losses(
                symbol, horizon, market_data, decision
            )
        
            if is_increasing and increase_score >= self.behavior_thresholds[ForbiddenBehaviorType.INCREASE_LEVERAGE_AFTER_LOSSES]:
                self.logger.warning(f"{symbol} {horizon.value}: Leverage increase after losses detected - {increase_explanation}")
                return ForbiddenBehaviorResult(
                    has_forbidden_behaviors=True,
                    behavior_type=ForbiddenBehaviorType.INCREASE_LEVERAGE_AFTER_LOSSES,
                    behavior_score=increase_score,
                    explanation=increase_explanation,
                    metrics={
                        "behavior_type": ForbiddenBehaviorType.INCREASE_LEVERAGE_AFTER_LOSSES.value,
                        "behavior_score": increase_score,
                    }
                )
        
            # 6. Narrative explanations
            has_narrative, narrative_score, narrative_explanation = self._check_narrative_explanations(
                symbol, horizon, market_data, decision
            )
        
            if has_narrative and narrative_score >= self.behavior_thresholds[ForbiddenBehaviorType.NARRATIVE_EXPLANATIONS]:
                self.logger.warning(f"{symbol} {horizon.value}: Narrative explanation detected - {narrative_explanation}")
                return ForbiddenBehaviorResult(
                    has_forbidden_behaviors=True,
                    behavior_type=ForbiddenBehaviorType.NARRATIVE_EXPLANATIONS,
                    behavior_score=narrative_score,
                    explanation=narrative_explanation,
                    metrics={
                        "behavior_type": ForbiddenBehaviorType.NARRATIVE_EXPLANATIONS.value,
                        "behavior_score": narrative_score,
                    }
                )
        
            # 7. Stationarity assumption
            assumes_stationarity, stationarity_score, stationarity_explanation = self._check_stationarity_assumption(
                symbol, horizon, market_data, decision
            )
        
            if assumes_stationarity and stationarity_score >= self.behavior_thresholds[ForbiddenBehaviorType.ASSUME_STATIONARITY]:
                self.logger.warning(f"{symbol} {horizon.value}: Stationarity assumption detected - {stationarity_explanation}")
                return ForbiddenBehaviorResult(
                    has_forbidden_behaviors=True,
                    behavior_type=ForbiddenBehaviorType.ASSUME_STATIONARITY,
                    behavior_score=stationarity_score,
                    explanation=stationarity_explanation,
                    metrics={
                        "behavior_type": ForbiddenBehaviorType.ASSUME_STATIONARITY.value,
                        "behavior_score": stationarity_score,
                    }
                )
        
            # No forbidden behaviors detected
            self.logger.info(f"{symbol} {horizon.value}: No forbidden behaviors detected")
        
            # Create metrics
            metrics = {
                "chase_recent_performance_score": chasing_score,
                "mix_time_horizons_score": mixing_score,
                "reuse_expired_signals_score": expiry_score,
                "retrain_during_drawdowns_score": retraining_score,
                "increase_leverage_after_losses_score": increase_score,
                "narrative_explanations_score": narrative_score,
                "assume_stationarity_score": stationarity_score,
            }
        
            # Create result
            result = ForbiddenBehaviorResult(
                has_forbidden_behaviors=False,
                behavior_score=0.0,
                explanation="No forbidden behaviors detected",
                metrics=metrics
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in check_behaviors: {e}")
            raise
