"""
Economic Theory Generator - Novel Theory Synthesis
====================================================

Implements automatic economic theory generation:
1. Pattern-based theory construction
2. Causal mechanism formalization
3. Theory validation framework
4. Theory evolution and refinement

Based on the Foundation Agents paper (arXiv:2504.01990) causal systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class TheoryType(Enum):
    """Types of economic theories"""
    BEHAVIORAL = "behavioral"           # Based on agent behavior
    STRUCTURAL = "structural"           # Market structure
    EQUILIBRIUM = "equilibrium"         # Equilibrium conditions
    DYNAMIC = "dynamic"                 # Time-varying relationships
    INFORMATIONAL = "informational"     # Information flow
    INSTITUTIONAL = "institutional"     # Institutional effects
    NETWORK = "network"                 # Network effects


class TheoryStatus(Enum):
    """Status of a theory"""
    PROPOSED = "proposed"
    TESTING = "testing"
    VALIDATED = "validated"
    REFUTED = "refuted"
    REFINED = "refined"
    ARCHIVED = "archived"


class MechanismType(Enum):
    """Types of causal mechanisms"""
    DIRECT = "direct"                   # Direct causation
    MEDIATED = "mediated"               # Through mediator
    MODERATED = "moderated"             # Conditional on moderator
    FEEDBACK = "feedback"               # Feedback loop
    THRESHOLD = "threshold"             # Threshold effect
    DELAYED = "delayed"                 # Time-delayed effect


@dataclass
class CausalMechanism:
    """A causal mechanism in a theory"""
    mechanism_id: str
    mechanism_type: MechanismType
    
    # Structure
    cause: str
    effect: str
    mediators: List[str] = field(default_factory=list)
    moderators: List[str] = field(default_factory=list)
    
    # Properties
    strength: float = 0.5
    lag: int = 0
    threshold: Optional[float] = None
    
    # Description
    description: str = ""
    mathematical_form: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'mechanism_id': self.mechanism_id,
            'mechanism_type': self.mechanism_type.value,
            'cause': self.cause,
            'effect': self.effect,
            'mediators': self.mediators,
            'moderators': self.moderators,
            'strength': self.strength,
            'description': self.description
        }


@dataclass
class EconomicTheory:
    """An economic theory"""
    theory_id: str
    name: str
    description: str
    theory_type: TheoryType
    
    # Core components
    assumptions: List[str] = field(default_factory=list)
    mechanisms: List[CausalMechanism] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)
    
    # Variables
    endogenous_vars: List[str] = field(default_factory=list)
    exogenous_vars: List[str] = field(default_factory=list)
    
    # Formal representation
    equations: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    # Validation
    status: TheoryStatus = TheoryStatus.PROPOSED
    evidence_for: List[Dict] = field(default_factory=list)
    evidence_against: List[Dict] = field(default_factory=list)
    confidence: float = 0.5
    
    # Evolution
    version: int = 1
    parent_theory_id: Optional[str] = None
    refinements: List[str] = field(default_factory=list)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_validated: Optional[datetime] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_evidence(self, evidence: Dict, supports: bool):
        """Add evidence for or against the theory"""
        if supports:
            self.evidence_for.append(evidence)
            self.confidence = min(0.95, self.confidence + 0.05)
        else:
            self.evidence_against.append(evidence)
            self.confidence = max(0.05, self.confidence - 0.05)
    
    def to_dict(self) -> Dict:
        return {
            'theory_id': self.theory_id,
            'name': self.name,
            'description': self.description,
            'theory_type': self.theory_type.value,
            'assumptions': self.assumptions,
            'mechanisms': [m.to_dict() for m in self.mechanisms],
            'predictions': self.predictions,
            'status': self.status.value,
            'confidence': self.confidence,
            'version': self.version
        }


class TheoryTemplate:
    """Templates for generating theories"""
    
    TEMPLATES = {
        TheoryType.BEHAVIORAL: {
            'assumptions': [
                "Agents have bounded rationality",
                "Information processing is costly",
                "Agents learn from experience"
            ],
            'mechanism_patterns': [
                "{agent_behavior} leads to {market_outcome}",
                "When {condition}, agents exhibit {behavior}",
                "{cognitive_bias} causes {price_anomaly}"
            ]
        },
        TheoryType.STRUCTURAL: {
            'assumptions': [
                "Market structure affects price formation",
                "Liquidity varies across market segments",
                "Transaction costs are non-negligible"
            ],
            'mechanism_patterns': [
                "{market_feature} affects {price_property}",
                "Changes in {structure} lead to changes in {outcome}",
                "{institutional_change} impacts {market_behavior}"
            ]
        },
        TheoryType.EQUILIBRIUM: {
            'assumptions': [
                "Markets tend toward equilibrium",
                "Arbitrage opportunities are temporary",
                "Prices reflect available information"
            ],
            'mechanism_patterns': [
                "{imbalance} triggers {adjustment_process}",
                "Deviation from {equilibrium} creates {force}",
                "{shock} causes temporary {disequilibrium}"
            ]
        },
        TheoryType.DYNAMIC: {
            'assumptions': [
                "Relationships evolve over time",
                "Past states influence current behavior",
                "Regime changes occur"
            ],
            'mechanism_patterns': [
                "{variable} at t-{lag} affects {outcome} at t",
                "Regime switches when {condition}",
                "{trend} persists until {reversal_condition}"
            ]
        },
        TheoryType.INFORMATIONAL: {
            'assumptions': [
                "Information is asymmetrically distributed",
                "Information revelation affects prices",
                "Agents update beliefs based on signals"
            ],
            'mechanism_patterns': [
                "{information_event} leads to {price_adjustment}",
                "{signal} reveals {underlying_state}",
                "Information flow from {source} to {recipient}"
            ]
        }
    }


class MechanismGenerator:
    """Generates causal mechanisms from patterns"""
    
    def generate_from_causal_edge(
        self,
        source: str,
        target: str,
        strength: float,
        lag: int = 0,
        context: Optional[Dict] = None
    ) -> CausalMechanism:
        """Generate mechanism from causal edge"""
        context = context or {}
        
        # Determine mechanism type
        if lag > 0:
            mech_type = MechanismType.DELAYED
        elif context.get('has_mediator'):
            mech_type = MechanismType.MEDIATED
        elif context.get('has_moderator'):
            mech_type = MechanismType.MODERATED
        elif context.get('is_feedback'):
            mech_type = MechanismType.FEEDBACK
        else:
            mech_type = MechanismType.DIRECT
        
        # Generate description
        if mech_type == MechanismType.DIRECT:
            description = f"Changes in {source} directly cause changes in {target}"
        elif mech_type == MechanismType.DELAYED:
            description = f"Changes in {source} affect {target} with a lag of {lag} periods"
        elif mech_type == MechanismType.MEDIATED:
            mediator = context.get('mediator', 'unknown')
            description = f"{source} affects {target} through {mediator}"
        elif mech_type == MechanismType.MODERATED:
            moderator = context.get('moderator', 'unknown')
            description = f"The effect of {source} on {target} depends on {moderator}"
        else:
            description = f"{source} influences {target}"
        
        # Generate mathematical form
        if mech_type == MechanismType.DIRECT:
            math_form = f"{target} = β * {source} + ε"
        elif mech_type == MechanismType.DELAYED:
            math_form = f"{target}_t = β * {source}_{{t-{lag}}} + ε"
        else:
            math_form = None
        
        return CausalMechanism(
            mechanism_id=f"mech_{hashlib.md5(f'{source}_{target}'.encode()).hexdigest()[:8]}",
            mechanism_type=mech_type,
            cause=source,
            effect=target,
            mediators=context.get('mediators', []),
            moderators=context.get('moderators', []),
            strength=strength,
            lag=lag,
            description=description,
            mathematical_form=math_form
        )


class TheoryValidator:
    """Validates economic theories"""
    
    def validate(
        self,
        theory: EconomicTheory,
        data: Dict[str, np.ndarray],
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """Validate a theory against data"""
        validation_results = {
            'theory_id': theory.theory_id,
            'mechanisms_tested': 0,
            'mechanisms_supported': 0,
            'predictions_tested': 0,
            'predictions_confirmed': 0,
            'overall_support': 0.0,
            'details': []
        }
        
        # Test each mechanism
        for mechanism in theory.mechanisms:
            if mechanism.cause in data and mechanism.effect in data:
                result = self._test_mechanism(
                    mechanism,
                    data[mechanism.cause],
                    data[mechanism.effect],
                    significance_level
                )
                validation_results['mechanisms_tested'] += 1
                if result['supported']:
                    validation_results['mechanisms_supported'] += 1
                validation_results['details'].append(result)
        
        # Calculate overall support
        if validation_results['mechanisms_tested'] > 0:
            validation_results['overall_support'] = (
                validation_results['mechanisms_supported'] / 
                validation_results['mechanisms_tested']
            )
        
        return validation_results
    
    def _test_mechanism(
        self,
        mechanism: CausalMechanism,
        cause_data: np.ndarray,
        effect_data: np.ndarray,
        significance_level: float
    ) -> Dict[str, Any]:
        """Test a single mechanism"""
        from scipy import stats
        
        # Adjust for lag
        if mechanism.lag > 0:
            cause_data = cause_data[:-mechanism.lag]
            effect_data = effect_data[mechanism.lag:]
        
        # Correlation test
        corr, p_value = stats.pearsonr(cause_data, effect_data)
        
        # Direction check
        expected_direction = mechanism.strength > 0
        actual_direction = corr > 0
        direction_match = expected_direction == actual_direction
        
        supported = p_value < significance_level and direction_match
        
        return {
            'mechanism_id': mechanism.mechanism_id,
            'correlation': corr,
            'p_value': p_value,
            'direction_match': direction_match,
            'supported': supported
        }


class EconomicTheoryGenerator:
    """
    Economic Theory Generator
    
    Generates and evolves economic theories from:
    - Causal discoveries
    - Pattern observations
    - Cross-domain analogies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.mechanism_generator = MechanismGenerator()
        self.validator = TheoryValidator()
        
        # Storage
        self.theories: Dict[str, EconomicTheory] = {}
        self.theory_history: List[EconomicTheory] = []
        
        # Statistics
        self.stats = {
            'theories_generated': 0,
            'theories_validated': 0,
            'theories_refuted': 0,
            'by_type': defaultdict(int)
        }
        
        logger.info("Economic Theory Generator initialized")
    
    def generate_from_causal_graph(
        self,
        graph_dict: Dict,
        theory_type: TheoryType = TheoryType.DYNAMIC
    ) -> EconomicTheory:
        """Generate theory from causal graph"""
        nodes = graph_dict.get('nodes', [])
        edges = graph_dict.get('edges', [])
        
        # Generate mechanisms
        mechanisms = []
        for edge in edges:
            mechanism = self.mechanism_generator.generate_from_causal_edge(
                source=edge.get('source', ''),
                target=edge.get('target', ''),
                strength=edge.get('strength', 0.5),
                lag=edge.get('lag', 0)
            )
            mechanisms.append(mechanism)
        
        # Identify endogenous and exogenous variables
        targets = set(e.get('target', '') for e in edges)
        sources = set(e.get('source', '') for e in edges)
        
        endogenous = list(targets)
        exogenous = list(sources - targets)
        
        # Generate assumptions based on theory type
        template = TheoryTemplate.TEMPLATES.get(theory_type, {})
        assumptions = template.get('assumptions', [])
        
        # Generate predictions
        predictions = []
        for mech in mechanisms:
            if mech.strength > 0:
                predictions.append(
                    f"Increases in {mech.cause} lead to increases in {mech.effect}"
                )
            else:
                predictions.append(
                    f"Increases in {mech.cause} lead to decreases in {mech.effect}"
                )
        
        # Create theory
        theory = EconomicTheory(
            theory_id=f"theory_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=f"Theory of {', '.join(endogenous[:2])} dynamics",
            description=f"A {theory_type.value} theory explaining relationships among {len(nodes)} variables",
            theory_type=theory_type,
            assumptions=assumptions,
            mechanisms=mechanisms,
            predictions=predictions,
            endogenous_vars=endogenous,
            exogenous_vars=exogenous,
            tags=[theory_type.value, 'auto_generated']
        )
        
        self._store_theory(theory)
        
        return theory
    
    def generate_from_pattern(
        self,
        pattern_description: str,
        variables: List[str],
        theory_type: TheoryType = TheoryType.BEHAVIORAL
    ) -> EconomicTheory:
        """Generate theory from observed pattern"""
        # Parse pattern to identify relationships
        mechanisms = []
        
        # Simple heuristic: first variable causes others
        if len(variables) >= 2:
            for i in range(1, len(variables)):
                mechanism = CausalMechanism(
                    mechanism_id=f"mech_pattern_{i}",
                    mechanism_type=MechanismType.DIRECT,
                    cause=variables[0],
                    effect=variables[i],
                    strength=0.5,
                    description=f"Pattern suggests {variables[0]} affects {variables[i]}"
                )
                mechanisms.append(mechanism)
        
        # Generate theory
        theory = EconomicTheory(
            theory_id=f"theory_pattern_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=f"Pattern-based theory: {pattern_description[:50]}",
            description=pattern_description,
            theory_type=theory_type,
            mechanisms=mechanisms,
            predictions=[f"The pattern '{pattern_description}' will persist"],
            endogenous_vars=variables[1:] if len(variables) > 1 else [],
            exogenous_vars=[variables[0]] if variables else [],
            tags=['pattern_based', theory_type.value]
        )
        
        self._store_theory(theory)
        
        return theory
    
    def generate_from_analogy(
        self,
        source_domain: str,
        target_domain: str,
        concept_mappings: List[Dict],
        theory_type: TheoryType = TheoryType.STRUCTURAL
    ) -> EconomicTheory:
        """Generate theory from cross-domain analogy"""
        mechanisms = []
        
        for mapping in concept_mappings:
            source_concept = mapping.get('source_concept', '')
            target_concept = mapping.get('target_concept', '')
            
            mechanism = CausalMechanism(
                mechanism_id=f"mech_analogy_{hashlib.md5(source_concept.encode()).hexdigest()[:6]}",
                mechanism_type=MechanismType.DIRECT,
                cause=target_concept.split('_')[-1] if '_' in target_concept else target_concept,
                effect="market_outcome",
                strength=mapping.get('similarity_score', 0.5),
                description=f"Analogous to {source_concept} in {source_domain}"
            )
            mechanisms.append(mechanism)
        
        # Generate assumptions from analogy
        assumptions = [
            f"Market dynamics are analogous to {source_domain}",
            f"Concepts from {source_domain} transfer to financial markets",
            "The analogy holds under normal market conditions"
        ]
        
        theory = EconomicTheory(
            theory_id=f"theory_analogy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=f"Analogical theory: {source_domain} → {target_domain}",
            description=f"Theory based on analogy from {source_domain} to {target_domain}",
            theory_type=theory_type,
            assumptions=assumptions,
            mechanisms=mechanisms,
            predictions=[
                f"Patterns observed in {source_domain} will manifest in markets"
            ],
            tags=['analogy_based', source_domain, target_domain]
        )
        
        self._store_theory(theory)
        
        return theory
    
    def refine_theory(
        self,
        theory_id: str,
        new_evidence: Dict,
        refinement_description: str
    ) -> Optional[EconomicTheory]:
        """Refine an existing theory based on new evidence"""
        if theory_id not in self.theories:
            return None
        
        original = self.theories[theory_id]
        
        # Create refined version
        refined = EconomicTheory(
            theory_id=f"{theory_id}_v{original.version + 1}",
            name=f"{original.name} (refined)",
            description=f"{original.description}\n\nRefinement: {refinement_description}",
            theory_type=original.theory_type,
            assumptions=original.assumptions.copy(),
            mechanisms=original.mechanisms.copy(),
            predictions=original.predictions.copy(),
            endogenous_vars=original.endogenous_vars.copy(),
            exogenous_vars=original.exogenous_vars.copy(),
            version=original.version + 1,
            parent_theory_id=theory_id,
            refinements=[refinement_description],
            evidence_for=original.evidence_for.copy(),
            evidence_against=original.evidence_against.copy(),
            confidence=original.confidence,
            tags=original.tags + ['refined']
        )
        
        # Add new evidence
        refined.add_evidence(new_evidence, supports=True)
        
        # Update original status
        original.status = TheoryStatus.REFINED
        
        self._store_theory(refined)
        
        return refined
    
    def validate_theory(
        self,
        theory_id: str,
        data: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Validate a theory against data"""
        if theory_id not in self.theories:
            return {'error': 'Theory not found'}
        
        theory = self.theories[theory_id]
        results = self.validator.validate(theory, data)
        
        # Update theory status based on results
        if results['overall_support'] >= 0.7:
            theory.status = TheoryStatus.VALIDATED
            self.stats['theories_validated'] += 1
        elif results['overall_support'] <= 0.3:
            theory.status = TheoryStatus.REFUTED
            self.stats['theories_refuted'] += 1
        else:
            theory.status = TheoryStatus.TESTING
        
        theory.last_validated = datetime.utcnow()
        theory.confidence = results['overall_support']
        
        return results
    
    def _store_theory(self, theory: EconomicTheory):
        """Store a theory"""
        self.theories[theory.theory_id] = theory
        self.theory_history.append(theory)
        self.stats['theories_generated'] += 1
        self.stats['by_type'][theory.theory_type.value] += 1
        
        logger.info(f"Generated theory: {theory.name}")
    
    def get_theory(self, theory_id: str) -> Optional[EconomicTheory]:
        """Get theory by ID"""
        return self.theories.get(theory_id)
    
    def get_theories_by_type(self, theory_type: TheoryType) -> List[EconomicTheory]:
        """Get theories by type"""
        return [t for t in self.theories.values() if t.theory_type == theory_type]
    
    def get_validated_theories(self) -> List[EconomicTheory]:
        """Get validated theories"""
        return [t for t in self.theories.values() if t.status == TheoryStatus.VALIDATED]
    
    def get_theory_lineage(self, theory_id: str) -> List[EconomicTheory]:
        """Get the evolution lineage of a theory"""
        lineage = []
        current_id = theory_id
        
        while current_id:
            theory = self.theories.get(current_id)
            if theory:
                lineage.append(theory)
                current_id = theory.parent_theory_id
            else:
                break
        
        return list(reversed(lineage))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generator statistics"""
        return {
            **self.stats,
            'total_theories': len(self.theories),
            'by_status': {
                status.value: len([t for t in self.theories.values() if t.status == status])
                for status in TheoryStatus
            },
            'avg_confidence': np.mean([t.confidence for t in self.theories.values()]) if self.theories else 0
        }
