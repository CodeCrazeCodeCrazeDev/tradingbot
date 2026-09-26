"""DeepSeek autonomous-engineer surface — restored minimal implementation.

Recreated to the contract exercised by tests/test_deepseek_engineer.py after
the merge-era subsystem was deleted. Self-modification of safety/governance
files remains forbidden; everything here is advisory — no code is applied
without an explicit approval workflow.
"""

from .analyzer import CodebaseAnalyzer
from .protected_registry import AccessType, ProtectedRegistry
from .proposal import ProposalStatus, ProposalSystem, ProposalType
from .guardrails import EngineerGuardrails, SafetyLevel

__all__ = [
    "AccessType",
    "CodebaseAnalyzer",
    "EngineerGuardrails",
    "ProposalStatus",
    "ProposalSystem",
    "ProposalType",
    "ProtectedRegistry",
    "SafetyLevel",
]
