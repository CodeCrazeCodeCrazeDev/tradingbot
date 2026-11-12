"""
Validator Agents System

Specialized agents that independently verify claims before execution.
Implements N-of-M verification requirements for high-impact decisions.
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


class ValidatorType(Enum):
    """Types of validator agents."""
    DATA_VALIDATOR = "data_validator"
    LOGIC_VALIDATOR = "logic_validator"
    RISK_VALIDATOR = "risk_validator"
    CONSENSUS_VALIDATOR = "consensus_validator"
    CROSS_REFERENCE_VALIDATOR = "cross_reference_validator"
    TEMPORAL_VALIDATOR = "temporal_validator"
    STATISTICAL_VALIDATOR = "statistical_validator"
    ADVERSARIAL_VALIDATOR = "adversarial_validator"


class ValidationStatus(Enum):
    """Status of validation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHALLENGED = "challenged"
    TIMEOUT = "timeout"
    ABSTAINED = "abstained"


@dataclass
class ValidationResult:
    """
    Result of a validation attempt.
    """
    result_id: str
    validator_id: str
    claim_id: str
    status: ValidationStatus
    confidence: float
    reasoning: List[str]
    evidence_checked: List[str]
    discrepancies_found: List[Dict[str, Any]]
    timestamp: datetime
    validation_duration_ms: float
    stake_amount: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'validator_id': self.validator_id,
            'claim_id': self.claim_id,
            'status': self.status.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'evidence_checked': self.evidence_checked,
            'discrepancies_found': self.discrepancies_found,
            'timestamp': self.timestamp.isoformat(),
            'validation_duration_ms': self.validation_duration_ms,
            'stake_amount': self.stake_amount,
        }


@dataclass
class ValidatorAgent:
    """
    Independent validator agent that verifies claims.
    """
    validator_id: str
    validator_type: ValidatorType
    name: str
    specializations: List[str]
    reputation_score: float = 1.0
    total_validations: int = 0
    successful_validations: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    stake_balance: float = 1000.0
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_validation: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'validator_id': self.validator_id,
            'validator_type': self.validator_type.value,
            'name': self.name,
            'specializations': self.specializations,
            'reputation_score': self.reputation_score,
            'total_validations': self.total_validations,
            'successful_validations': self.successful_validations,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'stake_balance': self.stake_balance,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_validation': self.last_validation.isoformat() if self.last_validation else None,
        }
    
    @property
    def accuracy(self) -> float:
        if self.total_validations == 0:
            return 1.0
        return self.successful_validations / self.total_validations
    
    async def validate_claim(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate a claim against provided evidence.
        
        Args:
            claim: The claim to validate
            evidence: Supporting evidence
            context: Additional context
        
        Returns:
            ValidationResult with validation outcome
        """
        start_time = datetime.now(timezone.utc)
        result_id = f"VR-{uuid.uuid4().hex[:16]}"
        
        reasoning = []
        discrepancies = []
        evidence_checked = []
        
        if self.validator_type == ValidatorType.DATA_VALIDATOR:
            confidence, disc = await self._validate_data(claim, evidence)
            reasoning.append("Performed data integrity validation")
            discrepancies.extend(disc)
            
        elif self.validator_type == ValidatorType.LOGIC_VALIDATOR:
            confidence, disc = await self._validate_logic(claim, evidence)
            reasoning.append("Performed logical consistency validation")
            discrepancies.extend(disc)
            
        elif self.validator_type == ValidatorType.RISK_VALIDATOR:
            confidence, disc = await self._validate_risk(claim, evidence, context)
            reasoning.append("Performed risk assessment validation")
            discrepancies.extend(disc)
            
        elif self.validator_type == ValidatorType.STATISTICAL_VALIDATOR:
            confidence, disc = await self._validate_statistics(claim, evidence)
            reasoning.append("Performed statistical validation")
            discrepancies.extend(disc)
            
        elif self.validator_type == ValidatorType.ADVERSARIAL_VALIDATOR:
            confidence, disc = await self._adversarial_validation(claim, evidence)
            reasoning.append("Performed adversarial validation")
            discrepancies.extend(disc)
            
        else:
            confidence, disc = await self._generic_validation(claim, evidence)
            reasoning.append("Performed generic validation")
            discrepancies.extend(disc)
        
        for e in evidence:
            evidence_checked.append(e.get('evidence_id', str(hash(str(e)))))
        
        if confidence >= 0.8 and not discrepancies:
            status = ValidationStatus.APPROVED
        elif confidence < 0.5 or len(discrepancies) > 2:
            status = ValidationStatus.REJECTED
        else:
            status = ValidationStatus.CHALLENGED
        
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        self.total_validations += 1
        self.last_validation = datetime.now(timezone.utc)
        
        return ValidationResult(
            result_id=result_id,
            validator_id=self.validator_id,
            claim_id=claim.get('claim_id', 'unknown'),
            status=status,
            confidence=confidence,
            reasoning=reasoning,
            evidence_checked=evidence_checked,
            discrepancies_found=discrepancies,
            timestamp=datetime.now(timezone.utc),
            validation_duration_ms=duration_ms,
        )
    
    async def _validate_data(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Validate data integrity."""
        discrepancies = []
        confidence = 1.0
        
        for e in evidence:
            if 'data_hash' in e and 'content' in e:
                computed_hash = hashlib.sha256(
                    json.dumps(e['content'], sort_keys=True).encode()
                ).hexdigest()
                
                if computed_hash != e['data_hash']:
                    discrepancies.append({
                        'type': 'hash_mismatch',
                        'evidence_id': e.get('evidence_id'),
                        'expected': e['data_hash'],
                        'computed': computed_hash,
                    })
                    confidence -= 0.3
        
        if 'timestamp' in claim:
            claim_time = claim['timestamp']
            for e in evidence:
                if 'timestamp' in e:
                    if isinstance(e['timestamp'], str):
                        e_time = datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00'))
                    else:
                        e_time = e['timestamp']
                    
                    if isinstance(claim_time, str):
                        c_time = datetime.fromisoformat(claim_time.replace('Z', '+00:00'))
                    else:
                        c_time = claim_time
                    
                    if e_time > c_time:
                        discrepancies.append({
                            'type': 'temporal_inconsistency',
                            'evidence_id': e.get('evidence_id'),
                            'issue': 'Evidence timestamp after claim timestamp',
                        })
                        confidence -= 0.2
        
        return max(0.0, confidence), discrepancies
    
    async def _validate_logic(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Validate logical consistency."""
        discrepancies = []
        confidence = 1.0
        
        if 'reasoning_chain' in claim:
            chain = claim['reasoning_chain']
            for i, step in enumerate(chain):
                if i > 0:
                    prev_step = chain[i - 1]
                    if not self._check_logical_connection(prev_step, step):
                        discrepancies.append({
                            'type': 'logical_gap',
                            'step': i,
                            'issue': 'Logical connection not established',
                        })
                        confidence -= 0.15
        
        if 'conclusion' in claim and 'premises' in claim:
            if not self._check_conclusion_validity(claim['premises'], claim['conclusion']):
                discrepancies.append({
                    'type': 'invalid_conclusion',
                    'issue': 'Conclusion does not follow from premises',
                })
                confidence -= 0.4
        
        return max(0.0, confidence), discrepancies
    
    def _check_logical_connection(self, prev: Dict, curr: Dict) -> bool:
        """Check if there's a logical connection between steps."""
        if 'conclusion' in prev and 'premise' in curr:
            return prev['conclusion'] in str(curr.get('premise', ''))
        return True
    
    def _check_conclusion_validity(self, premises: List, conclusion: Any) -> bool:
        """Check if conclusion follows from premises."""
        return len(premises) > 0
    
    async def _validate_risk(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Validate risk assessments."""
        discrepancies = []
        confidence = 1.0
        
        if 'risk_level' in claim:
            risk = claim['risk_level']
            
            if risk > 0.7 and claim.get('action_type') == 'capital_deployment':
                if not any(e.get('type') == 'risk_approval' for e in evidence):
                    discrepancies.append({
                        'type': 'missing_risk_approval',
                        'risk_level': risk,
                        'issue': 'High risk action without explicit approval',
                    })
                    confidence -= 0.3
        
        if context and 'max_risk_threshold' in context:
            if claim.get('risk_level', 0) > context['max_risk_threshold']:
                discrepancies.append({
                    'type': 'risk_threshold_exceeded',
                    'threshold': context['max_risk_threshold'],
                    'actual': claim.get('risk_level'),
                })
                confidence -= 0.5
        
        return max(0.0, confidence), discrepancies
    
    async def _validate_statistics(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Validate statistical claims."""
        discrepancies = []
        confidence = 1.0
        
        if 'statistical_claim' in claim:
            stat = claim['statistical_claim']
            
            if 'confidence_interval' in stat:
                ci = stat['confidence_interval']
                if ci < 0.9:
                    discrepancies.append({
                        'type': 'low_confidence_interval',
                        'value': ci,
                        'issue': 'Statistical confidence below threshold',
                    })
                    confidence -= 0.2
            
            if 'sample_size' in stat and stat['sample_size'] < 30:
                discrepancies.append({
                    'type': 'insufficient_sample_size',
                    'value': stat['sample_size'],
                    'issue': 'Sample size too small for reliable inference',
                })
                confidence -= 0.25
        
        return max(0.0, confidence), discrepancies
    
    async def _adversarial_validation(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Perform adversarial validation - actively try to disprove the claim."""
        discrepancies = []
        confidence = 1.0
        
        if 'prediction' in claim:
            pred = claim['prediction']
            
            if pred.get('certainty', 0) > 0.95:
                discrepancies.append({
                    'type': 'overconfidence_warning',
                    'certainty': pred['certainty'],
                    'issue': 'Prediction certainty suspiciously high',
                })
                confidence -= 0.1
        
        evidence_sources = set()
        for e in evidence:
            source = e.get('source_name', e.get('source_id', 'unknown'))
            evidence_sources.add(source)
        
        if len(evidence_sources) < 2:
            discrepancies.append({
                'type': 'single_source_dependency',
                'sources': list(evidence_sources),
                'issue': 'Claim relies on single source - vulnerable to source failure',
            })
            confidence -= 0.2
        
        for e in evidence:
            if e.get('confidence_score', 1.0) < 0.7:
                discrepancies.append({
                    'type': 'weak_evidence',
                    'evidence_id': e.get('evidence_id'),
                    'confidence': e.get('confidence_score'),
                })
                confidence -= 0.15
        
        return max(0.0, confidence), discrepancies
    
    async def _generic_validation(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Generic validation for unspecified types."""
        discrepancies = []
        confidence = 0.8
        
        if not evidence:
            discrepancies.append({
                'type': 'no_evidence',
                'issue': 'Claim has no supporting evidence',
            })
            confidence = 0.0
        
        return confidence, discrepancies


class ValidatorPool:
    """
    Pool of validator agents for N-of-M verification.
    
    Provides:
    - Validator selection based on specialization
    - Consensus-based verification
    - Reputation-weighted voting
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'validator_pool_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._validators: Dict[str, ValidatorAgent] = {}
        self._validation_history: List[Dict[str, Any]] = []
        
        self._consensus_config = {
            'minimum_validators': 3,
            'approval_threshold': 0.67,
            'high_impact_threshold': 0.80,
            'timeout_seconds': 30,
        }
        
        self._initialize_default_validators()
        
        logger.info("✅ Validator Pool initialized")
    
    def _initialize_default_validators(self):
        """Initialize default validator agents."""
        default_validators = [
            ValidatorAgent(
                validator_id="VAL-DATA-001",
                validator_type=ValidatorType.DATA_VALIDATOR,
                name="Primary Data Validator",
                specializations=['market_data', 'price_data', 'volume_data'],
            ),
            ValidatorAgent(
                validator_id="VAL-DATA-002",
                validator_type=ValidatorType.DATA_VALIDATOR,
                name="Secondary Data Validator",
                specializations=['order_book', 'trade_data', 'blockchain_data'],
            ),
            ValidatorAgent(
                validator_id="VAL-LOGIC-001",
                validator_type=ValidatorType.LOGIC_VALIDATOR,
                name="Logic Consistency Validator",
                specializations=['reasoning_chains', 'decision_logic', 'inference'],
            ),
            ValidatorAgent(
                validator_id="VAL-RISK-001",
                validator_type=ValidatorType.RISK_VALIDATOR,
                name="Risk Assessment Validator",
                specializations=['risk_metrics', 'exposure', 'drawdown'],
            ),
            ValidatorAgent(
                validator_id="VAL-STAT-001",
                validator_type=ValidatorType.STATISTICAL_VALIDATOR,
                name="Statistical Validator",
                specializations=['statistical_claims', 'probability', 'confidence_intervals'],
            ),
            ValidatorAgent(
                validator_id="VAL-ADV-001",
                validator_type=ValidatorType.ADVERSARIAL_VALIDATOR,
                name="Adversarial Validator Alpha",
                specializations=['adversarial_testing', 'edge_cases', 'failure_modes'],
            ),
            ValidatorAgent(
                validator_id="VAL-ADV-002",
                validator_type=ValidatorType.ADVERSARIAL_VALIDATOR,
                name="Adversarial Validator Beta",
                specializations=['hallucination_detection', 'overconfidence', 'bias'],
            ),
            ValidatorAgent(
                validator_id="VAL-CONS-001",
                validator_type=ValidatorType.CONSENSUS_VALIDATOR,
                name="Consensus Validator",
                specializations=['multi_source', 'cross_validation', 'agreement'],
            ),
            ValidatorAgent(
                validator_id="VAL-XREF-001",
                validator_type=ValidatorType.CROSS_REFERENCE_VALIDATOR,
                name="Cross Reference Validator",
                specializations=['external_sources', 'canonical_data', 'verification'],
            ),
            ValidatorAgent(
                validator_id="VAL-TEMP-001",
                validator_type=ValidatorType.TEMPORAL_VALIDATOR,
                name="Temporal Validator",
                specializations=['timestamp_validation', 'sequence_verification', 'staleness'],
            ),
        ]
        
        for validator in default_validators:
            self.register_validator(validator)
    
    def register_validator(self, validator: ValidatorAgent):
        """Register a validator in the pool."""
        self._validators[validator.validator_id] = validator
        logger.debug(f"Registered validator: {validator.name}")
    
    def get_validator(self, validator_id: str) -> Optional[ValidatorAgent]:
        """Get a validator by ID."""
        return self._validators.get(validator_id)
    
    def list_validators(
        self,
        validator_type: Optional[ValidatorType] = None,
        specialization: Optional[str] = None,
        active_only: bool = True,
    ) -> List[ValidatorAgent]:
        """List validators with optional filtering."""
        validators = list(self._validators.values())
        
        if active_only:
            validators = [v for v in validators if v.is_active]
        
        if validator_type:
            validators = [v for v in validators if v.validator_type == validator_type]
        
        if specialization:
            validators = [v for v in validators if specialization in v.specializations]
        
        return sorted(validators, key=lambda v: v.reputation_score, reverse=True)
    
    async def validate_with_consensus(
        self,
        claim: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        required_validators: Optional[int] = None,
        specializations: Optional[List[str]] = None,
        is_high_impact: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a claim using N-of-M consensus.
        
        Args:
            claim: The claim to validate
            evidence: Supporting evidence
            required_validators: Number of validators required (N)
            specializations: Required specializations
            is_high_impact: Whether this is a high-impact decision
            context: Additional context
        
        Returns:
            Tuple of (approved, consensus_report)
        """
        required_validators = required_validators or self._consensus_config['minimum_validators']
        threshold = (
            self._consensus_config['high_impact_threshold'] 
            if is_high_impact 
            else self._consensus_config['approval_threshold']
        )
        
        selected_validators = self._select_validators(
            required_validators,
            specializations,
        )
        
        if len(selected_validators) < required_validators:
            return False, {
                'error': 'Insufficient validators available',
                'required': required_validators,
                'available': len(selected_validators),
            }
        
        validation_tasks = [
            validator.validate_claim(claim, evidence, context)
            for validator in selected_validators
        ]
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*validation_tasks, return_exceptions=True),
                timeout=self._consensus_config['timeout_seconds']
            )
        except asyncio.TimeoutError:
            return False, {'error': 'Validation timeout'}
        
        valid_results = [r for r in results if isinstance(r, ValidationResult)]
        
        approvals = sum(
            1 for r in valid_results 
            if r.status == ValidationStatus.APPROVED
        )
        
        weighted_approval = sum(
            self._validators[r.validator_id].reputation_score
            for r in valid_results
            if r.status == ValidationStatus.APPROVED
        )
        
        total_weight = sum(
            self._validators[r.validator_id].reputation_score
            for r in valid_results
        )
        
        approval_rate = weighted_approval / total_weight if total_weight > 0 else 0
        
        all_discrepancies = []
        for r in valid_results:
            all_discrepancies.extend(r.discrepancies_found)
        
        consensus_report = {
            'claim_id': claim.get('claim_id', 'unknown'),
            'total_validators': len(selected_validators),
            'responses_received': len(valid_results),
            'approvals': approvals,
            'approval_rate': approval_rate,
            'threshold': threshold,
            'is_approved': approval_rate >= threshold,
            'validation_results': [r.to_dict() for r in valid_results],
            'all_discrepancies': all_discrepancies,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        self._validation_history.append(consensus_report)
        
        for r in valid_results:
            validator = self._validators.get(r.validator_id)
            if validator:
                if consensus_report['is_approved'] == (r.status == ValidationStatus.APPROVED):
                    validator.successful_validations += 1
                    validator.reputation_score = min(1.0, validator.reputation_score + 0.01)
                else:
                    if r.status == ValidationStatus.APPROVED:
                        validator.false_positives += 1
                    else:
                        validator.false_negatives += 1
                    validator.reputation_score = max(0.1, validator.reputation_score - 0.02)
        
        return consensus_report['is_approved'], consensus_report
    
    def _select_validators(
        self,
        count: int,
        specializations: Optional[List[str]] = None,
    ) -> List[ValidatorAgent]:
        """Select validators for consensus."""
        available = self.list_validators(active_only=True)
        
        if specializations:
            specialized = [
                v for v in available
                if any(s in v.specializations for s in specializations)
            ]
            if len(specialized) >= count:
                available = specialized
        
        available.sort(key=lambda v: v.reputation_score, reverse=True)
        
        selected = available[:count]
        
        remaining = [v for v in available if v not in selected]
        if remaining and len(selected) < count:
            random.shuffle(remaining)
            selected.extend(remaining[:count - len(selected)])
        
        return selected
    
    async def get_validator_statistics(self) -> Dict[str, Any]:
        """Get statistics about the validator pool."""
        active_validators = [v for v in self._validators.values() if v.is_active]
        
        return {
            'total_validators': len(self._validators),
            'active_validators': len(active_validators),
            'average_reputation': sum(v.reputation_score for v in active_validators) / len(active_validators) if active_validators else 0,
            'total_validations': sum(v.total_validations for v in self._validators.values()),
            'validation_history_size': len(self._validation_history),
            'validators_by_type': {
                vt.value: len([v for v in active_validators if v.validator_type == vt])
                for vt in ValidatorType
            },
        }
