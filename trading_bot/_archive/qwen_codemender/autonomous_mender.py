"""
Autonomous Mender - Self-directed code maintenance and repair

Runs continuous maintenance cycles: scan → analyze → fix → verify.
Operates within safety guardrails and requires human approval for risky changes.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from .codemender_core import QwenCodeMender, CodeMenderConfig, MendingResult, TaskType
from .code_analyzer import AnalysisReport, SeverityLevel
from .safety_guardrails import SafetyLevel

logger = logging.getLogger(__name__)


class MenderState(Enum):
    """States of the autonomous mender"""
    IDLE = "idle"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    FIXING = "fixing"
    VERIFYING = "verifying"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class MenderCycle:
    """Record of a single maintenance cycle"""
    cycle_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    state: MenderState = MenderState.IDLE
    files_scanned: int = 0
    issues_found: int = 0
    issues_fixed: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class MaintenanceReport:
    """Summary report of maintenance activity"""
    total_cycles: int = 0
    total_issues_found: int = 0
    total_issues_fixed: int = 0
    total_errors: int = 0
    cycles: List[MenderCycle] = field(default_factory=list)
    last_scan: Optional[AnalysisReport] = None
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def fix_rate(self) -> float:
        if self.total_issues_found == 0:
            return 1.0
        return self.total_issues_fixed / self.total_issues_found


class AutonomousMender:
    """
    Autonomous code maintenance engine.

    Continuously scans, analyzes, and fixes code issues within
    the safety guardrails. Requires human approval for risky changes.
    """

    def __init__(
        self,
        config: Optional[CodeMenderConfig] = None,
        scan_interval_minutes: int = 60,
        max_fixes_per_cycle: int = 10,
        auto_fix_safe_issues: bool = True,
    ):
        self.config = config or CodeMenderConfig()
        self.scan_interval = scan_interval_minutes * 60
        self.max_fixes_per_cycle = max_fixes_per_cycle
        self.auto_fix_safe = auto_fix_safe_issues

        self.mender = QwenCodeMender(self.config)
        self.state = MenderState.IDLE
        self._cycles: List[MenderCycle] = []
        self._cycle_counter = 0
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._pending_approvals: List[Dict[str, Any]] = []

    async def run_single_cycle(self) -> MenderCycle:
        """Run a single maintenance cycle: scan → fix → verify"""
        self._cycle_counter += 1
        cycle = MenderCycle(
            cycle_id=self._cycle_counter,
            started_at=datetime.now(),
        )
        start_time = time.monotonic()

        try:
            # Phase 1: Scan
            cycle.state = MenderState.SCANNING
            self.state = MenderState.SCANNING
            logger.info(f"[Cycle {cycle.cycle_id}] Scanning codebase...")

            report = self.mender.scan_codebase()
            cycle.files_scanned = report.files_scanned
            cycle.issues_found = report.total_issues

            if report.is_clean:
                logger.info(f"[Cycle {cycle.cycle_id}] Codebase is clean. No issues found.")
                cycle.state = MenderState.IDLE
                self.state = MenderState.IDLE
                cycle.completed_at = datetime.now()
                cycle.duration_seconds = time.monotonic() - start_time
                self._cycles.append(cycle)
                return cycle

            logger.info(
                f"[Cycle {cycle.cycle_id}] Found {report.total_issues} issues "
                f"across {report.files_scanned} files"
            )

            # Phase 2: Fix issues (prioritize syntax errors first)
            cycle.state = MenderState.FIXING
            self.state = MenderState.FIXING
            fixes_applied = 0

            # Fix syntax errors first
            for error in report.syntax_errors[:self.max_fixes_per_cycle]:
                if fixes_applied >= self.max_fixes_per_cycle:
                    break
                try:
                    result = await self.mender.fix_file(
                        error["file"],
                        f"Syntax error: {error['error']}"
                    )
                    if result.success and result.changes:
                        fixes_applied += 1
                        cycle.issues_fixed += 1
                except Exception as e:
                    cycle.errors.append(f"Fix failed for {error['file']}: {e}")

            # Fix code smells
            for smell in report.code_smells[:self.max_fixes_per_cycle - fixes_applied]:
                if fixes_applied >= self.max_fixes_per_cycle:
                    break
                if smell.severity in (SeverityLevel.ERROR, SeverityLevel.CRITICAL):
                    try:
                        result = await self.mender.fix_file(
                            smell.file_path,
                            smell.message,
                        )
                        if result.success and result.changes:
                            fixes_applied += 1
                            cycle.issues_fixed += 1
                    except Exception as e:
                        cycle.errors.append(f"Fix failed for {smell.file_path}: {e}")

            # Phase 3: Verify
            cycle.state = MenderState.VERIFYING
            self.state = MenderState.VERIFYING
            logger.info(f"[Cycle {cycle.cycle_id}] Verifying fixes...")

            verify_report = self.mender.scan_codebase()
            if verify_report.total_issues < report.total_issues:
                logger.info(
                    f"[Cycle {cycle.cycle_id}] Reduced issues from "
                    f"{report.total_issues} to {verify_report.total_issues}"
                )
            elif verify_report.total_issues > report.total_issues:
                logger.warning(
                    f"[Cycle {cycle.cycle_id}] Issues increased from "
                    f"{report.total_issues} to {verify_report.total_issues}!"
                )

        except Exception as e:
            cycle.state = MenderState.ERROR
            self.state = MenderState.ERROR
            cycle.errors.append(str(e))
            logger.error(f"[Cycle {cycle.cycle_id}] Error: {e}")

        cycle.completed_at = datetime.now()
        cycle.duration_seconds = time.monotonic() - start_time
        cycle.state = MenderState.IDLE
        self.state = MenderState.IDLE
        self._cycles.append(cycle)

        logger.info(
            f"[Cycle {cycle.cycle_id}] Complete: "
            f"{cycle.issues_fixed}/{cycle.issues_found} fixed, "
            f"{len(cycle.errors)} errors, "
            f"{cycle.duration_seconds:.1f}s"
        )
        return cycle

    async def start(self):
        """Start continuous maintenance loop"""
        if self._running:
            logger.warning("Autonomous mender is already running")
            return

        self._running = True
        logger.info(
            f"Starting autonomous mender (interval={self.scan_interval}s, "
            f"max_fixes={self.max_fixes_per_cycle})"
        )

        while self._running:
            try:
                await self.run_single_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")

            if self._running:
                logger.info(f"Next cycle in {self.scan_interval // 60} minutes")
                await asyncio.sleep(self.scan_interval)

    def stop(self):
        """Stop the continuous maintenance loop"""
        self._running = False
        self.state = MenderState.STOPPED
        logger.info("Autonomous mender stopped")

    def get_report(self) -> MaintenanceReport:
        """Get a summary report of all maintenance activity"""
        report = MaintenanceReport(
            total_cycles=len(self._cycles),
            total_issues_found=sum(c.issues_found for c in self._cycles),
            total_issues_fixed=sum(c.issues_fixed for c in self._cycles),
            total_errors=sum(len(c.errors) for c in self._cycles),
            cycles=list(self._cycles),
        )
        return report

    async def close(self):
        """Clean up resources"""
        self.stop()
        await self.mender.close()
