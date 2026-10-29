"""
Research Swarm.

A pool of SwarmResearchAgents that execute research programs in parallel —
the lab's distributed research capacity. Programs may be replicated across
independent agents so the swarm can cross-validate promotion verdicts
(replication desk behavior), and merged findings are archived as swarm
proceedings in the institutional knowledge base.
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from trading_bot.research.knowledge.registry import StandardKnowledgeRegistry
from trading_bot.research.lab.institutional_lab import InstitutionalResearchLab
from trading_bot.research.swarm.agents import (
    ResearchAgentRole,
    ResearchTask,
    SwarmFinding,
    SwarmResearchAgent,
)

logger = logging.getLogger(__name__)


@dataclass
class ProgramVerdict:
    """The swarm's collective verdict on one research program."""
    program_key: str
    replication_count: int
    completed_runs: int
    promoted_votes: int
    verdict: str  # promoted | rejected | inconclusive | error
    replication_agreement: float  # share of runs agreeing with the verdict
    mean_debate_consensus: float
    strategy_ids: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_key": self.program_key,
            "replication_count": self.replication_count,
            "completed_runs": self.completed_runs,
            "promoted_votes": self.promoted_votes,
            "verdict": self.verdict,
            "replication_agreement": self.replication_agreement,
            "mean_debate_consensus": self.mean_debate_consensus,
            "strategy_ids": self.strategy_ids,
            "decisions": self.decisions,
        }


@dataclass
class SwarmProceedings:
    """Institutional record of one swarm session."""
    swarm_id: str
    programs: int
    findings: List[SwarmFinding]
    verdicts: List[ProgramVerdict]
    agents: List[Dict[str, Any]]
    started_at: str
    finished_at: str

    @property
    def promoted_strategies(self) -> List[str]:
        ids: List[str] = []
        for v in self.verdicts:
            if v.verdict == "promoted":
                ids.extend(v.strategy_ids)
        return ids

    def to_dict(self) -> Dict[str, Any]:
        return {
            "swarm_id": self.swarm_id,
            "programs": self.programs,
            "findings": [f.to_dict() for f in self.findings],
            "verdicts": [v.to_dict() for v in self.verdicts],
            "agents": self.agents,
            "promoted_strategies": self.promoted_strategies,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class ResearchSwarm:
    """
    Coordinates a pool of research agents executing programs in parallel.

    Each agent owns a private InstitutionalResearchLab, so concurrent programs
    are isolated. With ``replication > 1`` each program is run by independent
    agents and the swarm cross-validates their promotion verdicts.
    """

    def __init__(self, max_workers: int = 4, config: Optional[Dict[str, Any]] = None,
                 lab_factory: Optional[Callable[[], InstitutionalResearchLab]] = None,
                 proceedings_registry: Optional[StandardKnowledgeRegistry] = None):
        self.config = config or {}
        self.max_workers = max(1, max_workers)
        self._lab_factory = lab_factory or InstitutionalResearchLab
        # When driven by an InstitutionalResearchLab, proceedings archive into
        # the lab's knowledge registry so the institutional KB is complete.
        self.proceedings_registry = proceedings_registry or StandardKnowledgeRegistry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def swarm(self, programs: List[Dict[str, Any]], replication: int = 1) -> SwarmProceedings:
        """
        Execute research programs in parallel and return the swarm proceedings.

        ``programs`` entries: {"kind": "full_pipeline", "symbol": ..., "query": ...}
        or {"kind": "evaluate_paper", "title": ..., "abstract": ...}.
        ``replication`` re-runs each program on independent agents.
        """
        swarm_id = f"swarm_{uuid.uuid4().hex[:8]}"
        started_at = datetime.utcnow().isoformat()
        replication = max(1, replication)

        tasks = self._build_tasks(programs, replication, swarm_id)
        agents = self._fan_out(tasks, programs, replication)

        verdicts = self._adjudicate(programs, agents["findings"], replication)
        finished_at = datetime.utcnow().isoformat()

        proceedings = SwarmProceedings(
            swarm_id=swarm_id,
            programs=len(programs),
            findings=agents["findings"],
            verdicts=verdicts,
            agents=agents["agents"],
            started_at=started_at,
            finished_at=finished_at,
        )
        self._archive_proceedings(proceedings)
        return proceedings

    def get_status(self) -> Dict[str, Any]:
        return {
            "max_workers": self.max_workers,
            "proceedings_archived": len(self.proceedings_registry._archive),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_tasks(self, programs: List[Dict[str, Any]],
                     replication: int, swarm_id: str) -> List[ResearchTask]:
        tasks: List[ResearchTask] = []
        for program in programs:
            kind = program.get("kind", "full_pipeline")
            program_key = program.get("program_key") or self._program_key(program)
            for rep in range(replication):
                role = ResearchAgentRole.ANALYST if rep == 0 else ResearchAgentRole.REPLICATOR
                if kind == "evaluate_paper":
                    role = ResearchAgentRole.SCOUT if rep == 0 else ResearchAgentRole.REPLICATOR
                tasks.append(ResearchTask(
                    task_id=f"{swarm_id}_t{len(tasks)}",
                    kind=kind,
                    payload=dict(program),
                    program_key=program_key,
                    role=role,
                ))
        return tasks

    def _fan_out(self, tasks: List[ResearchTask], programs: List[Dict[str, Any]],
                 replication: int) -> Dict[str, Any]:
        """
        Provision agents and execute tasks in parallel.

        Each replication index gets its own agent pool so replicated runs of the
        same program always land on different agents (independent labs) — a
        re-run on the same agent would not be a true replication.
        """
        seats = min(self.max_workers, max(1, len(programs)))
        pools: List[List[SwarmResearchAgent]] = []
        for rep in range(replication):
            role = ResearchAgentRole.ANALYST if rep == 0 else ResearchAgentRole.REPLICATOR
            pools.append([
                SwarmResearchAgent(role=role, lab_factory=self._lab_factory)
                for _ in range(seats)
            ])

        # Tasks are emitted program-major, replication-minor (see _build_tasks),
        # so rep index = position within each program block.
        findings: List[SwarmFinding] = []
        with ThreadPoolExecutor(max_workers=seats * replication) as pool:
            futures = {}
            for i, task in enumerate(tasks):
                rep = i % replication
                agent = pools[rep][(i // replication) % len(pools[rep])]
                futures[pool.submit(agent.execute, task)] = task
            for future in as_completed(futures):
                findings.append(future.result())

        order = {t.task_id: i for i, t in enumerate(tasks)}
        findings.sort(key=lambda f: order.get(f.task_id, 0))
        all_agents = [a for rep_pool in pools for a in rep_pool]
        return {"findings": findings, "agents": [a.get_status() for a in all_agents]}

    def _adjudicate(self, programs: List[Dict[str, Any]],
                    findings: List[SwarmFinding], replication: int) -> List[ProgramVerdict]:
        verdicts: List[ProgramVerdict] = []
        for program in programs:
            program_key = program.get("program_key") or self._program_key(program)
            kind = program.get("kind", "full_pipeline")
            runs = [f for f in findings if f.program_key == program_key]
            completed = [f for f in runs if f.status in ("success", "failed", "rejected")]
            promoted_votes = sum(1 for f in completed if f.promoted)

            if kind == "evaluate_paper":
                # Literature ingestion programs: a completed run that ingested
                # is a success; a duplicate rejection is a legitimate outcome.
                ingested = sum(1 for f in completed if f.status == "success")
                if not completed:
                    verdict, agreement = "error", 0.0
                else:
                    verdict = "ingested" if ingested else "rejected"
                    agreement = max(ingested, len(completed) - ingested) / len(completed)
            elif not completed:
                verdict = "error"
                agreement = 0.0
            else:
                majority_promoted = promoted_votes > len(completed) / 2
                unanimous = promoted_votes in (0, len(completed))
                if unanimous:
                    verdict = "promoted" if majority_promoted else "rejected"
                else:
                    verdict = "inconclusive"
                agree = max(promoted_votes, len(completed) - promoted_votes)
                agreement = agree / len(completed)

            consensus_vals = [f.debate_consensus for f in completed if f.debate_consensus]
            verdicts.append(ProgramVerdict(
                program_key=program_key,
                replication_count=replication,
                completed_runs=len(completed),
                promoted_votes=promoted_votes,
                verdict=verdict,
                replication_agreement=agreement,
                mean_debate_consensus=(sum(consensus_vals) / len(consensus_vals)) if consensus_vals else 0.0,
                strategy_ids=[f.strategy_id for f in completed if f.strategy_id],
                decisions=[f.decision for f in completed if f.decision],
            ))
        return verdicts

    def _archive_proceedings(self, proceedings: SwarmProceedings) -> None:
        promoted = proceedings.promoted_strategies
        inconclusive = [v.program_key for v in proceedings.verdicts if v.verdict == "inconclusive"]
        self.proceedings_registry.archive_knowledge(proceedings.swarm_id, {
            "title": f"Swarm Proceedings {proceedings.swarm_id}",
            "content": (
                f"{proceedings.programs} program(s), "
                f"{len(proceedings.findings)} run(s), "
                f"{len(promoted)} promoted strateg(ies). "
                f"Inconclusive programs: {inconclusive or 'none'}."
            ),
            "category": "swarm_proceedings",
            "evidence": proceedings.to_dict(),
            "tags": ["research_swarm"],
        })

    @staticmethod
    def _program_key(program: Dict[str, Any]) -> str:
        kind = program.get("kind", "full_pipeline")
        if kind == "evaluate_paper":
            return f"paper:{program.get('title', 'untitled')}"
        return f"pipeline:{program.get('symbol', 'EURUSD')}:{program.get('query', 'microstructure')}"
