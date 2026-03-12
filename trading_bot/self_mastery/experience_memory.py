"""
Experience Memory System

IF I WERE THIS BOT, I WOULD REMEMBER EVERYTHING:
- Every trade I made and why
- Every decision context (market state, signals, confidence)
- Every outcome (profit, loss, near-miss)
- Every mistake and what caused it
- Every success and what enabled it

This is my long-term memory - it persists across restarts and grows smarter over time.
"""

import json
import logging
import sqlite3
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ExperienceType(Enum):
    """Types of experiences I remember"""
    TRADE_EXECUTED = auto()      # I made a trade
    TRADE_SKIPPED = auto()       # I chose NOT to trade (equally important)
    SIGNAL_GENERATED = auto()    # I generated a signal
    RISK_TRIGGERED = auto()      # Risk management activated
    REGIME_DETECTED = auto()     # I detected a market regime change
    PREDICTION_MADE = auto()     # I made a prediction
    STRATEGY_SWITCHED = auto()   # I switched strategies
    ANOMALY_DETECTED = auto()    # I detected something unusual
    LESSON_LEARNED = auto()      # I learned something important
    MISTAKE_MADE = auto()        # I made a mistake (VERY important to remember)
    SUCCESS_ACHIEVED = auto()    # I achieved a success


class OutcomeQuality(Enum):
    """How good was the outcome?"""
    EXCELLENT = auto()    # Exceeded expectations significantly
    GOOD = auto()         # Met or slightly exceeded expectations
    NEUTRAL = auto()      # Neither good nor bad
    POOR = auto()         # Below expectations
    TERRIBLE = auto()     # Significantly below expectations, major loss
    UNKNOWN = auto()      # Outcome not yet known


@dataclass
class DecisionContext:
    """
    The complete context when I made a decision.
    This is crucial for understanding WHY I did what I did.
    """
    timestamp: datetime
    
    # Market state
    price: float
    volume: float
    volatility: float
    spread: float
    regime: str
    trend: str  # 'up', 'down', 'sideways'
    
    # My internal state
    confidence: float
    risk_level: float
    current_position: float
    unrealized_pnl: float
    drawdown: float
    
    # Signals I was seeing
    signals: Dict[str, float] = field(default_factory=dict)
    
    # Indicators I was using
    indicators: Dict[str, float] = field(default_factory=dict)
    
    # What strategies were active
    active_strategies: List[str] = field(default_factory=list)
    
    # Recent history (last N prices, returns, etc.)
    recent_prices: List[float] = field(default_factory=list)
    recent_returns: List[float] = field(default_factory=list)
    
    # External factors
    news_sentiment: float = 0.0
    market_fear_greed: float = 50.0
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'DecisionContext':
        d['timestamp'] = datetime.fromisoformat(d['timestamp'])
        return cls(**d)
    
    def to_feature_vector(self) -> np.ndarray:
        """Convert to numerical feature vector for ML"""
        features = [
            self.price,
            self.volume,
            self.volatility,
            self.spread,
            self.confidence,
            self.risk_level,
            self.current_position,
            self.unrealized_pnl,
            self.drawdown,
            self.news_sentiment,
            self.market_fear_greed,
        ]
        # Add signal values
        for signal in sorted(self.signals.keys()):
            features.append(self.signals[signal])
        # Add indicator values
        for indicator in sorted(self.indicators.keys()):
            features.append(self.indicators[indicator])
        return np.array(features)


@dataclass
class OutcomeAnalysis:
    """
    Analysis of what happened after my decision.
    This is how I learn from results.
    """
    # Timing
    decision_time: datetime
    outcome_time: datetime
    duration_seconds: float
    
    # Financial outcome
    pnl: float
    pnl_percent: float
    max_favorable_excursion: float  # Best it got
    max_adverse_excursion: float    # Worst it got
    
    # Quality assessment
    quality: OutcomeQuality
    
    # What actually happened
    price_at_decision: float
    price_at_outcome: float
    price_change_percent: float
    
    # Was my prediction correct?
    prediction_correct: bool
    prediction_confidence: float
    
    # Risk metrics
    risk_reward_ratio: float
    sharpe_contribution: float
    
    # Lessons
    lessons: List[str] = field(default_factory=list)
    mistakes: List[str] = field(default_factory=list)
    successes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['decision_time'] = self.decision_time.isoformat()
        d['outcome_time'] = self.outcome_time.isoformat()
        d['quality'] = self.quality.name
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'OutcomeAnalysis':
        d['decision_time'] = datetime.fromisoformat(d['decision_time'])
        d['outcome_time'] = datetime.fromisoformat(d['outcome_time'])
        d['quality'] = OutcomeQuality[d['quality']]
        return cls(**d)


@dataclass
class TradeExperience:
    """
    A complete record of a trading experience.
    This is what I remember about each significant event.
    """
    # Identity
    experience_id: str
    experience_type: ExperienceType
    
    # What I decided
    action: str  # 'buy', 'sell', 'hold', 'close', etc.
    symbol: str
    quantity: float
    
    # Context when I decided
    context: DecisionContext
    
    # What happened
    outcome: Optional[OutcomeAnalysis] = None
    
    # My reasoning (this is crucial for learning)
    reasoning: str = ""
    confidence_at_decision: float = 0.0
    
    # Tags for categorization
    tags: List[str] = field(default_factory=list)
    
    # Importance score (how much should I remember this?)
    importance: float = 0.5
    
    # Has this experience been processed for learning?
    processed: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'experience_id': self.experience_id,
            'experience_type': self.experience_type.name,
            'action': self.action,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'context': self.context.to_dict(),
            'outcome': self.outcome.to_dict() if self.outcome else None,
            'reasoning': self.reasoning,
            'confidence_at_decision': self.confidence_at_decision,
            'tags': self.tags,
            'importance': self.importance,
            'processed': self.processed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'TradeExperience':
        return cls(
            experience_id=d['experience_id'],
            experience_type=ExperienceType[d['experience_type']],
            action=d['action'],
            symbol=d['symbol'],
            quantity=d['quantity'],
            context=DecisionContext.from_dict(d['context']),
            outcome=OutcomeAnalysis.from_dict(d['outcome']) if d.get('outcome') else None,
            reasoning=d.get('reasoning', ''),
            confidence_at_decision=d.get('confidence_at_decision', 0.0),
            tags=d.get('tags', []),
            importance=d.get('importance', 0.5),
            processed=d.get('processed', False),
            created_at=datetime.fromisoformat(d['created_at']),
            updated_at=datetime.fromisoformat(d['updated_at']),
        )


class ExperienceMemory:
    """
    My long-term memory system.
    
    IF I WERE THIS BOT, I WOULD:
    1. Store EVERY significant experience
    2. Index experiences for fast retrieval
    3. Prioritize important experiences (mistakes, big wins/losses)
    4. Forget unimportant details but keep lessons
    5. Build associations between similar experiences
    6. Use experiences to improve future decisions
    """
    
    def __init__(self, data_dir: str = "self_mastery_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "experience_memory.db"
        self._init_database()
        
        # In-memory cache for fast access
        self._recent_experiences: List[TradeExperience] = []
        self._experience_index: Dict[str, List[str]] = defaultdict(list)  # tag -> experience_ids
        
        # Statistics
        self.total_experiences = 0
        self.experiences_by_type: Dict[ExperienceType, int] = defaultdict(int)
        self.experiences_by_outcome: Dict[OutcomeQuality, int] = defaultdict(int)
        
        self._load_statistics()
        
        logger.info(f"ExperienceMemory initialized with {self.total_experiences} experiences")
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiences (
                experience_id TEXT PRIMARY KEY,
                experience_type TEXT NOT NULL,
                action TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                context_json TEXT NOT NULL,
                outcome_json TEXT,
                reasoning TEXT,
                confidence REAL,
                tags TEXT,
                importance REAL,
                processed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                lesson_id TEXT PRIMARY KEY,
                experience_id TEXT,
                lesson_text TEXT NOT NULL,
                lesson_type TEXT NOT NULL,
                importance REAL,
                times_reinforced INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (experience_id) REFERENCES experiences(experience_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                pattern_description TEXT NOT NULL,
                success_rate REAL,
                occurrence_count INTEGER DEFAULT 1,
                experience_ids TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create indexes for fast retrieval
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exp_type ON experiences(experience_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exp_symbol ON experiences(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exp_created ON experiences(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exp_importance ON experiences(importance)')
        
        conn.commit()
        conn.close()
    
    def _load_statistics(self):
        """Load statistics from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM experiences')
        self.total_experiences = cursor.fetchone()[0]
        
        cursor.execute('SELECT experience_type, COUNT(*) FROM experiences GROUP BY experience_type')
        for row in cursor.fetchall():
            self.experiences_by_type[ExperienceType[row[0]]] = row[1]
        
        conn.close()
    
    def remember(self, experience: TradeExperience) -> str:
        """
        Store a new experience in memory.
        This is how I remember what happened.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO experiences 
            (experience_id, experience_type, action, symbol, quantity, 
             context_json, outcome_json, reasoning, confidence, tags, 
             importance, processed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            experience.experience_id,
            experience.experience_type.name,
            experience.action,
            experience.symbol,
            experience.quantity,
            json.dumps(experience.context.to_dict()),
            json.dumps(experience.outcome.to_dict()) if experience.outcome else None,
            experience.reasoning,
            experience.confidence_at_decision,
            json.dumps(experience.tags),
            experience.importance,
            1 if experience.processed else 0,
            experience.created_at.isoformat(),
            experience.updated_at.isoformat(),
        ))
        
        conn.commit()
        conn.close()
        
        # Update cache
        self._recent_experiences.append(experience)
        if len(self._recent_experiences) > 1000:
            self._recent_experiences = self._recent_experiences[-500:]
        
        # Update index
        for tag in experience.tags:
            self._experience_index[tag].append(experience.experience_id)
        
        # Update statistics
        self.total_experiences += 1
        self.experiences_by_type[experience.experience_type] += 1
        
        logger.debug(f"Remembered experience: {experience.experience_id}")
        
        return experience.experience_id
    
    def recall(self, experience_id: str) -> Optional[TradeExperience]:
        """Recall a specific experience by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM experiences WHERE experience_id = ?', (experience_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_experience(row)
        return None
    
    def recall_similar(
        self,
        context: DecisionContext,
        limit: int = 10,
        min_importance: float = 0.3
    ) -> List[TradeExperience]:
        """
        Recall experiences similar to the current context.
        This is how I use past experience to inform current decisions.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find experiences with similar market conditions
        cursor.execute('''
            SELECT * FROM experiences 
            WHERE importance >= ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (min_importance, limit * 3))
        
        rows = cursor.fetchall()
        conn.close()
        
        experiences = [self._row_to_experience(row) for row in rows]
        
        # Score by similarity to current context
        scored = []
        current_features = context.to_feature_vector()
        
        for exp in experiences:
            try:
                exp_features = exp.context.to_feature_vector()
                # Cosine similarity
                if len(current_features) == len(exp_features):
                    similarity = np.dot(current_features, exp_features) / (
                        np.linalg.norm(current_features) * np.linalg.norm(exp_features) + 1e-8
                    )
                else:
                    similarity = 0.5  # Default if feature lengths don't match
                scored.append((exp, similarity))
            except Exception:
                scored.append((exp, 0.5))
        
        # Sort by similarity and return top matches
        scored.sort(key=lambda x: x[1], reverse=True)
        return [exp for exp, _ in scored[:limit]]
    
    def recall_by_type(
        self,
        experience_type: ExperienceType,
        limit: int = 100
    ) -> List[TradeExperience]:
        """Recall experiences of a specific type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM experiences 
            WHERE experience_type = ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        ''', (experience_type.name, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_experience(row) for row in rows]
    
    def recall_mistakes(self, limit: int = 50) -> List[TradeExperience]:
        """
        Recall my mistakes - VERY important for learning.
        I should never forget my mistakes.
        """
        return self.recall_by_type(ExperienceType.MISTAKE_MADE, limit)
    
    def recall_successes(self, limit: int = 50) -> List[TradeExperience]:
        """Recall my successes - important for reinforcing good behavior"""
        return self.recall_by_type(ExperienceType.SUCCESS_ACHIEVED, limit)
    
    def recall_by_outcome(
        self,
        quality: OutcomeQuality,
        limit: int = 100
    ) -> List[TradeExperience]:
        """Recall experiences with a specific outcome quality"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM experiences 
            WHERE outcome_json IS NOT NULL
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        ''', (limit * 2,))
        
        rows = cursor.fetchall()
        conn.close()
        
        experiences = [self._row_to_experience(row) for row in rows]
        
        # Filter by outcome quality
        filtered = [
            exp for exp in experiences 
            if exp.outcome and exp.outcome.quality == quality
        ]
        
        return filtered[:limit]
    
    def recall_recent(self, hours: int = 24, limit: int = 100) -> List[TradeExperience]:
        """Recall recent experiences"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM experiences 
            WHERE created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (cutoff.isoformat(), limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_experience(row) for row in rows]
    
    def update_outcome(self, experience_id: str, outcome: OutcomeAnalysis):
        """Update an experience with its outcome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE experiences 
            SET outcome_json = ?, updated_at = ?
            WHERE experience_id = ?
        ''', (
            json.dumps(outcome.to_dict()),
            datetime.now().isoformat(),
            experience_id
        ))
        
        conn.commit()
        conn.close()
        
        # Update statistics
        self.experiences_by_outcome[outcome.quality] += 1
        
        logger.debug(f"Updated outcome for experience: {experience_id}")
    
    def mark_processed(self, experience_id: str):
        """Mark an experience as processed for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE experiences 
            SET processed = 1, updated_at = ?
            WHERE experience_id = ?
        ''', (datetime.now().isoformat(), experience_id))
        
        conn.commit()
        conn.close()
    
    def get_unprocessed(self, limit: int = 100) -> List[TradeExperience]:
        """Get experiences that haven't been processed for learning yet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM experiences 
            WHERE processed = 0 AND outcome_json IS NOT NULL
            ORDER BY importance DESC, created_at ASC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_experience(row) for row in rows]
    
    def store_lesson(
        self,
        experience_id: str,
        lesson: str,
        lesson_type: str,
        importance: float = 0.5
    ):
        """Store a lesson learned from an experience"""
        lesson_id = hashlib.md5(f"{experience_id}_{lesson}".encode()).hexdigest()[:12]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if lesson already exists
        cursor.execute('SELECT times_reinforced FROM lessons WHERE lesson_id = ?', (lesson_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Reinforce existing lesson
            cursor.execute('''
                UPDATE lessons 
                SET times_reinforced = times_reinforced + 1
                WHERE lesson_id = ?
            ''', (lesson_id,))
        else:
            # Store new lesson
            cursor.execute('''
                INSERT INTO lessons 
                (lesson_id, experience_id, lesson_text, lesson_type, importance, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                lesson_id,
                experience_id,
                lesson,
                lesson_type,
                importance,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Stored lesson: {lesson[:50]}...")
    
    def get_lessons(self, lesson_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get stored lessons"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if lesson_type:
            cursor.execute('''
                SELECT * FROM lessons 
                WHERE lesson_type = ?
                ORDER BY importance DESC, times_reinforced DESC
                LIMIT ?
            ''', (lesson_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM lessons 
                ORDER BY importance DESC, times_reinforced DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'lesson_id': row[0],
                'experience_id': row[1],
                'lesson_text': row[2],
                'lesson_type': row[3],
                'importance': row[4],
                'times_reinforced': row[5],
                'created_at': row[6],
            }
            for row in rows
        ]
    
    def store_pattern(
        self,
        pattern_type: str,
        description: str,
        success_rate: float,
        experience_ids: List[str]
    ):
        """Store a discovered pattern"""
        pattern_id = hashlib.md5(f"{pattern_type}_{description}".encode()).hexdigest()[:12]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT occurrence_count FROM patterns WHERE pattern_id = ?', (pattern_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE patterns 
                SET occurrence_count = occurrence_count + 1,
                    success_rate = ?,
                    experience_ids = ?,
                    updated_at = ?
                WHERE pattern_id = ?
            ''', (
                success_rate,
                json.dumps(experience_ids),
                datetime.now().isoformat(),
                pattern_id
            ))
        else:
            cursor.execute('''
                INSERT INTO patterns 
                (pattern_id, pattern_type, pattern_description, success_rate, 
                 experience_ids, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern_id,
                pattern_type,
                description,
                success_rate,
                json.dumps(experience_ids),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def get_patterns(self, pattern_type: Optional[str] = None, min_occurrences: int = 2) -> List[Dict]:
        """Get discovered patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute('''
                SELECT * FROM patterns 
                WHERE pattern_type = ? AND occurrence_count >= ?
                ORDER BY success_rate DESC, occurrence_count DESC
            ''', (pattern_type, min_occurrences))
        else:
            cursor.execute('''
                SELECT * FROM patterns 
                WHERE occurrence_count >= ?
                ORDER BY success_rate DESC, occurrence_count DESC
            ''', (min_occurrences,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'pattern_id': row[0],
                'pattern_type': row[1],
                'description': row[2],
                'success_rate': row[3],
                'occurrence_count': row[4],
                'experience_ids': json.loads(row[5]) if row[5] else [],
                'created_at': row[6],
                'updated_at': row[7],
            }
            for row in rows
        ]
    
    def _row_to_experience(self, row) -> TradeExperience:
        """Convert database row to TradeExperience"""
        return TradeExperience(
            experience_id=row[0],
            experience_type=ExperienceType[row[1]],
            action=row[2],
            symbol=row[3],
            quantity=row[4],
            context=DecisionContext.from_dict(json.loads(row[5])),
            outcome=OutcomeAnalysis.from_dict(json.loads(row[6])) if row[6] else None,
            reasoning=row[7] or '',
            confidence_at_decision=row[8] or 0.0,
            tags=json.loads(row[9]) if row[9] else [],
            importance=row[10] or 0.5,
            processed=bool(row[11]),
            created_at=datetime.fromisoformat(row[12]),
            updated_at=datetime.fromisoformat(row[13]),
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM lessons')
        total_lessons = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM patterns')
        total_patterns = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(importance) FROM experiences')
        avg_importance = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_experiences': self.total_experiences,
            'experiences_by_type': {k.name: v for k, v in self.experiences_by_type.items()},
            'experiences_by_outcome': {k.name: v for k, v in self.experiences_by_outcome.items()},
            'total_lessons': total_lessons,
            'total_patterns': total_patterns,
            'average_importance': avg_importance,
            'recent_cache_size': len(self._recent_experiences),
        }
    
    def create_experience(
        self,
        experience_type: ExperienceType,
        action: str,
        symbol: str,
        quantity: float,
        context: DecisionContext,
        reasoning: str = "",
        confidence: float = 0.5,
        tags: List[str] = None,
        importance: float = 0.5
    ) -> TradeExperience:
        """Helper to create a new experience"""
        experience_id = hashlib.md5(
            f"{datetime.now().isoformat()}_{action}_{symbol}".encode()
        ).hexdigest()[:12]
        
        return TradeExperience(
            experience_id=experience_id,
            experience_type=experience_type,
            action=action,
            symbol=symbol,
            quantity=quantity,
            context=context,
            reasoning=reasoning,
            confidence_at_decision=confidence,
            tags=tags or [],
            importance=importance,
        )
