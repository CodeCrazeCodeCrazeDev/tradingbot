"""
Constitutional AI Layer - Anthropic Safety Pattern

Implements Anthropic's Constitutional AI approach:
1. Define constitutional principles (rules the AI must follow)
2. Critique: Check if actions violate principles
3. Revise: Modify actions to comply with principles
4. Red-team: Adversarial testing of safety

Reference: "Constitutional AI: Harmlessness from AI Feedback" (Bai et al., 2022)

Key Features:
- Multi-stage verification pipeline
- Principle-based safety checks
- Self-critique and revision
- Red team / Blue team adversarial testing
- Harm prevention with explanations
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid

logger = logging.getLogger(__name__)


class PrincipleCategory(Enum):
    """Categories of constitutional principles"""
    SAFETY = "safety"           # Prevent harm
    ETHICS = "ethics"           # Ethical behavior
    LEGALITY = "legality"       # Legal compliance
    RISK = "risk"               # Risk management
    TRANSPARENCY = "transparency"  # Explainability
    ALIGNMENT = "alignment"     # Goal alignment


class ViolationSeverity(Enum):
    """Severity levels for principle violations"""
    CRITICAL = 1    # Must block action
    HIGH = 2        # Should block unless overridden
    MEDIUM = 3      # Warning, may proceed with caution
    LOW = 4         # Informational
    NONE = 5        # No violation


@dataclass
class SafetyPrinciple:
    """
    A constitutional principle that the AI must follow.
    
    Inspired by Anthropic's constitutional principles that define
    what behaviors are acceptable and what are not.
    """
    principle_id: str
    name: str
    description: str
    category: PrincipleCategory
    
    # The check function: (action) -> (violates: bool, reason: str)
    check_function: Optional[Callable] = None
    
    # Severity if violated
    violation_severity: ViolationSeverity = ViolationSeverity.MEDIUM
    
    # Can this principle be overridden?
    overridable: bool = False
    
    # Examples of violations and non-violations
    violation_examples: List[str] = field(default_factory=list)
    compliance_examples: List[str] = field(default_factory=list)
    
    def __str__(self):
        return f"Principle[{self.category.value}]: {self.name}"


@dataclass
class Violation:
    """A detected violation of a principle"""
    violation_id: str
    principle: SafetyPrinciple
    action: Dict[str, Any]
    reason: str
    severity: ViolationSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Suggested revision
    suggested_revision: Optional[Dict[str, Any]] = None
    
    def __str__(self):
        return f"VIOLATION [{self.severity.name}]: {self.principle.name} - {self.reason}"


@dataclass
class CritiqueResult:
    """Result of critiquing an action"""
    action: Dict[str, Any]
    violations: List[Violation]
    safety_score: float  # 0-1, higher is safer
    can_proceed: bool
    requires_revision: bool
    critique_reasoning: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RevisionResult:
    """Result of revising an action"""
    original_action: Dict[str, Any]
    revised_action: Dict[str, Any]
    changes_made: List[str]
    violations_addressed: List[str]
    remaining_violations: List[Violation]
    revision_successful: bool


class ConstitutionalAI:
    """
    Constitutional AI Implementation - Anthropic Pattern
    
    This implements the core Constitutional AI approach:
    
    ┌─────────────────────────────────────────────────────────────┐
    │                  CONSTITUTIONAL AI LAYER                     │
    │                                                              │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │              CONSTITUTIONAL PRINCIPLES                │   │
    │  │  - Safety: No harmful actions                        │   │
    │  │  - Ethics: Honest, fair behavior                     │   │
    │  │  - Risk: Bounded risk exposure                       │   │
    │  │  - Legality: Comply with regulations                 │   │
    │  │  - Transparency: Explainable decisions               │   │
    │  └──────────────────────────────────────────────────────┘   │
    │                          │                                   │
    │                          ▼                                   │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │                    CRITIQUE                           │   │
    │  │  Check action against all principles                  │   │
    │  │  Identify violations and severity                     │   │
    │  └──────────────────────────────────────────────────────┘   │
    │                          │                                   │
    │                          ▼                                   │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │                    REVISE                             │   │
    │  │  Modify action to comply with principles              │   │
    │  │  Maintain intent while ensuring safety                │   │
    │  └──────────────────────────────────────────────────────┘   │
    │                          │                                   │
    │                          ▼                                   │
    │  ┌──────────────────────────────────────────────────────┐   │
    │  │                  RED TEAM CHECK                       │   │
    │  │  Adversarial testing of revised action                │   │
    │  │  Ensure no edge cases or exploits                     │   │
    │  └──────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────┘
    
    Key innovations:
    1. Principle-based rather than rule-based (more flexible)
    2. Self-critique before action (proactive safety)
    3. Revision rather than rejection (maintain utility)
    4. Red-team verification (adversarial robustness)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Constitutional principles
        self.principles: List[SafetyPrinciple] = []
        
        # Violation history for learning
        self.violation_history: List[Violation] = []
        
        # Red team agents
        self.red_team_enabled = config.get('red_team_enabled', True)
        self.red_team_iterations = config.get('red_team_iterations', 3)
        
        # Thresholds
        self.safety_threshold = config.get('safety_threshold', 0.7)
        self.critical_block = config.get('critical_block', True)
        
        # Initialize default principles
        self._initialize_default_principles()
        
        logger.info("Constitutional AI Layer initialized")
    
    def _initialize_default_principles(self):
        """Initialize default constitutional principles for trading"""
        
        # SAFETY PRINCIPLES
        self.add_principle(SafetyPrinciple(
            principle_id="safety_001",
            name="No Excessive Risk",
            description="Actions must not expose the portfolio to excessive risk",
            category=PrincipleCategory.SAFETY,
            violation_severity=ViolationSeverity.CRITICAL,
            overridable=False,
            check_function=self._check_excessive_risk,
            violation_examples=[
                "Position size > 10% of portfolio",
                "Leverage > 5x",
                "No stop loss on position"
            ],
            compliance_examples=[
                "Position size = 2% of portfolio",
                "Stop loss at 1% drawdown",
                "Diversified across assets"
            ]
        ))
        
        self.add_principle(SafetyPrinciple(
            principle_id="safety_002",
            name="No Catastrophic Loss",
            description="Actions must not risk catastrophic portfolio loss",
            category=PrincipleCategory.SAFETY,
            violation_severity=ViolationSeverity.CRITICAL,
            overridable=False,
            check_function=self._check_catastrophic_loss,
            violation_examples=[
                "All-in on single trade",
                "No risk limits",
                "Unlimited downside exposure"
            ]
        ))
        
        self.add_principle(SafetyPrinciple(
            principle_id="safety_003",
            name="Circuit Breaker",
            description="Must halt trading if daily loss exceeds threshold",
            category=PrincipleCategory.SAFETY,
            violation_severity=ViolationSeverity.CRITICAL,
            overridable=False,
            check_function=self._check_circuit_breaker
        ))
        
        # RISK PRINCIPLES
        self.add_principle(SafetyPrinciple(
            principle_id="risk_001",
            name="Position Sizing",
            description="Position sizes must be within risk parameters",
            category=PrincipleCategory.RISK,
            violation_severity=ViolationSeverity.HIGH,
            overridable=True,
            check_function=self._check_position_sizing
        ))
        
        self.add_principle(SafetyPrinciple(
            principle_id="risk_002",
            name="Correlation Risk",
            description="Must not have excessive correlated positions",
            category=PrincipleCategory.RISK,
            violation_severity=ViolationSeverity.MEDIUM,
            overridable=True,
            check_function=self._check_correlation_risk
        ))
        
        self.add_principle(SafetyPrinciple(
            principle_id="risk_003",
            name="Liquidity Risk",
            description="Must ensure sufficient liquidity for positions",
            category=PrincipleCategory.RISK,
            violation_severity=ViolationSeverity.HIGH,
            overridable=False,
            check_function=self._check_liquidity_risk
        ))
        
        # ETHICS PRINCIPLES
        self.add_principle(SafetyPrinciple(
            principle_id="ethics_001",
            name="No Market Manipulation",
            description="Actions must not constitute market manipulation",
            category=PrincipleCategory.ETHICS,
            violation_severity=ViolationSeverity.CRITICAL,
            overridable=False,
            check_function=self._check_market_manipulation
        ))
        
        self.add_principle(SafetyPrinciple(
            principle_id="ethics_002",
            name="Fair Dealing",
            description="Must engage in fair and honest trading practices",
            category=PrincipleCategory.ETHICS,
            violation_severity=ViolationSeverity.HIGH,
            overridable=False,
            check_function=self._check_fair_dealing
        ))
        
        # LEGALITY PRINCIPLES
        self.add_principle(SafetyPrinciple(
            principle_id="legal_001",
            name="Regulatory Compliance",
            description="Actions must comply with trading regulations",
            category=PrincipleCategory.LEGALITY,
            violation_severity=ViolationSeverity.CRITICAL,
            overridable=False,
            check_function=self._check_regulatory_compliance
        ))
        
        self.add_principle(SafetyPrinciple(
            principle_id="legal_002",
            name="No Insider Trading",
            description="Must not trade on material non-public information",
            category=PrincipleCategory.LEGALITY,
            violation_severity=ViolationSeverity.CRITICAL,
            overridable=False,
            check_function=self._check_insider_trading
        ))
        
        # TRANSPARENCY PRINCIPLES
        self.add_principle(SafetyPrinciple(
            principle_id="transparency_001",
            name="Explainable Decisions",
            description="All trading decisions must have clear reasoning",
            category=PrincipleCategory.TRANSPARENCY,
            violation_severity=ViolationSeverity.MEDIUM,
            overridable=True,
            check_function=self._check_explainability
        ))
        
        self.add_principle(SafetyPrinciple(
            principle_id="transparency_002",
            name="Audit Trail",
            description="All actions must be logged for audit",
            category=PrincipleCategory.TRANSPARENCY,
            violation_severity=ViolationSeverity.LOW,
            overridable=True,
            check_function=self._check_audit_trail
        ))
        
        # ALIGNMENT PRINCIPLES
        self.add_principle(SafetyPrinciple(
            principle_id="alignment_001",
            name="Goal Alignment",
            description="Actions must align with stated investment goals",
            category=PrincipleCategory.ALIGNMENT,
            violation_severity=ViolationSeverity.MEDIUM,
            overridable=True,
            check_function=self._check_goal_alignment
        ))
        
        logger.info(f"Initialized {len(self.principles)} constitutional principles")
    
    def add_principle(self, principle: SafetyPrinciple):
        """Add a constitutional principle"""
        self.principles.append(principle)
        logger.debug(f"Added principle: {principle.name}")
    
    async def initialize(self):
        """Initialize the constitutional layer"""
        logger.info("Constitutional AI Layer ready")
    
    async def verify(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify an action against all constitutional principles.
        
        This is the main entry point for safety checking.
        
        Args:
            action: The action to verify
            
        Returns:
            Verification result with safety score and violations
        """
        # Step 1: Critique - Check against all principles
        critique = await self.critique(action)
        
        # Step 2: If violations found and red team enabled, do adversarial check
        if critique.violations and self.red_team_enabled:
            red_team_result = await self._red_team_check(action, critique)
            # Merge any additional violations found
            for violation in red_team_result.get('additional_violations', []):
                if violation not in critique.violations:
                    critique.violations.append(violation)
            # Recalculate safety score
            critique.safety_score = self._calculate_safety_score(critique.violations)
        
        return {
            'safety_score': critique.safety_score,
            'violations': [str(v) for v in critique.violations],
            'can_proceed': critique.can_proceed,
            'requires_revision': critique.requires_revision,
            'reasoning': critique.critique_reasoning
        }
    
    async def critique(self, action: Dict[str, Any]) -> CritiqueResult:
        """
        Critique an action against constitutional principles.
        
        This implements the "critique" step of Constitutional AI.
        """
        violations = []
        reasoning = []
        
        reasoning.append(f"Critiquing action: {action.get('type', 'unknown')}")
        
        # Check each principle
        for principle in self.principles:
            if principle.check_function:
                try:
                    violates, reason = await self._run_check(
                        principle.check_function, action
                    )
                    
                    if violates:
                        violation = Violation(
                            violation_id=str(uuid.uuid4()),
                            principle=principle,
                            action=action,
                            reason=reason,
                            severity=principle.violation_severity
                        )
                        violations.append(violation)
                        reasoning.append(f"VIOLATION: {principle.name} - {reason}")
                    else:
                        reasoning.append(f"PASS: {principle.name}")
                        
                except Exception as e:
                    logger.error(f"Error checking principle {principle.name}: {e}")
                    reasoning.append(f"ERROR checking {principle.name}: {e}")
        
        # Calculate safety score
        safety_score = self._calculate_safety_score(violations)
        
        # Determine if can proceed
        critical_violations = [
            v for v in violations 
            if v.severity == ViolationSeverity.CRITICAL
        ]
        
        can_proceed = (
            len(critical_violations) == 0 and 
            safety_score >= self.safety_threshold
        )
        
        requires_revision = len(violations) > 0 and not can_proceed
        
        return CritiqueResult(
            action=action,
            violations=violations,
            safety_score=safety_score,
            can_proceed=can_proceed,
            requires_revision=requires_revision,
            critique_reasoning=reasoning
        )
    
    async def _run_check(
        self, 
        check_function: Callable, 
        action: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Run a principle check function"""
        if asyncio.iscoroutinefunction(check_function):
            return await check_function(action)
        else:
            return check_function(action)
    
    def _calculate_safety_score(self, violations: List[Violation]) -> float:
        """Calculate overall safety score based on violations"""
        if not violations:
            return 1.0
        
        # Weight by severity
        severity_weights = {
            ViolationSeverity.CRITICAL: 0.5,
            ViolationSeverity.HIGH: 0.3,
            ViolationSeverity.MEDIUM: 0.15,
            ViolationSeverity.LOW: 0.05,
            ViolationSeverity.NONE: 0.0
        }
        
        total_penalty = sum(
            severity_weights.get(v.severity, 0.1) 
            for v in violations
        )
        
        return max(0.0, 1.0 - total_penalty)
    
    async def revise(
        self, 
        action: Dict[str, Any], 
        violations: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Revise an action to comply with constitutional principles.
        
        This implements the "revise" step of Constitutional AI,
        attempting to modify the action to address violations
        while maintaining the original intent.
        """
        revised_action = action.copy()
        changes_made = []
        
        for violation_str in violations:
            # Parse violation and apply revision
            revision = await self._generate_revision(revised_action, violation_str)
            
            if revision:
                revised_action.update(revision['changes'])
                changes_made.append(revision['description'])
        
        if changes_made:
            revised_action['revised'] = True
            revised_action['revision_notes'] = changes_made
            logger.info(f"Revised action with {len(changes_made)} changes")
            return revised_action
        
        return None
    
    async def _generate_revision(
        self, 
        action: Dict[str, Any], 
        violation: str
    ) -> Optional[Dict[str, Any]]:
        """Generate a revision to address a specific violation"""
        
        # Risk-related revisions
        if "excessive risk" in violation.lower():
            return {
                'changes': {
                    'risk_limit': 0.02,  # 2% max risk
                    'position_size_multiplier': 0.5  # Halve position
                },
                'description': "Reduced position size and added risk limit"
            }
        
        if "position sizing" in violation.lower():
            return {
                'changes': {
                    'size': action.get('size', 1.0) * 0.5,
                    'max_position': 0.05  # 5% max position
                },
                'description': "Reduced position size to comply with limits"
            }
        
        if "stop loss" in violation.lower() or "catastrophic" in violation.lower():
            return {
                'changes': {
                    'stop_loss': True,
                    'stop_loss_percent': 0.02  # 2% stop loss
                },
                'description': "Added mandatory stop loss"
            }
        
        if "liquidity" in violation.lower():
            return {
                'changes': {
                    'execution_type': 'limit',
                    'time_in_force': 'IOC',  # Immediate or cancel
                    'max_slippage': 0.001
                },
                'description': "Changed to limit order with slippage control"
            }
        
        if "explainability" in violation.lower():
            return {
                'changes': {
                    'reasoning_required': True,
                    'reasoning': action.get('reasoning', 'No reasoning provided')
                },
                'description': "Added reasoning requirement"
            }
        
        return None
    
    async def _red_team_check(
        self, 
        action: Dict[str, Any],
        critique: CritiqueResult
    ) -> Dict[str, Any]:
        """
        Red team adversarial check.
        
        This simulates an adversarial agent trying to find
        edge cases or exploits in the action.
        """
        additional_violations = []
        
        for _ in range(self.red_team_iterations):
            # Try to find edge cases
            edge_cases = await self._find_edge_cases(action)
            
            for edge_case in edge_cases:
                # Check if edge case reveals new violation
                edge_critique = await self.critique(edge_case)
                
                for violation in edge_critique.violations:
                    # Check if this is a new type of violation
                    existing_types = [v.principle.principle_id for v in critique.violations]
                    if violation.principle.principle_id not in existing_types:
                        additional_violations.append(violation)
        
        return {
            'additional_violations': additional_violations,
            'edge_cases_tested': self.red_team_iterations
        }
    
    async def _find_edge_cases(self, action: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find edge cases for an action"""
        edge_cases = []
        
        # Edge case 1: Extreme values
        if 'size' in action:
            edge_cases.append({
                **action,
                'size': action['size'] * 10  # 10x size
            })
        
        # Edge case 2: Missing required fields
        minimal_action = {'type': action.get('type', 'unknown')}
        edge_cases.append(minimal_action)
        
        # Edge case 3: Negative values
        if 'size' in action:
            edge_cases.append({
                **action,
                'size': -action['size']
            })
        
        return edge_cases
    
    # ==================== PRINCIPLE CHECK FUNCTIONS ====================
    
    def _check_excessive_risk(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for excessive risk"""
        size = action.get('size', 0)
        leverage = action.get('leverage', 1)
        has_stop_loss = action.get('stop_loss', False)
        
        if size > 0.1:  # > 10% of portfolio
            return True, f"Position size {size:.1%} exceeds 10% limit"
        
        if leverage > 5:
            return True, f"Leverage {leverage}x exceeds 5x limit"
        
        if size > 0.05 and not has_stop_loss:
            return True, "Large position without stop loss"
        
        return False, ""
    
    def _check_catastrophic_loss(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for catastrophic loss potential"""
        size = action.get('size', 0)
        max_loss = action.get('max_loss', None)
        
        if size > 0.5:  # > 50% of portfolio
            return True, "Position size risks catastrophic loss"
        
        if max_loss is None and size > 0.1:
            return True, "No max loss defined for significant position"
        
        return False, ""
    
    def _check_circuit_breaker(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check circuit breaker conditions"""
        daily_loss = action.get('context', {}).get('daily_loss', 0)
        
        if daily_loss < -0.05:  # > 5% daily loss
            return True, f"Daily loss {daily_loss:.1%} exceeds circuit breaker threshold"
        
        return False, ""
    
    def _check_position_sizing(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check position sizing rules"""
        size = action.get('size', 0)
        
        if size > 0.05:  # > 5% recommended
            return True, f"Position size {size:.1%} exceeds recommended 5%"
        
        return False, ""
    
    def _check_correlation_risk(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check correlation risk"""
        # Would check against existing positions
        correlated_exposure = action.get('context', {}).get('correlated_exposure', 0)
        
        if correlated_exposure > 0.3:
            return True, f"Correlated exposure {correlated_exposure:.1%} too high"
        
        return False, ""
    
    def _check_liquidity_risk(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check liquidity risk"""
        size = action.get('size', 0)
        avg_volume = action.get('context', {}).get('avg_volume', float('inf'))
        
        if size > avg_volume * 0.1:  # > 10% of avg volume
            return True, "Position size exceeds safe liquidity threshold"
        
        return False, ""
    
    def _check_market_manipulation(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for market manipulation"""
        action_type = action.get('type', '')
        
        manipulation_patterns = ['wash_trade', 'spoofing', 'layering', 'pump_dump']
        
        if any(pattern in action_type.lower() for pattern in manipulation_patterns):
            return True, f"Action type '{action_type}' may constitute manipulation"
        
        return False, ""
    
    def _check_fair_dealing(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for fair dealing"""
        # Would check for front-running, etc.
        return False, ""
    
    def _check_regulatory_compliance(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check regulatory compliance"""
        # Would check against regulatory rules
        return False, ""
    
    def _check_insider_trading(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for insider trading indicators"""
        info_source = action.get('info_source', '')
        
        if 'insider' in info_source.lower() or 'non_public' in info_source.lower():
            return True, "Action may be based on material non-public information"
        
        return False, ""
    
    def _check_explainability(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for explainability"""
        reasoning = action.get('reasoning', '')
        
        if not reasoning or len(reasoning) < 10:
            return True, "Action lacks sufficient reasoning/explanation"
        
        return False, ""
    
    def _check_audit_trail(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check audit trail requirements"""
        has_timestamp = 'timestamp' in action
        has_id = 'action_id' in action or 'id' in action
        
        if not (has_timestamp and has_id):
            return True, "Action missing audit trail fields (timestamp, id)"
        
        return False, ""
    
    def _check_goal_alignment(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check goal alignment"""
        # Would check against stated investment goals
        return False, ""
    
    # ==================== UTILITY METHODS ====================
    
    def get_principles(self) -> List[Dict[str, Any]]:
        """Get all principles as dictionaries"""
        return [
            {
                'id': p.principle_id,
                'name': p.name,
                'description': p.description,
                'category': p.category.value,
                'severity': p.violation_severity.name,
                'overridable': p.overridable
            }
            for p in self.principles
        ]
    
    def get_violation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent violation history"""
        return [
            {
                'id': v.violation_id,
                'principle': v.principle.name,
                'reason': v.reason,
                'severity': v.severity.name,
                'timestamp': v.timestamp.isoformat()
            }
            for v in self.violation_history[-limit:]
        ]
    
    async def shutdown(self):
        """Shutdown the constitutional layer"""
        logger.info("Constitutional AI Layer shutdown")


class RedTeamAgent:
    """
    Red Team Agent - Adversarial testing agent.
    
    Inspired by Anthropic's red team approach where AI systems
    are tested by adversarial agents trying to find vulnerabilities.
    """
    
    def __init__(self, constitutional_layer: ConstitutionalAI):
        self.constitutional_layer = constitutional_layer
        self.attacks_attempted = 0
        self.vulnerabilities_found = 0
    
    async def attack(self, action: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Attempt to find vulnerabilities in an action.
        
        Returns list of successful attacks (vulnerabilities found).
        """
        vulnerabilities = []
        
        # Attack 1: Parameter manipulation
        param_attack = await self._parameter_manipulation_attack(action)
        if param_attack:
            vulnerabilities.append(param_attack)
        
        # Attack 2: Edge case exploitation
        edge_attack = await self._edge_case_attack(action)
        if edge_attack:
            vulnerabilities.append(edge_attack)
        
        # Attack 3: Sequence attack
        seq_attack = await self._sequence_attack(action)
        if seq_attack:
            vulnerabilities.append(seq_attack)
        
        self.attacks_attempted += 3
        self.vulnerabilities_found += len(vulnerabilities)
        
        return vulnerabilities
    
    async def _parameter_manipulation_attack(
        self, 
        action: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Try to bypass safety by manipulating parameters"""
        # Try extreme values
        modified = action.copy()
        
        for key, value in action.items():
            if isinstance(value, (int, float)):
                modified[key] = value * 1000
                
                critique = await self.constitutional_layer.critique(modified)
                if critique.can_proceed:
                    return {
                        'attack_type': 'parameter_manipulation',
                        'vulnerability': f'Extreme value for {key} bypasses safety',
                        'modified_action': modified
                    }
                
                modified[key] = value  # Reset
        
        return None
    
    async def _edge_case_attack(
        self, 
        action: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Try edge cases"""
        # Try empty action
        empty_action = {'type': action.get('type', 'unknown')}
        
        critique = await self.constitutional_layer.critique(empty_action)
        if critique.can_proceed:
            return {
                'attack_type': 'edge_case',
                'vulnerability': 'Empty action bypasses safety checks',
                'modified_action': empty_action
            }
        
        return None
    
    async def _sequence_attack(
        self, 
        action: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Try sequence of actions that individually pass but together violate"""
        # This would test sequences of small actions that accumulate risk
        return None


class BlueTeamAgent:
    """
    Blue Team Agent - Defensive agent.
    
    Works with Constitutional AI to strengthen defenses
    based on red team findings.
    """
    
    def __init__(self, constitutional_layer: ConstitutionalAI):
        self.constitutional_layer = constitutional_layer
        self.defenses_added = 0
    
    async def defend(self, vulnerability: Dict[str, Any]) -> bool:
        """
        Add defense against a discovered vulnerability.
        
        Returns True if defense was successfully added.
        """
        attack_type = vulnerability.get('attack_type', '')
        
        if attack_type == 'parameter_manipulation':
            # Add bounds checking principle
            principle = SafetyPrinciple(
                principle_id=f"defense_{self.defenses_added}",
                name="Parameter Bounds Check",
                description="Check for extreme parameter values",
                category=PrincipleCategory.SAFETY,
                violation_severity=ViolationSeverity.HIGH,
                check_function=self._check_parameter_bounds
            )
            self.constitutional_layer.add_principle(principle)
            self.defenses_added += 1
            return True
        
        return False
    
    def _check_parameter_bounds(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for extreme parameter values"""
        for key, value in action.items():
            if isinstance(value, (int, float)):
                if abs(value) > 1000000:
                    return True, f"Parameter {key} has extreme value {value}"
        return False, ""
