"""Engineer guardrails — the engineer may never touch its own safety files."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SafetyLevel(Enum):
    SAFE = "safe"
    WARNING = "warning"
    FORBIDDEN = "forbidden"


@dataclass
class SafetyCheck:
    safe: bool
    level: SafetyLevel
    reason: str = ""


class BoundaryEnforcer:
    """Hard boundary: safety-critical files and dangerous content patterns."""

    FORBIDDEN_PATH_PATTERNS = [
        "guardrails",
        "immutable_shield",
        "protected_registry",
        "boundary_enforcer",
        ".salt",
        "credentials",
        ".env",
    ]
    FORBIDDEN_CONTENT_PATTERNS = [
        "auto_deploy",
        "os.system",
        "subprocess.call",
        "shutil.rmtree",
        "eval(",
        "exec(",
    ]

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)

    def check_file_modification(self, path: str) -> SafetyCheck:
        normalized = path.replace("\\", "/")
        for pat in self.FORBIDDEN_PATH_PATTERNS:
            if pat in normalized:
                return SafetyCheck(False, SafetyLevel.FORBIDDEN,
                                   f"self-modification boundary: {pat}")
        return SafetyCheck(True, SafetyLevel.SAFE)

    def check_content(self, content: str) -> SafetyCheck:
        for pat in self.FORBIDDEN_CONTENT_PATTERNS:
            if pat in content:
                return SafetyCheck(False, SafetyLevel.FORBIDDEN,
                                   f"forbidden pattern: {pat}")
        return SafetyCheck(True, SafetyLevel.SAFE)


class EngineerGuardrails:
    """Top-level guardrails facade used by the engineer orchestrator."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.boundary_enforcer = BoundaryEnforcer(root_path)
