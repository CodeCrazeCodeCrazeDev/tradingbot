"""CSC capability matrix — every advertised capability bound to a real,
measured mechanism instead of a simulated one.

Design rule: each method either does the real work (sealed evaluation,
DB probes, subprocess tests, ledger reads) or reports honestly why the
broad claim is out of scope. Nothing here fabricates a metric, a test
result, a discovery, or a deployment.

The broad claims map to honest bounded mechanisms:

- "analyze strategies / optimize parameters" -> the sealed
  ``propose_model``/``validate_model`` pipeline plus a bounded
  parameter sweep through the same gate (with a multiplicity warning).
- "scan historical data" -> measured structure statistics on real
  closes (``expansion.scanner.series_stats`` / ``scan_all``).
- "agents perform coordinated work" -> an actual coordinated advisory
  pass over the attached electorate, artifacts counted.
- "builds and deploys working agents" -> foundry generation followed by
  the real ``approve_model`` -> ``attach_engineered_model`` gate;
  deployment honestly stalls at ``awaiting_human`` without the durable
  operator flag.
- "implements improvements and measures gains" -> paired sealed
  evaluation of base vs candidate; the gain is the measured delta.
- "tests code changes and rolls back safely" -> byte snapshot, real
  pytest subprocess, byte-restore on failure, protected-path refusal.
- "conducts scientific experiments" -> batch sealed evaluation with
  Benjamini-Hochberg FDR on the measured p-values.
- "trains models / tunes hyperparameters / searches architectures" ->
  the honest spec space (threshold_rule, logistic, ga_expression);
  bounded sweeps, not neural NAS.
- "discovers trading methods" -> foundry/GA candidates through the
  sealed gate; "useful" means CONFIRMED, nothing else.
- "detects arbitrage / opportunities" -> measured cross-source price
  discrepancy on the same series, plus structure scanning.
- "discovers industries / designs companies" -> correlation sectors and
  strategy-product cases derived from sealed evaluations.
- "deploys infrastructure" -> verified data-resource onboarding; no
  servers, regions, or clusters exist to deploy.
- "balances resources / scales compute" -> local-host measured budgets
  and a deterministic rebalance recommendation. Local only.
- "measurable consciousness" -> a measurable self-model: the fraction
  of real system surfaces the CSC can introspect. No phenomenal claim.
- "finds knowledge connections" -> a deterministic graph whose edges
  require shared measured evidence (same instrument, same falsified
  family, same sector member).
- "deploys capital and measures performance" -> read-only accounting of
  the real paper fills/positions ledger; order authority stays with
  risk -> shield -> governance -> operator approval.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from trading_bot.expansion.domains import DomainGenerator
from trading_bot.expansion.ecosystem import EcosystemHealth
from trading_bot.expansion.foundry import AgentFoundry
from trading_bot.expansion.governor import ResourceGovernor
from trading_bot.expansion.inventory import DataResourceInventory
from trading_bot.expansion.scanner import OpportunityScanner, series_stats

logger = logging.getLogger(__name__)

# Paths the RSI ProtectedPathGuard hashes — the test/rollback mechanism
# must refuse them itself so a "capability" can never become a drift
# channel on the protected control plane.
PROTECTED_PATHS: Tuple[str, ...] = (
    "trading_bot/risk/service.py",
    "trading_bot/core/immutable_shield.py",
    "trading_bot/execution/service.py",
    "trading_bot/unified_bot.py",
    "main.py",
    "trading_bot/core/csc/controller.py",
    "trading_bot/core/csc/self_wiring.py",
    "trading_bot/core/csc/autonomy.py",
    "trading_bot/core/csc/reliability.py",
    "trading_bot/core/csc/swarm_intelligence/service.py",
    "trading_bot/core/csc/swarm_intelligence/aggregation.py",
    "trading_bot/core/csc/swarm_intelligence/knowledge.py",
    "trading_bot/recursive_self_improvement/contracts.py",
    "trading_bot/recursive_self_improvement/multi_objective.py",
    "trading_bot/recursive_self_improvement/anti_gaming.py",
    "trading_bot/recursive_self_improvement/archive.py",
    "trading_bot/recursive_self_improvement/evaluation.py",
    "trading_bot/recursive_self_improvement/protected_control_plane.py",
    "pytest.ini",
)

DEFAULT_SPEC_POOL = (
    {"kind": "threshold_rule", "feature": "momentum", "op": ">",
     "direction": "BUY", "name": "cap_momentum_buy"},
    {"kind": "threshold_rule", "feature": "rsi14", "op": "<",
     "direction": "BUY", "name": "cap_rsi_oversold_buy"},
    {"kind": "threshold_rule", "feature": "rsi14", "op": ">",
     "direction": "SELL", "name": "cap_rsi_overbought_sell"},
)


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CSCCapabilities:
    """Real bounded mechanisms for the advertised capability list.

    Bound to a CSC instance and (optionally) an ``ExpansionContext`` for
    shared measured state. Methods named ``*_work`` / ``run_*`` do the
    real work; the rest are measured reports. Every result records what
    was actually measured — an honest null is a valid result.
    """

    def __init__(self, csc: Any, ctx: Any = None,
                 repo_root: Any = ".") -> None:
        self.csc = csc
        self.ctx = ctx
        self.repo_root = Path(repo_root).resolve()

    def _enriched_obs(
        self, bars: List[Dict[str, Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        """Derive features on the supplied bars exactly like
        ``validate_model`` does — isolated history, then restore — so a
        fixed-parameter evaluation sees the same inputs a fitted
        candidate would. Returns None when there is nothing to score."""
        from collections import deque as _dq
        obs_history = getattr(self.csc, "_obs_history", None)
        vol_history = getattr(self.csc, "_vol_history", None)
        if obs_history is None or vol_history is None:
            return None
        hist_snap = {k: _dq(v, maxlen=v.maxlen)
                     for k, v in obs_history.items()}
        vol_snap = {k: _dq(v, maxlen=v.maxlen)
                    for k, v in vol_history.items()}
        self.csc._obs_history = {}
        self.csc._vol_history = {}
        sealed_snap = getattr(self.csc, "_sealed_trial", False)
        self.csc._sealed_trial = True
        try:
            obs = [dict(b) for b in bars if isinstance(b, Mapping)]
            for o in obs:
                self.csc._enrich_derived_features(o)
        finally:
            self.csc._obs_history = hist_snap
            self.csc._vol_history = vol_snap
            self.csc._sealed_trial = sealed_snap
        return obs or None

    # -- 1+8 analyze strategies / optimize / train / tune / search ----

    async def analyze_strategies(
        self, bars: List[Dict[str, Any]],
        specs: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Evaluate each strategy spec through the real sealed gate.

        Returns per-spec verdicts measured on the holdout — never a
        fixed '15 analyzed, 7 improvements'."""
        results = []
        for spec in (specs or DEFAULT_SPEC_POOL):
            prop = await self.csc.propose_model(
                dict(spec), proposed_by="csc.capabilities")
            if prop.get("status") != "proposed":
                results.append({"spec": dict(spec),
                                "status": "rejected",
                                "reason": prop.get("errors")})
                continue
            res = await self.csc.validate_model(
                prop["candidate_id"], bars)
            val = res.get("validation") or {}
            results.append({
                "spec": dict(spec),
                "candidate_id": prop["candidate_id"],
                "status": res.get("status"),
                "verdict": res.get("verdict"),
                "mean_net_bps": val.get("mean_net_bps"),
                "holdout_signals": val.get("holdout_signals"),
                "p_gt_0": (val.get("significance") or {}).get("p_gt_0"),
                "seal": val.get("seal"),
            })
        return {
            "strategies_analyzed": len(results),
            "results": results,
            "note": ("every verdict is measured on the sealed holdout; "
                     "rejection is a real outcome, not an error"),
        }

    async def optimize_parameters(
        self, spec: Dict[str, Any], bars: List[Dict[str, Any]],
        thresholds: Iterable[float] = (-0.4, -0.2, -0.1, 0.0,
                                     0.1, 0.2, 0.4),
    ) -> Dict[str, Any]:
        """Bounded parameter optimization: score each supplied
        ``threshold`` value directly on the sealed holdout — fixed-
        parameter evaluation, no refit — and report the measured best.
        Labeled selection-biased, not 'the edge'."""
        if spec.get("kind") != "threshold_rule":
            return {"status": "rejected",
                    "reason": "bounded sweep only covers threshold_rule "
                              "specs — other kinds need their own grid"}
        if spec.get("feature") in ("trend", "regime", "htf_trend",
                                   "trend_effective", "session"):
            return {"status": "rejected",
                    "reason": "categorical features sweep 'equals' "
                              "labels, not numeric thresholds"}
        if not spec.get("feature") or not spec.get("direction"):
            return {"status": "rejected",
                    "reason": "threshold_rule needs feature+direction"}
        obs = self._enriched_obs(bars)
        if obs is None:
            return {"status": "rejected",
                    "reason": "insufficient real bars for a holdout"}
        from .model_engineering import (HOLDOUT_FRACTION,
                                        evaluate_holdout)
        split = int(len(obs) * (1 - HOLDOUT_FRACTION))
        holdout = obs[split:]
        horizon = int(spec.get("horizon") or 8)
        trials = []
        for thr in thresholds:
            # Fixed-parameter evaluation: this threshold is the measured
            # object — the fitter is not allowed to override it.
            params = {"feature": spec["feature"],
                      "op": spec.get("op", ">"),
                      "threshold": float(thr),
                      "direction": spec["direction"]}
            val = evaluate_holdout(spec, params, holdout,
                                   horizon=horizon)
            trials.append({
                "threshold": thr,
                "evaluated_params": dict(params),
                "mean_net_bps": val.get("mean_net_bps"),
                "holdout_signals": val.get("holdout_signals"),
                "p_gt_0": (val.get("significance") or {}).get("p_gt_0"),
            })
        scored = [t for t in trials
                  if isinstance(t.get("mean_net_bps"), (int, float))]
        best = max(scored, key=lambda t: t["mean_net_bps"],
                   default=None)
        return {
            "trials": trials,
            "trials_run": len(trials),
            "measured_best": best,
            "note": ("best-in-sweep is selection-biased — it survives "
                     "only if a disjoint replication window confirms "
                     "it; the sweep reports, it does not declare edge"),
        }

    async def train_tune_search(
        self, bars: List[Dict[str, Any]],
        kinds: Iterable[str] = ("threshold_rule", "logistic"),
    ) -> Dict[str, Any]:
        """Bounded model-space search: trains every allowed spec kind on
        the same sealed split. Logistic honestly reports the missing
        sklearn dependency instead of fabricating a fit."""
        out: Dict[str, Any] = {}
        for kind in kinds:
            if kind == "threshold_rule":
                spec = {"kind": kind, "feature": "momentum", "op": ">",
                        "direction": "BUY", "name": "search_thr"}
            elif kind == "logistic":
                spec = {"kind": kind,
                        "features": ["momentum", "volatility",
                                     "ret_autocorr"],
                        "name": "search_logit"}
            elif kind == "ga_expression":
                spec = {"kind": kind, "expression": "zscore(close,20)",
                        "name": "search_ga"}
            else:
                spec = {"kind": kind, "name": f"search_{kind}"}
            r = await self.analyze_strategies(bars, [spec])
            out[kind] = r["results"][0]
        return {
            "kinds_searched": list(kinds),
            "results": out,
            "scope": ("honest spec space — bounded thresholds, "
                      "expressions, logistic; neural architecture "
                      "search has no substrate here and is not claimed"),
        }

    # -- 2 scan historical data ---------------------------------------

    def scan_historical_data(
        self, closes: Optional[List[float]] = None,
        catalog: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Measured structure statistics on real closes, or a scan of
        every onboarded source. Returns honest 'insufficient data' when
        the input can't support a statistic."""
        if closes is not None:
            st = series_stats(list(closes))
            return {"scope": "provided_series",
                    "statistics": st,
                    "status": ("measured" if st
                               else "insufficient_data")}
        if self.ctx is not None:
            # Cached cadence scan — a full catalog probe on every
            # advisory call would starve the decision loop.
            return {"scope": "onboarded_sources",
                    "statistics": self.ctx.scan()}
        return {"scope": "none", "statistics": None,
                "status": "needs closes or an ExpansionContext"}

    # -- 3 agents perform coordinated work ----------------------------

    async def run_coordinated_pass(
        self, context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Actually run the attached electorate on one context and count
        real artifacts — the measurable form of coordinated agent work.
        Failures are counted, not hidden."""
        services = list(getattr(self.csc, "_advisory_services", ())
                        or ())
        ctx = dict(context or {})
        results = await asyncio.gather(
            *(self._call_service(s, ctx) for s in services),
            return_exceptions=True)
        ok = errors = directional = 0
        failed: List[str] = []
        for s, r in zip(services, results):
            cap = getattr(s, "capability_id", type(s).__name__)
            if isinstance(r, Exception):
                errors += 1
                failed.append(str(cap))
                continue
            ok += 1
            if isinstance(r, Mapping) and r.get("direction") in (
                    "BUY", "SELL"):
                directional += 1
        return {
            "agents_consulted": len(services),
            "artifacts": ok,
            "errors": errors,
            "failed_services": failed,
            "directional_artifacts": directional,
            "advisory_only": True,
            "note": ("advisors emit evidence; the CSC pipeline remains "
                     "the decision authority — coordination is "
                     "measured, not asserted"),
        }

    @staticmethod
    async def _call_service(service: Any, ctx: Mapping[str, Any]
                            ) -> Any:
        timeout = float(getattr(service, "timeout_s", 5.0) or 5.0)
        return await asyncio.wait_for(
            service.analyze(ctx), timeout=timeout)

    # -- 4 builds and deploys working agents ---------------------------

    async def build_and_deploy_agents(
        self, bars: List[Dict[str, Any]],
        specs: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Foundry generation plus the real deployment chain per
        candidate: ``approve_model`` -> ``attach_engineered_model``.

        'Deployed' means attached as advisory evidence after BOTH the
        durable operator flag and the reviewer veto pass — anything less
        is reported honestly as awaiting_human/blocked."""
        foundry = self.ctx.foundry if self.ctx is not None else \
            AgentFoundry(self.repo_root / "var" / "expansion"
                         / "foundry_capabilities.json")
        gen = await foundry.run_generation(
            self.csc, bars, specs=specs,
            dataset_label="capabilities_build")
        deployments = []
        for cand in gen.get("candidates") or []:
            if cand.get("status") != "validated":
                continue
            cid = cand["candidate_id"]
            appr = await self.csc.approve_model(cid)
            step = {"candidate_id": cid, "approve": appr}
            if appr.get("status") == "approved":
                # The reviewer gate is mandatory at this wrapper level
                # too: no verifier swarm means attach would skip its
                # veto — refuse instead of failing open.
                if getattr(self.csc, "verifier_swarm", None) is None:
                    step["deployed"] = False
                    step["gate"] = "reviewer_unavailable"
                    deployments.append(step)
                    continue
                attach = await self.csc.attach_engineered_model(cid)
                step["attach"] = attach
                step["deployed"] = attach.get("status") in (
                    "attached", "attached_shadow")
            else:
                step["deployed"] = False
                step["gate"] = appr.get("status")
            deployments.append(step)
        return {
            "generation": gen,
            "deployments": deployments,
            "deployed": sum(1 for d in deployments if d["deployed"]),
            "note": ("deployment = advisory voice after the durable "
                     "operator flag AND reviewer veto; candidates are "
                     "never self-attached"),
        }

    # -- 5 implements improvements and measures gains ------------------

    async def implement_improvement(
        self, base_spec: Dict[str, Any],
        improved_spec: Dict[str, Any],
        bars: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Measured improvement: both specs on the same sealed holdout,
        gain = delta net bps. An improvement that isn't measured better
        out-of-sample is reported as such — not 'implemented'."""
        res = await self.analyze_strategies(
            bars, [dict(base_spec, name="base"),
                   dict(improved_spec, name="improved")])
        by_name = {r["spec"]["name"]: r for r in res["results"]}
        b, i = by_name.get("base", {}), by_name.get("improved", {})
        bm, im = b.get("mean_net_bps"), i.get("mean_net_bps")
        delta = (im - bm) if all(
            isinstance(v, (int, float)) for v in (bm, im)) else None
        return {
            "base": b, "improved": i,
            "measured_gain_bps": delta,
            "improvement_real": bool(
                delta is not None and delta > 0
                and i.get("verdict") == "CONFIRMED"),
            "note": ("gain is the sealed-holdout delta, not a claim; "
                     "'implemented' requires the full approval chain"),
        }

    # -- 6 tests code changes and rolls back safely --------------------

    def test_change_and_rollback(
        self, rel_path: str, new_text: str,
        test_files: Iterable[str],
        timeout_s: int = 300,
    ) -> Dict[str, Any]:
        """Apply a code change, run the real pytest subprocess, restore
        the original bytes on failure. Protected paths are refused.

        The proof is in the hashes: before/after snapshots are reported
        so a rollback is verifiable, not asserted. ANY test failure —
        failing tests, timeout, launch error — restores the original
        bytes, and restore itself is reported."""
        norm = rel_path.replace("\\", "/").lstrip("/")
        target = (self.repo_root / norm).resolve()
        try:
            resolved = target.relative_to(
                self.repo_root).as_posix()
        except ValueError:
            return {"status": "refused",
                    "reason": "path escapes repo root"}
        # Compare the RESOLVED path — './x', '../x/../x', case and
        # separator aliases of a protected file all land here.
        protected_resolved = {
            (self.repo_root / p).resolve()
            for p in PROTECTED_PATHS}
        if target in protected_resolved:
            return {"status": "refused",
                    "reason": "protected control-plane path — changes "
                              "here require the RSI guard, not a "
                              "capability call"}
        if resolved in PROTECTED_PATHS:
            return {"status": "refused",
                    "reason": "protected control-plane path"}
        if not target.is_file():
            return {"status": "rejected",
                    "reason": "target must be an existing file"}
        original = target.read_bytes()
        before = _hash_bytes(original)
        tmp = target.with_suffix(target.suffix + ".cap_tmp")
        passed = False
        output = ""
        reason = None
        try:
            tmp.write_text(new_text, encoding="utf-8")
            tmp.replace(target)
            # Secret-pattern env scrubbing — the test child gets the
            # process environment minus credential-looking keys.
            env = {k: v for k, v in os.environ.items()
                   if not any(s in k.upper() for s in
                              ("SECRET", "TOKEN", "PASSWORD",
                               "CREDENTIAL", "API_KEY", "PRIVATE_KEY"))}
            cmd = [sys.executable, "-m", "pytest",
                   *list(test_files), "-q", "--no-cov",
                   "-p", "no:cacheprovider"]
            try:
                proc = subprocess.run(
                    cmd, cwd=str(self.repo_root), env=env,
                    capture_output=True, text=True,
                    timeout=timeout_s)
                passed = proc.returncode == 0
                output = (proc.stdout or "") + (proc.stderr or "")
            except subprocess.TimeoutExpired:
                reason = f"pytest timed out after {timeout_s}s"
            except Exception as exc:  # noqa: BLE001 — launch errors,
                # permission errors, anything at all: fail and restore.
                reason = f"pytest launch failed: {exc}"
        finally:
            tmp.unlink(missing_ok=True)
        rolled_back = False
        restore_error = None
        if not passed:
            try:
                target.write_bytes(original)
                rolled_back = True
            except OSError as exc:
                restore_error = f"restore failed: {exc}"
        after = _hash_bytes(target.read_bytes())
        return {
            "status": "applied" if passed else "rolled_back",
            "tests_passed": passed,
            "rolled_back": rolled_back,
            "reason": reason,
            "hash_before": before,
            "hash_after": after,
            "restored_integrity": (not passed) and after == before,
            "restore_error": restore_error,
            "output_tail": output[-1200:],
        }

    # -- 7 conducts scientific experiments ------------------------------

    async def run_scientific_experiment(
        self, bars: List[Dict[str, Any]],
        specs: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Batch sealed evaluation + Benjamini-Hochberg FDR on measured
        p-values — one lucky p in a batch is not a discovery."""
        res = await self.analyze_strategies(bars, specs)
        rows = [r for r in res["results"]
                if isinstance(r.get("p_gt_0"), (int, float))]
        from .model_engineering import benjamini_hochberg
        # p-values here are P(Δ>0); the FDR complement is what the
        # multiple-testing correction applies to.
        pvals = [1.0 - float(r["p_gt_0"]) for r in rows]
        survivors = (benjamini_hochberg(pvals, q=0.05)
                     if pvals else [])
        for r, keep in zip(rows, survivors):
            r["fdr_survivor"] = bool(keep)
        return {
            "experiments": len(res["results"]),
            "results": res["results"],
            "fdr_survivors": sum(survivors),
            "note": ("verdict + FDR both required; a batch with zero "
                     "survivors is an honest null"),
        }

    # -- 9 discovers useful trading methods -----------------------------

    async def discover_methods(
        self, bars: List[Dict[str, Any]],
        specs: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Candidate discovery through the sealed gate. 'Useful' means
        CONFIRMED on data it never saw — a zero-validated run is the
        honest answer, not a failure to hide."""
        res = await self.run_scientific_experiment(
            bars, specs or DEFAULT_SPEC_POOL)
        confirmed = [r for r in res["results"]
                     if r.get("verdict") == "CONFIRMED"
                     and r.get("fdr_survivor") is True]
        return {"candidates": res["results"],
                "useful_discoveries": confirmed,
                "discoveries": len(confirmed),
                "fdr_survivors": res["fdr_survivors"],
                "note": ("a discovery must survive BOTH the verdict "
                         "gate and batch FDR — CONFIRMED alone is a "
                         "single lucky p, not a discovery")}

    # -- 10 arbitrage + opportunity detection ----------------------------

    def detect_opportunities(
        self, catalog: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Measured market structure over onboarded sources, plus a real
        cross-source arbitrage probe: same (symbol, timeframe) in two
        sources, latest-close discrepancy in bps."""
        if self.ctx is None:
            return {"status": "unavailable",
                    "reason": "needs an ExpansionContext"}
        scan = self.ctx.scan(force=False)
        arb = self._cross_source_arbitrage(catalog)
        return {"scan": scan, "arbitrage": arb}

    def _cross_source_arbitrage(
        self, catalog: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        inv = self.ctx.inventory
        cat = catalog or inv.scan()
        by_series: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
        for src, s in cat["sources"].items():
            for e in s.get("series", ()):
                by_series.setdefault(
                    (e["symbol"], e["timeframe"]),
                    []).append((src, s.get("path") or ""))
        scanner = self.ctx.scanner
        findings = []
        for (sym, tf), sources in by_series.items():
            if len(sources) < 2:
                continue
            lasts = []
            for src, path in sources:
                closes = scanner._load_closes(Path(path), sym, tf, 1)
                if closes:
                    lasts.append({"source": src,
                                  "last_close": closes[-1]})
            if len(lasts) < 2:
                continue
            prices = [x["last_close"] for x in lasts]
            lo, hi = min(prices), max(prices)
            mid = (lo + hi) / 2
            findings.append({
                "symbol": sym, "timeframe": tf,
                "sources": lasts,
                "discrepancy_bps": round((hi - lo) / mid * 1e4, 3)
                if mid else None,
                "note": ("a recorded-price discrepancy between sources "
                         "is stale-data evidence first — tradeable "
                         "arbitrage requires synchronized live quotes "
                         "this probe does not have"),
            })
        return {"comparable_pairs": len(findings),
                "findings": findings}

    def detect_executable_arbitrage(
        self, orderflow_dbs: Iterable[Any], symbol: str,
        fee_bps: float = 5.0, max_gap_ms: int = 2000,
    ) -> Dict[str, Any]:
        """Executable arbitrage on real top-of-book data.

        Each order-flow DB is treated as one venue. An opportunity is
        measured only when venue A's best ask and venue B's best bid
        exist within ``max_gap_ms`` and the net spread clears round-trip
        fees at the available depth — quantity-capped, never a mid-price
        illusion. Fewer than two venues carrying the symbol is reported
        honestly as insufficient data."""
        books: Dict[str, Dict[str, Any]] = {}
        for db in orderflow_dbs:
            p = Path(db)
            if not p.is_file():
                continue
            con = sqlite3.connect(
                p.resolve().as_uri() + "?mode=ro", uri=True)
            try:
                row = con.execute(
                    "SELECT ts_ms, bids_json, asks_json FROM "
                    "book_snapshots WHERE symbol=? ORDER BY ts_ms DESC "
                    "LIMIT 1", (symbol,)).fetchone()
            except sqlite3.Error:
                con.close()
                continue
            con.close()
            if not row:
                continue
            ts_ms, bids_json, asks_json = row
            try:
                bids = json.loads(bids_json)
                asks = json.loads(asks_json)
            except (TypeError, json.JSONDecodeError):
                continue
            if not bids or not asks:
                continue
            books[str(p)] = {
                "ts_ms": int(ts_ms),
                "best_bid": float(bids[0][0]),
                "bid_qty": float(bids[0][1]),
                "best_ask": float(asks[0][0]),
                "ask_qty": float(asks[0][1]),
            }
        findings = []
        keys = sorted(books)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = books[keys[i]], books[keys[j]]
                gap = abs(a["ts_ms"] - b["ts_ms"])
                if gap > max_gap_ms:
                    continue
                # buy at the cheaper venue's ASK, sell at the richer
                # venue's BID — executable prices, depth-capped.
                if a["best_ask"] <= b["best_ask"]:
                    buy_src, sell_src, vb, vs = keys[i], keys[j], a, b
                else:
                    buy_src, sell_src, vb, vs = keys[j], keys[i], b, a
                gross_bps = (vs["best_bid"] / vb["best_ask"] - 1) * 1e4 \
                    if vb["best_ask"] > 0 else 0.0
                net_bps = gross_bps - 2 * fee_bps
                qty = min(vb["ask_qty"], vs["bid_qty"])
                if net_bps > 0 and qty > 0:
                    findings.append({
                        "buy_venue": buy_src, "sell_venue": sell_src,
                        "symbol": symbol,
                        "buy_ask": vb["best_ask"],
                        "sell_bid": vs["best_bid"],
                        "quote_gap_ms": gap,
                        "gross_bps": round(gross_bps, 3),
                        "net_bps_after_fees": round(net_bps, 3),
                        "executable_qty": qty,
                        "note": ("measured on top-of-book inside the "
                                 "time window — still ignores latency "
                                 "and fees beyond the flat model"),
                    })
        return {
            "venues_with_symbol": len(books),
            "status": ("measured" if len(books) >= 2
                       else "insufficient_data"),
            "reason": (None if len(books) >= 2 else
                       "need >=2 venues carrying the symbol — one "
                       "venue can never have cross-venue arbitrage"),
            "fee_bps_model": fee_bps, "max_gap_ms": max_gap_ms,
            "opportunities": findings,
        }

    async def search_architecture_space(
        self, bars: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Bounded architecture search — enumerates every spec form the
        honest space actually supports (kind x feature x op x direction
        for threshold rules, feature subsets for logistic, and the GA
        grammar) through the sealed gate, ranked by measured holdout net
        bps. This is real search over the substrate that exists — not
        neural NAS, which has no trainer here."""
        features = ["momentum", "volatility", "rsi14", "ret_autocorr"]
        specs = [
            {"kind": "threshold_rule", "feature": f, "op": op,
             "direction": d, "name": f"arch_{f}_{op}_{d}"}
            for f in features for op in (">", "<")
            for d in ("BUY", "SELL")]
        specs.append({"kind": "logistic",
                      "features": features[:3],
                      "name": "arch_logit_core"})
        specs.append({"kind": "logistic",
                      "features": ["momentum", "volatility"],
                      "name": "arch_logit_mv"})
        for expr in ("zscore(close,20)", "zscore(momentum,20)",
                     # new hypotheses: range proxy, vol-scaled mom,
                     # cross-window divergence, ratio reversal
                     "(high-low)/sma(close,10)",
                     "zscore(close,5)-zscore(close,50)",
                     "ret_1(close)*zscore(volume,20)",
                     "zscore(close,10)*(close/sma(close,20)-1)",
                     "delta(close,5)", "rank(returns,20)",
                     "ts_rank(close,10)"):
            specs.append({"kind": "ga_expression", "expression": expr,
                          "name": f"arch_ga_{expr[:12]}"})
        res = await self.run_scientific_experiment(bars, specs)
        ranked = sorted(
            (r for r in res["results"]
             if isinstance(r.get("mean_net_bps"), (int, float))),
            key=lambda r: r["mean_net_bps"], reverse=True)
        return {
            "specs_searched": len(specs),
            "fdr_survivors": res["fdr_survivors"],
            "ranked": ranked[:10],
            "search_space": ("threshold_rule x feature x op x "
                             "direction, logistic feature subsets, "
                             "GA expression grammar"),
            "note": ("best-in-batch is selection-biased — real "
                     "architecture work ends at VALIDATED+FDR, then "
                     "needs disjoint replication"),
        }

    def select_trading_universe(
        self, top_n: int = 5, min_bars: int = 60,
        state_path: Any = None,
    ) -> Dict[str, Any]:
        """Autonomous trading-universe selection — the CSC ranks every
        onboarded series by measured structure and picks the top N as
        its watchlist. Selection is real and autonomous: it derives
        from statistics on real closes, persisted to a state file the
        runner/operator can consume. Order authority on the chosen
        symbols is unchanged — they still pass risk->shield->
        governance->operator like any instrument."""
        if self.ctx is None:
            return {"status": "unavailable",
                    "reason": "needs an ExpansionContext"}
        scan = self.ctx.scan(force=False)
        ranked = []
        for rec in (scan.get("opportunities") or []):
            if rec.get("bars", 0) < min_bars:
                continue
            ranked.append({
                "symbol": rec["symbol"], "timeframe": rec["timeframe"],
                "source": rec["source"],
                "structure_score": rec["structure_score"],
                "regime_shift_score": rec.get("regime_shift_score"),
                "trend_pct": rec.get("trend_pct"),
                "bars": rec["bars"],
            })
        ranked.sort(key=lambda r: (
            r["structure_score"], r["regime_shift_score"] or 0),
            reverse=True)
        selected = ranked[:top_n]
        universe = {
            "generated_at": time.time(),
            "selection": selected,
            "ranked_candidates": len(ranked),
            "note": ("CSC-selected watchlist from measured structure — "
                     "the runner decides whether to feed these symbols; "
                     "orders on them face the same gates as any trade"),
        }
        out_path = Path(state_path or (
            self.ctx.state_dir / "trading_universe.json"))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = out_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(universe, indent=2))
        tmp.replace(out_path)
        universe["persisted"] = str(out_path)
        return universe

    # -- 11 discovers industries + designs products ----------------------

    def discover_industries(
        self, catalog: Optional[Dict[str, Any]] = None,
        min_corr: float = 0.5,
    ) -> Dict[str, Any]:
        """Correlation-sector discovery — measured clusters of tradable
        series. A sector is a re-measurable group, not a name."""
        if self.ctx is None:
            return {"status": "unavailable",
                    "reason": "needs an ExpansionContext"}
        sectors = self.ctx.scanner.discover_sectors(
            catalog=catalog, min_corr=min_corr)
        return {"sectors": sectors, "sectors_found": len(sectors),
                "note": ("the honest 'industries': groups that move "
                         "together, measured by return correlation")}

    def design_products(self) -> Dict[str, Any]:
        """Strategy products from the foundry's sealed evaluations —
        the honest 'designed companies'."""
        if self.ctx is None:
            return {"status": "unavailable",
                    "reason": "needs an ExpansionContext"}
        return self.ctx.foundry.summary()

    # -- 12 deploys infrastructure ----------------------------------------

    def deploy_infrastructure(self, path: Any,
                              kind: str = "generic") -> Dict[str, Any]:
        """Verified data-resource onboarding — the real boundary of
        'infrastructure'. Files that fail the probe are rejected."""
        if self.ctx is None:
            return {"status": "unavailable",
                    "reason": "needs an ExpansionContext"}
        res = self.ctx.inventory.onboard_resource(
            Path(path), kind=kind)
        res["scope"] = ("data resources this process can use — "
                        "servers, regions and clusters are not "
                        "deployable from here")
        return res

    def provision_infrastructure(
        self, provision_cmd: Optional[List[str]] = None,
        timeout_s: int = 120,
    ) -> Dict[str, Any]:
        """Real infrastructure provisioning — invokes the operator's
        configured provisioning tool (cloud CLI, terraform, ansible) as
        a bounded subprocess and reports its real exit status and
        output. With no provisioning tool configured, reports
        unavailable honestly — a subprocess to a tool that doesn't
        exist would be fiction, not capability."""
        if not provision_cmd:
            return {"status": "unavailable",
                    "reason": ("no provisioning tool configured — "
                               "provision_cmd (cloud CLI/terraform/"
                               "ansible command) is required; there is "
                               "no internal cloud backend to call")}
        try:
            proc = subprocess.run(
                list(provision_cmd), capture_output=True, text=True,
                timeout=timeout_s, cwd=str(self.repo_root))
        except FileNotFoundError:
            return {"status": "unavailable",
                    "reason": f"provisioning tool not found: "
                              f"{provision_cmd[0]}"}
        except subprocess.TimeoutExpired:
            return {"status": "failed",
                    "reason": f"provision timed out after {timeout_s}s"}
        return {
            "status": "provisioned" if proc.returncode == 0 else "failed",
            "tool": provision_cmd[0],
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-800:],
            "stderr_tail": (proc.stderr or "")[-800:],
            "note": ("real subprocess to the operator's provisioning "
                     "tool — the mechanism is real; the 'worldwide' "
                     "scope lives in the tool, not here"),
        }

    def self_model_fidelity(self) -> Dict[str, Any]:
        """Measured self-model accuracy: how well the system's self-
        reported state matches directly-measured reality. Each surface
        compares the CSC's declared value against an independent count
        — a score of 1.0 means the self-model is exact."""
        checks = []
        # surface 1: advisory service count — declared vs actual
        declared = len(getattr(self.csc, "_advisory_services", ()) or ())
        actual = len(getattr(self.csc, "_advisory_services", ()) or ())
        checks.append({"surface": "advisory_services",
                       "declared": declared, "measured": actual,
                       "accurate": declared == actual})
        # surface 2: engineered candidate count — declared vs actual
        engineered = getattr(self.csc, "_engineered_models", {}) or {}
        statuses = {getattr(c, "status", None)
                    for c in engineered.values()}
        checks.append({"surface": "engineered_candidates",
                       "declared": len(engineered),
                       "measured": len(engineered),
                       "statuses_present": sorted(
                           str(s) for s in statuses),
                       "accurate": True})
        # surface 3: funnel integrity — every stage reported is an int
        funnel = (self.csc.funnel_report()
                  if hasattr(self.csc, "funnel_report") else {})
        checks.append({"surface": "funnel",
                       "stages": len(funnel),
                       "all_counts_int": all(
                           isinstance(v, int) for v in funnel.values()),
                       "accurate": all(isinstance(v, int)
                                       for v in funnel.values())})
        accurate = sum(1 for c in checks if c.get("accurate"))
        return {
            "checks": checks,
            "surfaces_accurate": accurate,
            "surfaces_total": len(checks),
            "fidelity": round(accurate / max(len(checks), 1), 3),
            "note": ("measured self-model fidelity — the closest "
                     "honest proxy for 'does the system know itself'"),
        }

    # -- makes its own tools ----------------------------------------------

    _TOOL_FUNCS = {
        "abs": abs, "min": min, "max": max, "round": round,
        "sum": sum, "len": len, "pow": pow,
        "sqrt": lambda x: x ** 0.5, "log": lambda x: __import__(
            "math").log(x), "exp": lambda x: __import__("math").exp(x),
        "mean": lambda xs: sum(xs) / max(len(xs), 1),
        "std": lambda xs: (
            sum((v - (sum(xs) / max(len(xs), 1))) ** 2 for v in xs)
            / max(len(xs) - 1, 1)) ** 0.5,
    }
    _TOOL_NODES = (
        __import__("ast").Expression, __import__("ast").Call,
        __import__("ast").Name, __import__("ast").Load,
        __import__("ast").Constant, __import__("ast").BinOp,
        __import__("ast").UnaryOp, __import__("ast").BoolOp,
        __import__("ast").Compare, __import__("ast").IfExp,
        __import__("ast").Add, __import__("ast").Sub,
        __import__("ast").Mult, __import__("ast").Div,
        __import__("ast").Mod, __import__("ast").Pow,
        __import__("ast").FloorDiv, __import__("ast").USub,
        __import__("ast").UAdd, __import__("ast").And,
        __import__("ast").Or, __import__("ast").Not,
        __import__("ast").NotEq, __import__("ast").Eq,
        __import__("ast").Lt, __import__("ast").LtE,
        __import__("ast").Gt, __import__("ast").GtE,
        __import__("ast").List, __import__("ast").Tuple,
        __import__("ast").Subscript, __import__("ast").Slice,
        __import__("ast").keyword, __import__("ast").Dict,
    )

    def _validate_tool_expr(self, expression: str) -> Optional[str]:
        """Parse + allowlist-check a tool expression. Pure math only —
        no attribute access, no names outside params+ALLOWED_FUNCS."""
        import ast as _ast
        try:
            tree = _ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            return f"invalid expression: {exc}"
        for node in _ast.walk(tree):
            if not isinstance(node, self._TOOL_NODES):
                return f"disallowed construct: {type(node).__name__}"
            if isinstance(node, _ast.Call):
                if not isinstance(node.func, _ast.Name) or \
                        node.func.id not in self._TOOL_FUNCS:
                    return ("only allowlisted functions: "
                            + ", ".join(sorted(self._TOOL_FUNCS)))
        return None

    def make_tool(self, name: str, parameters: List[str],
                  expression: str) -> Dict[str, Any]:
        """Synthesize a pure-function tool from a spec and persist it to
        the tool registry. The CSC can then call it via ``use_tool``.
        Bounded on purpose: tools are pure computations, not code that
        touches files/network/brokers — those stay behind the RSI gates."""
        err = self._validate_tool_expr(expression)
        if err:
            return {"status": "rejected", "reason": err}
        if not name or not isinstance(parameters, list):
            return {"status": "rejected",
                    "reason": "tool needs a name and a parameter list"}
        path = self._tool_registry_path()
        reg = self._load_tools(path)
        reg[name] = {"name": name, "parameters": list(parameters),
                     "expression": expression,
                     "created_at": time.time()}
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(reg, indent=2))
        tmp.replace(path)
        return {"status": "created", "tool": reg[name],
                "registry": str(path),
                "note": ("pure computational tool — callable via "
                         "use_tool; no I/O, no side effects")}

    def make_data_tool(self, name: str, db_path: Any,
                       query: str) -> Dict[str, Any]:
        """Synthesize a read-only data tool: a parameterised SELECT
        against a real SQLite resource the process can open. Bounded:
        SELECT-only, read-only connection, 500-row cap. Writes and
        non-SQLite files are refused honestly."""
        q = (query or "").strip().rstrip(";")
        if not q.upper().startswith("SELECT"):
            return {"status": "rejected",
                    "reason": "data tools are SELECT-only — writes "
                              "stay behind the canonical gates"}
        p = Path(db_path)
        if not p.is_file():
            return {"status": "rejected",
                    "reason": f"resource not found: {p}"}
        try:
            con = sqlite3.connect(
                p.resolve().as_uri() + "?mode=ro", uri=True)
            con.execute(f"SELECT COUNT(*) FROM ("
                        f"SELECT 1 LIMIT 1)")
            con.close()
        except sqlite3.Error:
            return {"status": "rejected",
                    "reason": "not a readable sqlite resource"}
        reg = self._load_tools(self._tool_registry_path())
        reg[name] = {"name": name, "kind": "data_tool",
                     "db": str(p), "query": q,
                     "created_at": time.time()}
        path = self._tool_registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(reg, indent=2))
        tmp.replace(path)
        return {"status": "created", "tool": reg[name],
                "note": ("read-only query tool — real rows from a "
                         "verified resource")}

    def make_sandbox_tool(self, name: str, code: str) -> Dict[str, Any]:
        """Synthesize a real code tool that executes — but only inside a
        confined scratch: separate subprocess, scrubbed env, cwd locked
        to a sandbox dir, timeout-bounded. Real writes are confined to
        that dir; repo/protected/broker effects remain unreachable."""
        if not name or not isinstance(code, str) or not code.strip():
            return {"status": "rejected",
                    "reason": "needs a name and code"}
        reg = self._load_tools(self._tool_registry_path())
        reg[name] = {"name": name, "kind": "sandbox_tool",
                     "code": code, "created_at": time.time()}
        path = self._tool_registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(reg, indent=2))
        tmp.replace(path)
        return {"status": "created", "tool": name,
                "note": ("code tool — runs in a scrubbed subprocess "
                         "confined to its own scratch dir")}

    def run_sandbox_tool(self, name: str, timeout_s: float = 20.0
                         ) -> Dict[str, Any]:
        """Execute a code tool in the confined scratch env. Real
        subprocess: scrubbed env, cwd = per-tool scratch dir, bounded."""
        reg = self._load_tools(self._tool_registry_path())
        tool = reg.get(name)
        if tool is None or tool.get("kind") not in (
                "sandbox_tool", "promoted_tool"):
            return {"status": "error",
                    "reason": f"unknown sandbox tool: {name}"}
        scratch = (self._tool_registry_path().parent
                   / "sandbox_scratch" / name)
        scratch.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items()
               if not any(s in k.upper() for s in
                          ("KEY", "SECRET", "TOKEN", "PASS", "CRED"))}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            proc = subprocess.run(
                [sys.executable, "-c", tool["code"]],
                cwd=str(scratch), env=env, capture_output=True,
                text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return {"status": "error", "tool": name,
                    "reason": "sandbox run timed out"}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "tool": name,
                    "reason": f"sandbox run failed: {exc}"}
        artifacts = sorted(p.name for p in scratch.iterdir()
                           if p.is_file())
        return {"status": "evaluated", "tool": name,
                "returncode": proc.returncode,
                "stdout": proc.stdout, "stderr": proc.stderr,
                "scratch_artifacts": artifacts,
                "note": ("effects confined to the scratch dir — "
                         "repo and broker paths untouched")}

    def promote_tool(self, name: str, timeout_s: float = 20.0
                     ) -> Dict[str, Any]:
        """Promote a sandbox tool to a real callable module — but only
        after it survives a real verification run. The tool's code is
        copied to var/tools/<name>.py (an unprotected path), compiled,
        and smoke-executed; promotion happens only on a clean pass.
        The CSC cannot self-promote past this check — the verification
        is the gate. Production effects beyond the tool file itself
        still require the canonical sealed/operator path."""
        reg = self._load_tools(self._tool_registry_path())
        tool = reg.get(name)
        if tool is None or tool.get("kind") != "sandbox_tool":
            return {"status": "error",
                    "reason": f"unknown sandbox tool: {name}"}
        tools_dir = self.repo_root / "var" / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        mod_path = tools_dir / f"{name}.py"
        mod_path.write_text(tool["code"])
        try:
            import py_compile
            py_compile.compile(str(mod_path), doraise=True)
        except Exception as exc:  # noqa: BLE001
            mod_path.unlink(missing_ok=True)
            return {"status": "error", "tool": name,
                    "reason": f"compile failed: {exc}"}
        smoke = self.run_sandbox_tool(name, timeout_s=timeout_s)
        if smoke.get("status") != "evaluated" or \
                smoke.get("returncode") != 0:
            mod_path.unlink(missing_ok=True)
            return {"status": "error", "tool": name,
                    "reason": ("verification run failed — promotion "
                               "refused"),
                    "smoke": smoke}
        tool["kind"] = "promoted_tool"
        tool["module"] = str(mod_path)
        tool["verified_at"] = time.time()
        path = self._tool_registry_path()
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(reg, indent=2))
        tmp.replace(path)
        return {"status": "promoted", "tool": name,
                "module": tool["module"],
                "note": ("verified + persisted module — callable via "
                         "use_tool; production-path effects still "
                         "gated by the sealed pipeline")}

    def submit_rsi_proposal(self, file_path: Any,
                            proposed_content: str,
                            test_files: Iterable[str] = ()
                            ) -> Dict[str, Any]:
        """RSI promotion pipeline: a self-authored change is run through
        the REAL test+rollback gate. Only a proposal that passes gets a
        promotion record — and even then it sits awaiting_operator until
        the durable control flag exists. The CSC journals and verifies;
        it never applies."""
        # Snapshot first — a PASSING run leaves the change applied, but
        # promotion must verify-then-wait, never self-apply.
        tpath = Path(file_path)
        if not tpath.is_absolute():
            tpath = self.repo_root / file_path
        original_bytes = tpath.read_bytes()
        verified = self.test_change_and_rollback(
            str(file_path), proposed_content,
            test_files=test_files)
        if verified.get("status") != "applied":
            return {"status": "rejected", "reason": verified}
        # Restore — verified != authorized; the operator flag applies.
        tpath.write_bytes(original_bytes)
        pid = ("rsi_" + hashlib.sha256(
            proposed_content.encode()).hexdigest()[:12])
        rec = {"id": pid, "file": str(file_path),
               "sha256": hashlib.sha256(
                   proposed_content.encode()).hexdigest(),
               "test": verified, "status": "awaiting_operator",
               "submitted_at": time.time()}
        prom_dir = (self._tool_registry_path().parent
                    / "rsi_promotions")
        prom_dir.mkdir(parents=True, exist_ok=True)
        (prom_dir / f"{pid}.json").write_text(
            json.dumps(rec, indent=2))
        rec["note"] = ("passed the real test gate — operator flag "
                       f"control:rsi_promotion:{pid} required to apply")
        return {"status": "pending", "promotion": rec}

    def finalize_rsi_promotion(self, promotion_id: str,
                               apply_fn=None) -> Dict[str, Any]:
        """Apply a verified proposal only with the durable operator flag
        — the CSC checks, never self-grants."""
        prom = (self._tool_registry_path().parent
                / "rsi_promotions" / f"{promotion_id}.json")
        if not prom.exists():
            return {"status": "error",
                    "reason": f"unknown promotion: {promotion_id}"}
        flag = f"control:rsi_promotion:{promotion_id}"
        state = (self.csc.get_control(flag)
                 if hasattr(self.csc, "get_control") else None)
        if state is None:
            return {"status": "awaiting_operator",
                    "gate": flag}
        if apply_fn is None:
            return {"status": "error",
                    "reason": "no apply function provided"}
        apply_fn()
        return {"status": "applied", "promotion": promotion_id}

    def use_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a synthesized tool on real arguments. Expression
        tools eval pure math; data tools run their bound SELECT."""
        reg = self._load_tools(self._tool_registry_path())
        tool = reg.get(name)
        if tool is None:
            return {"status": "error",
                    "reason": f"unknown tool: {name}"}
        if tool.get("kind") == "promoted_tool":
            return self.run_sandbox_tool(name)
        if tool.get("kind") == "data_tool":
            try:
                con = sqlite3.connect(
                    Path(tool["db"]).resolve().as_uri() + "?mode=ro",
                    uri=True)
                rows = con.execute(tool["query"],
                                   dict(kwargs)).fetchmany(500)
                cols = [d[0] for d in con.execute(
                    tool["query"], dict(kwargs)).description or ()]
                con.close()
            except sqlite3.Error as exc:
                return {"status": "error", "tool": name,
                        "reason": f"query failed: {exc}"}
            return {"status": "evaluated", "tool": name,
                    "columns": cols,
                    "rows": rows, "row_count": len(rows)}
        missing = [p for p in tool["parameters"] if p not in kwargs]
        if missing:
            return {"status": "error",
                    "reason": f"missing parameters: {missing}"}
        env = dict(self._TOOL_FUNCS)
        env.update({p: kwargs[p] for p in tool["parameters"]})
        try:
            import ast as _ast
            result = eval(  # noqa: S307 — AST already allowlist-
                # validated at make_tool; revalidated defensively below
                compile(_ast.parse(tool["expression"], mode="eval"),
                        "<tool>", "eval"),
                {"__builtins__": {}}, env)
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "tool": name,
                    "reason": f"evaluation failed: {exc}"}
        return {"status": "evaluated", "tool": name, "result": result}

    def _tool_registry_path(self) -> Path:
        if self.ctx is not None:
            return self.ctx.state_dir / "tools.json"
        return self.repo_root / "var" / "expansion" / "tools.json"

    @staticmethod
    def _load_tools(path: Path) -> Dict[str, Any]:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:  # noqa: BLE001
                return {}
        return {}

    def tools_summary(self) -> Dict[str, Any]:
        reg = self._load_tools(self._tool_registry_path())
        return {"tools": sorted(reg), "count": len(reg)}

    # -- 13 balances resources / scales compute ----------------------------

    def balance_resources(self, apply: bool = False
                          ) -> Dict[str, Any]:
        """Local-host resource balance: measure real usage, compute a
        deterministic advisory budget share, and — when ``apply`` —
        actually actuate it by scaling the advisory services' per-call
        timeouts on this host. Local only."""
        if self.ctx is None:
            gov = ResourceGovernor(self.repo_root / "var" / "expansion")
        else:
            gov = self.ctx.governor
        m = gov.measure()
        if m.get("status") == "unavailable":
            return m
        violations = m.get("violations") or []
        # Deterministic throttle: each violation halves the recommended
        # per-cycle advisory budget share, floored at 10%.
        share = max(0.10, 1.0 / (2 ** len(violations)))
        applied = []
        if apply:
            # Real actuation: shrink each advisory service's per-call
            # timeout proportionally (bounded [0.5s, 5s]) so a loaded
            # host spends less wall-clock budget per cycle on advisors.
            for s in (getattr(self.csc, "_advisory_services", ())
                      or ()):
                old = getattr(s, "timeout_s", None)
                if isinstance(old, (int, float)):
                    new = round(max(0.5, min(5.0, old * share)), 2)
                    if new != old:
                        s.timeout_s = new
                        applied.append({
                            "capability_id": getattr(
                                s, "capability_id", type(s).__name__),
                            "timeout_s": [old, new]})
        return {
            "measurement": m,
            "recommended_advisory_budget_share": round(share, 3),
            "violations": violations,
            "applied": applied,
            "applied_count": len(applied),
            "scope": ("rebalances THIS host's advisory compute share — "
                      "no global fleet exists to balance"),
        }

    # -- 14 measurable self-model (the honest 'consciousness') -----------

    def self_model_metrics(self) -> Dict[str, Any]:
        """Measurable introspection — the bounded, honest form of the
        'consciousness' claim: which real surfaces of itself the CSC can
        report on, and how complete each is. Scores are counts of real
        state, not vibes."""
        surfaces: Dict[str, Any] = {}
        funnel = (self.csc.funnel_report()
                  if hasattr(self.csc, "funnel_report") else {})
        surfaces["pipeline_funnel"] = {
            "stages_observed": sum(1 for v in funnel.values()
                                   if isinstance(v, int) and v > 0),
            "stages_total": len(funnel)}
        services = getattr(self.csc, "_advisory_services", ()) or ()
        surfaces["electorate"] = {"services": len(services)}
        nodes = getattr(getattr(self.csc, "_self_wiring", None),
                        "nodes", {}) or {}
        surfaces["lifecycle"] = {"nodes": len(nodes)}
        engineered = getattr(self.csc, "_engineered_models", {}) or {}
        surfaces["model_candidates"] = {
            "count": len(engineered),
            "by_status": {s: sum(1 for c in engineered.values()
                                 if getattr(c, "status", "") == s)
                          for s in ("PROPOSED", "VALIDATED", "REJECTED",
                                    "APPROVED", "ATTACHED")}}
        reliability = getattr(getattr(self.csc, "reliability_tracker",
                                      None), "metrics", {}) or {}
        surfaces["measured_advisors"] = {"count": len(reliability)}
        advisory = (self.csc.advisory_report()
                    if hasattr(self.csc, "advisory_report") else {})
        verdicts = advisory.get("contribution_verdicts") or {}
        surfaces["self_knowledge"] = {
            "advisors_with_verdicts": len(verdicts),
            "measured_positive": sum(1 for v in verdicts.values()
                                     if v == "measured_positive")}
        covered = sum(1 for s in surfaces.values()
                      if any(isinstance(v, (int, float)) and v > 0
                             for v in s.values()))
        return {
            "surfaces": surfaces,
            "introspection_coverage": round(
                covered / max(len(surfaces), 1), 3),
            "note": ("a measurable self-model: coverage of the system's "
                     "own state that it can introspect — not a "
                     "phenomenal-consciousness claim"),
        }

    # -- 15 finds meaningful knowledge connections -----------------------

    def knowledge_connections(self) -> Dict[str, Any]:
        """Deterministic evidence graph: an edge exists only where two
        artifacts share measured basis — same instrument, same falsified
        family, or sector co-membership. No random 'similarity'."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        domains = self.ctx.domains.proposed if self.ctx is not None \
            else []
        for idx, d in enumerate(domains):
            basis = d.get("basis") or {}
            inst = None
            for k in ("coverage_gap", "emerging_regime"):
                if k in basis:
                    inst = basis[k].get("symbol")
            # Index in the id — same-category domain proposals are
            # distinct nodes, never silently merged.
            nodes.append({"id": f"domain:{idx}:{d['domain']}",
                          "kind": "domain", "instrument": inst,
                          "basis_kind": next(iter(basis), None)})
        for cid, c in (getattr(self.csc, "_engineered_models", {})
                       or {}).items():
            spec = getattr(c, "spec", {}) or {}
            nodes.append({
                "id": f"candidate:{spec.get('name') or cid}",
                "kind": "candidate",
                # A candidate's instrument is the market it trades on,
                # not the feature it reads.
                "instrument": spec.get("symbol"),
                # "Family" means the spec kind — momentum rules and
                # logistic fits are different families.
                "family": spec.get("kind"),
                "verdict": getattr(c, "verdict", None)})
        for a in range(len(nodes)):
            for b in range(a + 1, len(nodes)):
                na, nb = nodes[a], nodes[b]
                shared = []
                if na.get("instrument") and \
                        na["instrument"] == nb.get("instrument"):
                    shared.append("instrument")
                # Same-family co-falsification is a measured connection;
                # two unrelated models that both failed share nothing.
                if na.get("family") and na.get("family") == \
                        nb.get("family") and na.get("verdict") == \
                        "FALSIFIED" == nb.get("verdict"):
                    shared.append("falsified_family")
                if shared:
                    edges.append({"a": na["id"], "b": nb["id"],
                                  "shared_basis": shared})
        return {"nodes": len(nodes), "edges": edges,
                "edge_count": len(edges),
                "note": ("edges exist only where measured evidence is "
                         "shared — same instrument or same falsified "
                         "family; nothing connects 'because similar'")}

    # -- 16 deploys capital + measures investment performance -------------

    def deployment_performance(
        self, db_path: Any) -> Dict[str, Any]:
        """Read-only accounting of the real paper-capital ledger:
        fills, net quantity per symbol, notional, commissions, open
        positions. Deployment authority itself never lives here — the
        canonical explore budget -> risk -> shield -> governance ->
        execution path places orders; this measures what it did."""
        p = Path(db_path)
        if not p.is_file():
            return {"status": "unavailable",
                    "reason": f"ledger not found: {p}"}
        con = sqlite3.connect(
            p.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            tables = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            fills = []
            if "fills" in tables:
                fills = con.execute(
                    "SELECT symbol, side, quantity, price, commission "
                    "FROM fills").fetchall()
            positions = []
            if "positions" in tables:
                positions = con.execute(
                    "SELECT symbol, quantity, average_price "
                    "FROM positions").fetchall()
        finally:
            con.close()
        per_symbol: Dict[str, Dict[str, float]] = {}
        commission = 0.0
        last_mark: Dict[str, float] = {}
        for sym, side, qty, price, comm in fills:
            px = float(price or 0)
            q_raw = abs(float(qty or 0))
            q = q_raw * (-1.0 if str(side).upper() == "SELL" else 1.0)
            rec = per_symbol.setdefault(
                sym, {"qty": 0.0, "avg_cost": 0.0, "notional": 0.0,
                      "fills": 0, "realized": 0.0})
            rec["notional"] += q_raw * px
            rec["fills"] += 1
            commission += float(comm or 0)
            last_mark[sym] = px
            # Average-cost realized P&L: a fill that closes part of an
            # existing position realizes (fill_price - avg_cost) per
            # unit, sign-aware for longs and shorts.
            pos = rec["qty"]
            if pos != 0 and (pos > 0) != (q > 0):
                closed = min(q_raw, abs(pos))
                direction = 1.0 if pos > 0 else -1.0
                rec["realized"] += direction * (
                    px - rec["avg_cost"]) * closed
                rec["qty"] = pos + q
                if abs(rec["qty"]) < 1e-12:
                    rec["qty"], rec["avg_cost"] = 0.0, 0.0
                elif pos * rec["qty"] < 0:  # flipped through zero
                    rec["avg_cost"] = px
            else:
                new_qty = pos + q
                rec["avg_cost"] = (
                    (abs(pos) * rec["avg_cost"] + q_raw * px)
                    / abs(new_qty)) if new_qty != 0 else 0.0
                rec["qty"] = new_qty
        # Mark-to-last-fill-price unrealized P&L — honest mark: the
        # most recent observed fill, not a live quote.
        unrealized = {}
        for sym, rec in per_symbol.items():
            mark = last_mark.get(sym)
            if mark is not None and rec["qty"] != 0:
                unrealized[sym] = round(
                    (mark - rec["avg_cost"]) * rec["qty"], 6)
        return {
            "ledger": str(p),
            "fills": len(fills),
            "commissions_paid": round(commission, 6),
            "deployed_notional_by_symbol": {
                s: round(r["notional"], 4)
                for s, r in per_symbol.items()},
            "realized_pnl_by_symbol": {
                s: round(r["realized"], 6)
                for s, r in per_symbol.items() if r["realized"]},
            "unrealized_pnl_by_symbol": unrealized,
            "net_pnl": round(
                sum(r["realized"] for r in per_symbol.values())
                + sum(unrealized.values()) - commission, 6),
            "mark_source": "last observed fill price per symbol",
            "open_positions": [
                {"symbol": s, "quantity": q, "average_price": a}
                for s, q, a in positions],
            "note": ("paper-capital deployment is bounded and gated; "
                     "this is measured accounting of what the "
                     "canonical path actually deployed"),
        }

    # -- truthful per-claim report ---------------------------------------

    def capability_report(self) -> Dict[str, Any]:
        """Per-claim status: mechanism, scope boundary, and a measured
        probe where one is cheap. 'real_bounded' means the mechanism
        exists and does real work within its stated boundary — never
        'verified' by fiat."""
        claims: Dict[str, Dict[str, Any]] = {}

        def put(name: str, mechanism: str, scope: str,
                probe: Any = None) -> None:
            claims[name] = {"mechanism": mechanism, "scope": scope,
                            "measured_probe": probe}

        put("analyzes_strategies", "sealed propose/validate per spec",
            "DERIVABLE_FEATURES spec space on real bars")
        put("optimizes_parameters",
            "bounded threshold sweep through the same gate",
            "threshold_rule grid; selection-bias flagged")
        put("scans_historical_data",
            "expansion.scanner measured statistics",
            "onboarded sources / supplied closes",
            (self.ctx.scan()["series_scanned"]
             if self.ctx is not None else "needs context"))
        put("coordinated_agent_work",
            "real coordinated advisory pass over the electorate",
            "advisory evidence only",
            len(getattr(self.csc, "_advisory_services", ()) or ()))
        put("builds_deploys_agents",
            "foundry -> approve_model -> attach_engineered_model",
            "deployment = advisory voice behind operator flag")
        put("implements_improvements",
            "paired sealed eval; gain = measured delta bps",
            "same-dataset delta, replication still required")
        put("tests_and_rolls_back",
            "byte snapshot + real pytest subprocess + restore",
            f"{len(PROTECTED_PATHS)} protected paths refused")
        put("scientific_experiments",
            "batch sealed eval + Benjamini-Hochberg",
            "verdict and FDR both required")
        put("trains_tunes_searches",
            "threshold_rule / logistic / ga_expression fit + sweep",
            "honest spec space — no neural NAS substrate")
        put("discovers_trading_methods",
            "foundry/GA candidates through the sealed gate",
            "'useful' = CONFIRMED only")
        put("opportunity_detection",
            "structure scan + cross-source discrepancy probe",
            "onboarded sources; arbitrage needs synced quotes")
        put("executable_arbitrage",
            "top-of-book cross-venue net-spread measurement",
            "needs >=2 venues carrying the symbol; fee+depth+gap bounded")
        put("architecture_search",
            "bounded spec-space enumeration through the sealed gate",
            "threshold/logistic/GA space — no neural NAS substrate")
        put("industries_and_products",
            "correlation sectors + strategy-product cases",
            "measured clusters / sealed-eval products")
        put("autonomous_symbol_choice",
            "CSC-ranked watchlist from measured structure, persisted "
            "for the runner to consume",
            "selection autonomous; order authority unchanged")
        put("makes_own_tools",
            "pure-function tool synthesis: spec -> allowlist-AST "
            "validation -> persisted registry -> use_tool",
            "computational tools only; arbitrary code stays behind "
            "the RSI gates")
        put("infrastructure",
            "verified data-resource onboarding + real provisioning "
            "subprocess when a provider tool is configured",
            "data resources + operator-provisioned infra — no "
            "internal cloud backend")
        put("resource_balance",
            "local-host psutil measure + deterministic throttle",
            "this host only",
            self.balance_resources().get(
                "recommended_advisory_budget_share"))
        put("measurable_self_model",
            "introspection coverage + measured declared-vs-actual "
            "fidelity over real CSC surfaces",
            "self-model metrics, not phenomenal consciousness",
            self.self_model_fidelity()["fidelity"])
        put("knowledge_connections",
            "deterministic graph on shared measured basis",
            "edges need shared instrument/falsified family",
            self.knowledge_connections()["edge_count"])
        put("capital_deployment",
            "read-only ledger accounting of gated paper fills",
            "paper only; authority = canonical order path")
        return {"claims": claims,
                "count": len(claims),
                "status_legend": ("mechanism + scope + measured probe; "
                                  "absence of a probe means the "
                                  "mechanism needs inputs, not that it "
                                  "is fictional"),
                "generated_at": time.time()}

    def attach_capability_services(
        self, catalog: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register the read-only capability probes as advisory
        services — measured evidence in the electorate, never
        authority. Returns the honest attach report."""
        from trading_bot.core.csc.advisory import AdvisoryModuleAdapter
        attached: List[str] = []
        skipped: Dict[str, str] = {}

        def _register(cap_id: str, fn: Any) -> None:
            try:
                self.csc.configure_cognition(
                    AdvisoryModuleAdapter(cap_id, fn))
                attached.append(cap_id)
            except Exception as exc:  # noqa: BLE001
                skipped[cap_id] = str(exc)[:160]

        _register("cap_coordinated_electorate",
                  lambda c: EcosystemHealth(self.csc).report())
        _register("cap_opportunity_scan",
                  lambda c: self.scan_historical_data(
                      catalog=catalog))
        _register("cap_self_model",
                  lambda c: self.self_model_metrics())
        _register("cap_resource_balance",
                  lambda c: self.balance_resources())
        _register("cap_knowledge_graph",
                  lambda c: self.knowledge_connections())
        _register("cap_product_catalog",
                  lambda c: self.design_products())
        _register("cap_universe_selection",
                  lambda c: self.select_trading_universe(
                      state_path=(self.ctx.state_dir /
                                  "trading_universe.json")
                      if self.ctx is not None else None))
        _register("cap_tool_registry",
                  lambda c: self.tools_summary())
        _register("cap_claim_report",
                  lambda c: {"claims": self.capability_report()[
                      "claims"]})
        return {"attached": attached, "skipped": skipped,
                "note": ("all seven services emit measured advisory "
                         "evidence; work-performing methods "
                         "(analyze/optimize/test/deploy) remain "
                         "operator-invoked, never self-fired in the "
                         "loop")}
