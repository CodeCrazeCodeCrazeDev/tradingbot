"""
CI-Enforced Architectural Invariant Checks.
Asserts that there is exactly one active, production implementation for each critical
subsystem in the AlphaAlgo ecosystem, preventing split-brain or competing layer logic.
"""

import os
import pytest
from pathlib import Path

# Paths to inspect
PRODUCTION_DIR = Path(__file__).resolve().parents[2] / "trading_bot"

def test_single_csc_implementation():
    """Assert exactly one Cognitive System Controller exists in production."""
    # Find all CSC controller.py files
    controller_paths = list(PRODUCTION_DIR.glob("**/csc/controller.py"))
    # Exclude _archive path glob
    active_controllers = [p for p in controller_paths if "_archive" not in p.parts]

    assert len(active_controllers) == 1, (
        f"Architectural Invariant Violation: Expected exactly 1 active CSC controller implementation, "
        f"found {len(active_controllers)}: {active_controllers}"
    )

def test_single_artifact_manager():
    """Assert exactly one central ArtifactManager exists in production."""
    manager_paths = list(PRODUCTION_DIR.glob("**/security/artifact_manager.py"))
    active_managers = [p for p in manager_paths if "_archive" not in p.parts]

    assert len(active_managers) == 1, (
        f"Architectural Invariant Violation: Expected exactly 1 active ArtifactManager implementation, "
        f"found {len(active_managers)}: {active_managers}"
    )

def test_single_risk_engine():
    """Assert exactly one active MASTER risk manager exists in production."""
    risk_paths = list(PRODUCTION_DIR.glob("**/risk/MASTER_risk_manager.py"))
    active_risks = [p for p in risk_paths if "_archive" not in p.parts]

    assert len(active_risks) == 1, (
        f"Architectural Invariant Violation: Expected exactly 1 active MasterRiskManager implementation, "
        f"found {len(active_risks)}: {active_risks}"
    )

def test_single_decision_bus():
    """Assert exactly one unified decision/event bus exists in production."""
    bus_paths = list(PRODUCTION_DIR.glob("**/event_pipeline/event_bus.py"))
    active_buses = [p for p in bus_paths if "_archive" not in p.parts]

    assert len(active_buses) == 1, (
        f"Architectural Invariant Violation: Expected exactly 1 active EventBus implementation, "
        f"found {len(active_buses)}: {active_buses}"
    )

def test_no_active_code_imports_from_archive():
    """Verify no active production code imports from deprecated _archive directories."""
    violations = []
    for root, dirs, files in os.walk(PRODUCTION_DIR):
        if "_archive" in Path(root).parts:
            continue
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            # Match actual import statements: e.g. "from ... import ..." or "import ..."
                            stripped_line = line.strip()
                            if (stripped_line.startswith("import ") or stripped_line.startswith("from ")) and "_archive" in stripped_line:
                                violations.append(
                                    f"{file_path.relative_to(PRODUCTION_DIR.parent)}:{idx} -> {line.strip()}"
                                )
                except Exception:
                    pass

    assert len(violations) == 0, (
        f"Architectural Invariant Violation: Active production code must NOT import from _archive folders. "
        f"Violations found:\n" + "\n".join(violations)
    )
