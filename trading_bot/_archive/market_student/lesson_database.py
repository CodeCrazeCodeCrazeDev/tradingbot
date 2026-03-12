"""
Lesson Database - Persistent Storage for Market Lessons
========================================================

Stores all lessons learned from the market for:
- Pattern recognition across time
- Weakness tracking
- Improvement validation
- Historical analysis
- Knowledge accumulation

Every lesson is preserved. Nothing is forgotten.

Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import logging
import json
import sqlite3
from pathlib import Path
import hashlib

from .market_teacher import MarketLesson, LessonType, LessonSeverity

logger = logging.getLogger(__name__)


# =============================================================================
# STORED LESSON
# =============================================================================

@dataclass
class StoredLesson:
    """A lesson stored in the database"""
    
    id: int
    lesson_id: str
    lesson_type: str
    severity: str
    
    # Content
    description: str
    what_market_showed: str
    what_ai_expected: str
    discrepancy: str
    lesson_learned: str
    actionable_insight: str
    
    # Metrics
    confidence: float
    impact_score: float
    
    # Context
    symbol: str
    timeframe: str
    market_context: Dict[str, Any]
    
    # Timestamps
    timestamp: datetime
    created_at: datetime
    
    # Usage tracking
    times_referenced: int
    last_referenced: Optional[datetime]
    
    @classmethod
    def from_market_lesson(cls, lesson: MarketLesson) -> 'StoredLesson':
        """Create StoredLesson from MarketLesson"""
        return cls(
            id=0,  # Will be set by database
            lesson_id=lesson.lesson_id,
            lesson_type=lesson.lesson_type.value,
            severity=lesson.severity.value,
            description=lesson.description,
            what_market_showed=lesson.what_market_showed,
            what_ai_expected=lesson.what_ai_expected,
            discrepancy=lesson.discrepancy,
            lesson_learned=lesson.lesson_learned,
            actionable_insight=lesson.actionable_insight,
            confidence=lesson.confidence,
            impact_score=lesson.impact_score,
            symbol=lesson.symbol,
            timeframe=lesson.timeframe,
            market_context=lesson.market_context,
            timestamp=lesson.timestamp,
            created_at=datetime.now(),
            times_referenced=0,
            last_referenced=None,
        )


# =============================================================================
# LESSON QUERY
# =============================================================================

@dataclass
class LessonQuery:
    """Query parameters for lesson search"""
    
    # Filters
    lesson_types: Optional[List[str]] = None
    severities: Optional[List[str]] = None
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    
    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Metrics
    min_confidence: Optional[float] = None
    min_impact: Optional[float] = None
    
    # Text search
    search_text: Optional[str] = None
    
    # Pagination
    limit: int = 100
    offset: int = 0
    
    # Sorting
    order_by: str = 'timestamp'
    order_desc: bool = True


# =============================================================================
# LESSON DATABASE
# =============================================================================

class LessonDatabase:
    """
    Persistent storage for market lessons.
    
    Uses SQLite for reliable, file-based storage.
    All lessons are preserved for future learning.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Database path
        db_path = self.config.get('db_path', 'market_student_data/lessons.db')
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Statistics
        self._stats = {
            'total_lessons': 0,
            'lessons_by_type': {},
            'lessons_by_symbol': {},
        }
        self._update_stats()
        
        logger.info(f"LessonDatabase initialized at {self._db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        # Lessons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id TEXT UNIQUE NOT NULL,
                lesson_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                what_market_showed TEXT,
                what_ai_expected TEXT,
                discrepancy TEXT,
                lesson_learned TEXT,
                actionable_insight TEXT,
                confidence REAL,
                impact_score REAL,
                symbol TEXT,
                timeframe TEXT,
                market_context TEXT,
                timestamp TEXT,
                created_at TEXT,
                times_referenced INTEGER DEFAULT 0,
                last_referenced TEXT
            )
        ''')
        
        # Patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE NOT NULL,
                pattern_type TEXT NOT NULL,
                description TEXT,
                occurrences INTEGER DEFAULT 1,
                confidence REAL,
                first_seen TEXT,
                last_seen TEXT,
                lesson_ids TEXT
            )
        ''')
        
        # Weaknesses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weaknesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                weakness_id TEXT UNIQUE NOT NULL,
                weakness_type TEXT NOT NULL,
                description TEXT,
                occurrences INTEGER DEFAULT 1,
                severity TEXT,
                first_seen TEXT,
                last_seen TEXT,
                lesson_ids TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Proposals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT UNIQUE NOT NULL,
                proposal_type TEXT NOT NULL,
                priority TEXT,
                status TEXT,
                title TEXT,
                description TEXT,
                rationale TEXT,
                target_component TEXT,
                current_value TEXT,
                proposed_value TEXT,
                created_at TEXT,
                approved_at TEXT,
                implemented_at TEXT,
                approved_by TEXT,
                rejection_reason TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lessons_type ON lessons(lesson_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lessons_symbol ON lessons(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lessons_timestamp ON lessons(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lessons_severity ON lessons(severity)')
        
        conn.commit()
        conn.close()
    
    def store_lesson(self, lesson: MarketLesson) -> int:
        """
        Store a lesson in the database.
        
        Args:
            lesson: The lesson to store
            
        Returns:
            Database ID of the stored lesson
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO lessons (
                    lesson_id, lesson_type, severity, description,
                    what_market_showed, what_ai_expected, discrepancy,
                    lesson_learned, actionable_insight, confidence,
                    impact_score, symbol, timeframe, market_context,
                    timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lesson.lesson_id,
                lesson.lesson_type.value,
                lesson.severity.value,
                lesson.description,
                lesson.what_market_showed,
                lesson.what_ai_expected,
                lesson.discrepancy,
                lesson.lesson_learned,
                lesson.actionable_insight,
                lesson.confidence,
                lesson.impact_score,
                lesson.symbol,
                lesson.timeframe,
                json.dumps(lesson.market_context),
                lesson.timestamp.isoformat(),
                datetime.now().isoformat(),
            ))
            
            lesson_db_id = cursor.lastrowid
            conn.commit()
            
            # Update stats
            self._stats['total_lessons'] += 1
            
            logger.debug(f"Stored lesson {lesson.lesson_id}")
            return lesson_db_id
            
        except Exception as e:
            logger.error(f"Error storing lesson: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_lesson(self, lesson_id: str) -> Optional[StoredLesson]:
        """Get a lesson by ID"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT * FROM lessons WHERE lesson_id = ?',
                (lesson_id,)
            )
            row = cursor.fetchone()
            
            if row:
                # Update reference count
                cursor.execute('''
                    UPDATE lessons 
                    SET times_referenced = times_referenced + 1,
                        last_referenced = ?
                    WHERE lesson_id = ?
                ''', (datetime.now().isoformat(), lesson_id))
                conn.commit()
                
                return self._row_to_stored_lesson(row)
            
            return None
            
        finally:
            conn.close()
    
    def query_lessons(self, query: LessonQuery) -> List[StoredLesson]:
        """
        Query lessons with filters.
        
        Args:
            query: Query parameters
            
        Returns:
            List of matching lessons
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            # Build query
            sql = 'SELECT * FROM lessons WHERE 1=1'
            params = []
            
            if query.lesson_types:
                placeholders = ','.join('?' * len(query.lesson_types))
                sql += f' AND lesson_type IN ({placeholders})'
                params.extend(query.lesson_types)
            
            if query.severities:
                placeholders = ','.join('?' * len(query.severities))
                sql += f' AND severity IN ({placeholders})'
                params.extend(query.severities)
            
            if query.symbols:
                placeholders = ','.join('?' * len(query.symbols))
                sql += f' AND symbol IN ({placeholders})'
                params.extend(query.symbols)
            
            if query.timeframes:
                placeholders = ','.join('?' * len(query.timeframes))
                sql += f' AND timeframe IN ({placeholders})'
                params.extend(query.timeframes)
            
            if query.start_date:
                sql += ' AND timestamp >= ?'
                params.append(query.start_date.isoformat())
            
            if query.end_date:
                sql += ' AND timestamp <= ?'
                params.append(query.end_date.isoformat())
            
            if query.min_confidence:
                sql += ' AND confidence >= ?'
                params.append(query.min_confidence)
            
            if query.min_impact:
                sql += ' AND impact_score >= ?'
                params.append(query.min_impact)
            
            if query.search_text:
                sql += ' AND (description LIKE ? OR lesson_learned LIKE ? OR actionable_insight LIKE ?)'
                search_pattern = f'%{query.search_text}%'
                params.extend([search_pattern, search_pattern, search_pattern])
            
            # Sorting
            order_dir = 'DESC' if query.order_desc else 'ASC'
            sql += f' ORDER BY {query.order_by} {order_dir}'
            
            # Pagination
            sql += ' LIMIT ? OFFSET ?'
            params.extend([query.limit, query.offset])
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            return [self._row_to_stored_lesson(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_lessons_by_type(self, lesson_type: str, limit: int = 100) -> List[StoredLesson]:
        """Get lessons of a specific type"""
        query = LessonQuery(lesson_types=[lesson_type], limit=limit)
        return self.query_lessons(query)
    
    def get_lessons_by_symbol(self, symbol: str, limit: int = 100) -> List[StoredLesson]:
        """Get lessons for a specific symbol"""
        query = LessonQuery(symbols=[symbol], limit=limit)
        return self.query_lessons(query)
    
    def get_high_impact_lessons(self, min_impact: float = 0.7, limit: int = 100) -> List[StoredLesson]:
        """Get high-impact lessons"""
        query = LessonQuery(min_impact=min_impact, limit=limit)
        return self.query_lessons(query)
    
    def get_recent_lessons(self, hours: int = 24, limit: int = 100) -> List[StoredLesson]:
        """Get lessons from the last N hours"""
        query = LessonQuery(
            start_date=datetime.now() - timedelta(hours=hours),
            limit=limit
        )
        return self.query_lessons(query)
    
    def store_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        description: str,
        confidence: float,
        lesson_ids: List[str]
    ):
        """Store a recognized pattern"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            # Check if pattern exists
            cursor.execute(
                'SELECT occurrences, lesson_ids FROM patterns WHERE pattern_id = ?',
                (pattern_id,)
            )
            row = cursor.fetchone()
            
            if row:
                # Update existing pattern
                existing_lessons = json.loads(row[1]) if row[1] else []
                all_lessons = list(set(existing_lessons + lesson_ids))
                
                cursor.execute('''
                    UPDATE patterns 
                    SET occurrences = occurrences + 1,
                        confidence = ?,
                        last_seen = ?,
                        lesson_ids = ?
                    WHERE pattern_id = ?
                ''', (confidence, datetime.now().isoformat(), json.dumps(all_lessons), pattern_id))
            else:
                # Insert new pattern
                cursor.execute('''
                    INSERT INTO patterns (
                        pattern_id, pattern_type, description, occurrences,
                        confidence, first_seen, last_seen, lesson_ids
                    ) VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                ''', (
                    pattern_id, pattern_type, description, confidence,
                    datetime.now().isoformat(), datetime.now().isoformat(),
                    json.dumps(lesson_ids)
                ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def store_weakness(
        self,
        weakness_id: str,
        weakness_type: str,
        description: str,
        severity: str,
        lesson_ids: List[str]
    ):
        """Store an identified weakness"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            # Check if weakness exists
            cursor.execute(
                'SELECT occurrences, lesson_ids FROM weaknesses WHERE weakness_id = ?',
                (weakness_id,)
            )
            row = cursor.fetchone()
            
            if row:
                # Update existing weakness
                existing_lessons = json.loads(row[1]) if row[1] else []
                all_lessons = list(set(existing_lessons + lesson_ids))
                
                cursor.execute('''
                    UPDATE weaknesses 
                    SET occurrences = occurrences + 1,
                        severity = ?,
                        last_seen = ?,
                        lesson_ids = ?
                    WHERE weakness_id = ?
                ''', (severity, datetime.now().isoformat(), json.dumps(all_lessons), weakness_id))
            else:
                # Insert new weakness
                cursor.execute('''
                    INSERT INTO weaknesses (
                        weakness_id, weakness_type, description, occurrences,
                        severity, first_seen, last_seen, lesson_ids
                    ) VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                ''', (
                    weakness_id, weakness_type, description, severity,
                    datetime.now().isoformat(), datetime.now().isoformat(),
                    json.dumps(lesson_ids)
                ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def get_active_weaknesses(self) -> List[Dict[str, Any]]:
        """Get all active weaknesses"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM weaknesses WHERE status = 'active' ORDER BY occurrences DESC"
            )
            rows = cursor.fetchall()
            
            return [
                {
                    'weakness_id': row[1],
                    'weakness_type': row[2],
                    'description': row[3],
                    'occurrences': row[4],
                    'severity': row[5],
                    'first_seen': row[6],
                    'last_seen': row[7],
                }
                for row in rows
            ]
            
        finally:
            conn.close()
    
    def mark_weakness_resolved(self, weakness_id: str):
        """Mark a weakness as resolved"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE weaknesses SET status = 'resolved' WHERE weakness_id = ?",
                (weakness_id,)
            )
            conn.commit()
            
        finally:
            conn.close()
    
    def _row_to_stored_lesson(self, row: tuple) -> StoredLesson:
        """Convert database row to StoredLesson"""
        return StoredLesson(
            id=row[0],
            lesson_id=row[1],
            lesson_type=row[2],
            severity=row[3],
            description=row[4],
            what_market_showed=row[5],
            what_ai_expected=row[6],
            discrepancy=row[7],
            lesson_learned=row[8],
            actionable_insight=row[9],
            confidence=row[10],
            impact_score=row[11],
            symbol=row[12],
            timeframe=row[13],
            market_context=json.loads(row[14]) if row[14] else {},
            timestamp=datetime.fromisoformat(row[15]) if row[15] else datetime.now(),
            created_at=datetime.fromisoformat(row[16]) if row[16] else datetime.now(),
            times_referenced=row[17] or 0,
            last_referenced=datetime.fromisoformat(row[18]) if row[18] else None,
        )
    
    def _update_stats(self):
        """Update internal statistics"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            # Total lessons
            cursor.execute('SELECT COUNT(*) FROM lessons')
            self._stats['total_lessons'] = cursor.fetchone()[0]
            
            # Lessons by type
            cursor.execute('SELECT lesson_type, COUNT(*) FROM lessons GROUP BY lesson_type')
            self._stats['lessons_by_type'] = dict(cursor.fetchall())
            
            # Lessons by symbol
            cursor.execute('SELECT symbol, COUNT(*) FROM lessons GROUP BY symbol')
            self._stats['lessons_by_symbol'] = dict(cursor.fetchall())
            
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        self._update_stats()
        
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        try:
            # Additional stats
            cursor.execute('SELECT COUNT(*) FROM patterns')
            pattern_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM weaknesses WHERE status = 'active'")
            active_weaknesses = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(confidence), AVG(impact_score) FROM lessons')
            row = cursor.fetchone()
            avg_confidence = row[0] or 0
            avg_impact = row[1] or 0
            
            return {
                **self._stats,
                'pattern_count': pattern_count,
                'active_weaknesses': active_weaknesses,
                'avg_confidence': avg_confidence,
                'avg_impact': avg_impact,
            }
            
        finally:
            conn.close()
    
    def export_lessons(self, filepath: str, query: Optional[LessonQuery] = None):
        """Export lessons to JSON file"""
        lessons = self.query_lessons(query or LessonQuery(limit=10000))
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_lessons': len(lessons),
            'lessons': [
                {
                    'lesson_id': l.lesson_id,
                    'lesson_type': l.lesson_type,
                    'severity': l.severity,
                    'description': l.description,
                    'lesson_learned': l.lesson_learned,
                    'actionable_insight': l.actionable_insight,
                    'confidence': l.confidence,
                    'impact_score': l.impact_score,
                    'symbol': l.symbol,
                    'timestamp': l.timestamp.isoformat(),
                }
                for l in lessons
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(lessons)} lessons to {filepath}")
