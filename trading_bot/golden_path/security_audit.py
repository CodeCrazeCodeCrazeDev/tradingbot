"""Local secret hygiene checks that never print secret values."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Union


DEFAULT_SECRET_FILENAMES = (
    ".env",
    ".key",
    ".salt",
    ".secret_key",
    "secrets.json",
    "credentials.json",
)
SECRET_PATTERNS = ("*.key", "*.pem", "*.p12", "*.pfx", "*.token", "*.secret", "*.vault")
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "htmlcov", "node_modules"}


@dataclass(frozen=True)
class SecretAuditFinding:
    path: str
    severity: str
    message: str
    tracked_by_git: bool = False
    reason: str = "filename"


def audit_local_secrets(
    root: Union[str, Path],
    *,
    filenames: Sequence[str] = DEFAULT_SECRET_FILENAMES,
    scan_patterns: Sequence[str] = SECRET_PATTERNS,
    include_entropy_scan: bool = True,
) -> List[SecretAuditFinding]:
    """Find local secret files and report whether Git tracks them."""

    root_path = Path(root)
    findings: List[SecretAuditFinding] = []
    tracked = _git_tracked_files(root_path)

    candidates = list(_iter_secret_candidates(root_path, filenames, scan_patterns))
    seen = set()
    for path in candidates:
        if path in seen or not path.exists() or not path.is_file():
            continue
        seen.add(path)
        findings.append(_build_finding(root_path, path, tracked, reason="filename"))

    if include_entropy_scan:
        for path in _iter_entropy_candidates(root_path):
            if path in seen:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if _looks_like_secret_content(content):
                seen.add(path)
                findings.append(_build_finding(root_path, path, tracked, reason="content"))

    return findings


def _iter_secret_candidates(
    root: Path,
    filenames: Sequence[str],
    scan_patterns: Sequence[str],
) -> Iterable[Path]:
    for name in filenames:
        yield root / name
    for pattern in scan_patterns:
        yield from root.rglob(pattern)


def _iter_entropy_candidates(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.stat().st_size > 256_000:
            continue
        if path.suffix.lower() not in {".env", ".json", ".yaml", ".yml", ".toml", ".txt", ".cfg", ".ini"}:
            continue
        yield path


def _build_finding(root: Path, path: Path, tracked: set[str], *, reason: str) -> SecretAuditFinding:
    rel = path.relative_to(root).as_posix()
    tracked_by_git = rel in tracked
    severity = "critical" if tracked_by_git else "warning"
    if tracked_by_git:
        message = "secret-like file is tracked by Git"
    elif reason == "content":
        message = "file contains secret-like keys or high-entropy values"
    else:
        message = "secret-like file exists locally"
    return SecretAuditFinding(
        path=str(path),
        severity=severity,
        message=message,
        tracked_by_git=tracked_by_git,
        reason=reason,
    )


def _looks_like_secret_content(content: str) -> bool:
    lowered = content.lower()
    secret_keys = (
        "api_key",
        "apikey",
        "secret",
        "password",
        "private_key",
        "access_token",
        "refresh_token",
        "client_secret",
    )
    if any(key in lowered for key in secret_keys):
        return True

    for token in content.replace('"', " ").replace("'", " ").split():
        cleaned = token.strip(",:;[]{}()")
        if len(cleaned) >= 32 and _shannon_entropy(cleaned) >= 4.2:
            return True
    return False


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    entropy = 0.0
    for char in set(value):
        probability = value.count(char) / len(value)
        entropy -= probability * __import__("math").log2(probability)
    return entropy


def _git_tracked_files(root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(root),
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except Exception:
        return set()
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}
