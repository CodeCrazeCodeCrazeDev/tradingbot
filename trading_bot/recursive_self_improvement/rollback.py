import os
import shutil
import logging
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RollbackManager:
    """
    Manages versioning and rollbacks for system configurations, strategy parameters, and code.
    Ensures that bad improvements can be quickly reverted.
    """

    def __init__(self, base_path: str = "recursive_improvement_data/backups/"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, domain: str, name: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a backup snapshot of a configuration or parameter set.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        snapshot_id = f"{domain}_{name}_{timestamp}"
        snapshot_dir = self.base_path / domain / name
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        file_path = snapshot_dir / f"{timestamp}.json"

        content = {
            "snapshot_id": snapshot_id,
            "domain": domain,
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": metadata or {}
        }

        with open(file_path, "w") as f:
            json.dump(content, f, indent=4)

        logger.info(f"Created snapshot: {snapshot_id}")
        return snapshot_id

    def rollback(self, domain: str, name: str, snapshot_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Rollback to a specific snapshot or the previous one.
        """
        snapshot_dir = self.base_path / domain / name
        if not snapshot_dir.exists():
            logger.error(f"No snapshots found for {domain}/{name}")
            return None

        files = sorted(snapshot_dir.glob("*.json"), reverse=True)
        if not files:
            return None

        target_file = None
        if snapshot_id:
            for f in files:
                if snapshot_id in f.name:
                    target_file = f
                    break
        else:
            # If no ID, rollback to the one BEFORE the latest if possible,
            # or just the latest if only one exists.
            target_file = files[1] if len(files) > 1 else files[0]

        if not target_file:
            logger.error(f"Snapshot {snapshot_id} not found")
            return None

        with open(target_file, "r") as f:
            snapshot_data = json.load(f)

        logger.info(f"Rolling back {domain}/{name} to {snapshot_data['snapshot_id']}")
        return snapshot_data["data"]

    def cleanup_old_snapshots(self, domain: str, name: str, keep: int = 10):
        """
        Remove old snapshots beyond the keep limit.
        """
        snapshot_dir = self.base_path / domain / name
        if not snapshot_dir.exists():
            return

        files = sorted(snapshot_dir.glob("*.json"), reverse=True)
        if len(files) > keep:
            for f in files[keep:]:
                os.remove(f)
                logger.debug(f"Deleted old snapshot: {f.name}")
