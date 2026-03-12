"""
meta package
"""

try:
    from .meta_systems import (
        DynamicMindsetSwitcher,
        EfficiencyMetric,
        FailSafeKillSwitchSystem,
        ForcedPerspectiveRotator,
        GameTheoryMarketProfiler,
        GameTheoryProfile,
        GameTheoryStrategy,
        KillSwitchLevel,
        KillSwitchStatus,
        MetaEfficiencyEngine,
        MetaRigorousPhilosophy,
        MetaSystemsOrchestrator,
        Mindset,
        MindsetState,
        Perspective,
        PerspectiveAnalysis,
        PhilosophicalAssessment
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in meta: {e}')

__all__ = [
    'DynamicMindsetSwitcher',
    'EfficiencyMetric',
    'FailSafeKillSwitchSystem',
    'ForcedPerspectiveRotator',
    'GameTheoryMarketProfiler',
    'GameTheoryProfile',
    'GameTheoryStrategy',
    'KillSwitchLevel',
    'KillSwitchStatus',
    'MetaEfficiencyEngine',
    'MetaRigorousPhilosophy',
    'MetaSystemsOrchestrator',
    'Mindset',
    'MindsetState',
    'Perspective',
    'PerspectiveAnalysis',
    'PhilosophicalAssessment',
]