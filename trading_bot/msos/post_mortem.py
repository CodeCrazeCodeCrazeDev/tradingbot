"""
AlphaAlgo MSOS - Post-Mortem Engine

Every strategy failure must produce:
- Assumption violated
- Early warning missed
- Preventability assessment
- Constraint update proposal

Memory exists to tighten constraints, not chase performance.
Failures are treated as system intelligence, not embarrassment.

Author: AlphaAlgo MSOS
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FailureSeverity(Enum):
    """Failure severity levels"""
    MINOR = auto()        # Small loss, expected variance
    MODERATE = auto()     # Significant loss, needs review
    SEVERE = auto()       # Major loss, immediate action needed
    CATASTROPHIC = auto() # System-threatening loss


class FailureCategory(Enum):
    """Categories of failures"""
    ASSUMPTION_VIOLATION = auto()
    REGIME_MISMATCH = auto()
    EXECUTION_FAILURE = auto()
    DATA_QUALITY = auto()
    MODEL_DECAY = auto()
    LIQUIDITY_CRISIS = auto()
    BLACK_SWAN = auto()
    OPERATIONAL = auto()
    UNKNOWN = auto()


class PreventabilityLevel(Enum):
    """How preventable was the failure"""
    FULLY_PREVENTABLE = auto()      # Should have been caught
    PARTIALLY_PREVENTABLE = auto()  # Some warning signs missed
    DIFFICULT_TO_PREVENT = auto()   # Limited warning
    UNPREVENTABLE = auto()          # True black swan


@dataclass
class AssumptionViolated:
    """Record of a violated assumption"""
    assumption_name: str
    expected_value: float
    actual_value: float
    deviation: float
    was_monitored: bool
    early_warning_available: bool
    warning_ignored: bool = False


@dataclass
class EarlyWarningMissed:
    """Record of a missed early warning"""
    warning_type: str
    signal_strength: float
    time_before_failure: float  # Seconds
    was_visible: bool
    why_missed: str


@dataclass
class ConstraintProposal:
    """Proposed constraint update based on failure"""
    constraint_name: str
    current_value: float
    proposed_value: float
    rationale: str
    expected_impact: str
    risk_of_change: str


@dataclass
class FailureAnalysis:
    """Complete analysis of a failure"""
    failure_id: str
    strategy_id: str
    timestamp: float
    severity: FailureSeverity
    category: FailureCategory
    loss_amount: float
    loss_percentage: float
    assumptions_violated: List[AssumptionViolated]
    warnings_missed: List[EarlyWarningMissed]
    preventability: PreventabilityLevel
    preventability_score: float  # 0-1
    root_cause: str
    contributing_factors: List[str]
    constraint_proposals: List[ConstraintProposal]
    lessons_learned: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'failure_id': self.failure_id,
            'strategy_id': self.strategy_id,
            'timestamp': self.timestamp,
            'severity': self.severity.name,
            'category': self.category.name,
            'loss_amount': self.loss_amount,
            'loss_percentage': self.loss_percentage,
            'assumptions_violated': len(self.assumptions_violated),
            'warnings_missed': len(self.warnings_missed),
            'preventability': self.preventability.name,
            'preventability_score': self.preventability_score,
            'root_cause': self.root_cause,
            'constraint_proposals': len(self.constraint_proposals),
            'lessons_learned': self.lessons_learned
        }


@dataclass
class PostMortemResult:
    """Result from post-mortem analysis"""
    analysis: FailureAnalysis
    action_items: List[str]
    constraints_to_update: List[ConstraintProposal]
    strategies_to_review: List[str]
    immediate_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'failure_id': self.analysis.failure_id,
            'severity': self.analysis.severity.name,
            'action_items': self.action_items,
            'constraints_to_update': len(self.constraints_to_update),
            'strategies_to_review': self.strategies_to_review,
            'immediate_actions': self.immediate_actions
        }


class PostMortemEngine:
    """
    Post-Mortem Engine
    
    RULES:
    1. Every failure MUST produce a post-mortem
    2. Identify assumptions violated
    3. Identify early warnings missed
    4. Assess preventability
    5. Propose constraint updates
    6. Memory is for tightening constraints, NOT chasing performance
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.post_mortem")
        
            # History
            self._analyses: List[FailureAnalysis] = []
            self._constraint_proposals: List[ConstraintProposal] = []
            self._failure_count = 0
        
            self.logger.info("Post-Mortem Engine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_failure(
        self,
        strategy_id: str,
        loss_amount: float,
        loss_percentage: float,
        market_data: Dict[str, Any],
        strategy_state: Dict[str, Any],
        assumptions: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ) -> PostMortemResult:
        """
        Perform complete post-mortem analysis of a failure.
        """
        try:
            self._failure_count += 1
            failure_id = f"FAILURE_{self._failure_count}_{int(time.time())}"
        
            # Determine severity
            severity = self._determine_severity(loss_percentage)
        
            # Analyze assumptions
            assumptions_violated = self._analyze_assumptions(assumptions, market_data)
        
            # Analyze warnings
            warnings_missed = self._analyze_warnings(warnings)
        
            # Determine category
            category = self._determine_category(
                assumptions_violated, warnings_missed, market_data
            )
        
            # Assess preventability
            preventability, prev_score = self._assess_preventability(
                assumptions_violated, warnings_missed
            )
        
            # Identify root cause
            root_cause = self._identify_root_cause(
                category, assumptions_violated, warnings_missed, market_data
            )
        
            # Identify contributing factors
            contributing_factors = self._identify_contributing_factors(
                market_data, strategy_state
            )
        
            # Generate constraint proposals
            constraint_proposals = self._generate_constraint_proposals(
                assumptions_violated, category, loss_percentage
            )
        
            # Extract lessons
            lessons = self._extract_lessons(
                category, assumptions_violated, warnings_missed, preventability
            )
        
            analysis = FailureAnalysis(
                failure_id=failure_id,
                strategy_id=strategy_id,
                timestamp=time.time(),
                severity=severity,
                category=category,
                loss_amount=loss_amount,
                loss_percentage=loss_percentage,
                assumptions_violated=assumptions_violated,
                warnings_missed=warnings_missed,
                preventability=preventability,
                preventability_score=prev_score,
                root_cause=root_cause,
                contributing_factors=contributing_factors,
                constraint_proposals=constraint_proposals,
                lessons_learned=lessons
            )
        
            # Store analysis
            self._analyses.append(analysis)
            self._constraint_proposals.extend(constraint_proposals)
        
            # Generate action items
            action_items = self._generate_action_items(analysis)
            immediate_actions = self._generate_immediate_actions(analysis)
            strategies_to_review = self._identify_related_strategies(strategy_id)
        
            result = PostMortemResult(
                analysis=analysis,
                action_items=action_items,
                constraints_to_update=constraint_proposals,
                strategies_to_review=strategies_to_review,
                immediate_actions=immediate_actions
            )
        
            self.logger.warning(
                f"POST-MORTEM: {failure_id} | {severity.name} | "
                f"Loss: {loss_percentage:.2%} | Category: {category.name} | "
                f"Preventability: {preventability.name}"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in analyze_failure: {e}")
            raise
    
    def _determine_severity(self, loss_percentage: float) -> FailureSeverity:
        """Determine failure severity"""
        try:
            if loss_percentage >= 0.10:
                return FailureSeverity.CATASTROPHIC
            elif loss_percentage >= 0.05:
                return FailureSeverity.SEVERE
            elif loss_percentage >= 0.02:
                return FailureSeverity.MODERATE
            else:
                return FailureSeverity.MINOR
        except Exception as e:
            logger.error(f"Error in _determine_severity: {e}")
            raise
    
    def _analyze_assumptions(
        self,
        assumptions: List[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> List[AssumptionViolated]:
        """Analyze which assumptions were violated"""
        try:
            violated = []
        
            for assumption in assumptions:
                name = assumption.get('name', 'unknown')
                expected = assumption.get('expected_value', 0)
                actual = market_data.get(assumption.get('market_field', ''), expected)
                tolerance = assumption.get('tolerance', 0.1)
            
                deviation = abs(actual - expected) / (abs(expected) + 1e-10)
            
                if deviation > tolerance:
                    violated.append(AssumptionViolated(
                        assumption_name=name,
                        expected_value=expected,
                        actual_value=actual,
                        deviation=deviation,
                        was_monitored=assumption.get('monitored', False),
                        early_warning_available=assumption.get('has_warning', False),
                        warning_ignored=assumption.get('warning_ignored', False)
                    ))
        
            return violated
        except Exception as e:
            logger.error(f"Error in _analyze_assumptions: {e}")
            raise
    
    def _analyze_warnings(
        self,
        warnings: List[Dict[str, Any]]
    ) -> List[EarlyWarningMissed]:
        """Analyze which early warnings were missed"""
        try:
            missed = []
        
            for warning in warnings:
                if warning.get('was_triggered', False) and not warning.get('was_acted_on', False):
                    missed.append(EarlyWarningMissed(
                        warning_type=warning.get('type', 'unknown'),
                        signal_strength=warning.get('strength', 0),
                        time_before_failure=warning.get('time_before', 0),
                        was_visible=warning.get('visible', True),
                        why_missed=warning.get('reason_missed', 'Unknown')
                    ))
        
            return missed
        except Exception as e:
            logger.error(f"Error in _analyze_warnings: {e}")
            raise
    
    def _determine_category(
        self,
        assumptions_violated: List[AssumptionViolated],
        warnings_missed: List[EarlyWarningMissed],
        market_data: Dict[str, Any]
    ) -> FailureCategory:
        """Determine failure category"""
        try:
            if len(assumptions_violated) > 0:
                return FailureCategory.ASSUMPTION_VIOLATION
        
            if market_data.get('regime_changed', False):
                return FailureCategory.REGIME_MISMATCH
        
            if market_data.get('execution_failed', False):
                return FailureCategory.EXECUTION_FAILURE
        
            if market_data.get('data_quality_issue', False):
                return FailureCategory.DATA_QUALITY
        
            if market_data.get('liquidity_crisis', False):
                return FailureCategory.LIQUIDITY_CRISIS
        
            if market_data.get('black_swan', False):
                return FailureCategory.BLACK_SWAN
        
            return FailureCategory.UNKNOWN
        except Exception as e:
            logger.error(f"Error in _determine_category: {e}")
            raise
    
    def _assess_preventability(
        self,
        assumptions_violated: List[AssumptionViolated],
        warnings_missed: List[EarlyWarningMissed]
    ) -> tuple:
        """Assess how preventable the failure was"""
        try:
            score = 0.0
        
            # Check if assumptions were monitored
            monitored_violations = sum(1 for a in assumptions_violated if a.was_monitored)
            if assumptions_violated:
                score += 0.3 * (monitored_violations / len(assumptions_violated))
        
            # Check if warnings were available
            available_warnings = sum(1 for a in assumptions_violated if a.early_warning_available)
            if assumptions_violated:
                score += 0.3 * (available_warnings / len(assumptions_violated))
        
            # Check if warnings were ignored
            ignored_warnings = sum(1 for a in assumptions_violated if a.warning_ignored)
            if assumptions_violated:
                score += 0.4 * (ignored_warnings / len(assumptions_violated))
        
            # Determine level
            if score >= 0.7:
                return PreventabilityLevel.FULLY_PREVENTABLE, score
            elif score >= 0.4:
                return PreventabilityLevel.PARTIALLY_PREVENTABLE, score
            elif score >= 0.2:
                return PreventabilityLevel.DIFFICULT_TO_PREVENT, score
            else:
                return PreventabilityLevel.UNPREVENTABLE, score
        except Exception as e:
            logger.error(f"Error in _assess_preventability: {e}")
            raise
    
    def _identify_root_cause(
        self,
        category: FailureCategory,
        assumptions_violated: List[AssumptionViolated],
        warnings_missed: List[EarlyWarningMissed],
        market_data: Dict[str, Any]
    ) -> str:
        """Identify root cause of failure"""
        try:
            if category == FailureCategory.ASSUMPTION_VIOLATION:
                if assumptions_violated:
                    main_violation = max(assumptions_violated, key=lambda a: a.deviation)
                    return f"Assumption '{main_violation.assumption_name}' violated: expected {main_violation.expected_value}, got {main_violation.actual_value}"
        
            if category == FailureCategory.REGIME_MISMATCH:
                return "Strategy operated in wrong regime"
        
            if category == FailureCategory.EXECUTION_FAILURE:
                return "Execution failed to meet expectations"
        
            if category == FailureCategory.LIQUIDITY_CRISIS:
                return "Liquidity crisis prevented proper execution"
        
            if category == FailureCategory.BLACK_SWAN:
                return "Unprecedented market event (black swan)"
        
            return "Root cause undetermined"
        except Exception as e:
            logger.error(f"Error in _identify_root_cause: {e}")
            raise
    
    def _identify_contributing_factors(
        self,
        market_data: Dict[str, Any],
        strategy_state: Dict[str, Any]
    ) -> List[str]:
        """Identify contributing factors"""
        try:
            factors = []
        
            if market_data.get('volatility', 0) > 0.03:
                factors.append("Elevated volatility")
        
            if market_data.get('liquidity', 1) < 0.5:
                factors.append("Low liquidity")
        
            if market_data.get('correlation', 0) > 0.8:
                factors.append("High correlation environment")
        
            if strategy_state.get('position_size', 0) > 0.1:
                factors.append("Large position size")
        
            if strategy_state.get('holding_period', 0) > 10:
                factors.append("Extended holding period")
        
            return factors
        except Exception as e:
            logger.error(f"Error in _identify_contributing_factors: {e}")
            raise
    
    def _generate_constraint_proposals(
        self,
        assumptions_violated: List[AssumptionViolated],
        category: FailureCategory,
        loss_percentage: float
    ) -> List[ConstraintProposal]:
        """Generate constraint update proposals"""
        try:
            proposals = []
        
            for violation in assumptions_violated:
                # Propose tighter tolerance
                new_tolerance = violation.deviation * 0.5  # Tighten by 50%
                proposals.append(ConstraintProposal(
                    constraint_name=f"{violation.assumption_name}_tolerance",
                    current_value=violation.deviation,
                    proposed_value=new_tolerance,
                    rationale=f"Assumption violated with deviation {violation.deviation:.2%}",
                    expected_impact="Earlier detection of assumption violations",
                    risk_of_change="May increase false positives"
                ))
        
            # Propose position size reduction if severe
            if loss_percentage > 0.05:
                proposals.append(ConstraintProposal(
                    constraint_name="max_position_size",
                    current_value=0.10,
                    proposed_value=0.05,
                    rationale=f"Severe loss of {loss_percentage:.2%}",
                    expected_impact="Reduced maximum loss per position",
                    risk_of_change="May reduce returns"
                ))
        
            return proposals
        except Exception as e:
            logger.error(f"Error in _generate_constraint_proposals: {e}")
            raise
    
    def _extract_lessons(
        self,
        category: FailureCategory,
        assumptions_violated: List[AssumptionViolated],
        warnings_missed: List[EarlyWarningMissed],
        preventability: PreventabilityLevel
    ) -> List[str]:
        """Extract lessons learned"""
        try:
            lessons = []
        
            if assumptions_violated:
                lessons.append(f"Monitor {len(assumptions_violated)} assumptions more closely")
        
            if warnings_missed:
                lessons.append(f"Act on {len(warnings_missed)} early warnings that were missed")
        
            if preventability == PreventabilityLevel.FULLY_PREVENTABLE:
                lessons.append("This failure was fully preventable - review monitoring systems")
        
            if category == FailureCategory.REGIME_MISMATCH:
                lessons.append("Improve regime detection before strategy deployment")
        
            lessons.append("Update constraints based on this failure")
        
            return lessons
        except Exception as e:
            logger.error(f"Error in _extract_lessons: {e}")
            raise
    
    def _generate_action_items(self, analysis: FailureAnalysis) -> List[str]:
        """Generate action items from analysis"""
        try:
            items = []
        
            items.append(f"Review strategy {analysis.strategy_id}")
        
            for proposal in analysis.constraint_proposals:
                items.append(f"Consider updating {proposal.constraint_name}")
        
            if analysis.preventability == PreventabilityLevel.FULLY_PREVENTABLE:
                items.append("Investigate why preventable failure was not prevented")
        
            if analysis.severity in [FailureSeverity.SEVERE, FailureSeverity.CATASTROPHIC]:
                items.append("Conduct full strategy review")
                items.append("Consider strategy suspension")
        
            return items
        except Exception as e:
            logger.error(f"Error in _generate_action_items: {e}")
            raise
    
    def _generate_immediate_actions(self, analysis: FailureAnalysis) -> List[str]:
        """Generate immediate actions"""
        try:
            actions = []
        
            if analysis.severity == FailureSeverity.CATASTROPHIC:
                actions.append("SUSPEND STRATEGY IMMEDIATELY")
                actions.append("REDUCE ALL EXPOSURE")
        
            if analysis.severity == FailureSeverity.SEVERE:
                actions.append("Reduce strategy exposure by 50%")
        
            return actions
        except Exception as e:
            logger.error(f"Error in _generate_immediate_actions: {e}")
            raise
    
    def _identify_related_strategies(self, strategy_id: str) -> List[str]:
        """Identify strategies that should be reviewed"""
        # In a real implementation, this would look at correlated strategies
        return [strategy_id]
    
    def get_failure_history(self) -> List[FailureAnalysis]:
        """Get failure history"""
        return self._analyses.copy()
    
    def get_pending_proposals(self) -> List[ConstraintProposal]:
        """Get pending constraint proposals"""
        return self._constraint_proposals.copy()
    
    def get_failure_stats(self) -> Dict[str, Any]:
        """Get failure statistics"""
        try:
            if not self._analyses:
                return {'total_failures': 0}
        
            return {
                'total_failures': len(self._analyses),
                'by_severity': {
                    s.name: sum(1 for a in self._analyses if a.severity == s)
                    for s in FailureSeverity
                },
                'by_category': {
                    c.name: sum(1 for a in self._analyses if a.category == c)
                    for c in FailureCategory
                },
                'average_preventability': np.mean([a.preventability_score for a in self._analyses]),
                'total_loss': sum(a.loss_amount for a in self._analyses)
            }
        except Exception as e:
            logger.error(f"Error in get_failure_stats: {e}")
            raise
