"""
Institutional Time Awareness for TAMIC

This module implements institutional time awareness focusing on:
1. Month-end/quarter-end flows - Institutional rebalancing and window dressing
2. Options expiry effects - Gamma-related flows around options expiry
3. Futures roll periods - Institutional positioning shifts during roll periods
4. Central bank meeting schedules - Liquidity changes around central bank events
5. Fiscal year-end effects - Tax-related positioning and capital flows

The primary goal is to identify periods where institutional flows may dominate
price action, potentially overriding other signals.
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


class FlowType(Enum):
    """Types of institutional flows"""
    MONTH_END = "month_end"
    QUARTER_END = "quarter_end"
    YEAR_END = "year_end"
    OPTIONS_EXPIRY = "options_expiry"
    FUTURES_ROLL = "futures_roll"
    CENTRAL_BANK = "central_bank"
    TAX_RELATED = "tax_related"
    INDEX_REBALANCE = "index_rebalance"


class FlowDirection(Enum):
    """Direction of institutional flows"""
    INFLOW = "inflow"
    OUTFLOW = "outflow"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class FlowStrength(Enum):
    """Strength of institutional flows"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    EXTREME = "extreme"


@dataclass
class InstitutionalFlow:
    """Representation of an institutional flow"""
    flow_type: FlowType
    direction: FlowDirection
    strength: FlowStrength
    start_date: datetime
    end_date: datetime
    description: str
    confidence: float  # 0-1
    is_forced: bool  # True if flow is forced (e.g., month-end rebalancing)
    affected_assets: List[str] = field(default_factory=list)
    source: str = "calendar"  # calendar, detected, estimated


@dataclass
class InstitutionalTimeResult:
    """Result from institutional time analysis"""
    has_forced_flows: bool
    flows: List[InstitutionalFlow]
    confidence_multiplier: float  # Multiplier for signal confidence
    metrics: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class InstitutionalTimeEngine:
    """
    Engine for detecting and analyzing institutional time-based flows.
    
    Identifies periods where institutional flows may dominate price action,
    potentially overriding other signals.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize InstitutionalTimeEngine.
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger("trading_bot.tamic.institutional_time")
        
        # Calendar of known events
        self.calendar = {}
        
        # Flow detection thresholds
        self.flow_thresholds = self.config.get("flow_thresholds", {
            "volume_ratio": 1.5,  # Volume ratio vs. average
            "flow_imbalance": 0.6,  # Imbalance ratio (0.5 = balanced)
            "price_impact": 0.3,  # Price impact vs. average volatility
        })
        
        # Window settings
        self.month_end_window = self.config.get("month_end_window", 3)  # Days before month-end
        self.quarter_end_window = self.config.get("quarter_end_window", 5)  # Days before quarter-end
        self.year_end_window = self.config.get("year_end_window", 7)  # Days before year-end
        self.options_expiry_window = self.config.get("options_expiry_window", 2)  # Days around options expiry
        
        # Flow confidence settings
        self.flow_confidence = self.config.get("flow_confidence", {
            FlowType.MONTH_END: 0.7,
            FlowType.QUARTER_END: 0.8,
            FlowType.YEAR_END: 0.9,
            FlowType.OPTIONS_EXPIRY: 0.6,
            FlowType.FUTURES_ROLL: 0.7,
            FlowType.CENTRAL_BANK: 0.8,
            FlowType.TAX_RELATED: 0.6,
            FlowType.INDEX_REBALANCE: 0.7,
        })
        
        # Initialize calendar
        self._initialize_calendar()
    
    def _initialize_calendar(self):
        """Initialize calendar with known institutional events"""
        # This would typically load from a database or file
        # For now, we'll just initialize with some basic logic
        
        today = datetime.now()
        year = today.year
        
        # Add month-end dates
        for month in range(1, 13):
            # Get last day of month
            if month == 12:
                last_day = datetime(year, month, 31)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Add to calendar
            event_id = f"month_end_{year}_{month}"
            self.calendar[event_id] = {
                "type": FlowType.MONTH_END,
                "date": last_day,
                "description": f"Month-end flows for {last_day.strftime('%B %Y')}",
                "affected_assets": ["all"],  # Affects all assets
            }
            
            # Add quarter-end if applicable
            if month in [3, 6, 9, 12]:
                event_id = f"quarter_end_{year}_{month//3}"
                self.calendar[event_id] = {
                    "type": FlowType.QUARTER_END,
                    "date": last_day,
                    "description": f"Quarter-end flows for Q{month//3} {year}",
                    "affected_assets": ["all"],  # Affects all assets
                }
            
            # Add year-end if applicable
            if month == 12:
                event_id = f"year_end_{year}"
                self.calendar[event_id] = {
                    "type": FlowType.YEAR_END,
                    "date": last_day,
                    "description": f"Year-end flows for {year}",
                    "affected_assets": ["all"],  # Affects all assets
                }
        
        # In a real implementation, would also add:
        # - Options expiry dates
        # - Futures roll periods
        # - Central bank meeting schedules
        # - Index rebalance dates
        
        self.logger.info(f"Initialized institutional calendar with {len(self.calendar)} events")
    
    def _is_in_window(self, target_date: datetime, current_date: datetime, window_days: int) -> bool:
        """
        Check if current_date is within window_days of target_date.
        
        Args:
            target_date: Target date
            current_date: Current date
            window_days: Window in days
            
        Returns:
            True if current_date is within window_days of target_date
        """
        delta = target_date - current_date
        return 0 <= delta.days <= window_days
    
    def _get_active_calendar_flows(self, current_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get active flows from calendar based on current date.
        
        Args:
            current_date: Current date (defaults to today)
            
        Returns:
            List of active flows
        """
        if current_date is None:
            current_date = datetime.now()
        
        active_flows = []
        
        for event_id, event in self.calendar.items():
            event_date = event["date"]
            event_type = event["type"]
            
            # Determine window based on event type
            if event_type == FlowType.MONTH_END:
                window = self.month_end_window
            elif event_type == FlowType.QUARTER_END:
                window = self.quarter_end_window
            elif event_type == FlowType.YEAR_END:
                window = self.year_end_window
            elif event_type == FlowType.OPTIONS_EXPIRY:
                window = self.options_expiry_window
            else:
                window = 2  # Default window
            
            # Check if current date is within window
            if self._is_in_window(event_date, current_date, window):
                active_flows.append(event)
        
        return active_flows
    
    def _detect_flows_from_data(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> List[InstitutionalFlow]:
        """
        Detect institutional flows from market data.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            List of detected institutional flows
        """
        detected_flows = []
        
        # This would typically use more sophisticated analysis
        # For now, we'll use a simple volume-based approach
        
        # Check if we have volume data
        if "volume" not in market_data:
            return detected_flows
        
        volume = market_data["volume"]
        if not isinstance(volume, (list, np.ndarray, pd.Series)):
            return detected_flows
        
        # Convert to numpy array if needed
        if isinstance(volume, list):
            volume = np.array(volume)
        elif isinstance(volume, pd.Series):
            volume = volume.values
        
        # Calculate average volume
        avg_volume = np.mean(volume)
        
        # Check for volume spikes
        recent_volume = volume[-5:]  # Last 5 periods
        recent_avg = np.mean(recent_volume)
        
        # If recent average volume is significantly higher than overall average
        if recent_avg > avg_volume * self.flow_thresholds["volume_ratio"]:
            # Check if we have price data to determine direction
            direction = FlowDirection.UNKNOWN
            
            if "close" in market_data:
                close = market_data["close"]
                if isinstance(close, list):
                    close = np.array(close)
                elif isinstance(close, pd.Series):
                    close = close.values
                
                # Calculate recent price change
                recent_change = (close[-1] / close[-6] - 1) if len(close) >= 6 else 0
                
                # Determine direction based on price change
                if recent_change > 0.01:  # 1% threshold
                    direction = FlowDirection.INFLOW
                elif recent_change < -0.01:
                    direction = FlowDirection.OUTFLOW
                else:
                    direction = FlowDirection.MIXED
            
            # Determine strength based on volume ratio
            volume_ratio = recent_avg / avg_volume
            
            if volume_ratio > 3.0:
                strength = FlowStrength.EXTREME
            elif volume_ratio > 2.0:
                strength = FlowStrength.STRONG
            elif volume_ratio > 1.5:
                strength = FlowStrength.MODERATE
            else:
                strength = FlowStrength.WEAK
            
            # Create flow object
            flow = InstitutionalFlow(
                flow_type=FlowType.INDEX_REBALANCE,  # Default assumption
                direction=direction,
                strength=strength,
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() + timedelta(days=1),
                description=f"Detected unusual volume activity in {symbol}",
                confidence=0.6,  # Lower confidence for detected flows
                is_forced=False,  # Not necessarily forced
                affected_assets=[symbol],
                source="detected"
            )
            
            detected_flows.append(flow)
        
        return detected_flows
    
    async def check_institutional_flows(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> InstitutionalTimeResult:
        """
        Check for institutional flows that may affect the given symbol.
        
        Args:
            symbol: Market symbol
            market_data: Market data dictionary
            
        Returns:
            InstitutionalTimeResult with flow analysis
        """
        self.logger.info(f"Checking institutional flows for {symbol}")
        
        # Get current date (use timestamp from market data if available)
        current_date = datetime.now()
        if "timestamp" in market_data:
            timestamp = market_data["timestamp"]
            if isinstance(timestamp, (int, float)):
                current_date = datetime.fromtimestamp(timestamp)
        
        # Get active flows from calendar
        calendar_flows = self._get_active_calendar_flows(current_date)
        
        # Convert calendar events to InstitutionalFlow objects
        flows = []
        for event in calendar_flows:
            event_type = event["type"]
            
            # Determine flow parameters based on event type
            if event_type == FlowType.MONTH_END:
                strength = FlowStrength.MODERATE
                is_forced = True
            elif event_type == FlowType.QUARTER_END:
                strength = FlowStrength.STRONG
                is_forced = True
            elif event_type == FlowType.YEAR_END:
                strength = FlowStrength.EXTREME
                is_forced = True
            else:
                strength = FlowStrength.MODERATE
                is_forced = False
            
            # Create flow object
            flow = InstitutionalFlow(
                flow_type=event_type,
                direction=FlowDirection.MIXED,  # Default to mixed
                strength=strength,
                start_date=event["date"] - timedelta(days=5),  # Approximate window
                end_date=event["date"] + timedelta(days=1),
                description=event["description"],
                confidence=self.flow_confidence.get(event_type, 0.7),
                is_forced=is_forced,
                affected_assets=event.get("affected_assets", ["all"]),
                source="calendar"
            )
            
            # Only add if this symbol is affected
            if "all" in flow.affected_assets or symbol in flow.affected_assets:
                flows.append(flow)
        
        # Detect flows from market data
        detected_flows = self._detect_flows_from_data(symbol, market_data)
        flows.extend(detected_flows)
        
        # Determine if there are forced flows
        has_forced_flows = any(flow.is_forced for flow in flows)
        
        # Calculate confidence multiplier based on flows
        if not flows:
            confidence_multiplier = 1.0
        else:
            # Start with neutral multiplier
            confidence_multiplier = 1.0
            
            # Adjust based on flow strength and confidence
            for flow in flows:
                # Stronger flows reduce confidence more
                if flow.strength == FlowStrength.EXTREME:
                    strength_factor = 0.5
                elif flow.strength == FlowStrength.STRONG:
                    strength_factor = 0.7
                elif flow.strength == FlowStrength.MODERATE:
                    strength_factor = 0.8
                else:
                    strength_factor = 0.9
                
                # Weighted by flow confidence
                flow_impact = (1 - strength_factor) * flow.confidence
                
                # Apply impact
                confidence_multiplier *= (1 - flow_impact)
            
            # Ensure multiplier is not too low
            confidence_multiplier = max(0.3, confidence_multiplier)
        
        # Prepare metrics
        metrics = {
            "flow_count": len(flows),
            "has_month_end": any(flow.flow_type == FlowType.MONTH_END for flow in flows),
            "has_quarter_end": any(flow.flow_type == FlowType.QUARTER_END for flow in flows),
            "has_year_end": any(flow.flow_type == FlowType.YEAR_END for flow in flows),
            "has_options_expiry": any(flow.flow_type == FlowType.OPTIONS_EXPIRY for flow in flows),
            "has_futures_roll": any(flow.flow_type == FlowType.FUTURES_ROLL for flow in flows),
            "has_detected_flows": any(flow.source == "detected" for flow in flows),
            "confidence_multiplier": confidence_multiplier,
        }
        
        # Log significant flows
        if has_forced_flows:
            self.logger.warning(f"Forced institutional flows detected for {symbol}")
            for flow in [f for f in flows if f.is_forced]:
                self.logger.info(f"  - {flow.description} ({flow.strength.value})")
        
        # Create result
        result = InstitutionalTimeResult(
            has_forced_flows=has_forced_flows,
            flows=flows,
            confidence_multiplier=confidence_multiplier,
            metrics=metrics
        )
        
        return result
