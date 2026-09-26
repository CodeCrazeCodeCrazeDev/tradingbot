"""Deterministic synthetic market generator: reproducibility and structure."""

import math

import pytest

from trading_bot.evaluation.synthetic_market import (
    RegimeSpec,
    SyntheticMarketGenerator,
    SyntheticMarketSpec,
    fingerprint,
    fingerprint_all,
)


def _spec(seed=7):
    return SyntheticMarketSpec(
        seed=seed,
        instruments=("EURUSD", "GBPUSD"),
        regimes=(
            RegimeSpec("trend", 40, drift=0.0004, vol=0.001),
            RegimeSpec("mean_revert", 40, drift=0.0, vol=0.001, ar1=-0.5),
            RegimeSpec("crash", 20, drift=-0.004, vol=0.004),
        ),
    )


def test_same_seed_identical_frames_and_fingerprint():
    a = SyntheticMarketGenerator(_spec()).generate()
    b = SyntheticMarketGenerator(_spec()).generate()
    assert fingerprint_all(a) == fingerprint_all(b)
    for sym in a:
        assert a[sym].equals(b[sym])


def test_different_seed_differs():
    a = SyntheticMarketGenerator(_spec(1)).generate()
    b = SyntheticMarketGenerator(_spec(2)).generate()
    assert fingerprint_all(a) != fingerprint_all(b)


def test_structure_and_ohlc_sanity():
    frames = SyntheticMarketGenerator(_spec()).generate()
    for sym, df in frames.items():
        assert len(df) == 100
        assert (df["high"] >= df[["open", "close"]].max(axis=1) - 1e-12).all()
        assert (df["low"] <= df[["open", "close"]].min(axis=1) + 1e-12).all()
        assert (df["open"] > 0).all() and (df["close"] > 0).all()
        assert list(df["timestamp"]) == list(range(100))


def test_planted_oscillation_is_detectable_in_returns():
    spec = SyntheticMarketSpec(
        seed=3,
        instruments=("EURUSD",),
        regimes=(RegimeSpec("mean_revert", 64, vol=0.0002,
                            sine_amp=0.004, sine_period=8),),
    )
    df = SyntheticMarketGenerator(spec).generate()["EURUSD"]
    rets = df["close"].pct_change().dropna()
    # The injected sine must dominate the flat noise floor.
    assert rets.abs().mean() > 0.002


def test_fingerprint_changes_on_any_cell():
    spec = SyntheticMarketSpec(seed=1, instruments=("EURUSD",),
                               regimes=(RegimeSpec("flat", 10, vol=0.0001),))
    df = SyntheticMarketGenerator(spec).generate()["EURUSD"]
    fp = fingerprint(df)
    df2 = df.copy()
    df2.loc[3, "close"] += 0.0001
    assert fingerprint(df2) != fp


def test_csv_dir_source_loads_and_provenance(tmp_path):
    """TD-05: governed real-data path — multi-instrument CSVs load with
    validation and auditable per-file provenance."""
    import pandas as pd
    from trading_bot.evaluation.synthetic_market import CsvDirSource

    for sym, n in (("EURUSD", 8), ("GBPUSD", 6)):
        pd.DataFrame({
            "timestamp": range(1_700_000_000, 1_700_000_000 + n * 900, 900),
            "open": [1.10 + i * 0.0001 for i in range(n)],
            "high": [1.10 + i * 0.0001 + 0.0005 for i in range(n)],
            "low": [1.10 + i * 0.0001 - 0.0005 for i in range(n)],
            "close": [1.10 + (i + 1) * 0.0001 for i in range(n)],
            "volume": [1000.0] * n,
        }).to_csv(tmp_path / f"{sym}.csv", index=False)

    src = CsvDirSource(str(tmp_path), ("EURUSD", "GBPUSD"))
    frames = src.load()
    assert set(frames) == {"EURUSD", "GBPUSD"}
    assert list(frames["EURUSD"]["timestamp"]) == list(range(8))
    assert src.dataset_hash() == fingerprint_all(frames)
    prov = src.provenance()
    assert prov["EURUSD"]["rows"] == 8 and prov["GBPUSD"]["rows"] == 6
    assert len(prov["EURUSD"]["file_sha256"]) == 64


def test_csv_dir_source_rejects_bad_files(tmp_path):
    import pandas as pd
    from trading_bot.evaluation.synthetic_market import CsvDirSource

    with pytest.raises(RuntimeError, match="missing real-data file"):
        CsvDirSource(str(tmp_path), ("EURUSD",)).load()

    pd.DataFrame({"timestamp": [3, 1, 2], "open": [1, 1, 1],
                  "high": [1, 1, 1], "low": [1, 1, 1],
                  "close": [1, 1, 1], "volume": [1, 1, 1]}
                 ).to_csv(tmp_path / "EURUSD.csv", index=False)
    with pytest.raises(RuntimeError, match="strictly increasing"):
        CsvDirSource(str(tmp_path), ("EURUSD",)).load()
