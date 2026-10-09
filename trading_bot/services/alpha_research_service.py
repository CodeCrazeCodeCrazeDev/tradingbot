"""Deprecated alias — moved to ``trading_bot.research.alpha_research_service``.

Kept so legacy imports keep resolving during the monolithic research
consolidation. Importing this module emits a DeprecationWarning and forwards
all attribute resolution to the canonical module.
"""

import importlib as _importlib
import sys as _sys
import warnings as _warnings

_warnings.warn(
    "trading_bot.services.alpha_research_service moved to "
    "trading_bot.research.alpha_research_service; update imports to the "
    "canonical path.",
    DeprecationWarning,
    stacklevel=2,
)

_real = _importlib.import_module(
    "trading_bot.research.alpha_research_service"
)
_sys.modules[__name__] = _real


def __getattr__(name):
    # PEP 562 fallback: covers spec-loaded module objects (tests that
    # exec_module this file under a different name) where replacing
    # sys.modules alone leaves the local module object empty.
    return getattr(_real, name)

