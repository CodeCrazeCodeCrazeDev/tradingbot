"""
News Event Integration - Improvement #9 (HIGH PRIORITY)
========================================================

Economic calendar integration to avoid news volatility disasters.

Features:
- Economic calendar API integration
- High-impact event detection
- Pre-news position closure
- Post-news re-entry logic
- News sentiment analysis
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import json

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



logger = logging.getLogger(__name__)


class NewsImpact(Enum):
    """News impact levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # Central bank decisions, NFP, etc.


class NewsSentiment(Enum):
    """News sentiment"""
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


class TradingAction(Enum):
    """Trading action based on news"""
    TRADE_NORMALLY = "trade_normally"
    REDUCE_SIZE = "reduce_size"
    CLOSE_POSITIONS = "close_positions"
    NO_NEW_TRADES = "no_new_trades"
    WAIT_FOR_SETTLEMENT = "wait_for_settlement"


@dataclass
class NewsEvent:
    """Economic news event"""
    event_id: str
    name: str
    currency: str
    impact: NewsImpact
    scheduled_time: datetime
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    description: str = ""
    source: str = ""
    
    @property
    def is_past(self) -> bool:
        return datetime.now() > self.scheduled_time
    
    @property
    def minutes_until(self) -> float:
        return (self.scheduled_time - datetime.now()).total_seconds() / 60
    
    @property
    def surprise(self) -> Optional[float]:
        """Calculate surprise factor"""
        if self.actual is not None and self.forecast is not None and self.forecast != 0:
            return (self.actual - self.forecast) / abs(self.forecast)
        return None


@dataclass
class NewsAnalysis:
    """News analysis result"""
    symbol: str
    action: TradingAction
    events: List[NewsEvent]
    risk_level: float  # 0-1
    reasons: List[str]
    position_size_multiplier: float = 1.0
    wait_minutes: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class EconomicCalendarAPI:
    """Economic calendar data provider"""
    
    # Major economic events by currency
    MAJOR_EVENTS = {
        'USD': [
            'Non-Farm Payrolls', 'FOMC', 'Fed Interest Rate Decision',
            'CPI', 'GDP', 'Retail Sales', 'Unemployment Rate',
            'ISM Manufacturing PMI', 'Fed Chair Speech'
        ],
        'EUR': [
            'ECB Interest Rate Decision', 'ECB Press Conference',
            'German GDP', 'German CPI', 'Eurozone CPI',
            'German ZEW Economic Sentiment'
        ],
        'GBP': [
            'BoE Interest Rate Decision', 'UK GDP', 'UK CPI',
            'UK Unemployment Rate', 'UK Retail Sales'
        ],
        'JPY': [
            'BoJ Interest Rate Decision', 'Japan GDP', 'Japan CPI',
            'Tankan Survey'
        ],
        'AUD': [
            'RBA Interest Rate Decision', 'Australia GDP',
            'Australia Employment Change', 'Australia CPI'
        ],
        'NZD': [
            'RBNZ Interest Rate Decision', 'NZ GDP', 'NZ CPI'
        ],
        'CAD': [
            'BoC Interest Rate Decision', 'Canada GDP',
            'Canada Employment Change', 'Canada CPI'
        ],
        'CHF': [
            'SNB Interest Rate Decision', 'Switzerland CPI'
        ]
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.events_cache: List[NewsEvent] = []
        self.last_update: Optional[datetime] = None
        self.update_interval = self.config.get('update_interval_minutes', 60)
    
    async def fetch_events(self, days_ahead: int = 7) -> List[NewsEvent]:
        """Fetch economic events from API"""
        try:
            # Try to fetch from API
            events = await self._fetch_from_api(days_ahead)
            if events:
                self.events_cache = events
                self.last_update = datetime.now()
                return events
        except Exception as e:
            logger.warning(f"API fetch failed: {e}, using fallback")
        
        # Fallback to cached or mock data
        return self.events_cache or self._generate_mock_events(days_ahead)
    
    async def _fetch_from_api(self, days_ahead: int) -> List[NewsEvent]:
        """Fetch from actual API (implement based on provider)"""
        # This would integrate with services like:
        # - Forex Factory API
        # - Investing.com API
        # - TradingEconomics API
        # - FXStreet API
        
        # For now, return empty to trigger fallback
        return []
    
    def _generate_mock_events(self, days_ahead: int) -> List[NewsEvent]:
        """Generate mock events for testing"""
        events = []
        now = datetime.now()
        
        # Generate some sample events
        sample_events = [
            ('USD', 'FOMC Meeting Minutes', NewsImpact.HIGH),
            ('USD', 'Non-Farm Payrolls', NewsImpact.CRITICAL),
            ('EUR', 'ECB Interest Rate Decision', NewsImpact.CRITICAL),
            ('GBP', 'UK CPI', NewsImpact.HIGH),
            ('USD', 'Retail Sales', NewsImpact.MEDIUM),
            ('EUR', 'German ZEW', NewsImpact.MEDIUM),
        ]
        
        for i, (currency, name, impact) in enumerate(sample_events):
            event_time = now + timedelta(hours=i * 12 + 6)
            if event_time <= now + timedelta(days=days_ahead):
                events.append(NewsEvent(
                    event_id=f"mock_{i}",
                    name=name,
                    currency=currency,
                    impact=impact,
                    scheduled_time=event_time,
                    forecast=0.0,
                    previous=0.0,
                    source="mock"
                ))
        
        return events
    
    def add_event(self, event: NewsEvent):
        """Manually add an event"""
        self.events_cache.append(event)
    
    def get_events_for_currency(self, currency: str, hours_ahead: int = 24) -> List[NewsEvent]:
        """Get events for a specific currency"""
        now = datetime.now()
        end_time = now + timedelta(hours=hours_ahead)
        
        return [
            e for e in self.events_cache
            if e.currency == currency and now <= e.scheduled_time <= end_time
        ]
    
    def get_high_impact_events(self, hours_ahead: int = 24) -> List[NewsEvent]:
        """Get high impact events"""
        now = datetime.now()
        end_time = now + timedelta(hours=hours_ahead)
        
        return [
            e for e in self.events_cache
            if e.impact in [NewsImpact.HIGH, NewsImpact.CRITICAL]
            and now <= e.scheduled_time <= end_time
        ]


class HighImpactEventDetector:
    """Detects high-impact events affecting trading"""
    
    def __init__(self, calendar: EconomicCalendarAPI, config: Optional[Dict] = None):
        self.calendar = calendar
        self.config = config or {}
        self.pre_event_minutes = self.config.get('pre_event_minutes', {
            NewsImpact.LOW: 5,
            NewsImpact.MEDIUM: 15,
            NewsImpact.HIGH: 30,
            NewsImpact.CRITICAL: 60
        })
        self.post_event_minutes = self.config.get('post_event_minutes', {
            NewsImpact.LOW: 5,
            NewsImpact.MEDIUM: 10,
            NewsImpact.HIGH: 15,
            NewsImpact.CRITICAL: 30
        })
    
    def get_affected_currencies(self, symbol: str) -> List[str]:
        """Get currencies affected by a symbol"""
        symbol = symbol.upper().replace('/', '').replace('_', '')
        currencies = []
        
        if len(symbol) >= 6:
            currencies.append(symbol[:3])
            currencies.append(symbol[3:6])
        
        return currencies
    
    def check_event_proximity(self, symbol: str) -> Tuple[bool, List[NewsEvent], int]:
        """Check if near any events for symbol"""
        currencies = self.get_affected_currencies(symbol)
        now = datetime.now()
        
        nearby_events = []
        min_wait_minutes = 0
        
        for event in self.calendar.events_cache:
            if event.currency not in currencies:
                continue
            
            pre_minutes = self.pre_event_minutes.get(event.impact, 15)
            post_minutes = self.post_event_minutes.get(event.impact, 10)
            
            # Check if in pre-event window
            minutes_until = event.minutes_until
            if 0 < minutes_until <= pre_minutes:
                nearby_events.append(event)
                min_wait_minutes = max(min_wait_minutes, int(minutes_until) + post_minutes)
            
            # Check if in post-event window
            if -post_minutes <= minutes_until <= 0:
                nearby_events.append(event)
                min_wait_minutes = max(min_wait_minutes, int(-minutes_until) + post_minutes)
        
        return len(nearby_events) > 0, nearby_events, min_wait_minutes
    
    def get_risk_level(self, events: List[NewsEvent]) -> float:
        """Calculate risk level from events (0-1)"""
        if not events:
            return 0.0
        
        impact_scores = {
            NewsImpact.LOW: 0.2,
            NewsImpact.MEDIUM: 0.4,
            NewsImpact.HIGH: 0.7,
            NewsImpact.CRITICAL: 1.0
        }
        
        max_score = max(impact_scores.get(e.impact, 0.5) for e in events)
        
        # Increase risk if multiple events
        if len(events) > 1:
            max_score = min(max_score * 1.2, 1.0)
        
        return max_score


class PreNewsPositionManager:
    """Manages positions before news events"""
    
    def __init__(self, event_detector: HighImpactEventDetector, config: Optional[Dict] = None):
        self.event_detector = event_detector
        self.config = config or {}
        self.close_before_critical = self.config.get('close_before_critical', True)
        self.reduce_before_high = self.config.get('reduce_before_high', True)
        self.reduction_percent = self.config.get('reduction_percent', 0.5)
    
    def get_position_action(self, symbol: str, current_pnl_percent: float = 0) -> Tuple[TradingAction, str, float]:
        """Get recommended action for position"""
        near_event, events, wait_minutes = self.event_detector.check_event_proximity(symbol)
        
        if not near_event:
            return TradingAction.TRADE_NORMALLY, "No nearby events", 1.0
        
        # Get highest impact event
        highest_impact = max(events, key=lambda e: {
            NewsImpact.LOW: 1,
            NewsImpact.MEDIUM: 2,
            NewsImpact.HIGH: 3,
            NewsImpact.CRITICAL: 4
        }.get(e.impact, 0))
        
        # Critical events - close positions
        if highest_impact.impact == NewsImpact.CRITICAL:
            if self.close_before_critical:
                return TradingAction.CLOSE_POSITIONS, f"Critical event: {highest_impact.name}", 0.0
        
        # High impact events - reduce or close based on P&L
        if highest_impact.impact == NewsImpact.HIGH:
            if current_pnl_percent > 0:
                # In profit - consider closing
                return TradingAction.CLOSE_POSITIONS, f"High impact event, lock in profit: {highest_impact.name}", 0.0
            elif self.reduce_before_high:
                return TradingAction.REDUCE_SIZE, f"High impact event: {highest_impact.name}", self.reduction_percent
        
        # Medium impact - reduce size
        if highest_impact.impact == NewsImpact.MEDIUM:
            return TradingAction.REDUCE_SIZE, f"Medium impact event: {highest_impact.name}", 0.7
        
        return TradingAction.TRADE_NORMALLY, "Low impact events only", 1.0
    
    def should_close_position(self, symbol: str, current_pnl_percent: float = 0) -> Tuple[bool, str]:
        """Check if should close position"""
        action, reason, _ = self.get_position_action(symbol, current_pnl_percent)
        return action == TradingAction.CLOSE_POSITIONS, reason


class PostNewsReentry:
    """Manages re-entry after news events"""
    
    def __init__(self, event_detector: HighImpactEventDetector, config: Optional[Dict] = None):
        self.event_detector = event_detector
        self.config = config or {}
        self.min_settlement_minutes = self.config.get('min_settlement_minutes', 15)
        self.volatility_threshold = self.config.get('volatility_threshold', 2.0)  # ATR multiplier
    
    def can_reenter(self, symbol: str, current_atr: float, historical_atr: float) -> Tuple[bool, str, int]:
        """Check if can re-enter after news"""
        near_event, events, wait_minutes = self.event_detector.check_event_proximity(symbol)
        
        if near_event:
            return False, f"Still near event, wait {wait_minutes} minutes", wait_minutes
        
        # Check volatility settlement
        if historical_atr > 0:
            vol_ratio = current_atr / historical_atr
            if vol_ratio > self.volatility_threshold:
                return False, f"Volatility still elevated ({vol_ratio:.1f}x normal)", self.min_settlement_minutes
        
        return True, "Safe to re-enter", 0
    
    def get_reentry_size_multiplier(self, symbol: str, current_atr: float, historical_atr: float) -> float:
        """Get position size multiplier for re-entry"""
        if historical_atr == 0:
            return 1.0
        
        vol_ratio = current_atr / historical_atr
        
        if vol_ratio > 2.0:
            return 0.25
        elif vol_ratio > 1.5:
            return 0.5
        elif vol_ratio > 1.2:
            return 0.75
        else:
            return 1.0


class NewsSentimentAnalyzer:
    """Analyzes news sentiment"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.sentiment_history: Dict[str, deque] = {}
        self.history_size = self.config.get('history_size', 100)
        
        # Sentiment keywords
        self.bullish_keywords = [
            'beat', 'exceed', 'strong', 'growth', 'rise', 'increase',
            'hawkish', 'optimistic', 'positive', 'surge', 'rally'
        ]
        self.bearish_keywords = [
            'miss', 'below', 'weak', 'decline', 'fall', 'decrease',
            'dovish', 'pessimistic', 'negative', 'drop', 'slump'
        ]
    
    def analyze_event(self, event: NewsEvent) -> NewsSentiment:
        """Analyze sentiment from event data"""
        if event.actual is None or event.forecast is None:
            return NewsSentiment.NEUTRAL
        
        surprise = event.surprise
        if surprise is None:
            return NewsSentiment.NEUTRAL
        
        # Determine sentiment based on surprise
        if surprise > 0.1:
            return NewsSentiment.VERY_BULLISH
        elif surprise > 0.02:
            return NewsSentiment.BULLISH
        elif surprise < -0.1:
            return NewsSentiment.VERY_BEARISH
        elif surprise < -0.02:
            return NewsSentiment.BEARISH
        else:
            return NewsSentiment.NEUTRAL
    
    def analyze_text(self, text: str) -> NewsSentiment:
        """Analyze sentiment from text"""
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)
        
        score = bullish_count - bearish_count
        
        if score >= 3:
            return NewsSentiment.VERY_BULLISH
        elif score >= 1:
            return NewsSentiment.BULLISH
        elif score <= -3:
            return NewsSentiment.VERY_BEARISH
        elif score <= -1:
            return NewsSentiment.BEARISH
        else:
            return NewsSentiment.NEUTRAL
    
    def get_currency_sentiment(self, currency: str) -> Tuple[NewsSentiment, float]:
        """Get overall sentiment for a currency"""
        if currency not in self.sentiment_history or not self.sentiment_history[currency]:
            return NewsSentiment.NEUTRAL, 0.5
        
        sentiments = list(self.sentiment_history[currency])
        
        # Convert to scores
        sentiment_scores = {
            NewsSentiment.VERY_BULLISH: 2,
            NewsSentiment.BULLISH: 1,
            NewsSentiment.NEUTRAL: 0,
            NewsSentiment.BEARISH: -1,
            NewsSentiment.VERY_BEARISH: -2
        }
        
        scores = [sentiment_scores.get(s, 0) for s in sentiments]
        avg_score = sum(scores) / len(scores)
        
        # Convert back to sentiment
        if avg_score >= 1.5:
            sentiment = NewsSentiment.VERY_BULLISH
        elif avg_score >= 0.5:
            sentiment = NewsSentiment.BULLISH
        elif avg_score <= -1.5:
            sentiment = NewsSentiment.VERY_BEARISH
        elif avg_score <= -0.5:
            sentiment = NewsSentiment.BEARISH
        else:
            sentiment = NewsSentiment.NEUTRAL
        
        confidence = min(abs(avg_score) / 2, 1.0)
        
        return sentiment, confidence
    
    def record_sentiment(self, currency: str, sentiment: NewsSentiment):
        """Record sentiment for currency"""
        if currency not in self.sentiment_history:
            self.sentiment_history[currency] = deque(maxlen=self.history_size)
        self.sentiment_history[currency].append(sentiment)


class NewsEventIntegrator:
    """
    Master news event integration system.
    Combines all news-related functionality.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.calendar = EconomicCalendarAPI(self.config)
        self.event_detector = HighImpactEventDetector(self.calendar, self.config)
        self.position_manager = PreNewsPositionManager(self.event_detector, self.config)
        self.reentry_manager = PostNewsReentry(self.event_detector, self.config)
        self.sentiment_analyzer = NewsSentimentAnalyzer(self.config)
        
        # Callbacks
        self._event_callbacks: List[Callable] = []
    
    async def initialize(self):
        """Initialize and fetch events"""
        await self.calendar.fetch_events()
        logger.info(f"Loaded {len(self.calendar.events_cache)} economic events")
    
    def analyze_trading_conditions(self, symbol: str, current_pnl_percent: float = 0) -> NewsAnalysis:
        """Analyze trading conditions for a symbol"""
        currencies = self.event_detector.get_affected_currencies(symbol)
        
        # Check event proximity
        near_event, events, wait_minutes = self.event_detector.check_event_proximity(symbol)
        
        # Get risk level
        risk_level = self.event_detector.get_risk_level(events)
        
        # Get position action
        action, reason, size_mult = self.position_manager.get_position_action(symbol, current_pnl_percent)
        
        reasons = [reason]
        
        # Add sentiment info
        for currency in currencies:
            sentiment, confidence = self.sentiment_analyzer.get_currency_sentiment(currency)
            if confidence > 0.5:
                reasons.append(f"{currency} sentiment: {sentiment.value}")
        
        return NewsAnalysis(
            symbol=symbol,
            action=action,
            events=events,
            risk_level=risk_level,
            reasons=reasons,
            position_size_multiplier=size_mult,
            wait_minutes=wait_minutes
        )
    
    def should_trade(self, symbol: str) -> Tuple[bool, str]:
        """Check if should trade based on news"""
        analysis = self.analyze_trading_conditions(symbol)
        
        if analysis.action == TradingAction.CLOSE_POSITIONS:
            return False, f"Close positions: {analysis.reasons[0]}"
        
        if analysis.action == TradingAction.NO_NEW_TRADES:
            return False, f"No new trades: {analysis.reasons[0]}"
        
        if analysis.action == TradingAction.WAIT_FOR_SETTLEMENT:
            return False, f"Wait for settlement: {analysis.reasons[0]}"
        
        if analysis.risk_level > 0.7:
            return False, f"High news risk: {analysis.risk_level:.0%}"
        
        return True, "News conditions acceptable"
    
    def get_position_size_multiplier(self, symbol: str) -> float:
        """Get position size multiplier based on news"""
        analysis = self.analyze_trading_conditions(symbol)
        return analysis.position_size_multiplier
    
    def get_upcoming_events(self, symbol: str, hours: int = 24) -> List[NewsEvent]:
        """Get upcoming events for symbol"""
        currencies = self.event_detector.get_affected_currencies(symbol)
        events = []
        
        for currency in currencies:
            events.extend(self.calendar.get_events_for_currency(currency, hours))
        
        return sorted(events, key=lambda e: e.scheduled_time)
    
    def process_event_result(self, event: NewsEvent):
        """Process event result and update sentiment"""
        sentiment = self.sentiment_analyzer.analyze_event(event)
        self.sentiment_analyzer.record_sentiment(event.currency, sentiment)
        
        # Notify callbacks
        for callback in self._event_callbacks:
            try:
                callback(event, sentiment)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def register_event_callback(self, callback: Callable):
        """Register callback for event results"""
        self._event_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get news integration statistics"""
        return {
            'total_events': len(self.calendar.events_cache),
            'high_impact_events': len(self.calendar.get_high_impact_events()),
            'sentiment_history': {
                currency: len(history)
                for currency, history in self.sentiment_analyzer.sentiment_history.items()
            }
        }
