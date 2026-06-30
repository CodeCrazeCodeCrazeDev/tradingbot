"""
Improvement Registry - Phase 2 Self-Improvement Evaluation Framework
Records every system change, hypothesis, and validated outcome.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ImprovementRecord:
    change_id: str
    timestamp: str
    layer: str # Architecture, AI, Trading, Engineering
    hypothesis: str
    experiment_details: Dict[str, Any]
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    result: str # keep, reject, pending
    reasoning: str

class ImprovementRegistry:
    """
    Central repository for tracking system evolution and ROI of improvements.
    """
    def __init__(self, storage_path: str = "improvement_history"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.records: List[ImprovementRecord] = []
        self._load()

    def record_improvement(self, record: ImprovementRecord):
        self.records.append(record)
        logger.info(f"Recorded Improvement: {record.change_id} for layer {record.layer} - Result: {record.result}")
        self._save()

    def get_layer_stats(self) -> Dict[str, Any]:
        stats = {}
        for r in self.records:
            if r.layer not in stats:
                stats[r.layer] = {"total": 0, "kept": 0, "rejected": 0}
            stats[r.layer]["total"] += 1
            if r.result == "keep":
                stats[r.layer]["kept"] += 1
            elif r.result == "reject":
                stats[r.layer]["rejected"] += 1
        return stats

    def _save(self):
        file_path = self.storage_path / "registry.json"
        data = [asdict(r) for r in self.records]
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        file_path = self.storage_path / "registry.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.records = [ImprovementRecord(**r) for r in data]

    def get_summary_report(self) -> str:
        stats = self.get_layer_stats()
        report = ["# AlphaAlgo Improvement Summary Report", ""]
        for layer, s in stats.items():
            report.append(f"## {layer}")
            report.append(f"- Total Improvements: {s['total']}")
            report.append(f"- Kept: {s['kept']}")
            report.append(f"- Rejected: {s['rejected']}")
            report.append("")
        return "\n".join(report)

# Global instance for Phase 2
_registry = ImprovementRegistry()

def get_improvement_registry() -> ImprovementRegistry:
    return _registry
