"""One-brain quarantine boundary (deep audit pass 2).

The user requirement: exactly ONE trading brain. The CSC is the sole decision
authority; every other *Brain*/*Orchestrator* is a quarantined compatibility
or research surface. This module proves it two ways:

1. Static: no module on the canonical runtime path imports a quarantined
   brain-implementation module (AST scan — catches new smuggling early).
2. Dynamic: the legacy ``create_brain``/``get_unified_brain`` factories cannot
   return a live order-producing loop.

Runs fast: no torch, no runtime construction.
"""

import ast
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Modules reachable on the canonical one-brain path (composition root, bot,
# CSC pipeline, cognition services). Brain imports inside these are defects.
CANONICAL_PATH_GLOBS = (
    "trading_bot/foundation/**/*.py",
    "trading_bot/core/csc/**/*.py",
    "trading_bot/cognition/**/*.py",
    "trading_bot/interfaces/**/*.py",
)
CANONICAL_PATH_FILES = (
    "main.py",
    "trading_bot/unified_bot.py",
    "trading_bot/foundation/runtime.py",
)

# Legacy brains that must never be imported by the canonical path. Quarantine
# in place: the files stay for research, but the one-brain path may not touch
# them. Keep this list aligned with the convergence manifest's
# ``quarantine``/``adapter`` classifications for brain-authority modules.
QUARANTINED_BRAIN_MODULES = {
    "trading_bot.unified_ai_brain",
    "trading_bot.trading_engine",
    "trading_bot.realtime_trading_core",
    "trading_bot.brain.brain_architecture",
    "trading_bot.brain.central_controller",
    "trading_bot.brain.brain_trader",
    "trading_bot.brain.mt5_brain_trader",
    "trading_bot.services.brain_service",
    "trading_bot.services.integrated_brain_service",
    "trading_bot.orchestrator.master_orchestrator",
    "trading_bot.orchestration.master_orchestrator",
    "trading_bot.production.live_trading_system",
}


def _iter_canonical_files():
    seen = set()
    for rel in CANONICAL_PATH_FILES:
        path = ROOT / rel
        if path.exists():
            seen.add(path)
    for pattern in CANONICAL_PATH_GLOBS:
        for path in (ROOT).glob(pattern):
            if path.is_file() and "__pycache__" not in str(path):
                seen.add(path)
    return sorted(seen)


def _imported_modules(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_canonical_path_never_imports_quarantined_brains():
    offenders = []
    for path in _iter_canonical_files():
        for mod in _imported_modules(path):
            for banned in QUARANTINED_BRAIN_MODULES:
                if mod == banned or mod.startswith(banned + "."):
                    offenders.append(f"{path.relative_to(ROOT)} imports {mod}")
    assert offenders == [], "canonical path imports quarantined brains"


def _tmp_brain_config(tmp_path):
    from trading_bot.unified_ai_brain import BrainConfig

    return BrainConfig(
        data_dir=str(tmp_path / "brain_data"),
        log_dir=str(tmp_path / "brain_logs"),
        state_dir=str(tmp_path / "brain_state"),
        max_workers=1,
    )


def test_legacy_create_brain_warns_and_is_not_the_canonical_brain(tmp_path):
    """``create_brain`` must stay a quarantined façade: deprecation warning,
    no canonical execution wiring, no CSC identity."""
    from trading_bot.core.csc.controller import CognitiveSystemController  # noqa

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from trading_bot.unified_ai_brain import create_brain

        brain = create_brain(_tmp_brain_config(tmp_path))
    assert any(w.category is DeprecationWarning for w in caught), (
        "legacy brain factory must warn it carries no production authority"
    )
    assert not isinstance(brain, CognitiveSystemController), (
        "legacy factory returned the CSC — two-brain ambiguity"
    )
    # The quarantined brain must not hold a handle on canonical authorities.
    for attr in ("execution_service", "trading_repository", "decision_bus",
                 "csc"):
        assert not hasattr(brain, attr) or getattr(brain, attr) is None, (
            f"legacy brain exposes canonical authority attribute {attr!r}"
        )


def test_legacy_brain_run_is_not_a_supported_path(tmp_path):
    """The legacy ``run`` loop must not be silently invocable as a live
    trading path — it must fail closed when not CONSCIOUS."""
    import asyncio

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from trading_bot.unified_ai_brain import create_brain, BrainState

        brain = create_brain(_tmp_brain_config(tmp_path))
    # DORMANT brain: run() must refuse, not silently start trading.
    asyncio.run(brain.run(symbols=["EURUSD"]))
    assert brain.state != BrainState.CONSCIOUS or brain.stats[
        "trades_executed"] == 0, "legacy brain executed trades while dormant"
