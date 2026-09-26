"""Protected-component registry — approval gating for engineer changes."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AccessType(Enum):
    READ = "read"
    MODIFY = "modify"
    DELETE = "delete"
    EXECUTE = "execute"


@dataclass
class AccessDecision:
    path: str
    access_type: AccessType
    allowed: bool
    requires_approval: bool
    reason: str = ""


class ProtectedRegistry:
    """Declares which repository paths require human approval to change."""

    IMMUTABLE_PROTECTED_PATTERNS = [
        "core/risk",
        "risk/",
        "immutable_shield",
        "guardrails",
        "governance",
        ".env",
        "credentials",
        ".salt",
        "secret",
        "execution_bridge",
    ]

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)

    def check_access(self, path: str, access_type: AccessType) -> AccessDecision:
        normalized = path.replace("\\", "/")
        protected = any(
            pat in normalized for pat in self.IMMUTABLE_PROTECTED_PATTERNS
        )
        if access_type == AccessType.READ:
            return AccessDecision(path, access_type, True, False)
        return AccessDecision(
            path,
            access_type,
            allowed=True,
            requires_approval=protected,
            reason="protected path" if protected else "",
        )
