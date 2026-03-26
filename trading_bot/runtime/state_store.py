from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class RuntimeStateStore:
    def __init__(self, path: str = "state/runtime_state.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save(self, payload: Dict[str, Any]) -> None:
        data = dict(payload)
        data["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
