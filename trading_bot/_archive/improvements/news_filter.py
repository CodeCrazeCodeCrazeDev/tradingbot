"""
News Event Filter
=================

Filters trades based on economic events:
1. Economic calendar integration
2. High-impact event detection
3. Pre-news position management
4. Post-news re-entry logic

Target: Avoid news volatility disasters
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class NewsImpact(Enum):
    """Impact level of news events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # NFP, FOMC, etc.


class EventType(Enum):
    """Types of economic events"""
    INTEREST_RATE = "interest_rate"
    EMPLOYMENT = "employment"
    GDP = "gdp"
    INFLATION = "inflation"
    RETAIL_SALES = "retail_sales"
    MANUFACTURING = "manufacturing"
    CENTRAL_BANK = "central_bank"
    TRADE_BALANCE = "trade_balance"
    HOUSING = "housing"
    CONSUMER = "consumer"
    OTHER = "other"


@dataclass
class EconomicEvent:
    """An economic calendar event"""
    event_id: str
    name: str
    currency: str
    impact: NewsImpact
    event_type: EventType
    scheduled_time: datetime
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'name': self.name,
            'currency': self.currency,
            'impact': self.impact.value,
            'event_type': self.event_type.value,
            'scheduled_time': self.scheduled_time.isoformat(),
            'actual': self.actual,
            'forecast': self.forecast,
            'previous': self.previous,
        }


@dataclass
class NewsFilterResult:
    """Result of news filter check"""
    can_trade: bool
    upcoming_events: List[EconomicEvent]
    minutes_to_next_event: Optional[int]
    affected_currencies: List[str]
    reason: str
    risk_level: str  # 'low', 'medium', 'high'


class EconomicCalendar:
    """
    Manages economic calendar data.
    
    Note: In production, this would fetch from an API like:
    - Forex Factory
    - Investing.com
    - Trading Economics
    """
    
    # Major recurring events by currency
    MAJOR_EVENTS = {
        'USD': [
            ('NFP', NewsImpact.CRITICAL, EventType.EMPLOYMENT),
            ('FOMC', NewsImpact.CRITICAL, EventType.INTEREST_RATE),
            ('CPI', NewsImpact.HIGH, EventType.INFLATION),
            ('GDP', NewsImpact.HIGH, EventType.GDP),
            ('Retail Sales', NewsImpact.MEDIUM, EventType.RETAIL_SALES),
            ('ISM Manufacturing', NewsImpact.MEDIUM, EventType.MANUFACTURING),
            ('Unemployment Claims', NewsImpact.MEDIUM, EventType.EMPLOYMENT),
        ],
        'EUR': [
            ('ECB Rate Decision', NewsImpact.CRITICAL, EventType.INTEREST_RATE),
            ('German CPI', NewsImpact.HIGH, EventType.INFLATION),
            ('Eurozone GDP', NewsImpact.HIGH, EventType.GDP),
            ('German ZEW', NewsImpact.MEDIUM, EventType.CONSUMER),
        ],
        'GBP': [
            ('BOE Rate Decision', NewsImpact.CRITICAL, EventType.INTEREST_RATE),
            ('UK CPI', NewsImpact.HIGH, EventType.INFLATION),
            ('UK GDP', NewsImpact.HIGH, EventType.GDP),
            ('UK Employment', NewsImpact.MEDIUM, EventType.EMPLOYMENT),
        ],
        'JPY': [
            ('BOJ Rate Decision', NewsImpact.CRITICAL, EventType.INTEREST_RATE),
            ('Japan CPI', NewsImpact.HIGH, EventType.INFLATION),
            ('Japan GDP', NewsImpact.HIGH, EventType.GDP),
        ],
        'AUD': [
            ('RBA Rate Decision', NewsImpact.CRITICAL, EventType.INTEREST_RATE),
            ('Australia Employment', NewsImpact.HIGH, EventType.EMPLOYMENT),
            ('Australia CPI', NewsImpact.HIGH, EventType.INFLATION),
        ],
        'CAD': [
            ('BOC Rate Decision', NewsImpact.CRITICAL, EventType.INTEREST_RATE),
            ('Canada Employment', NewsImpact.HIGH, EventType.EMPLOYMENT),
            ('Canada CPI', NewsImpact.HIGH, EventType.INFLATION),
        ],
        'CHF': [
            ('SNB Rate Decision', NewsImpact.CRITICAL, EventType.INTEREST_RATE),
        ],
        'NZD': [
            ('RBNZ Rate Decision', NewsImpact.CRITICAL, EventType.INTEREST_RATE),
        ],
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Cache for events
        self.events: List[EconomicEvent] = []
        self.last_update: Optional[datetime] = None
        
        # Cache file path
        self.cache_path = Path(self.config.get('cache_path', 'cache/economic_calendar.json'))
        
        # Load cached events
        self._load_cache()
        
        logger.info("EconomicCalendar initialized")
    
    def _load_cache(self):
        """Load cached events from file"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path) as f:
                    data = json.load(f)
                    self.events = [
                        EconomicEvent(
                            event_id=e['event_id'],
                            name=e['name'],
                            currency=e['currency'],
                            impact=NewsImpact(e['impact']),
                            event_type=EventType(e['event_type']),
                            scheduled_time=datetime.fromisoformat(e['scheduled_time']),
                            actual=e.get('actual'),
                            forecast=e.get('forecast'),
                            previous=e.get('previous'),
                        )
                        for e in data.get('events', [])
                    ]
                    self.last_update = datetime.fromisoformat(data.get('last_update', '2000-01-01'))
            except Exception as e:
                logger.warning(f"Failed to load calendar cache: {e}")
    
    def _save_cache(self):
        """Save events to cache file"""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, 'w') as f:
                json.dump({
                    'events': [e.to_dict() for e in self.events],
                    'last_update': datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save calendar cache: {e}")
    
    def add_event(self, event: EconomicEvent):
        """Add an event to the calendar"""
        self.events.append(event)
        self._save_cache()
    
    def get_upcoming_events(
        self,
        hours_ahead: int = 24,
        currencies: Optional[List[str]] = None,
        min_impact: NewsImpact = NewsImpact.MEDIUM
    ) -> List[EconomicEvent]:
        """
        Get upcoming events within the specified time window.
        
        Args:
            hours_ahead: Hours to look ahead
            currencies: Filter by currencies (None = all)
            min_impact: Minimum impact level
        
        Returns:
            List of upcoming events
        """
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours_ahead)
        
        impact_order = {
            NewsImpact.LOW: 0,
            NewsImpact.MEDIUM: 1,
            NewsImpact.HIGH: 2,
            NewsImpact.CRITICAL: 3,
        }
        min_impact_value = impact_order[min_impact]
        
        upcoming = []
        for event in self.events:
            # Check time
            event_time = event.scheduled_time
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            
            if not (now <= event_time <= cutoff):
                continue
            
            # Check currency
            if currencies and event.currency not in currencies:
                continue
            
            # Check impact
            if impact_order[event.impact] < min_impact_value:
                continue
            
            upcoming.append(event)
        
        # Sort by time
        upcoming.sort(key=lambda e: e.scheduled_time)
        
        return upcoming
    
    def get_events_for_symbol(
        self,
        symbol: str,
        hours_ahead: int = 24
    ) -> List[EconomicEvent]:
        """Get events affecting a trading symbol"""
        # Extract currencies from symbol
        currencies = []
        if len(symbol) >= 6:
            currencies.append(symbol[:3])
            currencies.append(symbol[3:6])
        
        return self.get_upcoming_events(
            hours_ahead=hours_ahead,
            currencies=currencies
        )
    
    def generate_sample_events(self):
        """Generate sample events for testing"""
        now = datetime.now(timezone.utc)
        
        sample_events = [
            EconomicEvent(
                event_id='nfp_001',
                name='Non-Farm Payrolls',
                currency='USD',
                impact=NewsImpact.CRITICAL,
                event_type=EventType.EMPLOYMENT,
                scheduled_time=now + timedelta(hours=2),
                forecast=180000,
                previous=175000,
            ),
            EconomicEvent(
                event_id='ecb_001',
                name='ECB Rate Decision',
                currency='EUR',
                impact=NewsImpact.CRITICAL,
                event_type=EventType.INTEREST_RATE,
                scheduled_time=now + timedelta(hours=5),
                forecast=4.25,
                previous=4.25,
            ),
            EconomicEvent(
                event_id='cpi_001',
                name='US CPI',
                currency='USD',
                impact=NewsImpact.HIGH,
                event_type=EventType.INFLATION,
                scheduled_time=now + timedelta(hours=8),
                forecast=3.2,
                previous=3.4,
            ),
        ]
        
        self.events.extend(sample_events)
        self._save_cache()
        
        return sample_events


class NewsEventFilter:
    """
    Filters trades based on upcoming news events.
    
    PRINCIPLE: Avoid trading during high-impact news releases.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize calendar
        self.calendar = EconomicCalendar(self.config.get('calendar', {}))
        
        # Time buffers (minutes)
        self.pre_news_buffer = self.config.get('pre_news_buffer', 30)  # Before event
        self.post_news_buffer = self.config.get('post_news_buffer', 15)  # After event
        
        # Critical event buffers (larger)
        self.critical_pre_buffer = self.config.get('critical_pre_buffer', 60)
        self.critical_post_buffer = self.config.get('critical_post_buffer', 30)
        
        # Whether to close positions before news
        self.close_before_news = self.config.get('close_before_news', True)
        
        # Minimum impact to filter
        self.min_impact = NewsImpact(self.config.get('min_impact', 'high'))
        
        logger.info(f"NewsEventFilter initialized: pre={self.pre_news_buffer}m, post={self.post_news_buffer}m")
    
    def check_can_trade(
        self,
        symbol: str,
        current_time: Optional[datetime] = None
    ) -> NewsFilterResult:
        """
        Check if trading is allowed based on news events.
        
        Args:
            symbol: Trading symbol
            current_time: Current time (default: now)
        
        Returns:
            NewsFilterResult with trading recommendation
        """
        current_time = current_time or datetime.now(timezone.utc)
        
        # Get upcoming events for this symbol
        events = self.calendar.get_events_for_symbol(symbol, hours_ahead=4)
        
        # Filter by minimum impact
        impact_order = {
            NewsImpact.LOW: 0,
            NewsImpact.MEDIUM: 1,
            NewsImpact.HIGH: 2,
            NewsImpact.CRITICAL: 3,
        }
        min_impact_value = impact_order[self.min_impact]
        
        relevant_events = [
            e for e in events
            if impact_order[e.impact] >= min_impact_value
        ]
        
        if not relevant_events:
            return NewsFilterResult(
                can_trade=True,
                upcoming_events=[],
                minutes_to_next_event=None,
                affected_currencies=[],
                reason="No high-impact news upcoming",
                risk_level='low'
            )
        
        # Check each event
        affected_currencies = set()
        closest_event = None
        min_minutes = float('inf')
        
        for event in relevant_events:
            event_time = event.scheduled_time
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            
            minutes_to_event = (event_time - current_time).total_seconds() / 60
            
            # Determine buffer based on impact
            if event.impact == NewsImpact.CRITICAL:
                pre_buffer = self.critical_pre_buffer
                post_buffer = self.critical_post_buffer
            else:
                pre_buffer = self.pre_news_buffer
                post_buffer = self.post_news_buffer
            
            # Check if within buffer zone
            if -post_buffer <= minutes_to_event <= pre_buffer:
                affected_currencies.add(event.currency)
                
                if abs(minutes_to_event) < abs(min_minutes):
                    min_minutes = minutes_to_event
                    closest_event = event
        
        if closest_event:
            # Within news buffer - don't trade
            if min_minutes > 0:
                reason = f"News in {int(min_minutes)}m: {closest_event.name} ({closest_event.currency})"
            else:
                reason = f"News released {int(-min_minutes)}m ago: {closest_event.name}"
            
            risk_level = 'high' if closest_event.impact == NewsImpact.CRITICAL else 'medium'
            
            return NewsFilterResult(
                can_trade=False,
                upcoming_events=relevant_events,
                minutes_to_next_event=int(min_minutes) if min_minutes != float('inf') else None,
                affected_currencies=list(affected_currencies),
                reason=reason,
                risk_level=risk_level
            )
        
        # Not within buffer, but events upcoming
        next_event = relevant_events[0]
        event_time = next_event.scheduled_time
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        
        minutes_to_next = int((event_time - current_time).total_seconds() / 60)
        
        return NewsFilterResult(
            can_trade=True,
            upcoming_events=relevant_events,
            minutes_to_next_event=minutes_to_next,
            affected_currencies=[e.currency for e in relevant_events],
            reason=f"Next event in {minutes_to_next}m: {next_event.name}",
            risk_level='medium' if minutes_to_next < 60 else 'low'
        )
    
    def should_close_position(
        self,
        symbol: str,
        position_direction: str,
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Check if position should be closed before news.
        
        Returns:
            Tuple of (should_close, reason)
        """
        if not self.close_before_news:
            return False, "Close before news disabled"
        
        result = self.check_can_trade(symbol, current_time)
        
        if not result.can_trade and result.risk_level == 'high':
            return True, f"Close before critical news: {result.reason}"
        
        return False, "No need to close"
    
    def get_safe_trading_windows(
        self,
        symbol: str,
        hours_ahead: int = 24
    ) -> List[Tuple[datetime, datetime]]:
        """
        Get safe trading windows avoiding news events.
        
        Returns:
            List of (start_time, end_time) tuples
        """
        events = self.calendar.get_events_for_symbol(symbol, hours_ahead)
        
        if not events:
            now = datetime.now(timezone.utc)
            return [(now, now + timedelta(hours=hours_ahead))]
        
        windows = []
        now = datetime.now(timezone.utc)
        current_start = now
        
        for event in sorted(events, key=lambda e: e.scheduled_time):
            event_time = event.scheduled_time
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            
            # Determine buffer
            if event.impact == NewsImpact.CRITICAL:
                pre_buffer = self.critical_pre_buffer
                post_buffer = self.critical_post_buffer
            else:
                pre_buffer = self.pre_news_buffer
                post_buffer = self.post_news_buffer
            
            # Window before event
            window_end = event_time - timedelta(minutes=pre_buffer)
            if window_end > current_start:
                windows.append((current_start, window_end))
            
            # Next window starts after post buffer
            current_start = event_time + timedelta(minutes=post_buffer)
        
        # Final window
        end_time = now + timedelta(hours=hours_ahead)
        if current_start < end_time:
            windows.append((current_start, end_time))
        
        return windows
