"""
Validation Module
============================================================

Auto-generated integration file.
"""

# risk_validation_gate
try:
    from .risk_validation_gate import RiskValidationGate, ValidationResponse, get_validation_gate
except ImportError as e:
    pass

# autonomous_validation
try:
    from .autonomous_validation import (
        AutonomousValidationSystem,
    )
except ImportError as e:
    # autonomous_validation not available
    pass

# data_validation_pipeline
try:
    from .data_validation_pipeline import (
        DataQuarantineManager,
    )
except ImportError as e:
    # data_validation_pipeline not available
    pass

# self_optimization
try:
    from .self_optimization import (
        SelfOptimizationSystem,
    )
except ImportError as e:
    # self_optimization not available
    pass

# self_testing
try:
    from .self_testing import (
        SelfTestingSystem,
    )
except ImportError as e:
    # self_testing not available
    pass

# self_verification
try:
    from .self_verification import (
        SelfVerificationSystem,
    )
except ImportError as e:
    # self_verification not available
    pass

__all__ = [
    'AutonomousValidationSystem',
    'DataQuarantineManager',
    'SelfOptimizationSystem',
    'SelfTestingSystem',
    'SelfVerificationSystem',
]


class ValidationOrchestrator:
    """Auto-generated stub orchestrator for validation."""
    
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "ValidationOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}

# Compat re-export
try:
    from .risk_validation_gate import RiskValidationGate  # noqa: F401
except ImportError:
    pass
