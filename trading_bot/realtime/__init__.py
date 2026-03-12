"""
Realtime Module
============================================================

Auto-generated integration file.
"""

# realtime_ml
try:
    from .realtime_ml import (
        RealTimeMLEngine,
    )
except ImportError as e:
    # realtime_ml not available
    pass

# realtime_orchestrator
try:
    from .realtime_orchestrator import (
        RealTimeOrchestrator,
        SystemMode,
        SystemState,
        SystemStatus,
    )
    # Alias for backward compatibility
    RealtimeOrchestrator = RealTimeOrchestrator
except ImportError as e:
    # realtime_orchestrator not available
    RealTimeOrchestrator = None
    SystemMode = None
    SystemState = None
    SystemStatus = None
    RealtimeOrchestrator = None

# realtime_signal_engine
try:
    from .realtime_signal_engine import (
        RealTimeSignalEngine,
    )
except ImportError as e:
    # realtime_signal_engine not available
    RealTimeSignalEngine = None

__all__ = [
    'RealTimeMLEngine',
    'RealTimeOrchestrator',
    'RealTimeSignalEngine',
    'SystemMode',
    'SystemState',
    'SystemStatus',
    'RealtimeOrchestrator',
]
