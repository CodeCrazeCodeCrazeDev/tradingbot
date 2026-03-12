"""
Persistent Memory for Perplexity Trading Architecture
============================================================

Three-tier memory system like Perplexity Computer:
- Short-term: Within session (cleared on restart)
- Medium-term: 7 days persistence
- Long-term: Permanent storage

Features:
- User preferences and trading style
- Recent trade history and outcomes
- Market context and patterns
- Knowledge graph for relationships
"""

import logging
import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import hashlib

from .core_types import (
    MemoryEntry,
    MemoryLevel,
    MemoryQuery,
)

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeNode:
    """Node in the knowledge graph"""
    id: str
    node_type: str  # e.g., "symbol", "pattern", "strategy", "event"
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'node_type': self.node_type,
            'label': self.label,
            'properties': self.properties,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class KnowledgeEdge:
    """Edge in the knowledge graph"""
    from_node: str
    to_node: str
    relationship: str  # e.g., "correlates_with", "causes", "precedes"
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'from_node': self.from_node,
            'to_node': self.to_node,
            'relationship': self.relationship,
            'weight': self.weight,
            'properties': self.properties,
        }


class KnowledgeGraph:
    """
    Simple knowledge graph for storing relationships.
    
    Used to track:
    - Symbol correlations
    - Pattern relationships
    - Strategy performance by regime
    - Event impacts
    """
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []
        self.adjacency: Dict[str, Set[str]] = {}
    
    def add_node(self, node: KnowledgeNode) -> None:
        """Add a node to the graph"""
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = set()
    
    def add_edge(self, edge: KnowledgeEdge) -> None:
        """Add an edge to the graph"""
        self.edges.append(edge)
        
        # Update adjacency
        if edge.from_node not in self.adjacency:
            self.adjacency[edge.from_node] = set()
        self.adjacency[edge.from_node].add(edge.to_node)
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all neighbors of a node"""
        return list(self.adjacency.get(node_id, set()))
    
    def get_related(self, node_id: str, relationship: str) -> List[KnowledgeNode]:
        """Get nodes related by a specific relationship"""
        related = []
        for edge in self.edges:
            if edge.from_node == node_id and edge.relationship == relationship:
                if edge.to_node in self.nodes:
                    related.append(self.nodes[edge.to_node])
        return related
    
    def find_path(self, from_id: str, to_id: str, max_depth: int = 5) -> Optional[List[str]]:
        """Find path between two nodes (BFS)"""
        if from_id not in self.nodes or to_id not in self.nodes:
            return None
        
        visited = {from_id}
        queue = [(from_id, [from_id])]
        
        while queue and len(queue[0][1]) <= max_depth:
            current, path = queue.pop(0)
            
            if current == to_id:
                return path
            
            for neighbor in self.adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodes': {k: v.to_dict() for k, v in self.nodes.items()},
            'edges': [e.to_dict() for e in self.edges],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGraph':
        graph = cls()
        
        for node_data in data.get('nodes', {}).values():
            node = KnowledgeNode(
                id=node_data['id'],
                node_type=node_data['node_type'],
                label=node_data['label'],
                properties=node_data.get('properties', {}),
            )
            graph.add_node(node)
        
        for edge_data in data.get('edges', []):
            edge = KnowledgeEdge(
                from_node=edge_data['from_node'],
                to_node=edge_data['to_node'],
                relationship=edge_data['relationship'],
                weight=edge_data.get('weight', 1.0),
                properties=edge_data.get('properties', {}),
            )
            graph.add_edge(edge)
        
        return graph


class PersistentMemory:
    """
    Three-tier persistent memory system.
    
    Levels:
    - SHORT_TERM: In-memory only, cleared on restart
    - MEDIUM_TERM: SQLite storage, 7-day retention
    - LONG_TERM: SQLite storage, permanent
    
    Categories:
    - user_preference: Trading preferences, risk tolerance
    - trade_history: Recent trades and outcomes
    - market_context: Market conditions, regimes
    - pattern: Recognized patterns and their outcomes
    - strategy: Strategy performance data
    """
    
    def __init__(self, db_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.db_path = db_path or "perplexity_trading_memory.db"
        
        # Short-term memory (in-memory)
        self.short_term: Dict[str, MemoryEntry] = {}
        
        # Knowledge graph
        self.knowledge_graph = KnowledgeGraph()
        
        # Initialize database
        self._init_db()
        
        # Load knowledge graph
        self._load_knowledge_graph()
    
    def _init_db(self) -> None:
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Memory entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_entries (
                id TEXT PRIMARY KEY,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        # Knowledge graph table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_category ON memory_entries(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_entries(key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_level ON memory_entries(level)')
        
        conn.commit()
        conn.close()
    
    def _load_knowledge_graph(self) -> None:
        """Load knowledge graph from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT data FROM knowledge_graph ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            conn.close()
            
            if row:
                data = json.loads(row[0])
                self.knowledge_graph = KnowledgeGraph.from_dict(data)
        except Exception as e:
            logger.warning(f"Could not load knowledge graph: {e}")
    
    def _save_knowledge_graph(self) -> None:
        """Save knowledge graph to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data = json.dumps(self.knowledge_graph.to_dict())
            cursor.execute(
                'INSERT INTO knowledge_graph (data, updated_at) VALUES (?, ?)',
                (data, datetime.utcnow().isoformat())
            )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Could not save knowledge graph: {e}")
    
    def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry"""
        # Set expiration for medium-term
        if entry.level == MemoryLevel.MEDIUM_TERM and not entry.expires_at:
            entry.expires_at = datetime.utcnow() + timedelta(days=7)
        
        if entry.level == MemoryLevel.SHORT_TERM:
            # Store in memory only
            self.short_term[entry.id] = entry
        else:
            # Store in database
            self._store_to_db(entry)
        
        logger.debug(f"Stored memory: {entry.category}/{entry.key} at {entry.level.value}")
        return entry.id
    
    def _store_to_db(self, entry: MemoryEntry) -> None:
        """Store entry to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO memory_entries 
            (id, level, category, key, value, metadata, created_at, updated_at, expires_at, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.id,
            entry.level.value,
            entry.category,
            entry.key,
            json.dumps(entry.value),
            json.dumps(entry.metadata),
            entry.created_at.isoformat(),
            entry.updated_at.isoformat(),
            entry.expires_at.isoformat() if entry.expires_at else None,
            entry.access_count,
        ))
        
        conn.commit()
        conn.close()
    
    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry by ID"""
        # Check short-term first
        if entry_id in self.short_term:
            entry = self.short_term[entry_id]
            entry.access_count += 1
            return entry
        
        # Check database
        return self._retrieve_from_db(entry_id)
    
    def _retrieve_from_db(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve entry from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM memory_entries WHERE id = ?', (entry_id,))
        row = cursor.fetchone()
        
        if row:
            # Update access count
            cursor.execute(
                'UPDATE memory_entries SET access_count = access_count + 1 WHERE id = ?',
                (entry_id,)
            )
            conn.commit()
        
        conn.close()
        
        if row:
            return self._row_to_entry(row)
        return None
    
    def _row_to_entry(self, row: tuple) -> MemoryEntry:
        """Convert database row to MemoryEntry"""
        return MemoryEntry(
            id=row[0],
            level=MemoryLevel(row[1]),
            category=row[2],
            key=row[3],
            value=json.loads(row[4]),
            metadata=json.loads(row[5]) if row[5] else {},
            created_at=datetime.fromisoformat(row[6]),
            updated_at=datetime.fromisoformat(row[7]),
            expires_at=datetime.fromisoformat(row[8]) if row[8] else None,
            access_count=row[9],
        )
    
    def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query memory entries"""
        results = []
        
        # Query short-term
        for entry in self.short_term.values():
            if self._matches_query(entry, query):
                results.append(entry)
        
        # Query database
        db_results = self._query_db(query)
        results.extend(db_results)
        
        # Sort by access count (most accessed first)
        results.sort(key=lambda e: e.access_count, reverse=True)
        
        # Apply limit
        return results[:query.limit]
    
    def _matches_query(self, entry: MemoryEntry, query: MemoryQuery) -> bool:
        """Check if entry matches query"""
        if query.categories and entry.category not in query.categories:
            return False
        if query.keys and entry.key not in query.keys:
            return False
        if query.levels and entry.level not in query.levels:
            return False
        if not query.include_expired and entry.expires_at:
            if entry.expires_at < datetime.utcnow():
                return False
        if query.text_search:
            # Simple text search in value
            value_str = json.dumps(entry.value).lower()
            if query.text_search.lower() not in value_str:
                return False
        return True
    
    def _query_db(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = 'SELECT * FROM memory_entries WHERE 1=1'
        params = []
        
        if query.categories:
            placeholders = ','.join('?' * len(query.categories))
            sql += f' AND category IN ({placeholders})'
            params.extend(query.categories)
        
        if query.keys:
            placeholders = ','.join('?' * len(query.keys))
            sql += f' AND key IN ({placeholders})'
            params.extend(query.keys)
        
        if query.levels:
            placeholders = ','.join('?' * len(query.levels))
            sql += f' AND level IN ({placeholders})'
            params.extend([l.value for l in query.levels])
        
        if not query.include_expired:
            sql += ' AND (expires_at IS NULL OR expires_at > ?)'
            params.append(datetime.utcnow().isoformat())
        
        sql += ' ORDER BY access_count DESC LIMIT ?'
        params.append(query.limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_context(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get aggregated context from memory"""
        query = MemoryQuery(
            categories=categories or ['user_preference', 'market_context', 'trade_history'],
            limit=50,
        )
        
        entries = self.query(query)
        
        context = {
            'user_preferences': {},
            'market_context': {},
            'recent_trades': [],
            'patterns': [],
        }
        
        for entry in entries:
            if entry.category == 'user_preference':
                context['user_preferences'][entry.key] = entry.value
            elif entry.category == 'market_context':
                context['market_context'][entry.key] = entry.value
            elif entry.category == 'trade_history':
                context['recent_trades'].append(entry.value)
            elif entry.category == 'pattern':
                context['patterns'].append(entry.value)
        
        return context
    
    def store_user_preference(self, key: str, value: Any) -> str:
        """Store a user preference (long-term)"""
        entry = MemoryEntry(
            level=MemoryLevel.LONG_TERM,
            category='user_preference',
            key=key,
            value=value,
        )
        return self.store(entry)
    
    def store_trade(self, trade_data: Dict[str, Any]) -> str:
        """Store a trade in history (medium-term)"""
        entry = MemoryEntry(
            level=MemoryLevel.MEDIUM_TERM,
            category='trade_history',
            key=f"trade_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            value=trade_data,
        )
        return self.store(entry)
    
    def store_market_context(self, key: str, value: Any) -> str:
        """Store market context (short-term)"""
        entry = MemoryEntry(
            level=MemoryLevel.SHORT_TERM,
            category='market_context',
            key=key,
            value=value,
        )
        return self.store(entry)
    
    def add_knowledge(self, node: KnowledgeNode, relationships: Optional[List[tuple]] = None) -> None:
        """Add knowledge to the graph"""
        self.knowledge_graph.add_node(node)
        
        if relationships:
            for to_node, relationship, weight in relationships:
                edge = KnowledgeEdge(
                    from_node=node.id,
                    to_node=to_node,
                    relationship=relationship,
                    weight=weight,
                )
                self.knowledge_graph.add_edge(edge)
        
        # Periodically save
        if len(self.knowledge_graph.nodes) % 10 == 0:
            self._save_knowledge_graph()
    
    def get_related_knowledge(self, node_id: str, relationship: str) -> List[KnowledgeNode]:
        """Get related knowledge nodes"""
        return self.knowledge_graph.get_related(node_id, relationship)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM memory_entries WHERE expires_at IS NOT NULL AND expires_at < ?',
            (datetime.utcnow().isoformat(),)
        )
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted} expired memory entries")
        return deleted
    
    def clear_short_term(self) -> None:
        """Clear short-term memory"""
        self.short_term.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT level, COUNT(*) FROM memory_entries GROUP BY level')
        level_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT category, COUNT(*) FROM memory_entries GROUP BY category')
        category_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'short_term_count': len(self.short_term),
            'level_counts': level_counts,
            'category_counts': category_counts,
            'knowledge_nodes': len(self.knowledge_graph.nodes),
            'knowledge_edges': len(self.knowledge_graph.edges),
        }
