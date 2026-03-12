"""
Alphaalgo Institutional Module
============================================================

Auto-generated integration file.
"""

# core_types
try:
    from .core_types import (
        SystemConstants,
    )
except ImportError as e:
    # core_types not available
    pass

# layer3_quantitative_research
try:
    from .layer3_quantitative_research import (
        ComplexSystemsModelGenerator,
    )
except ImportError as e:
    # layer3_quantitative_research not available
    pass

# layer4_portfolio_allocation
try:
    from .layer4_portfolio_allocation import (
        CapacityManager,
        CorrelationManager,
    )
except ImportError as e:
    # layer4_portfolio_allocation not available
    pass

# layer5_risk_governance
try:
    from .layer5_risk_governance import (
        DrawdownController,
        PositionLimitManager,
        TailRiskManager,
        VaREngine,
    )
except ImportError as e:
    # layer5_risk_governance not available
    pass

# layer7_monitoring_evolution
try:
    from .layer7_monitoring_evolution import (
        EvolutionAuditEngine,
        EvolutionEngine,
    )
except ImportError as e:
    # layer7_monitoring_evolution not available
    pass

# orchestrator
try:
    from .orchestrator import (
        SystemConfig,
        SystemState,
        SystemStatus,
        AlphaAlgoInstitutional,
    )
    # Alias for backward compatibility
    InstitutionalOrchestrator = AlphaAlgoInstitutional
except ImportError as e:
    # orchestrator not available
    SystemConfig = None
    SystemState = None
    SystemStatus = None
    AlphaAlgoInstitutional = None
    InstitutionalOrchestrator = None

# research_loop
try:
    from .research_loop import (
        CapitalApprovalEngine,
        RetirementEngine,
        SimulationEngine,
        ValidationEngine,
    )
except ImportError as e:
    # research_loop not available
    CapitalApprovalEngine = None
    RetirementEngine = None
    SimulationEngine = None
    ValidationEngine = None

__all__ = [
    'CapacityManager',
    'CapitalApprovalEngine',
    'ComplexSystemsModelGenerator',
    'CorrelationManager',
    'DrawdownController',
    'EvolutionAuditEngine',
    'EvolutionEngine',
    'PositionLimitManager',
    'RetirementEngine',
    'SimulationEngine',
    'SystemConfig',
    'SystemConstants',
    'SystemState',
    'SystemStatus',
    'TailRiskManager',
    'VaREngine',
    'ValidationEngine',
    'AlphaAlgoInstitutional',
    'InstitutionalOrchestrator',
]
