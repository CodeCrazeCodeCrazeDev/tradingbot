"""M1 method->candidate compiler tests (synthetic_market-free: plain
numpy series keep this file light per AGENTS.md import-cost rules)."""

import numpy as np
import pytest

from trading_bot.core.csc.research.method_spec import (
    FAMILIES, MethodSpec, SpecError, align_pair, compile_rule,
    pair_pnl_bps, pair_triple, positions_triple, spec_from_dict)


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
        if fam == "stat_arb":
            continue  # pair family needs spec.pair — tested below
        spec = MethodSpec(spec_id=fam, hypothesis="h", family=fam)
        fn = compile_rule(spec)
        closes = _series("mr", n=250)
        vals = {fn(closes, i) for i in range(200, 249)}
        assert vals <= {-1, 0, 1}


PAIR = {"db": "x.db", "symbol": "B", "timeframe": "D1"}


def test_statarb_requires_pair():
    spec = MethodSpec(spec_id="p", hypothesis="h", family="stat_arb")
    with pytest.raises(SpecError, match="spec.pair"):
        compile_rule(spec)
    spec.pair = PAIR
    rule2 = compile_rule(spec)
    assert callable(rule2)


def test_statarb_fades_spread_extremes():
    rng = np.random.RandomState(1)
    n = 300
    # b random walk; a = b + small stationary spread (cointegrated)
    lb = np.cumsum(rng.randn(n) * 0.01)
    b = 100 * np.exp(lb)
    spread = 0.002 * np.sin(np.arange(n) / 8.0)
    a = b * np.exp(spread)
    spec = MethodSpec(spec_id="p", hypothesis="h", family="stat_arb",
                      params={"window": 40, "z": 1.0, "hedge": 1.0},
                      pair=PAIR)
    rule2 = compile_rule(spec)
    sigs = [rule2(a, b, i) for i in range(60, n - 1)]
    assert set(sigs) <= {-1, 0, 1}
    # stationary spread must produce BOTH directions over time
    assert 1 in sigs and -1 in sigs


def test_align_pair_inner_join():
    a_ts = [f"2024-01-{i:02d}T00:00:00+00:00" for i in range(1, 62)]
    b_ts = [f"2024-01-{i:02d}T00:00:00+00:00" for i in range(2, 63)]
    a = np.arange(1., 62.)
    b = np.arange(10., 71.)
    aa, bb = align_pair(a_ts, a, b_ts, b)
    # shared timestamps are days 2..61 -> a idx 1..60, b idx 0..59
    assert list(aa) == list(np.arange(2., 62.))
    assert list(bb) == list(np.arange(10., 70.))
    with pytest.raises(SpecError, match="too thin"):
        align_pair(["t1"], np.array([1.]), ["t2"], np.array([2.]))


def test_pair_pnl_and_triple_shapes():
    rng = np.random.RandomState(2)
    n = 200
    b = 100 * np.exp(np.cumsum(rng.randn(n) * 0.01))
    a = b * np.exp(0.003 * np.sin(np.arange(n) / 6.0))
    spec = MethodSpec(spec_id="p", hypothesis="h", family="stat_arb",
                      params={"window": 30, "z": 1.5, "hedge": 1.0},
                      pair=PAIR)
    rule2 = compile_rule(spec)
    pnl = pair_pnl_bps(rule2, a, b, 1.0, 5.0)
    assert len(pnl) == n - 1
    pos, base, rets = pair_triple(rule2, a, b, 1.0)
    assert len(pos) == len(base) == len(rets) == n - 1
    assert all(x == 0.0 for x in base)
    # spread return identity: rets[i] = ra - hedge*rb
    i = 50
    expect = (a[i + 1] / a[i] - 1.0) - 1.0 * (b[i + 1] / b[i] - 1.0)
    assert rets[i] == pytest.approx(expect)


def test_statarb_spec_roundtrip_and_extractor():
    from trading_bot.core.csc.research.spec_extractor import (
        extract_specs)
    d = {"spec_id": "pp", "hypothesis": "h", "family": "stat_arb",
         "params": {"window": 45, "z": 1.5}, "pair": PAIR}
    s = spec_from_dict(d)
    assert s.pair == PAIR
    compile_rule(s)
    specs = extract_specs(
        "pairs trading cointegration forex z-score 2.0")
    assert specs and specs[0].family == "stat_arb"
    # extracted stat_arb has NO pair -> compile_rule must reject
    with pytest.raises(SpecError, match="spec.pair"):
        compile_rule(specs[0])
