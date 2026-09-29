"""
Self-Mastery Orchestrator — wires the self_mastery subsystem into one loop.

Composes the four existing components:
  ExperienceMemory      — what happened (episodic store)
  SelfReflector         — why it happened (insight extraction)
  KnowledgeConsolidator — what persists (skill ledger)
  CodeEvolver           — what changes (bounded, safety-checked proposals)

The orchestrator runs the ingest -> reflect -> consolidate -> evolve ->
verify cycle. Every stage is advisory: `evolve()` produces *proposals*
through the safety-gated CodeEvolver, never self-modifies code directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from .experience_memory import (
    DecisionContext,
    ExperienceMemory,
    ExperienceType,
    TradeExperience,
)
from .self_reflection import SelfReflector, ReflectionInsight
from .knowledge_consolidator import KnowledgeConsolidator, MasteredSkill
from .code_evolver import CodeEvolver

logger = logging.getLogger(__name__)

__all__ = [
    "MasteryPhase",
    "MasteryStatus",
    "MasteryConfig",
    "MasteryOrchestrator",
    "quick_start",
]


class MasteryPhase(Enum):
    """Stages of one mastery cycle."""
    INGEST = "ingest"
    REFLECT = "reflect"
    CONSOLIDATE = "consolidate"
    EVOLVE = "evolve"
    VERIFY = "verify"


class MasteryStatus(Enum):
    """Skill mastery classification derived from application outcomes."""
    LEARNING = "learning"
    PROGRESSING = "progressing"
    MASTERED = "mastered"
    DEGRADED = "degraded"


@dataclass
class MasteryConfig:
    """Thresholds governing the mastery loop."""
    mastery_threshold: float = 0.8     # application_success_rate -> MASTERED
    progress_threshold: float = 0.5    # -> PROGRESSING
    min_applications: int = 5          # samples before mastery can be claimed
    reflection_depth: str = "normal"   # quick | normal | deep
    max_evolution_proposals: int = 5   # bound on proposals per cycle
    data_dir: str = "self_mastery_data"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MasteryOrchestrator:
    """Runs the self-mastery cycle over the four component subsystems."""

    def __init__(self, data_dir: str = "self_mastery_data",
                 config: Optional[MasteryConfig] = None) -> None:
        self.config = config or MasteryConfig(data_dir=data_dir)
        self.memory = ExperienceMemory(data_dir=self.config.data_dir)
        self.reflector = SelfReflector(self.memory, data_dir=self.config.data_dir)
        self.consolidator = KnowledgeConsolidator(data_dir=self.config.data_dir)
        self.evolver = CodeEvolver(data_dir=self.config.data_dir)
        self.phase = MasteryPhase.INGEST
        logger.info("MasteryOrchestrator initialized (data_dir=%s)", self.config.data_dir)

    # -- INGEST ----------------------------------------------------------
    def record_trade(self, action: str = "", symbol: str = "",
                     quantity: float = 0.0,
                     context: Optional[DecisionContext] = None,
                     experience_type: Optional[ExperienceType] = None,
                     reasoning: str = "", confidence: float = 0.5,
                     tags: Optional[List[str]] = None,
                     importance: float = 0.5) -> str:
        """Record a decision as a TradeExperience and store it."""
        from datetime import datetime
        ctx = context or DecisionContext(
            timestamp=datetime.now(), price=0.0, volume=0.0,
            volatility=0.0, spread=0.0, regime="", trend="sideways",
            confidence=confidence, risk_level=0.0, current_position=0.0,
            unrealized_pnl=0.0, drawdown=0.0,
        )
        exp = self.memory.create_experience(
            experience_type or ExperienceType.TRADE_EXECUTED,
            action, symbol, quantity, ctx,
            reasoning=reasoning, confidence=confidence,
            tags=tags or [], importance=importance,
        )
        return self.memory.remember(exp)

    def record_outcome(self, experience_id: str = "",
                       analysis: Optional[Any] = None) -> bool:
        """Attach outcome analysis / mark an experience processed."""
        if not experience_id:
            return False
        if analysis is not None:
            self.memory.update_outcome(experience_id, analysis)
        else:
            self.memory.mark_processed(experience_id)
        return True

    # -- REFLECT ---------------------------------------------------------
    def reflect(self, depth: Optional[str] = None) -> List[ReflectionInsight]:
        """Run self-reflection over recent experiences."""
        self.phase = MasteryPhase.REFLECT
        return self.reflector.reflect(depth or self.config.reflection_depth)

    # -- CONSOLIDATE -----------------------------------------------------
    def consolidate(
        self, insights: Optional[List[Any]] = None
    ) -> Any:
        """Fold insights (or a fresh reflection) into the skill ledger."""
        self.phase = MasteryPhase.CONSOLIDATE
        if insights is None:
            insights = self.reflect()
        dicts = [
            i.to_dict() if hasattr(i, "to_dict") else dict(i) if isinstance(i, dict) else {"insight": str(i)}
            for i in insights
        ]
        return self.consolidator.consolidate_from_insights(dicts)

    # -- EVOLVE ----------------------------------------------------------
    def evolve(self, insights: Optional[List[ReflectionInsight]] = None,
               max_proposals: Optional[int] = None) -> List[Any]:
        """Turn actionable insights into safety-checked evolution proposals."""
        self.phase = MasteryPhase.EVOLVE
        if insights is None:
            insights = self.reflector.get_actionable_insights()
        proposals = []
        for insight in (insights or [])[:max_proposals or self.config.max_evolution_proposals]:
            try:
                proposals.append(self.evolver.propose_from_insight(
                    getattr(insight.insight_type, "name", str(insight.insight_type)),
                    insight.description,
                    insight.action_recommendation,
                    insight.evidence,
                    insight.confidence,
                ))
            except Exception as exc:  # noqa: BLE001 - a bad insight must not kill the loop
                logger.warning("Evolve: proposal from insight failed: %s", exc)
        return proposals

    # -- VERIFY ----------------------------------------------------------
    def verify_skill_mastery(
        self, skill_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify mastery status from application success rates."""
        self.phase = MasteryPhase.VERIFY
        cfg = self.config
        due = self.consolidator.get_skills_due_for_review()
        summary = {"due_for_review": len(due), "verified": []}
        skills = [s for s in self.consolidator.skills.values()
                  if skill_id is None or s.skill_id == skill_id]
        for s in skills:
            rate = s.application_success_rate()
            applications = s.successful_applications + s.failed_applications
            if applications < cfg.min_applications:
                status = MasteryStatus.LEARNING
            elif rate >= cfg.mastery_threshold and not s.needs_review():
                status = MasteryStatus.MASTERED
            elif rate >= cfg.progress_threshold:
                status = MasteryStatus.PROGRESSING
            else:
                status = MasteryStatus.DEGRADED
            entry = {"skill_id": s.skill_id, "name": s.name,
                     "status": status.value, "success_rate": rate,
                     "applications": applications}
            summary["verified"].append(entry)
        return summary

    def get_learning_recommendations(self) -> List[str]:
        """Recommendations from actionable insights + weakest skills."""
        recs = [
            getattr(i, "recommendation", None) or str(i)
            for i in self.reflector.get_actionable_insights()
        ]
        for skill in self.consolidator.get_weakest_skills(3):
            recs.append(f"Review skill '{skill.name}' "
                        f"(success rate {skill.application_success_rate():.0%})")
        return recs

    def run_continuous_learning(self, cycles: int = 1) -> Dict[str, Any]:
        """One bounded pass per cycle: ingest-unprocessed -> reflect ->
        consolidate -> evolve -> verify. Advisory only; returns a report."""
        report: Dict[str, Any] = {"cycles": cycles, "phases": []}
        for _ in range(cycles):
            for exp in self.memory.get_unprocessed():
                self.memory.mark_processed(exp.experience_id)
            insights = self.reflect()
            consolidation = self.consolidate(insights)
            proposals = self.evolve(insights)
            verification = self.verify_skill_mastery()
            report["phases"].append({
                "insights": len(insights or []),
                "consolidation": consolidation.to_dict()
                    if hasattr(consolidation, "to_dict") else str(consolidation),
                "proposals": len(proposals),
                "verified_skills": len(verification["verified"]),
            })
        return report

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "config": self.config.to_dict(),
            "memory_stats": self.memory.get_statistics(),
            "reflection_summary": self.reflector.get_reflection_summary(),
        }


def quick_start(data_dir: str = "self_mastery_data",
                config: Optional[MasteryConfig] = None) -> MasteryOrchestrator:
    """Construct a ready-to-use orchestrator with default wiring."""
    return MasteryOrchestrator(data_dir=data_dir, config=config)
