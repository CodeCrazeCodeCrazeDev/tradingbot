"""
Session Manager - Market session awareness, holiday calendars, and trading hours.

Provides session-specific risk adjustment, market hours tracking, and
holiday calendar management for global markets.
"""

import logging
from datetime import datetime, time, timedelta, timezone
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SessionType(Enum):
    """Market trading sessions."""
    ASIAN = "asian"
    EUROPEAN = "european"
    US = "us"
    PACIFIC = "pacific"
    OVERLAP_ASIAN_EUROPEAN = "overlap_asian_european"
    OVERLAP_EUROPEAN_US = "overlap_european_us"
    OFF_HOURS = "off_hours"


class MarketStatus(Enum):
    """Current market status."""
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"


@dataclass
class MarketHours:
    """Market trading hours definition."""
    market_name: str
    open_time: time
    close_time: time
    timezone_offset: int  # UTC offset in hours
    pre_market_start: Optional[time] = None
    after_hours_end: Optional[time] = None
    half_day_close: Optional[time] = None


@dataclass
class SessionInfo:
    """Information about the current trading session."""
    session_type: SessionType
    market_status: MarketStatus
    active_markets: List[str]
    time_to_close: Optional[timedelta] = None
    time_to_open: Optional[timedelta] = None
    is_high_liquidity: bool = False
    is_overlap: bool = False
    volatility_factor: float = 1.0
    risk_adjustment: float = 1.0
    notes: List[str] = field(default_factory=list)


@dataclass
class Holiday:
    """Market holiday definition."""
    date: datetime
    market: str
    name: str
    is_half_day: bool = False


class MarketCalendar:
    """
    Holiday and trading day calendar for global markets.
    
    Tracks holidays for major markets and provides trading day
    calculations for scheduling and risk management.
    """

    # Major market holidays (US-focused, extensible)
    US_HOLIDAYS_2026 = [
        Holiday(datetime(2026, 1, 1), "US", "New Year's Day"),
        Holiday(datetime(2026, 1, 19), "US", "Martin Luther King Jr. Day"),
        Holiday(datetime(2026, 2, 16), "US", "Presidents' Day"),
        Holiday(datetime(2026, 4, 3), "US", "Good Friday"),
        Holiday(datetime(2026, 5, 25), "US", "Memorial Day"),
        Holiday(datetime(2026, 7, 3), "US", "Independence Day (Observed)"),
        Holiday(datetime(2026, 9, 7), "US", "Labor Day"),
        Holiday(datetime(2026, 11, 26), "US", "Thanksgiving Day"),
        Holiday(datetime(2026, 11, 27), "US", "Day After Thanksgiving", is_half_day=True),
        Holiday(datetime(2026, 12, 25), "US", "Christmas Day"),
    ]

    UK_HOLIDAYS_2026 = [
        Holiday(datetime(2026, 1, 1), "UK", "New Year's Day"),
        Holiday(datetime(2026, 4, 3), "UK", "Good Friday"),
        Holiday(datetime(2026, 4, 6), "UK", "Easter Monday"),
        Holiday(datetime(2026, 5, 4), "UK", "Early May Bank Holiday"),
        Holiday(datetime(2026, 5, 25), "UK", "Spring Bank Holiday"),
        Holiday(datetime(2026, 8, 31), "UK", "Summer Bank Holiday"),
        Holiday(datetime(2026, 12, 25), "UK", "Christmas Day"),
        Holiday(datetime(2026, 12, 28), "UK", "Boxing Day (Observed)"),
    ]

    JP_HOLIDAYS_2026 = [
        Holiday(datetime(2026, 1, 1), "JP", "New Year's Day"),
        Holiday(datetime(2026, 1, 12), "JP", "Coming of Age Day"),
        Holiday(datetime(2026, 2, 11), "JP", "National Foundation Day"),
        Holiday(datetime(2026, 3, 20), "JP", "Vernal Equinox Day"),
        Holiday(datetime(2026, 4, 29), "JP", "Showa Day"),
        Holiday(datetime(2026, 5, 3), "JP", "Constitution Memorial Day"),
        Holiday(datetime(2026, 5, 4), "JP", "Greenery Day"),
        Holiday(datetime(2026, 5, 5), "JP", "Children's Day"),
        Holiday(datetime(2026, 7, 20), "JP", "Marine Day"),
        Holiday(datetime(2026, 9, 21), "JP", "Respect for the Aged Day"),
        Holiday(datetime(2026, 9, 23), "JP", "Autumnal Equinox Day"),
        Holiday(datetime(2026, 11, 3), "JP", "Culture Day"),
        Holiday(datetime(2026, 11, 23), "JP", "Labor Thanksgiving Day"),
    ]

    def __init__(self):
        self._holidays: Dict[str, List[Holiday]] = {
            "US": self.US_HOLIDAYS_2026,
            "UK": self.UK_HOLIDAYS_2026,
            "JP": self.JP_HOLIDAYS_2026,
        }
        self._custom_holidays: List[Holiday] = []
        logger.info("MarketCalendar initialized with %d markets", len(self._holidays))

    def is_holiday(self, date: datetime, market: str = "US") -> bool:
        """Check if a given date is a holiday for the specified market."""
        holidays = self._holidays.get(market, []) + self._custom_holidays
        date_only = date.date() if hasattr(date, 'date') else date
        return any(
            h.date.date() == date_only and h.market == market
            for h in holidays
        )

    def is_half_day(self, date: datetime, market: str = "US") -> bool:
        """Check if a given date is a half trading day."""
        holidays = self._holidays.get(market, []) + self._custom_holidays
        date_only = date.date() if hasattr(date, 'date') else date
        return any(
            h.date.date() == date_only and h.market == market and h.is_half_day
            for h in holidays
        )

    def is_trading_day(self, date: datetime, market: str = "US") -> bool:
        """Check if a given date is a trading day (not weekend, not holiday)."""
        if date.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        return not self.is_holiday(date, market)

    def next_trading_day(self, date: datetime, market: str = "US") -> datetime:
        """Get the next trading day after the given date."""
        next_day = date + timedelta(days=1)
        while not self.is_trading_day(next_day, market):
            next_day += timedelta(days=1)
        return next_day

    def trading_days_between(
        self, start: datetime, end: datetime, market: str = "US"
    ) -> int:
        """Count trading days between two dates."""
        count = 0
        current = start
        while current <= end:
            if self.is_trading_day(current, market):
                count += 1
            current += timedelta(days=1)
        return count

    def get_holiday_name(self, date: datetime, market: str = "US") -> Optional[str]:
        """Get the holiday name for a given date, if any."""
        holidays = self._holidays.get(market, []) + self._custom_holidays
        date_only = date.date() if hasattr(date, 'date') else date
        for h in holidays:
            if h.date.date() == date_only and h.market == market:
                return h.name
        return None

    def add_holiday(self, holiday: Holiday) -> None:
        """Add a custom holiday."""
        self._custom_holidays.append(holiday)
        logger.info("Added custom holiday: %s on %s for %s",
                     holiday.name, holiday.date, holiday.market)

    def get_upcoming_holidays(
        self, market: str = "US", days_ahead: int = 30
    ) -> List[Holiday]:
        """Get upcoming holidays within the specified number of days."""
        now = datetime.now()
        cutoff = now + timedelta(days=days_ahead)
        holidays = self._holidays.get(market, []) + self._custom_holidays
        return sorted(
            [h for h in holidays if now.date() <= h.date.date() <= cutoff.date()
             and h.market == market],
            key=lambda h: h.date,
        )


class SessionManager:
    """
    Market session tracking and awareness.
    
    Tracks active trading sessions globally, provides session-specific
    risk adjustments, and manages session transitions.
    """

    # Session definitions (UTC times)
    SESSIONS = {
        SessionType.PACIFIC: {
            "start": time(21, 0),  # 9 PM UTC (Sydney open)
            "end": time(6, 0),     # 6 AM UTC (Sydney close)
            "markets": ["ASX"],
            "volatility_factor": 0.7,
        },
        SessionType.ASIAN: {
            "start": time(0, 0),   # Midnight UTC (Tokyo open)
            "end": time(9, 0),     # 9 AM UTC (Tokyo close)
            "markets": ["TSE", "HKEX", "SSE", "SGX"],
            "volatility_factor": 0.8,
        },
        SessionType.EUROPEAN: {
            "start": time(7, 0),   # 7 AM UTC (London open)
            "end": time(16, 0),    # 4 PM UTC (London close)
            "markets": ["LSE", "XETRA", "Euronext", "SIX"],
            "volatility_factor": 1.0,
        },
        SessionType.US: {
            "start": time(13, 30),  # 1:30 PM UTC (NYSE open)
            "end": time(20, 0),     # 8 PM UTC (NYSE close)
            "markets": ["NYSE", "NASDAQ", "CME", "CBOE"],
            "volatility_factor": 1.2,
        },
    }

    # Overlap sessions (highest liquidity)
    OVERLAPS = {
        SessionType.OVERLAP_ASIAN_EUROPEAN: {
            "start": time(7, 0),
            "end": time(9, 0),
            "volatility_factor": 1.1,
        },
        SessionType.OVERLAP_EUROPEAN_US: {
            "start": time(13, 30),
            "end": time(16, 0),
            "volatility_factor": 1.4,
        },
    }

    # Market hours definitions
    MARKET_HOURS = {
        "NYSE": MarketHours("NYSE", time(9, 30), time(16, 0), -5,
                            pre_market_start=time(4, 0), after_hours_end=time(20, 0)),
        "NASDAQ": MarketHours("NASDAQ", time(9, 30), time(16, 0), -5,
                              pre_market_start=time(4, 0), after_hours_end=time(20, 0)),
        "LSE": MarketHours("LSE", time(8, 0), time(16, 30), 0),
        "TSE": MarketHours("TSE", time(9, 0), time(15, 0), 9),
        "HKEX": MarketHours("HKEX", time(9, 30), time(16, 0), 8),
        "ASX": MarketHours("ASX", time(10, 0), time(16, 0), 11),
        "XETRA": MarketHours("XETRA", time(9, 0), time(17, 30), 1),
        "FOREX": MarketHours("FOREX", time(0, 0), time(23, 59), 0),  # 24h Sun-Fri
        "CRYPTO": MarketHours("CRYPTO", time(0, 0), time(23, 59), 0),  # 24/7
    }

    def __init__(self, calendar: Optional[MarketCalendar] = None):
        self._calendar = calendar or MarketCalendar()
        self._session_history: List[Dict] = []
        self._risk_overrides: Dict[SessionType, float] = {}
        logger.info("SessionManager initialized")

    @property
    def calendar(self) -> MarketCalendar:
        """Access the market calendar."""
        return self._calendar

    def get_current_session(self, utc_now: Optional[datetime] = None) -> SessionInfo:
        """
        Determine the current trading session based on UTC time.
        
        Returns comprehensive session information including active markets,
        liquidity assessment, and risk adjustments.
        """
        if utc_now is None:
            utc_now = datetime.now(timezone.utc)

        current_time = utc_now.time()
        active_sessions: List[SessionType] = []
        active_markets: List[str] = []
        max_volatility = 0.5  # base off-hours volatility

        # Check main sessions
        for session_type, config in self.SESSIONS.items():
            start = config["start"]
            end = config["end"]

            if self._time_in_range(current_time, start, end):
                active_sessions.append(session_type)
                active_markets.extend(config["markets"])
                max_volatility = max(max_volatility, config["volatility_factor"])

        # Check overlaps
        is_overlap = False
        for overlap_type, config in self.OVERLAPS.items():
            if self._time_in_range(current_time, config["start"], config["end"]):
                active_sessions.append(overlap_type)
                is_overlap = True
                max_volatility = max(max_volatility, config["volatility_factor"])

        # Determine primary session
        if is_overlap and SessionType.OVERLAP_EUROPEAN_US in active_sessions:
            primary_session = SessionType.OVERLAP_EUROPEAN_US
        elif is_overlap and SessionType.OVERLAP_ASIAN_EUROPEAN in active_sessions:
            primary_session = SessionType.OVERLAP_ASIAN_EUROPEAN
        elif active_sessions:
            primary_session = active_sessions[0]
        else:
            primary_session = SessionType.OFF_HOURS

        # Check weekend / holiday
        is_weekend = utc_now.weekday() >= 5
        market_status = MarketStatus.OPEN

        if is_weekend:
            market_status = MarketStatus.WEEKEND
        elif self._calendar.is_holiday(utc_now, "US"):
            market_status = MarketStatus.HOLIDAY
        elif primary_session == SessionType.OFF_HOURS:
            market_status = MarketStatus.CLOSED

        # Calculate risk adjustment
        risk_adj = self._calculate_risk_adjustment(
            primary_session, market_status, is_overlap, utc_now
        )

        # Apply overrides
        if primary_session in self._risk_overrides:
            risk_adj = self._risk_overrides[primary_session]

        notes = []
        if is_weekend:
            notes.append("Weekend - markets closed")
        if self._calendar.is_holiday(utc_now, "US"):
            holiday_name = self._calendar.get_holiday_name(utc_now, "US")
            notes.append(f"US Holiday: {holiday_name}")
        if is_overlap:
            notes.append("Session overlap - high liquidity period")

        # Check for upcoming holidays
        upcoming = self._calendar.get_upcoming_holidays("US", days_ahead=3)
        for h in upcoming:
            notes.append(f"Upcoming: {h.name} on {h.date.strftime('%Y-%m-%d')}")

        session_info = SessionInfo(
            session_type=primary_session,
            market_status=market_status,
            active_markets=list(set(active_markets)),
            is_high_liquidity=is_overlap or primary_session in (
                SessionType.EUROPEAN, SessionType.US
            ),
            is_overlap=is_overlap,
            volatility_factor=max_volatility,
            risk_adjustment=risk_adj,
            notes=notes,
        )

        # Track session history
        self._session_history.append({
            "timestamp": utc_now.isoformat(),
            "session": primary_session.value,
            "status": market_status.value,
        })
        if len(self._session_history) > 1000:
            self._session_history = self._session_history[-500:]

        return session_info

    def get_market_status(
        self, market: str, utc_now: Optional[datetime] = None
    ) -> MarketStatus:
        """Get the status of a specific market."""
        if utc_now is None:
            utc_now = datetime.now(timezone.utc)

        if market == "CRYPTO":
            return MarketStatus.OPEN  # 24/7

        if utc_now.weekday() >= 5:
            return MarketStatus.WEEKEND

        hours = self.MARKET_HOURS.get(market)
        if not hours:
            return MarketStatus.CLOSED

        # Convert to market local time
        local_time = (utc_now + timedelta(hours=hours.timezone_offset)).time()

        if hours.pre_market_start and self._time_in_range(
            local_time, hours.pre_market_start, hours.open_time
        ):
            return MarketStatus.PRE_MARKET

        if self._time_in_range(local_time, hours.open_time, hours.close_time):
            return MarketStatus.OPEN

        if hours.after_hours_end and self._time_in_range(
            local_time, hours.close_time, hours.after_hours_end
        ):
            return MarketStatus.AFTER_HOURS

        return MarketStatus.CLOSED

    def get_session_risk_factor(
        self, session_type: Optional[SessionType] = None
    ) -> float:
        """
        Get risk adjustment factor for the current or specified session.
        
        Returns a multiplier (0.5 - 1.5) to apply to position sizing:
        - < 1.0: Reduce position size (low liquidity, off-hours)
        - 1.0: Normal position size
        - > 1.0: Can increase size (high liquidity overlap)
        """
        if session_type is None:
            session_info = self.get_current_session()
            session_type = session_info.session_type

        risk_factors = {
            SessionType.OFF_HOURS: 0.5,
            SessionType.PACIFIC: 0.7,
            SessionType.ASIAN: 0.8,
            SessionType.EUROPEAN: 1.0,
            SessionType.US: 1.0,
            SessionType.OVERLAP_ASIAN_EUROPEAN: 1.1,
            SessionType.OVERLAP_EUROPEAN_US: 1.2,
        }

        return risk_factors.get(session_type, 0.5)

    def set_risk_override(self, session_type: SessionType, factor: float) -> None:
        """Set a manual risk adjustment override for a session."""
        self._risk_overrides[session_type] = max(0.1, min(2.0, factor))
        logger.info("Risk override set for %s: %.2f", session_type.value, factor)

    def time_until_session(
        self, target_session: SessionType, utc_now: Optional[datetime] = None
    ) -> Optional[timedelta]:
        """Calculate time until a specific session starts."""
        if utc_now is None:
            utc_now = datetime.now(timezone.utc)

        config = self.SESSIONS.get(target_session) or self.OVERLAPS.get(target_session)
        if not config:
            return None

        target_time = config["start"]
        current_time = utc_now.time()

        # Calculate time difference
        today = utc_now.date()
        target_dt = datetime.combine(today, target_time, tzinfo=timezone.utc)

        if target_dt <= utc_now:
            # Session already started today, calculate for tomorrow
            target_dt += timedelta(days=1)

        return target_dt - utc_now

    def is_safe_to_trade(self, utc_now: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        Check if it's safe to trade based on session and calendar.
        
        Returns (is_safe, reason) tuple.
        """
        session = self.get_current_session(utc_now)

        if session.market_status == MarketStatus.WEEKEND:
            return False, "Markets closed for weekend"

        if session.market_status == MarketStatus.HOLIDAY:
            return False, f"Market holiday: {', '.join(session.notes)}"

        if session.market_status == MarketStatus.CLOSED:
            return False, "Markets currently closed"

        if session.risk_adjustment < 0.3:
            return False, "Risk adjustment too low for current session"

        return True, f"Safe to trade - {session.session_type.value} session active"

    def get_status(self) -> Dict:
        """Get comprehensive session status."""
        session = self.get_current_session()
        return {
            "session_type": session.session_type.value,
            "market_status": session.market_status.value,
            "active_markets": session.active_markets,
            "is_high_liquidity": session.is_high_liquidity,
            "is_overlap": session.is_overlap,
            "volatility_factor": session.volatility_factor,
            "risk_adjustment": session.risk_adjustment,
            "notes": session.notes,
            "history_length": len(self._session_history),
        }

    def _time_in_range(self, current: time, start: time, end: time) -> bool:
        """Check if current time is within a range (handles overnight ranges)."""
        if start <= end:
            return start <= current <= end
        else:
            # Overnight range (e.g., 21:00 - 06:00)
            return current >= start or current <= end

    def _calculate_risk_adjustment(
        self,
        session: SessionType,
        status: MarketStatus,
        is_overlap: bool,
        utc_now: datetime,
    ) -> float:
        """Calculate risk adjustment based on session characteristics."""
        base = self.get_session_risk_factor(session)

        # Reduce risk near market close
        if session in (SessionType.US, SessionType.EUROPEAN):
            config = self.SESSIONS[session]
            close_time = config["end"]
            close_dt = datetime.combine(utc_now.date(), close_time, tzinfo=timezone.utc)
            time_to_close = (close_dt - utc_now).total_seconds()
            if 0 < time_to_close < 1800:  # Last 30 minutes
                base *= 0.7  # Reduce risk near close
                logger.debug("Near market close - reducing risk factor")

        # Reduce risk on half days
        if self._calendar.is_half_day(utc_now, "US"):
            base *= 0.8

        # Boost during overlaps
        if is_overlap:
            base *= 1.1

        # Cap the adjustment
        return max(0.3, min(1.5, base))
