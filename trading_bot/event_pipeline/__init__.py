"""
Event Pipeline Module
============================================================

Auto-generated integration file.
"""

# consistency
try:
    from .consistency import (
        TransactionManager,
    )
except ImportError as e:
    # consistency not available
    TransactionManager = None

# events
try:
    from .events import (
        SystemEvent,
    )
except ImportError as e:
    # events not available
    SystemEvent = None

# pipeline
try:
    from .pipeline import (
        EventPipeline,
    )
except ImportError as e:
    # pipeline not available
    EventPipeline = None

# scalability
try:
    from .scalability import (
        ClusterCoordinator,
        ShardManager,
        ShardManagerConfig,
    )
except ImportError as e:
    # scalability not available
    ClusterCoordinator = None
    ShardManager = None
    ShardManagerConfig = None

__all__ = [
    'ClusterCoordinator',
    'ShardManager',
    'ShardManagerConfig',
    'SystemEvent',
    'TransactionManager',
    'EventPipeline',
]
