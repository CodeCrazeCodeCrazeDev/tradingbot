"""
NEWS FILTER MODULE - PHASE 2 QUICK-WIN #1
============================================================

Implements news-based trading filters to avoid trading during high-impact events.

Features:
- Economic calendar event detection
- News sentiment analysis
- Trading pause on major events
- Event impact scoring

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional

import numpy as np
import numpy

logger = logging.getLogger(__name__)


class EventImpact(Enum):
    """Economic event impact level."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class EventType(Enum):
    """Types of economic events."""
    CENTRAL_BANK = auto()
    EMPLOYMENT = auto()
    INFLATION = auto()
    GDP = auto()
    RETAIL_SALES = auto()
    HOUSING = auto()
    MANUFACTURING = auto()
    CONSUMER_CONFIDENCE = auto()
    TRADE = auto()
    EARNINGS = auto()


@dataclass
class EconomicEvent:
    """Economic event data."""
    event_type: EventType
    symbol: str
    event_time: datetime
    impact: EventImpact
    forecast: float
    actual: Optional[float] = None
    previous: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.now()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class NewsFilter:
    """Filters trades based on news and economic events."""
    
    def __init__(self, lookback_hours: int = 24, 
                 pause_duration_minutes: int = 30):
        """
        Initialize news filter.
        
        Args:
            lookback_hours: Hours to look back for events
            pause_duration_minutes: Minutes to pause trading after event
        """
        try:
            self.lookback_hours = lookback_hours
            self.pause_duration_minutes = pause_duration_minutes
        
            self.events: List[EconomicEvent] = []
            self.upcoming_events: List[EconomicEvent] = []
            self.trading_paused = False
            self.pause_until = None
        
            # Impact multipliers for position sizing
            self.impact_multipliers = {
                EventImpact.LOW: 1.0,
                EventImpact.MEDIUM: 0.75,
                EventImpact.HIGH: 0.5,
                EventImpact.CRITICAL: 0.0
            }
        
            logger.info("News filter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_event(self, event: EconomicEvent):
        """Add economic event."""
        try:
            self.events.append(event)
        
            # Keep only recent events
            cutoff = datetime.now() - timedelta(hours=self.lookback_hours)
            self.events = [e for e in self.events if e.timestamp >= cutoff]
        
            logger.info(f"Event added: {event.event_type.name} ({event.impact.name})")
        except Exception as e:
            logger.error(f"Error in add_event: {e}")
            raise
    
    def add_upcoming_event(self, event: EconomicEvent):
        """Add upcoming event."""
        try:
            self.upcoming_events.append(event)
            self.upcoming_events.sort(key=lambda e: e.event_time)
        
            logger.info(f"Upcoming event: {event.event_type.name} at {event.event_time}")
        except Exception as e:
            logger.error(f"Error in add_upcoming_event: {e}")
            raise
    
    def should_pause_trading(self) -> bool:
        """Check if trading should be paused."""
        try:
            now = datetime.now()
        
            # Check if pause duration has expired
            if self.trading_paused and self.pause_until:
                if now >= self.pause_until:
                    self.trading_paused = False
                    self.pause_until = None
                    logger.info("Trading pause lifted")
        
            # Check for upcoming critical events
            for event in self.upcoming_events:
                time_until = (event.event_time - now).total_seconds() / 60
            
                # Pause 5 minutes before critical events
                if event.impact == EventImpact.CRITICAL and 0 <= time_until <= 5:
                    self.trading_paused = True
                    self.pause_until = event.event_time + timedelta(minutes=self.pause_duration_minutes)
                    logger.warning(f"Trading paused for critical event: {event.event_type.name}")
                    return True
            
                # Pause 2 minutes before high-impact events
                if event.impact == EventImpact.HIGH and 0 <= time_until <= 2:
                    self.trading_paused = True
                    self.pause_until = event.event_time + timedelta(minutes=self.pause_duration_minutes)
                    logger.warning(f"Trading paused for high-impact event: {event.event_type.name}")
                    return True
        
            return self.trading_paused
        except Exception as e:
            logger.error(f"Error in should_pause_trading: {e}")
            raise
    
    def get_position_size_multiplier(self) -> float:
        """Get position size multiplier based on upcoming events."""
        try:
            now = datetime.now()
            min_multiplier = 1.0
        
            for event in self.upcoming_events:
                time_until = (event.event_time - now).total_seconds() / 60
            
                # Apply multiplier if event is within 60 minutes
                if 0 <= time_until <= 60:
                    multiplier = self.impact_multipliers[event.impact]
                    min_multiplier = min(min_multiplier, multiplier)
        
            return min_multiplier
        except Exception as e:
            logger.error(f"Error in get_position_size_multiplier: {e}")
            raise
    
    def get_event_summary(self, symbol: str) -> str:
        """Get event summary for symbol."""
        try:
            now = datetime.now()
            upcoming = [e for e in self.upcoming_events 
                       if e.symbol == symbol and e.event_time >= now]
        
            if not upcoming:
                return f"No upcoming events for {symbol}"
        
            summary = f"UPCOMING EVENTS - {symbol}\n"
            summary += "=" * 50 + "\n"
        
            for event in upcoming[:5]:  # Show next 5 events
                time_until = (event.event_time - now).total_seconds() / 60
                hours = int(time_until // 60)
                minutes = int(time_until % 60)
            
                summary += f"{event.event_type.name}: {hours}h {minutes}m ({event.impact.name})\n"
        
            summary += "=" * 50 + "\n"
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_event_summary: {e}")
            raise
    
    def get_recent_events(self, symbol: str, hours: int = 24) -> List[EconomicEvent]:
        """Get recent events for symbol."""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            return [e for e in self.events 
                   if e.symbol == symbol and e.timestamp >= cutoff]
        except Exception as e:
            logger.error(f"Error in get_recent_events: {e}")
            raise
    
    def calculate_surprise(self, event: EconomicEvent) -> float:
        """
        Calculate surprise factor (actual vs forecast).
        
        Returns:
            Surprise magnitude (0-1)
        """
        try:
            if event.actual is None or event.forecast is None:
                return 0
        
            if event.forecast == 0:
                return 0
        
            surprise = abs(event.actual - event.forecast) / abs(event.forecast)
            return min(1.0, surprise)
        except Exception as e:
            logger.error(f"Error in calculate_surprise: {e}")
            raise
    
    def get_volatility_spike_risk(self, symbol: str) -> float:
        """
        Estimate volatility spike risk based on upcoming events.
        
        Returns:
            Risk score (0-1)
        """
        try:
            now = datetime.now()
            risk = 0.0
        
            for event in self.upcoming_events:
                if event.symbol != symbol:
                    continue
            
                time_until = (event.event_time - now).total_seconds() / 60
            
                # Events within 60 minutes have risk
                if 0 <= time_until <= 60:
                    impact_risk = {
                        EventImpact.LOW: 0.1,
                        EventImpact.MEDIUM: 0.3,
                        EventImpact.HIGH: 0.6,
                        EventImpact.CRITICAL: 0.9
                    }
                
                    risk = max(risk, impact_risk[event.impact])
        
            return risk
        except Exception as e:
            logger.error(f"Error in get_volatility_spike_risk: {e}")
            raise
    
    def reset(self):
        """Reset filter."""
        try:
            self.events.clear()
            self.upcoming_events.clear()
            self.trading_paused = False
            self.pause_until = None
            logger.info("News filter reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
