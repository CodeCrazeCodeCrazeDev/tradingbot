"""
Alpha Engine Module
============================================================

Auto-generated integration file.
"""

# advanced_deep_learning
try:
    from .advanced_deep_learning import (
        IntegratedDeepLearningEngine,
    )
except ImportError as e:
    # advanced_deep_learning not available
    pass

# advanced_ensemble
try:
    from .advanced_ensemble import (
        ConsensusEngine,
    )
except ImportError as e:
    # advanced_ensemble not available
    pass

# advanced_monitoring
try:
    from .advanced_monitoring import (
        AlertManager,
        MonitoringEngine,
    )
except ImportError as e:
    # advanced_monitoring not available
    pass

# advanced_risk_management
try:
    from .advanced_risk_management import (
        AdvancedRiskManager,
    )
except ImportError as e:
    # advanced_risk_management not available
    pass

# backtesting
try:
    from .backtesting import (
        StressTestEngine,
    )
except ImportError as e:
    # backtesting not available
    pass

# behavioral_finance
try:
    from .behavioral_finance import (
        BehavioralFinanceEngine,
    )
except ImportError as e:
    # behavioral_finance not available
    pass

# compliance_xai
try:
    from .compliance_xai import (
        AuditTrailManager,
        ComplianceEngine,
    )
except ImportError as e:
    # compliance_xai not available
    pass

# cross_asset_arbitrage
try:
    from .cross_asset_arbitrage import (
        CrossAssetArbitrageEngine,
    )
except ImportError as e:
    # cross_asset_arbitrage not available
    pass

# dc_core
try:
    from .dc_core import (
        DCThresholdManager,
        DirectionalChangeEngine,
    )
except ImportError as e:
    # dc_core not available
    pass

# enhanced_dc_core
try:
    from .enhanced_dc_core import (
        EnhancedDCEngine,
        MarketMakingEngine,
    )
except ImportError as e:
    # enhanced_dc_core not available
    pass

# ensemble
try:
    from .ensemble import (
        ConsensusEngine,
    )
except ImportError as e:
    # ensemble not available
    pass

# monitoring
try:
    from .monitoring import (
        AlertSystem,
        SystemHealth,
    )
except ImportError as e:
    # monitoring not available
    pass

# multi_brain
try:
    from .multi_brain import (
        BaseBrain,
        BrainCoordinator,
        BrainSignal,
        BrainType,
        MeanReversionBrain,
        MomentumBrain,
        MultiBrainArchitecture,
        TrendFollowerBrain,
        VolatilityBrain,
    )
except ImportError as e:
    # multi_brain not available
    pass

# orchestrator
try:
    from .orchestrator import (
        AlphaEngineOrchestrator,
    )
    # Alias for backward compatibility
    AlphaEngine = AlphaEngineOrchestrator
except ImportError as e:
    # orchestrator not available
    AlphaEngine = None
    pass

# risk_management
try:
    from .risk_management import (
        MLRiskManager,
    )
except ImportError as e:
    # risk_management not available
    pass

# self_analysis
try:
    from .self_analysis import (
        SelfAnalysisEngine,
    )
except ImportError as e:
    # self_analysis not available
    pass

# trading_playbook
try:
    from .trading_playbook import (
        PositionManager,
    )
except ImportError as e:
    # trading_playbook not available
    pass

__all__ = [
    'AdvancedRiskManager',
    'AlertManager',
    'AlertSystem',
    'AlphaEngine',
    'AlphaEngineOrchestrator',
    'AuditTrailManager',
    'BaseBrain',
    'BehavioralFinanceEngine',
    'BrainCoordinator',
    'BrainSignal',
    'BrainType',
    'ComplianceEngine',
    'ConsensusEngine',
    'CrossAssetArbitrageEngine',
    'DCThresholdManager',
    'DirectionalChangeEngine',
    'EnhancedDCEngine',
    'IntegratedDeepLearningEngine',
    'MLRiskManager',
    'MarketMakingEngine',
    'MeanReversionBrain',
    'MomentumBrain',
    'MonitoringEngine',
    'MultiBrainArchitecture',
    'PositionManager',
    'SelfAnalysisEngine',
    'StressTestEngine',
    'SystemHealth',
    'TrendFollowerBrain',
    'VolatilityBrain',
]
