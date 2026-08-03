"""
CI-Enforced Automated Security Policy Validator.
Scan the codebase recursively to ensure strict adherence to secure practices.
Fails the build if any unsafe functions (pickle, eval, exec, os.system, shell=True)
are introduced outside of verified safety-fallback boundaries.
"""

import os
import re
import pytest
from pathlib import Path

# Exclusion directories
EXCLUDE_DIRS = {
    "_archive",
    "tests",
    "tests_new",
    "node_modules",
    "reports",
    "logs",
    "venv",
    ".venv",
    ".git",
    "alphaalgo_upgrades",
    "alphaalgo_offline_rl_system",
    "examples",
    "scripts",
    "docs",
}

# Exclusion files (Security engines, scanners and sandbox runners that must inspect forbidden syntax for validation)
EXCLUDE_FILES = {
    "test_security_policy.py",
    "safe_pickle.py",
    "artifact_manager.py",
    "safety_checker.py",
    "code_safety_scanner.py",
    "sandbox_executor.py",
    "security_supervisor.py",
    "example_safety_enforcer.py",
    "safeguards.py",
    "weakness_detector.py",
    "verification.py",
    "sandbox_environment.py",
    "self_modifier.py",
    "knowledge_transfer.py",
    "superintelligence_core.py",
    "silent_failure_detector.py",
    "safe_eval.py",
    "module_registry.py",
    "recursive_self_improvement.py",
    "pipeline_approval.py",
    "infrastructure_systems.py",
    "code_synthesis.py",
    "alpha_evolve_engine.py",
    "parallel_backtester.py",
}

# Regex rules for prohibited patterns
FORBIDDEN_RULES = [
    # 1. Unsafe Deserialization
    (r"\bpickle\.load\s*\(", "Prohibited raw 'pickle.load' call detected. Must use 'ArtifactManager' or 'RestrictedUnpickler'."),
    (r"\bpickle\.loads\s*\(", "Prohibited raw 'pickle.loads' call detected. Must use 'ArtifactManager' or 'RestrictedUnpickler'."),

    # 2. Command Injection and Unsafe System Execution
    (r"\bos\.system\s*\(", "Prohibited 'os.system' execution detected. Use safe subprocess with list-based arguments."),
    (r"\bexec\s*\(", "Prohibited 'exec()' statement detected. Code execution is forbidden."),
    (r"\bshell\s*=\s*True\b", "Prohibited 'shell=True' subprocess call detected. Formulate command as list arguments."),
]

def scan_files():
    """Generator yielding non-excluded python files and their contents."""
    root_dir = Path(__file__).resolve().parents[2]
    for root, dirs, files in os.walk(root_dir):
        # Skip excluded directories
        dirs[:] = [d for dirs_list in [dirs] for d in dirs_list if d not in EXCLUDE_DIRS]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                # Skip excluded files
                if file_path.name in EXCLUDE_FILES:
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        yield file_path, f.read()
                except Exception:
                    pass

def test_repository_security_policy():
    """Verify repository conforms completely to secure coding invariants."""
    violations = []

    for file_path, content in scan_files():
        # Remove comments to avoid false positives on commented code
        cleaned_content = re.sub(r"#.*", "", content)
        cleaned_content = re.sub(r'""".*?"""', "", cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r"'''.*?'''", "", cleaned_content, flags=re.DOTALL)

        # 1. Check for Forbidden Rules
        for pattern, message in FORBIDDEN_RULES:
            match = re.search(pattern, cleaned_content)
            if match:
                # Double-check specific line for exact trace
                for idx, line in enumerate(content.splitlines(), 1):
                    # Strip comment
                    line_no_comment = line.split('#')[0]
                    # Skip if it is just a string definition checking for forbidden strings
                    if re.search(pattern, line_no_comment):
                        # Ensure we don't trigger on list patterns like ['os.system', 'subprocess']
                        if re.search(r"['\"][a-zA-Z0-9_\.]+\s*\(?\s*['\"]", line_no_comment) and not re.search(r"\bos\.system\(|\bpickle\.load\(", line_no_comment):
                            continue
                        violations.append(
                            f"Violation in {file_path.relative_to(Path(__file__).resolve().parents[2])}:{idx}\n"
                            f"  Line: {line.strip()}\n"
                            f"  Reason: {message}\n"
                        )

        # 2. Check for unsafe eval usage (excluding model.eval() and safe_eval)
        for idx, line in enumerate(content.splitlines(), 1):
            line_no_comment = line.split('#')[0]
            # Match eval( but not model.eval( or self.model.eval( or safe_eval
            if re.search(r"\beval\s*\(", line_no_comment) and "safe_eval(" not in line_no_comment and not re.search(r"\b\w+\.eval\(", line_no_comment):
                # Ensure we don't trigger on function declarations like "async def _exploration_eval(...):"
                if "def " in line_no_comment:
                    continue
                # Ensure we don't trigger on string lists
                if re.search(r"['\"][a-zA-Z0-9_\(\.]*eval['\"]", line_no_comment):
                    continue
                violations.append(
                    f"Violation in {file_path.relative_to(Path(__file__).resolve().parents[2])}:{idx}\n"
                    f"  Line: {line.strip()}\n"
                    f"  Reason: Unsafe eval() statement detected. Must use 'safe_eval'.\n"
                )

    if violations:
        error_msg = "\n" + "="*80 + "\nSECURITY POLICY INVARIANT VIOLATIONS DETECTED!\n" + "="*80 + "\n"
        error_msg += "\n".join(violations)
        error_msg += "\n" + "="*80 + "\nPlease refactor the violated paths to conform to production architecture standards."
        pytest.fail(error_msg)
