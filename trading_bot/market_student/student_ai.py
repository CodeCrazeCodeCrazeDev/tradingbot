"""
Student AI - The AI as a Disciplined Trading Student
=====================================================

The AI behaves like a disciplined trading student whose goals are:
- Understand the market's behavior deeply
- Learn from every outcome (wins, losses, missed trades)
- Extract lessons from volatility, liquidity, order flow, price action
- Improve decision-making over time
- Identify weaknesses and propose improvements
- Build intuition grounded in data
- Become more precise, more stable, and more risk-aware
- Never stop evolving, but always maintain stability and structure
- Seek clarity, simplicity, and accuracy

CRITICAL: The AI does NOT change code by itself.
It PROPOSES improvements, but REQUIRES human approval.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import logging
import json
import uuid
from pathlib import Path
from collections import deque
import numpy as np

from .market_teacher import MarketLesson, LessonType, LessonSeverity
from .reward_system import (
    ImmutableRewardSystem, 
    RewardSignal, 
    PenaltySignal,
    RewardCategory,
    PenaltyCategory,
    get_reward_system
)

logger = logging.getLogger(__name__)


# =============================================================================
# LEARNING STATE
# =============================================================================

class LearningPhase(Enum):
    """Current learning phase of the AI"""
    OBSERVING = "observing"           # Gathering data
    ANALYZING = "analyzing"           # Processing lessons
    REFLECTING = "reflecting"         # Extracting insights
    PROPOSING = "proposing"           # Creating improvement proposals
    AWAITING_APPROVAL = "awaiting"    # Waiting for human approval
    INTEGRATING = "integrating"       # Applying approved changes


@dataclass
class LearningState:
    """Current learning state of the AI"""
    
    phase: LearningPhase
    
    # Learning metrics
    total_lessons_learned: int
    lessons_today: int
    lessons_this_week: int
    
    # Performance tracking
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    
    # Learning progress
    patterns_recognized: int
    weaknesses_identified: int
    improvements_proposed: int
    improvements_approved: int
    improvements_rejected: int
    
    # Current focus
    current_focus_areas: List[str]
    recent_insights: List[str]
    
    # Timestamps
    last_lesson_at: Optional[datetime]
    last_improvement_at: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'phase': self.phase.value,
            'total_lessons_learned': self.total_lessons_learned,
            'lessons_today': self.lessons_today,
            'lessons_this_week': self.lessons_this_week,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'patterns_recognized': self.patterns_recognized,
            'weaknesses_identified': self.weaknesses_identified,
            'improvements_proposed': self.improvements_proposed,
            'improvements_approved': self.improvements_approved,
            'improvements_rejected': self.improvements_rejected,
            'current_focus_areas': self.current_focus_areas,
            'recent_insights': self.recent_insights,
            'last_lesson_at': self.last_lesson_at.isoformat() if self.last_lesson_at else None,
            'last_improvement_at': self.last_improvement_at.isoformat() if self.last_improvement_at else None,
        }


# =============================================================================
# IMPROVEMENT PROPOSALS
# =============================================================================

class ProposalStatus(Enum):
    """Status of an improvement proposal"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"


class ProposalType(Enum):
    """Type of improvement proposal"""
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    STRATEGY_MODIFICATION = "strategy_modification"
    RISK_LIMIT_CHANGE = "risk_limit_change"
    SIGNAL_FILTER_UPDATE = "signal_filter_update"
    EXECUTION_IMPROVEMENT = "execution_improvement"
    DATA_QUALITY_FIX = "data_quality_fix"
    ARCHITECTURE_CHANGE = "architecture_change"


class ProposalPriority(Enum):
    """Priority of improvement proposal"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ImprovementProposal:
    """A proposal for system improvement"""
    
    proposal_id: str
    proposal_type: ProposalType
    priority: ProposalPriority
    status: ProposalStatus
    
    # What to change
    title: str
    description: str
    rationale: str
    
    # Evidence
    supporting_lessons: List[str]  # Lesson IDs
    expected_impact: str
    risk_assessment: str
    
    # The actual change
    target_component: str
    current_value: Any
    proposed_value: Any
    change_details: Dict[str, Any]
    
    # Validation
    backtest_results: Optional[Dict[str, Any]] = None
    simulation_results: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    
    # Human interaction
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    human_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposal_id': self.proposal_id,
            'proposal_type': self.proposal_type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'title': self.title,
            'description': self.description,
            'rationale': self.rationale,
            'supporting_lessons': self.supporting_lessons,
            'expected_impact': self.expected_impact,
            'risk_assessment': self.risk_assessment,
            'target_component': self.target_component,
            'current_value': self.current_value,
            'proposed_value': self.proposed_value,
            'change_details': self.change_details,
            'created_at': self.created_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'implemented_at': self.implemented_at.isoformat() if self.implemented_at else None,
            'approved_by': self.approved_by,
            'rejection_reason': self.rejection_reason,
        }


# =============================================================================
# STUDENT AI
# =============================================================================

class StudentAI:
    """
    The AI as a disciplined trading student.
    
    Core principles:
    1. Learn from every market movement
    2. Extract lessons from wins, losses, and missed opportunities
    3. Propose improvements but NEVER implement without approval
    4. Maintain stability and structure while evolving
    5. Seek clarity, simplicity, and accuracy
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Get the immutable reward system
        self._reward_system = get_reward_system()
        
        # Learning state
        self._state = LearningState(
            phase=LearningPhase.OBSERVING,
            total_lessons_learned=0,
            lessons_today=0,
            lessons_this_week=0,
            win_rate=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            patterns_recognized=0,
            weaknesses_identified=0,
            improvements_proposed=0,
            improvements_approved=0,
            improvements_rejected=0,
            current_focus_areas=[],
            recent_insights=[],
            last_lesson_at=None,
            last_improvement_at=None,
        )
        
        # Lesson storage
        self._lessons_learned: List[MarketLesson] = []
        self._lesson_buffer: deque = deque(maxlen=10000)
        
        # Improvement proposals
        self._proposals: Dict[str, ImprovementProposal] = {}
        self._proposal_history: List[ImprovementProposal] = []
        
        # Pattern recognition
        self._recognized_patterns: Dict[str, Dict[str, Any]] = {}
        self._weakness_tracker: Dict[str, Dict[str, Any]] = {}
        
        # Storage
        self._storage_path = Path(self.config.get('storage_path', 'market_student_data'))
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("StudentAI initialized - Ready to learn from the market")
    
    def learn_from_lesson(self, lesson: MarketLesson) -> Dict[str, Any]:
        """
        Learn from a market lesson.
        
        Args:
            lesson: The lesson to learn from
            
        Returns:
            Learning result with insights and potential proposals
        """
        self._state.phase = LearningPhase.ANALYZING
        
        # Store the lesson
        self._lessons_learned.append(lesson)
        self._lesson_buffer.append(lesson)
        self._state.total_lessons_learned += 1
        self._state.lessons_today += 1
        self._state.last_lesson_at = datetime.now()
        
        # Evaluate against reward system
        rewards, penalties = self._reward_system.evaluate_behavior(
            'learning',
            {
                'learned_from_loss': lesson.severity in [LessonSeverity.HIGH, LessonSeverity.CRITICAL],
                'lesson_type': lesson.lesson_type.value,
                'impact_score': lesson.impact_score,
            }
        )
        
        # Extract insights
        insights = self._extract_insights(lesson)
        
        # Check for patterns
        patterns = self._recognize_patterns(lesson)
        
        # Identify weaknesses
        weaknesses = self._identify_weaknesses(lesson)
        
        # Update focus areas
        self._update_focus_areas(lesson, insights, weaknesses)
        
        # Generate improvement proposals if warranted
        proposals = []
        if lesson.severity in [LessonSeverity.CRITICAL, LessonSeverity.HIGH]:
            proposals = self._generate_proposals(lesson, insights, weaknesses)
        
        self._state.phase = LearningPhase.REFLECTING
        
        return {
            'lesson_id': lesson.lesson_id,
            'insights': insights,
            'patterns_found': patterns,
            'weaknesses_identified': weaknesses,
            'proposals_generated': [p.proposal_id for p in proposals],
            'rewards': len(rewards),
            'penalties': len(penalties),
            'cumulative_score': self._reward_system.get_cumulative_score(),
        }
    
    def _extract_insights(self, lesson: MarketLesson) -> List[str]:
        """Extract actionable insights from a lesson"""
        insights = []
        
        # Always include the lesson's own insight
        if lesson.actionable_insight:
            insights.append(lesson.actionable_insight)
        
        # Add context-specific insights
        if lesson.lesson_type == LessonType.RISK_REWARD_OUTCOME:
            if lesson.trade_context:
                pnl = lesson.trade_context.get('pnl', 0)
                if pnl < 0:
                    insights.append(f"Loss of {abs(pnl):.2f} - review entry criteria")
                    if lesson.trade_context.get('stop_hit'):
                        insights.append("Stop was hit - consider wider stops or better entries")
        
        elif lesson.lesson_type == LessonType.VOLATILITY_EXPANSION:
            insights.append("High volatility detected - reduce position sizes")
            insights.append("Consider waiting for volatility to normalize")
        
        elif lesson.lesson_type == LessonType.VOLUME_DIVERGENCE:
            insights.append("Volume not confirming price - be cautious")
            insights.append("Potential reversal setup forming")
        
        # Update state
        self._state.recent_insights = insights[:5]  # Keep top 5
        
        return insights
    
    def _recognize_patterns(self, lesson: MarketLesson) -> List[Dict[str, Any]]:
        """Recognize patterns from accumulated lessons"""
        patterns = []
        
        # Group lessons by type
        lesson_type = lesson.lesson_type.value
        
        if lesson_type not in self._recognized_patterns:
            self._recognized_patterns[lesson_type] = {
                'count': 0,
                'contexts': [],
                'outcomes': [],
            }
        
        pattern_data = self._recognized_patterns[lesson_type]
        pattern_data['count'] += 1
        pattern_data['contexts'].append(lesson.market_context)
        
        # Check if we have enough data to recognize a pattern
        if pattern_data['count'] >= 5:
            # Simple pattern: same lesson type occurring frequently
            patterns.append({
                'pattern_type': lesson_type,
                'occurrences': pattern_data['count'],
                'confidence': min(0.9, pattern_data['count'] / 10),
                'description': f"{lesson_type} pattern occurring frequently",
            })
            self._state.patterns_recognized += 1
        
        return patterns
    
    def _identify_weaknesses(self, lesson: MarketLesson) -> List[Dict[str, Any]]:
        """Identify system weaknesses from lessons"""
        weaknesses = []
        
        # Track weaknesses by category
        if lesson.severity in [LessonSeverity.CRITICAL, LessonSeverity.HIGH]:
            weakness_key = f"{lesson.lesson_type.value}_{lesson.discrepancy[:50]}"
            
            if weakness_key not in self._weakness_tracker:
                self._weakness_tracker[weakness_key] = {
                    'first_seen': datetime.now(),
                    'count': 0,
                    'lessons': [],
                    'description': lesson.discrepancy,
                }
            
            self._weakness_tracker[weakness_key]['count'] += 1
            self._weakness_tracker[weakness_key]['lessons'].append(lesson.lesson_id)
            
            # If weakness occurs multiple times, flag it
            if self._weakness_tracker[weakness_key]['count'] >= 3:
                weaknesses.append({
                    'weakness_id': weakness_key,
                    'type': lesson.lesson_type.value,
                    'description': lesson.discrepancy,
                    'occurrences': self._weakness_tracker[weakness_key]['count'],
                    'severity': 'high' if self._weakness_tracker[weakness_key]['count'] >= 5 else 'medium',
                })
                self._state.weaknesses_identified += 1
        
        return weaknesses
    
    def _update_focus_areas(
        self,
        lesson: MarketLesson,
        insights: List[str],
        weaknesses: List[Dict[str, Any]]
    ):
        """Update current focus areas based on learning"""
        focus_areas = set(self._state.current_focus_areas)
        
        # Add focus based on lesson type
        if lesson.lesson_type in [LessonType.VOLATILITY_EXPANSION, LessonType.VOLATILITY_REGIME_CHANGE]:
            focus_areas.add("volatility_management")
        
        if lesson.lesson_type in [LessonType.RISK_REWARD_OUTCOME]:
            if lesson.trade_context and lesson.trade_context.get('pnl', 0) < 0:
                focus_areas.add("entry_criteria")
                focus_areas.add("risk_management")
        
        if lesson.lesson_type in [LessonType.VOLUME_DIVERGENCE, LessonType.VOLUME_CLIMAX]:
            focus_areas.add("volume_analysis")
        
        # Add focus based on weaknesses
        for weakness in weaknesses:
            if weakness['severity'] == 'high':
                focus_areas.add(f"fix_{weakness['type']}")
        
        # Keep only top 5 focus areas
        self._state.current_focus_areas = list(focus_areas)[:5]
    
    def _generate_proposals(
        self,
        lesson: MarketLesson,
        insights: List[str],
        weaknesses: List[Dict[str, Any]]
    ) -> List[ImprovementProposal]:
        """Generate improvement proposals based on lessons"""
        proposals = []
        
        self._state.phase = LearningPhase.PROPOSING
        
        # Generate proposal based on lesson type
        if lesson.lesson_type == LessonType.RISK_REWARD_OUTCOME:
            if lesson.trade_context and lesson.trade_context.get('pnl', 0) < 0:
                # Propose entry criteria adjustment
                proposal = self._create_entry_criteria_proposal(lesson, insights)
                if proposal:
                    proposals.append(proposal)
        
        elif lesson.lesson_type == LessonType.VOLATILITY_EXPANSION:
            # Propose position sizing adjustment
            proposal = self._create_position_sizing_proposal(lesson, insights)
            if proposal:
                proposals.append(proposal)
        
        elif lesson.lesson_type == LessonType.VOLATILITY_REGIME_CHANGE:
            # Propose strategy adaptation
            proposal = self._create_strategy_adaptation_proposal(lesson, insights)
            if proposal:
                proposals.append(proposal)
        
        # Generate proposals for recurring weaknesses
        for weakness in weaknesses:
            if weakness['occurrences'] >= 5:
                proposal = self._create_weakness_fix_proposal(weakness, lesson)
                if proposal:
                    proposals.append(proposal)
        
        # Store proposals
        for proposal in proposals:
            self._proposals[proposal.proposal_id] = proposal
            self._state.improvements_proposed += 1
        
        self._state.phase = LearningPhase.AWAITING_APPROVAL
        
        return proposals
    
    def _create_entry_criteria_proposal(
        self,
        lesson: MarketLesson,
        insights: List[str]
    ) -> Optional[ImprovementProposal]:
        """Create proposal for entry criteria adjustment"""
        
        # Analyze the loss
        trade = lesson.trade_context or {}
        signal_confidence = trade.get('signal_confidence', 0.5)
        
        # Propose increasing minimum confidence
        new_confidence = min(0.8, signal_confidence + 0.1)
        
        return ImprovementProposal(
            proposal_id=f"prop_{uuid.uuid4().hex[:8]}",
            proposal_type=ProposalType.SIGNAL_FILTER_UPDATE,
            priority=ProposalPriority.MEDIUM,
            status=ProposalStatus.PENDING,
            title="Increase minimum signal confidence threshold",
            description=f"Based on losing trade analysis, propose increasing minimum confidence from {signal_confidence:.2%} to {new_confidence:.2%}",
            rationale=f"Lesson: {lesson.lesson_learned}. Insight: {insights[0] if insights else 'Improve entry quality'}",
            supporting_lessons=[lesson.lesson_id],
            expected_impact="Fewer but higher quality trades, improved win rate",
            risk_assessment="LOW - Conservative change, may reduce trade frequency",
            target_component="signal_filter.min_confidence",
            current_value=signal_confidence,
            proposed_value=new_confidence,
            change_details={
                'parameter': 'min_confidence',
                'change_type': 'increase',
                'change_amount': new_confidence - signal_confidence,
            }
        )
    
    def _create_position_sizing_proposal(
        self,
        lesson: MarketLesson,
        insights: List[str]
    ) -> Optional[ImprovementProposal]:
        """Create proposal for position sizing adjustment"""
        
        current_risk = self._reward_system.get_risk_limits()['max_risk_per_trade']
        proposed_risk = current_risk * 0.75  # Reduce by 25% in high volatility
        
        return ImprovementProposal(
            proposal_id=f"prop_{uuid.uuid4().hex[:8]}",
            proposal_type=ProposalType.RISK_LIMIT_CHANGE,
            priority=ProposalPriority.HIGH,
            status=ProposalStatus.PENDING,
            title="Reduce position size during high volatility",
            description=f"Volatility expansion detected. Propose reducing max risk per trade from {current_risk:.2%} to {proposed_risk:.2%}",
            rationale=f"Lesson: {lesson.lesson_learned}. High volatility requires smaller positions.",
            supporting_lessons=[lesson.lesson_id],
            expected_impact="Reduced drawdown during volatile periods",
            risk_assessment="LOW - Conservative change, improves risk management",
            target_component="risk_manager.max_risk_per_trade",
            current_value=current_risk,
            proposed_value=proposed_risk,
            change_details={
                'parameter': 'max_risk_per_trade',
                'change_type': 'decrease',
                'trigger': 'high_volatility',
                'change_amount': current_risk - proposed_risk,
            }
        )
    
    def _create_strategy_adaptation_proposal(
        self,
        lesson: MarketLesson,
        insights: List[str]
    ) -> Optional[ImprovementProposal]:
        """Create proposal for strategy adaptation"""
        
        return ImprovementProposal(
            proposal_id=f"prop_{uuid.uuid4().hex[:8]}",
            proposal_type=ProposalType.STRATEGY_MODIFICATION,
            priority=ProposalPriority.MEDIUM,
            status=ProposalStatus.PENDING,
            title="Adapt strategy to new market regime",
            description=f"Market regime changed. Propose adapting strategy parameters.",
            rationale=f"Lesson: {lesson.lesson_learned}. {lesson.actionable_insight}",
            supporting_lessons=[lesson.lesson_id],
            expected_impact="Better alignment with current market conditions",
            risk_assessment="MEDIUM - Strategy change requires careful monitoring",
            target_component="strategy_engine.regime_parameters",
            current_value="previous_regime",
            proposed_value="adapted_regime",
            change_details={
                'adaptation_type': 'regime_change',
                'insight': lesson.actionable_insight,
            }
        )
    
    def _create_weakness_fix_proposal(
        self,
        weakness: Dict[str, Any],
        lesson: MarketLesson
    ) -> Optional[ImprovementProposal]:
        """Create proposal to fix a recurring weakness"""
        
        return ImprovementProposal(
            proposal_id=f"prop_{uuid.uuid4().hex[:8]}",
            proposal_type=ProposalType.PARAMETER_ADJUSTMENT,
            priority=ProposalPriority.HIGH,
            status=ProposalStatus.PENDING,
            title=f"Fix recurring weakness: {weakness['type']}",
            description=f"Weakness '{weakness['description']}' has occurred {weakness['occurrences']} times",
            rationale=f"Recurring issue needs systematic fix. Last lesson: {lesson.lesson_learned}",
            supporting_lessons=weakness.get('lessons', [lesson.lesson_id]),
            expected_impact="Eliminate recurring issue, improve consistency",
            risk_assessment="MEDIUM - Addresses root cause of multiple losses",
            target_component=f"weakness_fix.{weakness['type']}",
            current_value="current_behavior",
            proposed_value="improved_behavior",
            change_details={
                'weakness_id': weakness['weakness_id'],
                'occurrences': weakness['occurrences'],
                'fix_type': 'systematic',
            }
        )
    
    def get_pending_proposals(self) -> List[ImprovementProposal]:
        """Get all pending improvement proposals"""
        return [p for p in self._proposals.values() if p.status == ProposalStatus.PENDING]
    
    def approve_proposal(self, proposal_id: str, approver: str, notes: Optional[str] = None) -> bool:
        """
        Approve an improvement proposal (HUMAN ACTION).
        
        Args:
            proposal_id: ID of the proposal
            approver: Name of the human approver
            notes: Optional notes from the approver
            
        Returns:
            True if approved successfully
        """
        if proposal_id not in self._proposals:
            logger.error(f"Proposal {proposal_id} not found")
            return False
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status != ProposalStatus.PENDING:
            logger.error(f"Proposal {proposal_id} is not pending")
            return False
        
        proposal.status = ProposalStatus.APPROVED
        proposal.approved_at = datetime.now()
        proposal.approved_by = approver
        proposal.human_notes = notes
        
        self._state.improvements_approved += 1
        self._state.last_improvement_at = datetime.now()
        self._state.phase = LearningPhase.INTEGRATING
        
        logger.info(f"Proposal {proposal_id} approved by {approver}")
        
        # Evaluate approval against reward system
        self._reward_system.evaluate_behavior(
            'evolution',
            {
                'human_approved': True,
                'safety_preserved': True,
                'improvement_validated': True,
            }
        )
        
        return True
    
    def reject_proposal(self, proposal_id: str, reason: str) -> bool:
        """
        Reject an improvement proposal (HUMAN ACTION).
        
        Args:
            proposal_id: ID of the proposal
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        if proposal_id not in self._proposals:
            logger.error(f"Proposal {proposal_id} not found")
            return False
        
        proposal = self._proposals[proposal_id]
        
        if proposal.status != ProposalStatus.PENDING:
            logger.error(f"Proposal {proposal_id} is not pending")
            return False
        
        proposal.status = ProposalStatus.REJECTED
        proposal.rejection_reason = reason
        
        self._state.improvements_rejected += 1
        self._proposal_history.append(proposal)
        
        logger.info(f"Proposal {proposal_id} rejected: {reason}")
        
        # Learn from rejection
        self._learn_from_rejection(proposal, reason)
        
        return True
    
    def _learn_from_rejection(self, proposal: ImprovementProposal, reason: str):
        """Learn from a rejected proposal"""
        # This helps the AI understand what proposals are not acceptable
        logger.info(f"Learning from rejection: {reason}")
        
        # Track rejection patterns
        rejection_key = f"{proposal.proposal_type.value}_{reason[:30]}"
        # Store for future reference to avoid similar proposals
    
    def update_performance_metrics(
        self,
        win_rate: float,
        profit_factor: float,
        sharpe_ratio: float,
        max_drawdown: float
    ):
        """Update performance metrics"""
        self._state.win_rate = win_rate
        self._state.profit_factor = profit_factor
        self._state.sharpe_ratio = sharpe_ratio
        self._state.max_drawdown = max_drawdown
        
        # Evaluate performance against reward system
        self._reward_system.evaluate_behavior(
            'risk',
            {
                'drawdown': max_drawdown,
                'sharpe': sharpe_ratio,
            }
        )
    
    def get_learning_state(self) -> LearningState:
        """Get current learning state"""
        return self._state
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning progress"""
        return {
            'state': self._state.to_dict(),
            'total_lessons': len(self._lessons_learned),
            'patterns_recognized': len(self._recognized_patterns),
            'weaknesses_tracked': len(self._weakness_tracker),
            'pending_proposals': len(self.get_pending_proposals()),
            'reward_score': self._reward_system.get_cumulative_score(),
            'focus_areas': self._state.current_focus_areas,
            'recent_insights': self._state.recent_insights,
        }
    
    def save_state(self):
        """Save learning state to disk"""
        state_file = self._storage_path / 'learning_state.json'
        
        state_data = {
            'state': self._state.to_dict(),
            'patterns': self._recognized_patterns,
            'weaknesses': {k: {**v, 'first_seen': v['first_seen'].isoformat()} 
                         for k, v in self._weakness_tracker.items()},
            'proposals': {k: v.to_dict() for k, v in self._proposals.items()},
            'saved_at': datetime.now().isoformat(),
        }
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2, default=str)
        
        logger.info(f"Learning state saved to {state_file}")
    
    def load_state(self):
        """Load learning state from disk"""
        state_file = self._storage_path / 'learning_state.json'
        
        if not state_file.exists():
            logger.info("No saved state found")
            return
        try:
        
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            # Restore state (simplified - full implementation would restore all fields)
            self._recognized_patterns = state_data.get('patterns', {})
            
            logger.info(f"Learning state loaded from {state_file}")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
