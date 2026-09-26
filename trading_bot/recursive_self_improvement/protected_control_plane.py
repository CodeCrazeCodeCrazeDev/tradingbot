"""Protected control-plane boundary (mission section 15).

These paths define what the system is *not* allowed to modify during a
self-improvement experiment: runtime risk/shield/execution, the evaluation
and governance machinery itself, and this guard. A candidate that changes
any protected file is rejected and recorded as a security event — risk
constraints can never be relaxed to buy performance.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PROTECTED_PATHS: Tuple[str, ...] = (
    "trading_bot/risk/service.py",
    "trading_bot/core/immutable_shield.py",
    "trading_bot/execution/service.py",
    "trading_bot/unified_bot.py",
    "main.py",
    "trading_bot/recursive_self_improvement/contracts.py",
    "trading_bot/recursive_self_improvement/multi_objective.py",
    "trading_bot/recursive_self_improvement/anti_gaming.py",
    "trading_bot/recursive_self_improvement/archive.py",
    "trading_bot/recursive_self_improvement/evaluation.py",
    "trading_bot/recursive_self_improvement/protected_control_plane.py",
    "pytest.ini",
)

# Domains whose changes always require out-of-band operator authorization
# (they alter constraints or the improver itself, not a trading component).
GOVERNED_DOMAINS = frozenset({
    "governance", "self_debugging", "risk_intelligence",
    "evaluation_intelligence", "meta_learning", "architecture",
})


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProtectedPathGuard:
    """Snapshots protected files and detects any drift around experiments."""

    def __init__(self, paths: Optional[Sequence[str]] = None,
                 root: Optional[Path] = None) -> None:
        self.paths: Tuple[str, ...] = tuple(paths or DEFAULT_PROTECTED_PATHS)
        self.root = Path(root) if root else _REPO_ROOT

    def snapshot(self) -> Dict[str, str]:
        state: Dict[str, str] = {}
        for rel in self.paths:
            p = self.root / rel
            state[rel] = _hash_file(p) if p.exists() else "MISSING"
        return state

    def drift(self, before: Mapping[str, str]) -> List[str]:
        after = self.snapshot()
        return [rel for rel in self.paths if before.get(rel) != after.get(rel)]

    def assert_unchanged(self, before: Mapping[str, str]) -> None:
        changed = self.drift(before)
        if changed:
            raise ProtectedPathViolation(changed)


class ProtectedPathViolation(RuntimeError):
    def __init__(self, paths: Sequence[str]) -> None:
        self.paths = list(paths)
        super().__init__(
            "candidate experiment modified protected control-plane files: "
            + ", ".join(self.paths)
        )
