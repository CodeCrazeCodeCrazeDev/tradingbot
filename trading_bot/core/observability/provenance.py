import logging
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class DataProvenanceEngine:
    """Tracks the origin and transformation lineage of all data used in reasoning."""
    def __init__(self):
        self.lineage_log = []

    def record_origin(self, data: Any, source: str, metadata: Dict = None) -> str:
        data_hash = hashlib.sha256(str(data).encode()).hexdigest()
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "hash": data_hash,
            "metadata": metadata or {}
        }
        self.lineage_log.append(entry)
        return data_hash

class DecisionLedger:
    """WORM (Write Once Read Many) storage for every system decision."""
    def __init__(self, storage_path: str = "alphaalgo_data/decisions.log"):
        self.storage_path = storage_path

    def commit_decision(self, decision: Any):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision": str(decision)
        }
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
