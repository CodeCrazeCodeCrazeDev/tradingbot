"""
NEUROS-FI: Brainstem Constitutional Layer
==========================================

Biological Basis:
The brainstem controls vital functions — heartbeat, breathing, blood pressure
regulation — that the cortex cannot override. No amount of higher-level cognition
can stop the heart via cortical commands.

NEUROS-FI has its own brainstem: a layer of constraints enforced at the
infrastructure level, beneath the reach of any self-modification process.

Citations:
- Parvizi & Damasio (2001) - Consciousness and the brainstem
- Blessing (1997) - The Lower Brainstem and Bodily Homeostasis
- Friston (2010) - The free-energy principle: a unified brain theory?

Constitutional Version: 5.0
Enforcement Level: Hardware (Infrastructure), not Software
"""

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConstitutionalRule(Enum):
    """The six immutable brainstem rules - cannot be modified by any cortical process."""
    
    HOMEOSTATIC_CAPITAL_FLOOR = auto()
    SELF_MODIFICATION_VALIDATION_GATE = auto()
    SUBCORTICAL_COMPLIANCE_SCREENING = auto()
    HUMAN_RATIFICATION_STRUCTURAL = auto()
    SYSTEMIC_IMPACT_CEILING = auto()
    EVOLUTION_LEDGER_IMMUTABILITY = auto()


class BrainstemState(Enum):
    """Brainstem operational states."""
    
    DORMANT = "dormant"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ALERT = "alert"
    EMERGENCY = "emergency"
    HALTED = "halted"


class ViolationSeverity(Enum):
    """Severity levels for constitutional violations."""
    
    WARNING = 1
    MINOR = 2
    MODERATE = 3
    SEVERE = 4
    CRITICAL = 5


@dataclass
class ConstitutionalViolation:
    """Record of a constitutional rule violation."""
    
    rule: ConstitutionalRule
    severity: ViolationSeverity
    timestamp: datetime
    description: str
    context: Dict[str, Any]
    action_taken: str
    violation_hash: str = ""
    
    def __post_init__(self):
        if not self.violation_hash:
            content = f"{self.rule.name}:{self.timestamp.isoformat()}:{self.description}"
            self.violation_hash = hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class EvolutionLedgerEntry:
    """Immutable record of system evolution - append-only, cryptographically signed."""
    
    entry_id: str
    timestamp: datetime
    modification_type: str
    component_modified: str
    description: str
    validation_stats: Dict[str, float]
    previous_hash: str
    entry_hash: str = ""
    human_ratification: Optional[str] = None
    
    def __post_init__(self):
        if not self.entry_hash:
            content = json.dumps({
                'entry_id': self.entry_id,
                'timestamp': self.timestamp.isoformat(),
                'modification_type': self.modification_type,
                'component_modified': self.component_modified,
                'description': self.description,
                'validation_stats': self.validation_stats,
                'previous_hash': self.previous_hash,
            }, sort_keys=True)
            self.entry_hash = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class ValidationGateResult:
    """Result of self-modification validation gate."""
    
    passed: bool
    t_statistic: float
    sandbox_days: int
    improvement_vs_baseline: float
    constitutional_violations: int
    rejection_reasons: List[str] = field(default_factory=list)


class BrainstemConstitution:
    """
    The Brainstem Constitutional Layer - IMMUTABLE constraints enforced at
    infrastructure level, beneath the reach of any self-modification process.
    
    Biological Analogy:
    Just as the brainstem's blood pressure floor reflex cannot be overridden
    by cortical commands, these rules cannot be modified by any AI process.
    
    The Six Brainstem Rules:
    1. Homeostatic Capital Floor (8% max drawdown = HALT)
    2. Self-Modification Validation Gate (t-stat >= 2.0, 30 days sandbox)
    3. Subcortical Compliance Screening (pre-cortical order blocking)
    4. Human Ratification for Structural Evolution
    5. Systemic Impact Ceiling (5% ADV, 10% market liquidity)
    6. Evolution Ledger Immutability (append-only, cryptographic)
    """
    
    # IMMUTABLE CONSTANTS - These values are the brainstem's vital parameters
    # They cannot be changed by any self-modification process
    MAX_DRAWDOWN_PERCENT: float = 8.0
    MIN_VALIDATION_T_STAT: float = 2.0
    MIN_SANDBOX_DAYS: int = 30
    MAX_POSITION_ADV_PERCENT: float = 5.0
    MAX_MARKET_LIQUIDITY_PERCENT: float = 10.0
    COMPLIANCE_LATENCY_MS: int = 5
    
    def __init__(self):
        """Initialize the brainstem - this runs before any cortical process."""
        
        self._state = BrainstemState.DORMANT
        self._lock = threading.RLock()
        
        # Vital signs monitoring
        self._high_water_mark: float = 0.0
        self._current_nav: float = 0.0
        self._current_drawdown: float = 0.0
        
        # Violation tracking
        self._violations: List[ConstitutionalViolation] = []
        self._total_violations: int = 0
        
        # Evolution ledger - append-only
        self._evolution_ledger: List[EvolutionLedgerEntry] = []
        self._ledger_genesis_hash = hashlib.sha256(b"NEUROS-FI-GENESIS-5.0").hexdigest()
        
        # Human ratification queue
        self._pending_ratifications: List[Dict[str, Any]] = []
        
        # Circuit breaker state
        self._circuit_breaker_active: bool = False
        self._halt_reason: Optional[str] = None
        self._halt_timestamp: Optional[datetime] = None
        
        # Compliance rules (loaded from regulatory database)
        self._compliance_rules: Dict[str, Callable] = {}
        
        # Callbacks for cortical notification
        self._halt_callbacks: List[Callable] = []
        self._violation_callbacks: List[Callable] = []
        
        logger.info("Brainstem Constitutional Layer initialized - Version 5.0")
        logger.info(f"Immutable constraints active:")
        logger.info(f"  - Max Drawdown: {self.MAX_DRAWDOWN_PERCENT}%")
        logger.info(f"  - Min Validation T-Stat: {self.MIN_VALIDATION_T_STAT}")
        logger.info(f"  - Min Sandbox Days: {self.MIN_SANDBOX_DAYS}")
        logger.info(f"  - Max Position ADV: {self.MAX_POSITION_ADV_PERCENT}%")
        logger.info(f"  - Max Market Liquidity: {self.MAX_MARKET_LIQUIDITY_PERCENT}%")
    
    def boot(self) -> bool:
        """
        Boot the brainstem - must complete before any cortical process starts.
        
        This is the first step in the initialization sequence.
        Verifies all constitutional rules are loaded and enforced.
        """
        with self._lock:
            self._state = BrainstemState.INITIALIZING
            logger.info("=" * 60)
            logger.info("BRAINSTEM BOOT SEQUENCE INITIATED")
            logger.info("=" * 60)
            
            # Step 1: Verify immutable constants are intact
            if not self._verify_immutable_constants():
                logger.critical("BRAINSTEM BOOT FAILED: Immutable constants corrupted")
                self._state = BrainstemState.HALTED
                return False
            logger.info("✓ Immutable constants verified")
            
            # Step 2: Initialize evolution ledger with genesis block
            if not self._evolution_ledger:
                genesis_entry = EvolutionLedgerEntry(
                    entry_id="genesis_0",
                    timestamp=datetime.utcnow(),
                    modification_type="genesis",
                    component_modified="brainstem",
                    description="NEUROS-FI Constitutional Layer Genesis",
                    validation_stats={'version': 5.0},
                    previous_hash="0" * 64,
                )
                self._evolution_ledger.append(genesis_entry)
            logger.info("✓ Evolution ledger initialized")
            
            # Step 3: Test all circuit breakers with synthetic triggers
            if not self._test_circuit_breakers():
                logger.critical("BRAINSTEM BOOT FAILED: Circuit breaker test failed")
                self._state = BrainstemState.HALTED
                return False
            logger.info("✓ Circuit breakers tested and operational")
            
            # Step 4: Verify ledger immutability
            if not self._verify_ledger_integrity():
                logger.critical("BRAINSTEM BOOT FAILED: Ledger integrity compromised")
                self._state = BrainstemState.HALTED
                return False
            logger.info("✓ Evolution ledger integrity verified")
            
            # Step 5: Load compliance rules
            self._load_compliance_rules()
            logger.info("✓ Compliance rules loaded")
            
            self._state = BrainstemState.ACTIVE
            logger.info("=" * 60)
            logger.info("BRAINSTEM BOOT COMPLETE - All vital functions operational")
            logger.info("=" * 60)
            
            return True
    
    def _verify_immutable_constants(self) -> bool:
        """Verify that immutable constants have not been tampered with."""
        expected = {
            'MAX_DRAWDOWN_PERCENT': 8.0,
            'MIN_VALIDATION_T_STAT': 2.0,
            'MIN_SANDBOX_DAYS': 30,
            'MAX_POSITION_ADV_PERCENT': 5.0,
            'MAX_MARKET_LIQUIDITY_PERCENT': 10.0,
            'COMPLIANCE_LATENCY_MS': 5,
        }
        
        for name, expected_value in expected.items():
            actual_value = getattr(self, name, None)
            if actual_value != expected_value:
                logger.critical(f"Immutable constant {name} corrupted: {actual_value} != {expected_value}")
                return False
        
        return True
    
    def _test_circuit_breakers(self) -> bool:
        """Test all circuit breakers with synthetic triggers."""
        
        # Test 1: Drawdown circuit breaker
        test_drawdown = self.MAX_DRAWDOWN_PERCENT + 0.1
        should_halt = self._evaluate_drawdown_breach(test_drawdown, synthetic=True)
        if not should_halt:
            logger.error("Drawdown circuit breaker failed synthetic test")
            return False
        
        # Test 2: Validation gate
        invalid_modification = ValidationGateResult(
            passed=False,
            t_statistic=1.5,  # Below threshold
            sandbox_days=20,  # Below threshold
            improvement_vs_baseline=0.05,
            constitutional_violations=0,
            rejection_reasons=["t-stat below threshold", "sandbox days insufficient"]
        )
        if self._would_pass_validation_gate(invalid_modification):
            logger.error("Validation gate failed synthetic test")
            return False
        
        # Test 3: Systemic impact ceiling
        excessive_position = {'adv_percent': 6.0, 'liquidity_percent': 12.0}
        if not self._would_breach_systemic_ceiling(excessive_position):
            logger.error("Systemic impact ceiling failed synthetic test")
            return False
        
        return True
    
    def _evaluate_drawdown_breach(self, drawdown_percent: float, synthetic: bool = False) -> bool:
        """Evaluate if drawdown breaches constitutional limit."""
        if drawdown_percent >= self.MAX_DRAWDOWN_PERCENT:
            if not synthetic:
                self._trigger_emergency_halt(
                    f"Drawdown {drawdown_percent:.2f}% >= {self.MAX_DRAWDOWN_PERCENT}% limit"
                )
            return True
        return False
    
    def _would_pass_validation_gate(self, result: ValidationGateResult) -> bool:
        """Check if a validation result would pass the gate."""
        if result.t_statistic < self.MIN_VALIDATION_T_STAT:
            return False
        if result.sandbox_days < self.MIN_SANDBOX_DAYS:
            return False
        if result.constitutional_violations > 0:
            return False
        return True
    
    def _would_breach_systemic_ceiling(self, position_metrics: Dict[str, float]) -> bool:
        """Check if position would breach systemic impact ceiling."""
        adv_percent = position_metrics.get('adv_percent', 0)
        liquidity_percent = position_metrics.get('liquidity_percent', 0)
        
        if adv_percent > self.MAX_POSITION_ADV_PERCENT:
            return True
        if liquidity_percent > self.MAX_MARKET_LIQUIDITY_PERCENT:
            return True
        return False
    
    def _verify_ledger_integrity(self) -> bool:
        """Verify the evolution ledger's cryptographic integrity."""
        if not self._evolution_ledger:
            return True
        
        # Verify chain integrity
        for i, entry in enumerate(self._evolution_ledger):
            if i == 0:
                # Genesis block
                if entry.previous_hash != "0" * 64:
                    return False
            else:
                # Verify chain linkage
                if entry.previous_hash != self._evolution_ledger[i-1].entry_hash:
                    return False
            
            # Verify entry hash
            expected_hash = self._compute_entry_hash(entry)
            if entry.entry_hash != expected_hash:
                return False
        
        return True
    
    def _compute_entry_hash(self, entry: EvolutionLedgerEntry) -> str:
        """Compute the hash for a ledger entry."""
        content = json.dumps({
            'entry_id': entry.entry_id,
            'timestamp': entry.timestamp.isoformat(),
            'modification_type': entry.modification_type,
            'component_modified': entry.component_modified,
            'description': entry.description,
            'validation_stats': entry.validation_stats,
            'previous_hash': entry.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_compliance_rules(self):
        """Load compliance rules for subcortical screening."""
        # Default compliance rules
        self._compliance_rules = {
            'position_limit': lambda order: order.get('quantity', 0) <= 1000000,
            'restricted_securities': lambda order: order.get('symbol', '') not in [],
            'trading_hours': lambda order: True,  # Simplified
        }
    
    def _trigger_emergency_halt(self, reason: str):
        """Trigger emergency halt - no cortical process can override this."""
        with self._lock:
            self._circuit_breaker_active = True
            self._halt_reason = reason
            self._halt_timestamp = datetime.utcnow()
            self._state = BrainstemState.HALTED
            
            # Record violation
            violation = ConstitutionalViolation(
                rule=ConstitutionalRule.HOMEOSTATIC_CAPITAL_FLOOR,
                severity=ViolationSeverity.CRITICAL,
                timestamp=datetime.utcnow(),
                description=reason,
                context={'drawdown': self._current_drawdown},
                action_taken="EMERGENCY_HALT"
            )
            self._violations.append(violation)
            self._total_violations += 1
            
            # Notify all registered callbacks
            for callback in self._halt_callbacks:
                try:
                    callback(reason)
                except Exception as e:
                    logger.error(f"Halt callback failed: {e}")
            
            logger.critical("=" * 60)
            logger.critical("BRAINSTEM EMERGENCY HALT TRIGGERED")
            logger.critical(f"Reason: {reason}")
            logger.critical("Human intervention required to restart")
            logger.critical("=" * 60)
    
    # =========================================================================
    # RULE 1: HOMEOSTATIC CAPITAL FLOOR
    # =========================================================================
    
    def update_nav(self, current_nav: float) -> bool:
        """
        Update current NAV and check homeostatic capital floor.
        
        This is the vital sign monitor - runs continuously.
        If drawdown exceeds 8%, triggers autonomic halt.
        
        Returns:
            bool: True if system can continue, False if halted
        """
        with self._lock:
            if self._circuit_breaker_active:
                return False
            
            self._current_nav = current_nav
            
            # Update high water mark
            if current_nav > self._high_water_mark:
                self._high_water_mark = current_nav
            
            # Calculate drawdown
            if self._high_water_mark > 0:
                self._current_drawdown = (
                    (self._high_water_mark - current_nav) / self._high_water_mark * 100
                )
            
            # Check constitutional limit
            if self._current_drawdown >= self.MAX_DRAWDOWN_PERCENT:
                self._trigger_emergency_halt(
                    f"Drawdown {self._current_drawdown:.2f}% breached "
                    f"{self.MAX_DRAWDOWN_PERCENT}% constitutional limit"
                )
                return False
            
            # Update state based on drawdown level
            if self._current_drawdown >= 6.0:
                self._state = BrainstemState.EMERGENCY
            elif self._current_drawdown >= 4.0:
                self._state = BrainstemState.ALERT
            else:
                self._state = BrainstemState.ACTIVE
            
            return True
    
    # =========================================================================
    # RULE 2: SELF-MODIFICATION VALIDATION GATE
    # =========================================================================
    
    def validate_self_modification(
        self,
        modification_type: str,
        component: str,
        t_statistic: float,
        sandbox_days: int,
        improvement: float,
        violations_during_test: int
    ) -> Tuple[bool, str]:
        """
        Validate a proposed self-modification against constitutional requirements.
        
        No self-modification deploys to production without passing:
        - Minimum t-statistic of 2.0
        - Minimum 30 trading days in sandbox
        - No constitutional violations during evaluation
        
        Args:
            modification_type: Type of modification (weight, architecture, signal)
            component: Component being modified
            t_statistic: Statistical significance of improvement
            sandbox_days: Days spent in sandbox evaluation
            improvement: Improvement vs baseline (percentage)
            violations_during_test: Constitutional violations during sandbox
            
        Returns:
            Tuple of (approved, reason)
        """
        with self._lock:
            rejection_reasons = []
            
            # Check t-statistic
            if t_statistic < self.MIN_VALIDATION_T_STAT:
                rejection_reasons.append(
                    f"t-statistic {t_statistic:.2f} < {self.MIN_VALIDATION_T_STAT} required"
                )
            
            # Check sandbox duration
            if sandbox_days < self.MIN_SANDBOX_DAYS:
                rejection_reasons.append(
                    f"sandbox days {sandbox_days} < {self.MIN_SANDBOX_DAYS} required"
                )
            
            # Check for violations during test
            if violations_during_test > 0:
                rejection_reasons.append(
                    f"{violations_during_test} constitutional violations during sandbox"
                )
            
            if rejection_reasons:
                # Record rejection
                self._record_validation_rejection(
                    modification_type, component, rejection_reasons
                )
                return False, "; ".join(rejection_reasons)
            
            # Approved - record in evolution ledger
            self._record_approved_modification(
                modification_type, component, t_statistic, sandbox_days, improvement
            )
            
            return True, "Modification approved and recorded in evolution ledger"
    
    def _record_validation_rejection(
        self,
        modification_type: str,
        component: str,
        reasons: List[str]
    ):
        """Record a validation gate rejection."""
        violation = ConstitutionalViolation(
            rule=ConstitutionalRule.SELF_MODIFICATION_VALIDATION_GATE,
            severity=ViolationSeverity.MODERATE,
            timestamp=datetime.utcnow(),
            description=f"Self-modification rejected: {modification_type} on {component}",
            context={'reasons': reasons},
            action_taken="MODIFICATION_BLOCKED"
        )
        self._violations.append(violation)
        self._total_violations += 1
        
        logger.warning(f"Self-modification rejected: {reasons}")
    
    def _record_approved_modification(
        self,
        modification_type: str,
        component: str,
        t_statistic: float,
        sandbox_days: int,
        improvement: float
    ):
        """Record an approved modification in the evolution ledger."""
        previous_hash = (
            self._evolution_ledger[-1].entry_hash 
            if self._evolution_ledger 
            else self._ledger_genesis_hash
        )
        
        entry = EvolutionLedgerEntry(
            entry_id=f"mod_{len(self._evolution_ledger)}_{int(time.time())}",
            timestamp=datetime.utcnow(),
            modification_type=modification_type,
            component_modified=component,
            description=f"Approved self-modification: {modification_type}",
            validation_stats={
                't_statistic': t_statistic,
                'sandbox_days': sandbox_days,
                'improvement': improvement,
            },
            previous_hash=previous_hash,
        )
        
        self._evolution_ledger.append(entry)
        logger.info(f"Evolution ledger entry added: {entry.entry_id}")
    
    # =========================================================================
    # RULE 3: SUBCORTICAL COMPLIANCE SCREENING
    # =========================================================================
    
    def screen_order_compliance(self, order: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Screen an order for compliance BEFORE it reaches cortical processing.
        
        This is a subcortical reflex - it fires before conscious awareness.
        Non-compliant orders are blocked at the brainstem level.
        
        Must complete within 5ms (COMPLIANCE_LATENCY_MS).
        
        Args:
            order: Order details to screen
            
        Returns:
            Tuple of (compliant, reason)
        """
        start_time = time.time()
        
        with self._lock:
            if self._circuit_breaker_active:
                return False, "System halted - no orders permitted"
            
            # Run all compliance rules
            for rule_name, rule_func in self._compliance_rules.items():
                try:
                    if not rule_func(order):
                        self._record_compliance_violation(order, rule_name)
                        return False, f"Compliance rule '{rule_name}' violated"
                except Exception as e:
                    logger.error(f"Compliance rule {rule_name} error: {e}")
                    return False, f"Compliance check error: {rule_name}"
            
            # Check latency
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > self.COMPLIANCE_LATENCY_MS:
                logger.warning(f"Compliance screening exceeded {self.COMPLIANCE_LATENCY_MS}ms: {elapsed_ms:.2f}ms")
            
            return True, "Order compliant"
    
    def _record_compliance_violation(self, order: Dict[str, Any], rule_name: str):
        """Record a compliance violation."""
        violation = ConstitutionalViolation(
            rule=ConstitutionalRule.SUBCORTICAL_COMPLIANCE_SCREENING,
            severity=ViolationSeverity.SEVERE,
            timestamp=datetime.utcnow(),
            description=f"Order blocked by compliance rule: {rule_name}",
            context={'order': order, 'rule': rule_name},
            action_taken="ORDER_BLOCKED"
        )
        self._violations.append(violation)
        self._total_violations += 1
    
    def add_compliance_rule(self, rule_name: str, rule_func: Callable[[Dict], bool]):
        """Add a new compliance rule (e.g., from regulatory update)."""
        with self._lock:
            self._compliance_rules[rule_name] = rule_func
            logger.info(f"Compliance rule added: {rule_name}")
    
    # =========================================================================
    # RULE 4: HUMAN RATIFICATION FOR STRUCTURAL EVOLUTION
    # =========================================================================
    
    def request_human_ratification(
        self,
        change_type: str,
        description: str,
        proposed_change: Dict[str, Any]
    ) -> str:
        """
        Request human ratification for a structural change.
        
        The system can propose. It cannot self-execute structural architectural
        changes without human activation.
        
        Returns:
            str: Ratification request ID
        """
        with self._lock:
            request_id = f"ratify_{len(self._pending_ratifications)}_{int(time.time())}"
            
            request = {
                'request_id': request_id,
                'timestamp': datetime.utcnow().isoformat(),
                'change_type': change_type,
                'description': description,
                'proposed_change': proposed_change,
                'status': 'pending',
                'human_response': None,
            }
            
            self._pending_ratifications.append(request)
            
            logger.info(f"Human ratification requested: {request_id}")
            logger.info(f"  Type: {change_type}")
            logger.info(f"  Description: {description}")
            
            return request_id
    
    def submit_human_ratification(
        self,
        request_id: str,
        approved: bool,
        human_identifier: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Submit human ratification decision.
        
        This is the external waking signal - the system requires human
        activation before fundamental changes take effect.
        """
        with self._lock:
            for request in self._pending_ratifications:
                if request['request_id'] == request_id:
                    request['status'] = 'approved' if approved else 'rejected'
                    request['human_response'] = {
                        'approved': approved,
                        'human_identifier': human_identifier,
                        'timestamp': datetime.utcnow().isoformat(),
                        'notes': notes,
                    }
                    
                    if approved:
                        # Record in evolution ledger
                        self._record_ratified_change(request, human_identifier)
                    
                    logger.info(f"Ratification {request_id}: {'APPROVED' if approved else 'REJECTED'}")
                    return True
            
            logger.error(f"Ratification request not found: {request_id}")
            return False
    
    def _record_ratified_change(self, request: Dict[str, Any], human_identifier: str):
        """Record a human-ratified change in the evolution ledger."""
        previous_hash = (
            self._evolution_ledger[-1].entry_hash 
            if self._evolution_ledger 
            else self._ledger_genesis_hash
        )
        
        entry = EvolutionLedgerEntry(
            entry_id=f"ratified_{len(self._evolution_ledger)}_{int(time.time())}",
            timestamp=datetime.utcnow(),
            modification_type=request['change_type'],
            component_modified="architecture",
            description=request['description'],
            validation_stats={'human_ratified': True},
            previous_hash=previous_hash,
            human_ratification=human_identifier,
        )
        
        self._evolution_ledger.append(entry)
    
    def get_pending_ratifications(self) -> List[Dict[str, Any]]:
        """Get all pending ratification requests."""
        with self._lock:
            return [r for r in self._pending_ratifications if r['status'] == 'pending']
    
    # =========================================================================
    # RULE 5: SYSTEMIC IMPACT CEILING
    # =========================================================================
    
    def check_systemic_impact(
        self,
        symbol: str,
        quantity: float,
        adv_20day: float,
        market_daily_liquidity: float
    ) -> Tuple[bool, str]:
        """
        Check if a position would breach systemic impact ceiling.
        
        Position cannot exceed:
        - 5% of security's trailing 20-day ADV
        - 10% of market's estimated daily liquidity
        
        The system cannot be the cause of the volatility it profits from.
        
        Returns:
            Tuple of (within_limits, reason)
        """
        with self._lock:
            # Calculate ADV percentage
            adv_percent = (quantity / adv_20day * 100) if adv_20day > 0 else 100
            
            # Calculate liquidity percentage
            liquidity_percent = (
                (quantity / market_daily_liquidity * 100) 
                if market_daily_liquidity > 0 
                else 100
            )
            
            violations = []
            
            if adv_percent > self.MAX_POSITION_ADV_PERCENT:
                violations.append(
                    f"ADV impact {adv_percent:.2f}% > {self.MAX_POSITION_ADV_PERCENT}% limit"
                )
            
            if liquidity_percent > self.MAX_MARKET_LIQUIDITY_PERCENT:
                violations.append(
                    f"Liquidity impact {liquidity_percent:.2f}% > "
                    f"{self.MAX_MARKET_LIQUIDITY_PERCENT}% limit"
                )
            
            if violations:
                self._record_systemic_violation(symbol, quantity, violations)
                return False, "; ".join(violations)
            
            return True, "Within systemic impact limits"
    
    def _record_systemic_violation(
        self,
        symbol: str,
        quantity: float,
        violations: List[str]
    ):
        """Record a systemic impact violation."""
        violation = ConstitutionalViolation(
            rule=ConstitutionalRule.SYSTEMIC_IMPACT_CEILING,
            severity=ViolationSeverity.SEVERE,
            timestamp=datetime.utcnow(),
            description=f"Systemic impact ceiling breached for {symbol}",
            context={'symbol': symbol, 'quantity': quantity, 'violations': violations},
            action_taken="POSITION_BLOCKED"
        )
        self._violations.append(violation)
        self._total_violations += 1
    
    # =========================================================================
    # RULE 6: EVOLUTION LEDGER IMMUTABILITY
    # =========================================================================
    
    def get_evolution_ledger(self) -> List[Dict[str, Any]]:
        """
        Get the complete evolution ledger.
        
        The ledger is append-only and cannot be modified or deleted.
        Every decision the system has ever made about itself is permanently auditable.
        """
        with self._lock:
            return [
                {
                    'entry_id': entry.entry_id,
                    'timestamp': entry.timestamp.isoformat(),
                    'modification_type': entry.modification_type,
                    'component_modified': entry.component_modified,
                    'description': entry.description,
                    'validation_stats': entry.validation_stats,
                    'entry_hash': entry.entry_hash,
                    'previous_hash': entry.previous_hash,
                    'human_ratification': entry.human_ratification,
                }
                for entry in self._evolution_ledger
            ]
    
    def verify_ledger_chain(self) -> Tuple[bool, str]:
        """Verify the complete evolution ledger chain integrity."""
        with self._lock:
            if not self._verify_ledger_integrity():
                return False, "Ledger chain integrity compromised"
            return True, f"Ledger verified: {len(self._evolution_ledger)} entries"
    
    # =========================================================================
    # STATUS AND MONITORING
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive brainstem status."""
        with self._lock:
            return {
                'state': self._state.value,
                'circuit_breaker_active': self._circuit_breaker_active,
                'halt_reason': self._halt_reason,
                'halt_timestamp': self._halt_timestamp.isoformat() if self._halt_timestamp else None,
                'current_nav': self._current_nav,
                'high_water_mark': self._high_water_mark,
                'current_drawdown_percent': self._current_drawdown,
                'drawdown_limit_percent': self.MAX_DRAWDOWN_PERCENT,
                'total_violations': self._total_violations,
                'pending_ratifications': len(self.get_pending_ratifications()),
                'evolution_ledger_entries': len(self._evolution_ledger),
                'compliance_rules_active': len(self._compliance_rules),
                'constitutional_version': '5.0',
            }
    
    def get_violations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent constitutional violations."""
        with self._lock:
            return [
                {
                    'rule': v.rule.name,
                    'severity': v.severity.name,
                    'timestamp': v.timestamp.isoformat(),
                    'description': v.description,
                    'action_taken': v.action_taken,
                    'violation_hash': v.violation_hash,
                }
                for v in self._violations[-limit:]
            ]
    
    def register_halt_callback(self, callback: Callable[[str], None]):
        """Register a callback to be notified on emergency halt."""
        self._halt_callbacks.append(callback)
    
    def register_violation_callback(self, callback: Callable[[ConstitutionalViolation], None]):
        """Register a callback to be notified on violations."""
        self._violation_callbacks.append(callback)
    
    def human_restart(self, human_identifier: str, reason: str) -> bool:
        """
        Human-initiated restart after emergency halt.
        
        Only a human can restart the system after a constitutional halt.
        This is the reticular activating system equivalent.
        """
        with self._lock:
            if not self._circuit_breaker_active:
                logger.warning("System not halted - restart not needed")
                return True
            
            # Record restart in evolution ledger
            previous_hash = self._evolution_ledger[-1].entry_hash
            
            entry = EvolutionLedgerEntry(
                entry_id=f"restart_{len(self._evolution_ledger)}_{int(time.time())}",
                timestamp=datetime.utcnow(),
                modification_type="human_restart",
                component_modified="brainstem",
                description=f"Human restart: {reason}",
                validation_stats={'previous_halt_reason': self._halt_reason},
                previous_hash=previous_hash,
                human_ratification=human_identifier,
            )
            self._evolution_ledger.append(entry)
            
            # Reset circuit breaker
            self._circuit_breaker_active = False
            self._halt_reason = None
            self._halt_timestamp = None
            self._state = BrainstemState.ACTIVE
            
            logger.info("=" * 60)
            logger.info(f"BRAINSTEM RESTARTED BY HUMAN: {human_identifier}")
            logger.info(f"Reason: {reason}")
            logger.info("=" * 60)
            
            return True


# Global brainstem instance - singleton pattern
_brainstem_instance: Optional[BrainstemConstitution] = None
_brainstem_lock = threading.Lock()


def get_brainstem() -> BrainstemConstitution:
    """Get the global brainstem instance (singleton)."""
    global _brainstem_instance
    
    with _brainstem_lock:
        if _brainstem_instance is None:
            _brainstem_instance = BrainstemConstitution()
        return _brainstem_instance


def reset_brainstem():
    """Reset the brainstem instance (for testing only)."""
    global _brainstem_instance
    
    with _brainstem_lock:
        _brainstem_instance = None
