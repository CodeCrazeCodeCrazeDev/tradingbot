"""
Self Improvement Module
============================================================

Auto-generated integration file.
"""

# approval_manager
try:
    from .approval_manager import (
        ApprovalManager,
    )
except ImportError as e:
    # approval_manager not available
    pass

# autonomous_orchestrator
try:
    from .autonomous_orchestrator import (
        AutonomousOrchestrator,
    )
except ImportError as e:
    # autonomous_orchestrator not available
    pass

# engine
try:
    from .engine import (
        SelfImprovementEngine,
    )
except ImportError as e:
    # engine not available
    pass

# proposal_engine
try:
    from .proposal_engine import (
        ProposalEngine,
    )
except ImportError as e:
    # proposal_engine not available
    pass

# self_improvement_orchestrator
try:
    from .self_improvement_orchestrator import (
        SelfImprovementOrchestrator,
    )
except ImportError as e:
    # self_improvement_orchestrator not available
    pass

# triage
try:
    from .triage import (
        SystemMetrics,
    )
except ImportError as e:
    # triage not available
    pass

__all__ = [
    'ApprovalManager',
    'AutonomousOrchestrator',
    'ProposalEngine',
    'SelfImprovementEngine',
    'SelfImprovementOrchestrator',
    'SystemMetrics',
]
