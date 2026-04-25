"""
Claim Challenger System

Automatically challenges suspicious claims before execution.
Implements adversarial testing to detect potential hallucinations and errors.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid
import random

logger = logging.getLogger(__name__)


class ChallengeType(Enum):
    """Types of challenges that can be raised."""
    EVIDENCE_INSUFFICIENCY = "evidence_insufficiency"
    LOGICAL_INCONSISTENCY = "logical_inconsistency"
    DATA_STALENESS = "data_staleness"
    SOURCE_UNRELIABILITY = "source_unreliability"
    STATISTICAL_ANOMALY = "statistical_anomaly"
    OVERCONFIDENCE = "overconfidence"
    MISSING_CONTEXT = "missing_context"
    CONTRADICTORY_EVIDENCE = "contradictory_evidence"
    HALLUCINATION_SUSPECTED = "hallucination_suspected"
    TEMPORAL_IMPOSSIBILITY = "temporal_impossibility"
    CAUSAL_FALLACY = "causal_fallacy"
    SURVIVORSHIP_BIAS = "survivorship_bias"


class ChallengeStatus(Enum):
    """Status of a challenge."""
    RAISED = "raised"
    UNDER_REVIEW = "under_review"
    UPHELD = "upheld"
    DISMISSED = "dismissed"
    PARTIALLY_UPHELD = "partially_upheld"
    ESCALATED = "escalated"


class ChallengeSeverity(Enum):
    """Severity levels for challenges."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Challenge:
    """
    A challenge raised against a claim.
    """
    challenge_id: str
    claim_id: str
    challenge_type: ChallengeType
    severity: ChallengeSeverity
    description: str
    evidence: Dict[str, Any]
    status: ChallengeStatus
    raised_at: datetime
    raised_by: str
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    requires_human_review: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'challenge_id': self.challenge_id,
            'claim_id': self.claim_id,
            'challenge_type': self.challenge_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'evidence': self.evidence,
            'status': self.status.value,
            'raised_at': self.raised_at.isoformat(),
            'raised_by': self.raised_by,
            'resolution': self.resolution,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'requires_human_review': self.requires_human_review,
        }


@dataclass
class ChallengeResult:
    """
    Result of challenge evaluation.
    """
    claim_id: str
    total_challenges: int
    upheld_challenges: int
    dismissed_challenges: int
    challenges: List[Challenge]
    overall_status: str
    confidence_adjustment: float
    recommendation: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'claim_id': self.claim_id,
            'total_challenges': self.total_challenges,
            'upheld_challenges': self.upheld_challenges,
            'dismissed_challenges': self.dismissed_challenges,
            'challenges': [c.to_dict() for c in self.challenges],
            'overall_status': self.overall_status,
            'confidence_adjustment': self.confidence_adjustment,
            'recommendation': self.recommendation,
            'timestamp': self.timestamp.isoformat(),
        }


class ClaimChallenger:
    """
    System that automatically challenges claims before execution.
    
    Provides:
    - Automatic challenge generation
    - Multi-dimensional claim analysis
    - Hallucination detection
    - Confidence calibration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'claim_challenger_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._challenges: Dict[str, Challenge] = {}
        self._challenge_history: List[ChallengeResult] = []
        
        self._challenge_thresholds = {
            'confidence_too_high': 0.98,
            'confidence_too_low': 0.3,
            'min_evidence_count': 2,
            'max_data_age_seconds': 300,
            'min_source_trust': 0.7,
            'statistical_anomaly_zscore': 3.0,
        }
        
        self._severity_weights = {
            ChallengeSeverity.LOW: 0.1,
            ChallengeSeverity.MEDIUM: 0.25,
            ChallengeSeverity.HIGH: 0.5,
            ChallengeSeverity.CRITICAL: 1.0,
        }
        
        self._challenge_generators: Dict[ChallengeType, Callable] = {
            ChallengeType.EVIDENCE_INSUFFICIENCY: self._check_evidence_sufficiency,
            ChallengeType.LOGICAL_INCONSISTENCY: self._check_logical_consistency,
            ChallengeType.DATA_STALENESS: self._check_data_freshness,
            ChallengeType.SOURCE_UNRELIABILITY: self._check_source_reliability,
            ChallengeType.STATISTICAL_ANOMALY: self._check_statistical_validity,
            ChallengeType.OVERCONFIDENCE: self._check_overconfidence,
            ChallengeType.MISSING_CONTEXT: self._check_context_completeness,
            ChallengeType.CONTRADICTORY_EVIDENCE: self._check_evidence_consistency,
            ChallengeType.HALLUCINATION_SUSPECTED: self._check_hallucination_indicators,
            ChallengeType.TEMPORAL_IMPOSSIBILITY: self._check_temporal_validity,
            ChallengeType.CAUSAL_FALLACY: self._check_causal_reasoning,
            ChallengeType.SURVIVORSHIP_BIAS: self._check_survivorship_bias,
        }
        
        logger.info("✅ Claim Challenger initialized")
    
    async def challenge_claim(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> ChallengeResult:
        """
        Challenge a claim by running all challenge generators.
        
        Args:
            claim: The claim to challenge
            evidence: Supporting evidence
            context: Additional context
        
        Returns:
            ChallengeResult with all challenges found
        """
        claim_id = claim.get('claim_id', f"CLM-{uuid.uuid4().hex[:12]}")
        challenges = []
        
        for challenge_type, generator in self._challenge_generators.items():
            try:
                challenge = await generator(claim, evidence, context)
                if challenge:
                    challenges.append(challenge)
                    self._challenges[challenge.challenge_id] = challenge
            except Exception as e:
                logger.error(f"Challenge generator {challenge_type.value} failed: {e}")
        
        for challenge in challenges:
            await self._evaluate_challenge(challenge, claim, evidence)
        
        upheld = [c for c in challenges if c.status == ChallengeStatus.UPHELD]
        dismissed = [c for c in challenges if c.status == ChallengeStatus.DISMISSED]
        
        confidence_adjustment = self._calculate_confidence_adjustment(challenges)
        
        if any(c.severity == ChallengeSeverity.CRITICAL and c.status == ChallengeStatus.UPHELD for c in challenges):
            overall_status = "BLOCKED"
            recommendation = "Claim should not proceed - critical issues found"
        elif len(upheld) > len(challenges) / 2:
            overall_status = "REJECTED"
            recommendation = "Claim has significant issues - recommend rejection"
        elif len(upheld) > 0:
            overall_status = "CONDITIONAL"
            recommendation = "Claim may proceed with caution - address raised concerns"
        else:
            overall_status = "APPROVED"
            recommendation = "Claim passed challenge review"
        
        result = ChallengeResult(
            claim_id=claim_id,
            total_challenges=len(challenges),
            upheld_challenges=len(upheld),
            dismissed_challenges=len(dismissed),
            challenges=challenges,
            overall_status=overall_status,
            confidence_adjustment=confidence_adjustment,
            recommendation=recommendation,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._challenge_history.append(result)
        await self._persist_result(result)
        
        logger.info(f"Challenge result for {claim_id}: {overall_status} "
                   f"({len(upheld)}/{len(challenges)} upheld)")
        
        return result
    
    async def _check_evidence_sufficiency(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check if there is sufficient evidence for the claim."""
        min_evidence = self._challenge_thresholds['min_evidence_count']
        
        if len(evidence) < min_evidence:
            return Challenge(
                challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                claim_id=claim.get('claim_id', 'unknown'),
                challenge_type=ChallengeType.EVIDENCE_INSUFFICIENCY,
                severity=ChallengeSeverity.HIGH if len(evidence) == 0 else ChallengeSeverity.MEDIUM,
                description=f"Claim has only {len(evidence)} evidence items, minimum required is {min_evidence}",
                evidence={
                    'evidence_count': len(evidence),
                    'minimum_required': min_evidence,
                },
                status=ChallengeStatus.RAISED,
                raised_at=datetime.now(timezone.utc),
                raised_by="evidence_sufficiency_checker",
            )
        
        return None
    
    async def _check_logical_consistency(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check for logical inconsistencies in the claim."""
        if 'reasoning_chain' in claim:
            chain = claim['reasoning_chain']
            
            for i, step in enumerate(chain):
                if i > 0:
                    prev_conclusion = chain[i-1].get('conclusion', '')
                    curr_premise = step.get('premise', '')
                    
                    if prev_conclusion and curr_premise:
                        if not self._logical_connection_exists(prev_conclusion, curr_premise):
                            return Challenge(
                                challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                                claim_id=claim.get('claim_id', 'unknown'),
                                challenge_type=ChallengeType.LOGICAL_INCONSISTENCY,
                                severity=ChallengeSeverity.HIGH,
                                description=f"Logical gap detected between steps {i} and {i+1}",
                                evidence={
                                    'step': i,
                                    'previous_conclusion': prev_conclusion,
                                    'current_premise': curr_premise,
                                },
                                status=ChallengeStatus.RAISED,
                                raised_at=datetime.now(timezone.utc),
                                raised_by="logical_consistency_checker",
                            )
        
        return None
    
    def _logical_connection_exists(self, conclusion: str, premise: str) -> bool:
        """Check if there's a logical connection between conclusion and premise."""
        conclusion_lower = conclusion.lower()
        premise_lower = premise.lower()
        
        conclusion_words = set(conclusion_lower.split())
        premise_words = set(premise_lower.split())
        
        common_words = conclusion_words & premise_words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        meaningful_common = common_words - stopwords
        
        return len(meaningful_common) > 0
    
    async def _check_data_freshness(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check if evidence data is fresh enough."""
        max_age = self._challenge_thresholds['max_data_age_seconds']
        now = datetime.now(timezone.utc)
        
        stale_evidence = []
        for e in evidence:
            if 'timestamp' in e:
                try:
                    if isinstance(e['timestamp'], str):
                        e_time = datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00'))
                    else:
                        e_time = e['timestamp']
                    
                    if e_time.tzinfo is None:
                        e_time = e_time.replace(tzinfo=timezone.utc)
                    
                    age = (now - e_time).total_seconds()
                    if age > max_age:
                        stale_evidence.append({
                            'evidence_id': e.get('evidence_id', 'unknown'),
                            'age_seconds': age,
                        })
                except Exception:
                    pass
        
        if stale_evidence:
            return Challenge(
                challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                claim_id=claim.get('claim_id', 'unknown'),
                challenge_type=ChallengeType.DATA_STALENESS,
                severity=ChallengeSeverity.MEDIUM,
                description=f"{len(stale_evidence)} evidence items are older than {max_age} seconds",
                evidence={
                    'stale_items': stale_evidence,
                    'max_age_threshold': max_age,
                },
                status=ChallengeStatus.RAISED,
                raised_at=datetime.now(timezone.utc),
                raised_by="data_freshness_checker",
            )
        
        return None
    
    async def _check_source_reliability(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check if evidence sources are reliable."""
        min_trust = self._challenge_thresholds['min_source_trust']
        
        unreliable_sources = []
        for e in evidence:
            trust_score = e.get('metadata', {}).get('source_trust_score', 
                         e.get('confidence_score', 0.5))
            
            if trust_score < min_trust:
                unreliable_sources.append({
                    'evidence_id': e.get('evidence_id', 'unknown'),
                    'source': e.get('source_name', 'unknown'),
                    'trust_score': trust_score,
                })
        
        if unreliable_sources:
            severity = ChallengeSeverity.HIGH if len(unreliable_sources) > len(evidence) / 2 else ChallengeSeverity.MEDIUM
            
            return Challenge(
                challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                claim_id=claim.get('claim_id', 'unknown'),
                challenge_type=ChallengeType.SOURCE_UNRELIABILITY,
                severity=severity,
                description=f"{len(unreliable_sources)} evidence sources have trust scores below {min_trust}",
                evidence={
                    'unreliable_sources': unreliable_sources,
                    'min_trust_threshold': min_trust,
                },
                status=ChallengeStatus.RAISED,
                raised_at=datetime.now(timezone.utc),
                raised_by="source_reliability_checker",
            )
        
        return None
    
    async def _check_statistical_validity(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check for statistical anomalies in the claim."""
        if 'statistical_claim' in claim:
            stat = claim['statistical_claim']
            
            if 'zscore' in stat:
                zscore_threshold = self._challenge_thresholds['statistical_anomaly_zscore']
                if abs(stat['zscore']) > zscore_threshold:
                    return Challenge(
                        challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                        claim_id=claim.get('claim_id', 'unknown'),
                        challenge_type=ChallengeType.STATISTICAL_ANOMALY,
                        severity=ChallengeSeverity.HIGH,
                        description=f"Statistical claim has z-score of {stat['zscore']}, exceeding threshold of {zscore_threshold}",
                        evidence={
                            'zscore': stat['zscore'],
                            'threshold': zscore_threshold,
                        },
                        status=ChallengeStatus.RAISED,
                        raised_at=datetime.now(timezone.utc),
                        raised_by="statistical_validity_checker",
                    )
        
        return None
    
    async def _check_overconfidence(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check for overconfidence in predictions."""
        confidence = claim.get('confidence', claim.get('certainty', 0))
        threshold = self._challenge_thresholds['confidence_too_high']
        
        if confidence > threshold:
            evidence_confidence = [e.get('confidence_score', 0.5) for e in evidence]
            avg_evidence_confidence = sum(evidence_confidence) / len(evidence_confidence) if evidence_confidence else 0
            
            if confidence > avg_evidence_confidence + 0.2:
                return Challenge(
                    challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                    claim_id=claim.get('claim_id', 'unknown'),
                    challenge_type=ChallengeType.OVERCONFIDENCE,
                    severity=ChallengeSeverity.MEDIUM,
                    description=f"Claim confidence ({confidence:.2f}) significantly exceeds evidence confidence ({avg_evidence_confidence:.2f})",
                    evidence={
                        'claim_confidence': confidence,
                        'average_evidence_confidence': avg_evidence_confidence,
                        'threshold': threshold,
                    },
                    status=ChallengeStatus.RAISED,
                    raised_at=datetime.now(timezone.utc),
                    raised_by="overconfidence_checker",
                )
        
        return None
    
    async def _check_context_completeness(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check if necessary context is present."""
        required_context_fields = ['market_regime', 'risk_parameters', 'time_horizon']
        
        if context is None:
            return Challenge(
                challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                claim_id=claim.get('claim_id', 'unknown'),
                challenge_type=ChallengeType.MISSING_CONTEXT,
                severity=ChallengeSeverity.MEDIUM,
                description="Claim has no context provided",
                evidence={
                    'required_fields': required_context_fields,
                    'provided_fields': [],
                },
                status=ChallengeStatus.RAISED,
                raised_at=datetime.now(timezone.utc),
                raised_by="context_completeness_checker",
            )
        
        missing_fields = [f for f in required_context_fields if f not in context]
        
        if missing_fields:
            return Challenge(
                challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                claim_id=claim.get('claim_id', 'unknown'),
                challenge_type=ChallengeType.MISSING_CONTEXT,
                severity=ChallengeSeverity.LOW,
                description=f"Context missing fields: {', '.join(missing_fields)}",
                evidence={
                    'missing_fields': missing_fields,
                    'provided_fields': list(context.keys()),
                },
                status=ChallengeStatus.RAISED,
                raised_at=datetime.now(timezone.utc),
                raised_by="context_completeness_checker",
            )
        
        return None
    
    async def _check_evidence_consistency(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check for contradictions in evidence."""
        if len(evidence) < 2:
            return None
        
        price_evidence = [e for e in evidence if 'price' in e.get('content', {})]
        
        if len(price_evidence) >= 2:
            prices = [e['content']['price'] for e in price_evidence]
            avg_price = sum(prices) / len(prices)
            
            for i, price in enumerate(prices):
                deviation = abs(price - avg_price) / avg_price if avg_price > 0 else 0
                if deviation > 0.05:
                    return Challenge(
                        challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                        claim_id=claim.get('claim_id', 'unknown'),
                        challenge_type=ChallengeType.CONTRADICTORY_EVIDENCE,
                        severity=ChallengeSeverity.HIGH,
                        description=f"Price evidence shows {deviation*100:.1f}% deviation between sources",
                        evidence={
                            'prices': prices,
                            'average': avg_price,
                            'max_deviation': deviation,
                        },
                        status=ChallengeStatus.RAISED,
                        raised_at=datetime.now(timezone.utc),
                        raised_by="evidence_consistency_checker",
                    )
        
        return None
    
    async def _check_hallucination_indicators(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check for indicators of hallucination."""
        hallucination_indicators = []
        
        if claim.get('confidence', 0) > 0.99:
            hallucination_indicators.append("Unrealistically high confidence")
        
        if 'prediction' in claim:
            pred = claim['prediction']
            if pred.get('expected_return', 0) > 0.5:
                hallucination_indicators.append("Unrealistic expected return")
        
        if not evidence:
            hallucination_indicators.append("No supporting evidence")
        
        if 'source' in claim and claim['source'] == 'internal_generation':
            if not any(e.get('source_name') != 'internal' for e in evidence):
                hallucination_indicators.append("All evidence from internal sources only")
        
        if hallucination_indicators:
            severity = ChallengeSeverity.CRITICAL if len(hallucination_indicators) > 2 else ChallengeSeverity.HIGH
            
            return Challenge(
                challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                claim_id=claim.get('claim_id', 'unknown'),
                challenge_type=ChallengeType.HALLUCINATION_SUSPECTED,
                severity=severity,
                description=f"Potential hallucination detected: {'; '.join(hallucination_indicators)}",
                evidence={
                    'indicators': hallucination_indicators,
                    'indicator_count': len(hallucination_indicators),
                },
                status=ChallengeStatus.RAISED,
                raised_at=datetime.now(timezone.utc),
                raised_by="hallucination_detector",
                requires_human_review=severity == ChallengeSeverity.CRITICAL,
            )
        
        return None
    
    async def _check_temporal_validity(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check for temporal impossibilities."""
        if 'timestamp' in claim and evidence:
            try:
                if isinstance(claim['timestamp'], str):
                    claim_time = datetime.fromisoformat(claim['timestamp'].replace('Z', '+00:00'))
                else:
                    claim_time = claim['timestamp']
                
                for e in evidence:
                    if 'timestamp' in e:
                        if isinstance(e['timestamp'], str):
                            e_time = datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00'))
                        else:
                            e_time = e['timestamp']
                        
                        if e_time > claim_time:
                            return Challenge(
                                challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                                claim_id=claim.get('claim_id', 'unknown'),
                                challenge_type=ChallengeType.TEMPORAL_IMPOSSIBILITY,
                                severity=ChallengeSeverity.CRITICAL,
                                description="Evidence timestamp is after claim timestamp - temporal impossibility",
                                evidence={
                                    'claim_timestamp': claim_time.isoformat(),
                                    'evidence_timestamp': e_time.isoformat(),
                                    'evidence_id': e.get('evidence_id', 'unknown'),
                                },
                                status=ChallengeStatus.RAISED,
                                raised_at=datetime.now(timezone.utc),
                                raised_by="temporal_validity_checker",
                            )
            except Exception:
                pass
        
        return None
    
    async def _check_causal_reasoning(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check for causal fallacies."""
        if 'causal_claim' in claim:
            causal = claim['causal_claim']
            
            if causal.get('correlation_only', False):
                return Challenge(
                    challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                    claim_id=claim.get('claim_id', 'unknown'),
                    challenge_type=ChallengeType.CAUSAL_FALLACY,
                    severity=ChallengeSeverity.MEDIUM,
                    description="Causal claim based only on correlation",
                    evidence={
                        'causal_claim': causal,
                        'issue': 'correlation_not_causation',
                    },
                    status=ChallengeStatus.RAISED,
                    raised_at=datetime.now(timezone.utc),
                    raised_by="causal_reasoning_checker",
                )
        
        return None
    
    async def _check_survivorship_bias(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Challenge]:
        """Check for survivorship bias in analysis."""
        if 'backtest_results' in claim:
            backtest = claim['backtest_results']
            
            if not backtest.get('includes_delisted', False):
                return Challenge(
                    challenge_id=f"CHL-{uuid.uuid4().hex[:12]}",
                    claim_id=claim.get('claim_id', 'unknown'),
                    challenge_type=ChallengeType.SURVIVORSHIP_BIAS,
                    severity=ChallengeSeverity.MEDIUM,
                    description="Backtest may have survivorship bias - delisted securities not included",
                    evidence={
                        'backtest_period': backtest.get('period'),
                        'includes_delisted': False,
                    },
                    status=ChallengeStatus.RAISED,
                    raised_at=datetime.now(timezone.utc),
                    raised_by="survivorship_bias_checker",
                )
        
        return None
    
    async def _evaluate_challenge(
        self,
        challenge: Challenge,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ):
        """Evaluate a challenge and update its status."""
        if challenge.challenge_type == ChallengeType.HALLUCINATION_SUSPECTED:
            if len(challenge.evidence.get('indicators', [])) >= 2:
                challenge.status = ChallengeStatus.UPHELD
            else:
                challenge.status = ChallengeStatus.UNDER_REVIEW
        
        elif challenge.challenge_type == ChallengeType.TEMPORAL_IMPOSSIBILITY:
            challenge.status = ChallengeStatus.UPHELD
        
        elif challenge.challenge_type == ChallengeType.EVIDENCE_INSUFFICIENCY:
            if len(evidence) == 0:
                challenge.status = ChallengeStatus.UPHELD
            else:
                challenge.status = ChallengeStatus.PARTIALLY_UPHELD
        
        elif challenge.severity == ChallengeSeverity.CRITICAL:
            challenge.status = ChallengeStatus.UPHELD
        
        elif challenge.severity == ChallengeSeverity.HIGH:
            challenge.status = ChallengeStatus.UNDER_REVIEW
        
        else:
            challenge.status = ChallengeStatus.DISMISSED
    
    def _calculate_confidence_adjustment(self, challenges: List[Challenge]) -> float:
        """Calculate how much to adjust confidence based on challenges."""
        if not challenges:
            return 0.0
        
        total_penalty = 0.0
        
        for challenge in challenges:
            if challenge.status in [ChallengeStatus.UPHELD, ChallengeStatus.PARTIALLY_UPHELD]:
                weight = self._severity_weights.get(challenge.severity, 0.25)
                if challenge.status == ChallengeStatus.PARTIALLY_UPHELD:
                    weight *= 0.5
                total_penalty += weight
        
        return -min(total_penalty, 0.9)
    
    async def _persist_result(self, result: ChallengeResult):
        """Persist challenge result to storage."""
        result_file = self.storage_path / 'results' / f"{result.claim_id}_{result.timestamp.strftime('%Y%m%d%H%M%S')}.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
    
    def get_challenge(self, challenge_id: str) -> Optional[Challenge]:
        """Get a challenge by ID."""
        return self._challenges.get(challenge_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the challenger."""
        status_counts = {}
        type_counts = {}
        severity_counts = {}
        
        for challenge in self._challenges.values():
            status_counts[challenge.status.value] = status_counts.get(challenge.status.value, 0) + 1
            type_counts[challenge.challenge_type.value] = type_counts.get(challenge.challenge_type.value, 0) + 1
            severity_counts[challenge.severity.value] = severity_counts.get(challenge.severity.value, 0) + 1
        
        return {
            'total_challenges': len(self._challenges),
            'total_results': len(self._challenge_history),
            'challenges_by_status': status_counts,
            'challenges_by_type': type_counts,
            'challenges_by_severity': severity_counts,
        }
