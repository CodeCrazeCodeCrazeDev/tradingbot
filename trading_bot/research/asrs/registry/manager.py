import sqlite3
import os
import json
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime

class ExperimentRegistry:
    """
    Thread-safe and persistent SQLite Experiment Registry for tracking
    all active, queued, failed, verifying, and promoted research runs.
    """
    def __init__(self, db_path: str = "alphaalgo_data/research_experiments.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiment_registry (
                    experiment_id TEXT PRIMARY KEY,
                    hypothesis_id TEXT NOT NULL,
                    isolation_level INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    git_sha TEXT NOT NULL,
                    resources_allocated TEXT NOT NULL,
                    creation_timestamp TEXT NOT NULL,
                    last_update_timestamp TEXT NOT NULL,
                    error_log TEXT,
                    rollback_instructions TEXT NOT NULL
                );
            """)
            conn.commit()
            conn.close()

    def register_experiment(
        self,
        experiment_id: str,
        hypothesis_id: str,
        isolation_level: int,
        git_sha: str,
        resources: Dict[str, Any],
        rollback_instructions: Dict[str, Any]
    ):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO experiment_registry
                (experiment_id, hypothesis_id, isolation_level, state, git_sha, resources_allocated, creation_timestamp, last_update_timestamp, rollback_instructions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment_id,
                hypothesis_id,
                isolation_level,
                "QUEUED",
                git_sha,
                json.dumps(resources),
                now,
                now,
                json.dumps(rollback_instructions)
            ))
            conn.commit()
            conn.close()

    def update_state(self, experiment_id: str, state: str, error_log: Optional[str] = None):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                UPDATE experiment_registry
                SET state = ?, error_log = ?, last_update_timestamp = ?
                WHERE experiment_id = ?
            """, (state, error_log, now, experiment_id))
            conn.commit()
            conn.close()

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiment_registry WHERE experiment_id = ?", (experiment_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            return {
                "experiment_id": row[0],
                "hypothesis_id": row[1],
                "isolation_level": row[2],
                "state": row[3],
                "git_sha": row[4],
                "resources_allocated": json.loads(row[5]),
                "creation_timestamp": row[6],
                "last_update_timestamp": row[7],
                "error_log": row[8],
                "rollback_instructions": json.loads(row[9])
            }

    def list_experiments(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if state:
                cursor.execute("SELECT * FROM experiment_registry WHERE state = ?", (state,))
            else:
                cursor.execute("SELECT * FROM experiment_registry")
            rows = cursor.fetchall()
            conn.close()
            results = []
            for row in rows:
                results.append({
                    "experiment_id": row[0],
                    "hypothesis_id": row[1],
                    "isolation_level": row[2],
                    "state": row[3],
                    "git_sha": row[4],
                    "resources_allocated": json.loads(row[5]),
                    "creation_timestamp": row[6],
                    "last_update_timestamp": row[7],
                    "error_log": row[8],
                    "rollback_instructions": json.loads(row[9])
                })
            return results
