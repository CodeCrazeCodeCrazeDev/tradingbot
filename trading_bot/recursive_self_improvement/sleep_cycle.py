"""Sleep-phase orchestration for the Level-1 RSI engine.

Adapted from the "Sleep" paradigm for continual learning
(arXiv:2606.03979): adaptation runs as an offline, quiescent phase rather
than interleaved with live decision-making. The phase has two stages,
mirroring the paper's NREM/REM split:

1. **Memory consolidation** — fragile episodic experiment state
   (:class:`~.memory.ImprovementMemory` ``experiments`` rows and raw
   archive records) is distilled into durable ``lessons``, then the
   fragile layer is pruned ("synaptic pruning"). The append-only
   ``evidence_ledger`` is never touched; its hash chain is re-verified
   after consolidation.

2. **Dreaming** — synthetic regime-shifted scenarios are generated
   ("dreams"), ranked by *discriminative power* (the gradient-based data
   selection analog: a scenario where no bounded parameter choice changes
   the outcome carries no learning signal), and archived specialist
   parameter blocks are recombined across regimes ("random expert
   activation") and rehearsed on the kept dreams.

Dream evidence is **diagnostic only**: it is written to the evidence
ledger under ``status="dream_diagnostic"`` with ``promotion_eligible``
explicitly false, and it never reaches the multi-objective gate. Only
the ordinary gated cycle — sandboxed paired replay, independent verifier,
transfer classification — can mark a candidate eligible, and deployment
stages still require signed ``OperatorAuthorization``.

The wake/sleep boundary is fail-closed: if an ``is_active_fn`` probe
reports the trading runtime awake and no ``pause_fn`` is wired,
:meth:`SleepPhaseRunner.run_sleep` refuses to run.
"""

from __future__ import annotations

import json
import logging
import math
import random
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from trading_bot.evaluation.runner import PairedFamilyReplay
from trading_bot.evaluation.synthetic_market import (
    RegimeSpec, SyntheticMarketGenerator, SyntheticMarketSpec, fingerprint_all)

from .archive import ParetoArchive
from .candidate_adapters import AdapterSpec
from .engine_v2 import Hypothesis, RecursiveImprovementCycle
from .memory import ImprovementMemory
from .transfer import Scenario

logger = logging.getLogger(__name__)

DREAM_STATUS = "dream_diagnostic"

# Dream panels rehearse at observed cost; cost *stress* belongs to the
# real transfer panel, not to synthetic rehearsal.
_DREAM_REGIMES = ("trend", "mean_revert", "high_vol", "crash", "flat")


class SleepQuiesceError(RuntimeError):
    """Raised when the sleep phase cannot establish a quiescent runtime."""


# ---------------------------------------------------------------------------
# Dreaming: synthetic scenario generation + discriminative-power filtering
# ---------------------------------------------------------------------------

def _paired_delta(adapter: AdapterSpec, frames: Mapping[str, Any],
                  baseline_params: Mapping[str, Any],
                  candidate_params: Mapping[str, Any],
                  *, cost_bps: float, fraction: float) -> float:
    """Mean per-bar (candidate - baseline) net delta on the given frames."""
    runner = PairedFamilyReplay(adapter, cost_bps=float(cost_bps),
                                fraction=fraction)
    out = runner.run(dict(frames), baseline_params=dict(baseline_params),
                     candidate_params=dict(candidate_params))
    bars = out["bars"]
    if not bars:
        return 0.0
    return sum(b["candidate_net"] - b["baseline_net"] for b in bars) / len(bars)


class DreamScenarioFactory:
    """Generates regime-diverse synthetic ``Scenario`` objects (dreams).

    Deterministic given ``seed_base``: the same factory state always
    produces the same dream panel, so rehearsal evidence is replayable.
    """

    def __init__(self, instruments: Sequence[str], seed_base: int = 90000) -> None:
        if not instruments:
            raise ValueError("dream factory needs at least one instrument")
        self.instruments = tuple(sorted(instruments))
        self.seed_base = int(seed_base)

    @staticmethod
    def _regime(name: str, rng: random.Random, n_bars: int) -> RegimeSpec:
        if name == "trend":
            drift = rng.choice((-1.0, 1.0)) * rng.uniform(0.0005, 0.002)
            return RegimeSpec(name, n_bars, drift=drift,
                              vol=rng.uniform(0.0005, 0.002))
        if name == "mean_revert":
            return RegimeSpec(name, n_bars,
                              vol=rng.uniform(0.0002, 0.001),
                              ar1=-rng.uniform(0.05, 0.4),
                              sine_amp=rng.uniform(0.002, 0.02),
                              sine_period=rng.randint(6, 18))
        if name == "high_vol":
            return RegimeSpec(name, n_bars, vol=rng.uniform(0.003, 0.01))
        if name == "crash":
            return RegimeSpec(name, n_bars,
                              drift=-rng.uniform(0.002, 0.008),
                              vol=rng.uniform(0.003, 0.008))
        return RegimeSpec("flat", n_bars, vol=rng.uniform(0.00005, 0.0003))

    def generate(self, count: int, n_bars: int) -> List[Scenario]:
        scenarios: List[Scenario] = []
        for i in range(count):
            regime = _DREAM_REGIMES[i % len(_DREAM_REGIMES)]
            seed = self.seed_base + i
            rng = random.Random(seed)
            spec = SyntheticMarketSpec(
                seed=seed, instruments=self.instruments,
                regimes=(self._regime(regime, rng, n_bars),))
            frames = SyntheticMarketGenerator(spec).generate()
            scenarios.append(Scenario(
                label=f"dream-{regime}-{seed}", regime=regime,
                cost_multiplier=1.0, seed=seed, frames=frames))
        return scenarios


def probe_parameter_sets(adapter: AdapterSpec,
                         incumbent_params: Mapping[str, Any],
                         max_probes: int = 6) -> List[Dict[str, Any]]:
    """Bounded single-parameter probes used to measure discriminative power.

    Probes stay inside the adapter's allow-list and validator — dream
    rehearsal explores the same parameter space the gated cycle may touch.
    """
    probes: List[Dict[str, Any]] = []
    for name, (lo, hi) in adapter.allowed.items():
        incumbent = float(incumbent_params.get(name, (lo + hi) / 2))
        for raw in (incumbent * 0.5, incumbent * 1.5, math.sqrt(lo * hi)):
            v = max(lo, min(hi, raw))
            if isinstance(lo, int) and isinstance(hi, int):
                v = float(int(v))
            if v == incumbent:
                continue
            cand = {**dict(incumbent_params), name: v}
            if adapter.validate is not None and not adapter.validate(cand):
                continue
            if cand not in probes:
                probes.append(cand)
            if len(probes) >= max_probes:
                return probes
    return probes


@dataclass(frozen=True)
class DreamScore:
    """How much learning signal one dream scenario carries."""

    label: str
    regime: str
    seed: int
    frames_hash: str
    power: float                       # max |delta_net| across probes
    best_probe: Mapping[str, Any]      # probe params with max |delta|
    probe_deltas: Tuple[Mapping[str, Any], ...]


class DreamFilter:
    """Ranks dream scenarios by discriminative power.

    Analog of the paper's gradient-based data selection: a scenario where
    every bounded parameter choice produces the same outcome teaches
    nothing, so it is filtered out before rehearsal compute is spent on
    recombination. Ranking is by the largest |delta_net| any probe
    parameter set achieves against the incumbent.
    """

    def __init__(self, adapter: AdapterSpec, *, cost_bps: float,
                 fraction: float = 0.01) -> None:
        self.adapter = adapter
        self.cost_bps = float(cost_bps)
        self.fraction = float(fraction)

    def score(self, scenario: Scenario,
              baseline_params: Mapping[str, Any],
              probes: Sequence[Mapping[str, Any]]) -> DreamScore:
        deltas: List[Mapping[str, Any]] = []
        for probe in probes:
            try:
                d = _paired_delta(self.adapter, scenario.frames,
                                  baseline_params, probe,
                                  cost_bps=self.cost_bps,
                                  fraction=self.fraction)
            except Exception:  # noqa: BLE001 - a broken probe is a zero-signal probe
                logger.debug("dream probe failed on %s", scenario.label,
                             exc_info=True)
                d = 0.0
            deltas.append({"params": dict(probe), "delta_net": d})
        best = max(deltas, key=lambda r: abs(r["delta_net"]), default=None)
        return DreamScore(
            label=scenario.label, regime=scenario.regime, seed=scenario.seed,
            frames_hash=fingerprint_all(scenario.frames),
            power=abs(best["delta_net"]) if best else 0.0,
            best_probe=best["params"] if best else {},
            probe_deltas=tuple(deltas))

    def rank(self, scenarios: Sequence[Scenario],
             baseline_params: Mapping[str, Any],
             probes: Sequence[Mapping[str, Any]],
             *, keep_fraction: float = 0.5,
             min_power: float = 0.0) -> Tuple[List[DreamScore], List[DreamScore]]:
        """Return (kept, all_scores) sorted by descending power."""
        scored = sorted(
            (self.score(s, baseline_params, probes) for s in scenarios),
            key=lambda s: -s.power)
        keep_n = max(1, math.ceil(len(scored) * keep_fraction)) if scored else 0
        kept = [s for s in scored[:keep_n] if s.power > min_power]
        return kept, scored


# ---------------------------------------------------------------------------
# Dreaming: cross-regime specialist recombination ("random expert activation")
# ---------------------------------------------------------------------------

class SpecialistRecombiner:
    """Recombines parameter blocks from archived specialists.

    The archive's live members (champion, challengers, specialists,
    stepping stones) are the analog of the paper's experts: each is a
    parameter set tuned under some evidence context. Recombination mixes
    parameter values across members — including members tuned in
    different regime cells — to expose hybrids neither member was
    selected on. Hybrids are evaluated on dream scenarios only; they are
    diagnostic and carry no promotion authority (they may also change
    more than one parameter, which is permitted *here* precisely because
    no gated candidate path is involved).
    """

    def __init__(self, adapter: AdapterSpec) -> None:
        self.adapter = adapter

    def hybrids(self, archive: ParetoArchive,
                incumbent_params: Mapping[str, Any], count: int,
                rng: random.Random) -> List[Dict[str, Any]]:
        pools = [dict(incumbent_params)]
        pools.extend(
            dict(r["extra"]["candidate_parameters"])
            for r in archive.live_members()
            if (r.get("extra") or {}).get("candidate_parameters"))
        if len(pools) < 2:
            return []
        incumbent = dict(incumbent_params)
        hybrids: List[Dict[str, Any]] = []
        attempts = 0
        while len(hybrids) < count and attempts < max(8 * count, 8):
            attempts += 1
            a, b = rng.sample(pools, 2)
            hybrid: Dict[str, Any] = {}
            for name in self.adapter.allowed:
                pick = rng.choice((a.get(name), b.get(name)))
                hybrid[name] = (incumbent[name] if pick is None else pick)
            if hybrid == incumbent or hybrid in hybrids:
                continue
            if self.adapter.validate is not None and not self.adapter.validate(hybrid):
                continue
            hybrids.append(hybrid)
        return hybrids

    def evaluate(self, hybrid: Mapping[str, Any],
                 scenarios: Sequence[Scenario],
                 baseline_params: Mapping[str, Any], *,
                 cost_bps: float, fraction: float) -> Dict[str, Any]:
        per = []
        for s in scenarios:
            try:
                d = _paired_delta(self.adapter, s.frames, baseline_params,
                                  hybrid, cost_bps=cost_bps,
                                  fraction=fraction)
            except Exception:  # noqa: BLE001 - diagnostic rehearsal
                logger.debug("hybrid rehearsal failed on %s", s.label,
                             exc_info=True)
                d = 0.0
            per.append({"label": s.label, "regime": s.regime, "delta_net": d})
        mean = sum(p["delta_net"] for p in per) / len(per) if per else 0.0
        return {"params": dict(hybrid), "mean_delta_net": mean,
                "scenarios": per}


# ---------------------------------------------------------------------------
# Memory consolidation + synaptic pruning
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConsolidationReport:
    lessons_written: int
    already_distilled: int
    experiments_pruned: int
    evidence_chain_ok: bool


class SleepConsolidator:
    """Distills archive verdicts into durable lessons; prunes the buffer.

    Promotion into long-term memory is a *distillation*, not a copy:
    each archive record contributes one compact lesson (hypothesis,
    verdict, role, metric vector, transfer class) keyed by ``genome_id``
    so consolidation is idempotent. The fragile ``experiments`` table is
    then pruned to a retention bound; the hash-chained ``evidence_ledger``
    is never modified (database triggers forbid it anyway).
    """

    def __init__(self, memory: ImprovementMemory, archive: ParetoArchive) -> None:
        self.memory = memory
        self.archive = archive

    def consolidate(self, *, max_experiment_rows: int = 500,
                    domain: str = "trading_policy") -> ConsolidationReport:
        distilled = self.memory.lesson_source_ids()
        written = 0
        skipped = 0
        for rec in self.archive.records:
            if rec.get("kind") != "record":
                continue
            gid = rec["genome_id"]
            if gid in distilled:
                skipped += 1
                continue
            extra = rec.get("extra") or {}
            content = json.dumps({
                "hypothesis": extra.get("hypothesis", ""),
                "verdict": rec.get("verdict"),
                "role": rec.get("role"),
                "regime_cell": rec.get("regime_cell"),
                "metric_vector": dict(rec.get("metric_vector") or {}),
                "delta": dict(rec.get("delta") or {}),
                "transfer_class": extra.get("transfer_class"),
                "candidate_parameters": extra.get("candidate_parameters"),
            }, sort_keys=True, default=str)
            metrics = rec.get("metric_vector") or {}
            impact = float(metrics.get("net_return")
                           or (rec.get("delta") or {}).get("paired_mean_diff")
                           or 0.0)
            self.memory.add_lesson(
                domain=domain,
                topic=f"{rec.get('strategy_family', '?')}:{rec.get('verdict', '?')}",
                content=content, source_id=gid, impact=impact)
            written += 1
        pruned = self.memory.prune_experiments(max_experiment_rows)
        return ConsolidationReport(
            lessons_written=written, already_distilled=skipped,
            experiments_pruned=pruned,
            evidence_chain_ok=self.memory.verify_evidence_chain())


# ---------------------------------------------------------------------------
# Diversity-aware candidate selection ("better-conditioned search")
# ---------------------------------------------------------------------------

def dream_param_signal(scores: Sequence[DreamScore],
                       incumbent_params: Mapping[str, Any],
                       signal_gain: float = 1.0) -> Dict[str, float]:
    """Per-parameter steering weights from kept dream scores.

    Each dream's best probe varies exactly one parameter; that parameter
    gets credited with the dream's discriminative power (max wins across
    dreams). Weights normalize to ``1 + signal_gain * power/max_power``
    so a parameter with strong dream evidence re-ranks up to 2x —
    steering only: parameters with no dream signal keep weight 1.0 and
    are never demoted below the prioritizer's own ordering for their
    bucket. The signal cannot create hypotheses, widen the candidate
    budget, or touch the gate — it only reorders which of the cycle's
    already-admissible hypotheses get tried first.
    """
    raw: Dict[str, float] = {}
    for s in scores:
        for name, v in s.best_probe.items():
            if incumbent_params.get(name) != v:
                raw[name] = max(raw.get(name, 0.0), s.power)
    peak = max(raw.values()) if raw else 0.0
    if peak <= 0:
        return {}
    return {k: 1.0 + signal_gain * (v / peak) for k, v in raw.items()}


def steered_diverse_selector(
    param_weights: Mapping[str, float],
) -> Callable[[Sequence[Hypothesis], int], List[Hypothesis]]:
    """Selector: re-rank by dream-weighted expected value, then diversify.

    Mirrors ``ExperimentPrioritizer``'s expected-value-of-information
    proxy (gain / cost), scaled by the dream per-parameter weight, then
    hands the re-ranked pool to ``select_diverse_hypotheses`` so the
    per-cycle budget still spans distinct parameters.
    """
    def _select(hyps: Sequence[Hypothesis], k: int) -> List[Hypothesis]:
        reranked = sorted(
            hyps,
            key=lambda h: -(h.expected_gain
                            * param_weights.get(h.param, 1.0)
                            / max(h.est_cost, 1.0)))
        return select_diverse_hypotheses(reranked, k)
    return _select


def select_diverse_hypotheses(hypotheses: Sequence[Hypothesis],
                              k: int) -> List[Hypothesis]:
    """Round-robin across parameter buckets, preserving rank order.

    The per-cycle candidate budget should be spent on decorrelated
    hypotheses: three perturbations of one parameter explore a single
    direction, while hypotheses spanning distinct parameters (and thus
    distinct strategy mechanics) better condition the search — the paper's
    "fewer dominated directions" point applied to a k-per-cycle budget.
    """
    buckets: Dict[str, List[Hypothesis]] = {}
    for hyp in hypotheses:
        buckets.setdefault(hyp.param, []).append(hyp)
    out: List[Hypothesis] = []
    while len(out) < k and any(buckets.values()):
        for param in list(buckets):
            if len(out) >= k:
                break
            if buckets[param]:
                out.append(buckets[param].pop(0))
    return out


# ---------------------------------------------------------------------------
# Wake/sleep boundary
# ---------------------------------------------------------------------------

@dataclass
class ChannelSleepController:
    """Pause/resume wiring via the operator ``ControlChannel``.

    ``is_active`` fails safe: if the runner's state db exists and does not
    show ``control:paused``/``control:emergency`` set, the runtime is
    treated as awake (trading allowed) and the sleep phase must pause it
    first. A missing db means no runner state — quiescent by definition.
    """

    state_dir: Path
    poll_s: float = 0.5

    def _flag(self, key: str) -> Optional[str]:
        db = Path(self.state_dir) / "trading_state.db"
        if not db.exists():
            return None
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                row = con.execute(
                    "SELECT value FROM account_state WHERE key=?",
                    (key,)).fetchone()
                return row[0] if row else None
            finally:
                con.close()
        except sqlite3.Error:
            return None

    def is_active(self) -> bool:
        if not (Path(self.state_dir) / "trading_state.db").exists():
            return False
        return (self._flag("control:paused") != "1"
                and self._flag("control:emergency") != "1")

    def pause(self) -> None:
        from trading_bot.interfaces.control import ControlChannel
        ControlChannel(Path(self.state_dir) / "control").send(
            "pause", user="rsi-sleep", reason="sleep-phase consolidation window")

    def resume(self) -> None:
        from trading_bot.interfaces.control import ControlChannel
        ControlChannel(Path(self.state_dir) / "control").send(
            "resume", user="rsi-sleep", reason="sleep-phase complete")


def channel_sleep_controller(state_dir: Any) -> ChannelSleepController:
    """Build wake/sleep callables for ``SleepPhaseRunner`` from a state dir."""
    return ChannelSleepController(Path(state_dir))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SleepPhaseConfig:
    n_dream_scenarios: int = 6
    dream_bars: int = 160
    dream_keep_fraction: float = 0.5
    min_discriminative_power: float = 0.0
    dream_signal_gain: float = 1.0
    recombination_count: int = 4
    run_gated_cycle: bool = True
    consolidate: bool = True
    max_experiment_rows: int = 500
    dream_seed_base: int = 90000
    quiesce_timeout_s: float = 60.0


@dataclass
class SleepReport:
    paused_here: bool = False
    consolidation: Optional[ConsolidationReport] = None
    dreams_generated: int = 0
    dreams_kept: int = 0
    top_dreams: List[DreamScore] = field(default_factory=list)
    recombinations: List[Mapping[str, Any]] = field(default_factory=list)
    param_weights: Dict[str, float] = field(default_factory=dict)
    decisions: List[Any] = field(default_factory=list)
    ledger_ok: bool = False
    notes: List[str] = field(default_factory=list)


class SleepPhaseRunner:
    """Runs one sleep phase over an assembled ``RecursiveImprovementCycle``.

    Ordering follows the paper's sleep structure:

    1. quiesce (fail-closed),
    2. consolidation of the previous wake's records into durable lessons
       + pruning of the fragile experiment buffer,
    3. dreaming (synthetic scenario rehearsal + specialist recombination,
       diagnostic only),
    4. optionally, one gated improvement cycle with diversity-aware
       candidate selection — the only path that can produce
       ``eligible_for_operator_review`` verdicts, and never a deployment.

    ``resume_fn`` runs in ``finally`` so a failed sleep does not leave a
    paused runtime paused silently.
    """

    def __init__(
        self,
        *,
        cycle: RecursiveImprovementCycle,
        pause_fn: Optional[Callable[[], Any]] = None,
        resume_fn: Optional[Callable[[], Any]] = None,
        is_active_fn: Optional[Callable[[], bool]] = None,
        config: Optional[SleepPhaseConfig] = None,
    ) -> None:
        self.cycle = cycle
        self._pause = pause_fn
        self._resume = resume_fn
        self._is_active = is_active_fn
        self.config = config or SleepPhaseConfig()

    # -- quiescence ----------------------------------------------------------
    def _enter_sleep(self) -> bool:
        """Returns True if this call paused the runtime itself."""
        if self._is_active is None:
            # Standalone use: the caller asserts quiescence (e.g. offline
            # benchmark runs against an already-stopped runner).
            return False
        if not self._is_active():
            return False
        if self._pause is None:
            raise SleepQuiesceError(
                "trading runtime is awake and no pause control is wired; "
                "refusing to enter the sleep phase")
        self._pause()
        deadline = time.monotonic() + self.config.quiesce_timeout_s
        while time.monotonic() < deadline:
            if not self._is_active():
                return True
            time.sleep(0.5)
        raise SleepQuiesceError(
            "pause command sent but the runtime did not quiesce within "
            f"{self.config.quiesce_timeout_s:.0f}s")

    # -- dream evidence --------------------------------------------------------
    def _record_dream_evidence(self, report: SleepReport) -> None:
        payload = {
            "diagnostic": True,
            "promotion_eligible": False,
            "dreams": [
                {"label": s.label, "regime": s.regime, "seed": s.seed,
                 "frames_hash": s.frames_hash, "power": s.power,
                 "best_probe": dict(s.best_probe),
                 "probe_deltas": [dict(d) for d in s.probe_deltas]}
                for s in report.top_dreams
            ],
            "recombinations": report.recombinations,
            "param_weights": dict(report.param_weights),
            "dreams_generated": report.dreams_generated,
            "dreams_kept": report.dreams_kept,
        }
        try:
            self.cycle.memory.append_evidence(
                trial_id=f"DREAM-{uuid.uuid4().hex[:8]}",
                nonce=uuid.uuid4().hex, payload=payload, status=DREAM_STATUS)
        except Exception:  # noqa: BLE001 - evidence write must not kill the phase
            logger.exception("dream evidence append failed")
            report.notes.append("dream evidence write failed")

    # -- one full sleep --------------------------------------------------------
    def run_sleep(
        self, gaps: Optional[Sequence[Any]] = None
    ) -> SleepReport:
        report = SleepReport()
        cfg = self.config
        paused = False
        try:
            paused = self._enter_sleep()
            report.paused_here = paused

            if cfg.consolidate:
                report.consolidation = SleepConsolidator(
                    self.cycle.memory, self.cycle.archive).consolidate(
                        max_experiment_rows=cfg.max_experiment_rows)

            instruments = tuple(sorted(self.cycle.frames)) or ("EURUSD",)
            scenarios = DreamScenarioFactory(
                instruments, seed_base=cfg.dream_seed_base).generate(
                    cfg.n_dream_scenarios, cfg.dream_bars)
            report.dreams_generated = len(scenarios)

            probes = probe_parameter_sets(
                self.cycle.adapter, self.cycle.incumbent_params)
            cost = max(float(self.cycle.contract.get("min_cost_bps") or 1.0), 1.0)
            filt = DreamFilter(self.cycle.adapter, cost_bps=cost,
                               fraction=self.cycle.config.fraction)
            kept, _ = filt.rank(
                scenarios, self.cycle.incumbent_params, probes,
                keep_fraction=cfg.dream_keep_fraction,
                min_power=cfg.min_discriminative_power)
            report.top_dreams = kept
            report.dreams_kept = len(kept)
            if not probes:
                report.notes.append(
                    "no bounded probes available; dreams unranked by power")

            by_label = {s.label: s for s in scenarios}
            kept_scenarios = [by_label[s.label] for s in kept] or scenarios
            rng = random.Random(cfg.dream_seed_base ^ 0x5EED)
            recomb = SpecialistRecombiner(self.cycle.adapter)
            hybrid_sets = recomb.hybrids(
                self.cycle.archive, self.cycle.incumbent_params,
                cfg.recombination_count, rng)
            if not hybrid_sets:
                report.notes.append(
                    "archive holds no recombinable members; recombination skipped")
            report.recombinations = [
                recomb.evaluate(h, kept_scenarios, self.cycle.incumbent_params,
                                cost_bps=cost, fraction=self.cycle.config.fraction)
                for h in hybrid_sets]
            report.param_weights = dream_param_signal(
                kept, self.cycle.incumbent_params,
                signal_gain=cfg.dream_signal_gain)
            self._record_dream_evidence(report)

            if cfg.run_gated_cycle:
                selector = (steered_diverse_selector(report.param_weights)
                            if report.param_weights
                            else select_diverse_hypotheses)
                report.decisions = self.cycle.run_cycle(
                    gaps=gaps, selector=selector)

            report.ledger_ok = self.cycle.memory.verify_evidence_chain()
        finally:
            if paused and self._resume is not None:
                try:
                    self._resume()
                except Exception:  # noqa: BLE001 - surface, don't mask sleep result
                    logger.exception("resume after sleep phase failed")
                    report.notes.append("resume command failed — runtime may still be paused")
        return report
