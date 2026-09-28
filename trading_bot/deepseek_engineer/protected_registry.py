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

    def _is_protected(self, normalized: str) -> bool:
        """Component-aware match: multi-component patterns must align to path
        component boundaries; single-component patterns match within a
        component (errs toward denial, e.g. 'secret' matches secrets.py)."""
        parts = [p for p in normalized.split("/") if p]
        for pat in self.IMMUTABLE_PROTECTED_PATTERNS:
            if "/" in pat:
                pat_parts = pat.split("/")
                if any(
                    parts[i:i + len(pat_parts)] == pat_parts
                    for i in range(len(parts) - len(pat_parts) + 1)
                ):
                    return True
            elif any(pat in part for part in parts):
                return True
        return False

    def check_access(self, path: str, access_type: AccessType) -> AccessDecision:
        normalized = path.replace("\\", "/")
        protected = self._is_protected(normalized)
        if access_type == AccessType.READ:
            return AccessDecision(path, access_type, True, False)
        # Fail closed: immutable paths are denied outright. requires_approval
        # stays set so callers and audit logs still see WHY it was denied.
        return AccessDecision(
            path,
            access_type,
            allowed=not protected,
            requires_approval=protected,
            reason="immutable protected path" if protected else "",
        )
