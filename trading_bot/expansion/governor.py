"""Resource governor — manages the resources this process actually has.

Claim #11 is honestly bounded: the bot manages *its own* host's
resources — CPU, memory, disk, threads — with measured usage against
explicit budgets. It does not allocate a global fleet; "global resource
management" was the fiction. Budget violations are reported as advisory
evidence so the electorate sees resource pressure the way it sees any
other signal.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_BUDGETS = {
    "cpu_percent": 85.0,
    "rss_mb": 4096.0,
    "disk_free_gb": 1.0,
    "threads": 512,
}


class ResourceGovernor:
    """Measures real process/host resources against budgets."""

    def __init__(self, state_dir: Any = ".",
                 budgets: Optional[Dict[str, float]] = None) -> None:
        self.state_dir = Path(state_dir)
        self.budgets = dict(DEFAULT_BUDGETS)
        if budgets:
            self.budgets.update({k: float(v) for k, v in
                                 budgets.items()})
        self._proc = None
        self._psutil = None

    def _ensure(self) -> bool:
        if self._psutil is not None:
            return True
        try:
            import psutil
            self._psutil = psutil
            self._proc = psutil.Process(os.getpid())
            return True
        except Exception:  # noqa: BLE001
            return False

    def measure(self) -> Dict[str, Any]:
        """Real measurements only. If psutil is unavailable the report
        says so — it does not fabricate load."""
        if not self._ensure():
            return {"status": "unavailable",
                    "reason": "psutil not installed",
                    "scope": "local_host"}
        p = self._proc
        ps = self._psutil
        try:
            rss_mb = p.memory_info().rss / (1024.0 * 1024.0)
        except Exception:  # noqa: BLE001
            rss_mb = None
        try:
            cpu = p.cpu_percent(interval=0.05)
        except Exception:  # noqa: BLE001
            cpu = None
        try:
            threads = p.num_threads()
        except Exception:  # noqa: BLE001
            threads = None
        try:
            anchor = self.state_dir if self.state_dir.exists() \
                else Path.cwd()
            disk_free_gb = ps.disk_usage(str(anchor)).free \
                / (1024.0 ** 3)
        except Exception:  # noqa: BLE001
            disk_free_gb = None
        violations = []
        if cpu is not None and cpu > self.budgets["cpu_percent"]:
            violations.append("cpu_percent")
        if rss_mb is not None and rss_mb > self.budgets["rss_mb"]:
            violations.append("rss_mb")
        if disk_free_gb is not None \
                and disk_free_gb < self.budgets["disk_free_gb"]:
            violations.append("disk_free_gb")
        if threads is not None and threads > self.budgets["threads"]:
            violations.append("threads")
        return {
            "status": "over_budget" if violations else "within_budget",
            "scope": "local_host",
            "cpu_percent": cpu,
            "rss_mb": round(rss_mb, 1) if rss_mb is not None else None,
            "disk_free_gb": round(disk_free_gb, 3)
            if disk_free_gb is not None else None,
            "threads": threads,
            "budgets": dict(self.budgets),
            "violations": violations,
            "note": ("manages the resources of the host this process "
                     "runs on — not a global fleet"),
        }

    def advisory(self, ctx: Any = None) -> Dict[str, Any]:
        return self.measure()
