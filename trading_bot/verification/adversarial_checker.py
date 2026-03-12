"""
Adversarial Checker - Self-Questioning and Devil's Advocate System

Implements adversarial self-questioning to challenge the bot's own conclusions
and identify weaknesses, blind spots, and potential errors.

ADVERSARIAL TECHNIQUES:
1. Devil's Advocate - Argue against the decision
2. Pre-Mortem Analysis - Imagine the trade failed, explain why
3. Red Team Thinking - Attack the decision from all angles
4. Assumption Challenging - Question every assumption
5. Contrarian Analysis - What would a contrarian do?
6. Black Swan Hunting - What rare events could invalidate this?
7. Cognitive Bias Detection - Check for common biases

Author: AlphaAlgo Team
Date: 2026-01-28
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import random

logger = logging.getLogger(__name__)


class AdversarialTechnique(Enum):
    """Adversarial analysis techniques"""
    DEVILS_ADVOCATE = "devils_advocate"
    PRE_MORTEM = "pre_mortem"
    RED_TEAM = "red_team"
    ASSUMPTION_CHALLENGE = "assumption_challenge"
    CONTRARIAN = "contrarian"
    BLACK_SWAN = "black_swan"
    BIAS_DETECTION = "bias_detection"


class CognitiveBias(Enum):
    """Common cognitive biases in trading"""
    CONFIRMATION_BIAS = "confirmation_bias"
    RECENCY_BIAS = "recency_bias"
    ANCHORING = "anchoring"
    OVERCONFIDENCE = "overconfidence"
    LOSS_AVERSION = "loss_aversion"
    HINDSIGHT_BIAS = "hindsight_bias"
    GAMBLER_FALLACY = "gambler_fallacy"
    AVAILABILITY_HEURISTIC = "availability_heuristic"
    SUNK_COST_FALLACY = "sunk_cost_fallacy"
    HERDING = "herding"


class ChallengeLevel(Enum):
    """Level of challenge severity"""
    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"


@dataclass
class Challenge:
    """A single challenge to the decision"""
    technique: AdversarialTechnique
    question: str
    concern: str
    level: ChallengeLevel
    mitigation: Optional[str] = None
    addressed: bool = False


@dataclass
class BiasAlert:
    """Alert for detected cognitive bias"""
    bias_type: CognitiveBias
    evidence: str
    severity: float
    recommendation: str


@dataclass
class AdversarialResult:
    """Result of adversarial analysis"""
    decision_id: str
    challenges: List[Challenge]
    biases_detected: List[BiasAlert]
    overall_robustness: float  # 0.0 to 1.0
    critical_weaknesses: List[str]
    recommendations: List[str]
    should_proceed: bool
    confidence_adjustment: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'challenge_count': len(self.challenges),
            'critical_challenges': sum(1 for c in self.challenges if c.level == ChallengeLevel.CRITICAL),
            'biases_detected': len(self.biases_detected),
            'overall_robustness': self.overall_robustness,
            'should_proceed': self.should_proceed,
            'confidence_adjustment': self.confidence_adjustment,
            'timestamp': self.timestamp.isoformat()
        }


class AdversarialChecker:
    """
    Adversarial self-questioning system that challenges the bot's decisions.
    
    Implements multiple adversarial techniques to identify weaknesses
    and potential errors before they cause losses.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Thresholds
            self.min_robustness = self.config.get('min_robustness', 0.6)
            self.max_critical_challenges = self.config.get('max_critical_challenges', 1)
        
            # Question banks for each technique
            self._init_question_banks()
        
            # Bias detection patterns
            self._init_bias_patterns()
        
            # Analysis history
            self.analysis_history: List[AdversarialResult] = []
        
            logger.info("AdversarialChecker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_question_banks(self):
        """Initialize question banks for each technique"""
        try:
            self.question_banks = {
                AdversarialTechnique.DEVILS_ADVOCATE: [
                    ("Why is this trade wrong?", "Consider all reasons this could fail"),
                    ("What would make you NOT take this trade?", "Identify deal-breakers"),
                    ("If you had to argue against this, what would you say?", "Build the counter-case"),
                    ("What are you missing?", "Identify blind spots"),
                    ("Why would smart money take the opposite position?", "Consider institutional view"),
                ],
                AdversarialTechnique.PRE_MORTEM: [
                    ("It's 1 week later and this trade lost money. Why?", "Imagine failure and explain"),
                    ("What went wrong?", "List potential failure modes"),
                    ("What warning signs did you ignore?", "Identify overlooked signals"),
                    ("What assumption was wrong?", "Find the flawed premise"),
                    ("What external event caused the loss?", "Consider exogenous risks"),
                ],
                AdversarialTechnique.RED_TEAM: [
                    ("How would a market maker exploit this trade?", "Consider adversarial actors"),
                    ("What if this is a trap?", "Consider manipulation"),
                    ("How could you be fooled here?", "Identify deception vectors"),
                    ("What information asymmetry exists?", "Consider who knows more"),
                    ("Who benefits if you lose?", "Identify counterparties"),
                ],
                AdversarialTechnique.ASSUMPTION_CHALLENGE: [
                    ("What are you assuming about the market?", "List all assumptions"),
                    ("What if volatility doubles?", "Stress test assumptions"),
                    ("What if liquidity dries up?", "Consider liquidity risk"),
                    ("What if correlations break?", "Consider regime change"),
                    ("What if your data is wrong?", "Consider data quality"),
                ],
                AdversarialTechnique.CONTRARIAN: [
                    ("What would a contrarian do here?", "Consider opposite view"),
                    ("Is everyone else doing this?", "Check for crowded trade"),
                    ("What's the consensus and why is it wrong?", "Challenge consensus"),
                    ("When has the crowd been wrong before?", "Historical contrarian wins"),
                    ("What's the pain trade?", "Consider max pain scenario"),
                ],
                AdversarialTechnique.BLACK_SWAN: [
                    ("What rare event could destroy this trade?", "Identify tail risks"),
                    ("What if there's a flash crash?", "Consider extreme moves"),
                    ("What if a major player defaults?", "Consider systemic risk"),
                    ("What geopolitical event could impact this?", "Consider macro risks"),
                    ("What if the exchange goes down?", "Consider operational risk"),
                ],
                AdversarialTechnique.BIAS_DETECTION: [
                    ("Are you seeing what you want to see?", "Check confirmation bias"),
                    ("Are you anchored to a price level?", "Check anchoring"),
                    ("Are you overweighting recent events?", "Check recency bias"),
                    ("Are you too confident?", "Check overconfidence"),
                    ("Are you following the crowd?", "Check herding"),
                ],
            }
        except Exception as e:
            logger.error(f"Error in _init_question_banks: {e}")
            raise
    
    def _init_bias_patterns(self):
        """Initialize patterns for detecting cognitive biases"""
        try:
            self.bias_patterns = {
                CognitiveBias.CONFIRMATION_BIAS: {
                    'indicators': ['only bullish', 'only bearish', 'all indicators agree', 'perfect setup'],
                    'description': 'Seeking only confirming evidence',
                },
                CognitiveBias.RECENCY_BIAS: {
                    'indicators': ['just happened', 'recent', 'last few', 'yesterday'],
                    'description': 'Overweighting recent events',
                },
                CognitiveBias.ANCHORING: {
                    'indicators': ['previous high', 'previous low', 'round number', 'psychological level'],
                    'description': 'Fixating on specific price levels',
                },
                CognitiveBias.OVERCONFIDENCE: {
                    'indicators': ['certain', 'guaranteed', 'definitely', 'no doubt', 'sure thing'],
                    'description': 'Excessive certainty in predictions',
                },
                CognitiveBias.LOSS_AVERSION: {
                    'indicators': ['can\'t lose', 'recover losses', 'make back', 'revenge trade'],
                    'description': 'Irrational fear of losses',
                },
                CognitiveBias.GAMBLER_FALLACY: {
                    'indicators': ['due for', 'overdue', 'must reverse', 'can\'t keep going'],
                    'description': 'Believing past events affect future probabilities',
                },
                CognitiveBias.AVAILABILITY_HEURISTIC: {
                    'indicators': ['remember when', 'last time', 'famous example', 'everyone knows'],
                    'description': 'Overweighting easily recalled examples',
                },
                CognitiveBias.HERDING: {
                    'indicators': ['everyone is', 'consensus', 'popular', 'trending', 'viral'],
                    'description': 'Following the crowd without independent analysis',
                },
            }
        except Exception as e:
            logger.error(f"Error in _init_bias_patterns: {e}")
            raise
    
    def analyze(
        self,
        decision: Dict[str, Any],
        techniques: Optional[List[AdversarialTechnique]] = None
    ) -> AdversarialResult:
        """
        Perform adversarial analysis on a decision.
        
        Args:
            decision: The decision to analyze
            techniques: Specific techniques to use (all if None)
            
        Returns:
            AdversarialResult with challenges and recommendations
        """
        try:
            decision_id = decision.get('id', str(hash(str(decision)))[:8])
        
            if techniques is None:
                techniques = list(AdversarialTechnique)
        
            # Collect challenges from each technique
            all_challenges: List[Challenge] = []
        
            for technique in techniques:
                challenges = self._apply_technique(technique, decision)
                all_challenges.extend(challenges)
        
            # Detect cognitive biases
            biases = self._detect_biases(decision)
        
            # Calculate overall robustness
            robustness = self._calculate_robustness(all_challenges, biases)
        
            # Identify critical weaknesses
            critical_weaknesses = [
                c.concern for c in all_challenges 
                if c.level == ChallengeLevel.CRITICAL
            ]
        
            # Generate recommendations
            recommendations = self._generate_recommendations(all_challenges, biases)
        
            # Determine if should proceed
            critical_count = sum(1 for c in all_challenges if c.level == ChallengeLevel.CRITICAL)
            should_proceed = (
                robustness >= self.min_robustness and 
                critical_count <= self.max_critical_challenges
            )
        
            # Calculate confidence adjustment
            confidence_adjustment = self._calculate_confidence_adjustment(robustness, critical_count)
        
            result = AdversarialResult(
                decision_id=decision_id,
                challenges=all_challenges,
                biases_detected=biases,
                overall_robustness=robustness,
                critical_weaknesses=critical_weaknesses,
                recommendations=recommendations,
                should_proceed=should_proceed,
                confidence_adjustment=confidence_adjustment
            )
        
            self.analysis_history.append(result)
        
            logger.info(
                f"Adversarial analysis for {decision_id}: "
                f"robustness={robustness:.2f}, challenges={len(all_challenges)}, "
                f"proceed={should_proceed}"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _apply_technique(
        self,
        technique: AdversarialTechnique,
        decision: Dict[str, Any]
    ) -> List[Challenge]:
        """Apply a specific adversarial technique"""
        try:
            challenges = []
            questions = self.question_banks.get(technique, [])
        
            # Select relevant questions based on decision content
            for question, concern_template in questions:
                challenge = self._evaluate_question(technique, question, concern_template, decision)
                if challenge:
                    challenges.append(challenge)
        
            return challenges
        except Exception as e:
            logger.error(f"Error in _apply_technique: {e}")
            raise
    
    def _evaluate_question(
        self,
        technique: AdversarialTechnique,
        question: str,
        concern_template: str,
        decision: Dict[str, Any]
    ) -> Optional[Challenge]:
        """Evaluate a specific adversarial question"""
        
        try:
            reasoning = decision.get('reasoning', '') or decision.get('justification', '')
            confidence = decision.get('confidence', 0.5)
            direction = decision.get('direction', 'UNKNOWN')
        
            # Technique-specific evaluation
            if technique == AdversarialTechnique.DEVILS_ADVOCATE:
                return self._devils_advocate_check(question, concern_template, decision)
        
            elif technique == AdversarialTechnique.PRE_MORTEM:
                return self._pre_mortem_check(question, concern_template, decision)
        
            elif technique == AdversarialTechnique.RED_TEAM:
                return self._red_team_check(question, concern_template, decision)
        
            elif technique == AdversarialTechnique.ASSUMPTION_CHALLENGE:
                return self._assumption_check(question, concern_template, decision)
        
            elif technique == AdversarialTechnique.CONTRARIAN:
                return self._contrarian_check(question, concern_template, decision)
        
            elif technique == AdversarialTechnique.BLACK_SWAN:
                return self._black_swan_check(question, concern_template, decision)
        
            elif technique == AdversarialTechnique.BIAS_DETECTION:
                return self._bias_check(question, concern_template, decision)
        
            return None
        except Exception as e:
            logger.error(f"Error in _evaluate_question: {e}")
            raise
    
    def _devils_advocate_check(
        self,
        question: str,
        concern_template: str,
        decision: Dict[str, Any]
    ) -> Optional[Challenge]:
        """Devil's advocate analysis"""
        try:
            reasoning = decision.get('reasoning', '')
        
            # Check if reasoning considers counter-arguments
            counter_words = ['however', 'but', 'although', 'despite', 'risk', 'concern', 'warning']
            has_counter = any(word in reasoning.lower() for word in counter_words)
        
            if not has_counter and 'counter' not in reasoning.lower():
                return Challenge(
                    technique=AdversarialTechnique.DEVILS_ADVOCATE,
                    question=question,
                    concern="No counter-arguments considered in reasoning",
                    level=ChallengeLevel.MODERATE,
                    mitigation="Add explicit consideration of opposing view"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _devils_advocate_check: {e}")
            raise
    
    def _pre_mortem_check(
        self,
        question: str,
        concern_template: str,
        decision: Dict[str, Any]
    ) -> Optional[Challenge]:
        """Pre-mortem analysis"""
        try:
            stop_loss = decision.get('stop_loss')
            take_profit = decision.get('take_profit')
        
            # Check if failure scenarios are considered
            if not stop_loss:
                return Challenge(
                    technique=AdversarialTechnique.PRE_MORTEM,
                    question=question,
                    concern="No stop-loss defined - unlimited loss potential",
                    level=ChallengeLevel.CRITICAL,
                    mitigation="Define explicit stop-loss level"
                )
        
            # Check risk/reward
            if stop_loss and take_profit:
                current_price = decision.get('price') or decision.get('current_price', 0)
                if current_price > 0:
                    risk = abs(current_price - stop_loss)
                    reward = abs(take_profit - current_price)
                    rr_ratio = reward / risk if risk > 0 else 0
                
                    if rr_ratio < 1.0:
                        return Challenge(
                            technique=AdversarialTechnique.PRE_MORTEM,
                            question="What if R:R is negative?",
                            concern=f"Risk/Reward ratio is {rr_ratio:.2f} (< 1.0)",
                            level=ChallengeLevel.SIGNIFICANT,
                            mitigation="Adjust TP/SL for positive expectancy"
                        )
        
            return None
        except Exception as e:
            logger.error(f"Error in _pre_mortem_check: {e}")
            raise
    
    def _red_team_check(
        self,
        question: str,
        concern_template: str,
        decision: Dict[str, Any]
    ) -> Optional[Challenge]:
        """Red team analysis"""
        try:
            volume = decision.get('volume')
            spread = decision.get('spread')
        
            # Check for manipulation risk
            if volume and volume < 1000:
                return Challenge(
                    technique=AdversarialTechnique.RED_TEAM,
                    question=question,
                    concern="Low volume - susceptible to manipulation",
                    level=ChallengeLevel.MODERATE,
                    mitigation="Wait for higher volume confirmation"
                )
        
            if spread and spread > 0.01:  # 1% spread
                return Challenge(
                    technique=AdversarialTechnique.RED_TEAM,
                    question="Is the spread too wide?",
                    concern=f"Wide spread ({spread*100:.2f}%) - execution risk",
                    level=ChallengeLevel.MODERATE,
                    mitigation="Use limit orders or wait for tighter spread"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _red_team_check: {e}")
            raise
    
    def _assumption_check(
        self,
        question: str,
        concern_template: str,
        decision: Dict[str, Any]
    ) -> Optional[Challenge]:
        """Assumption challenge"""
        try:
            reasoning = decision.get('reasoning', '')
        
            # Check for explicit assumptions
            assumption_words = ['assume', 'assuming', 'if', 'given that', 'provided']
            has_assumptions = any(word in reasoning.lower() for word in assumption_words)
        
            if not has_assumptions and len(reasoning) > 50:
                return Challenge(
                    technique=AdversarialTechnique.ASSUMPTION_CHALLENGE,
                    question=question,
                    concern="Assumptions not explicitly stated",
                    level=ChallengeLevel.MINOR,
                    mitigation="List key assumptions explicitly"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _assumption_check: {e}")
            raise
    
    def _contrarian_check(
        self,
        question: str,
        concern_template: str,
        decision: Dict[str, Any]
    ) -> Optional[Challenge]:
        """Contrarian analysis"""
        try:
            sentiment = decision.get('sentiment')
        
            # Check if following crowd
            if sentiment:
                if isinstance(sentiment, (int, float)):
                    if abs(sentiment) > 0.8:
                        return Challenge(
                            technique=AdversarialTechnique.CONTRARIAN,
                            question=question,
                            concern=f"Extreme sentiment ({sentiment:.2f}) - crowded trade risk",
                            level=ChallengeLevel.MODERATE,
                            mitigation="Consider contrarian position or reduced size"
                        )
        
            return None
        except Exception as e:
            logger.error(f"Error in _contrarian_check: {e}")
            raise
    
    def _black_swan_check(
        self,
        question: str,
        concern_template: str,
        decision: Dict[str, Any]
    ) -> Optional[Challenge]:
        """Black swan analysis"""
        try:
            leverage = decision.get('leverage', 1.0)
            position_size = decision.get('position_size_pct', 0)
        
            # Check for tail risk exposure
            if leverage and leverage > 5:
                return Challenge(
                    technique=AdversarialTechnique.BLACK_SWAN,
                    question=question,
                    concern=f"High leverage ({leverage}x) - vulnerable to black swan",
                    level=ChallengeLevel.CRITICAL,
                    mitigation="Reduce leverage to survive tail events"
                )
        
            if position_size and position_size > 20:
                return Challenge(
                    technique=AdversarialTechnique.BLACK_SWAN,
                    question="What if this position gaps against you?",
                    concern=f"Large position ({position_size}%) - concentration risk",
                    level=ChallengeLevel.SIGNIFICANT,
                    mitigation="Reduce position size for diversification"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _black_swan_check: {e}")
            raise
    
    def _bias_check(
        self,
        question: str,
        concern_template: str,
        decision: Dict[str, Any]
    ) -> Optional[Challenge]:
        """Bias detection check"""
        try:
            confidence = decision.get('confidence', 0.5)
        
            # Check for overconfidence
            if confidence > 0.9:
                return Challenge(
                    technique=AdversarialTechnique.BIAS_DETECTION,
                    question=question,
                    concern=f"Very high confidence ({confidence:.2f}) - possible overconfidence",
                    level=ChallengeLevel.MODERATE,
                    mitigation="Verify confidence is justified by evidence"
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _bias_check: {e}")
            raise
    
    def _detect_biases(self, decision: Dict[str, Any]) -> List[BiasAlert]:
        """Detect cognitive biases in the decision"""
        try:
            biases = []
            reasoning = (decision.get('reasoning', '') or decision.get('justification', '')).lower()
        
            for bias_type, pattern_info in self.bias_patterns.items():
                indicators = pattern_info['indicators']
                matches = sum(1 for ind in indicators if ind.lower() in reasoning)
            
                if matches >= 2:
                    severity = min(matches / len(indicators), 1.0)
                    biases.append(BiasAlert(
                        bias_type=bias_type,
                        evidence=f"Found {matches} indicators: {[i for i in indicators if i.lower() in reasoning][:3]}",
                        severity=severity,
                        recommendation=f"Review for {pattern_info['description']}"
                    ))
        
            # Check for overconfidence bias separately
            confidence = decision.get('confidence', 0.5)
            if confidence > 0.95:
                biases.append(BiasAlert(
                    bias_type=CognitiveBias.OVERCONFIDENCE,
                    evidence=f"Confidence level: {confidence:.2f}",
                    severity=0.8,
                    recommendation="No prediction should be >95% confident in markets"
                ))
        
            return biases
        except Exception as e:
            logger.error(f"Error in _detect_biases: {e}")
            raise
    
    def _calculate_robustness(
        self,
        challenges: List[Challenge],
        biases: List[BiasAlert]
    ) -> float:
        """Calculate overall decision robustness"""
        try:
            if not challenges and not biases:
                return 1.0
        
            # Weight challenges by severity
            challenge_penalty = 0.0
            for c in challenges:
                if c.level == ChallengeLevel.CRITICAL:
                    challenge_penalty += 0.3
                elif c.level == ChallengeLevel.SIGNIFICANT:
                    challenge_penalty += 0.15
                elif c.level == ChallengeLevel.MODERATE:
                    challenge_penalty += 0.08
                else:  # MINOR
                    challenge_penalty += 0.03
        
            # Weight biases
            bias_penalty = sum(b.severity * 0.1 for b in biases)
        
            robustness = max(0.0, 1.0 - challenge_penalty - bias_penalty)
            return robustness
        except Exception as e:
            logger.error(f"Error in _calculate_robustness: {e}")
            raise
    
    def _calculate_confidence_adjustment(
        self,
        robustness: float,
        critical_count: int
    ) -> float:
        """Calculate confidence adjustment factor"""
        # Start with robustness as base
        try:
            adjustment = robustness
        
            # Additional penalty for critical challenges
            adjustment -= critical_count * 0.15
        
            return max(0.3, min(1.0, adjustment))
        except Exception as e:
            logger.error(f"Error in _calculate_confidence_adjustment: {e}")
            raise
    
    def _generate_recommendations(
        self,
        challenges: List[Challenge],
        biases: List[BiasAlert]
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        try:
            recommendations = []
        
            # Critical challenges
            critical = [c for c in challenges if c.level == ChallengeLevel.CRITICAL]
            if critical:
                recommendations.append("ADDRESS CRITICAL ISSUES BEFORE PROCEEDING:")
                for c in critical:
                    if c.mitigation:
                        recommendations.append(f"  - {c.mitigation}")
        
            # Significant challenges
            significant = [c for c in challenges if c.level == ChallengeLevel.SIGNIFICANT]
            if significant:
                recommendations.append("Consider these significant concerns:")
                for c in significant[:3]:
                    recommendations.append(f"  - {c.concern}")
        
            # Biases
            if biases:
                recommendations.append("Potential cognitive biases detected:")
                for b in biases[:3]:
                    recommendations.append(f"  - {b.bias_type.value}: {b.recommendation}")
        
            # General recommendations
            if not challenges and not biases:
                recommendations.append("Decision passed adversarial analysis")
                recommendations.append("Proceed with normal position sizing")
            elif len(challenges) <= 2 and not critical:
                recommendations.append("Minor concerns identified - proceed with caution")
            else:
                recommendations.append("Multiple concerns - consider reducing position size")
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in _generate_recommendations: {e}")
            raise
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        try:
            if not self.analysis_history:
                return {'status': 'no_history'}
        
            proceed_count = sum(1 for a in self.analysis_history if a.should_proceed)
            avg_robustness = sum(a.overall_robustness for a in self.analysis_history) / len(self.analysis_history)
        
            return {
                'total_analyses': len(self.analysis_history),
                'proceed_rate': proceed_count / len(self.analysis_history),
                'avg_robustness': avg_robustness,
                'avg_challenges': sum(len(a.challenges) for a in self.analysis_history) / len(self.analysis_history),
                'avg_biases': sum(len(a.biases_detected) for a in self.analysis_history) / len(self.analysis_history),
            }
        except Exception as e:
            logger.error(f"Error in get_analysis_stats: {e}")
            raise


def create_adversarial_checker(config: Optional[Dict[str, Any]] = None) -> AdversarialChecker:
    """Create a new adversarial checker instance"""
    return AdversarialChecker(config)


__all__ = [
    'AdversarialChecker',
    'AdversarialResult',
    'AdversarialTechnique',
    'Challenge',
    'ChallengeLevel',
    'BiasAlert',
    'CognitiveBias',
    'create_adversarial_checker',
]
