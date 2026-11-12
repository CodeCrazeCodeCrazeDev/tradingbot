#!/usr/bin/env python
"""CSC self-train orchestrator — bounded autonomous improvement.

Two training levels, both fail-closed through their existing gates:

  strategy  RSI improvement cycle (bounded numeric candidates on
            allow-listed families; ProtectedPathGuard + verifier +
            archive enforce the contract). Runs
            rsi_synthetic_benchmark.py --seeds N under hermes.

  model     rv-blend forecaster retrain — the ONLY model family
            whose save-gate has ever passed (AGENTS.md: world-model
            and vol-GRU both REJECTED; retraining proven-dead
            families is wasted compute). Its own gate decides
            checkpoint retention.

Triggers are interval-gated so repeated invocations are cheap:
  strategy: var/self_train/last_run.json age > --strategy-hours
  model:    var/rv_blend_forecaster.train_meta.json missing or
            market_data.db gained > --model-new-bars bars since
            the meta file's recorded max timestamp, AND age >
            --model-hours

Outputs: var/self_train_report.json + append-only
var/self_train_ledger.jsonl (provenance). Advisory-only — this
orchestrates training RUNS; promotion still needs signed
OperatorAuthorization. .venv-safe (subprocesses use hermes).

Usage:
    python scripts/self_train_orchestrator.py --dry-run
    python scripts/self_train_orchestrator.py            # gated run
"""

import argparse
import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAR = ROOT / "var"
ST = VAR / "self_train"
HERMES_PY = (Path.home() / "AppData" / "Local" / "hermes"
             / "hermes-agent" / "venv" / "Scripts" / "python.exe")
PY = str(HERMES_PY) if HERMES_PY.exists() else sys.executable


def _age_hours(path: Path) -> float:
    try:
        return (time.time() - path.stat().st_mtime) / 3600.0
    except OSError:
        return 1e9


def _market_max_ts() -> str:
    """Newest timestamp across market_data.db series — retrain
    trigger compares against the trainer's recorded split."""
    try:
        con = sqlite3.connect(str(ROOT / "market_data.db"))
        ts = con.execute("select max(timestamp) from market_data"
                         ).fetchone()[0]
        con.close()
        return str(ts or "")
    except Exception:
        return ""


def _launch(cmd: list, tag: str) -> dict:
    """Fire-and-forget: training runs detached so the calling cycle
    never blocks. stdout/stderr -> var/self_train/<tag>.log; the
    trainers' own save-gates decide what survives. Interval markers
    prevent relaunch storms (24h >> ~15min train time)."""
    ST.mkdir(parents=True, exist_ok=True)
    log = ST / f"{tag}.log"
    try:
        with open(log, "w", encoding="utf-8") as fh:
            p = subprocess.Popen(cmd, cwd=ROOT, stdout=fh,
                                 stderr=subprocess.STDOUT)
        return {"launched_pid": p.pid, "log": str(log.relative_to(ROOT)),
                "cmd_tail": " ".join(cmd[-3:])}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def strategy_due(args) -> bool:
    marker = ST / "strategy_last.json"
    return _age_hours(marker) > args.strategy_hours or \
        not marker.exists()


def search_due(args) -> bool:
    marker = ST / "search_last.json"
    return _age_hours(marker) > args.search_hours or \
        not marker.exists()


def model_due(args) -> bool:
    meta = VAR / "rv_blend_forecaster.train_meta.json"
    ckpt = VAR / "rv_blend_forecaster.pt"
    if not ckpt.exists():
        return True  # never trained — first run builds it
    if _age_hours(meta if meta.exists() else ckpt) < args.model_hours:
        return False
    # retrain only if market data advanced since last train meta
    try:
        m = json.loads(meta.read_text()) if meta.exists() else {}
        trained_max = str(m.get("max_timestamp") or
                          m.get("data_max_ts") or "")
    except Exception:
        trained_max = ""
    cur_max = _market_max_ts()
    return bool(cur_max and cur_max > trained_max)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy-hours", type=float, default=24.0)
    ap.add_argument("--model-hours", type=float, default=72.0)
    ap.add_argument("--search-hours", type=float, default=168.0,
                    help="model-engineering search interval (weekly)")
    ap.add_argument("--search-variants", type=int, default=4)
    ap.add_argument("--model-new-bars", type=int, default=2000,
                    help="(reserved; timestamp-advance check used)")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ST.mkdir(parents=True, exist_ok=True)
    report = {"ran_at": datetime.now(timezone.utc).isoformat(
        timespec="seconds"), "stages": {}, "dry_run": args.dry_run}

    s_due, m_due = strategy_due(args), model_due(args)
    se_due = search_due(args)
    report["triggers"] = {"strategy": s_due, "model": m_due,
                          "search": se_due}

    if args.dry_run:
        print(json.dumps(report, indent=2))
        return 0

    if s_due:
        res = _launch([PY, str(ROOT / "scripts"
                               / "rsi_synthetic_benchmark.py"),
                       "--seeds", str(args.seeds)], "strategy_rsi")
        report["stages"]["strategy"] = res
        (ST / "strategy_last.json").write_text(json.dumps(
            {"launched_at": report["ran_at"],
             "pid": res.get("launched_pid")}))
        print(f"strategy rsi benchmark launched: {res}")

    if m_due:
        res = _launch([PY, str(ROOT / "scripts"
                               / "train_rv_forecaster.py"),
                       "--ratio", "--blend"], "model_rv_blend")
        report["stages"]["model_rv_blend"] = res
        print(f"model rv-blend retrain launched: {res}")

    if se_due:
        res = _launch([PY, str(ROOT / "scripts"
                               / "model_engineering_search.py"),
                       "--max-variants",
                       str(args.search_variants)],
                      "model_engineering")
        report["stages"]["model_engineering"] = res
        (ST / "search_last.json").write_text(json.dumps(
            {"launched_at": report["ran_at"],
             "pid": res.get("launched_pid")}))
        print(f"model-engineering search launched: {res}")

    (VAR / "self_train_report.json").write_text(
        json.dumps(report, indent=2))
    with open(VAR / "self_train_ledger.jsonl", "a",
              encoding="utf-8") as f:
        f.write(json.dumps({"ts": report["ran_at"],
                            "stages": {k: {"pid": v.get("launched_pid"),
                                           "error": v.get("error")}
                                       for k, v in
                                       report["stages"].items()},
                            "triggers": report["triggers"]}) + "\n")
    print(f"report -> var/self_train_report.json "
          f"(strategy_due={s_due} model_due={m_due})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
