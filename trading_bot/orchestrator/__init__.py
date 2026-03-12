"""
Orchestrator Module
============================================================

Auto-generated integration file.
"""

# agent_orchestrator
try:
    from .agent_orchestrator import (
        AgentOrchestrator,
    )
except ImportError as e:
    # agent_orchestrator not available
    pass

# execution_engine
try:
    from .execution_engine import (
        ExecutionEngine,
    )
except ImportError as e:
    # execution_engine not available
    pass

# master_orchestrator
try:
    from .master_orchestrator import (
        MasterOrchestrator,
    )
except ImportError as e:
    # master_orchestrator not available
    pass

# performance_tracker
try:
    from .performance_tracker import (
        BacktestEngine,
    )
except ImportError as e:
    # performance_tracker not available
    pass

# risk_manager
try:
    from .risk_manager import (
        DrawdownController,
        PortfolioRiskManager,
    )
except ImportError as e:
    # risk_manager not available
    pass

# workflow_manager
try:
    from .workflow_manager import (
        WorkflowManager,
    )
except ImportError as e:
    # workflow_manager not available
    pass

__all__ = [
    'AgentOrchestrator',
    'BacktestEngine',
    'DrawdownController',
    'ExecutionEngine',
    'MasterOrchestrator',
    'PortfolioRiskManager',
    'WorkflowManager',
]
