"""Real data-resource inventory and onboarding.

"Infrastructure expansion" honestly means: resources this process can
actually use coming online — a market-data database with a verifiable
schema and rows, a state directory it owns. It does not provision
servers, regions, or clusters; anything claiming that would be fiction.

The inventory probes SQLite ``market_data`` tables read-only and records
what exists. ``onboard`` validates that a path is a real market-data
source before registering it — onboarding is a gate, not a formality.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

DEFAULT_SOURCES = (
    "market_data.db",
    "hl_data.db",
    "binance_data.db",
    "lse_data.db",
    "tv_data.db",
    "kraken_data.db",
    "us_stocks.db",
    "fx_data.db",
)

REQUIRED_COLS = {"timestamp", "symbol", "timeframe", "close"}


def _utc(ts: Any) -> Optional[str]:
    return str(ts) if ts else None


class DataResourceInventory:
    """Catalog of real, probed data resources."""

    def __init__(self, root: Any, sources: Iterable[str] = DEFAULT_SOURCES,
                 state_path: Optional[Any] = None) -> None:
        self.root = Path(root)
        self.sources = list(sources)
        self.state_path = Path(state_path) if state_path else None
        self._onboarded: List[str] = self._load_onboarded()

    # -- probing ----------------------------------------------------

    @staticmethod
    def probe_db(path: Any) -> Optional[Dict[str, Any]]:
        """Read-only probe of one SQLite file. Returns None if the file
        is not a usable market_data source."""
        p = Path(path)
        if not p.exists() or not p.is_file():
            return None
        try:
            con = sqlite3.connect(p.resolve().as_uri() + "?mode=ro",
                                  uri=True)
        except sqlite3.Error:
            return None
        try:
            tables = {r[0]: r[1] for r in con.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table'")}
            if "market_data" not in tables:
                return None
            cols = {c[1] for c in con.execute(
                'PRAGMA table_info("market_data")')}
            if not REQUIRED_COLS.issubset(cols):
                return None
            rows = []
            for sym, tf, n, first, last in con.execute(
                    "SELECT symbol, timeframe, COUNT(*), MIN(timestamp), "
                    "MAX(timestamp) FROM market_data "
                    "GROUP BY symbol, timeframe"):
                rows.append({
                    "symbol": sym, "timeframe": tf, "rows": n,
                    "first": _utc(first), "last": _utc(last),
                })
            return {"path": str(p), "size_bytes": p.stat().st_size,
                    "series": rows,
                    "total_rows": sum(r["rows"] for r in rows)}
        except sqlite3.Error:
            return None
        finally:
            con.close()

    # -- catalog -----------------------------------------------------

    def scan(self) -> Dict[str, Any]:
        """Probe every known + onboarded source. Real numbers only."""
        catalog: Dict[str, Any] = {"generated_at": time.time(),
                                   "sources": {}}
        for name in list(self.sources) + [
                s for s in self._onboarded if s not in self.sources]:
            p = self.root / name if not Path(name).is_absolute() else Path(name)
            probe = self.probe_db(p)
            catalog["sources"][name] = (
                probe if probe is not None else {"status": "unavailable"})
        catalog["series_total"] = sum(
            len(s.get("series", ()))
            for s in catalog["sources"].values())
        catalog["rows_total"] = sum(
            s.get("total_rows", 0) for s in catalog["sources"].values())
        return catalog

    def all_series(self, catalog: Optional[Dict[str, Any]] = None
                   ) -> List[Tuple[str, str, str]]:
        """(source, symbol, timeframe) for every probed series."""
        cat = catalog or self.scan()
        out = []
        for src, s in cat["sources"].items():
            for e in s.get("series", ()):
                out.append((src, e["symbol"], e["timeframe"]))
        return out

    def coverage_gaps(self, active: Iterable[Tuple[str, str]],
                      catalog: Optional[Dict[str, Any]] = None
                      ) -> List[Dict[str, Any]]:
        """Series present in data but NOT in the bot's active trading
        set — honest 'new markets': tradable coverage we hold but do not
        currently trade."""
        have = set(active)
        gaps = []
        for src, sym, tf in self.all_series(catalog):
            if (sym, tf) not in have:
                gaps.append({"source": src, "symbol": sym,
                             "timeframe": tf})
        return gaps

    # -- onboarding (#10) ---------------------------------------------

    def onboard(self, path: Any) -> Dict[str, Any]:
        """Bring a real data resource online. Validates the schema and
        requires at least one row — a file that proves nothing is not
        infrastructure."""
        probe = self.probe_db(path)
        if probe is None or not probe["series"]:
            return {"status": "rejected",
                    "reason": "not a usable market_data source"}
        key = str(Path(path))
        if key not in self._onboarded:
            self._onboarded.append(key)
            self._save_onboarded()
        return {"status": "onboarded", "path": key,
                "series": len(probe["series"]),
                "rows": probe["total_rows"]}

    def onboarded(self) -> List[str]:
        return list(self._onboarded)

    # -- resource expansion (#10 general form) ------------------------

    def onboard_resource(self, path: Any, kind: str = "generic"
                         ) -> Dict[str, Any]:
        """Register ANY verified SQLite resource the system can consume
        — order-flow stores, tick stores, sentiment, ledgers. Expanding
        infrastructure honestly means new data classes coming online
        with schema and row counts verified, not servers claimed."""
        p = Path(path)
        if not p.exists():
            return {"status": "rejected", "reason": "file not found"}
        try:
            con = sqlite3.connect(p.resolve().as_uri() + "?mode=ro",
                                  uri=True)
            tables = {}
            for name, in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"):
                try:
                    tables[name] = con.execute(
                        f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                except sqlite3.Error:
                    tables[name] = -1
            con.close()
        except sqlite3.Error:
            return {"status": "rejected",
                    "reason": "not a readable sqlite resource"}
        if not any(v > 0 for v in tables.values()):
            return {"status": "rejected",
                    "reason": "no rows — an empty store is not a resource"}
        res = {"path": str(p), "kind": kind, "tables": tables,
               "size_bytes": p.stat().st_size}
        state = self._load_state()
        res_list = state.setdefault("resources", [])
        if not any(r["path"] == res["path"] for r in res_list):
            res_list.append(res)
            self._save_state(state)
        return {"status": "onboarded", **res}

    def resources(self) -> List[Dict[str, Any]]:
        return list(self._load_state().get("resources", []))

    def _load_state(self) -> Dict[str, Any]:
        if self.state_path and self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except Exception:  # noqa: BLE001
                return {}
        return {}

    def _save_state(self, state: Dict[str, Any]) -> None:
        if not self.state_path:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2))
        tmp.replace(self.state_path)

    def _load_onboarded(self) -> List[str]:
        if self.state_path and self.state_path.exists():
            try:
                return list(json.loads(
                    self.state_path.read_text()).get("onboarded", []))
            except Exception:  # noqa: BLE001
                return []
        return []

    def _save_onboarded(self) -> None:
        if not self.state_path:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"onboarded": self._onboarded},
                                  indent=2))
        tmp.replace(self.state_path)
