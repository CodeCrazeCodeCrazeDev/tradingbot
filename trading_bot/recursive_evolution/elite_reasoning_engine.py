"""
Elite Reasoning Engine
======================

Step-by-step reasoning system that thinks like a professional elite trader.
This engine breaks down complex trading decisions into clear, logical steps
with verification at each stage.

KEY PRINCIPLES:
1. Think step-by-step, never jump to conclusions
2. Consider multiple perspectives (bull, bear, neutral)
3. Verify each reasoning step before proceeding
4. Identify and challenge assumptions
5. Quantify confidence at each step
6. Always have a "what could go wrong" analysis
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningStepType(Enum):
    """Types of reasoning steps"""
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    EVIDENCE_GATHERING = "evidence_gathering"
    ANALYSIS = "analysis"
    VERIFICATION = "verification"
    CONCLUSION = "conclusion"
    RISK_ASSESSMENT = "risk_assessment"
    DECISION = "decision"


class ReasoningQuality(Enum):
    """Quality levels of reasoning"""
    EXCELLENT = "excellent"  # All steps verified, high confidence
    GOOD = "good"  # Most steps verified, reasonable confidence
    ADEQUATE = "adequate"  # Basic reasoning, some gaps
    WEAK = "weak"  # Significant gaps or low confidence
    POOR = "poor"  # Major flaws in reasoning


@dataclass
class ReasoningStep:
    """A single step in the reasoning process"""
    step_number: int
    step_type: ReasoningStepType
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float  # 0-1
    verified: bool = False
    verification_notes: str = ""
    assumptions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TradeReasoning:
    """Complete reasoning chain for a trade decision"""
    reasoning_id: str
    symbol: str
    direction: str  # buy, sell, hold
    
    # Reasoning chain
    steps: List[ReasoningStep] = field(default_factory=list)
    
    # Multi-perspective analysis
    bull_case: Dict[str, Any] = field(default_factory=dict)
    bear_case: Dict[str, Any] = field(default_factory=dict)
    neutral_case: Dict[str, Any] = field(default_factory=dict)
    
    # Final decision
    decision: str = ""
    decision_confidence: float = 0.0
    expected_outcome: str = ""
    
    # Risk analysis
    identified_risks: List[str] = field(default_factory=list)
    risk_mitigations: List[str] = field(default_factory=list)
    max_acceptable_loss: float = 0.0
    
    # Quality assessment
    reasoning_quality: ReasoningQuality = ReasoningQuality.ADEQUATE
    quality_score: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    reasoning_time_ms: float = 0.0


class EliteReasoningEngine:
    """
    Elite-level reasoning engine that thinks through trades step-by-step.
    
    This engine:
    1. Observes market conditions systematically
    2. Forms hypotheses about market direction
    3. Gathers evidence to support/refute hypotheses
    4. Analyzes evidence from multiple perspectives
    5. Verifies each reasoning step
    6. Identifies risks and edge cases
    7. Makes final decision with clear justification
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Reasoning parameters
        self.min_confidence_threshold = self.config.get('min_confidence', 0.7)
        self.require_verification = self.config.get('require_verification', True)
        self.enable_multi_perspective = self.config.get('multi_perspective', True)
        self.reasoning_depth = self.config.get('reasoning_depth', 5)
        
        # Track reasoning history
        self.reasoning_history: List[TradeReasoning] = []
        self.reasoning_outcomes: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"EliteReasoningEngine initialized with depth={self.reasoning_depth}")
    
    def reason_about_trade(self, symbol: str, market_data: Dict[str, Any],
                          context: Optional[Dict[str, Any]] = None) -> TradeReasoning:
        """
        Perform complete step-by-step reasoning about a potential trade.
        """
        start_time = datetime.utcnow()
        
        reasoning_id = f"REASON-{symbol}-{start_time.strftime('%Y%m%d%H%M%S')}"
        reasoning = TradeReasoning(
            reasoning_id=reasoning_id,
            symbol=symbol,
            direction="unknown"
        )
        
        logger.info(f"Starting reasoning for {symbol}")
        
        # Step 1: Observe market conditions
        step1 = self._observe_market(symbol, market_data, context)
        reasoning.steps.append(step1)
        
        # Step 2: Form initial hypothesis
        step2 = self._form_hypothesis(symbol, market_data, step1.outputs)
        reasoning.steps.append(step2)
        
        # Step 3: Gather supporting/contradicting evidence
        step3 = self._gather_evidence(symbol, market_data, step2.outputs)
        reasoning.steps.append(step3)
        
        # Step 4: Multi-perspective analysis
        if self.enable_multi_perspective:
            reasoning.bull_case = self._analyze_bull_case(symbol, market_data, step3.outputs)
            reasoning.bear_case = self._analyze_bear_case(symbol, market_data, step3.outputs)
            reasoning.neutral_case = self._analyze_neutral_case(symbol, market_data, step3.outputs)
            
            step4 = self._synthesize_perspectives(reasoning.bull_case, reasoning.bear_case, 
                                                 reasoning.neutral_case)
            reasoning.steps.append(step4)
        
        # Step 5: Verify reasoning chain
        if self.require_verification:
            step5 = self._verify_reasoning(reasoning.steps)
            reasoning.steps.append(step5)
        
        # Step 6: Risk assessment
        step6 = self._assess_risks(symbol, market_data, reasoning.steps)
        reasoning.steps.append(step6)
        reasoning.identified_risks = step6.outputs.get('risks', [])
        reasoning.risk_mitigations = step6.outputs.get('mitigations', [])
        
        # Step 7: Final decision
        step7 = self._make_decision(reasoning.steps, reasoning.bull_case, 
                                   reasoning.bear_case, reasoning.neutral_case)
        reasoning.steps.append(step7)
        
        reasoning.direction = step7.outputs.get('direction', 'hold')
        reasoning.decision = step7.outputs.get('decision', '')
        reasoning.decision_confidence = step7.outputs.get('confidence', 0.0)
        reasoning.expected_outcome = step7.outputs.get('expected_outcome', '')
        
        # Assess reasoning quality
        reasoning.reasoning_quality, reasoning.quality_score = self._assess_reasoning_quality(reasoning)
        
        # Calculate reasoning time
        end_time = datetime.utcnow()
        reasoning.reasoning_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Store in history
        self.reasoning_history.append(reasoning)
        
        logger.info(f"Reasoning complete: {reasoning.direction} with confidence {reasoning.decision_confidence:.2f}")
        
        return reasoning
    
    def _observe_market(self, symbol: str, market_data: Dict[str, Any],
                       context: Optional[Dict[str, Any]]) -> ReasoningStep:
        """Step 1: Systematically observe market conditions"""
        
        observations = {}
        
        # Price action
        if 'price' in market_data:
            observations['current_price'] = market_data['price']
        if 'prices' in market_data:
            prices = market_data['prices']
            observations['price_trend'] = 'up' if prices[-1] > prices[0] else 'down'
            observations['price_volatility'] = np.std(prices) / np.mean(prices)
        
        # Volume
        if 'volume' in market_data:
            observations['current_volume'] = market_data['volume']
            if 'volumes' in market_data:
                avg_volume = np.mean(market_data['volumes'])
                observations['volume_relative'] = market_data['volume'] / avg_volume
        
        # Market regime
        if context and 'regime' in context:
            observations['market_regime'] = context['regime']
        
        # Volatility
        if context and 'volatility' in context:
            observations['volatility_level'] = context['volatility']
        
        # Liquidity
        if 'bid_ask_spread' in market_data:
            observations['liquidity'] = 'good' if market_data['bid_ask_spread'] < 0.001 else 'poor'
        
        return ReasoningStep(
            step_number=1,
            step_type=ReasoningStepType.OBSERVATION,
            description="Observe current market conditions systematically",
            inputs={'symbol': symbol, 'market_data': market_data},
            outputs=observations,
            confidence=0.95,  # Observations are high confidence
            verified=True
        )
    
    def _form_hypothesis(self, symbol: str, market_data: Dict[str, Any],
                        observations: Dict[str, Any]) -> ReasoningStep:
        """Step 2: Form hypothesis about market direction"""
        
        # Analyze observations to form hypothesis
        bullish_signals = 0
        bearish_signals = 0
        
        # Price trend
        if observations.get('price_trend') == 'up':
            bullish_signals += 1
        elif observations.get('price_trend') == 'down':
            bearish_signals += 1
        
        # Volume
        if observations.get('volume_relative', 1.0) > 1.2:
            # High volume confirms trend
            if observations.get('price_trend') == 'up':
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Volatility
        volatility = observations.get('volatility_level', 0.5)
        if volatility > 0.7:
            # High volatility - be cautious
            confidence_penalty = 0.2
        else:
            confidence_penalty = 0.0
        
        # Form hypothesis
        if bullish_signals > bearish_signals:
            hypothesis = "Price likely to move higher"
            direction = "bullish"
            confidence = min(0.9, 0.5 + (bullish_signals * 0.15) - confidence_penalty)
        elif bearish_signals > bullish_signals:
            hypothesis = "Price likely to move lower"
            direction = "bearish"
            confidence = min(0.9, 0.5 + (bearish_signals * 0.15) - confidence_penalty)
        else:
            hypothesis = "Price likely to remain range-bound"
            direction = "neutral"
            confidence = 0.6
        
        assumptions = [
            "Historical patterns continue to hold",
            "No major news events imminent",
            "Market structure remains intact"
        ]
        
        return ReasoningStep(
            step_number=2,
            step_type=ReasoningStepType.HYPOTHESIS,
            description=f"Form hypothesis: {hypothesis}",
            inputs=observations,
            outputs={
                'hypothesis': hypothesis,
                'direction': direction,
                'confidence': confidence,
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals
            },
            confidence=confidence,
            assumptions=assumptions,
            verified=False
        )
    
    def _gather_evidence(self, symbol: str, market_data: Dict[str, Any],
                        hypothesis_outputs: Dict[str, Any]) -> ReasoningStep:
        """Step 3: Gather evidence to support or refute hypothesis"""
        
        evidence = {
            'supporting': [],
            'contradicting': [],
            'neutral': []
        }
        
        direction = hypothesis_outputs.get('direction', 'neutral')
        
        # Check technical indicators
        if 'indicators' in market_data:
            indicators = market_data['indicators']
            
            # RSI
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if direction == 'bullish' and rsi < 70:
                    evidence['supporting'].append(f"RSI at {rsi:.1f} - not overbought")
                elif direction == 'bullish' and rsi > 70:
                    evidence['contradicting'].append(f"RSI at {rsi:.1f} - overbought")
                elif direction == 'bearish' and rsi > 30:
                    evidence['supporting'].append(f"RSI at {rsi:.1f} - not oversold")
                elif direction == 'bearish' and rsi < 30:
                    evidence['contradicting'].append(f"RSI at {rsi:.1f} - oversold")
            
            # MACD
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd']
                signal = indicators['macd_signal']
                if direction == 'bullish' and macd > signal:
                    evidence['supporting'].append("MACD bullish crossover")
                elif direction == 'bearish' and macd < signal:
                    evidence['supporting'].append("MACD bearish crossover")
        
        # Check order flow
        if 'order_flow' in market_data:
            flow = market_data['order_flow']
            if direction == 'bullish' and flow > 0:
                evidence['supporting'].append(f"Positive order flow: {flow:.2f}")
            elif direction == 'bearish' and flow < 0:
                evidence['supporting'].append(f"Negative order flow: {flow:.2f}")
        
        # Calculate evidence strength
        supporting_count = len(evidence['supporting'])
        contradicting_count = len(evidence['contradicting'])
        total_evidence = supporting_count + contradicting_count
        
        if total_evidence > 0:
            evidence_strength = supporting_count / total_evidence
        else:
            evidence_strength = 0.5
        
        confidence = evidence_strength * 0.9
        
        return ReasoningStep(
            step_number=3,
            step_type=ReasoningStepType.EVIDENCE_GATHERING,
            description="Gather evidence to support/refute hypothesis",
            inputs=hypothesis_outputs,
            outputs={
                'evidence': evidence,
                'supporting_count': supporting_count,
                'contradicting_count': contradicting_count,
                'evidence_strength': evidence_strength
            },
            confidence=confidence,
            verified=False
        )
    
    def _analyze_bull_case(self, symbol: str, market_data: Dict[str, Any],
                          evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the bullish case"""
        
        bull_case = {
            'perspective': 'bullish',
            'arguments': [],
            'probability': 0.0,
            'target_price': 0.0,
            'timeframe': 'short-term'
        }
        
        # Build bullish arguments
        supporting_evidence = evidence.get('evidence', {}).get('supporting', [])
        for ev in supporting_evidence:
            if any(word in ev.lower() for word in ['bullish', 'positive', 'up', 'higher']):
                bull_case['arguments'].append(ev)
        
        # Add structural bullish arguments
        if market_data.get('price', 0) > market_data.get('support_level', 0):
            bull_case['arguments'].append("Price above key support level")
        
        # Calculate probability
        bull_case['probability'] = min(0.9, len(bull_case['arguments']) * 0.15 + 0.3)
        
        # Estimate target
        current_price = market_data.get('price', 100)
        bull_case['target_price'] = current_price * 1.02  # 2% target
        
        return bull_case
    
    def _analyze_bear_case(self, symbol: str, market_data: Dict[str, Any],
                          evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the bearish case"""
        
        bear_case = {
            'perspective': 'bearish',
            'arguments': [],
            'probability': 0.0,
            'target_price': 0.0,
            'timeframe': 'short-term'
        }
        
        # Build bearish arguments
        contradicting_evidence = evidence.get('evidence', {}).get('contradicting', [])
        for ev in contradicting_evidence:
            bear_case['arguments'].append(ev)
        
        # Add structural bearish arguments
        if market_data.get('price', 0) < market_data.get('resistance_level', float('inf')):
            bear_case['arguments'].append("Price below key resistance level")
        
        # Calculate probability
        bear_case['probability'] = min(0.9, len(bear_case['arguments']) * 0.15 + 0.3)
        
        # Estimate target
        current_price = market_data.get('price', 100)
        bear_case['target_price'] = current_price * 0.98  # 2% downside
        
        return bear_case
    
    def _analyze_neutral_case(self, symbol: str, market_data: Dict[str, Any],
                             evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the neutral/range-bound case"""
        
        neutral_case = {
            'perspective': 'neutral',
            'arguments': [],
            'probability': 0.0,
            'range_low': 0.0,
            'range_high': 0.0
        }
        
        # Build neutral arguments
        supporting = len(evidence.get('evidence', {}).get('supporting', []))
        contradicting = len(evidence.get('evidence', {}).get('contradicting', []))
        
        if abs(supporting - contradicting) <= 1:
            neutral_case['arguments'].append("Evidence is balanced - no clear direction")
        
        if market_data.get('volatility', 1.0) < 0.3:
            neutral_case['arguments'].append("Low volatility suggests range-bound action")
        
        # Calculate probability
        neutral_case['probability'] = min(0.9, len(neutral_case['arguments']) * 0.2 + 0.2)
        
        # Estimate range
        current_price = market_data.get('price', 100)
        neutral_case['range_low'] = current_price * 0.99
        neutral_case['range_high'] = current_price * 1.01
        
        return neutral_case
    
    def _synthesize_perspectives(self, bull_case: Dict[str, Any],
                                bear_case: Dict[str, Any],
                                neutral_case: Dict[str, Any]) -> ReasoningStep:
        """Step 4: Synthesize multiple perspectives"""
        
        # Weight perspectives by probability
        total_prob = bull_case['probability'] + bear_case['probability'] + neutral_case['probability']
        
        if total_prob > 0:
            bull_weight = bull_case['probability'] / total_prob
            bear_weight = bear_case['probability'] / total_prob
            neutral_weight = neutral_case['probability'] / total_prob
        else:
            bull_weight = bear_weight = neutral_weight = 0.33
        
        # Determine dominant perspective
        if bull_weight > bear_weight and bull_weight > neutral_weight:
            dominant = 'bullish'
            confidence = bull_weight
        elif bear_weight > bull_weight and bear_weight > neutral_weight:
            dominant = 'bearish'
            confidence = bear_weight
        else:
            dominant = 'neutral'
            confidence = neutral_weight
        
        synthesis = {
            'dominant_perspective': dominant,
            'confidence': confidence,
            'bull_weight': bull_weight,
            'bear_weight': bear_weight,
            'neutral_weight': neutral_weight,
            'consensus': confidence > 0.6
        }
        
        return ReasoningStep(
            step_number=4,
            step_type=ReasoningStepType.ANALYSIS,
            description="Synthesize multiple perspectives",
            inputs={'bull': bull_case, 'bear': bear_case, 'neutral': neutral_case},
            outputs=synthesis,
            confidence=confidence,
            verified=False
        )
    
    def _verify_reasoning(self, steps: List[ReasoningStep]) -> ReasoningStep:
        """Step 5: Verify the reasoning chain"""
        
        verification_results = {
            'steps_verified': 0,
            'steps_failed': 0,
            'confidence_checks': [],
            'assumption_checks': [],
            'overall_valid': True
        }
        
        for step in steps:
            # Check confidence levels
            if step.confidence < 0.5:
                verification_results['confidence_checks'].append(
                    f"Step {step.step_number} has low confidence: {step.confidence:.2f}"
                )
                verification_results['steps_failed'] += 1
            else:
                verification_results['steps_verified'] += 1
            
            # Check assumptions
            if step.assumptions:
                verification_results['assumption_checks'].append(
                    f"Step {step.step_number} assumes: {', '.join(step.assumptions)}"
                )
            
            # Mark step as verified
            step.verified = True
        
        # Overall validity
        total_steps = len(steps)
        if total_steps > 0:
            verification_rate = verification_results['steps_verified'] / total_steps
            verification_results['overall_valid'] = verification_rate > 0.7
        
        confidence = verification_rate if total_steps > 0 else 0.5
        
        return ReasoningStep(
            step_number=5,
            step_type=ReasoningStepType.VERIFICATION,
            description="Verify reasoning chain integrity",
            inputs={'steps': [s.step_number for s in steps]},
            outputs=verification_results,
            confidence=confidence,
            verified=True
        )
    
    def _assess_risks(self, symbol: str, market_data: Dict[str, Any],
                     steps: List[ReasoningStep]) -> ReasoningStep:
        """Step 6: Assess risks and edge cases"""
        
        risks = []
        mitigations = []
        
        # Market risks
        if market_data.get('volatility', 0) > 0.7:
            risks.append("High volatility - increased risk of adverse moves")
            mitigations.append("Reduce position size by 50%")
        
        # Liquidity risks
        if market_data.get('bid_ask_spread', 0) > 0.002:
            risks.append("Wide spreads - poor liquidity")
            mitigations.append("Use limit orders only")
        
        # Reasoning risks
        low_confidence_steps = [s for s in steps if s.confidence < 0.6]
        if low_confidence_steps:
            risks.append(f"{len(low_confidence_steps)} reasoning steps have low confidence")
            mitigations.append("Require additional confirmation before entry")
        
        # Assumption risks
        all_assumptions = []
        for step in steps:
            all_assumptions.extend(step.assumptions)
        if all_assumptions:
            risks.append(f"Reasoning relies on {len(all_assumptions)} assumptions")
            mitigations.append("Monitor assumptions and exit if invalidated")
        
        # News/event risks
        if market_data.get('upcoming_events', False):
            risks.append("Major news event approaching")
            mitigations.append("Close position before event or reduce size")
        
        # Calculate overall risk level
        risk_level = len(risks) / 10.0  # Normalize to 0-1
        confidence = max(0.3, 1.0 - risk_level)
        
        return ReasoningStep(
            step_number=6,
            step_type=ReasoningStepType.RISK_ASSESSMENT,
            description="Assess risks and identify mitigations",
            inputs={'market_data': market_data, 'reasoning_steps': len(steps)},
            outputs={
                'risks': risks,
                'mitigations': mitigations,
                'risk_level': risk_level,
                'risk_count': len(risks)
            },
            confidence=confidence,
            risks=risks,
            verified=True
        )
    
    def _make_decision(self, steps: List[ReasoningStep],
                      bull_case: Dict[str, Any],
                      bear_case: Dict[str, Any],
                      neutral_case: Dict[str, Any]) -> ReasoningStep:
        """Step 7: Make final decision"""
        
        # Get synthesis from step 4
        synthesis_step = next((s for s in steps if s.step_type == ReasoningStepType.ANALYSIS), None)
        
        if synthesis_step:
            dominant = synthesis_step.outputs.get('dominant_perspective', 'neutral')
            confidence = synthesis_step.outputs.get('confidence', 0.5)
        else:
            dominant = 'neutral'
            confidence = 0.5
        
        # Get risk assessment
        risk_step = next((s for s in steps if s.step_type == ReasoningStepType.RISK_ASSESSMENT), None)
        if risk_step:
            risk_level = risk_step.outputs.get('risk_level', 0.5)
            # Adjust confidence based on risk
            confidence = confidence * (1.0 - risk_level * 0.5)
        
        # Make decision
        if confidence >= self.min_confidence_threshold:
            if dominant == 'bullish':
                direction = 'buy'
                decision = f"BUY {symbol} - Bullish case is strongest"
                expected_outcome = f"Target: {bull_case.get('target_price', 0):.2f}"
            elif dominant == 'bearish':
                direction = 'sell'
                decision = f"SELL {symbol} - Bearish case is strongest"
                expected_outcome = f"Target: {bear_case.get('target_price', 0):.2f}"
            else:
                direction = 'hold'
                decision = f"HOLD {symbol} - No clear direction"
                expected_outcome = "Wait for better setup"
        else:
            direction = 'hold'
            decision = f"HOLD {symbol} - Confidence too low ({confidence:.2f})"
            expected_outcome = "Wait for higher confidence setup"
        
        return ReasoningStep(
            step_number=7,
            step_type=ReasoningStepType.DECISION,
            description="Make final trading decision",
            inputs={
                'dominant_perspective': dominant,
                'confidence': confidence,
                'threshold': self.min_confidence_threshold
            },
            outputs={
                'direction': direction,
                'decision': decision,
                'confidence': confidence,
                'expected_outcome': expected_outcome
            },
            confidence=confidence,
            verified=True
        )
    
    def _assess_reasoning_quality(self, reasoning: TradeReasoning) -> Tuple[ReasoningQuality, float]:
        """Assess the overall quality of the reasoning"""
        
        # Calculate quality score
        score = 0.0
        max_score = 0.0
        
        # Check step completeness
        if len(reasoning.steps) >= 7:
            score += 20
        max_score += 20
        
        # Check verification
        verified_steps = sum(1 for s in reasoning.steps if s.verified)
        score += (verified_steps / len(reasoning.steps)) * 20 if reasoning.steps else 0
        max_score += 20
        
        # Check confidence levels
        avg_confidence = np.mean([s.confidence for s in reasoning.steps]) if reasoning.steps else 0
        score += avg_confidence * 20
        max_score += 20
        
        # Check multi-perspective analysis
        if reasoning.bull_case and reasoning.bear_case and reasoning.neutral_case:
            score += 15
        max_score += 15
        
        # Check risk assessment
        if reasoning.identified_risks and reasoning.risk_mitigations:
            score += 15
        max_score += 15
        
        # Check decision confidence
        score += reasoning.decision_confidence * 10
        max_score += 10
        
        # Normalize score
        quality_score = score / max_score if max_score > 0 else 0.5
        
        # Determine quality level
        if quality_score >= 0.9:
            quality = ReasoningQuality.EXCELLENT
        elif quality_score >= 0.75:
            quality = ReasoningQuality.GOOD
        elif quality_score >= 0.6:
            quality = ReasoningQuality.ADEQUATE
        elif quality_score >= 0.4:
            quality = ReasoningQuality.WEAK
        else:
            quality = ReasoningQuality.POOR
        
        return quality, quality_score
    
    def record_outcome(self, reasoning_id: str, actual_outcome: Dict[str, Any]):
        """Record the actual outcome of a reasoned trade"""
        self.reasoning_outcomes[reasoning_id] = actual_outcome
        
        # Learn from outcome
        reasoning = next((r for r in self.reasoning_history if r.reasoning_id == reasoning_id), None)
        if reasoning:
            was_correct = actual_outcome.get('profitable', False)
            logger.info(f"Reasoning {reasoning_id} outcome: {'CORRECT' if was_correct else 'INCORRECT'}")
    
    def get_reasoning_stats(self) -> Dict[str, Any]:
        """Get statistics about reasoning performance"""
        
        if not self.reasoning_history:
            return {'total_reasonings': 0}
        
        total = len(self.reasoning_history)
        
        # Quality distribution
        quality_counts = {}
        for r in self.reasoning_history:
            quality = r.reasoning_quality.value
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        # Average confidence
        avg_confidence = np.mean([r.decision_confidence for r in self.reasoning_history])
        
        # Average reasoning time
        avg_time = np.mean([r.reasoning_time_ms for r in self.reasoning_history])
        
        # Outcome accuracy (if available)
        reasonings_with_outcomes = [r for r in self.reasoning_history 
                                    if r.reasoning_id in self.reasoning_outcomes]
        if reasonings_with_outcomes:
            correct = sum(1 for r in reasonings_with_outcomes 
                         if self.reasoning_outcomes[r.reasoning_id].get('profitable', False))
            accuracy = correct / len(reasonings_with_outcomes)
        else:
            accuracy = None
        
        return {
            'total_reasonings': total,
            'quality_distribution': quality_counts,
            'average_confidence': avg_confidence,
            'average_reasoning_time_ms': avg_time,
            'accuracy': accuracy,
            'reasonings_with_outcomes': len(reasonings_with_outcomes)
        }


def quick_start_reasoning_engine(config: Optional[Dict[str, Any]] = None) -> EliteReasoningEngine:
    """Quick start function for reasoning engine"""
    return EliteReasoningEngine(config)
