"""
Session Awareness - Improvement #10 (HIGH PRIORITY)
====================================================

Session-optimized trading for high-probability times.

Features:
- London session detection (best for EUR pairs)
- New York session detection (best for USD pairs)
- Asian session (ranging, avoid)
- Session overlap (highest volume)
- Weekend gap protection
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, date
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class TradingSession(Enum):
    """Trading sessions"""
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"
    SYDNEY = "sydney"
    OVERLAP_LONDON_NY = "overlap_london_ny"
    OVERLAP_ASIAN_LONDON = "overlap_asian_london"
    OFF_HOURS = "off_hours"


class SessionQuality(Enum):
    """Session quality for trading"""
    EXCELLENT = "excellent"  # Best time to trade
    GOOD = "good"           # Good time
    FAIR = "fair"           # Acceptable
    POOR = "poor"           # Not recommended
    AVOID = "avoid"         # Don't trade


@dataclass
class SessionInfo:
    """Session information"""
    session: TradingSession
    quality: SessionQuality
    start_time: time
    end_time: time
    is_active: bool
    time_remaining_minutes: int
    characteristics: List[str] = field(default_factory=list)


@dataclass
class SessionAnalysis:
    """Session analysis result"""
    symbol: str
    current_session: TradingSession
    quality: SessionQuality
    should_trade: bool
    position_size_multiplier: float
    reasons: List[str]
    next_good_session: Optional[TradingSession] = None
    minutes_until_good_session: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class LondonSessionDetector:
    """London session detection"""
    
    # London session: 7:00 - 16:00 UTC (winter) / 6:00 - 15:00 UTC (summer)
    WINTER_START = time(7, 0)
    WINTER_END = time(16, 0)
    SUMMER_START = time(6, 0)
    SUMMER_END = time(15, 0)
    
    # Best currencies for London
    PREFERRED_CURRENCIES = ['EUR', 'GBP', 'CHF']
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def is_active(self, utc_time: Optional[datetime] = None) -> bool:
        """Check if London session is active"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        current_time = utc_time.time()
        start, end = self._get_session_times(utc_time)
        
        return start <= current_time <= end
    
    def _get_session_times(self, utc_time: datetime) -> Tuple[time, time]:
        """Get session times based on DST"""
        # Simple DST check (last Sunday of March to last Sunday of October)
        month = utc_time.month
        if 3 < month < 10:
            return self.SUMMER_START, self.SUMMER_END
        return self.WINTER_START, self.WINTER_END
    
    def get_session_info(self, utc_time: Optional[datetime] = None) -> SessionInfo:
        """Get London session info"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        start, end = self._get_session_times(utc_time)
        is_active = self.is_active(utc_time)
        
        if is_active:
            end_datetime = datetime.combine(utc_time.date(), end)
            remaining = (end_datetime - utc_time).total_seconds() / 60
        else:
            remaining = 0
        
        return SessionInfo(
            session=TradingSession.LONDON,
            quality=SessionQuality.EXCELLENT if is_active else SessionQuality.AVOID,
            start_time=start,
            end_time=end,
            is_active=is_active,
            time_remaining_minutes=int(remaining),
            characteristics=[
                "High liquidity for EUR, GBP, CHF",
                "Major economic releases",
                "Institutional trading activity"
            ]
        )
    
    def is_good_for_symbol(self, symbol: str) -> bool:
        """Check if London session is good for symbol"""
        symbol = symbol.upper()
        return any(curr in symbol for curr in self.PREFERRED_CURRENCIES)


class NewYorkSessionDetector:
    """New York session detection"""
    
    # NY session: 12:00 - 21:00 UTC (winter) / 11:00 - 20:00 UTC (summer)
    WINTER_START = time(12, 0)
    WINTER_END = time(21, 0)
    SUMMER_START = time(11, 0)
    SUMMER_END = time(20, 0)
    
    # Best currencies for NY
    PREFERRED_CURRENCIES = ['USD', 'CAD']
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def is_active(self, utc_time: Optional[datetime] = None) -> bool:
        """Check if NY session is active"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        current_time = utc_time.time()
        start, end = self._get_session_times(utc_time)
        
        return start <= current_time <= end
    
    def _get_session_times(self, utc_time: datetime) -> Tuple[time, time]:
        """Get session times based on DST"""
        month = utc_time.month
        if 3 < month < 11:
            return self.SUMMER_START, self.SUMMER_END
        return self.WINTER_START, self.WINTER_END
    
    def get_session_info(self, utc_time: Optional[datetime] = None) -> SessionInfo:
        """Get NY session info"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        start, end = self._get_session_times(utc_time)
        is_active = self.is_active(utc_time)
        
        if is_active:
            end_datetime = datetime.combine(utc_time.date(), end)
            remaining = (end_datetime - utc_time).total_seconds() / 60
        else:
            remaining = 0
        
        return SessionInfo(
            session=TradingSession.NEW_YORK,
            quality=SessionQuality.EXCELLENT if is_active else SessionQuality.AVOID,
            start_time=start,
            end_time=end,
            is_active=is_active,
            time_remaining_minutes=int(remaining),
            characteristics=[
                "High liquidity for USD pairs",
                "Major US economic releases",
                "High volatility potential"
            ]
        )
    
    def is_good_for_symbol(self, symbol: str) -> bool:
        """Check if NY session is good for symbol"""
        symbol = symbol.upper()
        return any(curr in symbol for curr in self.PREFERRED_CURRENCIES)


class AsianSessionDetector:
    """Asian session detection"""
    
    # Asian session: 23:00 - 08:00 UTC
    START = time(23, 0)
    END = time(8, 0)
    
    # Best currencies for Asian
    PREFERRED_CURRENCIES = ['JPY', 'AUD', 'NZD']
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def is_active(self, utc_time: Optional[datetime] = None) -> bool:
        """Check if Asian session is active"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        current_time = utc_time.time()
        
        # Handle overnight session
        if self.START > self.END:
            return current_time >= self.START or current_time <= self.END
        return self.START <= current_time <= self.END
    
    def get_session_info(self, utc_time: Optional[datetime] = None) -> SessionInfo:
        """Get Asian session info"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        is_active = self.is_active(utc_time)
        
        return SessionInfo(
            session=TradingSession.ASIAN,
            quality=SessionQuality.FAIR if is_active else SessionQuality.AVOID,
            start_time=self.START,
            end_time=self.END,
            is_active=is_active,
            time_remaining_minutes=0,  # Complex calculation for overnight
            characteristics=[
                "Lower volatility",
                "Range-bound trading",
                "Good for JPY, AUD, NZD",
                "Avoid EUR, GBP pairs"
            ]
        )
    
    def is_good_for_symbol(self, symbol: str) -> bool:
        """Check if Asian session is good for symbol"""
        symbol = symbol.upper()
        return any(curr in symbol for curr in self.PREFERRED_CURRENCIES)


class SessionOverlapDetector:
    """Detects session overlaps"""
    
    def __init__(
        self,
        london_detector: LondonSessionDetector,
        ny_detector: NewYorkSessionDetector,
        asian_detector: AsianSessionDetector,
        config: Optional[Dict] = None
    ):
        self.london = london_detector
        self.ny = ny_detector
        self.asian = asian_detector
        self.config = config or {}
    
    def get_current_overlap(self, utc_time: Optional[datetime] = None) -> Optional[TradingSession]:
        """Get current session overlap"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        london_active = self.london.is_active(utc_time)
        ny_active = self.ny.is_active(utc_time)
        asian_active = self.asian.is_active(utc_time)
        
        if london_active and ny_active:
            return TradingSession.OVERLAP_LONDON_NY
        
        if asian_active and london_active:
            return TradingSession.OVERLAP_ASIAN_LONDON
        
        return None
    
    def is_overlap_active(self, utc_time: Optional[datetime] = None) -> bool:
        """Check if any overlap is active"""
        return self.get_current_overlap(utc_time) is not None
    
    def get_overlap_info(self, utc_time: Optional[datetime] = None) -> Optional[SessionInfo]:
        """Get overlap session info"""
        overlap = self.get_current_overlap(utc_time)
        
        if overlap == TradingSession.OVERLAP_LONDON_NY:
            return SessionInfo(
                session=TradingSession.OVERLAP_LONDON_NY,
                quality=SessionQuality.EXCELLENT,
                start_time=time(12, 0),
                end_time=time(16, 0),
                is_active=True,
                time_remaining_minutes=0,
                characteristics=[
                    "Highest liquidity period",
                    "Best for all major pairs",
                    "Highest volatility",
                    "Most trading opportunities"
                ]
            )
        
        if overlap == TradingSession.OVERLAP_ASIAN_LONDON:
            return SessionInfo(
                session=TradingSession.OVERLAP_ASIAN_LONDON,
                quality=SessionQuality.GOOD,
                start_time=time(7, 0),
                end_time=time(8, 0),
                is_active=True,
                time_remaining_minutes=0,
                characteristics=[
                    "Moderate liquidity",
                    "Good for EUR/JPY, GBP/JPY",
                    "Transition period"
                ]
            )
        
        return None


class WeekendGapProtection:
    """Protects against weekend gaps"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.close_before_weekend_hours = self.config.get('close_before_weekend_hours', 2)
        self.reopen_after_weekend_hours = self.config.get('reopen_after_weekend_hours', 1)
    
    def is_weekend(self, utc_time: Optional[datetime] = None) -> bool:
        """Check if it's weekend"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        # Forex market closes Friday 21:00 UTC, opens Sunday 21:00 UTC
        weekday = utc_time.weekday()
        hour = utc_time.hour
        
        if weekday == 4 and hour >= 21:  # Friday after 21:00
            return True
        if weekday == 5:  # Saturday
            return True
        if weekday == 6 and hour < 21:  # Sunday before 21:00
            return True
        
        return False
    
    def should_close_positions(self, utc_time: Optional[datetime] = None) -> Tuple[bool, str]:
        """Check if should close positions before weekend"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        weekday = utc_time.weekday()
        hour = utc_time.hour
        
        # Friday approaching close
        if weekday == 4:
            hours_until_close = 21 - hour
            if hours_until_close <= self.close_before_weekend_hours:
                return True, f"Weekend approaching in {hours_until_close} hours"
        
        return False, "Not near weekend"
    
    def can_open_positions(self, utc_time: Optional[datetime] = None) -> Tuple[bool, str]:
        """Check if can open positions after weekend"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        if self.is_weekend(utc_time):
            return False, "Market closed for weekend"
        
        weekday = utc_time.weekday()
        hour = utc_time.hour
        
        # Sunday after open
        if weekday == 6 and hour >= 21:
            hours_since_open = hour - 21
            if hours_since_open < self.reopen_after_weekend_hours:
                return False, f"Wait {self.reopen_after_weekend_hours - hours_since_open} hours after weekend open"
        
        return True, "Market open"
    
    def get_weekend_risk(self, utc_time: Optional[datetime] = None) -> float:
        """Get weekend gap risk (0-1)"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        weekday = utc_time.weekday()
        hour = utc_time.hour
        
        if weekday == 4:  # Friday
            hours_until_close = 21 - hour
            if hours_until_close <= 4:
                return 1 - (hours_until_close / 4)
        
        return 0.0


class SessionAwareness:
    """
    Master session awareness system.
    Combines all session detection functionality.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize detectors
        self.london = LondonSessionDetector(self.config)
        self.ny = NewYorkSessionDetector(self.config)
        self.asian = AsianSessionDetector(self.config)
        self.overlap = SessionOverlapDetector(self.london, self.ny, self.asian, self.config)
        self.weekend = WeekendGapProtection(self.config)
        
        # Performance tracking
        self.session_performance: Dict[str, Dict[TradingSession, List[float]]] = {}
    
    def get_current_session(self, utc_time: Optional[datetime] = None) -> TradingSession:
        """Get current active session"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        # Check for weekend
        if self.weekend.is_weekend(utc_time):
            return TradingSession.OFF_HOURS
        
        # Check for overlaps first
        overlap = self.overlap.get_current_overlap(utc_time)
        if overlap:
            return overlap
        
        # Check individual sessions
        if self.london.is_active(utc_time):
            return TradingSession.LONDON
        if self.ny.is_active(utc_time):
            return TradingSession.NEW_YORK
        if self.asian.is_active(utc_time):
            return TradingSession.ASIAN
        
        return TradingSession.OFF_HOURS
    
    def analyze_session(self, symbol: str, utc_time: Optional[datetime] = None) -> SessionAnalysis:
        """Analyze session for symbol"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        current_session = self.get_current_session(utc_time)
        reasons = []
        
        # Check weekend
        if self.weekend.is_weekend(utc_time):
            return SessionAnalysis(
                symbol=symbol,
                current_session=TradingSession.OFF_HOURS,
                quality=SessionQuality.AVOID,
                should_trade=False,
                position_size_multiplier=0.0,
                reasons=["Market closed for weekend"]
            )
        
        # Check weekend proximity
        should_close, close_reason = self.weekend.should_close_positions(utc_time)
        if should_close:
            return SessionAnalysis(
                symbol=symbol,
                current_session=current_session,
                quality=SessionQuality.AVOID,
                should_trade=False,
                position_size_multiplier=0.0,
                reasons=[close_reason]
            )
        
        # Determine quality based on session and symbol
        quality, size_mult = self._get_session_quality(symbol, current_session)
        
        # Build reasons
        if current_session == TradingSession.OVERLAP_LONDON_NY:
            reasons.append("London-NY overlap - highest liquidity")
        elif current_session == TradingSession.LONDON:
            if self.london.is_good_for_symbol(symbol):
                reasons.append("London session - good for EUR/GBP/CHF")
            else:
                reasons.append("London session - not optimal for this pair")
        elif current_session == TradingSession.NEW_YORK:
            if self.ny.is_good_for_symbol(symbol):
                reasons.append("NY session - good for USD pairs")
            else:
                reasons.append("NY session - not optimal for this pair")
        elif current_session == TradingSession.ASIAN:
            if self.asian.is_good_for_symbol(symbol):
                reasons.append("Asian session - good for JPY/AUD/NZD")
            else:
                reasons.append("Asian session - low volatility, avoid EUR/GBP")
        else:
            reasons.append("Off-hours - reduced liquidity")
        
        # Find next good session
        next_session, minutes_until = self._find_next_good_session(symbol, utc_time)
        
        should_trade = quality in [SessionQuality.EXCELLENT, SessionQuality.GOOD, SessionQuality.FAIR]
        
        return SessionAnalysis(
            symbol=symbol,
            current_session=current_session,
            quality=quality,
            should_trade=should_trade,
            position_size_multiplier=size_mult,
            reasons=reasons,
            next_good_session=next_session,
            minutes_until_good_session=minutes_until
        )
    
    def _get_session_quality(self, symbol: str, session: TradingSession) -> Tuple[SessionQuality, float]:
        """Get session quality for symbol"""
        symbol = symbol.upper()
        
        # Overlap is always excellent
        if session == TradingSession.OVERLAP_LONDON_NY:
            return SessionQuality.EXCELLENT, 1.0
        
        if session == TradingSession.OVERLAP_ASIAN_LONDON:
            return SessionQuality.GOOD, 0.9
        
        # London session
        if session == TradingSession.LONDON:
            if self.london.is_good_for_symbol(symbol):
                return SessionQuality.EXCELLENT, 1.0
            elif 'USD' in symbol:
                return SessionQuality.GOOD, 0.8
            else:
                return SessionQuality.FAIR, 0.6
        
        # NY session
        if session == TradingSession.NEW_YORK:
            if self.ny.is_good_for_symbol(symbol):
                return SessionQuality.EXCELLENT, 1.0
            elif 'EUR' in symbol or 'GBP' in symbol:
                return SessionQuality.GOOD, 0.8
            else:
                return SessionQuality.FAIR, 0.6
        
        # Asian session
        if session == TradingSession.ASIAN:
            if self.asian.is_good_for_symbol(symbol):
                return SessionQuality.GOOD, 0.8
            elif 'EUR' in symbol or 'GBP' in symbol:
                return SessionQuality.POOR, 0.4
            else:
                return SessionQuality.FAIR, 0.5
        
        # Off hours
        return SessionQuality.AVOID, 0.2
    
    def _find_next_good_session(self, symbol: str, utc_time: datetime) -> Tuple[Optional[TradingSession], int]:
        """Find next good session for symbol"""
        # Check next 24 hours
        for minutes in range(0, 24 * 60, 30):
            future_time = utc_time + timedelta(minutes=minutes)
            session = self.get_current_session(future_time)
            quality, _ = self._get_session_quality(symbol, session)
            
            if quality in [SessionQuality.EXCELLENT, SessionQuality.GOOD]:
                return session, minutes
        
        return None, 0
    
    def should_trade(self, symbol: str) -> Tuple[bool, str]:
        """Check if should trade based on session"""
        analysis = self.analyze_session(symbol)
        
        if not analysis.should_trade:
            return False, analysis.reasons[0] if analysis.reasons else "Session not favorable"
        
        return True, f"Session: {analysis.current_session.value} ({analysis.quality.value})"
    
    def get_position_size_multiplier(self, symbol: str) -> float:
        """Get position size multiplier based on session"""
        analysis = self.analyze_session(symbol)
        return analysis.position_size_multiplier
    
    def record_trade_performance(self, symbol: str, session: TradingSession, pnl_percent: float):
        """Record trade performance by session"""
        if symbol not in self.session_performance:
            self.session_performance[symbol] = {}
        if session not in self.session_performance[symbol]:
            self.session_performance[symbol][session] = []
        
        self.session_performance[symbol][session].append(pnl_percent)
    
    def get_best_sessions(self, symbol: str) -> List[Tuple[TradingSession, float]]:
        """Get best performing sessions for symbol"""
        if symbol not in self.session_performance:
            return []
        
        session_returns = []
        for session, returns in self.session_performance[symbol].items():
            if len(returns) >= 5:
                avg_return = statistics.mean(returns)
                session_returns.append((session, avg_return))
        
        return sorted(session_returns, key=lambda x: x[1], reverse=True)
    
    def get_session_summary(self, utc_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get current session summary"""
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        current = self.get_current_session(utc_time)
        
        return {
            'current_session': current.value,
            'london_active': self.london.is_active(utc_time),
            'ny_active': self.ny.is_active(utc_time),
            'asian_active': self.asian.is_active(utc_time),
            'overlap_active': self.overlap.is_overlap_active(utc_time),
            'is_weekend': self.weekend.is_weekend(utc_time),
            'weekend_risk': self.weekend.get_weekend_risk(utc_time),
            'utc_time': utc_time.isoformat()
        }
