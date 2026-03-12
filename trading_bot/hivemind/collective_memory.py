"""
Collective Memory for Hivemind
============================================================

Shared knowledge base that all nodes can access and contribute to.
Enables emergent learning and pattern recognition across the swarm.
"""

import logging
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SharedKnowledge:
    """A piece of shared knowledge in the collective memory"""
    id: str = ""
    knowledge_type: str = ""  # pattern, correlation, regime, rule
    content: Dict[str, Any] = field(default_factory=dict)
    source_nodes: List[str] = field(default_factory=list)
    confidence: float = 0.5
    usage_count: int = 0
    success_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            content_str = json.dumps(self.content, sort_keys=True)
            self.id = hashlib.md5(content_str.encode()).hexdigest()[:12]
    
    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.5
        return self.success_count / self.usage_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'knowledge_type': self.knowledge_type,
            'content': self.content,
            'source_nodes': self.source_nodes,
            'confidence': self.confidence,
            'usage_count': self.usage_count,
            'success_count': self.success_count,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class EmergentPattern:
    """A pattern that emerged from collective analysis"""
    id: str = ""
    pattern_type: str = ""  # technical, fundamental, sentiment, cross_asset
    description: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    outcome: str = ""  # bullish, bearish, neutral
    confidence: float = 0.5
    occurrences: int = 0
    successful_predictions: int = 0
    contributing_nodes: List[str] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    timeframes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"pattern_{hashlib.md5(self.description.encode()).hexdigest()[:8]}"
    
    @property
    def accuracy(self) -> float:
        if self.occurrences == 0:
            return 0.5
        return self.successful_predictions / self.occurrences
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'pattern_type': self.pattern_type,
            'description': self.description,
            'conditions': self.conditions,
            'outcome': self.outcome,
            'confidence': self.confidence,
            'occurrences': self.occurrences,
            'accuracy': self.accuracy,
            'symbols': self.symbols,
        }


class CollectiveMemory:
    """
    Shared memory system for the hivemind.
    
    Features:
    - Shared knowledge base accessible by all nodes
    - Emergent pattern storage
    - Learning from collective outcomes
    - Knowledge decay for outdated information
    """
    
    def __init__(self, db_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.db_path = db_path or "hivemind_memory.db"
        
        # In-memory caches
        self.knowledge_cache: Dict[str, SharedKnowledge] = {}
        self.pattern_cache: Dict[str, EmergentPattern] = {}
        
        # Recent decisions for learning
        self.recent_decisions: List[Dict[str, Any]] = []
        
        # Initialize database
        self._init_db()
        self._load_cache()
    
    def _init_db(self) -> None:
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Shared knowledge table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_knowledge (
                id TEXT PRIMARY KEY,
                knowledge_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source_nodes TEXT,
                confidence REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_used TEXT
            )
        ''')
        
        # Emergent patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emergent_patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                description TEXT NOT NULL,
                conditions TEXT,
                outcome TEXT,
                confidence REAL DEFAULT 0.5,
                occurrences INTEGER DEFAULT 0,
                successful_predictions INTEGER DEFAULT 0,
                contributing_nodes TEXT,
                symbols TEXT,
                timeframes TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Decision history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decision_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                direction TEXT NOT NULL,
                consensus_score REAL,
                confidence REAL,
                outcome TEXT,
                profit REAL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_type ON shared_knowledge(knowledge_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pattern_type ON emergent_patterns(pattern_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decision_symbol ON decision_history(symbol)')
        
        conn.commit()
        conn.close()
    
    def _load_cache(self) -> None:
        """Load frequently used data into cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load recent knowledge
            cursor.execute('''
                SELECT * FROM shared_knowledge 
                ORDER BY usage_count DESC 
                LIMIT 100
            ''')
            
            for row in cursor.fetchall():
                knowledge = SharedKnowledge(
                    id=row[0],
                    knowledge_type=row[1],
                    content=json.loads(row[2]),
                    source_nodes=json.loads(row[3]) if row[3] else [],
                    confidence=row[4],
                    usage_count=row[5],
                    success_count=row[6],
                    created_at=datetime.fromisoformat(row[7]),
                    last_used=datetime.fromisoformat(row[8]) if row[8] else None,
                )
                self.knowledge_cache[knowledge.id] = knowledge
            
            # Load patterns
            cursor.execute('''
                SELECT * FROM emergent_patterns 
                ORDER BY occurrences DESC 
                LIMIT 50
            ''')
            
            for row in cursor.fetchall():
                pattern = EmergentPattern(
                    id=row[0],
                    pattern_type=row[1],
                    description=row[2],
                    conditions=json.loads(row[3]) if row[3] else {},
                    outcome=row[4],
                    confidence=row[5],
                    occurrences=row[6],
                    successful_predictions=row[7],
                    contributing_nodes=json.loads(row[8]) if row[8] else [],
                    symbols=json.loads(row[9]) if row[9] else [],
                    timeframes=json.loads(row[10]) if row[10] else [],
                    created_at=datetime.fromisoformat(row[11]),
                )
                self.pattern_cache[pattern.id] = pattern
            
            conn.close()
            logger.info(f"Loaded {len(self.knowledge_cache)} knowledge items and {len(self.pattern_cache)} patterns")
            
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
    
    def store_knowledge(self, knowledge: SharedKnowledge) -> str:
        """Store a piece of shared knowledge"""
        # Add to cache
        self.knowledge_cache[knowledge.id] = knowledge
        
        # Persist to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO shared_knowledge 
            (id, knowledge_type, content, source_nodes, confidence, usage_count, success_count, created_at, last_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            knowledge.id,
            knowledge.knowledge_type,
            json.dumps(knowledge.content),
            json.dumps(knowledge.source_nodes),
            knowledge.confidence,
            knowledge.usage_count,
            knowledge.success_count,
            knowledge.created_at.isoformat(),
            knowledge.last_used.isoformat() if knowledge.last_used else None,
        ))
        
        conn.commit()
        conn.close()
        
        return knowledge.id
    
    def get_knowledge(self, knowledge_id: str) -> Optional[SharedKnowledge]:
        """Retrieve a piece of knowledge"""
        if knowledge_id in self.knowledge_cache:
            knowledge = self.knowledge_cache[knowledge_id]
            knowledge.usage_count += 1
            knowledge.last_used = datetime.utcnow()
            return knowledge
        
        # Try database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM shared_knowledge WHERE id = ?', (knowledge_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            knowledge = SharedKnowledge(
                id=row[0],
                knowledge_type=row[1],
                content=json.loads(row[2]),
                source_nodes=json.loads(row[3]) if row[3] else [],
                confidence=row[4],
                usage_count=row[5] + 1,
                success_count=row[6],
                created_at=datetime.fromisoformat(row[7]),
                last_used=datetime.utcnow(),
            )
            self.knowledge_cache[knowledge.id] = knowledge
            return knowledge
        
        return None
    
    def query_knowledge(
        self,
        knowledge_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 20,
    ) -> List[SharedKnowledge]:
        """Query knowledge base"""
        results = []
        
        for knowledge in self.knowledge_cache.values():
            if knowledge_type and knowledge.knowledge_type != knowledge_type:
                continue
            if knowledge.confidence < min_confidence:
                continue
            results.append(knowledge)
        
        # Sort by success rate and usage
        results.sort(key=lambda k: (k.success_rate, k.usage_count), reverse=True)
        
        return results[:limit]
    
    def store_pattern(self, pattern: EmergentPattern) -> str:
        """Store an emergent pattern"""
        # Check if similar pattern exists
        existing = self._find_similar_pattern(pattern)
        if existing:
            # Merge with existing
            existing.occurrences += 1
            existing.confidence = (existing.confidence + pattern.confidence) / 2
            existing.contributing_nodes = list(set(existing.contributing_nodes + pattern.contributing_nodes))
            pattern = existing
        
        self.pattern_cache[pattern.id] = pattern
        
        # Persist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO emergent_patterns 
            (id, pattern_type, description, conditions, outcome, confidence, occurrences, 
             successful_predictions, contributing_nodes, symbols, timeframes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.id,
            pattern.pattern_type,
            pattern.description,
            json.dumps(pattern.conditions),
            pattern.outcome,
            pattern.confidence,
            pattern.occurrences,
            pattern.successful_predictions,
            json.dumps(pattern.contributing_nodes),
            json.dumps(pattern.symbols),
            json.dumps(pattern.timeframes),
            pattern.created_at.isoformat(),
        ))
        
        conn.commit()
        conn.close()
        
        return pattern.id
    
    def _find_similar_pattern(self, pattern: EmergentPattern) -> Optional[EmergentPattern]:
        """Find a similar existing pattern"""
        for existing in self.pattern_cache.values():
            if existing.pattern_type != pattern.pattern_type:
                continue
            if existing.outcome != pattern.outcome:
                continue
            
            # Check condition similarity
            if existing.conditions == pattern.conditions:
                return existing
        
        return None
    
    def get_relevant_patterns(
        self,
        symbol: str,
        market_conditions: Dict[str, Any],
        limit: int = 10,
    ) -> List[EmergentPattern]:
        """Get patterns relevant to current conditions"""
        relevant = []
        
        for pattern in self.pattern_cache.values():
            # Check symbol match
            if pattern.symbols and symbol not in pattern.symbols:
                continue
            
            # Check condition match
            match_score = self._calculate_condition_match(pattern.conditions, market_conditions)
            if match_score > 0.5:
                relevant.append((pattern, match_score))
        
        # Sort by match score and accuracy
        relevant.sort(key=lambda x: (x[1], x[0].accuracy), reverse=True)
        
        return [p for p, _ in relevant[:limit]]
    
    def _calculate_condition_match(
        self,
        pattern_conditions: Dict[str, Any],
        market_conditions: Dict[str, Any],
    ) -> float:
        """Calculate how well market conditions match pattern conditions"""
        if not pattern_conditions:
            return 0.5
        
        matches = 0
        total = len(pattern_conditions)
        
        for key, expected in pattern_conditions.items():
            actual = market_conditions.get(key)
            if actual is None:
                continue
            
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                # Numeric comparison with tolerance
                if abs(expected - actual) / max(abs(expected), 1) < 0.2:
                    matches += 1
            elif expected == actual:
                matches += 1
        
        return matches / total if total > 0 else 0.5
    
    def record_decision(
        self,
        symbol: str,
        action: str,
        direction: str,
        consensus_score: float,
        confidence: float,
    ) -> None:
        """Record a decision for later learning"""
        self.recent_decisions.append({
            'symbol': symbol,
            'action': action,
            'direction': direction,
            'consensus_score': consensus_score,
            'confidence': confidence,
            'timestamp': datetime.utcnow(),
            'outcome': None,
            'profit': None,
        })
        
        # Persist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO decision_history 
            (symbol, action, direction, consensus_score, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            action,
            direction,
            consensus_score,
            confidence,
            datetime.utcnow().isoformat(),
        ))
        
        conn.commit()
        conn.close()
        
        # Trim recent decisions
        if len(self.recent_decisions) > 100:
            self.recent_decisions = self.recent_decisions[-50:]
    
    def record_outcome(
        self,
        symbol: str,
        was_correct: bool,
        profit: float,
    ) -> None:
        """Record the outcome of a decision"""
        # Update recent decisions
        for decision in reversed(self.recent_decisions):
            if decision['symbol'] == symbol and decision['outcome'] is None:
                decision['outcome'] = 'correct' if was_correct else 'incorrect'
                decision['profit'] = profit
                break
        
        # Update knowledge success rates
        for knowledge in self.knowledge_cache.values():
            if symbol in str(knowledge.content):
                knowledge.usage_count += 1
                if was_correct:
                    knowledge.success_count += 1
        
        # Update pattern success rates
        for pattern in self.pattern_cache.values():
            if symbol in pattern.symbols or not pattern.symbols:
                pattern.occurrences += 1
                if was_correct:
                    pattern.successful_predictions += 1
    
    def learn_from_history(self) -> List[EmergentPattern]:
        """Analyze history to discover new patterns"""
        new_patterns = []
        
        # Get recent successful decisions
        successful = [d for d in self.recent_decisions if d.get('outcome') == 'correct']
        
        if len(successful) < 5:
            return new_patterns
        
        # Look for common conditions in successful decisions
        # This is a simplified pattern discovery
        symbols = {}
        for decision in successful:
            symbol = decision['symbol']
            symbols[symbol] = symbols.get(symbol, 0) + 1
        
        # If a symbol has many successful decisions, create a pattern
        for symbol, count in symbols.items():
            if count >= 3:
                pattern = EmergentPattern(
                    pattern_type='success_cluster',
                    description=f"Successful trading cluster for {symbol}",
                    conditions={'symbol': symbol},
                    outcome='bullish',  # Simplified
                    confidence=count / len(successful),
                    occurrences=count,
                    successful_predictions=count,
                    symbols=[symbol],
                )
                new_patterns.append(pattern)
                self.store_pattern(pattern)
        
        return new_patterns
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collective memory statistics"""
        return {
            'knowledge_count': len(self.knowledge_cache),
            'pattern_count': len(self.pattern_cache),
            'recent_decisions': len(self.recent_decisions),
            'avg_knowledge_success_rate': sum(k.success_rate for k in self.knowledge_cache.values()) / max(len(self.knowledge_cache), 1),
            'avg_pattern_accuracy': sum(p.accuracy for p in self.pattern_cache.values()) / max(len(self.pattern_cache), 1),
        }
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Remove old, unused data"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        removed = 0
        
        # Remove old knowledge
        to_remove = []
        for kid, knowledge in self.knowledge_cache.items():
            if knowledge.last_used and knowledge.last_used < cutoff:
                if knowledge.success_rate < 0.4:
                    to_remove.append(kid)
        
        for kid in to_remove:
            del self.knowledge_cache[kid]
            removed += 1
        
        logger.info(f"Cleaned up {removed} old knowledge items")
        return removed
