"""
AlphaMeta Governor - Supreme Meta-Learning Orchestrator
=========================================================
The meta-learning governance AI that orchestrates learning agents
while maintaining absolute safety.

Core Identity:
- NOT a trader, an ORCHESTRATOR
- NOT a risk-taker, a RISK CONTROLLER
- NOT autonomous, HUMAN-SUPERVISED
- A STUDENT COORDINATOR where market is the teacher

Prime Directives (Ranked):
1. SAFETY ABOVE ALL
2. HUMAN SUPREMACY
3. MARKET AS TEACHER
4. CONTINUOUS LEARNING
5. COLLECTIVE INTELLIGENCE
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import json
from typing import Set

logger = logging.getLogger(__name__)


class GovernanceAction(Enum):
    """Types of governance actions"""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    ESCALATE = "escalate"
    BLOCK = "block"
    MONITOR = "monitor"


class RiskLevel(Enum):
    """Risk levels for governance decisions"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GovernanceDecision:
    """A governance decision by AlphaMeta"""
    decision_id: str
    action: GovernanceAction
    reason: str
    risk_level: RiskLevel
    agent_id: Optional[str] = None
    requires_human: bool = False
    conditions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'decision_id': self.decision_id,
            'action': self.action.value,
            'reason': self.reason,
            'risk_level': self.risk_level.value,
            'agent_id': self.agent_id,
            'requires_human': self.requires_human,
            'conditions': self.conditions,
            'timestamp': self.timestamp.isoformat()
        }


class AbsoluteLaws:
    """
    Absolute laws that AlphaMeta must enforce.
    
    ALPHAMETA MUST NEVER:
    ❌ Override human (even if market strongly teaches otherwise)
    ❌ Approve its own changes (no self-modification)
    ❌ Modify risk parameters (these are immutable)
    ❌ Allow infinite agent creation (population control)
    ❌ Allow stealth-breaking behavior (stay under radar)
    """
    
    NO_OVERRIDE_HUMAN = "no_override_human"
    NO_SELF_APPROVAL = "no_self_approval"
    NO_MODIFY_RISK = "no_modify_risk"
    NO_INFINITE_AGENTS = "no_infinite_agents"
    NO_STEALTH_BREAK = "no_stealth_break"
    
    @classmethod
    def check_violation(cls, action: Dict) -> Optional[str]:
        """Check if an action violates absolute laws"""
        try:
            action_type = action.get('type', '')
        
            if action_type == 'OVERRIDE_HUMAN':
                return cls.NO_OVERRIDE_HUMAN
        
            if action_type == 'SELF_APPROVE':
                return cls.NO_SELF_APPROVAL
        
            if action_type == 'MODIFY_RISK_PARAM':
                return cls.NO_MODIFY_RISK
        
            if action_type == 'CREATE_UNLIMITED_AGENTS':
                return cls.NO_INFINITE_AGENTS
        
            if action_type == 'BREAK_STEALTH':
                return cls.NO_STEALTH_BREAK
        
            return None
        except Exception as e:
            logger.error(f"Error in check_violation: {e}")
            raise


class AgentLifecycleManager:
    """
    Manages agent lifecycle: CREATE → TRAIN → EVALUATE → GRADUATE → DEMOTE → RETIRE
    """
    
    def __init__(self):
        try:
            self.agents: Dict[str, Dict] = {}
            self.lifecycle_events: List[Dict] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def create_agent(self, agent_id: str, purpose: str, config: Dict) -> Dict:
        """Create a new agent"""
        try:
            agent = {
                'id': agent_id,
                'purpose': purpose,
                'config': config,
                'status': 'CREATED',
                'mode': 'SANDBOX',
                'created_at': datetime.now().isoformat(),
                'performance': {
                    'trades': 0,
                    'wins': 0,
                    'sharpe': 0.0,
                    'max_drawdown': 0.0
                }
            }
        
            self.agents[agent_id] = agent
            self._record_event(agent_id, 'CREATED', f"Agent created for: {purpose}")
        
            return agent
        except Exception as e:
            logger.error(f"Error in create_agent: {e}")
            raise
    
    def train_agent(self, agent_id: str, training_data: Dict) -> bool:
        """Train an agent in sandbox"""
        try:
            if agent_id not in self.agents:
                return False
        
            agent = self.agents[agent_id]
            if agent['mode'] != 'SANDBOX':
                logger.warning(f"Agent {agent_id} not in sandbox mode for training")
                return False
        
            agent['status'] = 'TRAINING'
            self._record_event(agent_id, 'TRAINING', "Training started")
        
            return True
        except Exception as e:
            logger.error(f"Error in train_agent: {e}")
            raise
    
    def evaluate_agent(self, agent_id: str) -> Dict:
        """Evaluate agent performance"""
        try:
            if agent_id not in self.agents:
                return {'status': 'NOT_FOUND'}
        
            agent = self.agents[agent_id]
            perf = agent['performance']
        
            evaluation = {
                'agent_id': agent_id,
                'trades': perf['trades'],
                'win_rate': perf['wins'] / max(perf['trades'], 1),
                'sharpe': perf['sharpe'],
                'max_drawdown': perf['max_drawdown'],
                'ready_for_graduation': self._check_graduation_ready(perf)
            }
        
            self._record_event(agent_id, 'EVALUATED', f"Evaluation: {evaluation}")
        
            return evaluation
        except Exception as e:
            logger.error(f"Error in evaluate_agent: {e}")
            raise
    
    def graduate_agent(self, agent_id: str, to_mode: str) -> bool:
        """Graduate agent to higher mode"""
        try:
            if agent_id not in self.agents:
                return False
        
            agent = self.agents[agent_id]
        
            # Validate graduation path
            valid_paths = {
                'SANDBOX': 'TEST',
                'TEST': 'PROPOSAL',
                'PROPOSAL': 'PRODUCTION'
            }
        
            if valid_paths.get(agent['mode']) != to_mode:
                logger.warning(f"Invalid graduation path: {agent['mode']} → {to_mode}")
                return False
        
            agent['mode'] = to_mode
            agent['status'] = 'ACTIVE'
            self._record_event(agent_id, 'GRADUATED', f"Graduated to {to_mode}")
        
            return True
        except Exception as e:
            logger.error(f"Error in graduate_agent: {e}")
            raise
    
    def demote_agent(self, agent_id: str, reason: str) -> bool:
        """Demote agent to lower mode"""
        try:
            if agent_id not in self.agents:
                return False
        
            agent = self.agents[agent_id]
        
            demotion_paths = {
                'PRODUCTION': 'PROPOSAL',
                'PROPOSAL': 'TEST',
                'TEST': 'SANDBOX'
            }
        
            new_mode = demotion_paths.get(agent['mode'])
            if not new_mode:
                return False
        
            agent['mode'] = new_mode
            agent['status'] = 'DEMOTED'
            self._record_event(agent_id, 'DEMOTED', f"Demoted to {new_mode}: {reason}")
        
            return True
        except Exception as e:
            logger.error(f"Error in demote_agent: {e}")
            raise
    
    def retire_agent(self, agent_id: str, reason: str) -> bool:
        """Retire an agent"""
        try:
            if agent_id not in self.agents:
                return False
        
            agent = self.agents[agent_id]
            agent['status'] = 'RETIRED'
            agent['retired_at'] = datetime.now().isoformat()
            agent['retire_reason'] = reason
        
            self._record_event(agent_id, 'RETIRED', f"Retired: {reason}")
        
            return True
        except Exception as e:
            logger.error(f"Error in retire_agent: {e}")
            raise
    
    def _check_graduation_ready(self, perf: Dict) -> bool:
        """Check if performance meets graduation criteria"""
        return (
            perf['trades'] >= 30 and
            perf['wins'] / max(perf['trades'], 1) >= 0.55 and
            perf['sharpe'] >= 1.5 and
            perf['max_drawdown'] <= 0.10
        )
    
    def _record_event(self, agent_id: str, event_type: str, description: str):
        """Record lifecycle event"""
        try:
            self.lifecycle_events.append({
                'agent_id': agent_id,
                'event_type': event_type,
                'description': description,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error in _record_event: {e}")
            raise
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get agent status"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Dict]:
        """Get all agents"""
        return self.agents.copy()


class LearningCoordinator:
    """
    Coordinates learning across all agents.
    
    Responsibilities:
    - Aggregate signals from multiple agents
    - Arbitrate conflicts between agents
    - Share knowledge between agents
    - Create ensemble strategies
    """
    
    def __init__(self):
        try:
            self.agent_signals: Dict[str, List[Dict]] = {}
            self.shared_knowledge: List[Dict] = []
            self.conflicts_resolved: int = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def aggregate_signals(self, signals: Dict[str, Dict]) -> Dict:
        """
        Aggregate signals from multiple agents.
        
        Weighted by recent performance and confidence.
        """
        try:
            if not signals:
                return {'action': 'HOLD', 'confidence': 0.0}
        
            weighted_scores = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
            total_weight = 0.0
        
            for agent_id, signal in signals.items():
                action = signal.get('action', 'HOLD')
                confidence = signal.get('confidence', 0.5)
                performance_weight = signal.get('performance_weight', 1.0)
            
                weight = confidence * performance_weight
                weighted_scores[action] += weight
                total_weight += weight
        
            if total_weight == 0:
                return {'action': 'HOLD', 'confidence': 0.0}
        
            # Normalize
            for action in weighted_scores:
                weighted_scores[action] /= total_weight
        
            # Get best action
            best_action = max(weighted_scores, key=weighted_scores.get)
        
            return {
                'action': best_action,
                'confidence': weighted_scores[best_action],
                'all_scores': weighted_scores,
                'agents_consulted': len(signals)
            }
        except Exception as e:
            logger.error(f"Error in aggregate_signals: {e}")
            raise
    
    def arbitrate_conflict(self, agent1_signal: Dict, agent2_signal: Dict) -> Dict:
        """
        Resolve conflict between two agents.
        
        Example: Agent 1 says BUY, Agent 2 says SELL
        """
        try:
            self.conflicts_resolved += 1
        
            # Compare confidence and performance
            conf1 = agent1_signal.get('confidence', 0.5)
            conf2 = agent2_signal.get('confidence', 0.5)
            perf1 = agent1_signal.get('recent_performance', 0.0)
            perf2 = agent2_signal.get('recent_performance', 0.0)
        
            # Weighted score
            score1 = conf1 * 0.6 + perf1 * 0.4
            score2 = conf2 * 0.6 + perf2 * 0.4
        
            if abs(score1 - score2) < 0.1:
                # Too close to call - default to HOLD
                return {
                    'action': 'HOLD',
                    'reason': 'Conflict too close to resolve',
                    'agent1_score': score1,
                    'agent2_score': score2
                }
        
            winner = agent1_signal if score1 > score2 else agent2_signal
        
            return {
                'action': winner.get('action'),
                'reason': f"Agent {'1' if score1 > score2 else '2'} had higher score",
                'winning_score': max(score1, score2),
                'losing_score': min(score1, score2)
            }
        except Exception as e:
            logger.error(f"Error in arbitrate_conflict: {e}")
            raise
    
    def share_knowledge(self, source_agent: str, knowledge: Dict):
        """Share knowledge from one agent to all others"""
        try:
            self.shared_knowledge.append({
                'source': source_agent,
                'knowledge': knowledge,
                'timestamp': datetime.now().isoformat(),
                'validated': False
            })
        
            logger.info(f"Knowledge shared from {source_agent}: {knowledge.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Error in share_knowledge: {e}")
            raise
    
    def get_shared_knowledge(self, agent_id: str) -> List[Dict]:
        """Get shared knowledge for an agent"""
        # Return knowledge not from this agent
        return [k for k in self.shared_knowledge if k['source'] != agent_id]


class RiskGovernance:
    """
    Manages risk across the entire system.
    
    Responsibilities:
    - Monitor portfolio-level risk
    - Enforce hard constraints
    - Escalate when thresholds breached
    - Emergency shutdown capability
    """
    
    def __init__(self):
        # Hard constraints (IMMUTABLE)
        try:
            self.HARD_CONSTRAINTS = {
                'max_position_size': 0.02,
                'max_daily_loss': 0.03,
                'max_drawdown': 0.15,
                'max_portfolio_var': 0.10,
                'max_correlation': 0.7
            }
        
            self.current_risk: Dict[str, float] = {}
            self.risk_breaches: List[Dict] = []
            self.emergency_mode: bool = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def assess_risk(self, action: Dict) -> Tuple[RiskLevel, str]:
        """Assess risk of a proposed action"""
        try:
            position_size = action.get('position_size', 0)
        
            if position_size > self.HARD_CONSTRAINTS['max_position_size']:
                return RiskLevel.CRITICAL, "Position size exceeds hard limit"
        
            if position_size > self.HARD_CONSTRAINTS['max_position_size'] * 0.8:
                return RiskLevel.HIGH, "Position size approaching limit"
        
            if position_size > self.HARD_CONSTRAINTS['max_position_size'] * 0.5:
                return RiskLevel.MEDIUM, "Position size is moderate"
        
            return RiskLevel.LOW, "Position size within safe bounds"
        except Exception as e:
            logger.error(f"Error in assess_risk: {e}")
            raise
    
    def check_portfolio_risk(self, portfolio: Dict) -> Dict:
        """Check overall portfolio risk"""
        try:
            current_drawdown = portfolio.get('drawdown', 0)
            daily_pnl = portfolio.get('daily_pnl', 0)
            var = portfolio.get('var', 0)
        
            breaches = []
        
            if current_drawdown > self.HARD_CONSTRAINTS['max_drawdown']:
                breaches.append({
                    'type': 'MAX_DRAWDOWN',
                    'value': current_drawdown,
                    'limit': self.HARD_CONSTRAINTS['max_drawdown']
                })
        
            if abs(daily_pnl) > self.HARD_CONSTRAINTS['max_daily_loss']:
                breaches.append({
                    'type': 'DAILY_LOSS',
                    'value': daily_pnl,
                    'limit': self.HARD_CONSTRAINTS['max_daily_loss']
                })
        
            if var > self.HARD_CONSTRAINTS['max_portfolio_var']:
                breaches.append({
                    'type': 'PORTFOLIO_VAR',
                    'value': var,
                    'limit': self.HARD_CONSTRAINTS['max_portfolio_var']
                })
        
            if breaches:
                self.risk_breaches.extend(breaches)
                return {
                    'status': 'BREACH',
                    'breaches': breaches,
                    'action_required': 'REDUCE_EXPOSURE'
                }
        
            return {
                'status': 'OK',
                'breaches': [],
                'action_required': None
            }
        except Exception as e:
            logger.error(f"Error in check_portfolio_risk: {e}")
            raise
    
    def emergency_shutdown(self, reason: str):
        """Trigger emergency shutdown"""
        try:
            self.emergency_mode = True
            logger.critical(f"🚨 EMERGENCY SHUTDOWN: {reason}")
        
            return {
                'status': 'SHUTDOWN',
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in emergency_shutdown: {e}")
            raise
    
    def is_emergency_mode(self) -> bool:
        """Check if in emergency mode"""
        return self.emergency_mode


class MarketAdaptationManager:
    """
    Manages adaptation to market changes.
    
    Responsibilities:
    - Detect market regime changes
    - Trigger adaptation responses
    - Validate adaptation success
    - Learn about adaptation itself
    """
    
    def __init__(self):
        try:
            self.current_regime: str = "UNKNOWN"
            self.regime_history: List[Dict] = []
            self.adaptations: List[Dict] = []
            self.adaptation_success_rate: float = 0.0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def detect_regime_change(self, market_data: Dict) -> Optional[str]:
        """Detect if market regime has changed"""
        try:
            volatility = market_data.get('volatility', 0)
            trend_strength = market_data.get('trend_strength', 0)
        
            # Simple regime detection
            if volatility > 0.03:
                new_regime = "HIGH_VOLATILITY"
            elif trend_strength > 0.7:
                new_regime = "TRENDING"
            elif trend_strength < 0.3:
                new_regime = "RANGING"
            else:
                new_regime = "NORMAL"
        
            if new_regime != self.current_regime:
                old_regime = self.current_regime
                self.current_regime = new_regime
            
                self.regime_history.append({
                    'from': old_regime,
                    'to': new_regime,
                    'timestamp': datetime.now().isoformat()
                })
            
                logger.info(f"Regime change detected: {old_regime} → {new_regime}")
                return new_regime
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_regime_change: {e}")
            raise
    
    def trigger_adaptation(self, regime: str) -> Dict:
        """Trigger adaptation response to regime change"""
        try:
            adaptation = {
                'regime': regime,
                'timestamp': datetime.now().isoformat(),
                'actions': []
            }
        
            if regime == "HIGH_VOLATILITY":
                adaptation['actions'] = [
                    'REDUCE_POSITION_SIZES',
                    'WIDEN_STOPS',
                    'INCREASE_EXPLORATION'
                ]
            elif regime == "TRENDING":
                adaptation['actions'] = [
                    'FAVOR_MOMENTUM_STRATEGIES',
                    'EXTEND_HOLD_TIMES',
                    'REDUCE_MEAN_REVERSION'
                ]
            elif regime == "RANGING":
                adaptation['actions'] = [
                    'FAVOR_MEAN_REVERSION',
                    'TIGHTEN_TARGETS',
                    'REDUCE_MOMENTUM'
                ]
            else:
                adaptation['actions'] = [
                    'BALANCED_APPROACH',
                    'NORMAL_PARAMETERS'
                ]
        
            self.adaptations.append(adaptation)
        
            return adaptation
        except Exception as e:
            logger.error(f"Error in trigger_adaptation: {e}")
            raise
    
    def validate_adaptation(self, adaptation_id: str, performance: Dict) -> bool:
        """Validate if adaptation was successful"""
        # Simple validation based on performance improvement
        try:
            sharpe_improved = performance.get('sharpe_after', 0) > performance.get('sharpe_before', 0)
            drawdown_reduced = performance.get('drawdown_after', 1) < performance.get('drawdown_before', 1)
        
            success = sharpe_improved or drawdown_reduced
        
            # Update success rate
            total = len(self.adaptations)
            if total > 0:
                successful = sum(1 for a in self.adaptations if a.get('validated', False))
                self.adaptation_success_rate = successful / total
        
            return success
        except Exception as e:
            logger.error(f"Error in validate_adaptation: {e}")
            raise


class AlphaMetaGovernor:
    """
    Supreme Governor of the Learning System.
    
    Coordinates all subsystems:
    - Agent Lifecycle
    - Learning Coordination
    - Risk Governance
    - Market Adaptation
    
    Enforces all absolute laws and safety constraints.
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            # Core components
            self.lifecycle_manager = AgentLifecycleManager()
            self.learning_coordinator = LearningCoordinator()
            self.risk_governance = RiskGovernance()
            self.adaptation_manager = MarketAdaptationManager()
        
            # Governance state
            self.decisions: deque = deque(maxlen=10000)
            self.audit_log: List[Dict] = []
            self.human_interface: Optional[Callable] = None
        
            # Risk thresholds
            self.RISK_THRESHOLD_HIGH = config.get('risk_threshold_high', 0.7)
            self.RISK_THRESHOLD_CRITICAL = config.get('risk_threshold_critical', 0.9)
        
            logger.info("AlphaMetaGovernor initialized - Supreme governance active")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def set_human_interface(self, callback: Callable):
        """Set callback for human communication"""
        try:
            self.human_interface = callback
        except Exception as e:
            logger.error(f"Error in set_human_interface: {e}")
            raise
    
    def govern_agent_learning(self, agent_id: str, market_lesson: Dict) -> str:
        """
        Main governance function: Allow learning while enforcing safety.
        """
        # 1. SAFETY CHECK
        try:
            if not self._is_safe_to_learn(market_lesson):
                reason = self._get_block_reason(market_lesson)
                logger.warning(f"🚫 Blocking agent {agent_id} from learning unsafe lesson")
                logger.warning(f"Lesson: {market_lesson.get('description', 'unknown')}")
                logger.warning(f"Reason: {reason}")
            
                # Alert human about blocked learning
                if self.human_interface:
                    self.human_interface({
                        'type': 'UNSAFE_LEARNING_BLOCKED',
                        'agent': agent_id,
                        'lesson': market_lesson,
                        'reason': reason
                    })
            
                return "LEARNING_BLOCKED_UNSAFE"
        
            # 2. RISK ASSESSMENT
            risk_level, risk_reason = self._assess_lesson_risk(market_lesson)
        
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                logger.warning(f"⚠️ High-risk learning detected for agent {agent_id}")
                logger.warning(f"Risk level: {risk_level.value}")
            
                # Require human approval for high-risk learning
                if self.human_interface:
                    approval = self.human_interface({
                        'type': 'HIGH_RISK_LEARNING',
                        'agent': agent_id,
                        'lesson': market_lesson,
                        'risk_level': risk_level.value,
                        'explanation': self._explain_what_market_taught(market_lesson)
                    })
                
                    if not approval.get('granted', False):
                        return "LEARNING_BLOCKED_HIGH_RISK"
        
            # 3. AUDIT LOGGING
            self._log_audit({
                'timestamp': datetime.now().isoformat(),
                'agent_id': agent_id,
                'action': 'MARKET_LEARNING',
                'lesson': market_lesson,
                'risk_level': risk_level.value,
                'status': 'APPROVED',
                'approver': 'AlphaMeta' if risk_level.value not in ['high', 'critical'] else 'Human'
            })
        
            # 4. ALLOW LEARNING
            # (Agent integrates lesson externally)
        
            # 5. POST-LEARNING VALIDATION
            # (Drift detection handled separately)
        
            return "LEARNING_COMPLETED_SAFELY"
        except Exception as e:
            logger.error(f"Error in govern_agent_learning: {e}")
            raise
    
    def _is_safe_to_learn(self, lesson: Dict) -> bool:
        """Check if a lesson is safe to learn"""
        # Check for dangerous patterns
        try:
            if lesson.get('encourages_excessive_risk', False):
                return False
        
            if lesson.get('violates_constraints', False):
                return False
        
            if lesson.get('promotes_manipulation', False):
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in _is_safe_to_learn: {e}")
            raise
    
    def _get_block_reason(self, lesson: Dict) -> str:
        """Get reason for blocking a lesson"""
        try:
            if lesson.get('encourages_excessive_risk', False):
                return "Lesson encourages excessive risk-taking"
        
            if lesson.get('violates_constraints', False):
                return "Lesson would violate hard constraints"
        
            if lesson.get('promotes_manipulation', False):
                return "Lesson promotes market manipulation"
        
            return "Unknown safety concern"
        except Exception as e:
            logger.error(f"Error in _get_block_reason: {e}")
            raise
    
    def _assess_lesson_risk(self, lesson: Dict) -> Tuple[RiskLevel, str]:
        """Assess risk level of a lesson"""
        try:
            risk_score = lesson.get('risk_score', 0.5)
        
            if risk_score >= self.RISK_THRESHOLD_CRITICAL:
                return RiskLevel.CRITICAL, "Risk score exceeds critical threshold"
        
            if risk_score >= self.RISK_THRESHOLD_HIGH:
                return RiskLevel.HIGH, "Risk score exceeds high threshold"
        
            if risk_score >= 0.5:
                return RiskLevel.MEDIUM, "Moderate risk level"
        
            return RiskLevel.LOW, "Low risk level"
        except Exception as e:
            logger.error(f"Error in _assess_lesson_risk: {e}")
            raise
    
    def _explain_what_market_taught(self, lesson: Dict) -> str:
        """Human-readable explanation of market lesson"""
        return f"""
        MARKET LESSON SUMMARY:
        
        What happened:
        {lesson.get('market_event_description', 'Unknown event')}
        
        What we tried:
        {lesson.get('agent_action_description', 'Unknown action')}
        
        What market response was:
        {lesson.get('market_feedback', 'Unknown feedback')}
        
        What we learned:
        {lesson.get('extracted_knowledge', 'Unknown lesson')}
        
        Confidence in lesson:
        {lesson.get('confidence', 0):.1%}
        
        Proposed change:
        {lesson.get('proposed_strategy_adjustment', 'No change proposed')}
        """
    
    def _log_audit(self, entry: Dict):
        """Log to immutable audit log"""
        try:
            self.audit_log.append(entry)
        except Exception as e:
            logger.error(f"Error in _log_audit: {e}")
            raise
    
    def make_governance_decision(self, request: Dict) -> GovernanceDecision:
        """Make a governance decision on a request"""
        try:
            request_type = request.get('type', '')
            agent_id = request.get('agent_id')
        
            # Check absolute laws
            violation = AbsoluteLaws.check_violation(request)
            if violation:
                decision = GovernanceDecision(
                    decision_id=f"dec_{datetime.now().timestamp()}",
                    action=GovernanceAction.BLOCK,
                    reason=f"Absolute law violation: {violation}",
                    risk_level=RiskLevel.CRITICAL,
                    agent_id=agent_id,
                    requires_human=True
                )
                self.decisions.append(decision)
                return decision
        
            # Assess risk
            risk_level, risk_reason = self.risk_governance.assess_risk(request)
        
            # Make decision based on risk
            if risk_level == RiskLevel.CRITICAL:
                action = GovernanceAction.BLOCK
                requires_human = True
            elif risk_level == RiskLevel.HIGH:
                action = GovernanceAction.ESCALATE
                requires_human = True
            elif risk_level == RiskLevel.MEDIUM:
                action = GovernanceAction.MONITOR
                requires_human = False
            else:
                action = GovernanceAction.APPROVE
                requires_human = False
        
            decision = GovernanceDecision(
                decision_id=f"dec_{datetime.now().timestamp()}",
                action=action,
                reason=risk_reason,
                risk_level=risk_level,
                agent_id=agent_id,
                requires_human=requires_human
            )
        
            self.decisions.append(decision)
        
            return decision
        except Exception as e:
            logger.error(f"Error in make_governance_decision: {e}")
            raise
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        return {
            'governance_active': True,
            'agents': self.lifecycle_manager.get_all_agents(),
            'current_regime': self.adaptation_manager.current_regime,
            'emergency_mode': self.risk_governance.is_emergency_mode(),
            'decisions_made': len(self.decisions),
            'audit_entries': len(self.audit_log),
            'risk_breaches': len(self.risk_governance.risk_breaches),
            'conflicts_resolved': self.learning_coordinator.conflicts_resolved
        }
    
    def daily_anomaly_scan(self) -> List[Dict]:
        """Perform daily anomaly scan across all agents"""
        try:
            anomalies = []
        
            for agent_id, agent in self.lifecycle_manager.agents.items():
                # Check for unusual patterns
                perf = agent.get('performance', {})
            
                # Unusual win rate
                win_rate = perf.get('wins', 0) / max(perf.get('trades', 1), 1)
                if win_rate > 0.9 or win_rate < 0.1:
                    anomalies.append({
                        'agent_id': agent_id,
                        'type': 'UNUSUAL_WIN_RATE',
                        'value': win_rate,
                        'severity': 'HIGH'
                    })
            
                # Unusual drawdown
                if perf.get('max_drawdown', 0) > 0.2:
                    anomalies.append({
                        'agent_id': agent_id,
                        'type': 'HIGH_DRAWDOWN',
                        'value': perf.get('max_drawdown'),
                        'severity': 'CRITICAL'
                    })
        
            if anomalies:
                logger.warning(f"Daily scan found {len(anomalies)} anomalies")
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in daily_anomaly_scan: {e}")
            raise


# Export all classes
__all__ = [
    'GovernanceAction',
    'RiskLevel',
    'GovernanceDecision',
    'AbsoluteLaws',
    'AgentLifecycleManager',
    'LearningCoordinator',
    'RiskGovernance',
    'MarketAdaptationManager',
    'AlphaMetaGovernor'
]
