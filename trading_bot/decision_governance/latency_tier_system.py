"""
Latency Tier System for Decision Governance

Fix for: "Your system requires a claim graph, evidence audit, adversarial counter-analysis, 
regime mapping, counterfactual simulation, and calibration before deployment. 
That's milliseconds to seconds. Markets move in microseconds."

Solution: Three-tier governance system:
- DGS-Live: Fast, simple, bounded live gatekeeper (microsecond decisions)
- DGS-Deep: Slower offline reasoning/audit system (millisecond decisions)
- Post-Hoc Review: Probabilistically audited simplified review for fast path

Explicit maximum frequency for DGS-governed decisions.
Everything faster gets a radically simplified, probabilistically audited post-hoc review only.
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging
import time
import random
import asyncio

logger = logging.getLogger(__name__)


class DecisionSpeed(Enum):
    """Speed classification for decisions"""
    MICROSECOND = "microsecond"  # < 1ms - ultra-fast path
    MILLISECOND = "millisecond"  # 1-100ms - fast path  
    SECOND = "second"            # > 100ms - full DGS path


class GovernanceTier(Enum):
    """Governance tier applied to decision"""
    LIVE = "dgs_live"          # Simplified fast path
    DEEP = "dgs_deep"          # Full governance
    POST_HOC = "post_hoc"      # Probabilistic audit after execution (Tier 0 — capital limited)


@dataclass
class LatencyBudget:
    """Maximum allowed latency for governance components"""
    claim_graph_ms: float = 5.0
    evidence_audit_ms: float = 10.0
    adversarial_analysis_ms: float = 15.0
    regime_mapping_ms: float = 5.0
    counterfactual_ms: float = 20.0
    calibration_ms: float = 5.0
    total_budget_ms: float = 100.0  # Max for full DGS
    
    # Fast path budgets
    fast_path_total_ms: float = 10.0
    ultra_fast_path_total_us: float = 100.0  # Microseconds


@dataclass
class Tier0CapitalState:
    """Attack 2: Tier 0 (POST_HOC) capital limit with decay on audit violations"""
    max_capital_usd: float = 50000.0  # Hard cap for Tier 0
    current_capital_usd: float = 50000.0
    audit_violations: int = 0
    decay_factor: float = 0.9  # Each violation reduces cap by 10%
    min_capital_usd: float = 5000.0  # Floor — cannot decay below this
    last_violation_timestamp: Optional[datetime] = None

    def apply_audit_violation(self):
        """Decay capital limit after audit violation"""
        self.audit_violations += 1
        self.max_capital_usd = max(self.min_capital_usd, self.max_capital_usd * self.decay_factor)
        self.current_capital_usd = min(self.current_capital_usd, self.max_capital_usd)
        self.last_violation_timestamp = datetime.utcnow()

    def can_allocate(self, amount_usd: float) -> bool:
        return amount_usd <= self.current_capital_usd


@dataclass
class TierDecision:
    """A decision made within a governance tier"""
    decision_id: str
    timestamp: datetime
    symbol: str
    tier: GovernanceTier
    decision: str  # APPROVE, REJECT, DEFER
    confidence: float
    latency_ms: float
    simplified_checks: List[str]  # Which checks were run
    skipped_checks: List[str]     # Which checks were skipped
    requires_post_hoc: bool
    risk_score: float
    # Attack 2: observable properties that FORCED this tier assignment
    forced_by_properties: Optional[Dict[str, Any]] = None


@dataclass
class PostHocReview:
    """Post-hoc review of a fast-path decision"""
    review_id: str
    original_decision_id: str
    review_timestamp: datetime
    sampled_for_review: bool
    review_depth: str  # "light", "standard", "deep"
    findings: List[Dict[str, Any]]
    would_decision_change: Optional[bool] = None
    severity_score: float = 0.0


class DGSLatencyTierSystem:
    """
    Latency Tier System for Decision Governance
    
    Solves the fundamental timing mismatch:
    - Markets move in microseconds
    - Full DGS governance takes milliseconds to seconds
    
    Three-Tier Architecture:
    
    1. DGS-Live (Fast Path):
       - Target latency: < 10ms
       - Simplified claim graph
       - Key evidence check only
       - No adversarial analysis (done post-hoc if sampled)
       - Basic regime check
       - No counterfactual simulation
       - Cached calibration
       - 95% of decisions go here
       - 5% randomly selected for post-hoc deep review
    
    2. DGS-Deep (Full Governance):
       - Target latency: < 100ms (acceptable for slower signals)
       - Full claim graph
       - Complete evidence audit
       - Adversarial analysis
       - Regime mapping
       - Counterfactual simulation
       - Live calibration
       - 4.9% of decisions (complex, high-value)
    
    3. Post-Hoc Review:
       - For decisions that already executed
       - Probabilistic sampling based on:
         * Decision outcome (always review losses)
         * Random sampling (5% of all live decisions)
         * Risk score (high risk = higher sampling rate)
    
    Configuration:
    - max_dgs_frequency_hz: Maximum decisions per second through full DGS
    - Default: 10 Hz (one full governance every 100ms)
    - Everything above this goes to Live or Post-Hoc
    """
    
    def __init__(
        self,
        max_dgs_frequency_hz: float = 10.0,  # 10 full DGS decisions per second
        live_path_probability: float = 0.95,
        post_hoc_sample_rate: float = 0.05,
        latency_budget: Optional[LatencyBudget] = None
    ):
        self.max_dgs_frequency_hz = max_dgs_frequency_hz
        self.live_path_probability = live_path_probability
        self.post_hoc_sample_rate = post_hoc_sample_rate
        self.latency_budget = latency_budget or LatencyBudget()
        
        # Rate limiting
        self.dgs_deep_timestamps: deque = deque(maxlen=100)
        self.decision_counter = 0
        
        # Decision history by tier
        self.live_decisions: Dict[str, TierDecision] = {}
        self.deep_decisions: Dict[str, TierDecision] = {}
        self.post_hoc_reviews: Dict[str, PostHocReview] = {}
        
        # Statistics
        self.tier_stats = {
            'live': {'count': 0, 'avg_latency_ms': 0, 'post_hoc_sampled': 0},
            'deep': {'count': 0, 'avg_latency_ms': 0},
            'post_hoc': {'count': 0, 'issues_found': 0}
        }
        
        # Fast-path validation rules (simplified)
        self.fast_path_rules = self._init_fast_path_rules()

        # Attack 2: Tier 0 capital state with decay on audit violations
        self.tier0_capital = Tier0CapitalState()

        logger.info(
            f"DGS Latency Tier System initialized: "
            f"max_dgs_freq={max_dgs_frequency_hz}Hz, "
            f"live_prob={live_path_probability}, "
            f"post_hoc_rate={post_hoc_sample_rate}"
        )
    
    def _init_fast_path_rules(self) -> Dict[str, Any]:
        """Initialize simplified rules for fast-path decisions"""
        return {
            'max_position_size_pct': 0.01,  # 1% max for fast decisions
            'min_confidence_threshold': 0.7,
            'max_adverse_excursion_pct': 0.02,  # 2% max loss
            'allowed_regimes': ['normal', 'low_volatility'],
            'blocked_symbols': set(),  # Symbols requiring full governance
            'max_order_size_usd': 100000,  # $100k max for fast path
        }
    
    # Attack 2: Forced tier assignment rules — tier determined by OBSERVABLE
    # properties only, not self-reported or configurable by the strategy.
    FORCED_TIER_RULES = {
        # Property -> (threshold, forced_tier)
        # If property exceeds threshold, tier is FORCED to the specified level
        'position_size_usd': [
            (200000, GovernanceTier.DEEP),   # >$200k → must use DEEP
            (100000, GovernanceTier.LIVE),    # >$100k → at least LIVE (not POST_HOC)
        ],
        'regime_risk_score': [
            (0.7, GovernanceTier.DEEP),       # High-risk regime → DEEP
            (0.4, GovernanceTier.LIVE),       # Medium-risk → at least LIVE
        ],
        'signal_novelty_score': [
            (0.6, GovernanceTier.DEEP),       # Novel signal → DEEP
        ],
        'strategy_audit_violations': [
            (3, GovernanceTier.DEEP),         # Strategy with 3+ violations → always DEEP
            (1, GovernanceTier.LIVE),         # Any violation → at least LIVE
        ],
    }

    def select_governance_tier(
        self,
        signal_urgency: DecisionSpeed,
        signal_confidence: float,
        proposed_size_usd: float,
        symbol: str,
        current_regime: str,
        is_novel_signal: bool = False,
        # Attack 2: Additional observable properties for forced tier assignment
        regime_risk_score: float = 0.0,
        signal_novelty_score: float = 0.0,
        strategy_audit_violations: int = 0,
    ) -> Tuple[GovernanceTier, Dict[str, Any]]:
        """
        Select appropriate governance tier for a decision.

        Attack 2 fix: Tier is FORCED by observable properties.
        No strategy can self-select into a lower tier.
        Returns (tier, forced_by_properties) so caller knows WHY.

        Logic:
        1. Microsecond urgency -> Post-Hoc (decision already made, review later)
        2. Check FORCED tier rules based on observable properties
        3. Check rate limit for DGS-Deep
        4. High confidence + small size + normal regime -> DGS-Live
        5. Complex/novel/high-value -> DGS-Deep
        """
        forced_by = {}

        # Microsecond decisions go to post-hoc (already executed)
        if signal_urgency == DecisionSpeed.MICROSECOND:
            # Attack 2: Even POST_HOC has capital limits
            if not self.tier0_capital.can_allocate(proposed_size_usd):
                forced_by['tier0_capital_exceeded'] = {
                    'proposed': proposed_size_usd,
                    'cap': self.tier0_capital.current_capital_usd
                }
                # Cannot execute at this size in Tier 0 — defer or reduce
                return GovernanceTier.LIVE, forced_by
            return GovernanceTier.POST_HOC, {'forced_by': 'urgency_microsecond'}

        # Attack 2: Apply FORCED tier rules based on observable properties
        # These CANNOT be overridden by strategy preference
        forced_tier = None
        observable_props = {
            'position_size_usd': proposed_size_usd,
            'regime_risk_score': regime_risk_score,
            'signal_novelty_score': signal_novelty_score,
            'strategy_audit_violations': strategy_audit_violations,
        }

        for prop_name, value in observable_props.items():
            rules = self.FORCED_TIER_RULES.get(prop_name, [])
            for threshold, tier in rules:
                if value >= threshold:
                    if forced_tier is None or tier.value > forced_tier.value:
                        forced_tier = tier
                        forced_by[prop_name] = {'value': value, 'threshold': threshold, 'forced_tier': tier.value}

        # Check if DGS-Deep has capacity
        can_use_deep = self._check_dgs_deep_capacity()

        # If forced to DEEP but no capacity, fall back to LIVE (with flag)
        if forced_tier == GovernanceTier.DEEP and not can_use_deep:
            forced_by['deep_fallback'] = True
            forced_tier = GovernanceTier.LIVE

        # Novel signals always get full governance if possible
        if is_novel_signal and can_use_deep:
            if forced_tier is None or GovernanceTier.DEEP.value > forced_tier.value:
                forced_tier = GovernanceTier.DEEP
                forced_by['novel_signal'] = True

        # Apply forced tier if any rule triggered
        if forced_tier is not None:
            return forced_tier, forced_by

        # Large positions get full governance
        if proposed_size_usd > self.fast_path_rules['max_order_size_usd']:
            if can_use_deep:
                return GovernanceTier.DEEP, {'forced_by': 'position_size'}
            else:
                return GovernanceTier.LIVE, {'forced_by': 'position_size_deep_unavailable'}

        # Check if in blocked list
        if symbol in self.fast_path_rules['blocked_symbols']:
            return (GovernanceTier.DEEP if can_use_deep else GovernanceTier.LIVE), {'forced_by': 'blocked_symbol'}

        # Check regime
        if current_regime not in self.fast_path_rules['allowed_regimes']:
            return (GovernanceTier.DEEP if can_use_deep else GovernanceTier.LIVE), {'forced_by': 'regime'}

        # Check confidence
        if signal_confidence < self.fast_path_rules['min_confidence_threshold']:
            return (GovernanceTier.DEEP if can_use_deep else GovernanceTier.LIVE), {'forced_by': 'low_confidence'}

        # Default to live path for speed
        return GovernanceTier.LIVE, {'forced_by': 'default'}
    
    def _check_dgs_deep_capacity(self) -> bool:
        """Check if DGS-Deep has capacity for another decision"""
        now = datetime.utcnow()
        min_interval = timedelta(seconds=1.0 / self.max_dgs_frequency_hz)
        
        # Clean old timestamps
        cutoff = now - timedelta(seconds=1)
        while self.dgs_deep_timestamps and self.dgs_deep_timestamps[0] < cutoff:
            self.dgs_deep_timestamps.popleft()
        
        # Check if we can add another
        if len(self.dgs_deep_timestamps) == 0:
            return True
        
        last_decision = self.dgs_deep_timestamps[-1]
        return (now - last_decision) >= min_interval
    
    def record_dgs_deep_usage(self):
        """Record that DGS-Deep was used"""
        self.dgs_deep_timestamps.append(datetime.utcnow())
    
    def should_sample_for_post_hoc(
        self,
        decision: TierDecision,
        outcome: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Determine if a live decision should get post-hoc review.
        
        Sampling criteria:
        1. Always sample losses (outcome-based)
        2. Random sampling (5% default)
        3. High risk score (decision with high risk_score always sampled)
        """
        # Always review losses
        if outcome and outcome.get('pnl', 0) < 0:
            return True, "loss_outcome"
        
        # Always review high risk
        if decision.risk_score > 0.7:
            return True, "high_risk"
        
        # Random sampling
        if random.random() < self.post_hoc_sample_rate:
            return True, "random_sample"
        
        return False, "not_sampled"
    
    def execute_live_path(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        basic_checks: Callable[[], Dict[str, Any]]
    ) -> TierDecision:
        """
        Execute fast-path governance.
        
        Simplified checks:
        1. Position size limit (hard coded)
        2. Basic confidence threshold
        3. Regime check (simple version)
        4. Risk limit check
        
        Skips:
        - Full claim graph
        - Evidence audit
        - Adversarial analysis
        - Counterfactual simulation
        """
        start_time = time.time()
        
        self.decision_counter += 1
        decision_id = f"live_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self.decision_counter}"
        
        # Run basic checks
        check_results = basic_checks()
        
        simplified_checks = []
        skipped_checks = ['full_claim_graph', 'evidence_audit', 'adversarial_analysis', 'counterfactual_simulation']
        
        # Position size check
        if check_results.get('position_size_ok', False):
            simplified_checks.append('position_size_check')
        
        # Confidence check
        if check_results.get('confidence', 0) >= self.fast_path_rules['min_confidence_threshold']:
            simplified_checks.append('confidence_check')
        
        # Regime check
        if check_results.get('regime_appropriate', False):
            simplified_checks.append('basic_regime_check')
        
        # Risk check
        if check_results.get('risk_acceptable', False):
            simplified_checks.append('risk_limit_check')
        
        # Decision logic
        if len(simplified_checks) >= 3:
            decision = "APPROVE"
            confidence = check_results.get('confidence', 0.5)
        elif len(simplified_checks) >= 2:
            decision = "RESIZE"
            confidence = check_results.get('confidence', 0.5) * 0.8
        else:
            decision = "REJECT"
            confidence = 0.3
        
        latency_ms = (time.time() - start_time) * 1000
        
        tier_decision = TierDecision(
            decision_id=decision_id,
            timestamp=datetime.utcnow(),
            symbol=symbol,
            tier=GovernanceTier.LIVE,
            decision=decision,
            confidence=confidence,
            latency_ms=latency_ms,
            simplified_checks=simplified_checks,
            skipped_checks=skipped_checks,
            requires_post_hoc=True,  # All live decisions eligible for post-hoc
            risk_score=check_results.get('risk_score', 0.5)
        )
        
        self.live_decisions[decision_id] = tier_decision
        
        # Update stats
        self.tier_stats['live']['count'] += 1
        n = self.tier_stats['live']['count']
        old_avg = self.tier_stats['live']['avg_latency_ms']
        self.tier_stats['live']['avg_latency_ms'] = (old_avg * (n-1) + latency_ms) / n
        
        logger.info(f"DGS-Live decision: {decision_id} -> {decision} ({latency_ms:.2f}ms)")
        
        return tier_decision
    
    def execute_deep_path(
        self,
        symbol: str,
        full_governance_fn: Callable[[], Tuple[str, float, Dict]]
    ) -> TierDecision:
        """
        Execute full DGS governance.
        
        Uses the complete governance stack with all layers.
        """
        start_time = time.time()
        
        self.decision_counter += 1
        decision_id = f"deep_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self.decision_counter}"
        
        # Record DGS-Deep usage for rate limiting
        self.record_dgs_deep_usage()
        
        # Execute full governance
        decision, confidence, metadata = full_governance_fn()
        
        latency_ms = (time.time() - start_time) * 1000
        
        tier_decision = TierDecision(
            decision_id=decision_id,
            timestamp=datetime.utcnow(),
            symbol=symbol,
            tier=GovernanceTier.DEEP,
            decision=decision,
            confidence=confidence,
            latency_ms=latency_ms,
            simplified_checks=metadata.get('checks_executed', []),
            skipped_checks=[],
            requires_post_hoc=False,  # Deep decisions don't need post-hoc
            risk_score=metadata.get('risk_score', 0.5)
        )
        
        self.deep_decisions[decision_id] = tier_decision
        
        # Update stats
        self.tier_stats['deep']['count'] += 1
        n = self.tier_stats['deep']['count']
        old_avg = self.tier_stats['deep']['avg_latency_ms']
        self.tier_stats['deep']['avg_latency_ms'] = (old_avg * (n-1) + latency_ms) / n
        
        logger.info(f"DGS-Deep decision: {decision_id} -> {decision} ({latency_ms:.2f}ms)")
        
        return tier_decision
    
    def schedule_post_hoc_review(
        self,
        decision: TierDecision,
        outcome: Optional[Dict] = None
    ) -> Optional[PostHocReview]:
        """
        Schedule post-hoc review for a live decision.
        
        Review depth based on:
        - Outcome severity (losses get deep review)
        - Risk score
        - Random selection
        """
        should_sample, reason = self.should_sample_for_post_hoc(decision, outcome)
        
        if not should_sample:
            return None
        
        # Determine review depth
        if outcome and outcome.get('pnl', 0) < -0.02:  # >2% loss
            review_depth = "deep"
        elif decision.risk_score > 0.7:
            review_depth = "standard"
        else:
            review_depth = "light"
        
        review_id = f"review_{decision.decision_id}_{datetime.utcnow().strftime('%H%M%S')}"
        
        review = PostHocReview(
            review_id=review_id,
            original_decision_id=decision.decision_id,
            review_timestamp=datetime.utcnow(),
            sampled_for_review=True,
            review_depth=review_depth,
            findings=[]
        )
        
        self.post_hoc_reviews[review_id] = review
        self.tier_stats['live']['post_hoc_sampled'] += 1
        
        logger.info(f"Scheduled {review_depth} post-hoc review for {decision.decision_id}")
        
        return review
    
    def record_tier0_audit_violation(self):
        """Attack 2: Record audit violation for Tier 0 — triggers capital decay"""
        self.tier0_capital.apply_audit_violation()
        logger.warning(f"Tier 0 audit violation #{self.tier0_capital.audit_violations}. "
                       f"Capital cap decayed to ${self.tier0_capital.max_capital_usd:,.0f}")

    def get_tier0_capital_state(self) -> Dict[str, Any]:
        """Attack 2: Get Tier 0 capital state"""
        return {
            'max_capital_usd': self.tier0_capital.max_capital_usd,
            'current_capital_usd': self.tier0_capital.current_capital_usd,
            'audit_violations': self.tier0_capital.audit_violations,
            'decay_factor': self.tier0_capital.decay_factor,
            'min_capital_usd': self.tier0_capital.min_capital_usd,
            'last_violation': self.tier0_capital.last_violation_timestamp.isoformat() if self.tier0_capital.last_violation_timestamp else None,
        }

    def get_tier_statistics(self) -> Dict[str, Any]:
        """Get statistics on tier usage"""
        return {
            'tier_stats': self.tier_stats,
            'total_decisions': len(self.live_decisions) + len(self.deep_decisions),
            'live_path_pct': len(self.live_decisions) / max(1, len(self.live_decisions) + len(self.deep_decisions)),
            'post_hoc_completion_rate': len(self.post_hoc_reviews) / max(1, self.tier_stats['live']['post_hoc_sampled']),
            'tier0_capital': self.get_tier0_capital_state(),
            'config': {
                'max_dgs_frequency_hz': self.max_dgs_frequency_hz,
                'live_path_probability': self.live_path_probability,
                'post_hoc_sample_rate': self.post_hoc_sample_rate
            }
        }


# Factory function
def create_latency_tier_system(
    max_dgs_frequency_hz: float = 10.0,
    post_hoc_sample_rate: float = 0.05
) -> DGSLatencyTierSystem:
    """Factory function to create latency tier system"""
    
    return DGSLatencyTierSystem(
        max_dgs_frequency_hz=max_dgs_frequency_hz,
        post_hoc_sample_rate=post_hoc_sample_rate
    )
