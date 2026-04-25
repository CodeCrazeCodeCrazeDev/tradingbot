"""
Decision Governance System (DGS) - Core Types and Data Structures

A self-auditing epistemic governance system that converts analysis into structured claims,
detects missing evidence and weak logic, attacks its own conclusions adversarially,
estimates regime-conditional validity and execution realism, calibrates uncertainty,
and only permits capital deployment when the reasoning graph is sufficiently
complete, coherent, and robust.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union
from collections import defaultdict, deque
import uuid
import json
import hashlib


class ClaimType(Enum):
    """Types of claims in the reasoning graph"""
    THESIS = "thesis"
    ASSUMPTION = "assumption"
    EVIDENCE = "evidence"
    INFERRED_CAUSAL_LINK = "inferred_causal_link"
    PREDICTED_OUTCOME = "predicted_outcome"
    INVALIDATION_CONDITION = "invalidation_condition"


class EvidenceStatus(Enum):
    """Status of evidence for a claim"""
    PRESENT = "present"
    MISSING = "missing"
    STALE = "stale"
    CONFLICTING = "conflicting"
    INSUFFICIENT = "insufficient"


class UncertaintyType(Enum):
    """Types of uncertainty in decision making"""
    ALEATORIC = "aleatoric"  # Inherent randomness
    EPISTEMIC = "epistemic"  # Lack of knowledge
    MODEL = "model"  # Model uncertainty
    REGIME = "regime"  # Regime applicability uncertainty
    EXECUTION = "execution"  # Execution feasibility uncertainty


class GovernanceDecision(Enum):
    """Final governance decisions"""
    APPROVE = "approve"
    RESIZE = "resize"
    DEFER = "defer"
    REJECT = "reject"
    ABSTAIN = "abstain"


class RegimeDimension(Enum):
    """Multidimensional regime ontology"""
    VOLATILITY_STATE = "volatility_state"
    LIQUIDITY_STATE = "liquidity_state"
    TREND_PERSISTENCE = "trend_persistence"
    CORRELATION_CLUSTERING = "correlation_clustering"
    MACRO_EVENT_DENSITY = "macro_event_density"
    ORDER_FLOW_TOXICITY = "order_flow_toxicity"
    SPREAD_IMPACT_CONDITIONS = "spread_impact_conditions"


@dataclass
class MarketRegime:
    """Multidimensional market regime characterization"""
    volatility_state: str  # low, normal, high, extreme
    liquidity_state: str  # ample, normal, constrained, scarce
    trend_persistence: float  # 0 to 1
    correlation_clustering: str  # dispersed, emerging, high
    macro_event_density: str  # quiet, normal, elevated, crisis
    order_flow_toxicity: str  # benign, elevated, toxic
    spread_impact_conditions: str  # favorable, normal, adverse, prohibitive
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_vector(self) -> Dict[str, float]:
        """Convert regime to numerical vector for similarity comparison"""
        volatility_map = {"low": 0.0, "normal": 0.33, "high": 0.66, "extreme": 1.0}
        liquidity_map = {"ample": 0.0, "normal": 0.33, "constrained": 0.66, "scarce": 1.0}
        correlation_map = {"dispersed": 0.0, "emerging": 0.5, "high": 1.0}
        macro_map = {"quiet": 0.0, "normal": 0.33, "elevated": 0.66, "crisis": 1.0}
        toxicity_map = {"benign": 0.0, "elevated": 0.5, "toxic": 1.0}
        spread_map = {"favorable": 0.0, "normal": 0.33, "adverse": 0.66, "prohibitive": 1.0}
        
        return {
            "volatility": volatility_map.get(self.volatility_state, 0.5),
            "liquidity": liquidity_map.get(self.liquidity_state, 0.5),
            "trend_persistence": self.trend_persistence,
            "correlation": correlation_map.get(self.correlation_clustering, 0.5),
            "macro_density": macro_map.get(self.macro_event_density, 0.5),
            "flow_toxicity": toxicity_map.get(self.order_flow_toxicity, 0.5),
            "spread_impact": spread_map.get(self.spread_impact_conditions, 0.5)
        }


@dataclass
class Claim:
    """A structured claim in the reasoning graph"""
    id: str
    claim_type: ClaimType
    content: str
    source: str  # Agent or system that generated this
    timestamp: datetime
    confidence: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)
    dependent_claims: List[str] = field(default_factory=list)  # Claims this depends on
    invalidation_conditions: List[str] = field(default_factory=list)
    regime_constraints: List[str] = field(default_factory=list)  # Regimes where this applies
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def compute_hash(self) -> str:
        """Compute unique hash of this claim"""
        content = f"{self.claim_type.value}:{self.content}:{self.source}:{self.timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class Evidence:
    """Evidence supporting or contradicting a claim"""
    id: str
    claim_id: str
    evidence_type: str
    content: Any
    source: str
    timestamp: datetime
    freshness: float  # 0 to 1, 1 being fresh
    strength: float  # 0 to 1
    status: EvidenceStatus = EvidenceStatus.PRESENT
    contradictions: List[str] = field(default_factory=list)  # IDs of conflicting evidence
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class AdversarialChallenge:
    """Challenge generated by adversarial counter-analyst"""
    id: str
    target_claim_id: str
    challenge_type: str  # rival_explanation, hidden_assumption, failure_condition, base_rate, regime_mismatch, execution
    content: str
    severity: float  # 0 to 1
    supporting_arguments: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class UncertaintyProfile:
    """Comprehensive uncertainty decomposition"""
    overall_confidence: float  # 0 to 1
    calibration_quality: float  # 0 to 1
    abstention_probability: float  # 0 to 1
    decomposition: Dict[UncertaintyType, float] = field(default_factory=dict)
    confidence_under_distribution_shift: float = 0.0
    
    def __post_init__(self):
        # Ensure all uncertainty types have values
        for ut in UncertaintyType:
            if ut not in self.decomposition:
                self.decomposition[ut] = 0.0


@dataclass
class ExecutionFeasibility:
    """Execution feasibility assessment"""
    feasible: bool
    expected_slippage: float
    expected_fill_rate: float
    cost_adjusted_expectancy: float
    liquidity_score: float  # 0 to 1
    timing_risks: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class DecisionRecord:
    """Complete record of a governance decision"""
    id: str
    timestamp: datetime
    symbol: str
    signal_source: str
    
    # Layer 1: Claim Graph
    claims: List[Claim] = field(default_factory=list)
    
    # Layer 2: Evidence Assessment
    evidence_coverage: Dict[str, EvidenceStatus] = field(default_factory=dict)
    evidence_gaps: List[str] = field(default_factory=list)
    contradictions: List[Tuple[str, str]] = field(default_factory=list)  # (evidence1, evidence2)
    
    # Layer 3: Adversarial Challenges
    adversarial_challenges: List[AdversarialChallenge] = field(default_factory=list)
    challenge_responses: Dict[str, str] = field(default_factory=dict)
    
    # Layer 4: Regime Fit
    current_regime: Optional[MarketRegime] = None
    regime_applicability_score: float = 0.0
    historical_regime_matches: List[Dict] = field(default_factory=list)
    regime_underrepresentation_warning: bool = False
    
    # Layer 5: Counterfactual Results
    counterfactual_scenarios: List[Dict] = field(default_factory=list)
    robustness_score: float = 0.0
    
    # Layer 6: Uncertainty
    uncertainty_profile: Optional[UncertaintyProfile] = None
    
    # Layer 7: Final Decision
    final_decision: GovernanceDecision = GovernanceDecision.ABSTAIN
    decision_reasoning: str = ""
    approved_size: float = 0.0
    risk_adjusted_size: float = 0.0
    
    # Audit trail
    audit_log: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class OutcomeRecord:
    """Outcome record for post-trade analysis"""
    decision_id: str
    realized_pnl: float
    realized_slippage: float
    fill_behavior: str  # full, partial, none
    invalidation_hit: bool
    regime_realized_post_entry: Optional[MarketRegime] = None
    confidence_error: float = 0.0  # Difference between predicted and actual
    calibration_error: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FailurePattern:
    """Recurring failure class for memory"""
    id: str
    pattern_name: str
    description: str
    conditions: Dict[str, Any]  # Conditions under which this failure occurs
    examples: List[str]  # Decision IDs where this occurred
    frequency: int
    severity: float
    root_cause_hypothesis: str
    proposed_fix: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class OpportunityCost:
    """Opportunity cost metrics for a trade"""
    trade_id: str
    selected_trade_return: float
    best_alternative_return: float
    opportunity_cost: float  # positive = opportunity cost
    capital_efficiency_score: float  # 0-1
    alternatives_considered: int
    alternatives_available: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


class OpportunityCostEngine:
    """
    Opportunity Cost Engine
    
    Evaluates: "Is this the BEST use of capital right now?"
    
    System compares:
    - Current trade vs all possible trades
    - Capital allocation efficiency
    
    Output: capital_efficiency_score
    """
    
    def __init__(self, min_efficiency_threshold: float = 0.7):
        self.min_efficiency_threshold = min_efficiency_threshold
        self.trade_history: Dict[str, OpportunityCost] = {}
        self.efficiency_history: List[float] = []
        
    def evaluate_opportunity_cost(
        self,
        selected_trade: Dict[str, Any],
        alternative_trades: List[Dict[str, Any]],
        capital_available: float
    ) -> OpportunityCost:
        """
        Evaluate if current trade is the best use of capital.
        
        Args:
            selected_trade: The trade being evaluated
            alternative_trades: List of alternative trade opportunities
            capital_available: Total capital available
            
        Returns:
            OpportunityCost with efficiency metrics
        """
        trade_id = selected_trade.get('id', 'unknown')
        
        # Calculate expected return for selected trade
        selected_return = selected_trade.get('expected_return', 0)
        selected_risk = selected_trade.get('risk', 0.01)
        
        # Risk-adjusted expected return
        selected_sharpe = selected_return / selected_risk if selected_risk > 0 else 0
        
        # Evaluate alternatives
        alternative_returns = []
        for alt in alternative_trades:
            alt_return = alt.get('expected_return', 0)
            alt_risk = alt.get('risk', 0.01)
            alt_sharpe = alt_return / alt_risk if alt_risk > 0 else 0
            
            # Only consider alternatives with positive expected value
            if alt_sharpe > 0:
                alternative_returns.append({
                    'id': alt.get('id', 'unknown'),
                    'expected_return': alt_return,
                    'sharpe': alt_sharpe,
                    'capital_required': alt.get('capital_required', 0)
                })
        
        # Find best alternative
        best_alternative_return = 0
        if alternative_returns:
            best_alt = max(alternative_returns, key=lambda x: x['sharpe'])
            best_alternative_return = best_alt['expected_return']
        
        # Calculate opportunity cost
        opportunity_cost = max(0, best_alternative_return - selected_return)
        
        # Calculate capital efficiency score
        efficiency = self._calculate_efficiency_score(
            selected_sharpe, alternative_returns, capital_available
        )
        
        opportunity = OpportunityCost(
            trade_id=trade_id,
            selected_trade_return=selected_return,
            best_alternative_return=best_alternative_return,
            opportunity_cost=opportunity_cost,
            capital_efficiency_score=efficiency,
            alternatives_considered=len(alternative_returns),
            alternatives_available=len(alternative_trades),
            timestamp=datetime.utcnow()
        )
        
        self.trade_history[trade_id] = opportunity
        self.efficiency_history.append(efficiency)
        
        if efficiency < self.min_efficiency_threshold:
            logger.warning(f"Low capital efficiency ({efficiency:.2f}) for trade {trade_id}")
        
        return opportunity
    
    def _calculate_efficiency_score(
        self,
        selected_sharpe: float,
        alternatives: List[Dict],
        capital_available: float
    ) -> float:
        """Calculate capital efficiency score (0-1)."""
        if not alternatives:
            return 1.0 if selected_sharpe > 0 else 0.0
        
        # Get best alternative Sharpe ratio
        best_sharpe = max(a['sharpe'] for a in alternatives)
        
        if best_sharpe <= 0:
            return 1.0 if selected_sharpe > 0 else 0.0
        
        # Efficiency = selected / best
        efficiency = selected_sharpe / best_sharpe
        
        # Bonus for diversification
        num_viable_alternatives = len([a for a in alternatives if a['sharpe'] > 0.5])
        if num_viable_alternatives > 5:
            efficiency *= 0.95  # Slight penalty when many good options exist
        
        return min(1.0, max(0.0, efficiency))
    
    def should_take_trade(self, trade_id: str) -> Tuple[bool, str]:
        """Determine if trade meets opportunity cost threshold."""
        if trade_id not in self.trade_history:
            return True, "No opportunity cost data available"
        
        opp = self.trade_history[trade_id]
        
        if opp.capital_efficiency_score < self.min_efficiency_threshold:
            return False, f"Efficiency {opp.capital_efficiency_score:.2f} below threshold {self.min_efficiency_threshold}"
        
        if opp.opportunity_cost > opp.selected_trade_return * 0.5:
            return False, f"Opportunity cost ({opp.opportunity_cost:.2%}) too high relative to expected return"
        
        return True, "Trade meets efficiency criteria"
    
    def get_portfolio_efficiency_report(self) -> Dict[str, Any]:
        """Get overall portfolio capital efficiency report."""
        if not self.efficiency_history:
            return {'status': 'no_data'}
        
        recent_efficiency = self.efficiency_history[-100:]
        
        return {
            'avg_efficiency': sum(recent_efficiency) / len(recent_efficiency),
            'min_efficiency': min(recent_efficiency),
            'max_efficiency': max(recent_efficiency),
            'trades_below_threshold': sum(1 for e in recent_efficiency if e < self.min_efficiency_threshold),
            'total_trades_evaluated': len(self.trade_history),
            'current_threshold': self.min_efficiency_threshold
        }


@dataclass
class CapitalSurvivalMetrics:
    """Metrics for capital survival priority engine"""
    timestamp: datetime
    survival_score: float  # 0-1
    drawdown_state: str  # 'normal', 'elevated', 'critical'
    risk_adjustment_factor: float  # Multiplier for position sizes
    aggressiveness_level: str  # 'conservative', 'moderate', 'aggressive'
    daily_loss_used_pct: float  # Percentage of daily loss limit used
    margin_of_safety: float  # Distance to critical thresholds
    recommended_action: str


class CapitalSurvivalPriorityEngine:
    """
    Capital Survival Priority Engine
    
    System prioritizes: survival > profit
    
    Adjusts:
    - Aggressiveness based on drawdown state
    - Risk dynamically
    
    Final layer of protection before catastrophic loss.
    """
    
    def __init__(
        self,
        max_daily_loss_pct: float = 2.0,
        max_drawdown_pct: float = 10.0,
        critical_drawdown_pct: float = 15.0
    ):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.critical_drawdown_pct = critical_drawdown_pct
        
        self.current_balance: float = 0.0
        self.peak_balance: float = 0.0
        self.daily_start_balance: float = 0.0
        self.daily_loss_used: float = 0.0
        
        self.metrics_history: List[CapitalSurvivalMetrics] = []
        
    def update_capital_state(
        self,
        current_balance: float,
        open_positions_risk: float = 0.0
    ) -> CapitalSurvivalMetrics:
        """
        Update capital state and calculate survival metrics.
        
        Args:
            current_balance: Current account balance
            open_positions_risk: Total risk from open positions
            
        Returns:
            CapitalSurvivalMetrics with survival assessment
        """
        self.current_balance = current_balance
        
        # Update peak
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        # Initialize daily start if needed
        if self.daily_start_balance == 0:
            self.daily_start_balance = current_balance
        
        # Calculate drawdown
        drawdown_pct = 0.0
        if self.peak_balance > 0:
            drawdown_pct = (self.peak_balance - current_balance) / self.peak_balance * 100
        
        # Calculate daily loss
        daily_loss_pct = 0.0
        if self.daily_start_balance > 0:
            daily_loss_pct = (self.daily_start_balance - current_balance) / self.daily_start_balance * 100
            self.daily_loss_used = daily_loss_pct
        
        # Determine drawdown state
        drawdown_state = self._classify_drawdown_state(drawdown_pct)
        
        # Calculate survival score
        survival_score = self._calculate_survival_score(
            drawdown_pct, daily_loss_pct, open_positions_risk
        )
        
        # Calculate risk adjustment factor
        risk_factor = self._calculate_risk_factor(drawdown_state, survival_score)
        
        # Determine aggressiveness level
        aggressiveness = self._determine_aggressiveness(drawdown_state, survival_score)
        
        # Calculate margin of safety
        margin = self._calculate_margin_of_safety(drawdown_pct, daily_loss_pct)
        
        # Determine recommended action
        action = self._determine_action(drawdown_state, survival_score, margin)
        
        metrics = CapitalSurvivalMetrics(
            timestamp=datetime.utcnow(),
            survival_score=survival_score,
            drawdown_state=drawdown_state,
            risk_adjustment_factor=risk_factor,
            aggressiveness_level=aggressiveness,
            daily_loss_used_pct=(self.daily_loss_used / self.max_daily_loss_pct) * 100 if self.max_daily_loss_pct > 0 else 0,
            margin_of_safety=margin,
            recommended_action=action
        )
        
        self.metrics_history.append(metrics)
        
        # Log critical states
        if survival_score < 0.3:
            logger.critical(f"CRITICAL SURVIVAL SCORE: {survival_score:.2f} - IMMEDIATE ACTION REQUIRED")
        elif survival_score < 0.5:
            logger.warning(f"Low survival score: {survival_score:.2f} - Reduce risk exposure")
        
        return metrics
    
    def _classify_drawdown_state(self, drawdown_pct: float) -> str:
        """Classify current drawdown state."""
        if drawdown_pct >= self.critical_drawdown_pct:
            return 'critical'
        elif drawdown_pct >= self.max_drawdown_pct:
            return 'elevated'
        elif drawdown_pct >= self.max_drawdown_pct * 0.5:
            return 'warning'
        else:
            return 'normal'
    
    def _calculate_survival_score(
        self,
        drawdown_pct: float,
        daily_loss_pct: float,
        open_risk: float
    ) -> float:
        """Calculate survival score (0-1, higher = safer)."""
        score = 1.0
        
        # Penalize based on drawdown
        if drawdown_pct > 0:
            score -= (drawdown_pct / self.critical_drawdown_pct) * 0.4
        
        # Penalize based on daily loss usage
        if self.max_daily_loss_pct > 0:
            daily_loss_usage = daily_loss_pct / self.max_daily_loss_pct
            score -= daily_loss_usage * 0.3
        
        # Penalize based on open risk
        if self.current_balance > 0:
            open_risk_pct = open_risk / self.current_balance * 100
            score -= (open_risk_pct / 5.0) * 0.2  # 5% open risk = full penalty
        
        return max(0.0, min(1.0, score))
    
    def _calculate_risk_factor(self, drawdown_state: str, survival_score: float) -> float:
        """Calculate position size multiplier."""
        base_factors = {
            'normal': 1.0,
            'warning': 0.7,
            'elevated': 0.4,
            'critical': 0.1
        }
        
        base = base_factors.get(drawdown_state, 0.5)
        
        # Further adjust based on survival score
        if survival_score < 0.3:
            base *= 0.5
        elif survival_score > 0.8:
            base = min(1.0, base * 1.1)
        
        return base
    
    def _determine_aggressiveness(
        self,
        drawdown_state: str,
        survival_score: float
    ) -> str:
        """Determine appropriate aggressiveness level."""
        if drawdown_state == 'critical' or survival_score < 0.3:
            return 'conservative'
        elif drawdown_state == 'elevated' or survival_score < 0.5:
            return 'defensive'
        elif drawdown_state == 'warning' or survival_score < 0.7:
            return 'moderate'
        else:
            return 'aggressive'
    
    def _calculate_margin_of_safety(
        self,
        drawdown_pct: float,
        daily_loss_pct: float
    ) -> float:
        """Calculate margin of safety to critical thresholds."""
        dd_margin = (self.critical_drawdown_pct - drawdown_pct) / self.critical_drawdown_pct
        daily_margin = (self.max_daily_loss_pct - daily_loss_pct) / self.max_daily_loss_pct if self.max_daily_loss_pct > 0 else 1.0
        
        return min(dd_margin, daily_margin)
    
    def _determine_action(
        self,
        drawdown_state: str,
        survival_score: float,
        margin: float
    ) -> str:
        """Determine recommended action."""
        if drawdown_state == 'critical':
            return 'EMERGENCY_HALT'
        elif survival_score < 0.3:
            return 'CLOSE_ALL_POSITIONS'
        elif drawdown_state == 'elevated':
            return 'REDUCE_EXPOSURE_75'
        elif survival_score < 0.5:
            return 'REDUCE_EXPOSURE_50'
        elif margin < 0.2:
            return 'REDUCE_EXPOSURE_25'
        else:
            return 'NORMAL_OPERATIONS'
    
    def reset_daily_limits(self):
        """Reset daily loss tracking."""
        self.daily_start_balance = self.current_balance
        self.daily_loss_used = 0.0
        logger.info("Daily loss limits reset")
    
    def get_position_size_multiplier(self) -> float:
        """Get current position size multiplier based on survival state."""
        if not self.metrics_history:
            return 1.0
        return self.metrics_history[-1].risk_adjustment_factor
    
    def can_take_new_trade(self, trade_risk: float) -> Tuple[bool, str]:
        """Determine if new trade can be taken given current survival state."""
        if not self.metrics_history:
            return True, "No survival metrics available"
        
        latest = self.metrics_history[-1]
        
        if latest.survival_score < 0.2:
            return False, "CRITICAL: Survival score too low - no new trades"
        
        if latest.drawdown_state == 'critical':
            return False, "Critical drawdown state - trading halted"
        
        if latest.recommended_action == 'CLOSE_ALL_POSITIONS':
            return False, "Emergency closure in effect"
        
        # Check if trade would exceed risk limits
        if self.current_balance > 0:
            trade_risk_pct = trade_risk / self.current_balance * 100
            max_allowed_risk = self.max_daily_loss_pct - self.daily_loss_used
            
            if trade_risk_pct > max_allowed_risk:
                return False, f"Trade risk ({trade_risk_pct:.2f}%) exceeds remaining daily risk budget"
        
        return True, f"Trade approved - survival score: {latest.survival_score:.2f}"
    
    def get_survival_report(self) -> Dict[str, Any]:
        """Generate comprehensive survival report."""
        if not self.metrics_history:
            return {'status': 'no_data'}
        
        recent = self.metrics_history[-100:]
        
        return {
            'current_balance': self.current_balance,
            'peak_balance': self.peak_balance,
            'current_drawdown_pct': ((self.peak_balance - self.current_balance) / self.peak_balance * 100) if self.peak_balance > 0 else 0,
            'daily_loss_used_pct': (self.daily_loss_used / self.max_daily_loss_pct * 100) if self.max_daily_loss_pct > 0 else 0,
            'current_survival_score': recent[-1].survival_score if recent else 0,
            'current_drawdown_state': recent[-1].drawdown_state if recent else 'unknown',
            'current_risk_factor': recent[-1].risk_adjustment_factor if recent else 1.0,
            'avg_survival_score': sum(m.survival_score for m in recent) / len(recent) if recent else 0,
            'critical_periods': sum(1 for m in recent if m.survival_score < 0.3),
            'recommended_action': recent[-1].recommended_action if recent else 'unknown',
            'can_trade': self.can_take_new_trade(0)[0]
        }


@dataclass
class CapabilityHypothesis:
    """Hypothesis for new capability to address a gap"""
    id: str
    gap_description: str
    capability_type: str  # model, feature, strategy, reasoning_pathway
    implementation_sketch: str
    expected_improvement: float
    tested: bool = False
    test_results: Optional[Dict] = None
    promoted: bool = False
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


class DGSException(Exception):
    """Base exception for DGS"""
    pass


class ValidationError(DGSException):
    """Validation failed"""
    pass


class GovernanceRejection(DGSException):
    """Decision rejected by governance"""
    pass
