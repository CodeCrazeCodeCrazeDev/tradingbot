"""
Backward-compatibility bridge for ai_learner.
"""

import warnings as _warnings
_warnings.warn(
    "trading_bot.ai_learner is deprecated: not on the canonical runtime path and carries no improvement authority; use trading_bot.recursive_self_improvement instead.",
    DeprecationWarning,
    stacklevel=2,
)
from trading_bot.sentient_core.ai_learner import *
