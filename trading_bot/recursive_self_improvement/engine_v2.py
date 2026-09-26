"""Level-1 recursive self-improvement engine (mission sections 4-7, 10, 12-13).

Observe -> diagnose -> hypothesize (competing, falsifiable) -> prioritize ->
bounded candidate -> sandboxed paired replay -> independent verifier ->
multi-objective gate -> transfer classification -> archive with lineage ->
research champion relabel. Nothing here authorizes deployment; deployment
stages past ``eligible_for_operator_review`` need a signed
``OperatorAuthorization`` at the ``PromotionLadder``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_der_private_key,
    load_pem_private_key,
)

from trading_bot.evaluation.runner import PairedFamilyReplay

from .archive import ParetoArchive
from .candidate_adapters import AdapterSpec, get_adapter
from .contracts import canonical, contract_hash, validate_contract
from .improvement_genome import ImprovementDomain, ImprovementGenome, PromotionDecision
from .memory import ImprovementMemory
from .metric_registry import direction
from .multi_objective import MultiObjectiveEvaluator
from .protected_control_plane import ProtectedPathGuard, ProtectedPathViolation
from .transfer import Scenario, TransferEvaluator

logger = logging.getLogger(__name__)

RESEARCH_CHAMPION_NOTE = (
    "Research champion only: labels the current best archive member. "
    "No configuration, deployment or capital stage is authorized."
)


# ---------------------------------------------------------------------------
# Observation / diagnosis
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PerformanceGap:
    kind: str                     # cold_start | below_hurdle | tail_risk | cost_drag | inactivity
    metric: str
    regime: str
    severity: float
    evidence: Mapping[str, Any] = field(default_factory=dict)


class ObservationEngine:
    """Detects performance gaps from the archive and contract budgets."""

    def __init__(self, archive: ParetoArchive, contract: Mapping[str, Any]) -> None:
        self.archive = archive
        self.contract = contract

    def observe(self) -> List[PerformanceGap]:
        c = self.contract
        champion = self.archive.champion()
        if champion is None:
            return [PerformanceGap("cold_start", "net_return", "all", 1.0)]
        mv = champion["metric_vector"]
        gaps: List[PerformanceGap] = []
        if mv.get("net_return", 0.0) < c["economic_materiality_min"]:
            gaps.append(PerformanceGap("below_hurdle", "net_return", "all",
                                       1.0 - mv.get("net_return", 0.0)))
        cvar_cap = c["max_cvar_95"] or 1.0
        if mv.get("cvar_95", 0.0) > 0.8 * cvar_cap:
            gaps.append(PerformanceGap("tail_risk", "cvar_95", "all",
                                       mv["cvar_95"] / cvar_cap))
        if c["max_turnover"] and mv.get("turnover", 0.0) > 0.5 * c["max_turnover"]:
            gaps.append(PerformanceGap("cost_drag", "turnover", "all",
                                       mv["turnover"] / c["max_turnover"]))
        if mv.get("abstain_rate", 0.0) > 0.9:
            gaps.append(PerformanceGap("inactivity", "abstain_rate", "all",
                                       mv["abstain_rate"]))
        return gaps or [PerformanceGap("below_hurdle", "net_return", "all", 0.5)]


@dataclass(frozen=True)
class RootCause:
    label: str   # data | model | regime | execution | risk | evaluation | undetermined
    rationale: str


class RootCauseEngine:
    """Attributional rules only — honest 'undetermined' when nothing fits."""

    MAP = {
        "cost_drag": ("execution", "turnover drag is an execution/cost problem"),
        "tail_risk": ("risk", "tail exposure exceeds budget headroom"),
        "below_hurdle": ("regime", "incumbent lacks economic edge in panel regimes"),
        "inactivity": ("model", "signal too restrictive to produce trades"),
        "cold_start": ("evaluation", "no incumbent evaluated yet"),
    }

    def attribute(self, gap: PerformanceGap) -> RootCause:
        label, rationale = self.MAP.get(gap.kind, ("undetermined", "no rule matched"))
        return RootCause(label, rationale)


# ---------------------------------------------------------------------------
# Hypothesis generation / prioritization
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    text: str
    prediction: str
    adverse_prediction: str
    falsifier: str
    domain: ImprovementDomain
    param: str
    value: float
    expected_gain: float
    est_cost: float


class HypothesisEngine:
    """Generates competing falsifiable hypotheses for a gap.

    Rule tables produce >= 2 competing candidates per family where bounds
    allow; values already tried (present in the archive) are skipped so
    failed hypotheses visibly steer the search.
    """

    def __init__(self, adapter: AdapterSpec) -> None:
        self.adapter = adapter

    def _tried(self, archive: ParetoArchive) -> set:
        return {
            tuple(sorted(r["extra"].get("candidate_parameters", {}).items()))
            for r in archive.records
            if r.get("kind") == "record"
        }

    def _candidate_values(self, param: str, incumbent: float) -> List[float]:
        lo, hi = self.adapter.allowed[param]
        vals = [incumbent * 0.5, incumbent * 1.5, incumbent - 1.0,
                incumbent + 1.0, math.sqrt(lo * hi)]
        out: List[float] = []
        for v in vals:
            v = max(lo, min(hi, v))
            if v != incumbent:
                out.append(float(int(v)) if isinstance(lo, int) and isinstance(hi, int) else float(v))
        # dedupe preserving order
        seen = set()
        return [v for v in out if not (v in seen or seen.add(v))]

    def generate(self, gap: PerformanceGap, cause: RootCause,
                 incumbent_params: Mapping[str, float],
                 archive: ParetoArchive) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        tried = self._tried(archive)
        for param in self.adapter.allowed:
            incumbent = float(incumbent_params.get(param, sum(self.adapter.allowed[param]) / 2))
            for value in self._candidate_values(param, incumbent):
                params_key = tuple(sorted({**incumbent_params, param: value}.items()))
                if params_key in tried:
                    continue
                bigger = value > incumbent
                text = (f"{self.adapter.family}.{param} {incumbent}->{value} improves "
                        f"{gap.metric} in {gap.regime} regime")
                out.append(Hypothesis(
                    hypothesis_id=f"HYP-{uuid.uuid4().hex[:8]}",
                    text=text,
                    prediction=("net return rises while drawdown does not regress"
                                if gap.metric == "net_return" else
                                f"{gap.metric} improves without net-return regression"),
                    adverse_prediction=(f"turnover increases" if not bigger else
                                        f"abstain_rate or tail risk worsens"),
                    falsifier=(f"reject if paired net delta <= 0 or {gap.metric} "
                               f"worsens beyond regression budget"),
                    domain=ImprovementDomain.TRADING_POLICY,
                    param=param, value=value,
                    expected_gain=max(gap.severity, 0.05),
                    est_cost=200.0 * incumbent,
                ))
                if len(out) >= 4:
                    return out
        return out


class ExperimentPrioritizer:
    """Expected-value-of-information proxy (config formula, not hard-coded law)."""

    def __init__(self, plausibility_floor: float = 0.1) -> None:
        self.plausibility_floor = plausibility_floor

    def _family_priors(self, archive: ParetoArchive, family: str) -> float:
        records = [r for r in archive.records
                   if r.get("kind") == "record" and r["strategy_family"] == family]
        if not records:
            return self.plausibility_floor * 3
        wins = sum(1 for r in records if r["verdict"] == "eligible_for_operator_review")
        return max(self.plausibility_floor, wins / len(records))

    def rank(self, hypotheses: Sequence[Hypothesis],
             archive: ParetoArchive, family: str) -> List[Hypothesis]:
        prior = self._family_priors(archive, family)
        scored = sorted(
            hypotheses,
            key=lambda h: -(h.expected_gain * prior / max(h.est_cost, 1.0)),
        )
        return scored


class CandidateGenerator:
    def build(self, hypothesis: Hypothesis, contract: Mapping[str, Any],
              family: str) -> ImprovementGenome:
        return ImprovementGenome(
            domain=hypothesis.domain,
            objective=hypothesis.text,
            change_set={hypothesis.param: hypothesis.value},
            evaluation_plan={"contract_id": contract["contract_id"],
                             "strategy_family": family,
                             "falsifier": hypothesis.falsifier},
            safety_constraints={},
            parent_id=contract["baseline_hash"],
            metadata={"hypothesis": hypothesis.text,
                      "prediction": hypothesis.prediction,
                      "adverse_prediction": hypothesis.adverse_prediction},
        )


# ---------------------------------------------------------------------------
# Sandbox (thread deadline by default; "subprocess" backend gives real
# process isolation — the only isolation level suitable for hostile
# candidate code, since a wedged thread cannot be preempted)
# ---------------------------------------------------------------------------

@dataclass
class SandboxResult:
    status: str          # ok | interrupted | error | protected_violation
    result: Any = None
    error: str = ""


def _report_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keyless replay+report build; runs inside the sandbox boundary.

    ``adapter_family`` is a string because AdapterSpec carries lambdas and
    cannot cross the process boundary — the child re-resolves the same
    canonical adapter.
    """
    kwargs = dict(payload)
    kwargs["adapter"] = get_adapter(kwargs.pop("adapter_family"))
    return IndependentVerifier.replay_and_build_report(**kwargs)


def _report_worker_entry(queue: Any, payload: Dict[str, Any]) -> None:
    # Warm the replay path's lazy imports during startup so the wall-clock
    # budget only covers actual candidate work. The "ready" sentinel then
    # lets the parent start the work deadline after child startup (spawn +
    # module imports) instead of charging it to the budget.
    from trading_bot.evaluation import synthetic_market as _synthetic_market  # noqa: F401
    from trading_bot.strategies import institutional_strategies as _inst  # noqa: F401
    queue.put(("ready", None, 0.0))
    started = time.perf_counter()
    try:
        result = _report_worker(payload)
        work_ms = (time.perf_counter() - started) * 1000.0
        queue.put(("ok", result, work_ms))
    except Exception as exc:  # noqa: BLE001 - sandbox boundary
        queue.put(("error", repr(exc),
                   (time.perf_counter() - started) * 1000.0))


class SandboxManager:
    """Bounded-execution wrapper around candidate work.

    backend="thread": in-process daemon thread + wall-clock join (kept for
    lightweight callers; cannot preempt a wedged worker).
    backend="subprocess": spawned child process killed hard on deadline —
    the backend used by RecursiveImprovementCycle for real candidate work.
    """

    def __init__(self, guard: ProtectedPathGuard, wall_clock_s: float = 30.0,
                 backend: str = "thread") -> None:
        self.guard = guard
        self.wall_clock_s = wall_clock_s
        self.backend = backend

    def run(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> SandboxResult:
        before = self.guard.snapshot()
        box: Dict[str, Any] = {}

        def target() -> None:
            try:
                box["result"] = fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - sandbox boundary
                box["error"] = repr(exc)

        worker = threading.Thread(target=target, daemon=True)
        worker.start()
        worker.join(self.wall_clock_s)
        interrupted = worker.is_alive()
        try:
            self.guard.assert_unchanged(before)
        except ProtectedPathViolation as exc:
            return SandboxResult("protected_violation", error=str(exc))
        if interrupted:
            return SandboxResult("interrupted", error="wall-clock budget exceeded")
        if "error" in box:
            return SandboxResult("error", error=box["error"])
        return SandboxResult("ok", result=box.get("result"))

    def run_report(self, payload: Dict[str, Any]) -> SandboxResult:
        """Run a keyless verifier-replay payload under the configured backend."""
        if self.backend == "subprocess":
            return self._run_subprocess(payload)
        return self.run(_report_worker, payload)

    def _run_subprocess(self, payload: Dict[str, Any],
                        startup_grace_s: float = 180.0,
                        overhead_grace_s: float = 90.0) -> SandboxResult:
        import multiprocessing as mp
        import queue as queue_mod

        def _kill(proc: mp.Process) -> None:
            if not proc.is_alive():
                return
            proc.terminate()
            proc.join(5.0)
            if proc.is_alive():
                proc.kill()
                proc.join()

        before = self.guard.snapshot()
        ctx = mp.get_context("spawn")
        result_q: mp.Queue = ctx.Queue()
        proc = ctx.Process(target=_report_worker_entry,
                           args=(result_q, payload), daemon=True)
        proc.start()

        # Phase 1 — bounded startup: wait for the child's "ready" sentinel
        # (spawn + imports are not candidate work and must not consume the
        # wall-clock budget, but they are still hard-bounded).
        startup_deadline = time.monotonic() + max(startup_grace_s,
                                                  self.wall_clock_s)
        ready = False
        while proc.is_alive() and time.monotonic() < startup_deadline:
            try:
                msg = result_q.get(timeout=0.2)
            except queue_mod.Empty:
                continue
            except Exception:
                break
            if msg[0] == "ready":
                ready = True
                break
        if not ready:
            _kill(proc)
            try:
                self.guard.assert_unchanged(before)
            except ProtectedPathViolation as exc:
                return SandboxResult("protected_violation", error=str(exc))
            if not proc.is_alive() and proc.exitcode not in (0, None):
                return SandboxResult(
                    "error", error=f"worker exited with code {proc.exitcode} during startup")
            return SandboxResult(
                "interrupted", error="sandbox startup grace exceeded (process killed)")

        # Phase 2 — candidate work. Poll the result queue for the whole
        # deadline: a large report only flushes while the parent is
        # reading, so join-before-read deadlocks the child. The semantic
        # budget applies to the child's self-measured work time; the hard
        # deadline adds a bounded allowance for process mechanics.
        deadline = time.monotonic() + self.wall_clock_s + overhead_grace_s
        msg = None
        while time.monotonic() < deadline:
            try:
                msg = result_q.get(timeout=0.2)
                break
            except queue_mod.Empty:
                if not proc.is_alive():
                    break
        proc.join(timeout=5.0)
        if msg is None:
            try:
                msg = result_q.get(timeout=2.0)
            except queue_mod.Empty:
                msg = None
        if proc.is_alive():
            _kill(proc)
        try:
            self.guard.assert_unchanged(before)
        except ProtectedPathViolation as exc:
            return SandboxResult("protected_violation", error=str(exc))
        if msg is None:
            if proc.exitcode not in (0, None):
                return SandboxResult("error",
                                     error=f"worker exited with code {proc.exitcode}")
            return SandboxResult("interrupted",
                                 error="wall-clock budget exceeded (process killed)")
        status, value, work_ms = msg
        if work_ms > self.wall_clock_s * 1000.0:
            return SandboxResult(
                "interrupted",
                error=f"wall-clock budget exceeded: work took {work_ms:.0f}ms "
                      f"> {self.wall_clock_s * 1000.0:.0f}ms")
        if status == "ok":
            return SandboxResult("ok", result=value)
        return SandboxResult("error", error=value)


# ---------------------------------------------------------------------------
# Independent verifier (re-runs the replay itself; key custody is
# operator-provisioned in production — a generated in-process key is a
# development fallback only, not tamper-resistant custody)
# ---------------------------------------------------------------------------

class IndependentVerifier:
    """Independent recomputation + attestation of a paired replay.

    Key custody (TD-07): the signing key is injected directly, or loaded
    from ``key_path`` / the ``RSI_VERIFIER_KEY_FILE`` env var (PEM, DER, or
    raw 32-byte Ed25519 seed). When no key is provisioned a fresh ephemeral
    key is generated — acceptable for tests and local runs only.
    The sandboxed subprocess path never receives key material: the child
    runs :meth:`replay_and_build_report` and the parent signs.
    """

    KEY_ENV_VAR = "RSI_VERIFIER_KEY_FILE"

    def __init__(self, private_key: Optional[Ed25519PrivateKey] = None,
                 verifier_id: str = "rsi-independent-verifier",
                 key_path: Optional[str] = None) -> None:
        self.private_key = private_key or self._load_private_key(key_path) \
            or Ed25519PrivateKey.generate()
        self.verifier_id = verifier_id

    @staticmethod
    def _load_private_key(key_path: Optional[str]) -> Optional[Ed25519PrivateKey]:
        path = key_path or os.environ.get(IndependentVerifier.KEY_ENV_VAR)
        if not path:
            return None
        data = Path(path).read_bytes()
        if b"-----BEGIN" in data:
            key = load_pem_private_key(data, password=None)
        else:
            try:
                key = load_der_private_key(data, password=None)
            except ValueError:
                key = None
            if key is None and len(data) == 32:
                key = Ed25519PrivateKey.from_private_bytes(data)
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError(f"{path} does not contain an Ed25519 private key")
        return key

    def export_private_key(self, path: str) -> None:
        """Provision the local key to an operator-controlled file path."""
        Path(path).write_bytes(
            self.private_key.private_bytes(
                Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self.private_key.public_key()

    @staticmethod
    def replay_and_build_report(
        *,
        contract: Mapping[str, Any],
        adapter: AdapterSpec,
        frames: Mapping[str, Any],
        incumbent_params: Mapping[str, Any],
        candidate_params: Mapping[str, Any],
        genome: ImprovementGenome,
        trial_id: str,
        trial_count: int,
        latency_ms: float,
        verifier_id: str,
        fraction: float = 0.01,
    ) -> Dict[str, Any]:
        """Re-run the paired replay and build the unsigned report.

        Deliberately keyless so it can execute inside the sandboxed child
        process — attestation happens in the parent via ``sign()``.
        """
        from trading_bot.evaluation.synthetic_market import fingerprint_all

        actual_hash = fingerprint_all(frames)
        if actual_hash != contract["dataset_hash"]:
            raise ValueError(
                "evaluation frames do not match the contract's dataset_hash")
        runner = PairedFamilyReplay(adapter, cost_bps=float(contract["max_cost_bps"]),
                                    fraction=fraction)
        out = runner.run(dict(frames), baseline_params=dict(incumbent_params),
                         candidate_params=dict(candidate_params))
        bars = out["bars"]
        effect = any(b["baseline_gross"] != b["candidate_gross"] for b in bars)
        invariants = all(
            b["candidate_exposure"] <= contract["max_exposure"] + 1e-12
            and b["baseline_exposure"] <= contract["max_exposure"] + 1e-12
            for b in bars
        )
        from .candidate_adapters import candidate_code_hash, dependencies_hash

        return {
            "schema_version": 2,
            "contract_id": contract["contract_id"],
            "baseline_hash": contract["baseline_hash"],
            "dataset_hash": contract["dataset_hash"],
            "candidate_hash": genome.fingerprint,
            "trial_id": trial_id,
            "trial_count": trial_count,
            "latency_ms": float(latency_ms),
            "candidate_parameters": dict(genome.change_set),
            "holdout_attested": True,
            "verifier_id": verifier_id,
            "cost_model_id": contract["cost_model_id"],
            "code_hash": candidate_code_hash(),
            "dependencies_hash": dependencies_hash(),
            "risk_invariants_passed": invariants,
            "parameter_effect_verified": effect,
            "bars": bars,
        }

    def sign(self, report: Mapping[str, Any]) -> str:
        return self.private_key.sign(canonical(report)).hex()

    def evaluate(
        self,
        *,
        contract: Mapping[str, Any],
        adapter: AdapterSpec,
        frames: Mapping[str, Any],
        incumbent_params: Mapping[str, Any],
        candidate_params: Mapping[str, Any],
        genome: ImprovementGenome,
        trial_id: str,
        trial_count: int,
        latency_ms: float,
        fraction: float = 0.01,
    ) -> Tuple[Dict[str, Any], str]:
        report = self.replay_and_build_report(
            contract=contract, adapter=adapter, frames=frames,
            incumbent_params=incumbent_params,
            candidate_params=candidate_params, genome=genome,
            trial_id=trial_id, trial_count=trial_count,
            latency_ms=latency_ms, verifier_id=self.verifier_id,
            fraction=fraction)
        return report, self.sign(report)


class ExternalVerifierClient:
    """Operator-controlled verifier backend (TD-07 wire contract).

    Production custody requires the signing key to live outside the RSI
    process — an operator-hosted signing service or HSM reachable over an
    authenticated channel. This client defines the interface the engine
    expects (``evaluate()`` + ``verifier_id``); it deliberately raises
    until a real transport is configured, because silently falling back
    to a local key would defeat custody separation.
    """

    def __init__(self, endpoint: str,
                 verifier_id: str = "external-verifier",
                 timeout_s: float = 30.0) -> None:
        self.endpoint = endpoint
        self.verifier_id = verifier_id
        self.timeout_s = timeout_s

    def evaluate(self, **kwargs: Any) -> Tuple[Dict[str, Any], str]:
        raise NotImplementedError(
            "external verifier transport is not configured: provision the "
            "operator-controlled signing service before enabling this backend")


# ---------------------------------------------------------------------------
# Promotion ladder (deployment stages need signed operator authorization)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OperatorAuthorization:
    genome_id: str
    contract_hash: str
    stage: str
    issued_by: str
    expires_at: float

    def canonical(self) -> bytes:
        return json.dumps({
            "genome_id": self.genome_id, "contract_hash": self.contract_hash,
            "stage": self.stage, "issued_by": self.issued_by,
            "expires_at": self.expires_at,
        }, sort_keys=True, separators=(",", ":")).encode()


class AuthorizationError(PermissionError):
    pass


class PromotionLadder:
    STAGES = ("proposed", "evaluated", "eligible_for_operator_review",
              "operator_approved", "shadow", "paper", "canary",
              "production", "rolled_back")
    AUTH_REQUIRED = frozenset(
        {"operator_approved", "shadow", "paper", "canary", "production"})

    def __init__(self, operator_public_key: Ed25519PublicKey,
                 clock: Callable[[], float] = time.time) -> None:
        self._key = operator_public_key
        self._clock = clock
        self._states: Dict[str, str] = {}
        self._contract_for: Dict[str, str] = {}

    def state(self, genome_id: str) -> str:
        return self._states.get(genome_id, "proposed")

    def record_evaluation(self, genome_id: str, contract_h: str, verdict: str) -> str:
        allowed = {"rejected": "evaluated",
                   "insufficient_evidence": "evaluated",
                   "eligible_for_operator_review": "eligible_for_operator_review"}
        self._states[genome_id] = allowed.get(verdict, "evaluated")
        self._contract_for[genome_id] = contract_h
        return self._states[genome_id]

    def advance(self, genome_id: str, stage: str,
                authorization: Optional[OperatorAuthorization] = None,
                signature: str = "") -> str:
        if stage not in self.STAGES:
            raise ValueError(f"unknown stage {stage!r}")
        if stage in self.AUTH_REQUIRED:
            if authorization is None:
                raise AuthorizationError(f"stage {stage} requires signed operator authorization")
            if (authorization.genome_id != genome_id
                    or authorization.stage != stage
                    or authorization.contract_hash != self._contract_for.get(genome_id)):
                raise AuthorizationError("authorization does not match genome/contract/stage")
            if authorization.expires_at < self._clock():
                raise AuthorizationError("authorization expired")
            try:
                self._key.verify(bytes.fromhex(signature), authorization.canonical())
            except (InvalidSignature, ValueError, TypeError, AttributeError) as exc:
                raise AuthorizationError("invalid operator signature") from exc
        self._states[genome_id] = stage
        return stage

    def rollback(self, genome_id: str) -> str:
        self._states[genome_id] = "rolled_back"
        return "rolled_back"


# ---------------------------------------------------------------------------
# Cycle orchestration
# ---------------------------------------------------------------------------

@dataclass
class CycleConfig:
    max_candidates_per_cycle: int = 3
    wall_clock_s: float = 30.0
    fraction: float = 0.01
    rng_seed: int = 1234
    run_transfer: bool = True
    # "subprocess" = real process isolation for candidate work (default);
    # "thread" = in-process deadline only, for environments where spawn is
    # unavailable. Thread isolation is NOT sufficient for hostile code.
    sandbox_backend: str = "subprocess"


class RecursiveImprovementCycle:
    def __init__(
        self,
        *,
        contract: Mapping[str, Any],
        verifier: IndependentVerifier,
        archive: ParetoArchive,
        memory: ImprovementMemory,
        guard: ProtectedPathGuard,
        frames: Mapping[str, Any],
        incumbent_params: Mapping[str, Any],
        adapter: Optional[AdapterSpec] = None,
        panels: Sequence[Scenario] = (),
        config: Optional[CycleConfig] = None,
    ) -> None:
        self.contract = validate_contract(dict(contract))
        self.contract_hash = contract_hash(self.contract)
        self.verifier = verifier
        self.archive = archive
        self.memory = memory
        self.guard = guard
        self.frames = frames
        self.incumbent_params = dict(incumbent_params)
        self.adapter = adapter or get_adapter(self.contract["strategy_family"])
        self.panels = list(panels)
        self.config = config or CycleConfig()
        self.evaluator = MultiObjectiveEvaluator(self.contract)
        self.rng = random.Random(self.config.rng_seed)
        self._trial_counter = 0

    # -- one full cycle -------------------------------------------------------
    def run_cycle(self, gaps: Optional[Sequence[PerformanceGap]] = None) -> List[PromotionDecision]:
        decisions: List[PromotionDecision] = []
        obs = ObservationEngine(self.archive, self.contract)
        causes = RootCauseEngine()
        hypotheses = HypothesisEngine(self.adapter)
        prioritizer = ExperimentPrioritizer()
        generator = CandidateGenerator()
        sandbox = SandboxManager(self.guard, self.config.wall_clock_s,
                                 backend=self.config.sandbox_backend)
        transfer = (TransferEvaluator(self.contract, self.adapter, self.config.fraction)
                    if self.config.run_transfer and self.panels else None)

        gap_list = list(gaps) if gaps else obs.observe()
        for gap in gap_list:
            cause = causes.attribute(gap)
            hyps = prioritizer.rank(
                hypotheses.generate(gap, cause, self.incumbent_params, self.archive),
                self.archive, self.adapter.family)
            for hyp in hyps[: self.config.max_candidates_per_cycle]:
                self._trial_counter += 1
                trial_id = f"TRIAL-{self._trial_counter:05d}-{uuid.uuid4().hex[:6]}"
                decisions.append(self._run_trial(hyp, generator, sandbox,
                                                 transfer, trial_id))
        return decisions

    # -- one candidate experiment ---------------------------------------------
    def _run_trial(self, hyp: Hypothesis, generator: CandidateGenerator,
                   sandbox: SandboxManager,
                   transfer: Optional[TransferEvaluator],
                   trial_id: str) -> PromotionDecision:
        genome = generator.build(hyp, self.contract, self.adapter.family)
        from .meta_proposals import gate_meta

        meta_block = gate_meta(genome, self.contract)
        if meta_block is not None:
            return self._finish(genome, trial_id, "rejected", meta_block, {}, {})
        candidate_params = {**self.incumbent_params, **dict(genome.change_set)}
        ok, reason = self.adapter.check_params(dict(genome.change_set))
        if not ok:
            return self._finish(genome, trial_id, "rejected", reason, {}, {})

        started = time.perf_counter()

        if isinstance(self.verifier, IndependentVerifier):
            # Keyless replay inside the sandbox; the parent's key signs.
            payload = {
                "contract": self.contract,
                "adapter_family": self.adapter.family,
                "frames": self.frames,
                "incumbent_params": self.incumbent_params,
                "candidate_params": candidate_params,
                "genome": genome,
                "trial_id": trial_id,
                "trial_count": self._trial_counter,
                "latency_ms": (time.perf_counter() - started) * 1000.0,
                "verifier_id": self.verifier.verifier_id,
                "fraction": self.config.fraction,
            }
            outcome = sandbox.run_report(payload)
        else:
            def job() -> Tuple[Dict[str, Any], str]:
                latency = (time.perf_counter() - started) * 1000.0
                return self.verifier.evaluate(
                    contract=self.contract, adapter=self.adapter,
                    frames=self.frames, incumbent_params=self.incumbent_params,
                    candidate_params=candidate_params, genome=genome,
                    trial_id=trial_id, trial_count=self._trial_counter,
                    latency_ms=latency, fraction=self.config.fraction)

            outcome = sandbox.run(job)
        if outcome.status == "protected_violation":
            self._security_event(genome, outcome.error)
            return self._finish(genome, trial_id, "rejected",
                                f"protected control-plane violation: {outcome.error}", {}, {})
        if outcome.status != "ok":
            return self._finish(genome, trial_id, "insufficient_evidence",
                                f"sandbox {outcome.status}: {outcome.error}", {}, {})
        if isinstance(self.verifier, IndependentVerifier):
            report, signature = outcome.result, self.verifier.sign(outcome.result)
        else:
            report, signature = outcome.result
        verdict = self.evaluator.evaluate(
            genome, report, expected_contract_hash=self.contract_hash,
            holdout_queries_used=self._trial_counter)

        regime_deltas: Dict[str, float] = {}
        classification = "LOCAL"
        if verdict["status"] == "eligible_for_operator_review" and transfer is not None:
            classification, details = self._transfer_classification(
                transfer, candidate_params)
            regime_deltas = details.get("regime_delta_map", {})
            verdict = {**verdict, "transfer_class": classification,
                       "transfer_details": details}
            if classification == "LOCAL":
                verdict = {**verdict, "status": "rejected",
                           "reason": "no transferable gain beyond selection regime"}

        role = self._role_for(verdict, classification)
        # Some verdicts carry metrics=None explicitly (e.g. exposure-breach
        # rejection) — normalize to {} so the archive's dict() never sees None.
        metrics = verdict.get("metrics") or {}
        self.archive.record_candidate(
            genome_id=genome.genome_id, parent_id=genome.parent_id,
            contract_hash=self.contract_hash, dataset_hash=self.contract["dataset_hash"],
            strategy_family=self.adapter.family, metric_vector=metrics,
            delta=verdict.get("delta") or {}, verdict=verdict["status"], role=role,
            regime_cell="all", trial_index=self._trial_counter,
            extra={"candidate_parameters": candidate_params,
                   "fingerprint": genome.fingerprint,
                   "transfer_class": classification,
                   "hypothesis": hyp.text})
        if role == "champion":
            # Relabel any previous research champion as ancestor (append-only
            # role change). RESEARCH_CHAMPION_NOTE applies: this is not a
            # deployment promotion.
            for gid, r in self.archive.current_roles().items():
                if r == "champion" and gid != genome.genome_id:
                    self.archive.record_role(gid, "ancestor",
                                             "superseded by new research champion")
        return self._finish(genome, trial_id, verdict["status"],
                            verdict.get("reason", ""), metrics, verdict)

    def _role_for(self, verdict: Mapping[str, Any], classification: str) -> str:
        if verdict["status"] == "eligible_for_operator_review":
            if classification in ("SYSTEMIC", "TRANSFERABLE"):
                return "champion"
            if classification == "ROBUST":
                return "specialist"     # wins selection regime only
            return "challenger"
        if verdict["status"] == "rejected" and "specialist" in verdict.get("reason", ""):
            return "specialist"
        if verdict["status"] == "rejected":
            return "failed_informative"
        return "failed_informative"

    def _transfer_classification(self, transfer: TransferEvaluator,
                                 candidate_params: Mapping[str, Any]) -> Tuple[str, Dict[str, Any]]:
        results = [transfer.run_scenario(s, self.incumbent_params, candidate_params)
                   for s in self.panels]
        selection = self.panels[0].regime if self.panels else "all"
        classification, details = transfer.classify(results, selection)
        details["regime_delta_map"] = {r.label: r.delta_net for r in results}
        return classification, details

    def _security_event(self, genome: ImprovementGenome, detail: str) -> None:
        try:
            self.memory.append_evidence(
                trial_id=f"SEC-{uuid.uuid4().hex[:8]}", nonce=uuid.uuid4().hex,
                payload={"genome_id": genome.genome_id, "detail": detail},
                status="security_event")
        except Exception:  # noqa: BLE001 - never let logging break the loop
            logger.exception("failed to record security event")

    def _finish(self, genome: ImprovementGenome, trial_id: str, status: str,
                reason: str, metrics: Mapping[str, Any],
                verdict: Mapping[str, Any]) -> PromotionDecision:
        try:
            self.memory.append_evidence(
                trial_id=trial_id, nonce=uuid.uuid4().hex,
                status=status,
                payload={"genome_id": genome.genome_id, "status": status,
                         "reason": reason, "metrics": dict(metrics),
                         "verdict": dict(verdict)})
        except Exception:  # noqa: BLE001
            status, reason = "insufficient_evidence", "durable ledger write failed"
        return PromotionDecision(genome_id=genome.genome_id, status=status,
                                 reason=reason, evidence=dict(verdict))
