"""SRE bridge x neuro-symbolic gate: a hypothesis that declares a
target_action is policy-gated in its advisory artifact — live_exec
refused, risky promote pending approval, research allowed."""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from trading_bot.core.csc.sre_bridge import SREAdvisoryService  # noqa
from trading_bot.core.csc.neuro_symbolic import (  # noqa: E402
    Ledger, NeuroSymbolicReasoner)


class _FakeEngine:
    def __init__(self, hyp):
        self.registry = {}
        self._hyp = hyp

    async def run_cycle(self, ctx):
        return "h1"

    def get_hypothesis(self, hid):
        return self._hyp


def _hyp(action):
    return SimpleNamespace(
        id="h1", name="t", state=SimpleNamespace(name="CONFIRMED"),
        level=SimpleNamespace(name="L1"), posterior=0.9,
        uncertainty=0.1, p_lower=0.8, p_upper=0.95,
        validation_score=0.7, calibration_error=0.05,
        expected_value=0.01, boundary_conditions={},
        model_params={"target_action": action})


def _svc(tmp_path, action):
    reasoner = NeuroSymbolicReasoner(
        ctx={}, ledger=Ledger(tmp_path / "nsr.jsonl"))
    return SREAdvisoryService(_FakeEngine(_hyp(action)),
                              reasoner=reasoner)


def _analyze_settled(svc):
    """analyze() is stale-while-revalidate: the lifecycle runs in a
    worker thread, so drive the loop until it lands, then re-read the
    artifact that carries the policy verdict."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(svc.analyze({}))
    pending = getattr(svc, "_pending", None)
    if pending is not None:
        loop.run_until_complete(pending)
    return loop.run_until_complete(svc.analyze({}))


def test_live_exec_hypothesis_gated_refused(tmp_path):
    rep = _analyze_settled(_svc(tmp_path, "live_exec"))
    pol = rep["evidence"]["policy"]
    assert pol["status"] == "gated" and pol["gate"] == "refused"


def test_promote_hypothesis_pending_approval(tmp_path):
    rep = _analyze_settled(_svc(tmp_path, "promote"))
    pol = rep["evidence"]["policy"]
    assert pol["gate"] == "requires_signed_approval"
    assert pol["verdict"] == "pending_approval"


def test_research_action_allowed(tmp_path):
    rep = _analyze_settled(_svc(tmp_path, "trading_research"))
    pol = rep["evidence"]["policy"]
    assert pol["status"] == "gated"
    assert pol["verdict"] in ("allowed", "needs_regression")


def test_no_action_not_applicable(tmp_path):
    h = _hyp(None)
    svc = SREAdvisoryService(
        _FakeEngine(h),
        NeuroSymbolicReasoner(ctx={}, ledger=Ledger(tmp_path / "n.jsonl")))
    rep = _analyze_settled(svc)
    assert rep["evidence"]["policy"]["status"] == "not_applicable"
