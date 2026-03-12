"""
TAMIC Market Time Engine

Implements the distinction between market time and clock time:
- Market time accelerates during volatility expansion, liquidity withdrawal, 
  correlation instability, and forced flow events
- When market time accelerates, TAMIC slows decision-making, reduces exposure,
  and prioritizes liquidity
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .core import MarketTimeState

logger = logging.getLogger(__name__)


@dataclass
class TimeDistortion:
    """Represents market time distortion relative to clock time"""
    distortion_factor: float  # >1 means market time is faster than clock time
    cause: str
    severity: float  # 0-1
    start_time: datetime
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class MarketTimeAccelerationEvent:
    """An event that causes market time acceleration"""
    event_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    severity: float = 0.0  # 0-1
    description: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Check if the event is currently active"""
        return self.end_time is None or datetime.now() < self.end_time
    
    @property
    def duration_seconds(self) -> float:
        """Get the duration of the event in seconds"""
        if not self.is_active:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()


@dataclass
class MarketTimeResult:
    """Result from market time evaluation"""
    state: MarketTimeState
    distortion_factor: float  # >1 means market time is faster than clock time
    active_events: List[MarketTimeAccelerationEvent]
    metrics: Dict[str, float] = field(default_factory=dict)
    recommendation: str = ""


class ClockTimeTracker:
    """
    Tracks clock time and provides utilities for time-based calculations.
    """
    
    def __init__(self):
        """Initialize clock time tracker"""
        self.logger = logging.getLogger("trading_bot.tamic.clock_time_tracker")
        self.start_time = datetime.now()
        self.last_update = self.start_time
    
    def update(self) -> float:
        """
        Update the clock time tracker.
        
        Returns:
            Seconds since last update
        """
        now = datetime.now()
        elapsed = (now - self.last_update).total_seconds()
        self.last_update = now
        return elapsed
    
    def get_elapsed_seconds(self) -> float:
        """Get seconds since tracker was initialized"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_elapsed_minutes(self) -> float:
        """Get minutes since tracker was initialized"""
        return self.get_elapsed_seconds() / 60.0
    
    def get_elapsed_hours(self) -> float:
        """Get hours since tracker was initialized"""
        return self.get_elapsed_seconds() / 3600.0
    
    def get_current_time_of_day(self) -> Tuple[int, int]:
        """Get current hour and minute"""
        now = datetime.now()
        return now.hour, now.minute


class MarketTimeEngine:
    """
    Implements the distinction between market time and clock time.
    
    Market time accelerates during:
    - Volatility expansion
    - Liquidity withdrawal
    - Correlation instability
    - Forced flow events
    
    When market time accelerates, TAMIC:
    - Slows decision-making
    - Reduces exposure
    - Prioritizes liquidity
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize market time engine.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger("trading_bot.tamic.market_time")
        self.config = config or {}
        
        # Default thresholds for market time acceleration
        self.thresholds = {
            "volatility_expansion": self.config.get("volatility_expansion", 2.0),
            "liquidity_withdrawal": self.config.get("liquidity_withdrawal", 0.5),
            "correlation_instability": self.config.get("correlation_instability", 0.7),
            "forced_flow": self.config.get("forced_flow", 0.8)
        }
        
        # Active market time acceleration events
        self.active_events = {}  # symbol -> List[MarketTimeAccelerationEvent]
        
        # Historical baselines for comparison
        self.baselines = {}  # symbol -> Dict[str, float]
        
        # Clock time tracker
        self.clock_tracker = ClockTimeTracker()
        
        self.logger.info("Market time engine initialized")
    
    async def evaluate_market_time(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> MarketTimeResult:
        """
        Evaluate market time state relative to clock time.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            MarketTimeResult with market time state and metrics
        """
        try:
            # Update clock tracker
            self.clock_tracker.update()
            
            # Initialize active events for this symbol if needed
            if symbol not in self.active_events:
                self.active_events[symbol] = []
            
            # Clean up expired events
            self._cleanup_expired_events(symbol)
            
            # Initialize metrics
            metrics = {}
            active_events = []
            
            # Check for volatility expansion
            volatility_event = self._check_volatility_expansion(symbol, market_data)
            if volatility_event:
                active_events.append(volatility_event)
                metrics["volatility_factor"] = volatility_event.severity
            
            # Check for liquidity withdrawal
            liquidity_event = self._check_liquidity_withdrawal(symbol, market_data)
            if liquidity_event:
                active_events.append(liquidity_event)
                metrics["liquidity_factor"] = liquidity_event.severity
            
            # Check for correlation instability
            correlation_event = self._check_correlation_instability(symbol, market_data)
            if correlation_event:
                active_events.append(correlation_event)
                metrics["correlation_factor"] = correlation_event.severity
            
            # Check for forced flows
            flow_event = self._check_forced_flows(symbol, market_data)
            if flow_event:
                active_events.append(flow_event)
                metrics["flow_factor"] = flow_event.severity
            
            # Calculate overall distortion factor
            distortion_factor = self._calculate_distortion_factor(active_events)
            metrics["distortion_factor"] = distortion_factor
            
            # Determine market time state
            state = self._determine_market_time_state(distortion_factor)
            
            # Generate recommendation based on state
            recommendation = self._generate_recommendation(state, distortion_factor)
            
            # Update active events for this symbol
            self.active_events[symbol] = active_events
            
            return MarketTimeResult(
                state=state,
                distortion_factor=distortion_factor,
                active_events=active_events,
                metrics=metrics,
                recommendation=recommendation
            )
            
        except Exception as e:
            self.logger.exception(f"Error in market time evaluation: {e}")
            return MarketTimeResult(
                state=MarketTimeState.NORMAL,
                distortion_factor=1.0,
                active_events=[]
            )
    
    def _cleanup_expired_events(self, symbol: str) -> None:
        """Clean up expired events for a symbol"""
        if symbol in self.active_events:
            self.active_events[symbol] = [
                event for event in self.active_events[symbol]
                if event.is_active
            ]
    
    def _check_volatility_expansion(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Optional[MarketTimeAccelerationEvent]:
        """
        Check for volatility expansion.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            MarketTimeAccelerationEvent if volatility expansion detected, None otherwise
        """
        # Check if we have volatility data
        if "volatility" not in market_data:
            return None
        
        volatility_data = market_data["volatility"]
        
        # Get current volatility
        if isinstance(volatility_data, dict) and "current" in volatility_data:
            current_volatility = volatility_data["current"]
        else:
            return None
        
        # Get baseline volatility
        if symbol in self.baselines and "volatility" in self.baselines[symbol]:
            baseline_volatility = self.baselines[symbol]["volatility"]
        else:
            # Initialize baseline if not available
            if symbol not in self.baselines:
                self.baselines[symbol] = {}
            self.baselines[symbol]["volatility"] = current_volatility
            return None
        
        # Calculate volatility ratio
        volatility_ratio = current_volatility / baseline_volatility if baseline_volatility > 0 else 1.0
        
        # Check if volatility expansion threshold is exceeded
        threshold = self.thresholds["volatility_expansion"]
        if volatility_ratio > threshold:
            # Calculate severity (0-1)
            severity = min(1.0, (volatility_ratio - threshold) / threshold)
            
            # Create event
            event = MarketTimeAccelerationEvent(
                event_type="volatility_expansion",
                start_time=datetime.now(),
                severity=severity,
                description=f"Volatility expansion: {volatility_ratio:.2f}x baseline",
                metrics={"volatility_ratio": volatility_ratio}
            )
            
            self.logger.info(
                f"Volatility expansion detected for {symbol}: "
                f"{volatility_ratio:.2f}x baseline (severity: {severity:.2f})"
            )
            
            return event
        
        return None
    
    def _check_liquidity_withdrawal(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Optional[MarketTimeAccelerationEvent]:
        """
        Check for liquidity withdrawal.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            MarketTimeAccelerationEvent if liquidity withdrawal detected, None otherwise
        """
        # Check if we have liquidity data
        if "liquidity" not in market_data:
            return None
        
        liquidity_data = market_data["liquidity"]
        
        # Get current liquidity
        if isinstance(liquidity_data, dict) and "depth" in liquidity_data:
            current_liquidity = liquidity_data["depth"]
        else:
            return None
        
        # Get baseline liquidity
        if symbol in self.baselines and "liquidity" in self.baselines[symbol]:
            baseline_liquidity = self.baselines[symbol]["liquidity"]
        else:
            # Initialize baseline if not available
            if symbol not in self.baselines:
                self.baselines[symbol] = {}
            self.baselines[symbol]["liquidity"] = current_liquidity
            return None
        
        # Calculate liquidity ratio
        liquidity_ratio = current_liquidity / baseline_liquidity if baseline_liquidity > 0 else 1.0
        
        # Check if liquidity withdrawal threshold is exceeded (ratio < threshold)
        threshold = self.thresholds["liquidity_withdrawal"]
        if liquidity_ratio < threshold:
            # Calculate severity (0-1)
            severity = min(1.0, (threshold - liquidity_ratio) / threshold)
            
            # Create event
            event = MarketTimeAccelerationEvent(
                event_type="liquidity_withdrawal",
                start_time=datetime.now(),
                severity=severity,
                description=f"Liquidity withdrawal: {liquidity_ratio:.2f}x baseline",
                metrics={"liquidity_ratio": liquidity_ratio}
            )
            
            self.logger.info(
                f"Liquidity withdrawal detected for {symbol}: "
                f"{liquidity_ratio:.2f}x baseline (severity: {severity:.2f})"
            )
            
            return event
        
        return None
    
    def _check_correlation_instability(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Optional[MarketTimeAccelerationEvent]:
        """
        Check for correlation instability.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            MarketTimeAccelerationEvent if correlation instability detected, None otherwise
        """
        # Check if we have correlation data
        if "correlations" not in market_data:
            return None
        
        correlation_data = market_data["correlations"]
        
        # Get correlation stability metric
        if isinstance(correlation_data, dict) and "stability" in correlation_data:
            correlation_stability = correlation_data["stability"]
        else:
            return None
        
        # Check if correlation instability threshold is exceeded (stability < 1 - threshold)
        threshold = self.thresholds["correlation_instability"]
        if correlation_stability < (1.0 - threshold):
            # Calculate severity (0-1)
            severity = min(1.0, ((1.0 - threshold) - correlation_stability) / (1.0 - threshold))
            
            # Create event
            event = MarketTimeAccelerationEvent(
                event_type="correlation_instability",
                start_time=datetime.now(),
                severity=severity,
                description=f"Correlation instability: {correlation_stability:.2f} stability",
                metrics={"correlation_stability": correlation_stability}
            )
            
            self.logger.info(
                f"Correlation instability detected for {symbol}: "
                f"{correlation_stability:.2f} stability (severity: {severity:.2f})"
            )
            
            return event
        
        return None
    
    def _check_forced_flows(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Optional[MarketTimeAccelerationEvent]:
        """
        Check for forced flows.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            MarketTimeAccelerationEvent if forced flows detected, None otherwise
        """
        # Check if we have flow data
        if "flows" not in market_data:
            return None
        
        flow_data = market_data["flows"]
        
        # Get forced flow metric
        if isinstance(flow_data, dict) and "forced_flow" in flow_data:
            forced_flow = flow_data["forced_flow"]
        else:
            return None
        
        # Check if forced flow threshold is exceeded
        threshold = self.thresholds["forced_flow"]
        if forced_flow > threshold:
            # Calculate severity (0-1)
            severity = min(1.0, (forced_flow - threshold) / (1.0 - threshold))
            
            # Create event
            event = MarketTimeAccelerationEvent(
                event_type="forced_flow",
                start_time=datetime.now(),
                severity=severity,
                description=f"Forced flow: {forced_flow:.2f} vs {threshold:.2f} threshold",
                metrics={"forced_flow": forced_flow}
            )
            
            self.logger.info(
                f"Forced flow detected for {symbol}: "
                f"{forced_flow:.2f} vs {threshold:.2f} threshold (severity: {severity:.2f})"
            )
            
            return event
        
        return None
    
    def _calculate_distortion_factor(
        self,
        events: List[MarketTimeAccelerationEvent]
    ) -> float:
        """
        Calculate overall market time distortion factor.
        
        Args:
            events: List of active market time acceleration events
            
        Returns:
            Distortion factor (>1 means market time is faster than clock time)
        """
        if not events:
            return 1.0
        
        # Calculate weighted average of event severities
        total_weight = 0
        weighted_severity = 0
        
        # Event type weights
        weights = {
            "volatility_expansion": 1.0,
            "liquidity_withdrawal": 1.2,
            "correlation_instability": 0.8,
            "forced_flow": 1.5
        }
        
        for event in events:
            weight = weights.get(event.event_type, 1.0)
            total_weight += weight
            weighted_severity += event.severity * weight
        
        if total_weight > 0:
            avg_severity = weighted_severity / total_weight
        else:
            avg_severity = 0.0
        
        # Convert severity to distortion factor
        # Distortion factor ranges from 1.0 (normal) to MAX_DISTORTION
        MAX_DISTORTION = 5.0
        distortion_factor = 1.0 + (MAX_DISTORTION - 1.0) * avg_severity
        
        return distortion_factor
    
    def _determine_market_time_state(self, distortion_factor: float) -> MarketTimeState:
        """
        Determine market time state based on distortion factor.
        
        Args:
            distortion_factor: Market time distortion factor
            
        Returns:
            MarketTimeState enum value
        """
        if distortion_factor < 1.5:
            return MarketTimeState.NORMAL
        elif distortion_factor < 3.0:
            return MarketTimeState.ACCELERATED
        else:
            return MarketTimeState.EXTREME
    
    def _generate_recommendation(
        self,
        state: MarketTimeState,
        distortion_factor: float
    ) -> str:
        """
        Generate recommendation based on market time state.
        
        Args:
            state: Market time state
            distortion_factor: Market time distortion factor
            
        Returns:
            Recommendation string
        """
        if state == MarketTimeState.NORMAL:
            return "Normal market time, standard trading protocols"
        elif state == MarketTimeState.ACCELERATED:
            exposure_reduction = min(0.8, (distortion_factor - 1.0) / 2.0)
            return (
                f"Market time accelerated ({distortion_factor:.1f}x), "
                f"reduce exposure by {exposure_reduction:.0%}, "
                f"prioritize liquidity"
            )
        else:  # EXTREME
            return (
                f"Market time extremely accelerated ({distortion_factor:.1f}x), "
                f"reduce exposure by 80-90%, "
                f"prioritize capital preservation"
            )
    
    def register_baseline(self, symbol: str, metric: str, value: float) -> None:
        """
        Register a baseline value for a symbol and metric.
        
        Args:
            symbol: Market symbol
            metric: Metric name
            value: Baseline value
        """
        if symbol not in self.baselines:
            self.baselines[symbol] = {}
        
        self.baselines[symbol][metric] = value
        self.logger.debug(f"Registered baseline for {symbol} {metric}: {value}")
    
    def get_active_events(self, symbol: str) -> List[MarketTimeAccelerationEvent]:
        """
        Get active market time acceleration events for a symbol.
        
        Args:
            symbol: Market symbol
            
        Returns:
            List of active events
        """
        return self.active_events.get(symbol, [])
