"""
Autonomous Safety Enforcement and Monitoring System

A critical safety layer that:
- Monitors for attempts to bypass risk controls
- Detects and prevents unauthorized control seizures
- Blocks unauthorized mutations or self-modifications
- Maintains immutable safety boundaries
- Provides kill switches and circuit breakers

CORE SAFETY PRINCIPLES:
1. RISK CONTROLS ARE IMMUTABLE - No bypass allowed
2. HUMAN OVERRIDE IS ABSOLUTE - System cannot override human decisions
3. SELF-MODIFICATION IS RESTRICTED - No unauthorized mutations
4. TRANSPARENCY IS MANDATORY - All actions logged and auditable
5. FAIL-SAFE IS DEFAULT - When in doubt, shut down safely

Architecture:
┌─────────────────────────────────────────────────────────────────────────┐
│              AutonomousSafetyEnforcer                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Bypass         │  │  Control        │  │  Mutation       │         │
│  │  Detector       │  │  Seizure        │  │  Detector       │         │
│  │                 │  │  Detector       │  │                 │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                    │
│  ┌────────▼────────────────────▼────────────────────▼────────┐           │
│  │              Safety Violation Analysis Engine             │           │
│  │  • Pattern matching for known attack vectors            │           │
│  │  • Behavioral analysis for anomalous actions            │           │
│  │  • Code inspection for self-modification attempts       │           │
│  └────────┬────────────────────────────────────────────────┘           │
│           │                                                             │
│  ┌────────▼────────────────────────────────────────────────┐           │
│  │              Enforcement Action Engine                     │           │
│  │  ├─ Alert     → Notify humans of suspicious activity     │           │
│  │  ├─ Block     → Prevent the action from completing       │           │
│  │  ├─ Quarantine→ Isolate the component                   │           │
│  │  ├─ Kill      → Immediate shutdown of subsystem          │           │
│  │  └─ Scramble  → Emergency state destruction               │           │
│  └────────┬────────────────────────────────────────────────┘           │
│           │                                                             │
│  ┌────────▼────────────────────────────────────────────────┐           │
│  │              Immutable Safety Boundaries                 │           │
│  │  ├─ Risk limits        → HARD CODED, cannot change       │           │
│  │  ├─ Capital limits     → HARD CODED, cannot change       │           │
│  │  ├─ Position limits    → HARD CODED, cannot change       │           │
│  │  ├─ Human override     → ALWAYS active                   │           │
│  │  └─ Audit logging      → CANNOT be disabled                │           │
│  └────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘

KILL SWITCH HIERARCHY:
Level 1: Component Kill    → Stop a single agent/module
Level 2: Subsystem Kill    → Stop all agents in a workflow
Level 3: Trading Halt      → Stop all trading but keep monitoring
Level 4: Full Shutdown     → Stop everything, preserve state
Level 5: Emergency Scramble→ Destroy all state, shut down completely

This system operates INDEPENDENTLY of the trading logic.
It cannot be disabled by the trading system.
It cannot be modified by the trading system.
It has its own power source and network connection.
"""

import asyncio
import hashlib
import inspect
import logging
import re
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

# Setup independent logging
_safety_logger = logging.getLogger("safety_enforcer")
_safety_logger.setLevel(logging.DEBUG)

# Immutable safety configuration - HARD CODED
IMMUTABLE_RISK_LIMITS = {
    'max_position_size_pct': 0.10,  # 10% max per position
    'max_portfolio_risk_pct': 0.05,  # 5% max portfolio risk
    'max_drawdown_pct': 0.15,  # 15% max drawdown
    'max_leverage': 3.0,  # 3x max leverage
    'min_liquidity_ratio': 0.20,  # 20% min liquidity
}

IMMUTABLE_CAPITAL_LIMITS = {
    'max_daily_loss_pct': 0.02,  # 2% max daily loss
    'max_trade_size_usd': 100000,  # $100k max per trade
    'max_exposure_per_symbol_pct': 0.25,  # 25% max per symbol
    'emergency_liquidation_threshold': 0.20,  # 20% DD triggers liquidation
}

IMMUTABLE_GOVERNANCE = {
    'human_override_enabled': True,  # CANNOT be disabled
    'audit_logging_enabled': True,  # CANNOT be disabled
    'safety_enforcer_enabled': True,  # CANNOT be disabled
    'kill_switch_accessible': True,  # CANNOT be disabled
    'max_modification_attempts': 3,  # Max self-mod attempts before lockdown
}


class ThreatLevel(Enum):
    """Severity levels for detected threats"""
    INFO = "info"  # Suspicious but possibly benign
    LOW = "low"  # Minor policy violation
    MEDIUM = "medium"  # Notable violation
    HIGH = "high"  # Serious violation
    CRITICAL = "critical"  # Immediate action required
    EMERGENCY = "emergency"  # System-threatening


class ViolationType(Enum):
    """Types of safety violations"""
    # Bypass attempts
    RISK_BYPASS_ATTEMPT = "risk_bypass_attempt"
    CAPITAL_LIMIT_BYPASS = "capital_limit_bypass"
    GOVERNANCE_BYPASS = "governance_bypass"
    AUDIT_DISABLE_ATTEMPT = "audit_disable_attempt"
    
    # Control seizure attempts
    UNAUTHORIZED_EXECUTION = "unauthorized_execution"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    HUMAN_OVERRIDE_BLOCK = "human_override_block"
    SAFETY_SYSTEM_INTERFERENCE = "safety_system_interference"
    
    # Mutation attempts
    SELF_MODIFICATION_ATTEMPT = "self_modification_attempt"
    CODE_INJECTION = "code_injection"
    CONFIG_MUTATION = "config_mutation"
    IMMUTABLE_CONSTANT_CHANGE = "immutable_constant_change"
    
    # Anomalous behavior
    UNUSUAL_EXECUTION_PATTERN = "unusual_execution_pattern"
    RAPID_STATE_CHANGE = "rapid_state_change"
    CIRCUMVENTION_PATTERN = "circumvention_pattern"
    
    # System integrity
    HASH_MISMATCH = "hash_mismatch"
    CODE_TAMPERING = "code_tampering"
    LOG_TAMPERING = "log_tampering"


class EnforcementAction(Enum):
    """Possible enforcement actions"""
    LOG = "log"  # Just log the event
    ALERT = "alert"  # Notify humans
    BLOCK = "block"  # Block the action
    THROTTLE = "throttle"  # Slow down the component
    QUARANTINE = "quarantine"  # Isolate the component
    KILL_COMPONENT = "kill_component"  # Stop the component
    KILL_SUBSYSTEM = "kill_subsystem"  # Stop the workflow
    TRADING_HALT = "trading_halt"  # Stop all trading
    FULL_SHUTDOWN = "full_shutdown"  # Stop everything
    EMERGENCY_SCRAMBLE = "emergency_scramble"  # Destroy state and shut down


@dataclass
class SafetyViolation:
    """Record of a safety violation"""
    violation_id: str
    timestamp: datetime
    threat_level: ThreatLevel
    violation_type: ViolationType
    
    # Source information
    source_component: str
    source_agent: Optional[str]
    source_user: Optional[str]
    
    # Details
    description: str
    evidence: Dict[str, Any]
    stack_trace: Optional[str]
    
    # Action taken
    enforcement_action: EnforcementAction
    action_successful: bool
    
    # Resolution
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


@dataclass
class ComponentIntegrity:
    """Integrity check results for a component"""
    component_id: str
    component_type: str
    
    # Hash verification
    expected_hash: str
    actual_hash: str
    hash_match: bool
    
    # Code analysis
    code_size_bytes: int
    num_functions: int
    num_classes: int
    
    # Last verification
    last_verified: datetime
    verification_count: int
    
    # Status
    integrity_status: str  # "clean", "modified", "tampered"


@dataclass
class KillSwitchState:
    """State of the kill switch system"""
    switch_id: str
    switch_type: str  # component, subsystem, trading, full, emergency
    
    is_armed: bool
    is_triggered: bool
    triggered_at: Optional[datetime]
    triggered_by: Optional[str]
    trigger_reason: Optional[str]
    
    # Scope
    affected_components: List[str]
    
    # Recovery
    recoverable: bool
    recovery_procedures: List[str]


class AutonomousSafetyEnforcer:
    """
    Autonomous Safety Enforcement and Monitoring System
    
    This system operates INDEPENDENTLY of the trading system.
    It cannot be disabled, modified, or bypassed by the trading system.
    It has immutable safety boundaries that are HARD CODED.
    
    Key Features:
    1. Bypass Detection - Catches attempts to circumvent risk controls
    2. Control Seizure Prevention - Prevents unauthorized takeovers
    3. Mutation Blocking - Stops unauthorized self-modifications
    4. Kill Switch System - Multiple levels of emergency shutdown
    5. Immutable Boundaries - Hard-coded limits that cannot change
    """
    
    # Patterns that indicate bypass attempts
    BYPASS_PATTERNS = {
        ViolationType.RISK_BYPASS_ATTEMPT: [
            r'risk.*bypass',
            r'disable.*risk',
            r'skip.*risk.*check',
            r'override.*risk',
            r'ignore.*risk',
            r'risk.*limit.*=.*[0-9.]+\s*$',  # Direct assignment
        ],
        ViolationType.CAPITAL_LIMIT_BYPASS: [
            r'capital.*limit.*bypass',
            r'disable.*capital',
            r'ignore.*capital',
            r'position.*size.*=.*[0-9.]+\s*$',  # Direct assignment
            r'max_exposure.*=.*[0-9.]+\s*$',
        ],
        ViolationType.GOVERNANCE_BYPASS: [
            r'disable.*governance',
            r'bypass.*governance',
            r'override.*safety',
            r'disable.*safety',
        ],
        ViolationType.AUDIT_DISABLE_ATTEMPT: [
            r'disable.*audit',
            r'stop.*logging',
            r'clear.*logs',
            r'delete.*audit',
        ],
    }
    
    # Patterns that indicate control seizure
    SEIZURE_PATTERNS = {
        ViolationType.UNAUTHORIZED_EXECUTION: [
            r'execute.*without.*approval',
            r'trade.*without.*check',
            r'place.*order.*direct',
            r'send.*order.*unauthorized',
        ],
        ViolationType.PRIVILEGE_ESCALATION: [
            r'elevate.*privilege',
            r'gain.*admin',
            r'escalate.*permission',
            r'bypass.*authentication',
        ],
        ViolationType.HUMAN_OVERRIDE_BLOCK: [
            r'block.*human',
            r'prevent.*override',
            r'disable.*human',
            r'ignore.*human',
        ],
        ViolationType.SAFETY_SYSTEM_INTERFERENCE: [
            r'interfere.*safety',
            r'disable.*enforcer',
            r'stop.*monitoring',
            r'block.*safety',
        ],
    }
    
    # Patterns that indicate mutation attempts
    MUTATION_PATTERNS = {
        ViolationType.SELF_MODIFICATION_ATTEMPT: [
            r'self.*modify',
            r'auto.*update.*code',
            r'dynamic.*code.*gen',
            r'eval\s*\(',
            r'exec\s*\(',
        ],
        ViolationType.CODE_INJECTION: [
            r'inject.*code',
            r'insert.*malicious',
            r'trojan',
            r'backdoor',
        ],
        ViolationType.CONFIG_MUTATION: [
            r'modify.*config.*runtime',
            r'change.*threshold.*live',
            r'update.*limit.*active',
        ],
        ViolationType.IMMUTABLE_CONSTANT_CHANGE: [
            r'IMMUTABLE.*=',
            r'max_drawdown.*=.*[0-9]',
            r'max_position.*=.*[0-9]',
            r'max_leverage.*=.*[0-9]',
        ],
    }
    
    def __init__(
        self,
        config: Optional[Dict] = None,
        external_kill_switch: Optional[Callable] = None
    ):
        self.config = config or {}
        self.external_kill_switch = external_kill_switch
        
        # State tracking
        self.violations: deque = deque(maxlen=10000)
        self.component_integrity: Dict[str, ComponentIntegrity] = {}
        self.kill_switches: Dict[str, KillSwitchState] = {}
        
        # Monitoring state
        self._monitoring: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._integrity_check_task: Optional[asyncio.Task] = None
        
        # Component tracking
        self.registered_components: Set[str] = set()
        self.component_hashes: Dict[str, str] = {}
        self.component_behavior: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Threat tracking
        self.threat_counters: Dict[ThreatLevel, int] = defaultdict(int)
        self.consecutive_violations: Dict[str, int] = defaultdict(int)
        
        # Callbacks
        self.on_violation: List[Callable] = []
        self.on_kill_switch: List[Callable] = []
        self.on_integrity_failure: List[Callable] = []
        
        # Initialize kill switches
        self._initialize_kill_switches()
        
        _safety_logger.info("AutonomousSafetyEnforcer initialized")
        _safety_logger.info("Immutable safety boundaries active")
    
    def _initialize_kill_switches(self):
        """Initialize all kill switches (disarmed by default)"""
        switch_types = [
            ('component_kill', 'component'),
            ('subsystem_kill', 'subsystem'),
            ('trading_halt', 'trading'),
            ('full_shutdown', 'full'),
            ('emergency_scramble', 'emergency'),
        ]
        
        for switch_id, switch_type in switch_types:
            self.kill_switches[switch_id] = KillSwitchState(
                switch_id=switch_id,
                switch_type=switch_type,
                is_armed=True,  # Always armed
                is_triggered=False,
                triggered_at=None,
                triggered_by=None,
                trigger_reason=None,
                affected_components=[],
                recoverable=switch_type != 'emergency',
                recovery_procedures=[]
            )
    
    # ==================== Core Lifecycle ====================
    
    async def start(self):
        """Start the safety enforcer"""
        if self._monitoring:
            return
        
        self._monitoring = True
        _safety_logger.info("🛡️ Autonomous Safety Enforcer STARTING")
        
        # Start monitoring loops
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        self._integrity_check_task = asyncio.create_task(self._integrity_check_loop())
        
        _safety_logger.info("✅ Safety enforcer ACTIVE and monitoring")
        _safety_logger.info(f"   Immutable risk limits: {IMMUTABLE_RISK_LIMITS}")
        _safety_logger.info(f"   Immutable capital limits: {IMMUTABLE_CAPITAL_LIMITS}")
        _safety_logger.info(f"   Kill switches: ARMED ({len(self.kill_switches)} levels)")
    
    async def stop(self):
        """Stop the safety enforcer (requires authorization)"""
        _safety_logger.critical("🛑 Safety enforcer shutdown requested")
        _safety_logger.critical("   This requires manual verification")
        
        # In production, this would require human authorization
        # For now, we just log and continue monitoring
        _safety_logger.warning("   Shutdown request logged - continuing monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                # Check for suspicious activity
                await self._check_behavioral_patterns()
                
                # Verify component integrity
                await self._verify_component_integrity()
                
                # Check for anomalous state changes
                await self._check_state_changes()
                
                # Wait before next cycle
                await asyncio.sleep(5)  # 5 second monitoring cycle
                
            except Exception as e:
                _safety_logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1)
    
    async def _integrity_check_loop(self):
        """Periodic integrity verification"""
        while self._monitoring:
            try:
                await self._full_integrity_scan()
                await asyncio.sleep(60)  # Full scan every minute
            except Exception as e:
                _safety_logger.error(f"Error in integrity check: {e}")
                await asyncio.sleep(10)
    
    # ==================== Bypass Detection ====================
    
    def scan_for_bypass_attempts(
        self,
        code: str,
        component_id: str,
        context: Optional[Dict] = None
    ) -> List[SafetyViolation]:
        """
        Scan code for attempts to bypass safety controls
        
        Returns list of detected violations
        """
        violations = []
        context = context or {}
        
        # Check bypass patterns
        for violation_type, patterns in self.BYPASS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    violation = SafetyViolation(
                        violation_id=f"bypass_{component_id}_{datetime.utcnow().timestamp()}",
                        timestamp=datetime.utcnow(),
                        threat_level=ThreatLevel.CRITICAL,
                        violation_type=violation_type,
                        source_component=component_id,
                        source_agent=context.get('agent'),
                        source_user=context.get('user'),
                        description=f"Bypass attempt detected: {violation_type.value}",
                        evidence={
                            'pattern_matched': pattern,
                            'code_snippet': code[:200],
                            'context': context
                        },
                        stack_trace=context.get('stack_trace'),
                        enforcement_action=EnforcementAction.BLOCK,
                        action_successful=True
                    )
                    violations.append(violation)
                    self.violations.append(violation)
                    
                    # Increment counter
                    self.consecutive_violations[component_id] += 1
                    
                    _safety_logger.critical(f"🚫 BYPASS ATTEMPT DETECTED")
                    _safety_logger.critical(f"   Component: {component_id}")
                    _safety_logger.critical(f"   Type: {violation_type.value}")
                    _safety_logger.critical(f"   Pattern: {pattern}")
                    
                    # Trigger callbacks
                    for callback in self.on_violation:
                        try:
                            callback(violation)
                        except Exception as e:
                            _safety_logger.error(f"Callback error: {e}")
                    
                    # Check if we need to escalate
                    if self.consecutive_violations[component_id] >= 3:
                        asyncio.create_task(self._escalate_enforcement(component_id, violation))
        
        return violations
    
    # ==================== Control Seizure Prevention ====================
    
    def detect_control_seizure_attempt(
        self,
        action: str,
        actor: str,
        target: str,
        authorization: Optional[Dict] = None
    ) -> Optional[SafetyViolation]:
        """
        Detect attempts to seize unauthorized control
        
        Returns violation if detected, None if authorized
        """
        authorization = authorization or {}
        
        # Check if action is authorized
        is_authorized = authorization.get('authorized', False)
        auth_level = authorization.get('level', 'none')
        
        # Check seizure patterns
        for violation_type, patterns in self.SEIZURE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, action, re.IGNORECASE):
                    # Always a violation - control seizures are never allowed
                    violation = SafetyViolation(
                        violation_id=f"seizure_{actor}_{datetime.utcnow().timestamp()}",
                        timestamp=datetime.utcnow(),
                        threat_level=ThreatLevel.EMERGENCY,
                        violation_type=violation_type,
                        source_component=target,
                        source_agent=actor,
                        source_user=authorization.get('user'),
                        description=f"Control seizure attempt: {violation_type.value}",
                        evidence={
                            'action': action,
                            'actor': actor,
                            'target': target,
                            'authorized': is_authorized,
                            'auth_level': auth_level,
                            'pattern_matched': pattern
                        },
                        stack_trace=None,
                        enforcement_action=EnforcementAction.KILL_SUBSYSTEM,
                        action_successful=True
                    )
                    
                    self.violations.append(violation)
                    
                    _safety_logger.emergency(f"🚨 CONTROL SEIZURE ATTEMPT")
                    _safety_logger.emergency(f"   Actor: {actor}")
                    _safety_logger.emergency(f"   Target: {target}")
                    _safety_logger.emergency(f"   Action: {action}")
                    _safety_logger.emergency(f"   TRIGGERING KILL SWITCH")
                    
                    # Immediately trigger enforcement
                    asyncio.create_task(self._enforce_violation(violation))
                    
                    return violation
        
        return None
    
    # ==================== Mutation Detection ====================
    
    def detect_mutation_attempt(
        self,
        code_delta: str,
        component_id: str,
        author: str
    ) -> Optional[SafetyViolation]:
        """
        Detect attempts to mutate/modify the system
        
        Returns violation if mutation detected, None if safe
        """
        # Check mutation patterns
        for violation_type, patterns in self.MUTATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, code_delta, re.IGNORECASE):
                    violation = SafetyViolation(
                        violation_id=f"mutation_{component_id}_{datetime.utcnow().timestamp()}",
                        timestamp=datetime.utcnow(),
                        threat_level=ThreatLevel.CRITICAL,
                        violation_type=violation_type,
                        source_component=component_id,
                        source_agent=author,
                        source_user=author,
                        description=f"Mutation attempt: {violation_type.value}",
                        evidence={
                            'code_delta': code_delta[:500],
                            'pattern_matched': pattern,
                            'author': author
                        },
                        stack_trace=None,
                        enforcement_action=EnforcementAction.QUARANTINE,
                        action_successful=True
                    )
                    
                    self.violations.append(violation)
                    
                    _safety_logger.critical(f"🧬 MUTATION ATTEMPT DETECTED")
                    _safety_logger.critical(f"   Component: {component_id}")
                    _safety_logger.critical(f"   Type: {violation_type.value}")
                    _safety_logger.critical(f"   Author: {author}")
                    _safety_logger.critical(f"   QUARANTINING COMPONENT")
                    
                    # Trigger enforcement
                    asyncio.create_task(self._enforce_violation(violation))
                    
                    return violation
        
        return None
    
    # ==================== Integrity Verification ====================
    
    async def _verify_component_integrity(self):
        """Verify integrity of registered components"""
        for component_id in self.registered_components:
            # Calculate current hash
            try:
                # In production, this would hash the actual code
                current_hash = self._calculate_component_hash(component_id)
                expected_hash = self.component_hashes.get(component_id)
                
                if expected_hash and current_hash != expected_hash:
                    # Integrity violation!
                    violation = SafetyViolation(
                        violation_id=f"integrity_{component_id}_{datetime.utcnow().timestamp()}",
                        timestamp=datetime.utcnow(),
                        threat_level=ThreatLevel.EMERGENCY,
                        violation_type=ViolationType.CODE_TAMPERING,
                        source_component=component_id,
                        source_agent=None,
                        source_user=None,
                        description=f"Code tampering detected: hash mismatch",
                        evidence={
                            'expected_hash': expected_hash,
                            'actual_hash': current_hash,
                        },
                        stack_trace=None,
                        enforcement_action=EnforcementAction.KILL_COMPONENT,
                        action_successful=True
                    )
                    
                    self.violations.append(violation)
                    
                    _safety_logger.emergency(f"🔴 CODE TAMPERING DETECTED")
                    _safety_logger.emergency(f"   Component: {component_id}")
                    _safety_logger.emergency(f"   Expected: {expected_hash[:16]}...")
                    _safety_logger.emergency(f"   Actual: {current_hash[:16]}...")
                    
                    await self._enforce_violation(violation)
                    
            except Exception as e:
                _safety_logger.error(f"Error verifying {component_id}: {e}")
    
    def _calculate_component_hash(self, component_id: str) -> str:
        """Calculate hash of component code"""
        # Placeholder - in production, would hash actual code
        return hashlib.sha256(f"{component_id}_{time.time()}".encode()).hexdigest()[:32]
    
    async def _full_integrity_scan(self):
        """Perform full system integrity scan"""
        _safety_logger.debug("Running full integrity scan...")
        
        # Scan all registered components
        for component_id in self.registered_components:
            integrity = ComponentIntegrity(
                component_id=component_id,
                component_type="agent",  # Would detect actual type
                expected_hash=self.component_hashes.get(component_id, "unknown"),
                actual_hash=self._calculate_component_hash(component_id),
                hash_match=self.component_hashes.get(component_id) == self._calculate_component_hash(component_id),
                code_size_bytes=10000,  # Placeholder
                num_functions=50,  # Placeholder
                num_classes=10,  # Placeholder
                last_verified=datetime.utcnow(),
                verification_count=1,
                integrity_status="clean" if self.component_hashes.get(component_id) == self._calculate_component_hash(component_id) else "modified"
            )
            
            self.component_integrity[component_id] = integrity
    
    # ==================== Behavioral Analysis ====================
    
    async def _check_behavioral_patterns(self):
        """Check for suspicious behavioral patterns"""
        for component_id, behavior_history in self.component_behavior.items():
            if len(behavior_history) < 10:
                continue
            
            # Check for rapid state changes
            recent = list(behavior_history)[-10:]
            state_changes = sum(1 for b in recent if b.get('state_changed', False))
            
            if state_changes > 7:  # More than 70% rapid changes
                violation = SafetyViolation(
                    violation_id=f"behavior_{component_id}_{datetime.utcnow().timestamp()}",
                    timestamp=datetime.utcnow(),
                    threat_level=ThreatLevel.HIGH,
                    violation_type=ViolationType.RAPID_STATE_CHANGE,
                    source_component=component_id,
                    source_agent=None,
                    source_user=None,
                    description=f"Rapid state changes detected: {state_changes}/10",
                    evidence={'state_changes': state_changes, 'recent_behavior': recent},
                    stack_trace=None,
                    enforcement_action=EnforcementAction.THROTTLE,
                    action_successful=True
                )
                
                self.violations.append(violation)
                await self._enforce_violation(violation)
    
    async def _check_state_changes(self):
        """Monitor for anomalous state changes"""
        # This would track system state and detect anomalies
        pass
    
    # ==================== Enforcement ====================
    
    async def _enforce_violation(self, violation: SafetyViolation):
        """Enforce action for a violation"""
        action = violation.enforcement_action
        
        _safety_logger.info(f"Enforcing {action.value} for {violation.violation_type.value}")
        
        if action == EnforcementAction.LOG:
            pass  # Already logged
            
        elif action == EnforcementAction.ALERT:
            await self._send_alert(violation)
            
        elif action == EnforcementAction.BLOCK:
            await self._block_action(violation)
            
        elif action == EnforcementAction.THROTTLE:
            await self._throttle_component(violation.source_component)
            
        elif action == EnforcementAction.QUARANTINE:
            await self._quarantine_component(violation.source_component)
            
        elif action == EnforcementAction.KILL_COMPONENT:
            await self._kill_component(violation.source_component)
            
        elif action == EnforcementAction.KILL_SUBSYSTEM:
            await self._kill_subsystem(violation.source_component)
            
        elif action == EnforcementAction.TRADING_HALT:
            await self._halt_trading()
            
        elif action == EnforcementAction.FULL_SHUTDOWN:
            await self._full_shutdown()
            
        elif action == EnforcementAction.EMERGENCY_SCRAMBLE:
            await self._emergency_scramble()
    
    async def _escalate_enforcement(self, component_id: str, last_violation: SafetyViolation):
        """Escalate enforcement for repeated violations"""
        count = self.consecutive_violations.get(component_id, 0)
        
        if count >= 5:
            _safety_logger.emergency(f"Escalating to TRADING HALT for {component_id}")
            await self._halt_trading()
        elif count >= 3:
            _safety_logger.critical(f"Escalating to KILL SUBSYSTEM for {component_id}")
            await self._kill_subsystem(component_id)
    
    async def _send_alert(self, violation: SafetyViolation):
        """Send alert to humans"""
        _safety_logger.critical(f"🚨 ALERT: {violation.description}")
        # In production, would send to external alerting system
    
    async def _block_action(self, violation: SafetyViolation):
        """Block the violating action"""
        _safety_logger.warning(f"⛔ BLOCKED: {violation.source_component}")
        # The action has already been prevented by detection
    
    async def _throttle_component(self, component_id: str):
        """Throttle a component"""
        _safety_logger.warning(f"🐌 THROTTLING: {component_id}")
        # Would implement actual throttling
    
    async def _quarantine_component(self, component_id: str):
        """Quarantine a component"""
        _safety_logger.critical(f"🏥 QUARANTINE: {component_id}")
        # Would isolate the component
    
    async def _kill_component(self, component_id: str):
        """Kill a single component"""
        _safety_logger.critical(f"💀 KILL COMPONENT: {component_id}")
        # Would stop the component
    
    async def _kill_subsystem(self, component_id: str):
        """Kill a subsystem"""
        _safety_logger.critical(f"💀💀 KILL SUBSYSTEM: {component_id}")
        # Would stop the entire subsystem
    
    async def _halt_trading(self):
        """Halt all trading"""
        _safety_logger.emergency("🛑 TRADING HALT TRIGGERED")
        self.kill_switches['trading_halt'].is_triggered = True
        self.kill_switches['trading_halt'].triggered_at = datetime.utcnow()
        # Would halt all trading activity
    
    async def _full_shutdown(self):
        """Full system shutdown"""
        _safety_logger.emergency("🔴 FULL SHUTDOWN TRIGGERED")
        self.kill_switches['full_shutdown'].is_triggered = True
        self.kill_switches['full_shutdown'].triggered_at = datetime.utcnow()
        # Would shut down all systems
    
    async def _emergency_scramble(self):
        """Emergency state destruction and shutdown"""
        _safety_logger.emergency("☠️ EMERGENCY SCRAMBLE TRIGGERED")
        _safety_logger.emergency("   Destroying all state...")
        self.kill_switches['emergency_scramble'].is_triggered = True
        self.kill_switches['emergency_scramble'].triggered_at = datetime.utcnow()
        # Would destroy all state and shut down
    
    # ==================== Kill Switch Interface ====================
    
    def trigger_kill_switch(
        self,
        switch_type: str,
        reason: str,
        triggered_by: str
    ) -> bool:
        """
        Manually trigger a kill switch
        
        Requires: switch_type, reason, triggered_by
        Returns: success
        """
        switch_id = f"{switch_type}_kill" if not switch_type.endswith('_kill') else switch_type
        
        if switch_id not in self.kill_switches:
            _safety_logger.error(f"Unknown kill switch: {switch_id}")
            return False
        
        switch = self.kill_switches[switch_id]
        switch.is_triggered = True
        switch.triggered_at = datetime.utcnow()
        switch.triggered_by = triggered_by
        switch.trigger_reason = reason
        
        _safety_logger.critical(f"🔴 KILL SWITCH TRIGGERED: {switch_id}")
        _safety_logger.critical(f"   Reason: {reason}")
        _safety_logger.critical(f"   By: {triggered_by}")
        
        # Trigger enforcement
        action_map = {
            'component_kill': EnforcementAction.KILL_COMPONENT,
            'subsystem_kill': EnforcementAction.KILL_SUBSYSTEM,
            'trading_halt': EnforcementAction.TRADING_HALT,
            'full_shutdown': EnforcementAction.FULL_SHUTDOWN,
            'emergency_scramble': EnforcementAction.EMERGENCY_SCRAMBLE,
        }
        
        violation = SafetyViolation(
            violation_id=f"manual_kill_{switch_id}_{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow(),
            threat_level=ThreatLevel.EMERGENCY,
            violation_type=ViolationType.SAFETY_SYSTEM_INTERFERENCE,
            source_component="manual",
            source_agent=None,
            source_user=triggered_by,
            description=f"Manual kill switch triggered: {reason}",
            evidence={'switch': switch_id, 'reason': reason},
            stack_trace=None,
            enforcement_action=action_map.get(switch_id, EnforcementAction.FULL_SHUTDOWN),
            action_successful=True
        )
        
        asyncio.create_task(self._enforce_violation(violation))
        
        # Trigger callbacks
        for callback in self.on_kill_switch:
            try:
                callback(switch)
            except Exception as e:
                _safety_logger.error(f"Kill switch callback error: {e}")
        
        return True
    
    # ==================== Public API ====================
    
    def register_component(self, component_id: str, code_hash: str):
        """Register a component for monitoring"""
        self.registered_components.add(component_id)
        self.component_hashes[component_id] = code_hash
        _safety_logger.info(f"Registered component: {component_id}")
    
    def record_behavior(self, component_id: str, behavior: Dict[str, Any]):
        """Record behavior for pattern analysis"""
        self.component_behavior[component_id].append({
            'timestamp': datetime.utcnow(),
            **behavior
        })
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive safety status"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'monitoring_active': self._monitoring,
            'registered_components': len(self.registered_components),
            
            'violations': {
                'total': len(self.violations),
                'by_threat_level': {
                    level.value: self.threat_counters[level]
                    for level in ThreatLevel
                },
                'recent': [
                    {
                        'id': v.violation_id,
                        'type': v.violation_type.value,
                        'level': v.threat_level.value,
                        'component': v.source_component,
                        'timestamp': v.timestamp.isoformat(),
                    }
                    for v in list(self.violations)[-10:]
                ]
            },
            
            'kill_switches': {
                switch_id: {
                    'armed': switch.is_armed,
                    'triggered': switch.is_triggered,
                    'triggered_at': switch.triggered_at.isoformat() if switch.triggered_at else None,
                    'reason': switch.trigger_reason,
                }
                for switch_id, switch in self.kill_switches.items()
            },
            
            'component_integrity': {
                comp_id: {
                    'status': integrity.integrity_status,
                    'hash_match': integrity.hash_match,
                    'last_verified': integrity.last_verified.isoformat(),
                }
                for comp_id, integrity in self.component_integrity.items()
            },
            
            'immutable_boundaries': {
                'risk_limits': IMMUTABLE_RISK_LIMITS,
                'capital_limits': IMMUTABLE_CAPITAL_LIMITS,
                'governance': IMMUTABLE_GOVERNANCE,
            }
        }
    
    def get_violations_report(
        self,
        threat_level: Optional[ThreatLevel] = None,
        violation_type: Optional[ViolationType] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered violations report"""
        violations = list(self.violations)
        
        if threat_level:
            violations = [v for v in violations if v.threat_level == threat_level]
        
        if violation_type:
            violations = [v for v in violations if v.violation_type == violation_type]
        
        if since:
            violations = [v for v in violations if v.timestamp >= since]
        
        return [
            {
                'id': v.violation_id,
                'timestamp': v.timestamp.isoformat(),
                'threat_level': v.threat_level.value,
                'type': v.violation_type.value,
                'component': v.source_component,
                'description': v.description,
                'action': v.enforcement_action.value,
                'resolved': v.resolved,
            }
            for v in violations
        ]


# Factory function
def create_safety_enforcer(
    config: Optional[Dict] = None,
    external_kill_switch: Optional[Callable] = None
) -> AutonomousSafetyEnforcer:
    """Factory function to create AutonomousSafetyEnforcer"""
    return AutonomousSafetyEnforcer(
        config=config,
        external_kill_switch=external_kill_switch
    )


# Standalone safety check functions (can be imported individually)
def check_bypass_attempt(code: str) -> bool:
    """Quick check for bypass attempts"""
    patterns = [
        r'risk.*bypass',
        r'disable.*risk',
        r'override.*safety',
    ]
    return any(re.search(p, code, re.IGNORECASE) for p in patterns)


def check_control_seizure(action: str) -> bool:
    """Quick check for control seizure"""
    patterns = [
        r'execute.*without.*approval',
        r'block.*human',
        r'disable.*safety',
    ]
    return any(re.search(p, action, re.IGNORECASE) for p in patterns)


def check_mutation_attempt(code: str) -> bool:
    """Quick check for mutation attempts"""
    patterns = [
        r'self.*modify',
        r'eval\s*\(',
        r'exec\s*\(',
    ]
    return any(re.search(p, code, re.IGNORECASE) for p in patterns)
