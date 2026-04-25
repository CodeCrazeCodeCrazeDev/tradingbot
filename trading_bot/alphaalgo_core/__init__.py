"""
Alphaalgo Core Module
============================================================

Auto-generated integration file.
"""

# alphaalgo_core
try:
    from .alphaalgo_core import (
        AlphaAlgoCore,
    )
except ImportError as e:
    # alphaalgo_core not available
    pass

# alphaalgo_orchestrator
try:
    from .alphaalgo_orchestrator import (
        AlphaAlgoOrchestrator,
    )
except ImportError as e:
    # alphaalgo_orchestrator not available
    pass

# capital_governance
try:
    from .capital_governance import (
        CapitalGovernanceSystem,
        ExposureControllerResult,
    )
except ImportError as e:
    # capital_governance not available
    pass

# central_controller
try:
    from .central_controller import (
        CentralController,
        G1_Controller,
    )
except ImportError as e:
    # central_controller not available
    pass

# exposure_controller
try:
    from .exposure_controller import (
        ExposureController,
    )
except ImportError as e:
    # exposure_controller not available
    pass

# fail_safe
try:
    from .fail_safe import (
        FailSafeSystem,
        SystemHealth,
        SystemStatus,
    )
except ImportError as e:
    # fail_safe not available
    pass

# governance_system
try:
    from .governance_system import (
        GovernanceSystem,
    )
except ImportError as e:
    # governance_system not available
    pass

# integration
try:
    from .integration import (
        AlphaAlgoCoreIntegration,
        MasterOrchestratorIntegration,
        PortfolioRiskManagerIntegration,
        TradingEngineIntegration,
    )
except ImportError as e:
    # integration not available
    pass

# mini_ai_factory
try:
    from .mini_ai_factory import (
        FeatureEngineerAI,
    )
except ImportError as e:
    # mini_ai_factory not available
    pass

# regime_hostility_engine
try:
    from .regime_hostility_engine import (
        RegimeHostilityEngine,
    )
except ImportError as e:
    # regime_hostility_engine not available
    pass

# security_core
try:
    from .security_core import (
        SecurityCore,
    )
except ImportError as e:
    # security_core not available
    pass

# self_repair
try:
    from .self_repair import (
        SelfRepairEngine,
    )
except ImportError as e:
    # self_repair not available
    pass

# alphaalgo_meta_system
try:
    from .alphaalgo_meta_system import (
        AlphaAlgoMetaSystem,
        WorkflowType,
        BottleneckType,
        ImprovementStatus,
        WorkflowBottleneck,
        ImprovementProposal,
        RiskCapabilityBalance,
        SandboxValidationResult,
        create_alphaalgo_meta_system,
    )
except ImportError as e:
    # alphaalgo_meta_system not available
    pass

__all__ = [
    'AlphaAlgoCore',
    'AlphaAlgoCoreIntegration',
    'AlphaAlgoMetaSystem',
    'AlphaAlgoOrchestrator',
    'BottleneckType',
    'CapitalGovernanceSystem',
    'CentralController',
    'ExposureController',
    'ExposureControllerResult',
    'FailSafeSystem',
    'FeatureEngineerAI',
    'G1_Controller',
    'GovernanceSystem',
    'ImprovementProposal',
    'ImprovementStatus',
    'MasterOrchestratorIntegration',
    'PortfolioRiskManagerIntegration',
    'RegimeHostilityEngine',
    'RiskCapabilityBalance',
    'SandboxValidationResult',
    'SecurityCore',
    'SelfRepairEngine',
    'SystemHealth',
    'SystemStatus',
    'TradingEngineIntegration',
    'WorkflowBottleneck',
    'WorkflowType',
    'create_alphaalgo_meta_system',
]
