"""
Alpha Learning Cycle - The Continuous Learning Loop
====================================================

The AI's evolution is guided by this loop:

1. OBSERVE (market data, indicators, structure, context)
2. ACT (generate a signal or decision)
3. RECEIVE FEEDBACK (market reaction, PnL, risk impact)
4. EVALUATE (did the decision match the outcome?)
5. EXTRACT LESSONS (patterns, mistakes, insights)
6. PROPOSE IMPROVEMENTS (algorithmic adjustments, parameter changes)
7. AWAIT HUMAN APPROVAL
8. INTEGRATE improvements safely

Repeat this loop continuously. It is the path to growth.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional
from enum import Enum
import logging
import asyncio
import uuid

from .market_teacher import MarketTeacher, MarketLesson, LessonType
from .student_ai import StudentAI, ImprovementProposal, ProposalStatus
from .reward_system import get_reward_system, ImmutableRewardSystem
from typing import Set

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


# =============================================================================
# CYCLE PHASES
# =============================================================================

class CyclePhase(Enum):
    """Phases of the Alpha Learning Cycle"""
    OBSERVE = "observe"
    ACT = "act"
    FEEDBACK = "feedback"
    EVALUATE = "evaluate"
    EXTRACT = "extract"
    PROPOSE = "propose"
    AWAIT_APPROVAL = "await_approval"
    INTEGRATE = "integrate"


# =============================================================================
# CYCLE RESULT
# =============================================================================

@dataclass
class CycleResult:
    """Result of a learning cycle iteration"""
    
    cycle_id: str
    phase: CyclePhase
    success: bool
    
    # Observation
    market_data_observed: bool
    indicators_calculated: bool
    context_analyzed: bool
    
    # Action
    signal_generated: Optional[Dict[str, Any]]
    decision_made: Optional[str]
    
    # Feedback
    market_reaction: Optional[Dict[str, Any]]
    pnl_impact: float
    risk_impact: float
    
    # Evaluation
    prediction_correct: Optional[bool]
    evaluation_score: float
    
    # Lessons
    lessons_extracted: List[str]
    patterns_found: List[str]
    weaknesses_identified: List[str]
    
    # Proposals
    proposals_generated: List[str]
    proposals_pending: int
    
    # Integration
    improvements_integrated: List[str]
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: float
    
    # Reward
    reward_score: float
    penalty_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_id': self.cycle_id,
            'phase': self.phase.value,
            'success': self.success,
            'market_data_observed': self.market_data_observed,
            'signal_generated': self.signal_generated is not None,
            'pnl_impact': self.pnl_impact,
            'prediction_correct': self.prediction_correct,
            'lessons_extracted': len(self.lessons_extracted),
            'proposals_generated': len(self.proposals_generated),
            'improvements_integrated': len(self.improvements_integrated),
            'duration_ms': self.duration_ms,
            'reward_score': self.reward_score,
            'penalty_score': self.penalty_score,
        }


# =============================================================================
# ALPHA LEARNING CYCLE
# =============================================================================

class AlphaLearningCycle:
    """
    The Alpha Learning Cycle - Continuous market-driven evolution.
    
    This is the core loop that drives AI learning:
    Observe → Act → Feedback → Evaluate → Extract → Propose → Approve → Integrate
    
    The cycle runs continuously, learning from every market movement.
    """
    
    def __init__(
        self,
        market_teacher: MarketTeacher,
        student_ai: StudentAI,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # Core components
        self._teacher = market_teacher
        self._student = student_ai
        self._reward_system = get_reward_system()
        
        # Cycle state
        self._current_phase = CyclePhase.OBSERVE
        self._cycle_count = 0
        self._last_cycle_result: Optional[CycleResult] = None
        
        # Callbacks for integration with trading system
        self._observation_callback: Optional[Callable] = None
        self._action_callback: Optional[Callable] = None
        self._feedback_callback: Optional[Callable] = None
        
        # Cycle history
        self._cycle_history: List[CycleResult] = []
        self._max_history = 1000
        
        # Running state
        self._is_running = False
        self._cycle_interval = self.config.get('cycle_interval_seconds', 60)
        
        logger.info("AlphaLearningCycle initialized")
    
    def set_observation_callback(self, callback: Callable):
        """Set callback for observation phase"""
        self._observation_callback = callback
    
    def set_action_callback(self, callback: Callable):
        """Set callback for action phase"""
        self._action_callback = callback
    
    def set_feedback_callback(self, callback: Callable):
        """Set callback for feedback phase"""
        self._feedback_callback = callback
    
    async def run_cycle(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        signal: Optional[Dict[str, Any]] = None,
        trade_result: Optional[Dict[str, Any]] = None
    ) -> CycleResult:
        """
        Run one complete learning cycle.
        
        Args:
            symbol: Trading symbol
            market_data: Current market data
            signal: Signal that was generated (if any)
            trade_result: Result of trade (if any)
            
        Returns:
            CycleResult with all learning outcomes
        """
        cycle_id = f"cycle_{uuid.uuid4().hex[:8]}"
        started_at = datetime.now()
        
        logger.info(f"Starting learning cycle {cycle_id} for {symbol}")
        
        # Initialize result
        result = CycleResult(
            cycle_id=cycle_id,
            phase=CyclePhase.OBSERVE,
            success=False,
            market_data_observed=False,
            indicators_calculated=False,
            context_analyzed=False,
            signal_generated=None,
            decision_made=None,
            market_reaction=None,
            pnl_impact=0.0,
            risk_impact=0.0,
            prediction_correct=None,
            evaluation_score=0.0,
            lessons_extracted=[],
            patterns_found=[],
            weaknesses_identified=[],
            proposals_generated=[],
            proposals_pending=0,
            improvements_integrated=[],
            started_at=started_at,
            completed_at=None,
            duration_ms=0.0,
            reward_score=0.0,
            penalty_score=0.0,
        )
        
        try:
            # Phase 1: OBSERVE
            result.phase = CyclePhase.OBSERVE
            observation = await self._observe(symbol, market_data)
            result.market_data_observed = observation['data_received']
            result.indicators_calculated = observation['indicators_ready']
            result.context_analyzed = observation['context_analyzed']
            
            # Phase 2: ACT
            result.phase = CyclePhase.ACT
            action = await self._act(symbol, market_data, signal)
            result.signal_generated = action.get('signal')
            result.decision_made = action.get('decision')
            
            # Phase 3: FEEDBACK
            result.phase = CyclePhase.FEEDBACK
            feedback = await self._receive_feedback(symbol, market_data, trade_result)
            result.market_reaction = feedback.get('reaction')
            result.pnl_impact = feedback.get('pnl', 0.0)
            result.risk_impact = feedback.get('risk', 0.0)
            
            # Phase 4: EVALUATE
            result.phase = CyclePhase.EVALUATE
            evaluation = await self._evaluate(signal, trade_result, market_data)
            result.prediction_correct = evaluation.get('correct')
            result.evaluation_score = evaluation.get('score', 0.0)
            
            # Phase 5: EXTRACT LESSONS
            result.phase = CyclePhase.EXTRACT
            extraction = await self._extract_lessons(
                symbol, market_data, signal, trade_result, evaluation
            )
            result.lessons_extracted = extraction.get('lessons', [])
            result.patterns_found = extraction.get('patterns', [])
            result.weaknesses_identified = extraction.get('weaknesses', [])
            
            # Phase 6: PROPOSE IMPROVEMENTS
            result.phase = CyclePhase.PROPOSE
            proposals = await self._propose_improvements(extraction)
            result.proposals_generated = proposals.get('proposal_ids', [])
            
            # Phase 7: AWAIT APPROVAL (non-blocking check)
            result.phase = CyclePhase.AWAIT_APPROVAL
            pending = self._student.get_pending_proposals()
            result.proposals_pending = len(pending)
            
            # Phase 8: INTEGRATE (approved improvements only)
            result.phase = CyclePhase.INTEGRATE
            integration = await self._integrate_approved()
            result.improvements_integrated = integration.get('integrated', [])
            
            # Calculate rewards/penalties
            rewards, penalties = self._reward_system.evaluate_behavior(
                'learning',
                {
                    'lessons_learned': len(result.lessons_extracted),
                    'patterns_found': len(result.patterns_found),
                    'weaknesses_identified': len(result.weaknesses_identified),
                    'proposals_generated': len(result.proposals_generated),
                }
            )
            result.reward_score = sum(r.magnitude for r in rewards)
            result.penalty_score = sum(p.magnitude for p in penalties)
            
            result.success = True
            
        except Exception as e:
            logger.error(f"Error in learning cycle {cycle_id}: {e}", exc_info=True)
            result.success = False
        
        # Finalize
        result.completed_at = datetime.now()
        result.duration_ms = (result.completed_at - started_at).total_seconds() * 1000
        
        # Store in history
        self._cycle_history.append(result)
        if len(self._cycle_history) > self._max_history:
            self._cycle_history = self._cycle_history[-self._max_history:]
        
        self._last_cycle_result = result
        self._cycle_count += 1
        
        logger.info(f"Completed learning cycle {cycle_id} in {result.duration_ms:.0f}ms")
        
        return result
    
    async def _observe(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Observe market data"""
        logger.debug(f"OBSERVE: Analyzing {symbol}")
        
        observation = {
            'data_received': False,
            'indicators_ready': False,
            'context_analyzed': False,
        }
        
        # Check if we have market data
        if market_data:
            observation['data_received'] = True
            
            # Check for indicators
            if 'indicators' in market_data or 'atr' in market_data:
                observation['indicators_ready'] = True
            
            # Analyze context
            if 'regime' in market_data or 'volatility' in market_data:
                observation['context_analyzed'] = True
        
        # Call external observation callback if set
        if self._observation_callback:
            try:
                if asyncio.iscoroutinefunction(self._observation_callback):
                    await self._observation_callback(symbol, market_data)
                else:
                    self._observation_callback(symbol, market_data)
            except Exception as e:
                logger.error(f"Observation callback error: {e}")
        
        return observation
    
    async def _act(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        signal: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Phase 2: Generate action/signal"""
        logger.debug(f"ACT: Processing signal for {symbol}")
        
        action = {
            'signal': signal,
            'decision': None,
        }
        
        if signal:
            direction = signal.get('direction', 'none')
            confidence = signal.get('confidence', 0)
            action['decision'] = f"{direction} with {confidence:.2%} confidence"
        
        # Call external action callback if set
        if self._action_callback:
            try:
                if asyncio.iscoroutinefunction(self._action_callback):
                    await self._action_callback(symbol, signal)
                else:
                    self._action_callback(symbol, signal)
            except Exception as e:
                logger.error(f"Action callback error: {e}")
        
        return action
    
    async def _receive_feedback(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        trade_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Phase 3: Receive market feedback"""
        logger.debug(f"FEEDBACK: Analyzing market reaction for {symbol}")
        
        feedback = {
            'reaction': None,
            'pnl': 0.0,
            'risk': 0.0,
        }
        
        if trade_result:
            feedback['pnl'] = trade_result.get('pnl', 0.0)
            feedback['risk'] = trade_result.get('risk_taken', 0.0)
            feedback['reaction'] = {
                'direction': 'favorable' if feedback['pnl'] > 0 else 'unfavorable',
                'magnitude': abs(feedback['pnl']),
            }
        
        # Call external feedback callback if set
        if self._feedback_callback:
            try:
                if asyncio.iscoroutinefunction(self._feedback_callback):
                    await self._feedback_callback(symbol, trade_result)
                else:
                    self._feedback_callback(symbol, trade_result)
            except Exception as e:
                logger.error(f"Feedback callback error: {e}")
        
        return feedback
    
    async def _evaluate(
        self,
        signal: Optional[Dict[str, Any]],
        trade_result: Optional[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Phase 4: Evaluate prediction vs outcome"""
        logger.debug("EVALUATE: Comparing prediction to outcome")
        
        evaluation = {
            'correct': None,
            'score': 0.0,
        }
        
        if signal and trade_result:
            predicted_direction = signal.get('direction', 'none')
            pnl = trade_result.get('pnl', 0)
            
            # Check if prediction was correct
            if predicted_direction == 'long':
                evaluation['correct'] = pnl > 0
            elif predicted_direction == 'short':
                evaluation['correct'] = pnl > 0
            else:
                evaluation['correct'] = None
            
            # Calculate evaluation score
            if evaluation['correct'] is True:
                evaluation['score'] = min(1.0, 0.5 + abs(pnl) / 100)
            elif evaluation['correct'] is False:
                evaluation['score'] = max(0.0, 0.5 - abs(pnl) / 100)
            else:
                evaluation['score'] = 0.5
        
        return evaluation
    
    async def _extract_lessons(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        signal: Optional[Dict[str, Any]],
        trade_result: Optional[Dict[str, Any]],
        evaluation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Phase 5: Extract lessons from the experience"""
        logger.debug("EXTRACT: Extracting lessons from experience")
        
        extraction = {
            'lessons': [],
            'patterns': [],
            'weaknesses': [],
        }
        
        # Extract lessons from market data
        if market_data:
            ohlcv = {
                'open': market_data.get('open', []),
                'high': market_data.get('high', []),
                'low': market_data.get('low', []),
                'close': market_data.get('close', []),
                'volume': market_data.get('volume', []),
            }
            indicators = market_data.get('indicators', {})
            
            # Get lessons from market teacher
            lessons = self._teacher.observe_price_action(
                symbol=symbol,
                timeframe=market_data.get('timeframe', '1H'),
                ohlcv=ohlcv,
                indicators=indicators,
                ai_prediction=signal
            )
            
            for lesson in lessons:
                extraction['lessons'].append(lesson.lesson_id)
                
                # Learn from each lesson
                learning_result = self._student.learn_from_lesson(lesson)
                extraction['patterns'].extend(
                    [p['pattern_type'] for p in learning_result.get('patterns_found', [])]
                )
                extraction['weaknesses'].extend(
                    [w['weakness_id'] for w in learning_result.get('weaknesses_identified', [])]
                )
        
        # Extract lessons from trade outcome
        if trade_result:
            trade_lessons = self._teacher.observe_trade_outcome(
                symbol=symbol,
                trade=trade_result,
                market_data=market_data,
                signal=signal or {}
            )
            
            for lesson in trade_lessons:
                extraction['lessons'].append(lesson.lesson_id)
                self._student.learn_from_lesson(lesson)
        
        return extraction
    
    async def _propose_improvements(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 6: Generate improvement proposals"""
        logger.debug("PROPOSE: Generating improvement proposals")
        
        proposals = {
            'proposal_ids': [],
        }
        
        # Proposals are generated automatically by StudentAI during learning
        # Here we just collect the pending ones
        pending = self._student.get_pending_proposals()
        proposals['proposal_ids'] = [p.proposal_id for p in pending]
        
        return proposals
    
    async def _integrate_approved(self) -> Dict[str, Any]:
        """Phase 8: Integrate approved improvements"""
        logger.debug("INTEGRATE: Applying approved improvements")
        
        integration = {
            'integrated': [],
        }
        
        # Get approved proposals
        for proposal_id, proposal in self._student._proposals.items():
            if proposal.status == ProposalStatus.APPROVED and not proposal.implemented_at:
                # Mark as implemented
                proposal.status = ProposalStatus.IMPLEMENTED
                proposal.implemented_at = datetime.now()
                integration['integrated'].append(proposal_id)
                
                logger.info(f"Integrated improvement: {proposal.title}")
        
        return integration
    
    async def start_continuous_learning(self):
        """Start continuous learning loop"""
        self._is_running = True
        logger.info("Starting continuous learning loop")
        
        while self._is_running:
            try:
                # In a real implementation, this would get live market data
                # For now, we just wait for the next cycle
                await asyncio.sleep(self._cycle_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in continuous learning: {e}")
                await asyncio.sleep(5)  # Brief pause on error
        
        logger.info("Continuous learning loop stopped")
    
    def stop_continuous_learning(self):
        """Stop continuous learning loop"""
        self._is_running = False
        logger.info("Stopping continuous learning loop")
    
    def get_cycle_statistics(self) -> Dict[str, Any]:
        """Get learning cycle statistics"""
        if not self._cycle_history:
            return {
                'total_cycles': 0,
                'success_rate': 0.0,
                'avg_duration_ms': 0.0,
                'total_lessons': 0,
                'total_proposals': 0,
            }
        
        successful = sum(1 for c in self._cycle_history if c.success)
        total_lessons = sum(len(c.lessons_extracted) for c in self._cycle_history)
        total_proposals = sum(len(c.proposals_generated) for c in self._cycle_history)
        
        return {
            'total_cycles': len(self._cycle_history),
            'success_rate': successful / len(self._cycle_history),
            'avg_duration_ms': sum(c.duration_ms for c in self._cycle_history) / len(self._cycle_history),
            'total_lessons': total_lessons,
            'total_proposals': total_proposals,
            'avg_lessons_per_cycle': total_lessons / len(self._cycle_history),
            'total_reward_score': sum(c.reward_score for c in self._cycle_history),
            'total_penalty_score': sum(c.penalty_score for c in self._cycle_history),
        }
    
    def get_last_cycle_result(self) -> Optional[CycleResult]:
        """Get the result of the last cycle"""
        return self._last_cycle_result
    
    def get_current_phase(self) -> CyclePhase:
        """Get the current phase"""
        return self._current_phase
