"""
AlphaAlgo Core - Anti-Learning Firewall (Layer 5)

FORBIDDEN from learning from:
- Tail events
- Black swans
- Liquidity vacuums
- Forced liquidations
- Structural breaks

Reason: Learning from rare extremes poisons generalization.
These events are logged, isolated, and excluded from model updates.
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
    AntiLearningResult
)

logger = logging.getLogger(__name__)


class ExtremeEventType(Enum):
    """Types of extreme events to exclude from learning"""
    TAIL_EVENT = "tail_event"
    BLACK_SWAN = "black_swan"
    LIQUIDITY_VACUUM = "liquidity_vacuum"
    FORCED_LIQUIDATION = "forced_liquidation"
    STRUCTURAL_BREAK = "structural_break"


class AntiLearningFirewall(GovernanceLayer):
    """
    Layer 5 - Anti-Learning Firewall
    
    Prevents the system from learning from extreme events that would poison generalization.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("anti_learning_firewall")
        self.config = config or {}
        
        # Detection thresholds
        self.thresholds = {
            "tail_event_zscore": self.config.get("tail_event_zscore", 3.5),  # Z-score threshold for tail events
            "black_swan_zscore": self.config.get("black_swan_zscore", 6.0),  # Z-score threshold for black swans
            "liquidity_vacuum_ratio": self.config.get("liquidity_vacuum_ratio", 0.2),  # Liquidity ratio threshold
            "forced_liquidation_volume_ratio": self.config.get("forced_liquidation_volume_ratio", 3.0),  # Volume spike ratio
            "structural_break_threshold": self.config.get("structural_break_threshold", 0.9),  # Structural break probability threshold
        }
        
        # Extreme event registry
        self.extreme_events = {}
        
        # Load previously identified extreme events if available
        self._load_extreme_events()
        
        # Event detectors for different extreme event types
        self.event_detectors = {
            ExtremeEventType.TAIL_EVENT: self._detect_tail_event,
            ExtremeEventType.BLACK_SWAN: self._detect_black_swan,
            ExtremeEventType.LIQUIDITY_VACUUM: self._detect_liquidity_vacuum,
            ExtremeEventType.FORCED_LIQUIDATION: self._detect_forced_liquidation,
            ExtremeEventType.STRUCTURAL_BREAK: self._detect_structural_break
        }
        
        logger.info(f"Anti-Learning Firewall initialized with thresholds: {self.thresholds}")
    
    def _load_extreme_events(self):
        """Load previously identified extreme events"""
        try:
            # Try to load from file
            events_path = self.config.get("extreme_events_path", "extreme_events.json")
            with open(events_path, 'r') as f:
                self.extreme_events = json.load(f)
            logger.info(f"Loaded {len(self.extreme_events)} extreme events")
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is invalid, start with empty dict
            self.extreme_events = {}
            logger.info("No existing extreme events found, starting fresh")
    
    def _save_extreme_events(self):
        """Save identified extreme events to persistent storage"""
        try:
            # Save to file
            events_path = self.config.get("extreme_events_path", "extreme_events.json")
            with open(events_path, 'w') as f:
                json.dump(self.extreme_events, f)
            logger.info(f"Saved {len(self.extreme_events)} extreme events")
        except Exception as e:
            logger.error(f"Error saving extreme events: {e}")
    
    def register_extreme_event(self, event_id: str, event_type: ExtremeEventType, details: Dict[str, Any]):
        """
        Register an extreme event to be excluded from learning.
        """
        if event_id not in self.extreme_events:
            self.extreme_events[event_id] = {
                "type": event_type.value,
                "timestamp": time.time(),
                "details": details
            }
            logger.warning(f"Extreme event {event_id} of type {event_type.value} registered and excluded from learning")
            self._save_extreme_events()
    
    async def process(self, event: Dict[str, Any]) -> AntiLearningResult:
        """
        Process a market event to determine if it should be excluded from learning.
        
        Args:
            event: Market event data
            
        Returns:
            AntiLearningResult with exclusion determination
        """
        try:
            # Extract event ID
            event_id = event.get("id", str(time.time()))
            
            # Check if event is already known to be extreme
            if event_id in self.extreme_events:
                event_type = self.extreme_events[event_id]["type"]
                return AntiLearningResult(
                    event_id=event_id,
                    is_extreme_event=True,
                    should_exclude=True,
                    reason=f"Previously identified extreme event of type {event_type}"
                )
            
            # Check for each type of extreme event
            for event_type in ExtremeEventType:
                detector = self.event_detectors.get(event_type)
                if detector:
                    is_extreme, details = await detector(event)
                    
                    if is_extreme:
                        # Register the extreme event
                        self.register_extreme_event(event_id, event_type, details)
                        
                        return AntiLearningResult(
                            event_id=event_id,
                            is_extreme_event=True,
                            should_exclude=True,
                            reason=f"Detected extreme event of type {event_type.value}: {details.get('reason', '')}"
                        )
            
            # If we get here, the event is not extreme
            return AntiLearningResult(
                event_id=event_id,
                is_extreme_event=False,
                should_exclude=False,
                reason="Normal market event, suitable for learning"
            )
            
        except Exception as e:
            logger.exception(f"Error in anti-learning firewall: {e}")
            # On error, exclude the event to be safe
            return AntiLearningResult(
                event_id=str(time.time()),
                is_extreme_event=True,
                should_exclude=True,
                reason=f"Error in extreme event detection: {str(e)}"
            )
    
    # === Extreme event detectors ===
    
    async def _detect_tail_event(self, event: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect tail events (extreme price moves beyond normal distribution).
        
        Returns a tuple of (is_extreme, details).
        """
        details = {"type": ExtremeEventType.TAIL_EVENT.value}
        
        # Check if event has price data
        if "price" not in event:
            return False, details
        
        # Check if event has return data
        if "return" not in event:
            return False, details
        
        # Get the return
        ret = event["return"]
        
        # Check if event has historical statistics
        if "stats" in event and "return_mean" in event["stats"] and "return_std" in event["stats"]:
            mean = event["stats"]["return_mean"]
            std = event["stats"]["return_std"]
            
            if std > 0:
                # Calculate z-score
                z_score = abs((ret - mean) / std)
                details["z_score"] = z_score
                
                # Check if z-score exceeds threshold
                threshold = self.thresholds["tail_event_zscore"]
                if z_score > threshold:
                    details["reason"] = f"Return z-score {z_score:.2f} exceeds threshold {threshold:.2f}"
                    return True, details
        
        # Alternative detection using price change
        if "price_change_pct" in event:
            change_pct = abs(event["price_change_pct"])
            
            # Check if percentage change is extreme
            if change_pct > 10.0:  # 10% move in a single event is extreme
                details["price_change_pct"] = change_pct
                details["reason"] = f"Price change of {change_pct:.2f}% is extreme"
                return True, details
        
        return False, details
    
    async def _detect_black_swan(self, event: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect black swan events (extremely rare, high-impact events).
        
        Returns a tuple of (is_extreme, details).
        """
        details = {"type": ExtremeEventType.BLACK_SWAN.value}
        
        # Check if event has return data
        if "return" not in event:
            return False, details
        
        # Get the return
        ret = event["return"]
        
        # Check if event has historical statistics
        if "stats" in event and "return_mean" in event["stats"] and "return_std" in event["stats"]:
            mean = event["stats"]["return_mean"]
            std = event["stats"]["return_std"]
            
            if std > 0:
                # Calculate z-score
                z_score = abs((ret - mean) / std)
                details["z_score"] = z_score
                
                # Check if z-score exceeds black swan threshold
                threshold = self.thresholds["black_swan_zscore"]
                if z_score > threshold:
                    details["reason"] = f"Return z-score {z_score:.2f} exceeds black swan threshold {threshold:.2f}"
                    return True, details
        
        # Check for market-wide impact
        if "market_impact" in event:
            impact = event["market_impact"]
            
            # Check if impact is extreme
            if impact > 0.8:  # 80% of market affected
                details["market_impact"] = impact
                details["reason"] = f"Market-wide impact of {impact:.2f} indicates black swan event"
                return True, details
        
        # Check for explicit black swan flag
        if "is_black_swan" in event and event["is_black_swan"]:
            details["reason"] = "Event explicitly flagged as black swan"
            return True, details
        
        return False, details
    
    async def _detect_liquidity_vacuum(self, event: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect liquidity vacuum events (sudden disappearance of market liquidity).
        
        Returns a tuple of (is_extreme, details).
        """
        details = {"type": ExtremeEventType.LIQUIDITY_VACUUM.value}
        
        # Check if event has liquidity data
        if "liquidity" not in event:
            return False, details
        
        liquidity = event["liquidity"]
        
        # Check if event has historical liquidity data
        if "normal_liquidity" in event:
            normal_liq = event["normal_liquidity"]
            
            if normal_liq > 0:
                # Calculate liquidity ratio
                liq_ratio = liquidity / normal_liq
                details["liquidity_ratio"] = liq_ratio
                
                # Check if liquidity ratio is below threshold
                threshold = self.thresholds["liquidity_vacuum_ratio"]
                if liq_ratio < threshold:
                    details["reason"] = f"Liquidity ratio {liq_ratio:.2f} below threshold {threshold:.2f}"
                    return True, details
        
        # Check for explicit liquidity vacuum flag
        if "is_liquidity_vacuum" in event and event["is_liquidity_vacuum"]:
            details["reason"] = "Event explicitly flagged as liquidity vacuum"
            return True, details
        
        # Check for bid-ask spread explosion
        if "spread" in event and "normal_spread" in event:
            spread = event["spread"]
            normal_spread = event["normal_spread"]
            
            if normal_spread > 0:
                spread_ratio = spread / normal_spread
                
                if spread_ratio > 5.0:  # Spread 5x normal indicates liquidity vacuum
                    details["spread_ratio"] = spread_ratio
                    details["reason"] = f"Spread ratio {spread_ratio:.2f} indicates liquidity vacuum"
                    return True, details
        
        return False, details
    
    async def _detect_forced_liquidation(self, event: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect forced liquidation events (cascading liquidations causing price spirals).
        
        Returns a tuple of (is_extreme, details).
        """
        details = {"type": ExtremeEventType.FORCED_LIQUIDATION.value}
        
        # Check if event has volume data
        if "volume" not in event:
            return False, details
        
        volume = event["volume"]
        
        # Check if event has historical volume data
        if "normal_volume" in event:
            normal_vol = event["normal_volume"]
            
            if normal_vol > 0:
                # Calculate volume ratio
                vol_ratio = volume / normal_vol
                details["volume_ratio"] = vol_ratio
                
                # Check if volume ratio exceeds threshold
                threshold = self.thresholds["forced_liquidation_volume_ratio"]
                if vol_ratio > threshold:
                    # High volume spike could indicate forced liquidations
                    
                    # Check if price moved significantly in the same direction
                    if "price_change_pct" in event and abs(event["price_change_pct"]) > 3.0:
                        details["reason"] = f"Volume ratio {vol_ratio:.2f} with significant price move indicates forced liquidation"
                        return True, details
        
        # Check for explicit forced liquidation flag
        if "is_forced_liquidation" in event and event["is_forced_liquidation"]:
            details["reason"] = "Event explicitly flagged as forced liquidation"
            return True, details
        
        # Check for liquidation data
        if "liquidations" in event:
            liquidations = event["liquidations"]
            
            if liquidations > 0:
                # Check if liquidations are abnormally high
                if "normal_liquidations" in event and event["normal_liquidations"] > 0:
                    liq_ratio = liquidations / event["normal_liquidations"]
                    
                    if liq_ratio > 3.0:  # 3x normal liquidations
                        details["liquidation_ratio"] = liq_ratio
                        details["reason"] = f"Liquidation ratio {liq_ratio:.2f} indicates forced liquidation cascade"
                        return True, details
        
        return False, details
    
    async def _detect_structural_break(self, event: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect structural breaks (fundamental changes in market relationships).
        
        Returns a tuple of (is_extreme, details).
        """
        details = {"type": ExtremeEventType.STRUCTURAL_BREAK.value}
        
        # Check for explicit structural break probability
        if "structural_break_probability" in event:
            prob = event["structural_break_probability"]
            details["probability"] = prob
            
            # Check if probability exceeds threshold
            threshold = self.thresholds["structural_break_threshold"]
            if prob > threshold:
                details["reason"] = f"Structural break probability {prob:.2f} exceeds threshold {threshold:.2f}"
                return True, details
        
        # Check for correlation breakdown
        if "correlation_breakdown" in event:
            breakdown = event["correlation_breakdown"]
            
            if breakdown > 0.7:  # Severe correlation breakdown
                details["correlation_breakdown"] = breakdown
                details["reason"] = f"Correlation breakdown of {breakdown:.2f} indicates structural break"
                return True, details
        
        # Check for regime change
        if "regime_change" in event and event["regime_change"]:
            if "regime_change_severity" in event:
                severity = event["regime_change_severity"]
                
                if severity > 0.8:  # Severe regime change
                    details["regime_change_severity"] = severity
                    details["reason"] = f"Severe regime change (severity: {severity:.2f}) indicates structural break"
                    return True, details
            else:
                details["reason"] = "Explicit regime change flagged"
                return True, details
        
        # Check for explicit structural break flag
        if "is_structural_break" in event and event["is_structural_break"]:
            details["reason"] = "Event explicitly flagged as structural break"
            return True, details
        
        return False, details
