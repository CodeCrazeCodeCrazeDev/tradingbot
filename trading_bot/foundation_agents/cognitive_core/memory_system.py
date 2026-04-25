"""
Memory System - Brain-Inspired Memory Architecture
===================================================

Implements three types of memory inspired by cognitive neuroscience:
1. Episodic Memory: Specific trading events and experiences
2. Semantic Memory: General market knowledge and concepts
3. Procedural Memory: Trading rules and strategies

Based on the Foundation Agents paper (arXiv:2504.01990) memory architecture.
"""

import asyncio
import json
import logging
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory in the cognitive system"""
    EPISODIC = "episodic"      # Specific events/experiences
    SEMANTIC = "semantic"      # General knowledge/concepts
    PROCEDURAL = "procedural"  # Rules and procedures
    WORKING = "working"        # Short-term active memory


class MemoryImportance(Enum):
    """Importance levels for memory consolidation"""
    CRITICAL = 5    # Never forget
    HIGH = 4        # Long-term retention
    MEDIUM = 3      # Standard retention
    LOW = 2         # May be forgotten
    TRIVIAL = 1     # Short-term only


@dataclass
class MemoryItem:
    """Base class for memory items"""
    memory_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    importance: MemoryImportance
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    associations: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'memory_id': self.memory_id,
            'memory_type': self.memory_type.value,
            'content': self.content,
            'importance': self.importance.value,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'associations': self.associations,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryItem':
        return cls(
            memory_id=data['memory_id'],
            memory_type=MemoryType(data['memory_type']),
            content=data['content'],
            importance=MemoryImportance(data['importance']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            access_count=data['access_count'],
            associations=data.get('associations', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class EpisodicMemoryItem(MemoryItem):
    """Memory of a specific trading event/experience"""
    event_type: str = ""
    outcome: str = ""  # positive, negative, neutral
    emotional_valence: float = 0.0  # -1 to 1
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.memory_type = MemoryType.EPISODIC


@dataclass  
class SemanticMemoryItem(MemoryItem):
    """General market knowledge and concepts"""
    concept: str = ""
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    confidence: float = 0.5
    sources: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.memory_type = MemoryType.SEMANTIC


@dataclass
class ProceduralMemoryItem(MemoryItem):
    """Trading rules and strategies"""
    rule_type: str = ""  # entry, exit, risk, filter
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    success_rate: float = 0.0
    usage_count: int = 0
    
    def __post_init__(self):
        self.memory_type = MemoryType.PROCEDURAL


class MemoryIndex:
    """Efficient memory indexing and retrieval"""
    
    def __init__(self):
        self.by_type: Dict[MemoryType, Set[str]] = defaultdict(set)
        self.by_importance: Dict[MemoryImportance, Set[str]] = defaultdict(set)
        self.by_tag: Dict[str, Set[str]] = defaultdict(set)
        self.temporal_index: List[Tuple[datetime, str]] = []
        
    def add(self, memory: MemoryItem):
        """Add memory to indices"""
        self.by_type[memory.memory_type].add(memory.memory_id)
        self.by_importance[memory.importance].add(memory.memory_id)
        self.temporal_index.append((memory.created_at, memory.memory_id))
        
        # Index by tags in metadata
        for tag in memory.metadata.get('tags', []):
            self.by_tag[tag].add(memory.memory_id)
    
    def remove(self, memory: MemoryItem):
        """Remove memory from indices"""
        self.by_type[memory.memory_type].discard(memory.memory_id)
        self.by_importance[memory.importance].discard(memory.memory_id)
        self.temporal_index = [(t, m) for t, m in self.temporal_index if m != memory.memory_id]
        
        for tag in memory.metadata.get('tags', []):
            self.by_tag[tag].discard(memory.memory_id)
    
    def get_by_type(self, memory_type: MemoryType) -> Set[str]:
        return self.by_type[memory_type]
    
    def get_by_importance(self, min_importance: MemoryImportance) -> Set[str]:
        result = set()
        for imp in MemoryImportance:
            if imp.value >= min_importance.value:
                result.update(self.by_importance[imp])
        return result
    
    def get_recent(self, n: int = 10) -> List[str]:
        sorted_temporal = sorted(self.temporal_index, key=lambda x: x[0], reverse=True)
        return [m for _, m in sorted_temporal[:n]]


class EpisodicMemory:
    """
    Episodic Memory System
    
    Stores specific trading events and experiences:
    - Trade executions and outcomes
    - Market events (crashes, rallies, regime changes)
    - Strategy performance episodes
    - Anomalies and surprises encountered
    """
    
    def __init__(self, max_size: int = 10000):
        self.memories: Dict[str, EpisodicMemoryItem] = {}
        self.max_size = max_size
        self.index = MemoryIndex()
        
    def store(
        self,
        event_type: str,
        content: Dict[str, Any],
        outcome: str = "neutral",
        emotional_valence: float = 0.0,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a new episodic memory"""
        memory_id = f"ep_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(content).encode()).hexdigest()[:8]}"
        
        memory = EpisodicMemoryItem(
            memory_id=memory_id,
            memory_type=MemoryType.EPISODIC,
            content=content,
            importance=importance,
            event_type=event_type,
            outcome=outcome,
            emotional_valence=emotional_valence,
            context=context or {},
            metadata=metadata or {}
        )
        
        self.memories[memory_id] = memory
        self.index.add(memory)
        
        # Consolidation: remove old low-importance memories if over capacity
        if len(self.memories) > self.max_size:
            self._consolidate()
        
        logger.debug(f"Stored episodic memory: {memory_id}")
        return memory_id
    
    def recall(
        self,
        query: Optional[Dict[str, Any]] = None,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 10
    ) -> List[EpisodicMemoryItem]:
        """Recall episodic memories matching criteria"""
        candidates = list(self.memories.values())
        
        if event_type:
            candidates = [m for m in candidates if m.event_type == event_type]
        
        if outcome:
            candidates = [m for m in candidates if m.outcome == outcome]
        
        if time_range:
            start, end = time_range
            candidates = [m for m in candidates if start <= m.created_at <= end]
        
        # Sort by relevance (access count + recency + importance)
        def relevance_score(m: EpisodicMemoryItem) -> float:
            recency = 1.0 / (1 + (datetime.utcnow() - m.last_accessed).days)
            return m.access_count * 0.3 + recency * 0.4 + m.importance.value * 0.3
        
        candidates.sort(key=relevance_score, reverse=True)
        
        # Update access info
        for m in candidates[:limit]:
            m.last_accessed = datetime.utcnow()
            m.access_count += 1
        
        return candidates[:limit]
    
    def recall_similar(self, memory_id: str, limit: int = 5) -> List[EpisodicMemoryItem]:
        """Recall memories similar to a given memory"""
        if memory_id not in self.memories:
            return []
        
        target = self.memories[memory_id]
        candidates = []
        
        for m in self.memories.values():
            if m.memory_id == memory_id:
                continue
            
            # Simple similarity based on event type and outcome
            similarity = 0.0
            if m.event_type == target.event_type:
                similarity += 0.5
            if m.outcome == target.outcome:
                similarity += 0.3
            
            # Temporal proximity
            time_diff = abs((m.created_at - target.created_at).days)
            similarity += 0.2 / (1 + time_diff)
            
            candidates.append((similarity, m))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in candidates[:limit]]
    
    def _consolidate(self):
        """Consolidate memories - remove low importance old memories"""
        # Sort by importance and recency
        sorted_memories = sorted(
            self.memories.values(),
            key=lambda m: (m.importance.value, m.last_accessed),
            reverse=True
        )
        
        # Keep top memories
        to_keep = sorted_memories[:int(self.max_size * 0.8)]
        
        # Remove others
        keep_ids = {m.memory_id for m in to_keep}
        to_remove = [m for m in self.memories.values() if m.memory_id not in keep_ids]
        
        for m in to_remove:
            self.index.remove(m)
            del self.memories[m.memory_id]
        
        logger.info(f"Consolidated episodic memory: removed {len(to_remove)} memories")


class SemanticMemory:
    """
    Semantic Memory System
    
    Stores general market knowledge and concepts:
    - Market relationships (correlations, lead-lag)
    - Economic principles and theories
    - Asset characteristics
    - Trading concepts and definitions
    """
    
    def __init__(self):
        self.memories: Dict[str, SemanticMemoryItem] = {}
        self.concept_graph: Dict[str, Set[str]] = defaultdict(set)  # Concept relationships
        self.index = MemoryIndex()
        
    def store(
        self,
        concept: str,
        content: Dict[str, Any],
        relationships: Optional[Dict[str, List[str]]] = None,
        confidence: float = 0.5,
        sources: Optional[List[str]] = None,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store semantic knowledge"""
        memory_id = f"sem_{concept.lower().replace(' ', '_')}_{hashlib.md5(str(content).encode()).hexdigest()[:8]}"
        
        memory = SemanticMemoryItem(
            memory_id=memory_id,
            memory_type=MemoryType.SEMANTIC,
            content=content,
            importance=importance,
            concept=concept,
            relationships=relationships or {},
            confidence=confidence,
            sources=sources or [],
            metadata=metadata or {}
        )
        
        self.memories[memory_id] = memory
        self.index.add(memory)
        
        # Update concept graph
        for rel_type, related_concepts in (relationships or {}).items():
            for related in related_concepts:
                self.concept_graph[concept].add(related)
                self.concept_graph[related].add(concept)
        
        logger.debug(f"Stored semantic memory: {memory_id}")
        return memory_id
    
    def recall(
        self,
        concept: Optional[str] = None,
        query: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 10
    ) -> List[SemanticMemoryItem]:
        """Recall semantic memories"""
        candidates = list(self.memories.values())
        
        if concept:
            candidates = [m for m in candidates if concept.lower() in m.concept.lower()]
        
        if min_confidence > 0:
            candidates = [m for m in candidates if m.confidence >= min_confidence]
        
        # Sort by confidence and importance
        candidates.sort(key=lambda m: (m.confidence, m.importance.value), reverse=True)
        
        return candidates[:limit]
    
    def get_related_concepts(self, concept: str, depth: int = 2) -> Set[str]:
        """Get concepts related to a given concept"""
        visited = set()
        to_visit = {concept}
        
        for _ in range(depth):
            next_visit = set()
            for c in to_visit:
                if c not in visited:
                    visited.add(c)
                    next_visit.update(self.concept_graph.get(c, set()))
            to_visit = next_visit - visited
        
        return visited - {concept}
    
    def update_confidence(self, memory_id: str, new_confidence: float, source: Optional[str] = None):
        """Update confidence in a semantic memory"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            # Bayesian-like update
            memory.confidence = 0.7 * memory.confidence + 0.3 * new_confidence
            if source:
                memory.sources.append(source)
            memory.last_accessed = datetime.utcnow()


class ProceduralMemory:
    """
    Procedural Memory System
    
    Stores trading rules and strategies:
    - Entry/exit rules
    - Risk management procedures
    - Signal filtering rules
    - Strategy templates
    """
    
    def __init__(self):
        self.memories: Dict[str, ProceduralMemoryItem] = {}
        self.by_rule_type: Dict[str, Set[str]] = defaultdict(set)
        self.index = MemoryIndex()
        
    def store(
        self,
        rule_type: str,
        conditions: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        content: Optional[Dict[str, Any]] = None,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a procedural rule"""
        memory_id = f"proc_{rule_type}_{hashlib.md5(str(conditions).encode()).hexdigest()[:8]}"
        
        memory = ProceduralMemoryItem(
            memory_id=memory_id,
            memory_type=MemoryType.PROCEDURAL,
            content=content or {'conditions': conditions, 'actions': actions},
            importance=importance,
            rule_type=rule_type,
            conditions=conditions,
            actions=actions,
            metadata=metadata or {}
        )
        
        self.memories[memory_id] = memory
        self.by_rule_type[rule_type].add(memory_id)
        self.index.add(memory)
        
        logger.debug(f"Stored procedural memory: {memory_id}")
        return memory_id
    
    def recall(
        self,
        rule_type: Optional[str] = None,
        min_success_rate: float = 0.0,
        limit: int = 10
    ) -> List[ProceduralMemoryItem]:
        """Recall procedural memories"""
        if rule_type:
            memory_ids = self.by_rule_type.get(rule_type, set())
            candidates = [self.memories[mid] for mid in memory_ids if mid in self.memories]
        else:
            candidates = list(self.memories.values())
        
        if min_success_rate > 0:
            candidates = [m for m in candidates if m.success_rate >= min_success_rate]
        
        # Sort by success rate and usage
        candidates.sort(key=lambda m: (m.success_rate, m.usage_count), reverse=True)
        
        return candidates[:limit]
    
    def update_performance(self, memory_id: str, success: bool):
        """Update performance metrics for a procedural memory"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            memory.usage_count += 1
            # Exponential moving average for success rate
            alpha = 0.1
            memory.success_rate = (1 - alpha) * memory.success_rate + alpha * (1.0 if success else 0.0)
            memory.last_accessed = datetime.utcnow()
    
    def get_applicable_rules(self, context: Dict[str, Any], rule_type: Optional[str] = None) -> List[ProceduralMemoryItem]:
        """Get rules applicable to current context"""
        candidates = self.recall(rule_type=rule_type, limit=100)
        applicable = []
        
        for rule in candidates:
            if self._check_conditions(rule.conditions, context):
                applicable.append(rule)
        
        return applicable
    
    def _check_conditions(self, conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """Check if conditions are met by context"""
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator', '==')
            value = condition.get('value')
            
            if field not in context:
                return False
            
            ctx_value = context[field]
            
            if operator == '==' and ctx_value != value:
                return False
            elif operator == '>' and ctx_value <= value:
                return False
            elif operator == '<' and ctx_value >= value:
                return False
            elif operator == '>=' and ctx_value < value:
                return False
            elif operator == '<=' and ctx_value > value:
                return False
            elif operator == 'in' and ctx_value not in value:
                return False
        
        return True


class MemorySystem:
    """
    Unified Memory System
    
    Coordinates all memory types and provides:
    - Cross-memory retrieval
    - Memory consolidation
    - Association building
    - Persistence
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.working_memory: List[MemoryItem] = []  # Short-term active memories
        self.working_memory_capacity = 7  # Miller's magic number
        
        self.storage_path = Path(storage_path) if storage_path else Path("foundation_agents_data/memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'episodic_stores': 0,
            'semantic_stores': 0,
            'procedural_stores': 0,
            'recalls': 0,
            'consolidations': 0
        }
        
        # Load persisted memories
        self._load()
        
        logger.info("Memory System initialized")
    
    def store_episode(self, **kwargs) -> str:
        """Store an episodic memory"""
        memory_id = self.episodic.store(**kwargs)
        self.stats['episodic_stores'] += 1
        return memory_id
    
    def store_knowledge(self, **kwargs) -> str:
        """Store semantic knowledge"""
        memory_id = self.semantic.store(**kwargs)
        self.stats['semantic_stores'] += 1
        return memory_id
    
    def store_rule(self, **kwargs) -> str:
        """Store a procedural rule"""
        memory_id = self.procedural.store(**kwargs)
        self.stats['procedural_stores'] += 1
        return memory_id
    
    def recall_all(
        self,
        query: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10
    ) -> Dict[MemoryType, List[MemoryItem]]:
        """Recall from all memory types"""
        self.stats['recalls'] += 1
        results = {}
        
        types_to_search = memory_types or [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]
        
        if MemoryType.EPISODIC in types_to_search:
            results[MemoryType.EPISODIC] = self.episodic.recall(limit=limit)
        
        if MemoryType.SEMANTIC in types_to_search:
            results[MemoryType.SEMANTIC] = self.semantic.recall(query=query, limit=limit)
        
        if MemoryType.PROCEDURAL in types_to_search:
            results[MemoryType.PROCEDURAL] = self.procedural.recall(limit=limit)
        
        return results
    
    def add_to_working_memory(self, memory: MemoryItem):
        """Add memory to working memory (short-term focus)"""
        self.working_memory.insert(0, memory)
        
        # Maintain capacity limit
        if len(self.working_memory) > self.working_memory_capacity:
            self.working_memory = self.working_memory[:self.working_memory_capacity]
    
    def get_working_memory(self) -> List[MemoryItem]:
        """Get current working memory contents"""
        return self.working_memory.copy()
    
    def clear_working_memory(self):
        """Clear working memory"""
        self.working_memory.clear()
    
    def build_association(self, memory_id_1: str, memory_id_2: str):
        """Build association between two memories"""
        # Find memories
        m1 = self._find_memory(memory_id_1)
        m2 = self._find_memory(memory_id_2)
        
        if m1 and m2:
            if memory_id_2 not in m1.associations:
                m1.associations.append(memory_id_2)
            if memory_id_1 not in m2.associations:
                m2.associations.append(memory_id_1)
    
    def _find_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Find a memory by ID across all stores"""
        if memory_id in self.episodic.memories:
            return self.episodic.memories[memory_id]
        if memory_id in self.semantic.memories:
            return self.semantic.memories[memory_id]
        if memory_id in self.procedural.memories:
            return self.procedural.memories[memory_id]
        return None
    
    def consolidate(self):
        """Consolidate memories - strengthen important, forget trivial"""
        self.stats['consolidations'] += 1
        self.episodic._consolidate()
        self._save()
        logger.info("Memory consolidation complete")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            **self.stats,
            'episodic_count': len(self.episodic.memories),
            'semantic_count': len(self.semantic.memories),
            'procedural_count': len(self.procedural.memories),
            'working_memory_size': len(self.working_memory)
        }
    
    def _save(self):
        """Persist memories to disk"""
        try:
            data = {
                'episodic': [m.to_dict() for m in self.episodic.memories.values()],
                'semantic': [m.to_dict() for m in self.semantic.memories.values()],
                'procedural': [m.to_dict() for m in self.procedural.memories.values()],
                'stats': self.stats
            }
            
            with open(self.storage_path / 'memories.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug("Memories persisted to disk")
            
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")
    
    def _load(self):
        """Load memories from disk"""
        memory_file = self.storage_path / 'memories.json'
        
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                
                # Restore episodic memories
                for m_data in data.get('episodic', []):
                    memory = MemoryItem.from_dict(m_data)
                    self.episodic.memories[memory.memory_id] = memory
                    self.episodic.index.add(memory)
                
                # Restore semantic memories
                for m_data in data.get('semantic', []):
                    memory = MemoryItem.from_dict(m_data)
                    self.semantic.memories[memory.memory_id] = memory
                    self.semantic.index.add(memory)
                
                # Restore procedural memories
                for m_data in data.get('procedural', []):
                    memory = MemoryItem.from_dict(m_data)
                    self.procedural.memories[memory.memory_id] = memory
                    self.procedural.index.add(memory)
                
                self.stats = data.get('stats', self.stats)
                
                logger.info(f"Loaded {len(self.episodic.memories)} episodic, "
                           f"{len(self.semantic.memories)} semantic, "
                           f"{len(self.procedural.memories)} procedural memories")
                
            except Exception as e:
                logger.error(f"Failed to load memories: {e}")
