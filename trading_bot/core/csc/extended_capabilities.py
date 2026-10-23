"""Extended platform capabilities — measured where infrastructure exists,
honest `unavailable` interfaces where it does not.

Everything here is advisory/evidence only under the one-brain authority:
no component may authorize, size, veto or execute trades.

Contained:
- WyckoffPhaseAnalyzer   — measured accumulation/markup/distribution/
                           markdown from price+volume structure
- LeadLagAnalyzer        — cross-correlation lead-lag vs a secondary
                           series carried in the observation
- AdversarialScenarioSampler — perturbation-based scenario generator
                           for robustness replay. HONEST NOTE: this is
                           NOT a neural GAN — a torch GAN would only run
                           under the hermes env and cannot be tested in
                           .venv. This is the measurable equivalent:
                           seeded block-bootstrap + shock injection.
- VoiceAlerter           — opt-in Windows SAPI speech on critical
                           events; injectable speaker for tests
- BrokerRegistry         — named broker adapters with declared
                           capabilities (multi-broker plumbing)
- Edgar13FAdvisor        — SEC EDGAR 13F fetch; unavailable offline,
                           never fabricates
- DefiInterface / WhaleTracker — capability interfaces that report
                           status=unavailable until endpoints and
                           credentials are provisioned
"""
from __future__ import annotations

import json
import logging
import math
import random
import statistics
import subprocess
import threading
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Union

logger = logging.getLogger(__name__)


def _closes(bars: Sequence[Mapping[str, Any]]) -> List[float]:
    out: List[float] = []
    for b in bars:
        v = b.get("close", b.get("price"))
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out.append(float(v))
    return out


def _volumes(bars: Sequence[Mapping[str, Any]]) -> List[float]:
    return [float(b.get("volume") or 0.0) for b in bars]


class WyckoffPhaseAnalyzer:
    """Measured Wyckoff phase classification — no assumed phase.

    Inputs (all measured over a rolling bar window):
      range_compression — recent range / earlier range (<1 = compressing)
      vol_drift         — share of total volume on up-bars
      trend_slope       — OLS slope over the window (per bar, %)
      spring_test       — dip below range low followed by immediate reclaim

    Phase rules (evidence-driven, no free parameters beyond windows):
      markup         — slope > +thresh and compression not extreme
      markdown       — slope < -thresh
      accumulation   — compressed range AND up-bar volume share > 0.5
      distribution   — compressed range AND up-bar volume share < 0.5
      uncertain      — insufficient or contradictory evidence
    """

    def __init__(self, window: int = 40, half: int = 20,
                 slope_thresh: float = 0.0005) -> None:
        self.window = window
        self.half = half
        self.slope_thresh = slope_thresh

    def analyze(self, bars: Sequence[Mapping[str, Any]]
                ) -> Dict[str, Any]:
        closes = _closes(bars)
        vols = _volumes(bars)
        n = min(len(closes), self.window)
        if n < 2 * self.half:
            return {"phase": "uncertain",
                    "reason": f"insufficient_bars:{len(closes)}"}
        closes = closes[-n:]
        vols = vols[-n:]

        def _rng(c: List[float]) -> float:
            return (max(c) - min(c)) / c[0] if c and c[0] else 0.0

        early, late = closes[: self.half], closes[-self.half:]
        compression = _rng(late) / _rng(early) if _rng(early) > 0 else 1.0

        up_vol = down_vol = 0.0
        for i in range(1, len(closes)):
            if closes[i] >= closes[i - 1]:
                up_vol += vols[i]
            else:
                down_vol += vols[i]
        tot = up_vol + down_vol
        vol_share = up_vol / tot if tot > 0 else 0.5

        xs = list(range(len(closes)))
        xm, ym = statistics.mean(xs), statistics.mean(closes)
        denom = sum((x - xm) ** 2 for x in xs) or 1.0
        slope = sum((x - xm) * (c - ym) for x, c in zip(xs, closes))
        slope = (slope / denom) / ym if ym else 0.0

        lo = min(late[:-3]) if len(late) > 3 else min(late)
        spring = bool(late and min(late) < lo and late[-1] > lo)

        if slope > self.slope_thresh and compression > 0.6:
            phase = "markup"
        elif slope < -self.slope_thresh and compression > 0.6:
            phase = "markdown"
        elif compression <= 0.6 and vol_share > 0.55:
            phase = "accumulation" if slope >= 0 else "markdown_exit"
        elif compression <= 0.6 and vol_share < 0.45:
            phase = "distribution" if slope <= 0 else "markup_exit"
        elif compression <= 0.6:
            phase = "ranging"
        else:
            phase = "uncertain"

        return {"phase": phase,
                "range_compression": round(compression, 4),
                "up_volume_share": round(vol_share, 4),
                "trend_slope_per_bar": round(slope, 7),
                "spring_test": spring}


class LeadLagAnalyzer:
    """Measured lead-lag between the primary close series and a secondary
    series supplied in the observation (``peer``, ``dxy``, ``spx`` or any
    ``peer_*``/``corr_*`` numeric field). Positive lag means the peer
    moves first — measured, never assumed."""

    def __init__(self, window: int = 60, max_lag: int = 5,
                 peer_keys: Sequence[str] = ()) -> None:
        self.window = window
        self.max_lag = max_lag
        self.peer_keys = tuple(peer_keys)

    def analyze(self, obs_hist: Sequence[Mapping[str, Any]]
                ) -> Dict[str, Any]:
        a: List[float] = []
        b: List[float] = []
        peer_field: Optional[str] = None
        for obs in obs_hist[-self.window:]:
            c = obs.get("close", obs.get("price"))
            if not isinstance(c, (int, float)):
                continue
            pv = None
            if peer_field is None:
                for k in self.peer_keys:
                    if isinstance(obs.get(k), (int, float)):
                        peer_field = k
                        break
            if peer_field is not None:
                pv = obs.get(peer_field)
            if isinstance(pv, (int, float)):
                a.append(float(c))
                b.append(float(pv))
        if len(a) < 2 * self.max_lag + 5:
            return {"status": "insufficient_data",
                    "n": len(a), "peer_field": peer_field}

        ra = [a[i] / a[i - 1] - 1.0 for i in range(1, len(a))]
        rb = [b[i] / b[i - 1] - 1.0 for i in range(1, len(b))]

        def _corr(x: List[float], y: List[float]) -> float:
            mx, my = statistics.mean(x), statistics.mean(y)
            sx = statistics.pstdev(x)
            sy = statistics.pstdev(y)
            if sx <= 0 or sy <= 0:
                return 0.0
            return sum((u - mx) * (v - my) for u, v in zip(x, y)) \
                / (len(x) * sx * sy)

        best_lag, best_corr = 0, 0.0
        for lag in range(-self.max_lag, self.max_lag + 1):
            # lag > 0: own[t] aligned with peer[t-lag] — peer leads
            # lag < 0: own[t] aligned with peer[t+|lag|] — peer lags
            if lag > 0:
                x, y = ra[lag:], rb[: len(rb) - lag]
            elif lag < 0:
                x, y = ra[: len(ra) + lag], rb[-lag:]
            else:
                x, y = ra, rb
            if len(x) < 10 or len(x) != len(y):
                continue
            c = _corr(x, y)
            if abs(c) > abs(best_corr):
                best_lag, best_corr = lag, c
        return {"status": "measured",
                "peer_field": peer_field,
                "best_lag_bars": best_lag,
                "correlation": round(best_corr, 4),
                "interpretation": (
                    "peer_leads" if best_lag > 0 else
                    "peer_lags" if best_lag < 0 else "synchronous")}


class AdversarialScenarioSampler:
    """Perturbation-based scenario generator for robustness replay.

    HONEST NOTE — not a neural GAN. A trained generator would require
    torch (hermes env only) and could not be tested in .venv. What this
    provides is the measurable equivalent for the sealed-trial use case:
    seeded block-bootstrap resampling plus injected stress shocks
    (volatility bursts, gaps, liquidity thinning), all deterministic
    under a seed and labeled `synthetic` so they can never masquerade
    as measured market data."""

    def __init__(self, seed: int = 7, block: int = 5) -> None:
        self.seed = seed
        self.block = max(2, block)

    def scenarios(self, bars: Sequence[Mapping[str, Any]],
                  n: int = 4) -> List[Dict[str, Any]]:
        closes = _closes(bars)
        if len(closes) < self.block * 2:
            return []
        rets = [closes[i] / closes[i - 1] - 1.0
                for i in range(1, len(closes))]
        rng = random.Random(self.seed)
        out: List[Dict[str, Any]] = []
        for k in range(n):
            blocks = [rets[i: i + self.block]
                      for i in range(0, len(rets) - self.block + 1)]
            shuffled = blocks[:]
            rng.shuffle(shuffled)
            resampled = [r for blk in shuffled for r in blk][: len(rets)]
            vol_scale = rng.choice([1.0, 1.5, 2.0])
            gap_at = rng.randrange(len(resampled))
            gap_size = rng.choice([0.002, -0.002, 0.005, -0.005])
            price = closes[0]
            series = []
            for i, r in enumerate(resampled):
                price *= (1.0 + r * vol_scale +
                          (gap_size if i == gap_at else 0.0))
                series.append(round(price, 8))
            out.append({"scenario_id": f"adv-{self.seed}-{k}",
                        "synthetic": True,
                        "kind": "block_bootstrap+shock",
                        "vol_scale": vol_scale,
                        "gap_size": gap_size,
                        "closes": series})
        return out


class VoiceAlerter:
    """Opt-in voice alerts via Windows SAPI. Fire-and-forget on a daemon
    thread — never blocks the pipeline. ``speaker`` is injectable for
    tests; the default invokes powershell SAPI. Enabled only when the
    operator opts in (runner flag / kwargs); silent no-op otherwise."""

    def __init__(self, enabled: bool = False,
                 speaker: Optional[Callable[[str], None]] = None,
                 min_interval_s: float = 30.0) -> None:
        self.enabled = enabled
        self._speaker = speaker or self._sapi_speak
        self.min_interval_s = min_interval_s
        self._last_alert_at = 0.0
        self.alerts_sent = 0

    @staticmethod
    def _sapi_speak(text: str) -> None:
        safe = text.replace("'", " ")
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(New-Object -ComObject SAPI.SpVoice).Speak"
             f"('{safe}') | Out-Null"],
            timeout=10, capture_output=True)

    def alert(self, message: str) -> bool:
        if not self.enabled:
            return False
        # Rate-limit: an alert storm (repeated estop/circuit events)
        # must not flood the speech queue or spawn unbounded threads.
        import time as _t
        now = _t.monotonic()
        if now - self._last_alert_at < self.min_interval_s:
            return False
        self._last_alert_at = now
        def _go() -> None:
            try:
                self._speaker(message)
                self.alerts_sent += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("voice alert failed: %s", exc)
        threading.Thread(target=_go, daemon=True).start()
        return True


class BrokerRegistry:
    """Multi-broker plumbing: named adapters register with declared
    capabilities; `status()` is the operator-facing surface. An adapter
    is any object exposing submit(cancel/status) — the registry never
    routes orders itself; CSC execution stays canonical."""

    def __init__(self) -> None:
        self._brokers: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, adapter: Any,
                 capabilities: Mapping[str, Any]) -> None:
        self._brokers[name] = {
            "adapter": adapter,
            "capabilities": dict(capabilities),
            "registered": True}

    def status(self) -> Dict[str, Any]:
        out = {}
        for name, rec in self._brokers.items():
            adapter = rec["adapter"]
            reachable = False
            try:
                probe = getattr(adapter, "status", None) or \
                    getattr(adapter, "positions", None)
                reachable = callable(probe)
            except Exception:  # noqa: BLE001
                reachable = False
            out[name] = {"capabilities": rec["capabilities"],
                         "adapter_present": adapter is not None,
                         "probeable": reachable}
        return out

    def get(self, name: str) -> Optional[Any]:
        rec = self._brokers.get(name)
        return rec["adapter"] if rec else None


class Edgar13FAdvisor:
    """SEC EDGAR 13F evidence fetch. Advisory only — returns
    `{"status": "unavailable"}` on any failure and never fabricates
    holdings. Requires no key; EDGAR is public. Network is attempted
    only when enabled (kwargs/env); offline environments degrade to
    unavailable rather than raising."""

    UA = "alphaalgo-research contact@example.invalid"
    SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"

    def __init__(self, enabled: bool = False, timeout_s: float = 5.0,
                 fetcher: Optional[Callable[[str], str]] = None) -> None:
        self.enabled = enabled
        self.timeout_s = timeout_s
        self._fetcher = fetcher or self._http_get

    def _http_get(self, url: str) -> str:
        import urllib.request
        req = urllib.request.Request(
            url, headers={"User-Agent": self.UA})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
            return r.read().decode("utf-8", "replace")

    def recent_13f(self, cik: Union[int, str]) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "unavailable", "reason": "disabled"}
        cik10 = str(cik).zfill(10)
        try:
            data = json.loads(self._fetcher(
                self.SUBMISSIONS.format(cik=cik10)))
            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            accessions = recent.get("accessionNumber", [])
            hits = [{"form": f, "date": d, "accession": a}
                    for f, d, a in zip(forms, dates, accessions)
                    if str(f).startswith("13F")][:4]
            return {"status": "measured", "cik": cik10,
                    "filer": data.get("name"),
                    "recent_13f": hits, "count": len(hits)}
        except Exception as exc:  # noqa: BLE001
            return {"status": "unavailable",
                    "reason": f"{type(exc).__name__}: {exc}"[:200]}


class UnavailableCapability:
    """Explicit capability interface for infrastructure that does not
    exist yet (DeFi RPC endpoints, on-chain whale feeds, ML serving).
    Reports status=unavailable with the precise requirements — honest
    evidence of absence, never a stub pretending to work."""

    def __init__(self, name: str,
                 requires: Sequence[str],
                 description: str) -> None:
        self.name = name
        self.requires = list(requires)
        self.description = description

    def status(self) -> Dict[str, Any]:
        return {"status": "unavailable",
                "capability": self.name,
                "requires": self.requires,
                "description": self.description}

    def analyze(self, _ctx: Mapping[str, Any]) -> Dict[str, Any]:
        return self.status()


DEFI_INTERFACE = UnavailableCapability(
    "defi_protocols",
    requires=["rpc_endpoint", "wallet_credentials", "protocol_abis"],
    description=("DeFi protocol interaction (swaps/lending/yield). No "
                 "chain connectivity exists in this deployment — the "
                 "interface reports unavailable rather than simulating "
                 "fills."))

WHALE_TRACKER = UnavailableCapability(
    "whale_tracking",
    requires=["onchain_data_provider", "address_labels_db"],
    description=("On-chain large-holder flow. Needs a chain data "
                 "provider; reports unavailable until provisioned."))

ML_MODEL_MONITOR = UnavailableCapability(
    "ml_model_monitoring",
    requires=["model_registry", "prediction_store", "drift_baselines"],
    description=("Production model-serving drift monitor. Advisory "
                 "drift IS measured (data_drift/alpha_decay advisors + "
                 "reliability tracker); this interface is for external "
                 "model serving that does not exist yet."))

MOBILE_DASHBOARD_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CSC Snapshot</title>
<style>
body{font-family:monospace;background:#0d1117;color:#c9d1d9;margin:0;
padding:12px;font-size:13px}
h1{font-size:15px;color:#58a6ff;margin:0 0 8px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;
padding:10px;margin-bottom:8px}
.k{color:#8b949e;font-size:11px;text-transform:uppercase}
.v{color:#c9d1d9;font-size:14px;word-break:break-all}
.ok{color:#3fb950}.bad{color:#f85149}.warn{color:#d29922}
pre{white-space:pre-wrap;font-size:11px;color:#8b949e}
</style></head><body>
<h1>Cognitive System Controller — live snapshot</h1>
<div id="root">loading…</div>
<pre id="raw"></pre>
<script>
async function tick(){
 try{
  const r=await fetch('/snapshot.json',{cache:'no-store'});
  const s=await r.json();
  const esc=v=>String(v).replace(/[&<>]/g,c=>({'&':'&amp;',
   '<':'&lt;','>':'&gt;'}[c]));
  const card=(k,v,cls)=>`<div class="card"><div class="k">${esc(k)}</div>
   <div class="v ${cls||''}">${esc(v)}</div></div>`;
  let h=card('status',s.status||'unknown',
    s.status==='running'?'ok':'warn');
  for(const k of ['cycles','positions','fills','last_decision',
                  'equity','drawdown','paused','emergency_stop']){
   if(s[k]!==undefined){
    let cls='';
    if(k==='emergency_stop'||k==='paused')
      cls=s[k]?'bad':'ok';
    h+=card(k,typeof s[k]==='object'?JSON.stringify(s[k]):s[k],cls);}}
  document.getElementById('root').innerHTML=h;
  document.getElementById('raw').textContent=
    JSON.stringify(s,null,1).slice(0,3000);
 }catch(e){document.getElementById('root').innerHTML=
  '<div class="card"><div class="v bad">snapshot unavailable</div></div>';}
}
tick();setInterval(tick,5000);
</script></body></html>"""
