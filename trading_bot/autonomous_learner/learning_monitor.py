"""
Learning Monitor - Tracks and Monitors Learning Progress

Provides real-time monitoring of:
- Learning progress across all levels
- Knowledge acquisition rate
- Test performance trends
- Evolution of understanding
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)


class LearningPhase(Enum):
    """Phases of learning"""
    INITIALIZATION = auto()
    BASIC_LEARNING = auto()
    INTERMEDIATE_LEARNING = auto()
    ADVANCED_LEARNING = auto()
    TESTING = auto()
    KNOWLEDGE_TRANSFER = auto()
    EVOLUTION = auto()
    COMPLETE = auto()


@dataclass
class LearningMetrics:
    """Metrics for learning progress"""
    resources_studied: int
    concepts_learned: int
    tests_taken: int
    tests_passed: int
    current_level: int
    highest_level_reached: int
    knowledge_gaps: int
    transfers_completed: int
    learning_rate: float  # concepts per hour
    accuracy_trend: List[float]
    time_spent: float  # hours
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resources_studied': self.resources_studied,
            'concepts_learned': self.concepts_learned,
            'tests_taken': self.tests_taken,
            'tests_passed': self.tests_passed,
            'current_level': self.current_level,
            'highest_level_reached': self.highest_level_reached,
            'knowledge_gaps': self.knowledge_gaps,
            'transfers_completed': self.transfers_completed,
            'learning_rate': self.learning_rate,
            'accuracy_trend': self.accuracy_trend[-10:],  # Last 10
            'time_spent': self.time_spent,
        }


@dataclass
class LearningEvent:
    """A learning event to track"""
    id: str
    event_type: str
    phase: LearningPhase
    details: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'event_type': self.event_type,
            'phase': self.phase.name,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
        }


class LearningMonitor:
    """
    Monitors and tracks all learning activities.
    
    Features:
    - Real-time progress tracking
    - Performance analytics
    - Learning rate calculation
    - Gap identification
    - Evolution tracking
    """
    
    def __init__(self, data_dir: str = "autonomous_learner_data"):
        try:
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
            self.db_path = self.data_dir / "learning_monitor.db"
            self._init_database()
        
            self.start_time = datetime.now()
            self.current_phase = LearningPhase.INITIALIZATION
            self.events: List[LearningEvent] = []
            self.metrics = LearningMetrics(
                resources_studied=0,
                concepts_learned=0,
                tests_taken=0,
                tests_passed=0,
                current_level=1,
                highest_level_reached=1,
                knowledge_gaps=0,
                transfers_completed=0,
                learning_rate=0.0,
                accuracy_trend=[],
                time_spent=0.0,
            )
        
            logger.info("LearningMonitor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_database(self):
        """Initialize monitoring database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT,
                    phase TEXT,
                    details TEXT,
                    timestamp TEXT
                )
            ''')
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metrics TEXT,
                    timestamp TEXT
                )
            ''')
        
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phase_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_phase TEXT,
                    to_phase TEXT,
                    reason TEXT,
                    timestamp TEXT
                )
            ''')
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in _init_database: {e}")
            raise
    
    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log a learning event"""
        try:
            event = LearningEvent(
                id=f"{event_type}_{datetime.now().timestamp()}",
                event_type=event_type,
                phase=self.current_phase,
                details=details,
                timestamp=datetime.now(),
            )
        
            self.events.append(event)
            self._store_event(event)
        
            # Update metrics based on event
            self._update_metrics(event)
        
            logger.debug(f"Event logged: {event_type}")
        except Exception as e:
            logger.error(f"Error in log_event: {e}")
            raise
    
    def _store_event(self, event: LearningEvent):
        """Store event in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                INSERT INTO learning_events (id, event_type, phase, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                event.id,
                event.event_type,
                event.phase.name,
                json.dumps(event.details),
                event.timestamp.isoformat(),
            ))
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in _store_event: {e}")
            raise
    
    def _update_metrics(self, event: LearningEvent):
        """Update metrics based on event"""
        try:
            if event.event_type == 'resource_studied':
                self.metrics.resources_studied += 1
            elif event.event_type == 'concept_learned':
                self.metrics.concepts_learned += 1
            elif event.event_type == 'test_completed':
                self.metrics.tests_taken += 1
                if event.details.get('passed', False):
                    self.metrics.tests_passed += 1
                self.metrics.accuracy_trend.append(event.details.get('score', 0))
            elif event.event_type == 'level_advanced':
                new_level = event.details.get('level', 1)
                self.metrics.current_level = new_level
                self.metrics.highest_level_reached = max(self.metrics.highest_level_reached, new_level)
            elif event.event_type == 'transfer_completed':
                self.metrics.transfers_completed += 1
            elif event.event_type == 'gap_identified':
                self.metrics.knowledge_gaps += 1
        
            # Update time spent
            self.metrics.time_spent = (datetime.now() - self.start_time).total_seconds() / 3600
        
            # Calculate learning rate
            if self.metrics.time_spent > 0:
                self.metrics.learning_rate = self.metrics.concepts_learned / self.metrics.time_spent
        except Exception as e:
            logger.error(f"Error in _update_metrics: {e}")
            raise
    
    def transition_phase(self, new_phase: LearningPhase, reason: str = ""):
        """Transition to a new learning phase"""
        try:
            old_phase = self.current_phase
            self.current_phase = new_phase
        
            # Log transition
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                INSERT INTO phase_transitions (from_phase, to_phase, reason, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (old_phase.name, new_phase.name, reason, datetime.now().isoformat()))
        
            conn.commit()
            conn.close()
        
            self.log_event('phase_transition', {
                'from': old_phase.name,
                'to': new_phase.name,
                'reason': reason,
            })
        
            logger.info(f"Phase transition: {old_phase.name} -> {new_phase.name}")
        except Exception as e:
            logger.error(f"Error in transition_phase: {e}")
            raise
    
    def save_metrics_snapshot(self):
        """Save current metrics to history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                INSERT INTO metrics_history (metrics, timestamp)
                VALUES (?, ?)
            ''', (json.dumps(self.metrics.to_dict()), datetime.now().isoformat()))
        
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in save_metrics_snapshot: {e}")
            raise
    
    def get_progress_report(self) -> Dict[str, Any]:
        """Generate a comprehensive progress report"""
        try:
            elapsed = datetime.now() - self.start_time
        
            return {
                'session_info': {
                    'start_time': self.start_time.isoformat(),
                    'elapsed_time': str(elapsed),
                    'elapsed_hours': elapsed.total_seconds() / 3600,
                    'current_phase': self.current_phase.name,
                },
                'metrics': self.metrics.to_dict(),
                'performance': {
                    'pass_rate': self.metrics.tests_passed / self.metrics.tests_taken if self.metrics.tests_taken > 0 else 0,
                    'avg_accuracy': sum(self.metrics.accuracy_trend) / len(self.metrics.accuracy_trend) if self.metrics.accuracy_trend else 0,
                    'learning_rate': self.metrics.learning_rate,
                    'concepts_per_resource': self.metrics.concepts_learned / self.metrics.resources_studied if self.metrics.resources_studied > 0 else 0,
                },
                'progress': {
                    'level_progress': f"{self.metrics.current_level}/7",
                    'completion_percentage': (self.metrics.current_level / 7) * 100,
                    'transfers_pending': self.metrics.concepts_learned - self.metrics.transfers_completed,
                },
                'recent_events': [e.to_dict() for e in self.events[-10:]],
            }
        except Exception as e:
            logger.error(f"Error in get_progress_report: {e}")
            raise
    
    def get_learning_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of learning events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            cursor.execute('''
                SELECT event_type, phase, details, timestamp 
                FROM learning_events 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''')
        
            timeline = []
            for row in cursor.fetchall():
                timeline.append({
                    'event_type': row[0],
                    'phase': row[1],
                    'details': json.loads(row[2]),
                    'timestamp': row[3],
                })
        
            conn.close()
            return timeline
        except Exception as e:
            logger.error(f"Error in get_learning_timeline: {e}")
            raise
    
    def print_status(self):
        """Print current status to console"""
        try:
            report = self.get_progress_report()
        
            print("\n" + "="*60)
            print("[STATUS] AUTONOMOUS LEARNING STATUS")
            print("="*60)
            print(f"[TIME] Elapsed: {report['session_info']['elapsed_time']}")
            print(f"[PHASE] Phase: {report['session_info']['current_phase']}")
            print(f"[LEVEL] Level: {report['progress']['level_progress']} ({report['progress']['completion_percentage']:.1f}%)")
            print("-"*60)
            print(f"[RESOURCES] Resources Studied: {report['metrics']['resources_studied']}")
            print(f"[CONCEPTS] Concepts Learned: {report['metrics']['concepts_learned']}")
            print(f"[TESTS] Tests Taken: {report['metrics']['tests_taken']}")
            print(f"[PASSED] Tests Passed: {report['metrics']['tests_passed']}")
            print(f"[RATE] Pass Rate: {report['performance']['pass_rate']:.1%}")
            print(f"[ACCURACY] Avg Accuracy: {report['performance']['avg_accuracy']:.1%}")
            print(f"[SPEED] Learning Rate: {report['metrics']['learning_rate']:.2f} concepts/hour")
            print(f"[TRANSFER] Transfers Completed: {report['metrics']['transfers_completed']}")
            print("="*60 + "\n")
        except Exception as e:
            logger.error(f"Error in print_status: {e}")
            raise
    
    def should_advance_level(self) -> Tuple[bool, str]:
        """Check if ready to advance to next level"""
        try:
            if len(self.metrics.accuracy_trend) < 3:
                return False, "Need more test attempts"
        
            recent_accuracy = sum(self.metrics.accuracy_trend[-3:]) / 3
        
            if recent_accuracy >= 0.8:
                return True, f"Recent accuracy {recent_accuracy:.1%} >= 80%"
            else:
                return False, f"Recent accuracy {recent_accuracy:.1%} < 80%"
        except Exception as e:
            logger.error(f"Error in should_advance_level: {e}")
            raise
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations for improving learning"""
        try:
            recommendations = []
        
            if self.metrics.tests_taken == 0:
                recommendations.append("Take some tests to validate learning")
            elif self.metrics.tests_passed / self.metrics.tests_taken < 0.7:
                recommendations.append("Focus on reviewing failed topics before advancing")
        
            if self.metrics.knowledge_gaps > 3:
                recommendations.append(f"Address {self.metrics.knowledge_gaps} knowledge gaps")
        
            if self.metrics.learning_rate < 5:
                recommendations.append("Increase study intensity for faster progress")
        
            if self.metrics.transfers_completed < self.metrics.concepts_learned * 0.5:
                recommendations.append("Transfer more learned concepts to the bot")
        
            if not recommendations:
                recommendations.append("Learning is progressing well! Keep going!")
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in get_recommendations: {e}")
            raise


# Tuple already imported at top of file
