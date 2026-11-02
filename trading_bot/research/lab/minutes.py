"""
Institutional Lab Minutes Ledger.

An append-only, auditable record of every pipeline stage executed under a lab
program — the research-lab equivalent of board minutes: which division acted,
what it concluded, and what evidence it produced.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LabMinute:
    """A single minute recording one division's action at one pipeline stage."""
    minute_id: str
    task_id: str
    division: str
    stage: str
    status: str  # completed | failed | rejected
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "minute_id": self.minute_id,
            "task_id": self.task_id,
            "division": self.division,
            "stage": self.stage,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class LabMinutesLedger:
    """Institutional audit trail of lab activity, replayable per program."""

    def __init__(self) -> None:
        self._minutes: List[LabMinute] = []

    def record(self, task_id: Optional[str], division: str, stage: str,
               status: str, details: Optional[Dict[str, Any]] = None) -> LabMinute:
        minute = LabMinute(
            minute_id=f"min_{uuid.uuid4().hex[:8]}",
            task_id=task_id or "unassigned",
            division=division,
            stage=stage,
            status=status,
            details=details or {},
        )
        self._minutes.append(minute)
        return minute

    def replay_task(self, task_id: str) -> List[LabMinute]:
        """Return the ordered minutes for a single research program."""
        return [m for m in self._minutes if m.task_id == task_id]

    def divisions_engaged(self, task_id: str) -> List[str]:
        """Ordered unique divisions that acted during a program."""
        seen: List[str] = []
        for m in self.replay_task(task_id):
            if m.division not in seen:
                seen.append(m.division)
        return seen

    def failed_stages(self, task_id: str) -> List[LabMinute]:
        return [m for m in self.replay_task(task_id) if m.status != "completed"]

    def __len__(self) -> int:
        return len(self._minutes)

    def export(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._minutes]
