"""
Elite Trading Bot - Economic Calendar

This module provides economic calendar integration for the Elite Trading Bot,
enabling tracking of scheduled economic events, forecasts, and results.
"""

import enum
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

try:
    import aiohttp
except ImportError:
    aiohttp = None
import pandas as pd
import numpy as np

from .event_monitor import EventMonitor, EconomicEvent, EventType, EventPriority, EventSource
from enum import Enum
import json
from enum import auto
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



# Configure logging
logger = logging.getLogger(__name__)


class EconomicIndicator(enum.Enum):
    """Types of economic indicators."""
    GDP = "gdp"                           # Gross Domestic Product
    CPI = "cpi"                           # Consumer Price Index
    PPI = "ppi"                           # Producer Price Index
    NFP = "nfp"                           # Non-Farm Payrolls
    UNEMPLOYMENT = "unemployment"         # Unemployment Rate
    RETAIL_SALES = "retail_sales"         # Retail Sales
    INDUSTRIAL_PRODUCTION = "industrial_production"  # Industrial Production
    HOUSING_STARTS = "housing_starts"     # Housing Starts
    BUILDING_PERMITS = "building_permits" # Building Permits
    EXISTING_HOME_SALES = "existing_home_sales"  # Existing Home Sales
    DURABLE_GOODS = "durable_goods"       # Durable Goods Orders
    TRADE_BALANCE = "trade_balance"       # Trade Balance
    INTEREST_RATE = "interest_rate"       # Interest Rate Decision
    PMI = "pmi"                           # Purchasing Managers' Index
    ISM = "ism"                           # Institute for Supply Management Index
    CONSUMER_CONFIDENCE = "consumer_confidence"  # Consumer Confidence
    FOMC_STATEMENT = "fomc_statement"     # FOMC Statement
    FOMC_MINUTES = "fomc_minutes"         # FOMC Meeting Minutes
    ECB_DECISION = "ecb_decision"         # European Central Bank Decision
    BOJ_DECISION = "boj_decision"         # Bank of Japan Decision
    BOE_DECISION = "boe_decision"         # Bank of England Decision
    OTHER = "other"                       # Other indicators


class EconomicEventImpact(enum.Enum):
    """Impact levels for economic events."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class EconomicEventResult:
    """Result of an economic event."""
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    revised_previous: Optional[float] = None
    surprise_factor: Optional[float] = None
    beat_expectations: Optional[bool] = None
    
    def __post_init__(self):
        """Calculate derived fields if not provided."""
        if (self.actual is not None and 
            self.forecast is not None and 
            self.surprise_factor is None and
            self.forecast != 0):
            self.surprise_factor = (self.actual - self.forecast) / abs(self.forecast)
            
        if (self.actual is not None and 
            self.forecast is not None and 
            self.beat_expectations is None):
            self.beat_expectations = self.actual > self.forecast


class ForecastAnalyzer:
    """Analyzes economic forecasts and results."""
    
    def __init__(self):
        """Initialize forecast analyzer."""
        # Historical data for indicators
        self.historical_data: Dict[str, List[EconomicEventResult]] = {}
        
    def add_result(self, indicator: str, result: EconomicEventResult):
        """
        Add a result for an indicator.
        
        Args:
            indicator: Indicator name or code
            result: Result data
        """
        if indicator not in self.historical_data:
            self.historical_data[indicator] = []
            
        self.historical_data[indicator].append(result)
        
        # Keep only recent history (last 10 results)
        if len(self.historical_data[indicator]) > 10:
            self.historical_data[indicator] = self.historical_data[indicator][-10:]
    
    def get_forecast_accuracy(self, indicator: str) -> Optional[float]:
        """
        Calculate forecast accuracy for an indicator.
        
        Args:
            indicator: Indicator name or code
            
        Returns:
            Accuracy as percentage (0-100) or None if insufficient data
        """
        if indicator not in self.historical_data:
            return None
            
        results = self.historical_data[indicator]
        
        # Need at least 3 results for meaningful accuracy
        if len(results) < 3:
            return None
            
        # Calculate average absolute surprise factor
        surprise_factors = [
            abs(result.surprise_factor) 
            for result in results 
            if result.surprise_factor is not None
        ]
        
        if not surprise_factors:
            return None
            
        avg_surprise = sum(surprise_factors) / len(surprise_factors)
        
        # Convert to accuracy percentage (inverse of surprise)
        # Lower surprise = higher accuracy
        accuracy = max(0, 100 - (avg_surprise * 100))
        
        return accuracy
    
    def get_trend(self, indicator: str) -> Optional[str]:
        """
        Determine trend for an indicator.
        
        Args:
            indicator: Indicator name or code
            
        Returns:
            'up', 'down', 'flat', or None if insufficient data
        """
        if indicator not in self.historical_data:
            return None
            
        results = self.historical_data[indicator]
        
        # Need at least 3 results for meaningful trend
        if len(results) < 3:
            return None
            
        # Get actual values
        actuals = [
            result.actual 
            for result in results 
            if result.actual is not None
        ]
        
        if len(actuals) < 3:
            return None
            
        # Simple trend calculation
        if actuals[-1] > actuals[-2] > actuals[-3]:
            return "up"
        elif actuals[-1] < actuals[-2] < actuals[-3]:
            return "down"
        else:
            return "flat"
    
    def get_beat_rate(self, indicator: str) -> Optional[float]:
        """
        Calculate how often an indicator beats expectations.
        
        Args:
            indicator: Indicator name or code
            
        Returns:
            Beat rate as percentage (0-100) or None if insufficient data
        """
        if indicator not in self.historical_data:
            return None
            
        results = self.historical_data[indicator]
        
        # Need at least 3 results for meaningful rate
        if len(results) < 3:
            return None
            
        beats = [
            result.beat_expectations 
            for result in results 
            if result.beat_expectations is not None
        ]
        
        if not beats:
            return None
            
        beat_rate = sum(1 for beat in beats if beat) / len(beats) * 100
        
        return beat_rate


class EconomicCalendar:
    """
    Economic calendar system for tracking scheduled economic events,
    forecasts, and results.
    """
    
    def __init__(self, 
                 event_monitor: EventMonitor,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize economic calendar.
        
        Args:
            event_monitor: Event monitoring system
            config: Optional configuration dictionary
        """
        self.event_monitor = event_monitor
        self.config = config or {}
        self._init_default_config()
        
        # Initialize components
        self.forecast_analyzer = ForecastAnalyzer()
        
        # Upcoming and past events
        self.upcoming_events: Dict[str, Dict[str, Any]] = {}
        self.past_events: Dict[str, Dict[str, Any]] = {}
        
        # API clients
        self.api_clients: Dict[str, Any] = {}
        
        # Enable economic source in event monitor
        self.event_monitor.enable_source(EventSource.ECONOMIC_CALENDAR)
        
        logger.info("EconomicCalendar initialized")
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        defaults = {
            "lookback_days": 7,
            "lookahead_days": 14,
            "high_impact_only": False,
            "default_countries": ["US", "EU", "GB", "JP", "CN", "CA", "AU", "NZ"],
            "refresh_interval_minutes": 60,
            "api_request_timeout": 30,
            "auto_refresh": True
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    async def configure_api(self, provider: str, api_key: str, **kwargs):
        """
        Configure API client for an economic calendar provider.
        
        Args:
            provider: Provider name (e.g., 'tradermade', 'forexfactory')
            api_key: API key for the provider
            **kwargs: Additional configuration parameters
        """
        self.api_clients[provider] = {
            "api_key": api_key,
            "base_url": kwargs.get("base_url"),
            "session": None,
            "config": kwargs
        }
        logger.info(f"Configured API client for {provider}")
    
    async def _get_session(self, provider: str) -> aiohttp.ClientSession:
        """Get or create an aiohttp session for a provider."""
        if provider not in self.api_clients:
            raise ValueError(f"API client for {provider} not configured")
            
        client = self.api_clients[provider]
        
        if client["session"] is None or client["session"].closed:
            client["session"] = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config["api_request_timeout"])
            )
            
        return client["session"]
    
    async def fetch_calendar(self, provider: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetch economic calendar data from a provider.
        
        Args:
            provider: Provider name
            start_date: Start date for events
            end_date: End date for events
            
        Returns:
            List of economic events
        """
        if provider not in self.api_clients:
            raise ValueError(f"API client for {provider} not configured")
            
        client = self.api_clients[provider]
        session = await self._get_session(provider)
        
        # Build request URL and parameters based on the provider
        if provider == "tradermade":
            url = f"{client['base_url']}/calendar"
            params = {
                "api_key": client["api_key"],
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            
            # Add countries filter if specified
            countries = self.config["default_countries"]
            if countries:
                params["countries"] = ",".join(countries)
        
        elif provider == "forexfactory":
            # ForexFactory doesn't have an official API, this is a placeholder
            # for a potential third-party API or scraper
            url = f"{client['base_url']}/calendar"
            params = {
                "api_key": client["api_key"],
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            }
        
        else:
            pass
        try:
            # Generic handling for other providers
            url = client["base_url"]
            params = {
                "api_key": client["api_key"],
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
        
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Parse response based on provider
                if provider == "tradermade":
                    return data.get("data", [])
                elif provider == "forexfactory":
                    return data.get("calendar", [])
                else:
                    return data.get("events", [])
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching calendar from {provider}: {e}")
            return []
    
    def _map_impact_level(self, impact: str) -> EconomicEventImpact:
        """Map provider-specific impact level to standard enum."""
        impact = impact.lower()
        
        if impact in ("high", "h", "3"):
            return EconomicEventImpact.HIGH
        elif impact in ("medium", "med", "m", "2"):
            return EconomicEventImpact.MEDIUM
        elif impact in ("low", "l", "1"):
            return EconomicEventImpact.LOW
        else:
            return EconomicEventImpact.UNKNOWN
    
    def _map_indicator_type(self, name: str) -> EconomicIndicator:
        """Map event name to indicator type."""
        name_lower = name.lower()
        
        # GDP
        if "gdp" in name_lower:
            return EconomicIndicator.GDP
        
        # Inflation
        elif any(term in name_lower for term in ["cpi", "consumer price", "inflation"]):
            return EconomicIndicator.CPI
        elif any(term in name_lower for term in ["ppi", "producer price"]):
            return EconomicIndicator.PPI
        
        # Employment
        elif any(term in name_lower for term in ["nfp", "non-farm", "payroll"]):
            return EconomicIndicator.NFP
        elif any(term in name_lower for term in ["unemployment", "jobless"]):
            return EconomicIndicator.UNEMPLOYMENT
        
        # Retail
        elif "retail sales" in name_lower:
            return EconomicIndicator.RETAIL_SALES
        
        # Manufacturing
        elif "industrial production" in name_lower:
            return EconomicIndicator.INDUSTRIAL_PRODUCTION
        elif "durable goods" in name_lower:
            return EconomicIndicator.DURABLE_GOODS
        elif "pmi" in name_lower:
            return EconomicIndicator.PMI
        elif "ism" in name_lower:
            return EconomicIndicator.ISM
        
        # Housing
        elif "housing starts" in name_lower:
            return EconomicIndicator.HOUSING_STARTS
        elif "building permits" in name_lower:
            return EconomicIndicator.BUILDING_PERMITS
        elif "existing home sales" in name_lower:
            return EconomicIndicator.EXISTING_HOME_SALES
        
        # Trade
        elif "trade balance" in name_lower:
            return EconomicIndicator.TRADE_BALANCE
        
        # Central Banks
        elif any(term in name_lower for term in ["interest rate", "rate decision"]):
            return EconomicIndicator.INTEREST_RATE
        elif "fomc statement" in name_lower:
            return EconomicIndicator.FOMC_STATEMENT
        elif "fomc minutes" in name_lower:
            return EconomicIndicator.FOMC_MINUTES
        elif "ecb" in name_lower:
            return EconomicIndicator.ECB_DECISION
        elif "boj" in name_lower:
            return EconomicIndicator.BOJ_DECISION
        elif "boe" in name_lower:
            return EconomicIndicator.BOE_DECISION
        
        # Consumer
        elif "consumer confidence" in name_lower:
            return EconomicIndicator.CONSUMER_CONFIDENCE
        
        # Default
        else:
            return EconomicIndicator.OTHER
    
    def _standardize_event(self, event: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """
        Standardize event data from different providers.
        
        Args:
            event: Raw event data
            provider: Provider name
            
        Returns:
            Standardized event data
        """
        if provider == "tradermade":
            # TraderMade format
            return {
                "id": event.get("id", str(hash(f"{event.get('date')}_{event.get('title')}"))),
                "title": event.get("title", ""),
                "country": event.get("country", ""),
                "date": datetime.fromisoformat(event.get("date").replace("Z", "+00:00")) if event.get("date") else None,
                "impact": self._map_impact_level(event.get("impact", "")),
                "forecast": self._parse_numeric(event.get("forecast", "")),
                "previous": self._parse_numeric(event.get("previous", "")),
                "actual": self._parse_numeric(event.get("actual", "")),
                "unit": event.get("unit", ""),
                "indicator": self._map_indicator_type(event.get("title", "")),
                "currency": event.get("currency", "")
            }
        
        elif provider == "forexfactory":
            # ForexFactory format (placeholder)
            return {
                "id": event.get("id", str(hash(f"{event.get('date')}_{event.get('title')}"))),
                "title": event.get("title", ""),
                "country": event.get("country", ""),
                "date": datetime.fromisoformat(event.get("date").replace("Z", "+00:00")) if event.get("date") else None,
                "impact": self._map_impact_level(event.get("impact", "")),
                "forecast": self._parse_numeric(event.get("forecast", "")),
                "previous": self._parse_numeric(event.get("previous", "")),
                "actual": self._parse_numeric(event.get("actual", "")),
                "unit": event.get("unit", ""),
                "indicator": self._map_indicator_type(event.get("title", "")),
                "currency": event.get("currency", "")
            }
        
        else:
            # Generic format
            return {
                "id": event.get("id", str(hash(f"{event.get('date')}_{event.get('name')}"))),
                "title": event.get("name", event.get("title", "")),
                "country": event.get("country", ""),
                "date": datetime.fromisoformat(event.get("date").replace("Z", "+00:00")) if event.get("date") else None,
                "impact": self._map_impact_level(event.get("impact", event.get("importance", ""))),
                "forecast": self._parse_numeric(event.get("forecast", "")),
                "previous": self._parse_numeric(event.get("previous", "")),
                "actual": self._parse_numeric(event.get("actual", "")),
                "unit": event.get("unit", ""),
                "indicator": self._map_indicator_type(event.get("name", event.get("title", ""))),
                "currency": event.get("currency", "")
            }
    
    def _parse_numeric(self, value: Any) -> Optional[float]:
        """Parse numeric value from various formats."""
        if value is None or value == "":
            return None
            
        if isinstance(value, (int, float)):
            return float(value)
            
        if isinstance(value, str):
            # Remove common non-numeric characters
            value = value.replace("%", "").replace("$", "").replace(",", "").strip()
            
            try:
                return float(value)
            except ValueError:
                return None
                
        return None
    
    def _is_high_impact(self, event: Dict[str, Any]) -> bool:
        """Check if an event is high impact."""
        # Central bank decisions are always high impact
        if event["indicator"] in (
            EconomicIndicator.INTEREST_RATE,
            EconomicIndicator.FOMC_STATEMENT,
            EconomicIndicator.ECB_DECISION,
            EconomicIndicator.BOJ_DECISION,
            EconomicIndicator.BOE_DECISION
        ):
            return True
            
        # Check impact level
        return event["impact"] == EconomicEventImpact.HIGH
    
    def _generate_event_id(self, event: Dict[str, Any]) -> str:
        """Generate a unique ID for an event."""
        if "id" in event and event["id"]:
            return f"econ_{event['id']}"
            
        # Generate from date and title
        date_str = event["date"].strftime("%Y%m%d%H%M") if event["date"] else ""
        return f"econ_{date_str}_{hash(event['title'])}"
    
    async def process_event(self, event: Dict[str, Any]) -> Optional[EconomicEvent]:
        """
        Process a single economic event and generate an event if relevant.
        
        Args:
            event: Standardized event data
            
        Returns:
            EconomicEvent or None if not relevant
        """
        # Skip if high impact only is enabled and event is not high impact
        if self.config["high_impact_only"] and not self._is_high_impact(event):
            return None
            
        # Generate event ID
        event_id = self._generate_event_id(event)
        
        # Determine if this is a new or updated event
        is_new = event_id not in self.upcoming_events and event_id not in self.past_events
        
        # Check if event has actual data (has occurred)
        has_occurred = event["actual"] is not None
        
        # Store in appropriate collection
        if has_occurred:
            self.past_events[event_id] = event
            if event_id in self.upcoming_events:
                del self.upcoming_events[event_id]
        else:
            self.upcoming_events[event_id] = event
        
        # Create result object
        result = EconomicEventResult(
            actual=event["actual"],
            forecast=event["forecast"],
            previous=event["previous"]
        )
        
        # Add to forecast analyzer if event has occurred
        if has_occurred and event["indicator"] != EconomicIndicator.OTHER:
            self.forecast_analyzer.add_result(event["indicator"].value, result)
        
        # Determine priority
        if self._is_high_impact(event):
            priority = EventPriority.HIGH
        elif event["impact"] == EconomicEventImpact.MEDIUM:
            priority = EventPriority.MEDIUM
        else:
            priority = EventPriority.LOW
        
        # Create event object
        econ_event = EconomicEvent(
            id=event_id,
            type=EventType.ECONOMIC,
            priority=priority,
            source=EventSource.ECONOMIC_CALENDAR,
            timestamp=event["date"] or datetime.now(),
            description=f"{event['country']} {event['title']}",
            indicator=event["indicator"].value,
            actual_value=event["actual"],
            forecast_value=event["forecast"],
            previous_value=event["previous"],
            impact_level=event["impact"].value,
            country=event["country"],
            currency=event["currency"],
            surprise_factor=result.surprise_factor,
            raw_data=event
        )
        
        # Only add to event monitor if new or has new actual data
        if is_new or (has_occurred and "actual" in event):
            await self.event_monitor.add_event(econ_event)
            
        return econ_event
    
    async def process_events(self, events: List[Dict[str, Any]], provider: str) -> List[EconomicEvent]:
        """
        Process a batch of economic events.
        
        Args:
            events: List of raw event data
            provider: Provider name
            
        Returns:
            List of generated EconomicEvents
        """
        processed_events = []
        
        for raw_event in events:
            # Standardize event data
            std_event = self._standardize_event(raw_event, provider)
            
            # Process event
            event = await self.process_event(std_event)
            if event:
                processed_events.append(event)
                
        logger.info(f"Processed {len(events)} economic events from {provider}, generated {len(processed_events)} events")
        return processed_events
    
    async def fetch_and_process(self, provider: str) -> List[EconomicEvent]:
        """
        Fetch and process economic calendar data.
        
        Args:
            provider: Provider name
            
        Returns:
            List of generated EconomicEvents
        """
        # Calculate date range
        now = datetime.now()
        start_date = now - timedelta(days=self.config["lookback_days"])
        end_date = now + timedelta(days=self.config["lookahead_days"])
        
        # Fetch calendar data
        events = await self.fetch_calendar(provider, start_date, end_date)
        
        # Process events
        return await self.process_events(events, provider)
    
    def get_upcoming_events(self, 
                           hours: Optional[int] = None, 
                           countries: Optional[List[str]] = None,
                           high_impact_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get upcoming economic events.
        
        Args:
            hours: Optional time window in hours
            countries: Optional list of country codes to filter by
            high_impact_only: Whether to include only high impact events
            
        Returns:
            List of upcoming events
        """
        events = list(self.upcoming_events.values())
        
        # Filter by time window
        if hours is not None:
            now = datetime.now()
            cutoff = now + timedelta(hours=hours)
            events = [
                event for event in events 
                if event["date"] and event["date"] <= cutoff
            ]
        
        # Filter by countries
        if countries:
            events = [
                event for event in events
                if event["country"] in countries
            ]
        
        # Filter by impact
        if high_impact_only:
            events = [
                event for event in events
                if self._is_high_impact(event)
            ]
        
        # Sort by date
        events.sort(key=lambda x: x["date"] if x["date"] else datetime.max)
        
        return events
    
    def get_recent_events(self, 
                         hours: Optional[int] = None,
                         countries: Optional[List[str]] = None,
                         high_impact_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get recent economic events.
        
        Args:
            hours: Optional time window in hours
            countries: Optional list of country codes to filter by
            high_impact_only: Whether to include only high impact events
            
        Returns:
            List of recent events
        """
        events = list(self.past_events.values())
        
        # Filter by time window
        if hours is not None:
            now = datetime.now()
            cutoff = now - timedelta(hours=hours)
            events = [
                event for event in events 
                if event["date"] and event["date"] >= cutoff
            ]
        
        # Filter by countries
        if countries:
            events = [
                event for event in events
                if event["country"] in countries
            ]
        
        # Filter by impact
        if high_impact_only:
            events = [
                event for event in events
                if self._is_high_impact(event)
            ]
        
        # Sort by date (most recent first)
        events.sort(key=lambda x: x["date"] if x["date"] else datetime.min, reverse=True)
        
        return events
    
    async def start_auto_refresh(self, provider: str, interval_minutes: Optional[int] = None):
        """
        Start automatic refresh of economic calendar.
        
        Args:
            provider: Provider name
            interval_minutes: Optional refresh interval in minutes
        """
        if not self.config["auto_refresh"]:
            logger.info("Auto-refresh is disabled in configuration")
            return
            
        interval = interval_minutes or self.config["refresh_interval_minutes"]
        
        async def refresh_loop():
            logger.info(f"Starting economic calendar auto-refresh every {interval} minutes")
            while True:
                try:
                    await self.fetch_and_process(provider)
                except Exception as e:
                    logger.error(f"Error in economic calendar refresh: {e}")
                
                await asyncio.sleep(interval * 60)
        
        # Start refresh loop
        asyncio.create_task(refresh_loop())
    
    async def close(self):
        """Close all API client sessions."""
        for provider, client in self.api_clients.items():
            if client["session"] and not client["session"].closed:
                await client["session"].close()
                
        logger.info("Closed all EconomicCalendar API sessions")
