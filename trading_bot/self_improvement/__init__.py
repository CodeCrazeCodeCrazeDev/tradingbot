"""
Self Improvement Module
============================================================

Auto-generated integration file.

QUARANTINED 2026-10: this package is a PARALLEL improvement engine and
carries NO authority to modify code, strategy parameters, evaluators,
risk limits, or protected controls. The canonical improvement path is
trading_bot/recursive_self_improvement/ (propose → sealed validate →
human approve → shadow → graduate/rollback). Individual tools here
(e.g. mirror_market_tester, root_cause_analyzer) may be re-homed as
subordinate research/diagnostic services only through CSC-gated calls.
"""

import warnings as _warnings
_warnings.warn(
    "trading_bot.self_improvement is a quarantined parallel improvement "
    "path: no mutation/promotion authority; canonical RSI lives in "
    "trading_bot.recursive_self_improvement",
    DeprecationWarning,
    stacklevel=2,
)

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

# autonomous_fixer / improvers
try:
    from .autonomous_fixer import AutonomousFixer
except ImportError:
    pass

try:
    from .internet_strategy_improver import InternetStrategyImprover
except ImportError:
    pass

try:
    from .mirror_market_tester import MirrorMarketTester
except ImportError:
    pass

__all__ = [
    'ApprovalManager',
    'AutonomousOrchestrator',
    'ProposalEngine',
    'SelfImprovementEngine',
    'SelfImprovementOrchestrator',
    'SystemMetrics',
]

# Compat re-export
try:
    from trading_bot.autonomous import AutonomousOrchestrator  # noqa: F401
except ImportError:
    pass
