"""
Safety & Alignment - Safe AI Systems
=====================================

Implements safety and alignment mechanisms:
- Harm Monitor: Detect harmful behaviors
- Alignment Checker: Ensure goal alignment
- Robustness Validator: Test against adversarial conditions
- Ethical Constraints: Enforce ethical boundaries
- Human Override: Always-available human control
- Audit Logger: Complete audit trail
"""

from .harm_monitor import HarmMonitor, HarmType, HarmAlert, RiskLevel
from .alignment_checker import AlignmentChecker, AlignmentStatus, GoalAlignment
from .human_override import HumanOverride, OverrideAction, OverrideResult
from .audit_logger import AuditLogger, AuditEvent, AuditTrail

__all__ = [
    "HarmMonitor",
    "HarmType",
    "HarmAlert",
    "RiskLevel",
    "AlignmentChecker",
    "AlignmentStatus",
    "GoalAlignment",
    "HumanOverride",
    "OverrideAction",
    "OverrideResult",
    "AuditLogger",
    "AuditEvent",
    "AuditTrail",
]
