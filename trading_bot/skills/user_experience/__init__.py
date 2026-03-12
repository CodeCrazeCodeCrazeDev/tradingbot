"""
User Experience Module
============================================================

Auto-generated integration file.
"""

# alert_system
try:
    from .alert_system import (
        IntelligentAlertSystem,
    )
except ImportError as e:
    # alert_system not available
    pass

# explainability
try:
    from .explainability import (
        ExplainabilityEngine,
    )
except ImportError as e:
    # explainability not available
    pass

__all__ = [
    'ExplainabilityEngine',
    'IntelligentAlertSystem',
]
