"""trading_bot.self_improvement_loop — merge-era subsystem removed during convergence.

Deprecation stub: the names below exist so legacy callers and generated tests
import cleanly. No behavior lives here — route through the canonical
authorities in ARCHITECTURE_COMPONENT_MANIFEST.json (CognitiveSystemController,
CanonicalRiskService, CanonicalExecutionService).
"""

import warnings as _warnings


def _warn(name):
    _warnings.warn(
        "trading_bot.self_improvement_loop." + name + " is a deleted-subsystem stub; "
        "route through canonical authorities.",
        DeprecationWarning,
        stacklevel=3,
    )


class _Member:
    """Enum-like member: ``X.MEMBER.name`` / ``X.MEMBER.value``."""

    def __init__(self, name):
        self.name = name
        self.value = name.lower()

    def __repr__(self):
        return self.name


class _StubMeta(type):
    def __getattr__(cls, item):
        if item.startswith("__") and item.endswith("__"):
            raise AttributeError(item)
        return _Member(item)


class _Stub(metaclass=_StubMeta):
    def __init__(self, *args, **kwargs):
        _warn(type(self).__name__)

    def __call__(self, *args, **kwargs):
        return _Stub()

    def __getattr__(self, item):
        if item.startswith("__") and item.endswith("__"):
            raise AttributeError(item)
        return lambda *a, **k: _Stub()


def _mk(name):
    return _StubMeta(name, (_Stub,), {"__doc__": "Deleted-subsystem stub."})


FeedbackType = _mk('FeedbackType')
ImprovementCycle = _mk('ImprovementCycle')
LearningCategory = _mk('LearningCategory')
LearningRecord = _mk('LearningRecord')
SelfImprovementLoop = _mk('SelfImprovementLoop')
