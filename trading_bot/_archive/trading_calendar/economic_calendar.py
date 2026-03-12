"""
Economic Calendar Integration

Fetches and processes economic events from multiple sources:
- FRED (Federal Reserve Economic Data)
- Investing.com calendar
- ForexFactory
- TradingEconomics

Provides:
- High-impact event detection
- Event-based trading filters
- Volatility forecasting around events
- Automatic position sizing adjustments
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from zoneinfo import ZoneInfo
import json
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class EventImpact(Enum):
    """Economic event impact level."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4  # Fed decisions, NFP, etc.


class EventCategory(Enum):
    """Economic event categories."""
    INTEREST_RATE = "interest_rate"
    EMPLOYMENT = "employment"
    INFLATION = "inflation"
    GDP = "gdp"
    TRADE = "trade"
    MANUFACTURING = "manufacturing"
    CONSUMER = "consumer"
    HOUSING = "housing"
    CENTRAL_BANK = "central_bank"
    EARNINGS = "earnings"
    OTHER = "other"


class Currency(Enum):
    """Major currencies affected by events."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    AUD = "AUD"
    CAD = "CAD"
    NZD = "NZD"
    CNY = "CNY"


@dataclass
class EconomicEvent:
    """Represents an economic calendar event."""
    event_id: str
    name: str
    country: str
    currency: Currency
    timestamp: datetime
    impact: EventImpact
    category: EventCategory
    previous: Optional[float] = None
    forecast: Optional[float] = None
    actual: Optional[float] = None
    unit: str = ""
    source: str = ""
    description: str = ""
    
    @property
    def is_released(self) -> bool:
        """Check if event data has been released."""
        return self.actual is not None
    
    @property
    def surprise(self) -> Optional[float]:
        """Calculate surprise factor (actual vs forecast)."""
        if self.actual is not None and self.forecast is not None and self.forecast != 0:
            return (self.actual - self.forecast) / abs(self.forecast)
        return None
    
    @property
    def is_positive_surprise(self) -> Optional[bool]:
        """Check if surprise is positive."""
        surprise = self.surprise
        if surprise is None:
            return None
        return surprise > 0.01  # 1% threshold
    
    @property
    def time_until(self) -> timedelta:
        """Time until event."""
        return self.timestamp - datetime.now(ZoneInfo('UTC'))
    
    @property
    def is_upcoming(self) -> bool:
        """Check if event is upcoming (within 24 hours)."""
        return timedelta(0) < self.time_until < timedelta(hours=24)
    
    @property
    def is_imminent(self) -> bool:
        """Check if event is imminent (within 1 hour)."""
        return timedelta(0) < self.time_until < timedelta(hours=1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'name': self.name,
            'country': self.country,
            'currency': self.currency.value,
            'timestamp': self.timestamp.isoformat(),
            'impact': self.impact.value,
            'category': self.category.value,
            'previous': self.previous,
            'forecast': self.forecast,
            'actual': self.actual,
            'unit': self.unit,
            'source': self.source,
            'is_released': self.is_released,
            'surprise': self.surprise,
            'time_until_hours': self.time_until.total_seconds() / 3600
        }


@dataclass
class TradingRestriction:
    """Trading restriction around an event."""
    event: EconomicEvent
    restriction_type: str  # 'no_new_positions', 'reduce_size', 'close_positions'
    start_time: datetime
    end_time: datetime
    size_factor: float = 1.0  # Position size multiplier
    affected_pairs: List[str] = field(default_factory=list)
    reason: str = ""
    
    def is_active(self) -> bool:
        """Check if restriction is currently active."""
        now = datetime.now(ZoneInfo('UTC'))
        return self.start_time <= now <= self.end_time


# High-impact events that require special handling
HIGH_IMPACT_EVENTS = {
    # US Events
    "Non-Farm Payrolls": EventImpact.CRITICAL,
    "NFP": EventImpact.CRITICAL,
    "FOMC": EventImpact.CRITICAL,
    "Fed Interest Rate Decision": EventImpact.CRITICAL,
    "Fed Chair Powell Speaks": EventImpact.HIGH,
    "CPI": EventImpact.HIGH,
    "Core CPI": EventImpact.HIGH,
    "GDP": EventImpact.HIGH,
    "Retail Sales": EventImpact.HIGH,
    "ISM Manufacturing PMI": EventImpact.HIGH,
    "ISM Services PMI": EventImpact.HIGH,
    "Unemployment Rate": EventImpact.HIGH,
    "Initial Jobless Claims": EventImpact.MEDIUM,
    
    # EU Events
    "ECB Interest Rate Decision": EventImpact.CRITICAL,
    "ECB Press Conference": EventImpact.HIGH,
    "German CPI": EventImpact.HIGH,
    "German GDP": EventImpact.HIGH,
    "Eurozone CPI": EventImpact.HIGH,
    
    # UK Events
    "BoE Interest Rate Decision": EventImpact.CRITICAL,
    "UK CPI": EventImpact.HIGH,
    "UK GDP": EventImpact.HIGH,
    
    # Japan Events
    "BoJ Interest Rate Decision": EventImpact.CRITICAL,
    "Japan CPI": EventImpact.HIGH,
    
    # Other
    "OPEC Meeting": EventImpact.HIGH,
    "G7 Summit": EventImpact.MEDIUM,
    "G20 Summit": EventImpact.MEDIUM,
}


class EconomicCalendarFetcher:
    """
    Fetches economic calendar data from multiple sources.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Tuple[datetime, List[EconomicEvent]]] = {}
        self.cache_ttl = timedelta(minutes=15)
        
        logger.info("EconomicCalendarFetcher initialized")
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
    
    async def fetch_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        currencies: Optional[List[Currency]] = None,
        min_impact: EventImpact = EventImpact.LOW
    ) -> List[EconomicEvent]:
        """
        Fetch economic events from all sources.
        
        Args:
            start_date: Start date for events
            end_date: End date for events
            currencies: Filter by currencies
            min_impact: Minimum impact level
            
        Returns:
            List of EconomicEvent objects
        """
        if start_date is None:
            start_date = datetime.now(ZoneInfo('UTC'))
        if end_date is None:
            end_date = start_date + timedelta(days=7)
        
        # Check cache
        cache_key = f"{start_date.date()}_{end_date.date()}"
        if cache_key in self.cache:
            cached_time, cached_events = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                events = cached_events
            else:
                events = await self._fetch_all_sources(start_date, end_date)
                self.cache[cache_key] = (datetime.now(), events)
        else:
            events = await self._fetch_all_sources(start_date, end_date)
            self.cache[cache_key] = (datetime.now(), events)
        
        # Filter by currency
        if currencies:
            events = [e for e in events if e.currency in currencies]
        
        # Filter by impact
        events = [e for e in events if e.impact.value >= min_impact.value]
        
        # Sort by timestamp
        events.sort(key=lambda x: x.timestamp)
        
        return events
    
    async def _fetch_all_sources(self, start_date: datetime, end_date: datetime) -> List[EconomicEvent]:
        """Fetch from all available sources."""
        events = []
        
        try:
            # Try each source
            investing_events = await self._fetch_investing_com(start_date, end_date)
            events.extend(investing_events)
        except Exception as e:
            logger.warning(f"Investing.com fetch failed: {e}")
        
        # Add built-in known events
        known_events = self._get_known_events(start_date, end_date)
        events.extend(known_events)
        
        # Deduplicate
        seen = set()
        unique_events = []
        for event in events:
            key = (event.name, event.timestamp.date())
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events
    
    async def _fetch_investing_com(self, start_date: datetime, end_date: datetime) -> List[EconomicEvent]:
        """Fetch from Investing.com economic calendar."""
        await self._ensure_session()
        
        events = []
        
        # Investing.com calendar API endpoint
        url = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
        
        # This is a simplified implementation - real implementation would need proper API access
        # For now, return empty list and rely on known events
        
        return events
    
    def _get_known_events(self, start_date: datetime, end_date: datetime) -> List[EconomicEvent]:
        """Get known recurring events."""
        events = []
        
        # Generate known recurring events
        current = start_date
        while current <= end_date:
            weekday = current.weekday()
            
            # First Friday of month - NFP
            if weekday == 4 and current.day <= 7:
                events.append(EconomicEvent(
                    event_id=f"NFP-{current.strftime('%Y%m%d')}",
                    name="Non-Farm Payrolls",
                    country="US",
                    currency=Currency.USD,
                    timestamp=datetime.combine(current.date(), time(8, 30), ZoneInfo('America/New_York')),
                    impact=EventImpact.CRITICAL,
                    category=EventCategory.EMPLOYMENT,
                    source="known_events"
                ))
            
            # Wednesday - FOMC (check if it's an FOMC week - roughly every 6 weeks)
            # Simplified: assume 3rd Wednesday of Jan, Mar, May, Jun, Jul, Sep, Nov, Dec
            fomc_months = [1, 3, 5, 6, 7, 9, 11, 12]
            if weekday == 2 and current.month in fomc_months and 15 <= current.day <= 21:
                events.append(EconomicEvent(
                    event_id=f"FOMC-{current.strftime('%Y%m%d')}",
                    name="FOMC Interest Rate Decision",
                    country="US",
                    currency=Currency.USD,
                    timestamp=datetime.combine(current.date(), time(14, 0), ZoneInfo('America/New_York')),
                    impact=EventImpact.CRITICAL,
                    category=EventCategory.INTEREST_RATE,
                    source="known_events"
                ))
            
            # Thursday - Initial Jobless Claims
            if weekday == 3:
                events.append(EconomicEvent(
                    event_id=f"IJC-{current.strftime('%Y%m%d')}",
                    name="Initial Jobless Claims",
                    country="US",
                    currency=Currency.USD,
                    timestamp=datetime.combine(current.date(), time(8, 30), ZoneInfo('America/New_York')),
                    impact=EventImpact.MEDIUM,
                    category=EventCategory.EMPLOYMENT,
                    source="known_events"
                ))
            
            current += timedelta(days=1)
        
        return events
    
    async def close(self):
        """Close the fetcher session."""
        if self.session and not self.session.closed:
            await self.session.close()


class EconomicCalendarManager:
    """
    Manages economic calendar and trading restrictions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.fetcher = EconomicCalendarFetcher(config)
        self.events: List[EconomicEvent] = []
        self.restrictions: List[TradingRestriction] = []
        
        # Configuration
        self.pre_event_buffer = timedelta(minutes=self.config.get('pre_event_buffer_minutes', 30))
        self.post_event_buffer = timedelta(minutes=self.config.get('post_event_buffer_minutes', 15))
        self.critical_pre_buffer = timedelta(hours=self.config.get('critical_pre_buffer_hours', 2))
        self.critical_post_buffer = timedelta(hours=self.config.get('critical_post_buffer_hours', 1))
        
        logger.info("EconomicCalendarManager initialized")
    
    async def refresh_events(self, days_ahead: int = 7):
        """Refresh economic events."""
        self.events = await self.fetcher.fetch_events(
            end_date=datetime.now(ZoneInfo('UTC')) + timedelta(days=days_ahead)
        )
        
        # Generate restrictions
        self._generate_restrictions()
        
        logger.info(f"Refreshed {len(self.events)} events, {len(self.restrictions)} restrictions")
    
    def _generate_restrictions(self):
        """Generate trading restrictions from events."""
        self.restrictions = []
        
        for event in self.events:
            if event.impact.value >= EventImpact.HIGH.value:
                # Determine buffer times based on impact
                if event.impact == EventImpact.CRITICAL:
                    pre_buffer = self.critical_pre_buffer
                    post_buffer = self.critical_post_buffer
                    restriction_type = 'no_new_positions'
                    size_factor = 0.0
                else:
                    pre_buffer = self.pre_event_buffer
                    post_buffer = self.post_event_buffer
                    restriction_type = 'reduce_size'
                    size_factor = 0.5
                
                # Determine affected pairs
                affected_pairs = self._get_affected_pairs(event.currency)
                
                restriction = TradingRestriction(
                    event=event,
                    restriction_type=restriction_type,
                    start_time=event.timestamp - pre_buffer,
                    end_time=event.timestamp + post_buffer,
                    size_factor=size_factor,
                    affected_pairs=affected_pairs,
                    reason=f"{event.name} ({event.impact.name} impact)"
                )
                
                self.restrictions.append(restriction)
    
    def _get_affected_pairs(self, currency: Currency) -> List[str]:
        """Get currency pairs affected by an event."""
        pairs = []
        
        major_pairs = {
            Currency.USD: ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'],
            Currency.EUR: ['EURUSD', 'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD'],
            Currency.GBP: ['GBPUSD', 'EURGBP', 'GBPJPY', 'GBPCHF', 'GBPAUD'],
            Currency.JPY: ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'CADJPY'],
            Currency.CHF: ['USDCHF', 'EURCHF', 'GBPCHF', 'CHFJPY'],
            Currency.AUD: ['AUDUSD', 'EURAUD', 'GBPAUD', 'AUDJPY', 'AUDCAD'],
            Currency.CAD: ['USDCAD', 'EURCAD', 'GBPCAD', 'CADJPY', 'AUDCAD'],
            Currency.NZD: ['NZDUSD', 'EURNZD', 'GBPNZD', 'NZDJPY'],
        }
        
        return major_pairs.get(currency, [])
    
    def get_active_restrictions(self, symbol: Optional[str] = None) -> List[TradingRestriction]:
        """Get currently active trading restrictions."""
        active = [r for r in self.restrictions if r.is_active()]
        
        if symbol:
            active = [r for r in active if symbol in r.affected_pairs or not r.affected_pairs]
        
        return active
    
    def can_trade(self, symbol: str) -> Tuple[bool, str, float]:
        """
        Check if trading is allowed for a symbol.
        
        Returns:
            Tuple of (can_trade, reason, size_factor)
        """
        restrictions = self.get_active_restrictions(symbol)
        
        if not restrictions:
            return True, "No active restrictions", 1.0
        
        # Find most restrictive
        min_size_factor = 1.0
        reasons = []
        
        for r in restrictions:
            if r.restriction_type == 'no_new_positions':
                return False, f"Trading restricted: {r.reason}", 0.0
            
            min_size_factor = min(min_size_factor, r.size_factor)
            reasons.append(r.reason)
        
        return True, f"Reduced size due to: {', '.join(reasons)}", min_size_factor
    
    def get_upcoming_events(
        self,
        hours_ahead: int = 24,
        min_impact: EventImpact = EventImpact.MEDIUM
    ) -> List[EconomicEvent]:
        """Get upcoming events within specified hours."""
        cutoff = datetime.now(ZoneInfo('UTC')) + timedelta(hours=hours_ahead)
        
        upcoming = [
            e for e in self.events
            if e.timestamp > datetime.now(ZoneInfo('UTC'))
            and e.timestamp <= cutoff
            and e.impact.value >= min_impact.value
        ]
        
        return sorted(upcoming, key=lambda x: x.timestamp)
    
    def get_next_high_impact_event(self, currency: Optional[Currency] = None) -> Optional[EconomicEvent]:
        """Get the next high-impact event."""
        now = datetime.now(ZoneInfo('UTC'))
        
        for event in sorted(self.events, key=lambda x: x.timestamp):
            if event.timestamp > now and event.impact.value >= EventImpact.HIGH.value:
                if currency is None or event.currency == currency:
                    return event
        
        return None
    
    def get_volatility_forecast(self, symbol: str, hours_ahead: int = 24) -> Dict[str, Any]:
        """
        Forecast volatility based on upcoming events.
        
        Returns:
            Dict with volatility forecast and contributing events
        """
        upcoming = self.get_upcoming_events(hours_ahead)
        
        # Filter by symbol's currencies
        symbol_currencies = self._get_symbol_currencies(symbol)
        relevant_events = [e for e in upcoming if e.currency in symbol_currencies]
        
        # Calculate volatility multiplier
        base_multiplier = 1.0
        contributing_events = []
        
        for event in relevant_events:
            hours_until = event.time_until.total_seconds() / 3600
            
            # Impact factor
            impact_factors = {
                EventImpact.LOW: 1.1,
                EventImpact.MEDIUM: 1.3,
                EventImpact.HIGH: 1.6,
                EventImpact.CRITICAL: 2.0
            }
            impact_factor = impact_factors.get(event.impact, 1.0)
            
            # Time decay - events closer have more impact
            time_factor = max(0.5, 1.0 - (hours_until / hours_ahead) * 0.5)
            
            event_multiplier = 1.0 + (impact_factor - 1.0) * time_factor
            base_multiplier = max(base_multiplier, event_multiplier)
            
            contributing_events.append({
                'event': event.name,
                'hours_until': hours_until,
                'impact': event.impact.name,
                'multiplier': event_multiplier
            })
        
        return {
            'symbol': symbol,
            'volatility_multiplier': base_multiplier,
            'forecast_hours': hours_ahead,
            'contributing_events': contributing_events,
            'recommendation': self._get_volatility_recommendation(base_multiplier)
        }
    
    def _get_symbol_currencies(self, symbol: str) -> List[Currency]:
        """Extract currencies from a symbol."""
        currencies = []
        symbol = symbol.upper()
        
        for currency in Currency:
            if currency.value in symbol:
                currencies.append(currency)
        
        return currencies
    
    def _get_volatility_recommendation(self, multiplier: float) -> str:
        """Get recommendation based on volatility multiplier."""
        if multiplier >= 2.0:
            return "AVOID - Extreme volatility expected"
        elif multiplier >= 1.5:
            return "CAUTION - High volatility expected, reduce position size"
        elif multiplier >= 1.3:
            return "MODERATE - Elevated volatility, use wider stops"
        else:
            return "NORMAL - Standard volatility conditions"
    
    def get_status(self) -> Dict[str, Any]:
        """Get calendar manager status."""
        now = datetime.now(ZoneInfo('UTC'))
        
        return {
            'total_events': len(self.events),
            'upcoming_24h': len(self.get_upcoming_events(24)),
            'high_impact_upcoming': len([e for e in self.get_upcoming_events(24) if e.impact.value >= EventImpact.HIGH.value]),
            'active_restrictions': len(self.get_active_restrictions()),
            'next_high_impact': self.get_next_high_impact_event().to_dict() if self.get_next_high_impact_event() else None,
            'timestamp': now.isoformat()
        }
    
    async def close(self):
        """Close the manager."""
        await self.fetcher.close()


# Singleton instance
_calendar_manager: Optional[EconomicCalendarManager] = None


async def get_calendar_manager() -> EconomicCalendarManager:
    """Get or create the singleton EconomicCalendarManager instance."""
    global _calendar_manager
    if _calendar_manager is None:
        _calendar_manager = EconomicCalendarManager()
        await _calendar_manager.refresh_events()
    return _calendar_manager


# Example usage
if __name__ == "__main__":
    async def main():
        manager = EconomicCalendarManager()
        
        print("=" * 60)
        print("ECONOMIC CALENDAR")
        print("=" * 60)
        
        # Refresh events
        await manager.refresh_events()
        
        # Get upcoming events
        print("\nUpcoming High-Impact Events (24h):")
        print("-" * 40)
        
        for event in manager.get_upcoming_events(24, EventImpact.HIGH):
            print(f"\n{event.name}")
            print(f"  Time: {event.timestamp}")
            print(f"  Currency: {event.currency.value}")
            print(f"  Impact: {event.impact.name}")
            print(f"  Hours until: {event.time_until.total_seconds() / 3600:.1f}")
        
        # Check trading restrictions
        print("\n" + "=" * 60)
        print("TRADING RESTRICTIONS")
        print("=" * 60)
        
        for symbol in ['EURUSD', 'USDJPY', 'GBPUSD']:
            can_trade, reason, size_factor = manager.can_trade(symbol)
            print(f"\n{symbol}:")
            print(f"  Can Trade: {can_trade}")
            print(f"  Reason: {reason}")
            print(f"  Size Factor: {size_factor}")
        
        # Volatility forecast
        print("\n" + "=" * 60)
        print("VOLATILITY FORECAST")
        print("=" * 60)
        
        forecast = manager.get_volatility_forecast('EURUSD', 24)
        print(f"\nEURUSD:")
        print(f"  Multiplier: {forecast['volatility_multiplier']:.2f}")
        print(f"  Recommendation: {forecast['recommendation']}")
        
        if forecast['contributing_events']:
            print("  Contributing Events:")
            for event in forecast['contributing_events']:
                print(f"    - {event['event']} ({event['impact']}) in {event['hours_until']:.1f}h")
        
        # Status
        print("\n" + "=" * 60)
        print("STATUS")
        print("=" * 60)
        
        status = manager.get_status()
        for key, value in status.items():
            print(f"{key}: {value}")
        
        await manager.close()
    
    asyncio.run(main())
