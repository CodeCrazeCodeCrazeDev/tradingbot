"""
Hierarchical Memory System (HMS) - UCA-2026 Core
==============================================

Authoritative memory system for storing episodic research traces,
semantic facts, and generalized scientific lessons.
"""

import logging
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from .models import ResearchLedgerEntry, ScientificMemoryObject

logger = logging.getLogger(__name__)

class HierarchicalMemorySystem:
    """
    Manages the persistent storage and retrieval of research artifacts.
    """

    def __init__(self, base_path: str = "alphaalgo_data/hms"):
        self.base_path = base_path
        self.ledger_path = os.path.join(base_path, "research_ledger")
        self.knowledge_path = os.path.join(base_path, "scientific_memory")

        os.makedirs(self.ledger_path, exist_ok=True)
        os.makedirs(self.knowledge_path, exist_ok=True)

    def store_ledger_entry(self, entry: ResearchLedgerEntry):
        """Persists a complete research snapshot to the ledger."""
        file_path = os.path.join(self.ledger_path, f"{entry.entry_id}.json")

        # In a real implementation, we would use a proper DB and handle graph serialization
        # For now, we mock the serialization
        entry_data = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp.isoformat(),
            "trade_id": entry.trade_id,
            "hypothesis": entry.hypothesis.description if entry.hypothesis else "N/A",
            "composite_confidence": entry.composite_confidence,
            "verifier_reports": [
                {"agent": r.agent_name, "valid": r.is_valid, "critique": r.critique}
                for r in entry.verifier_reports
            ],
            "evidence_node_count": len(entry.evidence_graph_snapshot.nodes)
        }

        with open(file_path, 'w') as f:
            json.dump(entry_data, f, indent=2)

        logger.info(f"HMS: Persisted ledger entry {entry.entry_id}")

    def store_scientific_lesson(self, lesson: ScientificMemoryObject):
        """Stores a generalized lesson derived from research outcomes."""
        file_path = os.path.join(self.knowledge_path, f"{lesson.object_id}.json")

        lesson_data = {
            "object_id": lesson.object_id,
            "pattern_type": lesson.pattern_type,
            "lesson": lesson.generalized_lesson,
            "reproducibility": lesson.reproducibility_score,
            "timestamp": lesson.last_updated.isoformat()
        }

        with open(file_path, 'w') as f:
            json.dump(lesson_data, f, indent=2)

        logger.info(f"HMS: Persisted scientific lesson {lesson.object_id}")

    def get_ledger_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        file_path = os.path.join(self.ledger_path, f"{entry_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None
