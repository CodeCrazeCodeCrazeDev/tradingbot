"""Supervise a bounded single-symbol database replay; never clears an operator stop.

The deadline includes runner startup. A stop request cancels the active
cycle; after 30 seconds of cleanup grace the process tree is terminated.
The supervisor heartbeat is independent of the runner's event loop.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def write_status(path: Path, status: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(status, indent=2), encoding="utf-8")
    for attempt in range(10):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.1)


def publish_status(path: Path, status: dict) -> None:
    """Telemetry contention must not disable deadline enforcement."""
    try:
        write_status(path, status)
    except OSError as exc:
        status["telemetry_error"] = f"{type(exc).__name__}: {exc}"
        print(f"Status publication failed; supervision continues: {exc}", file=sys.stderr, flush=True)


@contextmanager
def managed_process(command, stdout, stderr):
    """Own the entire child tree, including Windows venv interpreter launchers."""
    if sys.platform != "win32":
        import signal
        process = subprocess.Popen(command, cwd=PROJECT_ROOT, stdout=stdout,
                                   stderr=stderr, start_new_session=True)
        def stop_tree():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            yield process, stop_tree
        finally:
            stop_tree()
            process.wait(timeout=15)
        return

    import ctypes
    from ctypes import wintypes
    from trading_bot.recursive_self_improvement.job_limits import (
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION, LIMIT_KILL_ON_JOB_CLOSE)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                              ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.TerminateJobObject.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    process = None
    try:
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        # Suspend the launcher before it can spawn an unowned interpreter.
        process = subprocess.Popen(command, cwd=PROJECT_ROOT, stdout=stdout,
                                   stderr=stderr, creationflags=0x00000004)
        if not kernel.AssignProcessToJobObject(job, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        native = ctypes.WinDLL("ntdll")
        native.NtResumeProcess.argtypes = [wintypes.HANDLE]
        native.NtResumeProcess.restype = ctypes.c_long
        if native.NtResumeProcess(int(process._handle)) != 0:
            raise OSError("Could not resume the supervised paper process")

        def stop_tree():
            if not kernel.TerminateJobObject(job, 1):
                raise ctypes.WinError(ctypes.get_last_error())
        yield process, stop_tree
    finally:
        # Kernel kills every member even if the supervisor crashes or is killed.
        kernel.CloseHandle(job)
        if process is not None:
            if process.poll() is None:
                process.kill()  # also covers failed assignment while suspended
            process.wait(timeout=15)


def supervise(command, state_dir: Path, stop_file: Path, seconds: float,
              grace_seconds: float = 30) -> dict:
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Duration must be positive and finite.")
    started, start_clock = time.time(), time.monotonic()
    status = {"status": "starting", "started_at": started,
              "deadline": started + seconds, "duration_seconds": seconds,
              "heartbeat": started, "command": command,
              "stop_file": str(stop_file), "forced_stop": False}
    status_path = state_dir / "validation_run.json"
    write_status(status_path, status)
    with (state_dir / "validation.stdout.log").open("ab") as stdout, (
            state_dir / "validation.stderr.log").open("ab") as stderr, (
            managed_process(command, stdout, stderr)) as (process, stop_tree):
        status.update(pid=process.pid, status="running")
        requested_at = None
        try:
            while process.poll() is None:
                now = time.monotonic()
                if requested_at is None and now - start_clock >= seconds:
                    stop_file.write_text("one-hour validation deadline\n", encoding="utf-8")
                    requested_at = now
                    status.update(status="stopping", stop_requested_at=time.time())
                if requested_at is not None and now - requested_at >= grace_seconds:
                    status["forced_stop"] = True
                    stop_tree()
                    process.wait(timeout=15)
                    break
                status["heartbeat"] = time.time()
                publish_status(status_path, status)
                time.sleep(min(1, seconds / 10))
        except BaseException:
            try:
                stop_file.write_text("supervisor interrupted\n", encoding="utf-8")
                process.wait(timeout=grace_seconds)
            except (OSError, subprocess.TimeoutExpired):
                stop_tree()
                process.wait(timeout=15)
            status.update(status="interrupted", heartbeat=time.time(),
                          ended_at=time.time(), exit_code=process.returncode)
            publish_status(status_path, status)
            raise
    status.update(
        status=("forced_stop" if status["forced_stop"] else
                "completed" if requested_at is not None and process.returncode == 0 else
                "exited_early" if process.returncode == 0 else "failed"),
        ended_at=time.time(), heartbeat=time.time(), exit_code=process.returncode,
        elapsed_seconds=round(time.monotonic() - start_clock, 2),
    )
    publish_status(status_path, status)
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", default="var/hl_run")
    parser.add_argument("--db-path", default="hl_data.db")
    parser.add_argument("--duration-seconds", type=float, default=3600)
    parser.add_argument("--symbol", default="BTC")
    parser.add_argument("--timeframe", default="15m")
    args = parser.parse_args(argv)
    state_dir = Path(args.state_dir).resolve()
    if not math.isfinite(args.duration_seconds) or args.duration_seconds <= 0:
        parser.error("--duration-seconds must be positive and finite")
    # Inspect the durable controls, not an old dashboard snapshot.
    with sqlite3.connect((state_dir / "trading_state.db").as_uri() + "?mode=ro", uri=True) as con:
        controls = dict(con.execute(
            "SELECT key,value FROM account_state WHERE key IN ('control:emergency','control:paused')"))
    if controls.get("control:emergency") != "0" or controls.get("control:paused") != "0":
        parser.error("Paper validation blocked: emergency/pause must be explicitly clear.")
    if any((state_dir / "control").glob("cmd-*.json")):
        parser.error("Pending operator commands must be resolved first.")
    with sqlite3.connect(Path(args.db_path).resolve().as_uri() + "?mode=ro", uri=True) as con:
        count = con.execute(
            "SELECT COUNT(*) FROM market_data WHERE symbol=? AND timeframe=?",
            (args.symbol, args.timeframe)).fetchone()[0]
    if count <= 64:
        parser.error(f"At least 65 real {args.symbol} {args.timeframe} candles are required.")
    from trading_bot.interfaces.operator_reset import runner_lock
    # Separate supervisor lock; paper_runner owns the state lock for its lifetime.
    with runner_lock(state_dir / ".validation_supervisor"):
        stop_file = state_dir / ("validation-stop-" + uuid.uuid4().hex)
        command = [
            sys.executable, "-u", str(PROJECT_ROOT / "scripts" / "paper_runner.py"),
            "--source", "db", "--db-path", str(Path(args.db_path).resolve()),
            "--symbol", args.symbol, "--timeframe", args.timeframe,
            "--broker-tz-offset", "utc",
            "--state-dir", str(state_dir), "--cycles", "0", "--interval", "1",
            "--skip", "64", "--seed-bars", "64", "--stop-file", str(stop_file),
        ]
        print(f"Paper replay deadline: {args.duration_seconds}s from launch; "
              "up to 30s shutdown grace. Dashboard: http://localhost:8080", flush=True)
        result = supervise(command, state_dir, stop_file, args.duration_seconds)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
