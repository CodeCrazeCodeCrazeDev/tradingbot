"""Legacy duplicate subsystems warn on import but keep their import API."""

import importlib
import sys
import warnings

import pytest

SHIMMED_MODULES = [
    "trading_bot.recursive_improvement",
    "trading_bot.eternal_evolution",
    "trading_bot.alpha_evolve",
    "trading_bot.autonomous_learner",
    "trading_bot.adaptive_systems",
    "trading_bot.meta_learning",
    "trading_bot.code_evolver",
    "trading_bot.auto_optimizer",
    "trading_bot.auto_rollback",
    "trading_bot.continual_learner",
    "trading_bot.self_learning",
    "trading_bot.ai_learner",
    "trading_bot.experiment_tracker",
    "trading_bot.optimization",
    "trading_bot.performance_optimizer",
]


def _fresh_import(name: str):
    """Import a module with a clean sys.modules entry for it only."""
    sys.modules.pop(name, None)
    try:
        importlib.import_module(name)
    except ImportError:
        # Some legacy modules have broken optional imports; a shim warning is
        # still emitted before the failure, which is what we check.
        pass


@pytest.mark.parametrize("name", SHIMMED_MODULES)
def test_deprecated_module_emits_warning(name):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _fresh_import(name)
    assert any(
        w.category is DeprecationWarning
        and "not on the canonical runtime path" in str(w.message)
        for w in caught
    ), f"{name} did not emit the RSI deprecation shim warning"


def test_canonical_rsi_package_has_no_deprecation_shim():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _fresh_import("trading_bot.recursive_self_improvement")
    assert not any(
        "not on the canonical runtime path" in str(w.message) for w in caught
    )
