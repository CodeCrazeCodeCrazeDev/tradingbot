"""M1 method->candidate compiler tests (synthetic_market-free: plain
numpy series keep this file light per AGENTS.md import-cost rules)."""

import numpy as np
import pytest

from trading_bot.core.csc.research.method_spec import (
    FAMILIES, MethodSpec, SpecError, compile_rule, positions_triple,
    spec_from_dict)


def _series(kind="up", n=300, seed=0):
    rng = np.random.RandomState(seed)
    if kind == "up":
        return 100 * np.exp(np.cumsum(0.001 + rng.randn(n) * 0.005))
    if kind == "down":
        return 100 * np.exp(np.cumsum(-0.001 + rng.randn(n) * 0.005))
    if kind == "mr":  # mean-reverting around 100
        x = np.empty(n)
        x[0] = 100.0
        for i in range(1, n):
            x[i] = x[i - 1] + 0.3 * (100 - x[i - 1]) + rng.randn() * 0.4
        return x
    return 100 + np.cumsum(rng.randn(n) * 0.1)


def test_compile_rejects_unknown_family():
    spec = MethodSpec(spec_id="x", hypothesis="h", family="alchemy")
    with pytest.raises(SpecError, match="not allow-listed"):
        compile_rule(spec)


def test_compile_rejects_out_of_bounds_and_nonnumeric():
    spec = MethodSpec(spec_id="x", hypothesis="h", family="momentum",
                      params={"lookback": 500})
    with pytest.raises(SpecError, match="outside bounds"):
        compile_rule(spec)
    spec.params = {"lookback": float("nan")}
    with pytest.raises(SpecError, match="not finite"):
        compile_rule(spec)
    spec.params = {"bogus": 1.0}
    with pytest.raises(SpecError, match="not declared"):
        compile_rule(spec)


def test_compile_requires_ids():
    spec = MethodSpec(spec_id="", hypothesis="h", family="momentum")
    with pytest.raises(SpecError):
        compile_rule(spec)


def test_defaults_and_bounds_merge():
    spec = MethodSpec(spec_id="m", hypothesis="h", family="momentum",
                      params={"lookback": 5})
    fn = compile_rule(spec)  # threshold_bps falls back to default 15
    closes = _series("up", n=200)
    assert fn(closes, 100) in (-1, 0, 1)


def test_momentum_direction_on_trends():
    spec = MethodSpec(spec_id="m", hypothesis="h", family="momentum",
                      params={"lookback": 10, "threshold_bps": 5})
    fn = compile_rule(spec)
    up = _series("up", n=300)
    # deep into a sustained uptrend the rule must be long, not short
    late_signals = [fn(up, i) for i in range(250, 299)]
    assert sum(s == 1 for s in late_signals) > sum(s == -1 for s in late_signals)


def test_volmom_rejects_inverted_windows():
    spec = MethodSpec(spec_id="v", hypothesis="h",
                      family="vol_regime_momentum",
                      params={"vol_short": 40, "vol_long": 20})
    with pytest.raises(SpecError, match="vol_short"):
        compile_rule(spec)


def test_positions_triple_lookahead_free_alignment():
    spec = MethodSpec(spec_id="t", hypothesis="h", family="momentum",
                      params={"lookback": 5, "threshold_bps": 1})
    fn = compile_rule(spec)
    closes = _series("up", n=120)
    pos, base, rets = positions_triple(fn, closes)
    assert len(pos) == len(base) == len(rets) == len(closes) - 1
    assert all(b == 0.0 for b in base)
    # bar_returns[i] must be the NEXT bar's move: c[i+1]/c[i]-1
    assert rets[10] == pytest.approx(closes[11] / closes[10] - 1.0)
    # signal at i can only see closes[..i]: perturbing future bars
    # must not change pos[i]
    mutated = closes.copy()
    mutated[50:] *= 3.0
    pos2, _, _ = positions_triple(fn, mutated)
    assert pos[:45] == pos2[:45]


def test_spec_from_dict_preserves_extras_in_provenance():
    d = {"spec_id": "s", "hypothesis": "h", "family": "donchian",
         "params": {"channel": 15}, "source_url": "http://x",
         "falsification": "fails if LCB<=0 on any segment"}
    spec = spec_from_dict(d)
    assert spec.family == "donchian"
    assert spec.params == {"channel": 15.0}
    assert spec.provenance["spec_extra_keys"]["source_url"] == "http://x"
    assert spec.falsification.startswith("fails")
    compile_rule(spec)  # channel=15 within [5,60]


def test_all_families_compile_with_defaults():
    for fam in FAMILIES:
        spec = MethodSpec(spec_id=fam, hypothesis="h", family=fam)
        fn = compile_rule(spec)
        closes = _series("mr", n=250)
        vals = {fn(closes, i) for i in range(200, 249)}
        assert vals <= {-1, 0, 1}
