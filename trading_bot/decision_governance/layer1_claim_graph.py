"""
Layer 1: Claim Graph Constructor

Converts every agent output into structured claims:
- thesis
- assumption
- evidence
- inferred causal link
- predicted outcome
- invalidation conditions
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import logging
import re
import json

from .core_types import (
    Claim, ClaimType, Evidence, DecisionRecord, MarketRegime
)

logger = logging.getLogger(__name__)


class ClaimGraphConstructor:
    """
    Converts raw agent outputs into structured claim graphs.
    Every agent output is decomposed into its constituent claims.
    """
    
    def __init__(self):
        self.claims_registry: Dict[str, Claim] = {}
        self.evidence_registry: Dict[str, Evidence] = {}
        self.claim_relationships: Dict[str, Set[str]] = defaultdict(set)
        
    def construct_claim_graph(
        self,
        agent_output: Dict[str, Any],
        source_agent: str,
        symbol: str,
        timestamp: Optional[datetime] = None
    ) -> List[Claim]:
        """
        Convert agent output into structured claims.
        
        Args:
            agent_output: Raw output from an agent
            source_agent: Name of the agent that produced the output
            symbol: Trading symbol
            timestamp: When the claim was generated
            
        Returns:
            List of structured claims
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
            
        claims = []
        
        # Extract thesis/main claim
        thesis = self._extract_thesis(agent_output, source_agent, symbol, timestamp)
        if thesis:
            claims.append(thesis)
            self.claims_registry[thesis.id] = thesis
            
        # Extract assumptions
        assumptions = self._extract_assumptions(agent_output, source_agent, symbol, timestamp, thesis)
        for assumption in assumptions:
            claims.append(assumption)
            self.claims_registry[assumption.id] = assumption
            if thesis:
                assumption.dependent_claims.append(thesis.id)
                
        # Extract evidence claims
        evidence_claims = self._extract_evidence_claims(agent_output, source_agent, symbol, timestamp)
        for ev_claim in evidence_claims:
            claims.append(ev_claim)
            self.claims_registry[ev_claim.id] = ev_claim
            
        # Extract causal links
        causal_links = self._extract_causal_links(agent_output, source_agent, symbol, timestamp, claims)
        for link in causal_links:
            claims.append(link)
            self.claims_registry[link.id] = link
            
        # Extract predicted outcomes
        outcomes = self._extract_predicted_outcomes(agent_output, source_agent, symbol, timestamp, thesis)
        for outcome in outcomes:
            claims.append(outcome)
            self.claims_registry[outcome.id] = outcome
            if thesis:
                thesis.dependent_claims.append(outcome.id)
                
        # Extract invalidation conditions
        invalidations = self._extract_invalidation_conditions(agent_output, source_agent, symbol, timestamp, claims)
        for inv in invalidations:
            claims.append(inv)
            self.claims_registry[inv.id] = inv
            
        # Build claim relationships
        self._build_relationships(claims)
        
        logger.info(f"Constructed claim graph with {len(claims)} claims from {source_agent}")
        return claims
    
    def _extract_thesis(
        self,
        output: Dict[str, Any],
        source: str,
        symbol: str,
        timestamp: datetime
    ) -> Optional[Claim]:
        """Extract the main thesis/claim from agent output"""
        
        # Common keys where thesis might be found
        thesis_keys = ['thesis', 'recommendation', 'conclusion', 'prediction', 'signal', 'direction']
        
        content = None
        for key in thesis_keys:
            if key in output and output[key]:
                content = output[key]
                if isinstance(content, dict):
                    content = content.get('rationale') or content.get('reasoning') or str(content)
                break
                
        if not content:
            # Try to construct from signal/action
            action = output.get('action') or output.get('decision')
            if action:
                content = f"{action} {symbol} based on {source} analysis"
                
        if not content:
            content = f"Agent {source} generated output for {symbol}"
            
        confidence = output.get('confidence', 0.5)
        if isinstance(confidence, (int, float)):
            confidence = float(confidence)
        else:
            confidence = 0.5
            
        return Claim(
            id="",
            claim_type=ClaimType.THESIS,
            content=str(content),
            source=source,
            timestamp=timestamp,
            confidence=confidence
        )
    
    def _extract_assumptions(
        self,
        output: Dict[str, Any],
        source: str,
        symbol: str,
        timestamp: datetime,
        thesis: Optional[Claim]
    ) -> List[Claim]:
        """Extract implicit and explicit assumptions"""
        assumptions = []
        
        # Look for explicit assumptions
        explicit = output.get('assumptions', [])
        if isinstance(explicit, list):
            for assumption in explicit:
                assumptions.append(Claim(
                    id="",
                    claim_type=ClaimType.ASSUMPTION,
                    content=str(assumption),
                    source=source,
                    timestamp=timestamp,
                    confidence=0.7  # Assumptions are inherently less certain
                ))
                
        # Infer common trading assumptions if not explicit
        if not explicit:
            inferred_assumptions = [
                f"Market conditions for {symbol} will remain within historical patterns",
                f"Liquidity for {symbol} is sufficient for intended position size",
                "No major macro events will invalidate this thesis before execution",
                f"Signal from {source} is not based on stale or corrupted data"
            ]
            
            for assumption in inferred_assumptions:
                assumptions.append(Claim(
                    id="",
                    claim_type=ClaimType.ASSUMPTION,
                    content=assumption,
                    source=f"{source}_inferred",
                    timestamp=timestamp,
                    confidence=0.5  # Inferred assumptions have lower confidence
                ))
                
        return assumptions
    
    def _extract_evidence_claims(
        self,
        output: Dict[str, Any],
        source: str,
        symbol: str,
        timestamp: datetime
    ) -> List[Claim]:
        """Extract evidence-based claims"""
        evidence_claims = []
        
        # Look for evidence in various forms
        evidence_keys = ['evidence', 'indicators', 'metrics', 'data_points', 'factors']
        
        for key in evidence_keys:
            if key in output:
                evidence_data = output[key]
                if isinstance(evidence_data, list):
                    for item in evidence_data:
                        content = item if isinstance(item, str) else str(item)
                        evidence_claims.append(Claim(
                            id="",
                            claim_type=ClaimType.EVIDENCE,
                            content=content,
                            source=source,
                            timestamp=timestamp,
                            confidence=0.8
                        ))
                elif isinstance(evidence_data, dict):
                    for k, v in evidence_data.items():
                        content = f"{k}: {v}"
                        confidence = 0.8
                        if isinstance(v, dict):
                            confidence = v.get('confidence', 0.8)
                        evidence_claims.append(Claim(
                            id="",
                            claim_type=ClaimType.EVIDENCE,
                            content=content,
                            source=source,
                            timestamp=timestamp,
                            confidence=confidence
                        ))
                        
        return evidence_claims
    
    def _extract_causal_links(
        self,
        output: Dict[str, Any],
        source: str,
        symbol: str,
        timestamp: datetime,
        existing_claims: List[Claim]
    ) -> List[Claim]:
        """Extract inferred causal relationships"""
        causal_links = []
        
        # Look for causal reasoning
        reasoning = output.get('reasoning') or output.get('rationale') or output.get('explanation')
        if reasoning and isinstance(reasoning, str):
            # Simple pattern matching for causal language
            causal_patterns = [
                r'(\w+)\s+(?:causes?|leads? to|results? in|produces?|generates?)\s+(\w+)',
                r'(\w+)\s+(?:because|due to|as a result of|since)\s+(\w+)',
                r'if\s+(\w+).*then\s+(\w+)'
            ]
            
            for pattern in causal_patterns:
                matches = re.findall(pattern, reasoning, re.IGNORECASE)
                for match in matches:
                    cause, effect = match if isinstance(match, tuple) else (match, "unknown")
                    causal_links.append(Claim(
                        id="",
                        claim_type=ClaimType.INFERRED_CAUSAL_LINK,
                        content=f"{cause} → {effect}",
                        source=source,
                        timestamp=timestamp,
                        confidence=0.6  # Causal inferences are uncertain
                    ))
                    
        # If no explicit causal links found, infer from structure
        if not causal_links and 'factors' in output:
            factors = output['factors']
            if isinstance(factors, dict):
                for factor, impact in factors.items():
                    causal_links.append(Claim(
                        id="",
                        claim_type=ClaimType.INFERRED_CAUSAL_LINK,
                        content=f"{factor} influences {symbol} price",
                        source=f"{source}_inferred",
                        timestamp=timestamp,
                        confidence=abs(impact) if isinstance(impact, (int, float)) else 0.5
                    ))
                    
        return causal_links
    
    def _extract_predicted_outcomes(
        self,
        output: Dict[str, Any],
        source: str,
        symbol: str,
        timestamp: datetime,
        thesis: Optional[Claim]
    ) -> List[Claim]:
        """Extract predicted outcomes"""
        outcomes = []
        
        # Look for price targets, expected returns, etc.
        prediction_keys = ['target', 'price_target', 'expected_return', 'predicted_price', 'forecast']
        
        for key in prediction_keys:
            if key in output:
                value = output[key]
                outcomes.append(Claim(
                    id="",
                    claim_type=ClaimType.PREDICTED_OUTCOME,
                    content=f"Predicted {key} for {symbol}: {value}",
                    source=source,
                    timestamp=timestamp,
                    confidence=output.get('confidence', 0.5)
                ))
                
        # Look for timeframe predictions
        if 'timeframe' in output or 'horizon' in output:
            timeframe = output.get('timeframe') or output.get('horizon')
            outcomes.append(Claim(
                id="",
                claim_type=ClaimType.PREDICTED_OUTCOME,
                content=f"Expected to materialize within {timeframe}",
                source=source,
                timestamp=timestamp,
                confidence=0.6
            ))
            
        return outcomes
    
    def _extract_invalidation_conditions(
        self,
        output: Dict[str, Any],
        source: str,
        symbol: str,
        timestamp: datetime,
        claims: List[Claim]
    ) -> List[Claim]:
        """Extract conditions that would invalidate the thesis"""
        invalidations = []
        
        # Look for explicit invalidation conditions
        if 'invalidation_conditions' in output:
            conditions = output['invalidation_conditions']
            if isinstance(conditions, list):
                for condition in conditions:
                    invalidations.append(Claim(
                        id="",
                        claim_type=ClaimType.INVALIDATION_CONDITION,
                        content=str(condition),
                        source=source,
                        timestamp=timestamp,
                        confidence=0.9  # Invalidation conditions are factual
                    ))
                    
        # Generate standard invalidation conditions if not present
        if not invalidations:
            standard_conditions = [
                f"{symbol} price moves against thesis by more than 2x expected volatility",
                f"Volume in {symbol} drops below 50% of 20-day average",
                "Macro event fundamentally changes market structure",
                f"Opposite signal from {source} with higher confidence emerges",
                "Regime shifts to historically incompatible state"
            ]
            
            for condition in standard_conditions:
                invalidations.append(Claim(
                    id="",
                    claim_type=ClaimType.INVALIDATION_CONDITION,
                    content=condition,
                    source=f"{source}_standard",
                    timestamp=timestamp,
                    confidence=0.9
                ))
                
        return invalidations
    
    def _build_relationships(self, claims: List[Claim]) -> None:
        """Build and store claim relationships"""
        for claim in claims:
            if claim.dependent_claims:
                for dep_id in claim.dependent_claims:
                    self.claim_relationships[claim.id].add(dep_id)
                    
    def get_claim_dependencies(self, claim_id: str) -> Set[str]:
        """Get all claims this claim depends on (transitive)"""
        dependencies = set()
        to_process = [claim_id]
        visited = set()
        
        while to_process:
            current = to_process.pop()
            if current in visited:
                continue
            visited.add(current)
            
            claim = self.claims_registry.get(current)
            if claim and claim.dependent_claims:
                for dep in claim.dependent_claims:
                    dependencies.add(dep)
                    to_process.append(dep)
                    
        return dependencies
    
    def get_claim_subgraph(self, root_claim_id: str) -> List[Claim]:
        """Get the subgraph of claims rooted at the given claim"""
        subgraph = []
        dependencies = self.get_claim_dependencies(root_claim_id)
        dependencies.add(root_claim_id)
        
        for claim_id in dependencies:
            if claim_id in self.claims_registry:
                subgraph.append(self.claims_registry[claim_id])
                
        return subgraph
    
    def compute_claim_graph_hash(self, claims: List[Claim]) -> str:
        """Compute a hash representing the entire claim graph structure"""
        sorted_claims = sorted(claims, key=lambda c: c.id)
        content = "|".join([c.compute_hash() for c in sorted_claims])
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]


from collections import defaultdict
