"""
Institutional Research Lab.

Canonical facade that organizes the SovereignResearchOrchestrator as an
institution-grade research lab: a fixed org chart of divisions, an auditable
minutes ledger for every stage of every program, and a structured LabReport
per research program — without duplicating the kernel's orchestration.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from trading_bot.research.orchestration.kernel import SovereignResearchOrchestrator
from trading_bot.research.lab.divisions import (
    ResearchDivision,
    build_org_chart,
    division_for_stage,
)
from trading_bot.research.lab.minutes import LabMinute, LabMinutesLedger

logger = logging.getLogger(__name__)


@dataclass
class DivisionReport:
    """Summary of one division's activity during a research program."""
    division_key: str
    division_name: str
    stages_run: int = 0
    failed_stages: int = 0
    verdict: str = "not_reached"  # completed | failed | not_reached
    objections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "division_key": self.division_key,
            "division_name": self.division_name,
            "stages_run": self.stages_run,
            "failed_stages": self.failed_stages,
            "verdict": self.verdict,
            "objections": self.objections,
        }


@dataclass
class LabReport:
    """Institutional report for one research program execution."""
    program_id: str
    task_id: str
    symbol: str
    query: str
    status: str
    promoted: bool
    strategy_id: Optional[str]
    decision: str
    debate_consensus: float
    decision_record_id: Optional[str]
    divisions_engaged: List[str]
    division_reports: List[DivisionReport]
    minutes: List[LabMinute]
    started_at: str
    finished_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_id": self.program_id,
            "task_id": self.task_id,
            "symbol": self.symbol,
            "query": self.query,
            "status": self.status,
            "promoted": self.promoted,
            "strategy_id": self.strategy_id,
            "decision": self.decision,
            "debate_consensus": self.debate_consensus,
            "decision_record_id": self.decision_record_id,
            "divisions_engaged": self.divisions_engaged,
            "division_reports": [d.to_dict() for d in self.division_reports],
            "minutes": [m.to_dict() for m in self.minutes],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class InstitutionalResearchLab:
    """
    The AlphaAlgo research engine organized as an institutional research lab.

    Wraps a SovereignResearchOrchestrator kernel: all promotion authority stays
    in the kernel's gates; the lab adds division attribution, an auditable
    minutes ledger, and institutional reporting on top.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 orchestrator: Optional[SovereignResearchOrchestrator] = None):
        self.config = config or {}
        self.orchestrator = orchestrator or SovereignResearchOrchestrator(config=self.config)
        self.org_chart: List[ResearchDivision] = build_org_chart()
        self.minutes = LabMinutesLedger()
        self._divisions_by_key = {d.key: d for d in self.org_chart}
        self.orchestrator.register_stage_observer(self._observe_stage)

    # ------------------------------------------------------------------
    # Org chart
    # ------------------------------------------------------------------

    def org_chart_report(self) -> Dict[str, Any]:
        """Structured description of the lab's divisions and mandates."""
        return {
            "institution": "AlphaAlgo Institutional Research Lab",
            "divisions": [
                {
                    "key": d.key,
                    "name": d.name,
                    "mandate": d.mandate,
                    "stages": d.stages,
                    "subsystems": d.subsystems,
                }
                for d in self.org_chart
            ],
        }

    # ------------------------------------------------------------------
    # Program execution
    # ------------------------------------------------------------------

    def run_research_program(self, symbol: str, query: str,
                             task_id: Optional[str] = None) -> LabReport:
        """
        Execute the full quantitative research lifecycle through the lab's
        divisions and produce an institutional LabReport.
        """
        program_id = f"prog_{uuid.uuid4().hex[:8]}"
        task_id = task_id or f"lab_{uuid.uuid4().hex[:8]}"
        started_at = datetime.utcnow().isoformat()

        logger.info(
            f"[InstitutionalLab] Convening program {program_id}: "
            f"symbol={symbol} query={query}"
        )
        result = self.orchestrator._execute_full_pipeline(
            {"symbol": symbol, "query": query}, task_id
        )
        finished_at = datetime.utcnow().isoformat()

        task_minutes = self.minutes.replay_task(task_id)
        division_reports = self._compile_division_reports(task_minutes)

        report = LabReport(
            program_id=program_id,
            task_id=task_id,
            symbol=symbol,
            query=query,
            status=result.get("status", "failed"),
            promoted=bool(result.get("promoted", False)),
            strategy_id=result.get("strategy_id"),
            decision=result.get("decision", ""),
            debate_consensus=float(result.get("debate_consensus", 0.0)),
            decision_record_id=result.get("decision_record_id"),
            divisions_engaged=self.minutes.divisions_engaged(task_id),
            division_reports=division_reports,
            minutes=task_minutes,
            started_at=started_at,
            finished_at=finished_at,
        )

        self._archive_program(report)
        return report

    def evaluate_paper_submission(self, title: str, abstract: str,
                                  authors: Optional[List[str]] = None,
                                  task_id: Optional[str] = None) -> Dict[str, Any]:
        """Route a literature submission through the Literature & Discovery Desk."""
        task_id = task_id or f"lab_{uuid.uuid4().hex[:8]}"
        return self.orchestrator._execute_evaluate_paper(
            {"title": title, "abstract": abstract,
             "authors": authors or ["Institutional Lab Intake"]},
            task_id,
        )

    # ------------------------------------------------------------------
    # Minutes access
    # ------------------------------------------------------------------

    def get_minutes(self, task_id: str) -> List[LabMinute]:
        return self.minutes.replay_task(task_id)

    def export_minutes(self) -> List[Dict[str, Any]]:
        return self.minutes.export()

    # ------------------------------------------------------------------
    # Swarm dispatch
    # ------------------------------------------------------------------

    def dispatch_swarm(self, programs: List[Dict[str, Any]],
                       max_workers: int = 4, replication: int = 1):
        """
        Fan research programs out to the Research Swarm (parallel agents,
        each on its own lab instance) and return the SwarmProceedings.
        """
        from trading_bot.research.swarm.swarm import ResearchSwarm
        swarm = ResearchSwarm(max_workers=max_workers, config=self.config)
        return swarm.swarm(programs, replication=replication)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _observe_stage(self, event: Dict[str, Any]) -> None:
        """Stage observer: attribute each kernel stage to its lab division."""
        self.minutes.record(
            task_id=event.get("task_id"),
            division=division_for_stage(event.get("stage", "")),
            stage=event.get("stage", "unknown"),
            status=event.get("status", "completed"),
            details=event.get("details"),
        )

    def _compile_division_reports(self, task_minutes: List[LabMinute]) -> List[DivisionReport]:
        reports: List[DivisionReport] = []
        for division in self.org_chart:
            minutes = [m for m in task_minutes if m.division == division.key]
            report = DivisionReport(
                division_key=division.key,
                division_name=division.name,
                stages_run=len(minutes),
                failed_stages=sum(1 for m in minutes if m.status != "completed"),
            )
            if minutes:
                report.verdict = "failed" if report.failed_stages else "completed"
                for m in minutes:
                    if m.status != "completed":
                        report.objections.append(
                            f"Stage '{m.stage}' {m.status}: {m.details}"
                        )
            reports.append(report)
        return reports

    def _archive_program(self, report: LabReport) -> None:
        self.orchestrator.knowledge_registry.archive_knowledge(report.program_id, {
            "title": f"Lab Proceedings: {report.symbol} / {report.query}",
            "content": (
                f"Status: {report.status}. Promoted: {report.promoted}. "
                f"Decision: {report.decision}"
            ),
            "category": "lab_proceedings",
            "evidence": {
                "status": report.status,
                "promoted": report.promoted,
                "strategy_id": report.strategy_id,
                "debate_consensus": report.debate_consensus,
                "decision_record_id": report.decision_record_id,
                "divisions_engaged": report.divisions_engaged,
                "failed_stages": [
                    {"division": m.division, "stage": m.stage, "status": m.status}
                    for m in report.minutes if m.status != "completed"
                ],
            },
            "tags": [report.symbol, report.query, "institutional_lab"],
        })
