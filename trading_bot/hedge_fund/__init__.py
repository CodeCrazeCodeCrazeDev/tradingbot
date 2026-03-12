"""
Hedge Fund Module
============================================================

Auto-generated integration file.
"""

# compliance_regulatory
try:
    from .compliance_regulatory import (
        ComplianceEngine,
    )
except ImportError as e:
    # compliance_regulatory not available
    pass

# fund_management
try:
    from .fund_management import (
        FundManager,
    )
except ImportError as e:
    # fund_management not available
    pass

# hedge_fund_orchestrator
try:
    from .hedge_fund_orchestrator import (
        HedgeFundOrchestrator,
    )
except ImportError as e:
    # hedge_fund_orchestrator not available
    pass

# institutional_risk
try:
    from .institutional_risk import (
        InstitutionalRiskManager,
        MarginManager,
        StressTestEngine,
        VaREngine,
    )
except ImportError as e:
    # institutional_risk not available
    pass

# multi_strategy
try:
    from .multi_strategy import (
        MultiStrategyEngine,
    )
except ImportError as e:
    # multi_strategy not available
    pass

# portfolio_construction
try:
    from .portfolio_construction import (
        RebalanceEngine,
    )
except ImportError as e:
    # portfolio_construction not available
    pass

__all__ = [
    'ComplianceEngine',
    'FundManager',
    'HedgeFundOrchestrator',
    'InstitutionalRiskManager',
    'MarginManager',
    'MultiStrategyEngine',
    'RebalanceEngine',
    'StressTestEngine',
    'VaREngine',
]
