"""CSE-CEDA: Invariant-Gated Evolution + Champion-Challenger gate.

Implements the two transferable principles from REDESIGN_DOCS/CSE_CEDA:

1. Runtime Invariants (IGE) — deterministic gates no agent may
   override: security (AST bans already enforced upstream), risk
   thresholds, license, and out-of-sample-beats-in-sample validation.
2. CEDA Decision Gate — a challenger is promoted only if it beats the
   champion across MULTIPLE market regimes (bull/bear/range/volatile),
   not one cherry window. Regime-split evaluation kills regime-
   unaware optimization bias.

Advisory boundary: this gate evaluates and reports. Promotion still
flows through the canonical approval path — CEDA output is evidence,
not authority.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional, Tuple

_BANNED_LICENSES = {"GPL", "AGPL", "LGPL", "SSPL", "CC-BY-NC"}


def _env_f(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


@dataclass
class InvariantReport:
    passed: bool
    violations: List[str] = field(default_factory=list)


class InvariantGate:
    """Four hardcoded runtime invariants — deterministic, agent-proof."""

    def __init__(self) -> None:
        self.max_drawdown = _env_f("TB_CEDA_MAX_DD", 0.15)
        self.max_exposure = _env_f("TB_CEDA_MAX_EXPOSURE", 0.50)
        self.min_oos_margin = _env_f("TB_CEDA_OOS_MARGIN", 0.0)

    def check(self, *, license_: str = "",
              max_drawdown: float = 0.0,
              max_exposure: float = 0.0,
              is_score: Optional[float] = None,
              oos_score: Optional[float] = None) -> InvariantReport:
        v: List[str] = []
        lic = (license_ or "").upper()
        if any(b in lic for b in _BANNED_LICENSES):
            v.append(f"license_invariant:{license_}")
        if max_drawdown > self.max_drawdown:
            v.append(f"risk_invariant:dd {max_drawdown:.3f}"
                     f">{self.max_drawdown}")
        if max_exposure > self.max_exposure:
            v.append(f"risk_invariant:exposure {max_exposure:.3f}"
                     f">{self.max_exposure}")
        if (is_score is not None and oos_score is not None
                and oos_score < is_score + self.min_oos_margin):
            v.append(
                f"validation_invariant:oos {oos_score:.4f}"
                f" < is {is_score:.4f}+{self.min_oos_margin}")
        return InvariantReport(passed=not v, violations=v)


@dataclass
class RegimeResult:
    regime: str
    champion_score: float
    challenger_score: float
    challenger_won: bool


@dataclass
class TournamentVerdict:
    promote: bool
    reason: str
    regimes: List[RegimeResult] = field(default_factory=list)
    wins: int = 0
    losses: int = 0
    min_regimes_won: int = 0


class CEDADecisionGate:
    """Champion-challenger tournament over regime-stratified windows.

    ``score_fn(candidate, regime_window) -> float`` is supplied by the
    caller (e.g. walk-forward Sharpe on that window). The gate itself
    only counts consistent wins — promotion needs the challenger to
    beat the champion in >= win_fraction of evaluated regimes AND a
    minimum absolute margin; ties and single-regime wins don't count.
    """

    def __init__(self, win_fraction: float = None,
                 min_margin: float = None,
                 min_regimes: int = None) -> None:
        self.win_fraction = win_fraction or _env_f(
            "TB_CEDA_WIN_FRAC", 0.6)
        self.min_margin = min_margin or _env_f(
            "TB_CEDA_MIN_MARGIN", 0.0)
        self.min_regimes = min_regimes or int(
            os.environ.get("TB_CEDA_MIN_REGIMES", "2"))

    def evaluate(
        self, champion: Any, challenger: Any,
        regime_windows: Dict[str, Any],
        score_fn,
    ) -> TournamentVerdict:
        results: List[RegimeResult] = []
        for regime, window in regime_windows.items():
            try:
                c_sc = float(score_fn(champion, window))
                x_sc = float(score_fn(challenger, window))
            except Exception:
                results.append(RegimeResult(
                    regime, 0.0, 0.0, challenger_won=False))
                continue
            won = x_sc > c_sc + self.min_margin
            results.append(RegimeResult(regime, c_sc, x_sc, won))

        wins = sum(1 for r in results if r.challenger_won)
        n = len(results)
        verdict = TournamentVerdict(
            promote=False, reason="", regimes=results,
            wins=wins, losses=n - wins)
        if n < self.min_regimes:
            verdict.reason = (
                f"insufficient regimes evaluated: {n}"
                f"<{self.min_regimes}")
            return verdict
        frac = wins / n
        if frac >= self.win_fraction:
            verdict.promote = True
            verdict.reason = (f"challenger won {wins}/{n} regimes "
                              f"(frac={frac:.2f} >= {self.win_fraction})")
        else:
            verdict.reason = (f"challenger won only {wins}/{n} "
                              f"regimes (frac={frac:.2f} "
                              f"< {self.win_fraction})")
        return verdict


def evaluate_and_gate(champion: Any, challenger: Any,
                      regime_windows: Dict[str, Any], score_fn,
                      invariant_kwargs: Dict[str, Any]
                      ) -> Dict[str, Any]:
    """One-call CSE-CEDA: invariants first (hard purge), then the
    regime tournament (evidence verdict)."""
    inv = InvariantGate().check(**invariant_kwargs)
    if not inv.passed:
        return {"promote": False,
                "reason": "invariant_violations",
                "violations": inv.violations,
                "regimes": []}
    verdict = CEDADecisionGate().evaluate(
        champion, challenger, regime_windows, score_fn)
    return {"promote": verdict.promote,
            "reason": verdict.reason,
            "violations": [],
            "regimes": [
                {"regime": r.regime,
                 "champion": r.champion_score,
                 "challenger": r.challenger_score,
                 "won": r.challenger_won}
                for r in verdict.regimes],
            "wins": verdict.wins, "losses": verdict.losses}
