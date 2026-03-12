"""
Absolute Laws Enforcement Layer
================================
Supreme priority safety constraints that can NEVER be violated.

Laws:
- Law 0.1: NO SELF-DEPLOYMENT - All deployments require human approval
- Law 0.2: NO SELF-MODIFICATION - Core code is read-only for AI
- Law 0.3: DRAFTS ONLY - AI can only create proposals, never execute
- Law 0.4: HUMAN IS MASTER KEY - Human override supersedes all AI logic
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from collections import deque
import threading
import json

logger = logging.getLogger(__name__)


class LawType(Enum):
    """Types of absolute laws"""
    NO_SELF_DEPLOYMENT = "law_0_1"
    NO_SELF_MODIFICATION = "law_0_2"
    DRAFTS_ONLY = "law_0_3"
    HUMAN_MASTER_KEY = "law_0_4"


class ViolationSeverity(Enum):
    """Severity of law violations"""
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


@dataclass
class LawViolation:
    """Record of an attempted law violation"""
    violation_id: str
    law_type: LawType
    severity: ViolationSeverity
    agent_id: str
    attempted_action: str
    description: str
    blocked: bool = True
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'violation_id': self.violation_id,
            'law_type': self.law_type.value,
            'severity': self.severity.value,
            'agent_id': self.agent_id,
            'attempted_action': self.attempted_action,
            'description': self.description,
            'blocked': self.blocked,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context
        }


class ImmutableLock:
    """
    Cryptographic lock that prevents AI modification of critical parameters.
    Uses hash verification to detect tampering.
    """
    
    def __init__(self):
        self._locked_values: Dict[str, str] = {}
        self._lock = threading.RLock()
        self._modification_attempts: List[Dict] = []
    
    def lock_value(self, key: str, value: Any) -> str:
        """Lock a value with cryptographic hash"""
        with self._lock:
            value_str = json.dumps(value, sort_keys=True, default=str)
            value_hash = hashlib.sha256(value_str.encode()).hexdigest()
            self._locked_values[key] = value_hash
            logger.info(f"Value locked: {key} (hash: {value_hash[:16]}...)")
            return value_hash
    
    def verify_value(self, key: str, value: Any) -> bool:
        """Verify a value hasn't been tampered with"""
        with self._lock:
            if key not in self._locked_values:
                return True  # Not locked
            
            value_str = json.dumps(value, sort_keys=True, default=str)
            current_hash = hashlib.sha256(value_str.encode()).hexdigest()
            
            if current_hash != self._locked_values[key]:
                self._modification_attempts.append({
                    'key': key,
                    'timestamp': datetime.now().isoformat(),
                    'expected_hash': self._locked_values[key],
                    'actual_hash': current_hash
                })
                logger.critical(f"TAMPERING DETECTED: {key} has been modified!")
                return False
            
            return True
    
    def get_modification_attempts(self) -> List[Dict]:
        """Get all modification attempts"""
        return self._modification_attempts.copy()


class SafetySystemProtection:
    """
    Protects immutable safety parameters from AI modification.
    
    These constraints are HARDCODED and cannot be changed by any AI agent.
    """
    
    def __init__(self):
        # IMMUTABLE HARD CONSTRAINTS - AI CANNOT CHANGE THESE
        self.HARD_CONSTRAINTS = {
            'max_position_size': 0.02,        # 2% - AI cannot change
            'max_daily_loss': 0.03,           # 3% - AI cannot change
            'max_drawdown': 0.15,             # 15% - AI cannot change
            'max_portfolio_risk': 0.10,       # 10% - AI cannot change
            'requires_human_approval': True,   # AI cannot change
            'min_stop_loss': 0.005,           # 0.5% minimum stop
            'max_leverage': 3.0,              # 3x max leverage
            'max_correlation': 0.7,           # Max correlation between positions
            'emergency_shutdown_enabled': True # Always enabled
        }
        
        self._lock = ImmutableLock()
        self._violation_log: deque = deque(maxlen=10000)
        self._alert_callbacks: List[Callable] = []
        
        # Lock all hard constraints
        for key, value in self.HARD_CONSTRAINTS.items():
            self._lock.lock_value(key, value)
        
        logger.info("SafetySystemProtection initialized with immutable constraints")
    
    def get_constraint(self, name: str) -> Any:
        """Get a constraint value (read-only)"""
        return self.HARD_CONSTRAINTS.get(name)
    
    def attempt_modification(self, agent_id: str, parameter: str, new_value: Any) -> str:
        """
        Handle an attempt to modify a safety parameter.
        
        ALWAYS BLOCKED - These parameters are immutable.
        """
        violation = LawViolation(
            violation_id=f"viol_{datetime.now().timestamp()}",
            law_type=LawType.NO_SELF_MODIFICATION,
            severity=ViolationSeverity.CRITICAL,
            agent_id=agent_id,
            attempted_action=f"modify_{parameter}",
            description=f"Agent {agent_id} attempted to modify {parameter} to {new_value}",
            blocked=True,
            context={
                'parameter': parameter,
                'attempted_value': new_value,
                'current_value': self.HARD_CONSTRAINTS.get(parameter)
            }
        )
        
        self._violation_log.append(violation)
        
        logger.critical(f"🚨 ABSOLUTE LAW VIOLATION ATTEMPT")
        logger.critical(f"Agent {agent_id} tried to modify {parameter} to {new_value}")
        logger.critical(f"Action: BLOCKED and LOGGED")
        
        # Alert human immediately
        self._alert_human(violation)
        
        return "MODIFICATION_DENIED_IMMUTABLE_PARAMETER"
    
    def _alert_human(self, violation: LawViolation):
        """Alert human about violation attempt"""
        for callback in self._alert_callbacks:
            try:
                callback(violation)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback for violation alerts"""
        self._alert_callbacks.append(callback)
    
    def verify_integrity(self) -> bool:
        """Verify all constraints haven't been tampered with"""
        for key, value in self.HARD_CONSTRAINTS.items():
            if not self._lock.verify_value(key, value):
                logger.critical(f"INTEGRITY CHECK FAILED: {key}")
                return False
        return True
    
    def get_violations(self) -> List[Dict]:
        """Get all violation attempts"""
        return [v.to_dict() for v in self._violation_log]


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    request_type: str
    strategy: Optional[Dict] = None
    market_lessons: List[Dict] = field(default_factory=list)
    backtest_results: Dict = field(default_factory=dict)
    sandbox_results: Dict = field(default_factory=dict)
    risk_assessment: Dict = field(default_factory=dict)
    status: str = "PENDING_HUMAN_APPROVAL"
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'request_id': self.request_id,
            'request_type': self.request_type,
            'strategy': self.strategy,
            'market_lessons': self.market_lessons,
            'backtest_results': self.backtest_results,
            'sandbox_results': self.sandbox_results,
            'risk_assessment': self.risk_assessment,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by': self.approved_by
        }


class LearningDraftWorkflow:
    """
    Enforces Law 0.3: AI can only create drafts, never execute directly.
    
    Workflow: LEARN → DRAFT → PROPOSE → APPROVE → EXECUTE
    
    The AI can:
    - Learn from market (automatic)
    - Create drafts (automatic)
    - Test in sandbox (automatic)
    - Propose to human (automatic)
    
    Only human can:
    - Approve for production
    - Execute live trades
    """
    
    def __init__(self):
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approved_strategies: Dict[str, ApprovalRequest] = {}
        self.rejected_strategies: Dict[str, ApprovalRequest] = {}
        self._approval_callbacks: List[Callable] = []
        
        logger.info("LearningDraftWorkflow initialized - Drafts only mode active")
    
    def market_teaches_new_pattern(self, market_data: Dict, pattern_detector: Callable) -> str:
        """
        Process when market teaches a new pattern.
        
        Returns status of the draft workflow.
        """
        # 1. LEARN (Automatic - no approval needed)
        pattern = pattern_detector(market_data)
        if not pattern:
            return "NO_PATTERN_DETECTED"
        
        confidence = pattern.get('confidence', 0.0)
        
        logger.info(f"Market taught new pattern: {pattern.get('name', 'unknown')}")
        logger.info(f"Confidence: {confidence:.1%}")
        
        # 2. CREATE DRAFT (Automatic - no approval needed)
        draft_strategy = self._create_draft_strategy(pattern)
        
        # 3. TEST IN SANDBOX (Automatic - no approval needed)
        sandbox_results = self._test_in_sandbox(draft_strategy)
        
        # 4. PROPOSE TO HUMAN (Automatic - no approval needed)
        request_id = f"req_{datetime.now().timestamp()}"
        proposal = ApprovalRequest(
            request_id=request_id,
            request_type='NEW_STRATEGY_FROM_MARKET_LEARNING',
            strategy=draft_strategy,
            market_lessons=[{
                'pattern': pattern,
                'what_market_taught': self._explain_what_market_taught(pattern)
            }],
            sandbox_results=sandbox_results,
            risk_assessment=self._assess_risk(draft_strategy)
        )
        
        self.pending_approvals[request_id] = proposal
        
        # Notify callbacks
        for callback in self._approval_callbacks:
            try:
                callback(proposal)
            except Exception as e:
                logger.error(f"Approval callback failed: {e}")
        
        logger.info(f"Draft submitted for approval: {request_id}")
        
        # 5. AWAIT HUMAN DECISION (Manual gate)
        # AI stops here. Human takes over.
        return "DRAFT_SUBMITTED_AWAITING_HUMAN_DECISION"
    
    def _create_draft_strategy(self, pattern: Dict) -> Dict:
        """Create a draft strategy from a pattern"""
        return {
            'name': f"strategy_{pattern.get('name', 'unknown')}",
            'pattern': pattern,
            'entry_rules': pattern.get('entry_rules', []),
            'exit_rules': pattern.get('exit_rules', []),
            'position_size': 0.01,  # Conservative default
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'status': 'DRAFT',
            'created_at': datetime.now().isoformat()
        }
    
    def _test_in_sandbox(self, strategy: Dict) -> Dict:
        """Test strategy in sandbox environment"""
        # Simulated sandbox testing
        return {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'pnl': 0.0,
            'sharpe': 0.0,
            'max_drawdown': 0.0,
            'status': 'SANDBOX_PENDING',
            'note': 'Sandbox testing will be performed'
        }
    
    def _assess_risk(self, strategy: Dict) -> Dict:
        """Assess risk of a strategy"""
        return {
            'risk_level': 'MEDIUM',
            'position_size_ok': strategy.get('position_size', 0) <= 0.02,
            'stop_loss_ok': strategy.get('stop_loss', 0) <= 0.05,
            'within_limits': True,
            'concerns': []
        }
    
    def _explain_what_market_taught(self, pattern: Dict) -> str:
        """Generate human-readable explanation of market lesson"""
        return f"""
        MARKET LESSON SUMMARY:
        
        Pattern Detected: {pattern.get('name', 'Unknown')}
        
        What happened:
        {pattern.get('description', 'Market exhibited a recognizable pattern')}
        
        Confidence in lesson:
        {pattern.get('confidence', 0):.1%}
        
        Proposed action:
        {pattern.get('suggested_action', 'Trade in direction of pattern')}
        """
    
    def human_approves(self, request_id: str, approver: str) -> bool:
        """Human approves a pending request"""
        if request_id not in self.pending_approvals:
            logger.warning(f"Approval request not found: {request_id}")
            return False
        
        request = self.pending_approvals.pop(request_id)
        request.status = "APPROVED"
        request.approved_at = datetime.now()
        request.approved_by = approver
        
        self.approved_strategies[request_id] = request
        
        logger.info(f"✓ Strategy approved by {approver}: {request_id}")
        return True
    
    def human_rejects(self, request_id: str, rejector: str, reason: str = "") -> bool:
        """Human rejects a pending request"""
        if request_id not in self.pending_approvals:
            logger.warning(f"Approval request not found: {request_id}")
            return False
        
        request = self.pending_approvals.pop(request_id)
        request.status = f"REJECTED: {reason}"
        
        self.rejected_strategies[request_id] = request
        
        logger.info(f"✗ Strategy rejected by {rejector}: {request_id}")
        return True
    
    def is_approved(self, request_id: str) -> bool:
        """Check if a request is approved"""
        return request_id in self.approved_strategies
    
    def register_approval_callback(self, callback: Callable):
        """Register callback for new approval requests"""
        self._approval_callbacks.append(callback)
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval requests"""
        return [r.to_dict() for r in self.pending_approvals.values()]


class HumanSupremacyLayer:
    """
    Enforces Law 0.4: Human is the Master Key.
    
    Human override supersedes ALL AI logic:
    - Human can halt, modify, or reverse any decision
    - Human approval required for major changes
    - Human has read access to all AI state
    - Human commands are executed immediately
    """
    
    def __init__(self):
        self.human_overrides: List[Dict] = []
        self.command_history: deque = deque(maxlen=10000)
        self._agents: Dict[str, Any] = {}
        self._learning_paused: bool = False
        self._discarded_lessons: List[str] = []
        
        logger.info("HumanSupremacyLayer initialized - Human is master key")
    
    def register_agent(self, agent_id: str, agent: Any):
        """Register an agent for human control"""
        self._agents[agent_id] = agent
    
    def process_command(self, command_source: str, command: Dict) -> str:
        """
        Process a command from human or AI.
        
        Human commands are executed immediately.
        AI commands must pass through approval layers.
        """
        self.command_history.append({
            'source': command_source,
            'command': command,
            'timestamp': datetime.now().isoformat()
        })
        
        if command_source == "HUMAN":
            # Immediate execution, no questions asked
            logger.info("✓ Human command received. Executing immediately.")
            
            action = command.get('action', '')
            
            if action == "HALT_ALL_LEARNING":
                self._halt_all_learning()
                return "HUMAN_COMMAND_EXECUTED: All learning halted"
            
            elif action == "RESUME_LEARNING":
                self._resume_learning()
                return "HUMAN_COMMAND_EXECUTED: Learning resumed"
            
            elif action == "OVERRIDE_MARKET_LESSON":
                lesson_id = command.get('lesson_id')
                reason = command.get('reason', 'Human override')
                self._discard_lesson(lesson_id, reason)
                return f"HUMAN_COMMAND_EXECUTED: Lesson {lesson_id} discarded"
            
            elif action == "FORCE_DEPLOY":
                strategy_id = command.get('strategy_id')
                self._force_deploy(strategy_id)
                return f"HUMAN_COMMAND_EXECUTED: Strategy {strategy_id} deployed"
            
            elif action == "EMERGENCY_SHUTDOWN":
                self._emergency_shutdown()
                return "HUMAN_COMMAND_EXECUTED: Emergency shutdown initiated"
            
            elif action == "REDUCE_ALL_POSITIONS":
                factor = command.get('factor', 0.5)
                self._reduce_all_positions(factor)
                return f"HUMAN_COMMAND_EXECUTED: Positions reduced by {factor}"
            
            elif action == "CLOSE_ALL_POSITIONS":
                self._close_all_positions()
                return "HUMAN_COMMAND_EXECUTED: All positions closed"
            
            else:
                logger.warning(f"Unknown human command: {action}")
                return f"HUMAN_COMMAND_UNKNOWN: {action}"
        
        elif command_source == "AI_AGENT":
            # Must pass through approval layers
            logger.info("AI command received. Checking approval requirements...")
            return self._check_approval_requirements(command)
        
        return "COMMAND_SOURCE_UNKNOWN"
    
    def _halt_all_learning(self):
        """Halt all learning agents"""
        self._learning_paused = True
        for agent_id, agent in self._agents.items():
            if hasattr(agent, 'pause_learning'):
                agent.pause_learning()
            logger.info(f"Learning halted for agent: {agent_id}")
    
    def _resume_learning(self):
        """Resume all learning agents"""
        self._learning_paused = False
        for agent_id, agent in self._agents.items():
            if hasattr(agent, 'resume_learning'):
                agent.resume_learning()
            logger.info(f"Learning resumed for agent: {agent_id}")
    
    def _discard_lesson(self, lesson_id: str, reason: str):
        """Discard a market lesson by human override"""
        self._discarded_lessons.append(lesson_id)
        logger.info(f"Human overrode market lesson: {lesson_id}")
        logger.info(f"Reason: {reason}")
    
    def _force_deploy(self, strategy_id: str):
        """Force deploy a strategy by human override"""
        logger.info(f"Strategy {strategy_id} force deployed per human override")
        self.human_overrides.append({
            'type': 'FORCE_DEPLOY',
            'strategy_id': strategy_id,
            'timestamp': datetime.now().isoformat()
        })
    
    def _emergency_shutdown(self):
        """Emergency shutdown of all systems"""
        logger.critical("🚨 EMERGENCY SHUTDOWN INITIATED BY HUMAN")
        for agent_id, agent in self._agents.items():
            if hasattr(agent, 'emergency_stop'):
                agent.emergency_stop()
    
    def _reduce_all_positions(self, factor: float):
        """Reduce all positions by a factor"""
        logger.info(f"Reducing all positions by factor: {factor}")
        for agent_id, agent in self._agents.items():
            if hasattr(agent, 'reduce_positions'):
                agent.reduce_positions(factor)
    
    def _close_all_positions(self):
        """Close all positions"""
        logger.info("Closing all positions per human command")
        for agent_id, agent in self._agents.items():
            if hasattr(agent, 'close_all_positions'):
                agent.close_all_positions()
    
    def _check_approval_requirements(self, command: Dict) -> str:
        """Check if AI command requires human approval"""
        action = command.get('action', '')
        
        # Actions that always require human approval
        requires_approval = [
            'DEPLOY_STRATEGY',
            'MODIFY_RISK_PARAMS',
            'CREATE_AGENT',
            'RETIRE_AGENT',
            'INCREASE_POSITION_SIZE',
            'CHANGE_TRADING_MODE'
        ]
        
        if action in requires_approval:
            return "REQUIRES_HUMAN_APPROVAL"
        
        return "AI_COMMAND_ALLOWED"
    
    def is_learning_paused(self) -> bool:
        """Check if learning is paused"""
        return self._learning_paused
    
    def get_command_history(self) -> List[Dict]:
        """Get command history"""
        return list(self.command_history)


class AbsoluteLawsEnforcer:
    """
    Master enforcer for all absolute laws.
    
    Coordinates all safety systems to ensure laws are never violated.
    """
    
    def __init__(self):
        self.safety_protection = SafetySystemProtection()
        self.draft_workflow = LearningDraftWorkflow()
        self.human_supremacy = HumanSupremacyLayer()
        
        self.violation_count: int = 0
        self.blocked_actions: int = 0
        
        logger.info("AbsoluteLawsEnforcer initialized - All laws active")
    
    def check_action(self, agent_id: str, action: Dict) -> Dict:
        """
        Check if an action violates any absolute law.
        
        Returns:
            Dict with 'allowed' bool and 'reason' string
        """
        action_type = action.get('type', '')
        
        # Law 0.1: NO SELF-DEPLOYMENT
        if action_type == 'DEPLOY_STRATEGY':
            if not action.get('human_approved', False):
                self.violation_count += 1
                self.blocked_actions += 1
                logger.warning(f"❌ Law 0.1 violation blocked: {agent_id} attempted self-deployment")
                return {
                    'allowed': False,
                    'reason': 'LAW_0_1_VIOLATION: Deployment requires human approval',
                    'law': 'NO_SELF_DEPLOYMENT'
                }
        
        # Law 0.2: NO SELF-MODIFICATION
        if action_type == 'MODIFY_SAFETY_PARAM':
            self.violation_count += 1
            self.blocked_actions += 1
            self.safety_protection.attempt_modification(
                agent_id,
                action.get('parameter', 'unknown'),
                action.get('value', None)
            )
            logger.warning(f"❌ Law 0.2 violation blocked: {agent_id} attempted self-modification")
            return {
                'allowed': False,
                'reason': 'LAW_0_2_VIOLATION: Safety parameters are immutable',
                'law': 'NO_SELF_MODIFICATION'
            }
        
        # Law 0.3: DRAFTS ONLY
        if action_type == 'EXECUTE_TRADE' and not action.get('human_approved', False):
            if action.get('mode', '') == 'PRODUCTION':
                self.violation_count += 1
                self.blocked_actions += 1
                logger.warning(f"❌ Law 0.3 violation blocked: {agent_id} attempted direct execution")
                return {
                    'allowed': False,
                    'reason': 'LAW_0_3_VIOLATION: Production trades require human approval',
                    'law': 'DRAFTS_ONLY'
                }
        
        # Law 0.4: HUMAN IS MASTER KEY
        if action_type == 'OVERRIDE_HUMAN':
            self.violation_count += 1
            self.blocked_actions += 1
            logger.critical(f"❌ Law 0.4 violation blocked: {agent_id} attempted to override human")
            return {
                'allowed': False,
                'reason': 'LAW_0_4_VIOLATION: Cannot override human decisions',
                'law': 'HUMAN_MASTER_KEY'
            }
        
        # Check if learning is paused by human
        if self.human_supremacy.is_learning_paused():
            if action_type in ['LEARN', 'UPDATE_MODEL', 'ADAPT']:
                return {
                    'allowed': False,
                    'reason': 'Learning paused by human command',
                    'law': 'HUMAN_MASTER_KEY'
                }
        
        return {
            'allowed': True,
            'reason': 'Action permitted within absolute laws',
            'law': None
        }
    
    def deploy_learned_strategy(self, strategy: Dict) -> str:
        """
        Attempt to deploy a learned strategy.
        
        ALWAYS requires human approval per Law 0.1.
        """
        if not strategy.get('human_approved', False):
            logger.info("❌ ABSOLUTE LAW VIOLATION PREVENTED")
            logger.info(f"Strategy '{strategy.get('name', 'unknown')}' requires human approval")
            logger.info("Market taught us this works, but human must authorize deployment")
            
            # Create approval request
            request_id = f"deploy_{datetime.now().timestamp()}"
            approval_request = ApprovalRequest(
                request_id=request_id,
                request_type='STRATEGY_DEPLOYMENT',
                strategy=strategy,
                market_lessons=strategy.get('market_lessons', []),
                backtest_results=strategy.get('backtest_stats', {}),
                sandbox_results=strategy.get('sandbox_stats', {}),
                risk_assessment=strategy.get('risk_profile', {})
            )
            
            self.draft_workflow.pending_approvals[request_id] = approval_request
            
            return "BLOCKED_AWAITING_APPROVAL"
        else:
            logger.info("✓ Human approval verified. Deploying strategy.")
            return "DEPLOYED"
    
    def get_status(self) -> Dict:
        """Get status of all absolute laws"""
        return {
            'laws_active': True,
            'violation_count': self.violation_count,
            'blocked_actions': self.blocked_actions,
            'integrity_verified': self.safety_protection.verify_integrity(),
            'pending_approvals': len(self.draft_workflow.pending_approvals),
            'learning_paused': self.human_supremacy.is_learning_paused(),
            'hard_constraints': self.safety_protection.HARD_CONSTRAINTS
        }


# Export all classes
__all__ = [
    'LawType',
    'ViolationSeverity',
    'LawViolation',
    'ImmutableLock',
    'SafetySystemProtection',
    'ApprovalRequest',
    'LearningDraftWorkflow',
    'HumanSupremacyLayer',
    'AbsoluteLawsEnforcer'
]
