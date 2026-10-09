"""Deprecated alias — moved to ``trading_bot.research.ingestion``.

Kept so legacy imports (``import trading_bot.research_ingestion`` and
submodule imports) keep resolving during the monolithic research
consolidation. Importing this package emits a DeprecationWarning and
forwards all resolution to the canonical package under
``trading_bot/research/``.
"""

import importlib as _importlib
import sys as _sys
import warnings as _warnings

_warnings.warn(
    "trading_bot.research_ingestion moved to trading_bot.research.ingestion; "
    "update imports to the canonical path.",
    DeprecationWarning,
    stacklevel=2,
)

_sys.modules[__name__] = _importlib.import_module("trading_bot.research.ingestion")
