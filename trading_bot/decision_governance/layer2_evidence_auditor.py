"""
Layer 2: Evidence Sufficiency Auditor

For every claim, asks:
- What evidence is present?
- What evidence is missing?
- What evidence is stale?
- What evidence conflicts?
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from .core_types import (
    Claim, ClaimType, Evidence, EvidenceStatus, DecisionRecord
)

logger = logging.getLogger(__name__)


class EvidenceSufficiencyAuditor:
    """
    Audits evidence sufficiency for all claims in a decision.
    Detects missing evidence, stale evidence, and contradictions.
    """
    
    def __init__(
        self,
        staleness_threshold_hours: float = 24.0,
        min_evidence_per_claim: int = 1,
        evidence_quality_threshold: float = 0.5
    ):
        self.staleness_threshold = timedelta(hours=staleness_threshold_hours)
        self.min_evidence_per_claim = min_evidence_per_claim
        self.quality_threshold = evidence_quality_threshold
        
        # Evidence registry for tracking
        self.evidence_store: Dict[str, Evidence] = {}
        
    def audit_evidence(
        self,
        claims: List[Claim],
        available_evidence: Optional[List[Evidence]] = None,
        current_time: Optional[datetime] = None
    ) -> Tuple[Dict[str, EvidenceStatus], List[str], List[Tuple[str, str]]]:
        """
        Audit evidence for a set of claims.
        
        Returns:
            Tuple of:
            - evidence_coverage: Map of claim_id -> status
            - evidence_gaps: List of missing evidence descriptions
            - contradictions: List of (evidence1_id, evidence2_id) tuples
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        evidence_coverage = {}
        evidence_gaps = []
        contradictions = []
        
        # Index available evidence
        if available_evidence:
            for ev in available_evidence:
                self.evidence_store[ev.id] = ev
                
        for claim in claims:
            status, gaps, contras = self._audit_single_claim(
                claim, current_time
            )
            evidence_coverage[claim.id] = status
            evidence_gaps.extend(gaps)
            contradictions.extend(contras)
            
        return evidence_coverage, evidence_gaps, contradictions
    
    def _audit_single_claim(
        self,
        claim: Claim,
        current_time: datetime
    ) -> Tuple[EvidenceStatus, List[str], List[Tuple[str, str]]]:
        """Audit evidence for a single claim"""
        
        gaps = []
        contradictions = []
        
        # Check if claim has evidence references
        if not claim.evidence_refs:
            # Check if claim IS evidence
            if claim.claim_type != ClaimType.EVIDENCE:
                gaps.append(f"Claim '{claim.content[:50]}...' has no supporting evidence")
                return EvidenceStatus.MISSING, gaps, contradictions
            else:
                # Evidence claims need verification
                return EvidenceStatus.PRESENT, [], []
                
        # Check each evidence reference
        present_count = 0
        stale_count = 0
        conflicting_count = 0
        
        for ev_id in claim.evidence_refs:
            evidence = self.evidence_store.get(ev_id)
            
            if not evidence:
                gaps.append(f"Referenced evidence {ev_id} not found for claim '{claim.content[:50]}...'")
                continue
                
            # Check staleness
            age = current_time - evidence.timestamp
            if age > self.staleness_threshold:
                stale_count += 1
                evidence.status = EvidenceStatus.STALE
                gaps.append(f"Evidence for claim '{claim.content[:50]}...' is stale ({age.days} days old)")
                
            # Check quality
            if evidence.strength < self.quality_threshold:
                gaps.append(f"Evidence for claim '{claim.content[:50]}...' is weak (strength: {evidence.strength:.2f})")
                
            # Check for contradictions
            if evidence.contradictions:
                conflicting_count += 1
                for contra_id in evidence.contradictions:
                    contradictions.append((ev_id, contra_id))
                    
            present_count += 1
            
        # Determine overall status
        if conflicting_count > 0:
            return EvidenceStatus.CONFLICTING, gaps, contradictions
        elif stale_count > 0 and stale_count >= present_count / 2:
            return EvidenceStatus.STALE, gaps, contradictions
        elif present_count < self.min_evidence_per_claim:
            return EvidenceStatus.INSUFFICIENT, gaps, contradictions
        elif gaps:
            return EvidenceStatus.INSUFFICIENT, gaps, contradictions
        else:
            return EvidenceStatus.PRESENT, gaps, contradictions
    
    def check_evidence_contradictions(
        self,
        evidence_list: List[Evidence]
    ) -> List[Tuple[str, str, float]]:
        """
        Detect contradictions between evidence items.
        
        Returns:
            List of (ev1_id, ev2_id, severity) tuples
        """
        contradictions = []
        
        # Simple contradiction detection based on content analysis
        for i, ev1 in enumerate(evidence_list):
            for ev2 in evidence_list[i+1:]:
                severity = self._calculate_contradiction_severity(ev1, ev2)
                if severity > 0.5:
                    contradictions.append((ev1.id, ev2.id, severity))
                    
        return contradictions
    
    def _calculate_contradiction_severity(
        self,
        ev1: Evidence,
        ev2: Evidence
    ) -> float:
        """Calculate contradiction severity between two evidence items"""
        
        # Check for explicit contradiction tags
        if ev2.id in ev1.contradictions or ev1.id in ev2.contradictions:
            return 1.0
            
        # Analyze content for opposing signals
        content1 = str(ev1.content).lower()
        content2 = str(ev2.content).lower()
        
        # Check for opposing directional indicators
        bullish_terms = ['bullish', 'up', 'rise', 'increase', 'positive', 'buy', 'long']
        bearish_terms = ['bearish', 'down', 'fall', 'decrease', 'negative', 'sell', 'short']
        
        has_bullish_1 = any(term in content1 for term in bullish_terms)
        has_bearish_1 = any(term in content1 for term in bearish_terms)
        has_bullish_2 = any(term in content2 for term in bullish_terms)
        has_bearish_2 = any(term in content2 for term in bearish_terms)
        
        # Contradiction if one is bullish and other is bearish
        if (has_bullish_1 and has_bearish_2) or (has_bearish_1 and has_bullish_2):
            # Weight by strength of evidence
            avg_strength = (ev1.strength + ev2.strength) / 2
            return 0.7 + (0.3 * avg_strength)  # Base 0.7 + strength contribution
            
        return 0.0
    
    def generate_evidence_requirements(
        self,
        claim: Claim
    ) -> List[str]:
        """Generate list of required evidence types for a claim"""
        
        requirements = []
        
        if claim.claim_type == ClaimType.THESIS:
            requirements.extend([
                "Price action data supporting thesis",
                "Volume confirmation",
                "Market structure alignment"
            ])
        elif claim.claim_type == ClaimType.ASSUMPTION:
            requirements.extend([
                "Historical validation of assumption",
                "Current market conditions check"
            ])
        elif claim.claim_type == ClaimType.PREDICTED_OUTCOME:
            requirements.extend([
                "Statistical base rate for similar predictions",
                "Confidence interval estimation",
                "Alternative scenario analysis"
            ])
        elif claim.claim_type == ClaimType.INFERRED_CAUSAL_LINK:
            requirements.extend([
                "Historical correlation data",
                "Granger causality or similar statistical test",
                "Mechanism explanation"
            ])
            
        return requirements
    
    def compute_evidence_coverage_score(
        self,
        claims: List[Claim],
        evidence_coverage: Dict[str, EvidenceStatus]
    ) -> float:
        """Compute overall evidence coverage score (0 to 1)"""
        
        if not claims:
            return 0.0
            
        scores = {
            EvidenceStatus.PRESENT: 1.0,
            EvidenceStatus.INSUFFICIENT: 0.5,
            EvidenceStatus.STALE: 0.3,
            EvidenceStatus.MISSING: 0.0,
            EvidenceStatus.CONFLICTING: 0.0
        }
        
        total_score = sum(
            scores.get(evidence_coverage.get(c.id, EvidenceStatus.MISSING), 0.0)
            for c in claims
        )
        
        return total_score / len(claims)
    
    def identify_critical_evidence_gaps(
        self,
        claims: List[Claim],
        evidence_coverage: Dict[str, EvidenceStatus]
    ) -> List[Dict[str, Any]]:
        """Identify critical gaps that must be addressed"""
        
        critical_gaps = []
        
        # Thesis claims are critical
        for claim in claims:
            if claim.claim_type == ClaimType.THESIS:
                status = evidence_coverage.get(claim.id, EvidenceStatus.MISSING)
                if status in [EvidenceStatus.MISSING, EvidenceStatus.CONFLICTING]:
                    critical_gaps.append({
                        'claim_id': claim.id,
                        'claim_type': claim.claim_type.value,
                        'severity': 'CRITICAL',
                        'description': f"Main thesis lacks evidence: {claim.content[:100]}",
                        'required_evidence': self.generate_evidence_requirements(claim)
                    })
                    
        # Assumptions without evidence are also critical
        for claim in claims:
            if claim.claim_type == ClaimType.ASSUMPTION:
                status = evidence_coverage.get(claim.id, EvidenceStatus.MISSING)
                if status == EvidenceStatus.MISSING:
                    critical_gaps.append({
                        'claim_id': claim.id,
                        'claim_type': claim.claim_type.value,
                        'severity': 'HIGH',
                        'description': f"Unverified assumption: {claim.content[:100]}",
                        'required_evidence': self.generate_evidence_requirements(claim)
                    })
                    
        return critical_gaps
