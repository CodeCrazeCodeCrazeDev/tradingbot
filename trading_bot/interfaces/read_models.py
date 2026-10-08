"""Read-only projections for API, CLI, dashboards, and operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from trading_bot.foundation.runtime import ModularMonolithRuntime


class ModularMonolithReadModel:
    """Expose runtime state without importing domain authorities directly."""

    def __init__(self, runtime: ModularMonolithRuntime):
        self.runtime = runtime

    def component_graph(self) -> list:
        return self.runtime.component_graph()

    async def health(self) -> Dict[str, Any]:
        return await self.runtime.health_check()

    async def portfolio(self, account_id: str = "runtime") -> Dict[str, Any]:
        repository = self.runtime.bot.trading_repository
        if repository is None:
            return {"account_id": account_id, "positions": [], "available": False}
        snapshot = await repository.snapshot(account_id)
        return snapshot.to_dict()

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.runtime.running,
            "component_count": len(self.component_graph()),
            "mode": self.runtime.bot.execution_mode,
        }

    def ai_stack(self) -> Dict[str, Any]:
        """Three-plane AI snapshot (state/evidence/selection) — the §4
        read surface. Empty projection when the brain is not wired."""
        stack = getattr(self.runtime, "ai_stack", None)
        if stack is None:
            return {"available": False}
        snap = dict(stack.snapshot())
        snap["available"] = True
        return snap

    def decision_journal(self) -> Dict[str, Any]:
        """Read-only view of the CSC decision journal: pending predictions,
        folded summaries, and measured reliability. Empty projection when the
        brain is not wired."""
        csc = getattr(self.runtime.bot, "csc", None)
        if csc is None or not hasattr(csc, "get_decision_journal"):
            return {"available": False}
        journal = csc.get_decision_journal()
        journal["available"] = True
        return journal

    async def explain_decision(self, trade_id: str) -> Dict[str, Any]:
        """Advisory-only explanation of one decision from the durable audit
        trail: the DECISION event, its outcome if settled, and the pending
        prediction if still open. Never returns authority fields."""
        repository = getattr(self.runtime.bot, "trading_repository", None)
        csc = getattr(self.runtime.bot, "csc", None)
        explanation: Dict[str, Any] = {"trade_id": trade_id}
        if repository is not None and hasattr(repository, "list_audit_events"):
            rows = await repository.list_audit_events(correlation_id=trade_id)
            explanation["audit_trail"] = rows
        if csc is not None:
            pending = getattr(csc, "_pending_predictions", {})
            if trade_id in pending:
                explanation["pending_prediction"] = dict(pending[trade_id])
        if not explanation.get("audit_trail") and "pending_prediction" not in explanation:
            explanation["status"] = "no_record"
        return explanation

    async def dashboard_snapshot(self, account_id: str = "runtime") -> Dict[str, Any]:
        """Read-only projection for dashboards; no domain authority is exposed."""
        return {
            "status": self.status(),
            "health": await self.health(),
            "portfolio": await self.portfolio(account_id),
            "decision_journal": self.decision_journal(),
            "ai_stack": self.ai_stack(),
        }

    async def report_snapshot(self, account_id: str = "runtime") -> Dict[str, Any]:
        """Read-only projection for reporting and notifications."""
        snapshot = await self.portfolio(account_id)
        return {
            "account_id": account_id,
            "mode": self.runtime.bot.execution_mode,
            "component_count": len(self.component_graph()),
            "position_count": len(snapshot.get("positions", [])),
            "positions": snapshot.get("positions", []),
        }
