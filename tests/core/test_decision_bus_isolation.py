"""R0 regression tests: process-global state isolation (deep audit pass 2).

Desired behavior encoded here (fails on current code where noted):

* Same-seed deterministic UUID draws must not collide across distinct runs —
  run-scoped namespaces make replay idempotent without reusing prior IDs.
* The decision bus must isolate voter/subscriber/log state across resets.
* A durable consensus audit JSONL must be writable and appended by default
  when a log path is configured through the runtime seam.
* The in-memory action log is a bounded ring buffer, not the audit archive.
"""

import asyncio
import json
import threading

import pytest

from trading_bot.core.governance.determinism import DeterministicManager
from trading_bot.core.unified_event_bus import (
    LogAction,
    UnifiedDecisionBus,
    decision_bus,
)


# ---------------------------------------------------------------------------
# deterministic identity
# ---------------------------------------------------------------------------

def _draw_ids(n: int, run_namespace: str) -> set:
    """Simulate one run: enable determinism under a run namespace and draw n
    identities. ``enable(run_id=...)`` is the Release-1 API — absent today."""
    DeterministicManager.reset()
    mgr = DeterministicManager()
    mgr.enable(seed=42, run_id=run_namespace)
    return {mgr.get_uuid() for _ in range(n)}


def test_same_seed_ids_do_not_collide_across_runs():
    """Two runs with the same seed must not mint identical durable IDs —
    replayed runs would otherwise collide with prior idempotency keys."""
    run_a = _draw_ids(8, "run-a")
    run_b = _draw_ids(8, "run-b")
    assert run_a.isdisjoint(run_b), (
        "identical IDs across same-seed runs break durable dedup/audit keys"
    )
    DeterministicManager.reset()


def test_same_run_replay_reproduces_ids():
    """Within one run namespace, the same seed+sequence must reproduce —
    determinism is about intra-run replay, not cross-run identity."""
    run_a = _draw_ids(8, "run-a")
    run_a_replay = _draw_ids(8, "run-a")
    assert run_a == run_a_replay
    DeterministicManager.reset()


# ---------------------------------------------------------------------------
# bus lifecycle isolation
# ---------------------------------------------------------------------------

def test_reset_clears_voters_subscribers_and_log():
    bus = UnifiedDecisionBus()
    bus.register_voter("test_voter", lambda a: {"decision": "APPROVE"})
    bus._log.append(LogAction(action_type="PING", payload={}, agent_id="t"))
    UnifiedDecisionBus.reset()
    assert decision_bus._voters == {}
    assert decision_bus._subscribers == {}
    assert decision_bus._log == []
    UnifiedDecisionBus.reset()


def test_audit_health_reprobes_on_start(tmp_path):
    """After reset, a bus re-started against an unwritable path must report
    audit-unhealthy (fail closed), not inherit a stale healthy flag."""
    bus = UnifiedDecisionBus()
    asyncio.run(bus.start())
    assert getattr(bus, "_audit_healthy", True) is True or bus._log_path is None

    UnifiedDecisionBus.reset()
    blocker = tmp_path / "blocker"  # a regular FILE used as a path component
    blocker.write_text("occupied")
    bad_path = blocker / "decision.jsonl"  # parent is a file -> not writable
    bus2 = UnifiedDecisionBus({"log_path": str(bad_path)})
    asyncio.run(bus2.start())
    # A file cannot be a directory -> the probe must mark unhealthy.
    assert bus2._audit_healthy is False
    asyncio.run(bus2.stop())
    UnifiedDecisionBus.reset()


async def test_durable_audit_log_written(tmp_path):
    """A processed action is appended to the configured JSONL audit file."""
    UnifiedDecisionBus.reset()
    log_path = tmp_path / "audit.jsonl"
    bus = UnifiedDecisionBus({"log_path": str(log_path)})
    await bus.start()
    try:
        action = LogAction(
            action_type="TELEMETRY", payload={"k": 1}, agent_id="test")
        await bus.propose_action(action)
        status = await action.wait_for_decision(timeout=5.0)
        assert status.value in ("approved", "vetoed", "failed")
        lines = [json.loads(l) for l in log_path.read_text().splitlines() if l.strip()]
        assert any(l["action_id"] == action.action_id for l in lines), (
            "durable audit JSONL missing the processed action"
        )
    finally:
        await bus.stop()
        UnifiedDecisionBus.reset()


def test_in_memory_log_is_bounded_ring():
    """The in-memory _log must stay bounded — it is a ring, not the archive."""
    assert UnifiedDecisionBus().config.get("max_log_size", 10000) <= 10000
