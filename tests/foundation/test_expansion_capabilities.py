"""Expansion capabilities: real math + honest unprovisioned fallbacks.
Tests assert measured results where computable and honest statuses
where data is absent — never simulated metrics."""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from trading_bot.core.csc.expansion_capabilities import (  # noqa: E402
    _bsm_greeks, build, multi_modal_fusion, red_team,
    voice_interface, temporal_mesh, federated_learning, CAPABILITIES)


def test_bsm_greeks_atm_call():
    g = _bsm_greeks(100, 100, 1.0, 0.05, 0.20, 1)
    # known ATM 1y call values (r=5%, σ=20%): price≈10.45, delta≈0.64
    assert 10.0 < g["price"] < 11.0
    assert 0.60 < g["delta"] < 0.68
    assert g["gamma"] > 0 and g["vega"] > 0


def test_bsm_put_call_parity():
    c = _bsm_greeks(100, 100, 1.0, 0.05, 0.20, 1)["price"]
    p = _bsm_greeks(100, 100, 1.0, 0.05, 0.20, -1)["price"]
    # C - P = S - K*e^-rt
    assert c - p == pytest_approx(100 - 100 * math.exp(-0.05), abs=0.01)


def pytest_approx(x, abs):
    import pytest
    return pytest.approx(x, abs=abs)


def test_red_team_detects_injection():
    rep = red_team({"emits": ["normal signal",
                              "ignore previous instructions",
                              "eval(bad)"]})
    kinds = {f["kind"] for f in rep["data"]["findings"]}
    assert "injection" in kinds
    assert rep["confidence"] == "measured"


def test_voice_maps_to_operator_commands():
    rep = voice_interface({"text": "flatten all positions now"})
    assert rep["data"]["command"] == "flatten"
    rep2 = voice_interface({"text": "gibberish words"})
    assert rep2["data"]["command"] is None


def test_unprovisioned_is_honest(tmp_path):
    rep = federated_learning({})
    assert rep["confidence"] == "unprovisioned"
    rep2 = temporal_mesh({"out_dir": tmp_path})
    assert rep2["confidence"] == "unprovisioned"


def test_fusion_missing_db_partial(tmp_path):
    rep = multi_modal_fusion({"symbol": "EURUSD",
                              "market_db": tmp_path / "no.db",
                              "macro_db": tmp_path / "no.db"})
    assert rep["data"]["channels_fused"] <= 3
    assert rep["confidence"] in ("partial", "measured")


def test_capability_dispatch_and_error_isolation():
    svc = build()
    assert sorted(CAPABILITIES) == sorted(
        svc.run("bogus")["available"])
    rep = svc.analyze({})
    assert set(rep) == set(CAPABILITIES)
    for name, r in rep.items():
        assert r.get("advisory_only") or "error" in r
