"""
Semantic Knowledge Cognition Store
===================================

Embedding-indexed semantic knowledge base for the decision governance system.
Stores learned strategies, patterns, insights, and failures with semantic
search capabilities.

Features:
- Vector embedding-based semantic search
- Multi-modal knowledge storage (text, structured, metric)
- Dynamic knowledge graph construction
- Cross-domain similarity matching
- Temporal knowledge decay and refresh
- Importance-weighted retrieval

Based on cognition store patterns from ASI-Evolve research.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from collections import defaultdict
import heapq

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge entries"""
    STRATEGY = "strategy"
    PATTERN = "pattern"
    INSIGHT = "insight"
    FAILURE = "failure"
    SUCCESS = "success"
    MARKET_REGIME = "market_regime"
    RISK_FACTOR = "risk_factor"
    CORRELATION = "correlation"
    CAUSAL_LINK = "causal_link"
    HYPOTHESIS = "hypothesis"


class KnowledgeSource(Enum):
    """Source of knowledge"""
    EXPERIMENT = "experiment"
    DEBATE = "debate"
    ANALYSIS = "analysis"
    HUMAN = "human"
    EXTERNAL = "external"
    INFERENCE = "inference"
    SIMULATION = "simulation"


@dataclass
class KnowledgeEmbedding:
    """Vector embedding for knowledge entry"""
    vector: List[float]
    model_version: str = "default"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def dimension(self) -> int:
        return len(self.vector)
    
    def cosine_similarity(self, other: 'KnowledgeEmbedding') -> float:
        """Compute cosine similarity with another embedding"""
        if len(self.vector) != len(other.vector):
            # Pad or truncate to match
            min_len = min(len(self.vector), len(other.vector))
            v1 = self.vector[:min_len]
            v2 = other.vector[:min_len]
        else:
            v1 = self.vector
            v2 = other.vector
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = sum(a * a for a in v1) ** 0.5
        magnitude2 = sum(b * b for b in v2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


@dataclass
class KnowledgeMetadata:
    """Metadata for knowledge entry"""
    creator: str
    source: KnowledgeSource
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)
    confidence: float = 0.5
    importance: float = 0.5


@dataclass
class KnowledgeEntry:
    """Single knowledge entry in the cognition store"""
    id: str
    content: str
    knowledge_type: KnowledgeType
    embedding: KnowledgeEmbedding
    metadata: KnowledgeMetadata
    
    # Temporal tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    
    # Validation
    validation_status: str = "pending"  # pending, validated, invalidated
    validation_evidence: List[str] = field(default_factory=list)
    
    # Decay
    decay_rate: float = 0.01  # Daily decay rate
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    @property
    def current_value(self) -> float:
        """Current value considering decay"""
        days_since_creation = (datetime.utcnow() - self.created_at).days
        age_penalty = 1 - (days_since_creation * self.decay_rate)
        
        access_bonus = min(0.3, self.access_count * 0.01)
        
        importance = self.metadata.importance
        confidence = self.metadata.confidence
        
        return max(0, age_penalty) * (0.4 * importance + 0.4 * confidence + 0.2 * (1 + access_bonus))
    
    def record_access(self):
        """Record an access to this entry"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def compute_hash(self) -> str:
        """Compute hash for deduplication"""
        content = f"{self.content}:{self.knowledge_type.value}:{self.created_at.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class KnowledgeGraph:
    """Graph structure linking knowledge entries"""
    nodes: Dict[str, KnowledgeEntry] = field(default_factory=dict)
    edges: Dict[str, List[Tuple[str, float, str]]] = field(default_factory=lambda: defaultdict(list))
    # edges: source_id -> [(target_id, weight, relationship_type)]
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        weight: float,
        relationship: str = "related"
    ):
        """Add an edge between knowledge entries"""
        self.edges[source_id].append((target_id, weight, relationship))
    
    def get_related(
        self,
        entry_id: str,
        min_weight: float = 0.5,
        relationship_type: Optional[str] = None
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Get related entries"""
        related = []
        
        for target_id, weight, rel_type in self.edges.get(entry_id, []):
            if weight >= min_weight:
                if relationship_type is None or rel_type == relationship_type:
                    entry = self.nodes.get(target_id)
                    if entry:
                        related.append((entry, weight))
        
        related.sort(key=lambda x: x[1], reverse=True)
        return related
    
    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3
    ) -> List[List[str]]:
        """Find paths between two entries"""
        paths = []
        visited = {source_id}
        
        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            if current == target_id:
                paths.append(path.copy())
                return
            
            for next_id, weight, _ in self.edges.get(current, []):
                if next_id not in visited and weight > 0.3:
                    visited.add(next_id)
                    path.append(next_id)
                    dfs(next_id, path, depth + 1)
                    path.pop()
                    visited.remove(next_id)
        
        dfs(source_id, [source_id], 0)
        return paths


class CognitionStore:
    """
    Semantic Knowledge Cognition Store
    
    Central repository for domain knowledge with semantic search,
    knowledge graph construction, and importance-weighted retrieval.
    """
    
    def __init__(
        self,
        embedding_dimension: int = 128,
        default_decay_rate: float = 0.01,
        max_entries: int = 10000
    ):
        self.embedding_dim = embedding_dimension
        self.default_decay_rate = default_decay_rate
        self.max_entries = max_entries
        
        # Storage
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.hash_index: Dict[str, str] = {}  # hash -> entry_id
        self.type_index: Dict[KnowledgeType, Set[str]] = defaultdict(set)
        self.source_index: Dict[KnowledgeSource, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Knowledge graph
        self.graph = KnowledgeGraph()
        
        # Cache for embeddings (speeds up similarity search)
        self._embedding_cache: Dict[str, KnowledgeEmbedding] = {}
        
        # Statistics
        self.stats = {
            'entries_added': 0,
            'entries_removed': 0,
            'searches_performed': 0,
            'cache_hits': 0
        }
        
        # Initialize with domain knowledge
        self._initialize_domain_knowledge()
    
    def _initialize_domain_knowledge(self):
        """Seed with initial trading domain knowledge"""
        initial_knowledge = [
            {
                'content': 'Trend-following strategies exhibit superior risk-adjusted returns during high-volatility trending regimes',
                'type': KnowledgeType.STRATEGY,
                'importance': 0.9,
                'tags': ['trend', 'volatility', 'regime', 'momentum'],
                'context': {'market_condition': 'trending', 'volatility': 'high'}
            },
            {
                'content': 'Mean reversion strategies perform optimally in low-volatility, range-bound market conditions',
                'type': KnowledgeType.STRATEGY,
                'importance': 0.85,
                'tags': ['mean_reversion', 'volatility', 'range_bound'],
                'context': {'market_condition': 'ranging', 'volatility': 'low'}
            },
            {
                'content': 'Drawdown exceeding 10% significantly impairs compound growth and psychological decision-making',
                'type': KnowledgeType.INSIGHT,
                'importance': 0.95,
                'tags': ['risk', 'drawdown', 'psychology', 'compounding'],
                'context': {'risk_threshold': 0.10}
            },
            {
                'content': 'High-frequency trading strategies require transaction cost optimization below 0.1% per trade',
                'type': KnowledgeType.INSIGHT,
                'importance': 0.8,
                'tags': ['hft', 'costs', 'execution', 'microstructure'],
                'context': {'strategy_type': 'hft', 'cost_threshold': 0.001}
            },
            {
                'content': 'Breakout patterns with volume confirmation succeed 3x more frequently than those without',
                'type': KnowledgeType.PATTERN,
                'importance': 0.85,
                'tags': ['breakout', 'volume', 'confirmation', 'technical'],
                'context': {'pattern_type': 'breakout', 'confirmation': 'volume'}
            },
            {
                'content': 'Risk of ruin approaches certainty when risk-per-trade exceeds 2% of capital',
                'type': KnowledgeType.RISK_FACTOR,
                'importance': 0.95,
                'tags': ['risk', 'ruin', 'position_sizing', 'survival'],
                'context': {'risk_per_trade': 0.02, 'severity': 'critical'}
            },
            {
                'content': 'Portfolio diversification benefits diminish beyond 10-15 uncorrelated strategies',
                'type': KnowledgeType.INSIGHT,
                'importance': 0.75,
                'tags': ['diversification', 'correlation', 'portfolio', 'allocation'],
                'context': {'optimal_count': 12, 'concept': 'diversification'}
            },
            {
                'content': 'Market regime transitions often preceded by correlation breakdown among normally correlated assets',
                'type': KnowledgeType.PATTERN,
                'importance': 0.8,
                'tags': ['regime_change', 'correlation', 'early_warning', 'transition'],
                'context': {'signal_type': 'regime_change', 'indicator': 'correlation_breakdown'}
            },
            {
                'content': 'Stop-losses placed at technical support levels have higher probability of execution without excessive slippage',
                'type': KnowledgeType.STRATEGY,
                'importance': 0.8,
                'tags': ['stop_loss', 'execution', 'technical', 'risk_management'],
                'context': {'technique': 'stop_placement', 'factor': 'support_levels'}
            },
            {
                'content': 'Behavioral bias toward action leads to overtrading; systematic rules outperform discretionary decisions',
                'type': KnowledgeType.INSIGHT,
                'importance': 0.85,
                'tags': ['behavioral', 'bias', 'systematic', 'discipline'],
                'context': {'bias_type': 'action_bias', 'solution': 'systematic_rules'}
            }
        ]
        
        for i, knowledge in enumerate(initial_knowledge):
            # Create simple embedding (would use real embeddings in production)
            embedding_vector = self._create_embedding(knowledge['content'])
            
            entry = KnowledgeEntry(
                id=f"domain_knowledge_{i}",
                content=knowledge['content'],
                knowledge_type=knowledge['type'],
                embedding=KnowledgeEmbedding(vector=embedding_vector),
                metadata=KnowledgeMetadata(
                    creator="system",
                    source=KnowledgeSource.INFERENCE,
                    tags=knowledge.get('tags', []),
                    confidence=0.8,
                    importance=knowledge.get('importance', 0.5),
                    context=knowledge.get('context', {})
                ),
                decay_rate=0.005  # Slower decay for domain knowledge
            )
            
            self.add_entry(entry)
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create simple hash-based embedding (replace with transformer embeddings in production)"""
        # Character n-gram based embedding
        embedding = [0.0] * self.embedding_dim
        
        # Use character codes to populate embedding
        for i, char in enumerate(text.lower()):
            idx = i % self.embedding_dim
            embedding[idx] += ord(char) / 255.0
        
        # Add word-level features
        words = text.lower().split()
        for i, word in enumerate(words):
            idx = (i * 7) % self.embedding_dim  # Use prime for distribution
            embedding[idx] += hash(word) % 100 / 100.0
        
        # Normalize
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def add_entry(self, entry: KnowledgeEntry) -> bool:
        """
        Add entry to cognition store.
        
        Returns True if added, False if duplicate.
        """
        # Check for duplicates
        entry_hash = entry.compute_hash()
        if entry_hash in self.hash_index:
            logger.debug(f"Duplicate entry detected: {entry.content[:50]}...")
            return False
        
        # Check capacity
        if len(self.entries) >= self.max_entries:
            self._evict_least_valuable()
        
        # Store entry
        self.entries[entry.id] = entry
        self.hash_index[entry_hash] = entry.id
        self._embedding_cache[entry.id] = entry.embedding
        
        # Update indexes
        self.type_index[entry.knowledge_type].add(entry.id)
        self.source_index[entry.metadata.source].add(entry.id)
        for tag in entry.metadata.tags:
            self.tag_index[tag].add(entry.id)
        
        # Update graph
        self.graph.nodes[entry.id] = entry
        
        # Find and add semantic relationships
        self._update_graph_relationships(entry)
        
        self.stats['entries_added'] += 1
        
        logger.debug(f"Added knowledge entry {entry.id}: {entry.content[:50]}...")
        
        return True
    
    def _evict_least_valuable(self):
        """Remove least valuable entries when at capacity"""
        if not self.entries:
            return
        
        # Find entry with lowest current value
        least_valuable = min(
            self.entries.values(),
            key=lambda e: e.current_value
        )
        
        self.remove_entry(least_valuable.id)
        self.stats['entries_removed'] += 1
    
    def _update_graph_relationships(self, new_entry: KnowledgeEntry):
        """Update knowledge graph with relationships for new entry"""
        # Find semantically similar entries
        similar = self.search(
            query_embedding=new_entry.embedding,
            k=5,
            min_similarity=0.7
        )
        
        for similar_entry, similarity in similar:
            if similar_entry.id != new_entry.id:
                # Determine relationship type
                relationship = self._infer_relationship(new_entry, similar_entry)
                
                # Add bidirectional edges
                self.graph.add_edge(
                    new_entry.id,
                    similar_entry.id,
                    similarity,
                    relationship
                )
                self.graph.add_edge(
                    similar_entry.id,
                    new_entry.id,
                    similarity,
                    relationship
                )
    
    def _infer_relationship(
        self,
        entry1: KnowledgeEntry,
        entry2: KnowledgeEntry
    ) -> str:
        """Infer relationship type between two entries"""
        # Check type relationships
        if entry1.knowledge_type == entry2.knowledge_type:
            return f"same_{entry1.knowledge_type.value}"
        
        # Check tag overlap
        tags1 = set(entry1.metadata.tags)
        tags2 = set(entry2.metadata.tags)
        overlap = tags1 & tags2
        
        if overlap:
            return f"shared_{list(overlap)[0]}"
        
        # Check temporal relationship
        time_diff = abs((entry1.created_at - entry2.created_at).total_seconds())
        if time_diff < 3600:  # Within 1 hour
            return "temporal_proximity"
        
        return "semantic_similarity"
    
    def remove_entry(self, entry_id: str) -> bool:
        """Remove entry from store"""
        if entry_id not in self.entries:
            return False
        
        entry = self.entries[entry_id]
        
        # Remove from indexes
        del self.entries[entry_id]
        del self.hash_index[entry.compute_hash()]
        del self._embedding_cache[entry_id]
        
        self.type_index[entry.knowledge_type].discard(entry_id)
        self.source_index[entry.metadata.source].discard(entry_id)
        for tag in entry.metadata.tags:
            self.tag_index[tag].discard(entry_id)
        
        # Remove from graph
        del self.graph.nodes[entry_id]
        if entry_id in self.graph.edges:
            del self.graph.edges[entry_id]
        
        return True
    
    def search(
        self,
        query: Optional[str] = None,
        query_embedding: Optional[KnowledgeEmbedding] = None,
        k: int = 5,
        knowledge_type: Optional[KnowledgeType] = None,
        min_similarity: float = 0.5,
        min_importance: float = 0.0,
        tags: Optional[List[str]] = None
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Semantic search for knowledge entries.
        
        Returns list of (entry, similarity_score) tuples.
        """
        self.stats['searches_performed'] += 1
        
        # Create embedding from query if not provided
        if query_embedding is None:
            if query is None:
                return []
            query_embedding = KnowledgeEmbedding(
                vector=self._create_embedding(query)
            )
        
        # Get candidate set
        if knowledge_type:
            candidates = [self.entries[eid] for eid in self.type_index[knowledge_type]]
        elif tags:
            candidate_ids = set()
            for tag in tags:
                candidate_ids.update(self.tag_index[tag])
            candidates = [self.entries[eid] for eid in candidate_ids if eid in self.entries]
        else:
            candidates = list(self.entries.values())
        
        # Score candidates
        scored = []
        for entry in candidates:
            # Skip if below importance threshold
            if entry.metadata.importance < min_importance:
                continue
            
            # Compute similarity
            similarity = query_embedding.cosine_similarity(entry.embedding)
            
            # Apply importance weighting
            weighted_score = similarity * (0.7 + 0.3 * entry.metadata.importance)
            
            # Apply current value weighting (includes decay)
            weighted_score *= (0.5 + 0.5 * entry.current_value)
            
            if weighted_score >= min_similarity:
                scored.append((entry, weighted_score))
        
        # Sort by score and return top k
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Record access for returned entries
        for entry, _ in scored[:k]:
            entry.record_access()
        
        return scored[:k]
    
    def get_related_knowledge(
        self,
        entry_id: str,
        relationship_type: Optional[str] = None,
        k: int = 5
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Get knowledge related to specific entry"""
        return self.graph.get_related(entry_id, relationship_type=relationship_type)[:k]
    
    def find_knowledge_path(
        self,
        start_concept: str,
        end_concept: str,
        max_depth: int = 3
    ) -> Optional[List[KnowledgeEntry]]:
        """
        Find knowledge path connecting two concepts.
        
        Useful for explaining reasoning chains.
        """
        # Find entries matching concepts
        start_entries = self.search(start_concept, k=3)
        end_entries = self.search(end_concept, k=3)
        
        if not start_entries or not end_entries:
            return None
        
        start_id = start_entries[0][0].id
        end_id = end_entries[0][0].id
        
        # Find paths in graph
        paths = self.graph.find_paths(start_id, end_id, max_depth)
        
        if not paths:
            return None
        
        # Return shortest path
        shortest = min(paths, key=len)
        return [self.entries[eid] for eid in shortest if eid in self.entries]
    
    def get_knowledge_summary(
        self,
        knowledge_type: Optional[KnowledgeType] = None
    ) -> Dict[str, Any]:
        """Get summary of stored knowledge"""
        entries_to_summarize = [
            e for e in self.entries.values()
            if knowledge_type is None or e.knowledge_type == knowledge_type
        ]
        
        by_type = defaultdict(list)
        for entry in entries_to_summarize:
            by_type[entry.knowledge_type.value].append(entry)
        
        return {
            'total_entries': len(entries_to_summarize),
            'by_type': {
                k: {
                    'count': len(v),
                    'avg_importance': sum(e.metadata.importance for e in v) / len(v) if v else 0,
                    'avg_confidence': sum(e.metadata.confidence for e in v) / len(v) if v else 0
                }
                for k, v in by_type.items()
            },
            'total_graph_edges': sum(len(edges) for edges in self.graph.edges.values()),
            'most_accessed': [
                {'id': e.id, 'content': e.content[:50], 'access_count': e.access_count}
                for e in sorted(entries_to_summarize, key=lambda x: x.access_count, reverse=True)[:3]
            ],
            'recent_additions': [
                {'id': e.id, 'content': e.content[:50], 'created': e.created_at.isoformat()}
                for e in sorted(entries_to_summarize, key=lambda x: x.created_at, reverse=True)[:3]
            ]
        }
    
    def consolidate_knowledge(self):
        """Consolidate similar knowledge entries"""
        # Find highly similar entries
        to_merge = []
        checked = set()
        
        for entry1 in self.entries.values():
            if entry1.id in checked:
                continue
            
            similar_group = [entry1]
            
            for entry2 in self.entries.values():
                if entry2.id == entry1.id or entry2.id in checked:
                    continue
                
                similarity = entry1.embedding.cosine_similarity(entry2.embedding)
                if similarity > 0.9:  # Very similar
                    similar_group.append(entry2)
            
            if len(similar_group) > 1:
                to_merge.append(similar_group)
                checked.update(e.id for e in similar_group)
        
        # Merge groups
        for group in to_merge:
            self._merge_entries(group)
    
    def _merge_entries(self, entries: List[KnowledgeEntry]):
        """Merge multiple similar entries into one"""
        if len(entries) <= 1:
            return
        
        # Keep the most valuable one
        primary = max(entries, key=lambda e: e.current_value)
        
        # Merge metadata from others
        for entry in entries:
            if entry.id != primary.id:
                primary.metadata.tags.extend(entry.metadata.tags)
                primary.metadata.related_entries.extend(entry.metadata.related_entries)
                primary.validation_evidence.extend(entry.validation_evidence)
                
                # Remove merged entry
                self.remove_entry(entry.id)
        
        # Deduplicate
        primary.metadata.tags = list(set(primary.metadata.tags))
        primary.metadata.related_entries = list(set(primary.metadata.related_entries))
        
        # Boost importance
        primary.metadata.importance = min(1.0, primary.metadata.importance + 0.1)
        
        logger.info(f"Merged {len(entries)} entries into {primary.id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics"""
        return {
            **self.stats,
            'current_entries': len(self.entries),
            'cache_size': len(self._embedding_cache),
            'graph_nodes': len(self.graph.nodes),
            'graph_edges': sum(len(e) for e in self.graph.edges.values()),
            'types': {k.value: len(v) for k, v in self.type_index.items()},
            'sources': {k.value: len(v) for k, v in self.source_index.items()}
        }


def create_cognition_store(
    embedding_dim: int = 128,
    max_entries: int = 10000
) -> CognitionStore:
    """Factory function to create cognition store"""
    return CognitionStore(
        embedding_dimension=embedding_dim,
        max_entries=max_entries
    )
