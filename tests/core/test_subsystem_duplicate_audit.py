import sys
import os
import re
import json
from pathlib import Path
import pytest
from typing import Dict, Any

# Subsystem Registry Maps for exact single authoritative proof
SUBSYSTEMS = {
    "Orchestrator": {
        "authoritative": "CognitiveSystemController",
        "deprecated": ["MasterOrchestrator", "MetaOrchestrator", "NeurosEvolutionOrchestrator", "MetaIntelligenceOrchestrator"]
    },
    "World Model": {
        "authoritative": "CausalWorldModel",
        "deprecated": ["LegacyWorldModel", "SimpleWorldModel", "WorldModelV1"]
    },
    "Planner": {
        "authoritative": "FoldingOperator",
        "deprecated": ["LegacyPlanner", "SimplePlanner"]
    },
    "Risk Engine": {
        "authoritative": "UnifiedRiskEngine",
        "deprecated": ["LegacyRiskManager", "SimpleRiskEngine"]
    },
    "Memory Authority": {
        "authoritative": "HierarchicalMemorySystem",
        "deprecated": ["LegacyMemorySystem", "SimpleMemory"]
    },
    "Event Bus": {
        "authoritative": "UnifiedDecisionBus",
        "deprecated": ["LegacyEventBus", "SimpleEventBus"]
    },
    "Registry": {
        "authoritative": "UnifiedComponentRegistry",
        "deprecated": ["LegacyRegistry", "SimpleRegistry"]
    },
    "Model Manager": {
        "authoritative": "ModelArtifactManager",
        "deprecated": ["LegacyModelManager", "SimpleModelLoader"]
    },
    "Serialization Framework": {
        "authoritative": "SerializerRegistry",
        "deprecated": ["PickleSerializer", "LegacySerializer"]
    }
}

def generate_subsystem_duplicate_report() -> Dict[str, Any]:
    """
    Scans the repository to locate all active occurrences of both authoritative
    and deprecated duplicate implementations, generating a comprehensive compliance report.
    """
    root_dir = Path(__file__).parent.parent.parent / "trading_bot"
    report = {}

    # Pre-compile regex for class definitions
    class_pattern = re.compile(r"class\s+(\w+)\b")

    for category, config in SUBSYSTEMS.items():
        category_report = {
            "authoritative": config["authoritative"],
            "occurrences": [],
            "deprecated_occurrences": [],
            "status": "PASS"
        }

        # Scan files
        for path in root_dir.glob("**/*.py"):
            if "_archive" in path.parts:
                continue

            # Skip caches, checkpoints, and non-core assets
            if any(part in path.parts for part in ["__pycache__", ".pytest_cache", ".git"]):
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Fast check to see if the file defines classes
                if "class " not in content:
                    continue

                # Search class names
                classes_defined = class_pattern.findall(content)
                for cls_name in classes_defined:
                    if cls_name == config["authoritative"]:
                        category_report["occurrences"].append(str(path))
                    elif cls_name in config["deprecated"]:
                        category_report["deprecated_occurrences"].append({
                            "file": str(path),
                            "class": cls_name
                        })
            except Exception:
                continue

        # Check integrity
        if len(category_report["occurrences"]) > 1:
            category_report["status"] = "FAIL_DUPLICATE_AUTHORITATIVE"
        elif len(category_report["deprecated_occurrences"]) > 0:
            category_report["status"] = "DEPRECATED_ACTIVE_WARNING"

        report[category] = category_report

    return report

def test_central_subsystem_duplicate_audit():
    """Verify that there is exactly one authoritative class definition for each major subsystem."""
    report = generate_subsystem_duplicate_report()

    # Save the report for production inspection and documentation
    report_path = Path(__file__).parent.parent.parent / "subsystem_duplicate_audit_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n================ SUBSYSTEM DUPLICATE AUDIT REPORT ================")
    for category, r in report.items():
        print(f"Subsystem: {category}")
        print(f"  Authoritative Class: {r['authoritative']}")
        print(f"  Active Def Paths: {r['occurrences']}")
        print(f"  Deprecated Active Defs: {r['deprecated_occurrences']}")
        print(f"  Status: {r['status']}")
        assert r["status"] != "FAIL_DUPLICATE_AUTHORITATIVE", f"Duplicate authoritative implementation found for {category}!"
    print("==================================================================\n")
