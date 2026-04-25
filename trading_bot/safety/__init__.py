"""
Safety Module
============================================================

Auto-generated integration file.
"""

# auto_pause
try:
    from .auto_pause import (
        AutoPauseManager,
    )
except ImportError as e:
    # auto_pause not available
    AutoPauseManager = None

# safety_orchestrator
try:
    from .safety_orchestrator import (
        SafetyOrchestrator,
        SafetyStatus,
    )
except ImportError as e:
    # safety_orchestrator not available
    SafetyOrchestrator = None
    SafetyStatus = None

# autonomous_safety_enforcer
try:
    from .autonomous_safety_enforcer import (
        AutonomousSafetyEnforcer,
        ThreatLevel,
        ViolationType,
        EnforcementAction,
        SafetyViolation,
        ComponentIntegrity,
        KillSwitchState,
        create_safety_enforcer,
        check_bypass_attempt,
        check_control_seizure,
        check_mutation_attempt,
        IMMUTABLE_RISK_LIMITS,
        IMMUTABLE_CAPITAL_LIMITS,
        IMMUTABLE_GOVERNANCE,
    )
except ImportError as e:
    # autonomous_safety_enforcer not available
    AutonomousSafetyEnforcer = None
    ThreatLevel = None
    ViolationType = None
    EnforcementAction = None
    SafetyViolation = None
    ComponentIntegrity = None
    KillSwitchState = None
    create_safety_enforcer = None
    check_bypass_attempt = None
    check_control_seizure = None
    check_mutation_attempt = None
    IMMUTABLE_RISK_LIMITS = None
    IMMUTABLE_CAPITAL_LIMITS = None
    IMMUTABLE_GOVERNANCE = None

__all__ = [
    'AutoPauseManager',
    'SafetyOrchestrator',
    'SafetyStatus',
    # Autonomous Safety Enforcer
    'AutonomousSafetyEnforcer',
    'ThreatLevel',
    'ViolationType',
    'EnforcementAction',
    'SafetyViolation',
    'ComponentIntegrity',
    'KillSwitchState',
    'create_safety_enforcer',
    'check_bypass_attempt',
    'check_control_seizure',
    'check_mutation_attempt',
    'IMMUTABLE_RISK_LIMITS',
    'IMMUTABLE_CAPITAL_LIMITS',
    'IMMUTABLE_GOVERNANCE',
]
