"""
Layer 3: Adversarial Counter-Analyst

A second system whose job is to break the primary thesis.
Not "collaborate." Attack.

Generates:
- rival explanations
- hidden assumptions
- conditions where the thesis fails
- base-rate objections
- regime mismatch objections
- execution objections
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import logging
import random

from .core_types import (
    Claim, ClaimType, AdversarialChallenge, MarketRegime,
    DecisionRecord, Evidence, EvidenceStatus
)

logger = logging.getLogger(__name__)


@dataclass
class AttackStrategy:
    """Strategy for attacking a claim"""
    name: str
    attack_type: str
    applicable_claim_types: List[ClaimType]
    description: str


class AdversarialCounterAnalyst:
    """
    Generates adversarial challenges to trade theses.
    This system is explicitly designed to attack and find weaknesses.
    """
    
    def __init__(self, attack_depth: int = 3):
        self.attack_depth = attack_depth
        
        # Define attack strategies
        self.strategies = [
            AttackStrategy(
                name="rival_explanation",
                attack_type="rival_explanation",
                applicable_claim_types=[ClaimType.THESIS, ClaimType.INFERRED_CAUSAL_LINK],
                description="Generate alternative explanations for the observed pattern"
            ),
            AttackStrategy(
                name="hidden_assumption",
                attack_type="hidden_assumption",
                applicable_claim_types=[ClaimType.THESIS, ClaimType.ASSUMPTION, ClaimType.PREDICTED_OUTCOME],
                description="Surface unstated assumptions that underpin the claim"
            ),
            AttackStrategy(
                name="failure_condition",
                attack_type="failure_condition",
                applicable_claim_types=[ClaimType.THESIS, ClaimType.PREDICTED_OUTCOME],
                description="Identify specific conditions where the thesis fails"
            ),
            AttackStrategy(
                name="base_rate_objection",
                attack_type="base_rate",
                applicable_claim_types=[ClaimType.PREDICTED_OUTCOME, ClaimType.THESIS],
                description="Challenge using base rate / prior probability"
            ),
            AttackStrategy(
                name="regime_mismatch",
                attack_type="regime_mismatch",
                applicable_claim_types=[ClaimType.THESIS, ClaimType.INFERRED_CAUSAL_LINK],
                description="Attack based on current regime incompatibility"
            ),
            AttackStrategy(
                name="execution_objection",
                attack_type="execution",
                applicable_claim_types=[ClaimType.PREDICTED_OUTCOME, ClaimType.THESIS],
                description="Challenge based on execution feasibility"
            ),
            AttackStrategy(
                name="survivorship_bias",
                attack_type="bias",
                applicable_claim_types=[ClaimType.THESIS, ClaimType.EVIDENCE],
                description="Point out survivorship bias in evidence"
            ),
            AttackStrategy(
                name="overfitting_challenge",
                attack_type="overfitting",
                applicable_claim_types=[ClaimType.INFERRED_CAUSAL_LINK, ClaimType.THESIS],
                description="Challenge as potential overfit to recent data"
            )
        ]
        
    def generate_challenges(
        self,
        claims: List[Claim],
        current_regime: Optional[MarketRegime] = None,
        symbol: str = "UNKNOWN"
    ) -> List[AdversarialChallenge]:
        """
        Generate adversarial challenges for a set of claims.
        
        Args:
            claims: The claims to attack
            current_regime: Current market regime for context
            symbol: Trading symbol
            
        Returns:
            List of challenges
        """
        challenges = []
        
        for claim in claims:
            claim_challenges = self._attack_claim(claim, current_regime, symbol)
            challenges.extend(claim_challenges)
            
        # Sort by severity (highest first)
        challenges.sort(key=lambda c: c.severity, reverse=True)
        
        # Limit to top challenges
        if len(challenges) > self.attack_depth * len(claims):
            challenges = challenges[:self.attack_depth * len(claims)]
            
        logger.info(f"Generated {len(challenges)} adversarial challenges")
        return challenges
    
    def _attack_claim(
        self,
        claim: Claim,
        current_regime: Optional[MarketRegime],
        symbol: str
    ) -> List[AdversarialChallenge]:
        """Generate attacks for a single claim"""
        
        challenges = []
        
        # Find applicable strategies
        applicable = [
            s for s in self.strategies
            if claim.claim_type in s.applicable_claim_types
        ]
        
        # Apply each strategy
        for strategy in applicable:
            challenge = self._execute_attack(strategy, claim, current_regime, symbol)
            if challenge:
                challenges.append(challenge)
                
        return challenges
    
    def _execute_attack(
        self,
        strategy: AttackStrategy,
        claim: Claim,
        current_regime: Optional[MarketRegime],
        symbol: str
    ) -> Optional[AdversarialChallenge]:
        """Execute a specific attack strategy against a claim"""
        
        if strategy.attack_type == "rival_explanation":
            return self._generate_rival_explanation(claim, symbol)
        elif strategy.attack_type == "hidden_assumption":
            return self._generate_hidden_assumption_challenge(claim, symbol)
        elif strategy.attack_type == "failure_condition":
            return self._generate_failure_condition(claim, symbol)
        elif strategy.attack_type == "base_rate":
            return self._generate_base_rate_objection(claim, symbol)
        elif strategy.attack_type == "regime_mismatch":
            return self._generate_regime_mismatch(claim, current_regime, symbol)
        elif strategy.attack_type == "execution":
            return self._generate_execution_objection(claim, symbol)
        elif strategy.attack_type == "bias":
            return self._generate_bias_challenge(claim, symbol)
        elif strategy.attack_type == "overfitting":
            return self._generate_overfitting_challenge(claim, symbol)
            
        return None
    
    def _generate_rival_explanation(
        self,
        claim: Claim,
        symbol: str
    ) -> AdversarialChallenge:
        """Generate a rival explanation for the observed pattern"""
        
        rival_explanations = [
            f"The pattern in {symbol} could be random noise rather than signal",
            f"This could be a delayed reaction to news already priced in",
            f"The observed movement may be due to index rebalancing flows",
            f"This pattern matches seasonal effects unrelated to the thesis",
            f"The signal could be an artifact of low liquidity conditions",
            f"The thesis confuses correlation with causation"
        ]
        
        content = random.choice(rival_explanations)
        
        return AdversarialChallenge(
            id="",
            target_claim_id=claim.id,
            challenge_type="rival_explanation",
            content=content,
            severity=0.6,
            supporting_arguments=[
                "Alternative explanations often fit the same data",
                "Post-hoc rationalization is common in pattern recognition"
            ]
        )
    
    def _generate_hidden_assumption_challenge(
        self,
        claim: Claim,
        symbol: str
    ) -> AdversarialChallenge:
        """Surface hidden assumptions"""
        
        hidden_assumptions = [
            f"Assumes {symbol} liquidity will remain constant through execution",
            f"Assumes no major market-moving news during position holding",
            f"Assumes historical correlations will persist",
            f"Assumes the signal is not already known to other participants",
            f"Assumes execution costs won't exceed expected alpha",
            f"Assumes the model hasn't degraded since training"
        ]
        
        content = random.choice(hidden_assumptions)
        
        return AdversarialChallenge(
            id="",
            target_claim_id=claim.id,
            challenge_type="hidden_assumption",
            content=content,
            severity=0.5,
            supporting_arguments=[
                "Hidden assumptions are not validated",
                "Markets change, breaking old assumptions"
            ]
        )
    
    def _generate_failure_condition(
        self,
        claim: Claim,
        symbol: str
    ) -> AdversarialChallenge:
        """Identify conditions where the thesis fails"""
        
        failure_conditions = [
            f"Thesis fails if {symbol} volume drops below 50% of average",
            f"Thesis fails if VIX spikes above 30 during position",
            f"Thesis fails if earnings surprise exceeds 2 standard deviations",
            f"Thesis fails if sector rotation accelerates",
            f"Thesis fails if Fed makes unexpected announcement",
            f"Thesis fails if {symbol} breaks key technical level"
        ]
        
        content = random.choice(failure_conditions)
        
        return AdversarialChallenge(
            id="",
            target_claim_id=claim.id,
            challenge_type="failure_condition",
            content=content,
            severity=0.7,
            supporting_arguments=[
                "Clear failure conditions enable risk management",
                "Most theses have specific conditions where they break"
            ]
        )
    
    def _generate_base_rate_objection(
        self,
        claim: Claim,
        symbol: str
    ) -> AdversarialChallenge:
        """Challenge using base rate information"""
        
        base_rates = [
            f"Base rate for similar predictions: ~52% accuracy (barely better than coin flip)",
            f"Historical success rate of {claim.source} in this regime: <45%",
            f"Base rate of profitable trades in this asset class: 48%",
            f"Mean reversion occurs 65% of the time after similar moves",
            f"Momentum strategies fail 40% of months in volatile conditions"
        ]
        
        content = random.choice(base_rates)
        
        return AdversarialChallenge(
            id="",
            target_claim_id=claim.id,
            challenge_type="base_rate",
            content=content,
            severity=0.65,
            supporting_arguments=[
                "Base rates provide crucial context",
                "Ignoring base rates leads to overconfidence"
            ]
        )
    
    def _generate_regime_mismatch(
        self,
        claim: Claim,
        current_regime: Optional[MarketRegime],
        symbol: str
    ) -> AdversarialChallenge:
        """Challenge based on regime incompatibility"""
        
        if not current_regime:
            return AdversarialChallenge(
                id="",
                target_claim_id=claim.id,
                challenge_type="regime_mismatch",
                content=f"No regime analysis provided - thesis may be regime-inappropriate",
                severity=0.8,
                supporting_arguments=[
                    "Strategies often fail outside their designed regimes",
                    "Regime mismatch is a common cause of strategy failure"
                ]
            )
            
        regime_concerns = []
        
        if current_regime.volatility_state == "extreme":
            regime_concerns.append(f"Current extreme volatility invalidates mean-reversion thesis for {symbol}")
        if current_regime.liquidity_state in ["constrained", "scarce"]:
            regime_concerns.append(f"Poor liquidity in {symbol} makes execution alpha doubtful")
        if current_regime.order_flow_toxicity == "toxic":
            regime_concerns.append(f"Toxic flow conditions suggest informed trading against this position")
        if current_regime.macro_event_density == "elevated":
            regime_concerns.append(f"Elevated macro event density increases tail risk")
            
        if regime_concerns:
            content = random.choice(regime_concerns)
        else:
            content = f"Regime analysis incomplete - may have hidden mismatches with {symbol} thesis"
            
        return AdversarialChallenge(
            id="",
            target_claim_id=claim.id,
            challenge_type="regime_mismatch",
            content=content,
            severity=0.75 if regime_concerns else 0.5,
            supporting_arguments=[
                "Strategies have regime-dependent performance",
                "Current regime may not match historical training data"
            ]
        )
    
    def _generate_execution_objection(
        self,
        claim: Claim,
        symbol: str
    ) -> AdversarialChallenge:
        """Challenge based on execution feasibility"""
        
        execution_issues = [
            f"Expected slippage may exceed expected alpha for {symbol}",
            f"Position size may be too large for available liquidity",
            f"Partial fills could leave incomplete, unhedged exposure",
            f"Market impact may move price against position during entry",
            f"Execution delay may invalidate signal timing"
        ]
        
        content = random.choice(execution_issues)
        
        return AdversarialChallenge(
            id="",
            target_claim_id=claim.id,
            challenge_type="execution",
            content=content,
            severity=0.6,
            supporting_arguments=[
                "Paper alpha often disappears in real execution",
                "Transaction costs are frequently underestimated"
            ]
        )
    
    def _generate_bias_challenge(
        self,
        claim: Claim,
        symbol: str
    ) -> AdversarialChallenge:
        """Point out potential biases"""
        
        bias_challenges = [
            f"Evidence may suffer from survivorship bias - failed similar trades not counted",
            f"Recent winners overrepresented in evidence due to recency bias",
            f"Confirmation bias: only supporting evidence collected",
            f"Agency bias: {claim.source} incentivized to generate signals regardless of quality"
        ]
        
        content = random.choice(bias_challenges)
        
        return AdversarialChallenge(
            id="",
            target_claim_id=claim.id,
            challenge_type="bias",
            content=content,
            severity=0.55,
            supporting_arguments=[
                "Cognitive biases systematically distort judgment",
                "Financial markets amplify behavioral biases"
            ]
        )
    
    def _generate_overfitting_challenge(
        self,
        claim: Claim,
        symbol: str
    ) -> AdversarialChallenge:
        """Challenge as potential overfit"""
        
        overfitting_challenges = [
            f"Pattern may be overfit to recent {symbol} price action",
            f"Signal complexity suggests overfitting risk",
            f"High confidence with limited sample size indicates overfit",
            f"Rule may not generalize out-of-sample"
        ]
        
        content = random.choice(overfitting_challenges)
        
        return AdversarialChallenge(
            id="",
            target_claim_id=claim.id,
            challenge_type="overfitting",
            content=content,
            severity=0.6,
            supporting_arguments=[
                "Overfit strategies fail in live trading",
                "Complex rules often capture noise, not signal"
            ]
        )
    
    def evaluate_challenge_strength(
        self,
        challenge: AdversarialChallenge,
        claims: List[Claim],
        evidence: List[Evidence]
    ) -> float:
        """
        Evaluate how strong a challenge is based on available evidence.
        
        Returns:
            Score from 0 to 1, higher means challenge is more valid
        """
        base_severity = challenge.severity
        
        # Adjust based on evidence that addresses the challenge
        target_claim = next(
            (c for c in claims if c.id == challenge.target_claim_id),
            None
        )
        
        if not target_claim:
            return base_severity
            
        # If claim has strong evidence addressing this challenge type, reduce severity
        counter_evidence = [
            e for e in evidence
            if e.claim_id == target_claim.id and e.strength > 0.7
        ]
        
        if counter_evidence:
            # Reduce severity by up to 30% based on counter-evidence
            reduction = min(0.3, len(counter_evidence) * 0.1)
            return max(0, base_severity - reduction)
            
        return base_severity
    
    def generate_counter_arguments(
        self,
        challenge: AdversarialChallenge,
        claims: List[Claim]
    ) -> List[str]:
        """Generate possible counter-arguments to a challenge"""
        
        counter_arguments = []
        
        target_claim = next(
            (c for c in claims if c.id == challenge.target_claim_id),
            None
        )
        
        if not target_claim:
            return counter_arguments
            
        if challenge.challenge_type == "rival_explanation":
            counter_arguments.append(
                f"The thesis has survived multiple out-of-sample tests"
            )
            counter_arguments.append(
                f"Alternative explanations have been systematically ruled out"
            )
        elif challenge.challenge_type == "hidden_assumption":
            counter_arguments.append(
                f"Assumptions have been explicitly validated in current conditions"
            )
        elif challenge.challenge_type == "failure_condition":
            counter_arguments.append(
                f"Failure conditions are monitored and position sized accordingly"
            )
        elif challenge.challenge_type == "base_rate":
            counter_arguments.append(
                f"This specific setup has demonstrated edge over base rate historically"
            )
        elif challenge.challenge_type == "regime_mismatch":
            counter_arguments.append(
                f"Strategy has been validated in similar regime conditions"
            )
        elif challenge.challenge_type == "execution":
            counter_arguments.append(
                f"Execution costs have been conservatively estimated"
            )
            
        return counter_arguments


class CognitiveBiasDetector:
    """
    Cognitive Bias Detector (for AI)
    
    Your AI will develop biases.
    
    Detect patterns like:
    - overtrading after wins
    - avoiding trades after losses
    - overconfidence in certain signals
    - regime anchoring
    
    Prevents AI behaving like a bad human trader.
    """
    
    def __init__(self, lookback_window: int = 50):
        self.lookback_window = lookback_window
        self.decision_history: List[Dict] = []
        self.bias_alerts: List[Dict] = []
        
    def record_decision(
        self,
        decision: str,
        confidence: float,
        outcome: Optional[float],
        signal_type: str,
        regime: str,
        timestamp: Optional[datetime] = None
    ):
        """Record a trading decision for bias analysis."""
        self.decision_history.append({
            'decision': decision,
            'confidence': confidence,
            'outcome': outcome,
            'signal_type': signal_type,
            'regime': regime,
            'timestamp': timestamp or datetime.now()
        })
        
        # Keep only recent history
        if len(self.decision_history) > self.lookback_window * 2:
            self.decision_history = self.decision_history[-self.lookback_window:]
    
    def detect_all_biases(self) -> Dict[str, Any]:
        """Detect all cognitive biases in recent trading behavior."""
        if len(self.decision_history) < 20:
            return {'status': 'insufficient_data'}
        
        recent = self.decision_history[-self.lookback_window:]
        
        biases = {
            'overtrading_after_wins': self._detect_revenge_trading(recent),
            'loss_avoidance': self._detect_loss_avoidance(recent),
            'overconfidence_drift': self._detect_overconfidence_drift(recent),
            'regime_anchoring': self._detect_regime_anchoring(recent),
            'signal_favoritism': self._detect_signal_favoritism(recent),
            'recency_bias': self._detect_recency_bias(recent)
        }
        
        # Overall bias score
        bias_scores = [b['severity'] for b in biases.values() if isinstance(b, dict)]
        overall_bias = np.mean(bias_scores) if bias_scores else 0
        
        return {
            'overall_bias_score': overall_bias,
            'bias_detected': overall_bias > 0.5,
            'individual_biases': biases,
            'recommendation': 'Reduce trading size' if overall_bias > 0.6 else 'Continue monitoring',
            'sample_size': len(recent)
        }
    
    def _detect_revenge_trading(self, history: List[Dict]) -> Dict[str, Any]:
        """Detect overtrading after wins (revenge trading pattern)."""
        if len(history) < 10:
            return {'status': 'insufficient_data'}
        
        # Look for pattern: win -> increased activity
        trade_counts_after_win = []
        
        for i in range(1, len(history)):
            prev_outcome = history[i-1].get('outcome')
            if prev_outcome and prev_outcome > 0:  # Previous was a win
                # Count trades in next 3 decisions
                trades_in_window = sum(
                    1 for j in range(i, min(i+3, len(history)))
                    if history[j]['decision'] == 'TRADE'
                )
                trade_counts_after_win.append(trades_in_window)
        
        if not trade_counts_after_win:
            return {'detected': False, 'severity': 0}
        
        avg_trades_after_win = np.mean(trade_counts_after_win)
        
        # Compare to baseline (trades after losses)
        trades_after_loss = []
        for i in range(1, len(history)):
            prev_outcome = history[i-1].get('outcome')
            if prev_outcome and prev_outcome < 0:
                trades_in_window = sum(
                    1 for j in range(i, min(i+3, len(history)))
                    if history[j]['decision'] == 'TRADE'
                )
                trades_after_loss.append(trades_in_window)
        
        avg_after_loss = np.mean(trades_after_loss) if trades_after_loss else 1
        
        ratio = avg_trades_after_win / max(avg_after_loss, 0.5)
        
        return {
            'detected': ratio > 1.5,
            'severity': min(1.0, (ratio - 1) / 2) if ratio > 1 else 0,
            'trades_after_win': avg_trades_after_win,
            'trades_after_loss': avg_after_loss,
            'ratio': ratio,
            'description': 'Trading more aggressively after wins'
        }
    
    def _detect_loss_avoidance(self, history: List[Dict]) -> Dict[str, Any]:
        """Detect avoiding trades after losses."""
        if len(history) < 10:
            return {'status': 'insufficient_data'}
        
        # Look for pattern: loss -> reduced trading
        win_rates_after_loss = []
        
        for i in range(1, len(history) - 3):
            prev_outcome = history[i-1].get('outcome')
            if prev_outcome and prev_outcome < 0:  # Previous was a loss
                # Check next 5 decisions
                next_decisions = history[i:min(i+5, len(history))]
                trade_rate = sum(1 for d in next_decisions if d['decision'] == 'TRADE') / len(next_decisions)
                win_rates_after_loss.append(trade_rate)
        
        if not win_rates_after_loss:
            return {'detected': False, 'severity': 0}
        
        avg_trade_rate_after_loss = np.mean(win_rates_after_loss)
        
        # Compare to baseline
        baseline_trade_rate = sum(1 for d in history if d['decision'] == 'TRADE') / len(history)
        
        severity = max(0, baseline_trade_rate - avg_trade_rate_after_loss) / max(baseline_trade_rate, 0.1)
        
        return {
            'detected': severity > 0.3,
            'severity': severity,
            'trade_rate_after_loss': avg_trade_rate_after_loss,
            'baseline_trade_rate': baseline_trade_rate,
            'description': 'Reduced trading activity after losses'
        }
    
    def _detect_overconfidence_drift(self, history: List[Dict]) -> Dict[str, Any]:
        """Detect confidence increasing without performance improvement."""
        if len(history) < 30:
            return {'status': 'insufficient_data'}
        
        # Split into first and second half
        mid = len(history) // 2
        first_half = history[:mid]
        second_half = history[mid:]
        
        first_confidence = np.mean([d['confidence'] for d in first_half])
        second_confidence = np.mean([d['confidence'] for d in second_half])
        
        # Get outcomes with values
        first_outcomes = [d['outcome'] for d in first_half if d.get('outcome') is not None]
        second_outcomes = [d['outcome'] for d in second_half if d.get('outcome') is not None]
        
        first_performance = np.mean(first_outcomes) if first_outcomes else 0
        second_performance = np.mean(second_outcomes) if second_outcomes else 0
        
        # Check if confidence increased but performance didn't
        confidence_increase = second_confidence - first_confidence
        performance_change = second_performance - first_performance
        
        overconfidence = confidence_increase > 0.1 and performance_change < 0.01
        
        return {
            'detected': overconfidence,
            'severity': confidence_increase if overconfidence else 0,
            'confidence_trend': confidence_increase,
            'performance_trend': performance_change,
            'description': 'Confidence increasing without performance improvement'
        }
    
    def _detect_regime_anchoring(self, history: List[Dict]) -> Dict[str, Any]:
        """Detect sticking to old regime assumptions."""
        if len(history) < 20:
            return {'status': 'insufficient_data'}
        
        # Count regime transitions
        regime_changes = sum(
            1 for i in range(1, len(history))
            if history[i]['regime'] != history[i-1]['regime']
        )
        
        # Count performance after regime changes
        performance_after_change = []
        for i in range(1, len(history)):
            if history[i]['regime'] != history[i-1]['regime']:
                if history[i].get('outcome') is not None:
                    performance_after_change.append(history[i]['outcome'])
        
        if not performance_after_change:
            return {'detected': False, 'severity': 0}
        
        avg_after_change = np.mean(performance_after_change)
        
        # Poor performance after regime changes suggests anchoring
        anchoring = avg_after_change < -0.01 and regime_changes > 3
        
        return {
            'detected': anchoring,
            'severity': abs(avg_after_change) * 10 if anchoring else 0,
            'regime_changes_detected': regime_changes,
            'avg_performance_after_change': avg_after_change,
            'description': 'Poor adaptation to regime changes'
        }
    
    def _detect_signal_favoritism(self, history: List[Dict]) -> Dict[str, Any]:
        """Detect over-reliance on specific signal types."""
        if len(history) < 20:
            return {'status': 'insufficient_data'}
        
        signal_counts = {}
        signal_performance = defaultdict(list)
        
        for d in history:
            sig_type = d['signal_type']
            signal_counts[sig_type] = signal_counts.get(sig_type, 0) + 1
            if d.get('outcome') is not None:
                signal_performance[sig_type].append(d['outcome'])
        
        if len(signal_counts) < 2:
            return {'detected': False, 'severity': 0}
        
        # Find most used signal
        most_used = max(signal_counts.items(), key=lambda x: x[1])
        most_used_ratio = most_used[1] / len(history)
        
        # Check if it's overused despite poor performance
        most_used_perf = np.mean(signal_performance[most_used[0]]) if most_used[0] in signal_performance else 0
        
        favoritism = most_used_ratio > 0.6 and most_used_perf < 0.01
        
        return {
            'detected': favoritism,
            'severity': (most_used_ratio - 0.5) * 2 if favoritism else 0,
            'most_used_signal': most_used[0],
            'usage_ratio': most_used_ratio,
            'performance': most_used_perf,
            'description': f'Over-reliance on {most_used[0]} despite mediocre performance'
        }
    
    def _detect_recency_bias(self, history: List[Dict]) -> Dict[str, Any]:
        """Detect overweighting recent events."""
        if len(history) < 20:
            return {'status': 'insufficient_data'}
        
        # Compare recent confidence to overall
        recent = history[-10:]
        older = history[:-10] if len(history) > 20 else history[:10]
        
        recent_conf = np.mean([d['confidence'] for d in recent])
        older_conf = np.mean([d['confidence'] for d in older])
        
        recent_outcomes = [d['outcome'] for d in recent if d.get('outcome') is not None]
        older_outcomes = [d['outcome'] for d in older if d.get('outcome') is not None]
        
        recent_perf = np.mean(recent_outcomes) if recent_outcomes else 0
        older_perf = np.mean(older_outcomes) if older_outcomes else 0
        
        # High confidence after recent wins = recency bias
        recency_effect = (recent_conf - older_conf) * (recent_perf - older_perf)
        
        bias_detected = recency_effect > 0.05
        
        return {
            'detected': bias_detected,
            'severity': recency_effect if bias_detected else 0,
            'recent_confidence': recent_conf,
            'older_confidence': older_conf,
            'recent_performance': recent_perf,
            'description': 'Confidence excessively influenced by recent results'
        }
    
    def get_bias_mitigation_recommendations(self) -> List[str]:
        """Get recommendations for mitigating detected biases."""
        bias_report = self.detect_all_biases()
        recommendations = []
        
        if bias_report.get('bias_detected'):
            biases = bias_report.get('individual_biases', {})
            
            if biases.get('overtrading_after_wins', {}).get('detected'):
                recommendations.append("Enforce cooling-off period after wins")
                recommendations.append("Reduce position size after consecutive wins")
            
            if biases.get('loss_avoidance', {}).get('detected'):
                recommendations.append("Force minimum trading rate regardless of recent losses")
                recommendations.append("Review stop-loss levels - may be too tight")
            
            if biases.get('overconfidence_drift', {}).get('detected'):
                recommendations.append("Recalibrate confidence metrics")
                recommendations.append("Increase skepticism threshold")
            
            if biases.get('regime_anchoring', {}).get('detected'):
                recommendations.append("Implement mandatory regime re-evaluation after changes")
                recommendations.append("Reduce position size in new regimes until validated")
            
            if biases.get('signal_favoritism', {}).get('detected'):
                recommendations.append("Enforce signal diversification rules")
                recommendations.append("Review and potentially disable overused signals")
            
            if biases.get('recency_bias', {}).get('detected'):
                recommendations.append("Use longer lookback periods for performance evaluation")
                recommendations.append("Implement decay factor for recent outcomes")
        
        return recommendations if recommendations else ['No significant biases detected - continue monitoring']
