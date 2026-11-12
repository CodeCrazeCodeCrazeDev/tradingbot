"""
Evidence Reasoner

Enhanced reasoning system that requires evidence-backed citations for every step.
Ensures all conclusions are grounded in verifiable data sources.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """Types of reasoning."""
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CAUSAL = "causal"
    PROBABILISTIC = "probabilistic"


class StepStatus(Enum):
    """Status of a reasoning step."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    NEEDS_EVIDENCE = "needs_evidence"
    UNCERTAIN = "uncertain"


@dataclass
class EvidenceCitation:
    """Citation to evidence supporting a reasoning step."""
    citation_id: str
    evidence_id: str
    source_name: str
    source_type: str
    relevance_score: float
    excerpt: str
    timestamp: datetime
    verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'citation_id': self.citation_id,
            'evidence_id': self.evidence_id,
            'source_name': self.source_name,
            'source_type': self.source_type,
            'relevance_score': self.relevance_score,
            'excerpt': self.excerpt,
            'timestamp': self.timestamp.isoformat(),
            'verified': self.verified,
        }


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain."""
    step_id: str
    step_number: int
    premise: str
    conclusion: str
    reasoning_type: ReasoningType
    citations: List[EvidenceCitation]
    confidence: float
    status: StepStatus
    dependencies: List[str] = field(default_factory=list)
    uncertainty: float = 0.0
    verification_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_id': self.step_id,
            'step_number': self.step_number,
            'premise': self.premise,
            'conclusion': self.conclusion,
            'reasoning_type': self.reasoning_type.value,
            'citations': [c.to_dict() for c in self.citations],
            'confidence': self.confidence,
            'status': self.status.value,
            'dependencies': self.dependencies,
            'uncertainty': self.uncertainty,
            'verification_notes': self.verification_notes,
        }


@dataclass
class ReasoningChain:
    """A complete chain of reasoning from premises to conclusion."""
    chain_id: str
    objective: str
    steps: List[ReasoningStep]
    final_conclusion: str
    overall_confidence: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    is_valid: bool = False
    validation_report: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chain_id': self.chain_id,
            'objective': self.objective,
            'steps': [s.to_dict() for s in self.steps],
            'final_conclusion': self.final_conclusion,
            'overall_confidence': self.overall_confidence,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_valid': self.is_valid,
            'validation_report': self.validation_report,
        }


@dataclass
class ReasoningResult:
    """Result of a reasoning process."""
    result_id: str
    chain: ReasoningChain
    conclusion: str
    confidence: float
    uncertainty: float
    is_verified: bool
    evidence_coverage: float
    weakest_link: Optional[str]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'chain': self.chain.to_dict(),
            'conclusion': self.conclusion,
            'confidence': self.confidence,
            'uncertainty': self.uncertainty,
            'is_verified': self.is_verified,
            'evidence_coverage': self.evidence_coverage,
            'weakest_link': self.weakest_link,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat(),
        }


class EvidenceReasoner:
    """
    Evidence-backed reasoning system.
    
    Provides:
    - Multi-step reasoning with mandatory citations
    - Evidence verification for each step
    - Confidence propagation through chains
    - Uncertainty quantification
    - Reasoning validation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'evidence_reasoner_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._chains: Dict[str, ReasoningChain] = {}
        self._evidence_cache: Dict[str, Dict[str, Any]] = {}
        
        self._reasoning_config = {
            'minimum_citations_per_step': 1,
            'minimum_confidence_threshold': 0.5,
            'maximum_uncertainty': 0.3,
            'citation_relevance_threshold': 0.6,
            'confidence_decay_per_step': 0.05,
        }
        
        logger.info("✅ Evidence Reasoner initialized")
    
    async def create_reasoning_chain(
        self,
        objective: str,
        initial_premises: List[Dict[str, Any]],
    ) -> ReasoningChain:
        """
        Create a new reasoning chain.
        
        Args:
            objective: What we're trying to conclude
            initial_premises: Starting premises with evidence
        
        Returns:
            ReasoningChain
        """
        chain_id = f"RC-{uuid.uuid4().hex[:12]}"
        
        steps = []
        for i, premise in enumerate(initial_premises):
            citations = await self._create_citations(premise.get('evidence', []))
            
            step = ReasoningStep(
                step_id=f"RS-{uuid.uuid4().hex[:8]}",
                step_number=i + 1,
                premise=premise.get('premise', ''),
                conclusion=premise.get('conclusion', premise.get('premise', '')),
                reasoning_type=ReasoningType(premise.get('reasoning_type', 'deductive')),
                citations=citations,
                confidence=self._calculate_step_confidence(citations),
                status=StepStatus.PENDING if citations else StepStatus.NEEDS_EVIDENCE,
            )
            steps.append(step)
        
        chain = ReasoningChain(
            chain_id=chain_id,
            objective=objective,
            steps=steps,
            final_conclusion="",
            overall_confidence=0.0,
            created_at=datetime.now(timezone.utc),
        )
        
        self._chains[chain_id] = chain
        
        logger.info(f"Created reasoning chain {chain_id} with {len(steps)} initial steps")
        
        return chain
    
    async def add_reasoning_step(
        self,
        chain_id: str,
        premise: str,
        conclusion: str,
        reasoning_type: ReasoningType,
        evidence: List[Dict[str, Any]],
        dependencies: Optional[List[str]] = None,
    ) -> Optional[ReasoningStep]:
        """
        Add a reasoning step to a chain.
        
        Args:
            chain_id: ID of the chain
            premise: The premise for this step
            conclusion: The conclusion drawn
            reasoning_type: Type of reasoning used
            evidence: Supporting evidence
            dependencies: IDs of steps this depends on
        
        Returns:
            ReasoningStep if successful
        """
        if chain_id not in self._chains:
            return None
        
        chain = self._chains[chain_id]
        
        citations = await self._create_citations(evidence)
        
        if len(citations) < self._reasoning_config['minimum_citations_per_step']:
            logger.warning(f"Insufficient citations for reasoning step")
        
        step_number = len(chain.steps) + 1
        
        step = ReasoningStep(
            step_id=f"RS-{uuid.uuid4().hex[:8]}",
            step_number=step_number,
            premise=premise,
            conclusion=conclusion,
            reasoning_type=reasoning_type,
            citations=citations,
            confidence=self._calculate_step_confidence(citations),
            status=StepStatus.PENDING,
            dependencies=dependencies or [],
        )
        
        if dependencies:
            dep_confidences = []
            for dep_id in dependencies:
                dep_step = next((s for s in chain.steps if s.step_id == dep_id), None)
                if dep_step:
                    dep_confidences.append(dep_step.confidence)
            
            if dep_confidences:
                step.confidence *= min(dep_confidences)
        
        step.confidence *= (1 - self._reasoning_config['confidence_decay_per_step'] * step_number)
        
        chain.steps.append(step)
        
        return step
    
    async def _create_citations(
        self,
        evidence: List[Dict[str, Any]],
    ) -> List[EvidenceCitation]:
        """Create citations from evidence."""
        citations = []
        
        for ev in evidence:
            citation = EvidenceCitation(
                citation_id=f"CIT-{uuid.uuid4().hex[:8]}",
                evidence_id=ev.get('evidence_id', f"EV-{uuid.uuid4().hex[:8]}"),
                source_name=ev.get('source_name', 'unknown'),
                source_type=ev.get('source_type', 'unknown'),
                relevance_score=ev.get('relevance_score', 0.8),
                excerpt=ev.get('excerpt', str(ev.get('content', ''))),
                timestamp=datetime.now(timezone.utc),
                verified=ev.get('verified', False),
            )
            
            if citation.relevance_score >= self._reasoning_config['citation_relevance_threshold']:
                citations.append(citation)
        
        return citations
    
    def _calculate_step_confidence(self, citations: List[EvidenceCitation]) -> float:
        """Calculate confidence for a step based on citations."""
        if not citations:
            return 0.0
        
        verified_citations = [c for c in citations if c.verified]
        verification_ratio = len(verified_citations) / len(citations) if citations else 0
        
        avg_relevance = sum(c.relevance_score for c in citations) / len(citations)
        
        citation_count_factor = min(1.0, len(citations) / 3)
        
        confidence = (
            0.4 * verification_ratio +
            0.4 * avg_relevance +
            0.2 * citation_count_factor
        )
        
        return confidence
    
    async def verify_step(
        self,
        chain_id: str,
        step_id: str,
        verification_result: bool,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Verify a reasoning step.
        
        Args:
            chain_id: ID of the chain
            step_id: ID of the step
            verification_result: Whether verification passed
            notes: Optional verification notes
        
        Returns:
            True if successful
        """
        if chain_id not in self._chains:
            return False
        
        chain = self._chains[chain_id]
        step = next((s for s in chain.steps if s.step_id == step_id), None)
        
        if not step:
            return False
        
        if verification_result:
            step.status = StepStatus.VERIFIED
            step.confidence = min(1.0, step.confidence * 1.1)
        else:
            step.status = StepStatus.FAILED
            step.confidence *= 0.5
        
        step.verification_notes = notes
        
        return True
    
    async def complete_reasoning(
        self,
        chain_id: str,
        final_conclusion: str,
    ) -> ReasoningResult:
        """
        Complete a reasoning chain and generate result.
        
        Args:
            chain_id: ID of the chain
            final_conclusion: The final conclusion
        
        Returns:
            ReasoningResult
        """
        if chain_id not in self._chains:
            raise ValueError(f"Chain {chain_id} not found")
        
        chain = self._chains[chain_id]
        chain.final_conclusion = final_conclusion
        chain.completed_at = datetime.now(timezone.utc)
        
        validation_report = await self._validate_chain(chain)
        chain.validation_report = validation_report
        chain.is_valid = validation_report.get('is_valid', False)
        
        step_confidences = [s.confidence for s in chain.steps]
        chain.overall_confidence = min(step_confidences) if step_confidences else 0.0
        
        total_citations = sum(len(s.citations) for s in chain.steps)
        verified_citations = sum(
            len([c for c in s.citations if c.verified])
            for s in chain.steps
        )
        evidence_coverage = verified_citations / total_citations if total_citations > 0 else 0.0
        
        weakest_step = min(chain.steps, key=lambda s: s.confidence) if chain.steps else None
        
        uncertainty = 1 - chain.overall_confidence
        
        recommendations = self._generate_recommendations(chain, validation_report)
        
        result = ReasoningResult(
            result_id=f"RR-{uuid.uuid4().hex[:12]}",
            chain=chain,
            conclusion=final_conclusion,
            confidence=chain.overall_confidence,
            uncertainty=uncertainty,
            is_verified=chain.is_valid,
            evidence_coverage=evidence_coverage,
            weakest_link=weakest_step.step_id if weakest_step else None,
            recommendations=recommendations,
            timestamp=datetime.now(timezone.utc),
        )
        
        await self._persist_result(result)
        
        logger.info(f"Completed reasoning chain {chain_id}: "
                   f"confidence={chain.overall_confidence:.2f}, valid={chain.is_valid}")
        
        return result
    
    async def _validate_chain(self, chain: ReasoningChain) -> Dict[str, Any]:
        """Validate a reasoning chain."""
        report = {
            'is_valid': True,
            'issues': [],
            'step_validations': [],
            'citation_coverage': 0.0,
            'logical_consistency': True,
        }
        
        for step in chain.steps:
            step_validation = {
                'step_id': step.step_id,
                'is_valid': True,
                'issues': [],
            }
            
            if len(step.citations) < self._reasoning_config['minimum_citations_per_step']:
                step_validation['is_valid'] = False
                step_validation['issues'].append('Insufficient citations')
                report['is_valid'] = False
            
            if step.confidence < self._reasoning_config['minimum_confidence_threshold']:
                step_validation['issues'].append('Low confidence')
            
            if step.status == StepStatus.FAILED:
                step_validation['is_valid'] = False
                step_validation['issues'].append('Step verification failed')
                report['is_valid'] = False
            
            for dep_id in step.dependencies:
                dep_step = next((s for s in chain.steps if s.step_id == dep_id), None)
                if dep_step and dep_step.status == StepStatus.FAILED:
                    step_validation['is_valid'] = False
                    step_validation['issues'].append(f'Dependency {dep_id} failed')
                    report['logical_consistency'] = False
            
            report['step_validations'].append(step_validation)
        
        total_citations = sum(len(s.citations) for s in chain.steps)
        verified_citations = sum(
            len([c for c in s.citations if c.verified])
            for s in chain.steps
        )
        report['citation_coverage'] = verified_citations / total_citations if total_citations > 0 else 0.0
        
        if report['citation_coverage'] < 0.5:
            report['issues'].append('Low citation coverage')
        
        return report
    
    def _generate_recommendations(
        self,
        chain: ReasoningChain,
        validation_report: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations for improving reasoning."""
        recommendations = []
        
        if not validation_report.get('is_valid', False):
            recommendations.append("Address validation issues before proceeding")
        
        if validation_report.get('citation_coverage', 0) < 0.7:
            recommendations.append("Increase evidence verification coverage")
        
        for step_val in validation_report.get('step_validations', []):
            if 'Insufficient citations' in step_val.get('issues', []):
                recommendations.append(f"Add more citations to step {step_val['step_id']}")
        
        weak_steps = [s for s in chain.steps if s.confidence < 0.6]
        if weak_steps:
            recommendations.append(f"Strengthen evidence for {len(weak_steps)} weak steps")
        
        if not validation_report.get('logical_consistency', True):
            recommendations.append("Review logical dependencies between steps")
        
        return recommendations
    
    async def reason_with_evidence(
        self,
        objective: str,
        premises: List[Dict[str, Any]],
        reasoning_steps: List[Dict[str, Any]],
    ) -> ReasoningResult:
        """
        Complete end-to-end reasoning with evidence.
        
        Args:
            objective: What we're trying to conclude
            premises: Initial premises with evidence
            reasoning_steps: Steps to reach conclusion
        
        Returns:
            ReasoningResult
        """
        chain = await self.create_reasoning_chain(objective, premises)
        
        for step_data in reasoning_steps:
            await self.add_reasoning_step(
                chain_id=chain.chain_id,
                premise=step_data.get('premise', ''),
                conclusion=step_data.get('conclusion', ''),
                reasoning_type=ReasoningType(step_data.get('reasoning_type', 'deductive')),
                evidence=step_data.get('evidence', []),
                dependencies=step_data.get('dependencies', []),
            )
        
        final_conclusion = reasoning_steps[-1].get('conclusion', '') if reasoning_steps else objective
        
        return await self.complete_reasoning(chain.chain_id, final_conclusion)
    
    def get_chain(self, chain_id: str) -> Optional[ReasoningChain]:
        """Get a reasoning chain by ID."""
        return self._chains.get(chain_id)
    
    async def _persist_result(self, result: ReasoningResult):
        """Persist reasoning result to storage."""
        result_file = self.storage_path / 'results' / f"{result.result_id}.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reasoner statistics."""
        valid_chains = [c for c in self._chains.values() if c.is_valid]
        
        return {
            'total_chains': len(self._chains),
            'valid_chains': len(valid_chains),
            'total_steps': sum(len(c.steps) for c in self._chains.values()),
            'average_confidence': sum(c.overall_confidence for c in self._chains.values()) / len(self._chains) if self._chains else 0,
        }
