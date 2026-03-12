"""
Long-Term & Short-Term Memory Systems
Persistent market lessons, rules, and recent trade memory
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import pickle
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memories"""
    MARKET_LESSON = "market_lesson"
    TRADING_RULE = "trading_rule"
    PATTERN = "pattern"
    REGIME_BEHAVIOR = "regime_behavior"
    MISTAKE = "mistake"
    SUCCESS = "success"
    CORRELATION = "correlation"
    ANOMALY = "anomaly"


class MemoryImportance(Enum):
    """Memory importance levels"""
    CRITICAL = "critical"  # Never forget
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TEMPORARY = "temporary"


@dataclass
class LongTermMemory:
    """Persistent memory that lasts forever"""
    memory_id: str
    memory_type: MemoryType
    content: str
    
    # Context
    market_regime: str
    asset_class: str
    timeframe: str
    
    # Validation
    times_validated: int = 0
    times_invalidated: int = 0
    confidence: float = 0.5
    
    # Importance
    importance: MemoryImportance = MemoryImportance.MEDIUM
    
    # Lifecycle
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    
    # Connections
    related_memories: List[str] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ShortTermMemory:
    """Recent memory that fades over time"""
    memory_id: str
    trade_id: str
    
    # Trade details
    action: str  # BUY, SELL
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    
    # Outcome
    pnl: Optional[float]
    outcome: Optional[str]  # WIN, LOSS, BREAKEVEN
    
    # Context
    market_condition: str
    signals_used: List[str]
    conviction: float
    
    # Analysis
    what_worked: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    lessons: List[str] = field(default_factory=list)
    
    # Timing
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    
    # Decay
    decay_factor: float = 1.0  # Fades over time


@dataclass
class MarketLesson:
    """A lesson learned from the market"""
    lesson_id: str
    title: str
    description: str
    
    # When learned
    learned_from: str  # Trade ID or event
    learned_at: datetime
    
    # Validation
    times_applied: int = 0
    success_rate: float = 0.0
    
    # Cost of learning
    cost_to_learn: float = 0.0  # PnL lost to learn this
    
    # Application
    applicable_regimes: List[str] = field(default_factory=list)
    applicable_conditions: Dict[str, Any] = field(default_factory=dict)


class MemoryConsolidation:
    """
    Consolidates short-term memories into long-term knowledge
    """
    
    def __init__(self):
        self.consolidation_threshold = 3  # Need 3 confirmations
        self.pending_consolidations: Dict[str, List[str]] = defaultdict(list)
    
    def should_consolidate(self, pattern: str, short_term_memories: List[ShortTermMemory]) -> bool:
        """Check if pattern appears enough to consolidate"""
        
        count = sum(1 for mem in short_term_memories if pattern in mem.what_worked)
        
        return count >= self.consolidation_threshold
    
    def consolidate(self, short_term_memories: List[ShortTermMemory]) -> List[LongTermMemory]:
        """Consolidate short-term memories into long-term knowledge"""
        
        consolidated = []
        
        # Extract patterns that appear multiple times
        all_patterns = []
        for mem in short_term_memories:
            all_patterns.extend(mem.what_worked)
        
        # Count frequency
        from collections import Counter
        pattern_counts = Counter(all_patterns)
        
        # Consolidate frequent patterns
        for pattern, count in pattern_counts.items():
            if count >= self.consolidation_threshold:
                # Create long-term memory
                ltm = LongTermMemory(
                    memory_id=f"ltm_{hash(pattern) % 1000000}",
                    memory_type=MemoryType.PATTERN,
                    content=pattern,
                    market_regime="general",
                    asset_class="general",
                    timeframe="general",
                    times_validated=count,
                    confidence=min(1.0, count / 10),
                    importance=MemoryImportance.HIGH if count >= 5 else MemoryImportance.MEDIUM
                )
                
                consolidated.append(ltm)
        
        return consolidated


class MemorySystem:
    """
    Complete memory system with long-term and short-term memory
    """
    
    def __init__(self, max_short_term: int = 1000, max_long_term: int = 100000):
        # Long-term memory (persistent)
        self.long_term_memory: Dict[str, LongTermMemory] = {}
        
        # Short-term memory (recent trades)
        self.short_term_memory: deque = deque(maxlen=max_short_term)
        
        # Market lessons
        self.market_lessons: Dict[str, MarketLesson] = {}
        
        # Trading rules
        self.trading_rules: Dict[str, str] = {}
        
        # Memory consolidation
        self.consolidator = MemoryConsolidation()
        
        # Memory decay
        self.decay_rate = 0.01  # 1% per day
        
        # Statistics
        self.total_memories_created = 0
        self.total_memories_forgotten = 0
        
        logger.info("Memory System initialized")
    
    def store_trade_memory(self, trade_data: Dict[str, Any]) -> ShortTermMemory:
        """Store a trade in short-term memory"""
        
        memory = ShortTermMemory(
            memory_id=f"stm_{self.total_memories_created}",
            trade_id=trade_data.get('trade_id', 'unknown'),
            action=trade_data.get('action', 'UNKNOWN'),
            entry_price=trade_data.get('entry_price', 0.0),
            exit_price=trade_data.get('exit_price'),
            position_size=trade_data.get('position_size', 0.0),
            pnl=trade_data.get('pnl'),
            outcome=trade_data.get('outcome'),
            market_condition=trade_data.get('market_condition', 'unknown'),
            signals_used=trade_data.get('signals_used', []),
            conviction=trade_data.get('conviction', 0.0),
            what_worked=trade_data.get('what_worked', []),
            what_failed=trade_data.get('what_failed', []),
            lessons=trade_data.get('lessons', [])
        )
        
        self.short_term_memory.append(memory)
        self.total_memories_created += 1
        
        logger.info(f"Stored trade memory: {memory.trade_id}")
        
        return memory
    
    def store_market_lesson(self, lesson: MarketLesson):
        """Store a market lesson in long-term memory"""
        
        self.market_lessons[lesson.lesson_id] = lesson
        
        # Also create long-term memory
        ltm = LongTermMemory(
            memory_id=f"ltm_lesson_{lesson.lesson_id}",
            memory_type=MemoryType.MARKET_LESSON,
            content=lesson.description,
            market_regime="general",
            asset_class="general",
            timeframe="general",
            importance=MemoryImportance.CRITICAL,
            notes=f"Cost to learn: ${lesson.cost_to_learn:.2f}"
        )
        
        self.long_term_memory[ltm.memory_id] = ltm
        
        logger.info(f"Stored market lesson: {lesson.title}")
    
    def store_trading_rule(self, rule_id: str, rule: str, importance: MemoryImportance = MemoryImportance.HIGH):
        """Store a trading rule"""
        
        self.trading_rules[rule_id] = rule
        
        # Create long-term memory
        ltm = LongTermMemory(
            memory_id=f"ltm_rule_{rule_id}",
            memory_type=MemoryType.TRADING_RULE,
            content=rule,
            market_regime="general",
            asset_class="general",
            timeframe="general",
            importance=importance
        )
        
        self.long_term_memory[ltm.memory_id] = ltm
        
        logger.info(f"Stored trading rule: {rule_id}")
    
    def recall_similar_situations(self, current_situation: Dict[str, Any], 
                                 n: int = 5) -> List[ShortTermMemory]:
        """
        Recall similar past situations from short-term memory
        """
        
        current_regime = current_situation.get('regime', 'unknown')
        current_volatility = current_situation.get('volatility', 0.0)
        
        # Find similar memories
        similar = []
        
        for memory in self.short_term_memory:
            similarity_score = 0.0
            
            # Check regime match
            if memory.market_condition == current_regime:
                similarity_score += 0.5
            
            # Check if signals overlap
            current_signals = set(current_situation.get('signals', []))
            memory_signals = set(memory.signals_used)
            
            if current_signals & memory_signals:
                overlap = len(current_signals & memory_signals) / len(current_signals | memory_signals)
                similarity_score += overlap * 0.5
            
            if similarity_score > 0.3:
                similar.append((similarity_score, memory))
        
        # Sort by similarity and return top N
        similar.sort(key=lambda x: x[0], reverse=True)
        
        return [mem for _, mem in similar[:n]]
    
    def recall_lessons_for_regime(self, regime: str) -> List[MarketLesson]:
        """Recall lessons applicable to current regime"""
        
        applicable = []
        
        for lesson in self.market_lessons.values():
            if not lesson.applicable_regimes or regime in lesson.applicable_regimes:
                applicable.append(lesson)
        
        # Sort by success rate
        applicable.sort(key=lambda x: x.success_rate, reverse=True)
        
        return applicable
    
    def consolidate_memories(self):
        """
        Consolidate short-term memories into long-term knowledge
        """
        
        # Convert deque to list for processing
        stm_list = list(self.short_term_memory)
        
        # Consolidate
        new_ltm = self.consolidator.consolidate(stm_list)
        
        # Store consolidated memories
        for ltm in new_ltm:
            self.long_term_memory[ltm.memory_id] = ltm
        
        logger.info(f"Consolidated {len(new_ltm)} short-term memories into long-term knowledge")
        
        return len(new_ltm)
    
    def apply_memory_decay(self):
        """
        Apply decay to short-term memories
        Older memories fade
        """
        
        now = datetime.now()
        
        for memory in self.short_term_memory:
            # Calculate age in days
            age_days = (now - memory.entry_time).days
            
            # Apply decay
            memory.decay_factor = max(0.0, 1.0 - (age_days * self.decay_rate))
    
    def forget_weak_memories(self, confidence_threshold: float = 0.3):
        """
        Forget long-term memories with low confidence
        """
        
        to_forget = []
        
        for memory_id, memory in self.long_term_memory.items():
            # Don't forget critical memories
            if memory.importance == MemoryImportance.CRITICAL:
                continue
            
            # Calculate confidence
            if memory.times_validated + memory.times_invalidated > 0:
                confidence = memory.times_validated / (memory.times_validated + memory.times_invalidated)
                
                if confidence < confidence_threshold:
                    to_forget.append(memory_id)
        
        # Forget
        for memory_id in to_forget:
            del self.long_term_memory[memory_id]
            self.total_memories_forgotten += 1
        
        logger.info(f"Forgot {len(to_forget)} weak memories")
        
        return len(to_forget)
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        
        return {
            'long_term_memories': len(self.long_term_memory),
            'short_term_memories': len(self.short_term_memory),
            'market_lessons': len(self.market_lessons),
            'trading_rules': len(self.trading_rules),
            'total_created': self.total_memories_created,
            'total_forgotten': self.total_memories_forgotten,
            'memory_by_type': self._count_by_type(),
            'memory_by_importance': self._count_by_importance()
        }
    
    def save_to_disk(self, filepath: str):
        """Save memory system to disk"""
        
        data = {
            'long_term_memory': self.long_term_memory,
            'market_lessons': self.market_lessons,
            'trading_rules': self.trading_rules,
            'statistics': self.get_memory_statistics()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Saved memory system to {filepath}")
    
    def load_from_disk(self, filepath: str):
        """Load memory system from disk"""
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.long_term_memory = data.get('long_term_memory', {})
            self.market_lessons = data.get('market_lessons', {})
            self.trading_rules = data.get('trading_rules', {})
            
            logger.info(f"Loaded memory system from {filepath}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load memory system: {e}")
            return False
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count memories by type"""
        
        counts = defaultdict(int)
        for memory in self.long_term_memory.values():
            counts[memory.memory_type.value] += 1
        
        return dict(counts)
    
    def _count_by_importance(self) -> Dict[str, int]:
        """Count memories by importance"""
        
        counts = defaultdict(int)
        for memory in self.long_term_memory.values():
            counts[memory.importance.value] += 1
        
        return dict(counts)


# Example usage
if __name__ == "__main__":
    # Initialize memory system
    memory = MemorySystem()
    
    print("="*80)
    logger.info("MEMORY SYSTEM - LONG-TERM & SHORT-TERM")
    print("="*80)
    
    # 1. Store some trades in short-term memory
    logger.info("\n1. Storing trades in short-term memory...")
    
    for i in range(10):
        trade_data = {
            'trade_id': f'T{i+1:03d}',
            'action': np.random.choice(['BUY', 'SELL']),
            'entry_price': 100 + np.random.randn(),
            'exit_price': 100 + np.random.randn() + np.random.choice([1, -1]),
            'position_size': 1.0,
            'pnl': np.random.randn() * 100,
            'outcome': np.random.choice(['WIN', 'LOSS']),
            'market_condition': np.random.choice(['trending', 'ranging']),
            'signals_used': ['momentum', 'volume'],
            'conviction': 70 + np.random.rand() * 30,
            'what_worked': ['trend_following'] if i % 3 == 0 else [],
            'what_failed': ['mean_reversion'] if i % 4 == 0 else []
        }
        
        memory.store_trade_memory(trade_data)
    
    logger.info(f"   Stored {len(memory.short_term_memory)} trades")
    
    # 2. Store market lessons
    logger.info("\n2. Storing market lessons...")
    
    lesson = MarketLesson(
        lesson_id="L001",
        title="Don't fight the Fed",
        description="When Fed is hawkish, avoid aggressive longs",
        learned_from="T005",
        learned_at=datetime.now(),
        cost_to_learn=500.0,
        applicable_regimes=['trending_down', 'ranging']
    )
    
    memory.store_market_lesson(lesson)
    logger.info(f"   Stored lesson: {lesson.title}")
    
    # 3. Store trading rules
    logger.info("\n3. Storing trading rules...")
    
    rules = [
        ("R001", "Cut losses at 2% max", MemoryImportance.CRITICAL),
        ("R002", "Take profits at 5%", MemoryImportance.HIGH),
        ("R003", "Trade with trend", MemoryImportance.HIGH)
    ]
    
    for rule_id, rule, importance in rules:
        memory.store_trading_rule(rule_id, rule, importance)
    
    logger.info(f"   Stored {len(rules)} trading rules")
    
    # 4. Recall similar situations
    logger.info("\n4. Recalling similar situations...")
    
    current_situation = {
        'regime': 'trending',
        'volatility': 0.02,
        'signals': ['momentum', 'volume']
    }
    
    similar = memory.recall_similar_situations(current_situation, n=3)
    logger.info(f"   Found {len(similar)} similar past situations")
    
    for mem in similar:
        logger.info(f"     - Trade {mem.trade_id}: {mem.action} with {mem.outcome}")
    
    # 5. Consolidate memories
    logger.info("\n5. Consolidating short-term memories...")
    
    consolidated = memory.consolidate_memories()
    logger.info(f"   Consolidated {consolidated} patterns into long-term memory")
    
    # 6. Get statistics
    logger.info("\n6. Memory Statistics:")
    stats = memory.get_memory_statistics()
    
    logger.info(f"   Long-term memories: {stats['long_term_memories']}")
    logger.info(f"   Short-term memories: {stats['short_term_memories']}")
    logger.info(f"   Market lessons: {stats['market_lessons']}")
    logger.info(f"   Trading rules: {stats['trading_rules']}")
    
    logger.info("\n   Memory by type:")
    for mem_type, count in stats['memory_by_type'].items():
        logger.info(f"     {mem_type}: {count}")
    
    logger.info("\n   Memory by importance:")
    for importance, count in stats['memory_by_importance'].items():
        logger.info(f"     {importance}: {count}")
    
    print("\n" + "="*80)
    logger.info("MEMORY SYSTEM OPERATIONAL")
    print("="*80)
