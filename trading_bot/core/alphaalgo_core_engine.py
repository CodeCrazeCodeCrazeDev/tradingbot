"""
AlphaAlgo Core - Hostile Capital-Preserving Quantitative Decision Engine

Primary objective: NOT to trade.
Objective: Only allow trades that survive adversarial scrutiny under real market constraints.

Assumptions:
- Markets are adversarial
- Alpha decays
- Most trades are bad
- Overconfidence is lethal
- Bias toward inaction unless proven otherwise

ABSOLUTE RULES (NON-NEGOTIABLE):
- No narrative-driven decisions
- No averaging weak signals
- No commitment under uncertainty
- No trade is better than a bad trade
- Minimum confidence dominates mean confidence
- Every trade must survive an internal adversary

Author: AlphaAlgo Core
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketHostility(Enum):
    """Market hostility classification"""
    BENIGN = auto()           # Normal conditions
    CAUTIOUS = auto()         # Slightly elevated risk
    HOSTILE = auto()          # High risk environment
    EXTREME = auto()          # Extreme risk, no trading
    LOW_EDGE_DENSITY = auto() # Edge is sparse


class DecisionOutcome(Enum):
    """Final decision outcomes"""
    TRADE_APPROVED = "TRADE_APPROVED"
    TRADE_REJECTED = "TRADE_REJECTED"
    NO_TRADE_MARKET_HOSTILE = "NO_TRADE_MARKET_HOSTILE"


class ClaimType(Enum):
    """Types of falsifiable claims"""
    REGIME_VALIDITY = auto()
    SIGNAL_EXPECTANCY = auto()
    VOLATILITY_SUITABILITY = auto()
    LIQUIDITY_FEASIBILITY = auto()
    TAIL_RISK_BOUNDED = auto()
    CORRELATION_ACCEPTABLE = auto()


class AgentRole(Enum):
    """Adversarial committee agent roles"""
    PROPOSER = auto()              # Argues FOR the trade
    KILLER = auto()                # Attempts to invalidate
    HISTORIAN = auto()             # Finds similar past failures
    EXECUTION_SABOTEUR = auto()    # Assumes worst fills
    RISK_PROSECUTOR = auto()       # Searches for tail risk collapse


@dataclass
class Claim:
    """A falsifiable claim about a trade"""
    claim_type: ClaimType
    description: str
    testable: bool
    historical_reference: Optional[str] = None
    can_fail_independently: bool = True
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        try:
            if not self.testable:
                raise ValueError(f"Claim {self.claim_type} must be testable")
            if not self.can_fail_independently:
                raise ValueError(f"Claim {self.claim_type} must fail independently")
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


@dataclass
class ConfidenceVector:
    """Multi-dimensional confidence (no single scores)"""
    statistical: float          # Historical expectancy
    regime: float              # Regime validity
    execution: float           # Execution feasibility
    tail_risk: float           # Tail risk bounded
    model_stability: float     # Model reliability
    
    sample_size: int = 0
    regime_novelty_penalty: float = 0.0
    alpha_decay_factor: float = 1.0
    
    def min_confidence(self) -> float:
        """Minimum confidence dominates"""
        return min(
            self.statistical,
            self.regime,
            self.execution,
            self.tail_risk,
            self.model_stability
        )
    
    def apply_penalties(self):
        """Apply sample size, novelty, and decay penalties"""
        # Sample size penalty
        try:
            if self.sample_size < 100:
                penalty = 1.0 - (self.sample_size / 100.0) * 0.3
                self.statistical *= penalty
        
            # Regime novelty penalty
            self.regime *= (1.0 - self.regime_novelty_penalty)
        
            # Alpha decay
            self.statistical *= self.alpha_decay_factor
            self.regime *= self.alpha_decay_factor
        except Exception as e:
            logger.error(f"Error in apply_penalties: {e}")
            raise


@dataclass
class AgentVerdict:
    """Verdict from an adversarial agent"""
    agent: AgentRole
    approved: bool
    reason: str
    severity: float  # 0.0 to 1.0
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeProposal:
    """A proposed trade for evaluation"""
    trade_id: str
    symbol: str
    direction: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Context
    signal_strength: float = 0.0
    strategy_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Market data
    market_data: Optional[pd.DataFrame] = None
    regime: Optional[str] = None
    volatility: float = 0.0
    liquidity_score: float = 0.0
    
    # Portfolio context
    current_equity: float = 0.0
    current_drawdown: float = 0.0
    correlation_exposure: float = 0.0


@dataclass
class CoreDecision:
    """Final decision from AlphaAlgo Core"""
    outcome: DecisionOutcome
    trade_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Rejection details
    failed_claims: List[ClaimType] = field(default_factory=list)
    min_confidence_component: Optional[str] = None
    dominant_rejection_reason: Optional[str] = None
    
    # Approval details
    approved_position_size: float = 0.0
    confidence_vector: Optional[ConfidenceVector] = None
    
    # Audit trail
    market_hostility: Optional[MarketHostility] = None
    killer_verdict: Optional[AgentVerdict] = None
    all_verdicts: List[AgentVerdict] = field(default_factory=list)


class MarketHostilityDetector:
    """Stage 0: Market Hostility Check"""
    
    def __init__(self):
        try:
            self.performance_history = deque(maxlen=100)
            self.drawdown_history = deque(maxlen=50)
            self.regime_switches = deque(maxlen=20)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def evaluate(
        self,
        recent_performance: List[float],
        regime_stability: float,
        liquidity_stress: float,
        cross_strategy_dispersion: float
    ) -> Tuple[MarketHostility, str]:
        """
        Evaluate market hostility level
        
        Returns:
            (hostility_level, reason)
        """
        # Update history
        try:
            self.performance_history.extend(recent_performance)
        
            # Calculate metrics
            if len(self.performance_history) < 10:
                return MarketHostility.CAUTIOUS, "Insufficient history"
        
            perf_array = np.array(list(self.performance_history))
        
            # Drawdown clustering
            drawdowns = perf_array[perf_array < 0]
            if len(drawdowns) > len(perf_array) * 0.7:
                return MarketHostility.HOSTILE, "Drawdown clustering detected"
        
            # Cross-strategy dispersion (high = strategies disagree = hostile)
            if cross_strategy_dispersion > 0.8:
                return MarketHostility.HOSTILE, "High cross-strategy dispersion"
        
            # Regime instability
            if regime_stability < 0.3:
                return MarketHostility.HOSTILE, "Regime instability"
        
            # Liquidity stress
            if liquidity_stress > 0.7:
                return MarketHostility.EXTREME, "Liquidity stress detected"
        
            # Edge density (recent win rate)
            recent_wins = perf_array[-20:][perf_array[-20:] > 0]
            win_rate = len(recent_wins) / min(20, len(perf_array))
        
            if win_rate < 0.3:
                return MarketHostility.LOW_EDGE_DENSITY, "Low edge density"
        
            # Determine hostility level
            if liquidity_stress > 0.5 or regime_stability < 0.5:
                return MarketHostility.HOSTILE, "Elevated risk indicators"
            elif cross_strategy_dispersion > 0.6:
                return MarketHostility.CAUTIOUS, "Moderate dispersion"
            else:
                return MarketHostility.BENIGN, "Normal conditions"
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            raise


class ClaimGraphConstructor:
    """Stage 1: Claim Graph Construction"""
    
    def construct_claims(self, proposal: TradeProposal) -> List[Claim]:
        """
        Decompose trade into independent, falsifiable claims
        
        Minimum required claims:
        - Regime validity
        - Signal expectancy
        - Volatility suitability
        - Liquidity/execution feasibility
        - Tail risk boundedness
        - Portfolio correlation acceptability
        """
        try:
            claims = []
        
            # Claim 1: Regime Validity
            claims.append(Claim(
                claim_type=ClaimType.REGIME_VALIDITY,
                description=f"Current regime '{proposal.regime}' is valid for this strategy",
                testable=True,
                historical_reference=f"regime_{proposal.regime}_history",
                evidence={'regime': proposal.regime}
            ))
        
            # Claim 2: Signal Expectancy
            claims.append(Claim(
                claim_type=ClaimType.SIGNAL_EXPECTANCY,
                description=f"Signal strength {proposal.signal_strength:.3f} has positive expectancy",
                testable=True,
                historical_reference=f"strategy_{proposal.strategy_id}_expectancy",
                evidence={'signal_strength': proposal.signal_strength}
            ))
        
            # Claim 3: Volatility Suitability
            claims.append(Claim(
                claim_type=ClaimType.VOLATILITY_SUITABILITY,
                description=f"Volatility {proposal.volatility:.3f} is suitable for strategy",
                testable=True,
                historical_reference="volatility_regime_performance",
                evidence={'volatility': proposal.volatility}
            ))
        
            # Claim 4: Liquidity Feasibility
            claims.append(Claim(
                claim_type=ClaimType.LIQUIDITY_FEASIBILITY,
                description=f"Liquidity score {proposal.liquidity_score:.3f} allows execution",
                testable=True,
                historical_reference="execution_quality_history",
                evidence={'liquidity_score': proposal.liquidity_score}
            ))
        
            # Claim 5: Tail Risk Bounded
            claims.append(Claim(
                claim_type=ClaimType.TAIL_RISK_BOUNDED,
                description="Tail risk is bounded and acceptable",
                testable=True,
                historical_reference="tail_risk_events",
                evidence={'stop_loss': proposal.stop_loss}
            ))
        
            # Claim 6: Correlation Acceptable
            claims.append(Claim(
                claim_type=ClaimType.CORRELATION_ACCEPTABLE,
                description=f"Portfolio correlation {proposal.correlation_exposure:.3f} is acceptable",
                testable=True,
                historical_reference="correlation_risk_history",
                evidence={'correlation_exposure': proposal.correlation_exposure}
            ))
        
            return claims
        except Exception as e:
            logger.error(f"Error in construct_claims: {e}")
            raise


class OrthogonalEvaluator:
    """Stage 2: Orthogonal Evaluation"""
    
    def __init__(self):
        try:
            self.historical_data = {}
            self.regime_classifier = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def evaluate_claim(
        self,
        claim: Claim,
        proposal: TradeProposal
    ) -> Tuple[bool, float, str]:
        """
        Evaluate claim using independent perspectives
        
        Required perspectives:
        - Statistical (historical expectancy, drawdown)
        - Regime detection (state validity)
        - Market microstructure (spread, slippage)
        - Adversarial failure analysis
        - Execution stress testing
        - Risk/tail event exposure
        
        Returns:
            (passed, confidence, reason)
        """
        try:
            if claim.claim_type == ClaimType.REGIME_VALIDITY:
                return self._evaluate_regime(claim, proposal)
            elif claim.claim_type == ClaimType.SIGNAL_EXPECTANCY:
                return self._evaluate_expectancy(claim, proposal)
            elif claim.claim_type == ClaimType.VOLATILITY_SUITABILITY:
                return self._evaluate_volatility(claim, proposal)
            elif claim.claim_type == ClaimType.LIQUIDITY_FEASIBILITY:
                return self._evaluate_liquidity(claim, proposal)
            elif claim.claim_type == ClaimType.TAIL_RISK_BOUNDED:
                return self._evaluate_tail_risk(claim, proposal)
            elif claim.claim_type == ClaimType.CORRELATION_ACCEPTABLE:
                return self._evaluate_correlation(claim, proposal)
            else:
                return False, 0.0, "Unknown claim type"
        except Exception as e:
            logger.error(f"Error in evaluate_claim: {e}")
            raise
    
    def _evaluate_regime(self, claim: Claim, proposal: TradeProposal) -> Tuple[bool, float, str]:
        """Evaluate regime validity"""
        try:
            if not proposal.regime:
                return False, 0.0, "No regime specified"
        
            # Check regime stability (mock - integrate with actual regime detector)
            regime_confidence = 0.7  # Placeholder
        
            if regime_confidence < 0.5:
                return False, regime_confidence, "Regime confidence too low"
        
            return True, regime_confidence, "Regime valid"
        except Exception as e:
            logger.error(f"Error in _evaluate_regime: {e}")
            raise
    
    def _evaluate_expectancy(self, claim: Claim, proposal: TradeProposal) -> Tuple[bool, float, str]:
        """Evaluate signal expectancy"""
        try:
            signal_strength = proposal.signal_strength
        
            # Minimum signal threshold
            if signal_strength < 0.6:
                return False, signal_strength, "Signal strength below threshold"
        
            # Historical expectancy check (mock)
            historical_win_rate = 0.55  # Placeholder
        
            if historical_win_rate < 0.5:
                return False, historical_win_rate, "Negative historical expectancy"
        
            confidence = min(signal_strength, historical_win_rate)
            return True, confidence, "Positive expectancy"
        except Exception as e:
            logger.error(f"Error in _evaluate_expectancy: {e}")
            raise
    
    def _evaluate_volatility(self, claim: Claim, proposal: TradeProposal) -> Tuple[bool, float, str]:
        """Evaluate volatility suitability"""
        try:
            volatility = proposal.volatility
        
            # Volatility bounds
            if volatility > 0.5:  # Too high
                return False, 0.3, "Volatility too high"
            elif volatility < 0.05:  # Too low (potential regime shift)
                return False, 0.4, "Volatility suspiciously low"
        
            # Optimal range: 0.1 to 0.3
            if 0.1 <= volatility <= 0.3:
                confidence = 0.8
            else:
                confidence = 0.6
        
            return True, confidence, "Volatility acceptable"
        except Exception as e:
            logger.error(f"Error in _evaluate_volatility: {e}")
            raise
    
    def _evaluate_liquidity(self, claim: Claim, proposal: TradeProposal) -> Tuple[bool, float, str]:
        """Evaluate liquidity feasibility"""
        try:
            liquidity_score = proposal.liquidity_score
        
            if liquidity_score < 0.3:
                return False, liquidity_score, "Insufficient liquidity"
        
            # Execution quality estimate
            expected_slippage = (1.0 - liquidity_score) * 0.01  # 0-1% slippage
        
            if expected_slippage > 0.005:  # >0.5% slippage
                return False, liquidity_score, "Expected slippage too high"
        
            return True, liquidity_score, "Liquidity adequate"
        except Exception as e:
            logger.error(f"Error in _evaluate_liquidity: {e}")
            raise
    
    def _evaluate_tail_risk(self, claim: Claim, proposal: TradeProposal) -> Tuple[bool, float, str]:
        """Evaluate tail risk boundedness"""
        try:
            if not proposal.stop_loss:
                return False, 0.0, "No stop loss defined"
        
            # Calculate risk
            if proposal.direction == 'long':
                risk_pct = (proposal.entry_price - proposal.stop_loss) / proposal.entry_price
            else:
                risk_pct = (proposal.stop_loss - proposal.entry_price) / proposal.entry_price
        
            if risk_pct > 0.02:  # >2% risk
                return False, 0.3, f"Risk {risk_pct:.2%} exceeds 2% limit"
        
            # Tail risk confidence based on stop distance
            confidence = 1.0 - (risk_pct / 0.02)
        
            return True, confidence, "Tail risk bounded"
        except Exception as e:
            logger.error(f"Error in _evaluate_tail_risk: {e}")
            raise
    
    def _evaluate_correlation(self, claim: Claim, proposal: TradeProposal) -> Tuple[bool, float, str]:
        """Evaluate portfolio correlation"""
        try:
            correlation = proposal.correlation_exposure
        
            if correlation > 0.7:
                return False, 0.3, "Excessive correlation exposure"
        
            confidence = 1.0 - correlation
            return True, confidence, "Correlation acceptable"
        except Exception as e:
            logger.error(f"Error in _evaluate_correlation: {e}")
            raise


class AdversarialCommittee:
    """Stage 3: Adversarial Internal Committee"""
    
    def __init__(self):
        try:
            self.trade_history = deque(maxlen=1000)
            self.failure_patterns = defaultdict(list)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    async def evaluate(
        self,
        proposal: TradeProposal,
        claims: List[Claim],
        claim_results: Dict[ClaimType, Tuple[bool, float, str]]
    ) -> List[AgentVerdict]:
        """
        Run adversarial committee evaluation
        
        Agents:
        - Proposer: argues FOR the trade
        - Killer: attempts to invalidate the trade
        - Historian: finds similar past failures
        - Execution Saboteur: assumes worst fills
        - Risk Prosecutor: searches for tail risk collapse
        
        If the Killer succeeds, the trade is rejected immediately.
        """
        try:
            verdicts = []
        
            # Proposer
            proposer_verdict = self._proposer_evaluate(proposal, claims, claim_results)
            verdicts.append(proposer_verdict)
        
            # Killer (most important)
            killer_verdict = self._killer_evaluate(proposal, claims, claim_results)
            verdicts.append(killer_verdict)
        
            # If Killer rejects, stop immediately
            if not killer_verdict.approved:
                logger.warning(f"Killer rejected trade {proposal.trade_id}: {killer_verdict.reason}")
                return verdicts
        
            # Historian
            historian_verdict = self._historian_evaluate(proposal)
            verdicts.append(historian_verdict)
        
            # Execution Saboteur
            saboteur_verdict = self._execution_saboteur_evaluate(proposal)
            verdicts.append(saboteur_verdict)
        
            # Risk Prosecutor
            prosecutor_verdict = self._risk_prosecutor_evaluate(proposal)
            verdicts.append(prosecutor_verdict)
        
            return verdicts
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            raise
    
    def _proposer_evaluate(
        self,
        proposal: TradeProposal,
        claims: List[Claim],
        claim_results: Dict[ClaimType, Tuple[bool, float, str]]
    ) -> AgentVerdict:
        """Proposer argues FOR the trade"""
        try:
            passed_claims = sum(1 for result in claim_results.values() if result[0])
            total_claims = len(claims)
        
            if passed_claims == total_claims:
                return AgentVerdict(
                    agent=AgentRole.PROPOSER,
                    approved=True,
                    reason=f"All {total_claims} claims passed",
                    severity=0.0
                )
            else:
                return AgentVerdict(
                    agent=AgentRole.PROPOSER,
                    approved=False,
                    reason=f"Only {passed_claims}/{total_claims} claims passed",
                    severity=0.5
                )
        except Exception as e:
            logger.error(f"Error in _proposer_evaluate: {e}")
            raise
    
    def _killer_evaluate(
        self,
        proposal: TradeProposal,
        claims: List[Claim],
        claim_results: Dict[ClaimType, Tuple[bool, float, str]]
    ) -> AgentVerdict:
        """Killer attempts to invalidate the trade"""
        # Check for any failed claims
        try:
            failed_claims = [ct for ct, result in claim_results.items() if not result[0]]
        
            if failed_claims:
                return AgentVerdict(
                    agent=AgentRole.KILLER,
                    approved=False,
                    reason=f"Failed claims: {[ct.name for ct in failed_claims]}",
                    severity=1.0,
                    evidence={'failed_claims': failed_claims}
                )
        
            # Check for weak confidence
            min_confidence = min(result[1] for result in claim_results.values())
            if min_confidence < 0.6:
                return AgentVerdict(
                    agent=AgentRole.KILLER,
                    approved=False,
                    reason=f"Minimum confidence {min_confidence:.3f} below threshold",
                    severity=0.8,
                    evidence={'min_confidence': min_confidence}
                )
        
            # Check for overconfidence (signal too strong = suspicious)
            if proposal.signal_strength > 0.95:
                return AgentVerdict(
                    agent=AgentRole.KILLER,
                    approved=False,
                    reason="Signal suspiciously strong (potential overfitting)",
                    severity=0.7
                )
        
            # Check drawdown state
            if proposal.current_drawdown > 0.15:  # >15% drawdown
                return AgentVerdict(
                    agent=AgentRole.KILLER,
                    approved=False,
                    reason=f"Current drawdown {proposal.current_drawdown:.1%} too high",
                    severity=0.9
                )
        
            # Killer approves (no invalidation found)
            return AgentVerdict(
                agent=AgentRole.KILLER,
                approved=True,
                reason="No invalidation found",
                severity=0.0
            )
        except Exception as e:
            logger.error(f"Error in _killer_evaluate: {e}")
            raise
    
    def _historian_evaluate(self, proposal: TradeProposal) -> AgentVerdict:
        """Historian finds similar past failures"""
        # Check for similar failed trades (mock implementation)
        try:
            similar_failures = []
        
            for past_trade in self.trade_history:
                if (past_trade.get('symbol') == proposal.symbol and
                    past_trade.get('strategy_id') == proposal.strategy_id and
                    past_trade.get('outcome') == 'loss'):
                    similar_failures.append(past_trade)
        
            if len(similar_failures) > 5:  # Many similar failures
                return AgentVerdict(
                    agent=AgentRole.HISTORIAN,
                    approved=False,
                    reason=f"Found {len(similar_failures)} similar past failures",
                    severity=0.8,
                    evidence={'similar_failures': len(similar_failures)}
                )
        
            return AgentVerdict(
                agent=AgentRole.HISTORIAN,
                approved=True,
                reason="No significant failure pattern found",
                severity=0.0
            )
        except Exception as e:
            logger.error(f"Error in _historian_evaluate: {e}")
            raise
    
    def _execution_saboteur_evaluate(self, proposal: TradeProposal) -> AgentVerdict:
        """Execution Saboteur assumes worst fills"""
        # Assume worst-case slippage
        try:
            worst_slippage = 0.01  # 1%
            liquidity_penalty = (1.0 - proposal.liquidity_score) * 0.02  # Up to 2%
        
            total_slippage = worst_slippage + liquidity_penalty
        
            # Calculate impact on trade
            if proposal.direction == 'long':
                worst_entry = proposal.entry_price * (1 + total_slippage)
            else:
                worst_entry = proposal.entry_price * (1 - total_slippage)
        
            # Check if trade still viable with worst execution
            if proposal.stop_loss:
                if proposal.direction == 'long':
                    worst_risk = (worst_entry - proposal.stop_loss) / worst_entry
                else:
                    worst_risk = (proposal.stop_loss - worst_entry) / worst_entry
            
                if worst_risk > 0.03:  # >3% risk with slippage
                    return AgentVerdict(
                        agent=AgentRole.EXECUTION_SABOTEUR,
                        approved=False,
                        reason=f"Worst-case execution risk {worst_risk:.2%} exceeds limit",
                        severity=0.7,
                        evidence={'worst_slippage': total_slippage}
                    )
        
            return AgentVerdict(
                agent=AgentRole.EXECUTION_SABOTEUR,
                approved=True,
                reason="Trade viable under worst execution",
                severity=0.0
            )
        except Exception as e:
            logger.error(f"Error in _execution_saboteur_evaluate: {e}")
            raise
    
    def _risk_prosecutor_evaluate(self, proposal: TradeProposal) -> AgentVerdict:
        """Risk Prosecutor searches for tail risk collapse"""
        # Check for tail risk scenarios
        try:
            risk_factors = []
        
            # High volatility = tail risk
            if proposal.volatility > 0.4:
                risk_factors.append("High volatility")
        
            # High correlation = contagion risk
            if proposal.correlation_exposure > 0.6:
                risk_factors.append("High correlation exposure")
        
            # Large position relative to equity
            position_value = proposal.quantity * proposal.entry_price
            if proposal.current_equity > 0:
                position_pct = position_value / proposal.current_equity
                if position_pct > 0.2:  # >20% of equity
                    risk_factors.append(f"Large position {position_pct:.1%}")
        
            # Existing drawdown
            if proposal.current_drawdown > 0.1:
                risk_factors.append(f"Drawdown {proposal.current_drawdown:.1%}")
        
            if len(risk_factors) >= 2:  # Multiple risk factors
                return AgentVerdict(
                    agent=AgentRole.RISK_PROSECUTOR,
                    approved=False,
                    reason=f"Multiple tail risk factors: {', '.join(risk_factors)}",
                    severity=0.8,
                    evidence={'risk_factors': risk_factors}
                )
        
            return AgentVerdict(
                agent=AgentRole.RISK_PROSECUTOR,
                approved=True,
                reason="No tail risk collapse detected",
                severity=0.0
            )
        except Exception as e:
            logger.error(f"Error in _risk_prosecutor_evaluate: {e}")
            raise


class ConfidenceVectorBuilder:
    """Stage 4: Confidence Vector (No Single Scores)"""
    
    def build_confidence_vector(
        self,
        proposal: TradeProposal,
        claim_results: Dict[ClaimType, Tuple[bool, float, str]],
        sample_size: int = 100
    ) -> ConfidenceVector:
        """
        Build multi-dimensional confidence vector
        
        Each confidence must:
        - Include sample size awareness
        - Penalize regime novelty
        - Decay with time (alpha decay)
        """
        # Extract confidences from claim results
        try:
            statistical = claim_results.get(ClaimType.SIGNAL_EXPECTANCY, (False, 0.0, ""))[1]
            regime = claim_results.get(ClaimType.REGIME_VALIDITY, (False, 0.0, ""))[1]
            execution = claim_results.get(ClaimType.LIQUIDITY_FEASIBILITY, (False, 0.0, ""))[1]
            tail_risk = claim_results.get(ClaimType.TAIL_RISK_BOUNDED, (False, 0.0, ""))[1]
        
            # Model stability (based on volatility and correlation)
            vol_conf = claim_results.get(ClaimType.VOLATILITY_SUITABILITY, (False, 0.0, ""))[1]
            corr_conf = claim_results.get(ClaimType.CORRELATION_ACCEPTABLE, (False, 0.0, ""))[1]
            model_stability = (vol_conf + corr_conf) / 2.0
        
            # Regime novelty penalty (mock - should check historical regime frequency)
            regime_novelty_penalty = 0.1  # 10% penalty for new regimes
        
            # Alpha decay (mock - should track strategy age)
            alpha_decay_factor = 0.95  # 5% decay
        
            vector = ConfidenceVector(
                statistical=statistical,
                regime=regime,
                execution=execution,
                tail_risk=tail_risk,
                model_stability=model_stability,
                sample_size=sample_size,
                regime_novelty_penalty=regime_novelty_penalty,
                alpha_decay_factor=alpha_decay_factor
            )
        
            # Apply penalties
            vector.apply_penalties()
        
            return vector
        except Exception as e:
            logger.error(f"Error in build_confidence_vector: {e}")
            raise


class DecisionGate:
    """Stage 5: Decision Gate"""
    
    def __init__(self, required_threshold: float = 0.6):
        try:
            self.required_threshold = required_threshold
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def evaluate(
        self,
        proposal: TradeProposal,
        claims: List[Claim],
        claim_results: Dict[ClaimType, Tuple[bool, float, str]],
        confidence_vector: ConfidenceVector,
        verdicts: List[AgentVerdict]
    ) -> Tuple[bool, str]:
        """
        A trade is authorized ONLY IF:
        - All claims pass
        - min(confidence_vector) ≥ required_threshold
        - No catastrophic failure mode is detected
        - Expected drawdown is within limits
        - Portfolio impact is acceptable
        
        If ANY condition fails:
        → Reject trade
        → Log reason
        → Take no action
        
        Inaction is a valid and preferred outcome.
        """
        # Check 1: All claims must pass
        try:
            failed_claims = [ct for ct, result in claim_results.items() if not result[0]]
            if failed_claims:
                return False, f"Failed claims: {[ct.name for ct in failed_claims]}"
        
            # Check 2: Minimum confidence threshold
            min_conf = confidence_vector.min_confidence()
            if min_conf < self.required_threshold:
                component = self._identify_min_component(confidence_vector)
                return False, f"Min confidence {min_conf:.3f} < {self.required_threshold:.3f} ({component})"
        
            # Check 3: Killer verdict
            killer_verdict = next((v for v in verdicts if v.agent == AgentRole.KILLER), None)
            if killer_verdict and not killer_verdict.approved:
                return False, f"Killer rejected: {killer_verdict.reason}"
        
            # Check 4: Any agent with high severity rejection
            high_severity_rejections = [v for v in verdicts if not v.approved and v.severity > 0.7]
            if high_severity_rejections:
                reasons = [v.reason for v in high_severity_rejections]
                return False, f"High severity rejections: {reasons}"
        
            # Check 5: Expected drawdown within limits
            if proposal.current_drawdown > 0.15:  # >15%
                return False, f"Current drawdown {proposal.current_drawdown:.1%} exceeds limit"
        
            # Check 6: Portfolio impact
            if proposal.correlation_exposure > 0.7:
                return False, f"Portfolio correlation {proposal.correlation_exposure:.1%} too high"
        
            # All checks passed
            return True, "All conditions satisfied"
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            raise
    
    def _identify_min_component(self, vector: ConfidenceVector) -> str:
        """Identify which component has minimum confidence"""
        try:
            components = {
                'statistical': vector.statistical,
                'regime': vector.regime,
                'execution': vector.execution,
                'tail_risk': vector.tail_risk,
                'model_stability': vector.model_stability
            }
            return min(components, key=components.get)
        except Exception as e:
            logger.error(f"Error in _identify_min_component: {e}")
            raise


class PositionSizer:
    """Stage 6: Position Sizing (Secondary Intelligence)"""
    
    def calculate_position_size(
        self,
        proposal: TradeProposal,
        confidence_vector: ConfidenceVector,
        base_position_size: float = 1.0
    ) -> float:
        """
        Position size must be:
        - Confidence-weighted
        - Regime-adjusted
        - Correlation-penalized
        - Drawdown-capped
        
        Never size purely on signal strength.
        """
        # Start with base size
        try:
            size = base_position_size
        
            # Confidence weighting (use minimum confidence)
            min_conf = confidence_vector.min_confidence()
            size *= min_conf
        
            # Regime adjustment
            size *= confidence_vector.regime
        
            # Correlation penalty
            correlation_penalty = 1.0 - (proposal.correlation_exposure * 0.5)
            size *= correlation_penalty
        
            # Drawdown cap
            if proposal.current_drawdown > 0.05:  # >5% drawdown
                drawdown_penalty = 1.0 - (proposal.current_drawdown * 2.0)  # Linear reduction
                size *= max(drawdown_penalty, 0.2)  # Minimum 20% of normal size
        
            # Volatility adjustment
            if proposal.volatility > 0.3:
                vol_penalty = 0.3 / proposal.volatility
                size *= vol_penalty
        
            # Ensure positive and reasonable
            size = max(0.1, min(size, 1.0))
        
            return size * proposal.quantity
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise


class AlphaAlgoCoreEngine:
    """
    AlphaAlgo Core - Hostile Capital-Preserving Quantitative Decision Engine
    
    7-Stage Evaluation Pipeline:
    Stage 0: Market Hostility Check
    Stage 1: Claim Graph Construction
    Stage 2: Orthogonal Evaluation
    Stage 3: Adversarial Internal Committee
    Stage 4: Confidence Vector (No Single Scores)
    Stage 5: Decision Gate
    Stage 6: Position Sizing (Secondary Intelligence)
    Stage 7: Post-Trade Self-Fixing (handled externally)
    """
    
    def __init__(
        self,
        required_confidence_threshold: float = 0.6,
        enable_strict_mode: bool = True
    ):
        try:
            self.required_confidence_threshold = required_confidence_threshold
            self.enable_strict_mode = enable_strict_mode
        
            # Initialize components
            self.hostility_detector = MarketHostilityDetector()
            self.claim_constructor = ClaimGraphConstructor()
            self.orthogonal_evaluator = OrthogonalEvaluator()
            self.adversarial_committee = AdversarialCommittee()
            self.confidence_builder = ConfidenceVectorBuilder()
            self.decision_gate = DecisionGate(required_confidence_threshold)
            self.position_sizer = PositionSizer()
        
            # History
            self.decision_history = deque(maxlen=1000)
            self.rejection_reasons = defaultdict(int)
        
            logger.info(f"AlphaAlgo Core Engine initialized (threshold={required_confidence_threshold})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def evaluate_trade(
        self,
        proposal: TradeProposal,
        market_context: Optional[Dict[str, Any]] = None
    ) -> CoreDecision:
        """
        Evaluate a trade proposal through the 7-stage pipeline
        
        Returns:
            CoreDecision with outcome and details
        """
        try:
            start_time = time.time()
        
            # Extract market context
            if market_context is None:
                market_context = {}
        
            recent_performance = market_context.get('recent_performance', [])
            regime_stability = market_context.get('regime_stability', 0.7)
            liquidity_stress = market_context.get('liquidity_stress', 0.2)
            cross_strategy_dispersion = market_context.get('cross_strategy_dispersion', 0.3)
        
            # STAGE 0: Market Hostility Check
            hostility, hostility_reason = self.hostility_detector.evaluate(
                recent_performance=recent_performance,
                regime_stability=regime_stability,
                liquidity_stress=liquidity_stress,
                cross_strategy_dispersion=cross_strategy_dispersion
            )
        
            if hostility in [MarketHostility.HOSTILE, MarketHostility.EXTREME, MarketHostility.LOW_EDGE_DENSITY]:
                logger.warning(f"Market hostile ({hostility.name}): {hostility_reason}")
                decision = CoreDecision(
                    outcome=DecisionOutcome.NO_TRADE_MARKET_HOSTILE,
                    trade_id=proposal.trade_id,
                    dominant_rejection_reason=hostility_reason,
                    market_hostility=hostility
                )
                self.decision_history.append(decision)
                return decision
        
            # STAGE 1: Claim Graph Construction
            claims = self.claim_constructor.construct_claims(proposal)
            logger.debug(f"Constructed {len(claims)} claims for trade {proposal.trade_id}")
        
            # STAGE 2: Orthogonal Evaluation
            claim_results = {}
            for claim in claims:
                passed, confidence, reason = self.orthogonal_evaluator.evaluate_claim(claim, proposal)
                claim_results[claim.claim_type] = (passed, confidence, reason)
                if not passed:
                    logger.debug(f"Claim {claim.claim_type.name} failed: {reason}")
        
            # STAGE 3: Adversarial Internal Committee
            verdicts = await self.adversarial_committee.evaluate(proposal, claims, claim_results)
        
            # Check if Killer rejected
            killer_verdict = next((v for v in verdicts if v.agent == AgentRole.KILLER), None)
            if killer_verdict and not killer_verdict.approved:
                logger.warning(f"Killer rejected trade {proposal.trade_id}: {killer_verdict.reason}")
                decision = CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=proposal.trade_id,
                    dominant_rejection_reason=killer_verdict.reason,
                    killer_verdict=killer_verdict,
                    all_verdicts=verdicts,
                    market_hostility=hostility
                )
                self.decision_history.append(decision)
                self.rejection_reasons[killer_verdict.reason] += 1
                return decision
        
            # STAGE 4: Confidence Vector
            confidence_vector = self.confidence_builder.build_confidence_vector(
                proposal, claim_results
            )
        
            # STAGE 5: Decision Gate
            approved, reason = self.decision_gate.evaluate(
                proposal, claims, claim_results, confidence_vector, verdicts
            )
        
            if not approved:
                # Identify failed claims
                failed_claims = [ct for ct, result in claim_results.items() if not result[0]]
                min_component = self.decision_gate._identify_min_component(confidence_vector)
            
                logger.info(f"Trade {proposal.trade_id} rejected: {reason}")
                decision = CoreDecision(
                    outcome=DecisionOutcome.TRADE_REJECTED,
                    trade_id=proposal.trade_id,
                    failed_claims=failed_claims,
                    min_confidence_component=min_component,
                    dominant_rejection_reason=reason,
                    confidence_vector=confidence_vector,
                    all_verdicts=verdicts,
                    market_hostility=hostility
                )
                self.decision_history.append(decision)
                self.rejection_reasons[reason] += 1
                return decision
        
            # STAGE 6: Position Sizing
            approved_size = self.position_sizer.calculate_position_size(
                proposal, confidence_vector
            )
        
            # APPROVED
            elapsed = time.time() - start_time
            logger.info(f"Trade {proposal.trade_id} APPROVED (size={approved_size:.3f}, time={elapsed:.3f}s)")
        
            decision = CoreDecision(
                outcome=DecisionOutcome.TRADE_APPROVED,
                trade_id=proposal.trade_id,
                approved_position_size=approved_size,
                confidence_vector=confidence_vector,
                all_verdicts=verdicts,
                market_hostility=hostility
            )
            self.decision_history.append(decision)
        
            return decision
        except Exception as e:
            logger.error(f"Error in evaluate_trade: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        try:
            if not self.decision_history:
                return {}
        
            total = len(self.decision_history)
            approved = sum(1 for d in self.decision_history if d.outcome == DecisionOutcome.TRADE_APPROVED)
            rejected = sum(1 for d in self.decision_history if d.outcome == DecisionOutcome.TRADE_REJECTED)
            hostile = sum(1 for d in self.decision_history if d.outcome == DecisionOutcome.NO_TRADE_MARKET_HOSTILE)
        
            return {
                'total_evaluations': total,
                'approved': approved,
                'rejected': rejected,
                'market_hostile': hostile,
                'approval_rate': approved / total if total > 0 else 0.0,
                'rejection_rate': rejected / total if total > 0 else 0.0,
                'top_rejection_reasons': dict(sorted(
                    self.rejection_reasons.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5])
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise


# Factory function
def create_alphaalgo_core(
    required_confidence_threshold: float = 0.6,
    enable_strict_mode: bool = True
) -> AlphaAlgoCoreEngine:
    """Create AlphaAlgo Core Engine instance"""
    return AlphaAlgoCoreEngine(
        required_confidence_threshold=required_confidence_threshold,
        enable_strict_mode=enable_strict_mode
    )
