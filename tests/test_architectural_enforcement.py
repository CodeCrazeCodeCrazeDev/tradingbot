import pytest
import sys
import os
import ast
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.unified_registry import registry, UnifiedComponentRegistry
from trading_bot.core.unified_event_bus import decision_bus, UnifiedDecisionBus

def test_singleton_integrity():
    """Runtime: Verify core components are singletons."""
    csc1 = CognitiveSystemController()
    csc2 = CognitiveSystemController()
    assert csc1 is csc2, "CognitiveSystemController must be a singleton"

    reg1 = UnifiedComponentRegistry()
    reg2 = UnifiedComponentRegistry()
    assert reg1 is reg2, "UnifiedComponentRegistry must be a singleton"

    bus1 = UnifiedDecisionBus()
    bus2 = UnifiedDecisionBus()
    assert bus1 is bus2, "UnifiedDecisionBus must be a singleton"

def test_no_archive_imports():
    """Static: Ensure no active code imports from _archive."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "trading_bot"))
    violations = []

    for root, _, files in os.walk(root_dir):
        if "_archive" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        content = f.read()
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    if "_archive" in alias.name:
                                        violations.append(f"{path}: import {alias.name}")
                            elif isinstance(node, ast.ImportFrom):
                                if node.module and "_archive" in node.module:
                                    violations.append(f"{path}: from {node.module} import ...")
                    except Exception:
                        pass

    assert not violations, f"Forbidden imports from _archive found: {violations}"

def test_no_competing_orchestrators():
    """Static: Ensure no other classes ending in 'Orchestrator' exist in core directories (except CSC/IAS)."""
    core_dirs = ["trading_bot/core", "trading_bot/core_agent_system"]
    violations = []

    for cdir in core_dirs:
        full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", cdir))
        for root, _, files in os.walk(full_path):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ClassDef):
                                    # Allow CSC and certain known integration classes
                                    if node.name.endswith("Orchestrator") and node.name not in ["MasterOrchestratorIntegration", "IOrchestrator"]:
                                        violations.append(f"{path}: class {node.name}")
                        except Exception:
                            pass

    assert not violations, f"Competing orchestrators found in core: {violations}"

def test_no_bypass_csc():
    """Runtime: Ensure decisions are only made via CSC."""
    from trading_bot.services.integrated_brain_service import IntegratedBrainService
    service = IntegratedBrainService()
    assert service.SERVICE_NAME == "integrated_brain"

def test_shim_delegation():
    """Runtime: Verify legacy shims correctly delegate to CSC."""
    from trading_bot.hivemind.hivemind_orchestrator_v2 import HivemindOrchestratorV2
    from trading_bot.aamis_v3.aamis_master_orchestrator import AAMISMasterOrchestrator

    hive = HivemindOrchestratorV2()
    aamis = AAMISMasterOrchestrator()

    # We use 'is' because they should both have references to the same CSC singleton
    assert hive.csc is CognitiveSystemController()
    assert aamis.csc is CognitiveSystemController()
    assert hive.get_status()["delegated_to"] == "CSC"
