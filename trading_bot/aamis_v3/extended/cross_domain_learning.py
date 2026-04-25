"""
Cross-Domain Learning System for AAMIS V3 Extended

Advanced transfer learning system that enables the trading AI to learn from:
- Other traders (human and AI)
- Financial literature and research
- Nature and biological systems
- Physics and dynamical systems
- Other AI domains (games, robotics, NLP)
- Historical patterns across all eras

Implements knowledge transfer, domain adaptation, and analogical reasoning.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
from pathlib import Path
import json
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class KnowledgeDomain(Enum):
    """Domains from which knowledge can be transferred."""
    TRADING_HUMAN = "trading_human"  # Learn from human traders
    TRADING_AI = "trading_ai"  # Learn from other AI systems
    FINANCE_LITERATURE = "finance_literature"  # Academic papers, books
    BIOLOGY = "biology"  # Evolution, adaptation, flocking
    PHYSICS = "physics"  # Statistical mechanics, thermodynamics
    GAMES = "games"  # Chess, Go, poker strategies
    ROBOTICS = "robotics"  # Control theory, path planning
    NLP = "nlp"  # Language models, sentiment
    HISTORY = "history"  # Historical patterns, cycles
    NATURE = "nature"  # Weather, seismic, natural patterns
    NETWORKS = "networks"  # Graph theory, social networks
    COGNITIVE_SCIENCE = "cognitive_science"  # Human decision-making


class TransferMethod(Enum):
    """Methods for knowledge transfer."""
    ANALOGY = "analogy"  # Find structural similarities
    MAPPING = "mapping"  # Direct feature mapping
    ABSTRACTION = "abstraction"  # Extract general principles
    SIMULATION = "simulation"  # Run parallel simulations
    EMBEDDING = "embedding"  # Shared latent space
    META_LEARNING = "meta_learning"  # Learn how to learn


@dataclass
class KnowledgeFragment:
    """A piece of knowledge from any domain."""
    fragment_id: str
    domain: KnowledgeDomain
    content: Dict[str, Any]
    abstraction_level: int  # 0=concrete, 5=highly abstract
    
    # Structural properties for analogy matching
    structure_signature: str  # Hash of structure
    key_concepts: List[str]
    relationships: List[Tuple[str, str, str]]  # (from, to, type)
    
    # Quality metrics
    confidence: float  # 0-1
    generality: float  # How broadly applicable
    novelty: float  # How new/unique
    
    source: str  # Where this knowledge came from
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def structural_similarity(self, other: 'KnowledgeFragment') -> float:
        """Calculate structural similarity with another fragment."""
        # Jaccard similarity of concepts
        concept_overlap = len(set(self.key_concepts) & set(other.key_concepts))
        concept_union = len(set(self.key_concepts) | set(other.key_concepts))
        concept_sim = concept_overlap / concept_union if concept_union > 0 else 0
        
        # Relationship pattern similarity
        if self.relationships and other.relationships:
            self_patterns = set(r[2] for r in self.relationships)  # relationship types
            other_patterns = set(r[2] for r in other.relationships)
            pattern_sim = len(self_patterns & other_patterns) / len(self_patterns | other_patterns)
        else:
            pattern_sim = 0.5
        
        # Abstraction level similarity
        abstraction_sim = 1 - abs(self.abstraction_level - other.abstraction_level) / 5
        
        # Weighted combination
        return 0.4 * concept_sim + 0.4 * pattern_sim + 0.2 * abstraction_sim


@dataclass
class DomainBridge:
    """A bridge connecting two domains."""
    bridge_id: str
    source_domain: KnowledgeDomain
    target_domain: KnowledgeDomain
    
    # Mapping functions
    forward_mapping: Dict[str, str]  # source concept -> target concept
    backward_mapping: Dict[str, str]  # target concept -> source concept
    
    # Transformation function
    transformation: Optional[Callable] = None
    
    # Quality metrics
    mapping_accuracy: float  # 0-1
    coverage: float  # How much of domain is covered
    transfer_success_rate: float  # Historical success
    
    # Examples of successful transfers
    successful_transfers: List[Dict] = field(default_factory=list)
    
    def transfer_forward(self, source_knowledge: KnowledgeFragment) -> Optional[KnowledgeFragment]:
        """Transfer knowledge from source to target domain."""
        # Map concepts
        mapped_concepts = []
        for concept in source_knowledge.key_concepts:
            if concept in self.forward_mapping:
                mapped_concepts.append(self.forward_mapping[concept])
            else:
                mapped_concepts.append(concept)  # Keep original if no mapping
        
        # Create new fragment in target domain
        return KnowledgeFragment(
            fragment_id=f"TRANSFERRED-{uuid.uuid4().hex[:8]}",
            domain=self.target_domain,
            content={
                'translated_from': source_knowledge.fragment_id,
                'original_domain': source_knowledge.domain.value,
                'mapped_concepts': mapped_concepts,
            },
            abstraction_level=source_knowledge.abstraction_level,
            structure_signature=source_knowledge.structure_signature,  # Preserve structure
            key_concepts=mapped_concepts,
            relationships=source_knowledge.relationships,  # Preserve relationships
            confidence=source_knowledge.confidence * self.mapping_accuracy,
            generality=source_knowledge.generality,
            novelty=source_knowledge.novelty,
            source=f"transferred_from_{self.source_domain.value}",
        )


@dataclass
class TransferAttempt:
    """Record of a knowledge transfer attempt."""
    attempt_id: str
    source_fragment: str
    target_domain: KnowledgeDomain
    method: TransferMethod
    
    # Results
    success: bool
    transferred_fragment: Optional[str]
    utility_score: float  # How useful was the transfer
    
    # Evaluation
    validation_results: Dict[str, Any]
    lessons_learned: List[str]
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AnalogicalReasoningEngine:
    """
    Engine for finding and exploiting analogies across domains.
    
    Capabilities:
    - Find structural similarities
    - Map abstract patterns
    - Transfer solutions from analogous problems
    - Validate analogical inferences
    """
    
    def __init__(self):
        self.knowledge_graph: Dict[str, KnowledgeFragment] = {}
        self.analogy_cache: Dict[Tuple[str, str], float] = {}  # (id1, id2) -> similarity
        
    def add_knowledge(self, fragment: KnowledgeFragment):
        """Add knowledge fragment to the system."""
        self.knowledge_graph[fragment.fragment_id] = fragment
        
    def find_analogies(
        self,
        query_fragment: KnowledgeFragment,
        min_similarity: float = 0.6,
        max_results: int = 10,
    ) -> List[Tuple[KnowledgeFragment, float]]:
        """
        Find analogous knowledge fragments.
        
        Args:
            query_fragment: Fragment to find analogies for
            min_similarity: Minimum similarity threshold
            max_results: Maximum number of results
        
        Returns:
            List of (fragment, similarity) tuples
        """
        analogies = []
        
        for fragment_id, fragment in self.knowledge_graph.items():
            if fragment_id == query_fragment.fragment_id:
                continue
            
            # Check cache
            cache_key = tuple(sorted([query_fragment.fragment_id, fragment_id]))
            if cache_key in self.analogy_cache:
                similarity = self.analogy_cache[cache_key]
            else:
                similarity = query_fragment.structural_similarity(fragment)
                self.analogy_cache[cache_key] = similarity
            
            if similarity >= min_similarity:
                analogies.append((fragment, similarity))
        
        # Sort by similarity and return top results
        analogies.sort(key=lambda x: x[1], reverse=True)
        return analogies[:max_results]
    
    def transfer_by_analogy(
        self,
        source_fragment: KnowledgeFragment,
        target_domain: KnowledgeDomain,
    ) -> Optional[KnowledgeFragment]:
        """Transfer knowledge by finding analogies in target domain."""
        # Find the most analogous fragment in target domain
        best_analogy = None
        best_similarity = 0
        
        for fragment_id, fragment in self.knowledge_graph.items():
            if fragment.domain == target_domain:
                similarity = source_fragment.structural_similarity(fragment)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_analogy = fragment
        
        if best_analogy and best_similarity > 0.5:
            # Create bridge based on analogy
            bridge = DomainBridge(
                bridge_id=f"ANALOGY-BRIDGE-{uuid.uuid4().hex[:8]}",
                source_domain=source_fragment.domain,
                target_domain=target_domain,
                forward_mapping=dict(zip(
                    source_fragment.key_concepts,
                    best_analogy.key_concepts
                )),
                backward_mapping=dict(zip(
                    best_analogy.key_concepts,
                    source_fragment.key_concepts
                )),
                mapping_accuracy=best_similarity,
                coverage=0.5,
                transfer_success_rate=0.0,
            )
            
            return bridge.transfer_forward(source_fragment)
        
        return None


class CrossDomainLearningSystem:
    """
    Main system for cross-domain knowledge transfer.
    
    Features:
    - Multi-domain knowledge integration
    - Analogical reasoning
    - Domain bridge management
    - Transfer validation
    - Meta-learning from transfer history
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'cross_domain_learning'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Knowledge stores
        self.knowledge_fragments: Dict[str, KnowledgeFragment] = {}
        self.domain_bridges: Dict[str, DomainBridge] = {}
        self.transfer_history: List[TransferAttempt] = []
        
        # Engines
        self.analogy_engine = AnalogicalReasoningEngine()
        
        # Domain-specific learning modules
        self._domain_learners: Dict[KnowledgeDomain, Callable] = {
            KnowledgeDomain.TRADING_HUMAN: self._learn_from_human_traders,
            KnowledgeDomain.FINANCE_LITERATURE: self._learn_from_literature,
            KnowledgeDomain.BIOLOGY: self._learn_from_biology,
            KnowledgeDomain.PHYSICS: self._learn_from_physics,
            KnowledgeDomain.GAMES: self._learn_from_games,
            KnowledgeDomain.NATURE: self._learn_from_nature,
        }
        
        # Statistics
        self.transfer_stats = defaultdict(lambda: {
            'attempts': 0,
            'successes': 0,
            'total_utility': 0.0,
        })
        
        logger.info("✅ Cross-Domain Learning System initialized")
    
    async def ingest_knowledge(
        self,
        domain: KnowledgeDomain,
        content: Dict[str, Any],
        source: str,
        abstraction_level: int = 2,
    ) -> KnowledgeFragment:
        """
        Ingest new knowledge from any domain.
        
        Args:
            domain: Source domain
            content: Knowledge content
            source: Origin of knowledge
            abstraction_level: Abstraction level (0-5)
        
        Returns:
            Created knowledge fragment
        """
        # Extract structure from content
        concepts = content.get('concepts', [])
        relationships = content.get('relationships', [])
        
        # Create structure signature
        sig_parts = sorted(concepts) + sorted([r[2] for r in relationships])
        structure_sig = str(hash(tuple(sig_parts)))[:16]
        
        fragment = KnowledgeFragment(
            fragment_id=f"KF-{uuid.uuid4().hex[:12]}",
            domain=domain,
            content=content,
            abstraction_level=abstraction_level,
            structure_signature=structure_sig,
            key_concepts=concepts,
            relationships=relationships,
            confidence=content.get('confidence', 0.7),
            generality=content.get('generality', 0.5),
            novelty=content.get('novelty', 0.5),
            source=source,
        )
        
        self.knowledge_fragments[fragment.fragment_id] = fragment
        self.analogy_engine.add_knowledge(fragment)
        
        logger.info(f"📚 Ingested knowledge from {domain.value}: {fragment.fragment_id}")
        
        return fragment
    
    async def transfer_knowledge(
        self,
        source_fragment_id: str,
        target_domain: KnowledgeDomain,
        method: TransferMethod = TransferMethod.ANALOGY,
    ) -> Optional[KnowledgeFragment]:
        """
        Transfer knowledge to a target domain.
        
        Args:
            source_fragment_id: ID of knowledge to transfer
            target_domain: Domain to transfer to
            method: Transfer method
        
        Returns:
            Transferred knowledge fragment or None
        """
        source_fragment = self.knowledge_fragments.get(source_fragment_id)
        if not source_fragment:
            logger.warning(f"Source fragment not found: {source_fragment_id}")
            return None
        
        # Check for existing bridge
        existing_bridge = self._find_bridge(source_fragment.domain, target_domain)
        
        transferred = None
        
        if method == TransferMethod.ANALOGY:
            if existing_bridge:
                transferred = existing_bridge.transfer_forward(source_fragment)
            else:
                transferred = self.analogy_engine.transfer_by_analogy(
                    source_fragment, target_domain
                )
        
        elif method == TransferMethod.MAPPING:
            if existing_bridge:
                transferred = existing_bridge.transfer_forward(source_fragment)
        
        elif method == TransferMethod.ABSTRACTION:
            transferred = self._transfer_by_abstraction(source_fragment, target_domain)
        
        elif method == TransferMethod.SIMULATION:
            transferred = await self._transfer_by_simulation(source_fragment, target_domain)
        
        elif method == TransferMethod.META_LEARNING:
            transferred = await self._transfer_by_meta_learning(source_fragment, target_domain)
        
        # Record transfer attempt
        attempt = TransferAttempt(
            attempt_id=f"TA-{uuid.uuid4().hex[:12]}",
            source_fragment=source_fragment_id,
            target_domain=target_domain,
            method=method,
            success=transferred is not None,
            transferred_fragment=transferred.fragment_id if transferred else None,
            utility_score=0.0,  # To be evaluated
            validation_results={},
            lessons_learned=[],
        )
        
        self.transfer_history.append(attempt)
        
        # Update stats
        key = (source_fragment.domain, target_domain)
        self.transfer_stats[key]['attempts'] += 1
        if transferred:
            self.transfer_stats[key]['successes'] += 1
        
        if transferred:
            logger.info(f"🔄 Transferred {source_fragment_id} to {target_domain.value}: "
                       f"{transferred.fragment_id}")
        else:
            logger.warning(f"❌ Failed to transfer {source_fragment_id} to {target_domain.value}")
        
        return transferred
    
    async def learn_from_domain(
        self,
        domain: KnowledgeDomain,
        **kwargs
    ) -> List[KnowledgeFragment]:
        """
        Learn from a specific domain.
        
        Args:
            domain: Domain to learn from
            **kwargs: Domain-specific parameters
        
        Returns:
            List of created knowledge fragments
        """
        learner = self._domain_learners.get(domain)
        if not learner:
            logger.warning(f"No learner available for {domain.value}")
            return []
        
        return await learner(**kwargs)
    
    async def _learn_from_human_traders(self, **kwargs) -> List[KnowledgeFragment]:
        """Learn from human trader behavior patterns."""
        fragments = []
        
        # Extract patterns from provided trader data
        trader_data = kwargs.get('trader_data', [])
        
        for trader in trader_data:
            # Analyze trading patterns
            pattern = {
                'concepts': ['entry_timing', 'exit_strategy', 'risk_management'],
                'relationships': [
                    ('market_condition', 'entry_timing', 'influences'),
                    ('position_size', 'risk_management', 'determined_by'),
                ],
                'pattern_type': trader.get('style', 'unknown'),
                'success_rate': trader.get('win_rate', 0.5),
                'confidence': 0.6,
                'generality': 0.4,
                'novelty': 0.3,
            }
            
            fragment = await self.ingest_knowledge(
                domain=KnowledgeDomain.TRADING_HUMAN,
                content=pattern,
                source=f"trader_{trader.get('id', 'unknown')}",
                abstraction_level=2,
            )
            fragments.append(fragment)
        
        logger.info(f"👤 Learned from {len(fragments)} human traders")
        return fragments
    
    async def _learn_from_literature(self, **kwargs) -> List[KnowledgeFragment]:
        """Learn from financial literature."""
        fragments = []
        
        papers = kwargs.get('papers', [])
        for paper in papers:
            # Extract key insights
            insight = {
                'concepts': paper.get('key_terms', []),
                'relationships': paper.get('relationships', []),
                'findings': paper.get('conclusions', []),
                'methodology': paper.get('method', 'unknown'),
                'confidence': paper.get('statistical_significance', 0.7),
                'generality': 0.6,
                'novelty': 0.7,
            }
            
            fragment = await self.ingest_knowledge(
                domain=KnowledgeDomain.FINANCE_LITERATURE,
                content=insight,
                source=paper.get('title', 'unknown'),
                abstraction_level=3,
            )
            fragments.append(fragment)
        
        logger.info(f"📖 Learned from {len(fragments)} papers")
        return fragments
    
    async def _learn_from_biology(self, **kwargs) -> List[KnowledgeFragment]:
        """Learn from biological systems."""
        fragments = []
        
        # Examples of biological patterns applicable to trading
        biological_patterns = [
            {
                'name': 'evolutionary_adaptation',
                'concepts': ['population', 'selection', 'mutation', 'fitness'],
                'relationships': [
                    ('mutation', 'population', 'diversifies'),
                    ('selection', 'fitness', 'optimizes_for'),
                ],
                'trading_analogy': 'strategy_evolution',
                'confidence': 0.8,
                'generality': 0.7,
                'novelty': 0.6,
            },
            {
                'name': 'flocking_behavior',
                'concepts': ['alignment', 'separation', 'cohesion', 'emergence'],
                'relationships': [
                    ('alignment', 'cohesion', 'balances_with'),
                    ('local_rules', 'emergence', 'produces'),
                ],
                'trading_analogy': 'market_participant_behavior',
                'confidence': 0.7,
                'generality': 0.6,
                'novelty': 0.5,
            },
            {
                'name': 'immune_system',
                'concepts': ['recognition', 'response', 'memory', 'adaptation'],
                'relationships': [
                    ('recognition', 'response', 'triggers'),
                    ('exposure', 'memory', 'creates'),
                ],
                'trading_analogy': 'risk_detection_response',
                'confidence': 0.75,
                'generality': 0.65,
                'novelty': 0.7,
            },
        ]
        
        for pattern in biological_patterns:
            content = {
                'concepts': pattern['concepts'],
                'relationships': pattern['relationships'],
                'biological_pattern': pattern['name'],
                'trading_analogy': pattern['trading_analogy'],
                'confidence': pattern['confidence'],
                'generality': pattern['generality'],
                'novelty': pattern['novelty'],
            }
            
            fragment = await self.ingest_knowledge(
                domain=KnowledgeDomain.BIOLOGY,
                content=content,
                source=f"biology_{pattern['name']}",
                abstraction_level=3,
            )
            fragments.append(fragment)
        
        logger.info(f"🧬 Learned {len(fragments)} biological patterns")
        return fragments
    
    async def _learn_from_physics(self, **kwargs) -> List[KnowledgeFragment]:
        """Learn from physical systems."""
        fragments = []
        
        physics_concepts = [
            {
                'name': 'thermodynamics',
                'concepts': ['entropy', 'equilibrium', 'energy', 'dissipation'],
                'trading_analogy': 'market_efficiency_and_volatility',
                'confidence': 0.8,
            },
            {
                'name': 'phase_transitions',
                'concepts': ['critical_point', 'order_parameter', 'symmetry_breaking'],
                'trading_analogy': 'market_regime_changes',
                'confidence': 0.75,
            },
            {
                'name': 'oscillations',
                'concepts': ['frequency', 'amplitude', 'damping', 'resonance'],
                'trading_analogy': 'cyclical_market_patterns',
                'confidence': 0.7,
            },
        ]
        
        for concept in physics_concepts:
            content = {
                'concepts': concept['concepts'],
                'relationships': [],
                'physics_concept': concept['name'],
                'trading_analogy': concept['trading_analogy'],
                'confidence': concept['confidence'],
                'generality': 0.6,
                'novelty': 0.5,
            }
            
            fragment = await self.ingest_knowledge(
                domain=KnowledgeDomain.PHYSICS,
                content=content,
                source=f"physics_{concept['name']}",
                abstraction_level=3,
            )
            fragments.append(fragment)
        
        logger.info(f"⚛️ Learned {len(fragments)} physics concepts")
        return fragments
    
    async def _learn_from_games(self, **kwargs) -> List[KnowledgeFragment]:
        """Learn from game theory and strategies."""
        fragments = []
        
        game_strategies = [
            {
                'game': 'chess',
                'concepts': ['position_evaluation', 'tree_search', 'opening_theory', 'endgame'],
                'trading_analogy': 'market_position_analysis',
            },
            {
                'game': 'poker',
                'concepts': ['bluffing', 'pot_odds', 'position', 'read_opponent'],
                'trading_analogy': 'information_asymmetry_trading',
            },
            {
                'game': 'go',
                'concepts': ['territory', 'influence', 'life_and_death', 'pattern_recognition'],
                'trading_analogy': 'market_structure_analysis',
            },
        ]
        
        for game in game_strategies:
            content = {
                'concepts': game['concepts'],
                'relationships': [],
                'game': game['game'],
                'trading_analogy': game['trading_analogy'],
                'confidence': 0.75,
                'generality': 0.5,
                'novelty': 0.4,
            }
            
            fragment = await self.ingest_knowledge(
                domain=KnowledgeDomain.GAMES,
                content=content,
                source=f"game_{game['game']}",
                abstraction_level=2,
            )
            fragments.append(fragment)
        
        logger.info(f"🎮 Learned {len(fragments)} game strategies")
        return fragments
    
    async def _learn_from_nature(self, **kwargs) -> List[KnowledgeFragment]:
        """Learn from natural patterns."""
        fragments = []
        
        natural_patterns = [
            {
                'pattern': 'fractals',
                'concepts': ['self_similarity', 'scale_invariance', 'recursion'],
                'trading_analogy': 'multi_timeframe_patterns',
            },
            {
                'pattern': 'waves',
                'concepts': ['superposition', 'interference', 'frequency', 'amplitude'],
                'trading_analogy': 'market_wave_analysis',
            },
            {
                'pattern': 'networks',
                'concepts': ['nodes', 'edges', 'centrality', 'cascades'],
                'trading_analogy': 'market_network_effects',
            },
        ]
        
        for pattern in natural_patterns:
            content = {
                'concepts': pattern['concepts'],
                'relationships': [],
                'natural_pattern': pattern['pattern'],
                'trading_analogy': pattern['trading_analogy'],
                'confidence': 0.7,
                'generality': 0.6,
                'novelty': 0.5,
            }
            
            fragment = await self.ingest_knowledge(
                domain=KnowledgeDomain.NATURE,
                content=content,
                source=f"nature_{pattern['pattern']}",
                abstraction_level=3,
            )
            fragments.append(fragment)
        
        logger.info(f"🌿 Learned {len(fragments)} natural patterns")
        return fragments
    
    def _find_bridge(
        self,
        source: KnowledgeDomain,
        target: KnowledgeDomain
    ) -> Optional[DomainBridge]:
        """Find existing bridge between domains."""
        for bridge in self.domain_bridges.values():
            if bridge.source_domain == source and bridge.target_domain == target:
                return bridge
        return None
    
    def _transfer_by_abstraction(
        self,
        source: KnowledgeFragment,
        target_domain: KnowledgeDomain
    ) -> Optional[KnowledgeFragment]:
        """Transfer by extracting and applying abstract principles."""
        if source.abstraction_level < 2:
            # Too concrete to abstract
            return None
        
        # Extract abstract principles
        abstract_content = {
            'principles': source.key_concepts,
            'original_domain': source.domain.value,
            'abstraction_level': source.abstraction_level + 1,
            'confidence': source.confidence * 0.9,  # Slight confidence reduction
            'generality': min(1.0, source.generality + 0.1),
            'novelty': source.novelty,
        }
        
        return KnowledgeFragment(
            fragment_id=f"ABSTRACT-{uuid.uuid4().hex[:12]}",
            domain=target_domain,
            content=abstract_content,
            abstraction_level=source.abstraction_level + 1,
            structure_signature=source.structure_signature,
            key_concepts=source.key_concepts,
            relationships=source.relationships,
            confidence=source.confidence * 0.9,
            generality=min(1.0, source.generality + 0.1),
            novelty=source.novelty,
            source=f"abstracted_from_{source.fragment_id}",
        )
    
    async def _transfer_by_simulation(
        self,
        source: KnowledgeFragment,
        target_domain: KnowledgeDomain
    ) -> Optional[KnowledgeFragment]:
        """Transfer by running parallel simulations."""
        # Run simulations in both domains
        # Compare outcomes
        # If similar, transfer is valid
        
        # Simplified: assume success for demonstration
        return self._transfer_by_abstraction(source, target_domain)
    
    async def _transfer_by_meta_learning(
        self,
        source: KnowledgeFragment,
        target_domain: KnowledgeDomain
    ) -> Optional[KnowledgeFragment]:
        """Use meta-learning from transfer history."""
        # Analyze past successful transfers between these domains
        key = (source.domain, target_domain)
        stats = self.transfer_stats[key]
        
        if stats['attempts'] == 0:
            return None
        
        success_rate = stats['successes'] / stats['attempts']
        
        if success_rate < 0.3:
            # Low historical success, be cautious
            return None
        
        # Higher confidence if past transfers were successful
        adjusted_confidence = source.confidence * (0.5 + 0.5 * success_rate)
        
        return KnowledgeFragment(
            fragment_id=f"META-{uuid.uuid4().hex[:12]}",
            domain=target_domain,
            content={
                'transferred_using': 'meta_learning',
                'historical_success_rate': success_rate,
                'original_content': source.content,
            },
            abstraction_level=source.abstraction_level,
            structure_signature=source.structure_signature,
            key_concepts=source.key_concepts,
            relationships=source.relationships,
            confidence=adjusted_confidence,
            generality=source.generality,
            novelty=source.novelty,
            source=f"meta_transferred_from_{source.fragment_id}",
        )
    
    async def find_cross_domain_insights(
        self,
        trading_problem: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find insights from other domains applicable to a trading problem.
        
        Args:
            trading_problem: Description of trading problem
            top_k: Number of insights to return
        
        Returns:
            List of applicable insights with relevance scores
        """
        # Create query fragment
        query = KnowledgeFragment(
            fragment_id="QUERY",
            domain=KnowledgeDomain.TRADING_AI,
            content={'problem': trading_problem, 'concepts': trading_problem.split()},
            abstraction_level=2,
            structure_signature="",
            key_concepts=trading_problem.lower().split(),
            relationships=[],
            confidence=1.0,
            generality=0.5,
            novelty=0.5,
            source="query",
        )
        
        # Find analogies in other domains
        analogies = self.analogy_engine.find_analogies(query, min_similarity=0.4, max_results=20)
        
        # Filter to non-trading domains
        cross_domain = [
            {'fragment': frag, 'similarity': sim, 'source_domain': frag.domain.value}
            for frag, sim in analogies
            if frag.domain not in [KnowledgeDomain.TRADING_AI, KnowledgeDomain.TRADING_HUMAN]
        ]
        
        # Sort by similarity and take top_k
        cross_domain.sort(key=lambda x: x['similarity'], reverse=True)
        
        return cross_domain[:top_k]
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about learning activities."""
        by_domain = defaultdict(int)
        for frag in self.knowledge_fragments.values():
            by_domain[frag.domain.value] += 1
        
        return {
            'total_fragments': len(self.knowledge_fragments),
            'by_domain': dict(by_domain),
            'total_transfers': len(self.transfer_history),
            'successful_transfers': sum(1 for t in self.transfer_history if t.success),
            'transfer_success_rate': (
                sum(1 for t in self.transfer_history if t.success) / len(self.transfer_history)
                if self.transfer_history else 0
            ),
            'domain_pairs_tested': len(self.transfer_stats),
        }


# Example usage
async def example_cross_domain_learning():
    """Example of cross-domain learning."""
    system = CrossDomainLearningSystem()
    
    # Learn from biology
    bio_fragments = await system.learn_from_domain(KnowledgeDomain.BIOLOGY)
    print(f"Learned {len(bio_fragments)} biological patterns")
    
    # Learn from physics
    physics_fragments = await system.learn_from_domain(KnowledgeDomain.PHYSICS)
    print(f"Learned {len(physics_fragments)} physics concepts")
    
    # Transfer evolutionary adaptation to trading
    if bio_fragments:
        transferred = await system.transfer_knowledge(
            bio_fragments[0].fragment_id,
            KnowledgeDomain.TRADING_AI,
            TransferMethod.ANALOGY,
        )
        if transferred:
            print(f"\nTransferred to trading: {transferred.fragment_id}")
            print(f"Concepts: {transferred.key_concepts}")
    
    # Find insights for a specific problem
    insights = await system.find_cross_domain_insights(
        "portfolio diversification under uncertainty",
        top_k=3,
    )
    print("\nCross-domain insights:")
    for insight in insights:
        print(f"  - From {insight['source_domain']}: similarity={insight['similarity']:.2f}")
    
    # Statistics
    stats = system.get_learning_statistics()
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    asyncio.run(example_cross_domain_learning())
