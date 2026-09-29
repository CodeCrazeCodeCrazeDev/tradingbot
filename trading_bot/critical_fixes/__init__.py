"""
Critical Fixes Module
============================================================

Auto-generated integration file.
"""

# master_safety_orchestrator
try:
    from .master_safety_orchestrator import (
        MasterSafetyOrchestrator,
        SystemStatus,
    )
except ImportError as e:
    # master_safety_orchestrator not available
    pass

# position_state_manager
try:
    from .position_state_manager import (
        PositionStateManager,
        PositionState,
        PositionStatus,
    )
except ImportError as e:
    # position_state_manager not available
    pass

# realtime_risk_calculator
try:
    from .realtime_risk_calculator import (
        RealtimeRiskCalculator,
        RiskLimits,
        RiskMetrics,
        RiskLevel,
        DrawdownLevel,
    )
except ImportError:
    pass

# multi_layer_kill_switch
try:
    from .multi_layer_kill_switch import (
        MultiLayerKillSwitch,
        KillSwitchLevel,
        KillSwitchTrigger,
        KillSwitchBypassError,
    )
except ImportError:
    pass

# data_validator / execution_quality_monitor / silent_failure_detector /
# config_integrity_monitor / regulatory_compliance
try:
    from .data_validator import DataValidator, DataQualityReport, DataQualityLevel
except ImportError:
    pass
try:
    from .execution_quality_monitor import ExecutionQualityMonitor, ExecutionMetrics, ExecutionQuality
except ImportError:
    pass
try:
    from .silent_failure_detector import SilentFailureDetector, FailureReport, ComponentStatus
except ImportError:
    pass
try:
    from .config_integrity_monitor import ConfigIntegrityMonitor
except ImportError:
    pass
try:
    from .regulatory_compliance import RegulatoryComplianceMonitor, RegulatoryRegime
except ImportError:
    pass

__all__ = [
    'CriticalFixesManager',
    'MasterSafetyOrchestrator',
    'PositionStateManager',
    'PositionState',
    'PositionStatus',
    'SystemStatus',
    'RealtimeRiskCalculator',
    'RiskLimits',
    'RiskMetrics',
    'RiskLevel',
    'DrawdownLevel',
    'MultiLayerKillSwitch',
    'KillSwitchLevel',
    'KillSwitchTrigger',
    'KillSwitchBypassError',
    'DataValidator',
    'DataQualityReport',
    'DataQualityLevel',
    'ExecutionQualityMonitor',
    'ExecutionMetrics',
    'ExecutionQuality',
    'SilentFailureDetector',
    'FailureReport',
    'ComponentStatus',
    'ConfigIntegrityMonitor',
    'RegulatoryComplianceMonitor',
    'RegulatoryRegime',
]

class CriticalFixesOrchestrator:
    """Auto-generated stub orchestrator for module integration."""
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "CriticalFixesOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
        self._initialized = True
    
    async def start(self):
        """Start the orchestrator."""
        self.running = True
    
    async def stop(self):
        """Stop the orchestrator."""
        self.running = False
    
    def get_status(self):
        """Get orchestrator status."""
        return {"running": self.running, "initialized": self._initialized}



class CriticalFixesManager:
    """Stub for CriticalFixesManager."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
