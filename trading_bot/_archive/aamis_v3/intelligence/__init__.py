"""
intelligence package
"""

try:
    from .institutional_intelligence import (
        BehavioralFingerprinter,
        InstitutionType,
        InstitutionalFingerprint,
        InstitutionalIntelligenceSystem,
        InstitutionalOrderFlowEmulator,
        MarketMakerProfile,
        MarketMakerProfiler,
        OrderFlowPattern,
        ShadowModel,
        ShadowModelBuilder,
        TradingStyle,
        WhaleActivity,
        WhaleTracker
    )
    from .pattern_discovery import (
        CrossDomainInnovator,
        CrossDomainPattern,
        DiscoveredPattern,
        DiscoveryMethod,
        FailureLesson,
        PatternDiscoverySystem,
        PatternType,
        ProductiveFailureEngine,
        UnnamedPatternScanner
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in intelligence: {e}')

__all__ = [
    'BehavioralFingerprinter',
    'CrossDomainInnovator',
    'CrossDomainPattern',
    'DiscoveredPattern',
    'DiscoveryMethod',
    'FailureLesson',
    'InstitutionType',
    'InstitutionalFingerprint',
    'InstitutionalIntelligenceSystem',
    'InstitutionalOrderFlowEmulator',
    'MarketMakerProfile',
    'MarketMakerProfiler',
    'OrderFlowPattern',
    'PatternDiscoverySystem',
    'PatternType',
    'ProductiveFailureEngine',
    'ShadowModel',
    'ShadowModelBuilder',
    'TradingStyle',
    'UnnamedPatternScanner',
    'WhaleActivity',
    'WhaleTracker',
]