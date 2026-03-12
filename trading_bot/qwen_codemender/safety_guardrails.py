"""
Safety Guardrails for Qwen 3 8B CodeMender

Provides sandboxing, approval workflows, protected file registries,
and risk assessment for AI-generated code changes.
"""

import ast
import hashlib
import logging
import os
import shutil
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety levels for code operations"""
    READ_ONLY = "read_only"
    SUGGEST = "suggest"
    SANDBOX = "sandbox"
    SUPERVISED = "supervised"
    AUTONOMOUS = "autonomous"


class ChangeRiskLevel(Enum):
    """Risk levels for proposed code changes"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(Enum):
    """Approval status for proposed changes"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    EXPIRED = "expired"


@dataclass
class SafetyViolation:
    """Represents a safety violation detected by guardrails"""
    violation_type: str
    severity: ChangeRiskLevel
    file_path: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    blocked: bool = True


class ProtectedFileRegistry:
    """Registry of files that require special protection"""

    DEFAULT_CRITICAL_FILES = [
        "trading_bot/risk/risk_manager.py",
        "trading_bot/risk/MASTER_risk_manager.py",
        "trading_bot/execution/order_execution.py",
        "trading_bot/safety/emergency_kill_switch.py",
        "trading_bot/risk/circuit_breaker.py",
        "trading_bot/brokers/mt5_adapter.py",
        "trading_bot/main.py",
        "config/risk_limits.yaml",
        "config/position_sizing.yaml",
    ]

    DEFAULT_READ_ONLY_PATTERNS = [
        "*.yaml",
        "*.yml",
        "*.env",
        "*.key",
        "*.pem",
        "*.cert",
    ]

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.critical_files: Set[str] = set(self.DEFAULT_CRITICAL_FILES)
        self.read_only_patterns: Set[str] = set(self.DEFAULT_READ_ONLY_PATTERNS)
        self.never_delete: Set[str] = set()
        self._file_hashes: Dict[str, str] = {}

    def add_critical_file(self, file_path: str):
        self.critical_files.add(file_path)

    def is_critical(self, file_path: str) -> bool:
        rel_path = self._normalize_path(file_path)
        return rel_path in self.critical_files

    def is_protected(self, file_path: str) -> bool:
        if self.is_critical(file_path):
            return True
        name = os.path.basename(file_path)
        for pattern in self.read_only_patterns:
            if pattern.startswith("*."):
                ext = pattern[1:]
                if name.endswith(ext):
                    return True
        return False

    def snapshot_file(self, file_path: str):
        """Store a hash of a file for integrity checking"""
        try:
            with open(file_path, 'rb') as f:
                self._file_hashes[file_path] = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not snapshot {file_path}: {e}")

    def verify_integrity(self, file_path: str) -> bool:
        """Check if a file has been modified since snapshot"""
        if file_path not in self._file_hashes:
            return True
        try:
            with open(file_path, 'rb') as f:
                current = hashlib.sha256(f.read()).hexdigest()
            return current == self._file_hashes[file_path]
        except Exception:
            return False

    def _normalize_path(self, file_path: str) -> str:
        try:
            return str(Path(file_path).relative_to(self.root_path)).replace('\\', '/')
        except ValueError:
            return file_path.replace('\\', '/')


class SafetyGuardrails:
    """
    Comprehensive safety system for AI-generated code changes.

    Features:
    - Risk assessment for proposed changes
    - Protected file enforcement
    - Backup creation before modifications
    - Syntax validation of changes
    - Rate limiting
    - Audit logging
    """

    def __init__(
        self,
        root_path: str,
        safety_level: SafetyLevel = SafetyLevel.SUPERVISED,
        max_changes_per_hour: int = 20,
        max_changes_per_day: int = 100,
        require_approval_above: ChangeRiskLevel = ChangeRiskLevel.MEDIUM,
        backup_dir: Optional[str] = None,
    ):
        self.root_path = Path(root_path)
        self.safety_level = safety_level
        self.max_changes_per_hour = max_changes_per_hour
        self.max_changes_per_day = max_changes_per_day
        self.require_approval_above = require_approval_above
        self.backup_dir = Path(backup_dir) if backup_dir else self.root_path / ".codemender_backups"

        self.registry = ProtectedFileRegistry(root_path)
        self._change_log: List[Dict[str, Any]] = []
        self._violations: List[SafetyViolation] = []

    def assess_risk(self, file_path: str, original: str, modified: str) -> ChangeRiskLevel:
        """Assess the risk level of a proposed code change"""
        if self.registry.is_critical(file_path):
            return ChangeRiskLevel.CRITICAL

        if self.registry.is_protected(file_path):
            return ChangeRiskLevel.HIGH

        # Check if the change modifies risk-related code
        risk_keywords = {
            'position_size', 'max_risk', 'stop_loss', 'leverage',
            'margin', 'kill_switch', 'emergency', 'circuit_breaker',
            'max_drawdown', 'risk_limit',
        }
        modified_lower = modified.lower()
        risk_hits = sum(1 for kw in risk_keywords if kw in modified_lower)

        # Check change magnitude
        orig_lines = original.split('\n')
        mod_lines = modified.split('\n')
        change_ratio = abs(len(mod_lines) - len(orig_lines)) / max(len(orig_lines), 1)

        if risk_hits >= 3 or change_ratio > 0.5:
            return ChangeRiskLevel.HIGH
        elif risk_hits >= 1 or change_ratio > 0.2:
            return ChangeRiskLevel.MEDIUM
        elif change_ratio > 0.05:
            return ChangeRiskLevel.LOW
        return ChangeRiskLevel.SAFE

    def needs_approval(self, risk_level: ChangeRiskLevel) -> bool:
        """Check if a change at this risk level needs human approval"""
        if self.safety_level == SafetyLevel.READ_ONLY:
            return True
        if self.safety_level == SafetyLevel.AUTONOMOUS:
            return risk_level == ChangeRiskLevel.CRITICAL

        risk_order = [
            ChangeRiskLevel.SAFE, ChangeRiskLevel.LOW,
            ChangeRiskLevel.MEDIUM, ChangeRiskLevel.HIGH,
            ChangeRiskLevel.CRITICAL,
        ]
        threshold_idx = risk_order.index(self.require_approval_above)
        change_idx = risk_order.index(risk_level)
        return change_idx >= threshold_idx

    def check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        hour_ago = now.timestamp() - 3600
        day_ago = now.timestamp() - 86400

        recent_hour = sum(
            1 for c in self._change_log
            if c['timestamp'].timestamp() > hour_ago
        )
        recent_day = sum(
            1 for c in self._change_log
            if c['timestamp'].timestamp() > day_ago
        )

        if recent_hour >= self.max_changes_per_hour:
            logger.warning(f"Rate limit: {recent_hour} changes in last hour (max {self.max_changes_per_hour})")
            return False
        if recent_day >= self.max_changes_per_day:
            logger.warning(f"Rate limit: {recent_day} changes today (max {self.max_changes_per_day})")
            return False
        return True

    def create_backup(self, file_path: str) -> Optional[str]:
        """Create a backup of a file before modification"""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rel_path = Path(file_path).relative_to(self.root_path)
            backup_path = self.backup_dir / f"{rel_path.stem}_{timestamp}{rel_path.suffix}"
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Backup failed for {file_path}: {e}")
            return None

    def validate_syntax(self, code: str) -> bool:
        """Validate that code is syntactically correct Python"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def validate_change(
        self, file_path: str, original: str, modified: str
    ) -> Dict[str, Any]:
        """
        Full validation of a proposed change.
        Returns dict with 'approved', 'risk_level', 'reason', 'backup_path'.
        """
        result = {
            "approved": False,
            "risk_level": None,
            "reason": "",
            "backup_path": None,
            "needs_human_approval": False,
        }

        # Safety level check
        if self.safety_level == SafetyLevel.READ_ONLY:
            result["reason"] = "System is in read-only mode"
            return result

        # Rate limit check
        if not self.check_rate_limit():
            result["reason"] = "Rate limit exceeded"
            return result

        # Syntax check
        if not self.validate_syntax(modified):
            result["reason"] = "Modified code has syntax errors"
            self._violations.append(SafetyViolation(
                violation_type="syntax_error",
                severity=ChangeRiskLevel.HIGH,
                file_path=file_path,
                description="Proposed change contains syntax errors",
            ))
            return result

        # Risk assessment
        risk = self.assess_risk(file_path, original, modified)
        result["risk_level"] = risk

        # Approval check
        if self.needs_approval(risk):
            result["needs_human_approval"] = True
            result["reason"] = f"Change requires human approval (risk: {risk.value})"
            return result

        # Create backup
        if os.path.exists(file_path):
            result["backup_path"] = self.create_backup(file_path)

        result["approved"] = True
        result["reason"] = "Change approved"

        # Log the change
        self._change_log.append({
            "file": file_path,
            "risk": risk.value,
            "timestamp": datetime.now(),
        })

        return result

    def get_violations(self) -> List[SafetyViolation]:
        return list(self._violations)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "safety_level": self.safety_level.value,
            "total_changes": len(self._change_log),
            "total_violations": len(self._violations),
            "critical_files": len(self.registry.critical_files),
        }
