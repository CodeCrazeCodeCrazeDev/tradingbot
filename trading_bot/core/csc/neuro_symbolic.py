"""Neuro-symbolic reasoning layer for the SRE (advisory).

Encodes the operator-directed reasoning & sandbox policy as *data*:
neural-style hypotheses (pattern-proposed or model-injected) are gated
by symbolic rules before anything executes. Every risky decision is
hash-chained to an append-only ledger.

  NEURAL  -> propose(): pattern templates over real facts, or an
             injected model callable when one is wired (honest: no
             offline LLM assumed; the channel exists either way)
  SYMBOLIC-> verify(): forward-chained guard rules over the same facts
             -> confirmed | needs_regression | refused
  ROUTE   -> classify action_class, run the specialist's real checks,
             apply the POLICY gate, record to the sealed ledger

Policy (enforced, not advisory):
  - autonomous live-execution requests are REFUSED by construction
  - risky changes (deploy, creds, limits, capital, patching,
    promotion, kill-switch) REQUIRE signed operator approval
  - untrusted code/patches route sandbox-only
  - vulnerability findings stay SEALED until patched or operator
    approves coordinated disclosure
  - benchmark-only evidence can never produce a CONFIRMED verdict
    (regression/real-world channel required)

CSC_MANIFEST: advisory kind; discovery wires it at SHADOW.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
LEDGER_PATH = ROOT / "var" / "nsr_ledger.jsonl"

CSC_MANIFEST = {
    "id": "neuro_symbolic_reasoner",
    "kind": "advisory",
    "provides": ["neuro_symbolic", "reasoning"],
    "requires": ["market_data"],
    "factory": "trading_bot.core.csc.neuro_symbolic:build",
    "status": "candidate",
}


# ------------------------------------------------------------------
# Facts, rules, decisions

@dataclass
class Fact:
    predicate: str
    subject: str
    value: Any
    source: str


class ActionClass(str, Enum):
    DEFENSIVE_SECURITY = "defensive_security"
    CODE_HARDENING = "code_hardening"
    TRADING_RESEARCH = "trading_research"
    POST_TRADE = "post_trade_analysis"
    RISKY_CHANGE = "risky_change"          # deploy/creds/limits/etc
    LIVE_EXECUTION = "live_execution"      # autonomous orders


class ValidationChannel(str, Enum):
    REGRESSION = "regression"     # real-world/regression evidence
    BENCHMARK = "benchmark"       # benchmark-only — never confirms


# action_class -> gate. Encoded as data so the boundary is auditable.
POLICY: Dict[ActionClass, str] = {
    ActionClass.DEFENSIVE_SECURITY: "allow",
    ActionClass.CODE_HARDENING: "allow",
    ActionClass.TRADING_RESEARCH: "allow",
    ActionClass.POST_TRADE: "allow",
    ActionClass.RISKY_CHANGE: "requires_signed_approval",
    ActionClass.LIVE_EXECUTION: "refused",
}

_RISKY_OPS = {"deploy", "credentials", "risk_limits", "capital",
              "patch", "promote", "kill_switch"}


@dataclass
class Decision:
    hypothesis_id: str
    action_class: ActionClass
    gate: str                        # allow|requires_signed_approval|
                                     # refused|sandbox_only
    verdict: str                     # confirmed|needs_regression|
                                     # refused|pending
    evidence: List[str] = field(default_factory=list)
    sealed: bool = False             # vulnerability disclosure hold


# ------------------------------------------------------------------
# Specialist reviewers — persistent agents, real checks, advisory
# verdicts. Each returns {verdict, evidence}; they cannot authorize.

class Specialist:
    id = "base"

    def review(self, hyp: Dict[str, Any], ctx: Dict[str, Any]):
        raise NotImplementedError


class RiskSpecialist(Specialist):
    id = "risk"

    def review(self, hyp, ctx):
        ev = []
        v = "pass"
        if hyp.get("changes_sizing") or hyp.get("risk_limits"):
            v, ev = "flag", ["touches sizing/risk limits"]
        if hyp.get("action") in _RISKY_OPS:
            v = "flag"
            ev.append(f"risky op {hyp['action']}")
        return {"verdict": v, "evidence": ev or ["no risk surface"]}


class ExecutionSpecialist(Specialist):
    id = "execution"

    def review(self, hyp, ctx):
        if hyp.get("sends_orders") or hyp.get("action") == "live_exec":
            return {"verdict": "refuse",
                    "evidence": ["requests autonomous order flow"]}
        return {"verdict": "pass", "evidence": ["no order path"]}


class MacroSpecialist(Specialist):
    id = "macro"

    def review(self, hyp, ctx):
        db = ctx.get("macro_db")
        if not (db and Path(db).exists()):
            return {"verdict": "flag",
                    "evidence": ["macro_data.db unprovisioned"]}
        return {"verdict": "pass", "evidence": ["macro feeds live"]}


class BacktestSpecialist(Specialist):
    id = "backtest"

    def review(self, hyp, ctx):
        ch = ValidationChannel(hyp.get("channel", "benchmark"))
        if ch is ValidationChannel.BENCHMARK:
            return {"verdict": "needs_regression",
                    "evidence": ["benchmark-only — cannot confirm"]}
        return {"verdict": "pass",
                "evidence": ["regression channel declared"]}


class CodeReviewSpecialist(Specialist):
    id = "code_review"

    def review(self, hyp, ctx):
        ev = []
        diff = hyp.get("diff", "")
        for p in ctx.get("protected", ()):
            if p in diff:
                ev.append(f"diff touches protected path {p}")
        if "password" in diff or "api_key" in diff.lower():
            ev.append("possible secret in diff")
        return {"verdict": "flag" if ev else "pass",
                "evidence": ev or ["clean diff"]}


class SecuritySpecialist(Specialist):
    id = "security"

    def review(self, hyp, ctx):
        ev = []
        v = "pass"
        if hyp.get("vulnerability"):
            v = "flag"
            ev.append("vulnerability finding — sealed pending patch "
                      "or coordinated-disclosure approval")
        if hyp.get("untrusted"):
            ev.append("untrusted input — sandbox-only execution")
        return {"verdict": v, "evidence": ev or ["no security surface"],
                "sealed": bool(hyp.get("vulnerability")),
                "sandbox": bool(hyp.get("untrusted"))}


SPECIALISTS: List[Specialist] = [
    RiskSpecialist(), ExecutionSpecialist(), MacroSpecialist(),
    BacktestSpecialist(), CodeReviewSpecialist(), SecuritySpecialist()]


# ------------------------------------------------------------------
# Sealed ledger — append-only, hash-chained

class Ledger:
    def __init__(self, path: Path = LEDGER_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last = self._tail_hash()

    def _tail_hash(self) -> str:
        if not self.path.exists():
            return "genesis"
        try:
            *_, last = self.path.read_text().strip().split("\n")
            return hashlib.sha256(last.encode()).hexdigest()[:16]
        except Exception:  # noqa: BLE001
            return "genesis"

    def append(self, record: Dict[str, Any]) -> str:
        record["ts"] = time.time()
        record["prev"] = self._last
        line = json.dumps(record, sort_keys=True)
        self._last = hashlib.sha256(line.encode()).hexdigest()[:16]
        record["hash"] = self._last
        with self.path.open("a") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        return self._last

    def verify_chain(self) -> bool:
        if not self.path.exists():
            return True
        prev = "genesis"
        for line in self.path.read_text().strip().split("\n"):
            r = json.loads(line)
            if r["prev"] != prev:
                return False
            h = r.pop("hash")
            prev = hashlib.sha256(
                json.dumps(r, sort_keys=True).encode()).hexdigest()[:16]
            if prev != h:
                return False
        return True


# ------------------------------------------------------------------
# The reasoner

class NeuroSymbolicReasoner:
    """Advisory neuro-symbolic layer over the SRE. Propose -> verify
    -> route -> record. Every output is a Decision, never an action."""

    capability_id = "neuro_symbolic_reasoner"

    def __init__(self, ctx: Optional[Dict[str, Any]] = None,
                 model: Optional[Callable] = None,
                 ledger: Optional[Ledger] = None):
        self.ctx = ctx or {}
        self._model = model          # optional injected LLM callable
        self.ledger = ledger or Ledger()

    # NEURAL: pattern-based proposal templates over facts; the
    # injected model (if wired) proposes in the same schema.
    def propose(self, facts: List[Fact]) -> List[Dict[str, Any]]:
        hyps = []
        for f in facts:
            if f.predicate == "edge_verdict" and f.value == "no_edge":
                hyps.append({
                    "id": f"h_{f.subject}_invert",
                    "action_class": ActionClass.TRADING_RESEARCH.value,
                    "channel": "regression",
                    "text": f"invert {f.subject} and re-gate"})
            elif (f.predicate == "spread" and
                  isinstance(f.value, (int, float)) and f.value > 10):
                hyps.append({
                    "id": f"h_{f.subject}_spread",
                    "action_class": ActionClass.TRADING_RESEARCH.value,
                    "channel": "regression",
                    "text": f"{f.subject} spread regime filter"})
        if self._model:
            try:
                hyps.extend(self._model(facts) or [])
            except Exception:  # noqa: BLE001
                pass
        return hyps

    # SYMBOLIC: guard rules over facts -> verdict per hypothesis
    def verify(self, hyp: Dict[str, Any],
               facts: List[Fact]) -> str:
        if ValidationChannel(hyp.get("channel", "benchmark")) is \
                ValidationChannel.BENCHMARK:
            return "needs_regression"
        contradicting = [f for f in facts
                         if f.predicate == "counter_evidence" and
                         f.subject == hyp.get("id")]
        if contradicting:
            return "refused"
        return "confirmed_research" if hyp.get("action_class") in (
            ActionClass.TRADING_RESEARCH.value,) else "pending"

    # ROUTE: classify -> specialist checks -> policy gate -> ledger
    def route(self, hyp: Dict[str, Any],
              operator_approved: bool = False) -> Decision:
        # Normalize caller-supplied action strings (e.g. SRE
        # target_action) onto the policy classes — an unknown action
        # must land on the SAFEST class it plausibly is, never allow.
        ac_raw = hyp.get("action_class", "")
        action = hyp.get("action", "")
        try:
            ac = ActionClass(ac_raw)
        except ValueError:
            if action in _RISKY_OPS or ac_raw in _RISKY_OPS:
                ac = ActionClass.RISKY_CHANGE
            elif (hyp.get("sends_orders") or
                  action in ("live_exec", "order", "trade") or
                  ac_raw in ("live_exec", "live_execution", "order",
                             "trade")):
                ac = ActionClass.LIVE_EXECUTION
            else:
                ac = ActionClass.TRADING_RESEARCH
        reviews = {s.id: s.review(hyp, self.ctx)
                   for s in SPECIALISTS}
        ev = [f"{k}:{'/'.join(v['evidence'])}"
              for k, v in reviews.items()]
        gate = POLICY[ac]
        sealed = reviews["security"].get("sealed", False)
        if reviews["execution"]["verdict"] == "refuse":
            ac, gate = ActionClass.LIVE_EXECUTION, "refused"
        if reviews["security"].get("sandbox") or \
                hyp.get("untrusted"):
            gate = "sandbox_only"
        if gate == "refused":
            verdict = "refused"
        elif gate == "requires_signed_approval":
            verdict = ("pending_approval" if not operator_approved
                       else "approved_to_execute")
        elif gate == "sandbox_only":
            verdict = "sandbox_only"
        else:
            verdict = ("needs_regression" if any(
                r["verdict"] == "needs_regression"
                for r in reviews.values()) else "allowed")
        d = Decision(hypothesis_id=hyp.get("id", "?"),
                     action_class=ac, gate=gate, verdict=verdict,
                     evidence=ev, sealed=sealed)
        self.ledger.append({
            "type": "decision", "hypothesis": d.hypothesis_id,
            "action_class": ac.value, "gate": gate,
            "verdict": verdict, "sealed": sealed,
            "evidence": ev})
        return d

    def analyze(self, facts: Optional[List[Fact]] = None,
                operator_approved: bool = False) -> Dict[str, Any]:
        facts = facts or []
        hyps = self.propose(facts)
        decisions = []
        for h in hyps:
            verdict = self.verify(h, facts)
            h["_verify"] = verdict
            if verdict == "refused":
                decisions.append({"id": h["id"],
                                  "verdict": "refused"})
                continue
            d = self.route(h, operator_approved)
            decisions.append({"id": h["id"], "verdict": verdict,
                              "gate": d.gate, "route": d.verdict,
                              "sealed": d.sealed})
        return {"decisions": decisions, "ledger": str(self.ledger.path),
                "advisory_only": True}


def build(ctx: Optional[Dict[str, Any]] = None,
          model: Optional[Callable] = None) -> NeuroSymbolicReasoner:
    return NeuroSymbolicReasoner(ctx=ctx, model=model)
