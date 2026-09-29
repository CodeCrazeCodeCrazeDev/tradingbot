"""Bounded-parameter strategy adapters for Level-1 RSI candidates.

Candidates change exactly one numeric parameter of an allow-listed strategy
family; the adapter instantiates the *existing* strategy classes unchanged
and replays them causally (signal computed only from strictly-prior bars).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _file_hash(rel_path: str) -> str:
    return hashlib.sha256((_REPO_ROOT / rel_path).read_bytes()).hexdigest()


def candidate_code_hash() -> str:
    """Hash of the code a parameter candidate is allowed to touch."""
    parts = [
        _file_hash("trading_bot/strategies/institutional_strategies.py"),
        _file_hash("trading_bot/recursive_self_improvement/candidate_adapters.py"),
        _file_hash("trading_bot/evaluation/runner.py"),
    ]
    return hashlib.sha256("".join(parts).encode()).hexdigest()


def dependencies_hash() -> str:
    return _file_hash("poetry.lock")


@dataclass(frozen=True)
class AdapterSpec:
    """How to build and drive one allow-listed strategy family."""

    family: str
    allowed: Mapping[str, Tuple[float, float]]
    pairs: bool                     # True → operates on instrument pairs
    min_history: Callable[[Mapping[str, float]], int]
    build: Callable[[Mapping[str, Any]], Any]
    direction_of: Callable[[Dict[str, Any]], int]
    validate: Optional[Callable[[Mapping[str, float]], bool]] = None

    def check_params(self, params: Mapping[str, Any]) -> Tuple[bool, str]:
        if len(params) != 1:
            return False, "candidate must change exactly one parameter"
        name = next(iter(params))
        if name not in self.allowed:
            return False, f"{name!r} not in {self.family} allowlist"
        val = params[name]
        lo, hi = self.allowed[name]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            return False, f"{name} must be numeric"
        if not lo <= float(val) <= hi:
            return False, f"{name}={val} outside [{lo}, {hi}]"
        merged = dict(params)
        if self.validate is not None and not self.validate(merged):
            return False, f"{self.family} parameter constraint violated"
        return True, ""


def _dir_buy_sell(signal: Dict[str, Any]) -> int:
    return {"buy": 1, "sell": -1}.get(str(signal.get("action", "")).lower(), 0)


def _dir_spread(signal: Dict[str, Any]) -> int:
    return {"long_spread": 1, "short_spread": -1}.get(
        str(signal.get("action", "")).lower(), 0)


def _build_mean_reversion(params: Mapping[str, Any]) -> Any:
    from trading_bot.strategies.institutional_strategies import MeanReversionStrategy

    return MeanReversionStrategy(
        lookback=int(params["lookback"]),
        entry_threshold=float(params.get("entry_threshold", 1.0)),
    )


def _build_momentum(params: Mapping[str, Any]) -> Any:
    from trading_bot.strategies.institutional_strategies import MomentumStrategy

    return MomentumStrategy(
        fast_period=int(params.get("fast_period", 10)),
        slow_period=int(params.get("slow_period", 50)),
    )


def _build_stat_arb(params: Mapping[str, Any]) -> Any:
    from trading_bot.strategies.institutional_strategies import StatisticalArbitrageStrategy

    return StatisticalArbitrageStrategy(lookback=int(params["lookback"]))


def _momentum_ok(params: Mapping[str, float]) -> bool:
    fast = int(params.get("fast_period", 10))
    slow = int(params.get("slow_period", 50))
    return fast < slow


ADAPTERS: Dict[str, AdapterSpec] = {
    "mean_reversion": AdapterSpec(
        family="mean_reversion",
        allowed={"lookback": (2, 200), "entry_threshold": (0.5, 4.0)},
        pairs=False,
        min_history=lambda p: int(p.get("lookback", 20)) + 2,
        build=_build_mean_reversion,
        direction_of=_dir_buy_sell,
    ),
    "momentum": AdapterSpec(
        family="momentum",
        allowed={"fast_period": (2, 50), "slow_period": (10, 300)},
        pairs=False,
        min_history=lambda p: int(p.get("slow_period", 50)) + 2,
        build=_build_momentum,
        direction_of=_dir_buy_sell,
        validate=_momentum_ok,
    ),
    "stat_arb": AdapterSpec(
        family="stat_arb",
        allowed={"lookback": (10, 200)},
        pairs=True,
        min_history=lambda p: int(p.get("lookback", 60)) + 2,
        build=_build_stat_arb,
        direction_of=_dir_spread,
    ),
}


def get_adapter(family: str) -> AdapterSpec:
    try:
        return ADAPTERS[family]
    except KeyError as exc:
        raise KeyError(f"unsupported candidate strategy family {family!r}") from exc


def make_pairs(symbols: Tuple[str, ...]) -> Tuple[Tuple[str, str], ...]:
    """Deterministic instrument pairing for spread families."""
    ordered = tuple(sorted(symbols))
    return tuple((ordered[i], ordered[i + 1]) for i in range(0, len(ordered) - 1, 2))
