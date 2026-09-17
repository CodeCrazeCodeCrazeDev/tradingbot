"""
Core Module - AlphaAlgo UCA V5
============================================================
The central coordination and orchestration layer for the AlphaAlgo system.
"""

from typing import List, Optional, Dict, Any
from .main_trading_loop import MainTradingLoop, TradingMode, SystemHealth, SystemState
from .unified_event_bus import UnifiedDecisionBus, LogAction, ActionStatus
from .unified_registry import UnifiedComponentRegistry as UnifiedRegistry
from .error_recovery import RecoveryManager, get_recovery_manager

# Infrastructure
from .alerting_system import AlertingSystem
from .data_manager import DataManager
from .execution_manager import ExecutionManager
from .config_validator import ConfigValidator

# Logic and Reasoning
from .chainofthoughtreasoner import ChainOfThoughtReasoner
from .alphaalgo_core_engine import AlphaAlgoCoreEngine

__all__ = [
    'MainTradingLoop',
    'TradingMode',
    'SystemHealth',
    'SystemState',
    'UnifiedDecisionBus',
    'LogAction',
    'ActionStatus',
    'UnifiedRegistry',
    'RecoveryManager',
    'get_recovery_manager',
    'AlertingSystem',
    'DataManager',
    'ExecutionManager',
    'ConfigValidator',
    'ChainOfThoughtReasoner',
    'AlphaAlgoCoreEngine',
]
