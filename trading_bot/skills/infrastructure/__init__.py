"""
Infrastructure Module
============================================================

Auto-generated integration file.
"""

# canary_deployment
try:
    from .canary_deployment import (
        CanaryDeploymentSystem,
    )
except ImportError as e:
    # canary_deployment not available
    pass

# chaos_engineering
try:
    from .chaos_engineering import (
        ChaosEngineeringModule,
    )
except ImportError as e:
    # chaos_engineering not available
    pass

# distributed_state
try:
    from .distributed_state import (
        DistributedStateManager,
    )
except ImportError as e:
    # distributed_state not available
    pass

# feature_flags
try:
    from .feature_flags import (
        FeatureFlagManager,
    )
except ImportError as e:
    # feature_flags not available
    pass

__all__ = [
    'CanaryDeploymentSystem',
    'ChaosEngineeringModule',
    'DistributedStateManager',
    'FeatureFlagManager',
]
