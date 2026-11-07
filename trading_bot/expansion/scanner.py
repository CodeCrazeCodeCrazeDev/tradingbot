"""Opportunity scanner — measured market structure, not random branches.

Claims covered:

- #12 global opportunity detection: scans every data source the bot
  actually has (the real boundary of "global"), all instruments and
  timeframes, and scores *structure* — deviation from a random walk —
  not edge. A high structure score means "worth evaluating", never
  "worth trading".
- #13 emerging markets: regime-shift detection on tradable instruments —
  measured volatility-regime expansion or trend-persistence change.
- #15 new industries: tradable series found in onboarded sources that
  are not in the active trading set — new markets *to us*, honestly
  framed.

All statistics are deterministic functions of real closes. No random
gates, no hardcoded opportunity lists.
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

MIN_BARS = 60
VOL_SHIFT_THRESHOLD = 1.8
PERSIST_SHIFT = 0.12


def _closes(rows: Iterable[Tuple]) -> List[float]:
    return [float(r[0]) for r in rows if r and r[0] is not None
            and float(r[0]) > 0]


def series_stats(closes: List[float]) -> Optional[Dict[str, Any]]:
    """Deterministic structure statistics over a close series.

    Returns None when there is not enough data to say anything honest."""
    if len(closes) < MIN_BARS:
        return None
    rets = [math.log(closes[i] / closes[i - 1])
            for i in range(1, len(closes)) if closes[i - 1] > 0]
    n = len(rets)
    if n < MIN_BARS - 1:
        return None
    mu = sum(rets) / n
    var = sum((r - mu) ** 2 for r in rets) / max(n - 1, 1)
    vol = math.sqrt(var)
    if vol <= 0:
        return None
    # lag-1 return autocorrelation: negative -> mean-reverting structure,
    # positive -> trending structure. Measured, not assumed.
    num = sum(rets[i] * rets[i - 1] for i in range(1, n))
    den = sum(r * r for r in rets) or 1.0
    ret_autocorr = num / den
    # sign persistence: fraction of consecutive same-direction bars.
    signs = [1 if r > 0 else -1 for r in rets]
    sign_persist = sum(1 for i in range(1, n)
                       if signs[i] == signs[i - 1]) / (n - 1)
    # volatility regime: last-quarter vol vs the prior three quarters.
    cut = n - n // 4
    v_old = math.sqrt(sum((r - mu) ** 2 for r in rets[:cut])
                      / max(cut - 1, 1))
    v_new = math.sqrt(sum((r - mu) ** 2 for r in rets[cut:])
                      / max(n - cut - 1, 1))
    vol_regime_ratio = (v_new / v_old) if v_old > 0 else 1.0
    # trend persistence shift: recent-quarter sign persistence vs prior.
    sp_old = (sum(1 for i in range(1, cut)
                  if signs[i] == signs[i - 1]) / max(cut - 1, 1))
    sp_new = (sum(1 for i in range(cut, n)
                  if signs[i] == signs[i - 1]) / max(n - cut - 1, 1))
    trend = (closes[-1] - closes[0]) / closes[0]
    # structure score: how far this series sits from a coin-flip walk.
    # Bounded [0, ~1]; a score is a prioritization hint, not an edge.
    structure = min(1.0, abs(ret_autocorr) * 2.0
                    + 2.0 * abs(sign_persist - 0.5))
    shift = min(1.0, abs(vol_regime_ratio - 1.0) / 2.0
                + abs(sp_new - sp_old))
    return {
        "bars": len(closes),
        "vol_per_bar": round(vol, 6),
        "ret_autocorr": round(ret_autocorr, 4),
        "sign_persistence": round(sign_persist, 4),
        "vol_regime_ratio": round(vol_regime_ratio, 4),
        "trend_pct": round(trend * 100.0, 3),
        "structure_score": round(structure, 4),
        "regime_shift_score": round(shift, 4),
        "emerging_regime": bool(vol_regime_ratio >= VOL_SHIFT_THRESHOLD
                                or abs(sp_new - sp_old)
                                >= PERSIST_SHIFT),
    }


class OpportunityScanner:
    """Scans every onboarded data source for measurable structure."""

    def __init__(self, inventory: Any, active: Optional[set] = None,
                 tail_bars: int = 2000) -> None:
        self.inventory = inventory
        self.active = set(active or ())
        self.tail_bars = int(tail_bars)

    @staticmethod
    def _load_closes(db_path: Path, symbol: str, timeframe: str,
                     limit: int) -> List[float]:
        con = sqlite3.connect(
            db_path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            rows = con.execute(
                "SELECT close FROM (SELECT close, timestamp FROM "
                "market_data WHERE symbol=? AND timeframe=? "
                "ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp",
                (symbol, timeframe, limit)).fetchall()
            return _closes(rows)
        finally:
            con.close()

    def scan_all(self, catalog: Optional[Dict[str, Any]] = None
                 ) -> Dict[str, Any]:
        cat = catalog or self.inventory.scan()
        opportunities: List[Dict[str, Any]] = []
        emerging: List[Dict[str, Any]] = []
        new_markets: List[Dict[str, Any]] = []
        scanned = 0
        for src, s in cat["sources"].items():
            path = s.get("path")
            if not path:
                continue
            for e in s.get("series", ()):
                closes = self._load_closes(
                    Path(path), e["symbol"], e["timeframe"],
                    self.tail_bars)
                st = series_stats(closes)
                if st is None:
                    continue
                scanned += 1
                rec = {"source": src, "symbol": e["symbol"],
                       "timeframe": e["timeframe"],
                       "first": e["first"], "last": e["last"],
                       **st}
                if rec["structure_score"] >= 0.3:
                    opportunities.append(rec)
                if rec["emerging_regime"]:
                    emerging.append(rec)
                if (e["symbol"], e["timeframe"]) not in self.active:
                    new_markets.append({
                        "source": src, "symbol": e["symbol"],
                        "timeframe": e["timeframe"],
                        "rows": e["rows"],
                        "structure_score": rec["structure_score"]})
        opportunities.sort(key=lambda r: r["structure_score"],
                           reverse=True)
        return {
            "series_scanned": scanned,
            "opportunities": opportunities,
            "emerging_regimes": emerging,
            "new_markets": new_markets,
            "note": ("structure_score measures deviation from a "
                     "coin-flip walk — it prioritizes evaluation, it "
                     "is not evidence of tradeable edge"),
        }

    def advisory(self, catalog: Optional[Dict[str, Any]] = None
                 ) -> Dict[str, Any]:
        """Compact advisory-artifact payload for the evidence channel."""
        out = self.scan_all(catalog)
        return {
            "series_scanned": out["series_scanned"],
            "top_opportunity": (out["opportunities"][0]
                                if out["opportunities"] else None),
            "emerging_regimes": [
                {"symbol": r["symbol"], "timeframe": r["timeframe"],
                 "vol_regime_ratio": r["vol_regime_ratio"]}
                for r in out["emerging_regimes"][:5]],
            "new_market_count": len(out["new_markets"]),
        }
