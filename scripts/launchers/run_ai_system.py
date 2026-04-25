#!/usr/bin/env python3
"""Unified startup orchestrator for the trading AI system.

Goals:
- one command for environment checks + startup
- detect likely broken imports/dependencies/config before launch
- provide safe defaults (paper/smoke mode)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]

ENTRYPOINTS = {
    "main": [sys.executable, "main.py", "--mode", "smoke", "--symbol", "EURUSD", "--timeframe", "M15", "--bars", "50"],
    "integrated": [sys.executable, "scripts/launchers/run_integrated_system.py", "--orchestrator", "--mode", "paper", "--symbol", "EURUSD", "--timeframe", "M15"],
    "production": [sys.executable, "scripts/launchers/run_production_system.py", "--mode", "paper", "--symbols", "EURUSD"],
}

REQUIRED_DIRS = ["logs", "data", "models", "cache", "reports"]
REQUIRED_CONFIGS = [
    "config/alphaalgo_config.yaml",
    "config/survival_config.yaml",
    "elite_config.yaml",
]

CRITICAL_IMPORTS = [
    "numpy",
    "pandas",
    "trading_bot",
]

OPTIONAL_IMPORTS = [
    "yaml",
    "MetaTrader5",
    "torch",
    "transformers",
    "prometheus_client",
    "dash",
]


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _find_missing(modules: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for mod in modules:
        if importlib.util.find_spec(mod) is None:
            missing.append(mod)
    return missing


def ensure_dirs() -> list[CheckResult]:
    results: list[CheckResult] = []
    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        path.mkdir(parents=True, exist_ok=True)
        results.append(CheckResult(f"dir:{rel}", True, str(path)))
    return results


def check_configs() -> list[CheckResult]:
    results: list[CheckResult] = []
    for rel in REQUIRED_CONFIGS:
        path = ROOT / rel
        if path.exists():
            results.append(CheckResult(f"config:{rel}", True, "present"))
        else:
            results.append(CheckResult(f"config:{rel}", False, "missing"))
    return results


def check_imports() -> list[CheckResult]:
    results: list[CheckResult] = []
    missing_critical = _find_missing(CRITICAL_IMPORTS)
    missing_optional = _find_missing(OPTIONAL_IMPORTS)

    if missing_critical:
        results.append(CheckResult("imports:critical", False, f"missing: {', '.join(missing_critical)}"))
    else:
        results.append(CheckResult("imports:critical", True, "all installed"))

    if missing_optional:
        results.append(CheckResult("imports:optional", True, f"missing optional: {', '.join(missing_optional)}"))
    else:
        results.append(CheckResult("imports:optional", True, "all installed"))
    return results


def smoke_entrypoint(entrypoint: str, timeout_s: int) -> CheckResult:
    cmd = ENTRYPOINTS[entrypoint] + ["--help"]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    ok = proc.returncode == 0
    detail = f"rc={proc.returncode}"
    if not ok:
        tail = (proc.stderr or proc.stdout)[-500:]
        detail = f"rc={proc.returncode}; tail={tail}"
    return CheckResult(f"entrypoint:{entrypoint}:help", ok, detail)


def launch(entrypoint: str, passthrough: list[str], timeout_s: int) -> int:
    cmd = ENTRYPOINTS[entrypoint] + passthrough
    print(f"[RUN] {' '.join(shlex.quote(c) for c in cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        timeout=timeout_s,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    return proc.returncode


def write_report(results: list[CheckResult], path: Path) -> None:
    payload = {
        "project_root": str(ROOT),
        "results": [r.__dict__ for r in results],
        "all_critical_ok": all(r.ok for r in results if not r.name.startswith("imports:optional")),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified AI system startup orchestrator")
    parser.add_argument("--entrypoint", choices=sorted(ENTRYPOINTS.keys()), default="main")
    parser.add_argument("--mode", choices=["check", "run"], default="check")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--report",
        default="diagnostics/startup_orchestrator_report.json",
        help="Where to write JSON status report",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Extra args passed to selected entrypoint when --mode run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = ROOT / args.report

    checks: list[CheckResult] = []
    checks.extend(ensure_dirs())
    checks.extend(check_configs())
    checks.extend(check_imports())
    checks.append(smoke_entrypoint(args.entrypoint, timeout_s=max(30, args.timeout)))

    for item in checks:
        marker = "OK" if item.ok else "FAIL"
        print(f"[{marker}] {item.name}: {item.detail}")

    write_report(checks, report_path)
    print(f"[INFO] Report written to {report_path}")

    critical_ok = all(c.ok for c in checks if not c.name.startswith("imports:optional"))
    if args.mode == "check":
        return 0 if critical_ok else 2

    if not critical_ok:
        print("[ERROR] Startup checks failed. Fix critical issues before run mode.")
        return 2

    passthrough = args.args
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    return launch(args.entrypoint, passthrough=passthrough, timeout_s=args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
