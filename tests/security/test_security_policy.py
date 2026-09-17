"""
CI-Enforceable Repository-Wide Security and Architectural Policy Test
Automatically scans the codebase recursively for forbidden statements, security vulnerabilities,
and architectural invariants (ensuring 'One Brain, One Event Bus' singleton architectures).
"""

import os
import re
import pytest
from pathlib import Path

# Authoritative subsystems path mappings
T0_INVARIANTS = {
    "Strategic Controller": {
        "authoritative": "trading_bot/core/csc/controller.py",
        "pattern": re.compile(r"class CognitiveSystemController")
    },
    "Decision Event Bus": {
        "authoritative": "trading_bot/core/unified_event_bus.py",
        "pattern": re.compile(r"class UnifiedDecisionBus")
    },
    "Unified Component Registry": {
        "authoritative": "trading_bot/core/unified_registry.py",
        "pattern": re.compile(r"class UnifiedComponentRegistry")
    },
    "Hierarchical Memory System": {
        "authoritative": "trading_bot/core/hms/memory.py",
        "pattern": re.compile(r"class HierarchicalMemorySystem")
    },
    "Skill Router": {
        "authoritative": "trading_bot/core/csc/router.py",
        "pattern": re.compile(r"class SkillRouter")
    }
}

# Forbidden pattern definitions
FORBIDDEN_PATTERNS = {
    "eval_usage": re.compile(r"(?<!\.)\beval\s*\("), # Filters out PyTorch .eval()
    "exec_usage": re.compile(r"(?<!\.)\bexec\s*\("),
    "os_popen": re.compile(r"\bos\.popen\s*\("),
    "subprocess_shell": re.compile(r"\bsubprocess\.[A-Za-z0-9_]+\s*\(.*shell\s*=\s*True"),
    "disabled_tls": re.compile(r"verify\s*=\s*False", re.IGNORECASE),
}

def test_architecture_invariants():
    """Verify that there is exactly one authoritative singleton implementation of all Tier-0 systems."""
    root_dir = Path(__file__).resolve().parents[2]

    for name, inv_info in T0_INVARIANTS.items():
        authoritative_path = root_dir / inv_info["authoritative"]

        # 1. Assert authoritative file exists
        assert authoritative_path.exists(), f"Authoritative implementation for {name} is missing at {inv_info['authoritative']}"

        # 2. Assert it contains the actual class definition
        content = authoritative_path.read_text(encoding="utf-8")
        assert inv_info["pattern"].search(content), f"Authoritative class for {name} not found in {inv_info['authoritative']}"

        # 3. Assert no duplicate definitions exist in active code paths
        duplicates = []
        for file_path in root_dir.glob("trading_bot/**/*.py"):
            if any(p in str(file_path) for p in ["_archive", "tests", "sandbox", "safety"]):
                continue
            if str(file_path.relative_to(root_dir)) == inv_info["authoritative"]:
                continue

            try:
                file_content = file_path.read_text(encoding="utf-8")
                if inv_info["pattern"].search(file_content):
                    duplicates.append(str(file_path.relative_to(root_dir)))
            except Exception:
                continue

        assert len(duplicates) == 0, f"⚠️ Multiple duplicate implementations of Tier-0 subsystem '{name}' found at: {duplicates}. The system must enforce exactly one authoritative implementation."


def test_repository_security_policy():
    """Enforce security policy: recursively scan active production codebase to reject unapproved unsafe patterns."""
    root_dir = Path(__file__).resolve().parents[2]
    violations = []

    for file_path in root_dir.glob("trading_bot/**/*.py"):
        # Skip archive, tests, or legacy directories, sandbox executors, and safety checkers themselves
        if any(p in str(file_path) for p in ["_archive", "tests", "sandbox", "safety", "safety_scanner", "safe_eval", "improvement_agent"]):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue
            # Skip method/function definitions named eval
            if "def eval(" in line or "def eval " in line:
                continue
            # Skip string literal assertions or scanning rules inside detectors
            if any(kw in line for kw in ["dangerous_keywords", "forbidden_patterns", "forbidden_symbols", "pattern_name"]):
                continue
            # Skip string definitions/comparisons checking for eval/exec
            if any(kw in line for kw in ['"eval("', '"exec("', "'eval('", "'exec('"]):
                continue

            for pattern_name, pattern in FORBIDDEN_PATTERNS.items():
                if pattern.search(line):
                    # Filter out allowed self-assembly code synthesis or advanced executors
                    if "advanced_ai" in str(file_path) or "self_assembly" in str(file_path) or "aads" in str(file_path) or "distributed/parallel_backtester" in str(file_path):
                        continue
                    # Filter out clean screen commands
                    if "pipeline_approval.py" in str(file_path) and "os.system" in line:
                        continue

                    violations.append({
                        "file": str(file_path.relative_to(root_dir)),
                        "line": idx,
                        "type": pattern_name,
                        "content": line.strip()
                    })

    assert len(violations) == 0, f"Security Policy Violations found: {violations}"
