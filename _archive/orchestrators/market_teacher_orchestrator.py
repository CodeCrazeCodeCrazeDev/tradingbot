"""
Market Teacher Orchestrator
============================
Master controller that integrates all Market-as-Teacher components.

This is the main entry point for the complete system.

Architecture:
┌─────────────────────────────────────────────────────────┐
│                  HUMAN GOVERNANCE LAYER                  │
│              (Supreme Authority - Human Gateway)         │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                     ALPHAMETA GOVERNOR                   │
│              (Meta-Learning Orchestrator)                │
└─────────────────────────────────────────────────────────┘
                           ↕
┌──────────────────┬──────────────────┬──────────────────┐
│  LEARNING AGENTS  │  SAFETY SYSTEMS  │  MARKET FEEDBACK │
│  (Collective)     │  (Framework)     │  (Signals)       │
└──────────────────┴──────────────────┴──────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                   MARKET (TEACHER)                       │
│  - Provides feedback through price movements            │
│  - Rewards good decisions (profits)                     │
│  - Punishes bad decisions (losses)                      │
└─────────────────────────────────────────────────────────┘
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque

# Import all components
from .learning_framework import ContinuousLearner, MultiArmedBandit, ThompsonSampler, MetaLearner
from .market_feedback import MarketFeedbackSystem, FeedbackType
from .strategy_evolution import EvolutionaryStrategySystem, ConceptDriftDetector
from .curiosity_engine import CuriosityDrivenExplorer
from .agent_collective import AgentCollective
from .safety_framework import HierarchicalRiskManager, SafeExplorationFramework
from .alpha_meta import AlphaMetaGovernor
from .human_gateway import HumanApprovalGateway, ApprovalPriority
from .absolute_laws import AbsoluteLawsEnforcer
from .agent_population import AgentPopulationController
from .stealth_protection import StealthProtectionLayer, AntiDriftLock

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class LearningState(Enum):
    """Current state of the learning system"""
    INITIALIZING = "initializing"
    OBSERVING = "observing"
    LEARNING = "learning"
    PROPOSING = "proposing"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    ADAPTING = "adapting"
    PAUSED = "paused"
    EMERGENCY = "emergency"


@dataclass
class TeachingSession:
    """A session of market teaching"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    lessons_learned: int = 0
    trades_executed: int = 0
    total_pnl: float = 0.0
    state: LearningState = LearningState.INITIALIZING
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'lessons_learned': self.lessons_learned,
            'trades_executed': self.trades_executed,
            'total_pnl': self.total_pnl,
            'state': self.state.value,
            'duration_minutes': (
                (self.end_time or datetime.now()) - self.start_time
            ).total_seconds() / 60
        }


class MarketTeacherOrchestrator:
    """
    Master orchestrator for the Market-as-Teacher system.
    
    Core Philosophy: "The Market is Always Right"
    - Every tick, trade, and movement is a lesson
    - Learn continuously, adapt instantly, evolve perpetually
    - Ego is zero, humility is infinite
    - Market feedback is the only truth
    
    Prime Directives (Ranked):
    1. SAFETY ABOVE ALL
    2. HUMAN SUPREMACY
    3. MARKET AS TEACHER
    4. CONTINUOUS LEARNING
    5. COLLECTIVE INTELLIGENCE
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        # Core components
        self.continuous_learner = ContinuousLearner(config)
        self.market_feedback = MarketFeedbackSystem()
        self.strategy_evolution = EvolutionaryStrategySystem(config)
        self.curiosity_explorer = CuriosityDrivenExplorer(config)
        self.agent_collective = AgentCollective(config)
        
        # Safety systems
        self.risk_manager = HierarchicalRiskManager(config)
        self.safe_exploration = SafeExplorationFramework(config)
        
        # Governance
        self.alpha_meta = AlphaMetaGovernor(config)
        self.human_gateway = HumanApprovalGateway(config)
        self.absolute_laws = AbsoluteLawsEnforcer()
        self.population_controller = AgentPopulationController(config)
        
        # Protection
        self.stealth_protection = StealthProtectionLayer(config)
        self.anti_drift = AntiDriftLock()
        
        # State
        self.current_session: Optional[TeachingSession] = None
        self.session_history: List[TeachingSession] = []
        self.state = LearningState.INITIALIZING
        self.is_running: bool = False
        
        # Metrics
        self.total_lessons: int = 0
        self.total_trades: int = 0
        self.cumulative_pnl: float = 0.0
        
        # Wire up callbacks
        self._setup_callbacks()
        
        logger.info("MarketTeacherOrchestrator initialized")
        logger.info("Core Philosophy: The Market is Always Right")
    
    def _setup_callbacks(self):
        """Setup internal callbacks between components"""
        # Market feedback -> Learning
        self.market_feedback.register_lesson_callback(self._on_market_lesson)
        
        # Human gateway -> Governance
        self.human_gateway.register_approval_callback(self._on_approval)
        self.human_gateway.register_rejection_callback(self._on_rejection)
        
        # Alpha Meta -> Human interface
        self.alpha_meta.set_human_interface(self._request_human_decision)
    
    def _on_market_lesson(self, lesson):
        """Handle a new lesson from the market"""
        self.total_lessons += 1
        if self.current_session:
            self.current_session.lessons_learned += 1
        
        logger.debug(f"Market taught: {lesson.description}")
    
    def _on_approval(self, request):
        """Handle approval from human"""
        logger.info(f"Human approved: {request.title}")
    
    def _on_rejection(self, request):
        """Handle rejection from human"""
        logger.info(f"Human rejected: {request.title}")
    
    def _request_human_decision(self, request: Dict) -> Dict:
        """Request a decision from human"""
        approval_request = self.human_gateway.request_approval(
            request_type=request.get('type', 'UNKNOWN'),
            title=request.get('title', 'Decision Required'),
            description=request.get('explanation', ''),
            details=request,
            priority=ApprovalPriority.HIGH if request.get('risk_level') == 'high' else ApprovalPriority.MEDIUM
        )
        
        # In async mode, this would wait for approval
        # For now, return pending status
        return {
            'request_id': approval_request.request_id,
            'status': 'PENDING',
            'granted': False
        }
    
    def start_session(self) -> TeachingSession:
        """Start a new teaching session"""
        session = TeachingSession(
            session_id=f"session_{datetime.now().timestamp()}",
            start_time=datetime.now(),
            state=LearningState.OBSERVING
        )
        
        self.current_session = session
        self.state = LearningState.OBSERVING
        self.is_running = True
        
        logger.info(f"Teaching session started: {session.session_id}")
        
        return session
    
    def end_session(self) -> Optional[TeachingSession]:
        """End the current teaching session"""
        if not self.current_session:
            return None
        
        self.current_session.end_time = datetime.now()
        self.session_history.append(self.current_session)
        
        session = self.current_session
        self.current_session = None
        self.is_running = False
        self.state = LearningState.PAUSED
        
        logger.info(f"Teaching session ended: {session.session_id}")
        logger.info(f"Lessons learned: {session.lessons_learned}")
        logger.info(f"Trades executed: {session.trades_executed}")
        logger.info(f"Total P&L: {session.total_pnl:.2f}")
        
        return session
    
    def process_market_data(self, market_data: Dict) -> Dict:
        """
        Main processing loop for market data.
        
        This is where the market teaches us.
        """
        if not self.is_running:
            return {'status': 'NOT_RUNNING'}
        
        # 1. OBSERVE
        self.state = LearningState.OBSERVING
        observation = self.continuous_learner.observe(market_data)
        
        # 2. CHECK SAFETY
        if self.safe_exploration.is_halted:
            return {
                'status': 'HALTED',
                'reason': self.safe_exploration.halt_reason
            }
        
        # 3. GET COLLECTIVE ANALYSIS
        self.state = LearningState.LEARNING
        collective_signal = self.agent_collective.analyze_market(market_data)
        
        # 4. CHECK FOR CURIOSITY-DRIVEN EXPLORATION
        should_explore, explore_reason = self.curiosity_explorer.should_explore(market_data)
        
        # 5. GENERATE HYPOTHESES
        hypotheses = self.continuous_learner.hypothesize(observation)
        
        # 6. CHECK ABSOLUTE LAWS
        proposed_action = {
            'type': 'TRADE_SIGNAL',
            'action': collective_signal.get('action'),
            'confidence': collective_signal.get('confidence'),
            'human_approved': False
        }
        
        law_check = self.absolute_laws.check_action('system', proposed_action)
        if not law_check['allowed']:
            return {
                'status': 'BLOCKED',
                'reason': law_check['reason'],
                'law': law_check['law']
            }
        
        # 7. APPLY STEALTH PROTECTION
        if collective_signal.get('action') in ['BUY', 'SELL']:
            stealth_status, modified_trade = self.stealth_protection.enforce_stealth({
                'action': collective_signal.get('action'),
                'size': 0.01  # Default size
            })
            
            if stealth_status == 'SKIP_FOR_STEALTH':
                return {
                    'status': 'SKIPPED',
                    'reason': 'Stealth protection'
                }
        
        # 8. CHECK RISK
        risk_check = self.risk_manager.check_trade({
            'action': collective_signal.get('action'),
            'size': 0.01,
            'confidence': collective_signal.get('confidence')
        })
        
        if not risk_check['approved']:
            return {
                'status': 'REJECTED',
                'reason': risk_check['reason'],
                'level': risk_check['level']
            }
        
        # 9. GOVERNANCE CHECK
        self.state = LearningState.PROPOSING
        governance_decision = self.alpha_meta.make_governance_decision({
            'type': 'TRADE_PROPOSAL',
            'action': collective_signal.get('action'),
            'confidence': collective_signal.get('confidence'),
            'position_size': risk_check.get('trade', {}).get('size', 0.01)
        })
        
        if governance_decision.requires_human:
            self.state = LearningState.AWAITING_APPROVAL
            return {
                'status': 'AWAITING_APPROVAL',
                'decision_id': governance_decision.decision_id,
                'reason': governance_decision.reason
            }
        
        # 10. EXECUTE (if approved)
        if governance_decision.action.value == 'approve':
            self.state = LearningState.EXECUTING
            
            result = {
                'status': 'SIGNAL_GENERATED',
                'action': collective_signal.get('action'),
                'confidence': collective_signal.get('confidence'),
                'reasoning': collective_signal.get('reasoning'),
                'exploration_mode': should_explore,
                'modifications': risk_check.get('modifications', [])
            }
            
            if self.current_session:
                self.current_session.trades_executed += 1
            
            return result
        
        return {
            'status': 'NO_ACTION',
            'reason': governance_decision.reason
        }
    
    def process_trade_feedback(self, trade_result: Dict):
        """
        Process feedback from a completed trade.
        
        This is where the market grades our decisions.
        """
        self.state = LearningState.EVALUATING
        
        pnl = trade_result.get('pnl', 0)
        
        # Update metrics
        self.total_trades += 1
        self.cumulative_pnl += pnl
        
        if self.current_session:
            self.current_session.total_pnl += pnl
        
        # Process through market feedback system
        if 'entry_price' in trade_result and 'exit_price' in trade_result:
            self.market_feedback.process_trade_outcome(
                entry_price=trade_result['entry_price'],
                exit_price=trade_result['exit_price'],
                direction=trade_result.get('direction', 'LONG'),
                hold_time_minutes=trade_result.get('hold_time_minutes', 60),
                expected_outcome=trade_result.get('expected_outcome', 0),
                stop_loss=trade_result.get('stop_loss', 0.02),
                take_profit=trade_result.get('take_profit', 0.04)
            )
        
        # Update agent collective
        self.agent_collective.process_feedback(trade_result)
        
        # Update strategy evolution
        if 'strategy_id' in trade_result:
            self.strategy_evolution.evaluate_strategy(
                trade_result['strategy_id'],
                [trade_result]
            )
        
        # Record stealth metrics
        self.stealth_protection.record_trade(trade_result)
        
        # Update curiosity/regret
        self.curiosity_explorer.update_regret(
            action=trade_result.get('action', 'UNKNOWN'),
            reward=pnl,
            alternatives={}
        )
        
        self.state = LearningState.ADAPTING
        
        logger.info(f"Trade feedback processed: P&L = {pnl:.4f}")
    
    def evolve(self) -> Dict:
        """
        Run one evolution cycle.
        
        Let the market teach us which strategies work.
        """
        evolution_result = self.strategy_evolution.evolve()
        
        # Check for drift across all agents
        drift_status = self.anti_drift.check_all_agents()
        
        return {
            'evolution': evolution_result,
            'drift_status': drift_status
        }
    
    def emergency_shutdown(self, reason: str):
        """Emergency shutdown of all systems"""
        self.state = LearningState.EMERGENCY
        self.is_running = False
        
        # Shutdown all components
        self.risk_manager.emergency_shutdown(reason)
        self.safe_exploration.halt_all_trading(reason)
        
        if self.current_session:
            self.end_session()
        
        logger.critical(f"🚨 EMERGENCY SHUTDOWN: {reason}")
        
        return {
            'status': 'SHUTDOWN',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'state': self.state.value,
            'is_running': self.is_running,
            'current_session': self.current_session.to_dict() if self.current_session else None,
            'metrics': {
                'total_lessons': self.total_lessons,
                'total_trades': self.total_trades,
                'cumulative_pnl': self.cumulative_pnl,
                'sessions_completed': len(self.session_history)
            },
            'components': {
                'alpha_meta': self.alpha_meta.get_system_status(),
                'risk_manager': self.risk_manager.get_risk_status(),
                'human_gateway': self.human_gateway.get_status(),
                'absolute_laws': self.absolute_laws.get_status(),
                'agent_collective': self.agent_collective.get_collective_status(),
                'stealth': self.stealth_protection.get_stealth_status(),
                'market_feedback': self.market_feedback.get_lesson_summary()
            }
        }
    
    def get_learning_summary(self) -> str:
        """Get human-readable learning summary"""
        summary = self.market_feedback.get_lesson_summary()
        
        return f"""
        ═══════════════════════════════════════════════════════════
                    MARKET-AS-TEACHER LEARNING SUMMARY
        ═══════════════════════════════════════════════════════════
        
        Total Lessons Learned: {summary['total_lessons']}
        
        By Feedback Type:
        - Immediate: {summary['by_type'].get('immediate', 0)}
        - Short-term: {summary['by_type'].get('short_term', 0)}
        - Medium-term: {summary['by_type'].get('medium_term', 0)}
        - Long-term: {summary['by_type'].get('long_term', 0)}
        - Black Swan: {summary['by_type'].get('black_swan', 0)}
        
        Execution Quality:
        - Average Slippage: {summary['average_slippage']*100:.2f}%
        - Fill Quality: {summary['fill_quality']*100:.1f}%
        
        Trading Performance:
        - Recent Win Rate: {summary['recent_win_rate']*100:.1f}%
        
        Risk Events:
        - Black Swan Events: {summary['black_swan_events']}
        - Stress Tests Created: {summary['stress_tests_created']}
        
        ═══════════════════════════════════════════════════════════
        
        Core Philosophy: The Market is Always Right.
        Every loss is a lesson. Every win validates temporarily.
        Adaptation beats prediction. The market evolves, so must we.
        
        ═══════════════════════════════════════════════════════════
        """


def create_market_teacher_system(config: Dict = None) -> MarketTeacherOrchestrator:
    """Factory function to create a complete Market Teacher system"""
    return MarketTeacherOrchestrator(config)


async def quick_start_learning(config: Dict = None) -> MarketTeacherOrchestrator:
    """Quick start function for the learning system"""
    system = create_market_teacher_system(config)
    system.start_session()
    
    logger.info("Market Teacher system started and ready to learn")
    
    return system


# Export all classes
__all__ = [
    'LearningState',
    'TeachingSession',
    'MarketTeacherOrchestrator',
    'create_market_teacher_system',
    'quick_start_learning'
]
