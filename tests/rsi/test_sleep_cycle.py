"""Sleep-phase tests: consolidation, dreaming, diversity, quiesce gate.

Covers the transferable principles from arXiv:2606.03979 as implemented
in ``recursive_self_improvement.sleep_cycle``: offline-only adaptation,
dream evidence marked strictly diagnostic, fragile-buffer pruning that
never touches the evidence ledger, and fail-closed quiescence.
"""

from __future__ import annotations

import sqlite3

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from trading_bot.recursive_self_improvement.archive import ParetoArchive
from trading_bot.recursive_self_improvement.candidate_adapters import ADAPTERS
from trading_bot.recursive_self_improvement.engine_v2 import (
    CycleConfig, Hypothesis, IndependentVerifier, RecursiveImprovementCycle)
from trading_bot.recursive_self_improvement.improvement_genome import (
    ImprovementDomain)
from trading_bot.recursive_self_improvement.memory import ImprovementMemory
from trading_bot.recursive_self_improvement.protected_control_plane import (
    ProtectedPathGuard)
from trading_bot.recursive_self_improvement.sleep_cycle import (
    DREAM_STATUS, DreamScore, DreamScenarioFactory, SleepConsolidator,
    SleepPhaseConfig, SleepPhaseRunner, SleepQuiesceError,
    SpecialistRecombiner, DreamFilter, channel_sleep_controller,
    dream_param_signal, probe_parameter_sets, select_diverse_hypotheses,
    steered_diverse_selector)

from tests.rsi.helpers import make_contract, make_frames


@pytest.fixture()
def frames():
    return make_frames()


@pytest.fixture()
def stack(tmp_path, frames):
    contract = make_contract(frames)
    key_file = tmp_path / "verifier.pem"
    IndependentVerifier(
        private_key=Ed25519PrivateKey.generate()).export_private_key(str(key_file))
    verifier = IndependentVerifier(key_path=str(key_file))
    archive = ParetoArchive(tmp_path / "archive.jsonl")
    memory = ImprovementMemory(str(tmp_path / "mem.db"))
    cycle = RecursiveImprovementCycle(
        contract=contract, verifier=verifier, archive=archive, memory=memory,
        guard=ProtectedPathGuard(), frames=frames,
        incumbent_params={"lookback": 100, "entry_threshold": 1.0},
        adapter=ADAPTERS["mean_reversion"],
        # thread backend: dream/cycle machinery test, not a hostile-code test
        config=CycleConfig(run_transfer=False, max_candidates_per_cycle=4,
                           sandbox_backend="thread"))
    return {"contract": contract, "verifier": verifier, "archive": archive,
            "memory": memory, "cycle": cycle}


def _hyp(param, value):
    return Hypothesis(f"H-{param}-{value}", "t", "p", "a", "f",
                      ImprovementDomain.TRADING_POLICY, param, value, 1.0, 1.0)


# -- dreaming -----------------------------------------------------------------
def test_dream_factory_deterministic_and_regime_diverse():
    factory = DreamScenarioFactory(("EURUSD", "GBPUSD"), seed_base=42)
    a = factory.generate(6, 120)
    b = factory.generate(6, 120)
    assert [s.label for s in a] == [s.label for s in b]
    from trading_bot.evaluation.synthetic_market import fingerprint_all
    assert [fingerprint_all(s.frames) for s in a] == \
           [fingerprint_all(s.frames) for s in b]
    regimes = {s.regime for s in a}
    assert len(regimes) >= 3, "dream panel should span regimes"
    assert all(s.cost_multiplier == 1.0 for s in a)


def test_dream_filter_prefers_discriminating_scenarios(stack):
    adapter = ADAPTERS["mean_reversion"]
    incumbent = {"lookback": 100, "entry_threshold": 1.0}
    probes = probe_parameter_sets(adapter, incumbent)
    assert probes
    filt = DreamFilter(adapter, cost_bps=1.0, fraction=0.01)

    # Planted oscillation: lookback probes produce different PnL paths.
    rich = DreamScenarioFactory(("EURUSD", "GBPUSD"), seed_base=1).generate(1, 120)[0]
    from trading_bot.evaluation.synthetic_market import (
        RegimeSpec, SyntheticMarketGenerator, SyntheticMarketSpec)
    flat = SyntheticMarketGenerator(SyntheticMarketSpec(
        seed=2, instruments=("EURUSD", "GBPUSD"),
        regimes=(RegimeSpec("flat", 120, vol=1e-6),))).generate()
    from trading_bot.recursive_self_improvement.transfer import Scenario
    flat_sc = Scenario("dream-flat-2", "flat", 1.0, 2, flat)

    kept, scored = filt.rank([flat_sc, rich], incumbent, probes,
                             keep_fraction=1.0)
    powers = {s.label: s.power for s in scored}
    assert powers[rich.label] > powers[flat_sc.label], (
        "a near-flat dream where parameters cannot matter should carry "
        "less signal than a structured one")


def test_probe_sets_stay_within_adapter_bounds(stack):
    adapter = ADAPTERS["mean_reversion"]
    probes = probe_parameter_sets(adapter, {"lookback": 100,
                                            "entry_threshold": 1.0})
    for p in probes:
        for name, v in p.items():
            lo, hi = adapter.allowed[name]
            assert lo <= v <= hi


def test_recombiner_mixes_archive_member_parameters(stack):
    archive = stack["archive"]
    for i, params in enumerate(({"lookback": 20, "entry_threshold": 3.0},
                                {"lookback": 150, "entry_threshold": 0.6})):
        archive.record_candidate(
            genome_id=f"g{i}", parent_id="root", contract_hash="c",
            dataset_hash="d", strategy_family="mean_reversion",
            metric_vector={"net_return": 0.001}, delta={}, verdict="x",
            role="specialist", extra={"candidate_parameters": params})
    import random
    rec = SpecialistRecombiner(ADAPTERS["mean_reversion"])
    hybrids = rec.hybrids(archive, {"lookback": 100, "entry_threshold": 1.0},
                          6, random.Random(0))
    assert hybrids, "two specialists + incumbent should recombine"
    allowed = set(ADAPTERS["mean_reversion"].allowed)
    for h in hybrids:
        assert set(h) == allowed
        assert h != {"lookback": 100, "entry_threshold": 1.0}
        assert h["lookback"] in {20, 100, 150}
        assert h["entry_threshold"] in {0.6, 1.0, 3.0}


def test_recombiner_empty_archive_yields_nothing(stack):
    import random
    rec = SpecialistRecombiner(ADAPTERS["mean_reversion"])
    assert rec.hybrids(stack["archive"], {"lookback": 100}, 4,
                       random.Random(0)) == []


# -- diversity-aware selection --------------------------------------------------
def test_select_diverse_spreads_parameter_buckets():
    ranked = [_hyp("lookback", 50), _hyp("lookback", 150),
              _hyp("lookback", 75), _hyp("entry_threshold", 2.0)]
    chosen = select_diverse_hypotheses(ranked, 2)
    assert len(chosen) == 2
    assert {h.param for h in chosen} == {"lookback", "entry_threshold"}, (
        "budget should span distinct parameters, not two perturbations of one")


def test_select_diverse_preserves_rank_within_bucket():
    ranked = [_hyp("a", 1), _hyp("a", 2), _hyp("b", 1)]
    chosen = select_diverse_hypotheses(ranked, 3)
    assert chosen[0].param == "a" and chosen[0].value == 1


# -- dream-informed steering ---------------------------------------------------
def _dream(param, param_val, power, incumbent={"lookback": 100,
                                              "entry_threshold": 1.0}):
    probe = dict(incumbent)
    probe[param] = param_val
    return DreamScore(label="d", regime="mean_revert", seed=1,
                      frames_hash="h", power=power, best_probe=probe,
                      probe_deltas=())


def test_dream_param_signal_credits_varied_param():
    incumbent = {"lookback": 100, "entry_threshold": 1.0}
    scores = [_dream("lookback", 20.0, 0.01, incumbent),
              _dream("entry_threshold", 2.0, 0.005, incumbent)]
    w = dream_param_signal(scores, incumbent)
    # lookback carried the max-power dream -> weight 2.0 at gain=1;
    # entry_threshold got half the peak power -> weight 1.5.
    assert w["lookback"] == pytest.approx(2.0)
    assert w["entry_threshold"] == pytest.approx(1.5)


def test_dream_param_signal_empty_on_zero_power():
    assert dream_param_signal([_dream("lookback", 20.0, 0.0)],
                             {"lookback": 100}) == {}
    assert dream_param_signal([], {"lookback": 100}) == {}


def test_steered_selector_reranks_by_dream_weight():
    # Two equally-ranked hypotheses on different params; dream weight on
    # 'b' should pull b's hypothesis ahead in the round-robin order.
    ranked = [_hyp("a", 1), _hyp("b", 1)]
    chosen = steered_diverse_selector({"b": 2.0})(ranked, 1)
    assert chosen[0].param == "b"
    # No dream signal -> falls back to prioritizer order.
    chosen = steered_diverse_selector({})(ranked, 1)
    assert chosen[0].param == "a"


def test_run_sleep_exposes_param_weights(stack):
    runner = SleepPhaseRunner(
        cycle=stack["cycle"],
        config=SleepPhaseConfig(n_dream_scenarios=4, dream_bars=120,
                                run_gated_cycle=True))
    report = runner.run_sleep()
    assert report.dreams_kept >= 1
    for name, w in report.param_weights.items():
        assert name in stack["cycle"].adapter.allowed
        assert 1.0 < w <= 2.0


# -- consolidation + synaptic pruning -------------------------------------------
def test_consolidator_distills_once_and_prunes(stack, tmp_path):
    archive, memory = stack["archive"], stack["memory"]
    archive.record_candidate(
        genome_id="g1", parent_id="root", contract_hash="c", dataset_hash="d",
        strategy_family="mean_reversion",
        metric_vector={"net_return": 0.002}, delta={},
        verdict="eligible_for_operator_review", role="challenger",
        extra={"hypothesis": "lookback helps", "transfer_class": "ROBUST"})
    for i in range(10):
        memory.record_experiment(f"exp-{i}", "trading_policy", "h", {"p": i})
    memory.append_evidence(trial_id="t-1", nonce="n-1",
                           payload={"x": 1}, status="ok")

    con = SleepConsolidator(memory, archive)
    r1 = con.consolidate(max_experiment_rows=3)
    assert r1.lessons_written == 1
    assert r1.experiments_pruned == 7
    assert r1.evidence_chain_ok

    # Idempotent: the same archive record is never distilled twice.
    r2 = con.consolidate(max_experiment_rows=3)
    assert r2.lessons_written == 0 and r2.already_distilled == 1

    # Evidence ledger untouched and still valid; experiments capped.
    assert memory.verify_evidence_chain()
    assert len(memory.get_recent_experiments(limit=100)) == 3

    # The ledger still forbids deletion at the database layer.
    with pytest.raises(sqlite3.IntegrityError):
        with sqlite3.connect(memory.db_path) as c:
            c.execute("DELETE FROM evidence_ledger")


# -- orchestrator ---------------------------------------------------------------
def test_run_sleep_end_to_end(stack):
    runner = SleepPhaseRunner(
        cycle=stack["cycle"],
        config=SleepPhaseConfig(n_dream_scenarios=4, dream_bars=120,
                                recombination_count=2))
    report = runner.run_sleep()
    assert report.dreams_generated == 4
    assert report.dreams_kept >= 1
    assert report.consolidation is not None
    assert report.ledger_ok
    assert all(d.status != "promoted" for d in report.decisions)

    # Dream evidence landed in the ledger as diagnostic — never promotable.
    con = sqlite3.connect(stack["memory"].db_path)
    rows = con.execute(
        "SELECT status, payload FROM evidence_ledger WHERE status=?",
        (DREAM_STATUS,)).fetchall()
    con.close()
    assert rows, "dream diagnostics must be audited"
    import json as _json
    payload = _json.loads(rows[0][1])
    assert payload["diagnostic"] is True
    assert payload["promotion_eligible"] is False


def test_sleep_refuses_when_awake_and_unpausable(stack):
    runner = SleepPhaseRunner(cycle=stack["cycle"],
                              is_active_fn=lambda: True)
    with pytest.raises(SleepQuiesceError):
        runner.run_sleep()


def test_sleep_pauses_and_resumes_awake_runtime(stack):
    state = {"awake": True, "resumed": False}
    runner = SleepPhaseRunner(
        cycle=stack["cycle"],
        is_active_fn=lambda: state["awake"],
        pause_fn=lambda: state.update(awake=False),
        resume_fn=lambda: state.update(resumed=True),
        config=SleepPhaseConfig(n_dream_scenarios=2, dream_bars=80,
                                run_gated_cycle=False))
    report = runner.run_sleep()
    assert report.paused_here
    assert state["resumed"], "resume must run after the sleep phase"


def test_sleep_cycle_records_only_gated_candidates(stack):
    """Archive records must come from the gated cycle, never from dreams."""
    runner = SleepPhaseRunner(
        cycle=stack["cycle"],
        config=SleepPhaseConfig(n_dream_scenarios=2, dream_bars=80,
                                run_gated_cycle=True))
    report = runner.run_sleep()
    records = [r for r in stack["archive"].records if r["kind"] == "record"]
    assert len(records) == len(report.decisions)
    for rec in records:
        assert rec["verdict"] in ("rejected", "insufficient_evidence",
                                  "eligible_for_operator_review")


def test_channel_controller_flags(tmp_path):
    ctl = channel_sleep_controller(tmp_path)
    assert ctl.is_active() is False  # no state db => quiescent
