import json
import sqlite3
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ImprovementMemory:
    """
    Persistent memory for the Recursive Self-Improvement system.
    Stores experiment history, successes, failures, and lessons learned.
    """

    def __init__(self, db_path: str = "recursive_improvement_data/improvement_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Experiments Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    domain TEXT,
                    hypothesis TEXT,
                    parameters TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result_score REAL,
                    result_details TEXT,
                    market_context TEXT
                )
            ''')

            # Lessons Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lessons (
                    lesson_id TEXT PRIMARY KEY,
                    domain TEXT,
                    topic TEXT,
                    content TEXT,
                    source_experiment_id TEXT,
                    impact_score REAL,
                    created_at TIMESTAMP
                )
            ''')

            # Deployments Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    deployment_id TEXT PRIMARY KEY,
                    experiment_id TEXT,
                    domain TEXT,
                    version TEXT,
                    config_snapshot TEXT,
                    deployed_at TIMESTAMP,
                    status TEXT
                )
            ''')

            conn.commit()

    def record_experiment(self, experiment_id: str, domain: str, hypothesis: str, parameters: Dict[str, Any], market_context: Optional[Dict[str, Any]] = None):
        """Record a new experiment proposal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO experiments (experiment_id, domain, hypothesis, parameters, status, created_at, market_context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                experiment_id,
                domain,
                hypothesis,
                json.dumps(parameters),
                "pending",
                datetime.utcnow().isoformat(),
                json.dumps(market_context) if market_context else None
            ))
            conn.commit()

    def update_experiment_result(self, experiment_id: str, status: str, score: float, details: Dict[str, Any]):
        """Update an experiment with its results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE experiments
                SET status = ?, result_score = ?, result_details = ?, completed_at = ?
                WHERE experiment_id = ?
            ''', (
                status,
                score,
                json.dumps(details),
                datetime.utcnow().isoformat(),
                experiment_id
            ))
            conn.commit()

    def add_lesson(self, domain: str, topic: str, content: str, source_id: Optional[str] = None, impact: float = 0.0):
        """Add a learned lesson to memory."""
        import uuid
        lesson_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lessons (lesson_id, domain, topic, content, source_experiment_id, impact_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                lesson_id,
                domain,
                topic,
                content,
                source_id,
                impact,
                datetime.utcnow().isoformat()
            ))
            conn.commit()

    def get_recent_experiments(self, domain: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent experiments for analysis."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if domain:
                cursor.execute('SELECT * FROM experiments WHERE domain = ? ORDER BY created_at DESC LIMIT ?', (domain, limit))
            else:
                cursor.execute('SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def record_deployment(self, deployment_id: str, experiment_id: str, domain: str, version: str, config: Dict[str, Any]):
        """Record a successful deployment."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO deployments (deployment_id, experiment_id, domain, version, config_snapshot, deployed_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                deployment_id,
                experiment_id,
                domain,
                version,
                json.dumps(config),
                datetime.utcnow().isoformat(),
                "active"
            ))
            conn.commit()
