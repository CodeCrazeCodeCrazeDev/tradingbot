import os
import json
import hashlib
import sqlite3
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

class ResearchLedger:
    """
    Merkle-linked, immutable scientific ledger of record for all
    evaluated, promoted, and rejected research experiments.
    """
    def __init__(self, ledger_dir: str = "alphaalgo_data/ledger/"):
        self.ledger_dir = ledger_dir
        self.db_path = os.path.join(self.ledger_dir, "ledger_index.db")
        os.makedirs(self.ledger_dir, exist_ok=True)
        os.makedirs(os.path.join(self.ledger_dir, "records"), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ledger_index (
                    record_uuid TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    hypothesis_id TEXT NOT NULL,
                    git_sha TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    previous_record_hash TEXT NOT NULL
                );
            """)
            conn.commit()
            conn.close()

    def _calculate_sha256(self, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get_last_record_hash(self) -> str:
        """Fetch the hash of the preceding ledger entry to preserve the Merkle path."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT record_hash FROM ledger_index ORDER BY rowid DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "0" * 64

    def commit_record(
        self,
        record_uuid: str,
        hypothesis_id: str,
        git_context: Dict[str, str],
        configuration_hash: str,
        verification_report: Dict[str, Any],
        benchmark_metrics: Dict[str, Any],
        statistical_tests: Dict[str, Any],
        adversarial_audit_log: str,
        decision_rationale: str,
        promotion_outcome: str,
        rollback_instructions: Dict[str, str],
        originating_paper: str = "paper:unspecified"
    ) -> str:
        """Commit an experiment's full audit metadata with a Merkle parent hash."""
        previous_hash = self.get_last_record_hash()

        payload = {
            "record_uuid": record_uuid,
            "timestamp": datetime.utcnow().isoformat(),
            "originating_paper": originating_paper,
            "hypothesis_id": hypothesis_id,
            "git_context": git_context,
            "configuration_hash": configuration_hash,
            "verification_report": verification_report,
            "benchmark_metrics": benchmark_metrics,
            "statistical_tests": statistical_tests,
            "adversarial_audit_log": adversarial_audit_log,
            "decision_rationale": decision_rationale,
            "promotion_outcome": promotion_outcome,
            "rollback_instructions": rollback_instructions,
            "previous_record_hash": previous_hash
        }

        record_hash = self._calculate_sha256(payload)
        payload["record_hash"] = record_hash

        # Save JSON file
        record_path = os.path.join(self.ledger_dir, "records", f"{record_uuid}.json")
        with open(record_path, "w") as f:
            json.dump(payload, f, indent=2)

        # Index in DB
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ledger_index
                (record_uuid, timestamp, hypothesis_id, git_sha, outcome, record_hash, previous_record_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record_uuid,
                payload["timestamp"],
                hypothesis_id,
                git_context.get("promotion_sha", "none"),
                promotion_outcome,
                record_hash,
                previous_hash
            ))
            conn.commit()
            conn.close()

        return record_hash

    def scan_integrity(self) -> bool:
        """Recalculate hashes sequentially along the Merkle chain to detect tampering."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT record_uuid, record_hash, previous_record_hash FROM ledger_index ORDER BY rowid ASC")
            rows = cursor.fetchall()
            conn.close()

            expected_previous_hash = "0" * 64
            for uuid_val, record_hash, prev_hash in rows:
                if prev_hash != expected_previous_hash:
                    return False

                # Load JSON and recalculate
                record_path = os.path.join(self.ledger_dir, "records", f"{uuid_val}.json")
                if not os.path.exists(record_path):
                    return False
                with open(record_path, "r") as f:
                    data = json.load(f)

                # Exclude hash from own verification calculation
                raw_payload = {k: v for k, v in data.items() if k != "record_hash"}
                recomputed_hash = self._calculate_sha256(raw_payload)
                if recomputed_hash != record_hash:
                    return False

                expected_previous_hash = record_hash

            return True
