"""
Offline Rl Module
============================================================

Auto-generated integration file.
"""

# The agents imported below pull d3rlpy, which imports the deprecated
# `gym` package. gym's __init__ prints an unmaintained banner to
# stderr via gym_notices on first import — importing it once under a
# redirected stderr drains that notice so it never reaches the logs.
# No behavior change: gym remains importable for d3rlpy.
try:
    import contextlib as _contextlib
    import io as _io
    with _contextlib.redirect_stderr(_io.StringIO()):
        import gym as _gym  # noqa: F401
except Exception:  # noqa: BLE001
    pass

# alphaalgo_autonomous_system
try:
    from .alphaalgo_autonomous_system import (
        AlphaAlgoAutonomousSystem,
    )
except ImportError as e:
    # alphaalgo_autonomous_system not available
    pass

# autonomous_upgrade_orchestrator
try:
    from .autonomous_upgrade_orchestrator import (
        AutonomousUpgradeOrchestrator,
    )
except ImportError as e:
    # autonomous_upgrade_orchestrator not available
    pass

# continuous_learning_orchestrator
try:
    from .continuous_learning_orchestrator import (
        ContinuousLearningOrchestrator,
    )
except ImportError as e:
    # continuous_learning_orchestrator not available
    pass

__all__ = [
    'AlphaAlgoAutonomousSystem',
    'AutonomousUpgradeOrchestrator',
    'ContinuousLearningOrchestrator',
]
