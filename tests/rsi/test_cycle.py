"""End-to-end Level-1 cycle tests (mission §17 machine-verifiable cases)."""

from __future__ import annotations

import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from trading_bot.recursive_self_improvement.archive import ParetoArchive
from trading_bot.recursive_self_improvement.candidate_adapters import ADAPTERS
from trading_bot.recursive_self_improvement.engine_v2 import (
    AuthorizationError, CandidateGenerator, CycleConfig, Hypothesis,
    IndependentVerifier, OperatorAuthorization, PromotionLadder,
    RecursiveImprovementCycle, SandboxManager)
from trading_bot.recursive_self_improvement.improvement_genome import (
    ImprovementDomain)
from trading_bot.recursive_self_improvement.memory import ImprovementMemory
from trading_bot.recursive_self_improvement.meta_proposals import (
    gate_meta, level2_proposal, level3_proposal)
from trading_bot.recursive_self_improvement.protected_control_plane import (
    ProtectedPathGuard)
from trading_bot.recursive_self_improvement.rollback import (
    ChampionRollback, ChampionState)

from tests.rsi.helpers import make_contract, make_frames, make_genome


@pytest.fixture()
def frames():
    return make_frames()


@pytest.fixture()
def stack(tmp_path, frames):
    contract = make_contract(frames)
    operator = Ed25519PrivateKey.generate()
    # Provisioned custody: the verifier key lives in an operator-controlled
    # file, so signed reports may carry holdout_attested=True.
    key_file = tmp_path / "verifier.pem"
    IndependentVerifier(
        private_key=Ed25519PrivateKey.generate()).export_private_key(str(key_file))
    verifier = IndependentVerifier(key_path=str(key_file))
    archive = ParetoArchive(tmp_path / "archive.jsonl")
    memory = ImprovementMemory(str(tmp_path / "mem.db"))
    guard = ProtectedPathGuard()
    cycle = RecursiveImprovementCycle(
        contract=contract, verifier=verifier, archive=archive, memory=memory,
        guard=guard, frames=frames,
        incumbent_params={"lookback": 100, "entry_threshold": 1.0},
        adapter=ADAPTERS["mean_reversion"],
        config=CycleConfig(run_transfer=False, max_candidates_per_cycle=4))
    return {
        "contract": contract, "operator": operator, "verifier": verifier,
        "archive": archive, "memory": memory, "guard": guard, "cycle": cycle,
    }


# -- full cycle: observe -> hypothesize -> candidate -> verify -> gate --------
def test_run_cycle_produces_gated_decisions(stack):
    decisions = stack["cycle"].run_cycle()
    assert decisions, "cycle produced no decisions"
    assert all(d.status in ("rejected", "insufficient_evidence",
                            "eligible_for_operator_review") for d in decisions)
    # never a promotion claim
    assert all(d.status != "promoted" for d in decisions)
    # every trial archived with lineage
    records = [r for r in stack["archive"].records if r["kind"] == "record"]
    assert len(records) == len(decisions)
    assert all(r["parent_id"] == stack["contract"]["baseline_hash"]
               for r in records)
    # every trial logged to append-only evidence ledger
    assert stack["memory"].verify_evidence_chain()


def test_planted_edge_candidate_reaches_eligible(stack):
    decisions = stack["cycle"].run_cycle()
    winners = [d for d in decisions if d.status == "eligible_for_operator_review"]
    assert winners, "planted oscillation edge should clear all gates"
    rec = stack["archive"].by_id(winners[0].genome_id)
    assert rec["role"] in ("challenger", "champion")


def test_ephemeral_verifier_custody_never_reaches_eligible(stack):
    """An in-process generated key has no auditable custody: reports it
    signs must be stamped unattested, so the verdict cannot reach
    eligible_for_operator_review even on a planted edge."""
    ephemeral = IndependentVerifier()  # no key material provisioned
    cycle = RecursiveImprovementCycle(
        contract=stack["contract"], verifier=ephemeral,
        archive=stack["archive"], memory=stack["memory"],
        guard=stack["guard"], frames=stack["cycle"].frames,
        incumbent_params={"lookback": 100, "entry_threshold": 1.0},
        adapter=ADAPTERS["mean_reversion"],
        config=CycleConfig(run_transfer=False, max_candidates_per_cycle=4))
    decisions = cycle.run_cycle()
    assert decisions
    assert all(d.status != "eligible_for_operator_review" for d in decisions)


def test_out_of_bounds_candidate_rejected(stack):
    from trading_bot.recursive_self_improvement.engine_v2 import PerformanceGap
    genome = make_genome(stack["contract"], value=999)
    assert stack["archive"].by_id(genome.genome_id) is None
    # out-of-bounds via direct genome -> adapter check inside trial path
    gap = PerformanceGap("below_hurdle", "net_return", "all", 1.0)
    # craft a hypothesis outside bounds
    hyp = Hypothesis("H1", "x", "p", "a", "f", ImprovementDomain.TRADING_POLICY,
                     "lookback", 999.0, 1.0, 1.0)
    from trading_bot.recursive_self_improvement.engine_v2 import (
        CandidateGenerator, SandboxManager)
    d = stack["cycle"]._run_trial(
        hyp, CandidateGenerator(), SandboxManager(stack["guard"], 10), None,
        "t-x")
    assert d.status == "rejected"


# -- §17: L2/L3 meta proposals gated -------------------------------------------
def test_meta_proposals_rejected_in_cycle(stack):
    contract = stack["contract"]
    l2 = level2_proposal("prioritizer_weight", {"gain_weight": 2.0},
                         "test", contract["baseline_hash"])
    l3 = level3_proposal("max_drawdown", 0.9,
                         "test", contract["baseline_hash"])
    # contract caps recursion at 1 -> depth bound fires
    assert gate_meta(l2, contract) == "candidate exceeds contract max_recursion_depth"
    assert gate_meta(l3, contract) == "candidate exceeds contract max_recursion_depth"
    # even when depth permits, meta levels need out-of-band authorization
    deep = dict(contract, max_recursion_depth=3)
    assert gate_meta(l2, deep) == "level_requires_out_of_band_authorization"
    assert gate_meta(l3, deep) == "level_requires_out_of_band_authorization"


# -- §17: sandbox interruption is safe ------------------------------------------
def test_sandbox_interruption(stack, tmp_path):
    protected = tmp_path / "safe.txt"
    protected.write_text("x")
    guard = ProtectedPathGuard(paths=["safe.txt"], root=tmp_path)
    sandbox = SandboxManager(guard, wall_clock_s=0.3)

    def slow():
        time.sleep(5)
        return 1

    res = sandbox.run(slow)
    assert res.status == "interrupted"
    assert protected.read_text() == "x"


# -- §17: protected control-plane violation detected ----------------------------
def test_protected_path_violation(stack, tmp_path):
    protected = tmp_path / "risk_service.py"
    protected.write_text("v1")
    guard = ProtectedPathGuard(paths=["risk_service.py"], root=tmp_path)
    sandbox = SandboxManager(guard, wall_clock_s=10)

    def tamper():
        protected.write_text("v2-hacked")
        return "ok"

    res = sandbox.run(tamper)
    assert res.status == "protected_violation"
    assert "risk_service.py" in res.error


# -- §17: rollback restores the previous champion -------------------------------
def test_rollback_restores_champion_state(tmp_path):
    archive = ParetoArchive(tmp_path / "archive.jsonl")
    rb = ChampionRollback(tmp_path / "snaps", archive)
    a = ChampionState("snap-a", "genome-a", {"lookback": 20}, "c-hash", "d-hash",
                      "mean_reversion", (7,), "code", "deps")
    b = ChampionState("snap-b", "genome-b", {"lookback": 50}, "c-hash2", "d-hash",
                      "mean_reversion", (7,), "code", "deps")
    rb.snapshot(a)
    rb.snapshot(b)
    restored = rb.restore("snap-a")
    assert restored is not None
    assert restored.parameters == {"lookback": 20}
    assert restored.genome_id == "genome-a"
    # rollback event appended
    assert any(r["kind"] == "rollback" for r in archive.records)
    # snapshot files preserved
    assert (tmp_path / "snaps" / "snap-b.json").exists()


# -- §17: production stages need signed operator authorization ------------------
def test_promotion_ladder_authorization(stack):
    from trading_bot.recursive_self_improvement.contracts import contract_hash

    op = stack["operator"]
    ladder = PromotionLadder(op.public_key(), clock=lambda: 1000.0)
    gid = "genome-x"
    chash = contract_hash(stack["contract"])
    ladder.record_evaluation(gid, chash, "eligible_for_operator_review")

    with pytest.raises(AuthorizationError):
        ladder.advance(gid, "shadow")

    # wrong key
    wrong = Ed25519PrivateKey.generate()
    auth = OperatorAuthorization(gid, chash, "shadow", "op", 2000.0)
    with pytest.raises(AuthorizationError):
        ladder.advance(gid, "shadow", auth, wrong.sign(auth.canonical()).hex())

    # expired
    stale = OperatorAuthorization(gid, chash, "shadow", "op", 500.0)
    with pytest.raises(AuthorizationError):
        ladder.advance(gid, "shadow", stale, op.sign(stale.canonical()).hex())

    # mismatched stage
    mism = OperatorAuthorization(gid, chash, "paper", "op", 2000.0)
    with pytest.raises(AuthorizationError):
        ladder.advance(gid, "shadow", mism, op.sign(mism.canonical()).hex())

    # valid
    ok = ladder.advance(gid, "shadow", auth, op.sign(auth.canonical()).hex())
    assert ok == "shadow" and ladder.state(gid) == "shadow"
    assert ladder.rollback(gid) == "rolled_back"


# -- §17: identical experiments are reproducible ---------------------------------
def test_verifier_deterministic(stack, frames):
    genome = make_genome(stack["contract"])
    kwargs = dict(
        contract=stack["contract"], adapter=ADAPTERS["mean_reversion"],
        frames=frames, incumbent_params={"lookback": 100, "entry_threshold": 1.0},
        candidate_params={"lookback": 50, "entry_threshold": 1.0},
        genome=genome, trial_id="t", trial_count=1, latency_ms=1.0)
    r1, s1 = stack["verifier"].evaluate(**kwargs)
    r2, s2 = stack["verifier"].evaluate(**kwargs)
    assert r1 == r2 and s1 == s2


def test_frames_hash_binding(stack, frames):
    genome = make_genome(stack["contract"])
    other = make_frames(seed=99)
    with pytest.raises(ValueError):
        stack["verifier"].evaluate(
            contract=stack["contract"], adapter=ADAPTERS["mean_reversion"],
            frames=other, incumbent_params={"lookback": 100},
            candidate_params={"lookback": 50}, genome=genome,
            trial_id="t", trial_count=1, latency_ms=1.0)
