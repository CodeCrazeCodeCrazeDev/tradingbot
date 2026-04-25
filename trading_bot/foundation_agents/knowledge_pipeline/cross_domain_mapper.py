"""
Cross-Domain Mapper - Knowledge Transfer Across Domains
========================================================

Implements cross-domain knowledge mapping:
1. Concept mapping between domains (physics -> finance)
2. Analogy detection and transfer
3. Method adaptation from other fields
4. Cross-domain pattern recognition

Based on the Foundation Agents paper (arXiv:2504.01990) knowledge systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class Domain(Enum):
    """Knowledge domains"""
    FINANCE = "finance"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    COMPUTER_SCIENCE = "computer_science"
    MATHEMATICS = "mathematics"
    ECONOMICS = "economics"
    PSYCHOLOGY = "psychology"
    ENGINEERING = "engineering"
    STATISTICS = "statistics"
    NEUROSCIENCE = "neuroscience"


@dataclass
class Concept:
    """A concept in a domain"""
    concept_id: str
    name: str
    domain: Domain
    description: str
    
    # Properties
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)  # Related concept IDs
    
    # Embeddings (for similarity)
    embedding: Optional[np.ndarray] = None
    
    # Metadata
    source: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'concept_id': self.concept_id,
            'name': self.name,
            'domain': self.domain.value,
            'description': self.description,
            'properties': self.properties,
            'relationships': self.relationships
        }


@dataclass
class ConceptMapping:
    """Mapping between concepts across domains"""
    mapping_id: str
    source_concept: str
    target_concept: str
    source_domain: Domain
    target_domain: Domain
    
    # Mapping quality
    similarity_score: float = 0.0
    confidence: float = 0.0
    
    # Mapping type
    mapping_type: str = "analogy"  # analogy, generalization, specialization, equivalence
    
    # Explanation
    rationale: str = ""
    shared_properties: List[str] = field(default_factory=list)
    differences: List[str] = field(default_factory=list)
    
    # Validation
    validated: bool = False
    validation_evidence: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'mapping_id': self.mapping_id,
            'source_concept': self.source_concept,
            'target_concept': self.target_concept,
            'source_domain': self.source_domain.value,
            'target_domain': self.target_domain.value,
            'similarity_score': self.similarity_score,
            'confidence': self.confidence,
            'mapping_type': self.mapping_type,
            'rationale': self.rationale
        }


@dataclass
class DomainAnalogy:
    """An analogy between domains"""
    analogy_id: str
    source_domain: Domain
    target_domain: Domain
    
    # Analogy components
    source_system: str  # e.g., "thermodynamics"
    target_system: str  # e.g., "market dynamics"
    
    # Mappings
    concept_mappings: List[ConceptMapping] = field(default_factory=list)
    
    # Quality
    coherence_score: float = 0.0  # How well mappings fit together
    utility_score: float = 0.0    # How useful for predictions
    
    # Applications
    potential_insights: List[str] = field(default_factory=list)
    trading_applications: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'analogy_id': self.analogy_id,
            'source_domain': self.source_domain.value,
            'target_domain': self.target_domain.value,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'coherence_score': self.coherence_score,
            'utility_score': self.utility_score,
            'potential_insights': self.potential_insights,
            'trading_applications': self.trading_applications
        }


class ConceptExtractor:
    """Extract concepts from text"""
    
    # Domain-specific concept patterns
    DOMAIN_CONCEPTS = {
        Domain.PHYSICS: [
            ('entropy', 'measure of disorder/randomness'),
            ('equilibrium', 'state of balance'),
            ('momentum', 'tendency to continue motion'),
            ('energy', 'capacity to do work'),
            ('force', 'interaction causing change'),
            ('wave', 'propagating disturbance'),
            ('field', 'region of influence'),
            ('particle', 'discrete unit'),
            ('resonance', 'amplification at natural frequency'),
            ('phase_transition', 'sudden state change')
        ],
        Domain.BIOLOGY: [
            ('evolution', 'change through selection'),
            ('adaptation', 'adjustment to environment'),
            ('ecosystem', 'interacting system'),
            ('predator_prey', 'competitive dynamics'),
            ('mutation', 'random variation'),
            ('fitness', 'survival capability'),
            ('symbiosis', 'mutual benefit'),
            ('homeostasis', 'maintaining stability'),
            ('emergence', 'complex from simple'),
            ('network', 'interconnected nodes')
        ],
        Domain.PSYCHOLOGY: [
            ('herd_behavior', 'following the crowd'),
            ('cognitive_bias', 'systematic error'),
            ('anchoring', 'reliance on first information'),
            ('loss_aversion', 'fear of losses'),
            ('overconfidence', 'excessive certainty'),
            ('confirmation_bias', 'seeking confirming evidence'),
            ('fear', 'response to threat'),
            ('greed', 'excessive desire'),
            ('regret', 'negative emotion from decisions'),
            ('attention', 'focus of awareness')
        ],
        Domain.FINANCE: [
            ('volatility', 'price variation'),
            ('momentum', 'trend continuation'),
            ('mean_reversion', 'return to average'),
            ('liquidity', 'ease of trading'),
            ('risk', 'uncertainty of outcome'),
            ('return', 'profit from investment'),
            ('correlation', 'co-movement'),
            ('arbitrage', 'riskless profit'),
            ('leverage', 'amplification'),
            ('diversification', 'spreading risk')
        ]
    }
    
    def extract_concepts(self, text: str, domain: Domain) -> List[Concept]:
        """Extract concepts from text for a domain"""
        concepts = []
        text_lower = text.lower()
        
        domain_concepts = self.DOMAIN_CONCEPTS.get(domain, [])
        
        for concept_name, description in domain_concepts:
            if concept_name.replace('_', ' ') in text_lower or concept_name in text_lower:
                concept = Concept(
                    concept_id=f"{domain.value}_{concept_name}",
                    name=concept_name,
                    domain=domain,
                    description=description,
                    source=text[:100]
                )
                concepts.append(concept)
        
        return concepts


class AnalogyEngine:
    """Engine for finding and applying analogies"""
    
    # Pre-defined cross-domain analogies
    KNOWN_ANALOGIES = {
        (Domain.PHYSICS, Domain.FINANCE): [
            {
                'source': 'entropy',
                'target': 'volatility',
                'rationale': 'Both measure disorder/uncertainty in a system',
                'shared': ['increases over time', 'measure of randomness']
            },
            {
                'source': 'momentum',
                'target': 'momentum',
                'rationale': 'Tendency to continue in same direction',
                'shared': ['persistence', 'inertia']
            },
            {
                'source': 'equilibrium',
                'target': 'fair_value',
                'rationale': 'State where forces balance',
                'shared': ['stability', 'balance point']
            },
            {
                'source': 'phase_transition',
                'target': 'regime_change',
                'rationale': 'Sudden shift in system behavior',
                'shared': ['discontinuity', 'critical point']
            },
            {
                'source': 'resonance',
                'target': 'feedback_loop',
                'rationale': 'Amplification through reinforcement',
                'shared': ['amplification', 'frequency matching']
            }
        ],
        (Domain.BIOLOGY, Domain.FINANCE): [
            {
                'source': 'evolution',
                'target': 'market_adaptation',
                'rationale': 'Survival of fittest strategies',
                'shared': ['selection', 'adaptation']
            },
            {
                'source': 'predator_prey',
                'target': 'market_competition',
                'rationale': 'Competitive dynamics between participants',
                'shared': ['cycles', 'competition']
            },
            {
                'source': 'ecosystem',
                'target': 'market_structure',
                'rationale': 'Interconnected participants',
                'shared': ['interdependence', 'niches']
            },
            {
                'source': 'mutation',
                'target': 'strategy_innovation',
                'rationale': 'Random variations lead to new approaches',
                'shared': ['randomness', 'novelty']
            }
        ],
        (Domain.PSYCHOLOGY, Domain.FINANCE): [
            {
                'source': 'herd_behavior',
                'target': 'momentum',
                'rationale': 'Following crowd creates trends',
                'shared': ['social influence', 'trend following']
            },
            {
                'source': 'loss_aversion',
                'target': 'asymmetric_returns',
                'rationale': 'Losses hurt more than gains help',
                'shared': ['asymmetry', 'risk perception']
            },
            {
                'source': 'anchoring',
                'target': 'support_resistance',
                'rationale': 'Reference points influence decisions',
                'shared': ['reference dependence', 'memory']
            }
        ]
    }
    
    def find_analogies(
        self,
        source_domain: Domain,
        target_domain: Domain
    ) -> List[Dict]:
        """Find analogies between domains"""
        key = (source_domain, target_domain)
        reverse_key = (target_domain, source_domain)
        
        if key in self.KNOWN_ANALOGIES:
            return self.KNOWN_ANALOGIES[key]
        elif reverse_key in self.KNOWN_ANALOGIES:
            # Reverse the analogies
            reversed_analogies = []
            for analogy in self.KNOWN_ANALOGIES[reverse_key]:
                reversed_analogies.append({
                    'source': analogy['target'],
                    'target': analogy['source'],
                    'rationale': analogy['rationale'],
                    'shared': analogy['shared']
                })
            return reversed_analogies
        
        return []


class CrossDomainMapper:
    """
    Cross-Domain Mapper
    
    Maps knowledge across domains to enable transfer learning
    and novel insight generation.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.concept_extractor = ConceptExtractor()
        self.analogy_engine = AnalogyEngine()
        
        # Storage
        self.concepts: Dict[str, Concept] = {}
        self.mappings: Dict[str, ConceptMapping] = {}
        self.analogies: Dict[str, DomainAnalogy] = {}
        
        # Domain knowledge
        self.domain_concepts: Dict[Domain, Set[str]] = defaultdict(set)
        
        # Statistics
        self.stats = {
            'concepts_stored': 0,
            'mappings_created': 0,
            'analogies_found': 0,
            'insights_generated': 0
        }
        
        # Initialize with known concepts
        self._initialize_concepts()
        
        logger.info("Cross-Domain Mapper initialized")
    
    def _initialize_concepts(self):
        """Initialize with known domain concepts"""
        for domain, concepts in self.concept_extractor.DOMAIN_CONCEPTS.items():
            for name, description in concepts:
                concept = Concept(
                    concept_id=f"{domain.value}_{name}",
                    name=name,
                    domain=domain,
                    description=description
                )
                self.add_concept(concept)
    
    def add_concept(self, concept: Concept):
        """Add a concept to the knowledge base"""
        self.concepts[concept.concept_id] = concept
        self.domain_concepts[concept.domain].add(concept.concept_id)
        self.stats['concepts_stored'] += 1
    
    def find_mapping(
        self,
        source_concept: str,
        target_domain: Domain
    ) -> List[ConceptMapping]:
        """Find mappings from a source concept to target domain"""
        if source_concept not in self.concepts:
            return []
        
        source = self.concepts[source_concept]
        mappings = []
        
        # Find analogies between domains
        analogies = self.analogy_engine.find_analogies(source.domain, target_domain)
        
        for analogy in analogies:
            if analogy['source'] == source.name:
                target_id = f"{target_domain.value}_{analogy['target']}"
                
                mapping = ConceptMapping(
                    mapping_id=f"map_{source_concept}_{target_id}",
                    source_concept=source_concept,
                    target_concept=target_id,
                    source_domain=source.domain,
                    target_domain=target_domain,
                    similarity_score=0.7,  # Default for known analogies
                    confidence=0.8,
                    mapping_type="analogy",
                    rationale=analogy['rationale'],
                    shared_properties=analogy['shared']
                )
                
                mappings.append(mapping)
                self.mappings[mapping.mapping_id] = mapping
                self.stats['mappings_created'] += 1
        
        return mappings
    
    def map_domains(
        self,
        source_domain: Domain,
        target_domain: Domain
    ) -> DomainAnalogy:
        """Create comprehensive mapping between two domains"""
        analogy_id = f"analogy_{source_domain.value}_{target_domain.value}"
        
        # Get all analogies
        raw_analogies = self.analogy_engine.find_analogies(source_domain, target_domain)
        
        # Create concept mappings
        concept_mappings = []
        for analogy in raw_analogies:
            source_id = f"{source_domain.value}_{analogy['source']}"
            target_id = f"{target_domain.value}_{analogy['target']}"
            
            mapping = ConceptMapping(
                mapping_id=f"map_{source_id}_{target_id}",
                source_concept=source_id,
                target_concept=target_id,
                source_domain=source_domain,
                target_domain=target_domain,
                similarity_score=0.7,
                confidence=0.8,
                mapping_type="analogy",
                rationale=analogy['rationale'],
                shared_properties=analogy['shared']
            )
            concept_mappings.append(mapping)
        
        # Generate insights
        insights = self._generate_insights(source_domain, target_domain, concept_mappings)
        
        # Create domain analogy
        domain_analogy = DomainAnalogy(
            analogy_id=analogy_id,
            source_domain=source_domain,
            target_domain=target_domain,
            source_system=source_domain.value,
            target_system=target_domain.value,
            concept_mappings=concept_mappings,
            coherence_score=len(concept_mappings) / 10,  # More mappings = more coherent
            utility_score=0.6,
            potential_insights=insights,
            trading_applications=self._identify_trading_applications(insights)
        )
        
        self.analogies[analogy_id] = domain_analogy
        self.stats['analogies_found'] += 1
        
        return domain_analogy
    
    def _generate_insights(
        self,
        source_domain: Domain,
        target_domain: Domain,
        mappings: List[ConceptMapping]
    ) -> List[str]:
        """Generate insights from domain mappings"""
        insights = []
        
        for mapping in mappings:
            source = self.concepts.get(mapping.source_concept)
            target = self.concepts.get(mapping.target_concept)
            
            if source and target:
                insight = (
                    f"The concept of '{source.name}' in {source_domain.value} "
                    f"maps to '{target.name}' in {target_domain.value}. "
                    f"This suggests that {mapping.rationale.lower()}."
                )
                insights.append(insight)
                self.stats['insights_generated'] += 1
        
        # Generate higher-level insights
        if len(mappings) >= 3:
            insights.append(
                f"Multiple mappings between {source_domain.value} and {target_domain.value} "
                f"suggest deep structural similarities that could inform trading strategies."
            )
        
        return insights
    
    def _identify_trading_applications(self, insights: List[str]) -> List[str]:
        """Identify trading applications from insights"""
        applications = []
        
        trading_keywords = {
            'momentum': 'Momentum-based trading strategies',
            'equilibrium': 'Mean reversion strategies',
            'phase_transition': 'Regime change detection',
            'evolution': 'Adaptive strategy optimization',
            'predator_prey': 'Market maker strategies',
            'herd_behavior': 'Sentiment-based trading',
            'entropy': 'Volatility forecasting',
            'resonance': 'Feedback loop detection'
        }
        
        for insight in insights:
            insight_lower = insight.lower()
            for keyword, application in trading_keywords.items():
                if keyword in insight_lower:
                    if application not in applications:
                        applications.append(application)
        
        return applications
    
    def transfer_method(
        self,
        method_name: str,
        source_domain: Domain,
        target_domain: Domain
    ) -> Dict[str, Any]:
        """Transfer a method from one domain to another"""
        # Get domain mapping
        analogy = self.map_domains(source_domain, target_domain)
        
        # Create method transfer proposal
        transfer = {
            'method': method_name,
            'source_domain': source_domain.value,
            'target_domain': target_domain.value,
            'concept_mappings': [m.to_dict() for m in analogy.concept_mappings],
            'adaptation_needed': [],
            'potential_benefits': [],
            'risks': []
        }
        
        # Identify adaptations needed
        if source_domain == Domain.PHYSICS:
            transfer['adaptation_needed'].append(
                "Replace physical constants with market parameters"
            )
            transfer['adaptation_needed'].append(
                "Account for non-stationarity in financial data"
            )
        
        if source_domain == Domain.BIOLOGY:
            transfer['adaptation_needed'].append(
                "Adapt evolutionary timescales to market timescales"
            )
            transfer['adaptation_needed'].append(
                "Define fitness function in terms of returns/risk"
            )
        
        # Identify benefits
        transfer['potential_benefits'].append(
            f"Novel perspective from {source_domain.value}"
        )
        transfer['potential_benefits'].append(
            "Potential for discovering new patterns"
        )
        
        # Identify risks
        transfer['risks'].append(
            "Analogy may break down under certain conditions"
        )
        transfer['risks'].append(
            "Domain-specific assumptions may not transfer"
        )
        
        return transfer
    
    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept by ID"""
        return self.concepts.get(concept_id)
    
    def get_domain_concepts(self, domain: Domain) -> List[Concept]:
        """Get all concepts in a domain"""
        concept_ids = self.domain_concepts.get(domain, set())
        return [self.concepts[cid] for cid in concept_ids if cid in self.concepts]
    
    def find_related_concepts(
        self,
        concept_id: str,
        max_results: int = 10
    ) -> List[Tuple[Concept, float]]:
        """Find concepts related to a given concept"""
        if concept_id not in self.concepts:
            return []
        
        source = self.concepts[concept_id]
        related = []
        
        # Find through mappings
        for mapping in self.mappings.values():
            if mapping.source_concept == concept_id:
                target = self.concepts.get(mapping.target_concept)
                if target:
                    related.append((target, mapping.similarity_score))
            elif mapping.target_concept == concept_id:
                source_concept = self.concepts.get(mapping.source_concept)
                if source_concept:
                    related.append((source_concept, mapping.similarity_score))
        
        # Sort by similarity
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:max_results]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get mapper statistics"""
        return {
            **self.stats,
            'domains_covered': len(self.domain_concepts),
            'concepts_by_domain': {
                d.value: len(concepts)
                for d, concepts in self.domain_concepts.items()
            },
            'total_mappings': len(self.mappings),
            'total_analogies': len(self.analogies)
        }
