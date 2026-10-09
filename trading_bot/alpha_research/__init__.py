"""Deprecated alias — moved to ``trading_bot.research.alpha_research``.

Kept so legacy imports (``import trading_bot.alpha_research`` and submodule
imports such as ``trading_bot.alpha_research.dynamic_risk_matrix``) keep
resolving during the monolithic research consolidation. Importing this
package emits a DeprecationWarning and forwards all resolution to the
canonical package under ``trading_bot/research/``.
"""

import importlib as _importlib
import sys as _sys
import warnings as _warnings

_warnings.warn(
    "trading_bot.alpha_research moved to trading_bot.research.alpha_research; "
    "update imports to the canonical path.",
    DeprecationWarning,
    stacklevel=2,
)

_sys.modules[__name__] = _importlib.import_module("trading_bot.research.alpha_research")
