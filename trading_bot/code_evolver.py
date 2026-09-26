"""
Backward-compatibility bridge for code_evolver.
"""

import warnings as _warnings
_warnings.warn(
    "trading_bot.code_evolver is deprecated: not on the canonical runtime path and carries no improvement authority; use trading_bot.recursive_self_improvement instead.",
    DeprecationWarning,
    stacklevel=2,
)
from trading_bot.self_mastery.code_evolver import *
