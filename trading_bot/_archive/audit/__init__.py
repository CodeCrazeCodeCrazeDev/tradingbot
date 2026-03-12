"""
import logging
logger = logging.getLogger(__name__)
Audit and Trade Journal Module

Provides comprehensive logging and audit trail for all trading activities.
"""

from trading_bot.audit.trade_journal import (
    TradeJournal,
    TradeRecord,
    AuditEvent,
    EventType,
    get_trade_journal,
    log_trade_signal,
    log_order_placed,
    log_system_event
)

__all__ = [
    'TradeJournal',
    'TradeRecord',
    'AuditEvent',
    'EventType',
    'get_trade_journal',
    'log_trade_signal',
    'log_order_placed',
    'log_system_event'
]
