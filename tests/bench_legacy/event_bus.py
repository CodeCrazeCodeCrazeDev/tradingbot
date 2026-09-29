"""
Legacy EventBus Compatibility Adapter
====================================

Bridges the legacy benchmark to the original EventBus semantics
using the canonical orchestration implementation.
"""

from trading_bot.orchestration.event_bus import (
    EventBus,
    get_event_bus,
    Event,
    EventPriority,
    EventHandler
)
