"""
Session Manager - Market Hours, Holidays, and Session-Specific Trading
Comprehensive market session awareness for global trading
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, date
from enum import Enum
import pytz
from zoneinfo import ZoneInfo
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


class SessionType(Enum):
    """Trading session types"""
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    OVERNIGHT = "overnight"
    CLOSED = "closed"
    HOLIDAY = "holiday"


class MarketType(Enum):
    """Market types"""
    EQUITY = "equity"
    FOREX = "forex"
    CRYPTO = "crypto"
    FUTURES = "futures"
    OPTIONS = "options"
    COMMODITIES = "commodities"


@dataclass
class MarketHoliday:
    """Market holiday definition"""
    date: date
    name: str
    market: str
    early_close: bool = False
    close_time: Optional[time] = None
    

@dataclass
class MarketSession:
    """Market session definition"""
    session_type: SessionType
    start_time: time
    end_time: time
    timezone: str
    liquidity_factor: float = 1.0  # Relative liquidity
    volatility_factor: float = 1.0  # Expected volatility
    spread_factor: float = 1.0  # Expected spread widening


@dataclass
class SessionRiskProfile:
    """Risk parameters for different sessions"""
    max_position_size_pct: float = 1.0  # Multiplier on normal size
    max_leverage: float = 1.0
    stop_loss_buffer: float = 1.0  # Wider stops in volatile sessions
    take_profit_buffer: float = 1.0
    allowed_order_types: List[str] = field(default_factory=lambda: ["market", "limit"])
    min_liquidity_score: float = 0.5


class TradingCalendar:
    """
    Trading calendar with holiday and session management
    """
    
    # US Market Holidays (2024-2025)
    US_HOLIDAYS = {
        # 2024
        date(2024, 1, 1): ("New Year's Day", False),
        date(2024, 1, 15): ("MLK Day", False),
        date(2024, 2, 19): ("Presidents Day", False),
        date(2024, 3, 29): ("Good Friday", False),
        date(2024, 5, 27): ("Memorial Day", False),
        date(2024, 6, 19): ("Juneteenth", False),
        date(2024, 7, 4): ("Independence Day", False),
        date(2024, 9, 2): ("Labor Day", False),
        date(2024, 11, 28): ("Thanksgiving", False),
        date(2024, 11, 29): ("Day After Thanksgiving", True),  # Early close
        date(2024, 12, 24): ("Christmas Eve", True),  # Early close
        date(2024, 12, 25): ("Christmas", False),
        # 2025
        date(2025, 1, 1): ("New Year's Day", False),
        date(2025, 1, 20): ("MLK Day", False),
        date(2025, 2, 17): ("Presidents Day", False),
        date(2025, 4, 18): ("Good Friday", False),
        date(2025, 5, 26): ("Memorial Day", False),
        date(2025, 6, 19): ("Juneteenth", False),
        date(2025, 7, 4): ("Independence Day", False),
        date(2025, 9, 1): ("Labor Day", False),
        date(2025, 11, 27): ("Thanksgiving", False),
        date(2025, 11, 28): ("Day After Thanksgiving", True),
        date(2025, 12, 24): ("Christmas Eve", True),
        date(2025, 12, 25): ("Christmas", False),
    }
    
    # European Market Holidays
    EU_HOLIDAYS = {
        date(2024, 1, 1): ("New Year's Day", False),
        date(2024, 3, 29): ("Good Friday", False),
        date(2024, 4, 1): ("Easter Monday", False),
        date(2024, 5, 1): ("Labour Day", False),
        date(2024, 12, 25): ("Christmas", False),
        date(2024, 12, 26): ("Boxing Day", False),
        date(2025, 1, 1): ("New Year's Day", False),
        date(2025, 4, 18): ("Good Friday", False),
        date(2025, 4, 21): ("Easter Monday", False),
        date(2025, 5, 1): ("Labour Day", False),
        date(2025, 12, 25): ("Christmas", False),
        date(2025, 12, 26): ("Boxing Day", False),
    }
    
    # Asian Market Holidays (simplified)
    ASIA_HOLIDAYS = {
        date(2024, 1, 1): ("New Year's Day", False),
        date(2024, 2, 10): ("Chinese New Year", False),
        date(2024, 2, 11): ("Chinese New Year", False),
        date(2024, 2, 12): ("Chinese New Year", False),
        date(2025, 1, 1): ("New Year's Day", False),
        date(2025, 1, 29): ("Chinese New Year", False),
        date(2025, 1, 30): ("Chinese New Year", False),
    }
    
    def __init__(self):
        self.holidays: Dict[str, Dict[date, MarketHoliday]] = {
            'US': {},
            'EU': {},
            'ASIA': {}
        }
        self._load_holidays()
        
    def _load_holidays(self):
        """Load all holidays"""
        for d, (name, early) in self.US_HOLIDAYS.items():
            self.holidays['US'][d] = MarketHoliday(
                date=d, name=name, market='US', 
                early_close=early,
                close_time=time(13, 0) if early else None
            )
        for d, (name, early) in self.EU_HOLIDAYS.items():
            self.holidays['EU'][d] = MarketHoliday(
                date=d, name=name, market='EU', early_close=early
            )
        for d, (name, early) in self.ASIA_HOLIDAYS.items():
            self.holidays['ASIA'][d] = MarketHoliday(
                date=d, name=name, market='ASIA', early_close=early
            )
            
    def is_holiday(self, check_date: date, market: str = 'US') -> bool:
        """Check if date is a holiday"""
        return check_date in self.holidays.get(market, {})
    
    def get_holiday(self, check_date: date, market: str = 'US') -> Optional[MarketHoliday]:
        """Get holiday info if exists"""
        return self.holidays.get(market, {}).get(check_date)
    
    def is_weekend(self, check_date: date) -> bool:
        """Check if date is weekend"""
        return check_date.weekday() >= 5
    
    def is_trading_day(self, check_date: date, market: str = 'US') -> bool:
        """Check if it's a trading day"""
        if self.is_weekend(check_date):
            return False
        if self.is_holiday(check_date, market):
            holiday = self.get_holiday(check_date, market)
            return holiday.early_close if holiday else False
        return True
    
    def next_trading_day(self, from_date: date, market: str = 'US') -> date:
        """Get next trading day"""
        next_day = from_date + timedelta(days=1)
        while not self.is_trading_day(next_day, market):
            next_day += timedelta(days=1)
        return next_day
    
    def trading_days_between(self, start: date, end: date, market: str = 'US') -> int:
        """Count trading days between dates"""
        count = 0
        current = start
        while current <= end:
            if self.is_trading_day(current, market):
                count += 1
            current += timedelta(days=1)
        return count


class SessionManager:
    """
    Comprehensive session management for global markets
    Handles market hours, sessions, and session-specific risk
    """
    
    # Market session definitions
    MARKET_SESSIONS = {
        'NYSE': {
            'timezone': 'America/New_York',
            'sessions': {
                SessionType.PRE_MARKET: MarketSession(
                    SessionType.PRE_MARKET, time(4, 0), time(9, 30),
                    'America/New_York', 0.3, 1.2, 1.5
                ),
                SessionType.REGULAR: MarketSession(
                    SessionType.REGULAR, time(9, 30), time(16, 0),
                    'America/New_York', 1.0, 1.0, 1.0
                ),
                SessionType.AFTER_HOURS: MarketSession(
                    SessionType.AFTER_HOURS, time(16, 0), time(20, 0),
                    'America/New_York', 0.2, 1.3, 2.0
                ),
            }
        },
        'NASDAQ': {
            'timezone': 'America/New_York',
            'sessions': {
                SessionType.PRE_MARKET: MarketSession(
                    SessionType.PRE_MARKET, time(4, 0), time(9, 30),
                    'America/New_York', 0.3, 1.2, 1.5
                ),
                SessionType.REGULAR: MarketSession(
                    SessionType.REGULAR, time(9, 30), time(16, 0),
                    'America/New_York', 1.0, 1.0, 1.0
                ),
                SessionType.AFTER_HOURS: MarketSession(
                    SessionType.AFTER_HOURS, time(16, 0), time(20, 0),
                    'America/New_York', 0.2, 1.3, 2.0
                ),
            }
        },
        'LSE': {
            'timezone': 'Europe/London',
            'sessions': {
                SessionType.REGULAR: MarketSession(
                    SessionType.REGULAR, time(8, 0), time(16, 30),
                    'Europe/London', 1.0, 1.0, 1.0
                ),
            }
        },
        'TSE': {
            'timezone': 'Asia/Tokyo',
            'sessions': {
                SessionType.REGULAR: MarketSession(
                    SessionType.REGULAR, time(9, 0), time(15, 0),
                    'Asia/Tokyo', 1.0, 1.0, 1.0
                ),
            }
        },
        'FOREX': {
            'timezone': 'UTC',
            'sessions': {
                SessionType.REGULAR: MarketSession(
                    SessionType.REGULAR, time(0, 0), time(23, 59),
                    'UTC', 1.0, 1.0, 1.0
                ),
            },
            '24_hour': True
        },
        'CRYPTO': {
            'timezone': 'UTC',
            'sessions': {
                SessionType.REGULAR: MarketSession(
                    SessionType.REGULAR, time(0, 0), time(23, 59),
                    'UTC', 1.0, 1.0, 1.0
                ),
            },
            '24_hour': True
        },
        'CME': {
            'timezone': 'America/Chicago',
            'sessions': {
                SessionType.REGULAR: MarketSession(
                    SessionType.REGULAR, time(8, 30), time(15, 15),
                    'America/Chicago', 1.0, 1.0, 1.0
                ),
                SessionType.OVERNIGHT: MarketSession(
                    SessionType.OVERNIGHT, time(17, 0), time(8, 30),
                    'America/Chicago', 0.5, 1.5, 1.8
                ),
            }
        },
    }
    
    # Session-specific risk profiles
    SESSION_RISK_PROFILES = {
        SessionType.PRE_MARKET: SessionRiskProfile(
            max_position_size_pct=0.5,
            max_leverage=0.5,
            stop_loss_buffer=1.5,
            take_profit_buffer=1.2,
            allowed_order_types=["limit"],
            min_liquidity_score=0.7
        ),
        SessionType.REGULAR: SessionRiskProfile(
            max_position_size_pct=1.0,
            max_leverage=1.0,
            stop_loss_buffer=1.0,
            take_profit_buffer=1.0,
            allowed_order_types=["market", "limit", "stop", "stop_limit"],
            min_liquidity_score=0.3
        ),
        SessionType.AFTER_HOURS: SessionRiskProfile(
            max_position_size_pct=0.3,
            max_leverage=0.3,
            stop_loss_buffer=2.0,
            take_profit_buffer=1.5,
            allowed_order_types=["limit"],
            min_liquidity_score=0.8
        ),
        SessionType.OVERNIGHT: SessionRiskProfile(
            max_position_size_pct=0.4,
            max_leverage=0.4,
            stop_loss_buffer=1.8,
            take_profit_buffer=1.3,
            allowed_order_types=["limit"],
            min_liquidity_score=0.6
        ),
        SessionType.CLOSED: SessionRiskProfile(
            max_position_size_pct=0.0,
            max_leverage=0.0,
            stop_loss_buffer=1.0,
            take_profit_buffer=1.0,
            allowed_order_types=[],
            min_liquidity_score=1.0
        ),
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.calendar = TradingCalendar()
        self.respect_holidays = self.config.get('respect_holidays', True)
        self.session_specific_risk = self.config.get('session_specific_risk', True)
        
        # Active sessions tracking
        self._session_cache: Dict[str, Tuple[SessionType, datetime]] = {}
        self._cache_ttl = 60  # seconds
        
        logger.info("Session manager initialized")
        
    def get_current_time(self, timezone: str = 'UTC') -> datetime:
        """Get current time in specified timezone"""
        tz = pytz.timezone(timezone)
        return datetime.now(tz)
    
    def get_market_timezone(self, market: str) -> str:
        """Get timezone for market"""
        market_info = self.MARKET_SESSIONS.get(market, {})
        return market_info.get('timezone', 'UTC')
    
    def get_current_session(self, market: str = 'NYSE') -> Tuple[SessionType, Optional[MarketSession]]:
        """
        Get current trading session for a market
        
        Returns:
            Tuple of (SessionType, MarketSession or None)
        """
        # Check cache
        cache_key = market
        if cache_key in self._session_cache:
            cached_type, cached_time = self._session_cache[cache_key]
            if (datetime.now() - cached_time.replace(tzinfo=None)).seconds < self._cache_ttl:
                sessions = self.MARKET_SESSIONS.get(market, {}).get('sessions', {})
                return cached_type, sessions.get(cached_type)
        
        market_info = self.MARKET_SESSIONS.get(market)
        if not market_info:
            return SessionType.CLOSED, None
            
        tz = pytz.timezone(market_info['timezone'])
        now = datetime.now(tz)
        current_time = now.time()
        current_date = now.date()
        
        # Check if holiday
        market_region = 'US' if market in ['NYSE', 'NASDAQ', 'CME'] else 'EU' if market == 'LSE' else 'ASIA'
        if self.respect_holidays and self.calendar.is_holiday(current_date, market_region):
            holiday = self.calendar.get_holiday(current_date, market_region)
            if holiday and not holiday.early_close:
                return SessionType.HOLIDAY, None
            elif holiday and holiday.early_close and holiday.close_time:
                if current_time > holiday.close_time:
                    return SessionType.HOLIDAY, None
        
        # Check if weekend (except 24-hour markets)
        if not market_info.get('24_hour', False) and self.calendar.is_weekend(current_date):
            return SessionType.CLOSED, None
        
        # Find current session
        sessions = market_info.get('sessions', {})
        for session_type, session in sessions.items():
            if self._time_in_session(current_time, session):
                self._session_cache[cache_key] = (session_type, datetime.now(tz))
                return session_type, session
                
        return SessionType.CLOSED, None
    
    def _time_in_session(self, current_time: time, session: MarketSession) -> bool:
        """Check if time is within session"""
        if session.start_time <= session.end_time:
            return session.start_time <= current_time <= session.end_time
        else:
            # Overnight session (crosses midnight)
            return current_time >= session.start_time or current_time <= session.end_time
    
    def is_market_open(self, market: str = 'NYSE') -> bool:
        """Check if market is currently open"""
        session_type, _ = self.get_current_session(market)
        return session_type not in [SessionType.CLOSED, SessionType.HOLIDAY]
    
    def is_regular_hours(self, market: str = 'NYSE') -> bool:
        """Check if in regular trading hours"""
        session_type, _ = self.get_current_session(market)
        return session_type == SessionType.REGULAR
    
    def get_session_risk_profile(self, market: str = 'NYSE') -> SessionRiskProfile:
        """Get risk profile for current session"""
        session_type, _ = self.get_current_session(market)
        return self.SESSION_RISK_PROFILES.get(session_type, self.SESSION_RISK_PROFILES[SessionType.CLOSED])
    
    def get_time_until_session(self, target_session: SessionType, market: str = 'NYSE') -> Optional[timedelta]:
        """Get time until a specific session starts"""
        market_info = self.MARKET_SESSIONS.get(market)
        if not market_info:
            return None
            
        sessions = market_info.get('sessions', {})
        target = sessions.get(target_session)
        if not target:
            return None
            
        tz = pytz.timezone(market_info['timezone'])
        now = datetime.now(tz)
        
        # Create target datetime
        target_dt = datetime.combine(now.date(), target.start_time)
        target_dt = tz.localize(target_dt)
        
        if target_dt <= now:
            # Session already started today, get tomorrow's
            target_dt += timedelta(days=1)
            
        return target_dt - now
    
    def get_time_until_close(self, market: str = 'NYSE') -> Optional[timedelta]:
        """Get time until current session closes"""
        session_type, session = self.get_current_session(market)
        if not session or session_type in [SessionType.CLOSED, SessionType.HOLIDAY]:
            return None
            
        market_info = self.MARKET_SESSIONS.get(market)
        tz = pytz.timezone(market_info['timezone'])
        now = datetime.now(tz)
        
        close_dt = datetime.combine(now.date(), session.end_time)
        close_dt = tz.localize(close_dt)
        
        if close_dt <= now:
            close_dt += timedelta(days=1)
            
        return close_dt - now
    
    def should_reduce_exposure(self, market: str = 'NYSE', 
                               minutes_before_close: int = 30) -> bool:
        """Check if should reduce exposure before close"""
        time_until_close = self.get_time_until_close(market)
        if time_until_close is None:
            return False
        return time_until_close.total_seconds() / 60 <= minutes_before_close
    
    def get_adjusted_position_size(self, base_size: float, market: str = 'NYSE') -> float:
        """Get position size adjusted for current session"""
        if not self.session_specific_risk:
            return base_size
            
        risk_profile = self.get_session_risk_profile(market)
        return base_size * risk_profile.max_position_size_pct
    
    def get_adjusted_stop_loss(self, base_stop: float, market: str = 'NYSE') -> float:
        """Get stop loss adjusted for current session volatility"""
        if not self.session_specific_risk:
            return base_stop
            
        risk_profile = self.get_session_risk_profile(market)
        return base_stop * risk_profile.stop_loss_buffer
    
    def is_order_type_allowed(self, order_type: str, market: str = 'NYSE') -> bool:
        """Check if order type is allowed in current session"""
        risk_profile = self.get_session_risk_profile(market)
        return order_type.lower() in risk_profile.allowed_order_types
    
    def get_next_market_open(self, market: str = 'NYSE') -> Optional[datetime]:
        """Get next market open time"""
        market_info = self.MARKET_SESSIONS.get(market)
        if not market_info:
            return None
            
        tz = pytz.timezone(market_info['timezone'])
        now = datetime.now(tz)
        
        # Find regular session
        sessions = market_info.get('sessions', {})
        regular = sessions.get(SessionType.REGULAR)
        if not regular:
            return None
            
        # Start from today
        check_date = now.date()
        market_region = 'US' if market in ['NYSE', 'NASDAQ', 'CME'] else 'EU' if market == 'LSE' else 'ASIA'
        
        for _ in range(10):  # Check up to 10 days ahead
            if self.calendar.is_trading_day(check_date, market_region):
                open_dt = datetime.combine(check_date, regular.start_time)
                open_dt = tz.localize(open_dt)
                if open_dt > now:
                    return open_dt
            check_date += timedelta(days=1)
            
        return None
    
    def get_session_info(self, market: str = 'NYSE') -> Dict[str, Any]:
        """Get comprehensive session information"""
        session_type, session = self.get_current_session(market)
        risk_profile = self.get_session_risk_profile(market)
        
        return {
            'market': market,
            'session_type': session_type.value,
            'is_open': self.is_market_open(market),
            'is_regular_hours': self.is_regular_hours(market),
            'timezone': self.get_market_timezone(market),
            'current_time': self.get_current_time(self.get_market_timezone(market)).isoformat(),
            'session': {
                'start': session.start_time.isoformat() if session else None,
                'end': session.end_time.isoformat() if session else None,
                'liquidity_factor': session.liquidity_factor if session else 0,
                'volatility_factor': session.volatility_factor if session else 0,
                'spread_factor': session.spread_factor if session else 0,
            } if session else None,
            'risk_profile': {
                'max_position_size_pct': risk_profile.max_position_size_pct,
                'max_leverage': risk_profile.max_leverage,
                'stop_loss_buffer': risk_profile.stop_loss_buffer,
                'allowed_order_types': risk_profile.allowed_order_types,
            },
            'time_until_close': str(self.get_time_until_close(market)),
            'should_reduce_exposure': self.should_reduce_exposure(market),
        }
    
    async def monitor_sessions(self, markets: List[str], callback=None):
        """
        Monitor multiple markets for session changes
        
        Args:
            markets: List of market codes
            callback: Async function to call on session change
        """
        previous_sessions: Dict[str, SessionType] = {}
        
        while True:
            for market in markets:
                session_type, _ = self.get_current_session(market)
                prev_session = previous_sessions.get(market)
                
                if prev_session and prev_session != session_type:
                    logger.info(f"Session change for {market}: {prev_session.value} -> {session_type.value}")
                    if callback:
                        await callback(market, prev_session, session_type)
                        
                previous_sessions[market] = session_type
                
            await asyncio.sleep(60)  # Check every minute


# Convenience functions
def get_session_manager(config: Optional[Dict] = None) -> SessionManager:
    """Get or create session manager singleton"""
    if not hasattr(get_session_manager, '_instance'):
        get_session_manager._instance = SessionManager(config)
    return get_session_manager._instance


def is_market_open(market: str = 'NYSE') -> bool:
    """Quick check if market is open"""
    return get_session_manager().is_market_open(market)


def get_current_session(market: str = 'NYSE') -> SessionType:
    """Quick get current session type"""
    session_type, _ = get_session_manager().get_current_session(market)
    return session_type
