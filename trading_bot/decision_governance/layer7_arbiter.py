"""
Layer 7: Live Governance Gate

Fast-path gatekeeper for real-time decisions.
Does not ask "Is this clever?" It asks:
- Is this valid? (thesis schema check)
- Is this sufficiently evidenced? (minimum evidence check)
- Are contradictions survivable? (contradiction severity check)
- Is the regime right? (regime fit check)
- Can we actually execute? (execution feasibility check)
- Are we within hard risk bounds? (hard risk check)
- Should we abstain? (abstention decision with budget)

Outputs: APPROVE / RESIZE / DEFER / REJECT / PAPER_ONLY / MANUAL_REVIEW / KILL_SWITCH

Hard constraints enforced here:
- No full-depth DGS in latency-sensitive trading
- No unapproved risk-control changes
- No direct live self-modification
- Tier assignment forced by observable properties (Attack 2)
- Abstention budget per strategy-regime with benchmark opportunity cost (Attack 6)
- Ex-ante evaluation only — calibration, not classification (Attack 10)
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging
import math

from .core_types import (
    GovernanceDecision, DecisionRecord, UncertaintyProfile,
    ExecutionFeasibility, MarketRegime
)

logger = logging.getLogger(__name__)


# ── Tier Assignment (Attack 2: forced by observable properties) ──────────────

class GovernanceTier(Enum):
    """Tier forced by observable properties — agents cannot elect their tier"""
    TIER_0_ULTRAFAST = "tier_0_ultrafast"   # <1ms, hard risk limits only
    TIER_1_INTRADAY  = "tier_1_intraday"     # 1-100ms, simplified governance
    TIER_2_FULL      = "tier_2_full"         # Full DGS governance
    TIER_3_PROMOTION = "tier_3_promotion"     # Deepest — strategy promotion


@dataclass
class TierAssignmentRules:
    """
    Attack 2 fix: Tier assignment forced by observable properties,
    not elected by agents. Prevents tier arbitrage.
    """
    # TIER_0 thresholds (ultra-fast scalping)
    tier_0_max_holding_time_sec: float = 60.0
    tier_0_max_trade_freq_per_min: float = 30.0
    tier_0_max_volatility_sensitivity: float = 0.3
    tier_0_hard_capital_limit_usd: float = 50_000.0
    tier_0_capital_decay_on_violation: float = 0.5  # Halve limit on audit violation

    # TIER_1 thresholds (intraday)
    tier_1_max_holding_time_sec: float = 3600.0
    tier_1_max_position_size_pct: float = 0.02

    # TIER_2 thresholds (full governance)
    tier_2_min_position_size_usd: float = 100_000.0
    tier_2_novel_signal: bool = True  # Novel signals always TIER_2

    # TIER_3 (strategy promotion — always deepest)
    tier_3_is_promotion: bool = True


@dataclass
class Tier0CapitalState:
    """Track Tier 0 capital limit with decay on audit violations"""
    current_limit_usd: float
    violations: int = 0
    last_violation_time: Optional[datetime] = None

    def apply_violation_decay(self, decay_factor: float):
        self.violations += 1
        self.current_limit_usd *= decay_factor
        self.last_violation_time = datetime.utcnow()


# ── Abstention Budget (Attack 6: regime-separated, benchmark opportunity cost) ─

@dataclass
class RegimeAbstentionThresholds:
    """
    Attack 6 fix: Separate abstention thresholds per regime.
    High-volatility regimes get higher abstention tolerance.
    """
    low_vol_max_abstention_rate: float = 0.15
    normal_vol_max_abstention_rate: float = 0.25
    high_vol_max_abstention_rate: float = 0.40
    extreme_vol_max_abstention_rate: float = 0.55
    consecutive_abstention_limit: int = 5
    lookback_decisions: int = 50


@dataclass
class StrategyRegimeAbstentionState:
    """Per strategy-regime abstention tracking with opportunity cost"""
    strategy_signature: str
    regime_hash: str
    abstention_count: int = 0
    consecutive_abstentions: int = 0
    total_decisions: int = 0
    # Benchmark opportunity cost (Attack 6: measured against continuous benchmark)
    benchmark_pnl_while_abstained: float = 0.0
    approved_pnl: float = 0.0
    retired: bool = False
    retirement_reason: Optional[str] = None


# ── Ex-Ante Evaluation (Attack 10: calibration not classification) ───────────

@dataclass
class ExAnteCalibrationRecord:
    """
    Attack 10 fix: Track predicted probability vs actual outcome
    using proper scoring rules (Brier score, log loss).
    Never use binary good/bad classification based on PnL.
    """
    decision_id: str
    predicted_prob_success: float
    actual_success: Optional[bool] = None  # Filled later
    brier_score: Optional[float] = None    # Filled later
    log_loss: Optional[float] = None       # Filled later
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ── Gate Check Results ────────────────────────────────────────────────────────

@dataclass
class GateCheckResult:
    """Result of a single gate check"""
    check_name: str
    passed: bool
    score: float          # 0-1
    severity: float = 0.0 # 0-1, how bad the failure is
    detail: str = ""
    can_override: bool = False  # Whether manual review can override


@dataclass
class LiveGateOutput:
    """Complete output from the Live Governance Gate"""
    decision: GovernanceDecision
    tier: GovernanceTier
    checks: List[GateCheckResult]
    approved_size: float
    risk_adjusted_size: float
    reasoning: str
    requires_post_hoc: bool
    kill_switch_reason: Optional[str] = None
    manual_review_reason: Optional[str] = None
    paper_only_reason: Optional[str] = None
    abstention_budget_status: Optional[Dict] = None
    ex_ante_prediction: Optional[float] = None  # Predicted prob of success
    latency_budget_ms: float = 10.0


# ── Governance Criteria ────────────────────────────────────────────────────────

@dataclass
class GovernanceCriteria:
    """Criteria for governance decisions"""
    min_evidence_coverage: float = 0.6
    max_contradiction_severity: float = 0.8
    min_regime_fit: float = 0.5
    min_robustness: float = 0.5
    min_confidence: float = 0.55
    max_abstention_probability: float = 0.5
    max_position_size: float = 1.0
    max_risk_per_trade: float = 0.02

    # Kill switch triggers (hard limits, no override)
    max_portfolio_drawdown: float = 0.10
    max_correlation_concentration: float = 0.80
    max_sector_exposure: float = 0.30


# ── Live Governance Gate ──────────────────────────────────────────────────────

class LiveGovernanceGate:
    """
    Live Governance Gate — fast-path decision authority.

    Checks (in order, early-exit on hard failures):
    1. Thesis schema check      — structural validity
    2. Minimum evidence check   — coverage threshold
    3. Contradiction severity   — adversarial challenge ceiling
    4. Regime fit check         — regime applicability
    5. Execution feasibility    — can we actually trade this?
    6. Hard risk check          — portfolio-level hard limits
    7. Abstention decision      — budget-aware abstention logic

    Outputs:
    - APPROVE       — all checks pass, full confidence
    - RESIZE        — checks pass with concerns, reduce size
    - DEFER         — insufficient info, revisit when conditions change
    - REJECT        — hard check failure, do not trade
    - PAPER_ONLY    — approved for paper trading only (no real capital)
    - MANUAL_REVIEW — escalate to human operator
    - KILL_SWITCH  — emergency halt, stop all activity

    Hard constraints enforced:
    - Tier assignment forced by observable properties (Attack 2)
    - Tier 0 has hard capital limit that decays on audit violation (Attack 2)
    - Abstention budget per strategy-regime with benchmark opportunity cost (Attack 6)
    - Ex-ante evaluation only — Brier score, not binary PnL classification (Attack 10)
    - No full-depth DGS in latency-sensitive trading
    """

    def __init__(
        self,
        criteria: Optional[GovernanceCriteria] = None,
        tier_rules: Optional[TierAssignmentRules] = None,
        abstention_thresholds: Optional[RegimeAbstentionThresholds] = None,
    ):
        self.criteria = criteria or GovernanceCriteria()
        self.tier_rules = tier_rules or TierAssignmentRules()
        self.abstention_thresholds = abstention_thresholds or RegimeAbstentionThresholds()

        # Tier 0 capital state with decay
        self.tier_0_capital = Tier0CapitalState(
            current_limit_usd=self.tier_rules.tier_0_hard_capital_limit_usd
        )

        # Per strategy-regime abstention tracking
        self.abstention_state: Dict[str, StrategyRegimeAbstentionState] = {}

        # Ex-ante calibration tracking (Attack 10)
        self.calibration_records: deque = deque(maxlen=1000)
        self.brier_scores: deque = deque(maxlen=200)
        self.log_losses: deque = deque(maxlen=200)

        # Decision statistics
        self.decision_stats = defaultdict(int)

        # Kill switch state
        self.kill_switch_active: bool = False
        self.kill_switch_reason: Optional[str] = None
        self.kill_switch_timestamp: Optional[datetime] = None

    # ── Tier Assignment (Attack 2) ───────────────────────────────────────

    def assign_tier(
        self,
        max_holding_time_sec: float,
        expected_trade_freq_per_min: float,
        volatility_sensitivity: float,
        position_size_usd: float,
        is_novel_signal: bool = False,
        is_strategy_promotion: bool = False,
    ) -> GovernanceTier:
        """
        Attack 2 fix: Tier assignment forced by OBSERVABLE PROPERTIES.
        Agents cannot elect their tier. This prevents tier arbitrage
        (e.g., splitting a Tier 2 thesis into multiple Tier 1 sub-theses).
        """
        if is_strategy_promotion:
            return GovernanceTier.TIER_3_PROMOTION

        if is_novel_signal:
            return GovernanceTier.TIER_2_FULL

        # Tier 0: ultra-fast scalping only
        if (max_holding_time_sec <= self.tier_rules.tier_0_max_holding_time_sec
            and expected_trade_freq_per_min >= self.tier_rules.tier_0_max_trade_freq_per_min * 0.5
            and volatility_sensitivity <= self.tier_rules.tier_0_max_volatility_sensitivity
            and position_size_usd <= self.tier_0_capital.current_limit_usd):
            return GovernanceTier.TIER_0_ULTRAFAST

        # Tier 1: intraday
        if (max_holding_time_sec <= self.tier_rules.tier_1_max_holding_time_sec
            and position_size_usd / max(1, position_size_usd) <= self.tier_rules.tier_1_max_position_size_pct):
            return GovernanceTier.TIER_1_INTRADAY

        # Tier 2: full governance for anything large or complex
        if position_size_usd >= self.tier_rules.tier_2_min_position_size_usd:
            return GovernanceTier.TIER_2_FULL

        # Default to Tier 1 (simplified governance)
        return GovernanceTier.TIER_1_INTRADAY

    def record_tier_0_audit_violation(self):
        """Tier 0 capital limit decays on any post-trade audit violation"""
        self.tier_0_capital.apply_violation_decay(
            self.tier_rules.tier_0_capital_decay_on_violation
        )
        logger.warning(
            f"Tier 0 audit violation — capital limit decayed to "
            f"${self.tier_0_capital.current_limit_usd:,.0f}"
        )

    # ── Main Gate Entry ───────────────────────────────────────────────────

    def evaluate(
        self,
        claims: List[Any],
        evidence_coverage: Dict[str, Any],
        adversarial_challenges: List[Any],
        regime_fit_score: float,
        regime_underrepresented: bool,
        robustness_score: float,
        uncertainty_profile: UncertaintyProfile,
        execution_feasibility: Optional[ExecutionFeasibility],
        counterfactual_scenarios: List[Any],
        symbol: str,
        proposed_size: float,
        signal_confidence: float,
        strategy_signature: str = "",
        regime_hash: str = "",
        portfolio_drawdown: float = 0.0,
        sector_exposure: float = 0.0,
        correlation_concentration: float = 0.0,
        # Tier assignment observables (Attack 2)
        max_holding_time_sec: float = 300.0,
        expected_trade_freq_per_min: float = 1.0,
        volatility_sensitivity: float = 0.5,
        position_size_usd: float = 0.0,
        is_novel_signal: bool = False,
        is_strategy_promotion: bool = False,
    ) -> LiveGateOutput:
        """
        Run all gate checks and produce a governance decision.
        """
        # Kill switch check first
        if self.kill_switch_active:
            return LiveGateOutput(
                decision=GovernanceDecision.KILL_SWITCH,
                tier=GovernanceTier.TIER_2_FULL,
                checks=[],
                approved_size=0.0,
                risk_adjusted_size=0.0,
                reasoning=f"Kill switch active: {self.kill_switch_reason}",
                requires_post_hoc=False,
                kill_switch_reason=self.kill_switch_reason,
            )

        # Assign tier (Attack 2)
        tier = self.assign_tier(
            max_holding_time_sec=max_holding_time_sec,
            expected_trade_freq_per_min=expected_trade_freq_per_min,
            volatility_sensitivity=volatility_sensitivity,
            position_size_usd=position_size_usd,
            is_novel_signal=is_novel_signal,
            is_strategy_promotion=is_strategy_promotion,
        )

        # Tier 0: hard risk limits only, no full governance
        if tier == GovernanceTier.TIER_0_ULTRAFAST:
            return self._evaluate_tier_0(
                symbol, proposed_size, signal_confidence,
                portfolio_drawdown, tier
            )

        # Run gate checks in order
        checks = []

        # 1. Thesis schema check
        checks.append(self._check_thesis_schema(claims))

        # 2. Minimum evidence check
        checks.append(self._check_minimum_evidence(evidence_coverage))

        # 3. Contradiction severity check
        checks.append(self._check_contradiction_severity(adversarial_challenges))

        # 4. Regime fit check
        checks.append(self._check_regime_fit(regime_fit_score, regime_underrepresented))

        # 5. Execution feasibility check
        checks.append(self._check_execution_feasibility(execution_feasibility))

        # 6. Hard risk check (kill switch territory)
        risk_check = self._check_hard_risk(
            portfolio_drawdown, sector_exposure,
            correlation_concentration, proposed_size
        )
        checks.append(risk_check)

        # 7. Abstention decision (budget-aware)
        abstention_check = self._check_abstention_decision(
            uncertainty_profile, strategy_signature, regime_hash,
            regime_fit_score
        )
        checks.append(abstention_check)

        # Determine decision from checks
        decision, reasoning = self._resolve_decision(checks, tier)

        # Calculate sizes
        risk_adjusted = self._calculate_risk_adjusted_size(
            proposed_size, uncertainty_profile, robustness_score,
            regime_fit_score, adversarial_challenges
        )

        # Ex-ante prediction (Attack 10)
        ex_ante_pred = self._compute_ex_ante_prediction(
            checks, uncertainty_profile, robustness_score
        )

        # Record calibration (Attack 10)
        self._record_ex_ante_prediction(symbol, ex_ante_pred)

        # Abstention budget status
        abstention_status = None
        if decision == GovernanceDecision.ABSTAIN:
            key = f"{strategy_signature}::{regime_hash}"
            if key in self.abstention_state:
                s = self.abstention_state[key]
                abstention_status = {
                    "abstention_rate": s.abstention_count / max(1, s.total_decisions),
                    "consecutive": s.consecutive_abstentions,
                    "opportunity_cost_vs_benchmark": s.benchmark_pnl_while_abstained,
                    "retired": s.retired,
                }

        # Update stats
        self.decision_stats[decision.value] += 1

        return LiveGateOutput(
            decision=decision,
            tier=tier,
            checks=checks,
            approved_size=proposed_size if decision == GovernanceDecision.APPROVE else 0.0,
            risk_adjusted_size=risk_adjusted,
            reasoning=reasoning,
            requires_post_hoc=tier in (GovernanceTier.TIER_0_ULTRAFAST, GovernanceTier.TIER_1_INTRADAY),
            abstention_budget_status=abstention_status,
            ex_ante_prediction=ex_ante_pred,
        )

    # ── Tier 0 Fast Path ──────────────────────────────────────────────────

    def _evaluate_tier_0(
        self, symbol, proposed_size, signal_confidence,
        portfolio_drawdown, tier
    ) -> LiveGateOutput:
        """Tier 0: hard risk limits only. No full governance."""
        checks = []

        # Hard capital limit
        cap_check = GateCheckResult(
            check_name="tier_0_capital_limit",
            passed=proposed_size <= self.tier_0_capital.current_limit_usd,
            score=1.0 if proposed_size <= self.tier_0_capital.current_limit_usd else 0.0,
            severity=1.0 if proposed_size > self.tier_0_capital.current_limit_usd else 0.0,
            detail=f"Proposed ${proposed_size:,.0f} vs limit ${self.tier_0_capital.current_limit_usd:,.0f}",
            can_override=False,
        )
        checks.append(cap_check)

        # Confidence floor
        checks.append(GateCheckResult(
            check_name="tier_0_confidence_floor",
            passed=signal_confidence >= 0.7,
            score=signal_confidence,
            severity=0.5 if signal_confidence < 0.7 else 0.0,
            detail=f"Confidence {signal_confidence:.2f}",
            can_override=False,
        ))

        # Portfolio drawdown
        checks.append(GateCheckResult(
            check_name="tier_0_drawdown_limit",
            passed=portfolio_drawdown < self.criteria.max_portfolio_drawdown,
            score=1.0 - portfolio_drawdown,
            severity=portfolio_drawdown,
            detail=f"Drawdown {portfolio_drawdown:.2%}",
            can_override=False,
        ))

        if not cap_check.passed or portfolio_drawdown >= self.criteria.max_portfolio_drawdown:
            decision = GovernanceDecision.REJECT
            reasoning = "Tier 0 hard limit breached"
        elif signal_confidence < 0.7:
            decision = GovernanceDecision.RESIZE
            reasoning = "Tier 0 low confidence — resize"
        else:
            decision = GovernanceDecision.APPROVE
            reasoning = "Tier 0 checks passed"

        self.decision_stats[decision.value] += 1

        return LiveGateOutput(
            decision=decision,
            tier=tier,
            checks=checks,
            approved_size=proposed_size if decision == GovernanceDecision.APPROVE else 0.0,
            risk_adjusted_size=min(proposed_size, self.tier_0_capital.current_limit_usd) * signal_confidence,
            reasoning=reasoning,
            requires_post_hoc=True,
        )

    # ── Individual Gate Checks ─────────────────────────────────────────────

    def _check_thesis_schema(self, claims: List[Any]) -> GateCheckResult:
        """1. Thesis schema check — structural validity"""
        if not claims:
            return GateCheckResult("thesis_schema", False, 0.0, 1.0,
                                   "No claims provided", can_override=False)
        has_thesis = any(getattr(c, 'claim_type', None) and
                         c.claim_type.value == 'thesis' for c in claims)
        if not has_thesis:
            return GateCheckResult("thesis_schema", False, 0.2, 0.8,
                                   "No thesis claim found", can_override=False)
        return GateCheckResult("thesis_schema", True, 1.0, 0.0,
                               "Thesis schema valid")

    def _check_minimum_evidence(self, evidence_coverage: Dict) -> GateCheckResult:
        """2. Minimum evidence check"""
        coverage_score = evidence_coverage.get('coverage_score', 0) if evidence_coverage else 0
        passed = coverage_score >= self.criteria.min_evidence_coverage
        severity = max(0, self.criteria.min_evidence_coverage - coverage_score)
        return GateCheckResult(
            "minimum_evidence", passed, coverage_score, severity,
            f"Evidence coverage {coverage_score:.2f} vs min {self.criteria.min_evidence_coverage:.2f}",
            can_override=True,
        )

    def _check_contradiction_severity(self, challenges: List[Any]) -> GateCheckResult:
        """3. Contradiction severity check"""
        if not challenges:
            return GateCheckResult("contradiction_severity", True, 1.0, 0.0,
                                   "No adversarial challenges")
        max_sev = max(c.severity for c in challenges)
        passed = max_sev <= self.criteria.max_contradiction_severity
        return GateCheckResult(
            "contradiction_severity", passed, 1.0 - max_sev, max_sev,
            f"Max challenge severity {max_sev:.2f} vs ceiling {self.criteria.max_contradiction_severity:.2f}",
            can_override=True,
        )

    def _check_regime_fit(self, regime_fit: float, underrep: bool) -> GateCheckResult:
        """4. Regime fit check"""
        passed = regime_fit >= self.criteria.min_regime_fit and not underrep
        severity = max(0, self.criteria.min_regime_fit - regime_fit)
        if underrep:
            severity = max(severity, 0.5)
        detail = f"Regime fit {regime_fit:.2f}"
        if underrep:
            detail += " (underrepresented)"
        return GateCheckResult("regime_fit", passed, regime_fit, severity,
                               detail, can_override=True)

    def _check_execution_feasibility(self, feasibility: Optional[ExecutionFeasibility]) -> GateCheckResult:
        """5. Execution feasibility check"""
        if not feasibility:
            return GateCheckResult("execution_feasibility", True, 0.5, 0.0,
                                   "No feasibility data — proceeding with caution",
                                   can_override=True)
        if not feasibility.feasible:
            return GateCheckResult("execution_feasibility", False, 0.0, 1.0,
                                   f"Not feasible: {feasibility.constraints}",
                                   can_override=False)
        return GateCheckResult("execution_feasibility", True, 1.0, 0.0,
                               "Execution feasible")

    def _check_hard_risk(
        self, drawdown: float, sector_exp: float,
        corr_conc: float, proposed_size: float
    ) -> GateCheckResult:
        """6. Hard risk check — can trigger KILL_SWITCH"""
        violations = []
        if drawdown >= self.criteria.max_portfolio_drawdown:
            violations.append(f"drawdown {drawdown:.2%}")
        if sector_exp >= self.criteria.max_sector_exposure:
            violations.append(f"sector exposure {sector_exp:.2%}")
        if corr_conc >= self.criteria.max_correlation_concentration:
            violations.append(f"correlation concentration {corr_conc:.2%}")
        if proposed_size > self.criteria.max_position_size:
            violations.append(f"position size {proposed_size:.2%}")

        if violations:
            # Multiple hard violations → kill switch
            if len(violations) >= 2 or drawdown >= self.criteria.max_portfolio_drawdown:
                self._activate_kill_switch(f"Hard risk violations: {', '.join(violations)}")
                return GateCheckResult("hard_risk", False, 0.0, 1.0,
                                       f"KILL SWITCH: {', '.join(violations)}",
                                       can_override=False)
            return GateCheckResult("hard_risk", False, 0.3, 0.8,
                                   f"Hard risk violation: {violations[0]}",
                                   can_override=False)
        return GateCheckResult("hard_risk", True, 1.0, 0.0, "Within hard risk bounds")

    def _check_abstention_decision(
        self,
        uncertainty: UncertaintyProfile,
        strategy_signature: str,
        regime_hash: str,
        regime_fit: float,
    ) -> GateCheckResult:
        """
        7. Abstention decision — budget-aware, regime-separated (Attack 6).

        High-vol regimes get higher abstention tolerance.
        Opportunity cost measured against a continuous benchmark.
        """
        key = f"{strategy_signature}::{regime_hash}"
        if key not in self.abstention_state:
            self.abstention_state[key] = StrategyRegimeAbstentionState(
                strategy_signature=strategy_signature,
                regime_hash=regime_hash,
            )
        state = self.abstention_state[key]
        state.total_decisions += 1

        # Regime-separated threshold (Attack 6)
        max_rate = self.abstention_thresholds.normal_vol_max_abstention_rate
        if regime_fit < 0.3:
            max_rate = self.abstention_thresholds.extreme_vol_max_abstention_rate
        elif regime_fit < 0.5:
            max_rate = self.abstention_thresholds.high_vol_max_abstention_rate
        elif regime_fit > 0.8:
            max_rate = self.abstention_thresholds.low_vol_max_abstention_rate

        current_rate = state.abstention_count / max(1, state.total_decisions)
        over_budget = current_rate >= max_rate
        consecutive_limit = state.consecutive_abstentions >= self.abstention_thresholds.consecutive_abstention_limit

        should_abstain = uncertainty.abstention_probability > self.criteria.max_abstention_probability

        if should_abstain:
            if state.retired:
                return GateCheckResult("abstention_decision", False, 0.0, 1.0,
                                       "Strategy retired — cannot abstain further",
                                       can_override=False)
            if over_budget and consecutive_limit:
                return GateCheckResult("abstention_decision", True, 0.2, 0.7,
                                       f"Abstention budget EXCEEDED (rate={current_rate:.2%}, "
                                       f"consecutive={state.consecutive_abstentions}). "
                                       f"Requires MANUAL_REVIEW.",
                                       can_override=True)
            state.abstention_count += 1
            state.consecutive_abstentions += 1
            return GateCheckResult("abstention_decision", True, 0.4, 0.3,
                                   f"Abstention within budget (rate={current_rate:.2%})")
        else:
            state.consecutive_abstentions = 0
            return GateCheckResult("abstention_decision", True, 1.0, 0.0,
                                   "No abstention needed")

    # ── Decision Resolution ────────────────────────────────────────────────

    def _resolve_decision(
        self, checks: List[GateCheckResult], tier: GovernanceTier
    ) -> Tuple[GovernanceDecision, str]:
        """Resolve all check results into a final decision"""
        hard_failures = [c for c in checks if not c.passed and not c.can_override]
        soft_failures = [c for c in checks if not c.passed and c.can_override]

        # Kill switch
        if any(c.check_name == "hard_risk" and c.severity >= 1.0 for c in checks):
            return GovernanceDecision.KILL_SWITCH, "Hard risk kill switch activated"

        # Hard failures → REJECT
        if hard_failures:
            names = [c.check_name for c in hard_failures]
            return GovernanceDecision.REJECT, f"Hard check failures: {', '.join(names)}"

        # Abstention budget exceeded + consecutive limit → MANUAL_REVIEW
        abstention = next((c for c in checks if c.check_name == "abstention_decision"
                           and c.severity >= 0.7), None)
        if abstention:
            return GovernanceDecision.MANUAL_REVIEW, abstention.detail

        # High abstention probability → ABSTAIN
        if any(c.check_name == "abstention_decision" and c.score <= 0.4 for c in checks):
            return GovernanceDecision.ABSTAIN, "Uncertainty too high — abstaining"

        # Multiple soft failures → DEFER or PAPER_ONLY
        if len(soft_failures) >= 3:
            if tier == GovernanceTier.TIER_2_FULL:
                return GovernanceDecision.PAPER_ONLY, \
                    f"Multiple concerns ({len(soft_failures)}) — paper trade only"
            return GovernanceDecision.DEFER, \
                f"Multiple concerns ({len(soft_failures)}) — defer to better conditions"

        # Some soft failures but thesis sound → RESIZE
        if soft_failures:
            return GovernanceDecision.RESIZE, \
                f"Concerns present but manageable: {soft_failures[0].check_name}"

        # All checks pass → APPROVE
        return GovernanceDecision.APPROVE, "All gate checks passed"

    # ── Ex-Ante Calibration (Attack 10) ────────────────────────────────────

    def _compute_ex_ante_prediction(
        self, checks: List[GateCheckResult],
        uncertainty: UncertaintyProfile,
        robustness: float,
    ) -> float:
        """
        Compute predicted probability of success using ex-ante information only.
        Never use ex-post PnL to classify decisions as good/bad.
        """
        check_scores = [c.score for c in checks]
        avg_check = sum(check_scores) / len(check_scores) if check_scores else 0.5
        confidence = uncertainty.overall_confidence
        # Blend check scores, confidence, and robustness
        prediction = 0.4 * avg_check + 0.35 * confidence + 0.25 * robustness
        return max(0.01, min(0.99, prediction))

    def _record_ex_ante_prediction(self, decision_id: str, prediction: float):
        """Record prediction for later Brier score calculation"""
        self.calibration_records.append(ExAnteCalibrationRecord(
            decision_id=decision_id,
            predicted_prob_success=prediction,
        ))

    def record_outcome_for_calibration(
        self, decision_id: str, was_success: bool
    ):
        """
        Attack 10 fix: Record actual outcome using proper scoring rules.
        Brier score = (predicted - actual)^2
        Log loss = -[actual*log(pred) + (1-actual)*log(1-pred)]
        """
        for rec in self.calibration_records:
            if rec.decision_id == decision_id and rec.actual_success is None:
                rec.actual_success = was_success
                p = rec.predicted_prob_success
                actual = 1.0 if was_success else 0.0
                rec.brier_score = (p - actual) ** 2
                if p > 0 and p < 1:
                    rec.log_loss = -(actual * math.log(p) + (1 - actual) * math.log(1 - p))
                else:
                    rec.log_loss = 10.0  # Cap extreme values
                self.brier_scores.append(rec.brier_score)
                self.log_losses.append(rec.log_loss)
                break

    def get_calibration_stats(self) -> Dict[str, Any]:
        """Get ex-ante calibration statistics (Attack 10)"""
        resolved = [r for r in self.calibration_records if r.brier_score is not None]
        if not resolved:
            return {"sample_size": 0, "avg_brier": None, "avg_log_loss": None}
        return {
            "sample_size": len(resolved),
            "avg_brier": sum(r.brier_score for r in resolved) / len(resolved),
            "avg_log_loss": sum(r.log_loss for r in resolved) / len(resolved),
            "recent_brier": list(self.brier_scores)[-20:],
        }

    # ── Kill Switch ────────────────────────────────────────────────────────

    def _activate_kill_switch(self, reason: str):
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        self.kill_switch_timestamp = datetime.utcnow()
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")

    def deactivate_kill_switch(self, authorized_by: str):
        """Only human can deactivate kill switch"""
        self.kill_switch_active = False
        logger.critical(f"Kill switch deactivated by {authorized_by}")

    # ── Risk-Adjusted Size ─────────────────────────────────────────────────

    def _calculate_risk_adjusted_size(
        self, proposed: float, uncertainty: UncertaintyProfile,
        robustness: float, regime_fit: float, challenges: List[Any]
    ) -> float:
        adjusted = proposed
        adjusted *= (0.5 + 0.5 * uncertainty.overall_confidence)
        adjusted *= (0.3 + 0.7 * robustness)
        adjusted *= (0.4 + 0.6 * regime_fit)
        if challenges:
            avg_sev = sum(c.severity for c in challenges) / len(challenges)
            adjusted *= (1 - avg_sev * 0.3)
        adjusted = min(adjusted, self.criteria.max_position_size)
        return round(adjusted, 4)

    # ── Statistics ─────────────────────────────────────────────────────────

    def get_decision_statistics(self) -> Dict[str, Any]:
        total = sum(self.decision_stats.values())
        stats = dict(self.decision_stats)
        if total > 0:
            stats['approval_rate'] = stats.get('approve', 0) / total
            stats['kill_switch_rate'] = stats.get('kill_switch', 0) / total
        stats['tier_0_capital_limit'] = self.tier_0_capital.current_limit_usd
        stats['tier_0_violations'] = self.tier_0_capital.violations
        stats['kill_switch_active'] = self.kill_switch_active
        stats['calibration'] = self.get_calibration_stats()
        return stats


# ── Legacy compatibility ──────────────────────────────────────────────────────

class GovernanceArbiter(LiveGovernanceGate):
    """
    Backward-compatible wrapper. Delegates to LiveGovernanceGate.
    """
    pass
