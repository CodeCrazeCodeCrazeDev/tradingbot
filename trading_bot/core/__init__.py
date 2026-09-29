"""
Core Module - AlphaAlgo UCA V5
============================================================
The central coordination and orchestration layer for the AlphaAlgo system.

Names are resolved lazily (PEP 562): ``execution_manager`` pulls the risk
stack which pulls sklearn (~60s cold on this box), so nothing imports at
package-init time. Attribute access loads the owning module on demand.
"""

import importlib as _importlib

_LAZY = {
    'MainTradingLoop': '.main_trading_loop',
    'TradingMode': '.main_trading_loop',
    'SystemHealth': '.main_trading_loop',
    'SystemState': '.main_trading_loop',
    'UnifiedDecisionBus': '.unified_event_bus',
    'LogAction': '.unified_event_bus',
    'ActionStatus': '.unified_event_bus',
    'UnifiedRegistry': '.unified_registry',
    'RecoveryManager': '.error_recovery',
    'get_recovery_manager': '.error_recovery',
    'AlertingSystem': '.alerting_system',
    'DataManager': '.data_manager',
    'ExecutionManager': '.execution_manager',
    'ConfigValidator': '.config_validator',
    'ChainOfThoughtReasoner': '.chainofthoughtreasoner',
    'AlphaAlgoCoreEngine': '.alphaalgo_core_engine',
}

__all__ = list(_LAZY)


def __getattr__(name):
    mod = _LAZY.get(name)
    if mod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(_importlib.import_module(mod, __name__), name)


def __dir__():
    return sorted(__all__)
