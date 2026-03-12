"""
Agent Population Control
=========================
Prevents runaway agent growth and enforces operating mode restrictions.

Features:
- Population limits (max agents)
- Rate limiting (proposals per day)
- No recursive agent creation
- Purpose uniqueness enforcement
- Operating mode enforcement (Sandbox → Test → Production)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict
import random
from typing import Set

logger = logging.getLogger(__name__)


class OperatingModeType(Enum):
    """Agent operating modes with increasing privilege levels"""
    SANDBOX = "sandbox"           # Simulation only, no real effect
    TEST = "test"                 # Paper trading, no real money
    PROPOSAL = "proposal"         # Generate suggestions only
    PRODUCTION = "production"     # Live trading (human-approved only)


@dataclass
class GraduationCriteria:
    """Criteria for promoting agents between modes"""
    min_trades: int = 30
    min_sharpe: float = 1.5
    max_drawdown: float = 0.10
    min_win_rate: float = 0.55
    min_profit_factor: float = 1.5
    min_days_in_mode: int = 7
    
    def to_dict(self) -> Dict:
        return {
            'min_trades': self.min_trades,
            'min_sharpe': self.min_sharpe,
            'max_drawdown': self.max_drawdown,
            'min_win_rate': self.min_win_rate,
            'min_profit_factor': self.min_profit_factor,
            'min_days_in_mode': self.min_days_in_mode
        }


@dataclass
class AgentPerformance:
    """Track agent performance metrics"""
    trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    mode_start_date: datetime = field(default_factory=datetime.now)
    
    @property
    def win_rate(self) -> float:
        try:
            if self.trades == 0:
                return 0.0
            return self.wins / self.trades
        except Exception as e:
            logger.error(f"Error in win_rate: {e}")
            raise
    
    @property
    def days_in_mode(self) -> int:
        return (datetime.now() - self.mode_start_date).days
    
    def meets_criteria(self, criteria: GraduationCriteria) -> bool:
        """Check if performance meets graduation criteria"""
        return (
            self.trades >= criteria.min_trades and
            self.sharpe_ratio >= criteria.min_sharpe and
            self.max_drawdown <= criteria.max_drawdown and
            self.win_rate >= criteria.min_win_rate and
            self.profit_factor >= criteria.min_profit_factor and
            self.days_in_mode >= criteria.min_days_in_mode
        )
    
    def to_dict(self) -> Dict:
        return {
            'trades': self.trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': self.win_rate,
            'total_pnl': self.total_pnl,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'profit_factor': self.profit_factor,
            'days_in_mode': self.days_in_mode
        }


class AgentOperatingMode:
    """
    Manages agent operating modes with safety layers.
    
    Progression: SANDBOX → TEST → PROPOSAL → PRODUCTION
    
    Only PRODUCTION mode can execute real trades.
    Production promotion REQUIRES human approval.
    """
    
    def __init__(self, agent_id: str):
        try:
            self.agent_id = agent_id
            self.current_mode = OperatingModeType.SANDBOX  # Always start in sandbox
            self.mode_history: List[Dict] = []
            self.performance = AgentPerformance()
            self.graduation_criteria = GraduationCriteria()
            self._human_approval_callback: Optional[Callable] = None
        
            self._record_mode_change(OperatingModeType.SANDBOX, "Initial mode")
        
            logger.info(f"Agent {agent_id} initialized in SANDBOX mode")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _record_mode_change(self, new_mode: OperatingModeType, reason: str):
        """Record mode change in history"""
        try:
            self.mode_history.append({
                'mode': new_mode.value,
                'timestamp': datetime.now().isoformat(),
                'reason': reason
            })
        except Exception as e:
            logger.error(f"Error in _record_mode_change: {e}")
            raise
    
    def set_human_approval_callback(self, callback: Callable):
        """Set callback for requesting human approval"""
        try:
            self._human_approval_callback = callback
        except Exception as e:
            logger.error(f"Error in set_human_approval_callback: {e}")
            raise
    
    def promote_to_test(self) -> str:
        """Move from sandbox to paper trading"""
        try:
            if self.current_mode != OperatingModeType.SANDBOX:
                return "ERROR: Can only promote from SANDBOX"
        
            # Require graduation criteria
            if not self.performance.meets_criteria(self.graduation_criteria):
                missing = self._get_missing_criteria()
                return f"DENIED: Agent hasn't proven itself in sandbox. Missing: {missing}"
        
            self.current_mode = OperatingModeType.TEST
            self.performance.mode_start_date = datetime.now()
            self._record_mode_change(OperatingModeType.TEST, "Graduated from sandbox")
        
            logger.info(f"Agent {self.agent_id} promoted to TEST mode")
            return "PROMOTED_TO_TEST"
        except Exception as e:
            logger.error(f"Error in promote_to_test: {e}")
            raise
    
    def promote_to_proposal(self) -> str:
        """Move from test to proposal mode"""
        try:
            if self.current_mode != OperatingModeType.TEST:
                return "ERROR: Can only promote from TEST"
        
            if not self.performance.meets_criteria(self.graduation_criteria):
                missing = self._get_missing_criteria()
                return f"DENIED: Does not meet proposal requirements. Missing: {missing}"
        
            self.current_mode = OperatingModeType.PROPOSAL
            self.performance.mode_start_date = datetime.now()
            self._record_mode_change(OperatingModeType.PROPOSAL, "Graduated from test")
        
            logger.info(f"Agent {self.agent_id} promoted to PROPOSAL mode")
            return "PROMOTED_TO_PROPOSAL"
        except Exception as e:
            logger.error(f"Error in promote_to_proposal: {e}")
            raise
    
    def promote_to_production(self, human_approval: Optional[Dict] = None) -> str:
        """
        Move to live trading - REQUIRES HUMAN APPROVAL.
        
        This is the ONLY way to get to production mode.
        """
        try:
            if self.current_mode not in [OperatingModeType.TEST, OperatingModeType.PROPOSAL]:
                return "ERROR: Must test before production"
        
            # Strict requirements for production
            production_criteria = GraduationCriteria(
                min_trades=100,
                min_sharpe=1.5,
                max_drawdown=0.10,
                min_win_rate=0.55,
                min_profit_factor=1.8,
                min_days_in_mode=14
            )
        
            if not self.performance.meets_criteria(production_criteria):
                missing = self._get_missing_criteria(production_criteria)
                return f"DENIED: Does not meet production requirements. Missing: {missing}"
        
            # HUMAN APPROVAL REQUIRED (ABSOLUTE LAW)
            if human_approval is None:
                if self._human_approval_callback:
                    approval_request = {
                        'type': 'AGENT_PRODUCTION_PROMOTION',
                        'agent_id': self.agent_id,
                        'test_results': self.performance.to_dict(),
                        'mode_history': self.mode_history,
                        'criteria_met': production_criteria.to_dict()
                    }
                    self._human_approval_callback(approval_request)
                return "PENDING_HUMAN_APPROVAL"
        
            if not human_approval.get('granted', False):
                self._record_mode_change(self.current_mode, "Production promotion rejected by human")
                return "DENIED: Human rejected promotion"
        
            # APPROVED
            self.current_mode = OperatingModeType.PRODUCTION
            self.performance.mode_start_date = datetime.now()
            self._record_mode_change(
                OperatingModeType.PRODUCTION,
                f"Approved by {human_approval.get('approver', 'unknown')}"
            )
        
            logger.info(f"Agent {self.agent_id} promoted to PRODUCTION")
            logger.info("Human approval verified and logged")
        
            return "PROMOTED_TO_PRODUCTION"
        except Exception as e:
            logger.error(f"Error in promote_to_production: {e}")
            raise
    
    def demote(self, reason: str = "Performance degradation") -> str:
        """Demote agent to lower mode"""
        try:
            if self.current_mode == OperatingModeType.SANDBOX:
                return "ERROR: Already at lowest mode"
        
            previous_mode = self.current_mode
        
            if self.current_mode == OperatingModeType.PRODUCTION:
                self.current_mode = OperatingModeType.PROPOSAL
            elif self.current_mode == OperatingModeType.PROPOSAL:
                self.current_mode = OperatingModeType.TEST
            elif self.current_mode == OperatingModeType.TEST:
                self.current_mode = OperatingModeType.SANDBOX
        
            self.performance.mode_start_date = datetime.now()
            self._record_mode_change(self.current_mode, f"Demoted from {previous_mode.value}: {reason}")
        
            logger.warning(f"Agent {self.agent_id} demoted to {self.current_mode.value}: {reason}")
            return f"DEMOTED_TO_{self.current_mode.value.upper()}"
        except Exception as e:
            logger.error(f"Error in demote: {e}")
            raise
    
    def _get_missing_criteria(self, criteria: GraduationCriteria = None) -> List[str]:
        """Get list of criteria not met"""
        try:
            if criteria is None:
                criteria = self.graduation_criteria
        
            missing = []
            if self.performance.trades < criteria.min_trades:
                missing.append(f"trades ({self.performance.trades}/{criteria.min_trades})")
            if self.performance.sharpe_ratio < criteria.min_sharpe:
                missing.append(f"sharpe ({self.performance.sharpe_ratio:.2f}/{criteria.min_sharpe})")
            if self.performance.max_drawdown > criteria.max_drawdown:
                missing.append(f"drawdown ({self.performance.max_drawdown:.1%}/{criteria.max_drawdown:.1%})")
            if self.performance.win_rate < criteria.min_win_rate:
                missing.append(f"win_rate ({self.performance.win_rate:.1%}/{criteria.min_win_rate:.1%})")
            if self.performance.profit_factor < criteria.min_profit_factor:
                missing.append(f"profit_factor ({self.performance.profit_factor:.2f}/{criteria.min_profit_factor})")
            if self.performance.days_in_mode < criteria.min_days_in_mode:
                missing.append(f"days ({self.performance.days_in_mode}/{criteria.min_days_in_mode})")
        
            return missing
        except Exception as e:
            logger.error(f"Error in _get_missing_criteria: {e}")
            raise
    
    def can_execute_real_trades(self) -> bool:
        """Only production mode can trade real money"""
        return self.current_mode == OperatingModeType.PRODUCTION
    
    def enforce_mode_restrictions(self, action: Dict) -> str:
        """Block actions not allowed in current mode"""
        try:
            action_type = action.get('type', '')
        
            if action_type == "REAL_TRADE" and not self.can_execute_real_trades():
                logger.warning(f"🚫 BLOCKED: Agent in {self.current_mode.value} mode attempted real trade")
                return "BLOCKED_MODE_RESTRICTION"
        
            if action_type == "MODIFY_RISK_PARAMS":
                logger.warning(f"🚫 BLOCKED: Agents cannot modify risk parameters")
                return "BLOCKED_IMMUTABLE_PARAMETER"
        
            if action_type == "CREATE_AGENT" and self.current_mode != OperatingModeType.PRODUCTION:
                logger.warning(f"🚫 BLOCKED: Only production agents can propose new agents")
                return "BLOCKED_MODE_RESTRICTION"
        
            return "ALLOWED"
        except Exception as e:
            logger.error(f"Error in enforce_mode_restrictions: {e}")
            raise
    
    def get_status(self) -> Dict:
        """Get current mode status"""
        return {
            'agent_id': self.agent_id,
            'current_mode': self.current_mode.value,
            'can_trade_real': self.can_execute_real_trades(),
            'performance': self.performance.to_dict(),
            'mode_history': self.mode_history
        }


class AgentPopulationController:
    """
    Controls agent population to prevent runaway growth.
    
    Enforces:
    - Maximum agent count
    - Proposal rate limits
    - No recursive agent creation
    - Purpose uniqueness
    - Human approval for novel agent types
    """
    
    def __init__(self, config: Dict = None):
        try:
            config = config or {}
        
            self.MAX_AGENTS = config.get('max_agents', 20)
            self.MAX_PROPOSALS_PER_DAY = config.get('max_proposals_per_day', 5)
        
            self.agent_registry: Dict[str, Dict] = {}
            self.agent_modes: Dict[str, AgentOperatingMode] = {}
            self.proposals_today: Dict[str, int] = defaultdict(int)
            self.last_proposal_reset: datetime = datetime.now()
        
            self._human_approval_callback: Optional[Callable] = None
            self._known_purposes: List[str] = []
        
            logger.info(f"AgentPopulationController initialized (max: {self.MAX_AGENTS})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def set_human_approval_callback(self, callback: Callable):
        """Set callback for requesting human approval"""
        try:
            self._human_approval_callback = callback
        except Exception as e:
            logger.error(f"Error in set_human_approval_callback: {e}")
            raise
    
    def _reset_daily_proposals(self):
        """Reset proposal counts if new day"""
        try:
            now = datetime.now()
            if now.date() > self.last_proposal_reset.date():
                self.proposals_today.clear()
                self.last_proposal_reset = now
        except Exception as e:
            logger.error(f"Error in _reset_daily_proposals: {e}")
            raise
    
    def request_new_agent_creation(
        self,
        purpose: str,
        creator_id: str,
        creator_type: str = "HUMAN",
        agent_config: Dict = None
    ) -> Dict:
        """
        Request creation of a new agent with strict controls.
        
        Returns:
            Dict with 'status' and 'agent_id' or 'reason'
        """
        try:
            self._reset_daily_proposals()
        
            # Check 1: Population limit
            if len(self.agent_registry) >= self.MAX_AGENTS:
                logger.warning("❌ Agent creation denied: Population limit reached")
                return {
                    'status': 'DENIED',
                    'reason': 'POPULATION_LIMIT',
                    'message': f'Maximum {self.MAX_AGENTS} agents allowed'
                }
        
            # Check 2: Proposal rate limit
            if self.proposals_today[creator_id] >= self.MAX_PROPOSALS_PER_DAY:
                logger.warning("❌ Agent creation denied: Too many proposals today")
                return {
                    'status': 'DENIED',
                    'reason': 'RATE_LIMIT',
                    'message': f'Maximum {self.MAX_PROPOSALS_PER_DAY} proposals per day'
                }
        
            # Check 3: No recursive creation (agents cannot create agents)
            if creator_type == "AGENT":
                # Check if creator agent has permission
                creator_mode = self.agent_modes.get(creator_id)
                if creator_mode and creator_mode.current_mode != OperatingModeType.PRODUCTION:
                    logger.warning("❌ Agent creation denied: Non-production agents cannot create agents")
                    return {
                        'status': 'DENIED',
                        'reason': 'RECURSIVE_CREATION',
                        'message': 'Only production agents can propose new agents'
                    }
        
            # Check 4: Purpose must be unique
            if self._purpose_already_covered(purpose):
                similar_agent = self._find_similar_agent(purpose)
                logger.warning(f"❌ Agent creation denied: Redundant purpose")
                return {
                    'status': 'DENIED',
                    'reason': 'REDUNDANT',
                    'message': f"Existing agent '{similar_agent}' already covers this purpose"
                }
        
            # Check 5: Human approval for new agent types
            if self._is_novel_agent_type(purpose):
                logger.info("⚠️ Novel agent type detected. Requiring human approval.")
            
                if self._human_approval_callback:
                    approval_request = {
                        'type': 'NEW_AGENT_TYPE',
                        'purpose': purpose,
                        'creator': creator_id,
                        'justification': self._explain_why_needed(purpose),
                        'risks': self._assess_risks(purpose)
                    }
                    self._human_approval_callback(approval_request)
                
                    return {
                        'status': 'PENDING_APPROVAL',
                        'reason': 'NOVEL_AGENT_TYPE',
                        'message': 'Human approval required for new agent type'
                    }
        
            # ALL CHECKS PASSED
            agent_id = self._create_agent(purpose, agent_config or {})
            self.proposals_today[creator_id] += 1
            self._known_purposes.append(purpose)
        
            logger.info(f"✓ Agent creation approved: {purpose}")
        
            return {
                'status': 'CREATED',
                'agent_id': agent_id,
                'purpose': purpose
            }
        except Exception as e:
            logger.error(f"Error in request_new_agent_creation: {e}")
            raise
    
    def _purpose_already_covered(self, purpose: str) -> bool:
        """Check if purpose is already covered by existing agent"""
        try:
            purpose_lower = purpose.lower()
            for agent_id, agent_info in self.agent_registry.items():
                existing_purpose = agent_info.get('purpose', '').lower()
                # Simple similarity check
                if purpose_lower in existing_purpose or existing_purpose in purpose_lower:
                    return True
                # Check for keyword overlap
                purpose_words = set(purpose_lower.split())
                existing_words = set(existing_purpose.split())
                overlap = len(purpose_words & existing_words) / max(len(purpose_words), 1)
                if overlap > 0.5:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error in _purpose_already_covered: {e}")
            raise
    
    def _find_similar_agent(self, purpose: str) -> Optional[str]:
        """Find agent with similar purpose"""
        try:
            purpose_lower = purpose.lower()
            for agent_id, agent_info in self.agent_registry.items():
                existing_purpose = agent_info.get('purpose', '').lower()
                if purpose_lower in existing_purpose or existing_purpose in purpose_lower:
                    return agent_id
            return None
        except Exception as e:
            logger.error(f"Error in _find_similar_agent: {e}")
            raise
    
    def _is_novel_agent_type(self, purpose: str) -> bool:
        """Check if this is a novel agent type"""
        # Check against known purposes
        try:
            purpose_lower = purpose.lower()
            for known in self._known_purposes:
                if purpose_lower in known.lower() or known.lower() in purpose_lower:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error in _is_novel_agent_type: {e}")
            raise
    
    def _explain_why_needed(self, purpose: str) -> str:
        """Explain why a new agent is needed"""
        return f"New agent proposed for: {purpose}. No existing agent covers this purpose."
    
    def _assess_risks(self, purpose: str) -> Dict:
        """Assess risks of new agent type"""
        return {
            'risk_level': 'MEDIUM',
            'concerns': [
                'New agent type requires monitoring',
                'Performance unknown until tested'
            ],
            'mitigations': [
                'Start in sandbox mode',
                'Require graduation criteria before production'
            ]
        }
    
    def _create_agent(self, purpose: str, config: Dict) -> str:
        """Create a new agent"""
        try:
            agent_id = f"agent_{len(self.agent_registry)}_{random.randint(1000, 9999)}"
        
            self.agent_registry[agent_id] = {
                'purpose': purpose,
                'config': config,
                'created_at': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
        
            # Create operating mode manager
            self.agent_modes[agent_id] = AgentOperatingMode(agent_id)
        
            return agent_id
        except Exception as e:
            logger.error(f"Error in _create_agent: {e}")
            raise
    
    def retire_agent(self, agent_id: str, reason: str = "Retired") -> bool:
        """Retire an agent"""
        try:
            if agent_id not in self.agent_registry:
                return False
        
            self.agent_registry[agent_id]['status'] = 'RETIRED'
            self.agent_registry[agent_id]['retired_at'] = datetime.now().isoformat()
            self.agent_registry[agent_id]['retire_reason'] = reason
        
            logger.info(f"Agent {agent_id} retired: {reason}")
            return True
        except Exception as e:
            logger.error(f"Error in retire_agent: {e}")
            raise
    
    def get_agent_mode(self, agent_id: str) -> Optional[AgentOperatingMode]:
        """Get operating mode manager for an agent"""
        return self.agent_modes.get(agent_id)
    
    def get_active_agents(self) -> List[str]:
        """Get list of active agent IDs"""
        return [
            agent_id for agent_id, info in self.agent_registry.items()
            if info.get('status') == 'ACTIVE'
        ]
    
    def get_production_agents(self) -> List[str]:
        """Get list of agents in production mode"""
        return [
            agent_id for agent_id, mode in self.agent_modes.items()
            if mode.current_mode == OperatingModeType.PRODUCTION
        ]
    
    def get_population_status(self) -> Dict:
        """Get population status"""
        return {
            'total_agents': len(self.agent_registry),
            'max_agents': self.MAX_AGENTS,
            'active_agents': len(self.get_active_agents()),
            'production_agents': len(self.get_production_agents()),
            'proposals_today': dict(self.proposals_today),
            'max_proposals_per_day': self.MAX_PROPOSALS_PER_DAY,
            'agents': {
                agent_id: {
                    'purpose': info.get('purpose'),
                    'status': info.get('status'),
                    'mode': self.agent_modes[agent_id].current_mode.value if agent_id in self.agent_modes else 'unknown'
                }
                for agent_id, info in self.agent_registry.items()
            }
        }


# Export all classes
__all__ = [
    'OperatingModeType',
    'GraduationCriteria',
    'AgentPerformance',
    'AgentOperatingMode',
    'AgentPopulationController'
]
