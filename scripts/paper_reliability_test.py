#!/usr/bin/env python
"""Isolated paper reliability test — exercises the operational surfaces
that must never silently fail:

  1. PAUSE     — cycles stop advancing, state persists.
  2. RESUME    — cycles advance again.
  3. ESTOP     — emergency flag, processing halts.
  4. RESTART   — kill the process mid-run; on relaunch the persisted
                 emergency flag must still block cycles (fail-closed).
  5. RECOVERY  — pending orders reconciled on start; no fills orphaned.
  6. LEDGER    — fills/orders/positions internally consistent.

Everything runs against --source synthetic in an isolated state-dir;
no real broker, no capital, no shared state with a live run.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

HERMES = os.environ.get(
    "HERMES_PY",
    str(Path.home() / "AppData/Local/hermes/hermes-agent/venv/Scripts/"
        "python.exe"))


def _cli(state_dir: Path, *cmd) -> str:
    r = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts/operator_cli.py"),
         "--state-dir", str(state_dir), *cmd],
        capture_output=True, text=True, cwd=PROJECT_ROOT)
    return r.stdout + r.stderr


def _snapshot(state_dir: Path) -> dict:
    p = state_dir / "snapshot.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _cycles(state_dir: Path) -> int:
    return int(_snapshot(state_dir).get("cycles", -1))


def _control(state_dir: Path) -> dict:
    return _snapshot(state_dir).get("control") or {}


def _wait_cycles(state_dir: Path, want: int, timeout: float) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        if _cycles(state_dir) >= want:
            return True
        time.sleep(0.5)
    return False


def _start_runner(state_dir: Path, cycles: int, seed: int = 11,
                  measured_only: bool = True) -> subprocess.Popen:
    env = dict(os.environ)
    if measured_only:
        env["TB_MEASURED_ADVISORS"] = "1"
    log = open(state_dir / "runner.log", "ab")
    return subprocess.Popen(
        [HERMES, str(PROJECT_ROOT / "scripts/paper_runner.py"),
         "--source", "synthetic", "--cycles", str(cycles),
         "--state-dir", str(state_dir), "--interval", "0",
         "--seed", str(seed)],
        cwd=PROJECT_ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)


def _kill(proc: subprocess.Popen) -> None:
    try:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=15)
    except Exception:
        proc.kill()
        try:
            proc.wait(timeout=10)
        except Exception:
            pass


def _ledger_check(state_dir: Path) -> dict:
    db = state_dir / "trading_state.db"
    if not db.exists():
        return {"ok": False, "reason": "no trading_state.db"}
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        fills = con.execute("SELECT count(*) FROM fills").fetchone()[0]
        orders = con.execute("SELECT count(*) FROM orders").fetchone()[0]
        recon = con.execute(
            "SELECT count(*) FROM reconciliation_runs").fetchone()[0]
        # every fill must reference an order that exists
        orphans = con.execute(
            "SELECT count(*) FROM fills f WHERE NOT EXISTS ("
            "SELECT 1 FROM orders o WHERE o.client_order_id = "
            "f.client_order_id)").fetchone()[0]
        audit = con.execute(
            "SELECT count(*) FROM audit_events").fetchone()[0]
        return {"ok": orphans == 0, "fills": fills, "orders": orders,
                "recon_runs": recon, "orphan_fills": orphans,
                "audit_events": audit}
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default="var/reliability_run")
    ap.add_argument("--timeout-per-step", type=float, default=240.0)
    args = ap.parse_args()

    state_dir = (PROJECT_ROOT / args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    proc = None

    def record(name, ok, detail=""):
        results[name] = {"ok": bool(ok), "detail": detail}
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}",
              flush=True)

    try:
        # -- Phase 1: pause/resume/estop on a live runner -----------------
        proc = _start_runner(state_dir, cycles=10_000)
        ok = _wait_cycles(state_dir, 3, args.timeout_per_step)
        record("boot_cycles", ok, f"cycles={_cycles(state_dir)}")

        _cli(state_dir, "pause")
        time.sleep(3)
        frozen = _cycles(state_dir)
        time.sleep(4)
        still = _cycles(state_dir)
        record("pause_blocks_cycles",
               0 <= still - frozen <= 1 and still >= 0,
               f"cycles {frozen} -> {still}")
        record("pause_flag_persisted",
               _control(state_dir).get("paused") is True,
               f"control={_control(state_dir)}")

        _cli(state_dir, "resume")
        time.sleep(2)
        before = _cycles(state_dir)
        ok = _wait_cycles(state_dir, before + 2, args.timeout_per_step)
        record("resume_advances", ok, f"cycles {before} -> "
               f"{_cycles(state_dir)}")

        _cli(state_dir, "estop")
        time.sleep(3)
        frozen = _cycles(state_dir)
        time.sleep(4)
        record("estop_halts", _cycles(state_dir) - frozen <= 1,
               f"cycles {frozen} -> {_cycles(state_dir)}")
        record("estop_flag_persisted",
               (_control(state_dir).get("emergency") is True
                or _control(state_dir).get("estopped") is True
                or "emerg" in json.dumps(_control(state_dir)).lower()),
               f"control={_control(state_dir)}")

        # -- Phase 2: kill + restart — emergency flag must block ----------
        _kill(proc)
        proc = None
        time.sleep(2)

        proc = _start_runner(state_dir, cycles=10_000, seed=12)
        # Wait for boot: snapshot should appear. Then emergency flag from
        # the previous run must keep cycles at ~0 without reset-emergency.
        t0 = time.time()
        while time.time() - t0 < args.timeout_per_step \
                and not (state_dir / "snapshot.json").exists():
            time.sleep(0.5)
        boot_cycles = _cycles(state_dir)
        time.sleep(6)
        after = _cycles(state_dir)
        record("restart_preserves_emergency",
               after - boot_cycles <= 1,
               f"post-restart cycles {boot_cycles} -> {after} "
               "(no reset-emergency issued)")

        # Reset + resume: cycles must advance again.
        _cli(state_dir, "reset-emergency")
        _cli(state_dir, "resume")
        time.sleep(2)
        before = _cycles(state_dir)
        ok = _wait_cycles(state_dir, before + 2, args.timeout_per_step)
        record("post_reset_advances", ok,
               f"cycles {before} -> {_cycles(state_dir)}")

    finally:
        if proc is not None:
            _kill(proc)

    led = _ledger_check(state_dir)
    record("ledger_consistent", led.get("ok"), str(led))
    record("reconciliation_ran", led.get("recon_runs", 0) > 0,
           f"runs={led.get('recon_runs')}")

    out = state_dir / "reliability_report.json"
    out.write_text(json.dumps(results, indent=2))
    passed = sum(1 for v in results.values() if v["ok"])
    print(f"\n{passed}/{len(results)} checks passed -> {out}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
