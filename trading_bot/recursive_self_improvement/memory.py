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

            # Append-only hash-chained evidence ledger. trial_id and nonce are
            # UNIQUE so a signed verifier report cannot be replayed under a new
            # trial identity, and dropped trials cannot be silently hidden.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evidence_ledger (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    trial_id TEXT NOT NULL UNIQUE,
                    nonce TEXT NOT NULL UNIQUE,
                    status TEXT,
                    payload TEXT,
                    created_at TIMESTAMP
                )
            ''')

            # Enforce append-only at the database layer, not by convention.
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS evidence_ledger_no_update
                BEFORE UPDATE ON evidence_ledger
                BEGIN SELECT RAISE(ABORT, 'evidence_ledger is append-only'); END
            ''')
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS evidence_ledger_no_delete
                BEFORE DELETE ON evidence_ledger
                BEGIN SELECT RAISE(ABORT, 'evidence_ledger is append-only'); END
            ''')

            conn.commit()

    def _evidence_entry_hash(self, seq: int, prev_hash: str, trial_id: str,
                             nonce: str, status: str, payload: str, created_at: str) -> str:
        import hashlib
        body = json.dumps({
            "seq": seq, "prev_hash": prev_hash, "trial_id": trial_id, "nonce": nonce,
            "status": status, "payload": payload, "created_at": created_at,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def append_evidence(self, *, trial_id: str, nonce: str, payload: Dict[str, Any],
                        status: str = "") -> str:
        """Append one signed-evidence outcome to the hash-chained ledger.

        Duplicate ``trial_id`` or ``nonce`` raises (UNIQUE constraint) — callers
        treat any failure as insufficient evidence rather than retrying with a
        new identity.
        """
        created_at = datetime.utcnow().isoformat()
        payload_json = json.dumps(payload, sort_keys=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT seq, entry_hash FROM evidence_ledger ORDER BY seq DESC LIMIT 1')
            row = cursor.fetchone()
            seq, prev_hash = (row[0] + 1, row[1]) if row else (1, "GENESIS")
            entry_hash = self._evidence_entry_hash(seq, prev_hash, trial_id, nonce,
                                                   status, payload_json, created_at)
            cursor.execute('''
                INSERT INTO evidence_ledger (seq, entry_hash, prev_hash, trial_id, nonce, status, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (seq, entry_hash, prev_hash, trial_id, nonce, status, payload_json, created_at))
            conn.commit()
            return entry_hash

    def verify_evidence_chain(self) -> bool:
        """Verify ledger integrity: contiguity, linkage and entry hashes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM evidence_ledger ORDER BY seq ASC')
            rows = cursor.fetchall()
        expected_seq = 1
        prev_hash = "GENESIS"
        for row in rows:
            if row["seq"] != expected_seq or row["prev_hash"] != prev_hash:
                return False
            recomputed = self._evidence_entry_hash(
                row["seq"], row["prev_hash"], row["trial_id"], row["nonce"],
                row["status"] or "", row["payload"] or "", row["created_at"])
            if recomputed != row["entry_hash"]:
                return False
            prev_hash = row["entry_hash"]
            expected_seq += 1
        return True

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
