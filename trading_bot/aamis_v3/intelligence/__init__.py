"""
Intelligence Module
============================================================

Auto-generated integration file.
"""

# institutional_intelligence
try:
    from .institutional_intelligence import (
        InstitutionalIntelligenceSystem,
    )
except ImportError as e:
    # institutional_intelligence not available
    pass

# pattern_discovery
try:
    from .pattern_discovery import (
        PatternDiscoverySystem,
        ProductiveFailureEngine,
    )
except ImportError as e:
    # pattern_discovery not available
    pass

__all__ = [
    'InstitutionalIntelligenceSystem',
    'PatternDiscoverySystem',
    'ProductiveFailureEngine',
]
