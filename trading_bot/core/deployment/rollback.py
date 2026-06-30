"""
Rollback System - Phase 3 Safety
Versioning and state recovery for the AlphaAlgo system.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class StateSnapshot:
    version: str
    timestamp: str
    weights_path: str
    config: Dict[str, Any]
    performance_summary: Dict[str, float]
    rollback_path: Optional[str] = None

class RollbackSystem:
    """
    Maintains a historical record of system states to enable millisecond recovery.
    """
    def __init__(self, storage_path: str = "system_versions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.snapshots: List[StateSnapshot] = []
        self._load()

    def create_snapshot(self, weights_path: str, config: Dict[str, Any], performance: Dict[str, float]) -> str:
        version = f"v{len(self.snapshots) + 1}_{datetime.now().strftime('%Y%m%d%H%M')}"
        rollback_v = self.snapshots[-1].version if self.snapshots else None

        snapshot = StateSnapshot(
            version=version,
            timestamp=datetime.now().isoformat(),
            weights_path=weights_path,
            config=config,
            performance_summary=performance,
            rollback_path=rollback_v
        )
        self.snapshots.append(snapshot)
        self._save()
        logger.info(f"Created System Snapshot: {version}")
        return version

    def get_rollback_version(self, current_version: str) -> Optional[StateSnapshot]:
        for s in self.snapshots:
            if s.version == current_version:
                prev_v = s.rollback_path
                return next((snap for snap in self.snapshots if snap.version == prev_v), None)
        return None

    def _save(self):
        with open(self.storage_path / "versions.json", 'w') as f:
            json.dump([asdict(s) for s in self.snapshots], f, indent=2)

    def _load(self):
        file = self.storage_path / "versions.json"
        if file.exists():
            with open(file, 'r') as f:
                data = json.load(f)
                self.snapshots = [StateSnapshot(**d) for d in data]
