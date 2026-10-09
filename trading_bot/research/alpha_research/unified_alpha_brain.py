"""
Unified AlphaBrain
==================
All strategies share one memory - unified intelligence system.

Features:
- Shared memory across all strategies
- Cross-strategy learning
- Unified signal aggregation
- Memory-based pattern recognition
- Experience replay for strategies
- Collective intelligence

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import json
import pickle
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import deque
import threading
import sqlite3
import uuid

import numpy as np
import pandas as pd

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memories stored"""
    TRADE = auto()
    PATTERN = auto()
    REGIME = auto()
    SIGNAL = auto()
    PERFORMANCE = auto()
    MARKET_STATE = auto()
    STRATEGY_STATE = auto()
    LESSON = auto()


class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_WEAK = auto()
    WEAK = auto()
    MODERATE = auto()
    STRONG = auto()
    VERY_STRONG = auto()


@dataclass
class Memory:
    """Single memory unit"""
    memory_id: str
    memory_type: MemoryType
    timestamp: datetime
    
    # Content
    content: Dict[str, Any]
    
    # Metadata
    source_strategy: str = ""
    symbol: str = ""
    timeframe: str = ""
    
    # Importance and relevance
    importance: float = 0.5
    relevance_decay: float = 0.99  # Per day
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    # Associations
    related_memories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class StrategySignal:
    """Signal from a strategy"""
    signal_id: str
    strategy_name: str
    timestamp: datetime
    
    # Signal details
    symbol: str
    direction: str  # 'long', 'short', 'neutral'
    strength: SignalStrength
    confidence: float
    
    # Entry/Exit
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Reasoning
    reasoning: str = ""
    supporting_factors: List[str] = field(default_factory=list)
    
    # Performance tracking
    outcome: Optional[str] = None
    pnl: float = 0.0


@dataclass
class CollectiveDecision:
    """Unified decision from all strategies"""
    decision_id: str
    timestamp: datetime
    symbol: str
    
    # Aggregated signal
    direction: str
    strength: SignalStrength
    confidence: float
    
    # Contributing signals
    contributing_signals: List[StrategySignal] = field(default_factory=list)
    
    # Consensus metrics
    agreement_ratio: float = 0.0
    weighted_confidence: float = 0.0
    
    # Execution parameters
    position_size: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0


class SharedMemoryStore:
    """Persistent shared memory storage"""
    
    def __init__(self, db_path: str = "alpha_brain_memory.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                memory_type TEXT,
                timestamp TEXT,
                content TEXT,
                source_strategy TEXT,
                symbol TEXT,
                timeframe TEXT,
                importance REAL,
                access_count INTEGER,
                last_accessed TEXT,
                tags TEXT
            )
        ''')
        
        # Signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                strategy_name TEXT,
                timestamp TEXT,
                symbol TEXT,
                direction TEXT,
                strength TEXT,
                confidence REAL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                reasoning TEXT,
                outcome TEXT,
                pnl REAL
            )
        ''')
        
        # Patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT,
                pattern_data TEXT,
                success_rate REAL,
                occurrence_count INTEGER,
                last_seen TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_memory(self, memory: Memory):
        """Store a memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO memories 
            (memory_id, memory_type, timestamp, content, source_strategy, 
             symbol, timeframe, importance, access_count, last_accessed, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory.memory_id,
            memory.memory_type.name,
            memory.timestamp.isoformat(),
            json.dumps(memory.content),
            memory.source_strategy,
            memory.symbol,
            memory.timeframe,
            memory.importance,
            memory.access_count,
            memory.last_accessed.isoformat(),
            json.dumps(memory.tags)
        ))
        
        conn.commit()
        conn.close()
    
    def retrieve_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        symbol: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 100
    ) -> List[Memory]:
        """Retrieve memories matching criteria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM memories WHERE importance >= ?"
        params = [min_importance]
        
        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type.name)
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            memories.append(Memory(
                memory_id=row[0],
                memory_type=MemoryType[row[1]],
                timestamp=datetime.fromisoformat(row[2]),
                content=json.loads(row[3]),
                source_strategy=row[4],
                symbol=row[5],
                timeframe=row[6],
                importance=row[7],
                access_count=row[8],
                last_accessed=datetime.fromisoformat(row[9]),
                tags=json.loads(row[10])
            ))
        
        return memories
    
    def store_signal(self, signal: StrategySignal):
        """Store a strategy signal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO signals
            (signal_id, strategy_name, timestamp, symbol, direction, strength,
             confidence, entry_price, stop_loss, take_profit, reasoning, outcome, pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal.signal_id,
            signal.strategy_name,
            signal.timestamp.isoformat(),
            signal.symbol,
            signal.direction,
            signal.strength.name,
            signal.confidence,
            signal.entry_price,
            signal.stop_loss,
            signal.take_profit,
            signal.reasoning,
            signal.outcome,
            signal.pnl
        ))
        
        conn.commit()
        conn.close()
    
    def get_strategy_performance(self, strategy_name: str) -> Dict[str, float]:
        """Get strategy performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT outcome, pnl FROM signals 
            WHERE strategy_name = ? AND outcome IS NOT NULL
        ''', (strategy_name,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {'win_rate': 0.5, 'total_pnl': 0, 'trade_count': 0}
        
        wins = sum(1 for r in rows if r[0] == 'win')
        total_pnl = sum(r[1] for r in rows)
        
        return {
            'win_rate': wins / len(rows),
            'total_pnl': total_pnl,
            'trade_count': len(rows)
        }


class PatternRecognizer:
    """Pattern recognition from shared memory"""
    
    def __init__(self, memory_store: SharedMemoryStore):
        self.memory_store = memory_store
        self.pattern_cache: Dict[str, Dict] = {}
        
    def find_similar_patterns(
        self,
        current_state: Dict[str, Any],
        symbol: str,
        top_n: int = 5
    ) -> List[Tuple[Memory, float]]:
        """Find similar historical patterns"""
        
        # Get relevant memories
        memories = self.memory_store.retrieve_memories(
            memory_type=MemoryType.PATTERN,
            symbol=symbol,
            min_importance=0.3,
            limit=100
        )
        
        if not memories:
            return []
        
        # Calculate similarity scores
        similarities = []
        for memory in memories:
            similarity = self._calculate_similarity(current_state, memory.content)
            similarities.append((memory, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_n]
    
    def _calculate_similarity(
        self,
        state1: Dict[str, Any],
        state2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two states"""
        
        common_keys = set(state1.keys()) & set(state2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            v1, v2 = state1[key], state2[key]
            
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                # Numerical similarity
                max_val = max(abs(v1), abs(v2), 1)
                sim = 1 - abs(v1 - v2) / max_val
                similarities.append(sim)
            elif isinstance(v1, str) and isinstance(v2, str):
                # String similarity
                sim = 1.0 if v1 == v2 else 0.0
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def learn_pattern(
        self,
        pattern_state: Dict[str, Any],
        outcome: str,
        symbol: str,
        strategy: str
    ):
        """Learn from a pattern outcome"""
        
        # Create pattern memory
        memory = Memory(
            memory_id=str(uuid.uuid4())[:8],
            memory_type=MemoryType.PATTERN,
            timestamp=datetime.now(),
            content={
                'state': pattern_state,
                'outcome': outcome
            },
            source_strategy=strategy,
            symbol=symbol,
            importance=0.7 if outcome == 'win' else 0.5,
            tags=['pattern', outcome, symbol]
        )
        
        self.memory_store.store_memory(memory)


class ExperienceReplay:
    """Experience replay buffer for strategies"""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        self.priorities: deque = deque(maxlen=capacity)
        
    def add(
        self,
        state: Dict,
        action: str,
        reward: float,
        next_state: Dict,
        done: bool
    ):
        """Add experience to buffer"""
        
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'timestamp': datetime.now().isoformat()
        }
        
        # Priority based on reward magnitude
        priority = abs(reward) + 0.01
        
        self.buffer.append(experience)
        self.priorities.append(priority)
    
    def sample(self, batch_size: int) -> List[Dict]:
        """Sample experiences with priority"""
        
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        
        # Prioritized sampling
        priorities = np.array(self.priorities)
        probs = priorities / priorities.sum()
        
        indices = np.random.choice(len(self.buffer), batch_size, p=probs, replace=False)
        
        return [self.buffer[i] for i in indices]
    
    def get_statistics(self) -> Dict[str, float]:
        """Get buffer statistics"""
        
        if not self.buffer:
            return {'size': 0, 'avg_reward': 0, 'win_rate': 0}
        
        rewards = [e['reward'] for e in self.buffer]
        wins = sum(1 for r in rewards if r > 0)
        
        return {
            'size': len(self.buffer),
            'avg_reward': np.mean(rewards),
            'win_rate': wins / len(rewards),
            'max_reward': max(rewards),
            'min_reward': min(rewards)
        }


class StrategyWeightManager:
    """Manage strategy weights based on performance"""
    
    def __init__(self, memory_store: SharedMemoryStore):
        self.memory_store = memory_store
        self.weights: Dict[str, float] = {}
        self.min_weight = 0.1
        self.max_weight = 3.0
        
    def update_weights(self, strategies: List[str]):
        """Update strategy weights based on performance"""
        
        for strategy in strategies:
            perf = self.memory_store.get_strategy_performance(strategy)
            
            # Calculate weight from performance
            win_rate = perf['win_rate']
            trade_count = perf['trade_count']
            
            # Base weight from win rate
            base_weight = win_rate * 2  # 50% win rate = 1.0 weight
            
            # Confidence adjustment based on trade count
            confidence = min(trade_count / 50, 1.0)  # Full confidence at 50 trades
            
            # Final weight
            weight = 1.0 + (base_weight - 1.0) * confidence
            weight = np.clip(weight, self.min_weight, self.max_weight)
            
            self.weights[strategy] = weight
    
    def get_weight(self, strategy: str) -> float:
        """Get weight for a strategy"""
        return self.weights.get(strategy, 1.0)


class SignalAggregator:
    """Aggregate signals from multiple strategies"""
    
    def __init__(self, weight_manager: StrategyWeightManager):
        self.weight_manager = weight_manager
        
    def aggregate(
        self,
        signals: List[StrategySignal],
        symbol: str
    ) -> CollectiveDecision:
        """Aggregate multiple signals into collective decision"""
        
        if not signals:
            return self._neutral_decision(symbol)
        
        # Filter signals for this symbol
        symbol_signals = [s for s in signals if s.symbol == symbol]
        
        if not symbol_signals:
            return self._neutral_decision(symbol)
        
        # Calculate weighted votes
        long_score = 0.0
        short_score = 0.0
        neutral_score = 0.0
        total_weight = 0.0
        
        for signal in symbol_signals:
            weight = self.weight_manager.get_weight(signal.strategy_name)
            confidence_weight = weight * signal.confidence
            
            if signal.direction == 'long':
                long_score += confidence_weight
            elif signal.direction == 'short':
                short_score += confidence_weight
            else:
                neutral_score += confidence_weight
            
            total_weight += weight
        
        # Determine direction
        if long_score > short_score and long_score > neutral_score:
            direction = 'long'
            strength_score = long_score / total_weight
        elif short_score > long_score and short_score > neutral_score:
            direction = 'short'
            strength_score = short_score / total_weight
        else:
            direction = 'neutral'
            strength_score = neutral_score / total_weight
        
        # Determine strength
        if strength_score > 0.8:
            strength = SignalStrength.VERY_STRONG
        elif strength_score > 0.6:
            strength = SignalStrength.STRONG
        elif strength_score > 0.4:
            strength = SignalStrength.MODERATE
        elif strength_score > 0.2:
            strength = SignalStrength.WEAK
        else:
            strength = SignalStrength.VERY_WEAK
        
        # Calculate agreement ratio
        if direction == 'long':
            agreement = sum(1 for s in symbol_signals if s.direction == 'long') / len(symbol_signals)
        elif direction == 'short':
            agreement = sum(1 for s in symbol_signals if s.direction == 'short') / len(symbol_signals)
        else:
            agreement = sum(1 for s in symbol_signals if s.direction == 'neutral') / len(symbol_signals)
        
        # Aggregate entry/exit prices
        entry_prices = [s.entry_price for s in symbol_signals if s.entry_price and s.direction == direction]
        stop_losses = [s.stop_loss for s in symbol_signals if s.stop_loss and s.direction == direction]
        take_profits = [s.take_profit for s in symbol_signals if s.take_profit and s.direction == direction]
        
        return CollectiveDecision(
            decision_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=strength_score,
            contributing_signals=symbol_signals,
            agreement_ratio=agreement,
            weighted_confidence=strength_score,
            entry_price=np.median(entry_prices) if entry_prices else 0,
            stop_loss=np.median(stop_losses) if stop_losses else 0,
            take_profit=np.median(take_profits) if take_profits else 0
        )
    
    def _neutral_decision(self, symbol: str) -> CollectiveDecision:
        """Create neutral decision"""
        return CollectiveDecision(
            decision_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            symbol=symbol,
            direction='neutral',
            strength=SignalStrength.VERY_WEAK,
            confidence=0.0
        )


class LessonLearner:
    """Learn lessons from trading outcomes"""
    
    def __init__(self, memory_store: SharedMemoryStore):
        self.memory_store = memory_store
        
    def learn_from_trade(
        self,
        signal: StrategySignal,
        market_state: Dict[str, Any],
        outcome: str,
        pnl: float
    ):
        """Learn lesson from trade outcome"""
        
        # Create lesson memory
        lesson = {
            'signal': {
                'direction': signal.direction,
                'strength': signal.strength.name,
                'confidence': signal.confidence,
                'reasoning': signal.reasoning
            },
            'market_state': market_state,
            'outcome': outcome,
            'pnl': pnl,
            'lesson_type': 'win' if pnl > 0 else 'loss'
        }
        
        # Determine importance
        importance = 0.5
        if abs(pnl) > 0.02:  # Significant trade
            importance = 0.8
        if outcome == 'win' and signal.confidence < 0.5:
            importance = 0.9  # Surprising win
        if outcome == 'loss' and signal.confidence > 0.8:
            importance = 0.9  # Surprising loss
        
        memory = Memory(
            memory_id=str(uuid.uuid4())[:8],
            memory_type=MemoryType.LESSON,
            timestamp=datetime.now(),
            content=lesson,
            source_strategy=signal.strategy_name,
            symbol=signal.symbol,
            importance=importance,
            tags=['lesson', outcome, signal.strategy_name]
        )
        
        self.memory_store.store_memory(memory)
    
    def get_relevant_lessons(
        self,
        symbol: str,
        market_state: Dict[str, Any],
        top_n: int = 5
    ) -> List[Dict]:
        """Get relevant lessons for current situation"""
        
        memories = self.memory_store.retrieve_memories(
            memory_type=MemoryType.LESSON,
            symbol=symbol,
            min_importance=0.5,
            limit=50
        )
        
        if not memories:
            return []
        
        # Score by relevance
        scored = []
        for memory in memories:
            lesson_state = memory.content.get('market_state', {})
            similarity = self._calculate_state_similarity(market_state, lesson_state)
            scored.append((memory.content, similarity))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in scored[:top_n]]
    
    def _calculate_state_similarity(
        self,
        state1: Dict,
        state2: Dict
    ) -> float:
        """Calculate similarity between market states"""
        
        common_keys = set(state1.keys()) & set(state2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            v1, v2 = state1.get(key), state2.get(key)
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                max_val = max(abs(v1), abs(v2), 1)
                sim = 1 - abs(v1 - v2) / max_val
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0


class UnifiedAlphaBrain:
    """
    Unified AlphaBrain - All strategies share one memory.
    
    Features:
    - Shared memory across all strategies
    - Cross-strategy learning
    - Unified signal aggregation
    - Memory-based pattern recognition
    - Experience replay for strategies
    - Collective intelligence
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Storage
        db_path = self.config.get('db_path', 'alpha_brain_memory.db')
        self.memory_store = SharedMemoryStore(db_path)
        
        # Components
        self.pattern_recognizer = PatternRecognizer(self.memory_store)
        self.experience_replay = ExperienceReplay(capacity=10000)
        self.weight_manager = StrategyWeightManager(self.memory_store)
        self.signal_aggregator = SignalAggregator(self.weight_manager)
        self.lesson_learner = LessonLearner(self.memory_store)
        
        # Registered strategies
        self.strategies: Dict[str, Dict] = {}
        
        # Current signals
        self.pending_signals: List[StrategySignal] = []
        
        # State
        self._lock = threading.Lock()
        
        logger.info("UnifiedAlphaBrain initialized")
    
    def register_strategy(
        self,
        strategy_name: str,
        strategy_type: str,
        config: Dict = None
    ):
        """Register a strategy with the brain"""
        
        self.strategies[strategy_name] = {
            'type': strategy_type,
            'config': config or {},
            'registered_at': datetime.now(),
            'signal_count': 0
        }
        
        # Initialize weight
        self.weight_manager.weights[strategy_name] = 1.0
        
        logger.info(f"Registered strategy: {strategy_name}")
    
    def submit_signal(self, signal: StrategySignal):
        """Submit a signal from a strategy"""
        
        with self._lock:
            self.pending_signals.append(signal)
            
            # Store signal
            self.memory_store.store_signal(signal)
            
            # Update strategy stats
            if signal.strategy_name in self.strategies:
                self.strategies[signal.strategy_name]['signal_count'] += 1
    
    def get_collective_decision(self, symbol: str) -> CollectiveDecision:
        """Get collective decision for a symbol"""
        
        with self._lock:
            # Update weights
            self.weight_manager.update_weights(list(self.strategies.keys()))
            
            # Aggregate signals
            decision = self.signal_aggregator.aggregate(self.pending_signals, symbol)
            
            return decision
    
    def remember_market_state(
        self,
        symbol: str,
        state: Dict[str, Any],
        importance: float = 0.5
    ):
        """Store market state in memory"""
        
        memory = Memory(
            memory_id=str(uuid.uuid4())[:8],
            memory_type=MemoryType.MARKET_STATE,
            timestamp=datetime.now(),
            content=state,
            symbol=symbol,
            importance=importance,
            tags=['market_state', symbol]
        )
        
        self.memory_store.store_memory(memory)
    
    def recall_similar_situations(
        self,
        symbol: str,
        current_state: Dict[str, Any],
        top_n: int = 5
    ) -> List[Tuple[Memory, float]]:
        """Recall similar historical situations"""
        
        return self.pattern_recognizer.find_similar_patterns(
            current_state, symbol, top_n
        )
    
    def learn_from_outcome(
        self,
        signal: StrategySignal,
        market_state: Dict[str, Any],
        outcome: str,
        pnl: float
    ):
        """Learn from trade outcome"""
        
        # Update signal outcome
        signal.outcome = outcome
        signal.pnl = pnl
        self.memory_store.store_signal(signal)
        
        # Learn pattern
        self.pattern_recognizer.learn_pattern(
            market_state, outcome, signal.symbol, signal.strategy_name
        )
        
        # Learn lesson
        self.lesson_learner.learn_from_trade(signal, market_state, outcome, pnl)
        
        # Add to experience replay
        self.experience_replay.add(
            state=market_state,
            action=signal.direction,
            reward=pnl,
            next_state={},  # Would be filled with actual next state
            done=True
        )
    
    def get_lessons_for_situation(
        self,
        symbol: str,
        market_state: Dict[str, Any]
    ) -> List[Dict]:
        """Get relevant lessons for current situation"""
        
        return self.lesson_learner.get_relevant_lessons(symbol, market_state)
    
    def get_strategy_rankings(self) -> List[Tuple[str, float, Dict]]:
        """Get strategy rankings by performance"""
        
        rankings = []
        
        for strategy_name in self.strategies:
            perf = self.memory_store.get_strategy_performance(strategy_name)
            weight = self.weight_manager.get_weight(strategy_name)
            
            rankings.append((strategy_name, weight, perf))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def clear_pending_signals(self):
        """Clear pending signals after decision"""
        
        with self._lock:
            self.pending_signals = []
    
    def get_brain_status(self) -> Dict[str, Any]:
        """Get brain status"""
        
        return {
            'registered_strategies': len(self.strategies),
            'pending_signals': len(self.pending_signals),
            'experience_buffer': self.experience_replay.get_statistics(),
            'strategy_weights': dict(self.weight_manager.weights)
        }


# Factory function
def create_alpha_brain(config: Optional[Dict] = None) -> UnifiedAlphaBrain:
    """Create and return a UnifiedAlphaBrain instance"""
    return UnifiedAlphaBrain(config)
