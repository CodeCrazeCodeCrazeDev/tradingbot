"""
trading_calendar package
"""

try:
    from .economic_calendar import (
        Currency,
        EconomicCalendarFetcher,
        EconomicCalendarManager,
        EconomicEvent,
        EventCategory,
        EventImpact,
        HIGH_IMPACT_EVENTS,
        TradingRestriction,
        get_calendar_manager
    )
    from .session_manager import (
        MarketHoliday,
        MarketSession,
        MarketType,
        SessionManager,
        SessionRiskProfile,
        SessionType,
        TradingCalendar,
        get_current_session,
        get_session_manager,
        is_market_open,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in trading_calendar: {e}')

__all__ = [
    'Currency',
    'EconomicCalendarFetcher',
    'EconomicCalendarManager',
    'EconomicEvent',
    'EventCategory',
    'EventImpact',
    'HIGH_IMPACT_EVENTS',
    'MarketHoliday',
    'MarketSession',
    'MarketType',
    'SessionManager',
    'SessionRiskProfile',
    'SessionType',
    'TradingCalendar',
    'TradingRestriction',
    'get_calendar_manager',
    'get_current_session',
    'get_session_manager',
    'is_market_open',
    'retry',
]