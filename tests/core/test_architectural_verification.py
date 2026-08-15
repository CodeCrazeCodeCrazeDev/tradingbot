import sys
import os
import ast
import pytest
from pathlib import Path

# Authoritative singletons list
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.unified_registry import UnifiedComponentRegistry
from trading_bot.core.unified_event_bus import UnifiedDecisionBus, decision_bus

def test_singleton_integrity():
    """Verify system-wide singletons maintain unique instance identity."""
    csc1 = CognitiveSystemController()
    csc2 = CognitiveSystemController()
    assert csc1 is csc2

    registry1 = UnifiedComponentRegistry()
    registry2 = UnifiedComponentRegistry()
    assert registry1 is registry2

    bus1 = UnifiedDecisionBus()
    bus2 = UnifiedDecisionBus()
    assert bus1 is bus2
    assert decision_bus is bus1

def test_no_archive_imports_in_production():
    """Verify that no production files in trading_bot import from the _archive directory."""
    root_dir = Path(__file__).parent.parent.parent / "trading_bot"

    for path in root_dir.glob("**/*.py"):
        if "_archive" in path.parts:
            continue

        with open(path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(path))
                for node in ast.walk(tree):
                    # Check direct imports (e.g., import _archive)
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            assert "_archive" not in name.name, f"Forbidden import of _archive in {path}: {name.name}"
                    # Check from imports (e.g., from _archive import ...)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            assert "_archive" not in node.module, f"Forbidden from-import of _archive in {path}: {node.module}"
            except SyntaxError:
                # Skip files with syntax errors (legacy or templates)
                continue

def test_clean_dependency_resolution():
    """Verify that core modules can be imported cleanly without circular import errors."""
    import trading_bot.core.csc.controller
    import trading_bot.core.unified_event_bus
    import trading_bot.core.unified_registry
    import trading_bot.database.shared_memory_manager
    assert True
