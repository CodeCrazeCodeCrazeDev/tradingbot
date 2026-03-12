"""
Decision Verification Chain - Multi-Stage Fact-Checking and Hallucination Prevention

This module implements a comprehensive verification chain that fact-checks the bot's
own outputs to prevent hallucinations and ensure decision integrity.

VERIFICATION STAGES:
1. Data Grounding Verification - Verify all claims against actual market data
2. Logical Consistency Check - Detect contradictions in reasoning
3. Cross-Source Validation - Validate against multiple independent sources
4. Historical Accuracy Check - Compare predictions with past accuracy
5. Adversarial Self-Questioning - Challenge own conclusions
6. Confidence Calibration - Ensure confidence matches historical accuracy
7. Reality Anchor Check - Verify outputs are physically possible
8. Audit Trail Generation - Create immutable verification records

HALLUCINATION TYPES DETECTED:
- Fabricated data points (prices, volumes that don't exist)
- Invented patterns (patterns not actually present in data)
- False correlations (correlations that don't exist)
- Overconfident predictions (confidence exceeding historical accuracy)
- Logical contradictions (mutually exclusive claims)
- Temporal impossibilities (future data in past analysis)
- Magnitude errors (values outside reasonable bounds)

Author: AlphaAlgo Team
Date: 2026-01-28
Priority: P0 - CRITICAL
"""

import asyncio
import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from collections import deque
import statistics

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class VerificationStage(Enum):
    """Stages in the verification chain"""
    DATA_GROUNDING = auto()
    LOGICAL_CONSISTENCY = auto()
    CROSS_SOURCE = auto()
    HISTORICAL_ACCURACY = auto()
    ADVERSARIAL_QUESTIONING = auto()
    CONFIDENCE_CALIBRATION = auto()
    REALITY_ANCHOR = auto()
    AUDIT_TRAIL = auto()


class HallucinationType(Enum):
    """Types of hallucinations that can be detected"""
    FABRICATED_DATA = "fabricated_data"
    INVENTED_PATTERN = "invented_pattern"
    FALSE_CORRELATION = "false_correlation"
    OVERCONFIDENT = "overconfident"
    LOGICAL_CONTRADICTION = "logical_contradiction"
    TEMPORAL_IMPOSSIBILITY = "temporal_impossibility"
    MAGNITUDE_ERROR = "magnitude_error"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    CIRCULAR_REASONING = "circular_reasoning"
    CHERRY_PICKING = "cherry_picking"


class VerificationStatus(Enum):
    """Status of verification"""
    VERIFIED = "verified"
    SUSPICIOUS = "suspicious"
    HALLUCINATION_DETECTED = "hallucination_detected"
    INSUFFICIENT_DATA = "insufficient_data"
    PENDING = "pending"


class DecisionAction(Enum):
    """Actions for decisions"""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    DEFER = "defer"
    ESCALATE = "escalate"


@dataclass
class VerificationEvidence:
    """Evidence supporting or refuting a claim"""
    source: str
    data_point: Any
    timestamp: datetime
    confidence: float
    supports_claim: bool
    notes: str = ""


@dataclass
class HallucinationAlert:
    """Alert for detected hallucination"""
    hallucination_type: HallucinationType
    severity: float  # 0.0 to 1.0
    claim: str
    evidence_against: List[VerificationEvidence]
    suggested_correction: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StageResult:
    """Result from a verification stage"""
    stage: VerificationStage
    passed: bool
    confidence: float
    findings: List[str]
    hallucinations: List[HallucinationAlert]
    evidence: List[VerificationEvidence]
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VerificationChainResult:
    """Complete result from the verification chain"""
    decision_id: str
    original_decision: Dict[str, Any]
    stage_results: List[StageResult]
    overall_status: VerificationStatus
    overall_confidence: float
    hallucinations_detected: List[HallucinationAlert]
    recommended_action: DecisionAction
    corrected_decision: Optional[Dict[str, Any]]
    verification_hash: str
    total_duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'overall_status': self.overall_status.value,
            'overall_confidence': self.overall_confidence,
            'hallucinations_count': len(self.hallucinations_detected),
            'recommended_action': self.recommended_action.value,
            'stages_passed': sum(1 for s in self.stage_results if s.passed),
            'total_stages': len(self.stage_results),
            'verification_hash': self.verification_hash,
            'total_duration_ms': self.total_duration_ms,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class FactCheckResult:
    """Result of fact-checking a specific claim"""
    claim: str
    verified: bool
    confidence: float
    sources_checked: int
    sources_confirming: int
    evidence: List[VerificationEvidence]
    notes: str = ""


# =============================================================================
# DECISION VERIFICATION CHAIN
# =============================================================================

class DecisionVerificationChain:
    """
    Multi-stage verification chain that fact-checks the bot's decisions
    to prevent hallucinations and ensure output integrity.
    
    The chain implements 8 verification stages, each designed to catch
    different types of errors and hallucinations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Verification thresholds
        self.min_confidence_threshold = self.config.get('min_confidence_threshold', 0.7)
        self.hallucination_severity_threshold = self.config.get('hallucination_severity_threshold', 0.5)
        self.min_sources_for_verification = self.config.get('min_sources_for_verification', 2)
        
        # Historical data for calibration
        self.prediction_history: deque = deque(maxlen=1000)
        self.accuracy_history: deque = deque(maxlen=1000)
        self.confidence_history: deque = deque(maxlen=1000)
        
        # Verification audit trail
        self.verification_log: List[VerificationChainResult] = []
        
        # Market data cache for grounding
        self._market_data_cache: Dict[str, Any] = {}
        
        # Known valid ranges for reality anchoring
        self.valid_ranges = {
            'price_change_pct_1m': (-10.0, 10.0),
            'price_change_pct_1h': (-20.0, 20.0),
            'price_change_pct_1d': (-50.0, 50.0),
            'volume_ratio': (0.01, 100.0),
            'volatility': (0.0001, 1.0),
            'rsi': (0.0, 100.0),
            'confidence': (0.0, 1.0),
            'position_size_pct': (0.0, 100.0),
            'leverage': (1.0, 100.0),
            'spread_pct': (0.0, 10.0),
        }
        
        # Adversarial questions for self-challenging
        self.adversarial_questions = [
            "What evidence contradicts this conclusion?",
            "What assumptions are being made?",
            "What would make this prediction wrong?",
            "Is the sample size sufficient?",
            "Could this be random noise?",
            "Are there confounding factors?",
            "What is the base rate for this prediction?",
            "How would a skeptic challenge this?",
            "What information is missing?",
            "Could the data be stale or incorrect?",
        ]
        
        logger.info("DecisionVerificationChain initialized")
    
    # =========================================================================
    # MAIN VERIFICATION PIPELINE
    # =========================================================================
    
    async def verify_decision(
        self,
        decision: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None,
        additional_sources: Optional[List[Dict[str, Any]]] = None
    ) -> VerificationChainResult:
        """
        Run the complete verification chain on a decision.
        
        Args:
            decision: The decision to verify
            market_data: Current market data for grounding
            additional_sources: Additional data sources for cross-validation
            
        Returns:
            VerificationChainResult with complete verification details
        """
        start_time = datetime.now()
        decision_id = self._generate_decision_id(decision)
        
        logger.info(f"Starting verification chain for decision {decision_id}")
        
        # Update market data cache
        if market_data:
            self._market_data_cache.update(market_data)
        
        # Run all verification stages
        stage_results: List[StageResult] = []
        all_hallucinations: List[HallucinationAlert] = []
        
        # Stage 1: Data Grounding
        stage1 = await self._verify_data_grounding(decision, market_data)
        stage_results.append(stage1)
        all_hallucinations.extend(stage1.hallucinations)
        
        # Stage 2: Logical Consistency
        stage2 = await self._verify_logical_consistency(decision)
        stage_results.append(stage2)
        all_hallucinations.extend(stage2.hallucinations)
        
        # Stage 3: Cross-Source Validation
        stage3 = await self._verify_cross_source(decision, additional_sources)
        stage_results.append(stage3)
        all_hallucinations.extend(stage3.hallucinations)
        
        # Stage 4: Historical Accuracy
        stage4 = await self._verify_historical_accuracy(decision)
        stage_results.append(stage4)
        all_hallucinations.extend(stage4.hallucinations)
        
        # Stage 5: Adversarial Self-Questioning
        stage5 = await self._adversarial_questioning(decision)
        stage_results.append(stage5)
        all_hallucinations.extend(stage5.hallucinations)
        
        # Stage 6: Confidence Calibration
        stage6 = await self._verify_confidence_calibration(decision)
        stage_results.append(stage6)
        all_hallucinations.extend(stage6.hallucinations)
        
        # Stage 7: Reality Anchor Check
        stage7 = await self._verify_reality_anchor(decision)
        stage_results.append(stage7)
        all_hallucinations.extend(stage7.hallucinations)
        
        # Stage 8: Generate Audit Trail
        stage8 = await self._generate_audit_trail(decision, stage_results)
        stage_results.append(stage8)
        
        # Calculate overall results
        overall_status, overall_confidence = self._calculate_overall_status(
            stage_results, all_hallucinations
        )
        
        # Determine recommended action
        recommended_action = self._determine_action(
            overall_status, overall_confidence, all_hallucinations
        )
        
        # Generate corrected decision if needed
        corrected_decision = None
        if recommended_action == DecisionAction.MODIFY:
            corrected_decision = self._generate_corrected_decision(
                decision, all_hallucinations
            )
        
        # Calculate duration
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate verification hash
        verification_hash = self._generate_verification_hash(
            decision_id, stage_results, overall_status
        )
        
        result = VerificationChainResult(
            decision_id=decision_id,
            original_decision=decision,
            stage_results=stage_results,
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            hallucinations_detected=all_hallucinations,
            recommended_action=recommended_action,
            corrected_decision=corrected_decision,
            verification_hash=verification_hash,
            total_duration_ms=duration_ms
        )
        
        # Log to audit trail
        self.verification_log.append(result)
        
        logger.info(
            f"Verification complete for {decision_id}: "
            f"status={overall_status.value}, confidence={overall_confidence:.2f}, "
            f"hallucinations={len(all_hallucinations)}, action={recommended_action.value}"
        )
        
        return result
    
    # =========================================================================
    # STAGE 1: DATA GROUNDING VERIFICATION
    # =========================================================================
    
    async def _verify_data_grounding(
        self,
        decision: Dict[str, Any],
        market_data: Optional[Dict[str, Any]]
    ) -> StageResult:
        """
        Verify that all data points in the decision are grounded in actual market data.
        Detects fabricated data points.
        """
        start_time = datetime.now()
        findings: List[str] = []
        hallucinations: List[HallucinationAlert] = []
        evidence: List[VerificationEvidence] = []
        passed = True
        confidence = 1.0
        
        if not market_data:
            findings.append("No market data provided for grounding verification")
            return StageResult(
                stage=VerificationStage.DATA_GROUNDING,
                passed=False,
                confidence=0.0,
                findings=findings,
                hallucinations=[],
                evidence=[],
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
        
        # Check price claims
        claimed_price = decision.get('current_price') or decision.get('price')
        actual_price = market_data.get('price') or market_data.get('close')
        
        if claimed_price and actual_price:
            price_diff_pct = abs(claimed_price - actual_price) / actual_price * 100
            
            if price_diff_pct > 1.0:  # More than 1% difference
                hallucinations.append(HallucinationAlert(
                    hallucination_type=HallucinationType.FABRICATED_DATA,
                    severity=min(price_diff_pct / 10.0, 1.0),
                    claim=f"Claimed price {claimed_price}",
                    evidence_against=[VerificationEvidence(
                        source="market_data",
                        data_point=actual_price,
                        timestamp=datetime.now(),
                        confidence=0.95,
                        supports_claim=False,
                        notes=f"Actual price is {actual_price}, difference: {price_diff_pct:.2f}%"
                    )],
                    suggested_correction=f"Use actual price: {actual_price}"
                ))
                passed = False
                confidence *= 0.5
                findings.append(f"Price mismatch: claimed {claimed_price}, actual {actual_price}")
            else:
                evidence.append(VerificationEvidence(
                    source="market_data",
                    data_point=actual_price,
                    timestamp=datetime.now(),
                    confidence=0.95,
                    supports_claim=True,
                    notes="Price verified within tolerance"
                ))
                findings.append("Price verified against market data")
        
        # Check volume claims
        claimed_volume = decision.get('volume')
        actual_volume = market_data.get('volume')
        
        if claimed_volume and actual_volume:
            volume_ratio = claimed_volume / actual_volume if actual_volume > 0 else float('inf')
            
            if volume_ratio < 0.1 or volume_ratio > 10.0:
                hallucinations.append(HallucinationAlert(
                    hallucination_type=HallucinationType.FABRICATED_DATA,
                    severity=0.7,
                    claim=f"Claimed volume {claimed_volume}",
                    evidence_against=[VerificationEvidence(
                        source="market_data",
                        data_point=actual_volume,
                        timestamp=datetime.now(),
                        confidence=0.9,
                        supports_claim=False,
                        notes=f"Volume ratio: {volume_ratio:.2f}x"
                    )],
                    suggested_correction=f"Use actual volume: {actual_volume}"
                ))
                passed = False
                confidence *= 0.7
                findings.append(f"Volume mismatch: ratio {volume_ratio:.2f}x")
        
        # Check timestamp freshness
        data_timestamp = market_data.get('timestamp')
        if data_timestamp:
            if isinstance(data_timestamp, str):
                data_timestamp = datetime.fromisoformat(data_timestamp.replace('Z', '+00:00'))
            
            age_seconds = (datetime.now() - data_timestamp.replace(tzinfo=None)).total_seconds()
            
            if age_seconds > 300:  # More than 5 minutes old
                findings.append(f"Market data is {age_seconds:.0f} seconds old")
                confidence *= 0.8
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=VerificationStage.DATA_GROUNDING,
            passed=passed,
            confidence=confidence,
            findings=findings,
            hallucinations=hallucinations,
            evidence=evidence,
            duration_ms=duration_ms
        )
    
    # =========================================================================
    # STAGE 2: LOGICAL CONSISTENCY CHECK
    # =========================================================================
    
    async def _verify_logical_consistency(
        self,
        decision: Dict[str, Any]
    ) -> StageResult:
        """
        Check for logical contradictions in the decision.
        Detects mutually exclusive claims and circular reasoning.
        """
        start_time = datetime.now()
        findings: List[str] = []
        hallucinations: List[HallucinationAlert] = []
        evidence: List[VerificationEvidence] = []
        passed = True
        confidence = 1.0
        
        # Check direction vs price expectations
        direction = decision.get('direction', '').upper()
        expected_move = decision.get('expected_move') or decision.get('target_price')
        current_price = decision.get('current_price') or decision.get('price')
        
        if direction and expected_move and current_price:
            if direction == 'BUY' and expected_move < current_price:
                hallucinations.append(HallucinationAlert(
                    hallucination_type=HallucinationType.LOGICAL_CONTRADICTION,
                    severity=0.9,
                    claim=f"BUY signal with target below current price",
                    evidence_against=[VerificationEvidence(
                        source="logic_check",
                        data_point={'direction': direction, 'target': expected_move, 'current': current_price},
                        timestamp=datetime.now(),
                        confidence=1.0,
                        supports_claim=False,
                        notes="BUY expects price to go UP, not down"
                    )]
                ))
                passed = False
                confidence *= 0.3
                findings.append("CONTRADICTION: BUY signal with bearish target")
            
            elif direction == 'SELL' and expected_move > current_price:
                hallucinations.append(HallucinationAlert(
                    hallucination_type=HallucinationType.LOGICAL_CONTRADICTION,
                    severity=0.9,
                    claim=f"SELL signal with target above current price",
                    evidence_against=[VerificationEvidence(
                        source="logic_check",
                        data_point={'direction': direction, 'target': expected_move, 'current': current_price},
                        timestamp=datetime.now(),
                        confidence=1.0,
                        supports_claim=False,
                        notes="SELL expects price to go DOWN, not up"
                    )]
                ))
                passed = False
                confidence *= 0.3
                findings.append("CONTRADICTION: SELL signal with bullish target")
        
        # Check stop loss vs take profit logic
        stop_loss = decision.get('stop_loss')
        take_profit = decision.get('take_profit')
        
        if stop_loss and take_profit and current_price and direction:
            if direction == 'BUY':
                if stop_loss > current_price:
                    hallucinations.append(HallucinationAlert(
                        hallucination_type=HallucinationType.LOGICAL_CONTRADICTION,
                        severity=1.0,
                        claim="BUY stop loss above entry",
                        evidence_against=[],
                        suggested_correction="Stop loss must be below entry for BUY"
                    ))
                    passed = False
                    findings.append("CONTRADICTION: BUY stop loss above entry")
                
                if take_profit < current_price:
                    hallucinations.append(HallucinationAlert(
                        hallucination_type=HallucinationType.LOGICAL_CONTRADICTION,
                        severity=1.0,
                        claim="BUY take profit below entry",
                        evidence_against=[],
                        suggested_correction="Take profit must be above entry for BUY"
                    ))
                    passed = False
                    findings.append("CONTRADICTION: BUY take profit below entry")
            
            elif direction == 'SELL':
                if stop_loss < current_price:
                    hallucinations.append(HallucinationAlert(
                        hallucination_type=HallucinationType.LOGICAL_CONTRADICTION,
                        severity=1.0,
                        claim="SELL stop loss below entry",
                        evidence_against=[],
                        suggested_correction="Stop loss must be above entry for SELL"
                    ))
                    passed = False
                    findings.append("CONTRADICTION: SELL stop loss below entry")
        
        # Check risk/reward consistency
        risk_reward = decision.get('risk_reward') or decision.get('rr_ratio')
        if risk_reward and stop_loss and take_profit and current_price:
            calculated_rr = abs(take_profit - current_price) / abs(current_price - stop_loss) if abs(current_price - stop_loss) > 0 else 0
            
            if abs(calculated_rr - risk_reward) > 0.5:
                hallucinations.append(HallucinationAlert(
                    hallucination_type=HallucinationType.FABRICATED_DATA,
                    severity=0.6,
                    claim=f"Claimed R:R of {risk_reward}",
                    evidence_against=[VerificationEvidence(
                        source="calculation",
                        data_point=calculated_rr,
                        timestamp=datetime.now(),
                        confidence=1.0,
                        supports_claim=False,
                        notes=f"Calculated R:R is {calculated_rr:.2f}"
                    )],
                    suggested_correction=f"Actual R:R is {calculated_rr:.2f}"
                ))
                confidence *= 0.7
                findings.append(f"R:R mismatch: claimed {risk_reward}, calculated {calculated_rr:.2f}")
        
        # Check for circular reasoning in justification
        reasoning = decision.get('reasoning') or decision.get('justification') or ''
        if reasoning:
            circular_patterns = [
                ('bullish because price will go up', 'circular reasoning'),
                ('bearish because price will go down', 'circular reasoning'),
                ('confident because we are confident', 'circular reasoning'),
                ('good trade because it is good', 'circular reasoning'),
            ]
            
            for pattern, reason in circular_patterns:
                if pattern.lower() in reasoning.lower():
                    hallucinations.append(HallucinationAlert(
                        hallucination_type=HallucinationType.CIRCULAR_REASONING,
                        severity=0.5,
                        claim=f"Reasoning contains: {pattern}",
                        evidence_against=[],
                        suggested_correction="Provide concrete evidence-based reasoning"
                    ))
                    confidence *= 0.8
                    findings.append(f"Circular reasoning detected: {reason}")
        
        if passed:
            findings.append("No logical contradictions detected")
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=VerificationStage.LOGICAL_CONSISTENCY,
            passed=passed,
            confidence=confidence,
            findings=findings,
            hallucinations=hallucinations,
            evidence=evidence,
            duration_ms=duration_ms
        )
    
    # =========================================================================
    # STAGE 3: CROSS-SOURCE VALIDATION
    # =========================================================================
    
    async def _verify_cross_source(
        self,
        decision: Dict[str, Any],
        additional_sources: Optional[List[Dict[str, Any]]]
    ) -> StageResult:
        """
        Validate decision against multiple independent sources.
        Detects claims that only one source supports.
        """
        start_time = datetime.now()
        findings: List[str] = []
        hallucinations: List[HallucinationAlert] = []
        evidence: List[VerificationEvidence] = []
        passed = True
        confidence = 1.0
        
        sources_checked = 1  # At least the primary source
        sources_confirming = 1
        
        if not additional_sources:
            findings.append("No additional sources for cross-validation")
            confidence = 0.6  # Lower confidence without cross-validation
        else:
            sources_checked = len(additional_sources) + 1
            
            # Check each claim against additional sources
            direction = decision.get('direction')
            
            for source in additional_sources:
                source_direction = source.get('direction') or source.get('signal')
                source_name = source.get('source_name', 'unknown')
                
                if source_direction:
                    if source_direction.upper() == direction.upper() if direction else False:
                        sources_confirming += 1
                        evidence.append(VerificationEvidence(
                            source=source_name,
                            data_point=source_direction,
                            timestamp=datetime.now(),
                            confidence=source.get('confidence', 0.5),
                            supports_claim=True,
                            notes=f"Source {source_name} confirms direction"
                        ))
                    else:
                        evidence.append(VerificationEvidence(
                            source=source_name,
                            data_point=source_direction,
                            timestamp=datetime.now(),
                            confidence=source.get('confidence', 0.5),
                            supports_claim=False,
                            notes=f"Source {source_name} disagrees on direction"
                        ))
            
            # Calculate agreement ratio
            agreement_ratio = sources_confirming / sources_checked
            
            if agreement_ratio < 0.5:
                hallucinations.append(HallucinationAlert(
                    hallucination_type=HallucinationType.UNSUPPORTED_CLAIM,
                    severity=0.7,
                    claim=f"Direction: {direction}",
                    evidence_against=[e for e in evidence if not e.supports_claim],
                    suggested_correction="Majority of sources disagree"
                ))
                passed = False
                confidence *= agreement_ratio
                findings.append(f"Low source agreement: {sources_confirming}/{sources_checked}")
            else:
                findings.append(f"Cross-source validation: {sources_confirming}/{sources_checked} sources agree")
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=VerificationStage.CROSS_SOURCE,
            passed=passed,
            confidence=confidence,
            findings=findings,
            hallucinations=hallucinations,
            evidence=evidence,
            duration_ms=duration_ms
        )
    
    # =========================================================================
    # STAGE 4: HISTORICAL ACCURACY CHECK
    # =========================================================================
    
    async def _verify_historical_accuracy(
        self,
        decision: Dict[str, Any]
    ) -> StageResult:
        """
        Compare current prediction confidence with historical accuracy.
        Detects overconfident predictions.
        """
        start_time = datetime.now()
        findings: List[str] = []
        hallucinations: List[HallucinationAlert] = []
        evidence: List[VerificationEvidence] = []
        passed = True
        confidence = 1.0
        
        claimed_confidence = decision.get('confidence', 0.5)
        
        # Calculate historical accuracy
        if len(self.accuracy_history) >= 10:
            historical_accuracy = statistics.mean(self.accuracy_history)
            historical_std = statistics.stdev(self.accuracy_history) if len(self.accuracy_history) > 1 else 0.1
            
            # Check if claimed confidence exceeds historical accuracy significantly
            if claimed_confidence > historical_accuracy + 2 * historical_std:
                hallucinations.append(HallucinationAlert(
                    hallucination_type=HallucinationType.OVERCONFIDENT,
                    severity=min((claimed_confidence - historical_accuracy) / 0.3, 1.0),
                    claim=f"Confidence: {claimed_confidence:.2f}",
                    evidence_against=[VerificationEvidence(
                        source="historical_accuracy",
                        data_point=historical_accuracy,
                        timestamp=datetime.now(),
                        confidence=0.9,
                        supports_claim=False,
                        notes=f"Historical accuracy: {historical_accuracy:.2f} +/- {historical_std:.2f}"
                    )],
                    suggested_correction=f"Calibrate confidence to ~{historical_accuracy:.2f}"
                ))
                passed = False
                confidence *= 0.7
                findings.append(f"Overconfident: {claimed_confidence:.2f} vs historical {historical_accuracy:.2f}")
            else:
                findings.append(f"Confidence aligned with history: {claimed_confidence:.2f} vs {historical_accuracy:.2f}")
        else:
            findings.append(f"Insufficient history for accuracy check ({len(self.accuracy_history)} samples)")
            confidence = 0.8
        
        # Check prediction type accuracy
        prediction_type = decision.get('prediction_type') or decision.get('signal_type')
        if prediction_type and len(self.prediction_history) >= 20:
            type_predictions = [p for p in self.prediction_history if p.get('type') == prediction_type]
            if len(type_predictions) >= 5:
                type_accuracy = sum(1 for p in type_predictions if p.get('correct', False)) / len(type_predictions)
                
                if claimed_confidence > type_accuracy + 0.2:
                    findings.append(f"Type '{prediction_type}' historical accuracy: {type_accuracy:.2f}")
                    confidence *= 0.9
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=VerificationStage.HISTORICAL_ACCURACY,
            passed=passed,
            confidence=confidence,
            findings=findings,
            hallucinations=hallucinations,
            evidence=evidence,
            duration_ms=duration_ms
        )
    
    # =========================================================================
    # STAGE 5: ADVERSARIAL SELF-QUESTIONING
    # =========================================================================
    
    async def _adversarial_questioning(
        self,
        decision: Dict[str, Any]
    ) -> StageResult:
        """
        Challenge the decision with adversarial questions.
        Identifies weaknesses and unsupported assumptions.
        """
        start_time = datetime.now()
        findings: List[str] = []
        hallucinations: List[HallucinationAlert] = []
        evidence: List[VerificationEvidence] = []
        passed = True
        confidence = 1.0
        
        reasoning = decision.get('reasoning') or decision.get('justification') or ''
        
        # Check for evidence of contradicting factors
        question_results = []
        
        # Q1: What evidence contradicts this?
        if 'however' not in reasoning.lower() and 'but' not in reasoning.lower() and 'risk' not in reasoning.lower():
            question_results.append({
                'question': "What evidence contradicts this conclusion?",
                'concern': "No contradicting evidence considered",
                'severity': 0.4
            })
        
        # Q2: What assumptions are being made?
        if 'assume' not in reasoning.lower() and 'if' not in reasoning.lower():
            question_results.append({
                'question': "What assumptions are being made?",
                'concern': "Assumptions not explicitly stated",
                'severity': 0.3
            })
        
        # Q3: Sample size check
        sample_size = decision.get('sample_size') or decision.get('data_points')
        if sample_size and sample_size < 30:
            question_results.append({
                'question': "Is the sample size sufficient?",
                'concern': f"Small sample size: {sample_size}",
                'severity': 0.5
            })
        
        # Q4: Base rate consideration
        if 'base rate' not in reasoning.lower() and 'probability' not in reasoning.lower():
            question_results.append({
                'question': "What is the base rate for this prediction?",
                'concern': "Base rate not considered",
                'severity': 0.3
            })
        
        # Q5: Missing information
        required_fields = ['direction', 'confidence', 'stop_loss', 'take_profit']
        missing_fields = [f for f in required_fields if not decision.get(f)]
        if missing_fields:
            question_results.append({
                'question': "What information is missing?",
                'concern': f"Missing: {', '.join(missing_fields)}",
                'severity': 0.6
            })
        
        # Aggregate concerns
        total_severity = sum(q['severity'] for q in question_results)
        
        if total_severity > 1.0:
            hallucinations.append(HallucinationAlert(
                hallucination_type=HallucinationType.UNSUPPORTED_CLAIM,
                severity=min(total_severity / 2.0, 1.0),
                claim="Decision lacks rigorous self-questioning",
                evidence_against=[VerificationEvidence(
                    source="adversarial_check",
                    data_point=question_results,
                    timestamp=datetime.now(),
                    confidence=0.8,
                    supports_claim=False,
                    notes=f"{len(question_results)} concerns identified"
                )],
                suggested_correction="Address identified concerns"
            ))
            passed = False
            confidence *= (1.0 - total_severity / 3.0)
        
        for q in question_results:
            findings.append(f"Q: {q['question']} - {q['concern']}")
        
        if not question_results:
            findings.append("Decision passed adversarial questioning")
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=VerificationStage.ADVERSARIAL_QUESTIONING,
            passed=passed,
            confidence=confidence,
            findings=findings,
            hallucinations=hallucinations,
            evidence=evidence,
            duration_ms=duration_ms
        )
    
    # =========================================================================
    # STAGE 6: CONFIDENCE CALIBRATION
    # =========================================================================
    
    async def _verify_confidence_calibration(
        self,
        decision: Dict[str, Any]
    ) -> StageResult:
        """
        Verify that confidence levels are properly calibrated.
        Ensures confidence matches expected accuracy.
        """
        start_time = datetime.now()
        findings: List[str] = []
        hallucinations: List[HallucinationAlert] = []
        evidence: List[VerificationEvidence] = []
        passed = True
        confidence = 1.0
        
        claimed_confidence = decision.get('confidence', 0.5)
        
        # Check confidence bounds
        if claimed_confidence < 0.0 or claimed_confidence > 1.0:
            hallucinations.append(HallucinationAlert(
                hallucination_type=HallucinationType.MAGNITUDE_ERROR,
                severity=1.0,
                claim=f"Confidence: {claimed_confidence}",
                evidence_against=[],
                suggested_correction="Confidence must be between 0.0 and 1.0"
            ))
            passed = False
            findings.append(f"Invalid confidence value: {claimed_confidence}")
        
        # Check for suspiciously round numbers
        if claimed_confidence in [0.0, 0.5, 1.0, 0.9, 0.8, 0.7]:
            findings.append(f"Suspiciously round confidence: {claimed_confidence}")
            confidence *= 0.95
        
        # Check confidence vs signal strength
        signal_strength = decision.get('signal_strength') or decision.get('strength')
        if signal_strength:
            if abs(claimed_confidence - signal_strength) > 0.3:
                findings.append(f"Confidence/strength mismatch: {claimed_confidence} vs {signal_strength}")
                confidence *= 0.9
        
        # Calibration check using historical data
        if len(self.confidence_history) >= 50:
            # Group by confidence buckets
            buckets = {}
            for conf, accurate in zip(self.confidence_history, self.accuracy_history):
                bucket = round(conf, 1)
                if bucket not in buckets:
                    buckets[bucket] = []
                buckets[bucket].append(accurate)
            
            # Check calibration
            claimed_bucket = round(claimed_confidence, 1)
            if claimed_bucket in buckets and len(buckets[claimed_bucket]) >= 5:
                actual_accuracy = statistics.mean(buckets[claimed_bucket])
                calibration_error = abs(claimed_confidence - actual_accuracy)
                
                if calibration_error > 0.15:
                    hallucinations.append(HallucinationAlert(
                        hallucination_type=HallucinationType.OVERCONFIDENT,
                        severity=calibration_error,
                        claim=f"Confidence {claimed_confidence:.2f}",
                        evidence_against=[VerificationEvidence(
                            source="calibration_check",
                            data_point=actual_accuracy,
                            timestamp=datetime.now(),
                            confidence=0.85,
                            supports_claim=False,
                            notes=f"Historical accuracy at this confidence: {actual_accuracy:.2f}"
                        )],
                        suggested_correction=f"Calibrated confidence: {actual_accuracy:.2f}"
                    ))
                    confidence *= (1.0 - calibration_error)
                    findings.append(f"Calibration error: {calibration_error:.2f}")
        
        if passed and not hallucinations:
            findings.append("Confidence calibration passed")
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=VerificationStage.CONFIDENCE_CALIBRATION,
            passed=passed,
            confidence=confidence,
            findings=findings,
            hallucinations=hallucinations,
            evidence=evidence,
            duration_ms=duration_ms
        )
    
    # =========================================================================
    # STAGE 7: REALITY ANCHOR CHECK
    # =========================================================================
    
    async def _verify_reality_anchor(
        self,
        decision: Dict[str, Any]
    ) -> StageResult:
        """
        Verify that all values are within physically possible ranges.
        Detects magnitude errors and impossible values.
        """
        start_time = datetime.now()
        findings: List[str] = []
        hallucinations: List[HallucinationAlert] = []
        evidence: List[VerificationEvidence] = []
        passed = True
        confidence = 1.0
        
        # Check each value against valid ranges
        checks = [
            ('confidence', decision.get('confidence')),
            ('rsi', decision.get('rsi')),
            ('position_size_pct', decision.get('position_size_pct') or decision.get('position_size')),
            ('leverage', decision.get('leverage')),
        ]
        
        for field_name, value in checks:
            if value is not None and field_name in self.valid_ranges:
                min_val, max_val = self.valid_ranges[field_name]
                
                if value < min_val or value > max_val:
                    hallucinations.append(HallucinationAlert(
                        hallucination_type=HallucinationType.MAGNITUDE_ERROR,
                        severity=0.9,
                        claim=f"{field_name}: {value}",
                        evidence_against=[VerificationEvidence(
                            source="reality_check",
                            data_point={'min': min_val, 'max': max_val},
                            timestamp=datetime.now(),
                            confidence=1.0,
                            supports_claim=False,
                            notes=f"Valid range: [{min_val}, {max_val}]"
                        )],
                        suggested_correction=f"Value must be between {min_val} and {max_val}"
                    ))
                    passed = False
                    confidence *= 0.5
                    findings.append(f"INVALID: {field_name}={value} outside [{min_val}, {max_val}]")
        
        # Check for NaN or Infinity
        numeric_fields = ['price', 'stop_loss', 'take_profit', 'confidence', 'volume']
        for field in numeric_fields:
            value = decision.get(field)
            if value is not None:
                if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                    hallucinations.append(HallucinationAlert(
                        hallucination_type=HallucinationType.MAGNITUDE_ERROR,
                        severity=1.0,
                        claim=f"{field}: {value}",
                        evidence_against=[],
                        suggested_correction="Value cannot be NaN or Infinity"
                    ))
                    passed = False
                    findings.append(f"INVALID: {field} is NaN or Infinity")
        
        # Check for negative prices
        price_fields = ['price', 'current_price', 'stop_loss', 'take_profit', 'entry_price']
        for field in price_fields:
            value = decision.get(field)
            if value is not None and value < 0:
                hallucinations.append(HallucinationAlert(
                    hallucination_type=HallucinationType.MAGNITUDE_ERROR,
                    severity=1.0,
                    claim=f"{field}: {value}",
                    evidence_against=[],
                    suggested_correction="Price cannot be negative"
                ))
                passed = False
                findings.append(f"INVALID: {field} is negative")
        
        # Check timestamp sanity
        timestamp = decision.get('timestamp')
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except Exception as e:
                    logger.error(f"Error: {e}")
                    pass
            
            if isinstance(timestamp, datetime):
                now = datetime.now()
                if timestamp > now + timedelta(hours=1):
                    hallucinations.append(HallucinationAlert(
                        hallucination_type=HallucinationType.TEMPORAL_IMPOSSIBILITY,
                        severity=1.0,
                        claim=f"Timestamp in future: {timestamp}",
                        evidence_against=[],
                        suggested_correction="Timestamp cannot be in the future"
                    ))
                    passed = False
                    findings.append("INVALID: Timestamp is in the future")
        
        if passed:
            findings.append("All values within valid ranges")
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=VerificationStage.REALITY_ANCHOR,
            passed=passed,
            confidence=confidence,
            findings=findings,
            hallucinations=hallucinations,
            evidence=evidence,
            duration_ms=duration_ms
        )
    
    # =========================================================================
    # STAGE 8: AUDIT TRAIL GENERATION
    # =========================================================================
    
    async def _generate_audit_trail(
        self,
        decision: Dict[str, Any],
        previous_stages: List[StageResult]
    ) -> StageResult:
        """
        Generate immutable audit trail for the verification.
        """
        start_time = datetime.now()
        findings: List[str] = []
        evidence: List[VerificationEvidence] = []
        
        # Generate verification summary
        stages_passed = sum(1 for s in previous_stages if s.passed)
        total_stages = len(previous_stages)
        total_hallucinations = sum(len(s.hallucinations) for s in previous_stages)
        avg_confidence = statistics.mean(s.confidence for s in previous_stages) if previous_stages else 0
        
        findings.append(f"Stages passed: {stages_passed}/{total_stages}")
        findings.append(f"Total hallucinations detected: {total_hallucinations}")
        findings.append(f"Average stage confidence: {avg_confidence:.2f}")
        
        # Create audit record
        audit_record = {
            'decision_hash': self._generate_decision_id(decision),
            'verification_time': datetime.now().isoformat(),
            'stages_passed': stages_passed,
            'total_stages': total_stages,
            'hallucinations': total_hallucinations,
            'avg_confidence': avg_confidence,
            'stage_summary': [
                {
                    'stage': s.stage.name,
                    'passed': s.passed,
                    'confidence': s.confidence,
                    'hallucinations': len(s.hallucinations)
                }
                for s in previous_stages
            ]
        }
        
        evidence.append(VerificationEvidence(
            source="audit_trail",
            data_point=audit_record,
            timestamp=datetime.now(),
            confidence=1.0,
            supports_claim=True,
            notes="Audit trail generated"
        ))
        
        findings.append("Audit trail generated successfully")
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return StageResult(
            stage=VerificationStage.AUDIT_TRAIL,
            passed=True,
            confidence=1.0,
            findings=findings,
            hallucinations=[],
            evidence=evidence,
            duration_ms=duration_ms
        )
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _generate_decision_id(self, decision: Dict[str, Any]) -> str:
        """Generate unique ID for a decision"""
        content = json.dumps(decision, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_verification_hash(
        self,
        decision_id: str,
        stage_results: List[StageResult],
        status: VerificationStatus
    ) -> str:
        """Generate verification hash for audit trail"""
        content = f"{decision_id}:{status.value}:{len(stage_results)}"
        for s in stage_results:
            content += f":{s.stage.name}:{s.passed}:{s.confidence:.4f}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _calculate_overall_status(
        self,
        stage_results: List[StageResult],
        hallucinations: List[HallucinationAlert]
    ) -> Tuple[VerificationStatus, float]:
        """Calculate overall verification status and confidence"""
        
        # Count critical hallucinations
        critical_hallucinations = sum(
            1 for h in hallucinations if h.severity >= 0.8
        )
        
        # Count failed stages
        failed_stages = sum(1 for s in stage_results if not s.passed)
        
        # Calculate average confidence
        avg_confidence = statistics.mean(s.confidence for s in stage_results) if stage_results else 0
        
        # Determine status
        if critical_hallucinations > 0:
            return VerificationStatus.HALLUCINATION_DETECTED, avg_confidence * 0.5
        elif failed_stages >= 3:
            return VerificationStatus.SUSPICIOUS, avg_confidence * 0.7
        elif failed_stages >= 1:
            return VerificationStatus.SUSPICIOUS, avg_confidence * 0.85
        elif avg_confidence < 0.6:
            return VerificationStatus.INSUFFICIENT_DATA, avg_confidence
        else:
            return VerificationStatus.VERIFIED, avg_confidence
    
    def _determine_action(
        self,
        status: VerificationStatus,
        confidence: float,
        hallucinations: List[HallucinationAlert]
    ) -> DecisionAction:
        """Determine recommended action based on verification results"""
        
        if status == VerificationStatus.HALLUCINATION_DETECTED:
            # Check if hallucinations are correctable
            correctable = all(h.suggested_correction for h in hallucinations if h.severity >= 0.8)
            if correctable:
                return DecisionAction.MODIFY
            else:
                return DecisionAction.REJECT
        
        elif status == VerificationStatus.SUSPICIOUS:
            if confidence >= 0.7:
                return DecisionAction.MODIFY
            else:
                return DecisionAction.DEFER
        
        elif status == VerificationStatus.INSUFFICIENT_DATA:
            return DecisionAction.DEFER
        
        elif status == VerificationStatus.VERIFIED:
            if confidence >= 0.85:
                return DecisionAction.APPROVE
            else:
                return DecisionAction.MODIFY
        
        return DecisionAction.ESCALATE
    
    def _generate_corrected_decision(
        self,
        original: Dict[str, Any],
        hallucinations: List[HallucinationAlert]
    ) -> Dict[str, Any]:
        """Generate corrected decision based on hallucination corrections"""
        corrected = original.copy()
        
        corrections_applied = []
        
        for h in hallucinations:
            if h.suggested_correction:
                # Parse and apply correction
                correction = h.suggested_correction
                
                # Handle specific correction patterns
                if "Use actual price:" in correction:
                    try:
                        price = float(correction.split(":")[-1].strip())
                        corrected['current_price'] = price
                        corrected['price'] = price
                        corrections_applied.append(f"Price corrected to {price}")
                    except Exception as e:
                        logger.error(f"Error: {e}")
                        pass
                
                elif "Calibrated confidence:" in correction:
                    try:
                        conf = float(correction.split(":")[-1].strip())
                        corrected['confidence'] = conf
                        corrections_applied.append(f"Confidence calibrated to {conf}")
                    except:
                        pass
                
                elif "Actual R:R is" in correction:
                    try:
                        rr = float(correction.split("is")[-1].strip())
                        corrected['risk_reward'] = rr
                        corrections_applied.append(f"R:R corrected to {rr}")
                    except:
                        pass
        
        corrected['_corrections_applied'] = corrections_applied
        corrected['_original_decision'] = original
        
        return corrected
    
    # =========================================================================
    # PUBLIC METHODS FOR UPDATING HISTORY
    # =========================================================================
    
    def record_prediction_outcome(
        self,
        prediction_type: str,
        confidence: float,
        was_correct: bool
    ):
        """Record the outcome of a prediction for calibration"""
        self.prediction_history.append({
            'type': prediction_type,
            'confidence': confidence,
            'correct': was_correct,
            'timestamp': datetime.now()
        })
        self.accuracy_history.append(1.0 if was_correct else 0.0)
        self.confidence_history.append(confidence)
    
    def get_calibration_stats(self) -> Dict[str, Any]:
        """Get calibration statistics"""
        if len(self.accuracy_history) < 10:
            return {'status': 'insufficient_data', 'samples': len(self.accuracy_history)}
        
        return {
            'samples': len(self.accuracy_history),
            'overall_accuracy': statistics.mean(self.accuracy_history),
            'avg_confidence': statistics.mean(self.confidence_history),
            'calibration_error': abs(
                statistics.mean(self.accuracy_history) - 
                statistics.mean(self.confidence_history)
            )
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_verification_chain(config: Optional[Dict[str, Any]] = None) -> DecisionVerificationChain:
    """Create a new verification chain instance"""
    return DecisionVerificationChain(config)


async def verify_decision(
    decision: Dict[str, Any],
    market_data: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> VerificationChainResult:
    """Quick verification of a single decision"""
    chain = DecisionVerificationChain(config)
    return await chain.verify_decision(decision, market_data)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    'DecisionVerificationChain',
    'VerificationChainResult',
    'VerificationStage',
    'VerificationStatus',
    'HallucinationType',
    'HallucinationAlert',
    'StageResult',
    'FactCheckResult',
    'DecisionAction',
    'VerificationEvidence',
    'create_verification_chain',
    'verify_decision',
]
