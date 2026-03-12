"""
Self-Diagnostic Manager (Self-Managing Orchestrator)
=====================================================
Coordinates diagnostic scans and auto-repairs on a schedule.
Persists history to SQLite, tracks health trends, auto-escalates
critical issues, and runs as a background asyncio task.

This is the single entry point for the entire self-diagnostic system.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .diagnostic_engine import (
    DiagnosticCategory,
    DiagnosticEngine,
    DiagnosticReport,
    DiagnosticResult,
    DiagnosticSeverity,
)
from .auto_repair import AutoRepairEngine, RepairReport, RepairStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Health Trend Tracker
# ---------------------------------------------------------------------------

@dataclass
class HealthSnapshot:
    """Point-in-time health measurement."""
    timestamp: datetime
    health_score: float
    total_issues: int
    critical_count: int
    repaired_count: int
    failed_repairs: int


class HealthTrend:
    """Tracks health over time and detects degradation."""

    def __init__(self, max_history: int = 500):
        self._history: List[HealthSnapshot] = []
        self._max_history = max_history

    def record(self, snapshot: HealthSnapshot) -> None:
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    @property
    def latest(self) -> Optional[HealthSnapshot]:
        return self._history[-1] if self._history else None

    @property
    def is_degrading(self) -> bool:
        """True if health has been declining over the last 3 snapshots."""
        if len(self._history) < 3:
            return False
        recent = self._history[-3:]
        return all(recent[i].health_score < recent[i - 1].health_score for i in range(1, len(recent)))

    @property
    def average_score(self) -> float:
        if not self._history:
            return 100.0
        return sum(s.health_score for s in self._history) / len(self._history)

    def scores_last_n(self, n: int = 10) -> List[float]:
        return [s.health_score for s in self._history[-n:]]


# ---------------------------------------------------------------------------
# Persistence Layer
# ---------------------------------------------------------------------------

class DiagnosticStore:
    """SQLite-backed persistence for diagnostic and repair history."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""CREATE TABLE IF NOT EXISTS diagnostic_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time TEXT NOT NULL,
                health_score REAL,
                total_issues INTEGER,
                critical_count INTEGER,
                repairable_count INTEGER,
                is_runnable INTEGER,
                duration_ms REAL,
                report_json TEXT
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS repair_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time TEXT NOT NULL,
                success_count INTEGER,
                failed_count INTEGER,
                human_count INTEGER,
                duration_ms REAL,
                report_json TEXT
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS health_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                health_score REAL,
                total_issues INTEGER,
                critical_count INTEGER,
                repaired_count INTEGER,
                failed_repairs INTEGER
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                severity TEXT,
                message TEXT,
                acknowledged INTEGER DEFAULT 0
            )""")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not initialize diagnostic store: {e}")

    def save_diagnostic_run(self, report: DiagnosticReport, duration_ms: float) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                """INSERT INTO diagnostic_runs 
                   (run_time, health_score, total_issues, critical_count, repairable_count, is_runnable, duration_ms, report_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    report.health_score,
                    report.total_issues,
                    report.critical_count,
                    report.repairable_count,
                    1 if report.is_runnable else 0,
                    duration_ms,
                    json.dumps(report.to_dict(), default=str),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to save diagnostic run: {e}")

    def save_repair_run(self, report: RepairReport, duration_ms: float) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                """INSERT INTO repair_runs 
                   (run_time, success_count, failed_count, human_count, duration_ms, report_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    report.success_count,
                    report.failed_count,
                    report.human_count,
                    duration_ms,
                    json.dumps(report.to_dict(), default=str),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to save repair run: {e}")

    def save_health_snapshot(self, snapshot: HealthSnapshot) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                """INSERT INTO health_snapshots 
                   (timestamp, health_score, total_issues, critical_count, repaired_count, failed_repairs)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    snapshot.timestamp.isoformat(),
                    snapshot.health_score,
                    snapshot.total_issues,
                    snapshot.critical_count,
                    snapshot.repaired_count,
                    snapshot.failed_repairs,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to save health snapshot: {e}")

    def save_escalation(self, severity: str, message: str) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "INSERT INTO escalations (timestamp, severity, message) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), severity, message),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to save escalation: {e}")

    def get_recent_scores(self, limit: int = 20) -> List[float]:
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute(
                "SELECT health_score FROM health_snapshots ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            scores = [row[0] for row in cursor.fetchall()]
            conn.close()
            return list(reversed(scores))
        except Exception:
            return []

    def get_unacknowledged_escalations(self) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute(
                "SELECT id, timestamp, severity, message FROM escalations WHERE acknowledged = 0 ORDER BY id DESC LIMIT 50"
            )
            rows = [{"id": r[0], "timestamp": r[1], "severity": r[2], "message": r[3]} for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Self-Diagnostic Manager
# ---------------------------------------------------------------------------

class SelfDiagnosticManager:
    """
    Self-managing orchestrator that:
    1. Runs diagnostic scans on a schedule
    2. Auto-repairs repairable issues
    3. Tracks health trends over time
    4. Escalates persistent/critical issues
    5. Persists all history to SQLite
    6. Provides a simple API for on-demand scans
    7. Runs as a background asyncio task

    Usage:
        manager = SelfDiagnosticManager()

        # One-shot scan + repair
        report = await manager.run_full_diagnostic()
        repair = await manager.auto_repair(report)

        # Start background self-management
        await manager.start()

        # Stop
        await manager.stop()
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        scan_interval_seconds: int = 300,
        auto_repair_enabled: bool = True,
        max_repair_attempts: int = 3,
        escalation_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self.engine = DiagnosticEngine(project_root)
        self.repairer = AutoRepairEngine(project_root)
        self.project_root = self.engine.project_root

        self._scan_interval = scan_interval_seconds
        self._auto_repair_enabled = auto_repair_enabled
        self._max_repair_attempts = max_repair_attempts
        self._escalation_callback = escalation_callback

        # State
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_diagnostic: Optional[DiagnosticReport] = None
        self._last_repair: Optional[RepairReport] = None
        self._repair_attempt_counts: Dict[str, int] = {}
        self._health_trend = HealthTrend()

        # Persistence
        db_path = str(self.project_root / "data" / "self_diagnostic.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._store = DiagnosticStore(db_path)

        # Load historical scores
        for score in self._store.get_recent_scores(50):
            self._health_trend.record(HealthSnapshot(
                timestamp=datetime.now(),
                health_score=score,
                total_issues=0, critical_count=0,
                repaired_count=0, failed_repairs=0,
            ))

    # ------------------------------------------------------------------
    # Public API: One-shot operations
    # ------------------------------------------------------------------

    async def run_full_diagnostic(self) -> DiagnosticReport:
        """Run a complete diagnostic scan across all categories."""
        start = time.monotonic()
        logger.info("[SELF-DIAG] Running full diagnostic scan...")

        report = await self.engine.run_all()
        duration_ms = (time.monotonic() - start) * 1000

        self._last_diagnostic = report
        self._store.save_diagnostic_run(report, duration_ms)

        logger.info(
            f"[SELF-DIAG] Scan complete: score={report.health_score:.0f}/100, "
            f"issues={report.total_issues}, critical={report.critical_count}, "
            f"repairable={report.repairable_count} ({duration_ms:.0f}ms)"
        )
        return report

    async def run_category(self, category: DiagnosticCategory) -> List[DiagnosticResult]:
        """Run diagnostics for a single category."""
        return await self.engine.run_category(category)

    async def auto_repair(self, report: Optional[DiagnosticReport] = None) -> RepairReport:
        """Auto-repair all repairable issues from a diagnostic report."""
        if report is None:
            report = self._last_diagnostic
        if report is None:
            report = await self.run_full_diagnostic()

        start = time.monotonic()
        logger.info(f"[SELF-DIAG] Starting auto-repair for {report.repairable_count} issues...")

        # Filter out issues that have exceeded max repair attempts
        filtered_results = []
        for r in report.results:
            if r.repairable and not r.passed:
                attempts = self._repair_attempt_counts.get(r.check_id, 0)
                if attempts < self._max_repair_attempts:
                    filtered_results.append(r)
                    self._repair_attempt_counts[r.check_id] = attempts + 1
                else:
                    logger.warning(
                        f"[SELF-DIAG] Skipping {r.check_id}: exceeded {self._max_repair_attempts} repair attempts"
                    )

        # Create a filtered report for the repairer
        filtered_report = DiagnosticReport(results=filtered_results)
        repair_report = await self.repairer.repair_all(filtered_report)
        duration_ms = (time.monotonic() - start) * 1000

        self._last_repair = repair_report
        self._store.save_repair_run(repair_report, duration_ms)

        # Reset attempt counter for successful repairs
        for result in repair_report.results:
            if result.status == RepairStatus.SUCCESS:
                self._repair_attempt_counts.pop(result.action.action_id, None)

        logger.info(
            f"[SELF-DIAG] Repair complete: {repair_report.success_count} fixed, "
            f"{repair_report.failed_count} failed, {repair_report.human_count} need human ({duration_ms:.0f}ms)"
        )
        return repair_report

    # ------------------------------------------------------------------
    # Public API: Background self-management
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background self-management loop."""
        if self._running:
            logger.warning("[SELF-DIAG] Already running.")
            return
        self._running = True
        self._task = asyncio.create_task(self._management_loop())
        logger.info(f"[SELF-DIAG] Self-management started (interval={self._scan_interval}s)")

    async def stop(self) -> None:
        """Stop the background self-management loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[SELF-DIAG] Self-management stopped.")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def health_score(self) -> float:
        if self._last_diagnostic:
            return self._last_diagnostic.health_score
        return self._health_trend.average_score

    @property
    def is_healthy(self) -> bool:
        return self.health_score >= 70.0

    @property
    def is_degrading(self) -> bool:
        return self._health_trend.is_degrading

    @property
    def last_diagnostic(self) -> Optional[DiagnosticReport]:
        return self._last_diagnostic

    @property
    def last_repair(self) -> Optional[RepairReport]:
        return self._last_repair

    # ------------------------------------------------------------------
    # Status & Reporting
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """Get current system status as a dict."""
        return {
            "running": self._running,
            "health_score": self.health_score,
            "is_healthy": self.is_healthy,
            "is_degrading": self.is_degrading,
            "scan_interval_seconds": self._scan_interval,
            "auto_repair_enabled": self._auto_repair_enabled,
            "last_scan": self._last_diagnostic.started_at.isoformat() if self._last_diagnostic else None,
            "last_issues": self._last_diagnostic.total_issues if self._last_diagnostic else None,
            "last_repair_success": self._last_repair.success_count if self._last_repair else None,
            "health_trend": self._health_trend.scores_last_n(10),
            "pending_escalations": len(self._store.get_unacknowledged_escalations()),
        }

    def print_status(self) -> str:
        """Get a formatted status string."""
        s = self.status()
        lines = [
            f"{'='*60}",
            f"  SELF-DIAGNOSTIC SYSTEM STATUS",
            f"{'='*60}",
            f"  Running        : {'YES' if s['running'] else 'NO'}",
            f"  Health Score   : {s['health_score']:.0f}/100",
            f"  Healthy        : {'YES' if s['is_healthy'] else 'NO'}",
            f"  Degrading      : {'YES' if s['is_degrading'] else 'NO'}",
            f"  Scan Interval  : {s['scan_interval_seconds']}s",
            f"  Auto-Repair    : {'ON' if s['auto_repair_enabled'] else 'OFF'}",
            f"  Last Scan      : {s['last_scan'] or 'Never'}",
            f"  Last Issues    : {s['last_issues'] if s['last_issues'] is not None else 'N/A'}",
            f"  Trend (last 10): {s['health_trend']}",
            f"  Escalations    : {s['pending_escalations']} pending",
            f"{'='*60}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Background Loop
    # ------------------------------------------------------------------

    async def _management_loop(self) -> None:
        """Main self-management loop: scan → repair → record → sleep → repeat."""
        # Run initial scan immediately
        await self._run_cycle()

        while self._running:
            try:
                await asyncio.sleep(self._scan_interval)
                if not self._running:
                    break
                await self._run_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SELF-DIAG] Management loop error: {e}")
                await asyncio.sleep(30)

    async def _run_cycle(self) -> None:
        """Single diagnostic + repair + record cycle."""
        try:
            # 1. Diagnostic scan
            report = await self.run_full_diagnostic()

            # 2. Auto-repair if enabled and there are repairable issues
            repair_report = None
            if self._auto_repair_enabled and report.repairable_count > 0:
                repair_report = await self.auto_repair(report)

                # 3. Re-scan after repairs to verify
                if repair_report.success_count > 0:
                    report = await self.run_full_diagnostic()

            # 4. Record health snapshot
            snapshot = HealthSnapshot(
                timestamp=datetime.now(),
                health_score=report.health_score,
                total_issues=report.total_issues,
                critical_count=report.critical_count,
                repaired_count=repair_report.success_count if repair_report else 0,
                failed_repairs=repair_report.failed_count if repair_report else 0,
            )
            self._health_trend.record(snapshot)
            self._store.save_health_snapshot(snapshot)

            # 5. Escalation checks
            await self._check_escalations(report, repair_report)

            # 6. Adaptive interval: scan more frequently when unhealthy
            if report.critical_count > 0:
                self._scan_interval = max(60, self._scan_interval // 2)
            elif report.health_score >= 90:
                self._scan_interval = min(600, self._scan_interval + 30)

        except Exception as e:
            logger.error(f"[SELF-DIAG] Cycle error: {e}")

    async def _check_escalations(
        self, report: DiagnosticReport, repair_report: Optional[RepairReport]
    ) -> None:
        """Escalate persistent or critical issues."""
        # Critical issues that couldn't be repaired
        if report.critical_count > 0:
            msg = f"CRITICAL: {report.critical_count} critical issues detected. Health={report.health_score:.0f}/100"
            self._store.save_escalation("critical", msg)
            self._notify(msg)

        # Health degradation trend
        if self._health_trend.is_degrading:
            scores = self._health_trend.scores_last_n(3)
            msg = f"DEGRADATION: Health declining over last 3 scans: {scores}"
            self._store.save_escalation("high", msg)
            self._notify(msg)

        # Repeated repair failures
        if repair_report:
            for result in repair_report.results:
                if result.status == RepairStatus.FAILED:
                    attempts = self._repair_attempt_counts.get(result.action.action_id, 0)
                    if attempts >= self._max_repair_attempts:
                        msg = f"REPAIR FAILED: {result.action.description} after {attempts} attempts"
                        self._store.save_escalation("high", msg)
                        self._notify(msg)

    def _notify(self, message: str) -> None:
        """Send notification via callback or just log."""
        logger.warning(f"[SELF-DIAG ESCALATION] {message}")
        if self._escalation_callback:
            try:
                self._escalation_callback("self_diagnostic", message)
            except Exception as e:
                logger.error(f"Escalation callback failed: {e}")

    # ------------------------------------------------------------------
    # Convenience: Startup Pre-flight Check
    # ------------------------------------------------------------------

    async def preflight_check(self, auto_fix: bool = True) -> bool:
        """
        Run a pre-flight diagnostic before bot startup.
        Returns True if the system is safe to run.
        
        This is the recommended entry point for main.py integration:
            manager = SelfDiagnosticManager()
            if not await manager.preflight_check():
                sys.exit(1)
        """
        logger.info("[SELF-DIAG] ========== PRE-FLIGHT CHECK ==========")
        report = await self.run_full_diagnostic()

        if auto_fix and report.repairable_count > 0:
            logger.info(f"[SELF-DIAG] Attempting to fix {report.repairable_count} issues...")
            repair_report = await self.auto_repair(report)
            logger.info(repair_report.summary())

            # Re-scan after repairs
            if repair_report.success_count > 0:
                report = await self.run_full_diagnostic()

        logger.info(report.summary())

        if not report.is_runnable:
            logger.error("[SELF-DIAG] ❌ PRE-FLIGHT FAILED: Critical issues prevent startup.")
            return False

        if report.health_score < 50:
            logger.warning("[SELF-DIAG] ⚠️ PRE-FLIGHT WARNING: Low health score, proceeding with caution.")

        logger.info(f"[SELF-DIAG] ✅ PRE-FLIGHT PASSED (score={report.health_score:.0f}/100)")
        return True
