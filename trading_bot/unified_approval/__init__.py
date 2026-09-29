"""
Unified Approval Module
============================================================

Auto-generated integration file.
"""

# integrator
try:
    from .integrator import (
        ApprovalSystemIntegrator,
    )
except ImportError as e:
    # integrator not available
    pass

# notification_system
try:
    from .notification_system import (
        NotificationSystem,
    )
except ImportError as e:
    # notification_system not available
    pass

# pipeline_approval
try:
    from .pipeline_approval import (
        ApprovalRulesEngine,
        PipelineApprovalManager,
    )
except ImportError as e:
    # pipeline_approval not available
    pass

__all__ = [
    'UnifiedApprovalOrchestrator',
    'ApprovalRulesEngine',
    'ApprovalSystemIntegrator',
    'NotificationSystem',
    'PipelineApprovalManager',
]


class UnifiedApprovalOrchestrator:
    """Stub for UnifiedApprovalOrchestrator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        import warnings
        warnings.warn(
            "UnifiedApprovalOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
