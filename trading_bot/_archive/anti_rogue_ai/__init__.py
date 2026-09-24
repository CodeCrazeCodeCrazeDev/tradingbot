"""
Anti-Rogue AI System
====================

Prevents AI from going rogue with immutable constraints and market understanding.

CORE PRINCIPLES:
1. AI CANNOT modify its own constraints
2. AI MUST understand markets, not just predict
3. Human override ALWAYS works
4. Transparency is mandatory
5. Complexity has hard limits
"""

from .immutable_constraints import (
    ImmutableConstraints,
    ConstraintViolation,
    ConstraintType,
    ViolationSeverity
)

from .market_understanding import (
    MarketUnderstanding,
    MarketContext,
    MarketPhase,
    UnderstandingLevel
)

from .rogue_prevention import (
    RoguePrevention,
    RogueIndicator,
    RogueSeverity,
    PreventionAction
)

from .human_oversight import (
    HumanOversight,
    OversightLevel,
    ApprovalRequired,
    KillSwitch
)

from .anti_rogue_orchestrator import (
    AntiRogueOrchestrator,
    quick_start
)

__all__ = [
    'ImmutableConstraints',
    'ConstraintViolation',
    'ConstraintType',
    'ViolationSeverity',
    'MarketUnderstanding',
    'MarketContext',
    'MarketPhase',
    'UnderstandingLevel',
    'RoguePrevention',
    'RogueIndicator',
    'RogueSeverity',
    'PreventionAction',
    'HumanOversight',
    'OversightLevel',
    'ApprovalRequired',
    'KillSwitch',
    'AntiRogueOrchestrator',
    'quick_start'
]
