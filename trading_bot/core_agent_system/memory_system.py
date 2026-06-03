"""
Memory System - Multi-Tier Memory Architecture

Implements a comprehensive memory system inspired by:
- Human cognitive architecture (working, episodic, semantic, procedural)
- DeepMind's memory-augmented neural networks
- OpenAI's retrieval-augmented generation
- LangChain's memory abstractions

Key Features:
- Working Memory: Current context and active information
- Episodic Memory: Specific experiences and events
- Semantic Memory: General knowledge and facts
- Procedural Memory: Skills and learned behaviors
- Memory consolidation and retrieval
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import json
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory"""
    WORKING = "working"       # Short-term, current context
    EPISODIC = "episodic"     # Specific experiences
    SEMANTIC = "semantic"     # General knowledge
    PROCEDURAL = "procedural" # Skills and procedures


@dataclass
class MemoryEntry:
    """A single memory entry"""
    memory_id: str
    memory_type: MemoryType
    content: Any
    metadata: Dict[str, Any]
    importance: float  # 0-1, higher = more important
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    embedding: Optional[List[float]] = None  # For semantic search
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'memory_id': self.memory_id,
            'memory_type': self.memory_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'importance': self.importance,
            'timestamp': self.timestamp.isoformat(),
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(
            memory_id=data['memory_id'],
            memory_type=MemoryType(data['memory_type']),
            content=data['content'],
            metadata=data['metadata'],
            importance=data['importance'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            access_count=data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None
        )


class WorkingMemory:
    """
    Working Memory - Current context and active information.
    
    Like human working memory:
    - Limited capacity
    - Fast access
    - Temporary storage
    - Current focus of attention
    """
    
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.items: Dict[str, Any] = {}
        self.access_order: List[str] = []  # For LRU eviction
        
        logger.info(f"Working Memory initialized (capacity: {capacity})")
    
    def store(self, key: str, value: Any, priority: float = 0.5):
        """Store item in working memory"""
        # Evict if at capacity
        while len(self.items) >= self.capacity:
            self._evict_lru()
        
        self.items[key] = {
            'value': value,
            'priority': priority,
            'stored_at': datetime.now()
        }
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve item from working memory"""
        if key not in self.items:
            return None
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return self.items[key]['value']
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if self.access_order:
            lru_key = self.access_order.pop(0)
            if lru_key in self.items:
                del self.items[lru_key]
    
    def get_context(self) -> Dict[str, Any]:
        """Get current working memory context"""
        return {
            key: item['value']
            for key, item in self.items.items()
        }
    
    def clear(self):
        """Clear working memory"""
        self.items.clear()
        self.access_order.clear()
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'capacity': self.capacity,
            'used': len(self.items),
            'keys': list(self.items.keys())
        }


class EpisodicMemory:
    """
    Episodic Memory - Specific experiences and events.
    
    Like human episodic memory:
    - Stores specific experiences
    - Temporal ordering
    - Context-dependent retrieval
    - Supports learning from past experiences
    """
    
    def __init__(self, max_episodes: int = 10000):
        self.max_episodes = max_episodes
        self.episodes: List[MemoryEntry] = []
        self.index: Dict[str, List[int]] = {}  # Tag -> episode indices
        
        logger.info(f"Episodic Memory initialized (max: {max_episodes})")
    
    def store_episode(
        self,
        content: Dict[str, Any],
        importance: float = 0.5,
        tags: Optional[List[str]] = None
    ) -> str:
        """Store an episode"""
        memory_id = str(uuid.uuid4())
        
        episode = MemoryEntry(
            memory_id=memory_id,
            memory_type=MemoryType.EPISODIC,
            content=content,
            metadata={'tags': tags or []},
            importance=importance,
            timestamp=datetime.now()
        )
        
        self.episodes.append(episode)
        
        # Index by tags
        for tag in (tags or []):
            if tag not in self.index:
                self.index[tag] = []
            self.index[tag].append(len(self.episodes) - 1)
        
        # Trim if over capacity
        if len(self.episodes) > self.max_episodes:
            self._consolidate()
        
        return memory_id
    
    def retrieve_recent(self, n: int = 10) -> List[MemoryEntry]:
        """Retrieve n most recent episodes"""
        return self.episodes[-n:]
    
    def retrieve_by_tag(self, tag: str) -> List[MemoryEntry]:
        """Retrieve episodes by tag"""
        if tag not in self.index:
            return []
        
        indices = self.index[tag]
        return [self.episodes[i] for i in indices if i < len(self.episodes)]
    
    def retrieve_by_time_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[MemoryEntry]:
        """Retrieve episodes within time range"""
        return [
            ep for ep in self.episodes
            if start <= ep.timestamp <= end
        ]
    
    def retrieve_similar(
        self,
        query: Dict[str, Any],
        k: int = 5
    ) -> List[MemoryEntry]:
        """
        Retrieve similar episodes.
        
        In production, would use embeddings and vector similarity.
        Here we use simple key matching.
        """
        scores = []
        
        for i, episode in enumerate(self.episodes):
            score = self._calculate_similarity(query, episode.content)
            scores.append((i, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        return [self.episodes[i] for i, _ in scores[:k]]
    
    def _calculate_similarity(
        self,
        query: Dict[str, Any],
        content: Dict[str, Any]
    ) -> float:
        """Calculate similarity between query and content"""
        if not isinstance(content, dict):
            return 0.0
        
        # Simple key overlap similarity
        query_keys = set(str(k) for k in query.keys())
        content_keys = set(str(k) for k in content.keys())
        
        if not query_keys:
            return 0.0
        
        overlap = len(query_keys & content_keys)
        return overlap / len(query_keys)
    
    def _consolidate(self):
        """Consolidate memory - remove low importance old episodes"""
        # Keep important episodes and recent episodes
        cutoff = datetime.now() - timedelta(days=30)
        
        self.episodes = [
            ep for ep in self.episodes
            if ep.importance > 0.7 or ep.timestamp > cutoff
        ][-self.max_episodes:]
        
        # Rebuild index
        self.index.clear()
        for i, ep in enumerate(self.episodes):
            for tag in ep.metadata.get('tags', []):
                if tag not in self.index:
                    self.index[tag] = []
                self.index[tag].append(i)
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'total_episodes': len(self.episodes),
            'max_episodes': self.max_episodes,
            'tags': list(self.index.keys())
        }


class SemanticMemory:
    """
    Semantic Memory - General knowledge and facts.
    
    Like human semantic memory:
    - Stores facts and concepts
    - Organized by meaning
    - Supports inference
    - Long-term storage
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path
        self.knowledge: Dict[str, MemoryEntry] = {}
        self.concept_graph: Dict[str, List[str]] = {}  # Concept -> related concepts
    
    def store_knowledge(
        self,
        key: str,
        content: Any,
        related_concepts: Optional[List[str]] = None,
        importance: float = 0.5
    ) -> str:
        """Store a piece of knowledge"""
        memory_id = str(uuid.uuid4())
        
        entry = MemoryEntry(
            memory_id=memory_id,
            memory_type=MemoryType.SEMANTIC,
            content=content,
            metadata={'key': key, 'related': related_concepts or []},
            importance=importance,
            timestamp=datetime.now()
        )
        
        self.knowledge[key] = entry
        
        # Update concept graph
        if related_concepts:
            if key not in self.concept_graph:
                self.concept_graph[key] = []
            self.concept_graph[key].extend(related_concepts)
            
            # Bidirectional links
            for concept in related_concepts:
                if concept not in self.concept_graph:
                    self.concept_graph[concept] = []
                if key not in self.concept_graph[concept]:
                    self.concept_graph[concept].append(key)
        
        return memory_id
    
    def retrieve_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve knowledge by key"""
        if key not in self.knowledge:
            return None
        
        entry = self.knowledge[key]
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        
        return entry.content
    
    def retrieve_related(self, key: str, depth: int = 1) -> Dict[str, Any]:
        """Retrieve related knowledge"""
        if key not in self.concept_graph:
            return {}
        
        related = {}
        visited = set()
        to_visit = [(key, 0)]
        
        while to_visit:
            current, current_depth = to_visit.pop(0)
            
            if current in visited or current_depth > depth:
                continue
            
            visited.add(current)
            
            if current in self.knowledge:
                related[current] = self.knowledge[current].content
            
            if current in self.concept_graph:
                for neighbor in self.concept_graph[current]:
                    if neighbor not in visited:
                        to_visit.append((neighbor, current_depth + 1))
        
        return related
    
    def search(self, query: str) -> List[Tuple[str, Any]]:
        """Search knowledge base"""
        results = []
        
        query_lower = query.lower()
        
        for key, entry in self.knowledge.items():
            # Simple text matching
            if query_lower in key.lower():
                results.append((key, entry.content))
            elif isinstance(entry.content, str) and query_lower in entry.content.lower():
                results.append((key, entry.content))
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'total_knowledge': len(self.knowledge),
            'concepts': len(self.concept_graph),
            'keys': list(self.knowledge.keys())[:20]  # First 20
        }


class ProceduralMemory:
    """
    Procedural Memory - Skills and learned behaviors.
    
    Like human procedural memory:
    - Stores how to do things
    - Implicit knowledge
    - Improves with practice
    - Automatic execution
    """
    
    def __init__(self):
        self.procedures: Dict[str, Dict[str, Any]] = {}
        self.execution_history: Dict[str, List[Dict]] = {}
        
        logger.info("Procedural Memory initialized")

    def store_procedure(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        conditions: Optional[Dict[str, Any]] = None,
        success_rate: float = 0.5
    ):
        self.procedures[name] = {
            'steps': steps,
            'conditions': conditions or {},
            'success_rate': success_rate,
            'execution_count': 0,
            'last_executed': None,
            'created_at': datetime.now()
        }
    
    def get_procedure(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a procedure"""
        return self.procedures.get(name)
    
    def record_execution(
        self,
        name: str,
        success: bool,
        context: Optional[Dict] = None
    ):
        """Record procedure execution for learning"""
        if name not in self.procedures:
            return
        
        proc = self.procedures[name]
        proc['execution_count'] += 1
        proc['last_executed'] = datetime.now()
        
        # Update success rate with exponential moving average
        alpha = 0.1
        proc['success_rate'] = (1 - alpha) * proc['success_rate'] + alpha * (1.0 if success else 0.0)
        
        # Store execution history
        if name not in self.execution_history:
            self.execution_history[name] = []
        
        self.execution_history[name].append({
            'success': success,
            'context': context,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        self.execution_history[name] = self.execution_history[name][-100:]
    
    def get_best_procedure(
        self,
        task_type: str,
        context: Optional[Dict] = None
    ) -> Optional[str]:
        """Get best procedure for a task type"""
        candidates = [
            (name, proc)
            for name, proc in self.procedures.items()
            if task_type in name or task_type in str(proc.get('conditions', {}))
        ]
        
        if not candidates:
            return None
        
        # Sort by success rate
        candidates.sort(key=lambda x: x[1]['success_rate'], reverse=True)
        
        return candidates[0][0]
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'total_procedures': len(self.procedures),
            'procedures': {
                name: {
                    'success_rate': proc['success_rate'],
                    'execution_count': proc['execution_count']
                }
                for name, proc in self.procedures.items()
            }
        }


class MemorySystem:
    """
    Unified Memory System
    
    Integrates all memory types into a cohesive system:
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    MEMORY SYSTEM                             │
    │                                                              │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │              Working Memory                          │    │
    │  │  Current context, active information                 │    │
    │  │  Fast access, limited capacity                       │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                          ↕                                   │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │              Episodic Memory                         │    │
    │  │  Specific experiences, temporal ordering             │    │
    │  │  "What happened when..."                             │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                          ↕                                   │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │              Semantic Memory                         │    │
    │  │  Facts, concepts, knowledge                          │    │
    │  │  "What is..."                                        │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                          ↕                                   │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │              Procedural Memory                       │    │
    │  │  Skills, procedures, how-to                          │    │
    │  │  "How to..."                                         │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                          ↕                                   │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │              Memory Consolidation                    │    │
    │  │  Transfer important memories to long-term            │    │
    │  │  Forget unimportant information                      │    │
    │  └─────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        storage_path = Path(self.config.get('storage_path', 'memory_data'))
        storage_path.mkdir(parents=True, exist_ok=True)
        self.storage_path = storage_path
        
        # Initialize memory components
        self.working = WorkingMemory(
            capacity=self.config.get('working_memory_capacity', 10)
        )
        self.episodic = EpisodicMemory(
            max_episodes=self.config.get('max_episodes', 10000)
        )
        self.semantic = SemanticMemory(storage_path=storage_path)
        self.procedural = ProceduralMemory()
        
        # Consolidation settings
        self.consolidation_interval = self.config.get('consolidation_interval', 3600)
        self.last_consolidation = datetime.now()
        
        self.running = False
        
        logger.info("Memory System initialized")
    
    async def initialize(self):
        """Initialize the memory system"""
        logger.info("Initializing Memory System")
        
        # Load persisted memories
        await self._load_memories()
        
        self.running = True
        
        # Start consolidation loop
        asyncio.create_task(self._consolidation_loop())
        
        logger.info("Memory System ready")
    
    async def _load_memories(self):
        """Load persisted memories from storage"""
        # Load semantic memory
        semantic_file = self.storage_path / 'semantic_memory.json'
        if semantic_file.exists():
            try:
                with open(semantic_file, 'r') as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        entry = MemoryEntry.from_dict(entry_data)
                        self.semantic.knowledge[key] = entry
                logger.info(f"Loaded {len(self.semantic.knowledge)} semantic memories")
            except Exception as e:
                logger.error(f"Error loading semantic memory: {e}")
        
        # Load procedural memory
        procedural_file = self.storage_path / 'procedural_memory.json'
        if procedural_file.exists():
            try:
                with open(procedural_file, 'r') as f:
                    self.procedural.procedures = json.load(f)
                logger.info(f"Loaded {len(self.procedural.procedures)} procedures")
            except Exception as e:
                logger.error(f"Error loading procedural memory: {e}")
    
    async def _save_memories(self):
        """Save memories to storage"""
        # Save semantic memory
        semantic_file = self.storage_path / 'semantic_memory.json'
        try:
            data = {
                key: entry.to_dict()
                for key, entry in self.semantic.knowledge.items()
            }
            with open(semantic_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving semantic memory: {e}")
        
        # Save procedural memory
        procedural_file = self.storage_path / 'procedural_memory.json'
        try:
            # Convert datetime objects to strings
            procedures_data = {}
            for name, proc in self.procedural.procedures.items():
                proc_copy = proc.copy()
                if proc_copy.get('last_executed'):
                    proc_copy['last_executed'] = proc_copy['last_executed'].isoformat()
                if proc_copy.get('created_at'):
                    proc_copy['created_at'] = proc_copy['created_at'].isoformat()
                procedures_data[name] = proc_copy
            
            with open(procedural_file, 'w') as f:
                json.dump(procedures_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving procedural memory: {e}")
    
    async def _consolidation_loop(self):
        """Periodically consolidate memories"""
        while self.running:
            try:
                await asyncio.sleep(self.consolidation_interval)
                await self._consolidate()
            except Exception as e:
                logger.error(f"Error in consolidation loop: {e}")
    
    async def _consolidate(self):
        """
        Consolidate memories - transfer important short-term to long-term.
        
        Inspired by human memory consolidation during sleep.
        """
        logger.info("Running memory consolidation")
        
        # Get important items from working memory
        for key, item in list(self.working.items.items()):
            if item['priority'] > 0.7:
                # Store in semantic memory
                self.semantic.store_knowledge(
                    key=f"consolidated_{key}",
                    content=item['value'],
                    importance=item['priority']
                )
        
        # Consolidate episodic to semantic
        important_episodes = [
            ep for ep in self.episodic.episodes
            if ep.importance > 0.8
        ]
        
        for episode in important_episodes:
            # Extract patterns/knowledge from episodes
            if isinstance(episode.content, dict):
                if 'pattern' in episode.content:
                    self.semantic.store_knowledge(
                        key=f"pattern_{episode.memory_id}",
                        content=episode.content['pattern'],
                        importance=episode.importance
                    )
        
        # Save to disk
        await self._save_memories()
        
        self.last_consolidation = datetime.now()
        logger.info("Memory consolidation complete")
    
    # ==================== HIGH-LEVEL INTERFACE ====================
    
    async def store_decision(self, decision) -> str:
        """Store a decision in memory"""
        # Store in working memory for immediate access
        self.working.store(
            f"decision_{decision.decision_id}",
            decision,
            priority=decision.confidence
        )
        
        # Store in episodic memory for learning
        return self.episodic.store_episode(
            content={
                'decision_id': decision.decision_id,
                'decision_type': decision.decision_type,
                'action': decision.action,
                'expected_value': decision.expected_value,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning_chain
            },
            importance=decision.confidence,
            tags=['decision', decision.decision_type]
        )
    
    async def store_experience(self, experience: Dict[str, Any]) -> str:
        """Store an experience (decision + outcome)"""
        # Calculate importance based on outcome
        result = experience.get('result', {})
        success = result.get('success', False)
        importance = 0.8 if success else 0.6
        
        return self.episodic.store_episode(
            content=experience,
            importance=importance,
            tags=['experience', 'outcome']
        )
    
    async def store_episode(self, episode: Dict[str, Any]) -> str:
        """Store a general episode"""
        return self.episodic.store_episode(
            content=episode,
            importance=episode.get('importance', 0.5),
            tags=episode.get('tags', [])
        )
    
    async def retrieve_similar(self, context, k: int = 5) -> List[Dict]:
        """Retrieve similar past experiences"""
        # Convert context to query dict
        if hasattr(context, 'market_state'):
            query = {
                'market_state': context.market_state,
                'portfolio_state': context.portfolio_state
            }
        else:
            query = context if isinstance(context, dict) else {}
        
        episodes = self.episodic.retrieve_similar(query, k=k)
        
        return [
            {
                'memory_id': ep.memory_id,
                'content': ep.content,
                'importance': ep.importance,
                'timestamp': ep.timestamp,
                'action': ep.content.get('action') if isinstance(ep.content, dict) else None,
                'outcome': ep.content.get('result') if isinstance(ep.content, dict) else None
            }
            for ep in episodes
        ]
    
    async def get_context(self) -> Dict[str, Any]:
        """Get current context from working memory"""
        return self.working.get_context()
    
    async def store_knowledge(
        self,
        key: str,
        content: Any,
        related: Optional[List[str]] = None
    ):
        """Store knowledge in semantic memory"""
        self.semantic.store_knowledge(key, content, related)
    
    async def retrieve_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve knowledge from semantic memory"""
        return self.semantic.retrieve_knowledge(key)
    
    async def store_procedure(
        self,
        name: str,
        steps: List[Dict],
        conditions: Optional[Dict] = None
    ):
        """Store a procedure"""
        self.procedural.store_procedure(name, steps, conditions)
    
    async def get_procedure(self, name: str) -> Optional[Dict]:
        """Get a procedure"""
        return self.procedural.get_procedure(name)
    
    def get_status(self) -> Dict[str, Any]:
        """Get memory system status"""
        return {
            'working': self.working.get_status(),
            'episodic': self.episodic.get_status(),
            'semantic': self.semantic.get_status(),
            'procedural': self.procedural.get_status(),
            'last_consolidation': self.last_consolidation.isoformat()
        }
    
    async def shutdown(self):
        """Shutdown memory system"""
        logger.info("Shutting down Memory System")
        self.running = False
        
        # Final save
        await self._save_memories()
        
        logger.info("Memory System shutdown complete")
