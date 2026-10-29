"""
Research Swarm Agents.

Individual researcher agents of the swarm. Each agent owns a private
InstitutionalResearchLab (and therefore a private SovereignResearchOrchestrator),
so parallel programs never share mutable registries, graphs, or schedulers —
mirroring how institutional desks run independent research seats.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

from trading_bot.research.lab.institutional_lab import InstitutionalResearchLab, LabReport

logger = logging.getLogger(__name__)


class ResearchAgentRole(Enum):
    """Seat a swarm agent occupies during a program."""
    SCOUT = "scout"            # literature discovery & ingestion
    ANALYST = "analyst"        # full 14-stage pipeline execution
    REPLICATOR = "replicator"  # independent re-run for cross-validation


@dataclass
class ResearchTask:
    """One unit of research work dispatched to the swarm."""
    task_id: str
    kind: str  # "full_pipeline" | "evaluate_paper"
    payload: Dict[str, Any]
    program_key: str
    role: ResearchAgentRole = ResearchAgentRole.ANALYST


@dataclass
class SwarmFinding:
    """What one agent produced for one task."""
    agent_id: str
    role: str
    task_id: str
    program_key: str
    status: str
    promoted: bool = False
    strategy_id: Optional[str] = None
    decision: str = ""
    debate_consensus: float = 0.0
    lab_report: Optional[Dict[str, Any]] = None
    backtest: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    finished_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "task_id": self.task_id,
            "program_key": self.program_key,
            "status": self.status,
            "promoted": self.promoted,
            "strategy_id": self.strategy_id,
            "decision": self.decision,
            "debate_consensus": self.debate_consensus,
            "backtest": self.backtest,
            "error": self.error,
            "finished_at": self.finished_at,
        }


class SwarmResearchAgent:
    """
    One researcher seat in the swarm.

    Holds a private lab instance; executes dispatched tasks through its lab's
    divisions so every finding carries full institutional lineage.
    """

    def __init__(self, role: ResearchAgentRole,
                 lab_factory: Optional[Callable[[], InstitutionalResearchLab]] = None,
                 agent_id: Optional[str] = None):
        self.agent_id = agent_id or f"agent_{role.value}_{uuid.uuid4().hex[:6]}"
        self.role = role
        self._lab_factory = lab_factory or InstitutionalResearchLab
        self.lab: Optional[InstitutionalResearchLab] = None
        self.tasks_completed = 0
        self.tasks_failed = 0

    def _get_lab(self) -> InstitutionalResearchLab:
        if self.lab is None:
            self.lab = self._lab_factory()
        return self.lab

    def execute(self, task: ResearchTask) -> SwarmFinding:
        """Execute one research task and return a structured finding."""
        logger.info(f"[Swarm] {self.agent_id} ({self.role.value}) executing {task.kind} "
                    f"for program '{task.program_key}'")
        try:
            lab = self._get_lab()
            if task.kind == "full_pipeline":
                report: LabReport = lab.run_research_program(
                    symbol=task.payload.get("symbol", "EURUSD"),
                    query=task.payload.get("query", "microstructure"),
                    task_id=task.task_id,
                )
                self.tasks_completed += 1
                return SwarmFinding(
                    agent_id=self.agent_id,
                    role=task.role.value,
                    task_id=task.task_id,
                    program_key=task.program_key,
                    status=report.status,
                    promoted=report.promoted,
                    strategy_id=report.strategy_id,
                    decision=report.decision,
                    debate_consensus=report.debate_consensus,
                    lab_report=report.to_dict(),
                    backtest={},
                )
            elif task.kind == "evaluate_paper":
                result = lab.evaluate_paper_submission(
                    title=task.payload.get("title", ""),
                    abstract=task.payload.get("abstract", ""),
                    authors=task.payload.get("authors"),
                    task_id=task.task_id,
                )
                status = result.get("status", "failed")
                if status == "success":
                    self.tasks_completed += 1
                else:
                    self.tasks_failed += 1
                return SwarmFinding(
                    agent_id=self.agent_id,
                    role=task.role.value,
                    task_id=task.task_id,
                    program_key=task.program_key,
                    status=status,
                    decision=result.get("reason", "ingested"),
                    lab_report={"paper_result": result,
                                "minutes": [m.to_dict() for m in lab.get_minutes(task.task_id)]},
                )
            else:
                self.tasks_failed += 1
                return SwarmFinding(
                    agent_id=self.agent_id,
                    role=task.role.value,
                    task_id=task.task_id,
                    program_key=task.program_key,
                    status="failed",
                    error=f"unsupported task kind: {task.kind}",
                )
        except Exception as e:  # an agent's failure must not sink the swarm
            self.tasks_failed += 1
            logger.error(f"[Swarm] {self.agent_id} failed on {task.kind}: {e}")
            return SwarmFinding(
                agent_id=self.agent_id,
                role=task.role.value,
                task_id=task.task_id,
                program_key=task.program_key,
                status="error",
                error=str(e),
            )

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
        }
