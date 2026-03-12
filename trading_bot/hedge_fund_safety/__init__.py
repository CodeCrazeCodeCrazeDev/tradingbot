"""
Hedge Fund Safety Module
============================================================

Auto-generated integration file.
"""

# catastrophic_prevention
try:
    from .catastrophic_prevention import (
        LiquidityCrisisManager,
    )
except ImportError as e:
    # catastrophic_prevention not available
    pass

# financial_safeguards
try:
    from .financial_safeguards import (
        LeverageController,
    )
except ImportError as e:
    # financial_safeguards not available
    pass

# mitigation_orchestrator
try:
    from .mitigation_orchestrator import (
        HedgeFundSafetyOrchestrator,
    )
except ImportError as e:
    # mitigation_orchestrator not available
    pass

# operational_safety
try:
    from .operational_safety import (
        AuditTrailSystem,
        RecoveryManager,
    )
except ImportError as e:
    # operational_safety not available
    pass

# systemic_protection
try:
    from .systemic_protection import (
        CounterpartyRiskManager,
        SystemicProtection,
    )
except ImportError as e:
    # systemic_protection not available
    pass

__all__ = [
    'AuditTrailSystem',
    'CounterpartyRiskManager',
    'HedgeFundSafetyOrchestrator',
    'LeverageController',
    'LiquidityCrisisManager',
    'RecoveryManager',
    'SystemicProtection',
]
